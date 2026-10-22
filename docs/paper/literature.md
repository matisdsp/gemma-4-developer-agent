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


## 6. Context management and compute budgets


Literature notes compiled 2026-10-22. Every fiche below was written from a source actually opened (arXiv HTML/PDF full text or a blog page). Numbers are quoted from the papers' own tables/text. "Setting" = Google ADK agent, Gemma 4 31B / 4B, 32k context, ADK events compaction (LLM summary of everything except last ~5 events when prompt >= 14,336 tokens; summarizer sees only text parts, so tool outputs/diffs are dropped), overflow kills the session, ~6 min / ~30 tool calls per task, thinking on, ~30 tok/s.

### 1. Compaction strategies: masking vs summarization (SWE agents)

#### Complexity Trap: The Complexity Trap: Simple Observation Masking Is as Efficient as LLM Summarization for Agent Context Management
- **Ref**: Lindenbauer et al. (JetBrains Research / TU Munich), arXiv 2508.21433 (NeurIPS 2025 DL4Code), Aug 2025 (v3 Oct 2025), https://arxiv.org/abs/2508.21433
- **Contribution**: Controlled comparison inside SWE-agent on SWE-bench Verified (500 tasks, turn limit 250) of (a) raw agent, (b) observation masking (observations older than the last M=10 turns replaced by a placeholder, reasoning/actions kept), (c) LLM-Summary (OpenHands-style prompt, summarise N=21 turns, keep M=10 raw). Also a hybrid (masking + summary).
- **Numbers**: Qwen3-Coder 480B: raw 53.4% / $1.29; masking 54.8% / $0.61 (-52.7%); LLM-Summary 53.8% / $0.64 (-50.4%). Gemini 2.5 Flash: raw 32.8% / $0.41; masking 35.6% / $0.18; summary 36.0% / $0.24. Gemini 2.5 Flash (thinking): raw 40.4%, masking 36.4% (-9.9%), summary 31.4% (-22.3% relative to raw). Qwen3-32B (thinking, 122k YaRN window): raw 23.0, masking 24.6, summary 24.8, cost no better with summary (the only config where summary was not worse in cost-efficiency). "Trajectory elongation": summary makes trajectories longer (Gemini 2.5 Flash: 52 turns vs 44 masking vs 50 raw; Qwen3-Coder +15% vs raw), i.e. summaries hide failure signals and the agent keeps going. Summary calls are up to 7.2% of instance cost and defeat KV/prefix caching. Hybrid (N=21, M=W=10 re-used naively) actually degraded efficiency; tuned hybrid: -7% vs masking, -11% vs summary.
- **Admitted limitations / future work**: Sec. 6: (1) only SWE domain with very verbose tool outputs, which "naturally favors" masking; (2) heuristic fixed triggers (rolling window agnostic to staleness, e.g. keeps a file view after it was edited; summary on fixed turn schedule); (3) only initial evidence on other scaffolds (OpenHands).
- **Relevance**: Closest published ablation to the ADK compaction policy, but all models are large (>=32B) with 100k+ windows (no run under 32k, no wall-clock cap), and the summarizer there sees the observations (ADK's does not). Masking keeps the action/reasoning chain; ADK's summary replaces everything.

#### ACON: ACON: Optimizing Context Compression for Long-horizon LLM Agents
- **Ref**: Kang et al. (KAIST, Microsoft, Cambridge), arXiv 2510.00615 (ICLR 2026), Oct 2025, https://arxiv.org/abs/2510.00615
- **Contribution**: Learns the *compression guideline* in natural language: finds tasks where full context succeeds but compressed context fails, has an LLM analyse the failure and rewrite the guideline (utility step), then a cost-minimising step; compressor can be distilled into small models (LoRA). Compresses both observations and histories.
- **Numbers**: AppWorld/OfficeBench/Multi-objective QA with gpt-4.1: peak tokens -26% to -54% with accuracy preserved; on AppWorld history compression "reduces peak tokens by over 25% while preserving the accuracy of the no-compression upper bound" whereas baseline compressors "suffer severe degradation on medium and hard tasks spanning longer steps". Distilled compressors (Qwen3-14B, Qwen3-8B, Phi-4) keep >95% of the gpt-4.1 teacher. Small *agents* gain up to 46% (Qwen3-14B agent on AppWorld 26.8% -> 33.9%) "by mitigating context distraction".
- **Admitted limitations / future work**: App. A / Limitations: evaluation mostly on GPT models (no Gemini/Claude/large open-weight models, GPU limits); compression adds compute and latency; no SWE benchmark.
- **Relevance**: Direct evidence that naive prompting-based compression loses task-critical state on long tasks and that a failure-driven guideline fixes it; also first evidence that small agents (<=14B) benefit from compression. No coding tasks, so transfer to diffs/tool outputs is untested.

#### Context-Folding: Scaling Long-Horizon LLM Agent via Context-Folding (FoldAgent)
- **Ref**: Sun et al. (ByteDance Seed, CMU, Stanford), arXiv 2510.11967 (ICML 2026 as "Scaling Long-Horizon Agent via Context Folding"), Oct 2025, https://arxiv.org/abs/2510.11967
- **Contribution**: Agent gets two actions, `branch` (open a sub-trajectory for a sub-task) and `return` (fold the whole branch into a short result); trained with FoldGRPO (process rewards: unfolded-token penalty, out-of-scope penalty). Active context stays small; compared against ReAct at 32K/327K and a Summary Agent with 32,768 max context and 10 summary sessions.
- **Numbers** (Seed-OSS-36B, SWE-bench Verified N=500, pass@1): ReAct 327K 55.2%; ReAct **32K without management 43.6% (-11.6)**; Summary Agent (32K x 10) 48.8% untrained, 55.0% after GRPO; Folding Agent 49.2% untrained, 58.0% after FoldGRPO. BrowseComp-Plus: ReAct 32K 28.6%, ReAct 327K 47.8%, Summary 38.6%, Folding 42.0% untrained / 62.0% FoldGRPO. Tool calls: summary agent 77.0 vs ReAct-32K 25.8 on SWE (agent keeps working after compaction). Claims active context ~10x smaller.
- **Admitted limitations / future work**: Sec. 6: multi-layer (hierarchical) folding is future work; only two long-horizon tasks; gains rooted in RL training rather than in the mechanism alone (untrained folding is only +0.4 pt over untrained summary on SWE).
- **Relevance**: Only paper found that evaluates a 32k cap on SWE-bench: truncating at 32k costs ~12 pts, summary recovers ~5 of them untrained. A 36B model, not a Gemma 4B/31B, and it still uses 10 sessions of 32k (up to 327k total tokens), unlike a single 6-minute budget.

### 2. Budget awareness and overthinking

#### BATS: Budget-Aware Tool-Use Enables Effective Agent Scaling
- **Ref**: Liu et al. (UCSB, Google Cloud AI Research, Google DeepMind, NYU), arXiv 2511.17006, Nov 2025, https://arxiv.org/abs/2511.17006
- **Contribution**: Shows that giving a search agent a larger tool-call budget does not help because it lacks budget awareness; proposes a "Budget Tracker" (a prompt-level plug-in that tells the agent remaining tool calls) and BATS (budget-aware planning + verification), plus a unified token+tool cost metric.
- **Numbers**: Budget Tracker gives consistent gains over ReAct at the same budget: Gemini-2.5-Pro BrowseComp 12.6 -> 14.6, BrowseComp-ZH 31.5 -> 32.9, HLE-Search 20.5 -> 21.8; Gemini-2.5-Flash 9.7 -> 10.7 / 26.5 -> 28.7 / 14.7 -> 17.3; Claude-Sonnet-4 12.2 -> 14.0 / 29.1 -> 31.1 / 20.5 -> 23.0 (3 runs, SDs ~0.5-2). Budget 10 + tracker: 12.8% (6.8 cents) vs ReAct budget 100: 12.6% (9.9 cents). Full BATS (budget 100): 24.6% BrowseComp, 46.0% BrowseComp-ZH, 27.0% HLE-Search with Gemini-2.5-Pro; removing verification drops 18.7 -> 15.4 on BrowseComp.
- **Admitted limitations / future work**: App. G: only tool-call budgets studied; "a more realistic scenario involves managing multiple resource constraints jointly: token limits, inference latency and tool-call budgets"; no study of how an agent should allocate a budget; cost of repeated runs.
- **Relevance**: Direct template for telling the ADK agent "N of ~30 calls left"; but web-search domain, frontier models, no wall-clock, no coding, no small models. Explicitly leaves latency/token budgets open.

#### Overthinking: The Danger of Overthinking: Examining the Reasoning-Action Dilemma in Agentic Tasks
- **Ref**: Cuadron et al. (UC Berkeley, ETH, UIUC, CMU), arXiv 2502.08235 (ICML 2025), Feb 2025, https://arxiv.org/abs/2502.08235
- **Contribution**: Defines overthinking in agentic loops (analysis paralysis, rogue actions, premature disengagement), scores 4,018 SWE-bench Verified trajectories (OpenHands) with an LLM judge validated against human experts, and ties it to resolve rate.
- **Numbers**: Higher overthinking score <-> lower resolve rate across 19 models (regression on reasoning models beta1 = -7.894, R2 0.892; non-reasoning beta1 = -15.938, R2 0.839). Mean score reasoning 3.505 +/- 1.774 vs non-reasoning 2.228 +/- 0.751. Smaller models (32B/14B/7B of Qwen2.5-Instruct and R1-Distill-Qwen) overthink more as size decreases, and the reasoning/non-reasoning gap closes at small sizes. Abstract claims "almost 30%" gain at -43% cost; body: k=2 low-effort o1 samples, keep the one with lower overthinking = 27.3% resolved (about $800), "nearly matches" o1-high at 43% lower cost; k=3 gives 30.3%. o1-low overthinks 35% more than o1-high.
- **Admitted limitations / future work**: Judge-based metric (they report correlation with human experts); SWE-bench Verified/OpenHands only; native function calling and selective RL suggested as mitigations (Sec. 6-7).
- **Relevance**: Thinking-on small Gemma at 30 tok/s is exactly the regime where this predicts "think instead of act"; each thinking token costs wall-clock (6 min = ~10.8k generated tokens in total at 30 tok/s). Their cost axis is dollars, not time.

#### OpenHands-Condenser: OpenHands Context Condensation for More Efficient AI Agents (blog) + Software Agent SDK
- **Ref**: C. Smith (All Hands AI), blog, Apr 9 2025, https://openhands.dev/blog/openhands-context-condensensation-for-more-efficient-ai-agents ; Wang et al., "The OpenHands Software Agent SDK", arXiv 2511.03690, Nov 2025, Sec. 4.6
- **Contribution**: LLMSummarizingCondenser: once history reaches a size threshold, older events are replaced by an LLM summary (user goals, progress, what remains; for code "critical files and failing tests") while recent events stay intact; the full event log is kept, condensation is a stored event. SDK (2026 refactor) is the design ADK compaction closely resembles.
- **Numbers**: Blog: "up to 2x" per-turn API cost reduction (settles under half the baseline cost); on "a subset of SWE-bench Verified" it solves 54% vs 53% baseline; subset size, model, runs, variance and thresholds are not given. SDK paper repeats "reduce API costs by up to 2x with no degradation" citing the blog (no new measurement).
- **Admitted limitations / future work**: Blog: only trade-off is more turns ("the agent occasionally needs a turn to condense"); linear-cost claim holds "when events are of similar size" and is not measured. SDK Sec. 7 Limitations covers security/multi-agent only; nothing on compaction accuracy.
- **Relevance**: The production precedent for the ADK policy, but its only evidence is an unreplicated blog claim at large context; the independent test (Complexity Trap) found summary ~ masking on success and worse on cost; and 2605.18854 (below) finds LLM condensers cost +24-94%.

#### MemCondense: Evaluating Memory Condensation Strategies for Coding Agents in Data-Driven Scientific Discovery
- **Ref**: Chintalapati et al. (PNNL), arXiv 2605.18854, May 2026, https://arxiv.org/abs/2605.18854
- **Contribution**: Compares eight OpenHands condensers (NoOp, RecentEvents, AmortizedForgetting, ObservationMasking, ConversationWindow [reactive: fires only on context-overflow error], LLMSummarizing, StructuredSummary [18 fixed fields], LLMAttention) on 60 DiscoveryBench tasks x 8 = 480 runs with GPT-4o (GPT-5-mini condensing), 50-iteration cap, thresholds calibrated to the NoOp mean of 9 events (max_size=8, keep_first=2).
- **Numbers**: No condenser changes hypothesis quality significantly (0.559-0.637). LLM condensers increase total token cost by 24-94%; ObservationMasking is the only net saver (-8.6%; -52% on verbose sociology tasks, nothing on compact tasks). All heuristic condensers keep 100% task completion; LLM-based ones only 93-98% (i.e. summarization itself causes failed runs). Only tasks >10 events give positive savings (17-34%) for heuristics; short tasks get costlier under every strategy.
- **Admitted limitations / future work**: Sec. 6: one backbone (GPT-4o), "condensation effectiveness may differ for models with smaller context windows or weaker instruction-following"; tasks only 5-22 events; static per-run condenser choice (adaptive meta-condensers suggested).
- **Relevance**: 2026 confirmation (different domain, same OpenHands condenser family) that LLM summarization buys no quality and risks completion; explicitly flags small-window / weak models as untested, which is the Gemma-4B/32k gap.

#### SWE-Effi: SWE-Effi: Re-Evaluating Software AI Agent System Effectiveness Under Resource Constraints
- **Ref**: Fan et al. (Huawei, CUHK-SZ, KCL, Queen's), arXiv 2509.09853, Sep 2025, https://arxiv.org/abs/2509.09853
- **Contribution**: Resolve-rate metrics weighted by resource: AUC of cumulative-resolved vs tokens / (normalised) inference time / CPU time ("effectiveness under token budget", EuTB; under time budget). Five scaffolds (AutoCodeRover, OpenHands, SWE-agent, Agentless, Agentless-Mini) x three LLMs (GPT-4o-mini, Llama-3.3-70B, Qwen3-32B) on a SWE-bench subset.
- **Numbers**: Scaffold effectiveness is model-dependent: SWE-agent + Qwen3-32B 28% resolved (35.5 API calls, 440k input tokens) vs 10% with GPT-4o-mini; SWE-agent EuTB 21.8% (Qwen3-32B) vs 5.1% (GPT-4o-mini). "Token snowball": input tokens grow superlinearly with LLM calls. "Expensive failures": for SWE-agent + GPT-4o-mini an unresolved attempt uses >4x the resources of a resolved one (Table 3: 8,867k vs 1,865k tokens, 658 s vs 167 s total time, 192 vs 82 LLM requests). Clear trade-off between effectiveness under token budget and under time budget.
- **Admitted limitations / future work**: Sec. 5.3-6: suggests scaffolds stop when the snowball gets too large and "better memory abstraction" mitigates it; future work = progress-aware agents that detect stagnation and abort/redirect; subset-only evaluation; no thinking models, no <=32k setting.
- **Relevance**: Closest published thing to a time-budgeted SWE evaluation; shows failures dominate cost, which argues for budget-aware early stopping inside a 6-minute cap. Time is measured as wall-clock of hosted runs, not fixed per-task cap.

### 3. Learned memory and folding

#### MEM1: MEM1: Learning to Synergize Memory and Reasoning for Efficient Long-Horizon Agents
- **Ref**: Zhou et al. (SMART/NUS, MIT, Yonsei), arXiv 2506.15841 (NeurIPS 2025 workshop; ICLR 2026 poster), Jun 2025, https://arxiv.org/abs/2506.15841
- **Contribution**: RL (PPO-style with masked trajectories) trains a 7B agent to keep a constant-size "internal state" that is rewritten each turn and replaces all prior turns.
- **Numbers**: MEM1-7B vs Qwen2.5-14B-Instruct on 16-objective multi-hop QA: 3.5x better performance, 3.7x lower memory; at 16 objectives, 1.27x lower peak memory and 1.78x faster inference than the best non-collapsed baseline. Trained on 2-objective compositions, generalises to 16 objectives.
- **Admitted limitations / future work**: Sec. 5: assumes environments with well-defined verifiable rewards; open-ended/noisy-reward tasks left for future work. Tasks are QA/web shopping, not code.
- **Relevance**: A 7B model *trained* to compact; an untrained Gemma 4B/31B does not have this skill, so the summarizer-in-the-loop is the only option available here.

#### AgentFold: AgentFold: Long-Horizon Web Agents with Proactive Context Management (Folding)
- **Ref**: Ye et al. (Tongyi Lab, Alibaba), arXiv 2510.24699 (ICLR 2026), Oct 2025, https://arxiv.org/abs/2510.24699
- **Contribution**: Every step the agent emits a "folding" directive: granular condensation of the latest step or deep consolidation of a multi-step span, producing multi-scale state summaries; trained with SFT only.
- **Numbers**: AgentFold-30B-A3B 36.2% BrowseComp / 47.3% BrowseComp-ZH; context ~7k tokens after 100 turns, scales to 500 turns; on average 84k tokens (92%) smaller than ReAct (~7 GB memory saving per instance); context mostly <20k and non-monotonic (can undo dead ends).
- **Admitted limitations / future work**: Argues that step-wise full-history summarisation "risk[s] the premature and irreversible loss of crucial details"; extreme-turn scaling deferred "due to time constraints"; web-search only.
- **Relevance**: Evidence for lossless-first, selective compaction (keep recent step verbatim) vs the ADK approach of summarising nearly all at once. A 30B-A3B model can be a good fit for 32k only if trained for it.

### 4. 2026 evidence closest to the setting (tight windows, small models, time caps)

#### Bud-ContextCompact: Bud ContextCompact 2.0: Context Compaction for Agent Success and Accuracy with Small Language Models and Constrained Context Windows
- **Ref**: VG & PS (Bud), arXiv 2610.25516, 18 Oct 2026, https://arxiv.org/abs/2610.25516
- **Contribution**: A/B evaluation of compaction alone (everything else fixed) inside the Bud agent runtime: (a) recall questions over recorded agent sessions with 1.2B and 9B models, (b) 100 SWE-bench Verified tasks end to end with a 27B reasoning model on a 49K-token window (556 graded sessions), with threshold, wall-clock and 8B-model sub-studies. Summaries are checked for "critical-literal recall" before being applied.
- **Numbers**: Recall (16K budget): 1.2B model 0.335 compacted vs 0.247 truncated vs 0.176 with its full 32K history (p<0.001); 9B (32K budget) 0.577 vs 0.515 truncated (p=0.04). SWE-bench, 27B, 49K: long sessions 41% -> 53% resolved (+12.3 pp, 95% CI +1.6..+23.0, McNemar p=0.043), short sessions +1.7 pp (p=1.0); equal total tokens, 13% fewer tokens per solved task, +14% model time (compacted arm kept working on tasks the uncompacted arm abandoned when its window ran out). **Mechanism**: the dominant failure without compaction was "a reasoning turn exhausting the space the history left", not the history overflowing. **Wall-clock**: with 60 turns or 45 minutes per session the gain vanished (63/120 off vs 59/120 auto, -3.3 pp, p=0.48) because each summary took a median 161 s (p90 263 s) since the summariser is the agent's own reasoning model; auto sessions hit the 45-min limit 51 vs 39 times. **Threshold**: compaction at 24K threshold +13.9 pp on long pairs; at 48K it ran in only 4 of 50 sessions (no effect); default 0.8*B was between; "for reasoning models in tight windows a threshold around half the input budget worked". An 8B model on the same tasks submitted after ~10 turns at 5-8K tokens and never needed compaction. 134 applied compactions: mean critical-literal recall 1.000, each 24.7K -> 11.4K tokens with a 2.3K-token briefing.
- **Admitted limitations / future work**: Sec. 4.1 caveats: small-model results are single runs on 239 probes; harness layout changes moved all arms (full arm 0.63 -> 0.59). Sec. 6: summariser should be cheaper than the agent (reasoning off, smaller writer, or extractive fold) but "We did not measure these on agentic tasks"; accuracy transfers across hardware but time cost scales with hardware.
- **Relevance**: Nearest published match to the setting (small window, reasoning model, summary-based compaction, time cap) and it shows a null/negative result under a time budget when the summariser is slow; industry preprint, not peer-reviewed, 27B on 49K rather than 31B on 32k. Fires early (24K) works better than late, vs ADK's 14,336 of 32k (~44%), which is in the "early enough" regime.

#### AutoCompact: AutoCompact: Learning When to Compact Context in Long-Horizon Coding Agents
- **Ref**: Zhang et al., arXiv 2610.02163, 1 Oct 2026, https://arxiv.org/abs/2610.02163
- **Contribution**: Trains Qwen3-Coder-30B-A3B to call a `compact()` tool proactively (SFT on judge-corrected trajectories, then RL), compared with length-triggered compaction and other 2026 learned methods; evaluated on SWE-bench Verified and SWE-PolyBench Verified, at 256K and at a forced 16K window.
- **Numbers** (pass rate %, SWE-bench Verified / SWE-PolyBench Verified, avg of 3 runs): Full-history 256K baseline 30.4 / 19.5; **fixed length-triggered compaction at 16K 28.8 / 18.6** (i.e. -1.6 / -0.9 vs no compaction); CompactionRL (16K) 32.7 / 19.8; SelfCompact (rubric) 31.7 / 20.6; SWE-Compressor 31.0 / 20.1; AutoCompact-SFT 32.2 / 21.7; AutoCompact 39.6 / 24.5. Ignoring the same trained model's compaction calls lowers pass rate.
- **Admitted limitations / future work**: Sec. 5: RL used 32K-token sequences vs 256K eval; single scaffold; Codex and Claude Code use length-triggered auto-compaction and learned proactive triggers could be combined with them.
- **Relevance**: Independent numbers saying length-triggered compaction (the ADK policy) is neutral-to-negative for a 30B coder, while the *timing and content* of compaction are where gains come from. Their summarizer is the agent itself and sees tool outputs.

#### CompactionRL: CompactionRL: Reinforcement Learning with Context Compaction for Long-Horizon Agents
- **Ref**: Li et al. (Tsinghua / Z.AI), arXiv 2607.05378 (v2 1 Oct 2026), https://arxiv.org/abs/2607.05378
- **Contribution**: RL that jointly optimises task actions and summary actions across compaction boundaries (cross-segment GAE); GLM-4.5-Air 106B-A12B and GLM-4.7-Flash 30B-A3B.
- **Numbers**: GLM-4.5-Air 66.4% SWE-bench Verified (+6.6 over base with inference-time compaction), 26.2% Terminal-Bench 2.0 (+4.9). GLM-4.7-Flash 56.0% (+5.5), 20.2% TB 2.0 (+6.7). **Summariser quality** (Table 1): same execution agent GLM-4.7-Flash, only the summary agent varied: Qwen3.5-27B summaries 55.5% (1.010 summaries/trace), GLM-4.7-Flash itself 50.5% (1.075), Qwen3-30B-A3B 49.0% (1.126): a 6.5-pt swing from the summarizer alone. RL-trained summaries grow longer and more detailed (retaining paths, errors, failed commands).
- **Admitted limitations / future work**: gains do not consistently transfer to single-window inference; cross-segment GAE is an approximation.
- **Relevance**: Direct evidence that compaction outcome depends on summariser quality and on what it keeps (paths, error messages, failed commands, partial solutions); the ADK summarizer sees none of the tool outputs or diffs.

#### SWE-MeM: SWE-MeM: Learning Adaptive Memory Management for Long-Horizon Coding Agents
- **Ref**: Gao et al. (CUHK), arXiv 2606.28434, 26 Jun 2026, https://arxiv.org/abs/2606.28434
- **Contribution**: Memory tool the agent calls to decide when/what/how to compress given remaining budget; SFT + Memory-aware GRPO; OpenHands scaffold with a 32,768-token limit for data collection, SFT, RL and eval; models Qwen3-4B-Instruct-2507 and Qwen3-Coder-30B-A3B.
- **Numbers** (SWE-bench Verified resolve %): Qwen3-4B ReAct 7.0 (128k) / **5.2 (32k)**; SWE-MeM SFT 41.6, SFT+RL 43.4 (32k) (cf. SWE-Master-4B 33.4 at 128k). Qwen3-Coder-30B-A3B ReAct 51.6 (256k) / **38.6 (32k)**; SWE-MeM workflow-only (untrained, with a proprietary LLM making compression decisions) 58.4; SFT 58.8; SFT+RL 60.2 at 32k, with 94.7% of the base ReAct token use but 123.5% of its steps. Baselines at same table: threshold-compression summary agent 53.8 (32B, 64k, 204% tokens) / 55.0 (Seed-OSS-36B, 32k); Context Folding 58.0; SWE-Compressor 57.8.
- **Admitted limitations / future work**: No dedicated limitations section found in the text I extracted; trajectory synthesis relies on GPT-5.1; evaluated only on SWE-bench Verified at one window size.
- **Relevance**: The only SWE-bench numbers for a 4B-class model at 32k: untrained it is almost zero (5.2%), 32k costs the 30B model 13 points (51.6 -> 38.6) before any compaction; gains here come from trained policies, not from off-the-shelf summarisers.

#### CAT/SWE-Compressor: Context as a Tool: Context Management for Long-Horizon SWE-Agents
- **Ref**: Liu et al., arXiv 2512.22087, Dec 2025, https://arxiv.org/abs/2512.22087
- **Contribution**: CAT: context maintenance is a callable tool over a structured workspace (stable task semantics + condensed long-term memory + high-fidelity short-term interactions); SWE-Compressor (Qwen2.5-Coder-32B) trained with offline trajectory retrofitting.
- **Numbers**: SWE-bench Verified: ReAct agent 49.8, threshold-compression summary agent 53.8 (uses 204% of base-model tokens in SWE-MeM's accounting), SWE-Compressor 57.6.
- **Admitted limitations / future work**: Claims append-only and passively triggered compression cause "context explosion, semantic drift, and degraded reasoning"; no limitations section extracted; 64k window.
- **Relevance**: Establishes the "high-fidelity short-term + condensed long-term" structure; ADK keeps only the last ~5 events at full fidelity.

#### SWE-Pruner: SWE-Pruner: Self-Adaptive Context Pruning for Coding Agents
- **Ref**: Wang et al., arXiv 2601.16746 (v4 May 2026), https://arxiv.org/abs/2601.16746
- **Contribution**: A 0.6B "neural skimmer" prunes file reads line by line, guided by an agent-written goal hint, at the tool-output boundary rather than the history.
- **Numbers**: Read operations account for 76.1% of token cost (Mini-SWE-Agent, Claude Sonnet 4.5, SWE-bench Verified). 23-38% token reduction on SWE-bench Verified with success +1.2 to +1.4 pp (GLM-4.6: 55.4 -> 56.6; Sonnet 4.5 -39% tokens); up to -26% rounds; up to 14.84x compression on single-turn LongCodeQA.
- **Admitted limitations / future work**: Python only; possible training-data leakage controls; skimmer adds marginal latency.
- **Relevance**: Where the tokens are (file reads) and a cheap way to shrink them before compaction is needed; irrelevant if the session is time-limited by decode, not prefill.

#### Harness-Design: An Empirical Study of Harness Design for Coding Agents
- **Ref**: Fan et al., arXiv 2609.20804, Sep 2026, https://arxiv.org/abs/2609.20804
- **Contribution**: Fixed-loop lightweight harness; 176 matched settings across 4 models (Nemotron-3 30B/120B/550B, Mistral-Medium-3.5-128B), SWE-bench Verified + Terminal-Bench 2.1, five context-management tiers at 32k/64k/96k/128k budgets: T0 none (terminates on overflow), T1 elide stale tool observations, T2 elision + recoverable store (`recall_event`), T3 LLM summary only, T4 staged (elide at soft threshold B1, summarise oldest middle events at hard threshold B2; preamble and >=2 recent turns verbatim).
- **Numbers**: At 32k with no management (T0) all four models are at roughly 6-13% on SWE-bench (table text garbled by PDF extraction) vs 20.6-23.8 (30B), 39.6-43.0 (120B), 51.4-58.4 (550B), 63.2-66.2 (Mistral) with any managed tier, all significant by McNemar BH-FDR. At 32k, summary-only (T3) vs elision-only (T1): 23.8 vs 20.6 (30B), 39.6 vs 43.0 (120B), 58.4 vs 51.4 (550B), 63.2 vs 64.4: no consistent winner. Benefit shrinks as the window grows (128k: managed ~ T0 for most models). Recoverable elision (recall tool) "is rarely invoked and does not improve accuracy" (Nemotron 30B at 32k T2 averages 4.3 recalls/task and scores 3.4% below T1 on TB). T4 gives best efficiency.
- **Admitted limitations / future work**: One threshold policy with fixed settings; planning/action-space ablated only at 128k/T4; each setting run once per task; Terminal-Bench has only 89 tasks so many contrasts are not significant.
- **Relevance**: Confirms that at 32k the main benefit of management is simply avoiding overflow termination (matches "a context overflow kills the session"); elision-then-summary beats summary alone on efficiency, and masking is a strong cheap baseline at 32k as well.

### 5. Wall-clock and time-budgeted agents

#### On-the-Clock: On the Clock: Towards Punctual and Productive Time-Budgeted AI Agents
- **Ref**: arXiv 2610.10833 (NeurIPS 2026 Workshop on Resource-Aware Agentic AI), Oct 2026, https://arxiv.org/abs/2610.10833
- **Contribution**: Small agents under explicit wall-clock budgets: Qwen3.6-27B on 5 MLE-Bench Lite competitions and Qwen3-4B on Zork I. Compares prompt-only budgets, harness timing injection, enforcement hooks (shorten/block long commands), and GRPO with time-shaped rewards.
- **Numbers**: Prompt-only: Qwen3.6-27B "runs for roughly ten minutes regardless of the stated budget" (Dog Breed task: on-time 35% at 8 min, 83% at 15 min, 100% at 60 min; elapsed 12.9 +/- 12.6 min at 8-min budget). Harness-injected timing "substantially improves budget adherence without measurable loss in performance"; enforcement tightens further at small quality cost (shortening a command's time limit kept most quality and gave 90% valid submissions; blocking commands reduced valid submissions). GRPO gets near-perfect adherence on Zork I and generalises to unseen budgets, but task score does not improve over the untrained harness on MLE-Bench, and the policy pads extra time with repeated actions and collapses to the shortest-budget strategy.
- **Admitted limitations / future work**: Sec. 5: strategy collapse across budgets, memorisation of a walkthrough in fixed Zork, budget adherence through invalid actions; ML-engineering and text games only, not SWE.
- **Relevance**: Direct evidence for the fixed-6-minute design: a prompt-only time budget is not respected by small agents, but harness-side timers/enforcement are cheap and loss-free. Closest work to "wall-clock budget per task" but not a SWE benchmark.

#### Timely-Machine: Timely Machine: Awareness of Time Makes Test-Time Scaling Agentic
- **Ref**: Ma et al., arXiv 2601.16486, 23 Jan 2026, https://arxiv.org/abs/2601.16486
- **Contribution**: Redefines test-time compute as wall-clock time when tool latency decouples time from token count; Timely-Eval benchmark (high-/low-frequency tool calls, time-constrained reasoning) and Timely-RL (SFT cold start + RL; TimelyLM-8B).
- **Numbers**: With short tool latency smaller models can beat larger ones by doing more interaction rounds; as latency grows the large model's higher interaction quality wins; "existing models fail to adapt reasoning to time budgets"; TimelyLM-8B improves on Qwen3-8B across Timely-Eval (e.g. 36.0 -> 48.5 and 5.2 -> 29.5 on two columns of the main table).
- **Admitted limitations / future work**: Limitations: text-only tasks, multi-agent latency not handled, accuracy gains vary with benchmark difficulty; future work on balancing time constraint vs performance.
- **Relevance**: Supports the intuition that at 30 tok/s a small model's advantage is only more steps per minute, and the tipping point depends on tool latency; no SWE tasks.

#### AgentTime: AgentTime: Can Agents Estimate and Control Their Own Runtime?
- **Ref**: Ofengenden & Andriushchenko, arXiv 2610.09944, 7 Oct 2026, https://arxiv.org/abs/2610.09944
- **Contribution**: 222 tasks from 18 sources (coding, computer use, research); instructs an agent in its native harness to work for a requested duration (about a minute to days), predict its runtime, and estimate elapsed time.
- **Numbers**: Typical deviation from the requested runtime 2.9x (one Claude Code agent) vs 1.2x (one Codex agent); 14 of 158 reviewed runs of one agent explicitly slept after appearing to finish; runtime forecasts overestimate natural runtimes; removing temporal information more than doubles deviation in retrospective estimation. 3,442 attempts, ~1,700 agent-hours.
- **Admitted limitations / future work**: Sec. 6: single run per task/duration, three agents from two labs, one instruction wording at max reasoning effort; runtime depends on serving speed.
- **Relevance**: Frontier agents with native harnesses cannot reliably self-time without clocks; supports giving the Gemma agent a harness-side deadline rather than relying on prompts.

#### Real-Time-Deadlines: Real-Time Deadlines Reveal Fragile Temporal Adaptation in LLM Strategic Dialogues
- **Ref**: Sehgal et al., arXiv 2601.13206 (EMNLP 2026), Jan 2026, https://arxiv.org/abs/2601.13206
- **Contribution**: Paired-agent negotiations under 240-360 s wall-clock deadlines; compares initial-deadline-only against per-turn remaining-time updates and presentation variants.
- **Numbers**: Remaining-time feedback raises deal closure from 4% to 32% for GPT-5.1-chat-latest and offer acceptance more than sixfold; near-perfect closure under turn limits; qualitative urgency cues can beat numeric countdowns; repeated reminders do not consistently help; "fragile, model-dependent, and sensitive to how temporal constraints are presented".
- **Admitted limitations / future work**: negotiation domain only; effects vary by model.
- **Relevance**: A "budget-awareness prompting" result with a 4% -> 32% effect for wall-clock, in a non-coding domain.

#### SWE-Effi and BATS (see sections 2 and 3)
Cross-reference: SWE-Effi measures resolve-vs-time curves; BATS names latency as unaddressed.

### 6. Token economics of coding agents

#### Token-Spend: How Do AI Agents Spend Your Money? Analyzing and Predicting Token Consumption in Agentic Coding Tasks
- **Ref**: Bai et al., arXiv 2604.22750 (v3 2 Oct 2026), https://arxiv.org/abs/2604.22750
- **Contribution**: First systematic study of token consumption: 8 frontier LLMs on SWE-bench Verified trajectories; also whether models can predict their own token use.
- **Numbers**: Agentic tasks consume ~1000x more tokens than code reasoning/chat, input tokens dominate; same-task runs differ up to 30x in total tokens; accuracy peaks at intermediate cost and saturates; Kimi-K2 and Claude-Sonnet-4.5 use >1.5M more tokens than GPT-5 on average; self-predicted token use correlates at most r=0.39 and systematically underestimates.
- **Admitted limitations / future work**: eight models only; trajectory collection is expensive.
- **Relevance**: Support for early stopping/step caps: more tokens != more accuracy. Frontier models only.

#### Token-Not-Cost: Token Reduction Is Not Cost Reduction
- **Ref**: Weinberger et al., arXiv 2607.12161 (v5 Aug 2026), https://arxiv.org/abs/2607.12161
- **Contribution**: Controlled test of three tool-output compression tools against unmodified Claude Code, measuring provider-billed cost, success, cache traffic, behaviour.
- **Numbers**: Largest setup cut delivered tool-output tokens by 38.4% yet raised billed cost by 6.8%; correlation between token reduction and cost reduction r=0.15; compression changes trajectories (more retrieval, diagnosis, testing, turns); aggressive compression reduced successful patch application on a SWE-bench Go subset.
- **Admitted limitations / future work**: Sec. 14: one harness (Claude Code), one provider's cache and July-2026 prices, baseline success 96-98% so small effects are undetectable.
- **Relevance**: Compaction rewrites the prefix and breaks KV/prefix cache; this matters for a local 31B server with prefix caching, though with local serving the cost is latency rather than dollars.

#### Context-Contamination: Why Retrying Fails: Context Contamination in LLM Agent Pipelines
- **Ref**: Yang, arXiv 2605.08563, 8 May 2026, https://arxiv.org/abs/2605.08563
- **Contribution**: Formal model: a failed attempt left in context raises per-step error from eps0 to eps1; closed-form pass@K, optimal pipeline depth T* = sqrt(B log(1/(1-eps1))/log(1/(1-eps0))), clean-restart dominance.
- **Numbers**: On SWE-bench Verified data the IID model overestimates pass@3 by 17.4 pp (98.6% vs 81.2%); CCRM fits with error <0.001 and implies eps1/eps0 = 7.1.
- **Admitted limitations / future work**: theoretical model fit to a single dataset; no LLM experiments with compaction; one author.
- **Relevance**: Argues failed-attempt text left in context is harmful; a summary carrying forward "what failed" could either help or contaminate. Weak evidence (theory fit to aggregate data).

### 7. What compaction drops and what it costs (2026 empirical studies)

#### Beyond-Token-Savings: Beyond Token Savings: A Systematic Study of Context Compression in LLM Agents
- **Ref**: Satish, Sinha et al., arXiv 2609.32961, 26 Sep 2026, https://arxiv.org/abs/2609.32961
- **Contribution**: Isolates what/when/how-much of compression in a modified mini-swe-agent: 65 policies x 3 locally served open-weight models (Qwen3.5-35B-A3B, Devstral-Small-2-24B, GLM-4.7-Flash; vLLM, agent model also summarises by default) on SWE-bench Verified and Terminal-Bench 1.0, ~35,000 runs, 3 repeats each; primitives = truncation, tool-result clearing (TRC), summarisation (SU), structured summaries, stacked variants; trigger thresholds tight/primary/loose (10K/15K/20K for Qwen on SWE-bench).
- **Numbers**: Every policy cuts tokens (0.4-0.7x on SWE-bench) but success ranges from -11.0 pp to +0.7 pp vs full context; TRC mostly matches full context (tokens 0.57x, latency 0.79x, billed cost 0.71x; resolve 53.7%), whereas plain LLM summarisation (SU) at 0.59x tokens loses 11.0 pp. Policies using ~0.6x tokens still need 0.79-1.0x latency; on Terminal-Bench policies using ~1/3 of the tokens take 1.2-1.8x as long and 11 of 12 lose 5-13 pp. **Summarisation calls account for 28-46% of solved-run wall-clock time** for the four summarisation primitives. Summariser sensitivity (25 tasks, Qwen agent): SU falls from 53.3% (self-summary) to 37.3% with a Qwen3.5-9B summariser and **28.0% with a Gemma-4-12B summariser**, whereas stacked TRC+SU stays near its 68.0% baseline (62.7% / 66.7%); smaller summarisers did not reduce latency.
- **Admitted limitations / future work**: Sec. 5 argues for evaluating compression by "the executions it enables"; policies must be tailored to task/model/workload; note Qwen was served with prefix caching disabled (App. A) and subsets of 25 tasks for the summariser study; no dedicated limitations section found.
- **Relevance**: Strongest direct evidence against a summary-only policy for 24-35B local models and for slow summarisation inside a time cap; shows rule-based clearing of tool results first beats summarising everything. Also the only study here that reports end-to-end latency.

#### Reacquisition-Cost: What Does Context Compression Cost an Agent? Interaction Costs Unrevealed by Task-Completion Metrics
- **Ref**: Liu, arXiv 2608.16370, 17 Aug 2026, https://arxiv.org/abs/2608.16370
- **Contribution**: Controlled protocol in a deterministic planning environment (24-turn horizon, 3 models): compression severity, dropping vs fact-preserving operator, oracle restoration of dropped state, decomposition of tool calls into retrieval vs execution.
- **Numbers**: Retrieval calls rise in all 6 model-regime comparisons and explain almost all added interaction (5 of 6 significant after Holm); at the 5x compression point completion is unchanged in every cell. GPT-5.5: completion 80% -> 85% (p=1.0) while retrieval calls rise 21.0 -> 63.9 (p=.002). Replacing retained state with irrelevant content raises retrieval 57% (p<.001) with no significant completion change. In ALFWorld, sliding compression produced no retrieval surge, so the effect is environment-dependent.
- **Admitted limitations / future work**: Synthetic deterministic planning environment, 24-turn horizon, single-author, not SWE.
- **Relevance**: Mechanism for why compaction under a step cap (30 tool calls) can cost success: dropped state must be re-read with tool calls that count against the cap, which completion-only evaluations hide.

#### TRACE: Towards Reliable Context Compression for Long-Horizon Agents: An Empirical Study of Execution Instability
- **Ref**: Min et al., arXiv 2608.06503 (v2 14 Oct 2026), https://arxiv.org/abs/2608.06503
- **Contribution**: Preliminary study showing recurrent compression weakens the influence of recent interactions (more blocked actions, repeated exploration, run-to-run instability); TRACE evaluates each compaction event by paired closed-loop continuations from the same state and optimises the natural-language compression prompt with frozen models.
- **Numbers**: AppWorld only; improvements in task performance, multi-run reliability and context-execution efficiency over existing compression baselines (no SWE numbers).
- **Admitted limitations / future work**: Self-described "preliminary empirical study", single environment, initial results.
- **Relevance**: Names the failure mode "repeats exploration after a summary", which would burn a 30-call budget.

#### Brittle-Memory: Reclaim Evaluation: A Lossy Memory Is Worse Than an Empty One
- **Ref**: Kwon, arXiv 2606.25449 (v5 Jul 2026), https://arxiv.org/abs/2606.25449
- **Contribution**: Shows compression that keeps a conclusion but drops its derivation makes models re-emit stale values confidently instead of abstaining; source-first policy (keep recomputable source, drop re-derivable conclusion) restores correctability at equal budget; an 8B and a frontier model "wall in the same place".
- **Numbers**: Judge-free exact recovery tests on three deployed memory systems, MultiWOZ and tau-bench (numbers in 23 tables, not extracted).
- **Admitted limitations / future work**: Maps where the fix fails; effect compounds through memory loops; not coding-specific.
- **Relevance**: Conceptual support for "summaries of diffs without diffs are worse than nothing": relevant when the summarizer drops tool outputs and edits.

#### ICLR-Forget: When Can Agents Forget Their Reasoning? Interaction-Aware Compression for Long-Horizon Reasoning
- **Ref**: Wang et al., arXiv 2609.29875, 24 Sep 2026, https://arxiv.org/abs/2609.29875
- **Contribution**: Training-free ranking of historical reasoning blocks by frozen proxy entropy, dropping reasoning while keeping actions, tool calls and observations.
- **Numbers**: WorkBuddyBench (260 tasks): reward 0.699 -> 0.718 with input/output/cache-read tokens -25.5% / -14.4% / -33.3%; "trajectory amplification": local deletions can change total computation nonlinearly; historical reasoning is replaceable once derived state is externalised into code, files or tool outputs.
- **Admitted limitations / future work**: not a SWE benchmark; training-free proxy models.
- **Relevance**: With thinking on, old thinking blocks are the cheapest thing to drop; evidence that dropping reasoning but keeping observations is safe.

#### SWE-AGILE: SWE-AGILE: A Software Agent Framework for Efficiently Managing Dynamic Reasoning Context
- **Ref**: Lian et al., arXiv 2604.11716, 13 Apr 2026, https://arxiv.org/abs/2604.11716
- **Contribution**: Sliding window of detailed reasoning (window size random in [2,5]) plus compressed "Reasoning Digests" for older thoughts, avoiding both context explosion and re-reasoning; 7B-8B models, 2.2k trajectories.
- **Numbers**: Claims a new standard for 7B-8B on SWE-bench Verified; 14B SFT variant 30.06% on Verified; 8B reaches 14.77% on SWE-bench Lite vs SWE-smith-7B 11.7% and R2E-Gym 11.0%.
- **Admitted limitations / future work**: window size randomised and its effect not analysed ("Limitation" section).
- **Relevance**: Small-model recipe that treats thinking as a managed context component, directly the thinking-on + 32k problem; but trained.

#### ARC: Addressable Recall Compaction for Long Context-Window Control in AI Agents
- **Ref**: Ichikawa et al., arXiv 2607.25066, Jul 2026, https://arxiv.org/abs/2607.25066
- **Contribution**: Append-only ID-addressable log of tool observations; compaction replaces old observations with compact citations the agent can dereference. Qwen3-8B at 16k and Qwen3-32B at 32k.
- **Numbers**: Needle-in-a-haystack exact-answer accuracy 99.40% vs 88.12% for the best baseline; LongBench-v2 Hard 29.97% vs 28.25% (margin 1.6-2.3 pp, ARC 27.47% at 8B / 32.47% at 32B); lower serving time and HBM traffic under their hardware-cost model.
- **Admitted limitations / future work**: Margin narrows on tasks requiring synthesis since perfect recall can still give a wrong answer; not an agentic coding benchmark.
- **Relevance**: One of the few 16k/32k small-model compaction studies; but contrasts with Harness-Design finding that recall tools are rarely used by models.

#### DTOC: Dynamic Tool Output Compression for Adaptive Context Management in AI Agents
- **Ref**: arXiv 2609.26121 (Discovery Science 2026), Sep 2026, https://arxiv.org/abs/2609.26121
- **Contribution**: Reversible placeholders for tool outputs, with originals in external memory and on-demand restoration inside a ReAct loop; evaluated on DeepSWE.
- **Numbers**: Model-dependent: Sonnet 4.6 and GPT-5.4 input tokens -10.3% / -12.7%, steps -2.4% / -32.3%, solve rate 2.5x / 1.5x, cost per solved task 3x / 3.5x lower; GPT-5.5 doubles solve rate at half cost; other models no solve-rate change and worse cost. Disable-only (non-reversible) compression degraded performance.
- **Admitted limitations / future work**: mixed results for non-"responsive" models.
- **Relevance**: Reversibility helps strong models and not others, the same split as in Harness-Design; a Gemma 4B may not use restore tools.

#### Chroma-Context-Rot: Context Rot: How Increasing Input Tokens Impacts LLM Performance
- **Ref**: Hong, Troynikov, Huber (Chroma), technical report, 14 Jul 2025, https://www.trychroma.com/research/context-rot
- **Contribution**: 18 LLMs (Claude, GPT, Gemini, Qwen3 families) on needle-in-haystack variants (needle-question similarity, distractors, haystack topic/structure), repeated words, and LongMemEval focused (~300 tokens) vs full (~113k tokens) prompts (306 prompts).
- **Numbers**: Performance falls with input length even on simple tasks; lower needle-question similarity degrades faster; adding distractors lowers accuracy and one distractor already drops below the needle-only baseline; shuffled haystacks beat coherent ones across all 18 models; every model scores significantly higher on focused than full LongMemEval prompts; Qwen3-8B begins emitting random words around 5,000 repeated words, Gemini around 500-750; needle position (11 positions) had no notable effect. Exact per-model values are only in charts.
- **Admitted limitations / future work**: Real tasks harder so degradation likely worse; input length and difficulty hard to disentangle; mechanisms unexplained; two haystack topics only.
- **Relevance**: Background for why shorter active contexts help even below the window limit (Qwen3-8B degrades early), though non-agentic and not measured for Gemma.

#### Anthropic-Context-Engineering: Effective Context Engineering for AI Agents (blog)
- **Ref**: Anthropic engineering blog, 2025 (date not shown on fetched page), https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- **Contribution**: Practice guide: context is a finite "attention budget"; compaction = summarise near the limit and restart (Claude Code keeps architectural decisions, unresolved bugs and implementation details plus the five most recently accessed files); tool-result clearing is the "safest lightest touch" form; structured note-taking outside context; sub-agents return 1,000-2,000-token summaries of tens of thousands of tokens of exploration.
- **Numbers**: None for compaction, note-taking or sub-agents (only "substantial improvement" on research tasks, unquantified).
- **Admitted limitations / future work**: "overly aggressive compaction can result in the loss of subtle but critical context whose importance only becomes apparent later"; advice to tune the compaction prompt "to maximize recall" first, then precision; runtime exploration is slower.
- **Relevance**: The grey-literature origin of the ADK-style policy; its own advice (keep recent files, clear tool results first) differs from ADK's text-only summariser.

#### Manus: Context Engineering for AI Agents: Lessons from Building Manus (blog)
- **Ref**: Manus team, blog, 2025 (author byline not verified), https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus
- **Contribution**: KV-cache hit rate is "the single most important metric" (average input:output ratio ~100:1; Claude Sonnet cached $0.30/MTok vs uncached $3/MTok); keep prefix stable and append-only; compression "always designed to be restorable" (keep URL/path, drop content; filesystem as context); keep failed actions in context; rewrite todo.md to keep goals in recent attention; ~50 tool calls per typical task.
- **Numbers**: no measured hit rates or ablations ("Stochastic Graduate Descent").
- **Admitted limitations / future work**: explicitly "not universal truth"; "any irreversible compression carries risk".
- **Relevance**: For a local server, prefix-cache reuse is wall-clock (prefill) rather than dollars: compaction invalidates the cache from the rewritten point onward.

#### Cognition: Don't Build Multi-Agents (blog)
- **Ref**: Cognition (Walden Yan per later coverage), blog, mid-2025, https://cognition.com/blog/dont-build-multi-agents
- **Contribution**: Principles "Share context, and share full agent traces" and "Actions carry implicit decisions"; suggests a dedicated (possibly fine-tuned smaller) LLM to compress long action/conversation histories into key details, events and decisions; admits this is "hard to get right" and "You will still eventually hit a limit".
- **Numbers**: none.
- **Admitted limitations / future work**: no failure analysis of summarisation provided; Apr 2026 follow-up says multi-agent works if writes stay single-threaded (from search snippet, not opened).
- **Relevance**: Argues against sub-agent context isolation for write-heavy tasks; supports a single agent with a dedicated compressor trained on what to keep.

#### SWE-agent-history: SWE-agent history processors (documentation)
- **Ref**: SWE-agent docs, "History Processors", https://swe-agent.com/latest/reference/history_processor_config/ (accessed 2026-10-22)
- **Contribution**: `LastNObservations(n, polling)` elides all but the last n observations with "Old environment output: (n lines omitted)"; tag-based keep/remove; `RemoveRegex` (default strips `<diff>.*</diff>`, keep_last); cache-control processor for Anthropic.
- **Numbers**: none; notes the processor "breaks prompt caching" because history changes every query, with `polling` as partial workaround; says most current models fit enough context that it is often unnecessary; SWE-agent now maintenance-only (mini-swe-agent recommended).
- **Admitted limitations / future work**: the cache-breaking note.
- **Relevance**: The reference implementation of observation masking evaluated in Complexity Trap (M=10).

### 8. Budget awareness, early stopping, trajectory reduction, latency

#### BATS-v2-SWE: BATS v2 (COLM 2026), Appendix C.3 SWE-bench Verified check
- **Ref**: Liu et al., arXiv 2511.17006v2 (Aug 2026), HTML App. C.3, https://arxiv.org/html/2511.17006v2
- **Contribution**: Budget Tracker (same prompt as main paper, inserted after each tool response) added to mini-swe-agent with Gemini-3-Flash-Preview on all 500 SWE-bench Verified tasks, with a global tool-call budget.
- **Numbers** (resolve %, mean tool calls, cost): budget 50: baseline 36.8% (46.0 calls, 18.50 cents) vs +Tracker 55.4% (45.7 calls, 18.88 cents) = +18.6 pp; budget 60 baseline 53.2%; budget 70: baseline 63.0% (53.6 calls) vs +Tracker 70.0% (55.1 calls). Tracker at 50 beats baseline at 60 on every axis (-9.9% calls, -7.5% cost, +2.2 pp).
- **Admitted limitations / future work**: single model (Gemini-3-Flash-Preview), single scaffold, single run per cell as reported; mechanism not isolated (the text does not say whether the gain is from submitting before the cap or from better exploration).
- **Relevance**: The only budget-awareness measurement on SWE-bench with a hard tool-call cap that I found; the effect is largest when the cap binds (50 calls) which is the ~30-call regime here. Unknown for small models and for step caps that coincide with a time cap.

#### BAGEN: BAGEN: Are LLM Agents Budget-Aware?
- **Ref**: Lin et al., arXiv 2606.00198, 29 May 2026, https://arxiv.org/abs/2606.00198
- **Contribution**: Formalises budget-awareness as progressive interval estimation (predict upper/lower bound on remaining budget and alert when completion is unlikely); rollout-replay scoring on Sokoban, Search-R1, SWE-bench (cap 160 turns, 64 rollouts per model), and a Warehouse environment with cost/time/occupancy budgets; five frontier agents; Qwen-7B estimators trained with SFT+RL on Sokoban.
- **Numbers**: Budget-awareness correlates weakly with task success (r=0.35); frontier models are over-optimistic and keep spending on tasks unlikely to succeed; early stopping saves 28-64% of tokens on failed trajectories; interval-coverage caps at 47% after SFT+RL.
- **Admitted limitations / future work**: Extending training to more scales/environments, closing the loop beyond early stop, fungible budgets across dimensions; interval estimation "the central open problem".
- **Relevance**: Evidence that agents (without help) do not know when they will run out; early stop is the actionable lever. Estimators were trained only on Sokoban.

#### AgentDiet: Reducing Cost of LLM Agents with Trajectory Reduction
- **Ref**: Xiao et al. (FSE 2026), arXiv 2509.23586 (v2 Mar 2026), https://arxiv.org/abs/2509.23586
- **Contribution**: Inference-time removal of useless / redundant / expired information in a coding agent's trajectory by a separate reflection LLM looking at a sliding window (e.g. GPT-5 mini reducing a Claude 4 Sonnet trajectory); implemented on Trae Agent; found from 100 inspected SWE-bench Verified trajectories that waste is widespread.
- **Numbers**: Input tokens -39.9% to -59.7%, total computational cost -21.1% to -35.9%, with the Pass% within -1.0 to +2.0 points of the original and no increase in steps (2 LLMs, 2 benchmarks). Reflection overhead 5-10% of cost. A simple `erase` tool the agent could call was ignored even by Claude 4 Sonnet and Gemini 2.5 Pro despite explicit prompts (so agent-initiated compaction fails; external reduction works).
- **Admitted limitations / future work**: Sec. 6: only Trae Agent, about US$2000 of experiments; the reflection LLM could be a cheaper custom model; hyperparameters could adapt to task difficulty; possible data leakage.
- **Relevance**: A content-aware, per-step, tool-output-aware reducer (not threshold summarisation) that preserves success, but it uses frontier models and an extra LLM call per step, which in a 30 tok/s setting costs wall-clock.

#### ReSum: ReSum: Unlocking Long-Horizon Search Intelligence via Context Summarization
- **Ref**: Wu et al., arXiv 2509.13313 (v3 Mar 2026, ICML), https://arxiv.org/abs/2509.13313
- **Contribution**: Plug-and-play periodic summarisation tool for web agents; ReSum-GRPO with advantage broadcasting across segmented trajectories.
- **Numbers**: +4.5% over ReAct training-free, +8.2% more with ReSum-GRPO; WebSailor-3B goes 8.2% -> 20.5% Pass@1 on BrowseComp-zh with ReSum-GRPO; still helps with a 128k context; plain GRPO "fails to enable agents to master summary-conditioned reasoning".
- **Admitted limitations / future work**: Conclusion: current summarisation is rule-based and external; future work needs autonomous summarisation and "quality control to ensure the preservation of long-range dependencies".
- **Relevance**: Evidence on 3B-class agents: untrained agents do not reason well over summaries, i.e. a 4B Gemma may need adaptation to benefit.

#### SLIM: Lost in the Maze: Overcoming Context Limitations in Long-Horizon Agentic Search
- **Ref**: Yen et al. (Princeton, Samaya AI), arXiv 2510.18939 (v2 Jul 2026, ICML 2026), https://arxiv.org/abs/2510.18939
- **Contribution**: Shows popular agentic-search frameworks fail on >50% of long-trajectory samples mainly from context-window, tool-budget or early-stop failures; SLIM = separate search/browse tools + periodic summarisation.
- **Numbers**: o3 + SLIM 56% BrowseComp and 33% HLE, +8 and +6 points over the best open-source frameworks with 4-6x fewer tool calls; GLM-4.7-Flash + SLIM +10 points over Search-o1 on BrowseComp at a third of the cost.
- **Admitted limitations / future work**: web-search domain; the paper builds an automated trajectory-error taxonomy (no limitations section extracted).
- **Relevance**: >50% of failures in long agent runs come from context/budget mismanagement, the same failure class as an ADK overflow kill.

#### Speculative-Actions: Speculative Actions: A Lossless Framework for Faster Agentic Systems
- **Ref**: Ye et al. (Columbia), arXiv 2510.04371 (ICLR 2026 oral), https://arxiv.org/abs/2510.04371
- **Contribution**: A fast Speculator guesses next actions, executed in parallel with the slow Actor; results committed only if the guess matches (lossless); cost-latency analysis for speculative breadth.
- **Numbers**: up to 55% next-action prediction accuracy, up to 20% latency reduction (gaming, e-commerce, web search; lossy OS extension).
- **Admitted limitations / future work**: truncating context to a fixed window or disabling exploration after convergence "left for future work"; tested in four non-SWE environments.
- **Relevance**: The only parallel/speculative result found; gains need cheap speculators and idempotent actions; for a single local GPU decode-bound at 30 tok/s a second model would compete for the same device.

#### CacheWise-Continuum: KV-cache serving for coding agents
- **Ref**: Tiwari et al., CacheWise, arXiv 2606.16824, 15 Jun 2026, https://arxiv.org/abs/2606.16824 ; Continuum, arXiv 2511.02230 (Nov 2025), https://arxiv.org/abs/2511.02230
- **Contribution**: Coding-agent sessions reuse large prefixes and create sustained KV pressure; CacheWise (vLLM) does prefix-aware scheduling and reuse-aware eviction from tool-call metadata; Continuum pins KV during tool calls with a time-to-live.
- **Numbers**: CacheWise: up to 2-2.6x fewer KV evictions, up to 3.5x faster total session completion on collected traces. Continuum: >8x average job-completion improvement on SWE-Bench/BFCL/OpenHands traces with Llama-3.1 8B/70B, Gemma-3 12B, GLM-4.5 355B.
- **Admitted limitations / future work**: multi-session serving scenarios, not single-user local; neither studies compaction rewriting the prefix.
- **Relevance**: Confirms that prefix reuse is the main latency lever in agent loops; a compaction that rewrites the prompt invalidates the reusable prefix (the prefill cost of this is not measured in these papers).

### 9. Long-context degradation, thinking budgets, time-aware harnesses, memory

#### Lost-in-the-Middle: Lost in the Middle: How Language Models Use Long Contexts
- **Ref**: Liu et al., arXiv 2307.03172 (TACL), Jul 2023 (v3), https://arxiv.org/abs/2307.03172
- **Contribution**: Multi-document QA and key-value retrieval show a U-shaped accuracy curve over the position of the relevant passage; performance drops as inputs get longer, even for long-context models.
- **Numbers**: With the relevant document in the middle, GPT-3.5-Turbo does worse than closed-book (56.1%); extended-context variants often perform identically to their short-context versions; 50 retrieved documents instead of 20 improve only ~1.5% (GPT-3.5-Turbo) / ~1% (claude-1.3).
- **Admitted limitations / future work**: 2023 models, non-agentic retrieval tasks.
- **Relevance**: Background only; cited by Complexity Trap and SWE-AGILE as motivation, but no one in this list measures position effects inside agent trajectories.

#### Confucius-CCA: Confucius Code Agent: Scalable Agent Scaffolding for Real-World Codebases (App. D thinking-budget scaling)
- **Ref**: arXiv 2512.10398, Dec 2025, https://arxiv.org/abs/2512.10398
- **Contribution**: Scaffold with hierarchical working memory and note-taking; includes a thinking-budget sweep.
- **Numbers**: Claude 4 Sonnet on a SWE-bench Verified subset: thinking budget 8k / 16k / 32k = 67.3 / 68.4 / 68.7% resolve (diminishing returns beyond 16k); Table 5: CCA 74.6 vs OpenHands 72.8 vs SWE-agent 66.6 with Claude 4 Sonnet.
- **Admitted limitations / future work**: App. D: `thinkingBudget` "cannot precisely control" internal trace length and Claude returns only a summarised trace, so actual reasoning length is unknown.
- **Relevance**: Only SWE-bench thinking-budget sweep found; shows small effects at large budgets (8k-32k per step) on a frontier model, a regime of no relevance to a 10.8k-token total generation cap at 30 tok/s.

#### Subgoal-MiRA: A Subgoal-driven Framework for Improving Long-Horizon LLM Agents
- **Ref**: arXiv 2603.19685, Mar 2026, https://arxiv.org/abs/2603.19685
- **Contribution**: Subgoal decomposition for online planning plus milestone-based RL (MiRA); WebArena-Lite.
- **Numbers**: Gemma3-12B 6.4% -> 43.0% success with MiRA (above GPT-4-Turbo 17.6%, GPT-4o 13.9%, WebRL 38.4%). Per-step static thinking budget on Gemini: success ~24.3% (256 tokens) -> ~32.5% (8192) while per-step inference time rises from ~6.5 s to ~19 s; 16384 tokens drops back to ~26%; adaptive ("Auto") budget matches the best static budget.
- **Admitted limitations / future work**: web navigation, not SWE; proprietary planner at inference.
- **Relevance**: A per-step thinking-budget vs latency curve with non-monotonic returns, and evidence that Gemma-class 12B models can improve a lot with RL on agentic tasks.

#### LemonHarness: LemonHarness Technical Report
- **Ref**: arXiv 2606.24311, Jun 2026, https://arxiv.org/abs/2606.24311
- **Contribution**: Execution framework with a time-aware mechanism: tasks are assigned a time tier, elapsed and remaining time are fed back to the model so it can rebalance exploration, implementation, validation, and avoid timeouts from long waits or excessive verification.
- **Numbers**: Terminal-Bench 2.0 84.49% over 445 trials (GPT-5.3-CodeX), 86.52% with GPT-5.5; no ablation isolating the time-aware component found in the text.
- **Admitted limitations / future work**: Sec. 5: aligned to GPT-style tool calling; generality across other model families not validated.
- **Relevance**: A deployed instance of the "remaining-time feedback" lever but without a measured effect.

#### SWE-Serve: SWE-Serve: Benchmarking Agentic Engineering For Production Inference Serving
- **Ref**: Williams et al., arXiv 2609.26777, 22 Sep 2026, https://arxiv.org/abs/2609.26777
- **Contribution**: 53 SGLang tasks, 11 models x 31 model-effort configurations (low..max reasoning effort), mini-SWE-agent, reports pass@1, cost, output tokens and wall-clock per task.
- **Numbers**: Best configuration 75% pass@1; higher reasoning effort reliably raises cost but "not consistently" pass@1; E2E serving tests reject ~one-third of patches that pass all other tests (45.9% vs 69.4%).
- **Admitted limitations / future work**: frontier models only, one benchmark domain.
- **Relevance**: Reasoning effort is not monotone in success on agentic coding (cf. Overthinking); but no per-step budget granularity.

#### Less-Context: Less Context, Better Agents: Efficient Context Engineering for Long-Horizon Tool-Using LLM Agents
- **Ref**: Lodha et al. (Microsoft Dynamics), arXiv 2606.10209, 8 Jun 2026, https://arxiv.org/abs/2606.10209
- **Contribution**: Enterprise expense-itemisation workflow (50 tasks, 5 runs, GPT-5 configurations): full history vs last-5-tool-pairs pruning vs pruning + summarisation.
- **Numbers**: Full history 71.0% complete itemisation, 1,480,996 tokens, 14.56 h; prune to last 5 tool pairs 79.0%, 535,274 tokens, 5.39 h; prune + summary 91.6%, 553,374 tokens, 5.79 h. Cross-model check with Claude Sonnet 4.5.
- **Admitted limitations / future work**: one enterprise workflow, frontier models.
- **Relevance**: Shows "keep last k tool results verbatim + summarise the rest" beats both full history and pruning alone, the opposite of "summary-only" robustness results; k=5 matches ADK's last ~5 events but here those are tool pairs.

#### ACM: ACM: Agentic Context Management for Long Horizon Tasks
- **Ref**: Li et al., arXiv 2607.23809, 26 Jul 2026, https://arxiv.org/abs/2607.23809
- **Contribution**: Context-editing tools (agent decides when to compress, offloads discarded content to external memory, queries on demand), post-training pipeline with Qwen3.5-397B-A17B teacher and a Qwen3.5-9B student; agentic search and coding.
- **Numbers**: Reports consistent gains over ReAct and summary baselines (re-implemented by the authors); reduced peak token pressure and more consistent solutions across trials; a Qwen3-4B-Thinking comparison is in App. D (not extracted).
- **Admitted limitations / future work**: Limitations: presupposes a base model with strong long-horizon ability; "weaker models that fail or hallucinate within a few turns yield trajectories too short to benefit from compression"; baselines re-implemented.
- **Relevance**: Independent statement that sub-10B models "lose coherence after only a few turns", so compaction is moot for them (cf. Bud's 8B submitting after ~10 turns).

#### VibeMemBench: VibeMemBench: Evaluating Memory Systems for Coding Agents on Real Repository Coding Tasks
- **Ref**: Fan et al., arXiv 2609.23570, 20 Sep 2026, https://arxiv.org/abs/2609.23570
- **Contribution**: 111 SWE-rebench V2 targets from 90 repositories with 3,634 history trajectories; verified useful experience is injected, or four existing memory systems must build and retrieve it.
- **Numbers**: Direct injection of verified experience raises resolution on 4 of 5 solvers by 1.1-4.5 pp and lowers steps on all 5; but with four existing memory systems 11 of 12 solver-system pairings fail to beat memory-off.
- **Admitted limitations / future work**: cross-task persistent memory, not within-task compaction.
- **Relevance**: Warns against assuming that memory/summaries of past work help on coding; relevant if the paper proposes cross-task memory (not in the current setting).

### 10. The system under study (documentation, not a paper)

#### ADK-Compaction: Google ADK "Compress agent context for performance" (documentation)
- **Ref**: Google ADK docs, https://adk.dev/context/compaction/ (accessed 2026-10-22)
- **Contribution**: Two strategies: sliding window (every `compaction_interval` new user invocations, with `overlap_size` preceding invocations) and token-based (`token_threshold` triggers "tail-retention compaction"; `event_retention_size` recent events stay raw "to preserve immediate context and pronoun resolution"). If both are set the token-based one takes precedence. Summariser prompt is customisable.
- **Numbers**: none; no evaluation published.
- **Admitted limitations / future work**: No limitations section. The page does not say what content types the summariser receives (the "text parts only; tool outputs and diffs dropped" fact in this project comes from the task description / code, not from this page). Kotlin variant cuts the window back so that no function call is summarised without its response.
- **Relevance**: Policy under test; its closest published analogues are OpenHands LLMSummarizingCondenser (keep_first + recent events) and the "T3 summary-only" tier of Harness-Design.

