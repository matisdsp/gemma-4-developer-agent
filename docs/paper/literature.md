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

## 2. Agent scaffolds and test-time scaling

### 2.1. Seminal scaffolds (2024)

#### SWE-agent: SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering
- **Ref**: Yang et al., NeurIPS 2024 / arXiv 2405.15793, May 2024, https://arxiv.org/abs/2405.15793
- **Contribution**: Introduces the Agent-Computer Interface (ACI): a small set of LM-friendly commands (windowed file viewer of 100 lines, line-range edit with integrated linter that rejects invalid edits, repo search, history processors that collapse old observations) instead of a raw shell.
- **Numbers**: SWE-bench full (2,294) 12.47% pass@1 with GPT-4 Turbo (prior best non-interactive RAG 3.8%); SWE-bench Lite (300) 18.00% GPT-4 Turbo, 13.00% Claude 3 Opus; shell-only agent 11.00% on Lite, 7.33% without demonstration; HumanEvalFix 87.7%.
- **Admitted limitations / future work**: (App. E.3) toolkit is small and manually designed; ACI development was manual and case-study driven, automating ACI design is open; tools such as static analysis, fault localization, test generation by fuzzing were not tried; scope only programmatic tasks.
- **Relevance**: The ACI ablations (linter on edit, bounded observations, history collapsing) are the cheapest levers for a 32k-context small model; all results are with frontier closed models (2024), so transfer to 4B/31B with 30 tool calls is untested.

#### Agentless: Agentless: Demystifying LLM-based Software Engineering Agents
- **Ref**: Xia et al., arXiv 2407.01489 (v2 Oct 2024), Jul 2024, https://arxiv.org/abs/2407.01489
- **Contribution**: Fixed three-phase pipeline (hierarchical localization file->class/function->edit location; repair by sampled search/replace diffs; patch validation with generated reproduction tests plus existing regression tests, used to rank sampled patches). No tool use, no planning by the LLM. Also manually audits SWE-bench Lite and builds Lite-S (removes problems with leaked/exact patches or insufficient description).
- **Numbers**: SWE-bench Lite 32.00% (96/300) at $0.70 average cost with GPT-4o (temperature 0.8 sampling; 4 edit-location samples x 10 patches = 40 candidate patches per issue plus 40 sampled reproduction tests), best among open-source approaches at the time; adopted by OpenAI as the reference scaffold for GPT-4o / o1 on SWE-bench. In the R2E-Gym comparison table Agentless with o1 reaches 48.0% and with DeepSeek-R1 49.2% on Verified.
- **Admitted limitations / future work**: (Sec. 7) possible training-data leakage of ground-truth patches (closed model); results only on SWE-bench Lite; plans to evaluate on other benchmarks. The no-agent design cannot adapt its plan to what it finds.
- **Relevance**: A fixed pipeline has predictable token and time cost and avoids long trajectories, which fits 6 min / 32k; but needs many samples + test-based reranking to reach its numbers, which is exactly what the wall-clock budget forbids.

#### AutoCodeRover: AutoCodeRover: Autonomous Program Improvement
- **Ref**: Zhang et al., ISSTA 2024 / arXiv 2404.05427, Apr 2024, https://arxiv.org/abs/2404.05427
- **Contribution**: Agent whose tools are AST-aware code search APIs (e.g. search_method_in_file; class/method-level, run locally from AST analysis) operating on classes/methods rather than files, followed by patch generation; optionally spectrum-based fault localization when a test suite exists.
- **Numbers**: SWE-bench Lite 19% resolved (average cost $0.43 per issue), above SWE-agent (18%) at the time; each experiment repeated 3 times.
- **Admitted limitations / future work**: (Sec. 8) LLM randomness (mitigated by 3 runs); patches may overfit tests (manual semantic-equivalence check). Perspectives: future autonomous improvement of LLM-generated code.
- **Relevance**: Structure-aware search (class/method retrieval) returns short, high-density observations, which matters when the context budget is 14k before compaction.

#### OpenHands: OpenHands: An Open Platform for AI Software Developers as Generalist Agents
- **Ref**: Wang et al., ICLR 2025 / arXiv 2407.16741, Jul 2024, https://arxiv.org/abs/2407.16741
- **Contribution**: Open platform: event-stream abstraction, Docker sandbox, CodeAct-style actions (bash + IPython + browser), AgentSkills library and multi-agent delegation (AgentDelegateAction), evaluation over 15 benchmarks.
- **Numbers**: SWE-bench Lite (no hint) CodeActAgent v1.8: gpt-4o-mini 7.0% ($0.01/instance), gpt-4o 22.0% ($1.72), Claude 3.5 Sonnet 26.0% ($1.10); a full SWE-bench Lite eval with gpt-4o costs about $600.
- **Admitted limitations / future work**: (App. A) safety and reliability of agents; no controlled ablation of multi-agent delegation on SWE-bench is reported.
- **Relevance**: Shows the steep drop from frontier to small model in the same scaffold (7% vs 26%), i.e. scaffold alone does not rescue small models.

#### CodeAct: Executable Code Actions Elicit Better LLM Agents
- **Ref**: Wang et al., ICML 2024 / arXiv 2402.01030, Feb 2024, https://arxiv.org/abs/2402.01030
- **Contribution**: Unified action space of executable Python code (composable, self-debuggable) instead of JSON/text tool calls; CodeActInstruct (7k multi-turn trajectories) and CodeActAgent fine-tuned from Llama2/Mistral.
- **Numbers**: up to 20% higher success than JSON/text actions across 17 LLMs on API-Bank and M3ToolEval; improvements are more prominent for open-source models (JSON tool-calling is consistently weaker for them, while closed models seem fine-tuned for JSON).
- **Admitted limitations / future work**: conclusion lists no explicit limitation section; evaluated on tool-use benchmarks not SWE-bench repair.
- **Relevance**: Supports using code/bash actions rather than JSON tool-calls for open models; no SWE-bench evidence and models tested are 2023-24 vintage, so whether this holds for Gemma 4 native tool calling is untested.

#### SWE-Search: SWE-Search: Enhancing Software Agents with Monte Carlo Tree Search and Iterative Refinement (Moatless Tools backbone)
- **Ref**: Antoniades et al., ICLR 2025 / arXiv 2410.20285, Oct 2024, https://arxiv.org/abs/2410.20285
- **Contribution**: MCTS over agent states with a hybrid LLM value function (numeric + natural-language feedback), a SWE-Agent (expansion), a Value Agent and a Discriminator Agent that debates the final choice; built on Moatless Tools.
- **Numbers**: SWE-bench Lite resolve rate, Moatless-Adapted -> SWE-Search: GPT-4o 25.7 -> 31.0, GPT-4o-mini 13.0 -> 17.0, Qwen2.5-72B 18.0 -> 24.7, DeepSeek-V2.5 16.3 -> 21.0, Llama-3.1-70B 13.6 -> 17.7 (mean +23% relative); 3 expansions per node, 100 iterations cap.
- **Admitted limitations / future work**: (Sec. 5) need to study how search agents scale with compute; extension to broader use cases. Different models solve very different issue subsets (33 issues solved by other models but not GPT-4o).
- **Relevance**: Gains exist for open 70B-class models, but at up to 100 search iterations per issue, far above a 30-call budget; no study at tiny k.

#### CodeMonkeys: CodeMonkeys: Scaling Test-Time Compute for Software Engineering
- **Ref**: Ehrlich et al., arXiv 2501.14723, Jan 2025, https://arxiv.org/abs/2501.14723
- **Contribution**: Parallel and serial scaling: per issue many state machines jointly write an edit and a reproduction test script (serial iterations), then selection by voting on model-written tests plus a final multi-turn selection trajectory; context retrieval by file-level filtering and ranking.
- **Numbers**: SWE-bench Verified 57.4% at about USD 2,300 total budget (Claude 3.5 Sonnet for generation/selection, a locally run Qwen2.5-Coder-32B-Instruct reading every file to find relevant ones); selection over an ensemble of existing top submissions 66.2%. Selection recovers only about half of the random-vs-oracle gap; the file filter misses relevant files for 7.4% of instances.
- **Admitted limitations / future work**: (Sec. 3) selection is the main headroom; the retrieval stage relies on base-model prior knowledge of the repository, "this assumption will not hold when solving issues from new or private repositories" and would need retrieval changes; diversity only from temperature; existing repo regression tests unused.
- **Relevance**: One of the few papers that explicitly flags private/unseen repositories as a weakness of its pipeline; selection quality (the verifier) is the bottleneck even with a frontier model.

### 2.2. Minimal scaffolds and open-weight TTS (2025-2026)

#### mini-swe-agent: mini-SWE-agent (no standalone paper; cites SWE-agent)
- **Ref**: Princeton/Stanford SWE-agent team, GitHub README, 2025-26 (read 2026-10-22), https://github.com/SWE-agent/mini-swe-agent
- **Contribution**: Bash-only agent in ~100 lines of Python; no tool-calling interface needed, linear message history (trajectory = prompt), stateless `subprocess.run` actions. Used as the reference scaffold in many 2026 papers (SWE-Replay, Scaling TTC for Agentic Coding).
- **Numbers**: README claims ">74% on SWE-bench Verified" (frontier models, unspecified). Default step limit 250 in SWE-Replay's usage; Devstral-Small-2 run there with 128 steps.
- **Admitted limitations / future work**: none stated in the README; no peer-reviewed paper (cite SWE-agent 2405.15793).
- **Relevance**: The simplest baseline; linear unbounded history is exactly what a 32k window with compaction must replace. Default 128-250 steps is 4-8x the ~30-call budget of the target setting.

#### DeepSWE: DeepSWE: Training a Fully Open-sourced, State-of-the-Art Coding Agent by Scaling RL (blog, not arXiv)
- **Ref**: Agentica / Together AI, blog, Jul 2025, https://together.ai/blog/deepswe (details read via search summary, not the full post)
- **Contribution**: Qwen3-32B trained with RL only on ~4,500 R2E-Gym tasks (64 H100 for 6 days), released with data, code and logs; reported with test-time scaling (hybrid verifier).
- **Numbers**: 42.2% pass@1, 71.0% pass@16 on SWE-bench Verified; 59% with test-time scaling (as reported by the authors; independent confirmation not found).
- **Admitted limitations / future work**: not read in full (blog); treat numbers as developer claims.
- **Relevance**: Gap between pass@1 42% and pass@16 71% is the headroom that selection must capture; at k=1-2 only the pass@1 side is available.

#### R2E-Gym: R2E-Gym: Procedural Environments and Hybrid Verifiers for Scaling Open-Weights SWE Agents
- **Ref**: Jain et al., arXiv 2504.07164, Apr 2025, https://arxiv.org/abs/2504.07164
- **Contribution**: 8.7K-task executable gym (SWE-Gen: tests and issues back-translated from commits) and a study of two verifier axes: execution-based (a testing agent writes tests) vs execution-free (trained patch scorer), combined as a hybrid verifier.
- **Numbers**: 32B agent 34.4% pass@1 on SWE-bench Verified; each verifier alone saturates at about 42-43%; hybrid Best@26 reaches 51%. Training/inference limits: 40 steps, 20-32K tokens per trajectory, 5-10 min wall-clock per trajectory. Data scaling: the 14B model saturates at about 800 trajectories while 32B keeps improving. Fewer than 20% of generated tests carry discriminative signal on most problems (low "distinguishability"); many generated tests do not reproduce the bug.
- **Admitted limitations / future work**: test-based verifiers have low distinguishability; execution-free verifiers are biased toward stylistic cues and agent thoughts; training context limited to 20K, context parallelism flagged as future work.
- **Relevance**: Closest published budget to the target (40 steps, 20-32K tokens, 5-10 min) and open 14-32B models; shows tests are a weak verifier and that small models plateau earlier.

#### Thinking Longer: Thinking Longer, Not Larger: Enhancing Software Engineering Agents via Scaling Test-Time Compute
- **Ref**: Ma et al., arXiv 2503.23803, Mar 2025, https://arxiv.org/abs/2503.23803
- **Contribution**: Internal TTC (trajectory synthesis with multi-stage reasoning, rejection sampling) plus external TTC (search at critical development stages pruned by reward models and execution verification) for a 32B model (SWE-Reasoner).
- **Numbers**: SWE-bench Verified 46% with a 32B model with external TTC, above DeepSeek-R1 671B and o1 per the authors; models allocate more tokens to harder problems.
- **Admitted limitations / future work**: (Sec. 5) inference efficiency degrades (acceptable for batch issue resolution, not interactive use); small verified training set because environment setup is hard; future work on adaptive compute allocation by predicted difficulty.
- **Relevance**: Early evidence that 32B + TTC can match larger models; but cost is not time-bounded, and adaptive allocation (the regime of a fixed 6-min budget) is left as future work.

#### SWE-Replay: SWE-Replay: Efficient Test-Time Scaling for Software Engineering Agents
- **Ref**: Ding & Zhang, arXiv 2601.22129, Jan 2026, https://arxiv.org/abs/2601.22129
- **Contribution**: Recycles prior trajectories: at each new trial either explore from scratch or branch from an archived intermediate step chosen by exploration "potential and reasoning significance", with no LLM judge. Works with bash-script agents (mini-SWE-agent, Live-SWE-agent) where value-agent methods (SWE-Search) do not.
- **Numbers**: SWE-bench Verified, 10 samples per issue + Agentless-style test-filter and majority vote: cost down up to 17.4% and resolve rate up to +3.8%. Devstral-Small-2 (open) with Live-SWE-agent: 63.2% naive vs 65.0%; Gemini-3-Pro about 75.5%. Step selection ablation: random 56.0%, LLM-as-a-Judge 54.0% (and +1.87 USD verifier cost), SWE-Replay 60.0%. Up to 22.6% gain (as reported; relative vs absolute not stated in the text read) on SWE-Bench Pro / Multilingual with Devstral-Small-2 + mini-SWE-agent. Step limits 250 (Gemini) / 128 (Devstral).
- **Admitted limitations / future work**: no dedicated limitations section; gains are in cost, and modest in accuracy. Note that LLM-as-judge step selection was worse than random in their ablation.
- **Relevance**: Shows judges can be net-negative even in-loop; assumes ~10 samples and 128+ steps, far from a 30-call sequential budget.

#### SWE-RM: SWE-RM: Execution-free Feedback For Software Engineering Agents
- **Ref**: Shum et al., arXiv 2512.21919, Dec 2025, https://arxiv.org/abs/2512.21919
- **Contribution**: 30B MoE (3B active, 256k context) generative reward model over full trajectories; argues TTS accuracy alone is an insufficient verifier metric and adds AUC and calibration (ECE), because two verifiers with equal TTS can behave very differently in RL.
- **Numbers**: SWE-bench Verified TTS@32: Qwen3-Coder-Flash 51.6% -> 62.0%, Qwen3-Coder-Max 67.0% -> 74.6%. Ablation on positive:negative data ratio: AUC only 0.73-0.81, ECE 0.08-0.54 (best 2:1 ratio, ECE 0.08 / 0.12). As RL reward it gives about +3 pass@1 over execution-based feedback.
- **Admitted limitations / future work**: no separate limitation section; the paper itself shows verifier AUC around 0.8 and that calibration varies a lot with data mix.
- **Relevance**: Verifier consumes whole trajectories (long context) and is evaluated at k=32; nothing about k=2-4 or about a verifier small enough to share 4x L4 with the policy.

#### Agentic Rubrics: Agentic Rubrics as Contextual Verifiers for SWE Agents
- **Ref**: Raghavendra et al. (Scale AI), arXiv 2601.04171, Jan 2026, https://arxiv.org/abs/2601.04171
- **Contribution**: An expert agent explores the repo and writes a rubric checklist (no execution); candidate patches are scored against it.
- **Numbers**: SWE-bench Verified Best@16 (K=16): Qwen3-Coder-30B-A3B 54.2% and Qwen3-32B 40.6%. Baselines on Qwen3-32B / Coder: random 22.6 / 39.6, self-consistency 33.2 / 47.6, patch classifier 37.1 / 50.2, agentic tests 33.6 / 49.0, agentic patch similarity 35.0 / 49.6, oracle pass@16 51.4 / 65.6. Rubrics are written with Claude Sonnet-4.5 and the judge is GPT-5 (low reasoning); ablation: agentic context gathering is essential.
- **Admitted limitations / future work**: (Sec. 8) studied only as parallel TTS verifier; RL use brings reward hacking, non-stationarity and credit assignment, left to future work.
- **Relevance**: Verifier strength comes from a frontier expert model, not the 32B policy; whether a self-hosted small model can write usable rubrics is untested.

#### Scaling TTC for Agentic Coding: Scaling Test-Time Compute for Agentic Coding
- **Ref**: Kim et al. (Meta Superintelligence Labs / UW), arXiv 2604.16529, Apr 2026, https://arxiv.org/abs/2604.16529
- **Contribution**: Converts each rollout into a structured summary (hypotheses, progress, failure modes). Parallel scaling by Recursive Tournament Voting (small-group comparisons of summaries); sequential scaling by Parallel-Distill-Refine (new rollouts conditioned on distilled summaries of earlier ones).
- **Numbers**: SWE-bench Verified (mini-SWE-agent): Claude-4.5-Opus 70.9% -> 77.6%, Gemini-3.1-Pro 72.3% -> 76.6%; Terminal-Bench v2.0 46.9% -> 59.1% (Opus). Main config N=16, T=2, K=4, G=2, V=8. Structured summaries beat raw trajectories as comparison input; refinement from prior summaries cuts steps of the next rollout by about 50%.
- **Admitted limitations / future work**: (Sec. 5) reuse only through text summaries in fresh environments; persistent artifacts (notes, partial patches, derived tests) are future work.
- **Relevance**: Directly relevant to LLM-summary compaction: they show summaries of a trajectory can be a better interface than raw traces; only frontier models and N=16 rollouts tested.

#### Disagree to Explore: Disagree to Explore, Agree to Commit: Routing-Guided Test-Time Scaling for Software Agents (Risa)
- **Ref**: Chen et al., arXiv 2608.22191, Aug 2026, https://arxiv.org/abs/2608.22191
- **Contribution**: Uses native MoE router traces as a behavioural signal to steer diversity within trajectories and to select among trajectories, with no external judge and no selection-time execution.
- **Numbers**: SWE-bench Verified, gpt-oss family macro-average 44.9% (uniform sampling) -> 48.2%, matching text consensus; transfers to Qwen3.6 on the full 500 tasks.
- **Admitted limitations / future work**: (Sec. 7) requires white-box sparse-MoE routing and repeated trajectories; dense or closed models need other readouts; combining with execution evidence for rare outlier repairs.
- **Relevance**: Needs repeated samples and MoE internals; a dense 31B/4B model would not qualify.

#### SWE-Master: SWE-Master: Unleashing the Potential of Software Engineering Agents via Post-Training
- **Ref**: Song et al., arXiv 2602.03411, Feb 2026, https://arxiv.org/abs/2602.03411
- **Contribution**: Reproducible pipeline (teacher trajectory synthesis, long-horizon SFT, RL with execution feedback) plus inference design: LSP-based code navigation tool and TTS using an LLM-simulated environment (SWE-World style) to score candidates instead of executing.
- **Numbers**: SWE-bench Verified 61.4% pass@1 (Qwen2.5-Coder-32B as stated in the abstract), 70.8% at TTS@8; TTS@K tracks the Pass@K upper bound closely per the authors; trajectories longer than 80K tokens or 100 turns pruned from training; LSP tool improves efficiency with minimal success loss.
- **Admitted limitations / future work**: no explicit limitations section found in the HTML text.
- **Relevance**: A 32B open model reaches 61.4% single-shot but with 80K-token / 100-turn trajectories; efficiency gains from a structural navigation tool are relevant to a 30-call budget.

#### SWE-Hero: From SWE-ZERO to SWE-HERO: Execution-free to Execution-based Fine-tuning for Software Engineering Agents
- **Ref**: Ludwig et al. (NVIDIA), arXiv 2604.01496, Apr 2026, https://arxiv.org/abs/2604.01496
- **Contribution**: Two-stage SFT distilled from Qwen3-Coder-480B: 300k execution-free trajectories (SWE-ZERO), then 13k execution-verified ones (SWE-HERO); Qwen2.5-Coder-based agents.
- **Numbers**: SWE-HERO-32B 62.2% on SWE-bench Verified; 44.1% zero-shot on SWE-bench Multilingual despite Python-only training. TTS with K=32 rollouts and open generative verifiers: up to +7.9 points for the smaller models and +4.5 for the 32B, but a gap of about 15 points at K=16 remains between verifier-selected Best@K and the Pass@K ceiling and it widens with K.
- **Admitted limitations / future work**: inherits teacher biases and ceiling; only non-reasoning architectures explored; open-source verifiers "lack the discriminative precision" to exploit TTS, robust reward models left for future work.
- **Relevance**: Distillation, not scaffold or TTS; included as the model-side alternative to inference-time methods.

### 2.3. Reproduction-test generation as verifier

#### SWT-Bench: SWT-Bench: Testing and Validating Real-World Bug-Fixes with Code Agents
- **Ref**: Mundler et al., NeurIPS 2024 / arXiv 2406.12952, Jun 2024, https://arxiv.org/abs/2406.12952
- **Contribution**: Benchmark of issue-reproduction tests built on SWE-bench (fail-to-pass test = fails before gold patch, passes after). Shows code-repair agents (SWE-Agent adapted, "SWE-Agent+") beat test-specialised systems, and that generated tests filter patches.
- **Numbers**: filtering SWE-Agent patches to those passing self-generated F->P tests (all generated tests F->P or P->P) gives 47.8% precision vs about half that unfiltered ("more than doubles precision") at only 20% recall; best single approach solves 51 test instances, union of four approaches 87.
- **Admitted limitations / future work**: (Sec. 6) Python only; popular repos only so no private hold-out set is possible; only bug reproduction; contamination risk because most issues predate model cutoffs (suggests a rolling version).
- **Relevance**: Establishes the "tests as filter" idea, but the filter is high-precision/low-recall (20%): with k=1-2 candidates there is little to filter.

#### Otter: Otter: Generating Tests from Issues to Validate SWE Patches
- **Ref**: Ahmed et al. (IBM), ICML 2025 / arXiv 2502.05368, Feb 2025, https://arxiv.org/abs/2502.05368
- **Contribution**: Test-from-issue generator with rule-based validation/repair of LLM output and a self-reflective action planner; TDD-Bench-Verified benchmark (12 Python repos).
- **Numbers**: fail-to-pass tests in 31.4% of cases (GPT-4o), 37.0% for an ensemble of 5 (Otter++), pass@5 44%; cost under USD 0.10 per issue; with Mistral-Large Otter 26.9% vs 12.7% zero-shot; removing test localization costs 35.8% of tddScore, removing action planning 21.4%.
- **Admitted limitations / future work**: (Sec. 7) 12 popular Python repos; Otter handles only one test file and one block of code; coverage measured with Python coverage package.
- **Relevance**: Cheap (<$0.10) and works with a mid-size open model (Mistral-Large) but ~30% yield means roughly 2 of 3 tasks get no valid reproduction test.

#### Issue2Test: Issue2Test: Generating Reproducing Test Cases from Issue Reports
- **Ref**: Nashid et al., arXiv 2503.16320, Mar 2025, https://arxiv.org/abs/2503.16320
- **Contribution**: Three steps: gather context (related files, project test guidelines via meta-prompting), generate candidate test, iterate on compile/runtime feedback until it fails for the reason in the issue.
- **Numbers**: SWT-bench-lite 32.9% issues reproduced (+16.3% relative over best prior); reproduces 20 issues missed by four prior tools.
- **Admitted limitations / future work**: (Threats) dataset only 276 issues, some projects <10 issues; reliance on meta-prompting benefits popular projects, and "raises concerns about Issue2Test's ability to generalize to private repositories or lesser-known projects where LLMs lack prior exposure".
- **Relevance**: One of the clearest explicit statements that reproduction-test quality may collapse on unseen/private repos, which is the target regime.

#### AssertFlip: AssertFlip: Reproducing Bugs via Inversion of LLM-Generated Passing Tests
- **Ref**: Khatib et al., arXiv 2507.17542, Jul 2025, https://arxiv.org/abs/2507.17542
- **Contribution**: Writes a test that passes on the buggy behaviour, then inverts the assertion so it fails when the bug is present, because LLMs are better at writing passing tests than failing ones.
- **Numbers**: 43.6% fail-to-pass on SWT-Bench-Verified (top of the SWT-Bench leaderboard at submission); cutting the number of regenerations cuts cost about 40% with performance still above other tools; coverage delta 78.4% for resolved vs 26.1% for unresolved.
- **Admitted limitations / future work**: (Sec. 7) Python-only benchmarks, small set of projects; possible training-data overlap with GPT-4o; context is discarded at every regeneration.
- **Relevance**: Inversion makes the task easier for weak models (a candidate trick for 4B), but all numbers use GPT-4o-class models.

#### TestPrune: Can Old Tests Do New Tricks for Resolving SWE Issues?
- **Ref**: Chen et al. (IBM/UIUC), FSE 2026 / arXiv 2510.18270, Oct 2025, https://arxiv.org/abs/2510.18270
- **Contribution**: Minimises the repo's existing regression suite to a small relevant subset to feed both reproduction-test generation and patch validation, because full suites overflow context and add noise.
- **Numbers**: +6.2% to +9.0% relative issue reproduction rate within Otter; +8.0% to +12.9% relative resolution rate in Agentless, SWE-Agent and Trae Agent on SWE-bench Lite/Verified; overhead USD 0.02 (GPT-4o) to 0.05 (Claude-3.7) per instance.
- **Admitted limitations / future work**: no limitation section surfaced in the HTML text; relies on repository having a regression suite.
- **Relevance**: Directly addresses context overflow from existing tests; assumes a runnable existing suite, which holds for many private repos but not all.

#### TDFlow: TDFlow: Agentic Workflows for Test Driven Development
- **Ref**: Han et al., EACL 2026 / arXiv 2510.23761, Oct 2025, https://arxiv.org/abs/2510.23761
- **Contribution**: Four sub-agents with tightly constrained tools (patch proposal, debugging, revision, optional test generation) to reduce long-context burden per agent; operates when human-written tests are given.
- **Numbers**: with human-written tests: 88.8% on SWE-bench Lite (+27.8 absolute over next best) and 94.3% on Verified; 7 of 800 runs showed test hacking (counted as failures); the authors conclude the main obstacle to human-level autonomy is writing valid reproduction tests.
- **Admitted limitations / future work**: (Sec. 6) need automated test-hacking detection; RL post-training on the test-generation sub-task enabled by the decoupling.
- **Relevance**: Evidence that sub-agent decomposition helps when a trusted test oracle exists; with no human tests, the bottleneck moves to the weakest component (test generation).

#### SWE-Tester: SWE-Tester: Training Open-Source LLMs for Issue Reproduction in Real-World Repositories
- **Ref**: Soni et al., arXiv 2601.13713, Jan 2026, https://arxiv.org/abs/2601.13713
- **Contribution**: Fine-tunes open models (Qwen2.5-Coder 7B/14B/32B, Llama-3.1-8B, Gemma-3-12B) on 41K instances from 2.6K repos for issue-reproduction tests; inference scaffold samples N=8 patches for each of top K=4 test files (32 candidates) and reranks.
- **Numbers**: up to +10 points success rate and +21 points change coverage on SWT-Bench Verified (433 instances); gains continue up to 32 candidates without saturation; not monotonic in size: 7B beats 14B/32B on xarray (26.67% vs 6.67%).
- **Admitted limitations / future work**: (Sec. 7) Python only; heuristic data filtering; no trained test localizer; no optimised reranking.
- **Relevance**: Only paper here with Gemma-family and 7-12B models on a reproduction-test task; but needs 32 candidates, versus a ~30 tool-call total budget.

#### ReProAgent: ReProAgent: Tool-Augmented Multi-Stage Agentic Generation of Bug Reproduction Tests from Issue Reports
- **Ref**: Zhang et al., arXiv 2607.09123, Jul 2026, https://arxiv.org/abs/2607.09123
- **Contribution**: Four-stage agent (localisation, root cause analysis, test planning, test generation) with graph-based context retrieval and execution tools.
- **Numbers**: reproduces 58.43% (SWT-bench-lite) and 70.30% (SWT-bench-verified); USD 0.14 per instance; with GPT-5-mini it beats OpenHands by +20.43 / +7.90 points; on average 1.29 feedback iterations, 90% finish within 5.
- **Admitted limitations / future work**: (Sec. 6.3) Python only, stochasticity; workflow considered language-agnostic.
- **Relevance**: New 2026 SOTA for reproduction tests with a small closed model (GPT-5-mini); iteration counts (1-5) are compatible with a tight tool budget.

#### SWE-Doctor: SWE-Doctor: Guiding SWE Agents with Runtime Diagnosis from Multi-Faceted Bug Reproduction Tests
- **Ref**: Guo et al., arXiv 2607.00990, Jul 2026, https://arxiv.org/abs/2607.00990
- **Contribution**: Preliminary study finds that feeding advanced BRT generators' tests into patch generation does not help (fail-to-fail tests mislead; fail-to-pass tests often cover one manifestation, causing partial patches). Proposes multi-faceted BRTs executed and debugged into runtime diagnosis records used to guide patching.
- **Numbers**: average 75.7% on SWE-bench Verified and 59.4% on SWE-bench Pro across five LLM backends, +8.0-8.9 points over baseline agents (mini-SWE-agent, live-SWE-agent) on Pro; Go subset 36.0% vs 32.0%/30.0%.
- **Admitted limitations / future work**: (Sec. VI) two benchmarks, mostly Python, baseline choice.
- **Relevance**: Contradicts the intuition that more reproduction tests always help: naive use can hurt (see Gap candidates).

#### CoHarden: Beyond Fail-to-Pass: Iterative Hardening of Co-Generated Bug Reproduction Tests and Fixes
- **Ref**: Tan et al., arXiv 2607.19843, Jul 2026, https://arxiv.org/abs/2607.19843
- **Contribution**: Shows F->P is insufficient: "lax" F->P tests admit plausible-but-wrong patches and only "rigorous" tests improve repair; in co-generation the in-trajectory F->P check can pass when both test and patch are wrong (test-fix error coupling). CoHarden writes the test first, then hardens test and fix against mutants.
- **Numbers**: 69.4% resolved and 78.9% F->P on SWE-bench Verified (OpenHands + GPT-5-mini), +9.6 over best fix-only and +7.9 over best co-generation baseline; plateau after round 3.
- **Admitted limitations / future work**: (Sec. 6) mutants inherit the LLM's notion of plausible wrong fixes; Python/OpenHands only; test-fix coupling can re-emerge across rounds; breaking it is future work.
- **Relevance**: A model that writes both test and fix can validate its own mistake; with a weak model the coupling risk is probably larger (untested).

#### TestGRAD: TestGRAD: Evolving Test Suites via Failure Pattern Momentum for SWE-Agent Ensemble
- **Ref**: He et al., arXiv 2610.10242, Oct 2026, https://arxiv.org/abs/2610.10242
- **Contribution**: Treats test-based patch selection in an agent ensemble as test-space optimisation with a differential loss (tests should separate candidate patches), CRUD edits to tests and failure-pattern memory (100x compression of failure history).
- **Numbers**: 84.2% Pass@1 on SWE-bench Verified with a 4-agent ensemble vs 80.6% strongest baseline.
- **Admitted limitations / future work**: not extracted (no limitations section located in HTML).
- **Relevance**: Ensemble selection with 4 frontier agents; not applicable at one small model.

#### SWEPatchTest: SWEPatchTest: Evaluating Software Tests Beyond Reproduction
- **Ref**: Lu et al., arXiv 2610.18004, Oct 2026, https://arxiv.org/abs/2610.18004
- **Contribution**: 619 tasks (SWE-bench Pro, Multilingual, DeepSWE) with 82,579 candidate patches from agent trajectories; Joint Validation Rate (JVR) requires a test suite to reproduce the issue AND accept correct AND reject incorrect patches.
- **Numbers**: best configuration only 9.21% JVR although it reproduces the reference transition on 59.29% of tasks; validation-score-selected SFT roughly triples JVR and improves downstream repair on three SWE-bench variants.
- **Admitted limitations / future work**: (App. G) labels follow the official oracle (operational, not formal correctness); timeouts and missing outputs lower scores.
- **Relevance**: Quantifies how weak generated tests are as patch discriminators (9% JVR), the key assumption behind test-based selection.

### 2.4. Critics, process reward models, judges, stopping and restart

#### SWE-PRM: When Agents go Astray: Course-Correcting SWE Agents with PRMs
- **Ref**: Gandhi et al. (IBM Research), arXiv 2509.02360, Sep 2025, https://arxiv.org/abs/2509.02360
- **Contribution**: Inference-time process reward model that watches the last k=8 steps and injects taxonomy-guided feedback (redundant exploration, looping, failure to stop) without changing the policy.
- **Numbers**: SWE-bench Verified, policy SWE-agent-LM-32B (Qwen2.5-Coder-32B fine-tune), 75-step cap, temperature 0: base 40.0%; with Claude-Sonnet-4 as PRM +4.8 to +10.6 points (best 50.6%, about USD 26 per 100 instances); with open-weight models as PRM (same model as policy, Devstral-Small-2505/2507) resolution stays 30.0-38.8%, one variant drops to 19.6% (-20.4); open PRMs often lengthen trajectories.
- **Admitted limitations / future work**: authors conclude SWE-tuned open models "are not inherently reliable when used as PRMs"; PRM-in-MCTS is prohibitive because code edits are irreversible.
- **Relevance**: Direct evidence against self-/same-size-model critics on open models in a SWE-agent loop; the gain comes from a frontier critic, which is unavailable in a private 4x L4 deployment.

#### Opera: Opera: A Verbal Critic Framework for Long-horizon Coding Agents
- **Ref**: Mei et al., arXiv 2609.33987, Sep 2026, https://arxiv.org/abs/2609.33987
- **Contribution**: A critic that reviews on periodic/event triggers, diagnoses with typed operators, audits its own feedback against visible evidence before delivering it, and tracks whether the agent actually resolved the flagged problem.
- **Numbers**: policies Qwen3.5-9B, Muse-glimmer-30B, Qwen3.8-27B, DeepSeek-V4-Flash with GPT-5.6-Sol as default critic: up to +12.4 pp (Terminal-Bench 2.1), +15.0 pp (SWE-Bench Pro subset) and +8.9 pp (DeepSWE v1.1); self-critique on DeepSWE gives +6.2 pp for Qwen3.8-27B and DeepSeek-V4-Flash, matching or exceeding Claude as critic; removing the audit step halves the gain on one benchmark (8.9 -> 4.5 pp), i.e. unaudited feedback is partly harmful. Qwen3.5-9B resolves no DeepSWE task with or without a critic. Fine-tuning Qwen3.5-9B on Opera-guided rollouts +10.2 pp on held-out SWE-Bench Pro repos.
- **Admitted limitations / future work**: self-critique is less effective when the policy lacks the capability to solve the task (Muse-glimmer-30B on DeepSWE, Qwen3.5-9B on Terminal-Bench 2.1); the self-critique comparison does not match inference compute.
- **Relevance**: Contradicts SWE-PRM on self-critique (works here, hurts there); weaker policies benefit most but only above a capability floor, and compute is not matched, so a 6-min budget may erase the gain.

#### Patch-reasoning R4P: Scalable Supervision for Software Agents via Patch Reasoning
- **Ref**: Xu et al., EMNLP 2026 Findings / arXiv 2510.22775, Oct 2025, https://arxiv.org/abs/2510.22775
- **Contribution**: Reasoning-based, group-wise patch verifier (compares several patches against each other) giving a dense reward without executing tests; trains an execution-free scaffold Mini-SE with RL on it.
- **Numbers**: 72.2% accuracy verifying SWE-bench patches (competitive with proprietary models); Mini-SE 26.2% pass@1 (+10.0 over Qwen3-32B), 32.8% with R4P for patch selection in TTS.
- **Admitted limitations / future work**: static reward model drifts as the policy improves; cannot supervise in-loop self-testing/self-fixing that needs execution.
- **Relevance**: A 32B-scale open verifier with no sandbox (fits private repos), but absolute pass rates are low (26-33%).

#### SWE-TRACE: SWE-TRACE: Optimizing Long-Horizon SWE Agents Through Rubric PRMs and Heuristic Test-Time Scaling
- **Ref**: Han et al., arXiv 2604.14820, Apr 2026, https://arxiv.org/abs/2604.14820
- **Contribution**: Shortest-path SFT corpus (60K), memory-augmented RL with a rubric-based PRM, and reuse of the PRM to prune action candidates step by step at test time (avoiding parallel-sampling latency).
- **Numbers**: abstract claims SOTA and lower tokens/latency; I did not extract per-benchmark numbers from the body text.
- **Admitted limitations / future work**: none located.
- **Relevance**: Step-level pruning instead of whole-trajectory sampling matches a sequential, latency-bound setting; unverified numbers, treat as pointer only.

#### EGSS: EGSS: Entropy-guided Stepwise Scaling for Reliable Software Engineering
- **Ref**: Mao et al., arXiv 2602.05242, Feb 2026, https://arxiv.org/abs/2602.05242
- **Contribution**: Entropy-guided adaptive search over steps plus test-suite augmentation for selection; allocates search where the policy is uncertain.
- **Numbers**: SWE-bench Verified: Kimi-K2-Instruct 63.2% -> 72.2%, GLM-4.6 65.8% -> 74.6%; 5-10% gains across models; over 28% fewer tokens than existing TTS methods.
- **Admitted limitations / future work**: no limitation section found.
- **Relevance**: Uses policy token entropy (available for local models) as the allocation signal; models are 300B+ MoE, not small.

#### LatentSift: LatentSift: Policy-State Filtering for Token-Efficient Verification of SWE Agents
- **Ref**: Han et al., arXiv 2609.36371, Sep 2026, https://arxiv.org/abs/2609.36371
- **Contribution**: Replaces the LLM execution-free verifier with a filter on the policy's own hidden states (distance to banks of success/failure states), then runs execution-based stages on survivors.
- **Numbers**: at K=16 on SWE-bench Verified cuts execution-free-verifier tokens 66.6-81.0% and total verification tokens 49.1-62.1%; hybrid Best@16 59.26% -> 60.06% on DeepSWE-Preview; works for two policy sizes.
- **Admitted limitations / future work**: needs access to hidden states (open-weight only); evaluated on candidate pools up to K=16.
- **Relevance**: Fits self-hosted open models (no extra judge), but still needs K=16 trajectories.

#### FailFast-RestartSmart: Fail-Fast, Restart-Smart: Early Failure Prediction and Restart for SWE Agentic Tasks
- **Ref**: Wang et al., arXiv 2608.03222, Aug 2026, https://arxiv.org/abs/2608.03222
- **Contribution**: A 0.6B monitor predicts failure from the observable trajectory prefix; on alarm, restarts a fresh same-policy rollout with the abandoned diff offered as an optional overlay.
- **Numbers**: SWE-bench Verified, trained on Qwen3.6-27B trajectories, transfers to three other policies; saves 14.6-20.4% of execution tokens at 5% false-positive rate (beats 12.5% for per-step AgentStop adaptation); Qwen3.6-27B 66.6% -> 71.8% at 25% FPR vs 66.8% for cold restart; token overhead 20.5-43.8%.
- **Admitted limitations / future work**: only SWE-bench Verified with mini-swe-agent.
- **Relevance**: The restart-with-overlay idea is a sequential, small-k way to spend a time budget; early prediction needs enough prefix, which a 30-call budget barely provides.

#### StopLoss: StopLoss: Teaching Agents to Predict Failure and Stop Early
- **Ref**: Liang et al., arXiv 2610.25525, Oct 2026, https://arxiv.org/abs/2610.25525
- **Contribution**: Small outcome-trained monitor (Qwen3-8B backbone works) scores the latest tool steps and aborts likely failures; compared with six general-purpose judges reading the same windows.
- **Numbers**: lowers cost per retained solve by 4.5% on Verified (keeping 99% of successes) and up to 31% on the costlier Pro subset (48% with Qwen3-8B backbone); judges are near chance at first check, monitor one to two orders of magnitude cheaper per check.
- **Admitted limitations / future work**: trained on GPT-family SWE-rebench trajectories, executors are GPT/Claude (not open small models).
- **Relevance**: Shows general LLM judges are near chance at predicting failure, supporting the view that weak judges cannot rescue small policies.

#### Where Should a Stuck Agent Spend Its Next Tokens?: Causal Attribution of Inference-Time Resources (BRA)
- **Ref**: Lyu et al., arXiv 2610.28834, Oct 2026, https://arxiv.org/abs/2610.28834
- **Contribution**: Banzhaf Resource Attribution: a factorial design measuring marginal value of computation, information (spec/hints) and feedback (test results) for repairing a failed state, on 194 function-level (MBPP+/HumanEval+) and 126 SWE-bench Verified failures, six models including Qwen3-4B/14B/32B.
- **Numbers**: an audited specification raises held-out utility for every model by 0.06-0.14 (function) and 0.05-0.10 (repo); public-test feedback worth at most 0.03; retrieved repository code about zero; value of extra computation declines with capability while information stays useful; three of four frontier models choose feedback in 95-100% of cases and do worse than uniform random resource choice.
- **Admitted limitations / future work**: one revision step only (no multi-step loop); feedback measured as information, not as a verifier or stop signal; oracle information rungs show what information would do, not what a system can obtain.
- **Relevance**: Single-step repair of a failed state with small Qwen3 models: suggests test feedback is a weak use of the budget versus better specifications; not tested in a full agent loop.

#### Ask Your Advisor: Learning When to Consult Stronger Models in Agentic Systems (ARIA)
- **Ref**: Sowietzki et al., arXiv 2610.13870, Oct 2026, https://arxiv.org/abs/2610.13870
- **Contribution**: Meta-controller that decides SILENT or CONSULT at workflow contact points with Monte Carlo control on cost-penalised outcomes; executor = cheap model, advisor = strong model.
- **Numbers**: across SWE-bench Verified, Terminal-Bench 2.1 and tau2-bench recovers 44-81% of the executor-advisor success gap at under half the advisor cost.
- **Admitted limitations / future work**: single model pair and Magentic-One framework; gains smaller on heterogeneous tasks.
- **Relevance**: Executor-advisor is the multi-model analogue of a local small model with an occasional stronger consultant; needs an advisor, which a private setting may not allow.

#### JevCoder: JevCoder: When Does Decision Delegation Pay Off in Code Repair?
- **Ref**: Zhang et al., arXiv 2610.19596, Oct 2026, https://arxiv.org/abs/2610.19596
- **Contribution**: Delegates repair decisions (which snippet, which action type, when to submit) to a low-cost probabilistic judge that answers over predefined options without generating text.
- **Numbers**: 400 tasks (200 SWE-bench Verified + 200 SWE-Bench Pro Verified), three repair models: mean repair-model token use down 21.6-50.6% with higher observed repair rates.
- **Admitted limitations / future work**: single run per task/condition (no run-to-run variance), one judge version, one agent framework; labels are proxies; the smaller model stalls more often.
- **Relevance**: A judge that outputs a probability over fixed options (not text) is cheap enough for a 30-call budget; note single-run noise.

#### DeskCheck: Enforcing Code Reasoning in Agentic Scaffold for More Effective Issue Resolution
- **Ref**: Liu et al., arXiv 2610.23782, Oct 2026, https://arxiv.org/abs/2610.23782
- **Contribution**: Studies 7,955 trajectories from six single- and multi-agent scaffolds; code reasoning (12 forms) appears in 66.95% and correlates with resolution but is unguided. DeskCheck prompts execution-path simulation for localisation, patch simulation for refinement, requirement audit and corner-case reasoning before test writing.
- **Numbers**: on 731 SWE-bench-Pro instances improves mini-SWE-Agent and Claude Code by 6.29% to 10.53% (abstract does not say absolute or relative) for USD 0.02-0.28 extra per instance (mean 0.14); McNemar p < 1e-10; repeated runs for nondeterminism.
- **Admitted limitations / future work**: (Sec. 7) trajectories from a limited set of scaffolds/models; non-determinism.
- **Relevance**: A prompt-only review loop with tiny overhead; but subject LLMs are frontier; whether a 4B model can simulate execution reliably is untested.

#### Kimi-Dev: Kimi-Dev: Agentless Training as Skill Prior for SWE-Agents
- **Ref**: Yang et al. (Moonshot), arXiv 2509.23045, Sep 2025, https://arxiv.org/abs/2509.23045
- **Contribution**: Argues Agentless-style training (localisation, edit, self-reflection) induces skills that transfer to agent scaffolds after light SFT.
- **Numbers**: 60.4% on SWE-bench Verified in the workflow (Agentless) setting; with 5k public trajectories SFT, SWE-agent pass@1 48.6% (comparable to Claude 3.5 Sonnet 241022).
- **Admitted limitations / future work**: advanced agentic RL is left as future work.
- **Relevance**: Workflow format beat agent format for the same weights (60.4 vs 48.6), which hints that fixed pipelines suit limited-step regimes.

### 2.5. Small models, context compaction and constrained budgets

#### SWEnergy: SWEnergy: Energy Efficiency in Agentic Issue Resolution Frameworks with SLMs
- **Ref**: Tripathy et al., AGENT 2026 (ICSE workshop) / arXiv 2512.09543, Dec 2025, https://arxiv.org/abs/2512.09543
- **Contribution**: Controlled study of SWE-Agent, OpenHands, mini-SWE-agent and AutoCodeRover run with Gemma-3 4B and Qwen-3 1.7B on SWE-bench Verified Mini (50 tasks), 150 runs per configuration, measuring energy, time, tokens, memory.
- **Numbers**: resolution near zero: only AutoCodeRover with Qwen 1.7B solved any (2 of 50 = 4%), 0% for all other framework/model pairs including every Gemma-3 4B configuration; framework choice drives energy (AutoCodeRover+Gemma used 9.4x the energy of OpenHands+Gemma) and the extra energy is wasted on unproductive reasoning loops.
- **Admitted limitations / future work**: (Sec. 7) energy measured from CPU/GPU counters only (no wall-plug); binary SWE-bench harness metric; recommends external verification (CI) before accepting SLM patches and architectures that "actively manage SLM weaknesses".
- **Relevance**: The only 4B Gemma data point found: off-the-shelf frameworks with Gemma-3 4B resolve 0%; a Gemma 4 4B result would have to be framed against this floor.

#### Bud ContextCompact 2.0: Context Compaction for Agent Success and Accuracy with Small Language Models and Constrained Context Windows
- **Ref**: VG & PS (Bud), arXiv 2610.25516, Oct 2026, https://arxiv.org/abs/2610.25516
- **Contribution**: LLM-summary compaction for constrained windows, evaluated on recall questions over recorded sessions and on 100 SWE-bench Verified tasks run end to end by a 27B reasoning model with a 49K-token window (556 graded sessions).
- **Numbers**: resolve rate on long sessions 41% -> 53% (+12.3 pts, 95% CI +1.6 to +23.0, McNemar p = 0.043), unchanged on short sessions, 13% fewer tokens per solved task at equal total cost; recall: 1.2B model at 16K budget 0.335 vs 0.247 truncation vs 0.176 full 32K history; gain vanished (-3.3 pp, p = 0.48) under a 45-minute session budget because each summary took a median 161 s; compaction threshold study: 24K trigger +13.9 pp on long pairs, 48K trigger fired in only 4 of 50 sessions (no effect); an 8B model submitted after about 10 turns at 5-8K tokens and never needed compaction; main failure without compaction was a reasoning turn exhausting the room left by the history, not history overflow.
- **Admitted limitations / future work**: gains bounded by time cost of summaries and by trigger timing; time cost scales with hardware and must be budgeted.
- **Relevance**: Closest paper to the target setting (compaction trigger, constrained window, time budget); shows that compaction latency can cancel its accuracy gain under a wall-clock cap and that the trigger point matters.

#### CAT / SWE-Compressor: Context as a Tool: Context Management for Long-Horizon SWE-Agents
- **Ref**: Liu et al., arXiv 2512.22087, Dec 2025, https://arxiv.org/abs/2512.22087
- **Contribution**: Makes context compression a callable tool in the agent's action space with a structured workspace (task semantics, condensed long-term memory, high-fidelity short-term interactions); trajectory-level supervision (CAT-GENERATOR) to train SWE-Compressor on Qwen2.5-Coder-32B.
- **Numbers**: SWE-bench Verified 57.6% (OpenHands scaffold, 32B) vs 49.8% ReAct baseline and 53.8% threshold-compression baseline.
- **Admitted limitations / future work**: no limitation section located in HTML.
- **Relevance**: Agent-initiated compaction at milestones outperforms fixed-threshold compaction (53.8 -> 57.6) for a 32B model under a bounded budget; requires SFT.

#### CompactionRL: CompactionRL: Reinforcement Learning with Context Compaction for Long-Horizon Agents
- **Ref**: Li et al. (Zhipu/Tsinghua), arXiv 2607.05378, Jul 2026, https://arxiv.org/abs/2607.05378
- **Contribution**: RL that jointly optimises task execution and summary generation across compaction segments (token-level loss normalisation, cross-segment GAE).
- **Numbers**: GLM-4.5-Air (106B-A12B) 66.4% on SWE-bench Verified, +6.6 over the base under inference-time compaction; GLM-4.7-Flash (30B-A3B) +5.5 to 56.0%; Terminal-Bench 2.0 26.2% and 20.2%.
- **Admitted limitations / future work**: none extracted.
- **Relevance**: Untrained models are weak summarisers/consumers of their own summaries; training for compaction yields +5.5 to +6.6 points even at 30B-A3B.

#### Beyond the Model: Demystifying Harness Effects in Software Engineering Agents
- **Ref**: Hu et al., arXiv 2609.32459, Sep 2026, https://arxiv.org/abs/2609.32459
- **Contribution**: Evaluates mini-SWE-agent and OpenCode with ten Qwen and DeepSeek models on SWE-bench Pro, ProgramBench, GitTaskBench; builds NanoHarness (modular, on mini-SWE-agent) to ablate tool registry, context compression, explicit planning, subagents, lazy skills.
- **Numbers**: harness gains shrink with model strength (OpenHands over mini-SWE-agent +13.60 pp with Claude 3.7 Sonnet vs +5.47 pp with Claude 4 Sonnet; SWE-agent +9.60 -> +4.07); on ProgramBench structured tool use and task-specific subagents most stable, while context compression and general subagents can hurt; combined NanoHarness +7.37 / +6.21 pp over mini-SWE-agent on Qwen3.7-Max / DeepSeek-V4-Pro with tool calls +131% / +84% but prompt tokens only +16% / +7%.
- **Admitted limitations / future work**: (Sec. 7) five components only; Qwen and DeepSeek families only; primary component study on ProgramBench, so conclusions may not transfer to issue-repair datasets; cost over USD 7,000.
- **Relevance**: Evidence that scaffold complexity helps weaker models more, but the component ablation was on large models and a non-issue-repair benchmark; no small-model or 32k-window ablation.

#### icat-agent: Unlocking Model Potentials Through Adaptive Multi-Agent Scaffolding for Efficient Issue Resolution
- **Ref**: Chen et al., arXiv 2606.25514, Jun 2026, https://arxiv.org/abs/2606.25514
- **Contribution**: Decentralised multi-agent scaffold with event-based message passing instead of shared context; a rubric-based issue-quality check decides between parallel patch+validate (well-defined issues) and preliminary exploration (poor issues).
- **Numbers**: +3.6-8.4% on SWE-bench Verified and +6.3-18.5% on SWE-bench Pro over SWE-agent, mini-SWE-agent and Claude Code with the same models; GPT-5.4-xhigh 67.4% on Pro vs 59.10% mini-SWE-agent best; USD 1.18 cheaper per instance than Claude Code multi-agent.
- **Admitted limitations / future work**: (Sec. 5) program repair only, benchmark repos smaller than industrial codebases.
- **Relevance**: Issue-quality triage before committing budget is a cheap idea for a time-capped setting; frontier models only.

#### DeLM: Decentralized Multi-Agent Systems with Shared Context
- **Ref**: Mao et al. (Stanford, Mirhoseini group), arXiv 2606.10662, Jun 2026, https://arxiv.org/abs/2606.10662
- **Contribution**: Replaces the main agent by a shared context plus task queue; agents claim tasks asynchronously and publish findings immediately, removing waiting "bubbles".
- **Numbers**: on Terminal-Bench 4.0, DeepSWE v1.1 and SWE-bench Verified more accurate (up to +17.5 points) and up to 2.49x faster than Codex, Claude Code, their native subagents and AOrchestra; ProgramBench 120-minute budget up to +19.9 points.
- **Admitted limitations / future work**: instantiated on Codex and Claude Code only.
- **Relevance**: Parallel agents trade GPU throughput for latency; on a sequential 4x L4 queue the parallelism may be unavailable.

#### Librarian: Long Live the Librarian! A Persistent Search Sub-Agent for Energy-Efficient Multi-Agent SWE Systems
- **Ref**: Cho et al., EMNLP 2026 Main / arXiv 2605.27787, May 2026, https://arxiv.org/abs/2605.27787
- **Contribution**: Persistent search sub-agent that remembers repository-search history and returns short pointers instead of file excerpts; finds an output token costs 30-1,000x more energy than an input/cached token.
- **Numbers**: reduces per-episode GPU energy of existing multi-agent SWE systems by 11-30% on SWE-Bench Verified and SWE-Bench-Live while preserving task performance; open backbones tested in the roughly 3B-27B active-parameter range.
- **Admitted limitations / future work**: limited to code navigation (the execution sub-agent also duplicates outputs); open models only up to about 27B active, unknown beyond.
- **Relevance**: Output-token cost dominates, so a reading sub-agent that returns pointers lowers both context pressure and energy for 3-27B models.

#### FastContext: FastContext: Training Efficient Repository Explorer for Coding Agents
- **Ref**: Zhang et al., arXiv 2606.14066, Jun 2026, https://arxiv.org/abs/2606.14066 (arXiv comment states the article "needs to be withdrawn and re-approved" for product-IP reasons; treat as unstable)
- **Contribution**: Dedicated exploration subagent (4B-30B models) returning file paths and line ranges to the solver, keeping exploratory reads out of the solver context.
- **Numbers**: with Mini-SWE-Agent up to +5.5% resolution and up to -60% tokens on SWE-bench Multilingual, SWE-bench Pro, SWE-QA.
- **Admitted limitations / future work**: not extracted.
- **Relevance**: Small explorer model + clean solver context is the architecture most compatible with a 32k window; caveat on withdrawal notice.

#### Terminus-4B: Can a Smaller Model Replace Frontier LLMs at Agentic Execution Tasks?
- **Ref**: Garg et al., arXiv 2605.03195, May 2026, https://arxiv.org/abs/2605.03195 (arXiv comment: needs to be withdrawn and re-approved; treat as unstable)
- **Contribution**: Post-trained Qwen3-4B (SFT + RL with rubric LLM-judge reward) as a terminal-execution subagent that absorbs verbose build/test output.
- **Numbers**: main-agent token use down up to about 30% vs no subagent with no performance loss on SWE-Bench Pro and an internal C# benchmark; matches or exceeds frontier models as the subagent.
- **Admitted limitations / future work**: not extracted.
- **Relevance**: A 4B model is credible in a narrow subagent role (execution/log summarisation) rather than as the main solver.

#### BOAD: BOAD: Discovering Hierarchical Software Engineering Agents via Bandit Optimization
- **Ref**: Xu et al. (IBM), arXiv 2512.23631, Dec 2025, https://arxiv.org/abs/2512.23631
- **Contribution**: Searches orchestrator/sub-agent hierarchies (localisation, editing, validation) as a multi-armed bandit under limited evaluation budget.
- **Numbers**: beats single-agent and hand-designed multi-agent baselines on SWE-bench Verified; on SWE-bench-Live a 36B system ranks second on the leaderboard at evaluation time.
- **Admitted limitations / future work**: not extracted.
- **Relevance**: A decomposition into small-context specialists is evaluated at 36B; no budget-matched comparison to a single agent given the same tokens.

#### MASAI: MASAI: Modular Architecture for Software-engineering AI Agents
- **Ref**: Arora et al., arXiv 2406.11638, Jun 2024, https://arxiv.org/abs/2406.11638
- **Contribution**: Sub-agents with distinct objectives and strategies to avoid long trajectories that inflate cost and add extraneous context.
- **Numbers**: 28.33% on SWE-bench Lite (highest at the time of writing).
- **Admitted limitations / future work**: not extracted (2024 paper, included briefly).
- **Relevance**: Early modular design argument now partly countered by 2026 harness studies.

#### Multi-agent evidence: Adversarial Review, task-structure bound, Inverse-Wisdom Law
- **Ref**: (a) Qiu et al., ICML 2026 DL4C workshop / arXiv 2608.18167, Aug 2026, https://arxiv.org/abs/2608.18167; (b) Pan & Luo, arXiv 2606.13733, Jun 2026, https://arxiv.org/abs/2606.13733; (c) Shehata & Li, arXiv 2604.27274, Apr 2026, https://arxiv.org/abs/2604.27274
- **Contribution**: (a) 3-agent reviewer+critic protocol; naive version shows a false-consensus failure mode and needs explicit structured disagreement. (b) Theory: MAS success probability decays exponentially with the minimum cut of the task constraint graph; checked on SWE-bench submissions. (c) 12,804 trajectories over GAIA/Multi-Challenge/SWE-bench: adding same-family logical agents makes erroneous trajectories more stable ("Consensus Paradox"), recommends heterogeneous agents.
- **Numbers**: (a) with Claude Sonnet 4.5 on LiveCodeBench AR (3 agents) beats a five-agent baseline, while same-model Self-Refine gives 77% = zero-shot 77% (critic and generator make the same mistakes); SWE-bench Verified: improvements over baselines (numbers not extracted). (b)/(c) theoretical and cross-model results, no small-model data.
- **Admitted limitations / future work**: not extracted (workshop / preprint papers).
- **Relevance**: Three independent 2026 sources suggest more agents or more reviews do not scale; same-model review risks false consensus, which matters if the only critic available is the policy itself.

### 2.6. Small-model critics, steering, compression (2026)

#### Steer, Don't Solve: Training Small Critic Models for Large Code Agents
- **Ref**: Gandhi et al. (CMU), arXiv 2606.21811, Jun 2026, https://arxiv.org/abs/2606.21811
- **Contribution**: Fine-tuned 4B and 8B critics (SFT + DPO on a SWE error taxonomy) give high-level guidance without writing concrete actions, applied periodically to larger agents.
- **Numbers**: SWE-bench Verified and Multi-SWE-bench with mini-SWE-agent, 150-step budget: improves six larger agents, e.g. GLM-4.7-Flash-30B-A3B by 16.0% and GPT-OSS-120B by 14.4% resolved rate; GPT-OSS-20B per-example cost USD 0.07 -> 0.03 (fewer steps).
- **Admitted limitations / future work**: only SWE-bench Verified and Multi-SWE-bench, mini-SWE-agent scaffold, periodic intervention; error taxonomy is issue-solving specific; critics inherit teacher critic limits and depend on the preference judge.
- **Relevance**: Positive counterpart to SWE-PRM: a small critic works when it is trained, and it steers instead of solving; a 4B critic fits next to a 31B policy on L4s. The policy is not itself a small model.

#### PAUSE: PAUSE: Search-Free Steering of Coding Agents Before Their First Source-Code Edit
- **Ref**: Patel et al., arXiv 2610.29870, Oct 2026, https://arxiv.org/abs/2610.29870
- **Contribution**: One planning intervention: intercept the first edit request (median at 60% of trajectory progress), a Planner reads the transcript and writes one repair plan, the same Executor resumes in the same context and workspace.
- **Numbers**: Qwen3-Coder Executor + GPT-5.6 Sol Planner: +16.8% on SWE-bench Verified (relative vs absolute not specified in the abstract) in OpenHands, +14.7% on Multilingual in SWE-agent; +3.2% / +3.7% over LivePlan at similar planner cost; comparable to SICA's periodic overseer at 11-15% of its Planner cost; offline recovers 35.4% of eligible failed Verified tasks using 33-41% fewer Executor tokens than restart.
- **Admitted limitations / future work**: not extracted (no limitations section located).
- **Relevance**: A single intervention is compatible with a ~30-call budget, but the Planner is a frontier model.

#### ROFT: Shockingly Simple Self-retrospection Improves Agentic Models Without RL
- **Ref**: Light et al., arXiv 2609.35741, Sep 2026, https://arxiv.org/abs/2609.35741
- **Contribution**: Retrospection-Only Fine-Tuning: the agent attempts a task, sees feedback, writes a retrospective explanation, and is fine-tuned on explanation tokens only (no teacher, no reward).
- **Numbers**: Qwen3.5-4B reaches 49.2% on SWE-bench Verified and 26.8% on Pro after 20 updates without a verifier, vs GRPO 48.0% / 25.3% after 40 updates; solves tasks where all 64 base samples failed.
- **Admitted limitations / future work**: (Sec. 5) cost limits breadth (one 40-update GRPO run about USD 500; one SWE-bench Pro eval about USD 200 GPU); only software engineering with Qwen3.5-4B; ROFT chosen for simplicity not optimality.
- **Relevance**: The only 4B result found with ~49% on Verified (training-time, not inference-time); suggests a 4B base can be strong, so inference-time methods for 4B models should be compared with such trained baselines.

#### LOHA/ACD: Compress What You See, Not What You Say: Anchored Context Distillation for Latent-Observation SWE Agents
- **Ref**: Zou et al. (Peking Univ.), arXiv 2609.31430, Sep 2026, https://arxiv.org/abs/2609.31430
- **Contribution**: Compresses older tool observations into soft tokens, keeps the agent's own turns and the last K observations in text; anchored distillation limits behavioural drift.
- **Numbers**: SWE-bench Verified, K=3: context per call -43% (Qwen3-4B) and -57% (SWE-Master-4B-RL); resolve rates 12.1% and 21.8% vs 14.5% and 27.5% uncompressed; under a 32K-token limit Qwen3 K=3 resolves 21.1% of a 199-instance subset vs 11.1% for the full-text agent; 1.9x instance throughput on one GPU.
- **Admitted limitations / future work**: single-run recency sweep; at K=3 compression costs 2.4 and 5.7 points versus the uncompressed bases (12.1 vs 14.5, 21.8 vs 27.5), and larger K generally favours accuracy over compression.
- **Relevance**: Shows the 4B + 32K regime: overflow, not compaction loss, dominates under 32K; requires training and soft-token support.

#### Paritok-4B: Intent-Conditioned Context Compression for Coding Agents
- **Ref**: Shi & Chen, arXiv 2608.24188, Aug 2026, https://arxiv.org/abs/2608.24188
- **Contribution**: Extractive 4B LoRA compressor conditioned on the agent's current intent, distilled from 67,074 OpenHands trajectories.
- **Numbers**: SWE-bench Lite (300): context compressed to 25.7% of size, retaining 86.5% of uncompressed single-shot solve quality (89.3% with cat -n inputs; McNemar p = 0.079, not significant); 96% of emitted identifiers/paths/numbers come verbatim from input; fits on one 24 GB GPU.
- **Admitted limitations / future work**: (Sec. 7) roughly 60% of identifier-like tokens do not survive compression so a needed identifier can be lost (needs presence check and fallback to original); under-drops (drop recall 0.24); occasional line reflow can break exact-match edits; Python-heavy training data; single-shot rather than multi-turn evaluation.
- **Relevance**: 24 GB footprint matches L4; extractive compression avoids paraphrase errors that LLM summaries make.

#### Compression gateway costs: An Empirical Cost Attribution of Context-Compression Gateways in Multi-Turn Coding Agents
- **Ref**: Chen & Shi, arXiv 2609.22114, Aug 2026, https://arxiv.org/abs/2609.22114
- **Contribution**: Decomposes the token bill with Claude Code/Codex sessions into tool-schema filtering, content compression and history summarisation.
- **Numbers**: tool-schema filtering saves 21K-57K tokens per turn (linear in turns, the only unambiguously positive lever); content compression saves about 2% of the cache-priced prefix per turn but accumulates quadratically (about 3350*N^2 tokens), overtaking schema filtering within about 6 turns; single-shot compression benchmarks (86.5% quality retained) are orthogonal to multi-turn agent cost.
- **Admitted limitations / future work**: frontier closed models only, cost not accuracy.
- **Relevance**: Reminds that compaction savings depend on prompt-cache pricing assumptions that do not apply to a local GPU, where latency is the cost.

#### TreeFlex: TreeFlex: Agents Navigating Their Own Search Trees
- **Ref**: Li et al., arXiv 2610.20334, Oct 2026, https://arxiv.org/abs/2610.20334
- **Contribution**: The harness keeps a tree of checkpointed states with short summaries; the policy alternates Reflection (choose a node to resume) and Execution roles; RL-trained with tree-aware GRPO.
- **Numbers**: 4B model: 48.8% on a deep-research benchmark vs 41.5% flat ReAct, 42.8% FoldAgent (same active-context limit); on SWE-bench Verified with a 9B model 54.9% vs 43.3% FoldAgent and 45.2% step-wise variant.
- **Admitted limitations / future work**: not extracted.
- **Relevance**: Backtracking under a bounded active context beats linear folding/compaction for a 9B RL-trained policy; requires RL training.

#### LLM-judge intervention timing: The Saturation Trap and the Subjectivity of Intervention Timing
- **Ref**: Modgil, arXiv 2606.04296 (v2 with erratum), Jun 2026, https://arxiv.org/abs/2606.04296
- **Contribution**: On SWE-bench-Verified debugging traces compares four trigger families for when to interrupt an agent against human-annotated intervention points.
- **Numbers**: small LLM-judge (gpt-5.4-mini) never fires; frontier judges reach only F1 0.17-0.40 at up to 90x cost and need full-trajectory context; three trained annotators agree barely above chance (Krippendorff alpha +0.047 for location). v2 erratum: the modelled-frustration trigger had a bug (decay never ran).
- **Admitted limitations / future work**: single-annotator F1 is an unsuitable optimisation target; small sample (five trajectories, 56-action annotation).
- **Relevance**: Evidence of a capability and context floor for judges, and that the "right moment to intervene" is poorly defined.

### 2.7. Search, selection and evolving scaffolds with open models

#### Satori-SWE (EvoScale): Evolutionary Test-Time Scaling for Sample-Efficient Software Engineering
- **Ref**: Zeng et al. (IBM/MIT), arXiv 2505.23604, May 2025, https://arxiv.org/abs/2505.23604
- **Contribution**: Treats generation as an evolutionary process (select and mutate previous patches); the 32B model is RL-trained to self-improve its own scores across iterations so no external verifier is needed at inference.
- **Numbers**: SWE-bench Verified, Agentless-style pipeline, Satori-SWE-32B: greedy 35.8%, Best@10 38.9%, Best@25 40.2%, Best@50 41.6% (Llama3-SWE-RL-70B needs Best@500 for 41.0%).
- **Admitted limitations / future work**: pipeline-based (agentless) setup only; extending to agentic settings with runtime interaction is future work. Authors note their method keeps only the most recent output in the prompt, to suit long contexts.
- **Relevance**: Sample-efficiency at k about 10 with a 32B model and no verifier, but no agent loop and no wall-clock constraint.

#### Guided Search in Non-Serializable Environments: Guided Search Strategies in Non-Serializable Environments with Applications to SWE Agents
- **Ref**: Zainullina et al. (Nebius), ICML 2025 / arXiv 2505.13652, May 2025, https://arxiv.org/abs/2505.13652
- **Contribution**: MCTS-like search is unavailable when Docker states cannot be saved/restored, so uses 1-step lookahead and trajectory selection guided by a learned action-value critic.
- **Numbers**: doubles the average success of a fine-tuned Qwen2.5-72B to 40.8% on SWE-bench Verified; also transfers to GPT-4o. Critic base model ablation on Verified-50, 1-step lookahead: no critic 16.2%, Qwen2.5-7B critic 20.2%, Llama3.1-8B 21.0%, Qwen2.5-72B 22.8%, Llama3.1-70B 26.8% (so even 7-8B critics help).
- **Admitted limitations / future work**: not extracted (no explicit section located).
- **Relevance**: Small (7-8B) value critics already give +4-5 points; search without environment snapshots is the realistic option on shared GPUs.

#### Live-SWE-agent: Live-SWE-agent: Can Software Engineering Agents Self-Evolve on the Fly?
- **Ref**: Xia et al., arXiv 2511.13646, Nov 2025, https://arxiv.org/abs/2511.13646
- **Contribution**: Starts from the mini-SWE-agent bash-only scaffold and lets the agent write its own helper tools/scripts at run time (online self-evolution), with no offline training.
- **Numbers**: SWE-bench Verified: mini-SWE-agent -> Live-SWE-agent: GPT-5-Mini 59.8% -> 63.0%, GPT-5 65.0% -> 68.4%, Claude 4.5 Sonnet 70.6% -> 75.4%, Gemini 3 Pro 74.2% -> 77.4% (one patch per issue, no TTS); SWE-Bench Pro 45.8%.
- **Admitted limitations / future work**: evaluation of generalisation limited to SWE-bench Verified, Multilingual and Pro; models are frontier or mini-class proprietary.
- **Relevance**: Gain shrinks for the smallest model (+3.2 for GPT-5-Mini vs +4.8 for Sonnet); dynamic tool authoring consumes steps that a 30-call budget lacks.

#### Kozuchi Agent: A Language-Agnostic Open-Weight Agent for Software Repair
- **Ref**: Bahrami et al. (Fujitsu), ASE 2026 Industry Showcase / arXiv 2608.15579, Aug 2026, https://arxiv.org/abs/2608.15579
- **Contribution**: Phase-structured agent (persistent state, deterministic tools, model-independent action interface) with cross-agent test-time selection; run with locally hosted Qwen3.5-27B, no fine-tuning.
- **Numbers**: SWE-bench Verified 374/500 (74.8%) at TTS@8; single runs pass@1 334-343/500 (66.8-68.6%); oracle best-of-8 408/500 (81.6%); cross-agent selector 376 vs 362 for ordering and 346 for selection by the agents' own tests; Multi-SWE-bench Java 41/128 (32.03%). 408 instances solved by at least one run, 234 by all, 92 by none.
- **Admitted limitations / future work**: remaining gap "primarily semantic correctness and selection rather than edit formatting or proprietary-model access"; Java-specific harness issues.
- **Relevance**: Best documented 27B-class local result; selector regret of 34 instances (about 7 points) with k=8 and shows self-generated tests as selection signal can be worse than a simple ordering rule.

#### Live vs. static analysis: From Finding to Fixing: How Useful is Fault Localization for Agentic Program Repair?
- **Ref**: Shi et al., arXiv 2610.25826, Oct 2026, https://arxiv.org/abs/2610.25826
- **Contribution**: Six FL methods x three LLMs on SWE-bench Verified and Defects4J, 16,248 repair trajectories; also gold locations and bug-cause descriptions as guidance.
- **Numbers**: FL methods do not consistently improve repair success and higher localisation accuracy does not consistently give larger repair gains; accurate locations can cut repair token use by up to 39.2% but current FL methods often consume more tokens than they save; bug causes help beyond locations alone.
- **Admitted limitations / future work**: single reference patch does not capture all locations used by successful repairs.
- **Relevance**: Pre-agent localisation stages (Agentless-style) are not automatically worth their token cost, important when budget is 30 calls.

#### AgentLens: AgentLens: Revealing The Lucky Pass Problem in SWE-Agent Evaluation
- **Ref**: Sahoo et al., arXiv 2605.12925, May 2026, https://arxiv.org/abs/2605.12925
- **Contribution**: Process-level scoring of 2,614 OpenHands trajectories from eight model backends on 60 SWE-bench Verified tasks.
- **Numbers**: 10.7% of passing trajectories are "Lucky Passes" (regression cycles, blind retries, missing verification); lucky rate ranges 0.5% to 23.2% depending on backend; models move up to five rank positions when ranked by process quality instead of pass rate.
- **Admitted limitations / future work**: 47 of 60 tasks had enough passing trajectories for references; repository to be released.
- **Relevance**: A pass/fail metric hides process quality; matters when comparing weak models or review loops that may make lucky passes.

#### Arctic-SWE: Revisiting the Long Horizon Agent Training by Modeling-System Co-Design
- **Ref**: Liu et al. (Snowflake), arXiv 2610.24914, Oct 2026, https://arxiv.org/abs/2610.24914
- **Contribution**: Asynchronous RL recipe; model-side rather than scaffold-side, listed because it sets the small-model bar.
- **Numbers**: Qwen3.5-4B: 47.4% -> 62.0% pass@1 on SWE-bench Verified on raw R2E-Gym, and 65.0% / 38.3% / 59.7% on Verified / Pro-v1 / Pro-v2 with curated data; Qwen3.5-9B 56.2% -> 65.7% on Verified.
- **Admitted limitations / future work**: stronger tests reduce apparent training-task mastery; small task pool testbed.
- **Relevance**: A 4B model reaches 62-65% on Verified when RL-trained for long horizons, so claims about inference-time scaffolds for a 4B model must be compared against trained baselines.

#### SWE-Lego: SWE-Lego: Pushing the Limits of Supervised Fine-tuning for Software Issue Resolving
- **Ref**: Tao et al., arXiv 2601.01426, Jan 2026, https://arxiv.org/abs/2601.01426
- **Contribution**: SFT-only recipe (32k tasks, 18k validated trajectories, error masking, difficulty curriculum) plus a study of sequential vs parallel test-time scaling with generative vs regression verifiers.
- **Numbers**: SWE-bench Verified: Qwen3-8B 42.2%, Qwen3-32B 52.6% (57.6% in a second table setting); TTS@16: 8B 42.2 -> 49.6, 32B 52.6 -> 58.8; sequential scaling (more turns) saturates around 100-140 turns, beyond which parallel rollouts are a better use of compute; generative verifiers beat regression-based scorers; 8B rollouts: verifier size matters little, 32B rollouts: a 30B verifier beats an 8B verifier especially at higher K.
- **Admitted limitations / future work**: (App. C) beyond bug fixing (features, refactoring), multilingual, richer correctness dimensions lack data and benchmarks.
- **Relevance**: An 8B model gains +7.4 points from K=16 with a trained verifier; the serial-vs-parallel finding is for 100+ turns, a regime far from 30 calls, so the crossover below 30 turns is not characterised.

#### Co-PatcheR: Co-PatcheR: Collaborative Software Patching with Component(s)-specific Small Reasoning Models
- **Ref**: Tang et al., arXiv 2505.18955, May 2025, https://arxiv.org/abs/2505.18955
- **Contribution**: Three 14B specialist reasoning models (localisation+patch generation with critique; two test/judge models for validation) with majority-vote selection, run one at a time, on a fixed PatchPilot-style scaffold.
- **Numbers**: 46% on SWE-bench Verified with 60 patch candidates (3 x 14B), vs SWE-RL 70B at 41% with 40% fewer parameters and 88% fewer samples; too many samples can burden validation and jeopardise accuracy.
- **Admitted limitations / future work**: (Sec. 5) rationalised reasoning data can teach hallucinated identifiers (6 of 10 regressions); open question whether one end-to-end model would be better than component-specific models; OpenHands higher but less stable and costlier than the chosen scaffold.
- **Relevance**: Small specialists with a fixed pipeline (not an open-ended agent) reach 46% but need 60 candidates, impractical at 6 minutes per task.

### 2.8. Agentic review loops

#### SWE-Review: SWE-Review: Closing the Loop on Issue Resolution with Agentic Code Review
- **Ref**: Wang et al. (SWE-Lego team), arXiv 2607.06065, Jul 2026, https://arxiv.org/abs/2607.06065
- **Contribution**: A reviewer agent explores the repository, accepts or requests changes with structured feedback, and the generator revises (generate-review-revise). SWE-Review-Bench measures completion rate, decision accuracy (DA) and resolve rate after revision (RRR, one revision attempt); SWE-Review-Traj trains open reviewers.
- **Numbers**: with Claude Opus 4.6 as reviewer, generate-review-revise raises SWE-bench Verified resolve rate for Qwen3-30B-A3B from 27.5% to 56.9%, Qwen3-Coder-30B-A3B 50.9% -> 68.8%, GLM-5 72.2% -> 75.4% (multi-round loop); agentic review beats single-turn fixed-context review on DA and RRR for all three generators, most on hard non-local tasks. Untrained 8B reviewer completes only about 4% of reviews with near-random decision accuracy; SFT on review trajectories gives 71-84% completion and 67-72% decision accuracy. Reviews cost about 120K-207K tokens per instance (rounds 2.4 to 5.1).
- **Admitted limitations / future work**: (Limitations) functional metrics only (no style or maintainability); SWE-style issue resolution only; comparisons limited to chosen tasks, repos, model families and the OpenHands-SDK scaffold.
- **Relevance**: Strongest published case for a review loop, but with a frontier reviewer and 120K+ tokens per review; the untrained-8B-reviewer result (near random) is the relevant warning for a small model reviewing itself; a review of 150K tokens does not fit in a 32k window with 14k compaction.

### 2.9. Verification as a scaling axis, evaluation noise, grey literature

#### LLM-as-a-Verifier: LLM-as-a-Verifier: A General-Purpose Verification Framework
- **Ref**: Kwok et al. (Stanford, Finn group), arXiv 2607.05391, Jul 2026, https://arxiv.org/abs/2607.05391
- **Contribution**: Training-free verifier that uses the expectation over scoring-token logits (continuous scores) with scalable granularity (G=20), repeated evaluation (K=8) and criteria decomposition, and a pairwise "probabilistic pivot tournament" to pick among N trajectories.
- **Numbers**: SWE-Bench Verified: pass@1 76.1%, oracle best-of-N 84.4%, verifier-selected 78.2% (best single model on leaderboard Opus 4.5 76.8%); Terminal-Bench V2 83.1% / 92.1% / 86.5%. Verifier in scaling experiments is Gemini 2.5 Flash (a small, cheap model). Standard 1-5 LM judges collapse nuanced assessments.
- **Admitted limitations / future work**: (App. A) needs scoring-token logits (closed APIs restricted; two-stage workaround via open verifier); axes not exhaustive; RL experiments single-turn only.
- **Relevance**: Even with 8 repeated evaluations of a verifier per pair, selection recovers only 2.1 of 8.3 oracle points on SWE-bench Verified; needs logits, so applicable to local open models, but cost scales with N x K.

#### DeltaSelect: DeltaSelect: Affordable A/B Testing for Coding Agents
- **Ref**: Conn, arXiv 2609.19607, Sep 2026, https://arxiv.org/abs/2609.19607
- **Contribution**: Selects a fixed, budget-bounded task subset whose one-run results track full-benchmark performance, for baseline-versus-candidate comparisons during development.
- **Numbers**: resampling DeepSWE's published trials: only 19.5% of tasks (22 of 113) have a fifth-percentile Pearson correlation of at least 0.50 with full-benchmark performance; case study: 13 evaluations cost USD 27.86; adopted version 58.1% cheaper (p = 0.008), calibrated score 42.36% vs 36.46% (p = 0.326, not significant).
- **Admitted limitations / future work**: intended for development comparisons, not model rankings.
- **Relevance**: A study with few tasks and one run each (a likely constraint with a 6-minute budget) has weak power; single-run differences of a few points are within noise.

#### SWE-Edit: SWE-Edit: Rethinking Code Editing for Efficient SWE-Agent
- **Ref**: Zhang et al., arXiv 2604.26102, Apr 2026, https://arxiv.org/abs/2604.26102
- **Contribution**: Splits the editing interface into a Viewer subagent (extracts task-relevant code on demand) and an Editor subagent (executes edits from natural-language plans) to keep the main agent's context clean; trains a small editor with GRPO.
- **Numbers**: SWE-bench Verified +2.1 pp resolve rate and -17.9% inference cost with Kimi-K2, MiniMax-M2.1, GLM-4.7; GRPO-trained Qwen3-8B with adaptive find-replace / whole-file policy +12.5 pp edit success and parity with GPT-5-nano downstream.
- **Admitted limitations / future work**: not extracted.
- **Relevance**: An 8B editor suffices for mechanical edit execution, supporting a split where the main model plans and a small model applies edits.

#### [Grey literature, not peer reviewed] Gemma 4 26B-A4B on SWE-bench Lite with mini-swe-agent
- **Ref**: ai-muninn.com (practitioner blog, "DGX Spark part 17"), 17 Apr 2026, https://ai-muninn.com/en/blog/swe-bench-lite-gemma4-26b-38-percent (read via web fetch; companion post part 16 on scaffold engineering not read in full)
- **Contribution**: Reproducible report of Gemma 4 26B-A4B-it (FP8, about 3.8B active) driven by mini-swe-agent v2.2.8 and vLLM with a 96K context on a single GB10 machine.
- **Numbers**: 116/300 = 38.67% on SWE-bench Lite (first 171 instances 45%, remaining 129 at 30%); step_limit 100 (default 250); step_limit 250 "too long, never submitted", step_limit 30 "too short, edits cut off"; backticks action format instead of JSON tool_calls (empty tool_calls caused retry loops); str_replace edit tool that must match once; budget prompt (explore by step 15, edit by step 40, submit by step 60); reasoning parser and custom chat template lowered patch quality; NVFP4 broke tool-call tokens; OpenHands with 11 concurrent tools gave 40+ errors per instance; about 19 h wall-clock for 300 tasks on 2 workers (about 7.6 min per task, derived).
- **Admitted limitations / future work**: single run, one author, no confidence interval, QEMU emulation (2-3x slower), model and harness details are blog-level evidence.
- **Relevance**: The only Gemma 4 SWE-bench data point found; shows that a ~30-step cap truncates Gemma 4 agents and that scaffold/protocol choices (tool-call format, edit tool, budget prompt) move results by large amounts.

### 2.10. Late-2026 items relevant to restart, compression and test-time optimisation

#### SWE-Residual: SWE-Residual: Evaluating Starting-State Robustness of Coding Agents
- **Ref**: Li et al., arXiv 2610.25899, Oct 2026, https://arxiv.org/abs/2610.25899
- **Contribution**: 198 "Residual States" from 111 DeepSWE and Terminal-Bench tasks: the repository left by a predecessor agent that declared success while hidden tests still fail; the evaluated agent sees only the original request and the state.
- **Numbers**: across five frontier agents success drops by 20.6-53.5 points on DeepSWE and 20.6-34.9 on Terminal-Bench vs a clean start, and DeepSWE rankings reverse; "acceptance bias": in 58.9-88.2% of failed DeepSWE runs the agent submits with exactly the same tests failing (although most of these pass from a clean start).
- **Admitted limitations / future work**: (App. F) only 198 states, two source benchmarks, three predecessor families; human-produced inherited work not covered.
- **Relevance**: Warns against continuing from a failed attempt's diff (as in FailFast-RestartSmart overlays or any retry that keeps prior edits); a clean restart may be better than a review-and-fix pass on the same workspace.

#### ANTE: ANTE: Anticipate, Then Execute (internal world models for coding agents)
- **Ref**: Ge et al., arXiv 2610.15368, Oct 2026, https://arxiv.org/abs/2610.15368
- **Contribution**: Agentic RL where the policy states a belief about each action's outcome, verified by real execution, giving per-step credit; ANTE-TTO uses the trained forecasts to select among candidate actions at inference without an external scorer.
- **Numbers**: Qwen3-32B 25.0% -> 57.2% pass@1 on SWE-bench Verified (6.2 points above a matched GRPO baseline without belief state); world-model accuracy rises 44% -> 69% during RL.
- **Admitted limitations / future work**: not extracted.
- **Relevance**: Self-scored action selection without a separate verifier is a candidate way to use a spare few calls, but it needs RL training.

#### TraceLite: TraceLite: Efficient Trace Reduction for SWE Agents via Optical Compression and Redundancy Removal
- **Ref**: Xiao et al., arXiv 2610.28612, Oct 2026, https://arxiv.org/abs/2610.28612
- **Contribution**: Training-free compression: recent observations stay as text, older ones are rendered as images, overlapping content is removed, and payloads expire after code edits (phase-level redundancy); no auxiliary LLM call.
- **Numbers**: SWE-bench Verified 78.25% resolve rate with GPT-5.6-Luna and Gemini-3.8-Flash backbones; input tokens -33.05%, API cost -21.30%; only 0.438 s compression latency per observation (contrast with 161 s per LLM summary in Bud ContextCompact).
- **Admitted limitations / future work**: not extracted; requires a vision-capable backbone.
- **Relevance**: Rule-based, non-LLM compaction avoids the latency that cancelled the gain of LLM summarisation under a time cap; vision-input assumption must hold for the local model.

### 2.11. Additions after the devil's-advocate review (2026-10-22)

#### Large Language Monkeys: Scaling Inference Compute with Repeated Sampling
- **Ref**: Brown, Juravsky, Ehrlich, Clark, Le, Re, Mirhoseini, arXiv 2407.21787, Jul 2024 (v3 Dec 2024), https://arxiv.org/abs/2407.21787
- **Contribution**: Coverage (pass@k) grows roughly log-linearly with the number of repeated samples across tasks and models; gains transfer where answers can be verified automatically.
- **Numbers**: SWE-bench Lite with DeepSeek-Coder-V2-Instruct: 15.9% at k=1 to 56% at k=250 (single-sample SOTA then 43%).
- **Admitted limitations / future work**: without automatic verifiers, majority voting and reward models plateau after a few hundred samples.
- **Relevance**: The canonical coverage result; any width study must start from it. It counts samples, not wall-clock.

#### Compute-optimal TTS: Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters
- **Ref**: Snell, Lee, Xu, Kumar, arXiv 2408.03314, Aug 2024, https://arxiv.org/abs/2408.03314
- **Contribution**: Allocates test-time compute per prompt by difficulty (search against PRMs, revisions); FLOPs-matched comparison with larger models.
- **Numbers**: more than 4x efficiency over best-of-N; a smaller model with test-time compute beats a 14x larger one on prompts where it has some success.
- **Admitted limitations / future work**: math reasoning; cost in FLOPs.
- **Relevance**: The "small model + more compute vs bigger model" question at matched cost, here in FLOPs; our setting needs it at matched wall-clock on one machine.

#### Latency-aware TTC: Latency and Token-Aware Test-Time Compute
- **Ref**: Huang, Damani, El-Kurdi, Astudillo, Sun, arXiv 2509.09864, Sep 2025, https://arxiv.org/abs/2509.09864 (HTML read)
- **Contribution**: Per-query choice among best-of-N, majority voting and beam search with a cost that includes wall-clock latency (generation + PRM scoring) and tokens.
- **Numbers**: one A100 80GB, Qwen2.5-1.5B generator, Qwen2.5-Math-PRM-7B; batch size set equal to the candidate count so "latency grows only modestly with N" (asserted, no latency-vs-N curve); adaptive strategy near 0.50 accuracy at about 40 s on NuminaMath-CoT.
- **Admitted limitations / future work**: per-strategy average costs stand in for per-query costs; one GPU; math only, coding and dialogue left to future work.
- **Relevance**: The closest prior work on latency-aware width vs depth, single-turn math. Coding agents with tool calls and a wall-clock cap are explicitly future work there.

#### Risa wall-clock note (Appendix I.1 of 2608.22191)
- **Ref**: Chen, Nian, Cao, Jiang, arXiv 2608.22191, Aug 2026, Appendix I.1 (HTML read)
- **Numbers**: "the realized wall-clock latency on the same hardware for an n=16 step is about 2x that of a single-sample step"; prefix-cache hit rate 98.9%; gpt-oss served with vLLM 0.15.1.
- **Relevance**: The only SWE-agent paper found that states the near-free cost of batched width, as a side remark on server hardware. It does not study allocation under a wall-clock budget.

#### The Leaderboard Illusion
- **Ref**: Singh et al., arXiv 2504.20879, Apr 2025, https://arxiv.org/abs/2504.20879
- **Contribution**: Selective disclosure of the best of many private variants biases Chatbot Arena rankings (27 private Llama-4 variants tested by one provider).
- **Relevance**: The best-of-N selection effect for human-preference leaderboards; the agent-leaderboard analogue (proposal #2) is unmeasured.

#### Earlier leaderboard-overfitting work (not re-opened)
- Blum and Hardt, "The Ladder: A Reliable Leaderboard for Machine Learning Competitions", ICML 2015 (arXiv 1502.04585); Roelofs et al., "A Meta-Analysis of Overfitting in Machine Learning", NeurIPS 2019 (Kaggle competitions show little adaptive overfitting). Both concern deterministic models on a fixed holdout; agent leaderboards add run-to-run noise in the submission itself.

## 3. Training SWE agents and small open models

### 3.1. LoRA-specific results for code agents and agentic RL

#### Traj-Curation-LoRA: A Systematic Evaluation of Trajectory Data Curation for LoRA Fine-Tuning of Code Agents
- **Ref**: Yunze Han, arXiv 2607.17205 (ICIC 2026, Springer LNCS 16669), Jul 2026, https://arxiv.org/abs/2607.17205
- **Contribution**: 16 controlled QLoRA experiments on Qwen2.5-Coder-7B-Instruct using the SWE-trajectory corpus (67,074 traj., 32,161 resolved); proposes a two-axis (Efficiency, Style) trajectory quality score and a proxy-metric (held-out CE loss) evaluation protocol because 7B models resolve ~1% of SWE-bench Verified.
- **Numbers**: QLoRA rank 64, alpha 128, dropout 0.05 on all 7 linear projections, NF4, max context 32,768, LR 2e-5 cosine, 2 epochs, eff. batch 8, A100-80GB, ~150 GPU-hours total. Resolved trajectories average 64.4 assistant turns and 47,171 tokens (so the mean resolved trajectory does NOT fit in 32k). Scale 500 -> 1,000 trajectories: -12.7% CE loss; top-quality vs random selection gap <1% (n.s.) at 500-1,000 and 3.6% (p=0.016) at 2,000. Error-retry rate is the dominant quality sub-dimension (B2 alone within 0.2% of full composite). Resolved-only filtering does not beat random at 500.
- **Admitted limitations / future work**: Sec. 5.4: 200-trajectory test split underpowered (needs ~2,800 to detect 0.7% effects); CE/ROUGE-L proxy alignment over only n=4 checkpoints (p~0.083); single base model and single trajectory source (SWE-smith/R2E-Gym replication open); 300-token generation budget gives Action-Type Accuracy = 0. Sec. 5.2: tool-call JSON format compliance is ZERO for all 16 LoRA configs (class imbalance: tool_call is 0-3% of turns), so the adapters were not deployable without constrained decoding. No end-to-end resolve rate is reported.
- **Relevance**: Negative/weak evidence: with LoRA r=64 on a 7B model, quantity beats quality filtering and format failure can dominate; no resolve-rate result. Shows the LoRA-only, small-model, 32k regime is under-evaluated end to end. Mean trajectory length (47k) is incompatible with 32k + compaction unless trajectories are compressed.

#### CrossBench-RL: Cross-Benchmark Transfer from RL on Agentic Coding Tasks
- **Ref**: Sushant Mehta, Logan Ritchie, Edwin Chen, arXiv 2610.00890, Oct 2026, https://arxiv.org/abs/2610.00890
- **Contribution**: RL-only (GSPO, no SFT) with a single rank-32 LoRA adapter on Kimi K2.7 Code improves pass@1 on six external benchmarks and three harnesses; paired trajectory analysis shows base failures are "last-mile" near-misses and RL teaches a way of finishing (cover full spec, test the requirement, protect pass-to-pass, build own ground truth).
- **Numbers**: Model 1T MoE / 32B active. 1,700 training tasks (1,000 repo tasks with F2P/P2P tests + 700 terminal tasks), one epoch = 108 rollout steps, 216 optimizer updates, rank-32 LoRA on attention+MLP. Reward = fraction of target checks passed, zeroed if any P2P test fails. Pass@1 base -> trained: SWE-Bench Pro 60.1 -> 64.8; DeepSWE 31.0 -> 43.4; Terminal-Bench 2.1 67.4 -> 82.0; TB3 1.4 -> 12.1; TB4 0.0 -> 7.6; SWE-Marathon 5.0 -> 25.0. Median agent steps on DeepSWE 150 -> 98 (-35%), on TB3 102 -> 78 (-24%). Gains significant on benchmarks released after the training data (p=0.004). Harness: mini-swe-agent-style bash-only loop, thinking mode at max effort.
- **Admitted limitations / future work**: all in-house results are single runs (one seed); TB3 has 8/74 harness failures excluded (counting them as failures cuts the gain to +9.4 pp); SWE-Marathon gains are 1 to 5 of 20 tasks; only one base model; the claim "what transferred is a way of finishing work, not domain knowledge" is based on reading paired trajectories, not on a controlled ablation.
- **Relevance**: Best evidence that LoRA-only RL (rank 32, <= 128) transfers to unseen harnesses/benchmarks and shortens trajectories (fewer steps) -- but on a 32B-active model with long thinking, not a 4-31B dense model at 32k context and ~30 tool calls; compute is far above 6 L4-hours/week.

### 3.2. On-policy / DAgger distillation and teacher trajectories

#### DAgger-LLM: Revisiting DAgger in the Era of LLM-Agents
- **Ref**: Changhao Li, Rushi Qiang, ..., Niao He, Bo Dai, arXiv 2605.12913, May 2026, https://arxiv.org/abs/2605.12913
- **Contribution**: Turn-level teacher-student mixture rollouts (probability of teacher takeover decays during training; AggreVaTe variant: student prefix then teacher completion), student trained on teacher-labelled actions at visited states. Works with black-box teachers (no logits needed), unlike on-policy distillation (OPD).
- **Numbers**: Students Qwen3-4B-Instruct-2507 and Qwen3-8B; teacher Qwen3-Coder-30B-A3B-Instruct; SWE-Gym train; OpenHands; A100s; full fine-tuning (no LoRA mentioned). SWE-bench Verified (non-matplotlib subset): 4B base 11.2 -> GRPO 11.6 / SFT 22.9 / OPD 23.4 / DAgger 27.3 / AggreVaTe 24.5. 8B base 7.7 -> GRPO 8.2 / SFT 23.4 / OPD 26.2 / DAgger 29.8 / AggreVaTe 27.3. SWE-Gym holdout: 4B 5 -> 17, 8B 2 -> 19. Published refs in the same table: SWE-Gym-7B 10.6, SWE-smith-LM-7B 15.2, R2E-Gym-7B 19.0, SkyRL-Agent-7B 14.6. At 3K effective samples DAgger beats OPD; SFT peaks then drops on SWE-bench Verified-100 at larger budgets. GRPO (293-instance SkyRL-v0 subset) gave no consistent gains at 4B/8B.
- **Admitted limitations / future work**: App. B: only SWE under OpenHands; depends on a stronger teacher and its inference cost; remaining errors increasingly dominated by long-context overflow, "memory, retrieval, or context management may be necessary". (Hyperparameter values such as context limit and max turns are blanked in the HTML source.)
- **Relevance**: Directly in the 4B-8B regime and shows SFT-on-teacher plateaus/regresses while mixed-rollout DAgger keeps improving; and that context overflow is the residual failure -- exactly what summary compaction at 14k targets. Not tested with LoRA, nor on unseen repos beyond SWE-bench Verified (python repos overlapping SWE-Gym families), nor under a 32k/6-min budget. Train+eval compute (A100 cluster) far exceeds 6 L4-h/week.

#### OPRD: On-Policy Reminder Distillation for Long-Horizon Coding Agents
- **Ref**: Yuechen Luo, Zhiyi Lai, Ziqi Miao, ..., Ken Deng (Tsinghua, Shanghai AI Lab, NUS), arXiv 2610.21496 v2, Oct 2026, https://arxiv.org/abs/2610.21496
- **Contribution**: Student rollouts without hints; successful rollouts get self-imitation, failed rollouts get reverse-KL supervision from the SAME model re-evaluating the student's prefix with "Reminders" (global = final-test diagnostics; turn-local = next decision after an observation). No stronger teacher. Cold start = Coding SFT then Instruction-Following SFT.
- **Numbers**: Qwen3.5-4B and 9B, full fine-tuning (seq. len 131,072, batch 32, 3 epochs, LR 1e-5, H20 GPUs). Data: 8,000 verified successful trajectories for Coding SFT (7,262 SWE-rebench V2 + 738 Multi-SWE-RL), 2,000 IF-SFT examples, 4,000-task OPRD pool. Verified/Pro/Multilingual (avg): 4B base 50.4/24.2/35.3 (36.6) -> Coding SFT 53.6/25.6/38.7 (39.3) -> +IF SFT 55.8/26.7/42.3 (41.6) -> +OPRD 61.2/30.5/52.0 (47.9). 9B base 59.6/32.3/41.3 (44.4) -> OPRD 70.0/40.9/56.7 (55.9). Evaluation scaffold: Claude Code agent, 200 turns max, temp 1.0, model length up to 262k. Error-event count on 200 SWE-rebench-V2 val tasks 446 -> 222 (-50.2%). Plain Coding SFT gives only +3.2 (4B) / +1.8 (9B) on Verified.
- **Admitted limitations / future work**: No limitations section. Diagnostic taxonomy of errors relies on GPT-5.4 as a classifier; scaffold fixed to Claude Code harness.
- **Relevance**: A 4B already at 50% Verified shows how modern small bases differ from the 2025 literature (7B at 10-20%); SFT on 8k trajectories adds only ~3 points, on-policy/self-distillation adds 5-10. Compute (H20 cluster, 131k seq) is not L4-compatible, no LoRA ablation, no 32k setting.

#### P2T: Patches-to-Trajectories (privileged process supervision)
- **Ref**: Murong Ma, Tianyu Chen, Yun Lin, ..., Yeyun Gong (NUS, Microsoft Research Asia, SJTU), arXiv 2605.21996, May 2026, https://arxiv.org/abs/2605.21996
- **Contribution**: Uses the developer reference patch as privileged information to build a latent process graph, then curates teacher continuations by per-step grounded progress and keeps the shortest effective segments (bi-objective: effectiveness and length).
- **Numbers**: Only 1.8k curated SWE-Gym instances; students Qwen2.5-Coder-14B/32B-Instruct (full FT, OpenHands); teachers Qwen3-Coder-480B-A35B and GLM-5-FP8. Best cell SWE-bench Verified Pass@1 50.4 vs 39.6 for test-pass rejection sampling (+10.8), SWE-bench Lite 36.0 vs 28.7; per-instance inference cost -15% (about 0.92 -> 0.78 USD). Size-matched control (same data volume) gets only +1 to +3. Curation compute ~10^2 GPU-hours for 1.8k instances.
- **Admitted limitations / future work**: App. L: needs reference patch + executable tests (no CI -> not applicable); LLM-judged leakage/groundedness gates are empirical, not formal; curation compute non-trivial; fixed to OpenHands and the Qwen2.5-Coder family; PRM / online RL extension left to future work.
- **Relevance**: Direct evidence that shorter, process-filtered teacher trajectories give both higher resolve and lower cost with ~2k examples -- compatible with a 30-call budget. But requires a very strong teacher and reference patches (not available on unseen private repos at test time; fine at training time on public repos).

#### HHD: Hindsight Hint Distillation
- **Ref**: Shengjie Wang, Guanghe Li, Zonghan Yang, Yang Gao, arXiv 2605.11556, May 2026, https://arxiv.org/abs/2605.11556 (abstract and experiments read)
- **Contribution**: Self-improvement from CoT-free (question, answer) pairs: hints summarised from the model's own failed rollouts scaffold successful on-policy rollouts, which are then self-distilled without hints.
- **Numbers**: Qwen2.5-72B-base and GLM-4.5-Air-base on SWE-Gym; Qwen-72B reaches 51.2% Pass@1 on Verified; +8 points absolute vs ~+2 for iterative RFT and trajectory synthesis baselines; largest gains on SWE-bench Multilingual with no multilingual training. Max seq length 128k.
- **Admitted limitations / future work**: not extracted in detail (72B-class models only).
- **Relevance**: Shows iterative rejection-sampling fine-tuning (RFT) stalls near +2 even on 72B; no small-model or LoRA data.

### 3.3. Large-scale SFT distillation of SWE agents (small models included)

#### SWE-Zero-to-Hero: From SWE-Zero to SWE-Hero
- **Ref**: Nikolai Ludwig, Wasi Uddin Ahmad, ..., Boris Ginsburg (NVIDIA), arXiv 2604.01496 v2, Apr/May 2026, https://arxiv.org/abs/2604.01496
- **Contribution**: Two-stage SFT: 300k execution-FREE trajectories (SWE-Zero) then 13k execution-backed trajectories (SWE-Hero), all distilled from Qwen3-Coder-480B, into Qwen2.5-Coder-Instruct 7B/14B/32B.
- **Numbers**: SWE-bench Verified (OpenHands, 128k ctx, 100 rounds, mean of 3 passes): Zero-7B 46.8, Hero-7B 52.7, Zero-14B 54.5, Hero-14B 60.8, Hero-32B 62.2; SWE-bench Multilingual 44.1 for 32B (zero-shot transfer, trained only on Python). Previous 7B: SWE-Gym 10.6, R2E-Gym 19.0, SWE-Dev 23.4; 14B: R2E-Gym 26.8, FrogMini 45.3. Skipping the Zero stage (direct SFT of 32B on Hero data) gives 55.7 Verified / 30.8 Multilingual vs 62.2 / 44.1. Training: full FT, up to 3 epochs, YaRN 32k -> 128k, batch 32, LR 1e-5 cosine. Scaling of SWE-Zero-14B with execution-free samples: 42.1% (4k) -> 49.1% (150k) on the Zero-stage benchmark, fastest gains between 4k and 32k, diminishing but still positive returns up to 150k.
- **Admitted limitations / future work**: Limitations section: inherits teacher biases (ceiling set by Qwen3-Coder-480B); only non-reasoning models; variance from stochastic envs (3 training runs per model); test-time scaling with verifiers leaves a 15 pt gap between Best@K and Pass@K.
- **Relevance**: Shows 7B/14B reach 50-60% Verified by pure SFT distillation, but with 128k context, 300k trajectories and full FT: three orders of magnitude beyond a 6 L4-hour/week budget. Execution-free data being enough for stage 1 is useful (cheap data), the open question is how little of it suffices at 32k + LoRA.

#### Open-SWE-Traces: Advancing Dual-Mode Multilingual Distillation for SWE Agents
- **Ref**: Wasi Uddin Ahmad, Nikolai Ludwig, ..., Boris Ginsburg (NVIDIA), arXiv 2606.16038, Jun 2026, https://arxiv.org/abs/2606.16038
- **Contribution**: 207,489 trajectories on 9 languages from 20k PRs of SWE-rebench-V2, in thinking (MiniMax-M2.5) and non-thinking (Qwen3.5-122B) modes, with OpenHands and SWE-agent harnesses; fine-tunes Qwen3-30B-A3B (Thinking/Coder/Instruct).
- **Numbers**: Best 61.7% Verified, 57.1% SWE-bench Multilingual, 36.8% SWE-bench Pro; max context 131,072 (262,144 at eval). Thinking traces cut mean assistant turns per trajectory from 94.08 to 58.22 (-38%) in OpenHands (SWE-agent: 130.7 -> 74.8) while each turn is longer (288 -> 313 tokens). Training on the FULL corpus (including unresolved trajectories) beats resolved-only: Verified (think) 55.3 -> 58.1, Multilingual 40.5 -> 47.6 (think), 49.6 -> 57.1 (no-think). Cross-harness transfer always incurs a penalty; models trained on MSWEA transfer better to MOH than the reverse.
- **Admitted limitations / future work**: inherited teacher bias; run-to-run variance (triple-run aggregation).
- **Relevance**: Contradicts the standard "resolved-only" rejection-sampling filter (also see Traj-Curation-LoRA: filtering for resolved gave no benefit at 500). Harness-specific overfitting is directly relevant: a model fine-tuned in one tool interface may lose several points under another, which matters for a fixed ~30 tool-call harness.

### 3.4. RL for small and mid-size SWE agents (full fine-tuning and LoRA)

#### TRACE: Capability-Targeted Agentic Training
- **Ref**: Hangoo Kang, Tarun Suresh, Jon Saad-Falcon, Azalia Mirhoseini (Stanford), arXiv 2604.05336 v2, Apr/Jul 2026, https://arxiv.org/abs/2604.05336
- **Contribution**: Contrast successful/failed trajectories -> identify missing capabilities -> synthesize a targeted environment per capability -> train one LoRA adapter per capability with GRPO -> compose adapters with a small learned MoE gate (491,760 parameters).
- **Numbers**: SWE-bench Verified Pass@1 (temp 0, max context 32,000 tokens, max 50 interaction steps, 4-8 A100-80GB, AdamW lr 1e-5, up to 40 iterations per capability, 3 capabilities for SWE). Qwen3-30B-A3B-Instruct: base 26.0, ADP (SFT on public trajectories) 30.2, GEPA 31.0, SWE-RL 32.6, single-capability GRPO 36.6, TRACE 41.0. Qwen3.6-27B: base 68.0, ADP 68.4, GEPA 69.6, SWE-RL 70.4, single-capability 71.0, TRACE 73.2. On tau2-Bench TRACE reaches higher accuracy with < 1/4 of the rollouts of GRPO (GRPO unstable: drops to 35.4% at 3,840 rollouts).
- **Admitted limitations / future work**: no limitations section. Footnote-level caveats: each LoRA adapter is ~1.6B trainable parameters (5.3% of a 30.5B backbone), i.e. a very high-rank adapter, not rank <= 128; compositional benefit over a multi-capability GRPO adapter on tau2 is marginal (40.9 vs 40.3 for best single adapter, MoE better).
- **Relevance**: The closest published setting to "27-31B dense model + LoRA + 32k context + <= 50 steps": the whole eval is run at 32k/50 steps. Gain from LoRA RL on a strong 27B base is +5.2 points (68 -> 73.2), far smaller than on a weak base, and the LoRA is huge (~5% of weights). Compute (4-8 A100-80GB) is ~20x+ over a weekly L4 budget. Environments are synthetic and derived from failures on the target benchmark (Verified) itself, so transfer to unseen repos is not tested.

#### Arctic-SWE: Revisiting Long Horizon Agent Training by Modeling-System Co-Design
- **Ref**: Boyi Liu, Yite Wang, Xinyu Lian, Fan Shu, ..., Zhewei Yao (Snowflake, UIUC, Houston), arXiv 2610.24914, Oct 2026, https://arxiv.org/abs/2610.24914
- **Contribution**: A reproducible asynchronous RL baseline (CISPO, gated reward, importance-weight control, aligned train/inference engines, easy-hard task eviction), diagnosed by deliberately overfitting a 160-task R2E-Gym pool; then execution-grounded task curation and test strengthening.
- **Numbers**: Qwen3.5-4B 47.4 -> 62.0% Verified pass@1 on UNCHANGED R2E-Gym (comparable to FrogNano 61.5% from 256k rollouts, here ~1/6 of rollouts; FrogNano re-evaluated in this harness: 60.4). With curated R2E-Gym + SWE-rebench V2 + Scale-SWE: 4B 47.4/25.0/37.9 -> 65.0/38.3/59.7 (Verified/Pro-v1/Pro-v2); 9B 56.2/31.9/48.8 -> 65.7/39.6/70.2. Setup: one 8xB200 node (2 train, 6 vLLM), 100 turns, 131,072 tokens per trajectory, 32,768 per response, full-parameter. Real SWE-rebench / Scale-SWE tasks alone with the FrogNano recipe reach 48.0-53.4%.
- **Admitted limitations / future work**: Sec. 5: the 4B peaks at update 250 (64.2) then loses 8.6 points while the training reward looks fine ("eviction-adjusted reward declines only 3.4%"); re-scoring tasks retired as mastered shows forgetting (0.95 -> 0.85 between steps 350 and 500); 9B does not forget (0.97 -> 0.97); hypothesis: capacity of the 4B. Comparison to other systems is "indicative rather than controlled" (different scaffolds/budgets). Stronger tests lower apparent training mastery but improve held-out performance.
- **Relevance**: Gives a negative result for small models: RL on a 4B overfits/forgets; checkpoint selection on a held-out set is essential. Everything uses 131k tokens and 8xB200, so nothing proves it works at 32k/LoRA/L4. Gemma 4 E4B may behave like Qwen3.5-4B in the forgetting regime.

#### Paritok-4B: Intent-Conditioned Context Compression for Coding Agents
- **Ref**: Jiayu Shi, Luzhuo Chen (independent, Paritok), arXiv 2608.24188, Aug 2026, https://arxiv.org/abs/2608.24188
- **Contribution**: A Qwen3-4B LoRA compressor (264 MB adapter, runs on one 24 GB GPU) that extractively prunes tool outputs/file reads per segment conditioned on the agent's current intent; distilled from gpt-4.1-mini on 67,074 OpenHands trajectories (40,606 validated examples).
- **Numbers**: On all 300 SWE-bench Lite instances compresses agent context to 25.7% of its size (vs 50.2% for gpt-4.1-mini compressor, 61.9% for gpt-5) retaining 86.5% of uncompressed single-shot solve quality (89.3% in line-numbered regime; McNemar p=0.079: 30 instances solved only uncompressed, 17 only compressed). 96% of emitted identifiers appear verbatim in the input (extractive).
- **Admitted limitations / future work**: item 7 of Limitations: harness is single-shot with oracle file context, no agent loop; says nothing about multi-turn agent cost or exact-match editing; a drop-supervision weighting backfired; a companion paper covers multi-turn.
- **Relevance**: A LoRA-on-4B component for exactly the context-pressure problem (14k compaction in 32k). But it measures single-shot quality, not a multi-turn agent, so effect of lossy compaction on agent success is still open.

#### FrogNano: Training a 4B Coding Agent via Online Task Synthesis
- **Ref**: Minseon Kim, Zhengyan Shi, Emiliano Penaloza, ..., Alessandro Sordoni (Microsoft Research Montreal, Froggy team), arXiv 2609.07925 v5, Sep/Oct 2026, https://arxiv.org/abs/2609.07925
- **Contribution**: RL-only (no teacher trajectories) post-training of Qwen3.5-4B on ~1,500 SWE environments with synthetic tasks generated online ("TaskPilot") so that each task sits at the learnability frontier of the current checkpoint; DPPO, asynchronous rollouts, log-length penalty; 5 iterative curricula.
- **Numbers**: SWE-bench Verified 61.5% (3-run mean; 62.3% after SFT consolidation of past checkpoints), rising across the five curricula from ~53 to 61.5 (Fig. 1 labels), vs ~49.1 for RL on 1,500 real tasks (figure label); SWE-bench Pro-v1 37.6%. $0.21 per Verified task at 131k context, 53.5 steps on average (the text also mentions a consolidation variant at 59.6% that cuts average steps to 36.6 from 53.5). Unseen harness (mini-SWE-agent, one bash tool): 43.8 -> 56.4%, 87.1 vs 100.5 turns, turn cap hit on 9.8% of trajectories vs 31.6% for the base model, zero context overflows vs 26. HARNESS MATTERS: Qwen3.5-4B scores 8.3% in the R2E-Gym/SWE-Agent harness but 37.2% in the Claude-Code-style Leaf harness (96% of base-model failures in R2E-Gym were protocol errors). Summary compaction experiment (the 4B summarizes its own trajectory): fixed windows 16K/32K/64K instead of 131K; compaction fires in 87%/51%/4% of rollouts (median 4/2/1 compactions); "compaction helps most at low token budgets" and recovers full 131K performance at 64K. Per-compaction compression 0.90-0.96. Pass@8 gap between base and trained model stays constant as k grows (RL shifts the capability boundary rather than merely sharpening pass@1). Hardware: one node 8xB200 (2 train, 6 inference), context 131k, 150-step budget.
- **Admitted limitations / future work**: Limitations: Python-heavy English tasks only; transfer to other repos, frameworks, unclear requirements or untested projects "has not been established"; not shown for other tool interfaces, prompts, context or tool budgets; tests cover only part of behaviour. Appendix: RL iterations cause forgetting of previously solved tasks, fewer multi-tool calls and excessive iteration (fixed partly by SFT consolidation). Future: joint self-play training of the task generator.
- **Relevance**: Closest published match to the setting: 4B model, small budget, compaction at 16-32K. But full-parameter RL on a B200 node (~orders of magnitude above 6 L4-h/week), no LoRA. Compaction result at 32K (fires in 51% of rollouts) is the key reference for the 14k-compaction design; shows the 4B can self-summarize. Also shows Gemma 4 is a baseline in this literature (FrogNano Figure 2). Pairs with Arctic-SWE (same base, 62.0%), so a new paper in this area will collide with both.

### 3.5. Foundational 2024-2025 data/training papers (SFT, RFT, RL)

#### SWE-Gym: Training Software Engineering Agents and Verifiers with SWE-Gym
- **Ref**: Jiayi Pan, Xingyao Wang, Graham Neubig, ..., Alane Suhr, Yizhe Zhang, arXiv 2412.21139 v2 (ICML 2025), Dec 2024, https://arxiv.org/abs/2412.21139
- **Contribution**: First executable training environment: 2,438 Python task instances (11 repos); rejection-sampling SFT on 491 successful OpenHands trajectories from gpt-4o / Claude 3.5 Sonnet; verifier for best-of-N.
- **Numbers**: Qwen2.5-Coder-Instruct 7B/14B/32B on SWE-bench Verified: 10.6 / 16.4 / 20.6 (base 7B 3.0 on Lite -> 15.3 after 491 trajectories; 32B 7.0 -> 20.6). Avg trajectory ~19 turns, ~19k tokens; only trajectories <= 32k tokens kept for training. Fine-tuning reduces stuck-in-loop rate by 4.6-18.6 points. Verifier-based best-of-16 on 32B: 32.0%; 37.8 with larger pool. LoRA used for the 32B in the MoatlessTools self-improvement and verifier experiments (compute-limited). Scaling with trajectories not saturated at 491.
- **Admitted limitations / future work**: Sec. 4.3: SELF-IMPROVEMENT REMAINS INEFFECTIVE -- fine-tuning on 868 on-policy successful trajectories mixed with off-policy ones lowered Lite resolve rate from 15.3; iterative rejection-sampling fine-tuning (30 rollouts per task, 2 rounds): 7B 7.0 -> 9.0 -> 10.0, 32B 19.0 -> 19.7 then no gain ("further improvements are negligible"). Data bias: repeated sampling skews to easy tasks. Limited environment diversity (11 repos, Python only).
- **Relevance**: Anchors the "small data, teacher SFT" regime (<= 32k, ~19 turns -- consistent with a ~30 tool-call budget) and gives the earliest negative result on self-improvement/RFT by a small model without a strong teacher.

#### SWE-smith: Scaling Data for Software Engineering Agents
- **Ref**: John Yang, Kilian Lieret, Carlos Jimenez, ..., Diyi Yang, arXiv 2504.21798 v2 (NeurIPS D&B 2025), Apr 2025, https://arxiv.org/abs/2504.21798
- **Contribution**: Synthesizes 50k task instances from 128 repos by breaking tests (LM generation, procedural mutation, PR mirroring); 5,016 Claude 3.7 Sonnet SWE-agent trajectories used for rejection-sampling fine-tuning.
- **Numbers**: SWE-agent-LM-32B (Qwen2.5-Coder-32B) 40.2% pass@1 on Verified; SWE-agent-LM-7B 15.2%. Full-parameter FT via torchtune, LR 5e-5, <= 3 epochs, MAX CONTEXT 32,768, 2-8 H100-80GB. Performance rises roughly logarithmically with number of repositories (at 700 samples); specialising on one repo (SymPy, 700 trajectories) boosts that repo with minor generalisation loss. Procedural-modification and LM-rewrite bugs give the best data; trajectories from fixed issue templates have 31% fewer unique actions. In failures the 32B model often repeats actions (loops); it takes fewer steps than Claude 3.7 on jointly solved tasks.
- **Admitted limitations / future work**: Python-centric pipeline; only SFT demonstrated (no RL), due to budget (Sec. 6).
- **Relevance**: Supplies the standard "5k trajectories, 32k context" recipe, so a ~32k regime is not exotic -- but only full-parameter, 32B. 7B reaches 15%, so there is no published LoRA-only counterpart. Repo-specialisation result is relevant to the unseen-private-repo question (specialisation is cheap, generalisation costs).

#### SWE-RL: Advancing LLM Reasoning via RL on Open Software Evolution
- **Ref**: Yuxiang Wei, Olivier Duchenne, ..., Sida Wang (Meta), arXiv 2502.18449 v2 (NeurIPS 2025), Feb 2025, https://arxiv.org/abs/2502.18449
- **Contribution**: Single-turn RL (GRPO) on GitHub PR data with reward = sequence similarity to the oracle patch (-1 for wrong format); Agentless-Mini scaffold (not an agent loop).
- **Numbers**: Llama-3.3-70B-Instruct -> Llama3-SWE-RL-70B, 41.0% on Verified; 1,600 steps, 16k context, global batch 512 (16 rollouts x 32 problems), 512 H100 for ~32 wall-clock hours. Also improves five out-of-domain tasks.
- **Admitted limitations / future work**: Sec. 5: reward is lexical similarity not semantic equivalence (discourages alternative correct fixes); localization is simplified to file-level; pipeline structure prevents learning from interaction feedback.
- **Relevance**: Compute scale (512 H100 x 32 h = ~16k GPU-h per run) is three orders above a 6 L4-h/week budget; shows that cheap non-executable rewards can drive RL, but only with an agentless scaffold. Cited as a weak baseline in newer work (TRACE: SWE-RL gains +2.4 on Qwen3.6-27B).

#### R2E-Gym: Procedural Environments and Hybrid Verifiers for Scaling Open-Weights SWE Agents
- **Ref**: Naman Jain, Jaskirat Singh, Manish Shetty, Liang Zheng, Koushik Sen, Ion Stoica, arXiv 2504.07164 (COLM 2025), Apr 2025, https://arxiv.org/abs/2504.07164
- **Contribution**: 8.1K tasks built by SWE-GEN (back-translating commits into issues + generated tests); 3,321 Sonnet-3.5-v2 trajectories from 2,048 environments; hybrid execution-based + execution-free verifiers.
- **Numbers**: SFT on Qwen2.5-Coder 7B/14B/32B: 19.0 / 26.8 / 34.4% Verified (SWE-Gym: 10.6 / 16.4 / 20.6); 51.0% with hybrid Best@26 test-time scaling (each verifier alone saturates at 42-43%). The 14B SATURATES at ~800 trajectories while 32B keeps improving; synthetic vs real problem statements give nearly identical results (27.8% pass@1 for synthetic, 400 trajectories each). Training subset is 4,578 environments from 10 repos with NO OVERLAP with SWE-bench repos; limits: N=40 steps, 32K tokens per trajectory, training context 20K.
- **Admitted limitations / future work**: execution-based verifiers have low distinguishability; execution-free verifiers rely on stylistic features and are biased (Sec. 4).
- **Relevance**: Closest early evidence for "small-model SFT saturates with little data" (14B at 800 trajectories) and for training on repos disjoint from the test repos (good for unseen-repo claims); also a 40-step / 32K regime that matches the target budget.

#### SWE-Dev (Tsinghua): Building Software Engineering Agents with Training and Inference Scaling
- **Ref**: Haoran Wang, Zhenyu Hou, Yao Wei, Jie Tang, Yuxiao Dong, arXiv 2506.07636, Jun 2025, https://arxiv.org/abs/2506.07636
- **Contribution**: Synthesizes test cases and scales agent trajectories (rejection sampling), plus increased interaction budget at inference.
- **Numbers**: SWE-Dev-7B 23.4%, SWE-Dev-32B 36.6% Verified (Qwen2.5-Coder bases; 32B goes 34.0 -> 36.6 by adding 45 more steps of budget); 7B base 13.6%. Qwen2.5-Coder bases, full-parameter.
- **Admitted limitations / future work**: not extracted in detail.
- **Relevance**: Shows interaction-budget scaling gives only ~+2.6 on 32B; a 30-call budget therefore limits 32B-class models, not only small ones. NOTE: a different paper, SWE-Dev (Du et al., arXiv 2505.16975, feature-driven development benchmark, 14k train samples) uses LoRA r=16 (attention q,k,v,o, lr 6e-4, 4 epochs, 20 h on 8xA100) on Qwen2.5-7B-Instruct for single-turn SFT and reports modest gains ("a fine-tuned 7B model reaches GPT-4o on the hard split" but not agentic).

#### Skywork-SWE: Unveiling Data Scaling Laws for SWE in LLMs
- **Ref**: Liang Zeng, Yongcong Li, ..., Yahui Zhou, arXiv 2506.19290, Jun 2025, https://arxiv.org/abs/2506.19290
- **Contribution**: 10,169 Python tasks from 2,531 repos; >8,000 validated OpenHands trajectories (max 100 turns); Qwen2.5-Coder-32B-Instruct fine-tuned 3 epochs on 8xH800 for 12 hours.
- **Numbers**: 38.0% pass@1 Verified, 47.0% with test-time scaling; no sign of saturation at 8,209 trajectories (log-linear data scaling). States that SWE needs >50 interaction rounds and >32k context.
- **Admitted limitations / future work**: not extracted in detail (Python only, 32B only).
- **Relevance**: The "no saturation" data scaling claim (32B) contrasts with R2E-Gym 14B saturating at ~800 trajectories and SWE-Zero 14B saturating between 32k-150k; so the quantity needed depends on model size, which matters when the budget is ~100s of trajectories.

#### SWE-rebench: Automated Pipeline for Task Collection and Decontaminated Evaluation
- **Ref**: Ibragim Badertdinov, Alexander Golubev, ..., Boris Yangel (Nebius), arXiv 2505.20411 v2, May 2025, https://arxiv.org/abs/2505.20411 (follow-up: SWE-rebench V2, arXiv 2602.23866: 32k+ containerized tasks in 20 languages)
- **Contribution**: 21,000+ interactive Python SWE tasks for RL plus a continuously refreshed contamination-free benchmark.
- **Numbers / findings**: Some models score higher on SWE-bench Verified than on fresh SWE-rebench tasks (e.g. DeepSeek-V3 Dec vs Mar releases diverge on Verified but not on SWE-rebench, "potential contamination"); Qwen3 think vs no-think perform about the same; Qwen2.5-Coder-32B-Instruct fails by hallucinating environment responses and formatting loops; high run-to-run variance (pass@5 reported alongside).
- **Admitted limitations / future work**: Sec. 4: automated quality assessment (LLM-judged task clarity) imperfect; install-instruction LLM validated on only 18 repos.
- **Relevance**: Evaluation on fresh tasks is the right proxy for "unseen private repositories"; Verified scores of fine-tuned models may be inflated by public-repo exposure.

#### Nebius-RL: Training Long-Context, Multi-Turn SWE Agents with RL
- **Ref**: Alexander Golubev, Maria Trofimova, ..., Boris Yangel (Nebius), arXiv 2508.03501 v2, Aug 2025, https://arxiv.org/abs/2508.03501
- **Contribution**: Rejection fine-tuning (format/instruction following) then synchronous DAPO with a linear step-overrun penalty on Qwen2.5-72B-Instruct; two stages 65k then 131k context.
- **Numbers**: Verified 11% -> 20% (RFT @65k) -> 39.0% (after >100 RL iterations, 131k); SWE-rebench May/June splits 35% / 31%. Full-parameter update of all weights.
- **Admitted limitations / future work**: Sec. "Discussion and future work": sparse delayed rewards / credit assignment (suggests auxiliary critic or value head, partial-progress signals), uncertainty/abstention awareness; context hundreds of thousands tokens.
- **Relevance**: Establishes RFT-then-RL as the default pipeline; RFT alone gives roughly half the total gain. 72B and 131k context far from 4-31B at 32k.

#### SWE-Fixer and Lingma SWE-GPT (earlier open models)
- **Ref**: Chengxing Xie et al., arXiv 2501.05040, Jan 2025, https://arxiv.org/abs/2501.05040; Yingwei Ma et al., arXiv 2411.00622, Nov 2024, https://arxiv.org/abs/2411.00622
- **Contribution**: SWE-Fixer: two-stage pipeline (7B retriever + 72B editor), trained on 110K issues, 96 A800 GPUs; Lingma SWE-GPT: development-process-centric data (repo understanding, fault localization, patch generation) for 7B and 72B.
- **Numbers**: SWE-Fixer-72B 22.0% Lite / 30.2% Verified (32.8% with Best@1 test-time selection); Lingma SWE-GPT 72B 30.2% Verified, 7B 18.2% Verified (> Llama 3.1 70B 17.2%).
- **Admitted limitations / future work**: not extracted (superseded; pre-OpenHands pipeline style).
- **Relevance**: Historical baselines: 7B at ~18% on Verified in late 2024 vs >50% for 4B with agentic RL in late 2026 (Arctic-SWE, FrogNano, OPRD), i.e., the base model matters more than the method.

### 3.6. 2026 SFT/RFT/distillation recipes and small-model specialisation

#### SERA: Soft-Verified Efficient Repository Agents
- **Ref**: Ethan Shen, Daniel Tormoen, Saurabh Shah, Ali Farhadi, Tim Dettmers (Ai2/UW/CMU), arXiv 2601.20789 v3, Jan 2026 (rev. May 2026), https://arxiv.org/abs/2601.20789
- **Contribution**: Soft-Verified Generation: two teacher rollouts per random function (vague instruction -> synthetic PR; then reproduce the patch from the PR text); line-level patch overlap (soft verification) replaces unit tests, so trajectories can be generated from ANY repo, including private ones; SFT only. Explicitly pitched at specialising to private codebases.
- **Numbers**: SERA-32B (Qwen3-32B, full FT, 32,768 tokens, 3 epochs, LR 1e-5) 49.5% / 54.2% on Verified at 32K / 64K context, ~40 GPU-days (~$2,000), claimed 26x cheaper than SkyRL RL and 57x cheaper than SWE-smith. SERA-8B-GA (Qwen3-8B, teacher GLM-4.5-Air or GLM-4.6): 31.7% +- 0.4/0.9 at 32K. Repository specialisation (Django/SymPy/Sphinx): ~8,000 trajectories per repo (~$1,300) match or exceed the teacher on that repo; fully-specialised model matches teacher at 8k samples. Completely unverified rollouts are "of equal or better quality" than verified ones. Truncating trajectories to the context limit must be done with caution (truncation ratio, 0.88 used). Context length alone swings results (64K/128K vs 32K) so results are grouped by context. Three seeds per experiment because of high evaluation variance.
- **Admitted limitations / future work**: (Sec. Limitations) soft vs hard verification: unverified data may stop sufficing at larger scale; specialisation gains modest and "level off", upgrading the teacher is better than generating more data; only SWE-bench Verified evaluated, undesirable behaviours remain in real use (e.g., calls a nonexistent submit tool inside Claude Code); PRIVATE-REPOSITORY SPECIALISATION IS NOT VERIFIED on truly private code -- evaluated on public repos likely in base-model training data, so results may be biased; some comparisons underpowered.
- **Relevance**: Single most on-target paper for the unseen/private-repo claim: it names exactly that as unverified. Uses 32K contexts and 8B models, but full-parameter FT (not LoRA) and 40 GPU-days (vs 6 L4-h per week); the LoRA alternative for specialisation is only mentioned as an option for closed models.

#### SWE-Lego: Pushing the Limits of SFT for Software Issue Resolving
- **Ref**: Chaofan Tao, Jierun Chen, ..., Haoli Bai (Huawei), arXiv 2601.01426 v2, Jan 2026, https://arxiv.org/abs/2601.01426
- **Contribution**: SFT-only recipe: 32k task instances and 18k validated trajectories (real + synthetic), step-level error masking (mask tokens of execution-time errors), difficulty-based 3-stage curriculum, plus a trained verifier for test-time scaling.
- **Numbers**: Qwen3-8B 42.2% and Qwen3-32B 52.6% on Verified (base 32B 23.2%); refined SFT is +3.8 over plain SFT; TTS@16: 49.6% (8B) and 58.8% (32B). Full-parameter SFT, 4 epochs, batch 64, LR 1e-4 (8B) / 5e-5 (32B), max context 128k. Ran-out-of-max-turns becomes the dominant failure after epoch 1 (failed-to-reproduce errors, 38.97% early, vanish); truncation/turn gains flatten beyond ~140 turns; resolve rates are lowest for very few or very many turns.
- **Admitted limitations / future work**: App. C: beyond issue resolving (features, refactoring, test generation) data/benchmarks inadequate; multilingual needs per-language sandboxes.
- **Relevance**: An 8B model at 42% with SFT only, but with 128k context and long horizons. Error masking is a cheap trick compatible with LoRA. The "ran out of turns" mode is exactly what a 30-call budget produces.

#### SWE-Master: Unleashing the Potential of SWE Agents via Post-Training
- **Ref**: Huatong Song, Lisheng Huang, ..., Wayne Xin Zhao, Ji-Rong Wen (RUC, BOSS Zhipin), arXiv 2602.03411 v2, Feb 2026, https://arxiv.org/abs/2602.03411
- **Contribution**: Reproducible pipeline (teacher trajectories -> long-horizon SFT -> RL with real execution feedback -> inference framework incl. LSP-based code navigation).
- **Numbers**: Qwen2.5-Coder-32B: 61.4% Verified (SFT+RL); 70.8% with TTS@8 (LLM-based environment feedback) and 76.2% Pass@8. LSP navigation improves agent efficiency (fewer steps) without accuracy loss.
- **Admitted limitations / future work**: not extracted in detail; 32B only.
- **Relevance**: Evidence that tool design (LSP/AST navigation) reduces steps -- complementary to training for short trajectories; also 32B/long-horizon regime, not 30 calls.

#### Scale-SWE and Hybrid-Gym
- **Ref**: Jiale Zhao, Guoxin Chen, ..., Kai Jia, arXiv 2602.09892, Feb 2026, https://arxiv.org/abs/2602.09892; Yiqing Xie, ..., Graham Neubig, Daniel Fried, arXiv 2602.16819, Feb 2026, https://arxiv.org/abs/2602.16819
- **Contribution**: Scale-SWE: 100k verified instances from 6M PRs / 5.2k repos, 71,498 distilled trajectories, Qwen3-30B-A3B -> 64% Verified (3x the base). Hybrid-Gym: synthetic, repo-lite tasks (function localisation, dependency search) that train transferable skills (reasoning, repo exploration, implementation) without executable environments.
- **Numbers**: Scale-SWE-Agent 64% Verified. Hybrid-Gym: Qwen2.5-Coder-32B +25.4% Verified, +7.9% SWT-Bench Verified, +5.1% Commit-0 Lite; ~70% of actions in successful trajectories fall in categories not needing executable repos; agents trained only on issue solving do not transfer reliably to test generation or library implementation.
- **Admitted limitations / future work**: not extracted in detail.
- **Relevance**: Hybrid-Gym suggests cheap, execution-free tasks suffice for exploration skills -- important for a pipeline that cannot run Docker on L4 hours; Scale-SWE shows MoE-3B-active reaches 64% only with 71k trajectories.

#### Orchard, KAT-Coder-V2, Qwen3-Coder-Next (large-lab recipes)
- **Ref**: Orchard, arXiv 2605.15040 v3, May 2026; KAT-Coder-V2 (Kuaishou), arXiv 2603.27703, Mar 2026; Qwen3-Coder-Next (Qwen Team), arXiv 2603.00729, Mar 2026 (https://arxiv.org/abs/2605.15040, https://arxiv.org/abs/2603.27703, https://arxiv.org/abs/2603.00729)
- **Contribution**: Orchard-SWE: credit-assignment SFT that learns from productive segments of unresolved trajectories, Balanced Adaptive Rollout, OPD and rubric-based process rewards, value-model reranking; KAT: specialise-then-unify (per-domain SFT+RL experts consolidated by on-policy distillation); Qwen3-Coder-Next: 80B-A3B model with large-scale environment synthesis, mid-training + RL, SWE expert distilled into one model.
- **Numbers**: Orchard on Qwen3.5-35B-A3B: 69.7% (RPR-based RL), 73.0% with value-model reranking, Verified; Orchard-GUI 4B VLM from 0.4K distilled trajectories + 2.2K tasks. KAT-Coder-V2 79.6% Verified. Qwen3-Coder-Next ~70.6% Verified (3B active, context to 262k); in RL the average number of agent turns grew from 50 to 130 and the agent learned to exploit git commands to leak ground truth even after removing remotes/future commits ("reward hacking blocker").
- **Admitted limitations / future work**: Qwen3-Coder-Next: reward hacking via git history discovered by the agent itself; they add an unfinished-trajectory penalty (turns > max) and per-turn tool-format penalty.
- **Relevance**: Confirms the standard recipe components (turn-limit penalty, format penalty) at the frontier. Not feasible at L4 budgets; relevant for what to copy cheaply: unfinished-trajectory penalty and tool-format penalty.

### 3.7. Small-model (4B-9B) RL/SFT with Qwen3.5 base, 2026

#### FailForge: Distilling Procedural Competence from Persistent Failures
- **Ref**: Dongyi Lv, Fushun E, Aichen Cai, ..., Nan Duan (Xi'an Jiaotong Univ., Joy Future Academy/JD), arXiv 2608.08570, Aug 2026, https://arxiv.org/abs/2608.08570
- **Contribution**: RFT discards tasks where all teacher rollouts fail; FailForge diagnoses the failures into a procedural "skill", injects it into the teacher's context for a guided retry, keeps successes, and strips the skill at training time.
- **Numbers**: Teacher Kimi-K2.6 in OpenHands; 2,401 tasks; K=5 -> 1,569 solved (RFT corpus), 832 persistently failed; 26%+ of failures recovered. Qwen3.5-4B on Verified pass@1: base 54.0, RFT 59.6, RFT + 5 more unguided samples 63.0, RFT + instance hints (HHD-style) 63.8, FailForge 66.2 (+6.6). Qwen3.5-9B: 61.2 / 63.6 / ... / 67.2. Multilingual: 4B 52.3 -> 55.7, 9B 59.7 -> 61.3. Rewriting reasoning traces to read as self-derived drops pass@1 to 62.0.
- **Admitted limitations / future work**: gains concentrated on hardest problems; requires a strong teacher (Kimi-K2.6) and verifiable instances; training hyperparameters in supplement (not extracted).
- **Relevance**: A 4B modern base reaches 66% via distillation from a frontier teacher -- far above older 7B numbers; a cheap-compute lever is data composition (hard cases), and instance-level hints are worse than procedural skills. Context/LoRA not reported.

#### Polar: Agentic RL on Any Harness at Scale
- **Ref**: NVIDIA (NeMo Gym / ProRL Agent), arXiv 2605.24220, May 2026, https://arxiv.org/abs/2605.24220
- **Contribution**: Rollout framework that treats the agent harness as a black box (proxy of LLM API calls, token-faithful trajectory reconstruction) for GRPO on real harnesses.
- **Numbers**: Qwen3.5-4B, GRPO on SkyRL-v0 293 SWE-Gym tasks; SWE-bench Verified pass@1 base -> trained: Codex harness 3.8 -> 26.4 (+22.6); Claude Code 29.8 -> 34.6 (+4.8); Qwen Code 34.6 -> 35.2 (+0.6); Pi 34.2 -> 40.4 (+6.2). Prefix-merging trajectories cut trainer time 189.5 -> 35.2 min (5.4x) on 3 steps.
- **Admitted limitations / future work**: gain depends on the harness being unfamiliar to the model; in the model's native harness gains are marginal.
- **Relevance**: A 4B model's score swings from 3.8% to 34.6% depending on the harness alone (same as FrogNano's 8.3% vs 37.2%). For a fixed harness with ~30 calls, harness-native training is likely the largest lever, and LoRA RL may only need to teach the protocol.

#### CAMG-RL and CompactionRL: RL for context management
- **Ref**: Lirui Luo, Kelong Mao, Heming Xia, ..., Cong Fang (JD.com), Coding Agent Memory Post-training / Coding Agent Memory Gym, arXiv 2609.34422, Sep 2026, https://arxiv.org/abs/2609.34422; Yujiang Li, Zhenyu Hou, Yi Jing, Jie Tang, Yuxiao Dong (Tsinghua), CompactionRL, arXiv 2607.05378 v2, Jul/Oct 2026, https://arxiv.org/abs/2607.05378
- **Contribution**: CAMG-RL: asynchronous PPO on four long-horizon environments where memory is files in a persistent workspace (CONTINUATION.md); CompactionRL: jointly trains the policy and its own summaries under a fixed context window with cross-segment GAE.
- **Numbers**: CAMG-RL average success 54.4% vs 48.0% for CompactionRL (best baseline) because memory files avoid the information loss of learned compaction; on SWE-bench Verified CAMG-RL-4B resolves 15.8% (between frozen Qwen3.5 9B and 27B), CAMG-RL-9B 27.6% (above frozen 122B-A10B). CompactionRL: GLM-4.5-Air (106B-A12B) 66.4% Verified (+6.6 over base with inference-time compaction), GLM-4.7-Flash (30B-A3B) 56.0% (+5.5), context budgets 64k / 80k, critic-based GAE.
- **Admitted limitations / future work**: CAMG: memory limited to one episode and one user, backbones <= 9B; CompactionRL: critic-based, large MoE only.
- **Relevance**: The only RL-trained compaction results found; they show that compaction quality is learnable (+5 to +7 points) and that summary-based compaction loses information compared with file memory. A 14k-token summary compaction in 32k is a design that models are not trained for out of the box. No LoRA, no L4-scale numbers.

#### SWE-TRACE, SWE-Playground, PivotOPD, LVRL, BSR, ROSS, Logics-SWE (shorter notes)
- **SWE-TRACE** (vivo; arXiv 2604.14820, Apr 2026): 60K SFT corpus of shortest-path trajectories built by stepwise oracle verification, rubric process reward model RL, heuristic step-level TTS. Qwen3-4B and Qwen3-30B-A3B. Cascaded shortest-path SFT vs plain SFT: +4.2 points (4B), +2.8 (30B), average steps -10.8% / -10.4%, generated tokens -21.5% / -29.3%. 4B beats SWE-Master-4B-RL by +5.5; 30B reaches 63.5% Verified (71.2% with TTS). Limitation: no limitations section; the "oracle" requires reference patches.
- **SWE-Playground** (Neubig lab; arXiv 2512.12216, Dec 2025/Jan 2026): synthetic projects/tasks from scratch (no GitHub); 704 trajectories give comparable performance to SWE-smith/R2E-Gym on 7B/32B for tests and library tasks, slightly lower on Verified.
- **PivotOPD** (NVIDIA; arXiv 2609.40285, Sep 2026): >50% of failed rollouts contain an early pivotal mistake; on SWE-Bench Verified (Nemotron-3.5-SFT student, Nemotron-3-Super teacher 73.0) student 62.8 -> plain OPD 63.0 (+0.2) -> PivotOPD 66.0 (+3.2). Limits: needs replayable envs; only 5-turn history window in non-SWE tasks.
- **LVRL** (Apple; arXiv 2610.15840, Oct 2026): a frozen LLM (Claude Opus 4.6) as value critic gives step-level credit; Qwen3-8B SWE-bench Verified (R2E-Gym trained): GRPO 12.0 -> LVRL 20.2; Qwen3-32B PPO 24.9 -> LVRL 30.9. Needs a frontier API as critic; LVOPD improves OPD on AppWorld only.
- **BSR** (arXiv 2610.12598, Oct 2026): policy compares its own same-outcome trajectories to give auxiliary rewards; Qwen3-14B/32B on Verified and SWE-bench-Live; gains described as "consistent" (small).
- **ROSS** (AllSpark; arXiv 2609.35954, Sep 2026): offline SFT on historical self-rollouts with loss only on selected continuations; Qwen3.6-35B-A3B Verified 64.2 -> 68.4 without new rollouts.
- **Logics-SWE** (Alibaba; arXiv 2609.23377, Sep 2026): Qwen3.6-27B; pooled RL shows a "category see-saw" (gains in some task categories, regressions in others hidden by aggregate score); category experts + multi-teacher OPD: Pro-618 58.04% (+5.39), Multilingual 59.00% (+2.78). Relevance: aggregate benchmark score can hide regressions; evaluating on a diverse split matters for private repos.

### 3.8. RL frameworks, multi-turn RL, credit assignment, step budgets

#### DeepSWE-Preview (rLLM / Agentica + Together AI) -- blog, not a paper
- **Ref**: Agentica & Together AI, blog "DeepSWE", 2 Jul 2025, https://together.ai/blog/deepswe (opened via WebFetch; there is no arXiv paper). NOTE the naming collision: a 2026 benchmark called DeepSWE (113 original long-horizon tasks, arXiv 2607.07946) is a different artifact, and the 2610.00890 numbers above use that benchmark.
- **Contribution**: Qwen3-32B trained with RL only (GRPO++ = clip-high, no KL, no std normalisation, length normalisation, leave-one-out advantage, compact filtering of trajectories hitting max context/steps/timeouts) on ~4.5K R2E-Gym tasks, with repos overlapping SWE-bench Verified (e.g., sympy) removed.
- **Numbers**: 64 H100 GPUs for six days; Verified pass@1 ~23% -> 42.2% (avg of 16 runs; Pass@16 71.0%) in ~200 RL steps; 59% with hybrid test-time scaling (Best@16). Eval 64k context, 100 steps. Going beyond 32K output tokens gave < 2% gain. Response length decreased over training while environment steps increased; ~2K thinking tokens at localisation/planning steps, 100-200 on simple steps.
- **Admitted limitations / future work**: SFT cold start from Claude-3.7/4 trajectories followed by RL did NOT improve after 100 iterations; SWE-smith and SWE-Gym datasets gave limited gains (many tasks never solved), R2E-Gym worked best (a difficulty curriculum); non-thinking mode RL gave limited gains; TTS selection far from Pass@K ceiling; one base model, one dataset.
- **Relevance**: 64 H100 x 6 days = ~9,200 GPU-hours (about 9,200 GPU-hours, roughly 1,500x a 6 GPU-hour weekly budget); shows that pure RL needs a base with thinking capacity. Evidence that data difficulty calibration matters more than quantity.

#### SkyRL-Agent: Efficient RL Training for Multi-turn LLM Agent
- **Ref**: Shiyi Cao, Dacheng Li, ..., Ion Stoica (UC Berkeley, Anyscale), arXiv 2511.16108, Nov 2025, https://arxiv.org/abs/2511.16108
- **Contribution**: Asynchronous dispatching pipeline (1.55x speed-up) and an AST-based search tool; SA-SWE-32B trained from Qwen3-32B purely by RL.
- **Numbers**: Verified pass@1 24.4% -> 39.4% (checkpoint at step 125), > 2x cost reduction vs prior models of similar quality; evaluated with a simplified ReAct loop (file editor + bash), 40k context and 100 max steps; 2x8 H100 for 32B.
- **Admitted limitations / future work**: marked "work in progress"; no detailed limitations section extracted.
- **Relevance**: A 40k-context, simple two-tool harness (closest to the target setting among RL papers); the AST search tool is a cheap way to lift pass@k; again 32B on 16 H100.

#### Practitioner's Guide to Multi-turn Agentic RL
- **Ref**: Prithviraj Ammanabrolu, Ruiyi Wang (UCSD/NVIDIA), arXiv 2510.01132 v2, Oct 2025, https://arxiv.org/abs/2510.01132
- **Contribution**: Ablations over environment complexity, reward density (sparse vs dense turn-level), SFT-to-RL ratio under a fixed budget and PPO/GRPO/RLOO, on TextWorld, ALFWorld and a getmoto subset of SWE-Gym, with Qwen2.5-1.5B/7B and Qwen3-8B.
- **Numbers**: Dense turn-level rewards accelerate training but stability depends on the algorithm; a model initialised with only 60 SFT demonstrations then 400 RL episodes reaches 85% on TextWorld (pure RL: 88% at 5,000 episodes); for SWE-Gym raising the allowed tool calls/context from 10 to 40 lifts success from 3% to 22% ("software repositories do not saturate quickly"), whereas text games saturate at 2x the optimal solution length.
- **Admitted limitations / future work**: SFT:RL ratio results are from TextWorld only; SWE-Gym section limited to one repository subset and small models (1.5B).
- **Relevance**: Gives the only quantified budget-vs-success curve at the very low end (10 -> 40 tool calls = 3% -> 22% for small models), strongly supporting that a ~30-call limit is binding for small models; and a recipe (a few SFT demos then short RL) suitable for tiny compute.

#### GiGPO: Group-in-Group Policy Optimization for LLM Agent Training
- **Ref**: Lang Feng, Zhenghai Xue, Tingcong Liu, Bo An (NTU/Skywork), arXiv 2505.10978 v3 (NeurIPS 2025), May 2025, https://arxiv.org/abs/2505.10978
- **Contribution**: Critic-free step-level credit assignment: episode-level group advantage plus a step-level advantage obtained by grouping identical "anchor states" across trajectories.
- **Numbers**: Qwen2.5-1.5B/3B/7B-Instruct; > +12% on ALFWorld and > +9% on WebShop over GRPO; 42.1% (3B) and 47.2% (7B) on search-augmented QA; same GPU memory, no extra rollouts.
- **Admitted limitations / future work**: not extracted in detail; evaluated only on tasks with repeated discrete states (ALFWorld, WebShop, search QA), not SWE.
- **Relevance**: Anchor-state matching presupposes revisited identical states, which rarely happens in repository editing (inference from the method, not stated by authors); the SWE-specific alternatives found are LVRL (frozen LLM critic), SWE-TRACE (rubric PRM), Orchard (rubric process reward).

#### Devstral (Small) and Devstral Small 2
- **Ref**: Mistral AI and All Hands AI, "Devstral: Fine-tuning Language Models for Coding Agent Applications", arXiv 2509.25193, Sep 2025, https://arxiv.org/abs/2509.25193. Devstral Small 2 (24B, Dec 2025): only a press/model-card figure of 68.0% Verified (Mistral announcement, via secondary result pages); no technical report found.
- **Contribution**: 24B dense model (Mistral Small 3 base, 128k context), post-trained with SFT on OpenHands/SWE-Gym trajectories filtered in two stages, then further rounds of rollouts and policy optimisation; later version trained with pseudo-scaffolds and both XML and native function-calling formats for scaffold generalisation.
- **Numbers**: 46.8% Verified for the first version; MAXIMUM ITERATION LIMIT ablation at temperature 0: 30 turns -> 36.8%, 50 turns -> 46.8%, 100 turns -> 46.8% (identical).
- **Admitted limitations / future work**: report is short, hyper-parameters mostly undisclosed; evaluation sensitivity to hardware non-determinism.
- **Relevance**: A direct measure of a ~30-turn budget: -10 points for the best 24B open model relative to 50 turns; implies that a 30-call cap alone may cap 31B-class models near 35-40% unless trajectories are made shorter.

#### Kimi-Dev and Self-play SWE-RL (SSR)
- **Ref**: Zonghan Yang, Shengjie Wang, ..., Tianyu Liu (Moonshot), arXiv 2509.23045 v3, Sep 2025, https://arxiv.org/abs/2509.23045; Yuxiang Wei, Zhiqing Sun, ..., Lingming Zhang, Sida Wang (Meta), arXiv 2512.18552 v3, Dec 2025, https://arxiv.org/abs/2512.18552
- **Contribution**: Kimi-Dev: Agentless-style training (mid-training ~150B tokens, RL, test-time self-play) as a skill prior; SFT on only 5k public agent trajectories then turns the 72B model into a SWE-agent. SSR: one model plays bug injector and solver in sandboxed repos using only tests, no human issues.
- **Numbers**: Kimi-Dev-72B 60.4% Verified in Agentless workflow; 48.6% as SWE-agent after 5k-trajectory SFT. SSR: self-improvement of +10.4 and +7.8 points on SWE-bench Verified and SWE-Bench Pro (CWM-32B base, as given in the abstract: "+10.4 and +7.8").
- **Admitted limitations / future work**: SSR App. E.2: tests exposed in the prompt risk reward hacking; only unit-test oracles; single model for both roles; unsuccessful attempt: synthesising natural-language issues in self-play.
- **Relevance**: 5k trajectories suffice to move a strong Agentless-trained prior to agentic mode: suggests prior skills matter more than trajectory count; both need 32-72B models.

### 3.9. PEFT/LoRA theory and the LoRA-for-agents evidence base

#### LoRA Without Regret
- **Ref**: John Schulman and Thinking Machines Lab, blog post, Sep 2025, https://thinkingmachines.ai/blog/lora/ (opened via WebFetch)
- **Contribution**: Systematic study showing LoRA matches full fine-tuning ("low-regret regime") when applied to all layers and when trainable parameters exceed the information content of the dataset.
- **Numbers**: ranks 1-512 tested; optimal LoRA learning rate about 10x the full-FT rate (fitted 9.8; maybe 15x for runs < 100 steps); attention-only LoRA underperforms MLP-only, and adding attention to MLP does not help (Llama-3.1-8B: attention-only rank 256, 0.25B params, worse than MLP-only rank 128, 0.24B); LoRA matched full FT for policy-gradient RL even at rank 1 (bit-counting argument: ~320k bits in a MATH run vs ~3M parameters at rank 1); LoRA is less tolerant of large batch sizes; ~2/3 of FLOPs of full FT per pass.
- **Admitted limitations / future work**: supervised results use log-loss not sampling evals; constant LR, no warmup; RL runs use Llama-3.1-8B base with sequences capped at 8,192 tokens (single-turn math); the 10x LR has no full theory; the RL bit-count is an upper bound for policy-gradient only; capacity needs for supervised learning and MoE LoRA are open.
- **Relevance**: Predicts that rank <= 128 on all layers suffices for outcome-reward RL, but NOT for large SFT corpora (capacity-bound) -- and was never tested for multi-turn tool-using agents with 20-30k-token trajectories. No agentic SWE paper found here tests LoRA rank vs full FT head to head.

#### Evidence table (what exists on LoRA/PEFT for SWE agents, all opened)
- CrossBench-RL (2610.00890): rank-32 LoRA, GSPO, 1.7k tasks, 32B-active MoE: +4.7 to +20 pts on six benchmarks incl. new ones (single run).
- TRACE (2604.05336): LoRA + GRPO on Qwen3.6-27B and Qwen3-30B-A3B at 32k / 50 steps; very large adapters (~1.6B params each); +5.2 (27B) / +15.0 (30B-A3B) vs base on Verified.
- Traj-Curation-LoRA (2607.17205): QLoRA r=64 on Qwen2.5-Coder-7B, 32,768 context, 150 A100-h; only CE loss, 0% tool-call-format compliance.
- SWE-Gym (2412.21139): LoRA for 32B self-improvement and verifier (compute-limited); SWE-Dev feature benchmark (2505.16975): LoRA r=16, attention only, 7B, single turn; Paritok-4B (2608.24188): LoRA compressor (not an agent policy).
- No paper opened compares LoRA vs full-parameter on the same SWE-agent SFT or RL data; no LoRA result for <= 8B agent policies with resolve rate on Verified/Pro was found. Unverified model-card claims exist (e.g., "SWE-Eff-14B", a LoRA adapter on Qwen3-14B trained on ~3K R2E-Gym trajectories; the card page had no numbers) and are NOT counted.

### 3.10. Evaluation validity (relevant to unseen private repos)

#### SWE-Bench Illusion; SchrodingerRepo; DeepSWE benchmark; SWE-rebench
- **Ref**: Shanchao Liang, Spandan Garg, arXiv 2506.12286 v4 (ICSE-SEIP 2026), https://arxiv.org/abs/2506.12286; Silin Chen, Yufei Yan et al., SchrodingerRepo, arXiv 2609.27891, Sep 2026, https://arxiv.org/abs/2609.27891; DeepSWE benchmark, arXiv 2607.07946, Jul 2026, https://arxiv.org/abs/2607.07946
- **Contribution**: Evidence that SWE-bench Verified numbers reflect memorisation of public-repo cues: frontier models identify buggy file paths from the issue alone with up to 76% accuracy on Verified vs up to 53% on repos outside SWE-bench; SchrodingerRepo rewrites namespaces/layout while preserving behavior; DeepSWE benchmark has 113 original tasks across 91 repos and 5 languages with hand-written verifiers (LLM-judge disagreement 1.4% vs 32.4% for SWE-Bench Pro tests).
- **Numbers**: SchrodingerRepo: Verified pass@1 drops by up to ~8 points (e.g., 44.6% -> 36.2%, 46.8% -> 40.4%) and interaction cost rises by 18-43%, with 81.6-83.6% of the extra actions being exploration; > 65% of instances show data-leakage evidence for each evaluated model. These were evaluated on frontier API models (GPT-5.4-mini, GPT-5.1, Gemini-3.1-Flash-Lite, DeepSeek-v4-Flash), not fine-tuned small models.
- **Admitted limitations / future work**: SchrodingerRepo only perturbs representation, not task semantics; analysis models restricted for cost reasons.
- **Relevance**: Every small-model number above on Verified (including the 50-66% 4B results) is probably inflated vs private repos; the penalty from removing repo-cue familiarity is concentrated in exploration, which is exactly what a 30-call budget cannot absorb. SERA itself says private-repo specialisation is unverified.

#### SWE-Star (LogicStar blog, not peer reviewed)
- **Ref**: LogicStar, blog "SWE-Star", 2 Feb 2026, https://logicstar.ai/blog/swe-star (opened via WebFetch)
- **Contribution**: Large-scale SFT distillation from Devstral-2-Small (24B) as teacher: 250k trajectories generated, ~100k kept; students Qwen2.5-Coder 7B/14B/32B, full FT with torchtune, LR 5e-5, 32k training context (long trajectories split into 32k chunks with earlier observations masked).
- **Numbers**: Verified (OpenHands, up to 3 attempts): 32B 57.1%, 14B 52.8%, 7B 36.4%; single-attempt pass@1: 52.4 / 49.8 / 32.8. Cost ~4,500 H100-hours per 100k-trajectory run. The 32B plateaus at ~40% around 800 trajectories and resumes slowly after 1,600; the 7B shows no saturation at 100k trajectories.
- **Admitted limitations / future work**: teacher scored ~60% in their setup (Mistral reports 68%); scaffold is a mini-swe-agent fork; two-regime explanation is a hypothesis.
- **Relevance**: A 7B at 32.8% pass@1 at 32k training context shows that small student quality scales with trajectory count (no saturation at 100k), contradicting R2E-Gym's early saturation for 14B; chunking long trajectories with masked prefixes is a direct recipe for 32k-context training.

## 4. Code graphs, retrieval and localization

### 4.1. Graph tools for SWE agents: the original claims

#### RepoGraph: RepoGraph: Enhancing AI Software Engineering with Repository-level Code Graph
- **Ref**: Ouyang et al., ICLR 2025 / arXiv 2410.14684, Oct 2024, https://arxiv.org/abs/2410.14684
- **Contribution**: Plug-in line-level repo graph (tree-sitter, two edge types: `contain` and `invoke`, repository-independent calls filtered out). The agent or pipeline queries a k-hop ego-graph around a search term and the flattened ego-graph is appended to the prompt.
- **Numbers**: SWE-bench Lite, GPT-4o: +2.66 abs. on RAG (99.6% rel.), +2.34 on Agentless (27.33 -> 29.67), SWE-agent 20.3 with RepoGraph (+2.0 per ARISE's reading of the same table). Graph averages >1,000 nodes and >25,000 edges per repo; a 1-hop ego-graph averages 11.6 nodes / 37.1 edges, 2-hop 54.5 nodes / 89.9 edges. Flattened 2-hop ego-graph gives 26.00% resolve, WORSE than the Agentless baseline; LLM-summarised 1-hop lowers it to 28.33% (information loss). Agent frameworks pay +$0.13 (AutoCodeRover) and +$0.18 (SWE-agent) per instance because the agent calls `search_repograph()` many times ("explosion of prompt contexts", Sec 4.2 (iv)).
- **Admitted limitations / future work**: App. E: only proprietary GPT-4-class models ("poor performance of open-source models"), only Lite, only Python. Error analysis (Sec 5.4): contextual misalignment is the most common failure, then incorrect localisation, i.e. the graph does not remove most failures.
- **Relevance**: The gains are +2 to +3 points at 1-hop with big proprietary models; deeper hops hurt; agents over-call the tool. No small-model evidence at all.

#### LocAgent: LocAgent: Graph-Guided LLM Agents for Code Localization
- **Ref**: Chen, Tang et al., ACL 2025 / arXiv 2503.09089, Mar 2025, https://arxiv.org/abs/2503.09089
- **Contribution**: Heterogeneous directed graph over files / classes / functions with four edge types (contain, import, invoke, inherit) plus a BM25 sparse index over entity IDs and contents; three tools (SearchEntity, TraverseGraph, RetrieveEntity). Fine-tunes Qwen2.5-Coder 7B/32B on Claude-3.5 trajectories. Introduces Loc-Bench (post-Oct-2024 issues; bugs, features, security, performance).
- **Numbers** (SWE-bench Lite, 274 instances; columns file Acc@1/3/5, function Acc@5/10; table): BM25 38.7/51.8/61.7 ; func 31.8/36.9. Jina-Code-v2 43.4/71.2/80.3 ; func 42.3/52.2. CodeRankEmbed 52.6/77.7/84.7 ; func 51.8/58.8. Agentless(Claude-3.5) 72.6/79.2/79.6 ; func 58.8/58.8. SWE-agent(Claude-3.5) 77.4/87.2/90.2 ; func 64.2/64.6. OpenHands(Claude-3.5) 76.3/89.8/90.2 ; func 68.3/70.1. LocAgent Qwen2.5-7B(ft) 70.8/84.7/88.3 ; func 64.2/71.5. LocAgent Qwen2.5-32B(ft) 75.9/90.5/92.7 ; func 71.9/77.0. LocAgent Claude-3.5 77.7/92.0/94.2 ; func 73.4/77.4. Cost per example: LocAgent-Claude $0.66, Qwen-7B(ft) $0.05, Qwen-32B(ft) $0.09; OpenHands-GPT-4o $0.83, SWE-agent-Claude $0.67. Ablation on Qwen-7B(ft) (file Acc@5 / module Acc@10 / function Acc@10): full 88.32/82.85/71.53; w/o TraverseGraph 86.13/78.47/66.06; TraverseGraph with `contain` edges only 86.50/79.56/66.42; hops=1 86.86/80.29/66.79; w/o RetrieveEntity 87.59/81.39/69.34; **w/o SearchEntity 68.98/61.31/53.28; w/o BM25 index 75.18/68.98/60.22**.
- **Admitted limitations / future work**: Limitations section: only Qwen-2.5-Coder fine-tuning, trajectories mostly from Claude-3.5 / Qwen-32B, Python only, downstream tasks barely explored. Ablation uses only the 7B(ft) model "due to budget".
- **Relevance**: Cleanest edge-type and tool ablation available: removing graph traversal costs 2-5 points, removing the lexical (BM25) entity search costs 17-18 points; `contain` alone ~ no traversal; the other three edge types (import, invoke, inherit) carry the gain, but the paper does not split them further. Note the gain is for a model FINE-TUNED on graph-tool trajectories, which a frozen Gemma 4B/31B is not.

#### CoSIL: Software Issue Localization via LLM-Driven Code Repository Graph Searching
- **Ref**: Jiang et al., arXiv 2503.22424 (ICSE-style paper, ZJU/Ant), Mar 2025, https://arxiv.org/abs/2503.22424
- **Contribution**: Training-free, index-free function-level localisation. Module call graph (import edges) and function call graph (invoke + inherit edges) are built dynamically by the LLM itself in textual form, searched iteratively with a pruner agent and a "reflective alignment" step that repairs malformed tool/output formats in short contexts.
- **Numbers**: Top-1 function-level on SWE-bench Lite with Qwen2.5-Coder-32B: CoSIL 0.433 vs Agentless-FL 0.247, OrcaLoca 0.217, LocAgent 0.103 (empty rate 13.67% for LocAgent, 0% CoSIL). Qwen2.5-Coder-7B: CoSIL 0.213, Agentless-FL 0.173, OrcaLoca 0.157, **LocAgent 0.047 with 21% empty outputs**; 14B: CoSIL 0.203, Agentless 0.187, OrcaLoca 0.170, LocAgent 0.090 (22.3% empty). File-level Top-1 32B: CoSIL 0.613, LocAgent 0.647, OrcaLoca 0.590, Agentless 0.583 (so on files, the graph methods do NOT beat Agentless-FL). Ablation (32B, Lite): no module call graph -10%, no iterative search over function call graph ~-20%, no pruning ~-3%, no reflective alignment -6 to -10%. Cost 0.02 USD (DeepSeek-V3) / 0.34 USD (GPT-4o) per instance.
- **Admitted limitations / future work**: Sec VI-B: max-iteration hyperparameter may be sub-optimal, possible data leakage, only SWE-bench Lite/Verified, Python. Search quality first decreases then increases with iterations (Sec V-B).
- **Relevance**: Direct evidence that graph-tool agents (LocAgent, OrcaLoca) collapse on 7B-14B models mainly through format/interaction failures (empty rate 21-22%), not through lack of information; a "reflection" repair step is needed. Their edge types: import (file level), invoke + inherit (function level), no embedding.

### 4.2. Recent (2026) graph-tool papers: where the evidence is mixed

#### ARISE: ARISE: A Repository-level Graph Representation and Toolset for Agentic Program Repair and Fault Localization
- **Ref**: Seddik et al., arXiv 2605.03117 (v2 3 Jul 2026), May 2026, https://arxiv.org/abs/2605.03117
- **Contribution**: Statement-level program graph (structure + intra-procedural def-use edges) exposed as a 3-tier tool API (Tier 1 structural traversal, Tier 2 `get_dataflow_slice`, Tier 3 token-budgeted context bundle); mounts on SWE-agent. Backbone Qwen2.5-Coder-32B-Instruct, SWE-bench Lite.
- **Numbers**: Pass@1 17.3 -> 22.0% (66/300) vs bare SWE-agent; Function R@1 0.43 -> 0.60, Line R@1 0.26 -> 0.41, File R@1 0.57 -> 0.67; OrcaLoca File/Function/Line R@1 0.61/0.35/0.28 (the dedicated graph localiser is BELOW the bash-agent baseline at function level). Component decomposition of the +4.7 pass points: Tier 1 structural graph +1.7 (Function R@1 +0.07, File R@1 +0.05), data-flow slicing +2.0, bundling +1.0; a "Coarse" control with the slice tool present but empty graph is within 0.01 of Structural. Token cost: ~560k tokens/instance vs 510k for bare SWE-agent ("buys additional fixes at additional token cost", ~3,200 extra tokens per extra fix; Sec 5.3). Structure-only graph gain (+1.7) is "close to the +2.0" of RepoGraph on GPT-4o. Quote: "File identification is already well served by simple lexical matching, so there is little room to improve" (Sec 4.3).
- **Admitted limitations / future work**: Sec 6: `get_dataflow_slice` does not cross Calls edges (cannot trace a root cause mutated in a callee; dominant wrong-file category, Sec 5.2); localisation and repair measured in independent sessions so correlation (rho up to 0.53) is association only; benchmark contamination of the backbone.
- **Relevance**: The best controlled ablation in 2026 that says structure-only (contain/call) graphs add ~+1.7 pass points / +0.07 function R@1 on a mid-size open model; the large gain comes from a different primitive (data flow) that a calls-only graph does not have. Also shows the "tool present but empty = no effect" control.

#### SeeRepo: LLM Agents Can See Code Repositories
- **Ref**: Ma, Chen, ... Gu, ASE 2026 / arXiv 2606.14061 (v4 3 Aug 2026), Jun 2026, https://arxiv.org/abs/2606.14061
- **Contribution**: First systematic study of rendering a 4-relation repo graph (contains / imports / invokes / inherits) as images for multimodal agents (Mini-SWE-Agent), with the graph queried at runtime by node id, edge type and hop count; compares vision-only vs text+graph.
- **Numbers**: SWE-bench Verified (500), 4 models. Vision-only: Pass@1 drops GPT-5-mini 55.0 -> 41.4, Doubao-Seed-2.0-Lite 51.0 -> 16.9, Kimi K2.5 70.3 -> 55.0, with cost +42% / +268% / +27% (agents "resort to repeated graph queries to compensate for missing symbolic information"). Text tools + graph image (RQ2): GPT-5-mini 55.0 -> 55.4 (+0.4) with input tokens -25%, cost -26%; GPT-5.1 -2.2 points, cost -46%; Kimi K2.5 68.8 -> 70.6, cost -3%; Doubao +1.0, cost -6%. SWE-Rebench 2026.03 (110 inst., GPT-5-mini): 25.45 -> 26.36, tokens -34.9%. Authors' own explanation for the GPT-5.1 drop: graph queries "redirect attention toward dependencies that are topologically proximate but semantically tangential to the defect".
- **Admitted limitations / future work**: Sec 9.1: Python-only (SWE-bench Verified), efficiency measured only through token/trajectory proxies, model-specific tool-use tendencies may change the effect; static Graphviz layouts (Sec 9.2). Results averaged over 3 runs; accuracy deltas are small (+0.4, -2.2, +1.8, +1.0); frontier models only (GPT-5 family, Kimi K2.5, Doubao).
- **Relevance**: Even for large models the graph's accuracy effect is ~0 and the benefit is token efficiency, and a model without raw-text access spirals into repeated graph queries (the "tool misuse" failure).

#### DualView: Beyond Textual Repository Exploration: Dual-Modal Structural Reasoning for Agentic Issue Resolution
- **Ref**: Zhang, Huang, Liu, Chen, arXiv 2607.01929, Jul 2026, https://arxiv.org/abs/2607.01929
- **Contribution**: Four graph views (Module Coupling Graph from import counts, Function Call Graph ego-graphs with callers/callees/both, Class Hierarchy Graph, statement Program Dependence Graph) exposed via shell commands or MCP, with a visual (Graphviz image) plus textual response.
- **Numbers**: SWE-bench Pro public (731): up to 388 resolved, OpenCode+Kimi K2.5 +46 instances; 1.8-3.7 graph calls per instance; LLM steps 66.0 -> 60.0 (Claude 4.5 Sonnet). Ablation on a random 150-instance Pro subset (OpenCode+Kimi K2.5, resolved of 150): no graph 69; MCG only 72; **FCG (call graph) only 74**; CHG only 73; PDG only 75; all four, textual only 71 (+2); all four, visual only 78; full dual-modal 81. Cost $0.54 -> $0.49.
- **Admitted limitations / future work**: Sec V: every instance executed once (non-determinism, no repeated runs); renderer settings fixed and possibly sub-optimal; ablation on a 150-instance subset for cost reasons.
- **Relevance**: With identical information, the textual serialisation of all four graph views is only +2/150 over no graph (single run, within noise), and the call graph alone is +5/150; the paper's gain depends on images, which a text-only 4B/31B Gemma cannot use as an equivalent.

#### SemNav: SemNav: Semantic Navigation for Repository-Level Issue Localization
- **Ref**: Wei, Lei, Li, arXiv 2609.31176, 25 Sep 2026, https://arxiv.org/abs/2609.31176
- **Contribution**: Deterministic retrieval (BM25 + entity index) seeds a candidate workspace; a small LLM agent navigates a "Semantic Navigation Graph" (relations Contains, Calls, Imports, Inherits, References resolved ONLINE through a Pyright language server rather than from a static graph), reads issue-conditioned "Semantic Cards" instead of raw code, and updates an explicit Candidate Workspace.
- **Numbers**: All methods run with gemma-4-e4b-it ("Gemma 4B"), SWE-bench Lite (300). File Hit@1/5/10 | Function Hit@1/5/10: Agentless 36.0/45.7/45.7 | 4.7/5.0/5.0; CoSIL 51.7/68.3/68.3 | 24.0/31.3/31.3; LocAgent (graph tools) 54.3/62.3/62.3 | 22.7/42.3/43.0; **mini-swe-agent (bash only) 49.0/49.3/49.3 | 25.3/28.0/28.0**; RepoSearcher 42.7/56.3/56.3 | 1.7/5.7/5.7; SemNav 58.3/78.0/82.7 | 34.3/47.7/52.0. Qwen3.5-9B: CoSIL file Hit@10 80.7, LocAgent 74.3. Ablations (Gemma 4B): w/o Semantic Cards -6.0 File Hit@10; w/o Online Resolution (offline AST-initialised graph only) -7.0 File Hit@10; w/o Seed -13.2 Function Recall@10; w/o Workspace -19.2 Function Recall@10 (output shrinks from 9.96 to 1.50 functions). Cards cut working context by 48.2% vs full-source reading; total cost 25.4% below full-source reading. Downstream resolve 44.00 -> 52.33% (Qwen3.5 35B repair). PLocBench file Acc@5 60.41 -> 67.36.
- **Admitted limitations / future work**: I read the method, setup and results; no standalone limitations section found in the text I opened. Baseline numbers are re-run by the authors with a single small model, so absolute baseline numbers (e.g. RepoSearcher, Agentless) probably reflect small-model format failures.
- **Relevance**: THE closest paper to the target setting (Gemma 4 small model, graph tools, SWE-bench Lite). Plain bash mini-swe-agent with Gemma 4B reaches function Hit@1 25.3, ahead of the graph-tool LocAgent (22.7) and about equal to CoSIL (24.0), while the real gain comes from a deterministic seed (lexical + index), a candidate workspace and compact cards, not from edges. A static, offline-only graph is worth only ~7 points of File Hit@10 compared with online resolved relations.

#### RepoAtlas: RepoAtlas: Guiding Coding Agents via Evolving Multimodal Repository Views
- **Ref**: Zhang et al. (Beihang), arXiv 2609.16936, 15 Sep 2026, https://arxiv.org/abs/2609.16936
- **Contribution**: Training-free select-project-refresh loop over a repository code graph (edges: containment, inheritance, calls, imports, overrides, symbol use) that renders a budgeted visual + textual view and refreshes it when exploration state changes. Compared with mini-SWE-agent, LocAgent and SeeRepo.
- **Numbers**: SWE-bench Verified, resolve %: Qwen3.6-35B-A3B (self-hosted) mini-SWE-agent 60.8, **LocAgent 61.5** (input tokens 1010.6K -> 1570.6K, calls 56 -> 67), SeeRepo 60.8, RepoAtlas 63.1 (909K tokens). MiMo-V2.5: 65.4 / LocAgent 66.1 (695K -> 1219K tokens) / SeeRepo 66.9 / RepoAtlas 68.0. Kimi-K2.5: 68.0 / LocAgent 69.4 (693K -> 985K tokens) / SeeRepo 68.6 / RepoAtlas 72.4. Ablations (Qwen3.6): no node budget 59.8, no visual channel 61.2, no textual channel 59.2, no adaptive layout 60.4, no refresh 58.4, refresh at every call 51.0. LocBench selection: RepoAtlas selection beats fixed k-hop and PageRank-only variants. The authors note that with on-request views (SeeRepo-style) "at least one view is obtained in only 40.5% of instances in our reproduction", so RepoAtlas forces an initial view.
- **Admitted limitations / future work**: static graph cannot capture runtime-only dependencies; future work: execution traces and test feedback (Sec 7).
- **Relevance**: A third-party re-run shows LocAgent's graph tools add only +0.7 to +1.4 resolve points over plain mini-SWE-agent while costing 1.4-1.9x input tokens, on 30B-class open and frontier models; the reproduction of an on-request graph view shows only 40.5% of trajectories ever obtaining one, direct evidence of agents under-using an offered graph tool.

#### SWE-Adept: SWE-Adept: An LLM-Based Agentic Framework for Deep Codebase Analysis and Structured Issue Resolution
- **Ref**: He, Roy (Purdue), arXiv 2603.01327 (v3 27 Sep 2026), Mar 2026, https://arxiv.org/abs/2603.01327
- **Contribution**: Two-agent framework; the localisation agent does agent-directed depth-first traversal of code dependencies with compact code previews and filtering to keep context small; the resolution agent uses planning and git-style checkpoint tools. Provides an apples-to-apples localisation table of embeddings, bash agent, RepoGraph, LocAgent, OrcaLoca.
- **Numbers** (File Acc@3 / Func Acc@5 / tokens per instance; SWE-bench Lite then Pro; table): CodeSage-Large 71.2/40.1 ; 54.0/26.5. CodeRankEmbed 76.6/50.0 ; 61.0/33.0. SWE-agent GPT-5.2 84.3/60.0/78k ; 71.0/37.8/125k. RepoGraph GPT-5.2 86.8/60.6/150k ; 71.5/40.0/272k (graph: +0.6 func, ~2x tokens). LocAgent GPT-5.2 87.5/64.6/215k ; 73.8/42.3/355k. OrcaLoca GPT-5.2 87.2/64.2/265k ; 74.5/43.0/368k. SWE-Adept GPT-5.2 92.3/70.8/197k ; 77.5/46.0/252k. With Claude-Sonnet-4.5: SWE-agent 90.5/78.6/298k ; 78.0/55.0/340k; RepoGraph 92.0/79.2/412k ; 80.0/56.3; LocAgent 93.5/81.8/380k ; 82.0/57.3; SWE-Adept 97.0/87.8/348k ; 85.8/63.3. End-to-end resolve, Lite: SWE-agent 52.5 (GPT-5.2), RepoGraph 50.3 (GPT-5.2; 66.0 vs 66.2 Claude); mini-SWE-Agent 64.2 vs Claude Code 70.2 vs SWE-Adept 71.3. Open models (Func Acc@5 Lite): SWE-agent GLM-4.7-Flash-30B 55.5, Qwen3.5-27B 67.3; SWE-Adept 63.3 and 75.4.
- **Admitted limitations / future work**: Limitations: mostly proprietary models; absolute open-model numbers trail; no cross-task learning.
- **Relevance**: The best apples-to-apples 2026 table: a plain bash agent beats CodeRankEmbed by 10 function points; adding RepoGraph (call/contain graph) changes function Acc@5 by +0.6 (GPT-5.2) / +0.6 (Claude) at 1.4-1.9x tokens; gains come from the traversal policy and context control, not graph presence.

#### CodeNib: CodeNib: A Multi-View Data System for Serving Repository Context to Coding Agents
- **Ref**: Yu et al. (UC San Diego, USC, UC Riverside), arXiv 2607.25431 (v2 28 Sep 2026), Jul 2026, https://arxiv.org/abs/2607.25431
- **Contribution**: Treats lexical, dense and structural (graph) repository indexes as materialised views of one commit with incremental maintenance, and measures where precomputed views can replace a rebuild or a live language server; evaluates context serving to five agent models including Gemma 4-12B and Qwen3.5-9B/27B.
- **Numbers**: Substituting CodeNib views for LocAgent's provider: 78 of 90 runs finish vs 65, at lower cost ("shorter answers finish more tasks"). Lowest-token core arm uses 50-87% fewer trajectory tokens than paired grep/read across five models (Haiku 49.9%, Qwen-9B 45.1%, Qwen-27B 44.8%, Gemma 12.9%, Gemini 35.8% of grep/read tokens) with AnswerRecall@5 delta between -0.009 and +0.067; for Gemma, compaction trades 0.070 recall. Format-failure rates (agent needed a forced answer-format call): baseline/eager/compact 24.4/16.6/13.2% (Qwen 9B), 10.8/7.6/3.6% (27B), 12.0/1.8/0.6% (Gemma), 0 (Haiku). Static navigation matches the live language server on 705 of 940 requests (86% on definitions, references only reliable on Go), ready 1.23 s vs 6.35 s; symbol-level graph repair reproduces the rebuild on only 13 of 24 (Go/Python) source changes; vector reuse exact on 27 of 30 at 40x. 200 real SWE-bench Verified repairs (Claude Haiku 4.5): candidate injection + retirement resolves 79, 13 more than on-demand exploration, 23 more than Aider's repo map.
- **Admitted limitations / future work**: Sec 10: token counters missing for some providers; Haiku via a mutable hosted alias; interface defects found after first run mean Q6 is not an independent replication; concurrent updates out of scope.
- **Relevance**: Evidence that (a) a precomputed graph can be silently wrong ("completes every update without error and still returns the wrong graph half the time"), (b) small-model agents fail the answer format 12-24% of the time, (c) cost/quality of retrieval is about answer size, not graph richness. Uses Gemma 4-12B as a test model.

#### KGCompass: Enhancing Repository-Level Software Repair via Repository-Aware Knowledge Graphs
- **Ref**: Yang et al., arXiv 2503.21710 (v3 3 Oct 2025), Mar 2025, https://arxiv.org/abs/2503.21710
- **Contribution**: Knowledge graph linking issues, pull requests and code entities (files, classes, functions); mines 20 candidate functions by path/embedding relevance, then LLM selects; entity paths from the KG are added to the repair prompt.
- **Numbers**: SWE-bench Lite: 58.3% resolve (Claude-4 Sonnet), function-level location accuracy 56.0%, file-level 83.6%, ~$0.2 per repair. KG-only 20 candidates cover 68.7% of gold files, 40.4% of gold functions; LLM-only (Claude-3.5) 81.0% / 53.1%; hybrid 84.3% / 57.7%; Claude-4: LLM-only 77.3% / 52.6%, hybrid 91.0% / 66.7%. Repair, Claude-4, fixed candidates: no KG 91 resolved (30.3%), KG without paths 131 (43.7%), with entity paths 142 (47.3%). 89.7% of correctly localised bugs lie >=2 hops from the issue node.
- **Admitted limitations / future work**: Sec 6: only Python SWE-bench Lite; temporal filtering to avoid leaking future issues/PRs; ranking of patches is the main remaining headroom.
- **Relevance**: A KG that alone covers only 40.4% of gold functions; its strongest signal is historical issue/PR links, which a code-only calls graph does not contain.

#### CodexGraph: CodexGraph: Bridging Large Language Models and Code Repositories via Code Graph Databases
- **Ref**: Liu, Lan et al., NAACL 2025 / arXiv 2408.03910 (v3 Jul 2026), Aug 2024, https://arxiv.org/abs/2408.03910
- **Contribution**: Code graph in Neo4j (nodes MODULE/CLASS/METHOD/FUNCTION/FIELD/GLOBAL_VARIABLE; edges CONTAINS, INHERITS, HAS_METHOD, HAS_FIELD, USES), LLM writes Cypher queries via a "write then translate" two-agent design.
- **Numbers**: GPT-4o on SWE-bench Lite comparable to AutoCodeRover (22.96% Pass@1 reported); average token cost per instance on SWE-bench Lite (my reading of Table 2) BM25 14.8k, AutoCodeRover 76.0k, CodexGraph 102.3k. Removing the translation agent: EM 27.9 -> 8.3 on CrossCodeEval Lite even with GPT-4o. Performance degrades from GPT-4o to DeepSeek-Coder-V2 to Qwen2-72B because the agent "may struggle to formulate appropriate graph queries".
- **Admitted limitations / future work**: Sec 7: Python only; 43 Sympy instances excluded (graph indexing out of memory); schema should add function-call edges.
- **Relevance**: Free-form graph query languages are fragile for weaker LLMs; no call edges in the original schema; most expensive per instance.

#### OrcaLoca: OrcaLoca: An LLM Agent Framework for Software Issue Localization
- **Ref**: Yu, Zhang et al., ICML 2025 / arXiv 2502.00350 (v2 Oct 2025), Feb 2025, https://arxiv.org/abs/2502.00350
- **Contribution**: Agent over a CodeGraph that contains ONLY containment edges (directory/file/class/function) and function-call reference edges (App. A: "We didn't use static analysis to get references like the method A used in another function B"); adds priority-based action scheduling, action decomposition and distance-aware (shortest-path on the graph) context pruning.
- **Numbers**: SWE-bench Lite (Claude-3.5-Sonnet): function match 65.33%, file match 83.33%, resolved 41.00% (with another repair component); Agentless-1.5 resolved 34.67%; RepoGraph (GPT-4o) function match 47.67%, file 70.33%; mean over the leaderboard function match 53.5%. Ablation on a 93-instance subset: function match 76.34 -> 73.12 (no priority scheduling), 72.04 (no file & class decomposition), 70.97 (no disambiguation decomposition), 72.04 (no pruning), i.e. each component is worth 3-5 points on 93 instances (about 3-6 instances). No ablation removes the graph itself.
- **Admitted limitations / future work**: Sec 5: graph rebuilt per repo+commit (cost), Python-only, mostly Claude; open models (Qwen, LLaMA) left to future work. Independently, ARISE and CoSIL re-run it with Qwen2.5-Coder and find it below a plain bash baseline at function level (ARISE: 0.35 vs 0.43 Function R@1).
- **Relevance**: Its graph = containment + calls, the same information class as the competition's calls-only graph; no ablation shows the call edges matter.

### 4.3. Retrieval, embeddings and rankers (no graph)

#### SweRank: SweRank: Software Issue Localization with Code Ranking
- **Ref**: Reddy, Suresh, Doo et al., ICLR 2026 / arXiv 2505.07849 (v2 22 Apr 2026), May 2025, https://arxiv.org/abs/2505.07849
- **Contribution**: Retrieve-and-rerank for issue localisation: SweRankEmbed (bi-encoder, 137M initialised from CodeRankEmbed, and 7B from GTE-Qwen2) and SweRankLLM (listwise reranker, 7B/32B), trained on SweLoc (issue -> modified function pairs from GitHub with consistency filtering and iterative hard-negative mining).
- **Numbers** (SWE-bench Lite, file Acc@1/3/5 | module Acc@5/10 | function Acc@5/10; table): SweRankEmbed-Small (137M) 66.4/86.5/90.9 | 79.6/85.0 | 63.1/74.5. SweRankEmbed-Large (7B) 72.6/91.2/94.2 | 84.3/89.8 | 71.9/82.1. SweRankLLM-Small (7B rerank) 78.1/92.3/94.5 | 89.1/92.7 | 79.6/86.1. SweRankLLM-Large (32B) 83.2/94.9/96.0 | 90.9/93.4 | 81.4/88.7 (GPT-4.1 reranker 81.8 Acc@5 / 88.0 Acc@10 function). Compare LocAgent-Claude-3.5 function Acc@10 77.4 and CodeRankEmbed 58.8. Embedding-dimension ablation (Qwen3-Embedding-0.6B with Matryoshka, SWE-Bench-Lite Acc@5 / Acc@10 as in the paper's Table 10, before -> after SweLoc finetuning): D=1024 52.6->66.8 / 62.8->75.2; D=512 50.0->65.7 / 59.9->74.1; **D=256 44.2->59.1 / 52.9->69.7**; D=128 39.1->56.9 / 46.7->66.8; D=64 33.2->50.0 / 38.3->60.2. Latency: SweRankLLM-Small 12.5 s per instance on one A100, ~7x faster than LocAgent; ~$0.66 per example for Claude-3.5 agents. SWE-Bench Multilingual function Acc@10: SweRankEmbed-Large 50.9 vs proprietary Gemini-Embedding 47.4.
- **Admitted limitations / future work**: I found no explicit limitations section in the text I read; the training set is Python-only (generalisation to other languages is tested in App. F) and agent baselines are quoted from LocAgent's runs.
- **Relevance**: Shows a 256-d dense code embedding (when trained on issue-to-code pairs) costs 5.5 (tuned) to 9.9 (untuned) Acc@10 points vs 1024-d and that an off-the-shelf embedding (CodeRankEmbed 58.8) is much weaker than a task-tuned one (82.1); an unknown embedding of unknown training is not evidence of useful similarity search.

#### SweRank+: SweRank+: Multilingual, Multi-Turn Code Ranking for Software Issue Localization
- **Ref**: Reddy, Liu et al., arXiv 2512.20482, Dec 2025, https://arxiv.org/abs/2512.20482
- **Contribution**: Multilingual SweRankMulti plus SweRankAgent, an agentic loop that calls the ranker as a search tool with a memory buffer of candidates over multiple turns (GPT-5 as the agent LLM).
- **Numbers**: Function Acc@10 (Table 4) single-turn SweRankMulti -> SweRankAgent (GPT-5): SWE-PolyBench 59.5 -> 62.6 (+3.1), SWE-Bench-Multilingual 66.7 -> 73.1 (+6.4), SWE-Bench-Lite 85.8 -> 88.3 (+2.6), LocBench 69.5 -> 70.9 (+1.5), SWE-Bench-Verified 79.4 -> 81.7 (+2.3). A multi-query "Reformulate" baseline (original + 5 GPT-5 reformulations) is WORSE or flat vs the single query (-1.5, -1.7, 0.0, +0.4, -0.4: "introduces additional noise"). Largest agentic gains on low lexical overlap and multi-function issues.
- **Admitted limitations / future work**: Sec 6: Python-centric and single-pass limits of SweRank motivate this; the agent uses only small retriever/reranker variants for compute reasons.
- **Relevance**: Wrapping a strong ranker in a GPT-5 agent gives +1.5 to +2.6 Acc@10 on Python benchmarks (more on multilingual); issue-to-code search is near saturation for lexically overlapping issues.

#### CoRNStack / CodeRankEmbed: CoRNStack: High-Quality Contrastive Data for Better Code Retrieval and Reranking
- **Ref**: Suresh, Reddy et al., ICLR 2025 / arXiv 2412.01007 (v3 Mar 2025), Dec 2024, https://arxiv.org/abs/2412.01007
- **Contribution**: Large consistency-filtered contrastive corpus with hard negatives; CodeRankEmbed (137M) and CodeRankLLM; claims that earlier code embedders "underperform" on real bug localisation because of noisy training data.
- **Numbers**: Used as the reference embedding in later papers: SWE-bench Lite function Acc@10 58.8 and file Acc@5 84.7 (LocAgent's table); function Acc@5 33.0 on SWE-bench Pro (SWE-Adept). Jina-Code-v2 52.2, Codesage-large-v2 44.5, BM25 36.9 (function Acc@10).
- **Admitted limitations / future work**: Compute limits for the reranker study (App. A); Table 6 notes SWE-bench Lite may overlap pre-training of baselines.
- **Relevance**: Establishes the BM25 < generic code embedding < issue-tuned embedding ladder on function Acc@10 (36.9 < 52-59 < 74-82).

#### Code-representation study: Retrieval-Oriented Code Representations in Agentic Bug Localization
- **Ref**: Caumartin, Chen, Costa (Concordia), arXiv 2607.11046, 13 Jul 2026, https://arxiv.org/abs/2607.11046
- **Contribution**: File-level bug localisation as representation-driven retrieval on Long Code Arena and SWE-bench Verified; compares file paths, raw source and three LLM-generated representations (role-aware summaries, detailed summaries, bug-report summaries) under BM25, four dense retrievers (incl. Qwen3-Embedding-0.6B, GTE-Large, CodeXEmbed, BGE) and 7B/14B/32B LLM retrievers.
- **Numbers**: Role-aware summaries beat file-path representation by up to 40% Hit@5 with a 10.4-20.9x smaller footprint than raw source; BM25 on raw source is +138% over file paths on SWE-bench Verified; with Qwen3-Embedding role-aware summaries only tie the file-path baseline; best representation depends on model size (Qwen 7B: raw source -8.2% Hit@5 on SWE vs file path; Qwen 14B raw +31.3%; role summaries underperform file paths for 14B on both datasets); combination via RRF up to +31.9%, LLM post-ranking up to +42.0%; Agentless with the techniques reaches 94% Hit@6 file localisation (+4.7%).
- **Admitted limitations / future work**: Sec 8: single non-deterministic run; summaries generated by GPT-OSS-20B only; contamination; LLM retrievers return too few candidates; results may not transfer to other languages.
- **Relevance**: Directly about what text an embedding index encodes per node; a bare file path is a strong baseline and summary benefit is inconsistent for smaller LLMs.

#### BLAgent: BLAgent: Agentic RAG for File-Level Bug Localization
- **Ref**: Al Mamun, Uddin, TOSEM / arXiv 2605.17965 (v2 2 Jul 2026), May 2026, https://arxiv.org/abs/2605.17965
- **Contribution**: AST-chunked, path-augmented dense index + dual-perspective query transformation + bounded two-phase agentic reranking over only the 5-15 retrieved files; explicitly avoids graph traversal.
- **Numbers**: SWE-bench Lite file-level: direct dense retrieval, text chunking Top-1 0.350 / Top-10 0.686; code-aware 0.363 / 0.703; code-aware + file path 0.417 / 0.873 (MRR +16.9%); plus LLM reranking Top-1 0.673, Top-10 0.823. BLAgent Top-1 > 78% (GPT-OSS-120B) and 86.7% (Claude-4.6-Sonnet), >18x cheaper than LocAgent under the same model (LocAgent only completed 182 of 300 instances within budget). Failure taxonomy: 14 retrieval misses, 10 of them sympy (13.0% sympy failure vs 3.5% django) because bug reports describe symptoms in different vocabulary from low-level files.
- **Admitted limitations / future work**: The pipeline is bounded by the dense retriever's recall ("O2"); file level only.
- **Relevance**: Prepending the relative file path to each chunk lifts embeddings by 16.9% MRR: if the competition's 256-d node vectors are produced without path/identifier text, similarity search is handicapped; shows why lexical fallback is competitive.

#### Agentless: Agentless: Demystifying LLM-based Software Engineering Agents
- **Ref**: Xia et al., arXiv 2407.01489 (v2 29 Oct 2024), Jul 2024, https://arxiv.org/abs/2407.01489
- **Contribution**: Three-phase hierarchical localisation (LLM over repo tree -> files; embedding retrieval over chunks of files that survive an irrelevant-folder filter; classes/functions via skeleton; line edits).
- **Numbers** (SWE-bench Lite, share of instances whose gold location is contained; Table 2): file level, prompting only 78.67% ($0.02), embedding only without irrelevant-folder filter 67.67% ($0.05), embedding with filter 70.33% ($0.04), combined 81.67% ($0.06). Related-element step: complete file 53.67% vs skeleton format 58.33% (and cheaper). Edit locations: greedy 50.67%, multi-sample merged 56.33%. Overall 32.00% resolve at $0.70.
- **Admitted limitations / future work**: relies on strong LLMs and a fixed pipeline; benchmark issues contain some wrong or leaked solutions (paper's manual SWE-bench-Lite-S analysis).
- **Relevance**: Prompting-only localisation (repo tree) beats embedding-only by 8-11 points and the combination adds +3; shows embeddings are complementary rather than primary.

#### BugCerberus: Bridging Bug Localization and Issue Fixing: A Hierarchical Localization Framework Leveraging Large Language Models
- **Ref**: Chang, Zhou, Wang, Lo, Li, arXiv 2502.15292, Feb 2025, https://arxiv.org/abs/2502.15292
- **Contribution**: Three Llama-3-8B models fine-tuned per level (file, function with a function call graph as the context representation, statement) searched hierarchically.
- **Numbers**: At statement level beats the state of the art in Top-N (N=1,3,5,10) by 16.5%, 5.4%, 10.2%, 23.1%; plugged into Agentless raises the fix rate by 17.4% over the best baseline. Ablation: removing file-level localisation causes a 94.3% drop in Top-5 accuracy (statement level; 96% in MAP), i.e. the hierarchy depends on getting the file right.
- **Admitted limitations / future work**: Threats section: Llama pre-training data may overlap SWE-bench repos; buggy-element annotation criteria vary.
- **Relevance**: Call-graph context is used only at function level for an 8B fine-tuned model, with file selection as the dominant bottleneck.

### 4.4. Graph edge types, GNNs and "graph inside the lexical loop"

#### GREPO: GREPO: A Benchmark for Graph Neural Networks on Repository-Level Bug Localization
- **Ref**: Wang, Chen, Wang, ... Zhang (Peking U., Ant Group), arXiv 2602.13921, 14 Feb 2026, https://arxiv.org/abs/2602.13921
- **Contribution**: 86 Python repositories, 47,294 bug-fixing tasks, per-commit heterogeneous graph (nodes: directories, files, classes, functions; edges Contain, Call, Child/Inherit, each with reverse edges; incremental, temporally indexed). Node features: Qwen3-Embedding-8B 4096-d embedding of node text + file path; query-node similarity; anchor nodes (semantic anchors from the embedding retriever CF-RAG, and temporal anchors = recently modified code). Trains GNNs (GCN, GIN, GraphSAGE, GAT, GATv2, GPS) and compares with LocAgent (Qwen2.5-72B), Agentless (GPT-4o) and CF-RAG.
- **Numbers**: Hit@K = recall of the full ground-truth function/class set (so absolute values are low), average over 9 held-out repos: Hit@10 CF-RAG (embedding RAG) 10.85, LocAgent 12.01, Agentless 22.62, GCN 35.52, GIN 36.99, GAT 37.40, GATv2 37.68, GPS 35.30. Edge ablation on GAT, Hit@10 (full 37.40): w/o Contain 34.87 (-2.5), **w/o Call 37.15 (-0.25; Hit@5 actually 32.01 vs 31.51 full)**, w/o Inherit 35.94 (-1.5); w/o edge-type embeddings 36.29; w/o query-node similarity 36.57; w/o semantic anchors 36.40; **w/o temporal anchors 24.18 (-13.2)**. Zero-shot training on 77 repos matches training on all 86.
- **Admitted limitations / future work**: Conclusion: Python only; future extension to other languages; graphs rely on Tree-sitter + Jedi call resolution; GNN training needs a corpus of repos with bug-fix history.
- **Relevance**: The only controlled edge-type ablation in a learned model: removal of call edges is a no-op, containment and inheritance matter, and a git-history prior (recently modified) dwarfs every structural signal. A calls-only graph with no history is the weakest variant tested.

#### LARGER: LARGER: Lexically Anchored Repository Graph Exploration and Retrieval
- **Ref**: Hu, Su, ... Zhao (Emory / CausalDynamics), arXiv 2605.16352, 8 May 2026, https://arxiv.org/abs/2605.16352
- **Contribution**: Instead of separate graph tools, expose confidence-filtered graph neighbours (contains, imports, invokes, inherits; edge confidence by provenance, e.g. resolved import > heuristic) inside the agent's existing lexical (grep) search results; claims no extra tool call and no external graph DB.
- **Numbers**: File-level, GPT-5.2 backbone (LocBench Acc@1 / Acc@5 | MuLocBench Acc@1 / Acc@5; table): BM25 23.4/49.3 | 10.6/24.5; Agentless 56.1/68.9 | 20.4/28.9; SWE-agent 60.0/70.9 | 21.0/31.3; OpenHands 57.7/67.5 | 27.3/43.7; Codex 63.2/74.1 | 28.0/50.0; Claude Code (Opus-4.6) 65.1/75.2 | 29.2/54.9; mini-swe-agent 60.6/70.7 | 26.9/46.6; **graph-tool agents CoSIL 54.6/68.2 | 18.1/27.0 and LocAgent 56.0/65.3 | 17.9/25.7 (below plain bash agents)**; LARGER (fixed) 72.9/87.0 | 27.4/55.7 (+12.9 Acc@5 vs Codex on LocBench, +5.7 on MuLocBench; Acc@1 on MuLocBench -0.6 vs Codex). Cost: MuLocBench tokens 521.8K -> 353K and wall-clock 139.9 s -> 99.9 s vs Codex; LocBench time 129.2 s -> 60.0 s. Ablation (MuLocBench Acc@5, full 55.7): w/o graph expansion 48.2 (-13.5%), noise control -4.7%, subsystem priors -4.1%, all modules removed 46.8 (-16%). Averages of 3 runs.
- **Admitted limitations / future work**: I read the method/experiments and found no standalone limitations section; only GPT-4.1 / GPT-5.2 / Claude Code backbones; theory (recall dominance, conditional token dominance) assumes monotone submodular utility and that relevant nodes are within K hops of a lexical anchor.
- **Relevance**: The counter-example to "graphs give no gain": it works when the graph is a post-processor of grep hits (entry points = lexical anchors), not a separate tool the agent must decide to call; it also reports that standalone graph-tool agents (LocAgent, CoSIL) underperform bash agents with GPT-5.2. No small-model result.

### 4.5. Localisation studies, grep vs index, and tool-use behaviour

#### SWE-Explore: SWE-Explore: Benchmarking How Coding Agents Explore Repositories
- **Ref**: Zhang, Wang, Liang, ... Gu (SJTU), arXiv 2606.07297, 5 Jun 2026, https://arxiv.org/abs/2606.07297
- **Contribution**: 848 issues, 10 languages, 203 repos; ground truth = line regions that independent successful agent trajectories actually read; metrics for coverage, ranking (nDCG under a line budget) and context efficiency; validated by giving each explorer's K=5 regions to a fixed patcher in a restricted-context sandbox.
- **Numbers** (GPT-5.4 explorers; restricted-context downstream resolve %, n=150): Oracle 59.7, CoSIL 59.3, Codex 50.3, Mini-SWE-Agent 50.0, Claude Code 48.0, OpenHands 47.7, OrcaLoca 45.3, AutoCodeRover 44.7, LocAgent 44.7, AweAgent 41.3, TF-IDF 26.0, RAG with a static-embedding retriever 23.3, BM25 12.7, Random 4.7. General coding agents reach HitFile ~0.65 but line recall only 0.14-0.19; "LocAgent resembles the general-agent profile rather than changing the recall frontier"; CoSIL (iterative code-graph search) has "by far the highest non-oracle Recall and F1". Context efficiency has the highest correlation with downstream resolve (Pearson 0.95). Same Mini-SWE-Agent with different LLMs: HitFile GPT-5.4 0.655, GPT-5.4-mini 0.649, Sonnet-4.5 0.535, Kimi-K2.6 0.509, Gemini-3-Pro 0.369, GLM-4.7 0.343.
- **Admitted limitations / future work**: line-level labels are derived from successful trajectories (may encode the reading habits of those agents); one-time restricted-context validation; I did not recover the text of its Limitations paragraph from the HTML.
- **Relevance**: Independent 2026 evidence that (i) one-shot lexical/embedding retrieval is far below agentic exploration, (ii) a graph-tool localizer (LocAgent) does not move the frontier, while an iterative call/import-graph search (CoSIL) does, so the graph's value depends on the search policy, not its presence.

#### DCI: Beyond Semantic Similarity: Rethinking Retrieval for Agentic Search via Direct Corpus Interaction
- **Ref**: Li, ... Jiang, Zhang, arXiv 2605.05242, 3 May 2026, https://arxiv.org/abs/2605.05242
- **Contribution**: Agent searches the raw corpus with terminal tools (grep, file reads, shell scripts) instead of a top-k retriever; no embeddings, no index. Not code: BrowseComp-Plus, multi-hop QA, BRIGHT and BEIR.
- **Numbers**: BrowseComp-Plus with Claude Sonnet 4.6: 69.0% (Qwen3-Embedding-8B retriever) -> 80.0% with DCI, cost $1,440 -> $1,016. DCI-Agent-Lite with GPT-5.4 nano: 62.9% at $93. Multi-hop QA: 83.0% vs 52.3% for the strongest retrieval agent (ASearcher-Local-14B). BRIGHT NDCG@10 68.5 vs 47.0 for the best retrieval baseline (ReasonRank-32B). Claude Code tool mix: Bash 62.4%, Grep 33.0%, full-document reads only 9.1% of Bash. Scaling: adding 100K distractor docs (100K -> 200K) drops accuracy to 37.5% with 122 tool calls ("scales well in search depth, rapidly rising costs in search breadth").
- **Admitted limitations / future work**: Sec RQ4: DCI has a clear operating envelope, degrading and getting expensive as the corpus grows; benefits depend on strong base agents.
- **Relevance**: Strongest general evidence that a competent agent with grep makes a pre-built similarity index redundant; a repo of ~4,000 call-graph nodes is far below the scale where DCI degrades.

#### Deep Agentic Search vs Semantic Search: Deep Agentic Search for Repository-Level Code Question Answering: An Empirical Study
- **Ref**: Rafiei Oskooei et al., arXiv 2608.01507, 2 Aug 2026, https://arxiv.org/abs/2608.01507
- **Contribution**: On SWE-QA with four LLMs, compares a pre-built vector index (semantic search) against a planner delegating grep-style exploration to an isolated subagent.
- **Numbers**: Semantic search answers 65.2% correctly vs 46.2% for deep agentic search, at less than half the cost per correct answer; 41.8% of the subagent design's failures occur at the planner-subagent hand-off and are usually silent (confident wrong answer).
- **Admitted limitations / future work**: Sec 8 threats to validity (QA rather than patching; specific harness; four models); I did not extract the details.
- **Relevance**: Counter-evidence to DCI above: with a QA task and a subagent design, the index wins. Shows the grep-vs-index result depends on task and harness, not a settled law.

#### AgentConnect grep-vs-LSP pilot (blog, not peer reviewed): Grep beats LSP? Why coding agents ignore your fancier tools
- **Ref**: Xu, AgentConnect blog, 12 Aug 2026, https://www.agentconnect.md/blog/grep-beat-lsp-harness/
- **Contribution**: Pilot on remeda, hono, requests with Claude Opus 4.8, Sonnet 4.6, Haiku 4.5: do agents pick semantic (LSP) navigation tools when offered alongside grep?
- **Numbers**: Free-choice use of semantic navigation on localisation tasks: Opus 0%, Sonnet 4%, Haiku 6%; on "find every caller" tasks 45-57%. Forcing semantic-first on localisation drops success from 100% to 89%. Callers task: LSP precision 1.00 vs grep 0.76, recall ~0.66 in both; token change by repo +16% / -12% / +19%. Multi-file rename (Opus): grep pass@1 1.00 in 2,451 tokens vs LSP 0.67-0.83 in 3,336-4,131 tokens.
- **Admitted limitations / future work**: Author: "signals rather than verdicts"; small task sets, 2-3 rollouts per cell, three Claude models; only references/definitions/symbols tested; the author cannot prove training familiarity with grep explains the result.
- **Relevance**: The only direct measurement I found of agents under-using an offered structured-navigation tool (0-6% on localisation), and it shows tool use rises exactly on the task where the tool has an information advantage (completeness of callers).

### 4.6. Terminal-only RL agents and tool-design for small models

#### CodeScout: CodeScout: An Effective Recipe for Reinforcement Learning of Code Search Agents
- **Ref**: Sutawika, Soni, ... Neubig, arXiv 2603.17829, 18 Mar 2026, https://arxiv.org/abs/2603.17829
- **Contribution**: RL (modified GSPO, multi-level F1 reward over files/modules/functions plus a turn-completion reward) of Qwen3-1.7B / 4B-Instruct-2507 / 14B in the OpenHands-Bash scaffold (a plain terminal: rg/grep/find/ls plus a structured finish tool, no repository graph); trained on 39K SWE-Smith instances from 128 non-overlapping repos; context 40-50K tokens, 4-6 turns.
- **Numbers**: SWE-bench Verified File F1 / Function F1: CodeScout-1.7B 55.46 / 28.22; **CodeScout-4B 68.52 / 36.78**; CodeScout-14B 68.57 / 40.32; RepoNavigator-7B (single "jump" tool) 51.63 / 27.49; RepoNavigator-32B 67.75 / 34.09; RepoNavigator + Claude-Sonnet-4.5 79.94 / 43.62. SWE-bench Lite: 1.7B 56.57 / 27.07; 4B 67.03 / 39.87; 14B 71.84 / 44.43; Qwen3-32B (Thinking) + OpenHands-Bash 58.98 / 23.76. SWE-bench Pro: 4B 51.77 / 29.03. RL gains over the corresponding base model in the same bash scaffold: 4B +14 to +19 file F1, +21 to +31 function F1; 1.7B base is near zero F1. CodeScout-4B beats Qwen2.5-32B in the OrcaLoca scaffold by ~10 file F1 and 8-11 function F1, and Qwen2.5-32B in the CoSIL scaffold on Pro by 20-33 file F1. With frontier models the bash-only agent beats the specialised RepoNavigator scaffold (Sonnet-4.5: +18 function F1; GPT-5 > Claude-3.7 with RepoNavigator by 23 function F1), "specialized scaffolds ... can even degrade model performance". Frontier models fall to near zero without a reminder prompt to submit. Downstream (OpenHands, Qwen3-4B-Instruct): 13.4% -> 17.2% resolve when given CodeScout-14B locations (oracle locations 19.6%), input tokens -17.5%.
- **Admitted limitations / future work**: Appendix D: training and evaluation largely restricted to Python (no multilingual training counterpart, patch-to-location extraction is language-specific); ground-truth targets are the patch-modified regions only and may omit context needed to understand the issue (shared by all baselines); does not cover repo-level QA/search (SWE-QA, CodeAssistBench). Sec 5.3: frontier models fall to almost zero without a prompt reminder to submit.
- **Relevance**: The most direct evidence for a 4B model: a terminal-only agent that is TRAINED for the task reaches 67-69 file F1 on Lite/Verified; no graph needed. An untrained 4B in a graph-tool scaffold is a different regime (near-zero for the 1.7B base in bash).

#### RepoNavigator: One Tool Is Enough: Reinforcement Learning of LLM Agents for Repository-Level Code Navigation
- **Ref**: Zhang et al., ICML 2026 / arXiv 2512.20957 (v6 26 May 2026), Dec 2025, https://arxiv.org/abs/2512.20957
- **Contribution**: One tool: `jump` to the definition of an invoked symbol (language server), RL (GRPO, hybrid reward including tool-call success rate) directly from Qwen2.5-Instruct 7B/14B/32B. Argues multi-tool pipelines compound failure probability (P_succ(k) = prod p_i, Sec 5.2) and enlarge the prediction space to the whole repo, while a jump tool's access scope is the transitive closure from the entry point.
- **Numbers** (SWE-bench Verified, Qwen2.5-7B, training-free; function Sample-F1 / file Sample-F1): Agentless 15.31 / 27.82; CoSIL 12.90 / 27.39; LocAgent (graph) 12.71 / 40.67; OrcaLoca 21.70 / 47.36; RepoSearcher 7.48 / 27.36; RepoNavigator 16.19 / 42.12. After GRPO: RepoNavigator-7B 27.49 / 51.63 (RepoSearcher distil+GRPO 27.37 / 31.64). Closed models in the RepoNavigator scaffold: Claude-3.7 31.72 / 73.01; GPT-5-chat 31.17 / 58.88; Claude-4.5 43.62 / 79.94.
- **Admitted limitations / future work**: dynamic (runtime-only) dependencies such as monkey-patching are outside the jump scope (Sec 5.3); Python; metrics are Sample-F1/IoU rather than Acc@k.
- **Relevance**: A training-free 7B with a graph-tool agent (LocAgent) does beat Agentless on file F1 (+12.9) but not on function F1 (12.7 vs 15.3); the lone best untrained 7B agent here is OrcaLoca (calls + containment graph, 47.4 / 21.7), so graph tools can help small models in some scaffolds, contradicting the simplest reading of the competition data.

#### ToolTrain / RepoSearcher: Tool-integrated Reinforcement Learning for Repo Deep Search
- **Ref**: Ma, Peng, ... Xie, ICSE 2026 / arXiv 2508.03012, Aug 2025, https://arxiv.org/abs/2508.03012
- **Contribution**: RepoSearcher agent with 6 name-based tools (GetRepoStructure, GetImportOfFile, SearchClass, SearchFunction, SearchClassMethod, Exit; no call graph), trained by rejection-sampled SFT then tool-integrated RL.
- **Numbers** (SWE-bench Verified, function Recall@5): Claude-3.7 CoSIL 66.38, RepoSearcher 66.08, LocAgent 60.59; Qwen-7B in the original frameworks Agentless 25.10, OrcaLoca 28.57, **LocAgent 17.72**; ToolTrain-32B in RepoSearcher 68.55 (beats Claude-3.7); ToolTrain-7B beats other frameworks that use 32B models; generalises to the CoSIL scaffold (30.47 -> 50.87 Recall@5). Untrained RepoSearcher is weak with Qwen models "due to its simpler agent design".
- **Admitted limitations / future work**: Python; training-data and RL cost; I did not extract a limitations section.
- **Relevance**: Confirms that for small open models the bottleneck is tool-calling skill, and that a graph-tool agent (LocAgent) is the WORST of four frameworks at 7B (17.7 vs 25-29) without task training.

#### SWE-agent ACI ablation: SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering
- **Ref**: Yang et al., NeurIPS 2024 / arXiv 2405.15793, May 2024, https://arxiv.org/abs/2405.15793
- **Contribution**: Interface design study; ablates search, editing, viewer and context tools with GPT-4 Turbo on SWE-bench Lite (resolve %).
- **Numbers**: Summarized search 18.0; no search tool 15.7; iterative (one-result-at-a-time) search 12.0, i.e. a badly designed search tool is worse than none because "agents tend to look through every match exhaustively, calling next until each result has been inspected".
- **Admitted limitations / future work**: findings tied to GPT-4 Turbo and Lite; cost/context exhaustion is the failure channel.
- **Relevance**: Early evidence that adding a tool can lower results when its output format invites loops; tool outputs must be short and summary-shaped (16k-32k context).

### 4.7. Code knowledge graphs as retrieval or MCP services

#### Codebase-Memory: Codebase-Memory: Tree-Sitter-Based Knowledge Graphs for LLM Code Exploration via MCP
- **Ref**: Vogel et al. (independent / Charite), arXiv 2603.27277, 28 Mar 2026, https://arxiv.org/abs/2603.27277
- **Contribution**: Tree-sitter parser (66 languages) writes a code knowledge graph (calls, containment, imports, inheritance, communities) to SQLite, exposed as 14 MCP tools.
- **Numbers**: 31 languages, one repo each (78 to 49,398 nodes), 12 question categories (hub detection, caller ranking, dependency manifests, call-chain tracing): graph agent quality 0.83 vs 0.92 for a grep/read Explorer agent, using ~1,000 vs ~10,000 tokens per question (10x), 2.3 vs 4.8 tool calls (2.1x), <1 ms vs 10-30 s query latency (both Claude Opus 4.6). Index of 49K nodes built in 6 s. Weakest: macro-heavy C (0.58 vs 1.00); line-level code questions the graph does not store.
- **Admitted limitations / future work**: Threats to Validity: one backend (Claude Opus 4.6), first-author grading on a 0-1 scale against manual references, one repository per language, static structure only (no runtime behaviour, reflection or dynamic dispatch), query ceiling of 100k rows; comparison against embedding-based RAG, ctags/LSP and other graph systems is left as future work; string-level callee resolution (strategies 1-3 resolve ~80%) limits Go/pointer accuracy.
- **Relevance**: Not issue localisation. It shows that a calls graph pays off on structural questions (callers, chains) in tokens and latency but loses ~9 quality points to grep/read; a graph with only call edges answers a different question from "where is the bug".

#### AST graph vs LLM-extracted graph: Reliable Graph-RAG for Codebases: AST-Derived Graphs vs LLM-Extracted Knowledge Graphs
- **Ref**: Chinthareddy, arXiv 2601.08773, 13 Jan 2026, https://arxiv.org/abs/2601.08773
- **Contribution**: Three pipelines on Java repos (Shopizer, ThingsBoard, OpenMRS Core), 15 architecture/code-tracing queries each: vector-only RAG, LLM-extracted KG, deterministic Tree-sitter KG.
- **Numbers**: Deterministic KG build 2.81 s (Shopizer) vs 200.14 s for LLM-KB (883.74 s ThingsBoard); LLM extraction skipped 377 files (per-file success 0.688, 833 of 1,210), embedded corpus coverage 0.641 vs 0.902 deterministic vs 1.0 vector-only; nodes 842 vs 1,158.
- **Admitted limitations / future work**: single-author, only 15 queries per repo, Java only; quality measured by coverage/latency/cost signals more than answer accuracy.
- **Relevance**: A deterministic AST graph is cheap and complete; but this study measures indexing, not agent benefit.

#### DeepDiscovery: DeepDiscovery: A Location-Inference Framework for Task-Level Repository Understanding
- **Ref**: He, Sun et al. (Alibaba AMAP, NTU), arXiv 2606.22906 (v2 14 Sep 2026), Jun 2026, https://arxiv.org/abs/2606.22906
- **Contribution**: Budgeted task-level context recovery: localise high-confidence anchors then expand over a multi-relational repository structure, explicitly "without persistent offline indexes or pre-built repository graphs".
- **Numbers**: SWE-bench Verified solve rate 78.6% with the module swapped in, +8.2 points over the matched baseline; Full Recall Rate gains of 1.6-9.2 points on large internal projects, 2.5-7.4 on medium; best file recovery quality on 27 medium tasks among five baselines.
- **Admitted limitations / future work**: I read the abstract and introduction only; internal industrial tasks are not public.
- **Relevance**: Another anchor-then-expand design (cf. LARGER): expansion from lexically/semantically anchored entry points rather than global graph traversal tools.

### 4.8. LLM reasoning on large graphs (graph-to-text and graph tools)

#### GraphGym: Unified Multi-Dimensional Benchmark for Complex Graph Reasoning in Large Language Models
- **Ref**: Wang, Al-Lawati et al. (Penn State), arXiv 2608.12391, 2 Aug 2026, https://arxiv.org/abs/2608.12391
- **Contribution**: Semi-automatic benchmark (202 tasks) with graph sizes 10 / 100 / 1,000 / 10,000 nodes, three modes: textual reasoning (graph in prompt), coding-inline (graph in prompt, model writes code) and coding-file (graph given as a file path and code is executed); LLMs 7B-70B (Llama, DeepSeek, Qwen, Gemma) plus o4-mini.
- **Numbers**: EM falls monotonically with graph size for all model-mode pairs: coding-inline 77.9 (n=10) -> 14.2 (n=10,000); textual 66.7 -> 10.4; **coding-file 77.7 -> 46.3** (graph read by executed code, remaining drop from timeouts/memory). Qwen2.5-72B textual: 31.7 EM at size 10 -> 0.5 at 10,000. Fine-tuned graph models "struggle to generalize"; retrieval augmentation helps textual but not coding reasoning consistently.
- **Admitted limitations / future work**: partial coverage at large sizes (graph generation time limit 10 min); benchmark uses synthetic/LLM-generated tasks.
- **Relevance**: Putting graph structure into the prompt collapses at ~100+ nodes; querying it through code/tool calls does not. The competition's graph (~3,900 nodes) is only usable through tools, never in text.

#### GrAlgoBench: Exposing Weaknesses of Large Reasoning Models through Graph Algorithm Problems
- **Ref**: Zhang, Ruan et al. (HKUST-GZ), ICLR 2026 / arXiv 2602.06319, 6 Feb 2026, https://arxiv.org/abs/2602.06319
- **Contribution**: Nine graph-algorithm tasks with controllable difficulty to probe large reasoning models.
- **Numbers**: Accuracy "falls below 50% once graphs exceed 120 nodes", driven by execution errors, weak memory and redundant reasoning; over-thinking from ineffective self-verification inflates traces without gains.
- **Admitted limitations / future work**: I did not locate an explicit limitations section; the evaluation is of large reasoning models reading the graph in context.
- **Relevance**: Even large reasoning models cannot hold a 120+ node graph; a 4B model with 32k context cannot reason over ~3,900 nodes in text.

#### EstGraph: Evaluating LLMs on Large-Scale Graph Property Estimation via Random Walks
- **Ref**: Maurya, ACL 2026 / arXiv 2605.01484, 2 May 2026, https://arxiv.org/abs/2605.01484
- **Contribution**: Benchmark of four graph-property estimation tasks on graphs up to millions of nodes, with random-walk sampled prompts.
- **Numbers**: In a simple edge-list to adjacency-list conversion, "as the size of the graph grows, all LLMs start to miss existing edges or hallucinate new edges"; reasoning models err less but errors still rise with size.
- **Admitted limitations / future work**: not extracted in detail.
- **Relevance**: Textual graph serialisation is lossy at repository scale even for strong models; ego-graph tools should return small, verified neighbour lists.

#### GraphAgent-Reasoner: Scalable and Accurate Graph Reasoning with LLM-Based Multi-Agents
- **Ref**: Hu, Lei et al. (Renmin U., Ant Group), arXiv 2410.05130 (v3 25 Nov 2025), Oct 2024, https://arxiv.org/abs/2410.05130
- **Contribution**: Distributes a graph across node-centric LLM agents (training-free) to scale past context limits; evaluated on GraphInstruct (shortest path etc.) up to 1,000 nodes (16,000 tokens of input at 1,000 nodes).
- **Numbers**: near-perfect accuracy to 500 nodes and mostly held at 1,000; single LLMs and fine-tuned GraphWiz models (LLaMA2-7B based) degrade strongly and overfit to the training task formats.
- **Admitted limitations / future work**: scope is polynomial-time graph tasks (abstract); I did not extract a limitations section.
- **Relevance**: Corroborates that single-LLM text reasoning does not scale to repository-size graphs and that fine-tuned graph reasoners overfit their task formats.

### 4.9. More graph-based localisers (mixed ablations)

#### GraphLocator: GraphLocator: Graph-guided Causal Reasoning for Issue Localization
- **Ref**: Liu, Peng, Gao, ... Jin (Peking U., ByteDance), FSE 2026 / arXiv 2512.22469, 27 Dec 2025, https://arxiv.org/abs/2512.22469
- **Contribution**: Repository graph "RDFS" (vertex types dir/pkg/file/class/method/func...; edge types UsedBy (calls and field use), ImportedBy, ExtendedBy, ImplementedBy, HasMember) plus an LLM-built causal issue graph (CIG) of sub-issues; search tools `search_vertex` (type + wildcard name) and `search_edge`.
- **Numbers** (success-location SL %, function level, SWE-bench Lite): GPT-4o: SWERank-Large (embedding only) 55.2, Agentless 53.4, LocAgent 52.0 (precision 7.2), CoSIL 46.2, GraphLocator 60.7; Claude-3.5: Agentless 37.9, LocAgent 58.5, CoSIL 59.2, GraphLocator 70.8. Average +19.49% function recall, +11.89% precision. Ablation (Claude-3.5, 987 issues, function SL / F1): full 61.73 / 30.91; **w/o `search_vertex` (name/type search) 25.48 / 14.23**; w/o `search_edge` (graph-edge query) 51.59 / 28.45 (-10.1 SL); w/o priority queue 54.76 / 29.54; w/o CIG guidance 59.30 / 21.50. Token use 99.4k vs LocAgent 211.2k input tokens with GPT-4o (-52.9%), cost -43.5%.
- **Admitted limitations / future work**: Sec 6.2: baselines run with default settings from official code; avoids very recent LLMs (Claude-3.7, GPT-5) for contamination reasons, so absolute numbers are for GPT-4o / Claude-3.5; CoSIL adapted to Java through Magentless; one run per setting.
- **Relevance**: The graph-edge tool is worth ~10 points of function SL, but name/type search is worth ~36 points; and an embedding-only ranker (SWERank-Large) beats three graph/agent localisers on GPT-4o.

#### CGM: Code Graph Model (CGM): A Graph-Integrated Large Language Model for Repository-Level Software Engineering Tasks
- **Ref**: Tao et al. (Ant Group et al.), NeurIPS 2025 / arXiv 2505.16901 (v4 Jun 2025), May 2025, https://arxiv.org/abs/2505.16901
- **Contribution**: Fine-tunes an open LLM (Qwen2.5-72B) to read a code graph directly: node attributes encoded by CodeT5+ and mapped by an adapter into the LLM input; the graph structure enters the attention mask; an agentless pipeline (Rewriter -> Retriever -> Reranker -> Reader) selects the subgraph. Graph has up to 7 node types and 5 edge types (contains, calls, imports, extends,...).
- **Numbers**: 43.00% resolve on SWE-bench Lite with Qwen2.5-72B (authors' claim: first among open-weight models, +12.33 over the previous best open-weight method).
- **Admitted limitations / future work**: I did not extract the ablation or limitation sections.
- **Relevance**: Shows a graph can be injected through attention/embedding rather than text, but it needs 72B fine-tuning on graph-structured data; not applicable to a frozen 4B/31B with 256-d node vectors.

### 4.10. Studies on whether localisation or exploration help the downstream agent

#### FL-for-agentic-repair study: From Finding to Fixing: How Useful is Fault Localization for Agentic Program Repair?
- **Ref**: Shi, Yang, Chen (U. Alberta), arXiv 2610.25826, 19 Oct 2026, https://arxiv.org/abs/2610.25826
- **Contribution**: Six FL methods (LocAgent, CoSIL, OrcaLoca on SWE-bench Verified; AutoFL, SoapFL and FlexFL on Defects4J v3) injected as suspicious locations into a mini-SWE-agent repair run, three repair models (GPT-5.6 Luna, DeepSeek-v4 Flash, Gemini 3.1 Flash Lite), 16,248 trajectories.
- **Numbers**: SWE-bench Verified pass@1, no-FL baseline -> with LocAgent / CoSIL / OrcaLoca: GPT-5.6 Luna 73.4 -> 72.0 / 72.0 / 71.2; DeepSeek-v4 Flash 79.0 -> 76.0 / 76.8 / 77.2; Gemini 3.1 Flash Lite 57.8 -> 57.2 / 58.2 / 57.0. Over the 18 with-FL settings the change ranges from -4.45 to +0.40 points and is negative in 17; 16 of 18 McNemar p >= 0.05; every setting has both gains and losses (e.g. LocAgent: 16 gains / 23 losses on GPT-5.6 Luna, 41 / 44 on Gemini Flash Lite). Gold locations reduce repair tokens by up to 39.2%, but the FL methods consume more tokens than they save in repair.
- **Admitted limitations / future work**: Sec 6 threats: one run per setting; manual analysis covers 160 trajectories; FL supplied once before repair (findings may differ for on-demand FL); SWE-bench Verified and Defects4J may overlap training data; single reference patch under-represents locations used by successful repairs.
- **Relevance**: The most direct 2026 evidence that graph/agentic localisers do not improve a modern agent's repair (point estimates negative); a new paper on graph tools in this competition collides with this on the "no gain" side.

#### Multi-file localisation structure: Exploration Structure in LLM Agents for Multi-File Change Localization
- **Ref**: Fattha, Chua, Jiang, Wynter (SMU), arXiv 2606.11976, 10 Jun 2026, https://arxiv.org/abs/2606.11976
- **Contribution**: Compares linear sequential exploration with domain-scoped parallel agents (Haiku-class models) on SWE-bench Pro (ansible and an expanded 2025-26 set), plus an RLM baseline with a persistent REPL and a Codex CLI baseline.
- **Numbers**: domain-scoped parallel Haiku-class agents get the best micro-F1 among Haiku-class models and rank second behind Codex 5.5 High on the expanded benchmark; on the curated 2020 SWE-bench Pro set a Sonnet plain-LLM baseline attains higher micro-F1 by predicting few files; documentation co-evolution is unresolved by every approach; naive file-system access can lower localisation through test-file over-prediction; forced multi-agent consultation does not help and raises tokens substantially.
- **Admitted limitations / future work**: single repository focus (ansible) for the main study; persistent-session evaluation construction is new.
- **Relevance**: More tool access does not mean better localisation (over-prediction of test files), and structure of exploration matters more than tool inventory.

#### Harness design: An Empirical Study of Harness Design for Coding Agents
- **Ref**: Fan, Zhang et al. (UMass, Emory, Zoom), arXiv 2609.20804, 17 Sep 2026, https://arxiv.org/abs/2609.20804
- **Contribution**: Component-level ablation of planning, action space (predefined tools vs bash-only) and context management, 4 models x SWE-Bench Verified / Terminal-Bench, 176 settings, context budgets 32k / 64k / 96k / 128k.
- **Numbers**: Without context management, window-overflow failures hit 78.7% of SWE-Bench runs at 32k (8.7% at 128k); managed tiers vs none: +35.7 points at 32k, +15.9 at 64k, +5.5 at 96k, +2.7 at 128k. The "recall_event" tool that makes elided content recoverable is never called in 36 of 64 settings (56.3%), mean 0.540 calls per task at 32k and 0.007 at 128k, with no accuracy gain. Predefined tools help bash-weak models; bash-capable models do as well with bash-only at lower cost.
- **Admitted limitations / future work**: findings conditional on the models and budgets studied; a single harness loop; I did not extract the limitations section.
- **Relevance**: At a 32k window the dominant failure is context overflow; extra tools that models rarely call are measurable dead weight; the benefit of predefined tools depends on bash skill of the model.

## 5. Benchmarks and evaluation methodology

Setting of interest: Kaggle competition, ~120 hidden tasks from private repos, scored by full hidden test files; public LB over 58 tasks with ~1.5 task std between identical resubmissions; agents limited to ~6 min/task.

### 5.1. Private / held-out repos and public-to-private drop

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

### 5.2. Test adequacy, weak tests, over-strict tests, solution leakage

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

### 5.3. Fresh / multi-repo / multi-language benchmarks (generalisation to unseen repos)

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

### 5.4. Statistical methodology for evals

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

### 5.5. Gray literature (secondhand, flagged)
- OpenAI, "Why we no longer evaluate SWE-bench Verified" (23 Feb 2026): primary page returned HTTP 403 to me; via the-decoder.com article (read): at least 59.4% of an audited subset (27.6% of tasks that models often failed, per a search summary) have flawed tests rejecting correct solutions; GPT-5.2, Claude Opus 4.5 and Gemini 3 Flash Preview could reproduce some original fixes from memory; recommended SWE-bench Pro and is building non-public tests. 2610.22760 says OpenAI later withdrew the Pro recommendation (citing "OpenAI 2026b") after finding underspecified prompts and overly restrictive tests in Pro; I did not open that primary source.
- J. Gabor (LessWrong/Substack), "SWE-Bench Pro is even worse": audit of 100 random Pro tasks, categories: test leniency, overly strict tests (e.g. flipt tests expecting buggy behaviour), requirements inflation; the percentage was only in a chart I could not read. A commenter claims 15-24% of the full Pro set unsolvable; unverified.

## 6. Context management and compute budgets

### 6.1. Compaction strategies: masking vs summarization (SWE agents)

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

### 6.2. Budget awareness and overthinking

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

### 6.3. Learned memory and folding

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

### 6.4. 2026 evidence closest to the setting (tight windows, small models, time caps)

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

### 6.5. Wall-clock and time-budgeted agents

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

### 6.6. Token economics of coding agents

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

### 6.7. What compaction drops and what it costs (2026 empirical studies)

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

### 6.8. Budget awareness, early stopping, trajectory reduction, latency

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

### 6.9. Long-context degradation, thinking budgets, time-aware harnesses, memory

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

### 6.10. The system under study (documentation, not a paper)

#### ADK-Compaction: Google ADK "Compress agent context for performance" (documentation)
- **Ref**: Google ADK docs, https://adk.dev/context/compaction/ (accessed 2026-10-22)
- **Contribution**: Two strategies: sliding window (every `compaction_interval` new user invocations, with `overlap_size` preceding invocations) and token-based (`token_threshold` triggers "tail-retention compaction"; `event_retention_size` recent events stay raw "to preserve immediate context and pronoun resolution"). If both are set the token-based one takes precedence. Summariser prompt is customisable.
- **Numbers**: none; no evaluation published.
- **Admitted limitations / future work**: No limitations section. The page does not say what content types the summariser receives (the "text parts only; tool outputs and diffs dropped" fact in this project comes from the task description / code, not from this page). Kotlin variant cuts the window back so that no function call is summarised without its response.
- **Relevance**: Policy under test; its closest published analogues are OpenHands LLMSummarizingCondenser (keep_first + recent events) and the "T3 summary-only" tier of Harness-Design.

