"""The screening design and the prompts it generates."""

import importlib.util
import itertools
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "make_screening.py"
spec = importlib.util.spec_from_file_location("make_screening", SCRIPT)
screening = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screening)

DESIGN = screening.design()
LETTERS = list("ABCDEFGH")


def sign(cfg, letter):
    return 1 if cfg[letter] else -1


def column(*letters):
    out = []
    for cfg in DESIGN:
        value = 1
        for letter in letters:
            value *= sign(cfg, letter)
        out.append(value)
    return tuple(out)


def test_all_runs_distinct_and_every_recipe_balanced():
    assert len(DESIGN) == 32
    assert len({tuple(cfg[k] for k in LETTERS) for cfg in DESIGN}) == 32
    for letter in LETTERS:
        assert sum(cfg[letter] for cfg in DESIGN) == 16


def test_recipes_are_mutually_orthogonal():
    for a, b in itertools.combinations(LETTERS, 2):
        assert sum(column(a, b)) == 0


def test_main_effects_are_clear_of_two_way_interactions():
    mains = {column(k) for k in LETTERS} | {tuple(-v for v in column(k)) for k in LETTERS}
    for a, b in itertools.combinations(LETTERS, 2):
        assert column(a, b) not in mains


@pytest.mark.parametrize("letter", ["E", "H"])
def test_interactions_with_verification_and_example_are_clear(letter):
    pairs = list(itertools.combinations(LETTERS, 2))
    for other in LETTERS:
        if other == letter:
            continue
        target = column(letter, other)
        for a, b in pairs:
            if {a, b} == {letter, other}:
                continue
            assert column(a, b) != target and column(a, b) != tuple(-v for v in target)


def test_every_recipe_off_is_inside_the_fraction():
    assert any(not any(cfg.values()) for cfg in DESIGN)


@pytest.mark.parametrize("cfg", DESIGN)
def test_prompt_mentions_only_active_recipes(cfg):
    text = screening.prompt(cfg)
    assert text.count("{problem_description?}") == 1
    assert text.count("{") == 1  # ADK reads braces as session-state variables
    assert text.rstrip().endswith("{problem_description?}")
    assert ("## 1. Extract the specification" in text) == cfg["C"]
    assert ("step 1" in text) == cfg["C"]
    assert ("## 2b." in text) == cfg["D"]
    assert ("step 2b" in text) == cfg["D"]
    assert ("/tmp/repro.py" in text) == cfg["D"]
    assert ("far more budget" in text) == cfg["E"]
    assert ("(mandatory)" in text) == cfg["E"]
    assert ("(at most 2-3 calls)" in text) != cfg["E"]
    assert ("`-k`" in text or " -k " in text) != cfg["F"]
    assert ("Zero tests is not a check" in text) == cfg["F"]
    assert ("pre-existing" in text) != cfg["F"]
    assert ("py_compile" in text) == cfg["G"]
    assert ("# EXAMPLE SESSION" in text) == cfg["H"]


def test_sampling_levels():
    for cfg in DESIGN:
        text = screening.sampling(cfg)
        assert f"temperature: {0.7 if cfg['A'] else 0.2}\n" in text
        assert f"thinking_budget: {256 if cfg['B'] else 4096}\n" in text
