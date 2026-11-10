# Addendum to the screening pre-registration: replication of the best configuration

Status: **frozen 2026-11-10, committed before any attempt of the replication.** Matis approved the
run. This file was written after the main results were known. `preregistration_screening.md` and
its frozen analysis stay as they are: this addendum adds one study and changes nothing in them.

## Why

The frozen analysis prints the table of 32 configurations as an exploratory output. One of them,
`s04` (`spec_first`, `useful_test` and `worked_example` on, the five other recipes off), resolved 15
of 72 tasks. The base prompt `s00`, with no recipe, resolved 9, and the 32 configurations resolved
8.4 on average. If the configuration changed nothing, with each attempt a coin with its task's
success rate, the best of 32 configurations would reach 15 or more in 1.6% of 40,000 simulations
(`replicate.py --selection-null`, from the published records). The spread of the 32 means taken
together is within chance (p = 0.17 in `explore.py`), and the main effects of these three recipes
are all slightly negative.

`s04` was picked because it is the maximum of 32, so its lead is inflated by selection, and one
attempt per task cannot tell luck from an effect of this combination. Only fresh attempts can.

## Question

Does `s04` resolve more tasks than `s00` on fresh attempts?

## Design

- **Configurations.** `s00` and `s04`, unchanged: the files written into the kernel are
  byte-identical to those of the main run (`variants/screening/s00`, `variants/screening/s04`).
- **Tasks.** The same 72 tasks, `reports/screening_tasks_72.txt`.
- **Attempts.** 72 tasks x 2 configurations x 4 repeats = 576 fresh attempts. The attempts of the
  main run are not part of the estimate.
- **Stack.** One private Kaggle kernel, `g4agent-rep1`, on 4xL4, with the image, vLLM settings,
  harness, runner code, budgets and concurrency 8 of the main run. Each repeat is declared as its
  own variant (`s00r1` to `s00r4`, `s04r1` to `s04r4`), so every attempt has its own results
  directory, as in the main run. Attempt order is shuffled with seed 20261110, so both
  configurations share the same load. Deadline 6.5 h. Attempts a deadline leaves out are run by a
  top-up kernel with `--skip-done`.
- **Size.** Four repeats use about 8 of the 18 GPU hours left this week, which leaves room for a
  top-up. At the task rates of the main run, the 90% interval has a half-width of about 2.8 points
  if `s04` changes nothing.

## Analysis

`docs/paper/analysis/screening/replicate.py`, command in its docstring. For each task: the resolved
share of its `s04` attempts minus the resolved share of its `s00` attempts. The estimate is the mean
of these differences over the 72 tasks. Interval and p value come from `summarize` of the frozen
`analyze.py`, unchanged: 90% interval from 2,000 task-bootstrap resamples, two-sided sign flip of
task differences with 10,000 permutations. Seed 20261110. One test, no adjustment.

Reading, by the rules of the pre-registration applied to this one contrast:
- **helps**: the interval lies above zero and p is below 0.05;
- **no advantage beyond 3 points**: the upper bound of the interval is below +3 points;
- **unresolved**: anything else.

If the first two both hold, the reading is "helps".

**Descriptive, labelled so.** Resolved counts by repeat and by repository, the single attempt of
the main run next to the fresh ones, and the obedience measures of the fresh attempts.

**Exclusions and reruns.** As in the pre-registration: an attempt lost to infrastructure is rerun
with `--skip-done` until it exists, agent failures are never excluded, and a shortfall is reported.

**Reporting.** The paper reports the table of 32 configurations, `s04`, this addendum and the result
of the replication, whatever the reading is.

## Known limits

- The configuration to replicate was chosen after seeing the main results. This is why the estimate
  uses fresh attempts only.
- A "helps" reading would hold for this combination of three recipes on these 72 tasks, not for
  each recipe: their main effects stay as measured.
- Same 72 tasks from two repositories as the main run. Another day and another kernel session,
  shared by both configurations.
- With four repeats, an advantage between 0 and about 3 points will most likely read "unresolved".

## SHA-256 of the frozen files

Check with `shasum -a 256 -c` from the repository root. The last two are unchanged from the
pre-registration.

```
8c57d4bd147c8586bfad5172f7b95c2491f471d3d1efb1cb4ea66b33cc8c017b  docs/paper/analysis/screening/replicate.py
3f9c42e8087f78ed63c390fa5874642f57accc3eed154b938dc15dc7d89319ed  tests/test_replicate.py
3f459305deaeed06afc6380ded83db1b21987a773919fc70d81032f9e3518f0a  reports/runs/screening-rep1/run.py
3140f56dcaee11bd722e7e17cab3d364d1c708b69ec2038b320124111d9e637b  docs/paper/analysis/screening/analyze.py
22802de1edab2ba29ea8000fab8577cf108c073b3a717d3c1cf7a187c23ddea6  reports/screening_tasks_72.txt
```
