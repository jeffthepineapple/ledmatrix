# Contributing

1. Create a virtual environment.
2. Install `python -m pip install -e '.[dev,all]'`.
3. Run `pytest` before submitting a change.
4. Add a unit test for every protocol, packing, or drawing behavior change.
5. Do not add undocumented commands as stable public APIs. Gate experimental firmware behavior behind explicit capability checks.

Hardware-in-loop testing is encouraged, but source-level unit tests must remain deterministic with `MockTransport`.
