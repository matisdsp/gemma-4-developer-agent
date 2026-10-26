# Pre-registration: confirmatory run for direction 1

Frozen 2026-10-26, approved by Matis, committed before any agent attempt on the held-out tasks.
Exploratory evidence behind these hypotheses: `gaps.md` M7b, M7c, M11 (the 40-task pool,
`reports/modal_pool_40.txt`). Nothing below may be changed after the runs start; deviations
are reported as deviations.

## Hypotheses

- **H1'.** A1's pass@4 exceeds its pass@1 on the 35 held-out tasks, 90% task-bootstrap interval
  above zero. The fitted beta-binomial intra-task correlation is reported with its interval,
  against 0.46 on the 40-task pool.
- **H2'.** S1any (own repro passed OR last pytest clean, then smallest non-empty patch) gives
  best@4 - pass@1 > 0 for A1, 90% task-bootstrap interval above zero. S1 is secondary. S3 (LLM
  judge) is reported, if run at all, as a control for a small judge only.
- **H3'.** On one L4, E4B (A1) attempt time at 4 concurrent attempts is at most 1.6x the time
  at 1. If not, batched width is dropped and only sequential width is claimed.
- **Exploratory, not pre-registered:** A1 vs A0 (A0 is not re-run on the held-out tasks), A1 at
  thinking 2048 against 4096, the time-bound 31B and 12B results (already seen).

## Arms, tasks and runs

- **A1** = `variants/e4b-v2`, unchanged since e9bfad6 (Gemma 4 E4B QAT w4a16, temperature 0.2,
  thinking 4096, 36 calls / 7 min, forced reproduce-then-verify). A1 is the only arm.
- **Held-out tasks** = `reports/modal_heldout_35.txt`: the 35 tasks of `reports/gold_ok.txt`
  outside the 40-task pool (fastapi 16, rich 18, requests 1). Fixed by set difference, no
  selection. No agent has run on them on Modal. Reference patches pass 35/35 on the Modal image
  (run `gold-ho35`, CPU, 2026-10-26) before any agent run.
- **Run `a1-ho35`** (H1', H2'): A1, 35 tasks x 4 repeats = 140 attempts, concurrency 8 (as on
  the 40-task pool), deadline 2.5 h, Modal 1xL4 + 8 CPU.
- **Runs `t-c1` and `t-c4`** (H3'): A1 on `reports/eval_calib_14.txt`, one attempt per task, at
  concurrency 1 and 4 respectively, one vLLM server per run on its own L4, deadline 1.5 h each.
  These are development tasks: H3' is about time, not resolution.
- Stack for every run: runner `kaggle/runner.py` at 7b11402, Modal app `cloud/modal_eval.py` at
  9b3ff71, vLLM flags and harness settings as in `reports/runs/manifest.json`.

## Analysis (scripts frozen with this file)

```bash
python3 -I docs/paper/analysis/allocation/selectors.py --dirs a1-ho35 --arms A1=e4b-v2   # H1', H2'
python3 -I docs/paper/analysis/allocation/passk.py summary \
    results/modal/a1-ho35/results/e4b-v2/results.jsonl                                  # ICC, pass@k
python3 -I docs/paper/analysis/allocation/timing.py \
    results/modal/t-c1/results/e4b-v2/results.jsonl \
    results/modal/t-c4/results/e4b-v2/results.jsonl                                     # H3'
```

- H1' reads the `H1' pass@4 - pass@1` line, H2' the `H2' best@4(S1any) - pass@1` line (both
  in expected tasks, 2000 task-bootstrap resamples, seed 20261023).
- H3' reads the `agent_s (primary)` ratio: sum of agent seconds at c4 over c1, paired by task,
  2000 resamples, seed 20261026. Seconds per tool call and wall seconds are secondary.
- **Exclusions.** An attempt lost to infrastructure (container crash, no results line) is rerun
  with `--skip-done` until every task has 4 attempts. If a deadline still leaves a task short,
  it is excluded from H1'/H2' (the script prints it) and reported. Agent failures (empty patch,
  time cap, wrong fix) are never excluded.
- No selector, prompt or setting is tuned on these tasks. Selector code is the frozen file.

## SHA-256 of the frozen files

```
320bf32386391fa38d4cfcb3eb149b414ad69300c06726ca1136f3687e62276e  docs/paper/analysis/allocation/passk.py
a5eef7a1aec2c14fecff9b693255c63daf81fa00d215771ad6f99257f2ef7d05  docs/paper/analysis/allocation/selectors.py
b525355a218c0b18e26254afc0627211151322dee5078e68e51bc0218d7a941d  docs/paper/analysis/allocation/timing.py
577c4832fc1561bc7d49e96152f04b476794ecbc3ab1e1cf325fd5a51ff80dac  reports/runs/a1-ho35/run.py
d48cd7f7fdba851feb44dd4c4ab54caea56aab9112530ddf405df5cfaf12121e  reports/runs/t-c1/run.py
caca2110d4a1a49276b422a9dd3fe0376f56faadbfbeb26fd263589b11643f1f  reports/runs/t-c4/run.py
a81bb414d1a9be92da28cedfdb66785cd11643beba98d4c8504b7d6cee5e28be  reports/modal_heldout_35.txt
39619db5e6133d0c3a76d7c90621449670671408800595b0d44204d1bf20eabe  reports/eval_calib_14.txt
```

Check: `shasum -a 256 -c` on the block above, from the repository root.
