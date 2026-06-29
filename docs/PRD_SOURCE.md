# Product Requirements Document (PRD)
# `ledmatrix` — A Cross-Platform Python SDK for the Framework 16 LED Matrix

**Document version:** 1.1 (Revised for focused SDK scope)  
**Status:** Draft for review  
**Owner:** [You]  
**Target platforms:** Linux (x86_64, aarch64), Windows 10/11 (x86_64, arm64), macOS (best-effort)  
**Target Hardware:** Framework 16 LED Matrix Input Module *only*

---

## 1. Executive Summary

This document specifies a Python package, **`ledmatrix`**, that provides a unified, high-performance, cross-platform API for driving the Framework 16 Laptop's LED Matrix Input Module. The library is generalized from the core logic found in Framework Computer's `inputmodule-rs` project—the reference implementation that powers the 39×9 monochrome grid, including a port of DOOM that runs smoothly on the display.

The library's mission is to extract the core transport, HID framing, pixel packing, and frame-scheduling logic and package it as an installable, documented, tested Python module that works identically on Linux and Windows. 

Crucially, **this is a development toolkit, not an application**. It does not ship with prebuilt games or animations. Instead, it provides developers with precise, granular control over the hardware: lighting up specific individual pixels, drawing rectangular areas, rendering fonts, and streaming raw frames with v-blank synchronization. It serves as the foundational layer upon which users can build their own games, dashboards, and ambient animations.

---

## 2. Background & Motivation

### 2.1 The reference implementation

Framework Computer's `inputmodule-rs` repository contains the firmware (Rust, targeting RP2040) and a Python control tool. This tool proved that the host→device frame pipeline is fast enough for real-time game rendering (e.g., DOOM) via a `ScheduleFrame` command that paces the host to the device's v-blank. 

### 2.2 Why generalize?

The existing Python tooling is tightly coupled to Framework's CLI, monolithic in structure, and Linux-centric in its assumptions (udev rules, `/dev/hidraw*`). 

`ledmatrix` extracts the transport-, device-, and platform-agnostic kernels of that system and re-exposes them through a stable, typed, documented Python API focused entirely on **drawing primitives** and **frame streaming** for the Framework 16 module.

---

## 3. Research Summary

### 3.1 Target Hardware: Framework 16 LED Matrix
- **Controller:** RP2040
- **Interface:** USB HID (Full-Speed, 12 Mbps)
- **Native resolution:** 39×9 (351 pixels)
- **Color:** Monochrome (1-bit per pixel)
- **Report size:** 64 bytes max per HID output report. A 39×9 frame requires 44 bytes (351 bits rounded up), fitting comfortably in a single report.

### 3.2 Transport: USB HID
- **Linux backend:** `hidraw` (kernel) — accessible via `/dev/hidraw*`, requires udev rules for non-root access.
- **Windows backend:** `hid.dll` — accessible to any user. The Framework LED Matrix declares a vendor-specific usage page, avoiding Windows' exclusive-lock conflict on generic mice/keyboard usage pages.
- **macOS backend:** IOHIDManager — works via `hidapi`, best-effort support.

### 3.3 Frame timing
The firmware exposes a `ScheduleFrame` command that accepts a frame buffer and returns an ACK on v-blank. This allows host software to **pace** rather than **poll**. Naïve busy-loop streaming causes HID queue overflow and tearing; the v-blank-locked scheduler is essential for smooth rendering.

### 3.4 Cross-platform HID in Python
**Decision:** Use `hidapi` (the C library) via the **`hid` PyPI package** as the primary binding. Provide a ctypes fallback for environments where the compiled wheel is unavailable. Abstract the backend behind an internal `Transport` interface.

---

## 4. Goals & Non-Goals

### 4.1 Goals
1. **Cross-platform parity:** Identical public API on Linux and Windows; documented macOS support.
2. **First-class Framework 16 support:** Works out-of-the-box with the Framework 16 LED Matrix Input Module.
3. **Granular Drawing Primitives:** Provide explicit APIs to light up individual pixels, fill specific rectangular areas, draw lines, and clear regions.
4. **High-level canvas API:** A Pillow-compatible `Image`-like surface that "just prints" to the matrix.
5. **Low-level command API:** Direct access to the wire protocol for power users (brightness, sleep, bootloading).
6. **Frame-accurate streaming:** V-blank-aware frame scheduler; no tearing, no HID queue overflow.
7. **Installable in <60 seconds:** `pip install ledmatrix` with binary wheels for Linux/Windows; no manual `hidapi` install.

### 4.2 Non-Goals
1. **NOT an application or game engine:** No prebuilt games (Snake, DOOM, etc.) or ambient animations will be shipped. This is purely a library for developers to build their own.
2. **NOT multi-device:** Strictly supports the Framework 16 LED Matrix (39×9 Mono). Will not support Pimoroni, RGB matrices, or generic SH1106 displays.
3. **NOT a firmware project.** Firmware flashing stays in `inputmodule-rs` / vendor tools.
4. **NOT a GUI application.** CLI tools for debugging yes; GUI no.

---

## 5. Target Users & Personas

### 5.1 Persona A — "Maker Maya"
- Hobbyist with a Framework 16 laptop, wants to write a custom Python script to display CPU temps or a custom clock on the LED matrix.
- Wants: `pip install ledmatrix`, draw some text, light up a specific pixel, ship it.

### 5.2 Persona B — "Game Dev Greg"
- Building a small game (Snake, Tetris, a raycaster) targeting the 39×9 grid.
- Needs: A fast canvas to set specific pixels, draw bounding boxes, and stream frames at 60 FPS without tearing.
- Wants: A robust `Canvas` and `Device.show_frame()` API without having to learn HID protocols.

### 5.3 Persona C — "Integrator Iris"
- Embedding LED matrix control into a larger application (home automation, CI dashboard).
- Needs: Stable, versioned API; async; long-running reliability; device hot-plug handling.
- Wants: Explicit `Device` lifecycle, `async with Device.open() as d:`, hot-plug callbacks.

---

## 6. Functional Requirements

### FR-1 — Device discovery & lifecycle
- **FR-1.1** Enumerate connected Framework 16 LED Matrix devices, returning a list of `DeviceInfo`.
- **FR-1.2** Open a device, returning a `Device` handle.
- **FR-1.3** Support hot-plug events (device-connected / device-removed) via callback registration.
- **FR-1.4** Provide graceful degradation when a device is unplugged mid-session: raise `DeviceDisconnected` on the next I/O, do not crash.
- **FR-1.5** Support opening a specific device by serial number when multiple identical devices are present.

### FR-2 — Transport layer
- **FR-2.1** Send and receive HID feature/input/output reports by report ID.
- **FR-2.2** Abstract the backend (`hidapi` ctypes, `hid` PyPI wheel) behind a `Transport` interface.
- **FR-2.3** Support read timeouts (default 1000 ms) without busy-waiting.
- **FR-2.4** Provide a `MockTransport` for unit testing and CLI dry-runs.

### FR-3 — Granular Drawing Primitives (Core Feature)
- **FR-3.1** Provide a `Canvas` class representing the 39×9 grid.
- **FR-3.2** `set_pixel(x, y, state)`: Light up or turn off a specific individual pixel.
- **FR-3.3** `fill_rect(x, y, width, height, state)`: Light up or clear a specific rectangular area.
- **FR-3.4** `clear_rect(x, y, width, height)`: Shortcut for clearing a specific region.
- **FR-3.5** `clear()`: Clear the entire canvas.
- **FR-3.6** `invert_rect(x, y, width, height)`: Invert the state of all pixels in a specific area.
- **FR-3.7** `draw_line(x0, y0, x1, y1, state)`: Draw a line between two points.
- **FR-3.8** `get_pixel(x, y)`: Read the state of a specific pixel.

### FR-4 — Canvas & Framebuffer
- **FR-4.1** `Canvas` stores data as a 1-bit-per-pixel packed bytearray internally.
- **FR-4.2** Accept Pillow `Image` objects via `Canvas.from_pil(img, dither=...)` (converts to 39×9 mono).
- **FR-4.3** Accept numpy arrays `(9, 39)` uint8 via `Canvas.from_array(arr)`.
- **FR-4.4** `Canvas.show(device)` sends the canvas to the device with v-blank pacing.

### FR-5 — Command API (low-level)
- **FR-5.1** Expose typed methods for Framework 16 commands: `set_brightness`, `set_leds`, `set_pattern`, `sleep`, `wake`, `is_awake`, `set_fps`, `set_power_mode`, `panic`, `get_device_info`, `schedule_frame`.
- **FR-5.2** Each method validates argument ranges (e.g., 0 <= x < 39, 0 <= y < 9) and raises a `ProtocolError` before touching the wire.
- **FR-5.3** Provide `device.raw_command(opcode, payload)` for vendor-extension commands.

### FR-6 — Frame scheduler & streaming
- **FR-6.1** Provide a `FrameScheduler` that uses `set_fps` and `schedule_frame` to throttle the host.
- **FR-6.2** V-blank-locked pacing: host calls `device.show_frame(canvas)`, blocks on ACK, then returns. Guarantees no tearing.
- **FR-6.3** Backpressure: If the user calls `show()` faster than the device can drain, the call blocks (sync) or awaits (async) — it never silently drops frames.

### FR-7 — Image pipeline (for host rendering)
- **FR-7.1** `ImagePipeline` with stages: `resize`, `color_convert`, `dither`, `pack`.
- **FR-7.2** Resize strategies: `nearest`, `bilinear`, `area` (Pillow-backed).
- **FR-7.3** Dither strategies: `none`, `threshold`, `bayer2x2`, `bayer4x4`, `floyd_steinberg`.
- **FR-7.4** Pipeline output maps directly to the 39×9 1bpp packed wire format.

### FR-8 — Text rendering
- **FR-8.1** Bundle BDF fonts suitable for 9px height: `tom-thumb.bdf` (4×6), `5x7.bdf`, `3x5.bdf`.
- **FR-8.2** `Font` class with `text_width(s)`, `draw_text(canvas, x, y, s)`.
- **FR-8.3** `draw_text_scrolling(canvas, s, fps)` helper for scrolling marquees.

### FR-9 — CLI (for testing and debugging)
- **FR-9.1** `ledmatrix list` — list connected devices.
- **FR-9.2** `ledmatrix info` — show device info and firmware version.
- **FR-9.3** `ledmatrix brightness <0-255>` — set brightness.
- **FR-9.4** `ledmatrix pixel <x> <y>` — light up a specific pixel (CLI wrapper for FR-3.2).
- **FR-9.5** `ledmatrix rect <x> <y> <w> <h>` — light up a specific area (CLI wrapper for FR-3.3).
- **FR-9.6** `ledmatrix image <path> [--dither bayer4x4]` — display an image.
- **FR-9.7** `ledmatrix text "hello" [--font 5x7]` — display text.
- **FR-9.8** `ledmatrix clear` — clear the display.
- **FR-9.9** `ledmatrix raw <opcode> <hex-payload>` — send a raw command.

### FR-10 — Hot-plug & reliability
- **FR-10.1** Reconnect-on-disconnect with exponential backoff (configurable max retries).
- **FR-10.2** Watchdog: if no successful frame send within N seconds, raise `DeviceStalled`.

### FR-11 — Cross-platform packaging
- **FR-11.1** Publish wheels for: `cp39–cp313`, `manylinux_x86_64/aarch64`, `win_amd64`, `win_arm64`.
- **FR-11.2** Bundle `hidapi` shared library inside the wheel (no system install required).
- **FR-11.3** Ship udev rules for Framework devices on Linux via an optional `ledmatrix[udev]` install script.

---

## 7. Non-Functional Requirements

### NFR-1 Performance
- **NFR-1.1** Frame send latency (host `set_leds()` call → device ACK) < 5 ms p99.
- **NFR-1.2** CPU usage at 60 FPS streaming on the 39×9 matrix < 1% on a modern x86_64 laptop.
- **NFR-1.3** No GIL-held I/O for > 1 ms per frame (release GIL during HID write/read).

### NFR-2 Reliability
- **NFR-2.1** Library must not crash the interpreter on device disconnect or malformed HID response.
- **NFR-2.2** All public API calls raise typed exceptions (`DeviceError`, `ProtocolError`, `TransportError`).
- **NFR-2.3** Long-running loops (24+ hours) must not leak file descriptors or memory.

### NFR-3 Portability
- **NFR-3.1** No use of `os.fork`, `os.pipe`, `select` on Windows-incompatible paths.
- **NFR-3.2** No reliance on `/dev/hidraw*` paths in public API.
- **NFR-3.3** Tested on: Ubuntu 22.04/24.04, Windows 10/11, macOS 13/14 (best-effort).

### NFR-4 Compatibility
- **NFR-4.1** Python 3.9, 3.10, 3.11, 3.12, 3.13.
- **NFR-4.2** Pillow ≥ 9.0 optional (required for image features).
- **NFR-4.3** NumPy ≥ 1.21 optional (required for array features).

---

## 8. Architecture

### 8.1 Layered overview

```
┌──────────────────────────────────────────────────────────────┐
│                      CLI (ledmatrix)                          │
├──────────────────────────────────────────────────────────────┤
│         Image Pipeline  │  Font / Text Rendering             │  ← High-level
├──────────────────────────────────────────────────────────────┤
│ Canvas  │  Pixel / Rect / Line Primitives  │  Dither         │  ← Drawing Core
├──────────────────────────────────────────────────────────────┤
│                Device (high-level, FW16 specific)             │  ← Device API
├──────────────────────────────────────────────────────────────┤
│                Protocol (typed commands)                      │  ← Command API
├──────────────────────────────────────────────────────────────┤
│              Transport (HID: hidapi / mock / raw)             │  ← Transport
├──────────────────────────────────────────────────────────────┤
│         OS HID stack (hidraw / hid.dll / IOHIDManager)        │
└──────────────────────────────────────────────────────────────┘
```

### 8.2 Module map

```
ledmatrix/
├── __init__.py              # public re-exports
├── transport/
│   ├── __init__.py
│   base.py                  # Transport ABC
│   hidapi.py                # hidapi/ctypes backend
│   hid.py                   # `hid` PyPI backend
│   mock.py                  # in-memory mock for tests
├── protocol/
│   ├── __init__.py
│   types.py                 # enums, dataclasses for commands
│   framework16.py           # Framework 16 LED Matrix command set (hardcoded)
├── device.py                # Device class — the main user-facing handle
├── canvas.py                # Canvas class (pixel/rect/line drawing primitives)
├── font/
│   ├── __init__.py
│   bdf.py                   # BDF parser
│   font.py                  # Font class
│   data/
│   │   ├── tom-thumb.bdf
│   │   ├── 5x7.bdf
│   │   └── 3x5.bdf
├── shapes.py                # line, rect, circle, triangle (optional helpers)
├── dither.py                # threshold, bayer, floyd-steinberg
├── image.py                 # ImagePipeline, from_pil, from_array
├── scheduler.py             # V-blank frame scheduler
├── hotplug.py               # device-added/removed callbacks
├── exceptions.py            # typed exception hierarchy
├── logging.py               # structured logging helpers
└── cli/
    ├── __init__.py
    └── main.py              # click-based CLI
```

### 8.3 Concurrency model
- **Default path (sync):** `Device` performs blocking HID I/O in the calling thread. Suitable for CLIs and simple scripts.
- **Async path:** `AsyncDevice` wraps each blocking call in `asyncio.to_thread`. Suitable for integrators running matrix output alongside other I/O.

---

## 9. API Specification (Selected Highlights)

### 9.1 Device discovery and open

```python
from ledmatrix import list_devices, open_device, Device

for info in list_devices():
    print(info)  # DeviceInfo(vid=0x32ac, pid=0x0001, serial='...')

dev = open_device(serial="FW1234")          # by serial
dev = open_device(index=0)                   # by index

# Context-managed lifecycle:
with open_device() as dev:
    dev.set_brightness(128)
    dev.clear()
```

### 9.2 Granular Drawing Primitives (The Core)

```python
from ledmatrix import Canvas, open_device

with open_device() as dev:
    c = dev.get_canvas()  # Returns a 39x9 Canvas
    
    # Light up specific individual pixels
    c.set_pixel(0, 0, 1)
    c.set_pixel(38, 8, 1)
    
    # Light up specific rectangular areas
    c.fill_rect(5, 2, 10, 3, 1)  # x, y, width, height, state
    
    # Clear a specific area
    c.clear_rect(5, 2, 5, 3)
    
    # Draw a line
    c.draw_line(0, 0, 38, 8, 1)
    
    # Invert a specific area
    c.invert_rect(0, 0, 39, 9)
    
    # Stream it to the device
    c.show()
```

### 9.3 Image pipeline (For host-rendered graphics)

```python
from ledmatrix import ImagePipeline, open_device
from PIL import Image

pipe = ImagePipeline(target=(39, 9), mode="mono", dither="bayer4x4")
img = Image.open("photo.jpg").convert("RGB")
frame = pipe.process(img)

with open_device() as dev:
    dev.show_frame(frame)
```

### 9.4 Text rendering

```python
from ledmatrix import Font, open_device

font = Font.load("5x7")

with open_device() as dev:
    c = dev.get_canvas()
    c.clear()
    font.draw_text(c, x=0, y=1, text="HELLO")
    c.show()
```

### 9.5 Low-level / vendor commands

```python
with open_device() as dev:
    dev.raw_command(opcode=0x42, payload=b"\x01\x02\x03")
    info = dev.get_device_info()
    dev.panic()           # built-in panic pattern
    dev.bootloader_reset()  # jump to bootloader
```

---

## 10. Cross-Platform Considerations

### 10.1 Linux
- HID access via `/dev/hidraw*` requires the user to be in the `plugdev` group, OR a udev rule.
- Ship udev rule file `49-framework-ledmatrix.rules`:
  ```
  SUBSYSTEM=="hidraw", ATTRS{idVendor}=="32ac", ATTRS{idProduct}=="0001", MODE="0666"
  ```
- Installable via `sudo ledmatrix system install-udev`.

### 10.2 Windows
- HID access via `hid.dll` — works for vendor-usage-page devices without driver install.
- Windows may buffer HID reports aggressively; we explicitly flush by reading the response before sending the next frame.

### 10.3 macOS (best-effort)
- IOHIDManager backend in `hidapi`. No driver install required.

---

## 11. Performance & Reliability Strategy

### 11.1 Hot-path optimization
- Pixel packing (`mono_1bpp_packed`) implemented in pure Python first; profiled.
- A 39×9 mono frame is 44 bytes → fits in a single 64-byte HID report, minimizing chunking overhead.
- HID writes release the GIL via `Py_BEGIN_ALLOW_THREADS` in the ctypes wrapper.

### 11.2 Reliability
- Every public API call is wrapped in a `try/except` that translates low-level `OSError`/`IOError` into typed `TransportError`/`DeviceDisconnected`.
- `Device` is a context manager; `__exit__` guarantees transport close even on exception.

### 11.3 Backpressure
- The frame scheduler refuses to queue more than 2 frames ahead by default. If the user calls `show()` faster than the device can drain, the call blocks—ensuring developers do not accidentally overflow the HID buffer and drop frames.

---

## 12. Testing Strategy

### 12.1 Unit tests
- Protocol layer: encode/decode every command; golden-byte comparison.
- Canvas: pixel manipulation, `fill_rect`, `clear_rect`, `invert_rect` boundary testing.
- Dither: known input → known output for each algorithm.
- BDF parser: parse three reference BDFs, assert glyph tables.

### 12.2 Integration tests
- `MockTransport` records all writes; assertions on command sequencing.
- Hot-plug simulation: inject disconnect mid-stream, assert graceful recovery.
- Frame scheduler: simulate 1 kHz `show()` calls; assert no HID queue overflow.

### 12.3 Hardware-in-loop (HIL) tests
- CI matrix includes an optional self-hosted runner with a Framework 16 LED Matrix attached.
- HIL test suite: brightness sweep, pattern set, 1000-frame streaming test, hot-plug, sleep/wake.

---

## 13. Packaging & Distribution

### 13.1 PyPI
- Package name: `ledmatrix`
- Optional extras:
  - `ledmatrix[image]` — pulls Pillow.
  - `ledmatrix[array]` — pulls NumPy.
  - `ledmatrix[udev]` — triggers Linux udev install hint.

### 13.2 Wheels
- Built via `cibuildwheel` in CI.
- Bundle `hidapi` shared library inside the wheel via auditwheel (Linux) and delvewheel (Windows).

---

## 14. Development Roadmap

### Milestone 0 — Pre-flight (Week 0)
- Repo scaffolding: `pyproject.toml`, `ruff`, `black`, `mypy --strict`, `pytest`.
- CI matrix up.

### Milestone 1 — Transport & Protocol (Weeks 1–2)
- `Transport` ABC, `hidapi` ctypes backend, `MockTransport`.
- `DeviceInfo`, `list_devices`, `open_device`.
- `protocol.framework16` — all typed commands.
- Deliverable: `python -c "from ledmatrix import list_devices; print(list_devices())"` works on Linux and Windows.

### Milestone 2 — Canvas & Drawing Primitives (Weeks 3–4)
- `Canvas` with `set_pixel`, `fill_rect`, `clear_rect`, `invert_rect`, `draw_line`.
- `set_leds` and `schedule_frame` v-blank-locked scheduling.
- Deliverable: Python script can light up specific pixels and stream a bouncing box at 60 FPS with < 1% CPU.

### Milestone 3 — Text & Image Pipeline (Weeks 5–6)
- BDF parser + bundled fonts + `draw_text`.
- `dither` (threshold, bayer, floyd_steinberg).
- `ImagePipeline`, `Canvas.from_pil`, `Canvas.from_array`.
- Deliverable: CLI commands `ledmatrix image photo.jpg` and `ledmatrix text "HELLO"` work flawlessly.

### Milestone 4 — CLI Polish & Async (Weeks 7–8)
- Full CLI surface (FR-9).
- `AsyncDevice` implementation.
- udev-rule installer.
- Deliverable: 1.0.0 release on PyPI.

---

## 15. Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `hidapi` wheels missing for some Python/OS combo | Medium | High | Bundle shared lib in wheel; ship ctypes fallback that loads system `hidapi`. |
| Frame pacing jitter on Windows due to `hid.dll` buffering | Medium | Medium | Use feature-report ACK pattern; benchmark p99 on Windows CI runner. |
| Framework changes the protocol in a firmware update | Medium | Medium | Version the protocol via `get_device_info`; fail loudly on unknown firmware version. |
| GIL contention in async mode under heavy streaming | Low | Medium | Release GIL in `hidapi` writes; keep Python code out of the hot path. |

---

**End of PRD.**