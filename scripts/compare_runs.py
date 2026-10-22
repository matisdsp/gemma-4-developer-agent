"""Paired comparison of variants from one or more results.jsonl files (runner output).

    uv run python scripts/compare_runs.py results/modal/a0a1-r2/results/*/results.jsonl

Per variant: attempts, resolved, per-task success frequency, empty patches, mean agent seconds
and tool calls. Per pair: tasks where one variant's success frequency beats the other's, and
an exact two-sided sign test on those discordant tasks.
"""

import argparse
import json
from collections import defaultdict
from itertools import combinations
from math import comb
from pathlib import Path


def sign_test(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2**n)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="+", type=Path)
    args = ap.parse_args()
    rows = [json.loads(line) for f in args.files for line in f.read_text().splitlines() if line.strip()]
    freq: dict[str, dict[str, list[bool]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        freq[r["variant"]][r["instance_id"]].append(bool(r["resolved"]))
    for v, by_task in sorted(freq.items()):
        rs = [r for r in rows if r["variant"] == v]
        n = len(rs)
        print(f"{v}: {n} attempts on {len(by_task)} tasks, resolved {sum(r['resolved'] for r in rs)} "
              f"({sum(r['resolved'] for r in rs) / max(1, n):.3f}), tasks solved at least once "
              f"{sum(any(x) for x in by_task.values())}, empty patches "
              f"{sum(1 for r in rs if not r.get('patch_chars'))}, mean agent "
              f"{sum(r.get('agent_s') or 0 for r in rs) / max(1, n):.0f}s, mean calls "
              f"{sum(r.get('tool_calls') or 0 for r in rs) / max(1, n):.1f}")
    for a, b in combinations(sorted(freq), 2):
        common = sorted(set(freq[a]) & set(freq[b]))
        rate = {v: {t: sum(freq[v][t]) / len(freq[v][t]) for t in common} for v in (a, b)}
        wa = [t for t in common if rate[a][t] > rate[b][t]]
        wb = [t for t in common if rate[b][t] > rate[a][t]]
        print(f"{a} vs {b} on {len(common)} tasks: {a} better on {len(wa)}, {b} better on "
              f"{len(wb)}, sign test p={sign_test(len(wa), len(wb)):.3f}")
        print(f"  {a} better: {wa}\n  {b} better: {wb}")


if __name__ == "__main__":
    main()
