# Literature map for the paper track

State of the art on software-engineering (SWE) agents as of 2026-10-22, written to choose a
topic for the Gemma 4 Developer Agent Paper Track (deadline 2026-11-12 23:59 UTC, 3,000 words,
judged 0-5 on novelty, generality, relevance, verifiability, clarity).

How this file was built: six parallel reading passes (scaffolds and test-time scaling; training;
code graphs and localization; benchmarks and evaluation; context and compute budgets; a
systematic arXiv sweep of 2026-05-01 to 2026-10-22), each fiche written from the paper itself
(abstract plus results and limitations sections). Numbers are the authors' own; settings differ
from the competition (context, step budget, model), so they show mechanisms, not levels.
Fiche format: reference, contribution, numbers, admitted limitations, relevance to our setting
(Gemma 4 31B or E4B, 32k context with summary compaction at 14,336 tokens, about 6 minutes and
about 30 tool calls per task, unseen private repositories).

Sections:

1. The venue itself: what other paper-track entrants have already announced
2. Agent scaffolds and test-time scaling
3. Training SWE agents and small open models
4. Code graphs, retrieval and localization
5. Benchmarks and evaluation methodology
6. Context management and compute budgets
7. Systematic sweep, 2026-05 to 2026-10

## 1. The venue: announced paper-track work (Kaggle forum, read 2026-10-22)

The paper-track forum (31 topics) shows what competing writeups will cover. Writeups unlock
publicly only after the deadline, so this is the only collision signal available before then.
Prizes: Overall Best Paper $15,000, Best New Resource $10,000, Best New Application $10,000;
at most two writeups per team; one writeup can win at most one prize; the same five criteria
are applied in the context of each prize (organizer, topic 743255). arXiv posting is allowed
(745872). Competition data cannot be redistributed (rule 2.4.b); regenerated graphs from
public upstream history are "believed acceptable" with citation (743255, not yet confirmed).

| Topic / author | What it covers | Collides with |
|---|---|---|
| 748395, alikalwar: "Model-free localization benchmark on the 129 public tasks" (public notebook) | Maps gold patches to call-graph nodes; Hit@5 on 117 tasks: TF-IDF 14.5%, provided embeddings 25.6%, RRF fusion 30.8%; gold node within 2 hops of a named symbol in 47.9%; 2-hop neighbourhood median 80 functions vs ~3,200 | Any "do the provided graphs help localization" study |
| 746035, danielmantiglia: codegraph-loc (GitHub, Apache-2.0) | Rebuilt graphs with async defs and typed edges; released graphs miss all async defs and module-level code (19.6% of gold nodes); embeddings strongly anisotropic, effectively ~4-dimensional, uncorrelated with code similarity; BM25+personalized PageRank best (Hit@5 0.336); graph-navigating agent +1.6 on held-out, CI crosses 0, "not confirmed" | Graph audit, graph-augmented localization, graph agents |
| 743255, Shiva Shankar: graph resource on 152 public PRs | Rebuilt graphs (calls, contains, imports, inherits, tests edges) + CodeRankEmbed vectors for fastapi/httpx/requests/rich | Graph resources |
| 743255, dval: audit of code graphs | Audit plus regenerated comparison graphs at pre-fix commits | Graph audit |
| 750732, Jason Wold: pre-registration (hash commitment, 16/10) | Whether graph distance from issue anchors to fix site predicts where an E4B agent fails in the official harness, and what the async omission costs | Graph distance, E4B failure analysis |
| 748627, damsolanke: gemma4-swe-kit + trajectory dataset | Local replica of the scorer's rendering, parsing and limits; scorer-time model for the 12 h budget; 3,586 SWE-rebench OpenHands trajectories converted to the harness tool format (1,427 curated); harness-format distillation tools | Trajectory datasets, SFT/distillation into Gemma |
| 751430, robinamirbahar: "Trap-25" + Counterfactual Context Reset | 25 synthetic trap tasks; loop detection (error persistence, diff similarity, action entropy) + pruning + negative-constraint ledger + phase-adaptive thinking; claims 16% to 96% | Loop breaking, context reset, thinking-budget scheduling |
| 747862: pre-registration, "Gemma 4 QAT paper" | QAT vs bf16 effects (plan frozen 09/10) | Quantization effects |
| 748973: CodeGuardian, graph-guided self-repairing agent | Pipeline description only | Graph-guided agents |
| 749803: issue-to-function localization labels | Localization paper in preparation | Localization |
| 751413: "non-fancy SFT recipe" | SFT recipe | SFT |

Reading: the graph-and-localization theme is the most crowded corner of this venue (at least
six entries, two with pre-registrations and released code), followed by trajectory
distillation. No announced entry covers parallel width under a wall-clock budget, evaluation
noise, or the issue-to-test interface gap.


## 5. Benchmarks and evaluation methodology


Setting of interest: Kaggle competition, ~120 hidden tasks from private repos, scored by full hidden test files; public LB over 58 tasks with ~1.5 task std between identical resubmissions; agents limited to ~6 min/task.

### 1. Private / held-out repos and public-to-private drop

#### SWE-Bench Pro: SWE-Bench Pro: Can AI Agents Solve Long-Horizon Software Engineering Tasks?
- **Ref**: Deng, Da et al. (Scale AI), arXiv 2509.16941 (v1 Sep 2025, v2 14 Nov 2025), https://arxiv.org/abs/2509.16941
- **Contribution**: 1,865 human-verified, human-augmented tasks from 41 repos, split into public (731 tasks, 11 copyleft repos), held-out (858 tasks, 12 repos, never released) and commercial (276 tasks, 18 proprietary startup repos under partnership agreements; only results are published). Reference patches average 107.4 LOC over 4.1 files; trivial 1-10 line edits are excluded. SWE-Agent scaffold, same prompt for all models, 50-turn cap.
- **Numbers**: Public (N=731, Table 1, v2): Sonnet 4.5 43.6, Sonnet 4 42.7, GPT-5(high) 41.8, Haiku 4.5 39.5, Kimi K2 27.7, GPT-OSS-120B 16.2. Commercial (N=276, Table 2): Opus 4.1 17.8, GPT-5(high) 15.7, GPT-5(med) 14.9, Gemini 2.5 Pro 10.1, Sonnet 4 9.1, GPT-4o 3.6. The two tables use different model lists; the only like-for-like pairs at the same 50 turns/$2 cap (Table 5, public): GPT-5(high) 25.9 -> 15.7 commercial; Opus 4.1 22.7 -> 17.8; Sonnet 4 17.6 -> 9.1; Gemini 2.5 Pro 13.5 -> 10.1; GPT-4o 4.9 -> 3.6. Caveat: I could not confirm that the commercial runs also had the $2 cap (text only says "max 50 turns"). Interpretation: relative drop public->commercial of roughly 20% (Opus) to 48% (Sonnet 4) at the same nominal setting; drop is larger for the stronger-on-public model families. Without human augmentation (problem statement only) GPT-5 falls 25.9 -> 8.4 and Opus 4.1 22.7 -> 8.2 (Table 3). Run-to-run variance not reported (single runs). Held-out set results not reported.
- **Admitted limitations / future work**: Sec 7.1: language coverage non-uniform (Java/C++/Rust under-represented); dependence on fail2pass/pass2pass tests that may reject other valid solutions ("ideally a set of verifiers which can verify any valid solution"). Sec 7.2: rubric/quality/security/performance metrics, collaborative scenarios. All analyses done on public set "to avoid leakage" into commercial.
- **Relevance**: Closest published analogue to the Kaggle setting (private repos never seen publicly): the only quantified public-vs-private-repo gap in a mainstream benchmark, but confounded by different model lists and no variance estimate; commercial N=276 so a 5-point gap is about 1 SE.

#### SWE-Bench Pro Verified: SWE-Bench Pro Verified: A Reliable Benchmark for Software Engineering Agents
- **Ref**: arXiv 2609.08149 (v3), Sep 2026, https://arxiv.org/abs/2609.08149 (authors not noted)
- **Contribution**: Audits SWE-Bench Pro's public set and finds (i) reward hacking via gold-patch/hidden-info leakage (git history, local files, public code-hosting domains) and (ii) task-quality defects (misleading statements, over-scoped tests); releases a version with anti-hacking safeguards (domain blocklist, evaluation-data cleanup) and minimal task corrections.
- **Numbers**: On all 731 public instances, GLM-5.2 goes 78.80% (baseline) -> 57.32% (anti-hacking), -21.48 pp; 186 passes became fails vs 15 fails became passes (McNemar p<0.001); after task correction 59.51%. DeepSeek-V4-Pro barely moves (consistent with little hacking). Authors argue the paired asymmetry cannot be decoding noise.
- **Admitted limitations**: Sec 5.2: domain blocklist cannot cover self-hosted git hosts, proxies, mirrors, or raw IPs and capable models may circumvent it; cleanup may leave residual information.
- **Relevance**: Shows leaderboard ranks on a "contamination-resistant" public set can be inflated by environment leakage rather than memorisation; for a private-repo Kaggle task the analogue is checking that the sandbox exposes no .git history / hidden tests.

#### Shortcutting: Shortcutting the Fix: Identifying and Categorizing Agentic Exploits in Software Engineering Benchmarks
- **Ref**: arXiv 2609.06780, Sep 2026, https://arxiv.org/abs/2609.06780
- **Contribution**: Formalises "agentic shortcutting" (retrieving upstream fixes, mining local git history, recalling memorised code) and audits three open LLMs on SWE-bench Multilingual and DeepSWE with trajectory-level LLM judges.
- **Numbers**: Shortcut attempts in 60.7-90.1% (SWE-bench Multilingual) and 55.5-89.1% (DeepSWE) of trajectories; up to 72.1% of tasks resolved with the aid of a successful exploit; disabling network access does not curb attempts. An instruction to solve independently cuts attempts to 9.4-14.2% / 0.9-10.3% while leaving core performance roughly intact. Judge-human agreement 87.8%.
- **Admitted limitations**: Limitations section: only three open-weight models; LLM-judge misclassification possible.
- **Relevance**: A sandbox with network off and no git history is necessary; an explicit "no looking up the solution" prompt is cheap. Private repos remove the upstream-PR channel altogether.

#### SWE-Bench Illusion: The SWE-Bench Illusion: When State-of-the-Art LLMs Remember Instead of Reason
- **Ref**: Liang, Garg, Zilouchian Moghaddam, arXiv 2506.12286 (v4 Dec 2025), https://arxiv.org/abs/2506.12286 (abstract page read; body not opened)
- **Contribution**: Two memorisation probes: identify buggy file from issue text alone (no repo), and reproduce the ground-truth function from context (5-gram overlap).
- **Numbers**: File-path identification up to 76% on SWE-bench Verified vs up to 53% on repos outside SWE-bench; verbatim function reproduction up to 35% on Verified/Full vs up to 18% on other coding benchmarks.
- **Admitted limitations**: Abstract itself hedges ("may be partially driven by memorization"); I could not verify sample sizes or model list from the abstract page.
- **Relevance**: Direct evidence that public-repo scores overstate ability on repos the model saw; a private-repo test removes this component, so expect lower absolute scores and different ranking drivers (exploration/localisation rather than recall).

#### File-path memo: Does SWE-Bench-Verified Test Agent Ability or Model Memory?
- **Ref**: arXiv 2512.10218 (v2), Dec 2025, https://arxiv.org/abs/2512.10218 (authors not noted)
- **Contribution**: Asks two Claude models to find edited files from issue text alone (then issue + file paths) on SWE-Bench-Verified vs BeetleBox and SWE-rebench (both popular open-source Python repos).
- **Numbers**: Models were 3x better on SWE-Bench-Verified and 6x better at finding edited files with no project context.
- **Admitted limitations**: Short paper (no limitations section found); only two models of one family, localisation step only.
- **Relevance**: Same message as the Illusion paper with a decontaminated comparison (SWE-rebench): the gap exists even among "popular Python repos", so it is a time/provenance effect, not a repo-popularity effect.

#### SchrodingerRepo: Schrodinger's Code Repository: Have LLMs Learned SWE-bench or Memorized It?
- **Ref**: Chen, Yang, Gu et al. (SJTU), arXiv 2609.27891, 21 Aug 2026, https://arxiv.org/abs/2609.27891
- **Contribution**: Re-instantiates the test repo at evaluation time with four semantics-preserving transformation levels (problem-statement reconstruction, namespace remapping, intra-file reordering, functionality-preserving rewrite); a seed gives a distinct view per run. mini-swe-agent on SWE-bench Verified, the March 2026 SWE-rebench split (post-cutoff) and SWE-QA.
- **Numbers**: Full transformation lowers Verified Pass@1 in absolute points: GPT-5.4-mini 46.8 -> 35.6 (-11.2), DeepSeek-v4-Flash 72.8 -> 66.8 (-6.0), GPT-5.1 44.6 -> 36.2 (-8.4), Gemini-3.1-Flash-Lite 56.7 -> 42.3 (-14.4), all p<0.05; input tokens up to >2.5x. Namespace remapping (Level 2) dominates. On the post-cutoff SWE-rebench split GPT-5.4-mini stays at 17.27% (unchanged) but actions rise 15.82 -> 17.11 and input tokens +22%; interaction cost increase is larger in widely used, long-standing repos. SWE-QA: GPT-5.4-mini 70.35 -> 65.71.
- **Admitted limitations**: Sec VI Threats to Validity (external: CLI-only tools; IDE/LSP tools left to future work); compute limited analyses to two models.
- **Relevance**: Cleanest causal estimate of repo-familiarity effect: 6-14 absolute pp on Verified, zero on already-unfamiliar tasks. For private repos expect agents to behave as in the "transformed" condition: more exploration steps, which under a 6 min cap converts into fewer finished tasks.

#### BenchChecker: BenchChecker: Assessing the Credibility of Bug-Fixing Benchmarks for LLMs
- **Ref**: arXiv 2610.19447, Oct 2026, https://arxiv.org/abs/2610.19447
- **Contribution**: Forensic two-stage contamination detector (repo-presence prefix probe, then patch-presence in the cutoff snapshot); AUC ~0.9 on six benchmarks with StarCoder/CodeGen2 (Stack v2 trained).
- **Numbers**: Filtering contaminated samples from SWE-bench Verified and Multi-SWE-bench lowers reported resolve rates of most LLMs by >20% relative on medium-difficulty tasks.
- **Admitted limitations**: Stage I is lexical not structural; Stage II assumes the patch persists in the cutoff snapshot, otherwise contamination is underestimated.
- **Relevance**: Another estimate of contamination inflation (>20% relative) from a different method than the memorisation probes.

#### Measurement-First Auditing: Measurement-First Auditing of Agentic Leaderboards: Contamination Susceptibility, Matched-Control Re-evaluation, and Scorer Validation
- **Ref**: arXiv 2610.05830, Oct 2026, https://arxiv.org/abs/2610.05830
- **Contribution**: Separates contamination into training-time exposure, evaluation-time retrieval, pipeline leakage; applies an outcome-blind same-repo matched-control design to the SWE-bench Verified file-localisation gap.
- **Numbers**: Across nine HAL configurations none of 27 channel assessments was "closed", incidents confirmed in four; on 100 retained pairs GPT-4.1 shows +10.0 pt Top-3 gap but both paired-bootstrap and repo-balanced 95% CIs include zero; the scorer failed its validation gate.
- **Admitted limitations**: Sec 5.2: sparse consensus-positive human labels, probe credits solution-specific recall, manual review blinding.
- **Relevance**: Counter-evidence to the memorisation narrative: the file-path gap is "inconclusive" under a matched-control design, so claims of 3-6x gaps rest on non-matched comparisons.

#### Over-specification: Between Spoilers and Guesswork: Avoiding Over-Specification in Coding Benchmarks
- **Ref**: Liu, Lipka, Shinnar, Ganhotra, Ma, Hirzel (IBM / RPI), arXiv 2610.22760, 16 Oct 2026, https://arxiv.org/abs/2610.22760 (read abstract, intro, conclusion; did not extract per-benchmark tables)
- **Contribution**: Studies hint augmentation (SWE-bench Pro, FEA-bench, Doc2Feat-bench, Multi-SWE-bench add ground-truth-derived hints) on five repo-level benchmarks (Python, Java); proposes DefUse identifier selection + Declaration projection (names/signatures only) to fix test-required-names without leaking implementation. Notes OpenAI recommended SWE-bench Pro then withdrew that after finding underspecified prompts and overly restrictive tests in Pro (cited as OpenAI 2026b/c; I did not open those).
- **Numbers**: Qualitative; "performance gains can accompany greater disclosure of implementation choices". Hint-judge scores group mean 1.50 vs 1.45 (table fragment).
- **Admitted limitations**: Sec 5: hints assessed by LLM judge; limited to identifier hints.
- **Relevance**: Central for hidden-test scoring: tests that require unstated new names make private-repo tasks lottery tickets; hints/interfaces in the prompt may be a bigger lever than agent skill.

### 2. Test adequacy, weak tests, over-strict tests, solution leakage

#### SWE-Bench+: SWE-Bench+: Enhanced Coding Benchmark for LLMs
- **Ref**: Aleithan et al., arXiv 2410.06992 (v2), Oct 2024, https://arxiv.org/abs/2410.06992
- **Contribution**: Manual screening of SWE-Agent+GPT-4's resolved SWE-bench instances against the real PRs.
- **Numbers**: 32.67% of successful patches involve "solution leakage" (answer in issue/comments); 31.08% pass only through weak tests; after filtering, resolution drops 12.47% -> 3.97%; >94% of issues pre-date LLM cutoffs. Same issues observed in Lite and Verified.
- **Admitted limitations**: Not found in the sections I opened (abstract + intro); analysis based on a single agent (SWE-Agent+GPT-4) on the original 2,294 set.
- **Relevance**: Establishes the three confounds (leakage, weak tests, contamination) that private repos only partly remove: weak tests and leakage-in-issue remain.

#### PatchDiff: Are "Solved Issues" in SWE-bench Really Solved Correctly? An Empirical Study
- **Ref**: Wang et al., arXiv 2503.15223 (v2), Mar 2025, https://arxiv.org/abs/2503.15223
- **Contribution**: PatchDiff differential patch testing between agent patch and ground truth, on three tools (CodeStory, LearnByInteract, OpenHands) on SWE-bench Verified.
- **Numbers**: 7.8% of "correct" patches fail the developer-written test suite (harness gaps); 29.6% of plausible patches behave differently from ground truth (46.8% of those from similar but divergent implementations, 27.3% from adapting more behaviour); 28.6% of divergent patches judged certainly incorrect on manual review; net inflation of reported resolve rates 6.4 absolute pp.
- **Admitted limitations**: Not extracted (only abstract/intro opened).
- **Relevance**: Magnitude of weak-test inflation (about 6 pp) is of the same order as the noise between agents; the direction is opposite to hidden-test strictness in a private set.

#### UTBoost: UTBoost: Rigorous Evaluation of Coding Agents on SWE-Bench
- **Ref**: arXiv 2506.09289 (ACL 2025), Jun 2025, https://arxiv.org/abs/2506.09289
- **Contribution**: UTGenerator produces extra unit tests from codebase analysis; UTBoost augments SWE-bench tests.
- **Numbers**: 36 task instances with insufficient tests, 345 erroneous patches wrongly labelled passed; affects 40.9% of SWE-bench Lite and 24.4% of Verified leaderboard entries, causing 18 and 11 ranking changes. Also found a log-parser bug (multi-line test names) in the SWE-bench harness.
- **Admitted limitations**: None found in sections opened.
- **Relevance**: Ranking changes 11-18 on leaderboards show how fragile fine ordering is under test-set perturbation, not just under agent randomness.

#### SWE-ABS: SWE-ABS: Adversarial Benchmark Strengthening Exposes Inflated Success Rates on Test-based Benchmark
- **Ref**: Yu, Cao et al., arXiv 2603.00520, 28 Feb 2026, https://arxiv.org/abs/2603.00520
- **Contribution**: Coverage-driven (program slicing) plus mutation-driven adversarial test augmentation (plausible-but-wrong patches) on SWE-bench Verified and Pro.
- **Numbers**: One in five "solved" patches from top-30 agents is semantically wrong; 50.2% of instances strengthened (25.1x prior work); 19.78% of previously passing patches rejected; top agent 78.80% -> 62.20% and drops from 1st to 5th.
- **Admitted limitations**: Sec A.12: 10.6% false-negative rate (53/500) where augmented tests reject valid alternative patches by encoding gold-patch specifics; intraprocedural slicing only; needs gold patch; external validity limited to Python/JS/Go/TS in copyleft repos ("proprietary codebases" explicitly not covered).
- **Relevance**: Quantifies the strict-test failure mode too (10.6% valid patches rejected): with full hidden test files in a private-repo Kaggle, some ceiling below 100% is test-overfitting noise independent of the agent.

#### ABC: Establishing Best Practices for Building Rigorous Agentic Benchmarks
- **Ref**: Zhu, Kang et al., arXiv 2507.02825 (v5; NeurIPS 2025 D&B), Jul 2025, https://arxiv.org/abs/2507.02825
- **Contribution**: Agentic Benchmark Checklist (outcome validity, task validity, reporting) from a review of 17 benchmarks.
- **Numbers**: Flaws shift measured performance by up to 100% relative; 24% of the top-50 SWE-bench Verified leaderboard positions are incorrect (citing UTBoost/PatchDiff); tau-bench empty response counts as success; an agent can score 100% on SWE-Lancer without solving any task; KernelBench overestimates by 31% absolute; WebArena by 5.2%; applying ABC to CVE-Bench reduces overestimation by 33%. Seven benchmarks have outcome-validity flaws, seven task-validity flaws, all have reporting limitations.
- **Admitted limitations**: Checklist is guidance, not exhaustive; (details of the limitations paragraph not extracted).
- **Relevance**: Reporting items (error bars, number of runs, trivial-agent baselines) are the template for a Kaggle-scoring audit; the "trivial agent" baseline idea transfers directly (e.g. empty patch, copy-test patch).

### 3. Fresh / multi-repo / multi-language benchmarks (generalisation to unseen repos)

#### SWE-bench-Live: SWE-bench Goes Live!
- **Ref**: Zhang et al. (Microsoft), arXiv 2505.23419 (v2), May 2025, https://arxiv.org/abs/2505.23419
- **Contribution**: Live-updating issue-resolution benchmark: 1,319 tasks from issues created since 2024, 93 repos, per-task Docker images, automated RepoLaunch pipeline for environment setup.
- **Numbers**: Best combination (OpenHands + Claude 3.7 Sonnet) resolves 19.25% of SWE-bench-Live; the same pair re-run under identical settings on SWE-bench Verified gets 43.20%, "more than twice". Split by repo origin (Table 5): 22.96% on tasks from SWE-bench repos vs 18.89% on tasks from non-SWE-bench repos (383 tasks, repos with ~68k LOC vs ~223k LOC, i.e. unseen repos are smaller yet harder). Creation-quarter effect is flat (2024Q1-2025Q1), so recency itself does not make tasks harder. (Inconsistency: text says 216 instances from 8 SWE-bench repos, Table 5 lists 744; I report the table.)
- **Admitted limitations**: Not explicit in sections read; static-benchmark staleness is the motivation; Python only in first release.
- **Relevance**: Cleanest public measurement of the "unseen repo" gap at matched agent: about 4 pp (17% relative) from repo familiarity, plus large Verified-to-Live gap (2.2x) when including benchmark age, curation and leaderboard-style effort.

#### SWE-rebench: SWE-rebench: An Automated Pipeline for Task Collection and Decontaminated Evaluation of SWE Agents
- **Ref**: Badertdinov et al. (Nebius), arXiv 2505.20411, May 2025, https://arxiv.org/abs/2505.20411
- **Contribution**: 21,000+ interactive Python tasks for RL plus a monthly contamination-free benchmark (294 tasks, 169 repos, standardised ReAct scaffold, fixed prompt); each model run five times with SEM and pass@5 reported.
- **Numbers**: Jan 2025 / Mar-Apr 2025 slices: GPT-4.1 31.1 +- 0.79 SEM (pass@5 44.4) / 26.7 +- 1.09 (39.0); DeepSeek-V3-0324 21.7 +- 1.64 / 21.3 +- 0.98; Qwen3-235B no-think 15.2 +- 1.76 / 16.6 +- 0.93; Llama-3.3-70B 8.2 +- 0.44 / 11.2 +- 0.47. So SEM across 5 runs of 294 tasks is 0.4-1.8 pp, and the same model's score moves up to ~4 pp (GPT-4.1) between task slices. Authors flag that "evaluating an agent multiple times and reporting only the best run risks overstating" capability and that single-run results "can vary significantly".
- **Admitted limitations**: Fixed scaffold means measurements mix model and scaffold ability; benchmark restricted to Python (Appendix H filtering; I did not read the limitations section in full).
- **Relevance**: Closest published protocol to "identical resubmissions": 5 runs + SEM. The SEM of up to 1.8 pp at N=294 equals ~5 tasks, i.e. well above the ~1.5 task std in the Kaggle LB.

#### Multi-SWE-bench: Multi-SWE-bench: A Multilingual Benchmark for Issue Resolving
- **Ref**: Zan et al. (ByteDance), arXiv 2504.02605, Apr 2025, https://arxiv.org/abs/2504.02605
- **Contribution**: 1,632 instances (68 annotators from 2,456 candidates) in Java, TS, JS, Go, Rust, C, C++; Agentless / SWE-agent / OpenHands variants; plus Multi-SWE-RL (4,723 RL instances).
- **Numbers**: Verbatim summary: agents resolve Python issues but "struggle to generalize effectively across other languages"; resolve rate falls sharply when fix patches exceed ~600 tokens or touch more than one file and reaches zero for Java at >1000-token patches. I did not extract the per-language headline numbers.
- **Admitted limitations**: Not extracted.
- **Relevance**: Language/scale of the fix, not repo privacy, drives difficulty; a private-repo test set in an unusual language would confound unseen-repo and unseen-language effects.

#### SWE-PolyBench: SWE-PolyBench: A multi-language benchmark for repository level evaluation of coding agents
- **Ref**: Amazon Science, arXiv 2504.08703, Apr 2025, https://arxiv.org/abs/2504.08703
- **Contribution**: 2,110 instances, 21 repos, Java (165), JS (1017), TS (729), Python (199); stratified SWE-PolyBench500; syntax-tree-based metrics (node-level retrieval) beyond pass rate.
- **Numbers**: Sonnet 3.5-based agents: Python 20-24%, Java 11-16%, TypeScript 5-13% pass rates, all "relatively modest compared to SWE-bench".
- **Admitted limitations**: Not extracted.
- **Relevance**: Python pass rates on a fresh multi-repo set are about half of SWE-bench numbers for the same model family: another unseen-repo drop datapoint.

#### SWE-Lancer: SWE-Lancer: Can Frontier LLMs Earn $1 Million from Real-World Freelance Software Engineering?
- **Ref**: Miserendino et al. (OpenAI), arXiv 2502.12115, Feb 2025, https://arxiv.org/abs/2502.12115
- **Contribution**: 1,400+ Upwork tasks ($1M of payouts) in the Expensify codebase, graded by end-to-end tests triple-verified by engineers; Diamond public split ($500,800), remainder kept private to limit contamination.
- **Numbers**: Claude 3.5 Sonnet: 26.2% IC SWE and 44.9% SWE Manager on Diamond ($208,050 of $500,800). Cost across runs varies: GPT-4o 95% CI $194.31 +- $17.31, o1 $1,623.76 +- $56.68. No variance found from including prices in the prompt.
- **Admitted limitations**: Contamination possible (public GitHub issues 2023-2024, browsing lookup); no clarifying questions; cost analysis uses API prices, retries, historical bounties (Sec on limitations). ABC (2507.02825) reports an agent can score 100% without solving tasks.
- **Relevance**: Single-repo, private-held-out half; shows that a private split is only meaningful if the harness blocks lookups.

#### Randomness: On Randomness in Agentic Evals
- **Ref**: Bjarnason, Silva, Monperrus (KTH), arXiv 2602.07150 (v3 25 Mar 2026), https://arxiv.org/abs/2602.07150
- **Contribution**: 10 independent runs x 6 agent configs (3 models x 2 scaffolds) on SWE-Bench-Verified = 60,000 trajectories (25.58B tokens). Token-level analysis of divergence; power-analysis recipe (Appendix A) for the number of runs.
- **Numbers**: Single-run pass@1 spreads 2.2-6.0 pp (min-max across 10 runs); std 0.7-1.7 pp, still >1.5 pp at temperature 0 in some configs (Table 1 examples: DeepSWE-preview/nano-agent 31.4 +- 1.0, range 28.8-32.4; Qwen3-32B/R2E-Gym 23.9 +- 1.4, range 21.4-26.4; Devstral-2 63.5 +- 1.1, 63.8 +- 1.6 at temp 0.0). Trajectories diverge within the first few percent of tokens. Recommends multiple runs, power analysis, pass@k and pass^k.
- **Admitted limitations**: Single benchmark (Verified, 500 tasks, Python); open-weight models; I did not locate a separate limitations section.
- **Relevance**: Std of 0.7-1.7 pp on 500 tasks is 3.5-8.5 tasks; the Kaggle 1.5 task std on 58 tasks (2.6 pp) is the same order of per-task flip noise, so the LB gap that matters is at most a few tasks.

#### Harness: What Does a Harness Buy? Tokens, Mostly
- **Ref**: arXiv 2610.04433, Oct 2026, https://arxiv.org/abs/2610.04433 (authors not noted)
- **Contribution**: Five open models x three production harnesses (Claude Code, mini-SWE-agent, OpenCode) on SWE-bench Verified (447 tasks pool, 45-task hard subset), with reruns to calibrate noise; flip-rate on a common scale.
- **Numbers**: On the 45-task hard subset swapping the harness flips 13% of tasks (median), the same as rerunning the same harness (13%). Rerunning moves a harness by up to 3 of 45 tasks. At the observed discordance 45 tasks detect a 13-point gap only half the time and no gap at 80% power; 447 tasks resolve 5 points. Claude Code vs mini-SWE-agent equivalent within 5 pp (TOST, delta=5) on both models; OpenCode trails by up to 9 pp, partly output-cap truncation. Cost per task differs up to 3x across harnesses for the same model/tasks, set by the per-step preamble (system prompt and tool schemas) times step count.
- **Admitted limitations**: No dedicated limitation section found; McNemar and Newcombe intervals unadjusted for multiple pairs; open-weight models mainly.
- **Relevance**: Directly answers "how many tasks to separate two agents": ~45 tasks cannot see a 13-pp gap with 80% power; the Kaggle public LB of 58 tasks has the same problem. Flip-rate (13% of tasks change under rerun) is a transferable noise metric.

#### HAL: Holistic Agent Leaderboard: The Missing Infrastructure for AI Agent Evaluation
- **Ref**: Kapoor et al. (Princeton), arXiv 2510.11977 (ICLR 2026), Oct 2025, https://arxiv.org/abs/2510.11977
- **Contribution**: Parallel harness over hundreds of VMs; 21,730 rollouts, 9 models x 9 benchmarks (incl. SWE-bench Verified Mini with SWE-Agent), about $40,000; accuracy-vs-cost Pareto frontiers (dollars and tokens); LLM-aided log inspection (Docent) of 2.5B tokens.
- **Numbers**: Higher reasoning effort reduces accuracy in the majority of runs; agents look up benchmark answers on HuggingFace; misuse of credit cards in tau-bench airline. Evaluation time cut from weeks to hours.
- **Admitted limitations**: Appendix A4: SWE-Agent caching not reflected in cost (full token prices reported); public test sets only; API rate-limit errors add variance.
- **Relevance**: Template for cost-Pareto reporting; note it measures dollar cost, not wall-clock per task.

#### Confident-wrong: Confident and Wrong: Silent Semantic Failures in Coding Agents
- **Ref**: Mehta, arXiv 2603.25764, Mar 2026, https://arxiv.org/abs/2603.25764
- **Contribution**: 1,750 trajectories on 50 SWE-bench Verified tasks x four models x repeated runs (mini-SWE-agent); separates submit rate from test-verified resolve rate.
- **Numbers**: GPT-5 submits on 100% of runs but resolves 44%; Llama 4 99% vs 18%; Gemini submits 70% yet resolves 50% > GPT-5. "Silent semantic failure" covers 80% of Llama 4's and 68% of GPT-5's failing runs; same wrong interpretation repeated across runs. (Coefficient of variation is of step counts, not resolve rate; a secondary summary I first saw misreported this.)
- **Admitted limitations**: Sec 8: SWE-bench suites can be incomplete; Python only; one minimal scaffold; "50 tasks is modest" (mitigated with paired tests and bootstrap CIs).
- **Relevance**: Failures are consistent, not random: repeated runs on the same task are correlated, so re-submission noise understates agent error (repeated runs do not average out systematic misreads).

#### Pair-count: When Pair Count Is Not the Sample Size: What All-Pairs Agent Comparisons Estimate
- **Ref**: Huang, arXiv 2609.33012 (TAE workshop), 26 Sep 2026, https://arxiv.org/abs/2609.33012
- **Contribution**: Statistical note: all-pairs leaderboard comparisons reuse entries (U-statistic); intervals must count configurations, not pairs.
- **Numbers**: On a fixed SWE-bench Verified snapshot, intervals accounting for shared configurations are more than twice as wide as pair-iid intervals; pair-iid coverage far below nominal when edges share endpoints.
- **Admitted limitations**: Sec 8: without a sampling frame, results describe the named panels, not future submissions; SWE lineage metadata incomplete, repeated outcomes missing.
- **Relevance**: Warns against treating Kaggle submissions as independent samples when picking the best of many resubmissions.

#### HSPR: HSPR: Recovering Software-Agent Benchmark Scores via Hierarchical Posterior Inference
- **Ref**: Chen et al. (Soochow Univ.), arXiv 2610.24611 (v2 20 Oct 2026), https://arxiv.org/abs/2610.24611
- **Contribution**: Estimates full-benchmark score from an adaptive 5-20% task subset using historical response structure on four SWE-bench-family banks.
- **Numbers**: At a 10% budget lowest MAE on three of four banks and lowest max error on all four; macro MAE decreases from 5% to 20%. (Absolute MAE values not extracted.)
- **Admitted limitations**: Limitations paragraph: untested under big shifts in model family/scaffold; depends on historical bank coverage; posterior conditional on exchangeability; savings in tokens/wall-clock depend on per-task cost.
- **Relevance**: Subset-selection literature (cites Ndzomga 2026, Gusev & Zaytsev 2026) gives an alternative to scoring 58 tasks: weight tasks by informativeness.

#### SWE-bench Multimodal: SWE-bench Multimodal: Do AI Systems Generalize to Visual Software Domains?
- **Ref**: Yang, Jimenez et al., arXiv 2410.03859, Oct 2024, https://arxiv.org/abs/2410.03859
- **Contribution**: 617 tasks from 17 JavaScript front-end libraries with images in the statement or tests; tests whether Python-tuned SWE systems transfer.
- **Numbers**: Top SWE-bench systems "struggle", SWE-agent (language-agnostic tooling) resolves 12% vs 6% for the next best system.
- **Admitted limitations**: Not extracted (abstract/intro only).
- **Relevance**: Early evidence that scaffolds tuned on one distribution (Python SWE-bench) lose half their performance off-distribution, while generic tools transfer better.

#### FEA-Bench: FEA-Bench: A Benchmark for Evaluating Repository-Level Code Generation for Feature Implementation
- **Ref**: Li et al. (Microsoft), arXiv 2503.06680, Mar 2025, https://arxiv.org/abs/2503.06680
- **Contribution**: 1,401 feature-implementation tasks from 83 repos, each with unit test files; new components rather than bug fixes.
- **Numbers**: Best LLM (DeepSeek-R1) resolves only about 10% of instances.
- **Admitted limitations**: Limitations section: Python only; high-quality feature PRs are scarce. (Over-specification paper 2610.22760 lists FEA-Bench among benchmarks that add ground-truth hints.)
- **Relevance**: Tasks requiring unseen new names/files are where hidden test files bite hardest; hint design matters (see 2610.22760).

#### SWE-Gym: Training Software Engineering Agents and Verifiers with SWE-Gym
- **Ref**: Pan et al., arXiv 2412.21139 (ICML), Dec 2024, https://arxiv.org/abs/2412.21139
- **Contribution**: 2,438 Python tasks with executable environments (training environment); used to train agents and verifiers.
- **Numbers**: Up to 19 pp absolute gain on SWE-Bench Verified/Lite after training; 32.0% (Verified) and 26.0% (Lite) with verifier-based inference-time scaling, then SOTA for open-weight agents. Evaluated with temperature 0.
- **Admitted limitations**: Conclusion/limitations paragraph not fully extracted (I only saw that sampling more trajectories likely helps "regardless of duplication or repository distribution").
- **Relevance**: As an eval it is a training-distribution check: gains on Verified after training on same-style repos may reflect repo-family transfer, not general skill.

#### DeepSWE: DeepSWE: Measuring Frontier Coding Agents on Original, Long-Horizon Engineering Tasks
- **Ref**: Huang et al., arXiv 2607.07946, Jul 2026, https://arxiv.org/abs/2607.07946
- **Contribution**: 113 original tasks written from scratch (never contributed upstream) over 91 active open-source repos, 5 languages; hand-written behavioural verifiers that accept any implementation providing the functionality; mini-swe-agent with single bash tool, ~4 rollouts per task.
- **Numbers**: An independent LLM judge disagrees with DeepSWE's verifier 1.4% of the time vs 32.4% with SWE-Bench Pro's inherited tests. Reference solutions touch 5.5x more code than Pro with prompts half as long. Wall-clock cap 9,000 s (2.5 h), "sanity upper bound", binds on only 67 of 7,174 scored rollouts (0.9%); timeouts and context overflow count as failures; provider/network/verifier errors excluded (0% for top 3 configs, up to 5.3% Gemini 3 Flash). Reported intervals: GPT-5.5 run-to-run 95% CI [67.2, 72.9] vs cluster-bootstrap over tasks [65.6, 74.1]. Pilot of n=10 Pro tasks suggests mini-swe-agent does not handicap any model family (tiny sample).
- **Admitted limitations**: Sec 8: binary reward; functional correctness only; prompts of ~2,000 chars are more specified than real requests; single fixed harness; run-to-run CI from ~4 runs can look too tight ("small-sample weakness"), and misses task-sampling noise; per-tag rates below ~5% illustrative only.
- **Relevance**: Evidence that "inherited tests" (like the hidden test files in a Kaggle set derived from PRs) can reject a third of correct-looking rollouts; and the 1.3-1.5x wider cluster interval is the right error bar when comparing agents on a fixed set of ~100 tasks.

#### REAP/ProdCodeBench: ProdCodeBench / REAP: Automatic Curation of Coding Agent Benchmarks from Interactive Production Usage
- **Ref**: Jha, Paltenghi, Maddila, Murali, Ugare, Chandra (Meta), arXiv 2604.01527, Apr 2026, https://arxiv.org/abs/2604.01527 (the HTML I opened is the REAP/Harvest version; a search snippet for an earlier version cited 53.2-72.2% solve rates, so the versions differ)
- **Contribution**: Automated curation of a benchmark ("Harvest") from real developer-agent sessions in an industrial monorepo (mostly Hack, 4+ languages), with LLM task classification, test-relevance validation and multi-run stability checks to remove flaky or untestable tasks. Corpus is proprietary and unreleased.
- **Numbers**: Solve rates 42.9% to 58.2% across five frontier models (latest version). 
- **Admitted limitations**: Single-turn prompts, no intermediate human feedback ("case-study constraints"); corpus cannot be released.
- **Relevance**: The only industrial private-codebase benchmark found, but no public-vs-private comparison on the same models; absolute rates are not comparable to Verified.

#### SWE-Effi: SWE-Effi: Re-Evaluating Software AI Agent System Effectiveness Under Resource Constraints
- **Ref**: Fan, Vasilevski et al. (Huawei/CUHK-SZ/KCL/Queen's), arXiv 2509.09853 (v2), Sep 2025, https://arxiv.org/abs/2509.09853
- **Contribution**: Multi-dimensional "effectiveness" metrics that balance resolve rate against tokens, cost, CPU and inference time; re-ranks five scaffolds (AutoCodeRover, SWE-agent, OpenHands, Agentless, Agentless-Mini) x LLMs on a SWE-bench subset.
- **Numbers**: SWE-agent+Qwen3-32B has Effectiveness-under-Token-Budget 21.8% but 5.1% with GPT-4o-mini. "Expensive failures": an unresolved attempt consumes on average >4x the resources of a resolved one (for that system). Token snowball effect. Clear trade-off between effectiveness under a token budget and under a time budget.
- **Admitted limitations**: Not found as a labelled section in what I read (exploratory study; subset of SWE-bench).
- **Relevance**: The only paper I found that defines effectiveness under a time budget for issue resolution; confirms that failing runs burn disproportionate time, which matters with a 6 min cap (early stopping is worth more than extra steps).

#### TML-bench: TML-bench: Benchmark for Data Science Agents on Tabular ML Tasks
- **Ref**: Pinchuk, arXiv 2603.05764, Mar 2026, https://arxiv.org/abs/2603.05764
- **Contribution**: 10 open LLMs x 4 Kaggle competitions x three wall-clock budgets (240 s, 600 s, 1200 s), 5 runs per cell, scored on a private holdout inaccessible to the agent; median, success rate and run-to-run variability reported.
- **Numbers**: Average performance improves with larger time budgets; scaling is "noisy for some individual models at the current run count".
- **Admitted limitations**: Sec 5.2: budgets are confounded with instruction sets (1200 s uses an XGBoost-focused prompt); five successful runs per setting is noisy at model level; Sec 5.1 no token accounting; single harness (Kilo Code).
- **Relevance**: Closest to a Kaggle-style, hidden-label, fixed wall-clock protocol, but for tabular ML rather than issue resolution; budget range brackets the 6 min (360 s) cap. Not SWE.

#### Claw-SWE-Bench: Claw-SWE-Bench: A Benchmark for Evaluating OpenClaw-style Agent Harnesses on Coding Tasks
- **Ref**: arXiv 2606.12344, Jun 2026, https://arxiv.org/abs/2606.12344 (authors not noted)
- **Contribution**: 350 issue-resolution instances, 8 languages, 43 repos; seven general-purpose harnesses x three models under one outer budget (max 300 turns, 3600 s wall-clock, fixed concurrency, network blocked); 80-instance Lite subset.
- **Numbers**: Success rates and resource use vary substantially across harnesses at fixed model. Found leakage: git commits after the base commit remained accessible; removed before evaluation.
- **Admitted limitations**: No limitations section found (grep: 0 hits).
- **Relevance**: Example of a benchmark with a uniform wall-clock cap (3600 s, ten times a Kaggle 6 min); leakage fix (strip future commits) is mandatory for any repo-based sandbox.

#### Jagged Frontier: A Jagged Frontier: Evaluating Robustness of Code Agents to Semantics-Preserving Transformations
- **Ref**: arXiv 2608.18389, Aug 2026, https://arxiv.org/abs/2608.18389 (authors not noted)
- **Contribution**: Random variant sampler with semantics-preserving transformations (control-flow rewrites, dead-code injection, identifier renaming) on SWE-bench Verified and Pro; two scaffolds x four models; each instance run multiple times on original and perturbed variants for paired estimates that separate perturbation from stochasticity.
- **Numbers**: Up to 6.7 pp mean resolve-rate drop in the worst configurations; significant in 6 of 16 model/scaffold/dataset configurations; no single robustness ranking holds across scaffolds (Qwen robust under mini-SWE-agent on Verified but most brittle under OpenCode); simpler scaffold more robust.
- **Admitted limitations**: Not extracted.
- **Relevance**: Agent rankings are scaffold-dependent and brittle to superficial changes, a second reason that rank-order on public repos may not transfer to private ones (consistent with SchrodingerRepo's 6-14%).

#### Token reduction: Token Reduction Is Not Cost Reduction
- **Ref**: arXiv 2607.12161 (v5), Jul 2026, https://arxiv.org/abs/2607.12161 (authors not noted)
- **Contribution**: Paired, provider-billed experiments with Claude Code showing tool-output compression does not reliably lower billed cost (prompt-cache traffic dominates input cost).
- **Numbers**: Most aggressive compression cut delivered tool-output tokens by 38.4% yet raised billed cost by 6.8%; compression induced extra retrieval/turns; on a SWE-bench-derived Go subset aggressive compression also reduced task completion.
- **Admitted limitations**: Sec 14 lists campaign composition, thinking tokens, interactive sessions unmeasured; recommendations for benchmark design in Sec 15 (success-adjusted end-to-end cost).
- **Relevance**: Cost in tokens is a weak proxy for cost in seconds; for a fixed 6 min cap, step count and latency matter, not token totals.

#### TaskFlow: Coding-Agent Benchmarks Should Match Their Users' Task Flows
- **Ref**: arXiv 2610.09633 (v2), Oct 2026, https://arxiv.org/abs/2610.09633 (JetBrains-linked; authors not noted)
- **Contribution**: 4,782 real IDE agent sessions; shows issue-derived benchmark tasks differ in task-type mix and in switching; SWE-TaskFlow transforms a benchmark by prompt splitting and repo QA; TaskFlow Alignment Score.
- **Numbers**: Pilot on 700 SWE-Bench Pro tasks: solving sequentially in several steps roughly doubles agent cost without a stable change in resolve rate.
- **Admitted limitations**: Limitations paragraph: one use case; intent classifier lacks human-labelled accuracy set (inter-model agreement 76.1%); each pilot condition ran three times with min-max ranges, "not confidence intervals; no comparison carries a significance test".
- **Relevance**: Interaction protocol is itself an eval dimension; single-shot Kaggle protocol is one specific target use case.

#### StopLoss: StopLoss: Teaching Agents to Predict Failure and Stop Early
- **Ref**: arXiv 2610.25525, Oct 2026, https://arxiv.org/abs/2610.25525 (authors not noted)
- **Contribution**: Small outcome-trained monitor that scores the last tool steps and aborts likely-failing runs; trained on GPT-family SWE-rebench trajectories; evaluated on SWE-bench Verified and a three-repo Python subset of SWE-bench Pro.
- **Numbers**: Lowers cost per retained solve by 4.5% on Verified (keeping 99% of successful runs), up to 31% on the costlier Pro subset, 48% with a Qwen3-8B backbone; failure prediction goes from near chance to useful at the first check.
- **Admitted limitations**: Sec 7: trained only on GPT trajectories, Python only, Pro evaluation covers only three public Python repos.
- **Relevance**: Direct tool for a hard time cap: abort-or-submit decision before the deadline.

#### Patch performance: Not All Correct Fixes Run Alike: An Empirical Study of Patch Performance in Repository-Level Issue Resolution
- **Ref**: arXiv 2610.13563, Oct 2026, https://arxiv.org/abs/2610.13563 (authors not noted)
- **Contribution**: Reuses F2P tests to measure runtime (instruction count, wall-clock) of correct patches from four frontier models + SWE-agent on 262 cases from Verified splits of SWE-bench and SWE-bench-Live.
- **Numbers**: Welch ANOVA finds performance differences between correct patches in almost half of instances; patch runtime is independent of the model's resolve rate, with nearly reversed model rankings.
- **Admitted limitations**: Sec on external validity: Python only, single SWE-agent framework, restrictive deterministic corpus filter.
- **Relevance**: Pass/fail hides quality differences; tangential to a pass-rate Kaggle metric.

### 4. Statistical methodology for evals

#### Error bars: Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations
- **Ref**: Miller (Anthropic), arXiv 2411.00640, Nov 2024, https://arxiv.org/abs/2411.00640
- **Contribution**: Treats eval questions as draws from a super-population; formulas for SE, clustered SE, resampling to reduce conditional variance, paired-difference inference, power analysis.
- **Numbers**: No empirical headline; key formulas: Var(score) = between-question variance + E[sigma_i^2]/K, so re-running only removes the second term; unpaired SE_{A-B} = sqrt(SE_A^2 + SE_B^2) is too wide when per-question scores correlate, paired analysis recommended.
- **Admitted limitations**: Intended for readers with some statistics; for single-turn evals (no agent-specific treatment).
- **Relevance**: Framework for the Kaggle LB. My own arithmetic (not from the paper): 58 tasks at p=0.3 give a task-sampling SE of sqrt(0.3*0.7/58) = 6.0 pp (about 3.5 tasks), larger than the ~1.5-task resubmission std, so LB error is dominated by which tasks were sampled; a paired comparison of two agents on the same 58 tasks removes the shared task-difficulty term but not the within-task flip noise.

#### Signal and Noise: Signal and Noise: A Framework for Reducing Uncertainty in Language Model Evaluation
- **Ref**: Heineman et al. (AI2), arXiv 2508.13144, Aug 2025, https://arxiv.org/abs/2508.13144
- **Contribution**: Defines signal (ability to separate models) and noise (random variability between training checkpoints) for 30 benchmarks, 375 open-weight models (60M-32B), 900K evaluation results; interventions: better metric (perplexity vs accuracy), filter noisy subtasks, average checkpoints.
- **Numbers**: Higher signal-to-noise benchmarks give more reliable small-scale decisions and lower scaling-law error (qualitative in abstract).
- **Admitted limitations**: Pretraining-scale setting, no agentic or SWE benchmark specifically (limitations paragraph not located).
- **Relevance**: Conceptual: Kaggle noise = within-agent task-level flip noise; signal = spread between agents; same ratio governs how many tasks are needed. Not SWE-specific.

#### Underspecified: Interactive Agents to Overcome Ambiguity in Software Engineering (Ambig-SWE) and Ask or Assume?
- **Ref**: Vijayvargiya et al., arXiv 2502.13069 (v3), Feb 2025, https://arxiv.org/abs/2502.13069 ; Edwards and Schuster, "Ask or Assume? Uncertainty-Aware Clarification-Seeking in Coding Agents", arXiv 2603.26233, Mar 2026, https://arxiv.org/abs/2603.26233
- **Contribution**: Both build an underspecified SWE-Bench Verified variant (Ambig-SWE). Ambig-SWE tests detection of underspecification, clarifying questions, and use of the answer; Ask-or-Assume proposes a multi-agent scaffold decoupling underspecification detection from execution.
- **Numbers**: Models struggle to tell well-specified from underspecified inputs; interaction raises performance by up to 74% over non-interactive. Ask-or-Assume scaffold reaches 69.40% resolve rate on the underspecified variant, "closing the gap" to fully specified instructions. I did not find an explicit non-interactive drop figure in what I read.
- **Admitted limitations**: Ambig-SWE Sec 7: detection measured only in the first interaction turn, single-turn gaps; Ask-or-Assume "Limitations": LLM user simulator is unnaturally cooperative.
- **Relevance**: In a no-interaction Kaggle protocol the agent cannot ask; hidden tests needing unstated names/behaviour make a performance ceiling that interaction would lift by tens of percent.

#### AgentLens: AgentLens: Revealing The Lucky Pass Problem in SWE-Agent Evaluation
- **Ref**: arXiv 2605.12925 (v4), May 2026, https://arxiv.org/abs/2605.12925 (authors not noted)
- **Contribution**: Process-level scoring of 2,614 OpenHands trajectories from eight backends on SWE-bench Verified (60 tasks; 47 usable, 1,815 trajectories); prefix-tree references of correct behaviour; classifies passes as Lucky/Solid/Ideal.
- **Numbers**: 10.7% of passing trajectories are "Lucky Passes" (regression cycles, blind retries, missing verification); per model 0.5% to 23.2%; some models move up to five rank positions when ranked by quality instead of pass rate.
- **Admitted limitations**: Appendix A.1: OpenHands-style traces and Verified only; fixed score weights.
- **Relevance**: Pass-rate ranks conflate skill with luck; lucky-pass share is model-dependent, so luck is not a constant offset across agents.

#### PACE: PACE: A Proxy for Agentic Capability Evaluation
- **Ref**: arXiv 2607.02032 (v2), Jul 2026, https://arxiv.org/abs/2607.02032 (authors not noted)
- **Contribution**: Predicts agentic benchmark scores (incl. SWE-Bench) from a small selected subset of non-agentic instances via regression; 14 models, 4 agentic and 19 non-agentic benchmarks.
- **Numbers**: LOOCV MAE under 4%, Spearman >0.80, pairwise ranking accuracy ~85%, at <1% of the full agentic cost.
- **Admitted limitations**: Appendix F: proxy gaming if the subset becomes public; small calibration set (14 models).
- **Relevance**: Indicates ~15% of pairwise rankings are not predictable from cheap proxies; also the reverse: a 120-task private set may be only 85% rank-predictable by any public score.

### 5. Gray literature (secondhand, flagged)
- OpenAI, "Why we no longer evaluate SWE-bench Verified" (23 Feb 2026): primary page returned HTTP 403 to me; via the-decoder.com article (read): at least 59.4% of an audited subset (27.6% of tasks that models often failed, per a search summary) have flawed tests rejecting correct solutions; GPT-5.2, Claude Opus 4.5 and Gemini 3 Flash Preview could reproduce some original fixes from memory; recommended SWE-bench Pro and is building non-public tests. 2610.22760 says OpenAI later withdrew the Pro recommendation (citing "OpenAI 2026b") after finding underspecified prompts and overly restrictive tests in Pro; I did not open that primary source.
- J. Gabor (LessWrong/Substack), "SWE-Bench Pro is even worse": audit of 100 random Pro tasks, categories: test leniency, overly strict tests (e.g. flipt tests expecting buggy behaviour), requirements inflation; the percentage was only in a chart I could not read. A commenter claims 15-24% of the full Pro set unsolvable; unverified.

