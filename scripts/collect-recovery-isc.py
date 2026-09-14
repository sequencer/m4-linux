import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import re
import subprocess


def main():
    parser = argparse.ArgumentParser(description="Read-only M4 Recovery iSC acquisition to the M1 host")
    parser.add_argument("--host", default="root@172.25.27.133")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("select a fresh output directory")
    ssh = ["ssh", "-i", str(Path.home() / ".ssh/id_ed25519"),
           "-o", "UserKnownHostsFile=" + str(Path.home() / ".ssh/m4-recovery-known-hosts"),
           "-o", "StrictHostKeyChecking=yes", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", args.host]

    def read_remote(command):
        return subprocess.check_output(ssh + [command], timeout=60)

    model = read_remote("sysctl -n hw.model").decode().strip()
    if model != "Mac16,12":
        parser.error("target model differs from the M4 Air")
    chosen_bytes = read_remote("ioreg -p IODeviceTree -n chosen -r -l -a")
    chosen_nodes = [node for node in plistlib.loads(chosen_bytes)
                    if node.get("IORegistryEntryName") == "chosen"]
    if len(chosen_nodes) != 1:
        parser.error("expected one chosen device-tree node")
    chosen = chosen_nodes[0]
    ecid = int.from_bytes(chosen.get("unique-chip-id", b""), "little")
    chip = int.from_bytes(chosen.get("chip-id", b""), "little")
    if ecid != 0xA10A426B9001C or chip != 0x8132:
        parser.error("target ECID or chip differs from the guarded M4")
    listing_bytes = read_remote("diskutil list -plist")
    listing = plistlib.loads(listing_bytes)
    candidates = []
    for disk in listing.get("AllDisksAndPartitions", []):
        for partition in disk.get("Partitions", []):
            if partition.get("Content") == "Apple_APFS_ISC":
                candidates.append(partition)
    if len(candidates) != 1:
        parser.error("expected exactly one physical iSC partition")
    device = candidates[0]["DeviceIdentifier"]
    if not re.fullmatch(r"disk[0-9]+s[0-9]+", device):
        parser.error("unexpected partition identifier")
    info_bytes = read_remote("diskutil info -plist " + device)
    info = plistlib.loads(info_bytes)
    size = info.get("TotalSize", 0)
    if (info.get("Content") != "Apple_APFS_ISC" or info.get("WholeDisk") is not False
            or info.get("DeviceIdentifier") != device
            or info.get("Internal") is not True or not 64 * 1024 ** 2 <= size <= 1024 ** 3):
        parser.error("partition identity or size differs from the guarded iSC acquisition")
    args.output.mkdir(parents=True, mode=0o700)
    (args.output / "chosen.plist").write_bytes(chosen_bytes)
    (args.output / "disk-list.plist").write_bytes(listing_bytes)
    (args.output / "isc-info.plist").write_bytes(info_bytes)
    destination = args.output / "isc.raw"
    with destination.open("xb") as image, (args.output / "dd.log").open("wb") as errors:
        process = subprocess.Popen(ssh + ["dd if=/dev/r" + device + " bs=1048576"],
                                   stdout=image, stderr=errors)
        try:
            result = process.wait(timeout=300)
        except BaseException:
            process.kill()
            process.wait()
            raise
    if result or destination.stat().st_size != size:
        raise ValueError("iSC read failed or image length differs from partition size")
    with destination.open("rb") as image:
        digest = hashlib.file_digest(image, "sha256").hexdigest()
        image.seek(32)
        if image.read(4) != b"NXSB":
            raise ValueError("acquired partition lacks the APFS container superblock")
    report = {"model": model, "ecid": hex(ecid), "chip": hex(chip),
              "device": device, "size": size, "sha256": digest,
              "remote_operation": "dd if=physical iSC partition; no remote output device",
              "original_user_data_read": False, "remote_disk_writes_requested": False,
              "live_container_acquisition": True, "offline_checkpoint_validation_required": True,
              "guest_use_verified": False}
    (args.output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
