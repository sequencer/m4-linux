import json
import struct


PINNED_KERNEL = "f42ad6f51d130141095a94b4749d128d648f2be2ac0c291bf492ac1c64e5875d"


def install_panic_capture(hypervisor, output, kernel_digest):
    if kernel_digest != PINNED_KERNEL:
        return
    original_report = hypervisor.report_xnu_panic

    def capture():
        context = hypervisor.ctx
        state = {"cpu": context.cpu_id, "elr": hex(context.elr),
                 "reason": hypervisor.exc_reason.name, "event": hypervisor.exc_code.name,
                 "registers": [hex(value) for value in context.regs],
                 "stack_pointers": [hex(value) for value in context.sp]}
        try:
            header_address = hypervisor.p.hv_translate(0xfffffe000c638320)
            if not header_address:
                raise ValueError("console ring header translation failed")
            header = hypervisor.iface.readmem(header_address, 32)
            base, size, read_offset, aux, padding, write_pointer = struct.unpack("<QIIIIQ", header)
            if size != 16384 or not base <= write_pointer < base + size:
                raise ValueError("console ring layout differs from verified 25G83 state")
            physical_base = hypervisor.p.hv_translate(base)
            if not physical_base:
                raise ValueError("console ring buffer translation failed")
            buffer = hypervisor.iface.readmem(physical_base, size)
            output.with_suffix(".console-ring.bin").write_bytes(buffer)
            output.with_suffix(".console-ring.txt").write_text(
                buffer.replace(b"\x00", b"").decode("utf-8", errors="replace"))
            state["console_ring"] = {"base": hex(base), "size": size,
                                     "read_offset": read_offset, "write_pointer": hex(write_pointer),
                                     "raw_order": True}
        except Exception as error:
            state["console_capture_error"] = str(error)
        try:
            suffix = ".panic.json" if state["event"] == "XNU_PANIC" else ".inspection.json"
            output.with_suffix(suffix).write_text(json.dumps(state, indent=2) + "\n")
        except Exception as error:
            print("Panic evidence write failed:", error, flush=True)
        print("Guest diagnostic evidence captured:", state, flush=True)

    def report_and_capture():
        original_report()
        capture()

    hypervisor.report_xnu_panic = report_and_capture
    hypervisor.capture_guest_diagnostics = capture
