import argparse
import json
from pathlib import Path
import sys

from serial.tools import list_ports


def main():
    parser = argparse.ArgumentParser(description="Boot a single-core Linux RAM system through m1n1")
    parser.add_argument("kernel", type=Path)
    parser.add_argument("dtb", type=Path)
    parser.add_argument("initrd", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--device")
    parser.add_argument("--proxyclient", type=Path,
                        default=Path("result/share/m1n1-sptm/proxyclient"))
    args = parser.parse_args()
    kernel = args.kernel.read_bytes()
    dtb = args.dtb.read_bytes()
    initrd = args.initrd.read_bytes()
    if kernel[56:60] != b"ARM\x64":
        parser.error("Expected uncompressed arm64 Linux Image")
    ports = sorted((port for port in list_ports.comports()
                    if (port.vid, port.pid) == (0x1209, 0x316D)),
                   key=lambda port: port.device)
    if not args.device and (len(ports) != 2 or any(port.serial_number != "M49KYH65C9" for port in ports)):
        parser.error("Expected the M4 Air m1n1 dual USB serial interface")
    sys.path.insert(0, str(args.proxyclient.resolve()))
    from m1n1.proxy import M1N1Proxy, UartInterface, IODEV
    from m1n1.proxyutils import ProxyUtils, bootstrap_port
    from m1n1.sysreg import DAIF

    interface = UartInterface(args.device or ports[0].device)
    proxy = M1N1Proxy(interface)
    bootstrap_port(interface, proxy)
    utils = ProxyUtils(proxy)
    iodev = proxy.iodev_whoami()
    earlycon = "earlycon=dockchannel,0x38812c000 console=ttyKIS0" if iodev == IODEV.DOCKCHANNEL_UART else "earlycon"
    bootargs = (f"console=tty0 {earlycon} maxcpus=1 idle=nop arm64.nowfxt arm64.nosme "
                "clk_ignore_unused pd_ignore_unused quiet loglevel=1 "
                "panic=0 rdinit=/init")
    args.output.mkdir(parents=True, exist_ok=True)
    report = {"kernel": str(args.kernel.resolve()), "dtb": str(args.dtb.resolve()),
              "initrd": str(args.initrd.resolve()), "bootargs": bootargs,
              "linux_boot_verified": False, "stage": "uploading"}

    def record(stage):
        report["stage"] = stage
        (args.output / "boot.json").write_text(json.dumps(report, indent=2) + "\n")
        print(stage, flush=True)

    record("uploading")
    dtb_address = utils.malloc(len(dtb))
    initrd_address = utils.memalign(65536, len(initrd))
    kernel_address = utils.memalign(2 * 1024 * 1024, 512 * 1024 * 1024)
    interface.writemem(dtb_address, dtb)
    interface.writemem(initrd_address, initrd)
    proxy.kboot_set_chosen("bootargs", bootargs)
    proxy.kboot_set_initrd(initrd_address, len(initrd))
    record("preparing_device_tree")
    result = proxy.kboot_prepare_dt(dtb_address)
    if result:
        record(f"device_tree_failed_{result}")
        raise RuntimeError(f"m1n1 kboot_prepare_dt returned {result}")
    record("uploading_kernel")
    interface.dev.timeout = 40
    interface.writemem(kernel_address, kernel)
    proxy.dc_cvau(kernel_address, len(kernel))
    proxy.ic_ivau(kernel_address, len(kernel))
    utils.msr(DAIF, 0xC0)
    record("enabling_ane_power")
    result = proxy.pmgr_adt_power_enable("/arm-io/ane")
    if result:
        record(f"ane_power_failed_{result}")
        raise RuntimeError(f"m1n1 ANE power enable returned {result}")
    report.update(kernel_address=kernel_address, initrd_address=initrd_address,
                  dtb_input_address=dtb_address)
    record("requesting_native_linux_handoff")
    proxy.kboot_boot(kernel_address)
    record("handoff_command_returned_waiting_for_console")
    interface.ttymode()


if __name__ == "__main__":
    main()
