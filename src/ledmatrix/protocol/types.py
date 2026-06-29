"""Typed values shared by the Framework serial protocol."""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Tuple


class Command(IntEnum):
    BRIGHTNESS = 0x00
    PATTERN = 0x01
    BOOTLOADER = 0x02
    SLEEP = 0x03
    ANIMATE = 0x04
    PANIC = 0x05
    DRAW_BW = 0x06
    STAGE_COLUMN = 0x07
    FLUSH_COLUMNS = 0x08
    VERSION = 0x20


class Pattern(IntEnum):
    PERCENTAGE = 0
    GRADIENT = 1
    DOUBLE_GRADIENT = 2
    LOTUS_SIDEWAYS = 3
    ZIGZAG = 4
    ALL_ON = 5
    PANIC = 6
    LOTUS_TOP_DOWN = 7


POWER_AWAKE = "awake"
POWER_SLEEP = "sleep"


@dataclass(frozen=True)
class FirmwareVersion:
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return "%d.%d.%d" % (self.major, self.minor, self.patch)

    @classmethod
    def from_bytes(cls, data: bytes) -> "FirmwareVersion":
        if len(data) != 3:
            raise ValueError("firmware version requires exactly 3 bytes")
        return cls(data[0], data[1], data[2])


@dataclass(frozen=True)
class DeviceCapabilities:
    grayscale_columns: bool = True
    vblank_ack: bool = False
    schedule_frame: bool = False
