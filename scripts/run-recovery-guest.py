import argparse
import hashlib
import json
from pathlib import Path
import runpy
import struct
import sys

from sptm_timer import probe_timer
from recovery_root_auth import read_root_auth
from guest_diagnostics import install_panic_capture


class ConsoleLog:
    def __init__(self, stream, log):
        self.stream = stream
        self.log = log

    def write(self, text):
        self.log.write(text)
        self.log.flush()
        return self.stream.write(text)

    def flush(self):
        self.log.flush()
        self.stream.flush()

    def __getattr__(self, name):
        return getattr(self.stream, name)


def plan_ramdisk(physical_base, memory_size, kernel_end, disk_size, carveouts=()):
    alignment = 0x4000
    memory_end = physical_base + memory_size
    address = (kernel_end + alignment - 1) & -alignment
    reserved_end = (address + disk_size + alignment - 1) & -alignment
    aux_end = reserved_end + 64 * 1024 * 1024
    if not (physical_base <= kernel_end <= address < reserved_end < aux_end <= memory_end):
        raise ValueError("RAMDisk and HLE aux reservation do not fit guest physical memory")
    if disk_size <= 0 or disk_size % 4096:
        raise ValueError("RAMDisk must contain complete APFS blocks")
    for start, size in carveouts:
        if size <= 0 or (kernel_end < start + size and start < aux_end):
            raise ValueError("RAMDisk/HLE reservation overlaps a protected carveout")
    return {"physical_base": physical_base, "memory_end": memory_end,
            "kernel_end": kernel_end, "ramdisk_address": address, "ramdisk_size": disk_size,
            "reserved_end": reserved_end, "hle_aux_start": reserved_end, "hle_aux_end": aux_end}


def main():
    parser = argparse.ArgumentParser(description="Experimental SPTM-emulated XNU guest with a RAM-only Recovery root")
    parser.add_argument("kernel", type=Path)
    parser.add_argument("ramdisk", type=Path)
    parser.add_argument("--root-manifest", type=Path, required=True)
    parser.add_argument("--kernel-sha256", required=True)
    parser.add_argument("--skip-file-hashes", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="/dev/ttyACM0")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--guest-memory-gib", type=int, choices=(8, 16))
    parser.add_argument("--guest-cpus", type=int, choices=(1, 10), default=1)
    parser.add_argument("--recovery-root-hash", type=Path)
    parser.add_argument("--recovery-root-hash-sha256")
    parser.add_argument("--inspect-apfs-root", action="store_true")
    parser.add_argument("--direct-basesystem-root", action="store_true")
    parser.add_argument("--ram-root-boot-uuid", action="store_true")
    parser.add_argument("--iokit-ram-root", action="store_true")
    parser.add_argument("--isc-image", type=Path)
    parser.add_argument("--isc-manifest", type=Path)
    parser.add_argument("--resources-image", type=Path)
    parser.add_argument("--extra-bootargs", default="")
    parser.add_argument("--console-log", type=Path)
    parser.add_argument("--graphics", action="store_true")
    parser.add_argument("--proxyclient", type=Path, default=Path(__file__).resolve().parent.parent / "results/m1n1-resource-tools/share/m1n1-sptm/proxyclient")
    args = parser.parse_args()
    if bool(args.recovery_root_hash) != bool(args.recovery_root_hash_sha256):
        parser.error("Recovery root-hash path and SHA-256 must be supplied together")
    if args.direct_basesystem_root and not (args.inspect_apfs_root and args.recovery_root_hash):
        parser.error("direct BaseSystem experiment requires APFS inspection and a pinned Recovery root-hash")
    if args.ram_root_boot_uuid and not args.direct_basesystem_root:
        parser.error("RAM root boot UUID requires the pinned direct BaseSystem experiment")
    if args.iokit_ram_root and not args.ram_root_boot_uuid:
        parser.error("IOKit RAM root experiment requires aligned RAM root boot UUID")
    if bool(args.isc_image) != bool(args.isc_manifest) or (args.isc_image and not args.iokit_ram_root):
        parser.error("iSC image and manifest require the native IOKit RAM root experiment")
    if args.resources_image and not args.isc_image:
        parser.error("resources image requires the RAM GPT/iSC layout")
    root_auth = None
    if args.recovery_root_hash:
        root_auth = read_root_auth(args.recovery_root_hash, args.recovery_root_hash_sha256,
                                   verify_hash=not args.skip_file_hashes)
    if not args.prepare_only and not sys.stdin.isatty():
        parser.error("guest launch requires interactive stdin; run with a PTY to preserve panic-shell control, or use --prepare-only")
    if args.output.exists():
        parser.error("output report already exists; select a fresh experiment path")
    if args.console_log:
        args.console_log.parent.mkdir(parents=True, exist_ok=True)
        log = args.console_log.open("x", buffering=1)
        sys.stdout = ConsoleLog(sys.stdout, log)
        sys.stderr = ConsoleLog(sys.stderr, log)
    metadata = json.loads(args.root_manifest.read_text())
    with args.kernel.open("rb") as kernel:
        kernel_digest = args.kernel_sha256 if args.skip_file_hashes else hashlib.file_digest(kernel, "sha256").hexdigest()
    if kernel_digest != args.kernel_sha256:
        parser.error("kernel SHA-256 mismatch")
    size = args.ramdisk.stat().st_size
    with args.ramdisk.open("rb") as image:
        digest = metadata["root_sha256"] if args.skip_file_hashes else hashlib.file_digest(image, "sha256").hexdigest()
        image.seek(32)
        superblock_header = image.read(16)
        magic = superblock_header[:4]
    if size != metadata["root_size"] or digest != metadata["root_sha256"] or magic != b"NXSB":
        parser.error("RAM root hash/size/APFS superblock mismatch")
    if args.direct_basesystem_root and digest != "bda0c53dfb35ceffe371c1708b2443b9d55f60a70bbcbbcf6470bade2b552e9a":
        parser.error("direct BaseSystem experiment requires the verified 25G83 Recovery APFS root")
    if not 0 < size < 1800 * 1024 * 1024:
        parser.error("unsupported RAM root size")
    isc_media = None
    if args.isc_image:
        isc_manifest = json.loads(args.isc_manifest.read_text())
        isc_size = args.isc_image.stat().st_size
        if (isc_manifest.get("ecid") != "0xa10a426b9001c"
                or isc_manifest.get("chip") != "0x8132"
                or isc_manifest.get("size") != isc_size
                or not 64 * 1024 ** 2 <= isc_size <= 1024 ** 3):
            parser.error("iSC source identity or size mismatch")
        helpers = runpy.run_path(str(Path(__file__).with_name("prepare-ram-isc.py")))
        if not args.skip_file_hashes:
            helpers["check_source"](args.isc_image, isc_manifest["sha256"])
        resources_size = args.resources_image.stat().st_size if args.resources_image else 0
        prefix, suffix, media_layout = helpers["make_gpt"](size, isc_size, resources_size)
        if media_layout["gap_size"]:
            parser.error("scatter image currently requires contiguous partition boundaries")
        isc_media = (prefix, suffix, media_layout, isc_manifest.get("sha256"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(args.proxyclient))
    from m1n1.proxy import M1N1Proxy, UartInterface
    from m1n1.proxyutils import ProxyUtils, bootstrap_port
    from m1n1.hv import HV
    from m1n1.hv.types import TraceMode
    from m1n1.utils import irange
    from m1n1.tgtypes import BootArgs_r1, BootArgs_r2, BootArgs_r3

    interface = UartInterface(args.device)
    proxy = M1N1Proxy(interface)
    bootstrap_port(interface, proxy)
    utils = ProxyUtils(proxy, heap_size=256 * 1024 * 1024)
    if utils.adt["/chosen"].chip_id != 0x8132:
        parser.error("target is not T8132")
    if not args.prepare_only:
        timer = probe_timer(utils)
        interface.nop()
        proxy.nop()
        if not timer.get("readback_matches", False):
            args.output.write_text(json.dumps({"timer_probe": timer, "guest_started": False}, indent=2) + "\n")
            parser.error("timer routing register remains locked; update actual boot firmware before starting guest")
    hypervisor = HV(interface, proxy, utils)
    hypervisor.init()
    install_panic_capture(hypervisor, args.output, kernel_digest)
    assert utils.adt["/chosen"].chip_id == 0x8132
    boot_uuid_report = None
    if args.ram_root_boot_uuid:
        previous_boot_uuid = hypervisor.adt["/chosen"].boot_uuid
        hypervisor.adt["/chosen"].boot_uuid = "E93D361D-43AC-47A0-8DDA-A5D235BACC77"
        boot_uuid_report = {"previous": previous_boot_uuid,
                            "guest_boot_uuid": hypervisor.adt["/chosen"].boot_uuid,
                            "apfs_preboot_uuid_changed": False,
                            "source": "pinned 25G83 BaseSystem volume UUID verified in live APFS superblock at offset 0xf0"}
        print("Aligned guest RAM root boot UUID:", boot_uuid_report, flush=True)
    root_auth_report = None
    if root_auth:
        payload, root_digest = root_auth
        auth_node = hypervisor.adt["/chosen/secure-boot-hashes"]
        if auth_node.base_system_volume_auth_blob != payload:
            raise ValueError("live BaseSystem auth blob differs from pinned Recovery root-hash")
        previous_snapshot = hypervisor.adt["/chosen"].root_snapshot_name
        if not args.direct_basesystem_root:
            auth_node.system_volume_auth_blob = payload
        root_auth_report = {"root_hash_sha256": args.recovery_root_hash_sha256,
                            "inherited_snapshot": previous_snapshot, "recovery_root_digest": root_digest,
                            "snapshot_changed": False,
                            "system_auth_blob_matches_recovery": auth_node.system_volume_auth_blob == payload,
                            "system_auth_blob_changed": not args.direct_basesystem_root}
        print("Aligned guest root authentication:", root_auth_report, flush=True)
    removed = []
    for node in list(hypervisor.adt["/arm-io"]):
        if node.name.startswith("ans") or "nvme" in node.name.lower():
            removed.append(node.name)
            del hypervisor.adt["/arm-io/" + node.name]
    assert removed, "no SSD controller node removed; refusing guest start"
    print("Removed guest SSD controller nodes:", removed, flush=True)
    for name in ["/arm-io/exdisplaypipe", "/arm-io/exdisplaypipe-s-proxy", "/arm-io/dcp-exclave-ioreporting", "/arm-io/dcp-exclave-mailbox"]:
        try:
            del hypervisor.adt[name]
        except KeyError:
            pass
    try:
        nub = hypervisor.adt["/arm-io/dcp/iop-dcp-nub"]
        if getattr(nub, "routes", None) is not None:
            del nub.routes
    except KeyError:
        pass
    guest_bootargs = f"rd=md0 -nobsdmgroot cpus={args.guest_cpus} wdt=-1 sprr_tpro=0 sprr_tpro_pagers=0 wfi=0 cluster_power=0 processor_exit=0 vm_compressor=0 -v msgbuf=1048576 amfi_get_out_of_my_way=1"
    if args.graphics:
        guest_bootargs = " ".join(argument for argument in guest_bootargs.split() if argument != "-v")
    if args.extra_bootargs:
        guest_bootargs += " " + args.extra_bootargs
    hypervisor.set_bootargs(guest_bootargs)
    with args.kernel.open("rb") as kernel:
        hypervisor.load_macho(kernel)
    original_memory_size = hypervisor.tba.mem_size
    apfs_inspection = None
    if args.inspect_apfs_root:
        if kernel_digest != "f42ad6f51d130141095a94b4749d128d648f2be2ac0c291bf492ac1c64e5875d":
            raise ValueError("APFS inspection addresses are only verified for pinned 25G83 kernel")
        trap_address = 0xfffffe000b443a6c
        physical_address = hypervisor.guest_base + trap_address - hypervisor.macho.vmin
        expected_instruction = 0xb9406be8
        if proxy.read32(physical_address) != expected_instruction:
            raise ValueError("APFS inspection instruction differs from verified disassembly")
        original_handler = hypervisor.handle_brk

        def inspect_apfs_root(context):
            if context.esr.ISS != 0x4243 or context.elr != trap_address:
                return original_handler(context)
            proxy.write32(physical_address, expected_instruction)
            proxy.dc_cvau(physical_address, 4)
            proxy.ic_ivau(physical_address, 4)
            active_stack = context.sp[0] if int(context.spsr) & 0xf == 4 else context.sp[1]
            container = context.regs[27]
            volume = proxy.read64(proxy.hv_translate(context.regs[29] - 0x98))
            superblock = proxy.read64(proxy.hv_translate(volume + 0xc0))
            state = {"cpu": context.cpu_id, "first_mount_register_w23": context.regs[23] & 0xffffffff,
                     "stack_pointers": [hex(value) for value in context.sp],
                     "stack_flag": proxy.read32(proxy.hv_translate(active_stack + 0x68)),
                     "container": hex(container),
                     "nx_virtual_flag": proxy.read8(proxy.hv_translate(container + 0x166)),
                     "nx_device": hex(proxy.read64(proxy.hv_translate(container + 0x238))),
                     "volume": hex(volume),
                     "volume_role": proxy.read16(proxy.hv_translate(superblock + 0x3c4)),
                     "volume_sealed": bool(proxy.read64(proxy.hv_translate(superblock + 0x38)) & (1 << 5)),
                     "already_rooted": proxy.read8(proxy.hv_translate(0xfffffe000c94d7c0)),
                     "guest_elr": hex(context.elr),
                     "instruction_restored": True}
            if args.direct_basesystem_root:
                if (int(context.spsr) & 0xf != 4 or state["first_mount_register_w23"] != 1
                        or state["stack_flag"] != 0 or state["volume_role"] != 1 or not state["volume_sealed"]
                        or state["nx_device"] != "0x0" or state["nx_virtual_flag"] != 0
                        or state["already_rooted"] != 0):
                    state["adapter_refused"] = "APFS state differs from observed RAM-root baseline"
                else:
                    proxy.write8(proxy.hv_translate(container + 0x166), state["nx_virtual_flag"] | 1)
                    proxy.write8(proxy.hv_translate(0xfffffe000c94d7c0), 1)
                    state["nx_virtual_flag_after"] = proxy.read8(proxy.hv_translate(container + 0x166))
                    state["already_rooted_after"] = proxy.read8(proxy.hv_translate(0xfffffe000c94d7c0))
                    state["adapter_applied"] = (state["nx_virtual_flag_after"], state["already_rooted_after"]) == (1, 1)
            args.output.with_suffix(".apfs-inspection.json").write_text(json.dumps(state, indent=2) + "\n")
            if state.get("adapter_applied"):
                print("Experimental RAM BaseSystem classification applied:", state, flush=True)
                return True
            print("APFS root inspection suspended:", state, flush=True)
            return False

        hypervisor.handle_brk = inspect_apfs_root
        proxy.write32(physical_address, 0xd4200000 | (0x4243 << 5))
        proxy.dc_cvau(physical_address, 4)
        proxy.ic_ivau(physical_address, 4)
        apfs_inspection = {"address": hex(trap_address), "physical_address": hex(physical_address),
                           "original_instruction": hex(expected_instruction), "one_shot": True}
    if args.guest_memory_gib is not None:
        hypervisor.tba.mem_size = min(original_memory_size, args.guest_memory_gib * 1024 ** 3)
        hypervisor.tba.mem_size_actual = hypervisor.tba.mem_size
    symbols = hypervisor.symbol_dict
    hypervisor.sptm_symbols = tuple(symbols["com.apple.kernel:" + name] for name in ("_cons_ops", "_PAGE_SHIFT_CONST", "__TEXT")) + tuple(symbols.get("com.apple.kernel:" + name, 0) for name in ("_arm_amx_version", "__cpu_capabilities"))
    carveouts = []
    cursor = proxy.mcc_get_carveouts()
    for index in range(256):
        start, length = proxy.read64(cursor), proxy.read64(cursor + 8)
        if not start:
            break
        carveouts.append((start, length))
        cursor += 16
    else:
        raise ValueError("unterminated carveout table")
    reservation_size = isc_media[2]["total_size"] if isc_media else size
    layout = plan_ramdisk(hypervisor.tba.phys_base, hypervisor.tba.mem_size,
                          hypervisor.tba.top_of_kernel_data, reservation_size, carveouts)
    layout["ramdisk_size"] = size
    layout["reserved_payload_size"] = reservation_size
    address = layout["ramdisk_address"]
    iokit_ram_root = None
    if args.iokit_ram_root:
        extents = [(address, size)]
        if isc_media:
            prefix, suffix, media_layout, isc_digest = isc_media
            prefix_address = address + size
            isc_address = prefix_address + len(prefix)
            resources_address = isc_address + media_layout["isc_size"]
            suffix_address = resources_address + media_layout["resources_size"]
            extents = [(prefix_address, len(prefix)), (address, size),
                       (isc_address, media_layout["isc_size"])]
            if args.resources_image:
                extents.append((resources_address, media_layout["resources_size"]))
            extents.append((suffix_address, len(suffix)))
            if suffix_address + len(suffix) > layout["reserved_end"]:
                raise ValueError("scatter image exceeds reserved guest memory")
        image_size = sum(length for start, length in extents)
        hypervisor.adt["/chosen"].boot_ramdmg_size = struct.pack("<Q", image_size)
        hypervisor.adt["/chosen"].boot_ramdmg_extents = b"".join(struct.pack("<QQ", *extent) for extent in extents)
        iokit_ram_root = {"address": address, "size": size, "extent_count": 1,
                          "source": "pinned 25G83 di_root_ramfile consumes chosen boot-ramdmg-size and boot-ramdmg-extents"}
        iokit_ram_root.update({"image_size": image_size, "extents": extents,
                              "extent_count": len(extents), "isc_presented": bool(isc_media)})
        if isc_media:
            iokit_ram_root.update({"isc_sha256": isc_digest, "gpt_layout": media_layout,
                                  "live_isc_atomic_consistency_verified": False})
        print("Configured experimental native IOKit RAM image descriptor:", iokit_ram_root, flush=True)
    print("Validated RAM root layout:", json.dumps(layout), flush=True)
    with args.ramdisk.open("rb") as image:
        offset = 0
        while chunk := image.read(16 * 1024 * 1024):
            utils.compressed_writemem(address + offset, chunk)
            offset += len(chunk)
            print(f"Recovery RAM disk uploaded: {offset}/{size}", flush=True)
    if interface.readmem(address + 32, 16) != superblock_header:
        raise ValueError("RAM root superblock readback mismatch")
    if isc_media:
        for target, data in [(prefix_address, prefix), (suffix_address, suffix)]:
            utils.compressed_writemem(target, data)
            if interface.readmem(target, len(data)) != data:
                raise ValueError("RAM GPT metadata readback mismatch")
        with args.isc_image.open("rb") as image:
            offset = 0
            while chunk := image.read(16 * 1024 * 1024):
                utils.compressed_writemem(isc_address + offset, chunk)
                offset += len(chunk)
                print(f"iSC RAM image uploaded: {offset}/{media_layout['isc_size']}", flush=True)
        with args.isc_image.open("rb") as image:
            expected = image.read(4096)
        if interface.readmem(isc_address, len(expected)) != expected:
            raise ValueError("RAM iSC superblock readback mismatch")
        if args.resources_image:
            with args.resources_image.open("rb") as image:
                offset = 0
                while chunk := image.read(16 * 1024 * 1024):
                    utils.compressed_writemem(resources_address + offset, chunk)
                    offset += len(chunk)
                    print(f"Guest resources uploaded: {offset}/{media_layout['resources_size']}", flush=True)
        hypervisor.add_tracer(irange(prefix_address, reservation_size - size), "ISC-RAM-MEDIA", TraceMode.OFF)
    hypervisor.adt["/chosen/memory-map"].RAMDisk = struct.pack("<QQ", address, size)
    hypervisor.add_tracer(irange(address, size), "RECOVERY-RAMDISK", TraceMode.OFF)
    hypervisor.tba.top_of_kernel_data = layout["reserved_end"]
    structures = {1: BootArgs_r1, 2: BootArgs_r2, 3: BootArgs_r3}
    structure = structures[hypervisor.tba.revision]
    bootargs_address = hypervisor.guest_base + hypervisor.bootargs_off
    interface.writemem(bootargs_address, structure.build(hypervisor.tba))
    actual = interface.readstruct(bootargs_address, structure)
    if (actual.phys_base, actual.mem_size, actual.top_of_kernel_data) != (layout["physical_base"], hypervisor.tba.mem_size, layout["reserved_end"]):
        raise ValueError("serialized guest BootArgs readback mismatch")
    adt = hypervisor.adt.build()
    if len(adt) > ((utils.ba.devtree_size + 0x3fff) & ~0x3fff):
        raise ValueError("guest ADT exceeds reserved capacity")
    interface.writemem(hypervisor.adt_base, adt)
    if interface.readmem(hypervisor.adt_base, len(adt)) != adt:
        raise ValueError("guest ADT readback mismatch")
    args.output.with_suffix(".adt.bin").write_bytes(adt)
    report = {"root_sha256": digest, "kernel_sha256": kernel_digest, "layout": layout, "bootargs_readback_verified": True,
              "file_hashes_verified_this_run": not args.skip_file_hashes,
              "original_memory_size": original_memory_size, "guest_memory_size": hypervisor.tba.mem_size,
              "ramdisk_superblock_readback_verified": True, "ssd_nodes_removed": removed,
              "adt_address": hypervisor.adt_base, "bootargs_address": bootargs_address,
              "adt_readback_verified": True,
              "guest_start_attempted": False, "guest_started": False, "macos_boot_verified": False,
              "guest_cpus_requested": args.guest_cpus, "guest_bootargs": guest_bootargs,
              "graphics_requested": args.graphics, "boot_video_display": actual.video.display,
              "resources_image": str(args.resources_image) if args.resources_image else None,
              "root_authentication": root_auth_report, "apfs_inspection": apfs_inspection,
              "boot_uuid_alignment": boot_uuid_report, "iokit_ram_root": iokit_ram_root}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    if args.prepare_only:
        interface.nop()
        proxy.nop()
        print("RAM root prepared; guest not started", flush=True)
        return
    print(f"Starting Recovery XNU/SPTM guest, RAMDisk={address:#x}, size={size}", flush=True)
    report["guest_start_attempted"] = True
    report["guest_started"] = None
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    try:
        hypervisor.start()
    except Exception as error:
        report["guest_start_error"] = str(error)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        raise
    report["guest_start_returned"] = True
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print("Guest returned to hypervisor; macOS boot is not automatically verified", flush=True)


if __name__ == "__main__":
    main()
