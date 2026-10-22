"""Entry point: extract snapshots (py only) -> per-task analysis (parallel, cached) -> aggregate.

Usage (offline, read-only on the repo data):
  .venv/bin/python -I analysis/scripts/run_all.py [--force]
"""
import json
import subprocess
import sys
import time
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lib  # noqa: E402



def work(args):
    iid, df_max, per = args
    import analyze
    analyze.DF_MAX_FRAC = df_max
    p = Path(per) / f"{iid}.json"
    try:
        r = analyze.analyze(iid)
        p.write_text(json.dumps(r, sort_keys=True))
        return iid, None
    except Exception as e:  # keep going, report
        import traceback
        return iid, traceback.format_exc()


def main():
    force = "--force" in sys.argv
    df_max = 0.05  # identifiers present in >df_max of all code units are dropped as "very common names"
    if "--df-max" in sys.argv:
        df_max = float(sys.argv[sys.argv.index("--df-max") + 1])
        lib.OUT = lib.ANALYSIS / "out" / f"sens_df{df_max}"
        lib.OUT.mkdir(parents=True, exist_ok=True)
    PER = lib.OUT / "per_task"
    PER.mkdir(parents=True, exist_ok=True)
    tasks = [json.loads(l) for l in open(lib.DATA / "tasks.jsonl")]
    iids = sorted(t["instance_id"] for t in tasks)
    # 1. extraction (idempotent, only *.py, no .git)
    if not all((lib.SNAP / i / ".done").exists() for i in iids):
        subprocess.run([str(HERE / "extract_snaps.sh")], check=True)
    # 2. per-task analysis
    todo = [i for i in iids if force or not (PER / f"{i}.json").exists()]
    t0 = time.time()
    errs = {}
    if todo:
        with Pool(4) as pool:
            for iid, err in pool.imap_unordered(work, [(i, df_max, str(PER)) for i in todo]):
                if err:
                    errs[iid] = err
                    print("ERR", iid, err.splitlines()[-1], flush=True)
    print(f"per-task done: {len(todo)} tasks in {time.time()-t0:.0f}s, {len(errs)} errors")
    (lib.OUT / "errors.json").write_text(json.dumps(errs, indent=1))
    # 3. aggregate
    import aggregate
    aggregate.OUT = lib.OUT
    aggregate.main()


if __name__ == "__main__":
    main()
