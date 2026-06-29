"""Backpressured, host-paced frame scheduler."""
from __future__ import annotations

import threading
import time
from typing import Callable, Optional, TypeVar

from .exceptions import DeviceStalled

T = TypeVar("T")


class FrameScheduler:
    """Serializes frame sends and enforces a target frame rate.

    Current public firmware exposes no documented v-blank ACK command. Therefore this
    scheduler provides deliberate *host pacing*: each ``submit`` blocks until the next slot and
    completes only after the send callback returns. There is no frame queue, so callers naturally
    receive backpressure and frames are never silently dropped by this SDK.
    """

    def __init__(self, fps: float = 30.0, stalled_after: Optional[float] = 5.0) -> None:
        self._lock = threading.RLock()
        self._fps = 0.0
        self._interval = 0.0
        self.set_fps(fps)
        self.stalled_after = stalled_after
        self._next_slot: Optional[float] = None
        self._last_success: Optional[float] = None

    @property
    def fps(self) -> float:
        return self._fps

    def set_fps(self, fps: float) -> None:
        if fps <= 0:
            raise ValueError("fps must be greater than zero")
        self._fps = float(fps)
        self._interval = 1.0 / self._fps

    @property
    def last_success(self) -> Optional[float]:
        return self._last_success

    def submit(self, sender: Callable[[], T]) -> T:
        with self._lock:
            now = time.monotonic()
            if self._next_slot is not None and now < self._next_slot:
                time.sleep(self._next_slot - now)
            result = sender()
            completed = time.monotonic()
            self._last_success = completed
            self._next_slot = max(completed, self._next_slot or completed) + self._interval
            return result

    def check_watchdog(self) -> None:
        if self.stalled_after is None or self._last_success is None:
            return
        if time.monotonic() - self._last_success > self.stalled_after:
            raise DeviceStalled(
                "no successful frame transmission in %.3f seconds" % (time.monotonic() - self._last_success)
            )

    def reset(self) -> None:
        with self._lock:
            self._next_slot = None
            self._last_success = None
