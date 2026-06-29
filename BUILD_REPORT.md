# Build report - ledmatrix 0.1.0

This report captures the current repository status for documentation and
release-readiness purposes. It is not a substitute for hardware validation.

## Validation completed

- Package metadata identifies the project as `ledmatrix` version `0.1.0`.
- PyPI long description is sourced from `README.md`.
- Console script entry point is `ledmatrix = ledmatrix.cli.main:main`.
- Source package includes SDK modules for canvas drawing, device access,
  asynchronous device access, geometry, hotplug polling, image helpers,
  dithering, logging, scheduling, shapes, protocol, transport, CLI, fonts, and
  packaged data.
- Deterministic tests exist for CLI behavior, canvas operations, device helpers,
  dithering, fonts, protocol encoding, and scheduler behavior.
- `.venv/bin/python -m pytest` passes with 30 tests in the current environment.

## Validation follow-up

- `.venv/bin/python -m mypy src` reports existing typing issues in
  `src/ledmatrix/transport/serial.py`.
- `.venv/bin/python -m ruff check src tests examples` reports existing source
  lint issues. Markdown-only ruff checks pass.

## Important scope correction

The implemented SDK documents the Framework 16 LED Matrix Input Module as a
9x34 canvas. Older source requirements in `docs/PRD_SOURCE.md` are broader than
the current package and should not be treated as shipped behavior.

## Hardware validation remaining

The following checks still require real hardware:

1. Device discovery on target platforms.
2. Pixel, rectangle, image, text, and clear output on the physical module.
3. Brightness, power mode, and firmware information behavior.
4. Orientation confirmation on the installed module.
5. Linux udev/permission setup on a clean host.

Suggested hardware smoke test:

```bash
python examples/hardware_smoketest.py /dev/ttyACM0
```
