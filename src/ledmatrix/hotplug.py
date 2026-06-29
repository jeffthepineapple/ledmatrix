"""Portable polling-based device hot-plug watcher."""
from __future__ import annotations

import threading
from typing import Callable, Dict, Optional, Tuple

from .transport.serial import FRAMEWORK_VID, LED_MATRIX_PID, list_serial_ports

DeviceKey = Tuple[str, Optional[str]]
DeviceCallback = Callable[[DeviceKey], None]


class DeviceWatcher:
    """Poll serial ports and invoke callbacks for Framework LED Matrix arrivals/removals."""

    def __init__(self, interval: float = 1.0) -> None:
        if interval <= 0:
            raise ValueError("interval must be greater than zero")
        self.interval = interval
        self._connected: Optional[DeviceCallback] = None
        self._removed: Optional[DeviceCallback] = None
        self._known: Dict[DeviceKey, bool] = {}
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def on_connected(self, callback: DeviceCallback) -> "DeviceWatcher":
        self._connected = callback
        return self

    def on_removed(self, callback: DeviceCallback) -> "DeviceWatcher":
        self._removed = callback
        return self

    def _scan(self) -> Dict[DeviceKey, bool]:
        current: Dict[DeviceKey, bool] = {}
        for port in list_serial_ports():
            product = (port.product or "").lower()
            if (port.vid == FRAMEWORK_VID and port.pid == LED_MATRIX_PID) or "led_matrix" in product:
                current[(port.path, port.serial_number)] = True
        return current

    def poll_once(self) -> None:
        current = self._scan()
        for key in current:
            if key not in self._known and self._connected is not None:
                self._connected(key)
        for key in self._known:
            if key not in current and self._removed is not None:
                self._removed(key)
        self._known = current

    def start(self) -> "DeviceWatcher":
        if self._thread is not None and self._thread.is_alive():
            return self
        self._stop.clear()
        self.poll_once()
        self._thread = threading.Thread(target=self._run, name="ledmatrix-hotplug", daemon=True)
        self._thread.start()
        return self

    def _run(self) -> None:
        while not self._stop.wait(self.interval):
            self.poll_once()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self.interval + 0.2)
            self._thread = None

    def __enter__(self) -> "DeviceWatcher":
        return self.start()

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.stop()
