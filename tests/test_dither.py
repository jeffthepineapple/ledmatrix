import pytest

from ledmatrix.dither import dither


def test_threshold_dither():
    assert dither([[0, 127, 128, 255]], "threshold") == [[0, 0, 1, 1]]


def test_ordered_dither_is_reproducible():
    result = dither([[128] * 4 for _ in range(4)], "bayer4x4")
    assert result == [[1, 0, 1, 0], [0, 1, 0, 1], [1, 0, 1, 0], [0, 1, 0, 1]]


def test_invalid_dither_rejected():
    with pytest.raises(ValueError):
        dither([[1]], "vaporwave")
