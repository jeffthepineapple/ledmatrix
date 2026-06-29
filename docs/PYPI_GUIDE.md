# PyPI guide

This page is the expanded package guide behind the shorter PyPI README. It is
intended for users evaluating `ledmatrix` from PyPI or installing it into a
project.

## What the package provides

`ledmatrix` targets the Framework 16 LED Matrix Input Module. It provides three
main workflows:

- Draw frames in memory with `Canvas`.
- Send frames and control commands through `Device` or `AsyncDevice`.
- Use the `ledmatrix` CLI for quick diagnostics and simple drawing commands.

The default matrix geometry is 9x34 pixels. Pixel values are grayscale values in
the range `0..255`.

Per-pixel intensity and global brightness are different controls:

- Use `Canvas.set_pixel(x, y, value)` for one pixel's grayscale value.
- Use `Device.set_brightness(value)` for global module brightness.
- Use the Python API rather than the CLI `pixel` command when one coordinate
  needs a specific grayscale value.

## Installation profiles

Base install:

```bash
pip install ledmatrix
```

Image/font workflow with Pillow and NumPy helpers:

```bash
pip install "ledmatrix[image]"
```

Editable development checkout:

```bash
python -m pip install -e ".[dev,image]"
```

The base dependency is `pyserial`. Pillow and NumPy are optional so simple
device and canvas workflows can stay lightweight.

## Hardware-free workflow

Start by building frames and inspecting CLI output without a physical module:

```python
from ledmatrix import Canvas

canvas = Canvas().clear()
canvas.set_pixel(0, 0, 255)
canvas.set_pixel(1, 0, 64)
canvas.fill_rect(1, 8, 7, 4, 180)
print(canvas.to_bytes().hex())
```

The CLI also supports raw packet inspection:

```bash
ledmatrix pixel 0 0 --dry-run
ledmatrix rect 1 8 7 4 --dry-run
ledmatrix raw 0x32 00 --dry-run
```

Use the mock examples when you want a repeatable demo:

```bash
python examples/mock_demo.py
```

## Hardware workflow

When hardware is attached, list and inspect devices:

```bash
ledmatrix list
ledmatrix info
```

Draw basic output:

```bash
ledmatrix clear
ledmatrix pixel 4 17
ledmatrix rect 1 8 7 4
ledmatrix text "Hi"
```

Run the hardware smoke test from a checkout:

```bash
python examples/hardware_smoketest.py /dev/ttyACM0
```

If discovery fails on Linux, check serial permissions and install the packaged
udev rule from `src/ledmatrix/data/` as appropriate for your system.

## API patterns

For short scripts, use `open_device()`:

```python
from ledmatrix import Canvas, open_device

frame = Canvas().clear().fill_rect(2, 10, 5, 5, 200)

with open_device() as device:
    device.show_frame(frame)
```

For explicit device selection, use discovery:

```python
from ledmatrix import list_devices, Device

for info in list_devices():
    print(info.path, info.serial)

with Device("/dev/ttyACM0") as device:
    print(device.get_device_info())
```

For animation loops, use `FrameScheduler` to avoid unbounded sleep drift:

```python
from ledmatrix import Canvas, FrameScheduler, open_device

with open_device() as device:
    scheduler = FrameScheduler(fps=30)
    for x in range(9):
        frame = Canvas().clear().set_pixel(x, 17, 255)
        scheduler.submit(lambda frame=frame: device.show_frame(frame))
```

For asyncio applications, use `AsyncDevice` instead of wrapping synchronous I/O
inside application tasks.

## Images and fonts

Install the `image` extra before using Pillow-backed helpers:

```bash
pip install "ledmatrix[image]"
```

Example image workflow:

```python
from PIL import Image
from ledmatrix import ImagePipeline

source = Image.open("icon.png")
frame = ImagePipeline(dither="bayer4x4").process(source)
```

Example text workflow:

```python
from ledmatrix import Canvas
from ledmatrix.font import Font

frame = Canvas().clear()
font = Font.load("3x5")
font.draw_text(frame, 0, 0, "OK")
```

## Current limitations

- Full hardware validation is not complete in this checkout.
- Firmware-specific behavior should be confirmed on a real module before it is
  documented as guaranteed.
- Host setup can vary by OS and serial permissions.
- The source PRD is broader than the implemented SDK; use README, API docs, and
  implementation notes as the current user-facing source of truth.

## Related docs

- `README.md`: PyPI long description and quick start.
- `docs/API.md`: compact public API summary.
- `docs/IMPLEMENTATION_NOTES.md`: current implementation and validation notes.
- `BUILD_REPORT.md`: validation snapshot for the current package version.
