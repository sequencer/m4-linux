# 2026-09-20 NixOS RAM root checkpoint

## Verified on J713 / T8132

- Linux 7.1.13 boots through the RAM-loaded Gravity bootloader into NixOS stage2 and systemd.
- `/` is tmpfs; `/nix/store` is a read-only loop-mounted squashfs. This is not an SSD installation.
- `m4-linux login:` accepts `root` with an empty password over `/dev/ttyKIS0`.
- Both `getty@tty1` and `serial-getty@ttyKIS0` are active. The local screen displays the login interface.
- KIS remains interactive; no USB gadget or SSH server is needed.
- See `boot.json` for actual kernel, DTB, initrd and command line; `boot-console.log` is the captured host session.
- Earlier KIS raw-byte roundtrip, terminal controls and host reconnect tests are in `../2026-09-20-kis-tty/`.

## Known gaps, not fixed in this checkpoint

- Built-in keyboard is unavailable: `/proc/bus/input/devices` is empty and `/dev/input` does not exist. The live device tree has no MTP / keyboard / DockChannel input nodes.
- The original kernel provides DockChannel HID and Apple HID modules, but the current minimal RAM filesystem does not include that input-driver chain. Loading `hid-apple` alone cannot create the missing platform devices.
- The previously captured Apple ADT identifies `dockchannel-mtp/mtp-transport/keyboard`, an MTP ASC v6, and `dart-mtp`. These are distinct from the working KIS debug channel. MTP device-tree resources, mailbox/DART integration, HID modules and initialization/firmware requirements still need bring-up; older SoC addresses must not be copied verbatim.
- `systemd-sysctl.service` fails because `vm/mmap_rnd_bits=33` is rejected. This kernel has `CONFIG_ARCH_MMAP_RND_BITS_MAX=31` and currently reports 18. The system is therefore degraded despite working gettys.
- Early stage2 reported `/dev/fd/63: No such file or directory`; custom stage1 still needs the standard `/dev/fd` links before entering stage2.
- Only one CPU is enabled by the boot arguments. This checkpoint does not establish GPU, storage, networking or built-in input support.

## Resume

Build with `nix build .#nixos-root-initramfs --out-link results/nixos-root-initramfs`.
Use `scripts/boot-linux-ram.py` with the kernel/DTB listed in `boot.json`, this initrd, `--device /dev/m1n1`, and the Gravity proxyclient after RAM chainloading the bootloader.
Do not send m1n1 proxy commands while native Linux owns KIS, or open a second reader on the same host PTY.

The flake currently depends on local Nix-store kernel module/development outputs and the kernel Image lives in the sibling `colmena-jiuyang` build output. A Git clone alone does not restore those binary inputs. Firmware, raw memory captures, credentials and large build outputs are excluded from Git.

This checkpoint does not change SSD contents, boot policy or NVRAM. Historical Recovery/macOS guest scripts are retained as experiment history, not instructions to rerun them.
