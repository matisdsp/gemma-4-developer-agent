# Paper-track proposals, ranked

Deadline 2026-11-12 23:59 UTC, 3,000 words, five criteria at equal weight (novelty, generality,
relevance, verifiability, clarity). Topic to be locked by **2026-10-26**. Evidence for every claim
below is in `gaps.md` (G1-G10, measurements M1-M5) and `literature.md`.

## Constraints that drive the ranking

- **Compute.** Kaggle GPU quota is 6 h a week on this account (Kaggle API, 2026-10-22), not 30 h;
  a 4xL4 hour costs at least 2 quota hours. One 31B pass over 30 tasks takes 3-3.5 h of wall time,
  more than a week's quota. A small Modal budget (E4B/E2B only) may open, at the coordinator's
  discretion. The Mac (M4 Pro, 24 GB) runs E2B and E4B at 4 bits through mlx-lm, at 111 and 67
  decode tokens per second respectively (M1), and 12B at 4 bits fits. So: **experiments that run on the Mac
  or on CPU, with at most one or two small GPU runs to anchor them on the scorer's stack.**
- **Venue.** The graph and localization corner already has at least six announced entries; the
  trajectory-distillation corner has a dataset and a kit (gaps.md G6, G8). Avoid both as main
  topics.
- **Synergy.** The score agent's best open lead is the E4B bonus prize ($10,000; best E4B public
  score 0.06 on 2026-10-20). E4B stops after 66 s of its 420 s budget (M2). A paper about using
  that idle budget feeds the score work directly.
- **Data rule.** Competition data stays local; the paper may report aggregate results on the
  public tasks and must not redistribute them (rule 2.4.b). Any released resource is rebuilt
  from public upstream history or public benchmarks.

## Ranking at a glance

| # | Direction | Gaps | Novelty | Generality | Relevance | Verifiability | Feasibility in 3 weeks | Synergy with score |
|---|---|---|---|---|---|---|---|---|
| 1 | Spend the idle budget: wall-clock-matched width for small local coding agents | G1, G2, G3 | high | high | high | high (Mac-reproducible) | good: Mac + 1 GPU anchor | direct (E4B bonus) |
| 2 | Selection on noise: the winner's curse on agent leaderboards, with a pre-registered private-leaderboard prediction | G4 | high | medium-high | medium | very high (CPU) | very good | indirect (final-pick strategy) |
| 3 | What the tests know that the issue does not: measuring interface under-determination across SWE benchmarks | G5 | medium-low (2610.22760) | high | high | high (CPU) | good | small (prompt contract) |
| 4 | The marginal information of a calls-only code graph over lexical search | G6 | low in this venue | medium | medium | high (done, CPU) | done | none (tools already removed) |
| 5 | Harness-fit LoRA: distilling the 31B's harness behaviour into E4B | G8 | low-medium | medium | high | medium | poor (GPU) | direct but costly |

Recommendation: **#1 as the paper**, with #2 folded in as a short evaluation section only if the
noise model it needs comes out of #1's repeated samples anyway (it does: per-task success
frequencies). #3 is a fallback if #1 dies at its go/no-go on 2026-10-25. #4 becomes one paragraph
of related evidence. #5 is not recommended for the paper.

## 1. Spend the idle budget: wall-clock-matched width for small local coding agents

Working title: *Width Is Almost Free: Spending a Small Coding Agent's Idle Wall-Clock Budget on
Parallel Attempts.*

### Hypotheses (falsifiable)

- **H1 (coverage).** For Gemma 4 E4B on issue-resolution tasks, k independent attempts at
  temperature 1.0 cover more tasks than one: pass@4 exceeds pass@1 by at least 2 tasks on the 14
  calibration tasks and by at least 5 percentage points on the full Mac-scorable set. Null: E4B's
  failures are systematic (the same misreading in every attempt, as Confident-and-wrong 2603.25764
  reports for larger models), so coverage barely grows with k.
- **H2 (selection at tiny k).** A cheap execution-based selector (existing tests of the touched
  module + import check, then smallest diff) keeps at least half of the coverage gain at k = 4.
  Null: selection at k <= 4 with no trained verifier is no better than taking the first
  candidate (as for the agents' own tests in Kozuchi 2608.15579).
- **H3 (wall-clock rule).** On single-user hardware the wall-clock cost of b concurrent attempts
  is t(b) = t(1) * l(b)/l(1), with l the measured per-step decode latency (M1: l(2)/l(1) = 1.07,
  l(4)/l(1) = 1.47 for E4B on the Mac). The number of attempts that fit in a budget T is then
  n(b) = b * floor(T / t(b)), and the best b is predicted from l and the attempt-time
  distribution alone. Prediction: at T = 7 min and t(1) ~ 1-2 min, b = 2-4 beats both b = 1
  (sequential retries) and b = 8. Null: measured resolved-at-T does not follow the predicted
  ordering.

### Method

1. Sampling once, analysing many ways. For each task, draw r = 8 independent attempts of the
   unmodified E4B agent (official harness, same tools and prompt as `variants/e4b`, temperature
   1.0), store every patch and its timings. Unbiased pass@k for any k <= r follows from the
   number of successes c out of r (Chen et al. 2021 estimator), so k need not be re-run.
2. Selectors, applied offline to random k-subsets of the r candidates: S0 first candidate;
   S1 run the repository's existing tests nearest to the patched module + import check, pick
   fewest failures then smallest diff; S2 agreement, pick the candidate whose normalised diff
   (or behaviour on agent-written probes) is most common; S3 the model as judge (expected weak,
   kept as a negative control, cf. SWE-PRM 2509.02360). Report best@k = resolved rate of the
   selected candidate, and selection efficiency = (best@k - pass@1) / (pass@k - pass@1).
3. Wall-clock accounting. Measure l(b) for each model on each platform (Mac M4 Pro via mlx-lm;
   4xL4 vLLM via one 2-minute microbenchmark inside a kernel the score agent runs anyway), and the
   empirical attempt-time distribution; compute resolved-at-T for sequential retries, batched
   width and mixed schedules (H3).
4. End-to-end anchor. One configuration (e4b-k: a LoopAgent of k = 4 attempts + S1 selector, the
   design already recorded in the project notes) run once in the official harness on the scorer's stack on
   the 14 calibration tasks, to check that offline best@k predicts the real agent within noise.

### Experimental protocol

- Tasks: Mac-scorable public tasks (reference patch verified in the Mac subprocess sandbox; the
  Kaggle subprocess sandbox scores 75/129). Report by repository and by issue year (2026 issues
  postdate Gemma 4's release and limit memorisation).
- Models: E4B (main), E2B (smaller), 12B if time allows (second point on the size axis); 31B only
  through public numbers and the single scorer anchor, if quota allows.
- Baselines: the single-attempt agent (pass@1); sequential retry with the same total time; the
  oracle (pass@k) as the ceiling.
- Metrics: pass@1, pass@k, best@k per selector, selection efficiency, resolved-at-T, distinct
  non-empty patches per task (diversity), per-task success frequency c/r (noise model for #2).
- Statistics: paired comparisons on the same tasks (exact sign test on discordant tasks), task
  bootstrap intervals, all runs logged with seeds.
- Ablations: temperature 0.2 vs 1.0 (diversity vs precision); k = 1-8; selector S0-S3;
  sequential vs batched width; model size.
- Budget: Mac E4B attempt about 1-2 min (being measured), so 50 tasks x 8 attempts is about
  7-13 Mac-hours, i.e. two nights; selectors are CPU-only. GPU: one anchor run (about 1 h of 4xL4,
  2-3 quota hours) plus the microbenchmark.

### Expected result, and what a negative one would show

Expected: coverage grows like the literature's log-k curve but from a low base (2/12 at
pass@1), selection keeps a third to a half of the gain at k = 4, and batched width at b = 2-4
dominates sequential retries at matched wall-clock on the Mac. If coverage does not grow, the
paper becomes a clean negative result: a 4B agent's errors are systematic, so idle compute
cannot be converted into solved tasks without a better model or a better specification, which
bounds what scaffolds can do for small local agents (and redirects effort to training, G8). If
coverage grows but selection fails, the paper quantifies the verifier bottleneck at the k a
laptop can afford, the regime every large-k selection paper skips.

### Abandon criterion

Stop and switch to #3 if, on the first 12-14 tasks with r >= 4, pass@4 - pass@1 < 2 tasks
(decided by 2026-10-25, before the lock), or if the Mac harness cannot score tasks reliably by
2026-10-24 evening.

### Paper outline (3,000 words)

1. Introduction: local agents run one user at a time; decode is bandwidth-bound; small agents
   stop early; idle wall-clock is the cheapest compute there is. Contributions.
2. Setting: the competition harness, the models, the budget; wall-clock as the unit.
3. The cost of width on single-user hardware: l(b) curves (Mac, L4); the n(b) rule.
4. Coverage: pass@k curves, diversity, systematic vs random failures (per-task c/r histogram).
5. Selection at tiny k: S0-S3, efficiency, failure analysis.
6. Matched wall-clock: resolved-at-T for sequential vs batched width; scorer anchor.
7. Related work (TTS for SWE, verifiers, budget awareness, small models).
8. Limitations (public repos, one model family, offline selection), reproducibility statement.

### Collision risks

Scaling TTC for Agentic Coding (2604.16529, frontier model, tokens), Kozuchi (2608.15579, k = 8,
27B, no latency), Risa (2608.22191, MoE routing), FailFast-RestartSmart (2608.03222, restarts),
On the Clock (2610.10833, time budgets, not SWE). None prices width in wall-clock on
single-user hardware or studies k <= 4 for a 4B model. Venue: no announced entry.

## 2. Selection on noise: the winner's curse on agent leaderboards

Working title: *Best of Five Is Not Better: Resubmission Noise and the Winner's Curse on an Agent
Leaderboard of 3,476 Teams.*

- **Hypothesis.** Most of the spread at the top of the public leaderboard is selection on run
  noise: a model with a common latent rate per recipe family plus the measured per-task flip
  noise reproduces the observed rise of best score with submission count (M4), and predicts a
  regression toward the plateau on the private split. Falsifiable twice: the fit on the public
  table, then the private leaderboard after 2026-12-02 (pre-registered with a hash before
  2026-11-12).
- **Method.** Hierarchical model: team latent rate p_t (mixture over recipe families), per-task
  success frequencies q_i measured on our own repeated runs (from #1), best-of-n_t observation
  of k/58 truncated scores. Fit by likelihood on (best score, submission count). Predict each
  team's expected private rank change. Compare with resubmission data published on the forum
  (identical bundles: 13, 11, 9, 7, 7 tasks).
- **Protocol.** CPU only; leaderboard snapshots over time (Kaggle CLI); simulation checks of
  identifiability; sensitivity to the flip model.
- **Expected.** A shrinkage correction that ranks teams better than raw best score; a rule of
  thumb for how many resubmissions inflate a score by one task at n = 58.
- **Negative result.** If submission count explains nothing once skill is modelled, best-of-n
  inflation is negligible at this noise level, which is itself useful for organisers.
- **Abandon.** If the model is not identifiable from (best score, count) alone in simulation.
- **Collision.** Randomness in Agentic Evals (2602.07150), What Does a Harness Buy? (2610.04433),
  pair-count intervals (2609.33012), DeltaSelect (2609.19607): noise is measured, best-of-n
  leaderboard selection is not. Relevance to SE is indirect; works best as a section of #1.

## 3. What the tests know that the issue does not

Working title: *Unguessable Interfaces: How Often Hidden Tests Require Names the Issue Never
States.*

- **Hypothesis.** In freshly mined issue-resolution sets (not curated like SWE-bench Verified),
  10-20% of tasks have tests that use identifiers introduced by the reference fix and absent
  from the issue (M5: 21/129 here), and these tasks are near-unsolvable for every system, so
  they cap resolution rates independently of agent skill.
- **Method.** Static analysis of (issue, gold patch, test patch) triples on public benchmarks
  with per-instance results of many systems (SWE-bench Verified/Lite experiment logs, SWE-rebench,
  SWE-Gym), and on the 129 public tasks here; hand audit of a sample; correlation of the flag with
  per-instance resolution across systems.
- **Collision.** Between Spoilers and Guesswork (2610.22760) already extracts test-required
  names to build minimal hints; Ambig-SWE (2502.13069) studies ambiguity with interaction. Our
  margin would be the cross-system measurement and the uncurated-pipeline estimate. Thin but
  safe; CPU-only; a resource (labels + script) is possible from public data only.

## 4. The marginal information of a calls-only code graph

Done as M3 (gaps.md G6). Not recommended as a paper: at least six announced entries in this
venue work on the same graphs, one already reports the async omission and the near
4-dimensional embeddings (codegraph-loc, forum 746035). Keep as one paragraph of evidence that
the provided graph tools cannot help localization, which is why #1 spends compute on width and
not on graph tools.

## 5. Harness-fit LoRA from the 31B into E4B

Not recommended for the paper: GPU-bound (trajectory generation with the 31B, QLoRA training,
repeated evaluation) against 6 GPU-hours a week, and the venue already has a harness-format
trajectory dataset and distillation kit (forum 748627). If #1 shows that width cannot help
(systematic errors), this becomes the score agent's next lever, not a paper.

## Calendar for direction 1 (to 2026-11-12)

The agents run experiments overnight and on weekends; the author reviews and writes in short slots. Dates are UTC.

| Date | Milestone | Who | Decision gate |
|---|---|---|---|
| Thu 22/10 | Literature, gaps, proposals; latency curves M1 on the Mac; Mac harness spike started | scout | |
| Fri 23/10 | Mac harness scores the calibration tasks (gold check); first E4B attempts, r = 4 | scout agent | Mac harness works? |
| Sat 24/10 | r = 4 on 12-14 tasks; offline S0/S1; Kaggle quota resets 00:00 | scout agent | |
| Sun 25/10 | **Go/no-go**: pass@4 - pass@1 >= 2 tasks; else switch to #3 | Matis | go / switch |
| **Mon 26/10** | **Topic locked**; pre-register hypotheses H1-H3, selectors and analysis script (hash in the repo) | Matis | locked |
| 26/10-01/11 | Full Mac runs: E4B r = 8 on all Mac-scorable tasks (two nights), E2B r = 8 (one night); S2/S3 selectors; latency curves for 12B | agents | |
| by 01/11 | Scorer anchor: e4b-k (LoopAgent k = 4 + S1) on the 14 calibration tasks on 4xL4, plus the 2-minute l(b) microbenchmark | score agent | offline best@k vs real agent |
| 02/11-05/11 | Analysis frozen; figures (pass@k, selection efficiency, resolved-at-T); first full draft | scout + Matis | |
| 06/11-09/11 | Devil's-advocate review, ablation gaps filled (temperature, sequential vs batched); public reproduction notebook (no competition data) | agents + Matis | |
| 10/11-11/11 | Final edit to 3,000 words; optional arXiv PDF; writeup created on Kaggle as a draft | Matis | |
| **Thu 12/11** | **Submit before 23:59 UTC (target 12:00)** | Matis | |

Slack: two days (06-09/11 can absorb a late anchor run). If the scorer anchor cannot run
(quota or Modal not approved), the paper rests on the Mac results plus the l(b) curve from the
L4 microbenchmark alone, which is still verifiable.

Note on publicity: the writeup becomes public on Kaggle under Matis's name after the deadline
(an attached private notebook is made public too).
