"""Debugging CLI for Framework 16 LED Matrix modules."""
from __future__ import annotations

import argparse
import sys
from importlib import resources
from pathlib import Path
from typing import Optional, Sequence

from ..canvas import Canvas
from ..device import DeviceInfo, list_devices, open_device
from ..exceptions import LedMatrixError
from ..font import Font
from ..geometry import FW16_LED_MATRIX, MatrixGeometry
from ..image import ImagePipeline
from ..transport import FRAMEWORK_VID, LED_MATRIX_PID, MockTransport


def _int(value: str) -> int:
    return int(value, 0)


def _hex(value: str) -> bytes:
    try:
        return bytes.fromhex(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("payload must be hex bytes, e.g. 00 ff a1") from exc


def _add_target_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--port", help="explicit serial port (for example COM3 or /dev/ttyACM0)")
    parser.add_argument("--serial", help="Framework device serial number")
    parser.add_argument("--dry-run", action="store_true", help="record commands without opening hardware")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ledmatrix", description="Framework 16 LED Matrix SDK CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list discovered LED Matrix serial devices")

    info = sub.add_parser("info", help="show device metadata and firmware version")
    _add_target_arguments(info)

    brightness = sub.add_parser("brightness", help="set global brightness (0..100 percent)")
    _add_target_arguments(brightness)
    brightness.add_argument("value", type=int)

    pixel = sub.add_parser("pixel", help="show a single pixel on a cleared frame")
    _add_target_arguments(pixel)
    pixel.add_argument("x", type=int)
    pixel.add_argument("y", type=int)

    rect = sub.add_parser("rect", help="show a filled rectangle on a cleared frame")
    _add_target_arguments(rect)
    rect.add_argument("x", type=int)
    rect.add_argument("y", type=int)
    rect.add_argument("width", type=int)
    rect.add_argument("height", type=int)

    clear = sub.add_parser("clear", help="clear the display")
    _add_target_arguments(clear)

    image = sub.add_parser("image", help="load, resize, dither, and display an image")
    _add_target_arguments(image)
    image.add_argument("path")
    image.add_argument("--dither", default="threshold", choices=["none", "threshold", "bayer2x2", "bayer4x4", "floyd_steinberg"])
    image.add_argument("--resize", default="nearest", choices=["nearest", "bilinear", "area"])

    text = sub.add_parser("text", help="render text on a cleared frame")
    _add_target_arguments(text)
    text.add_argument("text")
    text.add_argument("--font", default="5x7", choices=["tom-thumb", "4x6", "5x7", "3x5"])
    text.add_argument("--x", type=int, default=0)
    text.add_argument("--y", type=int, default=0)
    text.add_argument("--rotate", type=int, default=0, choices=[0, 90, 180, 270])
    text.add_argument("--preview", action="store_true", help="print the 9x34 software frame before sending")

    orientation = sub.add_parser("orientation-test", help="show an asymmetric orientation diagnostic frame")
    _add_target_arguments(orientation)
    orientation.add_argument("--preview", action="store_true", help="print the 9x34 software frame before sending")

    raw = sub.add_parser("raw", help="send a raw opcode and hex payload")
    _add_target_arguments(raw)
    raw.add_argument("opcode", type=_int)
    raw.add_argument("payload", type=_hex, nargs="?", default=b"")
    raw.add_argument("--response-bytes", type=int, default=0)

    system = sub.add_parser("system", help="print or install the optional Linux udev rule")
    system_sub = system.add_subparsers(dest="system_command", required=True)
    system_sub.add_parser("udev-rule", help="print the packaged udev rule")
    install = system_sub.add_parser("install-udev", help="copy the udev rule to a chosen writable path")
    install.add_argument("--target", required=True, help="destination file; use sudo outside this tool if needed")

    return parser


def _open(args: argparse.Namespace):
    if args.dry_run:
        mock = MockTransport(responses=[bytes((0, 0, 0))])
        info = DeviceInfo(
            path="mock://cli", vid=FRAMEWORK_VID, pid=LED_MATRIX_PID, serial="DRYRUN", product="LED_Matrix"
        )
        return open_device(transport=mock, info=info), mock
    return open_device(port=args.port, serial=args.serial), None


def _print_dry_run(mock: Optional[MockTransport]) -> None:
    if mock is None:
        return
    for index, write in enumerate(mock.writes, start=1):
        print("dry-run write %d: %s" % (index, write.hex(" ")))


def _rule_text() -> str:
    resource = resources.files("ledmatrix.data").joinpath("50-framework-inputmodule.rules")
    return resource.read_text(encoding="utf-8")


def _print_preview(canvas: Canvas) -> None:
    for row in canvas.to_rows():
        print(row)


def _logical_canvas(rotation: int) -> Canvas:
    if rotation in (90, 270):
        return Canvas(MatrixGeometry(width=FW16_LED_MATRIX.height, height=FW16_LED_MATRIX.width))
    return Canvas()


def _rotate_canvas(canvas: Canvas, rotation: int) -> Canvas:
    rotation %= 360
    if rotation == 0:
        return canvas

    output = Canvas()
    if rotation == 90:
        for y in range(canvas.height):
            for x in range(canvas.width):
                output.set_pixel(output.width - 1 - y, x, canvas.get_pixel(x, y))
    elif rotation == 180:
        for y in range(canvas.height):
            for x in range(canvas.width):
                output.set_pixel(output.width - 1 - x, output.height - 1 - y, canvas.get_pixel(x, y))
    elif rotation == 270:
        for y in range(canvas.height):
            for x in range(canvas.width):
                output.set_pixel(y, output.height - 1 - x, canvas.get_pixel(x, y))
    else:
        raise ValueError("rotation must be one of 0, 90, 180, or 270")
    return output


def _orientation_test_canvas() -> Canvas:
    canvas = Canvas()
    canvas.draw_rect(0, 0, canvas.width, canvas.height)
    canvas.draw_line(0, 0, canvas.width - 1, canvas.height - 1)
    canvas.set_pixel(0, 0, True)
    canvas.set_pixel(canvas.width - 1, 0, True)
    canvas.set_pixel(0, canvas.height - 1, True)
    canvas.fill_rect(canvas.width - 2, canvas.height - 3, 2, 3, True)
    Font.load("3x5").draw_text(canvas, 1, 2, "HI")
    return canvas


def run(args: argparse.Namespace) -> int:
    try:
        if args.command == "list":
            devices = list_devices()
            if not devices:
                print("No Framework LED Matrix serial devices found.")
                return 0
            for index, info in enumerate(devices):
                vid = "%04x" % info.vid if info.vid is not None else "????"
                pid = "%04x" % info.pid if info.pid is not None else "????"
                serial = info.serial or ""
                print("%d: %s vid=%s pid=%s serial=%s" % (index, info.path, vid, pid, serial))
            return 0

        if args.command == "system":
            if args.system_command == "udev-rule":
                print(_rule_text(), end="")
                return 0
            if args.system_command == "install-udev":
                Path(args.target).write_text(_rule_text(), encoding="utf-8")
                print("installed udev rule to %s" % args.target)
                return 0

        device, mock = _open(args)
        with device:
            if args.command == "info":
                details = device.get_device_info()
                print("path: %s" % details.info.path)
                print("serial: %s" % (details.info.serial or ""))
                print("firmware: %s" % details.firmware)
                print("geometry: %dx%d" % (details.geometry.width, details.geometry.height))
                print("frame bytes: %d" % details.geometry.frame_bytes)
                print("vblank ack: %s" % details.capabilities.vblank_ack)
            elif args.command == "clear":
                device.show_frame(Canvas().clear())
            elif args.command == "pixel":
                device.show_frame(Canvas().clear().set_pixel(args.x, args.y, True))
            elif args.command == "rect":
                device.show_frame(Canvas().clear().fill_rect(args.x, args.y, args.width, args.height, True))
            elif args.command == "brightness":
                device.set_brightness(args.value)
            elif args.command == "image":
                from PIL import Image

                with Image.open(args.path) as source:
                    frame = ImagePipeline(dither=args.dither, resize=args.resize).process(source)
                device.show_frame(frame)
            elif args.command == "text":
                canvas = _logical_canvas(args.rotate).clear()
                Font.load(args.font).draw_text(canvas, args.x, args.y, args.text)
                canvas = _rotate_canvas(canvas, args.rotate)
                if args.preview:
                    _print_preview(canvas)
                device.show_frame(canvas)
            elif args.command == "orientation-test":
                canvas = _orientation_test_canvas()
                if args.preview:
                    _print_preview(canvas)
                device.show_frame(canvas)
            elif args.command == "raw":
                response = device.raw_command(args.opcode, args.payload, response_bytes=args.response_bytes)
                if response:
                    print(response.hex(" "))
            else:
                raise LedMatrixError("unknown command %r" % args.command)
        _print_dry_run(mock)
        return 0
    except LedMatrixError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except LedMatrixError as exc:
        parser.exit(2, "ledmatrix: error: %s\n" % exc)
    except ValueError as exc:
        parser.exit(2, "ledmatrix: error: %s\n" % exc)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
