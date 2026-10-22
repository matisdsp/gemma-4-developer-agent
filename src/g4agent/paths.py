"""Filesystem layout. Competition files live outside version control; override with G4_DATA."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get("G4_DATA", ROOT / "data"))

AGENT = ROOT / "agent"  # the submission source: agent.yaml at its root
SUBMISSIONS = ROOT / "submissions"
RESULTS = ROOT / "results"
REPORTS = ROOT / "reports"
LEDGER = REPORTS / "ledger.jsonl"
