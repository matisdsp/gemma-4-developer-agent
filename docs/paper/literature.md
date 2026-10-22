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

