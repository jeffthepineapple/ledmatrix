"""Optional immediate-mode shape helpers."""
from __future__ import annotations

from typing import Any

from .canvas import Canvas


def draw_circle(canvas: Canvas, cx: int, cy: int, radius: int, state: Any = True) -> Canvas:
    if radius < 0:
        raise ValueError("radius must be non-negative")
    x, y = radius, 0
    error = 1 - radius
    while x >= y:
        for px, py in (
            (cx + x, cy + y), (cx + y, cy + x), (cx - y, cy + x), (cx - x, cy + y),
            (cx - x, cy - y), (cx - y, cy - x), (cx + y, cy - x), (cx + x, cy - y),
        ):
            if 0 <= px < canvas.width and 0 <= py < canvas.height:
                canvas.set_pixel(px, py, state)
        y += 1
        if error < 0:
            error += 2 * y + 1
        else:
            x -= 1
            error += 2 * (y - x) + 1
    return canvas


def draw_triangle(
    canvas: Canvas, x0: int, y0: int, x1: int, y1: int, x2: int, y2: int, state: Any = True
) -> Canvas:
    canvas.draw_line(x0, y0, x1, y1, state)
    canvas.draw_line(x1, y1, x2, y2, state)
    canvas.draw_line(x2, y2, x0, y0, state)
    return canvas
