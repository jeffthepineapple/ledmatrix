"""Public device lifecycle and Framework 16 command API."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Optional, Sequence, Union

from .canvas import Canvas
from .exceptions import (
    DeviceDisconnected,
    DeviceNotFound,
    ProtocolError,
    TransportError,
    UnsupportedCapability,
)
from .geometry import FW16_LED_MATRIX, MatrixGeometry
from .protocol import Command, DeviceCapabilities, FirmwareVersion, Framework16Protocol, Pattern
from .scheduler import FrameScheduler
from .transport import FRAMEWORK_VID, LED_MATRIX_PID, SerialTransport, Transport, list_serial_ports


@dataclass(frozen=True)
class DeviceInfo:
    """Stable device metadata collected without opening the serial port."""

    path: str
    vid: Optional[int]
    pid: Optional[int]
    serial: Optional[str]
    product: Optional[str]
    manufacturer: Optional[str] = None

    @property
    def is_framework_led_matrix(self) -> bool:
        return (self.vid == FRAMEWORK_VID and self.pid == LED_MATRIX_PID) or (
            "led_matrix" in (self.product or "").lower()
        )


@dataclass(frozen=True)
class DeviceDetails:
    info: DeviceInfo
    firmware: FirmwareVersion
    geometry: MatrixGeometry
    capabilities: DeviceCapabilities


def list_devices() -> list[DeviceInfo]:
    """Discover current Framework LED Matrix USB serial endpoints."""
    devices = []
    for port in list_serial_ports():
        info = DeviceInfo(
            path=port.path,
            vid=port.vid,
            pid=port.pid,
            serial=port.serial_number,
            product=port.product,
            manufacturer=port.manufacturer,
        )
        if info.is_framework_led_matrix:
            devices.append(info)
    return devices


def _choose_device(
    devices: Sequence[DeviceInfo], serial: Optional[str], index: Optional[int], port: Optional[str]
) -> DeviceInfo:
    if port is not None:
        matches = [device for device in devices if device.path == port]
        if matches:
            return matches[0]
        # A caller may deliberately provide a non-enumerable serial path on a constrained platform.
        return DeviceInfo(path=port, vid=None, pid=None, serial=serial, product="LED_Matrix")
    if serial is not None:
        matches = [device for device in devices if device.serial == serial]
        if not matches:
            raise DeviceNotFound("no Framework LED Matrix with serial %r" % serial)
        return matches[0]
    if index is not None:
        try:
            return list(devices)[index]
        except IndexError as exc:
            raise DeviceNotFound("no Framework LED Matrix at index %d" % index) from exc
    if not devices:
        raise DeviceNotFound("no Framework LED Matrix serial device found")
    return devices[0]


def open_device(
    *,
    serial: Optional[str] = None,
    index: Optional[int] = None,
    port: Optional[str] = None,
    timeout: float = 1.0,
    fps: float = 30.0,
    transport: Optional[Transport] = None,
    info: Optional[DeviceInfo] = None,
) -> "Device":
    """Open a device by serial, discovery index, explicit serial path, or injected transport."""
    if transport is not None:
        selected = info or DeviceInfo(
            path="mock://transport", vid=FRAMEWORK_VID, pid=LED_MATRIX_PID, serial=serial, product="LED_Matrix"
        )
        return Device(transport=transport, info=selected, response_timeout=timeout, fps=fps)
    selected = info or _choose_device(list_devices(), serial, index, port)
    return Device(
        transport=SerialTransport(selected.path, timeout=timeout),
        info=selected,
        response_timeout=timeout,
        fps=fps,
    )


class Device:
    """Synchronous handle for one Framework 16 LED Matrix module.

    The device uses the official serial command protocol. ``show_frame`` is host-paced by a
    :class:`FrameScheduler`; it is synchronous and intentionally queues no extra frames.
    """

    geometry = FW16_LED_MATRIX
    capabilities = DeviceCapabilities()

    def __init__(
        self,
        transport: Transport,
        info: DeviceInfo,
        response_timeout: float = 1.0,
        fps: float = 30.0,
    ) -> None:
        self.transport = transport
        self.info = info
        self._protocol = Framework16Protocol(transport, response_timeout=response_timeout)
        self._scheduler = FrameScheduler(fps=fps)
        self._io_lock = threading.RLock()
        self._closed = False
        # ponytail: hardware calibration knob. Columns staged back-to-back get
        # dropped by the firmware, so we pause between each. 9 cols * 10ms ~= 90ms/frame
        # caps throughput near ~11fps; lower it if a given unit tolerates faster sends.
        self.column_delay = 0.01

    def __enter__(self) -> "Device":
        self._ensure_open()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    @property
    def is_open(self) -> bool:
        return not self._closed and self.transport.is_open

    @property
    def fps(self) -> float:
        return self._scheduler.fps

    def _ensure_open(self) -> None:
        if self._closed or not self.transport.is_open:
            raise DeviceDisconnected("device %s is not connected" % self.info.path)

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self.transport.close()

    def get_canvas(self) -> Canvas:
        return Canvas(self.geometry)

    def raw_command(
        self, opcode: int, payload: Union[bytes, bytearray, Sequence[int]] = b"", response_bytes: int = 0
    ) -> bytes:
        """Send a raw documented or vendor-extension command with byte-range validation."""
        with self._io_lock:
            self._ensure_open()
            return self._protocol.send(opcode, payload, response_bytes=response_bytes)

    def set_brightness(self, percent: int) -> None:
        """Set global LED max brightness in the documented 0..100 percent range."""
        if not 0 <= percent <= 100:
            raise ProtocolError("brightness percent must be between 0 and 100")
        self.raw_command(Command.BRIGHTNESS, bytes((percent,)))

    def get_brightness(self) -> int:
        return self.raw_command(Command.BRIGHTNESS, response_bytes=1)[0]

    def set_pattern(self, pattern: Union[int, Pattern], value: Optional[int] = None) -> None:
        try:
            pattern_value = int(pattern)
        except (TypeError, ValueError) as exc:
            raise ProtocolError("pattern must be a byte") from exc
        if not 0 <= pattern_value <= 0xFF:
            raise ProtocolError("pattern must be in range 0..255")
        payload = bytearray((pattern_value,))
        if value is not None:
            if not 0 <= value <= 100:
                raise ProtocolError("pattern value must be in range 0..100")
            payload.append(value)
        self.raw_command(Command.PATTERN, payload)

    def sleep(self) -> None:
        self.raw_command(Command.SLEEP, b"\x01")

    def wake(self) -> None:
        self.raw_command(Command.SLEEP, b"\x00")

    def is_awake(self) -> bool:
        """Return ``True`` when the device reports it is not sleeping."""
        return not bool(self.raw_command(Command.SLEEP, response_bytes=1)[0])

    def set_power_mode(self, mode: str) -> None:
        normalized = mode.lower().strip()
        if normalized == "sleep":
            self.sleep()
        elif normalized in {"awake", "wake"}:
            self.wake()
        else:
            raise ProtocolError("power mode must be 'awake' or 'sleep'")

    def set_animation(self, enabled: bool) -> None:
        self.raw_command(Command.ANIMATE, bytes((int(bool(enabled)),)))

    def is_animating(self) -> bool:
        return bool(self.raw_command(Command.ANIMATE, response_bytes=1)[0])

    def set_leds(self, frame: Union[Canvas, bytes, bytearray]) -> None:
        """Render a 1-bit frame by staging each column, then flushing.

        DrawBW (0x06) drops LEDs on real hardware; the documented reliable path is to
        stage all columns (0x07) with a short inter-column delay and commit once (0x08).
        """
        if isinstance(frame, Canvas):
            if frame.geometry != self.geometry:
                raise ProtocolError("canvas geometry does not match this device")
            canvas = frame
        else:
            payload = bytes(frame)
            if len(payload) != self.geometry.frame_bytes:
                raise ProtocolError(
                    "frame requires exactly %d bytes for %dx%d, got %d"
                    % (self.geometry.frame_bytes, self.geometry.width, self.geometry.height, len(payload))
                )
            canvas = Canvas.from_bytes(payload, self.geometry)
        self._show_columns(
            [
                [255 if canvas.get_pixel(x, y) else 0 for y in range(self.geometry.height)]
                for x in range(self.geometry.width)
            ]
        )

    def set_grayscale(self, grid: Sequence[Sequence[int]]) -> None:
        """Set per-LED brightness (0..255) from a row-major ``height x width`` grid.

        Use :meth:`set_brightness` for the whole module; this controls each LED.
        """
        if len(grid) != self.geometry.height:
            raise ProtocolError("grayscale frame needs %d rows" % self.geometry.height)
        for row in grid:
            if len(row) != self.geometry.width:
                raise ProtocolError("each row needs %d values" % self.geometry.width)
        columns = [[grid[y][x] for y in range(self.geometry.height)] for x in range(self.geometry.width)]
        self._show_columns(columns)

    def _show_columns(self, columns: Sequence[Sequence[int]]) -> None:
        """Stage every column (0x07) with an inter-column delay, then commit once (0x08)."""
        for x, column in enumerate(columns):
            self.stage_column(x, column)
            time.sleep(self.column_delay)
        self.flush_columns()

    def show_frame(self, frame: Union[Canvas, bytes, bytearray]) -> None:
        """Backpressured host-paced frame submit. Returns only after the serial write completes."""
        self._scheduler.submit(lambda: self.set_leds(frame))

    def schedule_frame(self, frame: Union[Canvas, bytes, bytearray]) -> None:
        """Compatibility name for host-paced ``show_frame``.

        Current documented Framework firmware provides no ScheduleFrame/v-blank ACK command;
        see :attr:`capabilities` before relying on device-locked pacing.
        """
        self.show_frame(frame)

    def set_fps(self, fps: float) -> None:
        """Set the host scheduler's target rate; it does not configure the device firmware."""
        self._scheduler.set_fps(fps)

    def check_watchdog(self) -> None:
        self._scheduler.check_watchdog()

    def stage_column(self, x: int, grayscale: Sequence[int]) -> None:
        """Stage one 8-bit grayscale column, then call :meth:`flush_columns` to display it."""
        if not 0 <= x < self.geometry.width:
            raise ProtocolError("column x must be between 0 and %d" % (self.geometry.width - 1))
        if len(grayscale) != self.geometry.height:
            raise ProtocolError("a grayscale column must contain %d values" % self.geometry.height)
        try:
            values = bytes(grayscale)
        except ValueError as exc:
            raise ProtocolError("grayscale values must be byte values") from exc
        self.raw_command(Command.STAGE_COLUMN, bytes((x,)) + values)

    def flush_columns(self) -> None:
        self.raw_command(Command.FLUSH_COLUMNS)

    def get_firmware_version(self) -> FirmwareVersion:
        with self._io_lock:
            self._ensure_open()
            return self._protocol.get_version()

    def get_device_info(self) -> DeviceDetails:
        return DeviceDetails(
            info=self.info,
            firmware=self.get_firmware_version(),
            geometry=self.geometry,
            capabilities=self.capabilities,
        )

    def bootloader_reset(self, *, confirm: bool = False) -> None:
        """Reset into RP2040 bootloader only after explicit confirmation."""
        if not confirm:
            raise UnsupportedCapability(
                "bootloader reset is destructive to the active connection; pass confirm=True to execute"
            )
        self.raw_command(Command.BOOTLOADER)

    def panic(self, *, confirm: bool = False) -> None:
        """Invoke firmware's documented crash test only after explicit confirmation."""
        if not confirm:
            raise UnsupportedCapability(
                "panic intentionally crashes the firmware; pass confirm=True to execute"
            )
        self.raw_command(Command.PANIC)

    def reconnect(self, max_retries: int = 5, initial_backoff: float = 0.25) -> "Device":
        """Reopen a removed device, using its serial number when available.

        The same instance is returned after a successful reconnect. Callers can safely retry
        this method in a long-running UI or service after catching :class:`DeviceDisconnected`.
        """
        if max_retries < 1:
            raise ValueError("max_retries must be at least 1")
        if initial_backoff <= 0:
            raise ValueError("initial_backoff must be greater than zero")
        last_error: Optional[Exception] = None
        try:
            self.transport.close()
        except Exception:
            pass
        self._closed = True
        for attempt in range(max_retries):
            try:
                replacement = open_device(
                    serial=self.info.serial,
                    port=None if self.info.serial else self.info.path,
                    fps=self.fps,
                )
                self.transport = replacement.transport
                self.info = replacement.info
                self._protocol = Framework16Protocol(self.transport)
                self._closed = False
                self._scheduler.reset()
                return self
            except (DeviceNotFound, TransportError, DeviceDisconnected) as exc:
                last_error = exc
                if attempt + 1 < max_retries:
                    time.sleep(initial_backoff * (2**attempt))
        raise DeviceDisconnected("unable to reconnect after %d attempts: %s" % (max_retries, last_error))
