"""Transport abstractions used by the documented USB CDC-ACM protocol."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class Transport(ABC):
    """Minimal byte-stream transport.

    The Framework module's current public protocol is USB CDC-ACM serial rather than HID;
    transports therefore expose ordered byte writes and timeout-aware reads.
    """

    @property
    @abstractmethod
    def is_open(self) -> bool:
        """Whether the underlying connection remains available."""

    @abstractmethod
    def write(self, data: bytes) -> int:
        """Write all bytes or raise a transport exception."""

    @abstractmethod
    def read(self, size: int, timeout: Optional[float] = None) -> bytes:
        """Read up to ``size`` bytes, returning ``b''`` if the timeout expires."""

    @abstractmethod
    def close(self) -> None:
        """Release the transport resource. This method must be idempotent."""
