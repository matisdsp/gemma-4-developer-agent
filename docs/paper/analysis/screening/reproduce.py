"""Reproduce every number of the screening paper on CPU, from the published per-attempt records.

    python3 -I docs/paper/analysis/screening/reproduce.py              # primary analysis
    python3 -I docs/paper/analysis/screening/reproduce.py --explore    # exploratory numbers

The frozen analysis script (`analyze.py`, pinned by SHA-256 in the pre-registration) and the
exploratory script (`explore.py`) read agent traces. This wrapper feeds them the rows of
`docs/paper/records/screening_attempts.csv` instead and runs them unchanged, so the output matches
the analysis of the traces.
"""

import argparse
import csv
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RECORDS = ROOT / "docs" / "paper" / "records" / "screening_attempts.csv"
BOOLS = {"resolved", "nonempty", "edited", "spec_stated", "repro_before_edit", "check_after_edit",
         "last_pytest_real", "last_pytest_green", "last_pytest_empty", "compile_after_edit",
         "syntax_broken"}
FLOATS = {"agent_s", "pytest_runs_tests", "completion_tokens_per_call"}
INTS = {"rep", "tool_calls", "calls_after_first_edit", "spec_terms_named", "first_message_chars"}


def module(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_records(path):
    rows = []
    with open(path, newline="") as f:
        for rec in csv.DictReader(f):
            row = {}
            for key, value in rec.items():
                if value == "":
                    row[key] = None
                elif key in BOOLS:
                    row[key] = value == "True"
                elif key in FLOATS:
                    row[key] = float(value)
                elif key in INTS:
                    row[key] = int(value)
                else:
                    row[key] = value
            row["error"] = row.get("error") or ""
            rows.append(row)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--records", type=Path, default=RECORDS)
    ap.add_argument("--explore", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()
    rows = read_records(args.records)
    analyze = module("analyze")

    def load(run_dirs, design, tasks, tasks_jsonl):
        return [r for r in rows if r["task"] in tasks and r["variant"] in design], 0

    analyze.load = load
    # The frozen script loops over a set of two names, whose order varies between Python runs and
    # shifts the bootstrap draws of the exploratory interactions. Use the order of the reported run.
    analyze.CLEAR_PARTNERS = ["imposed_verification", "worked_example"]
    common = ["--runs", "records", "--design", str(ROOT / "variants/screening/design.json"),
              "--tasks", str(ROOT / "reports/screening_tasks_72.txt"), "--tasks-jsonl", "unused"]
    if args.explore:
        explore = module("explore")
        explore.analyze = analyze
        sys.argv = ["explore.py", *common, "--out", args.out or "screening_explore.json"]
        explore.main()
    else:
        sys.argv = ["analyze.py", *common] + (["--out", args.out] if args.out else [])
        analyze.main()


if __name__ == "__main__":
    main()
