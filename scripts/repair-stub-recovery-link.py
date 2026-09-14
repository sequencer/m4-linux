import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import subprocess


GROUP = "DE77783E-D9C0-4695-8BE1-EBE0D3015748"
RECOVERY = "CF0A4023-ED78-4C1E-A430-AA11457E1883"
CONTAINER = "909274B1-CCC4-47DC-8314-9F00F7AF4885"
NSIH = "661D9FC1712305E86740FA2432F17217CC70994EFD2D72080D448D48B711656FBED46A25579114134EDAD82ACA3D55B2"
OLD_SHA256 = "f73e5b13f77e1cea01f573fee958d559b011f72d13602bb5933224bb8abad783"
NEW_SHA256 = "eeda386b1fb66a313cadef26e3e7ee06643d4d5ea8b3330a411a118ac7d14ed3"


def disk_info(identifier):
    return plistlib.loads(subprocess.check_output(["diskutil", "info", "-plist", identifier]))


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Restore the old stub Recovery cache symlink to its matching preserved 25E253 image")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    info = disk_info(RECOVERY)
    if info["VolumeUUID"] != RECOVERY or not info.get("MountPoint"):
        raise ValueError("expected mounted stub Recovery UUID")
    container = disk_info(info["APFSContainerReference"])
    if container.get("DiskUUID") != CONTAINER or container.get("TotalSize") != 3999997952:
        raise ValueError("unexpected container UUID or size")
    policy = subprocess.check_output(["bputil", "-d", "-v", GROUP], text=True)
    if NSIH not in policy or "0xA10A426B9001C" not in policy:
        raise ValueError("unexpected current stub policy or device")
    group = Path(info["MountPoint"]) / GROUP
    firmware = group / "usr/standalone/firmware"
    old_image = firmware / "arm64eBaseSystem-25E253.dmg"
    new_image = firmware / "arm64eBaseSystem.dmg"
    link = group / "boot" / NSIH / "usr/standalone/firmware/arm64eBaseSystem.dmg"
    previous = "../../../../../usr/standalone/firmware/arm64eBaseSystem.dmg"
    replacement = "../../../../../usr/standalone/firmware/arm64eBaseSystem-25E253.dmg"
    if not link.is_symlink() or os.readlink(link) != previous or link.resolve() != new_image:
        raise ValueError("cache does not have the expected mismatched symlink")
    if digest(old_image) != OLD_SHA256 or digest(new_image) != NEW_SHA256:
        raise ValueError("preserved old image or staged new image hash mismatch")
    backup = link.with_name(link.name + ".before-root-hash-fix")
    temporary = link.with_name(link.name + ".repair-staging")
    if os.path.lexists(backup) or os.path.lexists(temporary):
        raise ValueError("repair paths exist; inspect before retry")
    report = {"recovery_uuid": RECOVERY, "container_uuid": CONTAINER,
              "group": GROUP, "nsih": NSIH, "link": str(link),
              "old_image_sha256": OLD_SHA256, "new_image_sha256": NEW_SHA256,
              "previous_target": previous, "replacement_target": replacement,
              "applied": False, "boot_verified": False, "policy_modified": False}
    if args.apply:
        subprocess.run(["mount", "-uw", info["MountPoint"]], check=True)
        backup.symlink_to(previous)
        temporary.symlink_to(replacement)
        os.replace(temporary, link)
        subprocess.run(["sync"], check=True)
        if os.readlink(link) != replacement or link.resolve() != old_image or digest(link) != OLD_SHA256:
            raise ValueError("link repair readback failed; inspect without reboot")
        subprocess.run(["diskutil", "unmount", RECOVERY], check=True)
        subprocess.run(["diskutil", "mount", "readOnly", RECOVERY], check=True)
        report["applied"] = True
        report["resolved_image"] = str(link.resolve())
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
