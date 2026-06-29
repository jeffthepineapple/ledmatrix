"""Async wrapper around :class:`ledmatrix.device.Device`."""
from __future__ import annotations

import asyncio
from typing import Optional, Sequence, Union

from .canvas import Canvas
from .device import Device, DeviceDetails
from .protocol import FirmwareVersion, Pattern


class AsyncDevice:
    """Run the synchronous serial API in worker threads without changing its semantics."""

    def __init__(self, device: Device) -> None:
        self.device = device

    async def __aenter__(self) -> "AsyncDevice":
        await asyncio.to_thread(self.device.__enter__)
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        await self.close()

    async def close(self) -> None:
        await asyncio.to_thread(self.device.close)

    async def set_brightness(self, percent: int) -> None:
        await asyncio.to_thread(self.device.set_brightness, percent)

    async def get_brightness(self) -> int:
        return await asyncio.to_thread(self.device.get_brightness)

    async def set_pattern(self, pattern: Union[int, Pattern], value: Optional[int] = None) -> None:
        await asyncio.to_thread(self.device.set_pattern, pattern, value)

    async def sleep(self) -> None:
        await asyncio.to_thread(self.device.sleep)

    async def wake(self) -> None:
        await asyncio.to_thread(self.device.wake)

    async def is_awake(self) -> bool:
        return await asyncio.to_thread(self.device.is_awake)

    async def show_frame(self, frame: Union[Canvas, bytes, bytearray]) -> None:
        await asyncio.to_thread(self.device.show_frame, frame)

    async def schedule_frame(self, frame: Union[Canvas, bytes, bytearray]) -> None:
        await asyncio.to_thread(self.device.schedule_frame, frame)

    async def set_fps(self, fps: float) -> None:
        await asyncio.to_thread(self.device.set_fps, fps)

    async def get_firmware_version(self) -> FirmwareVersion:
        return await asyncio.to_thread(self.device.get_firmware_version)

    async def get_device_info(self) -> DeviceDetails:
        return await asyncio.to_thread(self.device.get_device_info)

    async def raw_command(
        self, opcode: int, payload: Union[bytes, bytearray, Sequence[int]] = b"", response_bytes: int = 0
    ) -> bytes:
        return await asyncio.to_thread(self.device.raw_command, opcode, payload, response_bytes)
