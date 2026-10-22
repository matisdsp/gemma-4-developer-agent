"""Compile agent/ with the harness compiler and render the root instruction.

Stronger than `build_submission.py --check-only`: it runs `compile_submission` with stub tools
and a stub model (no server needed) under the scorer's limits and generation constraints, then
renders the root instruction against a fake session state, as ADK does at run time.
"""

import argparse
import asyncio
from pathlib import Path
from types import SimpleNamespace

from adk_submission import compile_submission
from adk_submission.registry import ModelRegistry, ToolRegistry
from google.adk.models.lite_llm import LiteLlm
from google.adk.utils.instructions_utils import inject_session_state
from swegemma.config import build_submission_limits

from g4agent.paths import AGENT

TOOLS = ["run_command", "read_file", "edit_file", "write_file", "get_status", "submit_patch",
         "get_code_neighbors", "search_similar_code", "get_code_subgraph"]
MODELS = ["gemma-4-31b-it-qat-w4a16-ct", "gemma-4-12b-it-qat-w4a16-ct",
          "gemma-4-e4b-it-qat-w4a16-ct", "gemma-4-e2b-it-qat-w4a16-ct"]


def _stub(name):
    def tool() -> str:
        return "{}"
    tool.__name__ = name
    tool.__doc__ = f"stub {name}"
    return tool


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--agent-dir", type=Path, default=AGENT)
    args = ap.parse_args()

    tools = ToolRegistry()
    for name in TOOLS:
        tools.register(name, _stub(name))
    models = ModelRegistry()
    for name in MODELS:
        models.register(name, LiteLlm(model=f"openai/{name}", api_base="http://127.0.0.1:1/v1"))
    limits, constraints = build_submission_limits()
    agent = compile_submission(args.agent_dir, tool_registry=tools, model_registry=models,
                               limits=limits, generation_constraints=constraints)
    print(f"compiled: {type(agent).__name__} {agent.name}")
    for sub in getattr(agent, "sub_agents", []) or []:
        print(f"  sub-agent: {type(sub).__name__} {sub.name}")

    instruction = getattr(agent, "instruction", None)
    if isinstance(instruction, str):
        state = {"problem_description": "PROBLEM-STATEMENT-SENTINEL"}
        ctx = SimpleNamespace(_invocation_context=SimpleNamespace(
            session=SimpleNamespace(state=state, app_name="a", user_id="u", id="s"),
            artifact_service=None))
        rendered = asyncio.run(inject_session_state(instruction, ctx))
        print(f"instruction: {len(rendered)} chars rendered, "
              f"problem inlined: {'PROBLEM-STATEMENT-SENTINEL' in rendered}")


if __name__ == "__main__":
    main()
