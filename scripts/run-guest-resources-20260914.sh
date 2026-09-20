#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
exec nix develop --command bash -c '
exec sudo -n env PYTHONPATH="$PYTHONPATH" "$(command -v python3)" \
  scripts/run-recovery-guest.py \
  artifacts/current-25G83-post-restore-20260914/kernelcache-25G83.macho \
  artifacts/current-25G83-post-restore-20260914/recovery-25G83.apfs.raw \
  --root-manifest artifacts/current-25G83-post-restore-20260914/recovery-25G83.apfs.json \
  --kernel-sha256 f42ad6f51d130141095a94b4749d128d648f2be2ac0c291bf492ac1c64e5875d \
  --skip-file-hashes \
  --output experiments/2026-09-14-reinstall-retained/raw/guest-resources-run-1/guest.json \
  --guest-memory-gib 16 --guest-cpus 10 \
  --recovery-root-hash artifacts/current-25G83-post-restore-20260914/official/Firmware/022-22048-093.dmg.aea.root_hash \
  --recovery-root-hash-sha256 577661fd264e5745736d4d31ff14598c5ad1f7360fad5092f79ac04b7562e8d9 \
  --inspect-apfs-root --direct-basesystem-root --ram-root-boot-uuid --iokit-ram-root \
  --isc-image /home/sequencer/m4-linux-backups/20260914-clean-123915/current-isc/isc.raw \
  --isc-manifest /home/sequencer/m4-linux-backups/20260914-clean-123915/current-isc/manifest.json \
  --resources-image experiments/2026-09-14-reinstall-retained/raw/guest-resources-2/resources.fat \
  --extra-bootargs "serial=3 -s" \
  --console-log experiments/2026-09-14-reinstall-retained/raw/guest-resources-run-1/console.log \
  --proxyclient result/share/m1n1-sptm/proxyclient
'
