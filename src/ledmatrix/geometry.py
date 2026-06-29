"""Matrix geometry and packing conventions."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PackingOrder(str, Enum):
    """Packing order used by an on-wire monochrome frame."""

    COLUMN_MAJOR_LSB = "column-major-lsb"
    ROW_MAJOR_LSB = "row-major-lsb"


@dataclass(frozen=True)
class MatrixGeometry:
    """Immutable description of a monochrome LED matrix."""

    width: int
    height: int
    packing: PackingOrder = PackingOrder.COLUMN_MAJOR_LSB

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be positive")

    @property
    def pixels(self) -> int:
        return self.width * self.height

    @property
    def frame_bytes(self) -> int:
        return (self.pixels + 7) // 8

    def validate_point(self, x: int, y: int) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise ValueError(
                "pixel (%d, %d) is outside a %dx%d matrix" % (x, y, self.width, self.height)
            )

    def bit_index(self, x: int, y: int) -> int:
        self.validate_point(x, y)
        if self.packing is PackingOrder.COLUMN_MAJOR_LSB:
            return x * self.height + y
        return y * self.width + x


# Current upstream documentation describes the Framework 16 LED Matrix as 9 columns x 34 rows.
FW16_LED_MATRIX = MatrixGeometry(width=9, height=34, packing=PackingOrder.COLUMN_MAJOR_LSB)
