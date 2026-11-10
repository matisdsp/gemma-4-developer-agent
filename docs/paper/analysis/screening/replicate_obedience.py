"""Descriptive measures of the replication attempts: what the agent did under `s04` and `s00`.

    python3 -I docs/paper/analysis/screening/replicate_obedience.py \
        --runs results/kaggle/g4agent-rep1/results --tasks-jsonl data/tasks.jsonl \
        --export docs/paper/records/replication_features.csv
    python3 -I docs/paper/analysis/screening/replicate_obedience.py   # from the published records

Not part of the frozen analysis. The addendum lists the obedience measures of the fresh attempts as
descriptive, and this script was written after the replication result was known. The measures are
those of the main run: `attempt_features` of the frozen `analyze.py`, unchanged. For each measure:
its level under each configuration, then the `s04` minus `s00` difference by task with the interval
and p value of `summarize`. Resolved tasks are the business of `replicate.py`. Standard library only.
"""

import argparse
import csv
import importlib.util
import json
import random
import re
import statistics as st
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SEED = 20261110
BASE, TREATED = "s00", "s04"
# measure: scale of the printed value (100 for a share in %, 1 for a count or seconds)
MEASURES = {"spec_stated": 100, "first_message_chars": 1, "spec_terms_named": 1,
            "repro_before_edit": 100, "check_after_edit": 100, "pytest_runs_tests": 100,
            "last_pytest_real": 100, "last_pytest_green": 100, "last_pytest_empty": 100,
            "compile_after_edit": 100, "edited": 100, "nonempty": 100, "syntax_broken": 100,
            "agent_s": 1, "tool_calls": 1, "calls_after_first_edit": 1,
            "completion_tokens_per_call": 1}
FIELDS = ["task", "variant", "repeat", *MEASURES]

spec = importlib.util.spec_from_file_location("analyze", HERE / "analyze.py")
analyze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyze)


def load_runs(run_dirs, tasks_jsonl):
    """One row per attempt with its measures, read from the traces of the kernels."""
    statements = {}
    for line in Path(tasks_jsonl).read_text().splitlines():
        rec = json.loads(line)
        statements[rec["instance_id"]] = rec.get("problem_statement", "")
    seen = {}
    for run_dir in run_dirs:
        for path in sorted(Path(run_dir).glob("*/results.jsonl")):
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                r = json.loads(line)
                name = re.fullmatch(r"(s\d\d)r(\d+)", r["variant"])
                if not name or name.group(1) not in (BASE, TREATED):
                    continue
                task, rep, d = r["instance_id"], r["rep"], path.parent
                log = d / "test_outputs" / f"{task}.r{rep}.log"
                patch = d / "patches" / f"{task}.r{rep}.patch"
                features = analyze.attempt_features(
                    json.loads((d / "traces" / f"trace_{task}.r{rep}.json").read_text()),
                    statements.get(task, ""),
                    log.read_text(errors="replace") if log.is_file() else "",
                    patch.read_text(errors="replace") if patch.is_file() else "")
                row = {"task": task, "variant": name.group(1), "repeat": int(name.group(2)),
                       "nonempty": bool(r.get("patch_chars")), "agent_s": r.get("agent_s") or 0,
                       "tool_calls": r.get("tool_calls") or 0, **features}
                seen[(task, row["variant"], row["repeat"])] = {k: row[k] for k in FIELDS}
    return [seen[k] for k in sorted(seen)]


def read_records(path):
    """The rows written by `write_records`: empty is None, True and False are booleans."""
    rows = []
    with open(path, newline="") as f:
        for rec in csv.DictReader(f):
            row = {"task": rec["task"], "variant": rec["variant"], "repeat": int(rec["repeat"])}
            for key in MEASURES:
                value = rec[key]
                if value in ("True", "False"):
                    row[key] = value == "True"
                elif value == "":
                    row[key] = None
                else:
                    row[key] = float(value) if "." in value else int(value)
            rows.append(row)
    return rows


def write_records(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def compare(rows, measure, rng):
    """Level under each configuration, and the s04 minus s00 difference by task."""
    groups = defaultdict(lambda: ([], []))
    for r in rows:
        if r.get(measure) is not None:
            groups[r["task"]][0 if r["variant"] == TREATED else 1].append(float(r[measure]))
    pairs = [pair for _, pair in sorted(groups.items())]
    treated = [x for a, _ in pairs for x in a]
    base = [x for _, b in pairs for x in b]
    res = analyze.summarize([st.mean(a) - st.mean(b) for a, b in pairs if a and b], rng)
    res[TREATED] = st.mean(treated) if treated else None
    res[BASE] = st.mean(base) if base else None
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", nargs="+", help="results directories of the replication kernels")
    ap.add_argument("--tasks-jsonl", type=Path, default=ROOT / "data" / "tasks.jsonl")
    ap.add_argument("--records", type=Path,
                    default=ROOT / "docs" / "paper" / "records" / "replication_features.csv")
    ap.add_argument("--export", type=Path, help="write one record per attempt, without task text")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    rows = load_runs(args.runs, args.tasks_jsonl) if args.runs else read_records(args.records)
    print(f"{len(rows)} attempts, {len({r['task'] for r in rows})} tasks")
    print("\nDESCRIPTIVE: level under each configuration, then s04 minus s00 by task "
          "(90% task-bootstrap interval, sign-flip p)")
    rng = random.Random(SEED)
    out = {}
    for measure, scale in MEASURES.items():
        res = out[measure] = compare(rows, measure, rng)
        if not res["n_tasks"]:
            print(f"  {measure:28s} no data")
            continue
        print(f"  {measure:28s} {BASE} {scale * res[BASE]:7.1f}  {TREATED} {scale * res[TREATED]:7.1f}"
              f"  {analyze.fmt(res, float(scale))}  tasks={res['n_tasks']}")
    if args.export:
        write_records(rows, args.export)
        print(f"\n{len(rows)} records in {args.export}")
    if args.out:
        args.out.write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
