import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import shutil
import stat
import tarfile
import zipfile


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def copy_zip(archive, name, destination):
    info = archive.getinfo(name)
    mode = info.external_attr >> 16
    destination.parent.mkdir(parents=True, exist_ok=True)
    if stat.S_ISLNK(mode):
        target = archive.read(name).decode()
        if Path(target).is_absolute() or ".." in Path(target).parts:
            raise ValueError("unsafe Bootability symlink")
        destination.symlink_to(target)
    else:
        with archive.open(name) as source, destination.open("xb") as target:
            shutil.copyfileobj(source, target)
        destination.chmod(mode & 0o777 or 0o644)


def main():
    parser = argparse.ArgumentParser(description="Prepare a pinned J713 firmware update archive on the M1; does not access target disks")
    parser.add_argument("--output", type=Path, default=Path("artifacts/apple/25G83/stub-update"))
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; preserve it and select a fresh directory")
    ipsw = Path("artifacts/apple/25G83/UniversalMac_26.6.2_25G83_Restore.ipsw")
    recovery = Path("artifacts/apple/25G83/derived/022-22048-093.dmg")
    payload = Path("results/m1n1-resource-tools/share/m1n1-sptm/m1n1.bin")
    expected = {ipsw: "885503b7f4b06609e9a512f2befd40f59730640a3f1233e3892d60affdd51c95",
                recovery: "eeda386b1fb66a313cadef26e3e7ee06643d4d5ea8b3330a411a118ac7d14ed3",
                payload: "779c9ac3c696210dcbd54c06f1353aa35f095cbd2a899a7da8a7ceacd5a6f2b4"}
    for path, expected_hash in expected.items():
        if digest(path) != expected_hash:
            parser.error(f"source hash mismatch: {path}")
    args.output.mkdir(parents=True)
    restore = args.output / "restore"
    system = args.output / "system"
    restore.mkdir()
    with zipfile.ZipFile(ipsw) as archive:
        manifest = plistlib.loads(archive.read("BuildManifest.plist"))
        if (manifest["ProductVersion"], manifest["ProductBuildVersion"]) != ("26.6.2", "25G83"):
            raise ValueError("unexpected firmware build")
        identities = [identity for identity in manifest["BuildIdentities"]
                      if identity["Info"]["DeviceClass"] == "j713ap"
                      and identity["ApBoardID"] == "0x2C" and identity["ApChipID"] == "0x8132"
                      and identity["Info"]["Variant"] == "macOS Customer"]
        if len(identities) != 1:
            raise ValueError("ambiguous macOS Customer identity")
        identity = identities[0]
        excluded = {"BaseSystem", "OS", "Ap,SystemVolumeCanonicalMetadata", "RestoreRamDisk", "RestoreTrustCache"}
        paths = {component["Info"]["Path"] for name, component in identity["Manifest"].items()
                 if name not in excluded and not name.startswith("Cryptex")}
        for name in sorted(paths):
            if Path(name).is_absolute() or ".." in Path(name).parts:
                raise ValueError("unsafe manifest path")
            copy_zip(archive, name, restore / name)
        manifest["BuildIdentities"] = [identity]
        (restore / "BuildManifest.plist").write_bytes(plistlib.dumps(manifest))
        for name in ["SystemVersion.plist", "RestoreVersion.plist", "usr/standalone/bootcaches.plist"]:
            copy_zip(archive, name, restore / name)
        prefix = "BootabilityBundle/Restore/Bootability/"
        for name in archive.namelist():
            if name.startswith(prefix) and not archive.getinfo(name).is_dir():
                copy_zip(archive, name, restore / "Bootability" / name.removeprefix(prefix))
        copy_zip(archive, "BootabilityBundle/Restore/Firmware/Bootability.dmg.trustcache",
                 restore / "Bootability/Bootability.trustcache")
        copy_zip(archive, "Firmware/Manifests/restore/macOS Customer/apticket.j713ap.im4m",
                 restore / "apticket.j713ap.im4m")
        copy_zip(archive, "PlatformSupport.plist", system / "System/Library/CoreServices/PlatformSupport.plist")
        copy_zip(archive, "usr/standalone/bootcaches.plist", system / "usr/standalone/bootcaches.plist")
        version = plistlib.loads(archive.read("SystemVersion.plist"))
        version["ProductUserVisibleVersion"] += " (stub)"
        (system / "System/Library/CoreServices/SystemVersion.plist").write_bytes(plistlib.dumps(version))
    shutil.copyfile(payload, args.output / "boot.bin")
    plan = {"build": "25G83", "product_version": "26.6.2", "variant": "macOS Customer",
            "target_group": "DE77783E-D9C0-4695-8BE1-EBE0D3015748",
            "target_container": "909274B1-CCC4-47DC-8314-9F00F7AF4885",
            "sources": {str(path): expected_hash for path, expected_hash in expected.items()},
            "boot_verified": False, "personalized": False}
    (args.output / "update-plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    checksums = []
    for path in sorted(args.output.rglob("*")):
        if path.is_file() and not path.is_symlink():
            checksums.append(f"{digest(path)}  {path.relative_to(args.output)}\n")
    checksums.append(f"{expected[recovery]}  recovery/arm64eBaseSystem.dmg\n")
    (args.output / "SHA256SUMS").write_text("".join(checksums))
    package = args.output.with_suffix(".tar")
    with tarfile.open(package, "w") as archive:
        for path in sorted(args.output.iterdir()):
            archive.add(path, arcname=path.name)
        archive.add(recovery, arcname="recovery/arm64eBaseSystem.dmg")
    print(json.dumps({"archive": str(package), "bytes": package.stat().st_size,
                      "sha256": digest(package), "plan": plan}, indent=2))


if __name__ == "__main__":
    main()
