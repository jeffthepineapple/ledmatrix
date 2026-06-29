# ledmatrix

`ledmatrix` is a Python SDK and command-line tool for the Framework 16 LED
Matrix Input Module. It provides a small drawing API, device discovery, frame
transport, image/text helpers, frame pacing, and diagnostics that can run with
or without hardware attached.

Current package status: `0.1.0`. The SDK has deterministic tests for protocol
encoding, canvas operations, fonts, dithering, scheduler behavior, device
helpers, and CLI behavior. Hardware-in-loop validation is still tracked
separately because it requires a physical Framework 16 LED Matrix Input Module.

## Features

- Canvas drawing for pixels, rectangles, lines, fills, inversion, and packed
  frame output.
- Device discovery and synchronous or asynchronous device control.
- CLI commands for listing devices, showing pixels/rectangles/text/images,
  brightness, raw packet inspection, and diagnostics.
- Optional image and array support through Pillow and NumPy.
- Font rendering with bundled bitmap fonts.
- Mock transport for examples, dry runs, and tests without LED hardware.
- Geometry helpers for the Framework 16 LED Matrix Input Module layout.

## Install

Install the base package:

```bash
pip install ledmatrix
```

Install optional image and NumPy helpers:

```bash
pip install "ledmatrix[image]"
```

Install development tools from a checkout:

```bash
python -m pip install -e ".[dev,image]"
```

Linux users may need udev rules before a non-root process can access the input
module. A packaged rule is included under `src/ledmatrix/data/`.

## Quick Start

Create a frame in memory:

```python
from ledmatrix import Canvas

frame = Canvas()
frame.clear()
frame.set_pixel(0, 0, 255)
frame.fill_rect(2, 4, 5, 3, 180)
frame.draw_line(0, 33, 8, 0, 255)
```

Send a frame to the first discovered device:

```python
from ledmatrix import Canvas, open_device

canvas = Canvas().clear()
canvas.fill_rect(1, 8, 7, 4, 200)

with open_device() as device:
    device.show_frame(canvas)
```

Use explicit discovery if you want to choose a device:

```python
from ledmatrix import list_devices, open_device

devices = list_devices()
if not devices:
    raise SystemExit("No LED Matrix Input Module found")

with open_device(devices[0].path) as device:
    print(device.get_device_info())
```

## Drawing And Geometry

The default geometry is the Framework 16 LED Matrix Input Module: 9 columns by
34 rows. Coordinates are zero-based with `(0, 0)` at the top-left of the canvas.
Pixel values are grayscale integers from `0` to `255`.

```python
from ledmatrix import Canvas

canvas = Canvas()
canvas.clear()
canvas.set_pixel(8, 33, 255)
canvas.fill_rect(x=1, y=8, width=7, height=4, value=160)
canvas.invert_rect(x=2, y=9, width=2, height=2)

payload = canvas.to_bytes()
```

Additional helpers include `draw_circle`, `draw_triangle`, `ImagePipeline`,
`normalize_dither`, and `dither`.

Per-pixel intensity is controlled by the pixel value in the frame:

```python
canvas = Canvas().clear()
canvas.set_pixel(4, 17, 64)   # dim pixel
canvas.set_pixel(5, 17, 255)  # full-intensity pixel
```

Device brightness is separate and applies globally to the module:

```python
from ledmatrix import open_device

with open_device() as device:
    device.set_brightness(50)
    device.show_frame(canvas)
```

The CLI `pixel` command currently turns a coordinate on; use the Python API when
you need a specific per-pixel grayscale value.

## Text And Images

Text rendering uses bundled bitmap fonts:

```python
from ledmatrix import Canvas
from ledmatrix.font import Font

canvas = Canvas().clear()
font = Font.load("3x5")
font.draw_text(canvas, 0, 0, "Hi")
```

Image helpers are available when Pillow is installed:

```python
from PIL import Image
from ledmatrix import ImagePipeline

image = Image.open("icon.png")
canvas = ImagePipeline(dither="bayer4x4").process(image)
```

## Device API

The synchronous API is centered on `Device`:

```python
from ledmatrix import Canvas, Device

with Device("/dev/ttyACM0") as device:
    device.set_brightness(50)
    device.show_frame(Canvas().clear().set_pixel(4, 17, 255))
```

The package also exports `AsyncDevice` for asyncio applications,
`FrameScheduler` for frame pacing, and exceptions such as
`DeviceNotFound`, `DeviceDisconnected`, and `ProtocolError`.

## CLI

The package installs a `ledmatrix` command:

```bash
ledmatrix list
ledmatrix info
ledmatrix brightness 50
ledmatrix pixel 4 17
ledmatrix rect 1 8 7 4
ledmatrix clear
ledmatrix text "Hi"
ledmatrix image icon.png
```

Diagnostics and hardware-free inspection:

```bash
ledmatrix pixel 4 17 --dry-run
ledmatrix rect 1 8 7 4 --dry-run
ledmatrix raw 0x32 00 --dry-run
ledmatrix orientation-test
ledmatrix system
```

Use `ledmatrix --help` and `ledmatrix <command> --help` for command-specific
arguments such as device paths, orientation, brightness, and dry-run options.

## Current Validation Status

Validated in the repository:

- Canvas bounds handling, drawing primitives, and packed frame conversion.
- Protocol message encoding for SDK commands.
- Device helper behavior with mock transports.
- Font loading/rendering and image dithering helpers.
- CLI command behavior in deterministic tests.

Known validation follow-up:

- Static analysis cleanup remains for the current checkout. The test suite
  passes, but the virtualenv `mypy src` run reports existing serial-transport
  typing issues.

Still requiring real hardware validation:

- End-to-end frame display on a physical Framework 16 LED Matrix Input Module.
- Brightness/power behavior against firmware.
- Orientation confirmation on the installed module.
- Host setup notes for platform-specific serial permissions.

See `BUILD_REPORT.md` and `docs/IMPLEMENTATION_NOTES.md` for the current
validation notes.

## Development

From a checkout:

```bash
python -m pip install -e ".[dev,image]"
python -m pytest
ruff check src tests examples
mypy src
```

Examples are in `examples/`:

```bash
python examples/mock_demo.py
python examples/snake_game.py --dry-run
python examples/snake_game.py --port /dev/ttyACM0
python examples/draw_primitives.py /dev/ttyACM0
python examples/text_marquee.py /dev/ttyACM0
python examples/hardware_smoketest.py /dev/ttyACM0
```

More detailed API and PyPI-facing documentation is available in `docs/API.md`
and `docs/PYPI_GUIDE.md`.
