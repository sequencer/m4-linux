import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess


INSPECT_SPEC = importlib.util.spec_from_file_location("recovery_input", Path(__file__).with_name("inspect-recovery-input.py"))
INSPECT_MODULE = importlib.util.module_from_spec(INSPECT_SPEC)
INSPECT_SPEC.loader.exec_module(INSPECT_MODULE)
inspect_image = INSPECT_MODULE.inspect_image


def file_hash(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Convert a local Recovery UDIF and extract its APFS container; never accesses target disks")
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-sha256", required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    destination = args.output.resolve()
    if not source.is_file() or str(source).startswith("/dev/"):
        parser.error("source must be a regular local image")
    whole_disk = destination.with_suffix(".whole-disk.raw")
    metadata_path = destination.with_suffix(".json")
    if any(path.exists() for path in (destination, whole_disk, metadata_path)):
        parser.error("output exists; select fresh paths instead of overwriting")
    if file_hash(source) != args.source_sha256:
        parser.error("source SHA-256 mismatch")
    with source.open("rb") as image:
        image.seek(-512, 2)
        if image.read(4) != b"koly":
            parser.error("expected a decoded UDIF DMG, not an AEA container or raw disk")
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["dmg2img", str(source), str(whole_disk)], check=True)
    geometry = inspect_image(whole_disk)
    if geometry["gpt"] is None:
        parser.error("expected a GPT disk with one APFS partition")
    partitions = geometry["gpt"]["partitions"]
    if len(partitions) != 1 or partitions[0]["type_guid"] != "7c3457ef-0000-11aa-aa11-00306543ecac":
        parser.error("expected exactly one APFS partition")
    partition = partitions[0]
    if not partition["apfs_magic"] or partition["apfs_block_size"] != 4096:
        parser.error("invalid or unsupported APFS superblock")
    if partition["apfs_block_size"] * partition["apfs_block_count"] != partition["size"]:
        parser.error("APFS container geometry does not match the partition")
    digest = hashlib.sha256()
    with whole_disk.open("rb") as image, destination.open("xb") as root:
        image.seek(partition["offset"])
        remaining = partition["size"]
        while remaining:
            chunk = image.read(min(16 * 1024 * 1024, remaining))
            if not chunk:
                raise ValueError("truncated APFS partition")
            root.write(chunk)
            digest.update(chunk)
            remaining -= len(chunk)
    extracted = inspect_image(destination)
    if not extracted["initial_apfs_magic"] or extracted["gpt"] is not None:
        raise ValueError("extracted root is not a direct APFS container")
    metadata = {"source": str(source), "source_sha256": args.source_sha256,
                "whole_disk": str(whole_disk), "whole_disk_sha256": file_hash(whole_disk),
                "whole_disk_geometry": geometry, "partition": partition,
                "root": str(destination), "root_size": destination.stat().st_size,
                "root_sha256": digest.hexdigest(), "required_physical_alignment": 0x4000,
                "guest_boot_verified": False}
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
