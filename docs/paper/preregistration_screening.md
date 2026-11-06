# Pre-registration: which recipes move a 4B coding agent?

Status: **draft, not frozen**. It freezes when Matis approves it, before any attempt of the full
run. Nothing below may change after that; deviations are reported as deviations. This study is
independent of `preregistration.md`, which stays as it is.

## Question

Gemma 4 E4B resolves about 15% of the public gold-scorable tasks. Eight recipes, all available to
any declarative agent in the official harness, are claimed in papers, on the forum or in our own
traces to change that. Which of them move the resolved share, by how much, and does the model obey
them at all? Recipes vary together in a factorial design, so each one is measured on all attempts.

## Recipes

Each recipe has two levels. Exact text: `scripts/make_screening.py`.

| Letter | Recipe | Off | On |
|---|---|---|---|
| A | `temperature_0.7` | temperature 0.2 | temperature 0.7 |
| B | `thinking_256` | thinking budget 4096 | thinking budget 256 |
| C | `spec_first` | no such step | names, messages and edge cases listed before acting |
| D | `reproduce_first` | no such step | script in /tmp that must fail before the edit |
| E | `imposed_verification` | verify in at most 2-3 calls | no submission before the check, "spend your budget on checking" |
| F | `useful_test` | `-k` and `tail` advised, "pre-existing failures: ignore" | whole test file, "zero tests is not a check", no such excuse |
| G | `compile_check` | no such rule | `python -m py_compile` after every edit |
| H | `worked_example` | none | one session on a made-up project, showing only the active recipes |

Fixed: E4B QAT w4a16, top_p 0.95, max output 6144, 36 tool calls, 10 minutes per task (7 minutes on
an idle GPU; the 4xL4 decode bench gives 8.6 ms per step alone and 11.4 ms at 8 concurrent attempts,
and the pilot had 1 attempt of 96 at this cap), 6 tools.

## Design

2^(8-3) fractional factorial, resolution IV, 32 configurations: A to E crossed, F = ABC, G = ABD,
H = -ACDE. Every recipe is on in 16 configurations, recipes are orthogonal, and main effects are
clear of two-way interactions. Two-way interactions with E or H are all clear (13 of 28). The other
two-way interactions are aliased in pairs or triples and are not interpreted. Properties are tested
in `tests/test_screening.py`.

## Tasks and runs

- **Tasks.** `reports/screening_tasks_72.txt`: the 75 tasks of `reports/gold_ok.txt` minus the 3
  whose hidden tests pass with a patch that changes nothing (`g4agent-noop`: fastapi_14077,
  fastapi_14851, requests_6644). Fixed by that rule alone.
- **Attempts.** 72 tasks x 32 configurations x 1 repeat = 2,304 attempts.
- **Stack.** Private Kaggle kernels on 4xL4 with the scorer's vLLM settings (tensor parallel 4,
  bfloat16, gemma4 parsers), official harness with the subprocess sandbox, concurrency 8.
- **Blocks.** Three kernels, `g4agent-sc1` to `g4agent-sc3`, on `reports/screening_block{1,2,3}.txt`
  (24 tasks each, stratified by repository, seed 20261106), each attempt order shuffled by seed
  (20261101, 20261102, 20261103), deadline 10.5 h. Every configuration of a task runs inside the
  same block, so effects are measured within tasks and blocks cannot confound them.
- **Pilot.** `g4agent-pilot` (96 attempts on 3 calibration tasks) is excluded. Only infrastructure
  and compliance were read on it, with comparisons of resolved tasks hidden. It led to one change,
  the `spec_stated` compliance measure.

## Analysis

`docs/paper/analysis/screening/analyze.py`, command in its docstring. For each recipe and each task:
the mean outcome of attempts with the recipe on, minus the mean with it off. The effect is the mean
of these differences over tasks. Intervals: 90%, 2,000 task-bootstrap resamples. p values: two-sided
sign flip of task differences, 10,000 permutations. Seed 20261106.

**Primary outcome: resolved.** Eight tests, Holm adjusted. For each recipe, the reading is:
- **helps** or **hurts**: the interval excludes zero and the Holm p is below 0.05;
- **no effect beyond 3 points**: the interval lies inside (-3, +3) points;
- **unresolved**: anything else.

Three points is about one fifth of the base rate and one and a half tasks of 58 on the leaderboard.
Simulation from the earlier per-task rates gives an interval half-width of about 1.6 points, if a
recipe acts alike across tasks.

**Predictions, to be scored in the paper, not used as thresholds.** `useful_test` and
`worked_example` help. `reproduce_first` and `spec_first` show no effect beyond 3 points.
`compile_check` and `imposed_verification` are unresolved or help. `temperature_0.7` hurts.
`thinking_256` shows no effect beyond 3 points and saves time.

**Secondary.** Compliance of each rule: `spec_stated`, `repro_before_edit`, `check_after_edit`,
`pytest_runs_tests`, `last_pytest_real`, `compile_after_edit`. Manipulation checks: completion
tokens per call, distinct patches. Also non-empty patches, syntax-broken patches and agent seconds.

**Exploratory, labelled so.** The 13 clear interactions, first of all whether the worked example
raises obedience; the figure crossing "did it obey" with "did it help"; the table of 32
configurations; which tasks are ever resolved.

**Exclusions and reruns.** An attempt lost to infrastructure (kernel crash, no results line) is
rerun with `--skip-done` until it exists. Agent failures (empty patch, time cap, wrong fix) are
never excluded. If a task still lacks attempts in some configurations, effects use what exists and
the shortfall is reported.

**External check, optional, not part of the claims.** The best configuration according to the main
effects may be submitted to the leaderboard, on private repositories, only with Matis's approval.
One draw of 58 tasks has a noise of about 4 points, so it can only reject a large claim.

## Known limits, to state in the paper

- All tasks were used in earlier work. `useful_test` and `compile_check` come from reading traces on
  these same tasks, so their effects are measured on tasks that suggested them.
- 72 tasks from two repositories (rich, fastapi). Hidden private repositories may behave otherwise.
- Three tasks of the earlier 75 turned out not to discriminate. Earlier results include them.
- One model. Nothing here is claimed for larger models.
- 10-minute cap and concurrency 8 differ from the scorer's sequential runs at 7 to 8 minutes.

## SHA-256 of the frozen files

To be filled at freeze. Check with `shasum -a 256 -c` from the repository root.
