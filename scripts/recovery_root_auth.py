import hashlib
import struct


def read_root_auth(path, expected_sha256):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError("Recovery root-hash SHA-256 mismatch")

    def read_field(offset, limit):
        if offset + 2 > limit:
            raise ValueError("truncated root-hash DER header")
        tag, length = data[offset:offset + 2]
        start = offset + 2
        if length & 0x80:
            count = length & 0x7f
            if not 1 <= count <= 4 or start + count > limit:
                raise ValueError("invalid root-hash DER length")
            length = int.from_bytes(data[start:start + count], "big")
            start += count
        end = start + length
        if end > limit:
            raise ValueError("truncated root-hash DER value")
        return tag, start, end

    tag, offset, end = read_field(0, len(data))
    if tag != 0x30 or end != len(data):
        raise ValueError("expected one root-hash IM4P sequence")
    fields = []
    while offset < end:
        tag, start, offset = read_field(offset, end)
        fields.append((tag, data[start:offset]))
    if len(fields) != 4 or fields[:2] != [(0x16, b"IM4P"), (0x16, b"csys")] or fields[3][0] != 4:
        raise ValueError("expected csys IM4P root-hash payload")
    payload = fields[3][1]
    if len(payload) != 208 or struct.unpack_from("<IIII", payload) != (2, 0, 1, 32):
        raise ValueError("unsupported Recovery root-hash header")
    root_digest = payload[16:48].hex().upper()
    return payload, root_digest
