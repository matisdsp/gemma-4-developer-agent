"""Can a cheap, agent-side selector find a resolved attempt among k <= 4 attempts of a task?

Offline, standard library only. Run: python3 -I selectors.py [--dirs d1,d2] [--arms A1=e4b-v2]

Data (defaults): results/modal/a0a1-r2 and a0a1-r4, arms e4b (A0) and e4b-v2 (A1). If the same
(instance_id, rep) appears in two directories the later one wins (count printed).
Confirmatory run (pre-registered, docs/paper/preregistration.md):
  python3 -I selectors.py --dirs a1-ho35 --arms A1=e4b-v2
Only tasks with exactly 4 attempts enter the per-task analysis (the excluded count is printed).

Selectors use only information visible to the agent (its patch, its trace); the hidden
`resolved` verdict is used only to score them.

EXTRACTION RULES (all from the ATIF trace + patch file)
  nonempty     patch file size > 0 (checked equal to patch_chars > 0 for every attempt).
  repro run    a run_command whose command mentions "repro" AND that executes it: after removing
               heredoc bodies (<<EOF ... EOF) the command must contain `python* ... repro*`.
               A bare `cat > /tmp/repro.py <<EOF` is a write, not a run.
  repro pass   outcome of the LAST repro run: exit_code == 0 (top level, or details.exit_code on
               status "error"). If no exit code is available (no observation, e.g. session
               timeout, or two tool calls sharing one observation), heuristic: output containing
               Traceback / AssertionError / "FAILED" / "Error" => fail, otherwise pass if there is
               an observation at all, else unknown (counted as not passed).
  pytest run   a run_command matching \\bpytest\\b (not pip, not a repro run). Outcome of the LAST
               one, parsed from the summary line ("N passed, M failed, K errors in Xs"). ok iff
               passed >= 1, failed == 0, errors == 0. If no summary line (output cut by head/tail,
               collection crash) fall back to: exit 0 and "passed" present and no FAILED/ERROR/
               Traceback => ok; anything else => not ok. Exit codes are NOT trusted for pytest
               (pipes to head/tail mask them), the summary line is.
  submitted    submit_patch tool call present.
  ntool        number of tool calls in the trace (includes submit_patch; results.jsonl omits it and
               calls that never returned, hence small differences).
  Extra (not in the brief): S1any = prefer (repro pass OR pytest ok), then non-empty, ties smallest patch.
  verified     (self-verified flag) nonempty AND repro pass AND pytest ok.
"""
import argparse
import json
import random
import re
import statistics
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
RUNS = REPO / "results" / "modal"
DIRS = ["a0a1-r2", "a0a1-r4"]  # later directory wins on duplicates
ARMS = [("A0", "e4b"), ("A1", "e4b-v2")]
SEED = 20261023
NBOOT = 2000

FAIL_PAT = re.compile(r"Traceback|AssertionError|FAILED|Error")


def parse_obs(obs):
    """Return (dict or None, raw text) for a run_command observation."""
    if not obs:
        return None, ""
    c = obs.get("content") if isinstance(obs, dict) else obs
    if not isinstance(c, str):
        return None, str(c)
    try:
        j = json.loads(c)
    except Exception:
        return None, c
    return (j if isinstance(j, dict) else None), c


def obs_text_and_exit(j, raw):
    if j is None:
        return raw, None
    det = j.get("details") or {}
    parts = [str(j.get(k, "")) for k in ("stdout", "stderr", "error_message")]
    parts += [str(det.get(k, "")) for k in ("stdout", "stderr")]
    code = j.get("exit_code", det.get("exit_code"))
    return "\n".join(parts), code


def strip_heredocs(cmd):
    out, lines, i = [], cmd.split("\n"), 0
    term = None
    for ln in lines:
        if term is not None:
            if ln.strip() == term:
                term = None
            continue
        out.append(ln)
        m = re.search(r"<<-?\s*['\"]?(\w+)['\"]?", ln)
        if m:
            term = m.group(1)
    return "\n".join(out)


def is_repro_run(cmd):
    if "repro" not in cmd:
        return False
    return re.search(r"python\S*\s+(?:-\S+\s+)*\S*repro\S*", strip_heredocs(cmd)) is not None


def is_pytest_run(cmd):
    if is_repro_run(cmd) or "pip " in cmd:
        return False
    return re.search(r"\bpytest\b", strip_heredocs(cmd)) is not None


def repro_pass(text, code, has_obs):
    if code is not None:
        return code == 0
    if not has_obs:
        return None
    return FAIL_PAT.search(text) is None


def pytest_ok(text, code):
    lines = [ln for ln in text.split("\n") if re.search(r"\bin \d+(\.\d+)?s\b", ln)]
    if lines:
        cnt = defaultdict(int)
        for n, w in re.findall(r"(\d+) (passed|failed|errors?|skipped|xfailed|xpassed|deselected)", lines[-1]):
            cnt["error" if w.startswith("error") else w] += int(n)
        return cnt["passed"] >= 1 and cnt["failed"] == 0 and cnt["error"] == 0
    return code == 0 and "passed" in text and not re.search(r"FAILED|ERROR|Traceback", text)


def extract(trace_path):
    t = json.load(open(trace_path))
    f = dict(ran_repro=False, repro_pass=None, repro_runs=0, repro_first_pass=None,
             ran_pytest=False, pytest_ok=None, submitted=False, ntool=0, multi_call_steps=0)
    for s in t["steps"]:
        tcs = s.get("tool_calls") or []
        f["ntool"] += len(tcs)
        if len(tcs) > 1:
            f["multi_call_steps"] += 1
        for tc in tcs:
            name = tc["function_name"]
            if name == "submit_patch":
                f["submitted"] = True
            if name != "run_command":
                continue
            a = tc.get("arguments")
            cmd = a.get("command", "") if isinstance(a, dict) else str(a)
            j, raw = parse_obs(s.get("observation") if len(tcs) == 1 else None)
            text, code = obs_text_and_exit(j, raw)
            if is_repro_run(cmd):
                p = repro_pass(text, code, bool(raw))
                f["ran_repro"] = True
                f["repro_runs"] += 1
                if f["repro_runs"] == 1:
                    f["repro_first_pass"] = p
                f["repro_pass"] = p
            elif is_pytest_run(cmd):
                f["ran_pytest"] = True
                f["pytest_ok"] = pytest_ok(text, code) if raw else None
    return f


def norm_diff(patch_text):
    out = []
    for ln in patch_text.split("\n"):
        if ln.startswith(("+++", "---")) or not ln.startswith(("+", "-")):
            continue
        out.append(ln[0] + "".join(ln[1:].split()))
    return tuple(out)


def load():
    data, dups = {}, {}
    for arm, v in ARMS:
        rows = {}
        dup = 0
        for d in DIRS:
            for line in open(RUNS / d / "results" / v / "results.jsonl"):
                if not line.strip():
                    continue
                x = json.loads(line)
                k = (x["instance_id"], x["rep"])
                if k in rows:
                    dup += 1
                x["_dir"] = d
                rows[k] = x
        dups[arm] = dup
        att = []
        for (iid, rep), x in sorted(rows.items()):
            base = RUNS / x["_dir"] / "results" / v
            pf = base / "patches" / f"{iid}.r{rep}.patch"
            ptxt = pf.read_text(errors="replace") if pf.exists() else ""
            ne = len(ptxt) > 0
            assert ne == (x["patch_chars"] > 0), (iid, rep)
            f = extract(RUNS / x["_dir"] / "results" / x["trace"])
            f.update(arm=arm, iid=iid, rep=rep, resolved=bool(x["resolved"]), nonempty=ne,
                     patch_chars=len(ptxt), agent_s=x["agent_s"], ndiff=norm_diff(ptxt),
                     tool_calls_row=x["tool_calls"])
            f["rpass"] = bool(f["repro_pass"])
            f["pok"] = bool(f["pytest_ok"])
            f["verified"] = ne and f["rpass"] and f["pok"]
            att.append(f)
        data[arm] = att
    return data, dups


# ---- selectors: each returns the expected `resolved` of the selected attempt in the subset ----
def tie_mean(items, key):
    best = max(key(a) for a in items)
    top = [a for a in items if key(a) == best]
    return sum(a["resolved"] for a in top) / len(top), top


def key_s1(a):
    tier = 3 if (a["nonempty"] and a["rpass"] and a["pok"]) else 2 if (a["nonempty"] and a["pok"]) else 1 if a["nonempty"] else 0
    return (tier, -a["patch_chars"])


def key_s1r(a):
    tier = 2 if (a["nonempty"] and a["rpass"]) else 1 if a["nonempty"] else 0
    return (tier, -a["patch_chars"])


def key_s1any(a):
    tier = 2 if (a["nonempty"] and (a["rpass"] or a["pok"])) else 1 if a["nonempty"] else 0
    return (tier, -a["patch_chars"])


def sel_s1any(sub):
    return tie_mean(sub, key_s1any)[0]


def sel_s0(sub):
    return sum(a["resolved"] for a in sub) / len(sub)


def sel_nonempty(sub):
    ne = [a for a in sub if a["nonempty"]] or sub
    return sum(a["resolved"] for a in ne) / len(ne)


def sel_s1(sub):
    return tie_mean(sub, key_s1)[0]


def sel_s1r(sub):
    return tie_mean(sub, key_s1r)[0]


def sel_s2(sub):
    ne = [a for a in sub if a["nonempty"]]
    if not ne:
        return 0.0
    cnt = defaultdict(int)
    for a in ne:
        cnt[a["ndiff"]] += 1
    m = max(cnt.values())
    cand = [a for a in ne if cnt[a["ndiff"]] == m]
    return tie_mean(cand, key_s1)[0]


def sel_oracle(sub):
    return float(any(a["resolved"] for a in sub))


SELS = [("oracle", sel_oracle), ("S0", sel_s0), ("S_nonempty", sel_nonempty),
        ("S1", sel_s1), ("S1r", sel_s1r), ("S2", sel_s2), ("S1any", sel_s1any)]


def per_task(att):
    g = defaultdict(list)
    for a in att:
        g[a["iid"]].append(a)
    return g


def task_values(g):
    """task -> k -> selector -> expected value over all C(n,k) subsets."""
    out = {}
    for t, atts in g.items():
        out[t] = {}
        for k in range(1, len(atts) + 1):
            subs = list(combinations(atts, k))
            out[t][k] = {name: sum(f(s) for s in subs) / len(subs) for name, f in SELS}
    return out


def total(tv, k, name, tasks=None):
    return sum(tv[t][k][name] for t in (tasks if tasks is not None else tv))


def boot(tv, k, name, rng, tasks):
    res = []
    for _ in range(NBOOT):
        samp = [tasks[rng.randrange(len(tasks))] for _ in tasks]
        res.append(sum(tv[t][k][name] for t in samp))
    res.sort()
    return res[int(0.05 * NBOOT)], res[int(0.95 * NBOOT) - 1]


def boot_diff(tv, k, n1, n2, rng, tasks):
    res = []
    for _ in range(NBOOT):
        samp = [tasks[rng.randrange(len(tasks))] for _ in tasks]
        res.append(sum(tv[t][k][n1] - tv[t][k][n2] for t in samp))
    res.sort()
    return res[int(0.05 * NBOOT)], res[int(0.95 * NBOOT) - 1]


def main():
    global DIRS, ARMS
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", help="comma-separated run directories under results/modal")
    ap.add_argument("--arms", help="comma-separated ARM=variant pairs")
    args = ap.parse_args()
    if args.dirs:
        DIRS = args.dirs.split(",")
    if args.arms:
        ARMS = [tuple(x.split("=", 1)) for x in args.arms.split(",")]
    data, dups = load()
    print(f"repo root: {REPO}")
    print("duplicates (same instance_id, rep in r2 and r4; r4 kept): " + ", ".join(f"{a}={n}" for a, n in dups.items()))
    for arm in data:
        att = data[arm]
        g = per_task(att)
        print(f"{arm}: {len(att)} attempts, {len(g)} tasks, attempts/task {sorted(set(len(v) for v in g.values()))}, "
              f"multi-call steps {sum(a['multi_call_steps'] for a in att)}, "
              f"tool-call count mismatch vs results.jsonl: {sum(a['ntool'] != a['tool_calls_row'] for a in att)}")

    print("\n== Extracted fields (counts over attempts) ==")
    hdr = ["arm", "n", "resolved", "nonempty", "submit", "ran_repro", "repro_pass", "repro_1st_pass", "ran_pytest", "pytest_ok", "verified", "mean_s", "mean_tools"]
    print("  ".join(f"{h:>9}" for h in hdr))
    for arm, att in data.items():
        row = [arm, len(att), sum(a["resolved"] for a in att), sum(a["nonempty"] for a in att), sum(a["submitted"] for a in att),
               sum(a["ran_repro"] for a in att), sum(a["rpass"] for a in att), sum(bool(a["repro_first_pass"]) for a in att),
               sum(a["ran_pytest"] for a in att), sum(a["pok"] for a in att), sum(a["verified"] for a in att),
               round(statistics.mean(a["agent_s"] for a in att), 1), round(statistics.mean(a["ntool"] for a in att), 1)]
        print("  ".join(f"{str(x):>9}" for x in row))
    print("  (repro_1st_pass: attempts whose FIRST repro run already passed, i.e. repro never failed before the edit)")

    print("\n== 3 example attempts (sanity check of the parsing) ==")
    shown = 0
    for arm in [a for a in ("A1",) if a in data]:
        att = data[arm]
        picks = [next((a for a in att if a["ran_repro"] and a["rpass"] and a["resolved"]), None),
                 next((a for a in att if a["ran_repro"] and not a["rpass"]), None),
                 next((a for a in att if a["ran_pytest"] and a["pok"] and not a["resolved"]), None)]
        for a in filter(None, picks):
            print({k: a[k] for k in ("arm", "iid", "rep", "resolved", "nonempty", "patch_chars", "ran_repro", "repro_runs", "repro_pass",
                                      "ran_pytest", "pytest_ok", "submitted", "agent_s", "ntool")})
            shown += 1

    rng = random.Random(SEED)
    tvs = {}
    for arm in data:
        g = per_task(data[arm])
        short = sorted(t for t, v in g.items() if len(v) != 4)
        if short:
            print(f"{arm}: {len(short)} tasks without exactly 4 attempts excluded: {short}")
        g = {t: v for t, v in g.items() if len(v) == 4}
        tvs[arm] = task_values(g)
        tv = tvs[arm]
        tasks = sorted(tv)
        print(f"\n== {arm}: expected resolved tasks out of {len(tasks)} (mean over all C(4,k) subsets) ==")
        print(f"{'k':>2} " + " ".join(f"{n:>11}" for n, _ in SELS) + "   |  efficiency (Sx-S0)/(oracle-S0): " + " ".join(f"{n:>10}" for n, _ in SELS[2:]))
        for k in range(1, 5):
            vals = {n: total(tv, k, n) for n, _ in SELS}
            den = vals["oracle"] - vals["S0"]
            eff = " ".join(f"{(vals[n] - vals['S0']) / den:>10.2f}" if den > 1e-9 else f"{'n/a':>10}" for n, _ in SELS[2:])
            print(f"{k:>2} " + " ".join(f"{vals[n]:>11.2f}" for n, _ in SELS) + "   |  " + " " * 34 + eff)
        print(f"-- 90% task-bootstrap ({NBOOT} resamples, seed {SEED}) --")
        for k in (2, 3, 4):
            lo_o, hi_o = boot(tv, k, "oracle", rng, tasks)
            lo_s, hi_s = boot(tv, k, "S1", rng, tasks)
            lo_0, hi_0 = boot(tv, k, "S0", rng, tasks)
            lo_d, hi_d = boot_diff(tv, k, "oracle", "S1", rng, tasks)
            print(f"k={k}: oracle {total(tv, k, 'oracle'):.2f} [{lo_o:.2f}, {hi_o:.2f}]  S1 {total(tv, k, 'S1'):.2f} [{lo_s:.2f}, {hi_s:.2f}]  "
                  f"S0 {total(tv, k, 'S0'):.2f} [{lo_0:.2f}, {hi_0:.2f}]  oracle-S1 {total(tv, k, 'oracle') - total(tv, k, 'S1'):.2f} [{lo_d:.2f}, {hi_d:.2f}]")
        lo_h1, hi_h1 = boot_diff(tv, 4, "oracle", "S0", rng, tasks)
        lo_h2, hi_h2 = boot_diff(tv, 4, "S1any", "S0", rng, tasks)
        lo_h2b, hi_h2b = boot_diff(tv, 4, "S1", "S0", rng, tasks)
        print(f"H1' pass@4 - pass@1: {total(tv, 4, 'oracle') - total(tv, 1, 'S0'):.2f} [{lo_h1:.2f}, {hi_h1:.2f}]")
        print(f"H2' best@4(S1any) - pass@1: {total(tv, 4, 'S1any') - total(tv, 1, 'S0'):.2f} [{lo_h2:.2f}, {hi_h2:.2f}]"
              f"  (secondary S1: {total(tv, 4, 'S1') - total(tv, 1, 'S0'):.2f} [{lo_h2b:.2f}, {hi_h2b:.2f}])")
        print("-- tasks by number of resolved attempts out of 4:",
              dict(sorted(Counter(sum(a["resolved"] for a in v) for v in g.values()).items())))

    print("\n== Attempt-level flags vs hidden verdict (confusion counts) ==")
    print(f"{'arm':>3} {'flag':<24} {'TP':>4} {'FP':>4} {'FN':>4} {'TN':>4} {'precision':>10} {'recall':>8}")
    for arm, att in data.items():
        for name, fn in (("verified (repro&pytest)", lambda a: a["verified"]), ("repro pass (nonempty)", lambda a: a["nonempty"] and a["rpass"]),
                         ("pytest ok (nonempty)", lambda a: a["nonempty"] and a["pok"]),
                         ("repro OR pytest ok", lambda a: a["nonempty"] and (a["rpass"] or a["pok"])), ("nonempty", lambda a: a["nonempty"])):
            tp = sum(fn(a) and a["resolved"] for a in att)
            fp = sum(fn(a) and not a["resolved"] for a in att)
            fn_ = sum((not fn(a)) and a["resolved"] for a in att)
            tn = sum((not fn(a)) and not a["resolved"] for a in att)
            p = f"{tp / (tp + fp):.2f}" if tp + fp else "n/a"
            r = f"{tp / (tp + fn_):.2f}" if tp + fn_ else "n/a"
            print(f"{arm:>3} {name:<24} {tp:>4} {fp:>4} {fn_:>4} {tn:>4} {p:>10} {r:>8}")
    print("  base rate resolved: " + ", ".join(f"{arm} {sum(a['resolved'] for a in att)}/{len(att)}" for arm, att in data.items()))

    print("\n== Tasks where S1 at k=4 picks a resolved attempt vs oracle (A1, tasks with oracle=1) ==")
    if "A1" not in tvs:
        return
    tv = tvs["A1"]
    cov = [(t, tv[t][4]["S1"]) for t in sorted(tv) if tv[t][4]["oracle"] == 1]
    print(f"{len(cov)} tasks with >=1 resolved attempt; S1 expected hit rate on them: {sum(v for _, v in cov) / max(1, len(cov)):.2f}")


if __name__ == "__main__":
    main()
