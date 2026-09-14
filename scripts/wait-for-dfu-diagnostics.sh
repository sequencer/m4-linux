#!/usr/bin/env bash
set -euo pipefail
umask 077

project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd -- "$project_root"
output=${1:?Usage: wait-for-dfu-diagnostics.sh OUTPUT [WAIT_SECONDS]}
wait_seconds=${2:-21600}
if [[ ! "$wait_seconds" =~ ^[1-9][0-9]*$ ]] || (( wait_seconds > 43200 )); then
    printf 'WAIT_SECONDS must be between 1 and 43200\n' >&2
    exit 2
fi
output=$(realpath -m -- "$output")
if [[ "$output" != "$project_root/experiments/2026-09-13-iokit-ram-root/raw/"* ]] || [[ -e "$output" ]]; then
    printf 'Choose a fresh output directory inside the ignored experiment raw directory\n' >&2
    exit 2
fi
exec 9> "$project_root/experiments/2026-09-13-iokit-ram-root/raw/dfu-diagnostic-watcher.lock"
if ! flock -n 9; then
    printf 'Another DFU diagnostic watcher holds the lock; no upload\n' >&2
    exit 1
fi
tool=$(realpath -- "$project_root/results/firmware-diagnostic-tools/bin/idevicerestore")
query_tool=$(realpath -- "$project_root/results/dfu-command-diagnostic-tools/bin/irecovery")
ipsw=$(realpath -- "$project_root/artifacts/apple/25G83/UniversalMac_26.6.2_25G83_Restore.ipsw")
if [[ ! -x "$tool" || ! -x "$query_tool" || ! -r "$ipsw" ]]; then
    printf 'Build the pinned diagnostic tools and download the pinned IPSW first\n' >&2
    exit 2
fi
mkdir -- "$output"
exec > "$output/watcher.log" 2>&1
printf '%s waiting for verified M4 DFU; limit=%ss; one temporary load, no StartRestore\n' "$(date -u +%FT%TZ)" "$wait_seconds"
printf 'loader=%s\nquery_tool=%s\nipsw=%s\n' "$tool" "$query_tool" "$ipsw"
sha256sum -- "$tool" "$query_tool" > "$output/tools.sha256"
deadline=$((SECONDS + wait_seconds))
last_identity=
while (( SECONDS < deadline )); do
    for device in /sys/bus/usb/devices/*; do
        [[ -r "$device/idVendor" && -r "$device/idProduct" ]] || continue
        vendor=$(cat "$device/idVendor" 2>/dev/null) || continue
        product=$(cat "$device/idProduct" 2>/dev/null) || continue
        [[ "$vendor" == 05ac && "$product" =~ ^(1227|f014|1881)$ ]] || continue
        number=$(cat "$device/devnum" 2>/dev/null) || continue
        identity="$device:$product:$number"
        [[ "$identity" != "$last_identity" ]] || continue
        last_identity=$identity
        if ps -C idevicerestore -C kisd -o comm=; then
            printf '%s competing restore/debug process; stopping without upload\n' "$(date -u +%FT%TZ)"
            exit 1
        fi
        printf '%s candidate=%s\n' "$(date -u +%FT%TZ)" "$identity"
        if ! timeout 15s sudo -n "$query_tool" -q > "$output/device.txt" 2>&1; then
            printf 'Device identity query failed; no upload\n'
            continue
        fi
        if ! rg -Fqx 'PRODUCT: Mac16,12' "$output/device.txt" || ! rg -Fqx 'MODEL: j713ap' "$output/device.txt"; then
            printf 'Unexpected product/model; stopping without upload\n'
            exit 1
        fi
        if rg -Fqx 'MODE: DFU' "$output/device.txt"; then
            rg -q '^ECID: 0x0*a10a426b9001c$' "$output/device.txt" || exit 1
            rg -Fqx 'CPID: 0x8132' "$output/device.txt" || exit 1
            rg -Fqx 'BDID: 0x2c' "$output/device.txt" || exit 1
            restore_ecid=0xA10A426B9001C
        elif rg -Fqx 'MODE: Port DFU' "$output/device.txt"; then
            rg -Fqx 'ECID: 0x3fc75d711905dde9' "$output/device.txt" || exit 1
            restore_ecid=0x3fc75d711905dde9
        else
            printf 'Not DFU; no upload\n'
            continue
        fi
        printf '%s identity verified; starting temporary diagnostic loader\n' "$(date -u +%FT%TZ)"
        set +e
        timeout --signal=TERM --kill-after=10s 900s sudo -n "$tool" \
            --ecid "$restore_ecid" --no-restore --plain-progress --debug --debug \
            --logfile "$output/loader.log" "$ipsw" > "$output/loader.stdout" 2>&1
        loader_status=$?
        set -e
        printf '%s loader_exit=%s; no automatic retry/Revive/Erase\n' "$(date -u +%FT%TZ)" "$loader_status"
        exit "$loader_status"
    done
    sleep 0.25
done
printf '%s DFU wait expired; no upload\n' "$(date -u +%FT%TZ)"
exit 124
