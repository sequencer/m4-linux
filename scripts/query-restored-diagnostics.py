import argparse
import ctypes
import json
from pathlib import Path
import plistlib
import re
import subprocess


def main():
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Read-only HardwareInfo/SavedDebugInfo from Apple restored; never StartRestore")
    parser.add_argument("--tool", type=Path, default=root / "results/firmware-revive-tools/bin/idevicerestore")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("choose a fresh output directory")
    dependencies = subprocess.check_output(["ldd", str(args.tool)], text=True)

    def library(name):
        match = re.search(re.escape(name) + r"[^ ]* => (/nix/store/[^ ]+)", dependencies)
        if not match:
            raise ValueError("Nix library dependency not found: " + name)
        return ctypes.CDLL(match[1])

    mobile = library("libimobiledevice-1.0.so")
    plist = library("libplist-2.0.so")
    pointer = ctypes.c_void_p
    mobile.idevice_new.argtypes = [ctypes.POINTER(pointer), ctypes.c_char_p]
    mobile.idevice_free.argtypes = [pointer]
    mobile.restored_client_new.argtypes = [pointer, ctypes.POINTER(pointer), ctypes.c_char_p]
    mobile.restored_client_free.argtypes = [pointer]
    mobile.restored_query_type.argtypes = [pointer, ctypes.POINTER(pointer), ctypes.POINTER(ctypes.c_uint64)]
    mobile.restored_query_value.argtypes = [pointer, ctypes.c_char_p, ctypes.POINTER(pointer)]
    plist.plist_to_xml.argtypes = [pointer, ctypes.POINTER(pointer), ctypes.POINTER(ctypes.c_uint32)]
    plist.plist_free.argtypes = [pointer]
    plist.plist_mem_free.argtypes = [pointer]
    device = pointer()
    client = pointer()

    def check(result, operation):
        if result:
            raise ValueError(operation + " failed: " + str(result))

    try:
        check(mobile.idevice_new(ctypes.byref(device), b"00008132-000A10A426B9001C"), "idevice_new")
        check(mobile.restored_client_new(device, ctypes.byref(client), b"m4-readonly-diagnostics"), "restored_client_new")
        service_type = pointer()
        version = ctypes.c_uint64()
        check(mobile.restored_query_type(client, ctypes.byref(service_type), ctypes.byref(version)), "restored_query_type")
        name = ctypes.string_at(service_type).decode()
        if name != "com.apple.mobile.restored":
            raise ValueError("unexpected service: " + name)

        def query(key):
            node = pointer()
            check(mobile.restored_query_value(client, key.encode(), ctypes.byref(node)), key)
            xml = pointer()
            length = ctypes.c_uint32()
            try:
                plist.plist_to_xml(node, ctypes.byref(xml), ctypes.byref(length))
                if not xml or not 0 < length.value <= 64 * 1024 ** 2:
                    raise ValueError("invalid diagnostic plist size")
                return ctypes.string_at(xml, length.value)
            finally:
                if xml:
                    plist.plist_mem_free(xml)
                plist.plist_free(node)

        hardware_bytes = query("HardwareInfo")
        hardware = plistlib.loads(hardware_bytes)
        if (hardware.get("UniqueChipID") != 0xA10A426B9001C
                or hardware.get("ChipID") != 0x8132 or hardware.get("BoardID") != 0x2c):
            raise ValueError("target hardware identity mismatch")
        args.output.mkdir(parents=True, mode=0o700)
        (args.output / "HardwareInfo.plist").write_bytes(hardware_bytes)
        saved = query("SavedDebugInfo")
        (args.output / "SavedDebugInfo.plist").write_bytes(saved)
        report = {"service": name, "version": version.value, "hardware_identity_verified": True,
                  "start_restore_sent": False, "disk_writes_requested": False,
                  "saved_debug_keys": list(plistlib.loads(saved))}
        (args.output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    finally:
        if client:
            mobile.restored_client_free(client)
        if device:
            mobile.idevice_free(device)


if __name__ == "__main__":
    main()
