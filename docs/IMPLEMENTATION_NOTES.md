# Implementation notes and validated scope

These notes describe the current implementation status for `ledmatrix` 0.1.0.
They are intentionally narrower than the original product requirements in
`docs/PRD_SOURCE.md`.

## Current scope

The implemented package is a Python SDK and CLI for the Framework 16 LED Matrix
Input Module. It includes:

- A source-layout Python package under `src/ledmatrix/`.
- Canvas drawing, geometry, frame packing, image/font helpers, dithering, and
  frame scheduling.
- Synchronous and asynchronous device APIs.
- Serial/mock transport support and protocol encoding.
- A `ledmatrix` console script for device diagnostics and simple drawing.
- Deterministic pytest coverage for the SDK layers that do not require physical
  hardware.

## Source-of-truth adjustment

The source PRD contains broader goals and some dimensions that do not match the
implemented package. The current SDK treats the Framework 16 LED Matrix Input
Module as a 9x34 canvas and preserves the transport packing used by the code and
tests. Do not update user-facing docs to claim unsupported orientations,
dimensions, or firmware behavior without confirming them against hardware.

## Deliberate design choices

- Public APIs use plain Python objects and small helpers instead of a large
  framework.
- Hardware access is isolated behind transport classes so tests and examples can
  run with a mock transport.
- Optional image dependencies are kept behind the `image` extra.
- Examples prefer deterministic behavior and accept explicit device paths for
  hardware runs.
- CLI diagnostics include raw packet inspection to help debug without sending
  frames to a device.

## Validation completed

The repository includes tests for:

- Canvas drawing, bounds handling, and frame conversion.
- Protocol packet construction.
- Device helper behavior with mock transports.
- Scheduler timing behavior.
- Font loading/rendering and dithering.
- CLI command behavior.

The deterministic test suite passes in the current virtualenv. Static analysis
is not clean yet: `mypy src` reports existing typing issues in the serial
transport module, and broader ruff cleanup is outside this documentation update.

## Hardware validation remaining

Before presenting the SDK as fully hardware-validated, run the hardware smoke
test against a real Framework 16 LED Matrix Input Module:

```bash
python examples/hardware_smoketest.py /dev/ttyACM0
```

Confirm:

1. Discovery finds the module on supported platforms.
2. A single pixel, rectangle, and full clear command display correctly.
3. Brightness and power mode commands match firmware behavior.
4. Orientation matches the physical module installation.
5. Linux serial permissions or udev setup are documented for the target host.
