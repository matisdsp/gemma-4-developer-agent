# Obeyed but Not Helped: A Pre-registered Factorial Screening of Eight Prompt Recipes for a 4B Coding Agent

## Abstract

Small coding agents are tuned with prompt recipes: run the tests, reproduce the bug first, check
that the code compiles, show an example. A single A/B comparison cannot tell whether such a recipe
works: on 40 tasks its 90% interval spans about ±9 points, wider than most claimed effects. We
screen eight recipes at once for Gemma 4 E4B in the official harness of the Gemma 4 Developer Agent
competition, with a pre-registered 2^(8-3) fractional factorial design: 32 configurations, 72
tasks, 2,304 attempts, each recipe measured on all of them. We also measure whether the agent
follows each rule. The agent resolves 11.7% of attempts. Six recipes have no effect beyond 3
points, with 90% intervals between -2.4 and +1.5 points; the other two, temperature 0.7 and a
compile check, are unresolved and lean negative. The agent often obeys: a rule that zero collected
tests verify nothing raises the share of its pytest calls that run a test from 59% to 74%, and
imposed verification raises checks after the edit from 78% to 93%, with no gain in resolved
attempts. The task explains 58% of the outcome variance; the eight recipes together, 0.2%.

## 1. Introduction

Agents that run on one local GPU use small models, and small models are steered with words. Public
recipes for coding agents are lists of instructions: reproduce the issue before editing, run the
closest test file, never submit without checking, compile after each edit. Each recipe is cheap to
add and plausible, and each is usually justified by a single comparison.

Single comparisons cannot carry that weight. Outcomes are binary per task, and the same agent
resubmitted draws different tasks: in this competition, byte-identical bundles scored 0.18 and
0.13 on the public leaderboard, and identical files differed by up to six of 58 tasks. In our own
simulation from per-task success rates of the same model, a paired comparison of two prompts on 40
tasks has a 90% interval of ±8.6 points. Two consequences follow. Teams report that most
interventions are indistinguishable from noise, and studies that do reach significance test whole
bundles: a minimal against a maximal scaffold moved E4B from 10.0% to 15.4% in one entry, without
saying which component did it.

We screen eight recipes in one experiment. A fractional factorial design varies all of them at
once, so that every attempt informs every recipe, and the comparison for each recipe uses 1,152
attempts on each side, paired within tasks. With the budget of a large A/B test, each recipe gets
an interval of about ±1.5 points. Because a recipe that is ignored and a recipe that is followed
but useless call for different responses, we also measure, from the traces, whether the agent
obeys each rule. The design, the analysis script and the reading of results were frozen and
hashed before the first attempt.

The contributions are:

- a pre-registered screening of eight recipes for a 4B coding agent, in which none moves the
  resolved rate by more than 3 points;
- a separation of obedience from effect: three rules are followed far more often when given,
  and none of them changes the outcome;
- a measure of where the variance lies: 58% with the task, 0.7% with the 32 configurations, and
  44 of 72 tasks never resolved by any configuration;
- a reusable design and analysis for screening harness changes at the cost of one comparison.

## 2. Setting

**Harness.** The Gemma 4 Developer Agent competition scores declarative agents: YAML files,
prompts and optional adapters, compiled by the organisers into a Google ADK agent that runs one
Gemma 4 model behind vLLM. The agent receives a GitHub issue and a repository, works through tools
(`run_command`, `read_file`, `edit_file`, `write_file`, `get_status`, `submit_patch`), and is scored
SWE-bench style: hidden tests must pass on its patch.

**Model.** Gemma 4 E4B, the smallest model eligible for the competition's small-model prize, in
the quantised checkpoint used by the scorer (W4A16).

**Tasks.** Of the 129 public tasks, 75 pass with their reference patch in the harness's subprocess
sandbox. We ran a control in which the patch adds an unrelated file: three tasks pass their hidden
tests with it and were excluded, as they cannot discriminate. The remaining 72 tasks come from
fastapi (29) and rich (43).

**Stack.** All attempts ran in private Kaggle kernels on 4×L4 GPUs with the scorer's vLLM
settings (tensor parallel 4, bfloat16, the gemma4 tool and reasoning parsers, 32k context), the
official harness, and eight attempts in flight. Each attempt had 36 tool calls and 10 minutes. The
scorer runs tasks one at a time at 7 to 8 minutes; eight concurrent attempts slow decoding from 8.6
to 11.4 ms per token, and the longer cap compensates. In the pilot, 1 of 96 attempts reached it.

## 3. Recipes, design and analysis

**Recipes.** Each recipe has two levels (Table 1). Six are instructions in the system prompt; two
are sampling settings. Each comes from a published claim or from our earlier traces of the same
agent.

| | Recipe | Off | On | Source of the claim |
|---|---|---|---|---|
| A | Temperature 0.7 | 0.2 | 0.7 | 0.2 is the default of public top bundles; more diversity |
| B | Thinking budget 256 | 4,096 tokens | 256 tokens | a public 31B bundle at 0.20 used 256 |
| C | Spec first | absent | list names, messages, edge cases before acting | specification beats feedback (BRA) |
| D | Reproduce first | absent | a script in /tmp that must fail before the edit | contested (ECLoop vs SWE-Doctor) |
| E | Imposed verification | verify in at most 2-3 calls | no submission before a check; spend the budget checking | E4B stops early (Toeda) |
| F | Useful test | `-k` and `tail` advised; pre-existing failures may be ignored | run the whole test file; zero tests is not a check | 24-45% of earlier E4B pytest calls ran no test |
| G | Compile check | absent | `python -m py_compile` after every edit | 9-16% of earlier E4B attempts left syntax errors; linting on edit in SWE-agent |
| H | Worked example | absent | one session on a made-up project | small agents act on what they are shown |

*Table 1. The eight recipes.*

**Design.** A 2^(8-3) fractional factorial of resolution IV: recipes A to E are crossed in full,
and F = ABC, G = ABD, H = -ACDE. Each recipe is on in 16 of the 32 configurations, recipes are
orthogonal, and no main effect is aliased with a two-way interaction. The two-way interactions of
E and H with every other recipe are free of aliasing (13 of 28); the remaining ones are aliased in
pairs or triples and are not interpreted. Prompts are assembled so that an inactive recipe leaves
no trace, and the worked example shows only the steps of active recipes. Each configuration ran
once on each task: 2,304 attempts, in three kernels of 24 tasks stratified by repository, in a
seeded random order.

**Pre-registration.** The hypotheses, reading rules, predictions, run files and analysis script
were committed with their SHA-256 before any attempt. A pilot of 96 attempts on three tasks, run
beforehand and excluded, checked the infrastructure and the compliance measures with comparisons
of resolved tasks hidden; it led to one change, a better measure of obedience to spec first.

**Analysis.** For each recipe and task, the effect is the mean outcome of attempts with the
recipe on minus the mean with it off; the reported effect is the mean over tasks. Intervals are
90% task bootstraps (2,000 resamples); p values come from flipping the sign of task differences
(10,000 permutations) and are Holm-adjusted over the eight primary tests. The pre-registered
reading: a recipe **helps** or **hurts** if its interval excludes zero and its Holm p is below
0.05; it has **no effect beyond 3 points** if its interval lies within (-3, +3); otherwise it is
**unresolved**. Three points is a fifth of the expected base rate, and about two tasks of 58 on
the leaderboard.

**Obedience.** Measured from the tool calls in each trace: whether a reproduction script ran
before the first edit; whether a test or script ran after it; the share of pytest calls whose
summary reports at least one test run; whether `py_compile` ran after an edit; and, for spec
first, whether the first message names at least three identifiers of the issue and runs to 600
characters. These are pattern-based measures.

## 4. Results

**Overall.** E4B resolved 11.7% of attempts (fastapi 16.5%, rich 8.5%), and 28 of the 72 tasks at
least once. 92% of attempts left a non-empty patch. Attempts took 192 seconds and 15.3 tool calls
on average; 48 reached the time cap and 45 the tool-call cap. No attempt was lost to
infrastructure.

**No recipe helps.** Six recipes have no effect beyond 3 points (Figure 1, right; Table 2). Two
are unresolved: temperature 0.7, whose interval reaches -3.1, and the compile check, whose
interval excludes zero (-3.2 to -0.6 points; p = 0.023) but whose Holm-adjusted p is 0.18. No
estimate is positive.

| Recipe | Effect (points) | 90% interval | Holm p | Reading |
|---|---|---|---|---|
| Reproduce first | -0.2 | [-1.7, +1.4] | 1.00 | no effect beyond 3 points |
| Imposed verification | -0.2 | [-1.5, +1.3] | 1.00 | no effect beyond 3 points |
| Worked example | -0.2 | [-1.9, +1.5] | 1.00 | no effect beyond 3 points |
| Thinking budget 256 | -0.5 | [-1.6, +0.5] | 1.00 | no effect beyond 3 points |
| Spec first | -0.5 | [-2.3, +1.2] | 1.00 | no effect beyond 3 points |
| Useful test | -0.9 | [-2.3, +0.5] | 1.00 | no effect beyond 3 points |
| Temperature 0.7 | -1.6 | [-3.1, +0.1] | 1.00 | unresolved |
| Compile check | -1.9 | [-3.2, -0.6] | 0.18 | unresolved |

*Table 2. Effect of each recipe on resolved attempts, pre-registered analysis.*

![Figure 1](figures/fig1_obeyed_helped.png)

*Figure 1. Left: share of attempts that follow each rule, with the rule off and on. Right: effect
of each recipe on resolved attempts, with 90% task-bootstrap intervals; the band marks ±3 points.*

**The agent often obeys.** Three rules change behaviour substantially (Figure 1, left). Under the
useful-test rule, the share of pytest calls that run at least one test rises from 59% to 74%,
the last check is a real test 21 points more often, and an empty last check 12 points less often.
Imposed verification raises checks after the edit from 78% to 93% and adds two tool calls after
the edit. The compile check is followed in 15% of attempts that receive it. Two rules are nearly
ignored: a reproduction script runs before the edit in 2.5% of attempts told to write one, and
spec first barely moves our measure (29% to 33%). The worked example raises obedience to other
rules: 13 points more pytest calls run a test, and 6 points more attempts compile after editing.
None of these changes in behaviour shows up in the resolved rate.

**Costs.** Recipes that make the agent check more cost time: imposed verification adds 22 seconds
per attempt (90% interval 14 to 31), the worked example 17, the useful test 14. The thinking budget
of 256 tokens cuts 79 completion tokens per call and saves 16 seconds per attempt (7 to 25), about
8% of the mean, with no measurable loss; it leaves an empty patch 3.4 points more often. One
secondary contrast was unexpected: the useful-test rule raises syntax-broken final patches by 3.3
points (1.4 to 5.4), one of 24 secondary contrasts and unadjusted.

**Predictions.** We registered eight predictions. Three were right: reproduce first, spec first
and the thinking budget have no effect beyond 3 points, and the thinking budget saves time. Three
were wrong: we expected the useful test and the worked example to help, and imposed verification
to help or remain unresolved. For temperature (predicted to hurt) and the compile check (predicted
unresolved or helpful), the estimates lean negative and remain unresolved.

**Exploratory: where the variance lies.** No clear two-way interaction reaches significance; the
largest, compile check by worked example, is -1.6 points (-2.8 to -0.4; p = 0.052, one of 13). The
task explains 58.5% of the variance of attempt outcomes; the 32 configurations, 0.7%; the main
effects of the eight recipes, 0.2%. The standard deviation of the 32 configuration means, 2.7
points, is below the 3.8 points that sampling alone would produce if configurations did not
matter. Figure 2 shows why: 44 tasks are never resolved by any configuration, one is always
resolved, and 27 fall in between.

![Figure 2](figures/fig2_task_spread.png)

*Figure 2. Number of tasks by how many of the 32 configurations resolve them.*

## 5. Discussion

**Obedience is not competence.** The recipes do what they say: the agent runs real tests, checks
after editing and, shown an example, follows the rules more often. What changes is the process,
not the result. For a model of this size, the instruction-following channel works, and the
competence it would need to turn better checks into better patches is not there. A test that
fails tells the agent that its patch is wrong, not how to fix it.

**The task decides first.** Most of the outcome is fixed before any recipe applies. Forty-four
tasks are beyond the model in every configuration, and on the others the configuration explains
less than sampling noise. A recipe could still matter for a few tasks in the middle band, but its
average effect over realistic task sets is bounded by this structure: with 27 tasks that are ever
solved, a recipe would need to flip a large share of them to move the average by 3 points.

**Verification is not yet the bottleneck at this size.** Recent accounts place the bottleneck of
coding agents in verification rather than generation. For strong models with near-perfect test
oracles that may hold. For a 4B model, the result here is consistent with the reverse: making the
agent verify more, and more truthfully, did not help, which suggests that generation is the
binding constraint. We did not test a perfect verifier, so this remains an interpretation.

**Practical advice.** For small agents, prompt tuning is unlikely to repay the effort; model size
or training are the levers. One recipe is free: a thinking budget of 256 tokens saves about 8% of
the time per attempt without measurable loss, which matters under a global time limit. A rule
should be judged on two outcomes, whether it is obeyed and whether it helps, because "no effect"
means something different in each case. And a fractional factorial screen costs the same as one
well-powered comparison while measuring many changes at once; the design and scripts are reusable
for any agent and harness.

## 6. Threats to validity

**Tasks.** All 72 tasks were used in our earlier work, and the useful-test and compile-check
recipes came from reading traces on them. A recipe suggested by these tasks still failed on them,
which makes overfitting an unlikely explanation of a null, but the tasks come from two
repositories only, and the competition's hidden tasks come from private ones.

**One model.** Results concern Gemma 4 E4B. A larger model may turn the same behaviours into
better patches; one entry reports that a maximal scaffold helped E4B but not 12B or 26B, so
effects need not grow with size either.

**Levels and measures.** Each recipe was tested at one wording and one level (temperature 0.7, not
1.0; 256 thinking tokens, not none). Obedience measures are pattern-based; the one for spec first
is weak, so "ignored" is less certain for that recipe.

**Budget and concurrency.** The 10-minute cap with eight concurrent attempts differs from the
scorer's sequential runs. Few attempts reached the cap (2%), but time-hungry recipes could behave
differently under a tighter one.

**Averages.** The primary test is an average over tasks. A recipe could help some tasks and hurt
others in ways that cancel; the configuration spread, below sampling noise, makes large opposing
effects unlikely but does not exclude small ones.

## 7. Related work

**Evaluation noise.** A repeated-run study attributes 53% of outcome variance to the issue, 42% to
the run and 4.6% to the model-issue interaction [1]; harness choice alone moves a lightweight
model by up to 44 points, measured with one attempt per pairing [2]. A position paper calls for
factorial protocols that report variance components [3]. We apply such a protocol inside one
harness.

**Prompt and scaffold studies.** Instruction files and context files show small or no effects for
frontier agents [4, 5]. In this competition, a minimal against maximal scaffold comparison helped
only E4B [6], a pre-registered study found a prompt rule followed 20 times out of 20 by a 31B model
with no gain in solved tasks [7], and a calibrated noise study found twenty interventions
indistinguishable from noise for a 31B agent [8]. We separate eight components at once, for the
smallest model, with intervals tight enough to bound their effects.

**What helps repair.** Specification information is worth more than test feedback for repairing
failed states [9]. Delaying edits until evidence is gathered helps [10], while naive reproduction
tests mislead [11]. Linting on edit helped frontier models in SWE-agent [12]. Verification is
increasingly described as the hard part of agentic coding [13]. Our results add a small-model data
point in which more and truer verification did not translate into success.

## Reproducibility

Run files, prompts for all 32 configurations, the analysis script and the pre-registration with
SHA-256 hashes are in the repository [link to the public copy]. The public tasks are not
redistributed; results are reported as aggregates, and per-attempt records can be regenerated
from the competition data. All runs used the free Kaggle GPU quota.

## Use of AI tools

[Statement to be written by the author, for example: experiments and analysis code were written
with an AI coding assistant; the text was drafted with an AI assistant and revised by the author.]

## References

1. Hard Issue, Weak Model, or Bad Run? arXiv:2611.08285.
2. Pairing Matters: Performance, Failures, and Efficiency in Lightweight Coding Agents. arXiv:2610.32131.
3. Position paper on agent harnesses and factorial evaluation protocols. arXiv:2605.23950.
4. Instruction Adherence in Coding Agent Configuration Files: A Factorial Study of Four File-Structure Variables. arXiv:2605.10039.
5. Do Context Files Help Coding Agents? A Two-Agent Ablation Study on Real Repositories. arXiv:2607.27250.
6. T. Toeda. Scaffolding Helps the Smallest Gemma 4 Agent, Not the Larger Ones. Zenodo, doi:10.5281/zenodo.23813680, 2026.
7. kb2326. Ask or Enforce? Pre-registered test of prompt rules vs agent structure for Gemma 4 31B. GitHub, 2026.
8. fjcarmona78. Most Agent Improvements Are Noise: A Calibrated Study of a Gemma 4 31B Coding Agent. GitHub, 2026.
9. Where Should a Stuck Agent Spend Its Next Tokens? Causal Attribution of Inference-Time Resources (BRA). arXiv:2610.28834.
10. ECLoop. arXiv:2607.28815.
11. SWE-Doctor. arXiv:2607.00990.
12. J. Yang et al. SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering. arXiv:2405.15793.
13. The Verification Horizon. arXiv:2606.26300.
