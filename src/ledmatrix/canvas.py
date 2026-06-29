"""Packed 1-bit drawing surface for the Framework LED Matrix."""
from __future__ import annotations

from typing import Any, Iterable, Optional, Sequence, TYPE_CHECKING

from .geometry import FW16_LED_MATRIX, MatrixGeometry

if TYPE_CHECKING:
    from .device import Device


class Canvas:
    """A mutable 1-bit canvas backed by a packed :class:`bytearray`.

    Coordinates are zero-based: ``x`` increases across the short edge and ``y`` down the
    long edge. The default 9x34 geometry and column-major LSB packing match the current
    upstream Framework protocol's DrawBW payload.
    """

    def __init__(self, geometry: MatrixGeometry = FW16_LED_MATRIX, data: Optional[bytes] = None) -> None:
        self.geometry = geometry
        if data is None:
            self._data = bytearray(geometry.frame_bytes)
        else:
            if len(data) != geometry.frame_bytes:
                raise ValueError(
                    "expected %d packed bytes, got %d" % (geometry.frame_bytes, len(data))
                )
            self._data = bytearray(data)

    @property
    def width(self) -> int:
        return self.geometry.width

    @property
    def height(self) -> int:
        return self.geometry.height

    @property
    def buffer(self) -> bytearray:
        """The mutable packed framebuffer. Treat direct mutation as an advanced API."""
        return self._data

    def _address(self, x: int, y: int) -> tuple[int, int]:
        index = self.geometry.bit_index(x, y)
        return index // 8, index % 8

    def set_pixel(self, x: int, y: int, state: Any = True) -> "Canvas":
        byte_index, bit = self._address(x, y)
        mask = 1 << bit
        if bool(state):
            self._data[byte_index] |= mask
        else:
            self._data[byte_index] &= ~mask & 0xFF
        return self

    def get_pixel(self, x: int, y: int) -> bool:
        byte_index, bit = self._address(x, y)
        return bool(self._data[byte_index] & (1 << bit))

    def clear(self) -> "Canvas":
        self._data[:] = b"\x00" * len(self._data)
        return self

    def fill(self, state: Any = True) -> "Canvas":
        self._data[:] = (b"\xff" if bool(state) else b"\x00") * len(self._data)
        # The last byte may contain unused bits. Clear them so frames are deterministic.
        unused = len(self._data) * 8 - self.geometry.pixels
        if bool(state) and unused:
            self._data[-1] &= (1 << (8 - unused)) - 1
        return self

    def _clip_rect(self, x: int, y: int, width: int, height: int) -> tuple[int, int, int, int]:
        if width < 0 or height < 0:
            raise ValueError("rectangle width and height must be non-negative")
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + width)
        y1 = min(self.height, y + height)
        return x0, y0, x1, y1

    def fill_rect(self, x: int, y: int, width: int, height: int, state: Any = True) -> "Canvas":
        x0, y0, x1, y1 = self._clip_rect(x, y, width, height)
        for xx in range(x0, x1):
            for yy in range(y0, y1):
                self.set_pixel(xx, yy, state)
        return self

    def clear_rect(self, x: int, y: int, width: int, height: int) -> "Canvas":
        return self.fill_rect(x, y, width, height, False)

    def draw_rect(
        self, x: int, y: int, width: int, height: int, state: Any = True
    ) -> "Canvas":
        if width < 0 or height < 0:
            raise ValueError("rectangle width/height must be non-negative")
        if width == 0 or height == 0:
            return self

        x1 = x + width - 1
        y1 = y + height - 1
        self.draw_line(x, y, x1, y, state)
        if height > 1:
            self.draw_line(x, y1, x1, y1, state)
        if height > 2:
            self.draw_line(x, y + 1, x, y1 - 1, state)
            if width > 1:
                self.draw_line(x1, y + 1, x1, y1 - 1, state)
        return self

    def invert_rect(self, x: int, y: int, width: int, height: int) -> "Canvas":
        x0, y0, x1, y1 = self._clip_rect(x, y, width, height)
        for xx in range(x0, x1):
            for yy in range(y0, y1):
                byte_index, bit = self._address(xx, yy)
                self._data[byte_index] ^= 1 << bit
        return self

    def draw_line(self, x0: int, y0: int, x1: int, y1: int, state: Any = True) -> "Canvas":
        """Draw an inclusive Bresenham line; pixels outside the canvas are clipped."""
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        error = dx + dy
        while True:
            if 0 <= x0 < self.width and 0 <= y0 < self.height:
                self.set_pixel(x0, y0, state)
            if x0 == x1 and y0 == y1:
                break
            twice_error = 2 * error
            if twice_error >= dy:
                error += dy
                x0 += sx
            if twice_error <= dx:
                error += dx
                y0 += sy
        return self

    def shift(self, dx: int, dy: int, fill: Any = False) -> "Canvas":
        if dx == 0 and dy == 0:
            return self

        source = self.copy()
        self.fill(fill)

        for y in range(self.height):
            src_y = y - dy
            if not 0 <= src_y < self.height:
                continue
            for x in range(self.width):
                src_x = x - dx
                if 0 <= src_x < self.width:
                    self.set_pixel(x, y, source.get_pixel(src_x, src_y))
        return self

    def copy(self) -> "Canvas":
        return Canvas(self.geometry, bytes(self._data))

    clone = copy

    def to_bytes(self) -> bytes:
        """Return an immutable copy in the device's packed DrawBW wire format."""
        return bytes(self._data)

    def to_rows(self, on: str = "#", off: str = ".") -> list[str]:
        return [
            "".join(on if self.get_pixel(x, y) else off for x in range(self.width))
            for y in range(self.height)
        ]

    def show(self, device: "Device") -> None:
        device.show_frame(self)

    @classmethod
    def from_bytes(cls, data: bytes, geometry: MatrixGeometry = FW16_LED_MATRIX) -> "Canvas":
        return cls(geometry=geometry, data=data)

    @classmethod
    def from_array(
        cls, values: Sequence[Sequence[Any]], geometry: MatrixGeometry = FW16_LED_MATRIX, threshold: int = 0
    ) -> "Canvas":
        """Build a canvas from a row-major nested sequence or NumPy ``(height, width)`` array."""
        if len(values) != geometry.height:
            raise ValueError("expected %d rows, got %d" % (geometry.height, len(values)))
        canvas = cls(geometry)
        for y, row in enumerate(values):
            if len(row) != geometry.width:
                raise ValueError("expected %d columns in row %d, got %d" % (geometry.width, y, len(row)))
            for x, value in enumerate(row):
                canvas.set_pixel(x, y, bool(value) if isinstance(value, bool) else int(value) > threshold)
        return canvas

    @classmethod
    def from_pil(
        cls,
        image: Any,
        geometry: MatrixGeometry = FW16_LED_MATRIX,
        dither: str = "threshold",
        resize: str = "nearest",
        threshold: int = 128,
    ) -> "Canvas":
        from .image import ImagePipeline

        return ImagePipeline(geometry=geometry, dither=dither, resize=resize, threshold=threshold).process(image)

    def __repr__(self) -> str:
        return "Canvas(width=%d, height=%d, bytes=%r)" % (self.width, self.height, bytes(self._data))
