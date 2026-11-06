"""Generate the E4B screening design: eight recipes crossed in 32 configurations.

    uv run python scripts/make_screening.py            # writes variants/screening/s00..s31

The design is a 2^(8-3) fractional factorial of resolution IV: A to E are crossed in full, and
F = ABC, G = ABD, H = -ACDE. Every recipe is on in 16 configurations and off in 16, recipes are
mutually orthogonal, and no main effect is aliased with a two-way interaction. The two recipes
with the most interesting interactions sit on E and H, whose two-way interactions are all clear.
The sign of H puts the configuration with every recipe off inside the fraction.

Prompt text is assembled so that a recipe that is off leaves no trace: no mention of a step that
does not exist, no `-k` under the useful-test recipe, and a worked example that only shows what
the active recipes ask for.
"""

import argparse
import itertools
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "variants" / "screening"

MODEL = "gemma-4-e4b-it-qat-w4a16-ct"
TOOL_CALLS = 36
MINUTES = 10  # 7 on an idle GPU; eight concurrent attempts cost about 1.5x per token on one L4

RECIPES = {
    "A": "temperature_0.7",
    "B": "thinking_256",
    "C": "spec_first",
    "D": "reproduce_first",
    "E": "imposed_verification",
    "F": "useful_test",
    "G": "compile_check",
    "H": "worked_example",
}


def design() -> list[dict[str, bool]]:
    """The 32 configurations, in the standard order of the base factors A to E."""
    runs = []
    for a, b, c, d, e in itertools.product((-1, 1), repeat=5):
        levels = {"A": a, "B": b, "C": c, "D": d, "E": e,
                  "F": a * b * c, "G": a * b * d, "H": -a * c * d * e}
        runs.append({k: v == 1 for k, v in levels.items()})
    return runs


def section(*lines: str) -> str:
    return "\n".join(line for line in lines if line)


def hard_limits(useful_test: bool) -> str:
    test_rule = (
        "Always name one real test file, run it whole, and pipe through `tail -40`."
        if useful_test else
        "Always name one test file, add `-k` when you can, and pipe through `tail -40`.")
    return section(
        "# HARD LIMITS",
        f"- {TOOL_CALLS} tool calls and {MINUTES} minutes in total. When either runs out, the "
        "working tree is graded as it is. An edit that exists counts even if you never call "
        "`submit_patch`. An unedited tree always scores zero.",
        "- Never create, modify or delete test files (`test_*.py`, `*_test.py`, anything under "
        "`tests/`), `pytest.ini`, `conftest.py`, `pyproject.toml`, `setup.cfg`. Such changes are "
        "discarded by the grader.",
        "- Scratch files go in /tmp only (write them with run_command). Any file left under "
        "/workspace becomes part of the graded patch.",
        f"- Never run a full test suite (bare `pytest`, `pytest .`, `unittest discover`). {test_rule}",
        "- Never look outside /workspace. All dependencies are already installed; there is no "
        "network.",
        "- Never run the same command twice. Never repeat a failed edit unchanged.",
    )


def call_plan(imposed: bool, reproduce: bool) -> str:
    read = "locate, read and reproduce the problem (step 2b)" if reproduce else "locate and read"
    if imposed:
        checks = ("your reproduction script and the closest existing test file have both been run"
                  if reproduce else "the closest existing test file has been run")
        lines = [
            ("- You have far more budget than a first fix needs. Spend it on checking, not on "
             "early submission."),
            (f"- Calls 1-10: {read}. Calls 11-15: edit. You MUST have edited a source file by "
             "call 15."),
            "- Calls 16-30: verify, correct and verify again.",
            "- From call 30: no new exploration. Check, fix, submit.",
            f"- Never call `submit_patch` before {checks} against your edit.",
        ]
    else:
        lines = [
            (f"- Calls 1-11: {read}. Calls 12-15: edit. You MUST have edited a source file by "
             "call 15. If unsure, make your best-guess edit in the most likely place now; a "
             "wrong edit can be corrected, pure reading cannot score."),
            "- Calls 16-26: verify and correct.",
            "- From call 27: no new exploration. Check, fix, submit.",
        ]
    return section(
        "# CALL PLAN", *lines,
        "- Always finish with `git status --short && git diff` and then `submit_patch`.")


SPEC_STEP = section(
    "## 1. Extract the specification (no tool call)",
    "From the issue, note: the exact module, function, class, option or CLI name; the exact "
    "error message and exception type; the expected return value or output; the inputs that "
    "trigger the bug; every edge case mentioned (None, empty, negative, unicode, duplicates, "
    "defaults). Every concrete string and name in the issue is a literal that must appear "
    "exactly in your code.",
)

LOCATE_STEP = section(
    "## 2. Locate",
    "- Use exact paths from the issue directly. Otherwise combine independent searches into one "
    "run_command: `git grep -n -F \"<literal>\" -- '*.py' | head -20` for each exact symbol or "
    "message, plus `git ls-files | grep <keyword> | head`.",
    "- If the next search depends on a result, read that result first. Never dump whole files "
    "or the repository tree.",
    "- Read small regions with `sed -n 'A,Bp' path` (about 40-80 lines, up to three regions in "
    "one command) or `read_file` with a line range. Include enough to see signatures, defaults "
    "and error handling.",
    "- Bug: find where the wrong behaviour is produced, not where it is observed. Feature: find "
    "the closest existing sibling (a similar function, option, class or parameter) and copy its "
    "pattern, including registration points such as `__all__`, option lists, dispatch tables, "
    "imports and type hints.",
    "- If the issue contains a reproducing snippet, you may run it once with `python -c` or a "
    "heredoc written to /tmp to see the real error.",
)

REPRODUCE_STEP = section(
    "## 2b. Reproduce before editing",
    "- Write a short script to /tmp/repro.py with run_command (`cat > /tmp/repro.py <<'EOF' ... "
    "EOF`) that exercises exactly what the issue describes, using the issue's own example when "
    "it gives one, and asserts the expected behaviour. Run it with `cd /workspace && python "
    "/tmp/repro.py`. It must FAIL now; if it passes, your script does not capture the issue: "
    "fix the script first.",
)


def edit_step(compile_check: bool) -> str:
    return section(
        "## 3. Edit",
        "- Use edit_file for existing code. Copy old_string exactly from what you read, choose a "
        "short unique match. Use write_file only for a genuinely new source file the issue "
        "requires.",
        "- If edit_file fails, read the exact region again and retry with a smaller unique "
        "snippet. After two failures, use one inline Python script via run_command that asserts "
        "the old text occurs exactly once, replaces it and writes the file.",
        "- After every edit, run `python -m py_compile <edited file>` before anything else. If "
        "it fails, fix the syntax at once." if compile_check else "",
        "- Fix the cause, not the symptom. Do not special-case the example from the issue.",
        "- The grader runs the whole test file, including tests that pass today. Keep current "
        "behaviour for every input the issue does not mention; keep existing signatures, "
        "defaults and backward compatibility unless the issue says otherwise.",
        "- If the behaviour has parallel implementations (sync and async variants, several "
        "classes or backends, overloads, re-exports in `__init__.py`), change all of them.",
        "- Use the exact exception class and message text from the issue. If the issue only "
        "describes the error, follow the wording style of neighbouring messages.",
    )


def verify_step(imposed: bool, reproduce: bool, useful_test: bool) -> str:
    find = "`git ls-files | grep -i test | grep <keyword> | head`"
    k = "" if useful_test else " -k <keyword>"
    command = f"`timeout 150 python -m pytest path/to/test_file.py -x -q{k} 2>&1 | tail -40`"
    repro = "- Rerun `cd /workspace && python /tmp/repro.py`. It must pass now." if reproduce else ""
    if useful_test:
        excuses = ("- Never repair tests or the environment. Do not explain a failed or empty "
                   "check away: read what it says.")
        zero = (f"- Zero tests is not a check. If pytest prints `no tests ran`, `deselected`, "
                f"`collected 0 items` or `file or directory not found`, nothing was verified. "
                f"Tests live in test files, not in source modules: find a real one with {find} "
                "and run it.")
    else:
        excuses = ("- Failures from missing fixtures, missing data, network or unrelated import "
                   "errors are pre-existing: ignore them, never repair tests or the environment.")
        zero = ""
    if imposed:
        again = "the repro still fails or a related test breaks" if reproduce else (
            "a related test breaks")
        return section(
            "## 4. Verify (mandatory)", repro,
            f"- Run the closest existing test file: {find}, then {command}. The grader runs "
            "whole test files, so a test of that file that your change breaks is a failure.",
            zero, excuses,
            f"- If {again}, read the error, fix the source, and verify again. Repeat while you "
            "have calls left.",
        )
    return section(
        "## 4. Verify (at most 2-3 calls)", repro,
        f"- Find the closest existing test file ({find}), then run {command}. Or check the "
        "behaviour directly with a short `python -c` script that exercises the issue's example.",
        zero, excuses,
        "- If a check related to your change fails, read the traceback, fix the source once and "
        "rerun once.",
    )


def submit_step(spec: bool) -> str:
    names = (" and every name, message and type from step 1 appears exactly" if spec else "")
    return section(
        "## 5. Final check and submit",
        "- Run `git status --short && git diff`. Remove any scratch file under /workspace and "
        "restore any touched test file with `git checkout -- <path>`. Confirm only source files "
        f"changed{names}.",
        "- Call `submit_patch`. Confirm `patch_size > 0`. If it is 0, edit now and submit again.",
        "- End with a one-sentence summary.",
    )


DECISION_RULES = section(
    "# DECISION RULES",
    "- Ambiguous issue: take the most literal reading and act. Do not ask questions, do not "
    "stall.",
    "- Search found nothing: try one different specific string, then edit your best candidate "
    "anyway.",
    "- Stuck after a failed fix: make a different, smaller change.",
    "- Never conclude that nothing needs to change. Every task requires a non-empty source patch.",
)


def worked_example(spec: bool, reproduce: bool, useful_test: bool, compile_check: bool) -> str:
    """A session on a made-up project. It shows only what the active recipes ask for."""
    edit = "unitkit/size.py"
    test = "tests/test_size.py"
    steps = [
        "# EXAMPLE SESSION (a made-up project, to show the shape of the work; your issue is below)",
        "Issue: `parse_size(\"2KB\")` raises ValueError; it should return 2048.",
    ]
    if spec:
        steps.append("Spec, before any tool call: function `parse_size`, input \"2KB\", expected "
                     "2048, no exception, other units unchanged.")
    steps += [
        "run_command: git grep -n -F \"def parse_size\" -- '*.py' | head -20",
        f"  -> {edit}:14:def parse_size(text):",
        f"read_file: {edit}, lines 1-40",
    ]
    if reproduce:
        steps += [
            "run_command: cat > /tmp/repro.py <<'EOF'",
            "from unitkit.size import parse_size",
            "assert parse_size(\"2KB\") == 2048",
            "EOF",
            "cd /workspace && python /tmp/repro.py",
            "  -> ValueError: unknown unit 'KB' (it fails, so the script captures the issue)",
        ]
    steps.append(f"edit_file: {edit}, old_string `UNITS = dict(B=1, MB=1048576)`, "
                 "new_string `UNITS = dict(B=1, KB=1024, MB=1048576)`")
    if compile_check:
        steps += [f"run_command: python -m py_compile {edit}", "  -> no output: the syntax is fine"]
    if reproduce:
        steps += ["run_command: cd /workspace && python /tmp/repro.py", "  -> no error: it passes"]
    if useful_test:
        steps += [
            f"run_command: timeout 150 python -m pytest {edit} -x -q 2>&1 | tail -40",
            "  -> no tests ran in 0.03s",
            "Nothing was verified: that is a source module. Find a real test file.",
        ]
    steps += ["run_command: git ls-files | grep -i test | grep size | head", f"  -> {test}"]
    k = "" if useful_test else " -k size"
    steps += [
        f"run_command: timeout 150 python -m pytest {test} -x -q{k} 2>&1 | tail -40",
        "  -> 12 passed in 0.08s",
        "run_command: git status --short && git diff",
        f"  -> M {edit}, one line changed",
        "submit_patch",
    ]
    return "\n".join(steps)


def prompt(cfg: dict[str, bool]) -> str:
    spec, reproduce, imposed = cfg["C"], cfg["D"], cfg["E"]
    useful_test, compile_check, example = cfg["F"], cfg["G"], cfg["H"]
    head = ("You are an autonomous software engineer. Your job: make the smallest correct change "
            "to the SOURCE code in /workspace so that the hidden tests for the issue pass. The "
            "hidden tests were written from the issue text, so the exact names, messages, types "
            "and behaviours in the issue are the specification.")
    steps = [SPEC_STEP if spec else "", LOCATE_STEP, REPRODUCE_STEP if reproduce else "",
             edit_step(compile_check), verify_step(imposed, reproduce, useful_test),
             submit_step(spec)]
    parts = [
        head, hard_limits(useful_test), call_plan(imposed, reproduce),
        "# PROCEDURE", *[s for s in steps if s], DECISION_RULES,
        worked_example(spec, reproduce, useful_test, compile_check) if example else "",
        "# THE ISSUE (repeated here so it survives context compaction)\n{problem_description?}",
    ]
    return "\n\n".join(p for p in parts if p) + "\n"


def sampling(cfg: dict[str, bool]) -> str:
    return (f"temperature: {0.7 if cfg['A'] else 0.2}\n"
            "top_p: 0.95\n"
            "max_output_tokens: 6144\n"
            "thinking_config:\n"
            f"  thinking_budget: {256 if cfg['B'] else 4096}\n"
            "  include_thoughts: true\n")


AGENT_YAML = f"""name: swe_agent
model: {MODEL}
instruction: !include prompts/system.md
tools:
  - run_command
  - read_file
  - edit_file
  - write_file
  - get_status
  - submit_patch
generate_content_config: !include configs/sampling.yaml
"""

EVAL_CONFIG = f"""evaluation:
  timeout_seconds: 240
  max_tool_calls: {TOOL_CALLS}
  max_time_minutes: {MINUTES}
  max_turns: 80
"""


def write_variant(path: Path, cfg: dict[str, bool]) -> None:
    (path / "prompts").mkdir(parents=True)
    (path / "configs").mkdir()
    (path / "agent.yaml").write_text(AGENT_YAML)
    (path / "eval_config.yaml").write_text(EVAL_CONFIG)
    (path / "prompts" / "system.md").write_text(prompt(cfg))
    (path / "configs" / "sampling.yaml").write_text(sampling(cfg))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    shutil.rmtree(args.out, ignore_errors=True)
    table = {}
    for i, cfg in enumerate(design()):
        name = f"s{i:02d}"
        write_variant(args.out / name, cfg)
        table[name] = {RECIPES[k]: v for k, v in cfg.items()}
    (args.out / "design.json").write_text(json.dumps(table, indent=2) + "\n")
    print(f"{len(table)} configurations in {args.out}")


if __name__ == "__main__":
    main()
