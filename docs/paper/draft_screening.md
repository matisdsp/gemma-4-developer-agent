# Eight Recipes Did Not Help a 4B Coding Agent, Even When It Followed Them: A Pre-registered Factorial Screening

## Abstract

Small coding agents are tuned with prompt recipes: run the tests, reproduce the bug first, compile
after each edit, show an example. A paired A/B comparison on 40 tasks has a 90% interval of about
±7.6 points, too wide to judge such recipes one at a time. We screened eight recipes at once for
Gemma 4 E4B in the harness of the Gemma 4 Developer Agent competition, with a pre-registered
2^(8-3) fractional factorial design: 32 configurations on 72 tasks, 2,304 attempts. The agent
resolved 11.7% of attempts. No recipe raised that rate: every upper 90% bound is at most +1.5
points, six recipes are bounded within ±3 points, and two (temperature 0.7, a compile check) lean
negative but remain unresolved. Behaviour did change: told to run whole test files, the agent ran a
test in 74% of its pytest calls, up from 59%, and imposed verification raised the attempts that
check after the edit from 78% to 93%. The best of the 32 configurations led the base prompt by 8
points; in a registered replication on 576 fresh attempts, by 1.4 (-1.4 to +4.2). Exploratory: 81%
of attempts whose last test run passed still failed the hidden tests, against 92% of the others.

## 1. Introduction

Agents that run on local GPUs use small models, steered with words: reproduce the issue before
editing, run the closest test file, never submit without checking. Each recipe is cheap to add,
plausible, and usually justified by a single comparison.

Single comparisons cannot carry that weight. Runs of the same agent on the same tasks differ:
byte-identical submissions scored 0.18 and 0.13 on the public leaderboard [5]. At the task rates of
this study, a paired comparison on 40 tasks, one attempt per arm, has a 90% interval of ±7.6
points. One team found twenty interventions that moved nothing beyond noise [5], and the
significant results compare whole scaffolds: a maximal against a minimal scaffold raised E4B from
10.0% to 15.4% [3], without saying which component did it.

We screen eight recipes in one experiment. A fractional factorial design varies all of them at
once, so every attempt informs every recipe: each comparison uses 1,152 attempts per side, paired
within tasks, with an interval of about ±1.5 points. An ignored rule and a followed but useless
rule call for different responses, so we also measure from the traces whether the agent obeys each
rule.

We contribute a pre-registered screening in which no recipe raises the resolved rate, a separation
of obedience from effect, a registered replication of the one configuration that stood out, an
exploratory analysis (a passing test run is weak evidence; the task explains 58.5% of the
variance), and a reusable screening design.

## 2. Setting

**Harness and model.** The competition compiles declarative agents into a Google ADK agent running
one Gemma 4 model behind vLLM. Given a GitHub issue and a repository, the agent works through six
tools and is scored SWE-bench style: hidden tests must pass on its patch. We use Gemma 4 E4B, the
second smallest eligible model, in the scorer's 4-bit checkpoint.

**Base prompt.** All configurations share a structured system prompt of about 840 words: hard
limits (36 tool calls, 10 minutes, no edits to tests), a call plan, a procedure (locate, edit,
verify, submit) and decision rules. Recipes add to it or change parts of it.

**Tasks.** Of the 129 public tasks, 75 pass with their reference patch in the harness's subprocess
sandbox. Three of them still pass their hidden tests when the patch only adds an unrelated file,
and were excluded. The remaining 72 come from fastapi (29) and rich (43).

**Stack.** All attempts ran in private Kaggle kernels on 4×L4 GPUs with the scorer's vLLM settings,
the official harness, and eight attempts in flight. The scorer runs tasks one at a time. Since
decoding slowed from 8.6 to 11.4 ms per token at eight concurrent requests in a benchmark, we set
the time cap to 10 minutes instead of our usual 7, without measuring whether this compensates.

## 3. Recipes, design and analysis

**Recipes.** Each recipe has two levels (Table 1). Six are prompt changes and two are sampling
settings; each comes from a published claim or from our earlier runs.

| | Recipe | Off | On | Source |
|---|---|---|---|---|
| A | Temperature 0.7 | 0.2 | 0.7 | 0.2 in earlier runs and public submissions |
| B | Thinking budget 256 | 4,096 tokens | 256 tokens | a public 31B submission scoring 0.20 used 256 [12] |
| C | Spec first | - | list names, messages, edge cases before acting | specification beats test feedback [6] |
| D | Reproduce first | - | a script in /tmp that must fail before the edit | evidence first helps [7]; reproduction tests can mislead [8] |
| E | Imposed verification | verify in at most 2-3 calls | no submission before a check; spend the budget checking | E4B stops early [3] |
| F | Useful test | add `-k`; failures from missing fixtures may be ignored | run the whole test file; zero tests is not a check; no such excuse | 24-45% of E4B pytest calls ran no test in four earlier runs |
| G | Compile check | - | `python -m py_compile` after every edit | 9-16% of attempts had syntax errors in the same runs; linting on edit [9] |
| H | Worked example | - | one session on a made-up project | an agent acts on information it is shown, not on instructions [11] |

*Table 1. The eight recipes. Both levels of F pipe test output through `tail -40`. Earlier runs (F,
G): another stack, not in the released records.*

**Design.** A 2^(8-3) fractional factorial of resolution IV: recipes A to E are crossed in full,
and F = ABC, G = ABD, H = -ACDE. Each recipe is on in 16 of the 32 configurations, and no main
effect is aliased with a two-way interaction. The two-way interactions of E and H with every other
recipe are unaliased (13 of 28 pairs); the others are not interpreted. When off, recipes C, D, G
and H leave no trace in the prompt; the worked example shows only active recipes. Each
configuration ran once on each task, in three kernels of 24 tasks stratified by repository, in a
seeded random order.

**Pre-registration.** Hypotheses, reading rules, predictions, run files and the analysis script
were committed with their SHA-256 before the main run. An excluded pilot of 96 attempts checked the
infrastructure and the obedience measures, with resolved comparisons hidden; it changed one measure
before the freeze, and the predictions were written after its obedience output. There was no
deviation. An addendum, written after the main results and frozen before its run, registers the
replication of Section 4; analyses beyond the registration (`explore.py`, `controls.py`) are
exploratory.

**Analysis.** For each recipe and task, the effect is the mean outcome with the recipe on minus the
mean with it off; the reported effect is the mean over tasks. Intervals are 90% task bootstraps
(2,000 resamples); p values come from sign flips of task differences (10,000 permutations) and are
Holm-adjusted over the eight primary tests. Reading rules: a recipe **helps** or **hurts** if its
interval excludes zero and its Holm p is below 0.05; it has **no effect beyond 3 points** if its
interval lies within (-3, +3); otherwise it is **unresolved**. Three points is 1.7 of the
leaderboard's 58 tasks.

**Obedience.** Pattern-based measures from the tool calls of each trace: a reproduction script run
before the first edit; a test or script run after it; the share of pytest calls whose summary
reports a test passed, failed or in error; `py_compile` run after an edit; and, for spec first, a
first message of 600 characters or more that names three identifiers of the issue.

## 4. Results

**Overall.** E4B resolved 11.7% of attempts and 28 of the 72 tasks at least once. Attempts took 192
seconds and 15.3 tool calls on average; 50 ran the full 10 minutes and the harness stopped 45 at
the tool-call cap. No attempt was lost to infrastructure, and identical patches always received the
same verdict.

**No recipe helps.** Six recipes have no effect beyond 3 points (Table 2, Figure 1). Two are
unresolved: temperature 0.7, whose interval reaches -3.1, and the compile check, whose interval
excludes zero (p = 0.023) but whose Holm-adjusted p is 0.18. No estimate is positive, and no upper
bound exceeds +1.5 points.

| Recipe | Effect (points) | 90% interval | Holm p | Reading |
|---|---|---|---|---|
| Reproduce first | -0.2 | [-1.7, +1.4] | 1.00 | within ±3 |
| Imposed verification | -0.2 | [-1.5, +1.3] | 1.00 | within ±3 |
| Worked example | -0.2 | [-1.9, +1.5] | 1.00 | within ±3 |
| Thinking budget 256 | -0.5 | [-1.6, +0.5] | 1.00 | within ±3 |
| Spec first | -0.5 | [-2.3, +1.2] | 1.00 | within ±3 |
| Useful test | -0.9 | [-2.3, +0.5] | 1.00 | within ±3 |
| Temperature 0.7 | -1.6 | [-3.1, +0.1] | 1.00 | unresolved |
| Compile check | -1.9 | [-3.2, -0.6] | 0.18 | unresolved |

*Table 2. Effect of each recipe on resolved attempts, pre-registered analysis. Within ±3: no effect
beyond 3 points.*

![Figure 1](figures/fig1_obeyed_helped.png)

*Figure 1. Left: obedience with the rule off and on (useful test: share of pytest calls). Right:
effect on resolved attempts with 90% intervals; the band marks ±3 points.*

**Obedience.** Two rules change behaviour strongly. Under the useful-test rule, the share of pytest
calls that run a test rises from 59% to 74% (48% to 62% by a stricter, exploratory count), and the
last pytest call runs tests 21 points more often. Imposed verification raises the attempts that
check after the edit from 78% to 93% and adds two tool calls. The compile check is followed in 15%
of the attempts given it. A reproduction script runs before the edit in 2.5% of attempts told to
write one; 37% run one at some point, mostly after editing. Spec first barely moves its measure
(29% to 33%). None of these changes moves the resolved rate.

**Costs and secondary outcomes.** Checking costs time: imposed verification adds 22 seconds per
attempt (90% interval 14 to 31). The thinking budget of 256 saves 16 seconds (7 to 25) but leaves
an empty patch 3.4 points more often. The compile check did not reduce syntax-broken patches (+1.6;
-0.4 to +3.6); `reproduce.py` prints the other registered secondary outcomes.

**Predictions.** Four of eight registered predictions held. Among the failures, the useful test and
the worked example had been expected to help.

**Exploratory: the worked example.** The example shows a test file run and passing. It raised the
share of pytest calls that run a test from 50% to 67% without the useful-test rule and from 68% to
79% with it, and compile obedience from 9% to 21% among attempts told to compile: on these two
measures, the demonstration moves the agent about as much as the rule does.

**Exploratory: passing checks.** 855 attempts ended on a passing test run, and 81% of them failed
the hidden tests, against 92% of the others (within tasks, +6.2 points for a passing run; 2.9 to
9.9). The useful-test rule raised passing last runs from 28% to 46% of attempts, while the resolved
rate went from 12.2% to 11.3%.

**Exploratory: where the variance lies.** None of the 13 two-way interactions has p < 0.05
(smallest 0.052, compile check by worked example). The task explains 58.5% of the variance of
attempt outcomes. The standard deviation of configuration means is 2.7 points, inside the central
90% (1.9 to 2.9) that chance alone produces with these tasks. Forty-four tasks are never resolved,
one always, and 27 sometimes (Figure 2).

![Figure 2](figures/fig2_task_spread.png)

*Figure 2. Tasks by number of configurations that resolve them.*

**Replication of the best configuration.** Configuration `s04` (spec first, useful test, worked
example) resolved 15 of 72 tasks, against 9 for the base prompt (`reproduce.py` lists the 32
configurations, from 6.9% to 20.8%); if configurations changed nothing (task rates fixed as
observed), the best of 32 would reach 15 or more in 1.6% of simulations. The addendum registered
four fresh attempts per task for both, 576 attempts. `s04` resolved 12.2% and the base prompt
10.8%: +1.4 points (-1.4 to +4.2; p = 0.56), unresolved by the registered rule. The 8-point lead
did not hold; a gain up to 4 points is not excluded. `s04` ended on a passing test run in 53% of
attempts against 21% and took 37 seconds longer.

## 5. Discussion

**The process changed, the outcome did not.** Two rules worked as instructions: more executed
tests, more checks after editing, more passing test runs. A likely reason, untested: the rules send
the agent to existing test files, which wrong patches also pass, while the hidden tests encode the
behaviour the issue asks for. A passing run is weak evidence.

**Ignored rules could be enforced.** Reproducing before editing (2.5%) and compiling (15%) were
mostly ignored. A harness can enforce such steps rather than ask for them: linting on every edit
[9], an execution layer that postpones edits until evidence is gathered [7], or structure instead
of prompt rules [4]. We did not test enforcement.

**Most of the outcome is set by the task.** Forty-four tasks were never resolved in 32 attempts,
and the configuration spread is within chance. Recipes act, if at all, on the 27 tasks that are
sometimes solved: raising the average by 3 points would require about 8 points more success on each
of them.

**Practical advice.** On top of a structured base prompt, these recipes are not worth tuning for
E4B. Judge a rule on whether it is obeyed and whether it helps: "no effect" means something
different in each case. Rerun the best of many configurations before believing it. A fractional
factorial screen costs one well-powered comparison and transfers to other agents.

## 6. Threats to validity

**Scope.** Effects are measured for E4B on top of a long structured prompt. On a minimal prompt the
recipes could matter more, and a larger model might turn the same behaviours into better patches,
though a full scaffold helped E4B but not 12B or 26B [3].

**Tasks.** All 72 tasks were used in earlier work, and two recipes (useful test, compile check)
came from traces on them, yet failed on them. The tasks come from two repositories; the hidden
tasks come from private ones. 12.6% of fastapi pytest calls stop on a module missing from the
sandbox, which hampers checking there.

**Levels and measures.** Each recipe was tested at one wording and one level. Obedience measures
are pattern-based; the one for spec first is weak, so its low obedience is less certain.

**Budget.** The 10-minute cap with eight concurrent attempts differs from the scorer's sequential
runs; 2% of attempts hit it. Tool calls are synchronous in the runner: a slow command stalls the
seven other attempts, so durations and time-cap stops are overstated. Attempts ran in random order,
which spreads the stalls over configurations.

**Averages.** Each effect is averaged over tasks and over the other seven recipes: a recipe could
help some tasks and hurt others, and one that helps only alone would be missed, since no
configuration has exactly one recipe on. All eight estimates are negative; their sum is -5.9 points
(-10.6 to -1.6; post hoc).

## 7. Related work

**Evaluation noise.** A repeated-run study attributes 53% of outcome variance to the issue, 42% to
the run and 4.6% to the model-issue interaction [1]. We apply a factorial protocol inside one
harness.

**Prompt and scaffold studies.** For frontier agents, instruction-file structure barely changes
adherence [2]. In this competition, a full scaffold helped only E4B [3] and a 31B agent followed a
prompt rule 20 times out of 20 with no gain [4]. We separate eight components at once.

**What helps repair.** Specification information, there drawn from the reference patch, is worth
more than test feedback for repairing failed states [6]. Delaying edits until evidence is gathered
helps [7], generated reproduction tests can mislead [8], and linting on edit helped GPT-4 Turbo
[9]. One study argues that, for today's coding agents, verifying solutions has become harder than
generating them [10]. We add a small-model case in which more checking against existing tests did
not bring success.

## Reproducibility

Run files, the 32 prompts, the scripts, the pre-registration and its addendum, with SHA-256 hashes,
are at https://github.com/matisdsp/gemma-4-developer-agent. The pre-registration commit (97bbbf5)
is dated before the main run, but the date is self-declared: the repository became public
afterwards. The addendum has an OpenTimestamps receipt anchored before its run ended. Records per
attempt (no task text) and CPU scripts reproduce every number of Sections 4 to 6. The main run and
the replication took about 21 hours of 4×L4 time on the free Kaggle quota.

## Use of AI tools

The author was assisted by AI tools for writing the code and the text of this report.

## References

1. X. Shi et al. Hard Issue, Weak Model, or Bad Run? Rethinking Failure Prediction for Coding Agents. arXiv:2611.08285, 2026.
2. D. McMillan. Instruction Adherence in Coding Agent Configuration Files: A Factorial Study of Four File-Structure Variables. arXiv:2605.10039, 2026.
3. T. Toeda. Scaffolding Helps the Smallest Gemma 4 Agent, Not the Larger Ones. Zenodo, doi:10.5281/zenodo.23813680, 2026.
4. kb2326. Ask or Enforce? Pre-registered test of prompt rules vs agent structure for Gemma 4 31B under a fixed budget. https://github.com/kb2326/gemma4-ask-or-enforce, 2026.
5. fjcarmona78. Most Agent Improvements Are Noise: A Calibrated Study of a Gemma 4 31B Coding Agent. https://github.com/fjcarmona78/gemma4-agent-noise-study, 2026.
6. S. Lyu et al. Where Should a Stuck Agent Spend Its Next Tokens? Causal Attribution of Inference-Time Resources. arXiv:2610.28834, 2026.
7. Y. Xu et al. Preventing Premature Commitment in Coding Agents with an Evidence-Conditioned Execution Layer. arXiv:2607.28815, 2026.
8. Y. Guo et al. SWE-Doctor: Guiding Software Engineering Agents with Runtime Diagnosis from Multi-Faceted Bug Reproduction Tests. arXiv:2607.00990, 2026.
9. J. Yang et al. SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering. arXiv:2405.15793, 2024.
10. B. Wang et al. The Verification Horizon: No Silver Bullet for Coding Agent Rewards. arXiv:2606.26300, 2026.
11. lspecian. gemma4-moving-failures. https://github.com/lspecian/gemma4-moving-failures, 2026.
12. XingLing. Same 8 minutes, scores from 0.05 to 0.20. Kaggle notebook, https://www.kaggle.com/code/xingling666/same-8-minutes-scores-from-0-05-to-0-20, 2026.
