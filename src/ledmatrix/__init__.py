"""Framework 16 LED Matrix SDK."""
from .async_device import AsyncDevice
from .canvas import Canvas
from .device import Device, DeviceDetails, DeviceInfo, list_devices, open_device
from .dither import dither
from .exceptions import (
    DeviceDisconnected,
    DeviceError,
    DeviceNotFound,
    DeviceStalled,
    ImageDependencyError,
    LedMatrixError,
    ProtocolError,
    TransportError,
    TransportUnavailable,
    UnsupportedCapability,
)
from .geometry import FW16_LED_MATRIX, MatrixGeometry, PackingOrder
from .font import Font, draw_text_scrolling
from .hotplug import DeviceWatcher
from .image import ImagePipeline
from .protocol import Command, DeviceCapabilities, FirmwareVersion, Pattern
from .scheduler import FrameScheduler

__version__ = "0.1.0"

__all__ = [
    "AsyncDevice", "Canvas", "Command", "Device", "DeviceCapabilities", "DeviceDetails", "DeviceDisconnected",
    "DeviceError", "DeviceInfo", "DeviceNotFound", "DeviceStalled", "DeviceWatcher", "FW16_LED_MATRIX",
    "FirmwareVersion", "Font", "FrameScheduler", "ImageDependencyError", "ImagePipeline", "LedMatrixError",
    "MatrixGeometry", "PackingOrder", "Pattern", "ProtocolError", "TransportError", "TransportUnavailable",
    "UnsupportedCapability", "__version__", "dither", "draw_text_scrolling", "list_devices", "open_device",
]
