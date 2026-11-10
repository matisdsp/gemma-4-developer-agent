"""Replication of the screening's best configuration against the base prompt.

    python3 -I docs/paper/analysis/screening/replicate.py \
        --runs results/kaggle/g4agent-rep1/results --out results/screening_replication.json \
        --export docs/paper/records/replication_attempts.csv
    python3 -I docs/paper/analysis/screening/replicate.py          # from the published records
    python3 -I docs/paper/analysis/screening/replicate.py --selection-null

Design and reading rules: `docs/paper/preregistration_screening_addendum.md`. Standard library only.
The kernel runs `s00` and `s04` four times each on every task, as variants `s00r1`..`s00r4` and
`s04r1`..`s04r4`. For each task: the resolved share of the `s04` attempts minus the share of the
`s00` attempts. The estimate is the mean of these differences over tasks. Interval and p value come
from `summarize` of the frozen `analyze.py`, unchanged: 2,000 task-bootstrap resamples, 10,000 sign
flips.

--selection-null reads the per-attempt records of the main run and asks how often the best of the
32 configurations reaches the observed maximum when the configuration changes nothing: each attempt
is a coin with its task's success rate, the null of `explore.py`.
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
RECORDS = ROOT / "docs" / "paper" / "records"
SEED = 20261110
BASE, TREATED = "s00", "s04"
REPEATS = 4
MARGIN = 3.0  # points, the margin of the pre-registration
SIMULATIONS = 40000
FIELDS = ["task", "variant", "repeat", "resolved", "nonempty", "agent_s", "tool_calls", "error"]

spec = importlib.util.spec_from_file_location("analyze", HERE / "analyze.py")
analyze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyze)


def load_runs(run_dirs, tasks):
    """One row per attempt, read from the results lines of the kernels."""
    seen = {}
    for run_dir in run_dirs:
        for path in sorted(Path(run_dir).glob("*/results.jsonl")):
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                r = json.loads(line)
                name = re.fullmatch(r"(s\d\d)r(\d+)", r["variant"])
                if (not name or name.group(1) not in (BASE, TREATED)
                        or r["instance_id"] not in tasks):
                    continue
                key = (r["instance_id"], name.group(1), int(name.group(2)))
                seen[key] = {"task": key[0], "variant": key[1], "repeat": key[2],
                             "resolved": bool(r.get("resolved")),
                             "nonempty": bool(r.get("patch_chars")),
                             "agent_s": r.get("agent_s") or 0,
                             "tool_calls": r.get("tool_calls") or 0,
                             "error": (r.get("error") or "")[:60]}
    return [seen[k] for k in sorted(seen)]


def read_records(path):
    rows = []
    with open(path, newline="") as f:
        for rec in csv.DictReader(f):
            rows.append({"task": rec["task"], "variant": rec["variant"],
                         "repeat": int(rec["repeat"]), "resolved": rec["resolved"] == "True",
                         "nonempty": rec["nonempty"] == "True",
                         "agent_s": float(rec["agent_s"] or 0),
                         "tool_calls": int(rec["tool_calls"] or 0), "error": rec["error"]})
    return rows


def write_records(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def differences(rows):
    """Per task, in task order: resolved share of the s04 attempts minus that of the s00 ones."""
    groups = defaultdict(lambda: ([], []))
    for r in rows:
        groups[r["task"]][0 if r["variant"] == TREATED else 1].append(float(r["resolved"]))
    return [st.mean(a) - st.mean(b) for _, (a, b) in sorted(groups.items()) if a and b]


def reading(res):
    if 100 * res["low"] > 0 and res["p"] < 0.05:
        return "helps"
    if 100 * res["high"] < MARGIN:
        return "no advantage beyond 3 points"
    return "unresolved"


def selection_null(path):
    by_task, by_config = defaultdict(list), defaultdict(int)
    with open(path, newline="") as f:
        for rec in csv.DictReader(f):
            by_task[rec["task"]].append(rec["resolved"] == "True")
            by_config[rec["variant"]] += rec["resolved"] == "True"
    rates = [st.mean(v) for _, v in sorted(by_task.items()) if any(v)]
    best = max(sorted(by_config), key=by_config.get)
    rng = random.Random(SEED)
    maxima = sorted(max(sum(rng.random() < q for q in rates) for _ in by_config)
                    for _ in range(SIMULATIONS))
    return {"best": best, "resolved": by_config[best], "tasks": len(by_task),
            "configurations": len(by_config),
            "mean_resolved": st.mean(by_config.values()),
            "p_best_at_least_observed": sum(m >= by_config[best] for m in maxima) / SIMULATIONS,
            "median_best": maxima[SIMULATIONS // 2], "p95_best": maxima[int(0.95 * SIMULATIONS)]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", nargs="+", help="results directories of the replication kernels")
    ap.add_argument("--records", type=Path, default=RECORDS / "replication_attempts.csv")
    ap.add_argument("--main-records", type=Path, default=RECORDS / "screening_attempts.csv")
    ap.add_argument("--tasks", type=Path, default=ROOT / "reports" / "screening_tasks_72.txt")
    ap.add_argument("--export", type=Path, help="write one record per attempt, without task text")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--selection-null", action="store_true")
    args = ap.parse_args()

    if args.selection_null:
        out = selection_null(args.main_records)
        print(f"best of {out['configurations']} configurations: {out['best']} with "
              f"{out['resolved']} of {out['tasks']} tasks (mean {out['mean_resolved']:.2f})")
        print(f"configuration changes nothing, {SIMULATIONS} simulations: the best reaches "
              f"{out['resolved']} or more in {100 * out['p_best_at_least_observed']:.2f}% "
              f"(median {out['median_best']}, 95th percentile {out['p95_best']})")
        if args.out:
            args.out.write_text(json.dumps(out, indent=2))
        return

    tasks = {t for t in args.tasks.read_text().split() if t}
    rows = load_runs(args.runs, tasks) if args.runs else read_records(args.records)
    expected = 2 * REPEATS * len(tasks)
    print(f"{len(rows)} attempts of {expected} expected, {len({r['task'] for r in rows})} tasks")
    out = {"attempts": len(rows), "attempts_expected": expected, "resolved": {}}

    print("\nRESOLVED BY CONFIGURATION (attempts, then by repeat, then by repository)")
    for variant in (BASE, TREATED):
        mine = [r for r in rows if r["variant"] == variant]
        by_repeat = defaultdict(list)
        by_repo = defaultdict(list)
        for r in mine:
            by_repeat[r["repeat"]].append(r["resolved"])
            by_repo[r["task"].rsplit("_", 1)[0]].append(r["resolved"])
        out["resolved"][variant] = {"attempts": len(mine),
                                    "resolved": sum(r["resolved"] for r in mine)}
        share = 100 * st.mean(float(r["resolved"]) for r in mine) if mine else float("nan")
        print(f"  {variant} {out['resolved'][variant]['resolved']:3d} of {len(mine):3d} "
              f"({share:5.1f}%)  repeats: "
              + " ".join(f"{sum(v)}/{len(v)}" for _, v in sorted(by_repeat.items()))
              + "  " + " ".join(f"{k} {sum(v)}/{len(v)}" for k, v in sorted(by_repo.items())))

    res = analyze.summarize(differences(rows), random.Random(SEED))
    print("\nPRIMARY: s04 minus s00 on resolved, points, 90% task-bootstrap interval, sign-flip p")
    if res["n_tasks"]:
        res["reading"] = reading(res)
        print(f"  {analyze.fmt(res)}  tasks={res['n_tasks']}  reading: {res['reading']}")
    else:
        print("  no data")
    out["primary"] = res

    if args.main_records.is_file():
        print("\nDESCRIPTIVE: the single attempt of the main run, which selected s04")
        with open(args.main_records, newline="") as f:
            main_rows = [r for r in csv.DictReader(f) if r["variant"] in (BASE, TREATED)]
        out["main_run"] = {}
        for variant in (BASE, TREATED):
            got = [r["resolved"] == "True" for r in main_rows if r["variant"] == variant]
            out["main_run"][variant] = {"attempts": len(got), "resolved": sum(got)}
            print(f"  {variant} {sum(got)} of {len(got)}")

    if args.export:
        write_records(rows, args.export)
        print(f"\n{len(rows)} records in {args.export}")
    if args.out:
        args.out.write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
