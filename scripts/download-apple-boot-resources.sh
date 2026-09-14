#!/usr/bin/env bash
set -euo pipefail

directory=artifacts/apple/25G83
filename=UniversalMac_26.6.2_25G83_Restore.ipsw
url=https://updates.cdn-apple.com/2026SummerFCS/fullrestores/140-75212/A2A24B94-1FC1-45A3-93F7-C51B02AF1F4D/UniversalMac_26.6.2_25G83_Restore.ipsw
digest=885503b7f4b06609e9a512f2befd40f59730640a3f1233e3892d60affdd51c95

mkdir -p "$directory"
nix build '.#apple-download-tools^bin' --out-link results/apple-download-tools-bin
nix build .#apple-restore-catalog-20260913 --out-link "$directory/apple-restore-catalog.plist"
if [[ ! -e "$directory/$filename" ]]; then
    results/apple-download-tools-bin/bin/aria2c \
        --max-connection-per-server=16 --split=16 --min-split-size=64M \
        --file-allocation=none --continue=true --check-certificate=true \
        --checksum="sha-256=$digest" --summary-interval=60 \
        --dir="$directory" --out="$filename.download" "$url"
    nix store add --mode flat --name "$filename" "$directory/$filename.download"
fi
nix build .#apple-m4-restore-25G83 --out-link "$directory/$filename"
printf '%s  %s\n' "$digest" "$directory/$filename" | nix develop --command sha256sum -c -
if [[ ! -e "$directory/j713" ]]; then
    nix develop --command python scripts/extract-apple-boot-resources.py "$directory/$filename"
fi
nix develop --command bash -c 'cd artifacts/apple/25G83/j713 && sha256sum -c SHA256SUMS'
mkdir -p "$directory/derived"
nix build .#ipsw-tools --out-link results/ipsw-tools
nix build .#apple-base-system-key-25G83 --out-link "$directory/derived/fcs-key-response.bin"
if [[ ! -e "$directory/derived/kernelcache-25G83.macho" ]]; then
    nix build .#m1n1-sptm --out-link results/m1n1-resource-tools
    nix develop --command python scripts/extract-kernelcache.py \
        "$directory/j713/kernelcache.release.mac16g" "$directory/derived/kernelcache-25G83.macho" \
        --proxyclient results/m1n1-resource-tools/share/m1n1-sptm/proxyclient \
        > "$directory/derived/kernel-symbols.json"
fi
if [[ ! -e "$directory/derived/sptm.t8132.bin" ]]; then
    results/ipsw-tools/bin/ipsw img4 im4p extract \
        "$directory/j713/Firmware/sptm.t8132.release.im4p" --output "$directory/derived/sptm.t8132.bin"
fi
if [[ ! -e "$directory/derived/txm.macosx.bin" ]]; then
    results/ipsw-tools/bin/ipsw img4 im4p extract \
        "$directory/j713/Firmware/txm.macosx.release.im4p" --output "$directory/derived/txm.macosx.bin"
fi
if [[ ! -e "$directory/derived/DeviceTree.j713ap.bin" ]]; then
    results/ipsw-tools/bin/ipsw img4 im4p extract \
        "$directory/j713/Firmware/all_flash/DeviceTree.j713ap.im4p" --output "$directory/derived/DeviceTree.j713ap.bin"
fi
if [[ ! -e "$directory/derived/022-22048-093.dmg" ]]; then
    nix develop --command ipsw fw aea --pem "$directory/derived/fcs-key-response.bin" \
        --output "$directory/derived" "$directory/j713/022-22048-093.dmg.aea"
fi
nix develop --command bash -c \
    'cd artifacts/apple/25G83/derived && sha256sum -c ../../../../experiments/2026-09-13-apple-25G83/DERIVED_SHA256SUMS'
