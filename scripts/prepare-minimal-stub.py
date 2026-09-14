import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import plistlib
import shutil
import subprocess


TARGET_UUID = "909274B1-CCC4-47DC-8314-9F00F7AF4885"
SOURCE_UUID = "B8663CA8-7F9F-4EF7-8947-75F71A14BDA9"
SOURCE = Path("/Volumes/Preboot") / SOURCE_UUID
TOOLS = Path("/tmp/m4-stub-tools")


def run(*command):
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def read_diskutil(*arguments):
    command = ["diskutil", "info", "-plist", *arguments[1:]] if arguments[0] == "info" else ["diskutil", *arguments, "-plist"]
    return plistlib.loads(subprocess.check_output(command))


def target():
    return next(container for container in read_diskutil("apfs", "list")["Containers"] if container["APFSContainerUUID"] == TARGET_UUID)


def copy_file(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def main():
    parser = argparse.ArgumentParser(description="Experimental local-resource J713 boot stub preparation")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    container = target()
    assert container["DesignatedPhysicalStore"] == "disk0s5"
    assert container["CapacityCeiling"] in (64000000000, 3999997952)
    restore = SOURCE / "restore"
    manifest = plistlib.loads((restore / "BuildManifest.plist").read_bytes())
    identity = next(identity for identity in manifest["BuildIdentities"] if identity["Info"]["DeviceClass"] == "j713ap" and identity["ApBoardID"] == "0x2C" and identity["ApChipID"] == "0x8132")
    assert manifest["ProductBuildVersion"] == "25E253"
    excluded = {"BaseSystem", "OS", "Ap,SystemVolumeCanonicalMetadata", "RestoreRamDisk", "RestoreTrustCache"}
    paths = sorted({value["Info"]["Path"] for key, value in identity["Manifest"].items() if key not in excluded and not key.startswith("Cryptex")})
    assert all(not Path(path).is_absolute() and ".." not in Path(path).parts for path in paths)
    missing = [path for path in paths if not (restore / path).is_file()]
    print(json.dumps({"target": TARGET_UUID, "build": "25E253", "missing_local_resources": missing}, indent=2), flush=True)
    if not args.apply:
        return
    volumes = container["Volumes"]
    if len(volumes) == 1 and not volumes[0]["Roles"]:
        assert volumes[0]["APFSVolumeUUID"] == "DE77783E-D9C0-4695-8BE1-EBE0D3015748"
        run("diskutil", "apfs", "changeVolumeRole", volumes[0]["DeviceIdentifier"], "D")
        run("diskutil", "rename", volumes[0]["DeviceIdentifier"], "M4 Linux Bootstrap - Data")
    container = target()
    by_role = {tuple(volume["Roles"]): volume for volume in container["Volumes"]}
    data_device = by_role[("Data",)]["DeviceIdentifier"]
    for role, code, name in [("System", "S", "M4 Linux Bootstrap"), ("Preboot", "B", "Preboot"), ("Recovery", "R", "Recovery")]:
        if (role,) not in by_role:
            command = ["diskutil", "apfs", "addVolume", container["ContainerReference"], "APFS", name, "-role", code]
            if role == "System":
                command.extend(["-groupWith", data_device])
            run(*command)
    container = target()
    by_role = {tuple(volume["Roles"]): volume for volume in container["Volumes"]}
    mounts = {}
    for role in ["System", "Data", "Preboot", "Recovery"]:
        device = by_role[(role,)]["DeviceIdentifier"]
        run("diskutil", "mount", device)
        mounts[role] = Path(read_diskutil("info", device)["MountPoint"])
    groups = read_diskutil("apfs", "listVolumeGroups", container["ContainerReference"])["Containers"][0]["VolumeGroups"]
    assert len(groups) == 1
    group_uuid = groups[0]["APFSVolumeGroupUUID"]
    assert group_uuid != SOURCE_UUID
    system = mounts["System"]
    preboot = mounts["Preboot"] / group_uuid
    destination = preboot / "restore"
    destination.mkdir(parents=True, exist_ok=True)
    manifest["BuildIdentities"] = [identity]
    (destination / "BuildManifest.plist").write_bytes(plistlib.dumps(manifest))
    for name in ["SystemVersion.plist", "RestoreVersion.plist", "usr/standalone/bootcaches.plist"]:
        copy_file(restore / name, destination / name)
    shutil.copytree(restore / "Bootability", destination / "Bootability", dirs_exist_ok=True, symlinks=True)
    copied = []
    for path in paths:
        if path not in missing:
            copy_file(restore / path, destination / path)
            copied.append(path)
    generic_ticket = restore / "apticket.j713ap.im4m"
    if generic_ticket.is_file():
        copy_file(generic_ticket, destination / generic_ticket.name)
    copy_file(restore / "usr/standalone/bootcaches.plist", system / "usr/standalone/bootcaches.plist")
    copy_file(Path("/Volumes/Macintosh HD/System/Library/CoreServices/PlatformSupport.plist"), system / "System/Library/CoreServices/PlatformSupport.plist")
    sysver = plistlib.loads((restore / "SystemVersion.plist").read_bytes())
    sysver["ProductUserVisibleVersion"] += " (stub)"
    (system / "System/Library/CoreServices/SystemVersion.plist").write_bytes(plistlib.dumps(sysver))
    if not (system / "restore").exists():
        (system / "restore").symlink_to(destination)
    (mounts["Data"] / "private/var/db/dslocal").mkdir(parents=True, exist_ok=True)
    admin = preboot / "var/db/AdminUserRecoveryInfo.plist"
    if admin.exists():
        run("chflags", "noschg", str(admin))
    copy_file(SOURCE / "var/db/AdminUserRecoveryInfo.plist", admin)
    run("chflags", "schg", str(admin))
    recovery_image = mounts["Recovery"] / group_uuid / "usr/standalone/firmware/arm64eBaseSystem.dmg"
    copy_file(Path("/Volumes/Recovery") / SOURCE_UUID / "usr/standalone/firmware/arm64eBaseSystem.dmg", recovery_image)
    shutil.copytree(TOOLS / "step2/Finish Installation.app", system / "Finish Installation.app", dirs_exist_ok=True, symlinks=True)
    resources = system / "Finish Installation.app/Contents/Resources"
    step2 = (TOOLS / "step2/step2.sh").read_text().replace("##DISTRO##", "M4 Linux experimental stub").replace("##VGID##", group_uuid).replace("##PREBOOT##", by_role[("Preboot",)]["APFSVolumeUUID"])
    step2 = step2.replace("while ! kmutil configure-boot", "csrutil disable\n\nwhile ! kmutil configure-boot")
    (resources / "step2.sh").write_text(step2)
    (resources / "step2.sh").chmod(0o755)
    copy_file(Path("/tmp/m1n1-sptm.bin"), resources / "boot.bin")
    copy_file(TOOLS / "step2/IAPhysicalMedia.plist", system / ".IAPhysicalMedia")
    library = ctypes.CDLL("libSystem.B.dylib", use_errno=True)
    library.fsctl.argtypes = [ctypes.c_char_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_int), ctypes.c_uint]
    operation = ctypes.c_int(1)
    if library.fsctl(str(system).encode(), 0xC0044A57, ctypes.byref(operation), 0) == -1:
        raise OSError(ctypes.get_errno(), "APFS bootable flag failed")
    report = {"group_uuid": group_uuid, "mounts": {role: str(path) for role, path in mounts.items()}, "devices": {role[0]: volume["DeviceIdentifier"] for role, volume in by_role.items()}, "copied": copied, "missing_local_resources": missing, "m1n1_sha256": hashlib.sha256((resources / "boot.bin").read_bytes()).hexdigest(), "personalized": False, "boot_verified": False}
    (system / "m4-stub-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
