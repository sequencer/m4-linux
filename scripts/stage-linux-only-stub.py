import ctypes
import hashlib
import json
from pathlib import Path
import plistlib
import shutil
import subprocess


GROUP = "0F4B67C2-B48A-4F7F-B324-B02EB3362E5A"
CONTAINER = "AC02838C-5B6E-4B30-8BE1-C73937F42460"


def main():
    containers = plistlib.loads(subprocess.check_output(["diskutil", "apfs", "list", "-plist"]))["Containers"]
    target = next(container for container in containers if container["APFSContainerUUID"] == CONTAINER)
    if target["CapacityCeiling"] != 3999997952:
        raise ValueError("Unexpected stub size")
    mounts = {}
    for volume in target["Volumes"]:
        info = plistlib.loads(subprocess.check_output(["diskutil", "info", "-plist", volume["DeviceIdentifier"]]))
        mounts[tuple(volume["Roles"])] = Path(info["MountPoint"])
    stage = mounts[("Data",)] / "staging"
    for line in (stage / "SHA256SUMS").read_text().splitlines():
        expected, relative = line.split("  ", 1)
        with (stage / relative).open("rb") as source:
            if hashlib.file_digest(source, "sha256").hexdigest() != expected:
                raise ValueError(f"Hash mismatch: {relative}")
    system = mounts[("System",)]
    preboot = mounts[("Preboot",)] / GROUP
    recovery = mounts[("Recovery",)] / GROUP / "usr/standalone/firmware"
    if (preboot / "restore").exists():
        raise ValueError("Already staged; inspect before retrying")
    manifest = plistlib.loads((stage / "restore/BuildManifest.plist").read_bytes())
    if manifest["ProductBuildVersion"] != "25G83":
        raise ValueError("Wrong firmware build")
    preboot.mkdir(parents=True)
    recovery.mkdir(parents=True)
    shutil.copytree(stage / "system", system, dirs_exist_ok=True, symlinks=True)
    shutil.move(str(stage / "restore"), str(preboot / "restore"))
    shutil.move(str(stage / "recovery/arm64eBaseSystem.dmg"), str(recovery / "arm64eBaseSystem.dmg"))
    (system / "restore").symlink_to(preboot / "restore")
    resources = system / "m1n1"
    resources.mkdir()
    shutil.copy2(stage / "boot.bin", resources / "boot.bin")
    (mounts[("Data",)] / "private/var/db/dslocal").mkdir(parents=True)
    report = {"group": GROUP, "container": CONTAINER, "build": "25G83",
              "payload_sha256": hashlib.sha256((resources / "boot.bin").read_bytes()).hexdigest(),
              "owner_credentials_present": False, "personalized": False, "boot_verified": False}
    (system / "m4-stub-report.json").write_text(json.dumps(report, indent=2) + "\n")
    library = ctypes.CDLL("libSystem.B.dylib", use_errno=True)
    library.fsctl.argtypes = [ctypes.c_char_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_int), ctypes.c_uint]
    operation = ctypes.c_int(1)
    if library.fsctl(str(system).encode(), 0xC0044A57, ctypes.byref(operation), 0) == -1:
        raise OSError(ctypes.get_errno(), "APFS bootable flag failed")
    subprocess.run(["sync"], check=True)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
