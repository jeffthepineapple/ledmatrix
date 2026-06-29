"""Animated 1-bit demo: a ball bounces around the panel leaving a trail.

Run on hardware:  .venv/bin/python examples/draw_primitives.py [--port /dev/ttyACM0]
Ctrl+C to stop.
"""
import argparse
import time

import _bootstrap  # noqa: F401  (selects installed package or in-repo src/)
from ledmatrix import Canvas, open_device

ap = argparse.ArgumentParser()
ap.add_argument("--port")
args = ap.parse_args()

with open_device(port=args.port) as device:
    device.wake()
    device.set_animation(False)
    device.set_brightness(100)

    W, H = 9, 34
    x, y, dx, dy = 4, 0, 1, 1
    try:
        while True:
            canvas = Canvas()
            canvas.draw_rect(0, 0, W, H, True)        # static frame
            canvas.fill_rect(x - 1, y - 1, 3, 3, True)  # the ball
            device.show_frame(canvas)

            x += dx
            y += dy
            if x <= 1 or x >= W - 2:
                dx = -dx
            if y <= 1 or y >= H - 2:
                dy = -dy
            time.sleep(0.05)
    except KeyboardInterrupt:
        device.set_leds(Canvas())
