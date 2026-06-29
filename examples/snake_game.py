#!/usr/bin/env python3
"""Play a small terminal-controlled Snake game on the LED Matrix module.

Controls: W/A/S/D or arrow keys to turn, Q to quit.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import random
import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass, field

if os.name == "nt":
    import msvcrt
else:
    import select
    import termios
    import tty

import _bootstrap  # noqa: F401

from ledmatrix import Canvas, FrameScheduler, open_device

WIDTH = 9
HEIGHT = 34
START_LENGTH = 4

Point = tuple[int, int]
Direction = tuple[int, int]

UP: Direction = (0, -1)
DOWN: Direction = (0, 1)
LEFT: Direction = (-1, 0)
RIGHT: Direction = (1, 0)

KEY_DIRECTIONS: dict[str, Direction] = {
    "w": UP,
    "a": LEFT,
    "s": DOWN,
    "d": RIGHT,
    "\x1b[A": UP,
    "\x1b[D": LEFT,
    "\x1b[B": DOWN,
    "\x1b[C": RIGHT,
}


@dataclass
class SnakeGame:
    snake: list[Point]
    direction: Direction
    food: Point
    score: int = 0
    game_over: bool = False
    rng: random.Random = field(default_factory=random.Random)

    @classmethod
    def create(cls, seed: int | None = None) -> SnakeGame:
        rng = random.Random(seed)
        center_x = WIDTH // 2
        center_y = HEIGHT // 2
        snake = [(center_x, center_y + offset) for offset in range(START_LENGTH)]
        game = cls(snake=snake, direction=UP, food=(0, 0), rng=rng)
        game.food = game._spawn_food()
        return game

    def turn(self, direction: Direction) -> None:
        if self.game_over:
            return
        if direction == (-self.direction[0], -self.direction[1]):
            return
        self.direction = direction

    def step(self) -> None:
        if self.game_over:
            return

        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        head = (head_x + dx, head_y + dy)

        if not (0 <= head[0] < WIDTH and 0 <= head[1] < HEIGHT):
            self.game_over = True
            return

        tail = self.snake[-1]
        body = set(self.snake[:-1] if head == tail else self.snake)
        if head in body:
            self.game_over = True
            return

        self.snake.insert(0, head)
        if head == self.food:
            self.score += 1
            self.food = self._spawn_food()
        else:
            self.snake.pop()

    def render(self) -> Canvas:
        canvas = Canvas().clear()
        if self.game_over:
            for y in range(0, HEIGHT, 2):
                canvas.draw_line(0, y, WIDTH - 1, y, 80)
            return canvas

        food_x, food_y = self.food
        canvas.set_pixel(food_x, food_y, 96)

        for x, y in self.snake[1:]:
            canvas.set_pixel(x, y, 160)

        head_x, head_y = self.snake[0]
        canvas.set_pixel(head_x, head_y, 255)
        return canvas

    def _spawn_food(self) -> Point:
        occupied = set(self.snake)
        choices = [
            (x, y)
            for y in range(HEIGHT)
            for x in range(WIDTH)
            if (x, y) not in occupied
        ]
        if not choices:
            self.game_over = True
            return self.snake[0]
        return self.rng.choice(choices)


@contextlib.contextmanager
def raw_terminal(enabled: bool) -> Iterator[None]:
    if os.name == "nt" or not enabled or not sys.stdin.isatty():
        yield
        return

    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())
        yield
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def read_key() -> str | None:
    if os.name == "nt":
        if not msvcrt.kbhit():
            return None

        key = msvcrt.getwch()
        if key in ("\x00", "\xe0") and msvcrt.kbhit():
            return {
                "H": "\x1b[A",
                "P": "\x1b[B",
                "K": "\x1b[D",
                "M": "\x1b[C",
            }.get(msvcrt.getwch())
        return key

    readable, _, _ = select.select([sys.stdin], [], [], 0)
    if not readable:
        return None

    key = sys.stdin.read(1)
    if key == "\x1b" and select.select([sys.stdin], [], [], 0)[0]:
        key += sys.stdin.read(2)
    return key


def render_terminal(canvas: Canvas, score: int, game_over: bool) -> None:
    rows = []
    for y in range(canvas.height):
        row = "".join("#" if canvas.get_pixel(x, y) else "." for x in range(canvas.width))
        rows.append(row)
    suffix = "game over" if game_over else "WASD/arrows, Q quits"
    status = f"score={score} {suffix}"
    print("\x1b[H\x1b[J" + "\n".join(rows) + "\n" + status, flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", help="explicit serial port, for example /dev/ttyACM0")
    parser.add_argument("--serial", help="Framework device serial number")
    parser.add_argument("--fps", type=float, default=6.0, help="game speed in frames per second")
    parser.add_argument(
        "--brightness",
        type=int,
        default=40,
        help="module brightness, 0..100",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="random seed for repeatable food placement",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="draw to the terminal instead of hardware",
    )
    parser.add_argument("--frames", type=int, help="stop after this many frames")
    return parser.parse_args()


def run_game(args: argparse.Namespace) -> int:
    game = SnakeGame.create(seed=args.seed)
    scheduler = FrameScheduler(fps=args.fps)
    frame_count = 0

    with contextlib.ExitStack() as stack:
        stack.enter_context(raw_terminal(enabled=True))
        device = None
        if not args.dry_run:
            device = stack.enter_context(
                open_device(port=args.port, serial=args.serial, fps=args.fps)
            )
            device.set_brightness(args.brightness)

        try:
            while True:
                key = read_key()
                if key in {"q", "Q"}:
                    break
                if key in KEY_DIRECTIONS:
                    game.turn(KEY_DIRECTIONS[key])

                game.step()
                canvas = game.render()

                if device is None:
                    render_terminal(canvas, game.score, game.game_over)
                else:
                    scheduler.submit(lambda canvas=canvas: device.show_frame(canvas))

                frame_count += 1
                if args.frames is not None and frame_count >= args.frames:
                    break

                if game.game_over:
                    time.sleep(1.5)
                    break

                if device is None:
                    time.sleep(max(0.0, 1.0 / args.fps))
        finally:
            blank = Canvas().clear()
            if device is None:
                render_terminal(blank, game.score, game.game_over)
            else:
                device.show_frame(blank)

    return 0


def main() -> int:
    return run_game(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
