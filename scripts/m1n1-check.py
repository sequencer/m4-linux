import argparse
import datetime
import json
from pathlib import Path
import sys

from serial.tools import list_ports


def main():
    parser = argparse.ArgumentParser(description="Check native m1n1 USB proxy without booting a payload")
    parser.add_argument("--device")
    parser.add_argument("--proxyclient", type=Path, default=Path(__file__).resolve().parent.parent / "result/share/m1n1-sptm/proxyclient")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not (args.proxyclient / "m1n1/proxy.py").is_file():
        parser.error("proxyclient missing; run nix build .#m1n1-sptm first")
    ports = sorted(
        (port for port in list_ports.comports() if (port.vid, port.pid) == (0x1209, 0x316D)),
        key=lambda port: port.device,
    )
    if args.device:
        selected = next((port for port in ports if port.device == args.device), None)
        if selected is None:
            parser.error("requested device is not an enumerated 1209:316d m1n1 port")
    else:
        if len(ports) != 2 or len({port.serial_number for port in ports}) != 1:
            parser.error("expected one m1n1 with two serial ports; reconnect or specify --device")
        selected = ports[0]
    sys.path.insert(0, str(args.proxyclient.resolve()))
    from m1n1.proxy import M1N1Proxy, UartInterface

    interface = UartInterface(selected.device)
    interface.nop()
    M1N1Proxy(interface).nop()
    result = {
        "time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "device": selected.device,
        "serial_number": selected.serial_number,
        "uart_nop": "ok",
        "proxy_nop": "ok",
        "linux_boot_verified": False,
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n")
    print(rendered)


if __name__ == "__main__":
    main()
