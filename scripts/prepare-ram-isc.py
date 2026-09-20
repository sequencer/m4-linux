import argparse
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import struct
import uuid
import zlib

inspect_image = runpy.run_path(str(Path(__file__).with_name("inspect-recovery-input.py")))["inspect_image"]


def make_gpt(root_size, isc_size, resources_size=0):
    alignment = 1024 * 1024
    if min(root_size, isc_size) <= 0 or root_size % 4096 or isc_size % 4096:
        raise ValueError("APFS partition sizes must be positive complete blocks")
    root_offset = alignment
    isc_offset = (root_offset + root_size + alignment - 1) // alignment * alignment
    resources_offset = isc_offset + isc_size
    suffix_offset = resources_offset + resources_size
    total_size = (suffix_offset + 33 * 512 + 4095) // 4096 * 4096
    last_lba = total_size // 512 - 1
    entries = bytearray(16384)
    namespace = uuid.UUID("c51b3477-f34c-4b22-9e26-c576f3472fd3")
    partitions = [
        ("7c3457ef-0000-11aa-aa11-00306543ecac", root_offset, root_size, "Recovery BaseSystem"),
        ("69646961-6700-11aa-aa11-00306543ecac", isc_offset, isc_size, "RAM iBootSystemContainer"),
    ]
    if resources_size:
        partitions.append(("ebd0a0a2-b9e5-4433-87c0-68b6b72699c7", resources_offset,
                           resources_size, "Guest resources"))
    for index, (type_guid, offset, size, name) in enumerate(partitions):
        entry = struct.pack("<16s16sQQQ72s", uuid.UUID(type_guid).bytes_le,
                            uuid.uuid5(namespace, name).bytes_le, offset // 512,
                            (offset + size) // 512 - 1, 0, name.encode("utf-16-le"))
        entries[index * 128:(index + 1) * 128] = entry
    entries_crc = zlib.crc32(entries)

    def header(current, alternate, table_lba):
        packed = bytearray(struct.pack("<8sIIIIQQQQ16sQIII", b"EFI PART", 0x10000,
                                      92, 0, 0, current, alternate, 34, last_lba - 33,
                                      uuid.uuid5(namespace, "M4 RAM media").bytes_le,
                                      table_lba, 128, 128, entries_crc))
        struct.pack_into("<I", packed, 16, zlib.crc32(packed))
        return bytes(packed).ljust(512, b"\0")

    prefix = bytearray(root_offset)
    struct.pack_into("<B3sB3sII", prefix, 446, 0, b"\0\x02\0", 0xee,
                     b"\xff\xff\xff", 1, min(last_lba, 0xffffffff))
    prefix[510:512] = b"\x55\xaa"
    prefix[512:1024] = header(1, last_lba, 2)
    prefix[1024:1024 + len(entries)] = entries
    suffix = bytearray(total_size - suffix_offset)
    table_offset = (last_lba - 32) * 512 - suffix_offset
    suffix[table_offset:table_offset + len(entries)] = entries
    suffix[-512:] = header(last_lba, 1, last_lba - 32)
    return bytes(prefix), bytes(suffix), {
        "root_offset": root_offset, "root_size": root_size,
        "isc_offset": isc_offset, "isc_size": isc_size,
        "resources_offset": resources_offset, "resources_size": resources_size,
        "suffix_offset": suffix_offset, "total_size": total_size,
        "logical_sector_size": 512,
        "gap_size": isc_offset - root_offset - root_size,
    }


def check_source(path, expected):
    with path.open("rb") as image:
        digest = hashlib.file_digest(image, "sha256").hexdigest()
        image.seek(32)
        if digest != expected or image.read(4) != b"NXSB":
            raise ValueError("source SHA-256 or APFS magic mismatch: " + str(path))


def main():
    parser = argparse.ArgumentParser(description="Host-only GPT wrapper for pinned Recovery and acquired iSC")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--isc", type=Path, required=True)
    parser.add_argument("--isc-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("choose a fresh output directory")
    manifest = json.loads(args.isc_manifest.read_text())
    if (manifest.get("ecid") != "0xa10a426b9001c" or manifest.get("chip") != "0x8132"
            or manifest.get("size") != args.isc.stat().st_size):
        parser.error("iSC manifest identity or size mismatch")
    check_source(args.root, "bda0c53dfb35ceffe371c1708b2443b9d55f60a70bbcbbcf6470bade2b552e9a")
    check_source(args.isc, manifest["sha256"])
    prefix, suffix, layout = make_gpt(args.root.stat().st_size, args.isc.stat().st_size)
    args.output.mkdir(parents=True, mode=0o700)
    (args.output / "prefix.bin").write_bytes(prefix)
    (args.output / "suffix.bin").write_bytes(suffix)
    destination = args.output / "ram-media.img"
    with destination.open("xb") as image:
        image.truncate(layout["total_size"])
        image.write(prefix)
        for source, offset in [(args.root, layout["root_offset"]), (args.isc, layout["isc_offset"])]:
            image.seek(offset)
            with source.open("rb") as partition:
                shutil.copyfileobj(partition, image, 16 * 1024 * 1024)
        image.seek(layout["suffix_offset"])
        image.write(suffix)
    inspected = inspect_image(destination)
    report = {"layout": layout, "inspection": inspected, "isc_sha256": manifest["sha256"],
              "live_isc_atomic_consistency_verified": False, "guest_use_verified": False,
              "remote_disk_writes_requested": False,
              "gpt_specification": "https://uefi.org/specs/UEFI/2.10/05_GUID_Partition_Table_Format.html"}
    (args.output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
