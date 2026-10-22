# gemma-4-developer-agent

A software engineering agent built on Gemma 4 for the
[Gemma 4 Developer Agent](https://www.kaggle.com/competitions/gemma-4-developer-agent) Kaggle
competition: given a real GitHub issue on fastapi, rich, requests or httpx, the agent edits the
repository offline and submits a patch, scored SWE-bench style (the hidden tests must pass).

A submission is declarative: `agent.yaml`, prompts, sub-agents, skills and optional LoRA
adapters, compiled by the organisers' harness into a Google ADK agent that runs on one Gemma 4
model (31B, 12B, E4B or E2B, int4) served by vLLM on 4x L4, with a 32k context and 12 hours for
the whole hidden test set.

## Layout

- `agent/`: the submission source (starts as the organisers' sample, without its dummy adapters).
- `src/g4agent/package.py`: validation with the harness's own checks, and packaging into
  `submissions/submission.zip` (`scripts/build_submission.py`).
- `scripts/fetch_harness.sh`: fetches the official harness wheels (`swegemma`, `adk-submission`,
  `adk-eval-core`, `google-adk`) from the competition's wheelhouse dataset into `vendor/`.
- `scripts/build_sandbox.sh`: builds the `swebench-sandbox:latest` Docker image the tasks run in.
- `scripts/eval_local.sh`: runs `swegemma eval` on the 129 public tasks against a local
  OpenAI-compatible server (`models.local.yaml` maps the declared model to it).

## Setup

```bash
kaggle competitions download -c gemma-4-developer-agent -p data && unzip -oq data/*.zip -d data
scripts/fetch_harness.sh
uv sync
uv run pytest
scripts/build_sandbox.sh
uv run python scripts/build_submission.py
```

The competition data (20 GB of repository snapshots) is not redistributed here.
