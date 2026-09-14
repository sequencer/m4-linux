import hashlib
from pathlib import Path
import plistlib
import subprocess


def main():
    directory = Path("/Volumes/M4 Install Assets")
    info = plistlib.loads(subprocess.check_output(["diskutil", "info", "-plist", str(directory)]))
    if info["VolumeUUID"] != "1E95E303-A64C-414F-9338-4FBD9815230E":
        raise ValueError("Unexpected installation resource volume")
    target = directory / "UniversalMac_26.6.2_25G83_Restore.ipsw"
    partial = target.with_suffix(".ipsw.partial")
    if target.exists():
        raise ValueError("Final path already exists; do not overwrite")
    if partial.stat().st_size != 19772231540:
        raise ValueError("Transfer size mismatch; preserve partial file")
    with partial.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    if digest != "885503b7f4b06609e9a512f2befd40f59730640a3f1233e3892d60affdd51c95":
        raise ValueError("IPSW SHA-256 mismatch; preserve partial file")
    partial.rename(target)
    subprocess.run(["sync"], check=True)
    print(f"VERIFIED {target.stat().st_size} bytes SHA256={digest}")
    print(target)


if __name__ == "__main__":
    main()
