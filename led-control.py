#!/usr/bin/env python3
"""
Framework Laptop 16 LED Matrix Control
Fixed to perfectly mirror the official Rust SDK serial strategy.
"""

import sys
import time
import signal

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("ERROR: pyserial required. Install with: python3 -m pip install pyserial")
    sys.exit(1)

# =============================================================================
# PROTOCOL CONSTANTS (From Rust SDK)
# =============================================================================
MAGIC = bytes([0x32, 0xAC])
FRAMEWORK_VID = 0x32AC
LED_MATRIX_PID = 0x0020

# Commands
CMD_BRIGHTNESS     = 0x00
CMD_SLEEPING       = 0x03
CMD_ANIMATE        = 0x04
CMD_SEND_COL       = 0x07  # send_col() in Rust
CMD_COMMIT_COLS    = 0x08  # commit_cols() in Rust

WIDTH = 9
HEIGHT = 34

# Rust SDK uses exactly 20ms timeout for everything
SERIAL_TIMEOUT = 0.02 

# =============================================================================
# CORE SERIAL COMMUNICATION (Mimics simple_cmd_port & send_col in Rust)
# =============================================================================

def send_cmd(port: serial.Serial, command: int, payload: bytes = b""):
    """
    Exact Python equivalent of Rust's simple_cmd_port().
    Constructs the buffer and sends it in one piece.
    """
    buffer = bytearray(MAGIC)
    buffer.append(command)
    buffer.extend(payload)
    port.write(bytes(buffer))

def send_col(port: serial.Serial, x: int, vals: list[int] | bytes):
    """
    Exact Python equivalent of Rust's send_col().
    Stages a single 1x34 column. MUST be followed by commit_cols().
    """
    if isinstance(vals, list):
        vals = bytes(vals)
    # Payload format from Rust: [x, val0, val1, ... val33]
    payload = bytes([x]) + vals
    send_cmd(port, CMD_SEND_COL, payload)

def commit_cols(port: serial.Serial):
    """
    Exact Python equivalent of Rust's commit_cols().
    Pushes the staged columns to the physical display.
    """
    send_cmd(port, CMD_COMMIT_COLS)

# =============================================================================
# PORT MANAGEMENT
# =============================================================================

def find_port() -> str | None:
    for p in serial.tools.list_ports.comports():
        if p.vid == FRAMEWORK_VID and p.pid == LED_MATRIX_PID:
            return p.device
    return None

def open_port(device: str) -> serial.Serial:
    """
    Opens port EXACTLY like Rust: 115200 baud, 20ms timeout.
    NO DTR RESET. NO WRITE TIMEOUT.
    """
    return serial.Serial(device, 115200, timeout=SERIAL_TIMEOUT)

# =============================================================================
# PATTERN GENERATORS
# =============================================================================

def get_all_on() -> list[list[int]]:
    return [[255] * WIDTH for _ in range(HEIGHT)]

def get_all_off() -> list[list[int]]:
    return [[0] * WIDTH for _ in range(HEIGHT)]

def get_gradient_v() -> list[list[int]]:
    return [[int(r * 255 / (HEIGHT - 1))] * WIDTH for r in range(HEIGHT)]

def get_gradient_h() -> list[list[int]]:
    return [[int(c * 255 / (WIDTH - 1)) for c in range(WIDTH)] for _ in range(HEIGHT)]

def get_checkerboard() -> list[list[int]]:
    return [[255 if (r + c) % 2 == 0 else 0 for c in range(WIDTH)] for r in range(HEIGHT)]

def get_border() -> list[list[int]]:
    return [[255 if r in (0, HEIGHT-1) or c in (0, WIDTH-1) else 0 for c in range(WIDTH)] for r in range(HEIGHT)]

def get_x() -> list[list[int]]:
    pixels = [[0] * WIDTH for _ in range(HEIGHT)]
    for r in range(HEIGHT):
        c1 = int(r * (WIDTH - 1) / (HEIGHT - 1))
        c2 = int((HEIGHT - 1 - r) * (WIDTH - 1) / (HEIGHT - 1))
        pixels[r][c1] = 255
        pixels[r][c2] = 255
    return pixels

def get_heart() -> list[list[int]]:
    heart = ["0.10.10.", "1.11.11.", "11111111", "11111111", "01111110", "00111100", "00011000"]
    pixels = [[0] * WIDTH for _ in range(HEIGHT)]
    for i, row_str in enumerate(heart):
        for c, ch in enumerate(row_str):
            if ch == "1" and 8 + i < HEIGHT and c < WIDTH:
                pixels[8 + i][c] = 255
    return pixels

# =============================================================================
# FRAME RENDERING
# =============================================================================

def render_matrix(port: serial.Serial, pixels: list[list[int]]):
    """
    Sends a 2D array to the display.
    Exactly mimics the loop in all_brightnesses_cmd() in Rust.
    """
    # Convert [row][col] to [col][row] if needed
    if len(pixels) == HEIGHT and len(pixels[0]) == WIDTH:
        cols = [[pixels[r][c] for r in range(HEIGHT)] for c in range(WIDTH)]
    else:
        cols = pixels

    for x in range(WIDTH):
        send_col(port, x, cols[x])
        # CRITICAL: 10ms delay prevents USB hardware buffer overflow.
        # The Rust SDK relies on write_all() blocking, but Python's write()
        # returns instantly to the OS buffer. We must yield to let the 
        # device's UART drain the buffer.
        time.sleep(0.01) 
        
    commit_cols(port)

# =============================================================================
# DEMOS
# =============================================================================

def demo_scan(port: serial.Serial):
    print("Scanning each LED individually...")
    for r in range(HEIGHT):
        for c in range(WIDTH):
            pixels = [[0] * WIDTH for _ in range(HEIGHT)]
            pixels[r][c] = 255
            render_matrix(port, pixels)
            print(f"\r  row={r:2d}, col={c}  ", end="", flush=True)
    print("\n  Done!")

def demo_cycle(port: serial.Serial):
    patterns = [
        ("All On", get_all_on()), ("Gradient V", get_gradient_v()),
        ("Gradient H", get_gradient_h()), ("Checkerboard", get_checkerboard()),
        ("Border", get_border()), ("X", get_x()), ("Heart", get_heart()),
        ("All Off", get_all_off()),
    ]
    for name, pat in patterns:
        render_matrix(port, pat)
        print(f"\r  {name:<15s}  ", end="", flush=True)
        time.sleep(1.0)
    print("\n  Done!")

# =============================================================================
# MAIN
# =============================================================================

PATTERNS = {
    "all_on": get_all_on, "on": get_all_on,
    "all_off": get_all_off, "off": get_all_off,
    "gradient": get_gradient_v, "gradient_v": get_gradient_v, "gradient_h": get_gradient_h,
    "checkerboard": get_checkerboard, "check": get_checkerboard,
    "border": get_border, "x": get_x, "heart": get_heart,
}

def main():
    if not sys.argv[1:] or "--help" in sys.argv[1:]:
        print("Usage: python3 led-control.py [--port /dev/ttyACM0] [pattern|demo]")
        print("Patterns: all_on, all_off, gradient, gradient_h, checkerboard, border, x, heart")
        print("Demos: scan, cycle")
        sys.exit(0)

    args = sys.argv[1:]
    device = None
    command = None
    
    i = 0
    while i < len(args):
        if args[i] == "--port" and i + 1 < len(args):
            device = args[i+1]; i += 2
        elif not args[i].startswith("--"):
            command = args[i]; i += 1
        else:
            i += 1

    if not command:
        print("No command specified."); sys.exit(1)

    device = device or find_port()
    if not device:
        print("ERROR: No Framework LED Matrix found!"); sys.exit(1)

    print(f"Opening {device}...")
    port = open_port(device)

    # Initialize like Rust SDK
    send_cmd(port, CMD_SLEEPING, b'\x00') # Wake
    send_cmd(port, CMD_ANIMATE, b'\x00')  # Stop built-in animations
    send_cmd(port, CMD_BRIGHTNESS, b'\xff') # Full brightness
    time.sleep(0.05)

    def cleanup(signum=None, frame=None):
        try:
            render_matrix(port, get_all_off())
            port.close()
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)

    try:
        if command in PATTERNS:
            print(f"Displaying '{command}'...")
            render_matrix(port, PATTERNS[command]())
            print("Press Ctrl+C to exit")
            while True: time.sleep(1)
        elif command == "scan":
            demo_scan(port)
        elif command == "cycle":
            demo_cycle(port)
        else:
            print(f"Unknown command: {command}")
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

if __name__ == "__main__":
    main()
