import argparse
import datetime
import json
from pathlib import Path
import sys

from sptm_timer import probe_timer


def main():
    parser = argparse.ArgumentParser(description="Initialize the M4 hypervisor without starting a guest")
    parser.add_argument("--device", default="/dev/ttyACM0")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--probe-timer", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "result/share/m1n1-sptm/proxyclient"))
    from m1n1.proxy import M1N1Proxy, UartInterface
    from m1n1.proxyutils import ProxyUtils, bootstrap_port
    from m1n1.hv import HV

    interface = UartInterface(args.device)
    proxy = M1N1Proxy(interface)
    bootstrap_port(interface, proxy)
    utils = ProxyUtils(proxy, heap_size=128 * 1024 * 1024)
    chosen = str(utils.adt["/chosen"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    chosen_path = args.output.with_suffix(".adt.txt")
    chosen_path.write_text(chosen + "\n")
    timer = None
    if args.probe_timer:
        timer = probe_timer(utils)
        interface.nop()
        proxy.nop()
        if not timer.get("readback_matches", False):
            report = {"time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      "device": args.device, "chip_id": utils.adt["/chosen"].chip_id,
                      "timer_probe": timer, "proxy_nop_after_probe": "ok",
                      "chosen_file": str(chosen_path), "hv_init": "not attempted",
                      "guest_started": False, "macos_boot_verified": False}
            args.output.write_text(json.dumps(report, indent=2) + "\n")
            print(json.dumps(report, indent=2), flush=True)
            raise SystemExit(2)
    hypervisor = HV(interface, proxy, utils)
    hypervisor.init()
    interface.nop()
    proxy.nop()
    report = {
        "time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "device": args.device,
        "chip_id": utils.adt["/chosen"].chip_id,
        "apple_sysregs_unlocked": bool(utils.cpu_features.apple_sysregs_unlocked),
        "hv_init": "ok",
        "proxy_nop_after_init": "ok",
        "chosen_file": str(chosen_path),
        "guest_started": False,
        "macos_boot_verified": False,
        "timer_probe": timer,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
