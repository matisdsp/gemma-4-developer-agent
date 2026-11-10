"""The descriptive measures of the replication: traces and records give the same rows."""

import importlib.util
import json
import random
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parent.parent / "docs" / "paper" / "analysis" / "screening"
          / "replicate_obedience.py")
spec = importlib.util.spec_from_file_location("replicate_obedience", SCRIPT)
obedience = importlib.util.module_from_spec(spec)
spec.loader.exec_module(obedience)


def trace(pytest_output):
    step = {"source": "agent", "message": "plan",
            "tool_calls": [{"function_name": "run_command",
                            "arguments": {"command": "python -m pytest tests/test_a.py"}}],
            "observation": {"content": json.dumps({"stdout": pytest_output, "exit_code": 0})},
            "metrics": {"completion_tokens": 120}}
    return {"steps": [step]}


def write_run(root, variant, pytest_output, resolved):
    d = root / "results" / variant
    (d / "traces").mkdir(parents=True)
    lines = []
    for task in ("a_1", "b_2"):
        (d / "traces" / f"trace_{task}.r0.json").write_text(json.dumps(trace(pytest_output)))
        lines.append({"variant": variant, "instance_id": task, "rep": 0, "resolved": resolved,
                      "patch_chars": 10, "agent_s": 12.5, "tool_calls": 1, "error": ""})
    (d / "results.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n")


def test_runs_and_records_give_the_same_rows(tmp_path):
    write_run(tmp_path, "s00r1", "no tests ran in 0.01s", False)
    write_run(tmp_path, "s04r1", "2 passed in 0.10s", True)
    write_run(tmp_path, "s07r1", "2 passed in 0.10s", True)
    tasks = tmp_path / "tasks.jsonl"
    tasks.write_text("\n".join(json.dumps({"instance_id": t, "problem_statement": "x"})
                               for t in ("a_1", "b_2")) + "\n")
    rows = obedience.load_runs([tmp_path / "results"], tasks)
    assert [(r["task"], r["variant"], r["repeat"]) for r in rows] == [
        ("a_1", "s00", 1), ("a_1", "s04", 1), ("b_2", "s00", 1), ("b_2", "s04", 1)]
    assert [r["last_pytest_real"] for r in rows] == [False, True, False, True]
    assert [r["last_pytest_empty"] for r in rows] == [True, False, True, False]

    obedience.write_records(rows, tmp_path / "out" / "features.csv")
    assert obedience.read_records(tmp_path / "out" / "features.csv") == rows

    res = obedience.compare(rows, "last_pytest_real", random.Random(1))
    assert (res["s00"], res["s04"], res["estimate"], res["n_tasks"]) == (0.0, 1.0, 1.0, 2)
