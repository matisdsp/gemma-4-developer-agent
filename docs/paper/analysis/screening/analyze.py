"""Analysis of the E4B screening: main effects, compliance and clear interactions.

    python3 -I docs/paper/analysis/screening/analyze.py \
        --runs results/kaggle/g4agent-sc1/results results/kaggle/g4agent-sc2/results \
               results/kaggle/g4agent-sc3/results \
        --design variants/screening/design.json --tasks reports/screening_tasks_72.txt \
        --tasks-jsonl data/tasks.jsonl --out results/screening_analysis.json

Standard library only. An effect is computed task by task: the mean outcome of the attempts with
the recipe on, minus the mean outcome with it off, then averaged over tasks. Tasks are the unit of
every interval: the 90% interval resamples tasks, and the two-sided p value flips the sign of each
task's difference. Holm adjusts the eight primary p values.

--compliance-only hides every comparison of resolved tasks. The pilot uses it.
"""

import argparse
import hashlib
import json
import random
import re
import statistics as st
from collections import defaultdict
from pathlib import Path

SEED = 20261106
BOOTSTRAP = 2000
PERMUTATIONS = 10000
LETTERS = {"temperature_0.7": "A", "thinking_256": "B", "spec_first": "C", "reproduce_first": "D",
           "imposed_verification": "E", "useful_test": "F", "compile_check": "G",
           "worked_example": "H"}
EDIT_TOOLS = {"edit_file", "write_file"}


def observation(step):
    ob = step.get("observation") or {}
    raw = ob.get("content", "") if isinstance(ob, dict) else ""
    if isinstance(raw, list):
        raw = json.dumps(raw)
    try:
        j = json.loads(raw)
        details = j.get("details") or {}
        text = "\n".join(str(x) for x in (j.get("stdout", ""), j.get("stderr", ""),
                                          j.get("error_message", ""), details.get("stdout", ""),
                                          details.get("stderr", "")))
        return text, j.get("exit_code", details.get("exit_code"))
    except (ValueError, AttributeError):
        return str(raw), None


def pytest_class(text):
    """real_green, real_red, or empty when nothing ran. The final summary line decides."""
    lines = [ln for ln in text.splitlines()
             if re.search(r"\b(passed|failed|errors?|no tests ran|deselected|skipped|xfailed)\b", ln)
             and re.search(r"\bin \d+(\.\d+)?\s*s", ln)]
    if lines:
        counts = defaultdict(int)
        for n, word in re.findall(r"(\d+) (\w+)", lines[-1]):
            counts[word[:4]] += int(n)
        if counts["pass"] + counts["fail"] + counts["erro"] == 0:
            return "empty"
        return "real_red" if counts["fail"] + counts["erro"] else "real_green"
    if re.search(r"no tests ran|collected 0 items|file or directory not found|ERROR: not found|"
                 r"found no collectors", text):
        return "empty"
    return "unknown"


def issue_terms(statement):
    """Literal-looking names in an issue: backticked text, dotted, snake_case or CamelCase words."""
    terms = set(re.findall(r"`([^`\n]{3,60})`", statement))
    terms |= set(re.findall(r"\b[A-Za-z_]+(?:\.[A-Za-z_]+)+\b|\b[a-z]+_[a-z_]+\b|"
                            r"\b[A-Z][a-z]+[A-Z][A-Za-z]+\b", statement))
    return {t for t in terms if len(t) >= 4}


def attempt_features(trace, statement, test_log, patch):
    calls, first_text = [], ""
    for step in trace["steps"]:
        if step.get("source") != "agent":
            continue
        tools = step.get("tool_calls") or []
        if not calls and not tools and not first_text:
            first_text = step.get("message") or ""
        if not calls and tools and not first_text:
            first_text = step.get("message") or ""
        text, code = observation(step)
        for call in tools:
            calls.append({"name": call.get("function_name"), "args": call.get("arguments") or {},
                          "text": text, "code": code})
    first_edit = None
    for i, call in enumerate(calls):
        path = str(call["args"].get("filepath") or call["args"].get("path") or "")
        if call["name"] in EDIT_TOOLS and not path.startswith("/tmp"):
            first_edit = i
            break
    before = calls if first_edit is None else calls[:first_edit]
    after = [] if first_edit is None else calls[first_edit + 1:]

    def commands(part):
        return [c["args"].get("command", "") for c in part if c["name"] == "run_command"]

    pytest_calls = [c for c in calls if c["name"] == "run_command"
                    and re.search(r"\bpytest\b", c["args"].get("command", ""))
                    and "pip " not in c["args"].get("command", "")
                    and not re.match(r"\s*cat\s*>", c["args"].get("command", ""))]
    classes = [pytest_class(c["text"]) for c in pytest_calls]
    scripted = re.compile(r"python3?\s+/tmp/\S+\.py|/tmp/repro")
    named = sum(1 for t in issue_terms(statement) if t in first_text)
    tokens = [(s.get("metrics") or {}).get("completion_tokens") for s in trace["steps"]]
    tokens = [t for t in tokens if t]
    return {
        "edited": first_edit is not None,
        "calls_after_first_edit": len(after),
        "spec_terms_named": named,
        "first_message_chars": len(first_text),
        "spec_stated": named >= 3 and len(first_text) >= 600,
        "repro_before_edit": any(scripted.search(c) for c in commands(before)),
        "check_after_edit": any(re.search(r"\bpytest\b|python3?\s+(/tmp/|-c)", c)
                                for c in commands(after)),
        "pytest_runs_tests": (sum(1 for c in classes if c.startswith("real")) / len(classes)
                              if classes else None),
        "last_pytest_real": bool(classes) and classes[-1].startswith("real"),
        "last_pytest_green": bool(classes) and classes[-1] == "real_green",
        "last_pytest_empty": bool(classes) and classes[-1] == "empty",
        "compile_after_edit": any("py_compile" in c for c in commands(after)),
        "syntax_broken": bool(re.search(r"\b(SyntaxError|IndentationError)\b", test_log)),
        "completion_tokens_per_call": st.mean(tokens) if tokens else None,
        "patch_hash": hashlib.sha256(patch.encode()).hexdigest()[:16] if patch.strip() else None,
    }


def load(run_dirs, design, tasks, tasks_jsonl):
    statements = {}
    for line in Path(tasks_jsonl).read_text().splitlines():
        rec = json.loads(line)
        statements[rec["instance_id"]] = rec.get("problem_statement", "")
    seen, missing_traces = {}, 0
    for run_dir in run_dirs:
        for path in sorted(Path(run_dir).glob("*/results.jsonl")):
            for line in path.read_text().splitlines():
                r = json.loads(line)
                if r["variant"] in design and r["instance_id"] in tasks:
                    r["_dir"] = path.parent
                    seen[(r["variant"], r["instance_id"], r["rep"])] = r
    rows = []
    for (variant, task, rep), r in sorted(seen.items()):
        d = r["_dir"]
        trace_file = d / "traces" / f"trace_{task}.r{rep}.json"
        log_file = d / "test_outputs" / f"{task}.r{rep}.log"
        patch_file = d / "patches" / f"{task}.r{rep}.patch"
        features = {}
        if trace_file.is_file():
            features = attempt_features(
                json.loads(trace_file.read_text()), statements.get(task, ""),
                log_file.read_text(errors="replace") if log_file.is_file() else "",
                patch_file.read_text(errors="replace") if patch_file.is_file() else "")
        else:
            missing_traces += 1
        rows.append({"variant": variant, "task": task, "rep": rep,
                     "resolved": bool(r.get("resolved")), "agent_s": r.get("agent_s") or 0,
                     "tool_calls": r.get("tool_calls") or 0,
                     "nonempty": bool(r.get("patch_chars")), "error": r.get("error") or "",
                     **features})
    return rows, missing_traces


def task_differences(rows, design, sign, outcome):
    """One difference per task: mean outcome where sign(config) is True, minus where it is False."""
    groups = defaultdict(lambda: ([], []))
    for r in rows:
        value = r.get(outcome)
        if value is None:
            continue
        groups[r["task"]][0 if sign(design[r["variant"]]) else 1].append(float(value))
    return [st.mean(a) - st.mean(b) for a, b in groups.values() if a and b]


def summarize(diffs, rng):
    n = len(diffs)
    if not n:
        return {"n_tasks": 0}
    estimate = st.mean(diffs)
    boots = sorted(st.mean(rng.choices(diffs, k=n)) for _ in range(BOOTSTRAP))
    extreme = 0
    for _ in range(PERMUTATIONS):
        flipped = sum(d if rng.random() < 0.5 else -d for d in diffs) / n
        extreme += abs(flipped) >= abs(estimate) - 1e-12
    return {"estimate": estimate, "low": boots[int(0.05 * BOOTSTRAP)],
            "high": boots[int(0.95 * BOOTSTRAP) - 1], "p": (extreme + 1) / (PERMUTATIONS + 1),
            "n_tasks": n}


def holm(results):
    order = sorted(results, key=lambda k: results[k]["p"])
    m, running = len(order), 0.0
    for i, key in enumerate(order):
        running = max(running, min(1.0, (m - i) * results[key]["p"]))
        results[key]["p_holm"] = running


def diversity(rows, design, recipe):
    """Share of distinct non-empty patches per task, recipe on minus off (temperature check)."""
    groups = defaultdict(lambda: ([], []))
    for r in rows:
        if r.get("patch_hash"):
            groups[r["task"]][0 if design[r["variant"]][recipe] else 1].append(r["patch_hash"])
    return [len(set(a)) / len(a) - len(set(b)) / len(b) for a, b in groups.values() if a and b]


COMPLIANCE = {
    "temperature_0.7": ["nonempty", "syntax_broken"],
    "thinking_256": ["completion_tokens_per_call", "agent_s"],
    "spec_first": ["spec_stated", "spec_terms_named", "first_message_chars"],
    "reproduce_first": ["repro_before_edit"],
    "imposed_verification": ["check_after_edit", "calls_after_first_edit", "tool_calls"],
    "useful_test": ["pytest_runs_tests", "last_pytest_real", "last_pytest_empty"],
    "compile_check": ["compile_after_edit", "syntax_broken"],
    "worked_example": ["spec_stated", "repro_before_edit", "pytest_runs_tests",
                       "compile_after_edit"],
}
RULE_CHECK = {"spec_first": "spec_stated", "reproduce_first": "repro_before_edit",
              "useful_test": "pytest_runs_tests", "compile_check": "compile_after_edit",
              "imposed_verification": "check_after_edit"}
CLEAR_PARTNERS = {"imposed_verification", "worked_example"}


def fmt(res, scale=100.0):
    if not res.get("n_tasks"):
        return "no data"
    return (f"{scale * res['estimate']:+7.2f} [{scale * res['low']:+6.2f}, {scale * res['high']:+6.2f}]"
            f"  p={res['p']:.4f}" + (f"  holm={res['p_holm']:.4f}" if "p_holm" in res else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--design", required=True)
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--tasks-jsonl", required=True)
    ap.add_argument("--out")
    ap.add_argument("--compliance-only", action="store_true")
    args = ap.parse_args()

    rng = random.Random(SEED)
    design = json.loads(Path(args.design).read_text())
    recipes = list(next(iter(design.values())))
    tasks = {t for t in Path(args.tasks).read_text().split() if t}
    rows, missing = load(args.runs, design, tasks, args.tasks_jsonl)
    print(f"{len(rows)} attempts, {len({r['task'] for r in rows})} tasks, "
          f"{len({r['variant'] for r in rows})} configurations, traces missing: {missing}")
    out = {"attempts": len(rows), "traces_missing": missing}

    print("\nCOMPLIANCE AND MANIPULATION CHECKS (recipe on minus off, by task)")
    out["compliance"] = {}
    for recipe in recipes:
        for outcome in COMPLIANCE[recipe]:
            res = summarize(task_differences(rows, design, lambda c, k=recipe: c[k], outcome), rng)
            out["compliance"][f"{recipe}:{outcome}"] = res
            scale = 1.0 if outcome in ("completion_tokens_per_call", "agent_s", "tool_calls",
                                       "calls_after_first_edit", "spec_terms_named",
                                       "first_message_chars") else 100.0
            print(f"  {recipe:22s} {outcome:28s} {fmt(res, scale)}")
    res = summarize(diversity(rows, design, "temperature_0.7"), rng)
    out["compliance"]["temperature_0.7:distinct_patches"] = res
    print(f"  {'temperature_0.7':22s} {'distinct_patches':28s} {fmt(res)}")
    print("\n  obedience level with the rule on, without and with the worked example")
    for recipe, check in RULE_CHECK.items():
        for shown in (False, True):
            values = [r[check] for r in rows if design[r["variant"]][recipe]
                      and design[r["variant"]]["worked_example"] == shown
                      and r.get(check) is not None]
            if values:
                print(f"    {recipe:22s} {check:22s} example={int(shown)} "
                      f"{100 * st.mean(float(v) for v in values):6.1f}%  (n={len(values)})")

    if args.compliance_only:
        print("\nOutcome comparisons hidden (--compliance-only).")
        if args.out:
            Path(args.out).write_text(json.dumps(out, indent=2))
        return

    print("\nPRIMARY: EFFECT ON RESOLVED, points, 90% task-bootstrap interval, sign-flip p, Holm over 8")
    primary = {r: summarize(task_differences(rows, design, lambda c, k=r: c[k], "resolved"), rng)
               for r in recipes}
    holm(primary)
    for recipe in sorted(primary, key=lambda k: -primary[k]["estimate"]):
        print(f"  {recipe:22s} {fmt(primary[recipe])}")
    out["primary"] = primary
    per_task = defaultdict(list)
    for r in rows:
        per_task[r["task"]].append(r["resolved"])
    out["mean_resolved"] = st.mean(float(r["resolved"]) for r in rows)
    out["tasks_ever_resolved"] = sum(any(v) for v in per_task.values())
    print(f"\n  overall resolved {100 * out['mean_resolved']:.1f}%, tasks ever resolved "
          f"{out['tasks_ever_resolved']} of {len(per_task)}")

    print("\nSECONDARY: empty patches, syntax-broken patches and time")
    out["secondary"] = {}
    for outcome, scale in (("nonempty", 100.0), ("syntax_broken", 100.0), ("agent_s", 1.0)):
        for recipe in recipes:
            res = summarize(task_differences(rows, design, lambda c, k=recipe: c[k], outcome), rng)
            out["secondary"][f"{recipe}:{outcome}"] = res
            print(f"  {recipe:22s} {outcome:15s} {fmt(res, scale)}")

    print("\nEXPLORATORY: clear two-way interactions on resolved (half the difference between the "
          "effect of one recipe with the other on and off)")
    out["interactions"] = {}
    for partner in CLEAR_PARTNERS:
        for recipe in recipes:
            key = "*".join(sorted((partner, recipe)))
            if recipe == partner or key in out["interactions"]:
                continue

            def agree(c, a=partner, b=recipe):
                return c[a] == c[b]
            res = summarize(task_differences(rows, design, agree, "resolved"), rng)
            out["interactions"][key] = res
            print(f"  {key:46s} {fmt(res)}")

    print("\nEXPLORATORY: the 32 configurations, resolved share")
    by_config = defaultdict(list)
    for r in rows:
        by_config[r["variant"]].append(r["resolved"])
    for name, values in sorted(by_config.items(), key=lambda kv: -st.mean(kv[1])):
        on = "".join(LETTERS[k] for k, v in design[name].items() if v)
        print(f"  {name} {100 * st.mean(float(v) for v in values):5.1f}%  n={len(values)}  on: {on}")
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
