#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'usage: m4-experiment-record <name> [description]\n' >&2
  exit 2
}

name=${1:-}
description=${2:-}
[[ -n "$name" ]] || usage

root=${M4_LINUX_ROOT:-$(git rev-parse --show-toplevel)}
timestamp=$(date -u +%Y%m%dT%H%M%SZ)
experiment_dir="$root/experiments/${timestamp}-${name}"
mkdir -p "$experiment_dir/raw" "$experiment_dir/build"

cat > "$experiment_dir/metadata.json" <<EOF
{
  "name": $(jq -Rn --arg value "$name" '$value'),
  "description": $(jq -Rn --arg value "$description" '$value'),
  "created_at": $(jq -Rn --arg value "$(date -u +%Y-%m-%dT%H:%M:%SZ)" '$value'),
  "host": $(jq -Rn --arg value "$(uname -a)" '$value'),
  "repo_revision": $(jq -Rn --arg value "$(git -C "$root" rev-parse HEAD 2>/dev/null || printf unknown)" '$value')
}
EOF

{
  printf '# Experiment %s\n\n' "$name"
  printf '%s\n\n' "$description"
  printf '%s\n\n' "Created: \`$(date -u +%Y-%m-%dT%H:%M:%SZ)\`"
  printf '## Hardware\n\n- Model: M4 MacBook Air, 32 GB RAM, 2 TB SSD\n- SoC: T8132 (to verify from ADT/firmware)\n- Firmware: record exact build before every run\n\n'
  printf '## Commands\n\n```text\n'
  printf '# Fill in the exact command and environment used for this run.\n'
  printf '```\n\n## Result\n\n- Status: pending\n- First failing stage: unknown\n- Log: raw/\n'
} > "$experiment_dir/REPORT.md"

printf '%s\n' "$experiment_dir"
