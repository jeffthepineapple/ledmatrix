"""Small, strict-enough BDF bitmap font parser."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class Glyph:
    codepoint: int
    name: str
    width: int
    height: int
    x_offset: int
    y_offset: int
    advance: int
    rows: tuple[int, ...]

    def pixel(self, x: int, y: int) -> bool:
        if not 0 <= x < self.width or not 0 <= y < self.height:
            return False
        return bool(self.rows[y] & (1 << (self.width - 1 - x)))


@dataclass(frozen=True)
class BdfFont:
    name: str
    ascent: int
    descent: int
    glyphs: Dict[int, Glyph]
    default_advance: int


def _parse_ints(text: str, expected: int, context: str) -> list[int]:
    values = text.split()
    if len(values) != expected:
        raise ValueError("%s requires %d values" % (context, expected))
    try:
        return [int(value) for value in values]
    except ValueError as exc:
        raise ValueError("invalid integer in %s" % context) from exc


def parse_bdf(text: str) -> BdfFont:
    """Parse a bitmap BDF font file into glyphs.

    This parser purposely handles the portable common BDF subset used by bundled fonts;
    unsupported metadata is ignored rather than silently altering bitmap data.
    """
    lines = [line.rstrip("\n") for line in text.splitlines()]
    font_name = "unnamed"
    ascent = 0
    descent = 0
    glyphs: Dict[int, Glyph] = {}
    default_advance = 1
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("FONT "):
            font_name = line[5:].strip()
        elif line.startswith("FONT_ASCENT "):
            ascent = int(line.split(maxsplit=1)[1])
        elif line.startswith("FONT_DESCENT "):
            descent = int(line.split(maxsplit=1)[1])
        elif line.startswith("STARTCHAR "):
            name = line.split(maxsplit=1)[1].strip()
            codepoint: Optional[int] = None
            width = height = x_offset = y_offset = 0
            advance = 0
            rows: List[int] = []
            index += 1
            while index < len(lines) and lines[index] != "ENDCHAR":
                item = lines[index]
                if item.startswith("ENCODING "):
                    codepoint = int(item.split(maxsplit=1)[1])
                elif item.startswith("DWIDTH "):
                    advance = _parse_ints(item[7:], 2, "DWIDTH")[0]
                elif item.startswith("BBX "):
                    width, height, x_offset, y_offset = _parse_ints(item[4:], 4, "BBX")
                elif item == "BITMAP":
                    index += 1
                    while index < len(lines) and lines[index] != "ENDCHAR":
                        bitmap_line = lines[index].strip()
                        if bitmap_line:
                            rows.append(int(bitmap_line, 16))
                        index += 1
                    break
                index += 1
            if codepoint is not None and codepoint >= 0:
                if height != len(rows):
                    raise ValueError("glyph %s has BBX height %d but %d bitmap rows" % (name, height, len(rows)))
                # BDF bitmaps are padded on the right to a full byte. Shift down to visible width.
                padded = ((width + 7) // 8) * 8
                normalized = tuple(row >> (padded - width) for row in rows)
                glyphs[codepoint] = Glyph(
                    codepoint=codepoint,
                    name=name,
                    width=width,
                    height=height,
                    x_offset=x_offset,
                    y_offset=y_offset,
                    advance=advance or width,
                    rows=normalized,
                )
                default_advance = advance or default_advance
        index += 1
    return BdfFont(font_name, ascent, descent, glyphs, default_advance)


def load_bdf(path: Path) -> BdfFont:
    return parse_bdf(path.read_text(encoding="ascii"))
