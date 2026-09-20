import json
from pathlib import Path


def capture_processes(hypervisor, output):
    expected = {
        0xfffffe000bd22c90: 0xb9406020,
        0xfffffe000bd250b8: 0x91173001,
    }
    for address, instruction in expected.items():
        physical = hypervisor.p.hv_translate(address)
        if not physical or hypervisor.p.read32(physical) != instruction:
            raise ValueError("Process layout requires verified 25G83 instructions")

    def read_virtual(address, size):
        physical = hypervisor.p.hv_translate(address)
        if not physical or (address & 0x3fff) + size > 0x4000:
            raise ValueError("Unmapped or cross-page process field")
        return hypervisor.iface.readmem(physical, size)

    def read_pointer(address):
        return int.from_bytes(read_virtual(address, 8), "little")

    kernel_symbol = hypervisor.symbol_dict["com.apple.kernel:_kernproc"]
    current = read_pointer(kernel_symbol)
    seen = set()
    rows = []
    stopped = "limit"
    for step in range(256):
        if not current or current in seen:
            stopped = "null_or_cycle"
            break
        pid = int.from_bytes(read_virtual(current + 0x60, 4), "little")
        name = read_virtual(current + 0x5cc, 17).split(b"\x00")[0].decode("ascii", errors="replace")
        if pid > 100000 or not name or not name.isprintable():
            stopped = "head_or_invalid_record"
            break
        if not rows and (pid != 0 or name != "kernel_task"):
            raise ValueError("Kernel process anchor mismatch")
        rows.append({"pid": pid, "name": name, "address": hex(current)})
        seen.add(current)
        previous_link = read_pointer(current + 8)
        if not previous_link or read_pointer(previous_link) != current:
            stopped = "backlink_mismatch"
            break
        current = previous_link
    report = {"processes": rows, "stop_reason": stopped,
              "complete_list_verified": False, "names_may_be_truncated": True}
    Path(output).write_text(json.dumps(report, indent=2) + "\n")
    return report
