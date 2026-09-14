import argparse
import json
from pathlib import Path
import re
import struct
import uuid
import zlib


ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments/2026-09-13-sptm-macos/raw"


def inspect_image(path):
    size = path.stat().st_size
    if size < 1024:
        raise ValueError("image too small for header inspection")
    with path.open("rb") as image:
        first = image.read(512)
        header = image.read(512)
        result = {"size": size, "initial_apfs_magic": first[32:36] == b"NXSB", "gpt": None}
        if header[:8] != b"EFI PART":
            return result
        header_size, header_crc = struct.unpack_from("<II", header, 12)
        if not 92 <= header_size <= 512:
            raise ValueError("invalid GPT header size")
        checksum_header = bytearray(header[:header_size])
        checksum_header[16:20] = bytes(4)
        if zlib.crc32(checksum_header) != header_crc:
            raise ValueError("GPT header checksum mismatch")
        entry_lba, entry_count, entry_size, entries_crc = struct.unpack_from("<QIII", header, 72)
        table_size = entry_count * entry_size
        if entry_size < 128 or entry_size % 8 or not 0 < table_size <= 1024 * 1024:
            raise ValueError("unsupported GPT partition table size")
        if entry_lba * 512 + table_size > size:
            raise ValueError("GPT partition table outside image")
        image.seek(entry_lba * 512)
        entries = image.read(table_size)
        if zlib.crc32(entries) != entries_crc:
            raise ValueError("GPT partition table checksum mismatch")
        partitions = []
        for offset in range(0, table_size, entry_size):
            entry = entries[offset:offset + entry_size]
            if entry[:16] == bytes(16):
                continue
            first_lba, last_lba = struct.unpack_from("<QQ", entry, 32)
            if first_lba > last_lba or (last_lba + 1) * 512 > size:
                raise ValueError("GPT partition outside image")
            image.seek(first_lba * 512)
            superblock = image.read(4096)
            partitions.append({
                "type_guid": str(uuid.UUID(bytes_le=entry[:16])),
                "offset": first_lba * 512,
                "size": (last_lba - first_lba + 1) * 512,
                "offset_aligned_for_memdev": first_lba * 512 % 4096 == 0,
                "apfs_magic": superblock[32:36] == b"NXSB",
                "apfs_block_size": struct.unpack_from("<I", superblock, 36)[0] if superblock[32:36] == b"NXSB" else None,
                "apfs_block_count": struct.unpack_from("<Q", superblock, 40)[0] if superblock[32:36] == b"NXSB" else None,
            })
        result["gpt"] = {"header_crc_valid": True, "entries_crc_valid": True, "partitions": partitions}
        return result


def main():
    parser = argparse.ArgumentParser(description="Offline Recovery image and recorded guest-memory layout inspection; never connects to the target")
    parser.add_argument("--image", type=Path, default=RAW / "recovery-25E253.raw")
    parser.add_argument("--log", type=Path, default=RAW / "guest-attempt-2.txt")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        image = inspect_image(args.image)
        log = args.log.read_text()
        physical = re.search(r"^Physical memory: (0x[0-9a-f]+) \.\. (0x[0-9a-f]+)$", log, re.MULTILINE)
        ramdisk = re.search(r"^Starting Recovery XNU/SPTM guest, RAMDisk=(0x[0-9a-f]+), size=(\d+)$", log, re.MULTILINE)
        if physical is None or ramdisk is None:
            raise ValueError("recorded guest physical range or RAMDisk missing")
        start, end = (int(value, 16) for value in physical.groups())
        address, size = int(ramdisk[1], 16), int(ramdisk[2])
        if start >= end or size <= 0:
            raise ValueError("invalid recorded memory range")
        within_physmap = start <= address and address + size <= end
        result = {
            "image": str(args.image.relative_to(ROOT)) if args.image.is_relative_to(ROOT) else str(args.image),
            "log": str(args.log.relative_to(ROOT)) if args.log.is_relative_to(ROOT) else str(args.log),
            "image_layout": image,
            "guest_physical_range": [hex(start), hex(end)],
            "recorded_ramdisk_range": [hex(address), hex(address + size)],
            "recorded_size_matches_image": size == image["size"],
            "ramdisk_inside_hle_physmap": within_physmap,
            "requires_root_partition_review": image["gpt"] is not None,
            "guest_boot_verified": False,
        }
        rendered = json.dumps(result, indent=2)
        if args.output:
            args.output.write_text(rendered + "\n")
        print(rendered)
    except (OSError, ValueError, struct.error) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
