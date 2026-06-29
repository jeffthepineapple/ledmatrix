"""Pillow-backed image preparation for the 1-bit canvas."""
from __future__ import annotations

from typing import Any, Sequence

from .canvas import Canvas
from .dither import dither as apply_dither, normalize_dither
from .exceptions import ImageDependencyError
from .geometry import FW16_LED_MATRIX, MatrixGeometry


class ImagePipeline:
    """Resize, luminance-convert, dither, and pack an image into a :class:`Canvas`."""

    def __init__(
        self,
        geometry: MatrixGeometry = FW16_LED_MATRIX,
        dither: str = "threshold",
        resize: str = "nearest",
        threshold: int = 128,
    ) -> None:
        self.geometry = geometry
        self.dither = normalize_dither(dither)
        self.resize = resize.lower()
        self.threshold = threshold
        if self.resize not in {"nearest", "bilinear", "area"}:
            raise ValueError("resize must be 'nearest', 'bilinear', or 'area'")
        if not 0 <= threshold <= 255:
            raise ValueError("threshold must be between 0 and 255")

    def process(self, image: Any) -> Canvas:
        try:
            from PIL import Image
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise ImageDependencyError("Image support requires: pip install ledmatrix[image]") from exc

        if not hasattr(image, "convert"):
            raise TypeError("process() expects a Pillow Image object")
        resampling = getattr(Image, "Resampling", Image)
        resample_map = {
            "nearest": resampling.NEAREST,
            "bilinear": resampling.BILINEAR,
            "area": getattr(resampling, "BOX", resampling.BILINEAR),
        }
        gray = image.convert("L").resize((self.geometry.width, self.geometry.height), resample_map[self.resize])
        values = list(gray.getdata())
        rows = [
            values[y * self.geometry.width : (y + 1) * self.geometry.width]
            for y in range(self.geometry.height)
        ]
        bits = apply_dither(rows, self.dither, self.threshold)
        return Canvas.from_array(bits, geometry=self.geometry, threshold=0)

    def process_array(self, values: Sequence[Sequence[int]]) -> Canvas:
        bits = apply_dither(values, self.dither, self.threshold)
        return Canvas.from_array(bits, geometry=self.geometry, threshold=0)
