"""Text rendering on a monochrome :class:`ledmatrix.Canvas`."""
from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Iterator, Optional

from ..canvas import Canvas
from .bdf import BdfFont, Glyph, load_bdf


_FONT_FILES = {
    "tom-thumb": "tom-thumb.bdf",
    "tom_thumb": "tom-thumb.bdf",
    "4x6": "tom-thumb.bdf",
    "5x7": "5x7.bdf",
    "3x5": "3x5.bdf",
}


class Font:
    """Bitmap BDF font loaded from a bundled resource or a custom path."""

    def __init__(self, bdf: BdfFont) -> None:
        self._bdf = bdf

    @property
    def name(self) -> str:
        return self._bdf.name

    @property
    def height(self) -> int:
        return self._bdf.ascent + self._bdf.descent

    def glyph(self, char: str) -> Optional[Glyph]:
        if len(char) != 1:
            raise ValueError("glyph() expects one character")
        return self._bdf.glyphs.get(ord(char)) or self._bdf.glyphs.get(ord("?"))

    def text_width(self, text: str, spacing: int = 1) -> int:
        if spacing < 0:
            raise ValueError("spacing must be non-negative")
        if not text:
            return 0
        width = 0
        for char in text:
            glyph = self.glyph(char)
            width += glyph.advance if glyph is not None else self._bdf.default_advance
        return width + spacing * (len(text) - 1)

    def draw_text(
        self,
        canvas: Canvas,
        x: int,
        y: int,
        text: str,
        state: bool = True,
        spacing: int = 1,
    ) -> Canvas:
        cursor = x
        for char in text:
            glyph = self.glyph(char)
            if glyph is None:
                cursor += self._bdf.default_advance + spacing
                continue
            for gy in range(glyph.height):
                for gx in range(glyph.width):
                    if glyph.pixel(gx, gy):
                        px, py = cursor + gx + glyph.x_offset, y + gy
                        if 0 <= px < canvas.width and 0 <= py < canvas.height:
                            canvas.set_pixel(px, py, state)
            cursor += glyph.advance + spacing
        return canvas

    @classmethod
    def load(cls, name_or_path: str) -> "Font":
        normalized = name_or_path.lower().replace(" ", "-")
        if normalized in _FONT_FILES:
            resource = resources.files("ledmatrix.font.data").joinpath(_FONT_FILES[normalized])
            with resources.as_file(resource) as path:
                return cls(load_bdf(path))
        path = Path(name_or_path)
        if not path.is_file():
            raise FileNotFoundError("font %r not found; bundled fonts: %s" % (name_or_path, sorted(_FONT_FILES)))
        return cls(load_bdf(path))


def draw_text_scrolling(
    canvas: Canvas,
    text: str,
    font: Optional[Font] = None,
    fps: float = 15.0,
    y: int = 0,
    spacing: int = 1,
    gap: int = 3,
) -> Iterator[Canvas]:
    """Yield marquee frames; callers choose their timing and device lifecycle.

    ``fps`` is validated and attached to the iterator as design intent; frame emission itself is
    pull-based so it does not block an event loop or own a device connection.
    """
    if fps <= 0:
        raise ValueError("fps must be greater than zero")
    if gap < 0:
        raise ValueError("gap must be non-negative")
    active_font = font or Font.load("5x7")
    width = active_font.text_width(text, spacing=spacing)
    for offset in range(canvas.width, -width - gap, -1):
        frame = canvas.copy()
        active_font.draw_text(frame, offset, y, text, spacing=spacing)
        yield frame
