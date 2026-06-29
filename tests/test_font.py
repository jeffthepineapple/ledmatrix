from ledmatrix import Canvas
from ledmatrix.font import Font, draw_text_scrolling


def test_bundled_bdf_font_draws_pixels():
    font = Font.load("3x5")
    canvas = Canvas()
    font.draw_text(canvas, 0, 0, "HI")
    assert any(canvas.to_bytes())
    assert font.text_width("HI") > 0


def test_marquee_yields_frames():
    frames = draw_text_scrolling(Canvas(), "HI", font=Font.load("3x5"), fps=10)
    first = next(frames)
    assert isinstance(first, Canvas)
def test_3x5_glyph_rows_are_stable():
    font = Font.load("3x5")
    expected = {
        "A": [
            ".#.......",
            "#.#......",
            "###......",
            "#.#......",
            "#.#......",
        ],
        "H": [
            "#.#......",
            "#.#......",
            "###......",
            "#.#......",
            "#.#......",
        ],
        "I": [
            ".#.......",
            ".#.......",
            ".#.......",
            ".#.......",
            ".#.......",
        ],
        "HI": [
            "#.#...#..",
            "#.#...#..",
            "###...#..",
            "#.#...#..",
            "#.#...#..",
        ],
    }

    for text, rows in expected.items():
        canvas = Canvas()
        font.draw_text(canvas, 0, 0, text)
        assert canvas.to_rows()[:5] == rows


def test_3x5_text_packed_bytes_are_stable():
    canvas = Canvas()
    Font.load("3x5").draw_text(canvas, 0, 0, "HI")

    assert (
        canvas.to_bytes().hex()
        == "1f00000010000000f001000000000000000000000000000000f001000000000000000000000000"
    )
