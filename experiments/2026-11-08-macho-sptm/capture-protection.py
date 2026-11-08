import datetime
import json
from pathlib import Path
import re
import sys


source = Path("/home/sequencer/projects/slop-linux/forks/m1n1")
sys.path.insert(0, str(source / "proxyclient"))
from m1n1.proxy import M1N1Proxy, ProxyError, UartInterface
from m1n1.proxyutils import ProxyUtils, bootstrap_port


interface = UartInterface("/dev/ttyACM0")
proxy = M1N1Proxy(interface)
bootstrap_port(interface, proxy)
utils = ProxyUtils(proxy, heap_size=128 * 1024 * 1024)
registers = {
    "CurrentEL": (3, 0, 4, 2, 2),
    "MIDR_EL1": (3, 0, 0, 0, 0),
    "MPIDR_EL1": (3, 0, 0, 0, 5),
    "S3_5_C15_C6_2": (3, 5, 15, 6, 2),
    "VM_TMR_FIQ_ENA_EL2": (3, 5, 15, 1, 3),
    "CTRR_A_LWR": (3, 4, 15, 2, 3),
    "CTRR_A_UPR": (3, 4, 15, 2, 4),
    "CTRR_B_LWR": (3, 4, 15, 1, 7),
    "CTRR_B_UPR": (3, 4, 15, 1, 6),
}
# Register encodings are the maintained M4 definitions, not guessed aliases.
for name, encoding in re.findall(
    r"#define (SYS_IMP_APL_\w+)\s+sys_reg\(([^)]+)\)",
    (source / "src/cpu_regs.h").read_text(),
):
    if "CTRR" in name or "CTXR" in name or "SPR_LOCKDOWN" in name:
        registers[name] = tuple(int(part.strip()) for part in encoding.split(","))

output = Path(__file__).parent / "raw/macho-v1-protection.jsonl"
with output.open("w") as log:
    def record(data):
        line = json.dumps(data)
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    record({
        "time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "m1n1_base": hex(utils.base),
        "chip_id": proxy.get_chipid(),
        "cpu_feature_table_apple_sysregs_unlocked": bool(utils.cpu_features.apple_sysregs_unlocked),
        "measurement_stage": "boot CPU, after m1n1 initialization",
    })
    for name, encoding in registers.items():
        try:
            record({"register": name, "encoding": encoding,
                    "value": f"0x{utils.mrs(encoding, silent=True):016x}"})
        except ProxyError as error:
            record({"register": name, "encoding": encoding, "exception": str(error)})
    for name in ("chip-id", "board-id", "firmware-version", "kernel-ctrr-to-be-enabled"):
        value = utils.adt["/chosen"].getprop(name)
        if isinstance(value, bytes):
            value = value.rstrip(b"\0").decode("ascii")
        record({"chosen_property": name, "value": value})
    record({"memory_map_entries": list(utils.adt["/chosen/memory-map"]._properties)})
    interface.nop()
    proxy.nop()
    record({"proxy_nop_after_reads": "ok"})
