import pytest

from ledmatrix import Canvas, FW16_LED_MATRIX


def test_default_geometry_and_packing_are_framework_drawbw_shape():
    canvas = Canvas()
    assert (canvas.width, canvas.height) == (9, 34)
    assert len(canvas.to_bytes()) == 39

    canvas.set_pixel(0, 0, True)
    canvas.set_pixel(0, 33, True)
    canvas.set_pixel(1, 0, True)
    assert canvas.buffer[0] == 0b00000001
    assert canvas.buffer[4] == 0b00000110


def test_pixel_and_bounds_validation():
    canvas = Canvas()
    canvas.set_pixel(8, 33, True)
    assert canvas.get_pixel(8, 33)
    canvas.set_pixel(8, 33, False)
    assert not canvas.get_pixel(8, 33)
    with pytest.raises(ValueError):
        canvas.set_pixel(9, 0, True)


def test_rectangles_clip_and_invert():
    canvas = Canvas()
    canvas.fill_rect(-2, -2, 4, 4, True)
    assert canvas.get_pixel(0, 0)
    assert canvas.get_pixel(1, 1)
    assert not canvas.get_pixel(2, 2)
    canvas.invert_rect(0, 0, 2, 2)
    assert not canvas.get_pixel(0, 0)
    canvas.clear_rect(0, 0, 3, 3)
    assert not any(canvas.to_bytes())


def test_draw_rect_clips_and_draws_outline_only():
    canvas = Canvas()

    assert canvas.draw_rect(-1, 1, 4, 3) is canvas

    assert canvas.get_pixel(0, 1)
    assert canvas.get_pixel(2, 1)
    assert canvas.get_pixel(0, 3)
    assert canvas.get_pixel(2, 3)
    assert canvas.get_pixel(2, 2)
    assert not canvas.get_pixel(1, 2)
    assert not canvas.get_pixel(0, 2)


def test_draw_rect_handles_degenerate_sizes():
    canvas = Canvas()

    canvas.draw_rect(1, 1, 3, 1)
    assert canvas.get_pixel(1, 1)
    assert canvas.get_pixel(2, 1)
    assert canvas.get_pixel(3, 1)

    canvas.clear().draw_rect(1, 1, 1, 3)
    assert canvas.get_pixel(1, 1)
    assert canvas.get_pixel(1, 2)
    assert canvas.get_pixel(1, 3)

    before = canvas.to_bytes()
    assert canvas.draw_rect(0, 0, 0, 2) is canvas
    assert canvas.to_bytes() == before

    with pytest.raises(ValueError):
        canvas.draw_rect(0, 0, -1, 1)


def test_bresenham_line_is_inclusive_and_clipped():
    canvas = Canvas()
    canvas.draw_line(0, 0, 8, 33)
    assert canvas.get_pixel(0, 0)
    assert canvas.get_pixel(8, 33)
    assert sum(row.count("#") for row in canvas.to_rows()) >= 9


def test_shift_moves_pixels_and_fills_exposed_area():
    canvas = Canvas()
    canvas.set_pixel(0, 0, True)
    canvas.set_pixel(8, 33, True)

    assert canvas.shift(2, 3) is canvas

    assert canvas.get_pixel(2, 3)
    assert not canvas.get_pixel(0, 0)
    assert not canvas.get_pixel(8, 33)

    canvas.clear().set_pixel(2, 3, True).shift(-2, -3, fill=True)
    assert canvas.get_pixel(0, 0)
    assert canvas.get_pixel(8, 33)
    assert canvas.get_pixel(8, 0)
    assert canvas.get_pixel(0, 33)
    assert not canvas.get_pixel(2, 3)


def test_shift_noop_preserves_buffer_identity():
    canvas = Canvas()
    buffer = canvas.buffer

    assert canvas.shift(0, 0) is canvas
    assert canvas.buffer is buffer


def test_from_array_shape_and_threshold():
    values = [[0] * 9 for _ in range(34)]
    values[3][4] = 128
    canvas = Canvas.from_array(values, threshold=127)
    assert canvas.get_pixel(4, 3)
    with pytest.raises(ValueError):
        Canvas.from_array([[0] * 9], geometry=FW16_LED_MATRIX)
