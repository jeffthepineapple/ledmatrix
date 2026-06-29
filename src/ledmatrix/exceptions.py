"""Exception hierarchy for ledmatrix."""


class LedMatrixError(Exception):
    """Base class for all SDK errors."""


class DeviceError(LedMatrixError):
    """A device-level operation failed."""


class DeviceNotFound(DeviceError):
    """No suitable Framework LED Matrix device was discovered."""


class DeviceDisconnected(DeviceError):
    """The device was removed or became unavailable during I/O."""


class DeviceStalled(DeviceError):
    """No successfully transmitted frame was observed within the watchdog window."""


class TransportError(DeviceError):
    """Underlying transport failed."""


class TransportUnavailable(TransportError):
    """An optional transport dependency is not installed or cannot be loaded."""


class ProtocolError(LedMatrixError):
    """A request cannot be represented by the documented module protocol."""


class UnsupportedCapability(DeviceError):
    """The connected firmware does not support the requested capability."""


class ImageDependencyError(LedMatrixError):
    """An optional image dependency is required for this operation."""
