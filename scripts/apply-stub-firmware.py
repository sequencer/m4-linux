import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import tarfile


GROUP = "DE77783E-D9C0-4695-8BE1-EBE0D3015748"
CONTAINER = "909274B1-CCC4-47DC-8314-9F00F7AF4885"


def diskutil(*arguments):
    return plistlib.loads(subprocess.check_output(["diskutil", *arguments, "-plist"]))


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Stage and atomically select pinned 25G83 resources only in the existing experimental stub")
    parser.add_argument("archive", type=Path)
    parser.add_argument("--archive-sha256", required=True)
    args = parser.parse_args()
    if digest(args.archive) != args.archive_sha256:
        parser.error("update archive SHA-256 mismatch")
    container = next(item for item in diskutil("apfs", "list")["Containers"] if item["APFSContainerUUID"] == CONTAINER)
    if container["CapacityCeiling"] != 3999997952:
        raise ValueError("experimental container size changed")
    groups = diskutil("apfs", "listVolumeGroups", container["ContainerReference"])["Containers"][0]["VolumeGroups"]
    if len(groups) != 1 or groups[0]["APFSVolumeGroupUUID"] != GROUP:
        raise ValueError("experimental volume group mismatch")
    policy = subprocess.check_output(["bputil", "-d", "-v", GROUP], text=True)
    if "one true recoveryOS" not in policy or ": Paired" not in policy or "Valid" not in policy:
        raise ValueError("not in the experimental stub's paired 1TR")
    roles = {tuple(volume["Roles"]): volume for volume in container["Volumes"]}
    mounts = {}
    for role in ("System", "Preboot", "Recovery"):
        volume = roles[(role,)]
        subprocess.run(["diskutil", "mount", volume["DeviceIdentifier"]], check=True)
        info = plistlib.loads(subprocess.check_output(["diskutil", "info", "-plist", volume["DeviceIdentifier"]]))
        if info["APFSContainerReference"] != container["ContainerReference"]:
            raise ValueError("mount belongs to another container")
        mounts[role] = Path(info["MountPoint"])
    system = mounts["System"]
    preboot = mounts["Preboot"] / GROUP
    recovery = mounts["Recovery"] / GROUP
    restore = preboot / "restore"
    old_manifest = plistlib.loads((restore / "BuildManifest.plist").read_bytes())
    if old_manifest["ProductBuildVersion"] != "25E253":
        raise ValueError("current restore is not the backed-up 25E253 build")
    stage = preboot / "update-25G83-staging"
    recovery_stage = recovery / "update-25G83-staging"
    old_restore = preboot / "restore-25E253-before-25G83"
    old_recovery = recovery / "usr/standalone/firmware/arm64eBaseSystem-25E253.dmg"
    recovery_image = recovery / "usr/standalone/firmware/arm64eBaseSystem.dmg"
    cached_links = []
    for cached_image in (recovery / "boot").rglob("arm64eBaseSystem.dmg"):
        if cached_image.is_symlink() and cached_image.resolve() == recovery_image:
            backup_link = cached_image.with_name(cached_image.name + ".before-25G83")
            temporary_link = cached_image.with_name(cached_image.name + ".update-staging")
            if os.path.lexists(backup_link) or os.path.lexists(temporary_link):
                raise ValueError("cached Recovery link update paths already exist")
            cached_links.append((cached_image, backup_link, temporary_link))
    if any(path.exists() for path in (stage, recovery_stage, old_restore, old_recovery)):
        raise ValueError("update staging/backup paths already exist; inspect before resuming")
    with tarfile.open(args.archive) as archive:
        plan = json.load(archive.extractfile("update-plan.json"))
        if (plan["build"], plan["target_group"], plan["target_container"]) != ("25G83", GROUP, CONTAINER):
            raise ValueError("update plan identity mismatch")
        regular = [member for member in archive.getmembers() if not member.name.startswith("recovery/")]
        recovery_members = [member for member in archive.getmembers() if member.name.startswith("recovery/")]
        stage.mkdir()
        recovery_stage.mkdir()
        archive.extractall(stage, members=regular, filter="data")
        archive.extractall(recovery_stage, members=recovery_members, filter="data")
    for line in (stage / "SHA256SUMS").read_text().splitlines():
        expected, relative = line.split("  ", 1)
        path = (recovery_stage if relative.startswith("recovery/") else stage) / relative
        if digest(path) != expected:
            raise ValueError(f"staged resource hash mismatch: {relative}")
    brain = stage / "restore/Bootability/BootabilityBrain.framework/BootabilityBrain"
    if not brain.is_file() or not brain.is_symlink():
        raise ValueError("Bootability framework symlinks are incomplete")
    subprocess.run(["mount", "-uw", str(system)], check=True)
    for source in (stage / "system").rglob("*"):
        if source.is_file():
            relative = source.relative_to(stage / "system")
            destination = system / relative
            if destination.exists():
                shutil.copy2(destination, destination.with_name(destination.name + ".before-25G83"))
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    payload = system / "Finish Installation.app/Contents/Resources/boot.bin"
    shutil.copy2(payload, payload.with_name("boot-25E253-original.bin"))
    shutil.copy2(stage / "boot.bin", payload)
    restore.rename(old_restore)
    (stage / "restore").rename(restore)
    recovery_image.rename(old_recovery)
    for cached_image, backup_link, temporary_link in cached_links:
        backup_link.symlink_to(os.readlink(cached_image))
        temporary_link.symlink_to(os.path.relpath(old_recovery, cached_image.parent))
        os.replace(temporary_link, cached_image)
        if cached_image.resolve() != old_recovery:
            raise ValueError("old cached Recovery image preservation failed")
    (recovery_stage / "recovery/arm64eBaseSystem.dmg").rename(recovery_image)
    link = system / "restore"
    if not link.is_symlink():
        raise ValueError("System restore path is not the expected symlink")
    link.unlink()
    link.symlink_to(restore)
    report = {"group": GROUP, "container": CONTAINER, "build": "25G83",
              "mounts": {role: str(path) for role, path in mounts.items()},
              "old_restore": str(old_restore), "old_recovery": str(old_recovery),
              "boot_payload_sha256": digest(payload), "recovery_sha256": digest(recovery_image),
              "resources_updated": True, "policy_updated": False, "boot_verified": False}
    (system / "m4-firmware-update.json").write_text(json.dumps(report, indent=2) + "\n")
    subprocess.run(["sync"], check=True)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
