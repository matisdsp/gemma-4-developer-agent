"""Exploratory numbers for the screening paper, beyond the pre-registered analysis.

    python3 -I docs/paper/analysis/screening/explore.py \
        --runs results/kaggle/g4agent-sc1/results results/kaggle/g4agent-sc2/results \
               results/kaggle/g4agent-sc3/results \
        --design variants/screening/design.json --tasks reports/screening_tasks_72.txt \
        --tasks-jsonl data/tasks.jsonl --out results/screening_explore.json

Everything here is exploratory and labelled so in the paper: obedience levels with each rule off
and on, how many configurations solve each task, how much of the outcome variance the task
explains, and outcomes by repository. It reuses the parsing of the frozen analysis script.
"""

import argparse
import importlib.util
import json
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("analyze", HERE / "analyze.py")
analyze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyze)

RULES = {"spec_first": "spec_stated", "reproduce_first": "repro_before_edit",
         "imposed_verification": "check_after_edit", "useful_test": "pytest_runs_tests",
         "compile_check": "compile_after_edit"}


def mean(values):
    values = [float(v) for v in values if v is not None]
    return st.mean(values) if values else None


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
    rows, _ = analyze.load(args.runs, design, tasks, args.tasks_jsonl)
    out = {}

    out["obedience"] = {}
    for recipe, check in RULES.items():
        off = mean(r.get(check) for r in rows if not design[r["variant"]][recipe])
        on = mean(r.get(check) for r in rows if design[r["variant"]][recipe])
        out["obedience"][recipe] = {"check": check, "off": off, "on": on}

    solved = defaultdict(int)
    for r in rows:
        solved[r["task"]] += r["resolved"]
    hist = Counter(solved[t] for t in tasks)
    out["configs_solving_task"] = {str(k): hist.get(k, 0) for k in range(33)}
    out["tasks_never"] = hist.get(0, 0)
    out["tasks_always"] = hist.get(32, 0)
    out["tasks_sometimes"] = len(tasks) - out["tasks_never"] - out["tasks_always"]

    y = [float(r["resolved"]) for r in rows]
    grand = st.mean(y)
    total = sum((v - grand) ** 2 for v in y)
    task_mean = {t: st.mean(float(r["resolved"]) for r in rows if r["task"] == t) for t in tasks}
    between_task = sum((task_mean[r["task"]] - grand) ** 2 for r in rows)
    recipes = list(next(iter(design.values())))
    explained_recipes = 0.0
    for recipe in recipes:
        on = [float(r["resolved"]) for r in rows if design[r["variant"]][recipe]]
        off = [float(r["resolved"]) for r in rows if not design[r["variant"]][recipe]]
        explained_recipes += len(on) * (st.mean(on) - grand) ** 2 + len(off) * (st.mean(off) - grand) ** 2
    config_mean = defaultdict(list)
    for r in rows:
        config_mean[r["variant"]].append(float(r["resolved"]))
    between_config = sum(len(v) * (st.mean(v) - grand) ** 2 for v in config_mean.values())
    out["variance_share"] = {"task": between_task / total, "eight_recipes": explained_recipes / total,
                             "configuration": between_config / total}
    # what a configuration spread looks like if configurations did not matter at all
    p, n = grand, len(rows) // len(config_mean)
    out["config_sd_points"] = 100 * st.pstdev(st.mean(v) for v in config_mean.values())
    out["config_sd_points_if_no_effect"] = 100 * (p * (1 - p) / n) ** 0.5
    out["config_range_points"] = [100 * min(st.mean(v) for v in config_mean.values()),
                                  100 * max(st.mean(v) for v in config_mean.values())]

    by_repo = defaultdict(list)
    for r in rows:
        by_repo[r["task"].split("_")[0]].append(r["resolved"])
    out["by_repo"] = {k: {"attempts": len(v), "resolved": mean(v),
                          "tasks": len({r["task"] for r in rows if r["task"].startswith(k)})}
                      for k, v in by_repo.items()}
    out["mean_agent_s"] = mean(r["agent_s"] for r in rows)
    out["mean_tool_calls"] = mean(r["tool_calls"] for r in rows)
    out["nonempty"] = mean(r["nonempty"] for r in rows)
    out["errors"] = Counter((r["error"] or "none")[:60] for r in rows).most_common(6)
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
