"""Per-LED brightness demo: an animated sine plasma using set_grayscale().

Run on hardware:  .venv/bin/python examples/grayscale_wave.py [--port /dev/ttyACM0]
Every LED is driven at its own 0..255 level. Ctrl+C to stop.
"""
import argparse
import math
import time

import _bootstrap  # noqa: F401  (selects installed package or in-repo src/)
from ledmatrix import open_device

ap = argparse.ArgumentParser()
ap.add_argument("--port")
args = ap.parse_args()

W, H = 9, 34

with open_device(port=args.port) as device:
    device.wake()
    device.set_animation(False)
    device.set_brightness(100)
    device.column_delay = 0.005  # plasma needs throughput; lower per-column pause

    t = 0.0
    try:
        while True:
            grid = [
                [
                    int(127.5 + 127.5 * math.sin(x * 0.7 + y * 0.35 + t))
                    for x in range(W)
                ]
                for y in range(H)
            ]
            device.set_grayscale(grid)
            t += 0.25
            time.sleep(0.02)
    except KeyboardInterrupt:
        device.set_grayscale([[0] * W for _ in range(H)])
