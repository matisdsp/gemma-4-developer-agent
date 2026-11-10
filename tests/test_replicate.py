"""The replication analysis: loading, the per-task difference and the reading rule."""

import importlib.util
import json
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parent.parent / "docs" / "paper" / "analysis" / "screening"
          / "replicate.py")
spec = importlib.util.spec_from_file_location("replicate", SCRIPT)
replicate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replicate)


def row(task, variant, repeat, resolved):
    return {"task": task, "variant": variant, "repeat": repeat, "resolved": resolved,
            "nonempty": True, "agent_s": 1.0, "tool_calls": 2, "error": ""}


def test_difference_is_computed_within_each_task():
    rows = [row("a_1", "s04", k, k <= 3) for k in (1, 2, 3, 4)]
    rows += [row("a_1", "s00", k, k <= 1) for k in (1, 2, 3, 4)]
    rows += [row("b_2", "s04", k, False) for k in (1, 2, 3, 4)]
    rows += [row("b_2", "s00", k, k <= 2) for k in (1, 2, 3, 4)]
    assert replicate.differences(rows) == [0.5, -0.5]
    assert replicate.differences(list(reversed(rows))) == [0.5, -0.5]


def test_reading_rule():
    assert replicate.reading({"low": 0.01, "high": 0.09, "p": 0.01}) == "helps"
    assert replicate.reading({"low": 0.01, "high": 0.09, "p": 0.06}) == "unresolved"
    assert replicate.reading({"low": -0.02, "high": 0.029, "p": 0.6}) == "no advantage beyond 3 points"
    assert replicate.reading({"low": -0.08, "high": -0.01, "p": 0.01}) == "no advantage beyond 3 points"
    assert replicate.reading({"low": -0.02, "high": 0.04, "p": 0.5}) == "unresolved"
    assert replicate.reading({"low": 0.005, "high": 0.02, "p": 0.01}) == "helps"


def test_runs_and_records_give_the_same_rows(tmp_path):
    for variant, resolved in (("s00r1", False), ("s04r1", True), ("s04r2", False), ("s07r1", True)):
        d = tmp_path / "results" / variant
        d.mkdir(parents=True)
        lines = [{"variant": variant, "instance_id": t, "rep": 0, "resolved": resolved,
                  "patch_chars": 10, "agent_s": 12.5, "tool_calls": 7, "error": "x" * 80}
                 for t in ("a_1", "b_2", "not_a_task")]
        (d / "results.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n")
    rows = replicate.load_runs([tmp_path / "results"], {"a_1", "b_2"})
    assert len(rows) == 6
    assert {(r["variant"], r["repeat"]) for r in rows} == {("s00", 1), ("s04", 1), ("s04", 2)}
    assert all(len(r["error"]) == 60 for r in rows)
    assert replicate.differences(rows) == [0.5, 0.5]
    replicate.write_records(rows, tmp_path / "out" / "records.csv")
    assert replicate.read_records(tmp_path / "out" / "records.csv") == rows
