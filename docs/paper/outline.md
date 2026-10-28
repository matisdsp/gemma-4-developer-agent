# Paper outline (2026-10-28)

Deadline 2026-11-12 23:59 UTC (target 12:00), 3,000 words, five criteria at equal weight:
novelty, generality, relevance, verifiability, clarity. Evidence: `gaps.md` (M1-M12),
`preregistration.md`, `literature.md`. Numbers tagged **[new]** come from the 2026-10-28
brainstorm's CPU analyses (scratch scripts, not frozen yet): each must be frozen as a script under
`analysis/allocation/` and logged in `gaps.md` as M13 before it enters the draft.

## 1. Brainstorm: what the paper is about

### What the evidence supports (75 tasks, three replicate cells)

1. **Failures are task-correlated.** Intra-task correlation 0.46-0.75 across A0, A1 and
   A1-2048 (M7c, M12). Four attempts buy 27-46% of what independent sampling predicts (pool A1
   8.00 vs 13.02 at k = 4; held-out 11.00 vs 21.17).
2. **Width still pays, pre-registered.** pass@4 - pass@1 = +3.75 [1.75, 6.00] of 35 (H1', M12);
   replicated at thinking 2048 (+3.50 [1.50, 6.00]) and on the pool (+4.25, M7c).
3. **Selection from the agent's own checks keeps most of it, but which rule wins is unstable.**
   Held-out: S1any (primary) +1.75 [-0.75, 4.25] failed, S1 +2.75 [0.75, 5.00]. Thinking-2048
   replicate: S1any +3.50 [1.50, 6.00], S1 +1.50 [-0.25, 3.50] (rerun 2026-10-28 with the
   frozen `selectors.py`). Pooled over 75 tasks both give about +5.00 **[new]**. Defensible claim:
   the class "filter on own pytest/repro, then smallest patch", not one rule.
4. **Width is nearly free only when batched.** One L4: agent time at 4 concurrent attempts 1.33x
   [0.99, 1.73] of one, 1.09x per tool call (H3', M12). Matched-time simulation **[new]**:
   batched k = 4 reaches 10.00 of 35 at a mean straggler time of ~316 s, while 4 attempts run in
   sequence within the 420 s task cap reach about 7.0-7.3 (measured speed) or 8.2-8.6 (crudely
   rescaled to solo speed).
5. **Depth and thinking are small and confounded.** A1 - A0 +1.00 [-0.25, 2.25], p = 0.40
   (M7c); 4096 - 2048 thinking +0.75 [-0.25, 1.75] (M12 addendum): the thinking share is bounded
   at roughly the size of the whole effect, not separated.
6. **Boundary: bigger models are time-bound here.** 12B: 36/36 attempts at the 7-min cap on one
   L4 (M8). 31B: verification prompt loses 2 tasks, wins 0 (M10, L40S, one rep, not
   pre-registered). The 31B's edit calls break Gemma's string delimiter (M9).

### Framings considered

| Framing | For | Against | Verdict |
|---|---|---|---|
| A. Idle-bound vs time-bound agents (the 2026-10-24 thesis) | general on paper | time-bound leg rests on weak runs (M8, M10); A1 is not idle under load (234-256 s mean, ~22% at the cap **[new]**); "66 s" is A0 on Kaggle 4xL4 (M2) | discussion paragraph only |
| **B. Width is cheap only when batched** | unclaimed in an agentic setting (G1, SPLIT treats latency as additive); one falsifiable claim; one figure carries it | batched width cannot run inside the official harness | **main claim** |
| **C. What pass@k hides under task correlation** | very verifiable, general, explains why width is weaker than the textbook | qualitatively known (2605.08563, SPLIT) | **method spine** |
| D. A recipe for local agents | relevant | reads as a Kaggle writeup, low novelty; the shipped A1 scored public 0.05 | no |
| E. Verification first, then width (the old "depth then width") | intuitive | depth +1.0, p = 0.40, confounded; repro ran in 37/160 and 40/140 attempts; signal is mostly pytest | dropped |

**Recommendation: B as the claim, C as the method, depth/thinking/size as bounded secondary
results.** State the result through two measurable quantities a reader can take to their own
model and GPU: the intra-task correlation and the batching cost ratio.

### Candidate titles

1. *Four Attempts for the Price of 1.3: A Pre-registered Study of Best-of-k for a Small Local Coding Agent*
2. *Width Is Cheap Only When Batched: Best-of-4 for a 4B Coding Agent on One GPU*
3. *Correlated Failures, Cheap Parallelism: How a Small Local Coding Agent Should Spend Its Deadline*
4. *Same Deadline, Four Attempts: Batched Sampling and Own-Test Selection for Small Coding Agents*
5. *What Best-of-k Buys a Small Coding Agent When Its Failures Are Correlated*

### Novelty statements (positioning)

- For a single-user ~4B coding agent, we measure best-of-k at matched wall-clock: one L4 runs
  four attempts in 1.33x the time of one, so batched width fits one task deadline, while the same
  attempts run in sequence do not.
- Outcomes are strongly task-correlated (0.46-0.75), so the homogeneous pass@k overstates
  coverage about 1.6-1.9x at k = 4; allocation rules must use measured heterogeneity.
- A pre-registered test confirms the width gain; the pre-registered primary selector failed, and
  the replicate shows why: the ranking between own-check rules is not stable at k <= 4.

## 2. Section plan (3,000 words)

| § | Words | Claim | Numbers (source) | Exhibit |
|---|---|---|---|---|
| Abstract | 150 | story in five sentences, failed primary selector named | H1' +3.75; S1any failed; pooled own-check +5.00 **[new]**; 1.33x | |
| 1 Introduction | 350 | local agents are judged in seconds, not tokens; on one GPU the price of k is set by batching; small agents' failures are correlated, so k buys less than the textbook says | M1 (16.7-18.2 ms/step at 1-8 concurrent on L4), M2 | |
| 2 Setting and protocol | 400 | official harness, subprocess sandbox, Modal 1xL4 pinned to the Kaggle image; pool 40 + held-out 35 fixed before any run; pre-registration with sha256; statistics | gold 40/40 and 35/35; 160+160+140+140 attempts; concurrency 8; a224c74, a4aec30 | T1 |
| 3 Failures are correlated | 400 | width pays, at 27-46% of the independent prediction; a handful of mixed tasks carry it | M7c, M12, addendum; c/4 histograms | F1 |
| 4 Selection from the agent's own checks | 550 | an own-check filter + smallest patch keeps ~60% of the gain; the exact rule is not stable; flags are weak (precision 0.17-0.44) and the gain comes from discarding failing attempts | M11, M12, 2048 rerun, pooled 75 **[new]** | T2, opt. F3 |
| 5 The cost in wall-clock | 450 | batching makes k = 4 fit one deadline; sequential width inside 420 s buys little; when the harness allows only sequential attempts, the per-task cap decides | H3' 1.33 / 1.09 / 1.27; matched-time simulation **[new]** | F2 (key figure) |
| 6 Depth, thinking and size | 300 | bounded, exploratory: verification prompt about +1 task and confounded with thinking; 12B and 31B time-bound at this budget | M7c, addendum, M8, M10, one sentence on M9 | row in T1 |
| 7 Threats to validity | 200 | contamination, scorer stack gap, one model family, temperature 0.2, offline subset simulation | see §4 below | |
| 8 Related work | 200 | SPLIT, Large Language Monkeys, Latency-aware TTC, Risa I.1, Kozuchi, CodeMonkeys, Context Contamination, On the Clock | `literature.md` | |

Reproducibility statement (inside §2 or a footer): scripts, run files and hashes; public tasks
are not redistributed (rule 2.4.b), only aggregates; per-attempt logs re-creatable from the
public upstream repositories.

## 3. Exhibits (max 5)

- **T1, runs.** run, arm, tasks, reps, concurrency, attempts, resolved, mean agent s, share at
  cap, share empty. Rows: A0 and A1 pool, A1 held-out, A1-2048 held-out, t-c1, t-c4, 12B, 31B.
  New script over `results/modal/*/results/*/results.jsonl`.
- **F1, pass@k under correlation.** x = k (1-4), y = share of tasks solved; solid observed,
  dashed homogeneous, one line per cell; inset: histogram of c/4. `passk.py summary`.
- **T2, selectors.** rows random, non-empty, S1, S1any, S2, oracle; columns k = 2/3/4 for pool
  A1, held-out A1, held-out A1-2048, and pooled-75 gain at k = 4 with interval. `selectors.py`.
- **F2, matched wall-clock (key figure).** x = mean per-task wall-clock (s), y = expected tasks
  solved; batched k = 1-4 (time = slowest of k), sequential policies at T = 420/840/1260 s with
  and without stop-at-first-clean-pytest; vertical line at the 420 s cap. New `wallclock.py`.
- **F3 (optional), flag quality.** precision vs recall of non-empty, pytest ok, repro pass, OR,
  AND across three cells, base-rate lines.

No per-task tables with instance ids in the paper (data rule): histograms and aggregates only.

## 4. Reviewer objections and answers

| # | Objection | Answer / defusing analysis |
|---|---|---|
| 1 | n = 35, ~7 mixed tasks carry the effect | pool 75 tasks (+8.00 [4.75, 11.75] pass@4 gain **[new]**); leave-one-task-out influence; two-level bootstrap |
| 2 | primary selector failed | say it first; show the flip on the 2048 replicate; claim the rule class, not S1 |
| 3 | one model | express results via correlation and batching ratio; closed-form best@k from those two, checked on the 4 cells |
| 4 | held-out easier than the pool (20.7% vs 9.4% pass@1) | both fixed by seeded draws before any run; gold patches half the size **[new]**; report gains in tasks (+3.75 vs +4.25) |
| 5 | A1 thinking confound | no headline claim depends on A1 vs A0; disclose the bound; S1@4 gap 4096 vs 2048 +2.00 [-1, 5] **[new]** |
| 6 | Modal 1xL4 TP1 vs the scorer's 4xL4 TP4 | calibration solved set identical across three stacks (M6); batched width impossible in the official harness: say it, give the sequential answer |
| 7 | contamination of public tasks | date split against Gemma 4's cutoff (n small, disclose); claims are relative (gain, share kept), not absolute rates |
| 8 | matched time is an offline simulation | attempts ran at concurrency 8, heavier than batched-4, so conservative; straggler 1.35x agrees with H3' 1.33x |
| 9 | H1' trivial (pass@4 >= pass@1) | the informative number is the shortfall vs the homogeneous prediction; add the correlation interval promised in the pre-registration |
| 10 | temperature 0.2, 12B/31B claims | scope width to the submission temperature; 12B/31B as a boundary condition, not findings |
| 11 | "verify before submit" is known (ECLoop, DeskCheck, SWE-Doctor) | not claimed; ours is a bounded small-model measurement |
| 12 | own-test selection contradicts Kozuchi (own tests below a fixed rule at k = 8, 27B) | different regime: k <= 4, 4B, the gain is filtering out ~72% failing attempts, not ranking |
| 13 | trained 4B models reach 49-62% on Verified (2609.35741, 2610.24914) | scope: no training, inference-time allocation on fixed weights |

## 5. Honesty rules for the draft

- Do not write "S1, specified before M11" or "the selector that held": S1 was committed with
  the M11 results (355e1de); what is verifiable is "pre-registered as secondary".
- Do not call A1 "depth" alone: "verification prompt (+ thinking 4096)".
- "Idle-bound" only with its setting: 66 s is A0 on Kaggle 4xL4 at low load (M2).
- "About half of independent sampling" holds only for pool A1 (46%); A0 31%, held-out 27%.
- "Width pays twice as much on top of A1": paired difference +2.00 [-1.00, 5.00] **[new]**, not
  established.
- 1.33x: "point estimate within the 1.6 threshold, interval reaches 1.73".
- Percentages of the random-to-oracle gap second, after tasks and intervals (denominators are
  2-4 tasks).
- "Matched wall-clock" means the per-attempt cap plus the offline simulation; A2 (informed
  retry) and temperature-1.0 width were never run at 40+ tasks: not in title or abstract.
- Pool results are exploratory (selectors were developed on the 14 calibration tasks inside it).
- E4B prize relevance: the shipped A1 scored public 0.05; batched width cannot run in the
  official harness. Say both.
- Related work: "not treated as an allocation problem", not "undocumented" (Bud 2610.25516,
  ACM 2607.23809 report early submission).

## 6. CPU work before the draft (ranked by value over effort)

| # | Task | Effort | Feeds |
|---|---|---|---|
| 1 | freeze `analysis/allocation/wallclock.py` (matched-time simulation, scratch `wall.py`) | 1 h | F2, §5 |
| 2 | selector table on three cells + pooled 75 (scratch `extra.py`) | 1 h | T2, §4 |
| 3 | bootstrap interval for the intra-task correlation (pre-registration deviation) | 15 min | §3 |
| 4 | per-repo breakdown and difficulty proxies (gold patch size) | 30 min | §7, objection 4 |
| 5 | contamination date split vs Gemma 4 cutoff | 30 min | §7 |
| 6 | two-level bootstrap (tasks, then attempts) of the whole pipeline | 2 h | objection 1 |
| 7 | failure mechanism on never-solved tasks: diff diversity, right-file rate, empty and cap shares | 3 h | §3 mechanism |
| 8 | closed-form best@k from (correlation, flag precision/recall), checked on 4 cells | 2 h | generality |
| 9 | T1 runs table script | 30 min | T1 |

All results logged as M13 in `gaps.md`, then the figures.

## 7. Calendar

| Date | Milestone |
|---|---|
| 28-29/10 | Matis picks framing and title; CPU tasks 1-3 and 9 |
| 30/10-01/11 | CPU tasks 4-8; M13 in `gaps.md`; figures F1, F2, T1, T2 |
| 02/11-05/11 | first full draft (agents draft, the author rewrites in short slots) |
| 06/11-09/11 | devil's-advocate review of the draft; word count; reproduction package (public tasks only) |
| 10/11-11/11 | final edit to 3,000 words; Kaggle writeup created as a draft |
| 12/11 | submit (target 12:00 UTC) |

## 8. Open decisions for Matis

1. Framing B + C (recommended) vs A.
2. Title.
3. Whether 12B/31B appear (recommended: one boundary paragraph in §6 plus a T1 row).
4. Optional arXiv PDF in addition to the Kaggle writeup.
