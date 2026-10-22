"""Best public score vs number of submissions on a Kaggle leaderboard CSV (k/58 truncated scores).

Usage: python -I best_score_vs_submissions.py <leaderboard.csv>
The CSV comes from `kaggle competitions leaderboard gemma-4-developer-agent -d`.
"""
import csv, math, statistics as st, sys, collections

N_TASKS = 58
rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8-sig")))

def k_from(score):
    """Smallest k whose k/58, truncated to two decimals, equals the displayed score."""
    ks = [k for k in range(N_TASKS + 1) if math.floor(k / N_TASKS * 100 + 1e-9) / 100 == score]
    return ks[0] if ks else None

k = [k_from(float(r["Score"])) for r in rows]
n = [int(r["SubmissionCount"]) for r in rows]
print("teams", len(rows), "distribution of k:", sorted(collections.Counter(k).items()))
for lo, hi in [(1, 1), (2, 3), (4, 6), (7, 10), (11, 15), (16, 1000)]:
    ks = [a for a, b in zip(k, n) if lo <= b <= hi and a is not None]
    print(f"submissions {lo}-{hi}: teams {len(ks)}, mean best k {st.mean(ks):.2f}, "
          f"median {st.median(ks)}, share >= 13: {sum(x >= 13 for x in ks) / len(ks):.3f}")
