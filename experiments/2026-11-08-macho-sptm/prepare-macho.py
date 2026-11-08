import json
from pathlib import Path
import struct


root = Path(__file__).parent / "raw"
image = bytearray((root / "m1n1-ddf.macho").read_bytes())
header = list(struct.unpack_from("<8I", image))
segments = {}
offset = 32
for _ in range(header[4]):
    command, size = struct.unpack_from("<II", image, offset)
    if command == 5:
        thread = bytes(image[offset:offset + size])
    elif command == 0x19:
        segment = struct.unpack_from("<II16sQQQQIIII", image, offset)
        segments[segment[2].rstrip(b"\0").decode()] = segment
    offset += size

# 26A428 kmutil 0x100025158 requires these four segment names.
# 0x100025490 looks up optional __TEXT_BOOT_EXEC; omit it for bx_size = 0.
base = segments["_HDR"][3]
text_offset = segments["TEXT"][5]
data_offset = segments["RODA"][5]
payload_offset = segments["PYLD"][3] - base
layout = [
    ("__TEXT", 0, text_offset, 1),
    ("__TEXT_EXEC", text_offset, data_offset - text_offset, 5),
    ("__PRELINK_INFO", data_offset, payload_offset - data_offset, 3),
    ("__LINKEDIT", payload_offset, 0x4000, 1),
]

# Materialize DATA's zero-fill before the original _payload_start. The final
# zero page terminates m1n1's payload scan, leaving it at the proxy prompt.
image.extend(bytes(payload_offset + 0x4000 - len(image)))
commands = bytearray(thread)
for name, offset, size, protection in layout:
    commands += struct.pack(
        "<II16sQQQQIIII", 0x19, 72, name.encode(),
        base + offset, size, offset, size, protection, protection, 0, 0,
    )
header[4] = 5
header[5] = len(commands)
image[:text_offset] = bytes(text_offset)
struct.pack_into("<8I", image, 0, *header)
image[32:32 + len(commands)] = commands
destination = root / "m1n1-macho-layout-v1.macho"
destination.write_bytes(image)
print(json.dumps({
    "output": str(destination), "bytes": len(image),
    "entry": hex(struct.unpack_from("<Q", thread, 16 + 32 * 8)[0]),
    "segments": [{"name": n, "offset": hex(o), "size": hex(s)}
                 for n, o, s, _ in layout],
}, indent=2))
