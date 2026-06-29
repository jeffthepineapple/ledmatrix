import pytest

from ledmatrix.exceptions import ProtocolError
from ledmatrix.protocol import Command, FirmwareVersion, encode_command


def test_encode_command_uses_documented_magic_and_opcode():
    assert encode_command(Command.BRIGHTNESS, b"\x32") == b"\x32\xac\x00\x32"


def test_invalid_command_is_rejected():
    with pytest.raises(ProtocolError):
        encode_command(256)
