"""Vertical text marquee: text rotated 90 deg, scrolling up or down the tall panel.

Run:  .venv/bin/python examples/text_marquee.py [TEXT] [--port /dev/ttyACM0] [--down]
Live keys (no Enter):  space = cycle speed, d = flip direction, q/Ctrl+C = quit.
"""
import argparse
import select
import sys
import termios
import time
import tty

import _bootstrap  # noqa: F401  (selects installed package or in-repo src/)
from ledmatrix import Font, draw_text_scrolling, open_device
from ledmatrix.cli.main import _logical_canvas, _rotate_canvas

SPEEDS = [0.12, 0.06, 0.03]  # seconds per frame; space cycles through these


def poll_key():
    """Return a pending keystroke without blocking, or None."""
    if select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.read(1)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?", default="HELLO ")
    ap.add_argument("--port")
    ap.add_argument("--down", action="store_true", help="start scrolling down (default: up)")
    args = ap.parse_args()

    font = Font.load("5x7")
    speed_i = 1
    rotation = 270 if args.down else 90

    old = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())
    with open_device(port=args.port) as device:
        device.wake()
        device.set_animation(False)
        device.set_brightness(100)
        print("space=speed  d=direction  q=quit")
        try:
            while True:
                logical = _logical_canvas(rotation)
                for frame in draw_text_scrolling(logical, args.text, font=font, y=1):
                    device.set_leds(_rotate_canvas(frame, rotation))
                    time.sleep(SPEEDS[speed_i])
                    key = poll_key()
                    if key in ("q", "\x03"):
                        return
                    if key == " ":
                        speed_i = (speed_i + 1) % len(SPEEDS)
                    elif key == "d":
                        rotation = 270 if rotation == 90 else 90
                        break  # restart the pass in the new direction
        except KeyboardInterrupt:
            pass
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old)
            device.set_leds(_logical_canvas(0))  # clear (blank 9x34)


if __name__ == "__main__":
    main()
