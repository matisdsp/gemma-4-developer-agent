#!/bin/bash
# Upload what a Modal evaluation needs to the private Volume g4agent-data.
#   cloud/upload.sh reports/modal_pool_40.txt     # tasks.jsonl, data/wheels, those snapshots
#   cloud/upload.sh --model gemma-4-e4b-it-qat-w4a16-ct data/modal/e4b   # model weights dir
# Delete everything afterwards: modal volume delete g4agent-data
set -euo pipefail
cd "$(dirname "$0")/.."
M=~/.local/bin/modal
V=g4agent-data
C=/input/comp/gemma-4-developer-agent
$M volume create $V 2>/dev/null || true
if [ "${1:-}" = "--model" ]; then
  $M volume put --force $V "$3" "/input/models/$2"
  exit 0
fi
$M volume put --force $V data/tasks.jsonl $C/tasks.jsonl
$M volume put --force $V data/wheels $C/wheels
while read -r id; do
  [ -n "$id" ] || continue
  for f in data/snapshots/"$id".*; do
    $M volume put --force $V "$f" "$C/snapshots/$(basename "$f")"
  done
done < "$1"
