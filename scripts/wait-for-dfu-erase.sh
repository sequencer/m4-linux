#!/usr/bin/env bash
set -euo pipefail
umask 077

project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd -- "$project_root"
if [[ ${1:-} != --authorized-erase || $# -lt 2 || $# -gt 4 ]]; then
    printf 'Usage: wait-for-dfu-erase.sh --authorized-erase OUTPUT [WAIT_SECONDS] [diagnostic|matched-tty]\nErases all data on the verified M4 target; never retries automatically.\n' >&2
    exit 2
fi
output=$(realpath -m -- "$2")
wait_seconds=${3:-1800}
profile=${4:-diagnostic}
if [[ ! "$wait_seconds" =~ ^[1-9][0-9]*$ ]] || (( wait_seconds > 1800 )); then
    printf 'WAIT_SECONDS must be between 1 and 1800\n' >&2
    exit 2
fi
if [[ "$profile" != diagnostic && "$profile" != matched-tty ]]; then
    printf 'Choose diagnostic or matched-tty profile\n' >&2
    exit 2
fi
if [[ "$profile" == matched-tty ]]; then
    if [[ ! -t 0 ]]; then
        printf 'matched-tty requires interactive stdin; no restore\n' >&2
        exit 2
    fi
    command -v script > /dev/null
fi
if [[ "$output" != "$project_root/experiments/2026-09-13-iokit-ram-root/raw/"* || -e "$output" ]]; then
    printf 'Choose a fresh directory inside the ignored experiment raw directory\n' >&2
    exit 2
fi
exec 9> "$project_root/experiments/2026-09-13-iokit-ram-root/raw/dfu-diagnostic-watcher.lock"
if ! flock -n 9; then
    printf 'Another DFU watcher holds the lock; no restore\n' >&2
    exit 1
fi
if ps -C idevicerestore -C kisd -o comm=; then
    printf 'Competing restore/debug process; no restore\n' >&2
    exit 1
fi
tool=$(realpath -- "$project_root/results/firmware-upstream-tools/bin/idevicerestore")
query_tool=$(realpath -- "$project_root/results/dfu-tools/bin/irecovery")
ipsw=$(realpath -- "$project_root/artifacts/apple/25G83/UniversalMac_26.6.2_25G83_Restore.ipsw")
if [[ "$tool" != /nix/store/a6p6a74jfnm1nacbzkmq91p17wy2pb4h-idevicerestore-1.0.0-unstable-2026-09-07/bin/idevicerestore ||
      "$query_tool" != /nix/store/2g1pmkp7v2y3mcyzgnavdk7sr6ykg7l7-libirecovery-1.3.1-unstable-2026-08-23/bin/irecovery ||
      "$ipsw" != /nix/store/gy1rm7g6m5xv4ba9qjvnjvns3zvb2da9-UniversalMac_26.6.2_25G83_Restore.ipsw ]]; then
    printf 'Unexpected tool or IPSW store path; no restore\n' >&2
    exit 1
fi
if [[ ! -x "$tool" || ! -x "$query_tool" || ! -r "$ipsw" || ! -d /home/sequencer/liqi_backup ]]; then
    printf 'Missing baseline tools, IPSW, or M1 backup directory; no restore\n' >&2
    exit 1
fi
printf '%s  %s\n' \
    4c6febb6a5a5f9cef7df149965fd3a7a97af60d8926bc2b6a299cce15225701b "$tool" \
    1db8b28444e23a616de9bd59c2c67ca4bf1b61e4737f0766ac1504d2bcd9050a "$query_tool" | sha256sum --check --status
sudo -n true
mkdir -- "$output"
exec > "$output/watcher.log" 2>&1
printf '%s authorized destructive Restore; waiting at most %ss for verified M4 DFU\n' "$(date -u +%FT%TZ)" "$wait_seconds"
printf 'profile=%s\n' "$profile"
printf 'loader=%s\nquery_tool=%s\nipsw=%s\nM1 backup is not a complete disk backup; Pictures excluded.\n' "$tool" "$query_tool" "$ipsw"
sha256sum -- "$tool" "$query_tool" > "$output/tools.sha256"
env -u LD_LIBRARY_PATH -u LD_PRELOAD ldd "$tool" > "$output/loader.ldd"
rg -Fq 'libirecovery-1.0.so.5 => /nix/store/2g1pmkp7v2y3mcyzgnavdk7sr6ykg7l7-libirecovery-1.3.1-unstable-2026-08-23/lib/libirecovery-1.0.so.5 ' "$output/loader.ldd"
deadline=$((SECONDS + wait_seconds))
while (( SECONDS < deadline )); do
    candidates=()
    for device in /sys/bus/usb/devices/*; do
        [[ -r "$device/idVendor" && -r "$device/idProduct" ]] || continue
        vendor=$(cat "$device/idVendor" 2>/dev/null) || continue
        product=$(cat "$device/idProduct" 2>/dev/null) || continue
        [[ "$vendor" == 05ac && "$product" =~ ^(1227|f014|1881|1281|190[1-5])$ ]] || continue
        candidates+=("$device:$product")
    done
    if (( ${#candidates[@]} > 1 )); then
        printf '%s multiple Apple recovery devices; stopping without restore\n' "$(date -u +%FT%TZ)"
        exit 1
    fi
    if (( ${#candidates[@]} == 1 )) && [[ "${candidates[0]}" =~ :(1227|f014)$ ]]; then
        if ps -C idevicerestore -C kisd -o comm=; then
            printf 'Competing restore/debug process; stopping without restore\n'
            exit 1
        fi
        printf '%s candidate=%s\n' "$(date -u +%FT%TZ)" "${candidates[0]}"
        if ! timeout 15s sudo -n env -u LD_LIBRARY_PATH -u LD_PRELOAD "$query_tool" -q > "$output/device.txt" 2>&1; then
            printf 'Identity query failed; stopping without restore\n'
            exit 1
        fi
        rg -Fqx 'PRODUCT: Mac16,12' "$output/device.txt"
        rg -Fqx 'MODEL: j713ap' "$output/device.txt"
        if rg -Fqx 'MODE: DFU' "$output/device.txt"; then
            rg -q '^ECID: 0x0*a10a426b9001c$' "$output/device.txt"
            rg -Fqx 'CPID: 0x8132' "$output/device.txt"
            rg -Fqx 'BDID: 0x2c' "$output/device.txt"
            restore_ecid=0xA10A426B9001C
        elif rg -Fqx 'MODE: Port DFU' "$output/device.txt"; then
            rg -Fqx 'ECID: 0x3fc75d711905dde9' "$output/device.txt"
            rg -Fqx 'CPID: 0x0022' "$output/device.txt"
            rg -Fqx 'BDID: 0x2c813200' "$output/device.txt"
            restore_ecid=0x3fc75d711905dde9
        else
            printf 'Not DFU; stopping without restore\n'
            exit 1
        fi
        printf '%s identity verified; starting upstream --erase; ecid=%s\n' "$(date -u +%FT%TZ)" "$restore_ecid"
        set +e
        if [[ "$profile" == matched-tty ]]; then
            printf -v restore_command '%q ' sudo -n env -u LD_LIBRARY_PATH -u LD_PRELOAD "$tool" \
                --erase --debug --ecid "$restore_ecid" \
                --variant 'Customer Erase Install (IPSW)' \
                --cache-path "$project_root/artifacts/apple/25G83/revive-cache" \
                --logfile "$output/restore.log" "$ipsw"
            printf '%s\n' "$restore_command" > "$output/restore.argv"
            script --quiet --return --flush --command "$restore_command" \
                "$output/restore.pty" > "$output/restore.stdout" 2>&1
        else
            sudo -n env -u LD_LIBRARY_PATH -u LD_PRELOAD "$tool" \
                --erase --ecid "$restore_ecid" --plain-progress --debug --debug \
                --logfile "$output/restore.log" "$ipsw" < /dev/null > "$output/restore.stdout" 2>&1
        fi
        restore_status=$?
        set -e
        printf '%s restore_exit=%s; no automatic retry; native boot verification still required\n' "$(date -u +%FT%TZ)" "$restore_status"
        if [[ -f "$output/restore.log" ]]; then
            sudo -n sha256sum -- "$output/restore.log" "$output/restore.stdout" > "$output/restore.sha256"
            if [[ -f "$output/restore.pty" ]]; then
                sha256sum -- "$output/restore.pty" >> "$output/restore.sha256"
            fi
        fi
        exit "$restore_status"
    fi
    sleep 0.5
done
printf '%s DFU wait expired; no restore/upload started\n' "$(date -u +%FT%TZ)"
exit 124
