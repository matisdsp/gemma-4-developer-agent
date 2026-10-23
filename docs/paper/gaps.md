# Open gaps in the SWE-agent literature, as of 2026-10-22

Each gap states what is open, the evidence that it is open (papers in `literature.md`, cited by
arXiv id), the check that it has not been closed in the last six months, what we measured
ourselves, and how crowded the paper-track venue already is. The gaps are ordered by how much
leverage they give a paper written in three weeks with almost no GPU (6 GPU-hours a week on
Kaggle, a Mac M4 Pro with 24 GB, no paid API).

Verification method: six reading passes (about 260 fiches), a systematic arXiv sweep of
2026-05-01 to 2026-10-22 (section 7 of `literature.md`), targeted web and arXiv searches on each
gap, and the paper-track forum (31 topics), whose announced entries are the most direct
collision risk because writeups stay hidden until the deadline.

Our own measurements quoted below (all reproducible; scripts and how to run them in `analysis/README.md`):

- **M1, decode latency vs batch size on a laptop** (Mac M4 Pro, mlx-lm 0.32.2, 4-bit, median of
  3, ms per decode step): E2B 9.0 / 9.0 / 11.6 / 20.3 / 32.8 and E4B 14.9 / 16.0 / 22.0 / 37.9 /
  61.3 at batch 1 / 2 / 4 / 8 / 16. A second concurrent sample costs 0-7% more wall-clock per
  step, a fourth 28-47%.
  On one L4 GPU (vLLM TP1, E4B, official image, Modal, 256-token completions, score agent's
  microbenchmark): 16.7 / 16.9 / 17.1 / 18.2 ms per step at 1 / 2 / 4 / 8 concurrent requests,
  i.e. eight concurrent samples cost 9% more per step than one (slowest request per level kept).
- **M2, E4B leaves most of its budget idle** (official harness on Kaggle 4xL4, vLLM as the scorer,
  12 calibration tasks, run by the score agent on 2026-10-22): 2/12 resolved; E4B calls
  `submit_patch` after a mean 8.2 tool calls and 66 s of agent time out of a 36-call / 420 s
  budget; failures are wrong fixes, not timeouts; no compaction (prompts stay near 5k tokens).
- **M3, provided code graph vs lexical search** (CPU, 129 public tasks, reference patches mapped
  to 511 gold functions/classes, 120 tasks evaluable): function Acc@10 grep 49/120, BM25 74/120,
  seeds + 2-hop call expansion 35/120, embedding neighbours 4/120. On the 71 tasks where grep's
  top 10 misses every gold unit, call-graph expansion recovers 3-5, embedding neighbours 0-1,
  BM25 29. All `async def` are missing from the graphs (44/44 async gold units); 50.8% of nodes
  are isolated; embedding cosine is nearly unrelated to lexical overlap (Spearman 0.067 over
  380,826 random pairs).
- **M4, the public leaderboard** (CSV of 2026-10-22, 3,476 teams, scores are k/58 truncated):
  mean best score rises monotonically with a team's submission count, from 5.1 tasks (1
  submission) to 10.4 tasks (16-40 submissions); share of teams at 13+ tasks rises from 0.2% to
  5.8%.
- **M5, tests that need names the issue never states** (heuristic on the 129 public tasks): in 28
  tasks the hidden test uses an identifier that the reference fix introduces; in 21 of them at
  least one such name is absent from the issue text, in 14 none is mentioned.

- **M6, E4B's failures are systematic, not stochastic** (Mac pilot, 2026-10-22/23: official
  harness, subprocess sandbox on macOS, E4B 4-bit served by mlx-lm, temperature 1.0, r = 4 on the
  14 calibration tasks, 56 attempts, mean 296 s per attempt): pass@1 = 1.25 expected tasks,
  pass@4 = 2 tasks. Only 2 tasks have mixed outcomes (rich_3454 2/4, fastapi_14786 3/4); the other
  12 are never solved. They are the same two tasks solved on Kaggle 4xL4 (temperature 0.2) and on
  Modal 1xL4, so the solved set is stable across three serving stacks and two temperatures.
  41% of attempts (23/56) end with an empty patch; non-empty patches are diverse (on most tasks
  every non-empty attempt differs) and 19/25 touch a file the reference fix touches: E4B usually
  finds the right file and writes a wrong fix. Caveats: 14 tasks; the Mac stack differs from
  the scorer (mlx-lm tool parsing, no thinking-budget control); temperature 1.0 may inflate empty
  patches. The pilot's concurrent sandboxes are the likely cause of the Mac memory saturation of
  2026-10-23 00:27; heavy runs belong on Modal.

- **M7, depth helps E4B a little, width still does not** (Modal 1xL4, run by the score agent,
  2026-10-22, interrupted by the Mac crash at 122/160 attempts: rep 0 complete for both arms, rep 1
  partial): A0 `variants/e4b` 4/62 resolved, 2 tasks ever solved; A1 `variants/e4b-v2` (forced
  reproduce-then-verify, thinking 4096) 8/60, 5 tasks ever solved. Paired on the 40 tasks: A1
  wins 3 tasks, loses 0, +2.5 expected tasks (90% task-bootstrap interval +0.5 to +5.0),
  permutation p = 0.25. Of the tasks with two repeats, 0/22 (A0) and 1/20 (A1) are mixed: the
  solved set is again almost deterministic.

- **M8, size buys coverage but not time** (Modal 1xL4 TP1, 2026-10-23, `variants/12b` =
  `variants/e4b` with the model swapped to Gemma 4 12B, temperature 0.2, concurrency 6; stopped at
  36/56 attempts, reps 0-1 complete on all 14 calibration tasks): 8/36 resolved, 4 distinct tasks
  solved at least once (rich_3454 3/3, fastapi_14786 3/3, rich_3882 1/2, rich_3067 1/2) against 2
  for E4B; 2 mixed tasks. But all 36 attempts hit the 7-minute cap and 28/36 end without a patch:
  12B decodes at 34.4 / 34.7 / 35.5 / 37.5 ms per step at 1 / 2 / 4 / 8 concurrent requests on
  one L4, about twice E4B's. On single-user hardware at this budget the larger model is
  time-bound, not capability-bound. Cost about 1.2 $ (estimate).

## G1. Test-time scaling has never been costed in wall-clock on single-user hardware

**What is open.** Every test-time-scaling result for SWE agents prices extra samples in tokens or
dollars, the datacenter view in which a second sample costs as much as the first. On a laptop or
a single-tenant GPU serving one agent, decoding is memory-bandwidth-bound: the weights are read
once per step whatever the batch, so a second or fourth concurrent sample costs little extra
time (M1). Under a wall-clock budget, which is how a developer experiences a local agent and how
this competition scores, the cost-optimal mix of width (parallel samples) and depth (more steps)
is therefore different from the one the literature reports. Nobody has measured it for coding
agents.

**Evidence.**
- Published SWE test-time scaling uses k >= 8 and counts tokens or dollars: Scaling TTC for
  Agentic Coding (2604.16529, N=16, Claude Opus), R2E-Gym (2504.07164, Best@26), SWE-Lego
  (2601.01426, TTS@16), SWE-Hero (2604.01496, K=16 to 32), Kozuchi (2608.15579, TTS@8 with a
  locally hosted Qwen3.5-27B, but no latency analysis), Risa (2608.22191, no wall-clock).
- Latency-aware compute allocation exists only for single-turn reasoning (Latency and Token-Aware
  Test-Time Compute, 2509.09864) and for tool latency (Timely Machine, 2601.16486). The one
  agentic data point on batched width is a single remark in Risa's serving setup (16 candidates
  for about 2x the time of one, server hardware).
- Wall-clock-capped issue resolution is otherwise unstudied in the 1-10 minute range: SWE-Effi
  (2509.09853) defines a time-budget effectiveness metric but does not vary width; DeepSWE
  (2607.07946) caps at 9,000 s, binding on 0.9% of rollouts; Claw-SWE-Bench (2606.12344) at
  3,600 s; On the Clock (2610.10833) studies time budgets for a 27B on MLE-Bench, not SWE.
- The physics is textbook in serving (decode is bandwidth-bound at small batch), so the novelty
  is not the latency curve but what it implies for agent design and how to evaluate it.

**Not closed in the last six months.** Targeted searches (wall-clock + agent + test-time;
latency + parallel + SWE; batch + best-of-n + consumer hardware) and the 2026-05 to 2026-10
sweep (1,217 relevant papers triaged) return no SWE-agent paper that allocates a wall-clock
budget across depth, retry, width and model size on single-user hardware. Closest items, read:
Risa (2608.22191, Appendix I.1: an n = 16 step costs about 2x one step on its vLLM server, a
side remark), Latency and Token-Aware TTC (2509.09864, single-turn math on one A100, coding left
as future work), SPLIT (2610.23255, 2026-10-16, allocates among sampling, model mixing and
verification under imperfect verifiers, with latency as one possible cost, no batching, no
depth or retry), SquidAgent (2610.08647, wall-clock criterion for parallelising agent layers),
Inference-Time Amplification of Weak Reasoning Models (2605.14163, GPT-5.4 nano, 8 proposals,
API tokens), Kozuchi (2608.15579), On the Clock (2610.10833).

**Venue.** No paper-track entry announces it.

**Risk.** A referee may call the latency curve obvious. The contribution must be the agent-level
consequence (resolved tasks at matched wall-clock) and a usable rule for choosing k from a
measured latency curve, not the curve itself.

## G2. Small models under-use their budget, and the literature only studies the opposite failure

**What is open.** Budget-awareness work assumes agents overrun: BATS (2511.17006) and BAGEN
(2606.00198) teach frontier agents to stop or ration; On the Clock (2610.10833) finds a 27B
ignores a prompt-only time budget and overruns; StopLoss (2610.25525) and FailFast-RestartSmart
(2608.03222) abort runs early. The reverse failure, a small model that submits a wrong patch
after a fraction of its budget and leaves the rest idle, is undocumented. M2 measures it for
Gemma 4 E4B: 66 s used out of 420 s, 8 of 36 calls. Confident-and-wrong (2603.25764) shows the
same symptom for larger models (submit rate 99-100% with resolve rate 18-44%) but does not
connect it to idle budget.

**Why it matters.** Idle budget is free compute. It can buy independent retries (width in
time), parallel samples (width in batch, G1), or verification. Which one pays for a 4B model is
open: FailFast-RestartSmart finds a cold restart worth +0.2 points and a restart with the old
diff as overlay +5.2 (Qwen3.6-27B, 2608.03222), while SWE-Residual (2610.25899) finds that
starting from a predecessor's failed work costs 20.6-53.5 points.

**First answer for E4B (M6).** Width cannot pay on the calibration tasks: 12 of 14 are never
solved in 4 attempts at temperature 1.0, on any of three stacks. What remains open for a 4B model
is whether depth (forced verification) or a larger model converts the idle budget.

**Not closed.** No paper in the sweep studies under-use of a time budget by small SWE agents;
the budget papers it lists (2607.19338 CodeRescue, 2609.38147 meta-reasoning under remaining
budget, 2610.25525 StopLoss, 2610.09944 AgentTime) address overrun, escalation or abort.

**Venue.** None announced.

## G3. Patch selection at tiny k with no trained verifier

**What is open.** Selection recovers only part of the pass@k gap even at k = 8-32 with strong
verifiers: about 15 points left at K=16 (SWE-Hero 2604.01496); 2.1 of 8.3 oracle points with a
frontier verifier queried 8 times per pair (LLM-as-a-Verifier 2607.05391); 34/500 regret at k=8
(Kozuchi 2608.15579), where selection by the agents' own tests (346/500) does worse than a fixed
ordering rule (362/500). Untrained small judges are near chance or harmful: SWE-PRM
(2509.02360, -20.4 points with a same-size PRM), SWE-Review (2607.06065, an untrained 8B
reviewer completes about 4% of reviews), SWE-Replay (2601.22129, LLM-as-judge step selection
worse than random). Reproduction tests are weak verifiers: 31-44% valid with GPT-4o-class models
(Otter, Issue2Test, AssertFlip), under 20% discriminative in R2E-Gym (2504.07164); SWE-Doctor
(2607.00990) finds them of limited or negative use in patch generation.

Nobody reports what a cheap execution-based selector (existing tests of the touched module,
import and smoke checks, agreement between candidates) delivers at k = 2-4 for a 4B model,
nor how much of the coverage gain it keeps.

**Not closed.** The 2026 selection papers in the sweep use k >= 8 or a trained or frontier
verifier: 2605.14163 (critic-comparator over 8 proposals, 67.0% to 76.4% for GPT-5.4 nano),
2610.03984 (trained self-verification, eight samples), 2610.10242 (TestGRAD, evolved test
suites over an ensemble), 2608.15579. SPLIT (2610.23255) gives a model of selection under
imperfect, correlated verifiers that we can reuse to analyse k <= 4.

## G4. Selection on noise: best-of-resubmissions on small agent leaderboards

**What is open.** Run-to-run variance of agents is now well measured: 0.7-1.7 points std over
10 runs of 500 tasks (Randomness in Agentic Evals, 2602.07150), 13% of tasks flip between reruns
on a 45-task subset (What Does a Harness Buy?, 2610.04433), run-to-run intervals understate
task-sampling uncertainty by 1.3-1.5x (DeepSWE, 2607.07946), 10.7% of passes are lucky
(AgentLens, 2605.12925). What happens when hundreds of teams each submit the same stochastic
agent several times and keep the best public score has not been quantified: the pair-count
paper (2609.33012) warns that leaderboard entries are not independent, and no paper sizes the
winner's curse for agent leaderboards.

**Our evidence.** M4: on this competition's public leaderboard the mean best score rises
monotonically with the number of submissions (5.1 to 10.4 tasks out of 58), and the plateau at
9-11 tasks holds 42% of teams. With identical bundles drawing 13, 11, 9, 7, 7 tasks (community
report), most of the top of the table is consistent with selection on run noise. The private
leaderboard (revealed after 2026-12-02) gives a rare out-of-sample check of any shrinkage model
fitted now, so a prediction can be pre-registered before the paper deadline.

**Not closed.** The sweep finds many 2026 noise papers, none on best-of-n resubmission:
SWE-bench's top 30 are not separable pairwise (2609.17394), the number of tasks needed varies
sharply by benchmark (2607.12338), run-to-run variation exceeds differences between agent and
model pairings (2609.33812), about 54% of outcome variance comes from repeated runs
(2610.01618). The best-of-N effect is documented for Chatbot Arena (The Leaderboard Illusion,
2504.20879) and for deterministic models on Kaggle holdouts (The Ladder, 1502.04585; Roelofs et
al., NeurIPS 2019), not for stochastic agents.

**Limits.** Only each team's best public score and submission count are public; per-submission
histories are not. Heterogeneous team skill confounds submission count, so the analysis needs a
model (e.g. latent per-team rate plus run noise) and the private leaderboard to validate it.
Relevance to "software engineering and agentic learning" is indirect: it is an evaluation paper.

## G5. Tests that require names the issue does not state

**What is open.** Hidden tests written with the reference fix often import or call identifiers
that the fix creates (a new exception class, a keyword argument, a helper). An agent that
implements the right behaviour under another name scores zero. The literature knows the
phenomenon: SWE-bench Verified's annotation removed under-specified tasks; SWE-Bench Pro and
others add ground-truth "interface" hints; Between Spoilers and Guesswork (2610.22760, 2026-10-16)
shows such hints over-specify and proposes declaration-only hints selected by def-use analysis;
Ambig-SWE (2502.13069) measures up to 74% gains when the agent may ask. What is not measured is
the share of tasks in un-curated, freshly mined sets (SWE-rebench-style pipelines, this
competition's private repositories) whose hidden tests are unguessable from the issue, and how
much of an agent's failure rate it explains.

**Our evidence.** M5: 21/129 public tasks (16%) have a test that uses at least one identifier
introduced by the fix and absent from the issue; 14 (11%) mention none of them. Heuristic, not
yet audited by hand.

**Collision.** 2610.22760 is close (it already extracts test-required names to build hints).
A paper here would have to be a measurement across several public benchmarks with per-instance
results of many systems, which is CPU-only and feasible, but its novelty margin is thin.

## G6. Does a code graph add information that lexical search does not already reach?

**What is open.** Papers disagree on whether graph tools help (LocAgent, CoSIL, GraphLocator,
LARGER for; RepoAtlas, SWE-Adept, ARISE, 2610.25826 against), and every comparison changes the
scaffold and the tool set at once. The literature never measures the fraction of gold locations
that are (a) named in the issue, (b) found by BM25 or grep, (c) reachable only through call
edges, on unseen repositories (C-gap 2: CodeScout 2603.17829, SemNav 2609.31176, LARGER
2605.16352, KGCompass).

**Our evidence.** M3 answers (a)-(c) for the competition's calls-only graphs: call expansion
recovers 3-5 of 71 grep misses at a median 15.6k tokens, BM25 recovers 29 at 3.7k; embeddings
recover 0-1. This explains the public finding that graph tools give no gain: in this schema the
graph carries almost no localization information beyond lexical search, and its embeddings
carry almost none at all.

**Venue: crowded.** At least six paper-track entries work on exactly these graphs: a public
model-free localization benchmark on the 129 tasks (forum 748395), codegraph-loc with rebuilt
typed graphs and an agent experiment (746035; it already reports the async omission and the
near-4-dimensional embeddings), a 152-PR graph resource (743255), a graph audit (743255), a
pre-registered anchor-distance study on E4B (750732). A seventh entry would be judged against
them. Use M3 as supporting evidence, not as a paper.

## G7. LLM-summary compaction at 14k inside a 32k window

**What is open.** Text-only summarisation at a fixed threshold with an untrained small
summariser, latency charged to a wall-clock budget, is not measured (E-gaps G1-G3; Bud
ContextCompact 2.0 2610.25516 is the closest and finds the gain turns negative under a 45-minute
cap because a summary takes a median 161 s).

**Why we rank it low.** The corner is crowded in 2026 (Bud 2610.25516, AutoCompact 2610.02163,
CompactionRL 2607.05378, Beyond Token Savings 2609.32961, Harness-Design 2609.20804, SWE-MeM
2606.28434, Reacquisition-Cost 2608.16370, plus the paper-track "Trap-25" context-reset entry),
and M2 shows the small model never reaches the compaction threshold (prompts stay near 5k
tokens). It matters for the 31B, which we cannot afford to run much.

## G8. Is a small model's fine-tuning gain capability or harness fit?

**What is open.** Polar (2605.24220): RL lifts Qwen3.5-4B from 3.8% to 26.4% under the Codex
harness but only from 34.6% to 35.2% under its native one; FrogNano (2609.07925): 8.3% vs 37.2%
across two harnesses before any training. Whether a LoRA on harness-format trajectories teaches
protocol or skill is open, and no LoRA-vs-full comparison exists for multi-turn SWE agents
(LoRA Without Regret was single-turn math).

**Why we rank it low here.** Needs GPU training and many evaluation runs (6 GPU-hours a week);
the venue already has a trajectory dataset and harness-format distillation kit (748627) and an
SFT-recipe entry (751413).

## G9. The public-to-private drop is measured once, and confounded

SWE-Bench Pro (2509.16941) is the only benchmark with a commercial-repo split: like-for-like
pairs drop by 20-48% relative (e.g. GPT-5 high 25.9 to 15.7), single runs, no intervals.
SchrodingerRepo (2609.27891) estimates the familiarity share at 6-14 points by renaming.
This competition is a natural experiment (about 37% locally on public tasks vs about 17% on the
hidden private set for the same recipe, community numbers), but per-task hidden results are not
observable, so we cannot fill this gap.

## G10. Training on tiny compute

No paper trains an SWE agent on anything close to 6 GPU-hours a week (cheapest found: about 150
A100-hours, 2607.17205). Out of reach for us; listed for completeness.

