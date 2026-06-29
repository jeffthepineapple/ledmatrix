"""pyserial implementation and portable discovery helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from ..exceptions import DeviceDisconnected, TransportError, TransportUnavailable
from .base import Transport

FRAMEWORK_VID = 0x32AC
LED_MATRIX_PID = 0x0020


@dataclass(frozen=True)
class SerialPortInfo:
    path: str
    vid: Optional[int]
    pid: Optional[int]
    serial_number: Optional[str]
    product: Optional[str]
    manufacturer: Optional[str]


def _serial_modules():
    try:
        import serial  # type: ignore[import-not-found]
        from serial.tools import list_ports  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - depends on install
        raise TransportUnavailable("Serial support requires: pip install ledmatrix") from exc
    return serial, list_ports


def list_serial_ports() -> List[SerialPortInfo]:
    """Return all serial ports with enough metadata for filtering."""
    _serial, list_ports = _serial_modules()
    return [
        SerialPortInfo(
            path=port.device,
            vid=port.vid,
            pid=port.pid,
            serial_number=port.serial_number,
            product=port.product,
            manufacturer=port.manufacturer,
        )
        for port in list_ports.comports()
    ]


class SerialTransport(Transport):
    """Cross-platform USB CDC-ACM transport backed by ``pyserial``."""

    def __init__(self, path: str, baudrate: int = 115200, timeout: float = 1.0) -> None:
        serial, _ = _serial_modules()
        self.path = path
        self._timeout = timeout
        try:
            # ponytail: blocking writes (write_timeout=None) like the Rust/reference driver.
            # A finite write timeout trips on USB CDC startup; raise to a value if you need it.
            self._serial = serial.Serial(port=path, baudrate=baudrate, timeout=timeout, write_timeout=None)
        except (OSError, Exception) as exc:  # pyserial portability varies
            # Do not leak pyserial's platform-specific exceptions through the SDK.
            raise TransportError("unable to open serial device %s: %s" % (path, exc)) from exc

    @property
    def is_open(self) -> bool:
        return bool(getattr(self._serial, "is_open", False))

    def write(self, data: bytes) -> int:
        if not self.is_open:
            raise DeviceDisconnected("serial device %s is closed" % self.path)
        try:
            count = self._serial.write(data)
            self._serial.flush()
            if count != len(data):
                raise TransportError("short serial write: sent %d of %d bytes" % (count, len(data)))
            return count
        except TransportError:
            raise
        except Exception as exc:
            raise DeviceDisconnected("serial write failed for %s: %s" % (self.path, exc)) from exc

    def read(self, size: int, timeout: Optional[float] = None) -> bytes:
        if size < 0:
            raise ValueError("size must be non-negative")
        if not self.is_open:
            raise DeviceDisconnected("serial device %s is closed" % self.path)
        old_timeout = self._serial.timeout
        try:
            if timeout is not None:
                self._serial.timeout = timeout
            return bytes(self._serial.read(size))
        except Exception as exc:
            raise DeviceDisconnected("serial read failed for %s: %s" % (self.path, exc)) from exc
        finally:
            self._serial.timeout = old_timeout

    def close(self) -> None:
        if self.is_open:
            try:
                self._serial.close()
            except Exception as exc:
                raise TransportError("failed to close serial device %s: %s" % (self.path, exc)) from exc
