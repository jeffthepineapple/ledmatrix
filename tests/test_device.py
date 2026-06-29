import pytest

from ledmatrix import Canvas, DeviceDisconnected, ProtocolError, UnsupportedCapability, open_device
from ledmatrix.transport import MockTransport


def test_device_stages_columns_and_validates_frame_length():
    transport = MockTransport()
    with open_device(transport=transport, fps=10_000) as device:
        device.column_delay = 0  # keep the test fast and deterministic
        canvas = Canvas().set_pixel(0, 0, True)
        device.set_leds(canvas)
        with pytest.raises(ProtocolError):
            device.set_leds(b"\x00")
    expected = [b"\x32\xac\x07\x00\xff" + b"\x00" * 33]
    expected += [b"\x32\xac\x07" + bytes((x,)) + b"\x00" * 34 for x in range(1, 9)]
    expected += [b"\x32\xac\x08"]
    assert transport.writes == expected


def test_device_set_grayscale_stages_per_led_brightness():
    transport = MockTransport()
    with open_device(transport=transport, fps=10_000) as device:
        device.column_delay = 0
        grid = [[0] * 9 for _ in range(34)]
        grid[0][0] = 128  # one LED at half brightness
        device.set_grayscale(grid)
        with pytest.raises(ProtocolError):
            device.set_grayscale([[0] * 9])  # wrong row count
        with pytest.raises(ProtocolError):
            device.set_grayscale([[300] * 9 for _ in range(34)])  # out of byte range
    expected = [b"\x32\xac\x07\x00\x80" + b"\x00" * 33]
    expected += [b"\x32\xac\x07" + bytes((x,)) + b"\x00" * 34 for x in range(1, 9)]
    expected += [b"\x32\xac\x08"]
    assert transport.writes == expected


def test_getters_read_documented_response_sizes():
    transport = MockTransport(responses=[b"\x2a", b"\x01\x02\x03"])
    with open_device(transport=transport) as device:
        assert device.get_brightness() == 42
        assert str(device.get_firmware_version()) == "1.2.3"


def test_dangerous_calls_require_confirmation():
    transport = MockTransport()
    with open_device(transport=transport) as device:
        with pytest.raises(UnsupportedCapability):
            device.panic()
        device.panic(confirm=True)
    assert transport.writes == [b"\x32\xac\x05"]


def test_disconnect_is_typed():
    transport = MockTransport()
    device = open_device(transport=transport)
    transport.disconnect()
    with pytest.raises(DeviceDisconnected):
        device.set_brightness(1)
