import hashlib
import json
from pathlib import Path
import plistlib
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
DESTINATION = ROOT / "artifacts/current-25G83-post-restore-20260914"
IPSW_HASH = "885503b7f4b06609e9a512f2befd40f59730640a3f1233e3892d60affdd51c95"


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def main():
    if DESTINATION.exists():
        raise ValueError("Output exists; preserve it and inspect instead of overwriting")
    official = ROOT / "artifacts/apple/25G83"
    entries = []
    for directory, checksums, target in (
        (official / "j713", ROOT / "experiments/2026-09-13-apple-25G83/SHA256SUMS", "official"),
        (official / "derived", ROOT / "experiments/2026-09-13-apple-25G83/DERIVED_SHA256SUMS", "derived"),
    ):
        for line in checksums.read_text().splitlines():
            expected, relative = line.split("  ", 1)
            relative = Path(relative)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Unsafe manifest path")
            entries.append((directory / relative, Path(target) / relative, expected))
    entries.extend([
        (official / "UniversalMac_26.6.2_25G83_Restore.ipsw", Path("restore.ipsw"), IPSW_HASH),
        (ROOT / "result/share/m1n1-sptm/m1n1.bin", Path("m1n1.bin"),
         "779c9ac3c696210dcbd54c06f1353aa35f095cbd2a899a7da8a7ceacd5a6f2b4"),
    ])
    manifest = plistlib.loads((official / "j713/BuildManifest.plist").read_bytes())
    if manifest["ProductBuildVersion"] != "25G83":
        raise ValueError("Wrong build")
    for source, relative, expected in entries:
        if digest(source) != expected:
            raise ValueError(f"Checksum mismatch: {source}")
        print(f"Verified {relative}", flush=True)
    DESTINATION.mkdir()
    report = {
        "build": "25G83", "product_version": "26.6.2", "model": "Mac16,12",
        "ecid": "0xa10a426b9001c", "device_class": "j713ap",
        "macos_group": "742D07D7-4C78-4BAB-B4E1-D6F3B239A2D8",
        "stub_group": "530FE39B-6AE3-47D0-9168-29F1A7EE2763",
        "isc_partition_uuid": "2935ACB5-2A69-4996-942A-87B29BC17A2F",
        "observed_boot_firmware": "mBoot-18000.161.10",
        "guest_execution_allowed": False,
        "current_isc_capture": None,
        "personalized_state_included": False,
        "files": [],
    }
    for source, relative, expected in entries:
        output = DESTINATION / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.symlink_to(source.resolve())
        report["files"].append({"path": str(relative), "sha256": expected,
                                "bytes": source.stat().st_size})
    kernel = DESTINATION / "kernelcache-25G83.macho"
    subprocess.run([
        sys.executable, str(ROOT / "scripts/extract-kernelcache.py"),
        str(DESTINATION / "official/kernelcache.release.mac16g"), str(kernel),
    ], check=True)
    if digest(kernel) != "f42ad6f51d130141095a94b4749d128d648f2be2ac0c291bf492ac1c64e5875d":
        raise ValueError("Fresh kernel extraction differs from pinned output")
    root = DESTINATION / "recovery-25G83.apfs.raw"
    subprocess.run([
        sys.executable, str(ROOT / "scripts/prepare-recovery-root.py"),
        str(DESTINATION / "derived/022-22048-093.dmg"), str(root),
        "--source-sha256", "eeda386b1fb66a313cadef26e3e7ee06643d4d5ea8b3330a411a118ac7d14ed3",
    ], check=True)
    if digest(root) != "bda0c53dfb35ceffe371c1708b2443b9d55f60a70bbcbbcf6470bade2b552e9a":
        raise ValueError("Fresh Recovery conversion differs from pinned output")
    for generated in sorted(DESTINATION.iterdir()):
        if generated.is_file() and not generated.is_symlink():
            report["files"].append({"path": generated.name, "sha256": digest(generated),
                                    "bytes": generated.stat().st_size})
    (DESTINATION / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    (DESTINATION / "SHA256SUMS").write_text("".join(
        f"{entry['sha256']}  {entry['path']}\n" for entry in report["files"]
    ))
    print("Current assets verified and regenerated; guest execution remains blocked.")


if __name__ == "__main__":
    main()
