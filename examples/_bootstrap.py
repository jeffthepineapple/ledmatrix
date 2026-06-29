"""Import shim for examples: use installed ``ledmatrix`` if present, else in-repo ``src/``.

Each example does ``import _bootstrap`` before importing ``ledmatrix`` so they run with a
plain ``python examples/foo.py`` even when the package isn't pip-installed.
"""
import pathlib
import sys

try:
    import ledmatrix  # noqa: F401
except ModuleNotFoundError:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))
