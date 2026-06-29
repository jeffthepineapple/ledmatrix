"""Encoding helpers for the documented Framework 16 USB serial command protocol."""
from __future__ import annotations

from typing import Optional, Sequence, Union

from ..exceptions import ProtocolError, TransportError
from ..transport.base import Transport
from .types import Command, FirmwareVersion

MAGIC = bytes((0x32, 0xAC))
DEFAULT_RESPONSE_BYTES = 32


def _coerce_payload(payload: Union[bytes, bytearray, Sequence[int]]) -> bytes:
    try:
        result = bytes(payload)
    except (TypeError, ValueError) as exc:
        raise ProtocolError("payload must contain byte values") from exc
    return result


def encode_command(command: Union[int, Command], payload: Union[bytes, bytearray, Sequence[int]] = b"") -> bytes:
    """Build ``0x32 0xAC <command> <payload>`` after rigorous byte-range validation."""
    try:
        opcode = int(command)
    except (TypeError, ValueError) as exc:
        raise ProtocolError("command must be an integer byte") from exc
    if not 0 <= opcode <= 0xFF:
        raise ProtocolError("command must be in range 0..255")
    raw_payload = _coerce_payload(payload)
    return MAGIC + bytes((opcode,)) + raw_payload


class Framework16Protocol:
    """Serial command sender with strict response length handling."""

    def __init__(self, transport: Transport, response_timeout: float = 1.0) -> None:
        self.transport = transport
        self.response_timeout = response_timeout

    def send(
        self,
        command: Union[int, Command],
        payload: Union[bytes, bytearray, Sequence[int]] = b"",
        response_bytes: int = 0,
    ) -> bytes:
        if response_bytes < 0:
            raise ProtocolError("response_bytes must be non-negative")
        frame = encode_command(command, payload)
        try:
            count = self.transport.write(frame)
        except OSError as exc:
            raise TransportError("write failed: %s" % exc) from exc
        if count != len(frame):
            raise TransportError("short transport write: %d of %d bytes" % (count, len(frame)))
        if response_bytes == 0:
            return b""
        response = self.transport.read(response_bytes, timeout=self.response_timeout)
        if len(response) != response_bytes:
            raise TransportError(
                "expected %d response bytes, received %d" % (response_bytes, len(response))
            )
        return response

    def get_version(self) -> FirmwareVersion:
        return FirmwareVersion.from_bytes(self.send(Command.VERSION, response_bytes=3))
