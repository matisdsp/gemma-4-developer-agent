"""Export one record per screening attempt, without any task text, for publication.

    python3 -I docs/paper/analysis/screening/export_records.py \
        --runs results/kaggle/g4agent-sc1/results results/kaggle/g4agent-sc2/results \
               results/kaggle/g4agent-sc3/results \
        --design variants/screening/design.json --tasks reports/screening_tasks_72.txt \
        --tasks-jsonl data/tasks.jsonl --out docs/paper/records/screening_attempts.csv

Each row holds the task id, the configuration, the outcome and the features the frozen analysis
derives from the trace (obedience measures, tokens, a truncated patch hash). Task ids are derived
labels, which the host allows; issue text, patches and test logs stay out.
"""

import argparse
import csv
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("analyze", HERE / "analyze.py")
analyze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyze)

FIELDS = ["block", "task", "variant", "rep", "resolved", "nonempty", "agent_s", "tool_calls",
          "error", "edited", "calls_after_first_edit", "spec_terms_named", "first_message_chars",
          "spec_stated", "repro_before_edit", "check_after_edit", "pytest_runs_tests",
          "last_pytest_real", "last_pytest_green", "last_pytest_empty", "compile_after_edit",
          "syntax_broken", "completion_tokens_per_call", "patch_hash"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--design", required=True)
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--tasks-jsonl", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    design = json.loads(Path(args.design).read_text())
    tasks = {t for t in Path(args.tasks).read_text().split() if t}
    block = {}
    for k, run_dir in enumerate(args.runs, 1):
        for path in Path(run_dir).glob("*/results.jsonl"):
            for line in path.read_text().splitlines():
                block[json.loads(line)["instance_id"]] = k
    rows, missing = analyze.load(args.runs, design, tasks, args.tasks_jsonl)
    if missing:
        raise SystemExit(f"{missing} traces missing")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            out = {k: r.get(k) for k in FIELDS}
            out["block"] = block[r["task"]]
            out["error"] = (r.get("error") or "")[:60]
            w.writerow(out)
    print(f"{len(rows)} records in {args.out}")


if __name__ == "__main__":
    main()
