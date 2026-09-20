import importlib.util
from pathlib import Path
import plistlib
import subprocess


def main():
    if subprocess.check_output(["sysctl", "-n", "hw.model"], text=True).strip() != "Mac16,12":
        raise ValueError("Wrong target model")
    info = plistlib.loads(subprocess.check_output(["diskutil", "info", "-plist", "disk0s5"]))
    if info["DiskUUID"] != "F322BE9F-F630-400D-B965-EB29A87BC3F6":
        raise ValueError("Wrong stub physical store")
    spec = importlib.util.spec_from_file_location(
        "stub_stage", Path(__file__).with_name("stage-linux-only-stub.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.GROUP = "530FE39B-6AE3-47D0-9168-29F1A7EE2763"
    module.CONTAINER = "FCD42C83-7878-4C61-BE47-322972C988CC"
    module.main()


if __name__ == "__main__":
    main()
