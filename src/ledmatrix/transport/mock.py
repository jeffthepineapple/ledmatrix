"""In-memory transport for deterministic tests and CLI dry runs."""
from __future__ import annotations

from collections import deque
from typing import Deque, Iterable, Optional

from ..exceptions import DeviceDisconnected
from .base import Transport


class MockTransport(Transport):
    """Records writes and serves programmed byte responses in FIFO order."""

    def __init__(self, responses: Optional[Iterable[bytes]] = None) -> None:
        self.writes: list[bytes] = []
        self._responses: Deque[bytes] = deque(responses or [])
        self._pending = bytearray()
        self._open = True

    @property
    def is_open(self) -> bool:
        return self._open

    def queue_response(self, response: bytes) -> None:
        self._responses.append(bytes(response))

    def disconnect(self) -> None:
        self._open = False

    def write(self, data: bytes) -> int:
        if not self._open:
            raise DeviceDisconnected("mock transport is disconnected")
        self.writes.append(bytes(data))
        return len(data)

    def read(self, size: int, timeout: Optional[float] = None) -> bytes:
        del timeout
        if not self._open:
            raise DeviceDisconnected("mock transport is disconnected")
        while len(self._pending) < size and self._responses:
            self._pending.extend(self._responses.popleft())
        result = bytes(self._pending[:size])
        del self._pending[:size]
        return result

    def close(self) -> None:
        self._open = False
