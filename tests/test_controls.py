"""The exploratory controls: strict pytest measure, reproduction script and the records."""

import importlib.util
import json
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parent.parent / "docs" / "paper" / "analysis" / "screening"
          / "controls.py")
spec = importlib.util.spec_from_file_location("controls", SCRIPT)
controls = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controls)


def step(name, arguments, stdout=""):
    return {"source": "agent", "tool_calls": [{"function_name": name, "arguments": arguments}],
            "observation": {"content": json.dumps({"stdout": stdout, "exit_code": 0})}}


def test_an_error_only_summary_is_not_a_test_passed_or_failed():
    assert controls.passed_or_failed("==== 2 passed in 0.10s ====")
    assert controls.passed_or_failed("==== 1 failed, 1 error in 0.20s ====")
    assert not controls.passed_or_failed("==== 1 error in 0.37s ====")
    assert not controls.passed_or_failed("==== no tests ran in 0.01s ====")
    assert not controls.passed_or_failed("nothing that looks like a summary")


def test_counts_of_one_attempt():
    trace = {"steps": [
        step("run_command", {"command": "python3 /tmp/repro.py"}),
        step("edit_file", {"filepath": "pkg/a.py"}),
        step("run_command", {"command": "python3 /tmp/repro.py"}),
        step("run_command", {"command": "python -m pytest tests/test_a.py"},
             "ModuleNotFoundError: No module named 'dirty_equals'\n==== 1 error in 0.37s ===="),
        step("run_command", {"command": "python -m pytest tests/test_b.py"},
             "==== 3 passed in 0.50s ===="),
        step("run_command", {"command": "pip install pytest"}, "==== 1 passed in 0.10s ===="),
    ]}
    assert controls.attempt_counts(trace) == {
        "pytest_calls": 2, "pytest_ran": 2, "pytest_passed_or_failed": 1,
        "pytest_missing_module": 1, "repro_runs": 2, "repro_runs_before_edit": 1}


def test_counts_round_trip(tmp_path):
    rows = [{"task": "a_1", "variant": "s00", "rep": 0, "pytest_calls": 2, "pytest_ran": 1,
             "pytest_passed_or_failed": 1, "pytest_missing_module": 0, "repro_runs": 0,
             "repro_runs_before_edit": 0}]
    controls.write_counts(rows, tmp_path / "out" / "counts.csv")
    assert controls.read_counts(tmp_path / "out" / "counts.csv") == rows
    assert controls.share(rows, "pytest_ran", "pytest_calls") == 0.5
