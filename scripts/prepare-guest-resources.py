import argparse
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description="Build a FAT RAM resource disk for the macOS guest")
    parser.add_argument("--firmware", type=Path, required=True)
    parser.add_argument("--ticket", type=Path, required=True)
    parser.add_argument("--ipsw", type=Path, required=True)
    parser.add_argument("--boot-objects-path", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    tree = args.output / "files"
    firmware_directory = tree / args.boot_objects_path.lstrip("/") / "usr/standalone/firmware/FUD"
    firmware_directory.mkdir(parents=True, exist_ok=True)
    files = []
    for name in ("J713_InputDevice.im4p", "J713_Multitouch.im4p", "J713_MtpFirmware.im4p"):
        source = args.firmware / name
        destination = firmware_directory / name.replace(".im4p", ".img4")
        subprocess.run([str(args.ipsw), "img4", "create", "--im4p", str(source),
                        "--im4m", str(args.ticket), "--output", str(destination)], check=True)
        files.append({"source": str(source.resolve()), "path": str(destination.relative_to(tree)),
                      "size": destination.stat().st_size, "format": "IMG4 with supplied IM4M"})
    image = args.output / "resources.fat"
    with image.open("xb") as stream:
        stream.truncate(64 * 1024 * 1024)
    subprocess.run(["mkfs.fat", "-F", "32", "-n", "M4RESOURCES", str(image)], check=True)
    for child in tree.iterdir():
        subprocess.run(["mcopy", "-i", str(image), "-s", str(child), "::/"], check=True)
    report = {"image": str(image), "boot_objects_path": args.boot_objects_path,
              "files": files, "ticket": str(args.ticket.resolve()),
              "current_ticket_acceptance_verified": False, "guest_loading_verified": False}
    (args.output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
