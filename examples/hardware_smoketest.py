#!/usr/bin/env python3
"""Hardware smoke test: walks through every draw/brightness path on a real matrix.

Run:  .venv/bin/python examples/hardware_smoketest.py [--port /dev/ttyACM0]
Watch the panel between steps; Ctrl+C aborts and clears.
"""
import argparse
import time

import _bootstrap  # noqa: F401  (selects installed package or in-repo src/)
from ledmatrix import Canvas, open_device

W, H = 9, 34


def step(name):
    print(f"-> {name}")
    time.sleep(1.2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", help="serial path, e.g. /dev/ttyACM0 (default: auto-detect)")
    ap.add_argument("--delay", type=float, help="override per-column delay (seconds)")
    args = ap.parse_args()

    d = open_device(port=args.port)
    if args.delay is not None:
        d.column_delay = args.delay
    print(f"Connected: {d.info.path}  (column_delay={d.column_delay}s)")

    try:
        d.wake()
        d.set_animation(False)
        d.set_brightness(100)

        step("all LEDs ON (every pixel must light, no gaps)")
        d.set_leds(Canvas().fill(True))

        for pct in (75, 50, 25, 5):
            step(f"module brightness {pct}%")
            d.set_brightness(pct)
        d.set_brightness(100)

        step("per-LED vertical gradient 0->255 (dim top, bright bottom)")
        d.set_grayscale([[int(y * 255 / (H - 1))] * W for y in range(H)])

        step("per-LED horizontal gradient 0->255 (dim left, bright right)")
        d.set_grayscale([[int(x * 255 / (W - 1)) for x in range(W)] for _ in range(H)])

        step("checkerboard (1-bit)")
        c = Canvas()
        for y in range(H):
            for x in range(W):
                c.set_pixel(x, y, (x + y) % 2 == 0)
        d.set_leds(c)

        step("border")
        b = Canvas()
        b.draw_rect(0, 0, W, H, True)
        d.set_leds(b)

        step("single-LED scan (one pixel walks the whole panel)")
        for y in range(H):
            for x in range(W):
                d.set_leds(Canvas().set_pixel(x, y, True))

        step("clear")
        d.set_leds(Canvas())
        print("Done. All paths exercised.")
    except KeyboardInterrupt:
        print("\nAborted.")
    finally:
        try:
            d.set_leds(Canvas())
        finally:
            d.close()


if __name__ == "__main__":
    main()
