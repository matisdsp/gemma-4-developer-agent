#!/bin/bash
# Run the official harness on the 129 public tasks with agent/ as the submission.
#
# Needs an OpenAI-compatible server for the declared model (default http://localhost:8000/v1,
# override with LOCAL_INFERENCE_URL, or map the alias in models.local.yaml) and the sandbox image
# (scripts/build_sandbox.sh). Extra arguments go to `swegemma eval`, e.g.:
#   scripts/eval_local.sh --task-id fastapi_11194 --max-time-minutes 10
set -euo pipefail
cd "$(dirname "$0")/.."
run=results/$(date +%Y%m%d-%H%M%S)
uv run swegemma eval \
  --tasks data/tasks.jsonl \
  --snapshots-dir data/snapshots \
  --submission-dir agent \
  --results-dir "$run" \
  --sandbox docker \
  --models-yaml models.local.yaml \
  "$@"
echo "results in $run (summary.json, patches/, traces/)"
