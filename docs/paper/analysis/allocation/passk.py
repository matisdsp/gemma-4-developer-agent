"""Per-task heterogeneity, pass@k and paired arm comparisons from harness results.jsonl files.

Each line of a results.jsonl is one attempt: {"variant", "instance_id", "rep", "resolved",
"agent_s", ...} (format written by kaggle/runner.py and the Modal/Mac runners).

Usage:
  python -I passk.py summary <results.jsonl> [more.jsonl ...] [--variant V] [--tasks list.txt]
  python -I passk.py compare <results.jsonl> [...] --a VARIANT_A --b VARIANT_B [--tasks list.txt]

summary: per-task successes c out of r, share of tasks with 0 < c < r, unbiased pass@k for
k = 1..r_min (Chen et al. 2021), the homogeneous prediction 1 - (1 - p)^k, a method-of-moments
beta-binomial intra-task correlation, and 90% task-bootstrap intervals.
compare: per-task expected success of each arm (c / r), mean difference in tasks, a paired
sign-flip permutation test on the per-task differences, and the discordant-task counts.
"""
import argparse
import json
import random
from collections import defaultdict
from math import comb


def load(paths, variant=None, tasks=None):
    keep = set(open(tasks).read().split()) if tasks else None
    per = defaultdict(lambda: defaultdict(list))  # variant -> task -> [resolved...]
    secs = defaultdict(list)
    for p in paths:
        for line in open(p):
            if not line.strip():
                continue
            r = json.loads(line)
            if variant and r.get("variant") != variant:
                continue
            if keep is not None and r["instance_id"] not in keep:
                continue
            per[r.get("variant", "?")][r["instance_id"]].append(bool(r["resolved"]))
            secs[r.get("variant", "?")].append(float(r.get("agent_s", 0.0)))
    return per, secs


def pass_at_k(n, c, k):
    """Unbiased estimator of pass@k from c successes in n samples."""
    if n - c < k:
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)


def icc_beta_binomial(cs, r):
    """Method-of-moments intra-task correlation for equal r (0 = homogeneous binomial)."""
    m = len(cs)
    p = sum(cs) / (m * r)
    if p in (0.0, 1.0) or r < 2:
        return float("nan")
    var = sum((c / r - p) ** 2 for c in cs) / (m - 1)
    # Var(c/r) = p(1-p)/r * (1 + (r-1) rho)
    return (var * r / (p * (1 - p)) - 1) / (r - 1)


def bootstrap(fn, items, n=2000, seed=0):
    rng = random.Random(seed)
    vals = sorted(fn([rng.choice(items) for _ in items]) for _ in range(n))
    return vals[int(0.05 * n)], vals[int(0.95 * n)]


def summary(per, secs):
    for v, tasks in per.items():
        r = min(len(x) for x in tasks.values())
        rows = [(t, sum(x[:r]), r) for t, x in sorted(tasks.items())]
        cs = [c for _, c, _ in rows]
        m = len(rows)
        mixed = sum(0 < c < r for c in cs)
        p = sum(cs) / (m * r)
        print(f"== variant {v}: {m} tasks, r = {r}, mean agent s = "
              f"{sum(secs[v]) / max(len(secs[v]), 1):.1f}")
        print(f"   successes per task: {dict(sorted({c: cs.count(c) for c in set(cs)}.items()))}")
        print(f"   mixed tasks (0 < c < r): {mixed}/{m}; never solved {cs.count(0)}; always {cs.count(r)}")
        print(f"   intra-task correlation (beta-binomial, moments): {icc_beta_binomial(cs, r):.3f}")
        for k in range(1, r + 1):
            pk = sum(pass_at_k(r, c, k) for c in cs)
            lo, hi = bootstrap(lambda s: sum(pass_at_k(r, c, k) for c in s), cs)
            homo = m * (1 - (1 - p) ** k)
            print(f"   pass@{k}: {pk:.2f} tasks (90% CI {lo:.2f}-{hi:.2f}); homogeneous prediction {homo:.2f}")
        print("   per task: " + ", ".join(f"{t}:{c}/{rr}" for t, c, rr in rows))


def compare(per, a, b, n_perm=20000, seed=0):
    ta, tb = per[a], per[b]
    common = sorted(set(ta) & set(tb))
    d = [sum(ta[t]) / len(ta[t]) - sum(tb[t]) / len(tb[t]) for t in common]
    obs = sum(d)
    rng = random.Random(seed)
    ge = sum(abs(sum(x if rng.random() < 0.5 else -x for x in d)) >= abs(obs) - 1e-12
             for _ in range(n_perm))
    lo, hi = bootstrap(lambda s: sum(s), d)
    print(f"== {a} minus {b} on {len(common)} common tasks: {obs:+.2f} expected tasks "
          f"(90% CI {lo:+.2f} to {hi:+.2f}), permutation p = {ge / n_perm:.3f}")
    print(f"   tasks better under {a}: {sum(x > 0 for x in d)}, under {b}: {sum(x < 0 for x in d)}, "
          f"tied: {sum(x == 0 for x in d)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["summary", "compare"])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--variant")
    ap.add_argument("--tasks")
    ap.add_argument("--a")
    ap.add_argument("--b")
    args = ap.parse_args()
    per, secs = load(args.files, args.variant, args.tasks)
    if args.mode == "summary":
        summary(per, secs)
    else:
        compare(per, args.a, args.b)


if __name__ == "__main__":
    main()
