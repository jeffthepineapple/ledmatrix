"""No-hardware demo: render patterns to the terminal via MockTransport.

Run:  .venv/bin/python examples/mock_demo.py
Shows what the SDK would draw without needing a real panel.
"""
import _bootstrap  # noqa: F401  (selects installed package or in-repo src/)
from ledmatrix import Canvas, open_device
from ledmatrix.transport import MockTransport


def preview(name, canvas):
    print(f"\n{name}:")
    print("\n".join(canvas.to_rows(on="#", off=".")))


with open_device(transport=MockTransport()) as device:
    border = Canvas()
    border.draw_rect(0, 0, border.width, border.height, True)
    preview("border", border)

    cross = Canvas()
    cross.draw_line(0, 0, 8, 33, True)
    cross.draw_line(8, 0, 0, 33, True)
    preview("X", cross)

    device.set_leds(border)  # exercises the real column-staging encode path
    print(f"\nframe -> {len(device.transport.writes)} serial writes "
          f"(9 columns + 1 commit)")
