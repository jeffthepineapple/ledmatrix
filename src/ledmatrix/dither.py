"""Dependency-free 1-bit dithering algorithms."""
from __future__ import annotations

from typing import Iterable, List, Sequence

DitherName = str

_BAYER_2 = ((0, 2), (3, 1))
_BAYER_4 = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)


def normalize_dither(name: str) -> str:
    normalized = name.lower().replace("-", "_")
    valid = {"none", "threshold", "bayer2x2", "bayer4x4", "floyd_steinberg"}
    if normalized not in valid:
        raise ValueError("unknown dither strategy %r; choose from %s" % (name, sorted(valid)))
    return normalized


def _coerce_grid(values: Sequence[Sequence[int]]) -> List[List[int]]:
    if not values:
        return []
    width = len(values[0])
    if width == 0:
        return [[] for _ in values]
    result: List[List[int]] = []
    for row in values:
        if len(row) != width:
            raise ValueError("all image rows must have the same width")
        result.append([max(0, min(255, int(v))) for v in row])
    return result


def _threshold(values: Sequence[Sequence[int]], threshold: int) -> List[List[int]]:
    return [[1 if value >= threshold else 0 for value in row] for row in values]


def _bayer(values: Sequence[Sequence[int]], matrix: Sequence[Sequence[int]]) -> List[List[int]]:
    size = len(matrix)
    scale = size * size
    output: List[List[int]] = []
    for y, row in enumerate(values):
        output_row: List[int] = []
        for x, value in enumerate(row):
            threshold = ((matrix[y % size][x % size] + 0.5) / scale) * 255
            output_row.append(1 if value >= threshold else 0)
        output.append(output_row)
    return output


def _floyd_steinberg(values: Sequence[Sequence[int]], threshold: int) -> List[List[int]]:
    work = [[float(value) for value in row] for row in values]
    height = len(work)
    width = len(work[0]) if height else 0
    out = [[0] * width for _ in range(height)]
    for y in range(height):
        for x in range(width):
            old = work[y][x]
            new = 255.0 if old >= threshold else 0.0
            out[y][x] = int(new > 0)
            error = old - new
            if x + 1 < width:
                work[y][x + 1] += error * 7 / 16
            if y + 1 < height:
                if x > 0:
                    work[y + 1][x - 1] += error * 3 / 16
                work[y + 1][x] += error * 5 / 16
                if x + 1 < width:
                    work[y + 1][x + 1] += error * 1 / 16
    return out


def dither(
    values: Sequence[Sequence[int]], strategy: str = "threshold", threshold: int = 128
) -> List[List[int]]:
    """Convert a grayscale grid (0..255) to a grid of bits.

    The return value is always row-major ``height x width``. Packing happens in :class:`Canvas`.
    """
    if not 0 <= threshold <= 255:
        raise ValueError("threshold must be between 0 and 255")
    grid = _coerce_grid(values)
    selected = normalize_dither(strategy)
    if selected in ("none", "threshold"):
        return _threshold(grid, threshold)
    if selected == "bayer2x2":
        return _bayer(grid, _BAYER_2)
    if selected == "bayer4x4":
        return _bayer(grid, _BAYER_4)
    return _floyd_steinberg(grid, threshold)
