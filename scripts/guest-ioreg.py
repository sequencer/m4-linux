import json
from pathlib import Path


def capture_registry(hypervisor, root, output):
    strings = {}

    def read(address, size):
        if not address or size > 65536:
            raise ValueError("Invalid registry read")
        data = bytearray()
        while size:
            count = min(size, 0x4000 - (address & 0x3fff))
            physical = hypervisor.p.hv_translate(address)
            if not physical:
                raise ValueError("Unmapped registry address")
            data.extend(hypervisor.iface.readmem(physical, count))
            address += count
            size -= count
        return bytes(data)

    def pointer(address):
        return hypervisor.unpac(int.from_bytes(read(address, 8), "little"))

    def string(address):
        if address not in strings:
            strings[address] = read(pointer(address + 16), 128).split(b"\x00")[0].decode("utf-8", errors="replace")
        return strings[address]

    def dictionary(address):
        count = int.from_bytes(read(address + 20, 4), "little")
        if count > 4096:
            raise ValueError("Invalid dictionary count")
        entries = read(pointer(address + 32), count * 16) if count else b""
        return {string(hypervisor.unpac(int.from_bytes(entries[offset:offset + 8], "little"))):
                hypervisor.unpac(int.from_bytes(entries[offset + 8:offset + 16], "little"))
                for offset in range(0, len(entries), 16)}

    pending = [(root, "")]
    seen = set()
    rows = []
    while pending and len(seen) < 4096:
        address, parent = pending.pop()
        if address in seen:
            continue
        seen.add(address)
        try:
            links = dictionary(pointer(address + 24))
            name = string(links["IOServiceName"] if "IOServiceName" in links else links["IOName"]) if "IOServiceName" in links or "IOName" in links else hex(address)
            path = parent + "/" + name
            row = {"address": hex(address), "path": path}
            if any(token in path.lower() for token in ("mtp", "hid", "keyboard", "touch", "firmware")):
                properties = dictionary(pointer(address + 32))
                row["properties"] = {key: hex(value) for key, value in properties.items()}
                row["string_properties"] = {}
                for key in ("IOClass", "CFBundleIdentifier", "IOProviderClass", "IOUserClass", "IONameMatched"):
                    if key in properties:
                        try:
                            row["string_properties"][key] = string(properties[key])
                        except ValueError:
                            pass
            rows.append(row)
            if "IOServiceChildLinks" in links:
                children = links["IOServiceChildLinks"]
                count = int.from_bytes(read(children + 20, 4), "little")
                if count > 4096:
                    raise ValueError("Invalid children count")
                entries = read(pointer(children + 32), count * 8) if count else b""
                pending.extend((hypervisor.unpac(int.from_bytes(entries[offset:offset + 8], "little")), path)
                               for offset in range(0, len(entries), 8))
        except (ValueError, KeyError) as error:
            rows.append({"address": hex(address), "parent": parent, "error": str(error)})
    report = {"layout": "25G83 disassembly-derived; caller must verify", "entries": rows,
              "limit_reached": bool(pending)}
    Path(output).write_text(json.dumps(report, indent=2) + "\n")
    return report
