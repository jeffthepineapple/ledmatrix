# Repository Guidelines

## Project Structure & Module Organization

This is a Python SDK laid out with source under `src/ledmatrix/`. Core device APIs live in `device.py`, `async_device.py`, and `canvas.py`; drawing helpers are in `shapes.py`, `geometry.py`, `image.py`, and `dither.py`; transport, protocol, CLI, font, and data assets are in their matching subpackages. Tests are in `tests/` and use `test_*.py` names. Examples are in `examples/`, and longer reference material is in `docs/`.

## Build, Test, and Development Commands

Install for local development:

```bash
python -m pip install -e ".[dev]"
```

Run the test suite:

```bash
python -m pytest
```

Run linting and type checks:

```bash
ruff check src tests examples
mypy src
```

Run examples from the repository root, for example:

```bash
python examples/mock_demo.py
```

## Coding Style & Naming Conventions

Target Python 3.9 or newer. Use four-space indentation, type hints for public APIs, and descriptive snake_case names for modules, functions, variables, and test files. Keep classes in CapWords. Follow the existing compact module style and prefer small helpers near the code that uses them. Ruff is configured in `pyproject.toml`; run it before submitting changes.

## Testing Guidelines

Tests use pytest. Add or update focused tests in `tests/` when changing SDK behavior, protocol encoding, CLI output, scheduling, fonts, or drawing primitives. Name files `test_<area>.py` and test functions `test_<expected_behavior>()`. Prefer deterministic tests that do not require LED hardware; hardware-in-loop checks should be documented separately.

## Commit & Pull Request Guidelines

This checkout does not expose usable git history, so use clear imperative commit subjects such as `Add canvas clipping tests` or `Fix serial reconnect handling`. Keep commits scoped to one logical change. Pull requests should include a short summary, test results, linked issues when relevant, and screenshots or terminal output for visible CLI/example changes.

## Security & Configuration Tips

Do not commit local device paths, secrets, or machine-specific serial settings. Keep udev rules and packaged data under `src/ledmatrix/data/`, and document any required host setup in `docs/` or `README.md`.
