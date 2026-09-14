import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import zipfile


IPSW_SHA256 = "885503b7f4b06609e9a512f2befd40f59730640a3f1233e3892d60affdd51c95"


def digest_file(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Extract pinned Apple 25G83 J713 boot resources without accessing hardware")
    parser.add_argument("ipsw", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/apple/25G83/j713"))
    args = parser.parse_args()
    if digest_file(args.ipsw) != IPSW_SHA256:
        raise ValueError("IPSW SHA-256 does not match the pinned Apple CDN digest")
    if args.output.exists():
        raise ValueError("Output already exists; preserve it or select a fresh directory")
    with zipfile.ZipFile(args.ipsw) as archive:
        manifest = plistlib.loads(archive.read("BuildManifest.plist"))
        if (manifest["ProductVersion"], manifest["ProductBuildVersion"]) != ("26.6.2", "25G83"):
            raise ValueError("Unexpected macOS version/build")
        identities = [identity for identity in manifest["BuildIdentities"]
                      if identity["Info"].get("DeviceClass") == "j713ap"
                      and int(identity["ApBoardID"], 16) == 0x2C
                      and int(identity["ApChipID"], 16) == 0x8132]
        if not identities:
            raise ValueError("No matching J713/T8132 identity")
        components = {}
        excluded = {"OS", "Ap,SystemVolumeCanonicalMetadata"}
        for identity in identities:
            for name, component in identity["Manifest"].items():
                path = component.get("Info", {}).get("Path")
                if path and name not in excluded and not name.startswith("Cryptex"):
                    components.setdefault(path, set()).add(name)
        for name in archive.namelist():
            if name in {"BuildManifest.plist", "Restore.plist", "SystemVersion.plist", "RestoreVersion.plist", "usr/standalone/bootcaches.plist"} or name.startswith("Bootability/") or name == "apticket.j713ap.im4m":
                if not archive.getinfo(name).is_dir():
                    components.setdefault(name, set()).add("auxiliary")
        for name in components:
            path = Path(name)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"Unsafe archive path: {name}")
            archive.getinfo(name)
        args.output.mkdir(parents=True)
        records = []
        for name, roles in sorted(components.items()):
            destination = args.output / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            with archive.open(name) as source, destination.open("xb") as target:
                while chunk := source.read(1024 * 1024):
                    target.write(chunk)
                    digest.update(chunk)
            record = {"path": name, "bytes": destination.stat().st_size,
                      "sha256": digest.hexdigest(), "components": sorted(roles)}
            records.append(record)
            print(json.dumps(record), flush=True)
        inventory = {"ipsw_sha256": IPSW_SHA256, "product_version": "26.6.2",
                     "build": "25G83", "device_class": "j713ap", "chip_id": "0x8132",
                     "board_id": "0x2C", "variants": [identity["Info"]["Variant"] for identity in identities],
                     "excluded": ["OS image", "system canonical metadata", "Cryptex components"],
                     "files": records}
        (args.output / "inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")
        (args.output / "SHA256SUMS").write_text("".join(f'{record["sha256"]}  {record["path"]}\n' for record in records))


if __name__ == "__main__":
    main()
