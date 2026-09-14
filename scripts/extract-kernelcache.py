import argparse
import json
from pathlib import Path
import subprocess
import sys


def read_der(data, offset):
    tag = data[offset]
    length = data[offset + 1]
    start = offset + 2
    if length & 0x80:
        count = length & 0x7F
        if not 1 <= count <= 8 or start + count > len(data):
            raise ValueError("unsupported DER length")
        length = int.from_bytes(data[start:start + count], "big")
        start += count
    end = start + length
    if end > len(data):
        raise ValueError("truncated DER payload")
    return tag, data[start:end], end


def main():
    parser = argparse.ArgumentParser(description="Extract an unencrypted LZFSE IM4P kernelcache and check SPTM symbols")
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--proxyclient", type=Path, default=Path(__file__).resolve().parent.parent / "result/share/m1n1-sptm/proxyclient")
    args = parser.parse_args()
    tag, sequence, end = read_der(args.source.read_bytes(), 0)
    if tag != 0x30 or end != args.source.stat().st_size:
        parser.error("expected one IM4P DER sequence")
    fields = []
    offset = 0
    while offset < len(sequence):
        tag, value, offset = read_der(sequence, offset)
        fields.append((tag, value))
    if len(fields) < 4 or fields[0] != (0x16, b"IM4P") or fields[1] != (0x16, b"krnl") or fields[3][0] != 4:
        parser.error("expected a krnl IM4P payload")
    payload = fields[3][1]
    if not payload.startswith((b"bvx2", b"bvx1", b"bvx-", b"bvxn")):
        parser.error("payload is not a supported unencrypted LZFSE stream")
    compressed = args.output.with_suffix(".lzfse")
    compressed.write_bytes(payload)
    subprocess.run(["lzfse", "-decode", "-i", str(compressed), "-o", str(args.output)], check=True)
    if args.output.read_bytes()[:4] != b"\xcf\xfa\xed\xfe":
        parser.error("decoded payload is not a 64-bit little-endian Mach-O")
    sys.path.insert(0, str(args.proxyclient))
    from m1n1.macho import MachO

    with args.output.open("rb") as source:
        macho = MachO(source)
        macho.add_fileset_symbols("com.apple.kernel")
        required = ["com.apple.kernel:" + name for name in ("_cons_ops", "_PAGE_SHIFT_CONST", "__TEXT")]
        missing = [name for name in required if name not in macho.symbols]
        print(json.dumps({"output": str(args.output), "size": args.output.stat().st_size, "required_symbols": {name: macho.symbols.get(name) for name in required}, "missing_symbols": missing}, indent=2))
        if missing:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
