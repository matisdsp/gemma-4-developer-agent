# Paper-track proposals, ranked

Deadline 2026-11-12 23:59 UTC, 3,000 words, five criteria at equal weight (novelty, generality,
relevance, verifiability, clarity). Topic to be locked by **2026-10-26**. Evidence for every claim
below is in `gaps.md` (G1-G10, measurements M1-M5) and `literature.md`.

## Constraints that drive the ranking

- **Compute.** Kaggle GPU quota is 6 h a week on this account (Kaggle API, 2026-10-22), not 30 h;
  a 4xL4 hour costs at least 2 quota hours. One 31B pass over 30 tasks takes 3-3.5 h of wall time,
  more than a week's quota. A small Modal budget (E4B/E2B only) may open, at the coordinator's
  discretion. The Mac (M4 Pro, 24 GB) runs E2B and E4B at 4 bits through mlx-lm, at 111 and 67
  decode tokens per second respectively (M1), and 12B at 4 bits fits (mlx-community/gemma-4-12B-it-4bit).
  **Update 2026-10-22 late:** a Modal budget of 10 $ was approved for E4B/E2B (one L4, TP1, official
  harness with the subprocess sandbox, image pinned to the Kaggle notebook versions; gold check
  40/40 on a 40-task pool). One L4 serving one agent is itself the single-user setting the paper
  is about, so Modal can carry most of the attempt volume (E4B attempt about 66 s on L4) while the
  Mac gives the laptop point (E4B attempts take 2-11 min there in the first pilot runs). So:
  **experiments on Modal L4 and the Mac, CPU for selection and analysis, at most one 4xL4 anchor.**
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
| 1 | Spending a small agent's idle wall-clock: depth, retry, width or size, at matched time | G1, G2, G3 | medium-high | high | high | high (Mac-reproducible) | fair: Mac pipeline to build, 1 GPU anchor | direct (E4B bonus) |
| 2 | Selection on noise: the winner's curse on agent leaderboards, with a pre-registered private-leaderboard prediction | G4 | high | medium-high | medium | very high (CPU) | very good | indirect (final-pick strategy) |
| 3 | What the tests know that the issue does not: measuring interface under-determination across SWE benchmarks | G5 | medium-low (2610.22760) | high | high | high (CPU) | good | small (prompt contract) |
| 4 | The marginal information of a calls-only code graph over lexical search | G6 | low in this venue | medium | medium | high (done, CPU) | done | none (tools already removed) |
| 5 | Harness-fit LoRA: distilling the 31B's harness behaviour into E4B | G8 | low-medium | medium | high | medium | poor (GPU) | direct but costly |

Recommendation: **#1 (revised to the four-arm allocation study after review) as the paper.** #2
at most one paragraph: our E4B noise is not the leaderboard's 31B noise, and the private
leaderboard resolves only after the paper deadline. #3 is the fallback if #1's pipeline gate
fails on 2026-10-25. #4 becomes one paragraph of related evidence. #5 is not recommended for the
paper.

## 1. Spending a small agent's idle wall-clock: depth, retry, width or size?

Working title: *Idle Seconds: How a Small Local Coding Agent Should Spend a Fixed Wall-Clock
Budget.* (Revised after the devil's-advocate review of 2026-10-22: the first version tested
width alone, whose coverage gain is predictable from Large Language Monkeys 2407.21787 and whose
near-free batching was already noted in a SWE paper, Risa 2608.22191 Appendix I.1. The
contribution is now the allocation question at matched wall-clock, which stays informative
whichever arm wins.)

### Question

A small model in the official harness finishes a task in about 66 s of a 420 s budget (M2). On
one machine serving one agent, what converts the remaining time into solved tasks: thinking and
checking more within one attempt (depth), retrying with knowledge of the failed attempt
(informed retry), independent attempts with a cheap selector (width, sequential or batched), or
a single attempt of a larger model that uses the whole budget (size)? Same tasks, same harness,
same wall-clock.

### Arms (all at the same per-task wall-clock T)

- **A0 baseline**: E4B as in `variants/e4b` (its own temperature, 0.2), one attempt. This is the
  pass@1 reference, not a temperature-1.0 sample.
- **A1 depth**: one attempt with a mandatory reproduce-then-verify step before `submit_patch`
  (the score agent's `variants/e4b-v2`: a /tmp/repro.py that must fail before and pass after the
  edit, the nearest existing test file run before submitting, a 36-call plan, thinking 4096). Motivation: in the calibration run, 4 of 10 E4B
  failures ran no test or snippet at all and both successes did (trace reading).
- **A2 informed retry**: sequential attempts; each new attempt starts from a clean tree and sees
  the previous diff and its test output (cf. FailFast-RestartSmart 2608.03222, +5.2 points with
  the overlay vs +0.2 for a cold restart; SWE-Residual 2610.25899 warns of the opposite effect).
- **A3 width**: k independent attempts (temperature 1.0), sequential (fits ADK today as a
  LoopAgent) or batched (Mac only: concurrent sessions, each with its own sandbox), then a cheap
  selector.
- **A4 size**: one attempt of Gemma 4 12B with the same T (the next size the competition allows;
  it fits the Mac at 4 bits).

### Hypotheses (falsifiable, pre-registered with a hash before full runs)

- **H1 (heterogeneity, the precondition for width and retry).** E4B's per-task success is
  heterogeneous: with r = 8 attempts, the share of tasks with 0 < c < 8 is at least 15%. We
  report the fitted beta-binomial intra-task correlation and how far observed pass@k falls below
  the homogeneous prediction 1 - (1 - p)^k. Null: errors are systematic
  (Confident-and-wrong 2603.25764; Context-Contamination 2605.08563 shows the i.i.d. model
  overestimates pass@3 by 17.4 points), so width and retry cannot pay. Caveat built in: at r = 8 a
  task with true p = 0.1 shows c = 0 in 43% of draws, so "rare" and "systematic" are separated by
  the fitted model, not by counting.
- **H2 (selection at tiny k).** Selector S1 (existing tests nearest the patched module + import
  check, then smallest diff) gives best@4 - pass@1 > 0 with a 90% task-bootstrap interval above
  zero. Reported in tasks, with its interval; selection efficiency only as a secondary number.
- **H3 (allocation).** At matched T on the Mac, the ranking of A1-A4 is not the ranking predicted
  by token cost: batched A3 at b = 2-4 is at least as good as sequential A3 at equal T, and the
  time model t(b) predicts measured end-to-end attempt times within 20% (prefill, tool and test
  time and stragglers included). Null: measured times break the model (e.g. the server does not
  batch, or tool time dominates), which is itself the practical answer for local agents.

### Method and protocol

- **Sample once, analyse offline.** Per task: r = 8 attempts for A3 (temperature 1.0), r = 4 for
  A0, A1, A2 and A4. Store every patch with its timings and verification outcome. Unbiased pass@k
  for k <= r from c successes (Chen et al. 2021). best@k for each selector is averaged over all
  k-subsets of the r candidates; intervals by bootstrap over tasks (never over subsets).
- **Selectors** S0 first candidate, S1 existing tests + import check, S2 agreement between
  normalised diffs, S3 model-as-judge (one-line negative control). Selector code frozen and
  hashed before scoring; developed only on the 14 calibration tasks.
- **Tasks.** Mac-scorable public tasks. Raise n toward 100+: on the Mac the network is available
  to install missing test dependencies (`inline_snapshot`) and run a local `httpbin`, which the
  Kaggle sandbox could not (75/129 scorable there). Report by repository and by issue year.
- **Timing.** l(b) per model from the decode microbenchmark (M1) and, more importantly, t(b)
  measured end to end on real concurrent attempts through the local server. One 4xL4
  microbenchmark inside a kernel the score agent runs anyway gives the scorer-side l(b).
- **Scorer anchor.** e4b-k (sequential A3, k = 4, S1) once on the 14 calibration tasks on 4xL4,
  only if quota or Modal allows. It validates sequential width on the real stack; batched width
  cannot run inside the official harness (one `/workspace` per task; ParallelAgent with tools is
  broken in ADK 1.36), so it is a Mac-side result, and the paper says so.
- **Statistics.** Paired permutation test on per-task expected outcomes (continuous, more power
  than binary sign tests); all runs logged with seeds; no selector or prompt tuning on the
  evaluation tasks.
- **Compute.** First Mac pilot: E4B attempts take 2-11 min each on the Mac (vs about 66 s on
  L4), so the Mac cannot carry r = 8 on 100 tasks; it carries a laptop subset (14-30 tasks, r = 4)
  and the end-to-end t(b) measurement. Volume goes to Modal L4 (10 $ at about 0.80 $/h is about
  12 L4-hours, i.e. several hundred E4B attempts with setup), arm A1 being the score agent's
  `variants/e4b-v2` so both tracks share one YAML. A4 (12B) is the most expensive arm and is run
  on the smallest task subset. GPU: at most one 4xL4 anchor plus the microbenchmark.

### Go/no-go gate (2026-10-24/25)

1. The Mac pipeline scores the 14 calibration tasks (gold patches pass, agent patches verified).
2. Measured end-to-end t(4)/t(1) <= 1.6 with four concurrent sessions through the local server
   (else batched width is dropped and only sequential A2/A3 remain).
3. At least 3 of 14 tasks have mixed outcomes at r = 4.

If (3) fails because E4B sits at the floor, the main model becomes 12B and E4B a secondary point.
If (1) fails, switch to proposal #3.

### Expected result, and what a negative one shows

Expected: heterogeneity on a minority of tasks; S1 keeps part of the coverage gain; batched
width near-free on the Mac; and a clear answer to "depth, retry, width or size" at one T. Any
ordering is a finding: if size wins, local users should run the biggest model that fits and
ignore test-time tricks; if width wins, a laptop agent should batch 2-4 attempts; if nothing
beats A0, the idle budget of small agents is not convertible without better models or
specifications. The weakest outcome (no heterogeneity and no arm beats A0) is still a rigorous
negative result with a mechanism (systematic errors), which the criteria value.

### Paper outline (3,000 words)

1. Introduction: local agents serve one user; small agents stop early; the question.
2. Setting: harness, models, wall-clock as the unit, tasks and their limits.
3. The cost of time on one machine: l(b) and measured t(b); the allocation model (short).
4. Heterogeneity: per-task c/r, intra-task correlation, pass@k.
5. Arms at matched wall-clock: A0-A4; selectors at k <= 4.
6. Scorer anchor and limitations (public repositories, one model family, offline selection).
7. Related work (about 250 words) and reproducibility statement.

### Collision risks

Large Language Monkeys (2407.21787, coverage vs samples); Latency and Token-Aware TTC
(2509.09864, latency-aware width vs depth, single-turn math, coding left as future work); Risa
(2608.22191, n = 16 step about 2x one step, server); Inference-Time Amplification of Weak
Reasoning Models (2605.14163, GPT-5.4 nano, 8 proposals 79.0% coverage, critic selection 76.4%
vs 67.0% single, API tokens); Kozuchi (2608.15579, k = 8, 27B); SquidAgent (2610.08647,
wall-clock criterion for parallelising agent layers); FailFast-RestartSmart (2608.03222);
SPLIT (2610.23255, 2026-10-16: allocation among sampling, model mixing and verification under
imperfect verifiers, latency as one cost, no batching, no depth or retry; we reuse its selection
model rather than compete with it). None
compares depth, retry, width and size at matched wall-clock on single-user hardware for a small
model. Venue: no announced entry.

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
| Sun 25/10 | **Go/no-go gate** (three conditions in section 1): pipeline scores the 14 tasks; t(4)/t(1) <= 1.6; >= 3 mixed tasks at r = 4. Else 12B as main model, or #3 if the pipeline fails | Matis | go / adapt / switch |
| **Mon 26/10** | **Topic locked**; pre-register H1-H3, arms, selectors and analysis script (hash in the repo); make more tasks Mac-scorable (inline_snapshot, local httpbin) | Matis + agents | locked |
| 26/10-01/11 | Full Mac runs: A3 (E4B, r = 8) and A0/A1/A2 (E4B, r = 4) on all Mac-scorable tasks, A4 (12B, r = 4); end-to-end t(b); selectors S0-S3 frozen | agents | |
| by 01/11 | Scorer anchor (if quota/Modal allows): e4b-k (sequential A3, k = 4 + S1) on the 14 calibration tasks on 4xL4, plus the 2-minute l(b) microbenchmark | score agent | offline best@k vs real agent |
| 02/11-05/11 | Analysis frozen; figures (per-task heterogeneity, arms at matched T, selectors at k <= 4, t(b)); first full draft | scout + Matis | |
| 06/11-09/11 | Devil's-advocate review, missing ablations filled (temperature, sequential vs batched); reproduction package on public tasks only | agents + Matis | |
| 10/11-11/11 | Final edit to 3,000 words; optional arXiv PDF; writeup created on Kaggle as a draft | Matis | |
| **Thu 12/11** | **Submit before 23:59 UTC (target 12:00)** | Matis | |

Slack: two days (06-09/11 can absorb a late anchor run). If the scorer anchor cannot run
(quota or Modal not approved), the paper rests on the Mac results plus the l(b) curve from the
L4 microbenchmark alone, which is still verifiable.

Note on publicity: the writeup becomes public on Kaggle under Matis's name after the deadline
(an attached private notebook is made public too).
