#!/bin/bash
# Extract only *.py files (excluding .git) from each snapshot tgz into snap/<instance_id>/ . Idempotent.
D="$(cd "$(dirname "$0")/../../../.." && pwd)/data"
A=$(cd "$(dirname "$0")" && pwd)
ext() {
  id=$(basename "$1" .tgz); out="$A/snap/$id"
  [ -f "$out/.done" ] && exit 0
  mkdir -p "$out"
  tar -xzf "$1" -C "$out" --include '*.py' --exclude '.git' --exclude './.git/*' 2>/dev/null
  touch "$out/.done"
}
export -f ext; export A
ls $D/snapshots/*.tgz | xargs -n1 -P4 bash -c 'ext "$0"'
