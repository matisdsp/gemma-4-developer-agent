"""Exploratory controls of the screening paper, written after the results were known.

    python3 -I docs/paper/analysis/screening/controls.py \
        --runs results/kaggle/g4agent-sc1/results results/kaggle/g4agent-sc2/results \
               results/kaggle/g4agent-sc3/results \
        --export docs/paper/records/screening_controls.csv
    python3 -I docs/paper/analysis/screening/controls.py        # from the published records

Nothing here is pre-registered. The script checks how far the wording of the paper can go:

- the frozen measure of "a pytest call that runs tests" counts a call whose summary reports only
  errors, such as a failed import of the test file. The strict variant asks for at least one test
  passed or failed;
- a reproduction script can run at any point of the attempt, not only before the first edit;
- pytest calls that stop on a missing module, by repository;
- the resolved rate after a green last test run and after anything else, within tasks;
- the sum of the eight main effects, the verdicts of identical patches, the attempts at the time
  cap and the number of recipes on in a configuration.

Counts per attempt come from the traces (`--runs`) or from `screening_controls.csv`; everything else
comes from `screening_attempts.csv`. Parsing, intervals and p values are those of the frozen
`analyze.py`. Standard library only.
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
SEED = 20261111
COUNTS = ["pytest_calls", "pytest_ran", "pytest_passed_or_failed", "pytest_missing_module",
          "repro_runs", "repro_runs_before_edit"]
FIELDS = ["task", "variant", "rep", *COUNTS]
SCRIPTED = re.compile(r"python3?\s+/tmp/\S+\.py|/tmp/repro")


def module(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


analyze = module("analyze")
reproduce = module("reproduce")


def passed_or_failed(text):
    """True when the final pytest summary line reports at least one test passed or failed."""
    lines = [ln for ln in text.splitlines()
             if re.search(r"\b(passed|failed|errors?|no tests ran|deselected|skipped|xfailed)\b", ln)
             and re.search(r"\bin \d+(\.\d+)?\s*s", ln)]
    if not lines:
        return False
    counts = defaultdict(int)
    for n, word in re.findall(r"(\d+) (\w+)", lines[-1]):
        counts[word[:4]] += int(n)
    return counts["pass"] + counts["fail"] > 0


def attempt_counts(trace):
    """Counts over the tool calls of one attempt, with the call selection of `attempt_features`."""
    calls = []
    for step in trace["steps"]:
        if step.get("source") != "agent":
            continue
        text, _ = analyze.observation(step)
        for call in step.get("tool_calls") or []:
            calls.append((call.get("function_name"), call.get("arguments") or {}, text))
    first_edit = None
    for i, (name, args, _) in enumerate(calls):
        path = str(args.get("filepath") or args.get("path") or "")
        if name in analyze.EDIT_TOOLS and not path.startswith("/tmp"):
            first_edit = i
            break
    commands = [(i, args.get("command", ""), text) for i, (name, args, text) in enumerate(calls)
                if name == "run_command"]
    pytest_calls = [text for _, command, text in commands
                    if re.search(r"\bpytest\b", command) and "pip " not in command
                    and not re.match(r"\s*cat\s*>", command)]
    repro = [i for i, command, _ in commands if SCRIPTED.search(command)]
    return {"pytest_calls": len(pytest_calls),
            "pytest_ran": sum(analyze.pytest_class(t).startswith("real") for t in pytest_calls),
            "pytest_passed_or_failed": sum(passed_or_failed(t) for t in pytest_calls),
            "pytest_missing_module": sum(bool(re.search(r"ModuleNotFoundError|No module named", t))
                                         for t in pytest_calls),
            "repro_runs": len(repro),
            "repro_runs_before_edit": sum(first_edit is None or i < first_edit for i in repro)}


def load_runs(run_dirs, design, tasks):
    seen = {}
    for run_dir in run_dirs:
        for path in sorted(Path(run_dir).glob("*/results.jsonl")):
            for line in path.read_text().splitlines():
                r = json.loads(line)
                if r["variant"] not in design or r["instance_id"] not in tasks:
                    continue
                trace = path.parent / "traces" / f"trace_{r['instance_id']}.r{r['rep']}.json"
                seen[(r["variant"], r["instance_id"], r["rep"])] = {
                    "task": r["instance_id"], "variant": r["variant"], "rep": r["rep"],
                    **attempt_counts(json.loads(trace.read_text()))}
    return [seen[k] for k in sorted(seen)]


def read_counts(path):
    with open(path, newline="") as f:
        return [{"task": rec["task"], "variant": rec["variant"],
                 **{k: int(rec[k]) for k in ("rep", *COUNTS)}} for rec in csv.DictReader(f)]


def write_counts(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def share(rows, top, bottom):
    """Mean over attempts of top / bottom, attempts with bottom at zero left out."""
    values = [r[top] / r[bottom] for r in rows if r[bottom]]
    return st.mean(values) if values else None


def by_task(rows, value, group):
    """One difference per task, in task order: mean value where group is True minus where False."""
    cells = defaultdict(lambda: ([], []))
    for r in rows:
        v = value(r)
        if v is not None:
            cells[r["task"]][0 if group(r) else 1].append(float(v))
    return [st.mean(a) - st.mean(b) for _, (a, b) in sorted(cells.items()) if a and b]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", nargs="+", help="results directories of the three kernels")
    ap.add_argument("--counts", type=Path, default=RECORDS / "screening_controls.csv")
    ap.add_argument("--attempts", type=Path, default=RECORDS / "screening_attempts.csv")
    ap.add_argument("--design", type=Path, default=ROOT / "variants/screening/design.json")
    ap.add_argument("--tasks", type=Path, default=ROOT / "reports/screening_tasks_72.txt")
    ap.add_argument("--export", type=Path, help="write the counts per attempt")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    design = json.loads(args.design.read_text())
    tasks = {t for t in args.tasks.read_text().split() if t}
    counts = load_runs(args.runs, design, tasks) if args.runs else read_counts(args.counts)
    attempts = [r for r in reproduce.read_records(args.attempts)
                if r["task"] in tasks and r["variant"] in design]
    rng = random.Random(SEED)
    out = {"attempts": len(attempts), "attempts_with_counts": len(counts)}
    print(f"{len(attempts)} attempts, {len(counts)} with counts from the traces")

    def on(recipe):
        return lambda r: design[r["variant"]][recipe]

    print("\nPYTEST CALLS THAT RUN TESTS, useful test off and on (mean over attempts with a call)")
    out["pytest"] = {}
    for label, top in (("frozen measure, errors count", "pytest_ran"),
                       ("strict, a test passed or failed", "pytest_passed_or_failed")):
        off = share([r for r in counts if not on("useful_test")(r)], top, "pytest_calls")
        lit = share([r for r in counts if on("useful_test")(r)], top, "pytest_calls")
        res = analyze.summarize(by_task(
            counts, lambda r, k=top: r[k] / r["pytest_calls"] if r["pytest_calls"] else None,
            on("useful_test")), rng)
        out["pytest"][top] = {"off": off, "on": lit, **res}
        print(f"  {label:32s} off {100 * off:5.1f}%  on {100 * lit:5.1f}%  {analyze.fmt(res)}")
    calls = sum(r["pytest_calls"] for r in counts)
    ran = sum(r["pytest_ran"] for r in counts)
    strict = sum(r["pytest_passed_or_failed"] for r in counts)
    out["pytest"]["calls"] = {"all": calls, "ran": ran, "passed_or_failed": strict}
    print(f"  {calls} pytest calls, {ran} run tests by the frozen measure, {ran - strict} of them "
          "report errors only")

    print("\nPYTEST CALLS THAT STOP ON A MISSING MODULE, by repository")
    out["missing_module"] = {}
    for repo in sorted({r["task"].rsplit("_", 1)[0] for r in counts}):
        mine = [r for r in counts if r["task"].rsplit("_", 1)[0] == repo]
        n = sum(r["pytest_calls"] for r in mine)
        hit = sum(r["pytest_missing_module"] for r in mine)
        hit_tasks = len({r["task"] for r in mine if r["pytest_missing_module"]})
        out["missing_module"][repo] = {"calls": n, "missing_module": hit, "tasks_hit": hit_tasks,
                                       "tasks": len({r["task"] for r in mine})}
        print(f"  {repo:8s} {hit} of {n} calls ({100 * hit / n:.1f}%), on {hit_tasks} of "
              f"{out['missing_module'][repo]['tasks']} tasks")

    print("\nREPRODUCTION SCRIPT, share of attempts that run one (reproduce first off, on)")
    out["reproduction"] = {}
    for label, key in (("at any point", "repro_runs"), ("before the first edit",
                                                         "repro_runs_before_edit")):
        off = st.mean(bool(r[key]) for r in counts if not on("reproduce_first")(r))
        lit = st.mean(bool(r[key]) for r in counts if on("reproduce_first")(r))
        out["reproduction"][key] = {"off": off, "on": lit}
        print(f"  {label:22s} off {100 * off:5.1f}%  on {100 * lit:5.1f}%")

    print("\nRESOLVED AFTER A GREEN LAST TEST RUN, against every other attempt")
    green = [r for r in attempts if r.get("last_pytest_green")]
    other = [r for r in attempts if not r.get("last_pytest_green")]
    res = analyze.summarize(by_task(attempts, lambda r: r["resolved"],
                                    lambda r: bool(r.get("last_pytest_green"))), rng)
    out["green"] = {"green": len(green), "green_resolved": st.mean(r["resolved"] for r in green),
                    "other": len(other), "other_resolved": st.mean(r["resolved"] for r in other),
                    "within_task": res}
    print(f"  green {100 * out['green']['green_resolved']:.1f}% of {len(green)}, other "
          f"{100 * out['green']['other_resolved']:.1f}% of {len(other)}")
    print(f"  within tasks, green minus other: {analyze.fmt(res)}  tasks={res['n_tasks']}")

    print("\nSUM OF THE EIGHT MAIN EFFECTS ON RESOLVED, by task")
    recipes = list(next(iter(design.values())))
    per_recipe = [by_task(attempts, lambda r: r["resolved"], on(k)) for k in recipes]
    res = analyze.summarize([sum(d) for d in zip(*per_recipe, strict=True)], rng)
    out["sum_of_effects"] = res
    print(f"  {analyze.fmt(res)}  negative estimates: "
          f"{sum(st.mean(d) < 0 for d in per_recipe)} of {len(recipes)}")

    groups = defaultdict(list)
    for r in attempts:
        if r.get("patch_hash"):
            groups[(r["task"], r["patch_hash"])].append(r["resolved"])
    repeated = [v for v in groups.values() if len(v) > 1]
    out["identical_patches"] = {"patches": len(repeated), "attempts": sum(map(len, repeated)),
                                "contradictory": sum(len(set(v)) > 1 for v in repeated)}
    print(f"\nIDENTICAL PATCHES: {len(repeated)} patches produced more than once, "
          f"{out['identical_patches']['attempts']} attempts, "
          f"{out['identical_patches']['contradictory']} with two verdicts")

    capped = [r for r in attempts if r["agent_s"] >= 600]
    out["time_cap"] = {"attempts": len(capped), "resolved": sum(r["resolved"] for r in capped)}
    print(f"TIME CAP: {len(capped)} attempts ran 600 s or more, "
          f"{out['time_cap']['resolved']} of them resolved")
    lit = sorted(sum(v.values()) for v in design.values())
    out["recipes_on"] = {"min": lit[0], "mean": st.mean(lit), "max": lit[-1],
                         "configurations_with_one": lit.count(1)}
    print(f"RECIPES ON per configuration: {lit[0]} to {lit[-1]}, mean {st.mean(lit):.1f}, "
          f"{lit.count(1)} configurations with exactly one")

    if args.export:
        write_counts(counts, args.export)
        print(f"\n{len(counts)} records in {args.export}")
    if args.out:
        args.out.write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
