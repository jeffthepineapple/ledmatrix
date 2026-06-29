# API summary

This document summarizes the public `ledmatrix` 0.1.0 API. The README is the
PyPI long description; this page is a compact reference for the current package
surface.

## Package exports

The top-level `ledmatrix` package exposes the main SDK entry points:

- `Canvas` for drawing and frame packing.
- `Device`, `AsyncDevice`, `open_device`, and `list_devices` for hardware
  access.
- `DeviceInfo` and `DeviceDetails` for discovered and connected device data.
- `DeviceWatcher` for hotplug-style polling.
- `FrameScheduler` for paced frame loops.
- `MatrixGeometry`, `PackingOrder`, and `FW16_LED_MATRIX` for layout and byte
  packing.
- `ImagePipeline`, `normalize_dither`, `dither`, `draw_circle`, and
  `draw_triangle` for rendering helpers.
- `DeviceNotFound`, `DeviceDisconnected`, and `ProtocolError` for common
  failure modes.

## Discovery and device control

Use `list_devices()` to inspect available modules and `open_device()` when the
first matching device is acceptable. Use `Device(path)` when an explicit serial
path is required.

```python
from ledmatrix import Canvas, list_devices, open_device

devices = list_devices(timeout=1.0)
with open_device(devices[0].path if devices else None) as device:
    device.set_brightness(50)
    device.show_frame(Canvas().clear().set_pixel(0, 0, 255))
```

`Device` supports frame display, brightness changes, power mode control,
animation commands, and device information queries. `AsyncDevice` mirrors the
hardware workflow for asyncio applications.

## Drawing

`Canvas` defaults to the Framework 16 LED Matrix Input Module geometry: 9x34
pixels. Coordinates are zero-based and grayscale values use `0..255`.

Core operations include:

- `clear()` and `fill(value)`.
- `set_pixel(x, y, value)` and `get_pixel(x, y)`.
- `fill_rect(x, y, width, height, value)` and `clear_rect(...)`.
- `invert_rect(x, y, width, height)`.
- `draw_line(x0, y0, x1, y1, value)`.
- `to_bytes()` for transport-ready frame payloads.

Shape helpers currently include `draw_circle(...)` and `draw_triangle(...)`.

Per-pixel brightness is represented by the canvas pixel value. For example,
`set_pixel(4, 17, 64)` sets a dim pixel and `set_pixel(4, 17, 255)` sets a
full-intensity pixel. `Device.set_brightness(...)` is a separate global device
setting and does not target one coordinate.

## Image, font, and dither helpers

Install the `image` extra for Pillow and NumPy backed workflows:

```bash
pip install "ledmatrix[image]"
```

`ImagePipeline(...).process(image)` prepares source images for the matrix.
`normalize_dither()` and `dither()` provide deterministic grayscale conversion
helpers. Bundled BDF fonts are available through `ledmatrix.font.Font.load(...)`,
including compact fonts such as `3x5` and `5x7`.

## Reliability and diagnostics

The SDK includes a mock transport so tests and examples can inspect encoded
messages without hardware. Use `FrameScheduler` for stable frame pacing instead
of ad hoc sleeps in animation loops.

The CLI installs as `ledmatrix` and includes:

```text
list, info, brightness, pixel, rect, clear, image, text,
orientation-test, raw, system
```

Use `ledmatrix raw ...` for packet inspection without sending to hardware.
The `pixel` CLI command currently targets coordinates only; use the Python
`Canvas` API for explicit per-pixel grayscale values.
Hardware validation remains separate from deterministic unit tests.
