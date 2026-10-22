"""Print a hand-check view of tasks: issue head, gold, tokens, top-5 of each localizer."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib, analyze
for iid in sys.argv[1:]:
    r = json.load(open(lib.OUT / "per_task" / f"{iid}.json"))
    T = analyze.load_task(iid)
    print("=" * 100); print(iid, r["created_at"], "nodes", r["schema"]["n_nodes"])
    print("ISSUE:", T["problem_statement"][:500].replace("\n", " | "))
    g = r["gold"]
    print("GOLD files:", g["gold_files"], "new:", g["new_files"], "modlevel:", g["module_level_files"])
    print("GOLD units:", g["gold_units"], "in graph:", g["gold_units_in_graph"], "async:", g.get("gold_units_async"))
    print("TOKENS:", r["issue"]["plain"][:15], r["issue"]["dotted"][:5], r["issue"]["paths"][:3])
    print("SEEDS:", r["seeds"]["n_seed_nodes"], r["seeds"]["s3"])
    for k, v in r["top"].items():
        m = r["methods"].get(k, {})
        print(f"  {k:7s} n={m.get('n')} first_gold={m.get('first_gold')} :: " + " ; ".join(x.split('/')[-1] for x in v[:5]))
