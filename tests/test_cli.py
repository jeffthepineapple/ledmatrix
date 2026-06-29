from ledmatrix.cli.main import main


def test_cli_dry_run_pixel(capsys):
    assert main(["pixel", "0", "0", "--dry-run"]) == 0
    captured = capsys.readouterr().out
    assert "dry-run write 1:" in captured
    assert "32 ac 07" in captured


def test_cli_text_preview_dry_run(capsys):
    assert main(["text", "HI", "--font", "3x5", "--preview", "--dry-run"]) == 0
    captured = capsys.readouterr().out

    assert "#.#...#.." in captured
    assert "###...#.." in captured
    assert "dry-run write 1:" in captured
    assert "32 ac 07" in captured


def test_cli_text_preview_can_rotate_90_degrees(capsys):
    assert main(["text", "HI", "--font", "3x5", "--rotate", "90", "--preview", "--dry-run"]) == 0
    captured = capsys.readouterr().out

    assert "....#####" in captured
    assert "dry-run write 1:" in captured
    assert "32 ac 07" in captured


def test_cli_orientation_test_preview_dry_run(capsys):
    assert main(["orientation-test", "--preview", "--dry-run"]) == 0
    captured = capsys.readouterr().out
    rows = [line for line in captured.splitlines() if set(line) <= {"#", "."}]

    assert len(rows) == 34
    assert rows[0] == "#########"
    assert rows[-1] == "#########"
    assert "##.#...##" in rows
    assert "dry-run write 1:" in captured


def test_cli_prints_udev_rule(capsys):
    assert main(["system", "udev-rule"]) == 0
    assert 'ATTRS{idVendor}=="32ac"' in capsys.readouterr().out
