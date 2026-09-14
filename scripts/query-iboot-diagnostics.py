import argparse
import ctypes
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess


class DeviceInfo(ctypes.Structure):
    _fields_ = [("cpid", ctypes.c_uint), ("cprv", ctypes.c_uint),
                ("cpfm", ctypes.c_uint), ("scep", ctypes.c_uint),
                ("bdid", ctypes.c_uint), ("ecid", ctypes.c_uint64)]


class Event(ctypes.Structure):
    _fields_ = [("size", ctypes.c_int), ("data", ctypes.c_void_p),
                ("progress", ctypes.c_double), ("type", ctypes.c_int)]


def main():
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Query pinned M4 iBoot values; optional explicit auto-boot repair and existing-system boot")
    parser.add_argument("--tool", type=Path, default=root / "results/dfu-tools/bin/irecovery")
    parser.add_argument("--output", type=Path, required=True)
    repair = parser.add_mutually_exclusive_group()
    repair.add_argument("--restore-autoboot-and-fsboot", action="store_true")
    repair.add_argument("--restore-autoboot-only", action="store_true")
    repair.add_argument("--request-fallback-recovery", action="store_true")
    parser.add_argument("--no-console", action="store_true")
    parser.add_argument("--persistent-fallback", action="store_true")
    args = parser.parse_args()
    if args.persistent_fallback and not args.request_fallback_recovery:
        parser.error("--persistent-fallback requires --request-fallback-recovery")
    if args.output.exists():
        parser.error("choose a fresh output directory")
    dependencies = subprocess.check_output(["ldd", str(args.tool)], text=True)
    match = re.search(r"libirecovery[^ ]* => (/nix/store/[^ ]+)", dependencies)
    if not match:
        raise ValueError("Nix libirecovery dependency not found")
    library = ctypes.CDLL(match[1])
    pointer = ctypes.c_void_p
    library.irecv_open_with_ecid.argtypes = [ctypes.POINTER(pointer), ctypes.c_uint64]
    library.irecv_get_device_info.argtypes = [pointer]
    library.irecv_get_device_info.restype = ctypes.POINTER(DeviceInfo)
    library.irecv_get_mode.argtypes = [pointer, ctypes.POINTER(ctypes.c_int)]
    library.irecv_usb_control_transfer.argtypes = [pointer, ctypes.c_uint8, ctypes.c_uint8,
                                                 ctypes.c_uint16, ctypes.c_uint16, pointer,
                                                 ctypes.c_uint16, ctypes.c_uint]
    library.irecv_receive.argtypes = [pointer]
    library.irecv_close.argtypes = [pointer]
    callback_type = ctypes.CFUNCTYPE(ctypes.c_int, pointer, ctypes.POINTER(Event))
    library.irecv_event_subscribe.argtypes = [pointer, ctypes.c_int, callback_type, pointer]
    client = pointer()
    result = library.irecv_open_with_ecid(ctypes.byref(client), 0xA10A426B9001C)
    if result:
        raise ValueError("irecv_open_with_ecid failed: " + str(result))
    try:
        info = library.irecv_get_device_info(client)
        if not info or (info.contents.cpid, info.contents.bdid, info.contents.ecid) != (0x8132, 0x2c, 0xA10A426B9001C):
            raise ValueError("target identity mismatch")
        mode = ctypes.c_int()
        result = library.irecv_get_mode(client, ctypes.byref(mode))
        if result or not 0x1280 <= mode.value <= 0x1283:
            raise ValueError("target is not firmware Recovery")
        args.output.mkdir(parents=True, mode=0o700)
        report = {"time": datetime.now(timezone.utc).isoformat(), "mode": hex(mode.value),
                  "hardware_identity_verified": True, "boot_or_write_commands_sent": False,
                  "values": {}}
        console = bytearray()

        @callback_type
        def receive(client_pointer, event_pointer):
            event = event_pointer.contents
            if event.type == 1 and event.data and 0 < event.size <= 65536 and len(console) + event.size <= 1024 ** 2:
                console.extend(ctypes.string_at(event.data, event.size))
            return 0

        result = library.irecv_event_subscribe(client, 1, receive, None)
        if result:
            raise ValueError("irecv_event_subscribe failed: " + str(result))
        for key in ("boot-stage", "build-version", "auto-boot", "boot-command",
                    "iboot-failure-reason", "iboot-failure-reason-str", "iboot-failure-volume",
                    "boot-volume", "boot-device", "failboot-breadcrumbs", "recovery-reason",
                    "panicmedic-engaged", "panicmedic-panic-count", "panicmedic-timestamps",
                    "panicmedic-auxkc-present",
                    "recovery-boot-mode", "one-time-boot-command", "upgrade-fallback-boot-command",
                    "is-tethered", "boot-args", "recovery-mode", "saved-debug-info"):
            command = ("getenv " + key).encode() + b"\0"
            command_buffer = ctypes.create_string_buffer(command)
            sent = library.irecv_usb_control_transfer(client, 0x40, 0, 0, 0, command_buffer, len(command), 2000)
            response = ctypes.create_string_buffer(256)
            received = library.irecv_usb_control_transfer(client, 0xc0, 0, 0, 0, response, 255, 2000) if sent == len(command) else None
            value = response.raw[:received].split(b"\0", 1)[0].decode(errors="replace") if received is not None and received >= 0 else None
            report["values"][key] = {"command_bytes": len(command), "send_result": sent,
                                     "receive_result": received, "value": value}
        if args.restore_autoboot_and_fsboot or args.restore_autoboot_only or args.request_fallback_recovery:
            if args.request_fallback_recovery:
                failure_volume = report["values"]["iboot-failure-volume"]["value"] or ""
                if (report["values"]["boot-stage"]["value"] != "1"
                        or report["values"]["auto-boot"]["value"] != "true"
                        or report["values"]["boot-command"]["value"] != "recover-system"
                        or report["values"]["recovery-boot-mode"]["value"] != "panicmedic"
                        or not failure_volume.endswith(":DE77783E-D9C0-4695-8BE1-EBE0D3015748")):
                    raise ValueError("refusing fallback request without pinned Bootstrap panicmedic state")
            elif (report["values"]["boot-stage"]["value"] != "1"
                    or report["values"]["boot-command"]["value"] not in (("fsboot", "recover-system") if args.restore_autoboot_only else ("fsboot",))
                    or report["values"]["auto-boot"]["value"] not in ("false", "true")):
                raise ValueError("refusing boot repair without valid Stage1 auto-boot/fsboot state")
            report["boot_or_write_commands_sent"] = True
            report["repair_commands"] = []
            if args.request_fallback_recovery:
                fallback_key = "boot-command" if args.persistent_fallback else "one-time-boot-command"
                commands = ("setenv " + fallback_key + " recover-fallback", "saveenv", "reboot")
            else:
                commands = ("setenv auto-boot true", "saveenv") if args.restore_autoboot_only else ("setenv auto-boot true", "saveenv", "fsboot")
            for command_text in commands:
                command = command_text.encode() + b"\0"
                command_buffer = ctypes.create_string_buffer(command)
                request = 1 if command_text == "reboot" else 0
                sent = library.irecv_usb_control_transfer(client, 0x40, request, 0, 0, command_buffer, len(command), 2000)
                report["repair_commands"].append({"command": command_text, "send_result": sent,
                                                   "expected_bytes": len(command)})
                (args.output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
                if sent != len(command):
                    report["repair_transport_error"] = command_text
                    break
                if command_text == "saveenv":
                    query_key = fallback_key if args.request_fallback_recovery else "auto-boot"
                    expected_value = "recover-fallback" if args.request_fallback_recovery else "true"
                    query_command = ("getenv " + query_key).encode() + b"\0"
                    query_buffer = ctypes.create_string_buffer(query_command)
                    query_sent = library.irecv_usb_control_transfer(client, 0x40, 0, 0, 0, query_buffer, len(query_command), 2000)
                    response = ctypes.create_string_buffer(256)
                    query_received = library.irecv_usb_control_transfer(client, 0xc0, 0, 0, 0, response, 255, 2000) if query_sent == len(query_command) else None
                    query_value = response.raw[:query_received].split(b"\0", 1)[0].decode(errors="replace") if query_received is not None and query_received >= 0 else None
                    report["repair_readback"] = {"key": query_key, "send_result": query_sent,
                                                   "receive_result": query_received, "value": query_value}
                    if query_value != expected_value:
                        report["repair_transport_error"] = query_key + " readback"
                        break
        report["final_receive_status"] = None if args.no_console else library.irecv_receive(client)
        (args.output / "console.txt").write_bytes(console)
        (args.output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        if report.get("repair_transport_error"):
            raise ValueError("boot repair command transport failed: " + report["repair_transport_error"])
    finally:
        library.irecv_close(client)


if __name__ == "__main__":
    main()
