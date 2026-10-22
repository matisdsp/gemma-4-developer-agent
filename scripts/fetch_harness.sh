#!/bin/bash
# Fetch the official harness wheels (pure Python) from the competition's wheelhouse dataset.
# vLLM and the CUDA stack stay on Kaggle: local evaluation talks to any OpenAI-compatible server.
set -euo pipefail
cd "$(dirname "$0")/../vendor" 2>/dev/null || { mkdir -p "$(dirname "$0")/../vendor"; cd "$(dirname "$0")/../vendor"; }
mkdir -p wheels && cd wheels
for f in adk_eval_core-0.1.0-py3-none-any.whl adk_submission-0.2.13-py3-none-any.whl \
         google_adk-1.36.1-py3-none-any.whl swegemma-0.2.11-py3-none-any.whl; do
  [ -f "$f" ] || kaggle datasets download metric/gemma-4-developer-agent-wheelhouse -f "$f" -q -p .
done
ls -la
