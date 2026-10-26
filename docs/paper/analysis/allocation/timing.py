"""H3': does one L4 batch E4B attempts? Attempt time at concurrency 4 against concurrency 1.

Offline, standard library only. Run:
  python3 -I timing.py results/modal/t-c1/results/e4b-v2/results.jsonl \
                       results/modal/t-c4/results/e4b-v2/results.jsonl

The two files are the same arm on the same tasks, one attempt per task, at concurrency 1 and 4.
Primary statistic: ratio of total agent seconds, sum(agent_s at c4) / sum(agent_s at c1), over
the tasks present in both files, with a 90% task-bootstrap interval. H3' holds if the ratio is
<= 1.6. Secondary: the same ratio for seconds per tool call (the two runs take different paths,
so per-call time separates server slowdown from path length) and for wall seconds (setup and
hidden-test verification included).
"""
import json
import random
import sys

SEED = 20261026
NBOOT = 2000


def load(path):
    rows = {}
    for line in open(path):
        if line.strip():
            x = json.loads(line)
            rows[x["instance_id"]] = x
    return rows


def ratio(tasks, a, b, f):
    return sum(f(b[t]) for t in tasks) / sum(f(a[t]) for t in tasks)


def boot(tasks, a, b, f, rng):
    res = []
    for _ in range(NBOOT):
        samp = [tasks[rng.randrange(len(tasks))] for _ in tasks]
        res.append(ratio(samp, a, b, f))
    res.sort()
    return res[int(0.05 * NBOOT)], res[int(0.95 * NBOOT) - 1]


def main():
    a, b = load(sys.argv[1]), load(sys.argv[2])
    tasks = sorted(set(a) & set(b))
    print(f"{len(tasks)} paired tasks (c1 only: {sorted(set(a) - set(b))}, c4 only: {sorted(set(b) - set(a))})")
    rng = random.Random(SEED)
    stats = [("agent_s (primary)", lambda x: float(x["agent_s"])),
             ("agent_s per tool call", lambda x: float(x["agent_s"]) / max(1, x["tool_calls"])),
             ("wall_s", lambda x: float(x["wall_s"]))]
    for name, f in stats:
        lo, hi = boot(tasks, a, b, f, rng)
        print(f"{name:<24} c1 mean {sum(f(a[t]) for t in tasks) / len(tasks):7.1f}  "
              f"c4 mean {sum(f(b[t]) for t in tasks) / len(tasks):7.1f}  "
              f"ratio c4/c1 {ratio(tasks, a, b, f):.2f} [{lo:.2f}, {hi:.2f}]")
    print(f"resolved: c1 {sum(bool(a[t]['resolved']) for t in tasks)}, c4 {sum(bool(b[t]['resolved']) for t in tasks)}")


if __name__ == "__main__":
    main()
