"""Why do edit_file calls arrive without old_string? Classify every failing call in the traces,
and replay the pattern through vLLM's own gemma4 argument parser.

    uv run python scripts/edit_arg_failures.py results/modal \\
        --wheel data/modal/wheelhouse/vllm-0.19.1-cp38-abi3-manylinux_2_31_x86_64.whl

Gemma 4 writes tool arguments as ``key:<|"|>value<|"|>``. The parser
(``vllm/tool_parsers/gemma4_tool_parser.py::_parse_gemma4_args``) pairs ``<|"|>`` tokens
strictly. If the model closes a string with another character (a backtick in most observed
cases), the parser runs on to the next ``<|"|>``. It then swallows ``,old_string:`` into
new_string and turns the following code into junk keys. It raises no error, so the harness
only sees a call without old_string.
"""

import argparse
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

D = '<|"|>'
MARKER = re.compile(r"(.)(,|\n)\s*(old_string|new_string)\s*:")


def classify(root: Path) -> None:
    fail = ok = 0
    kinds: Counter[str] = Counter()
    for trace in root.glob("*/results/*/traces/*.json"):
        for step in json.loads(trace.read_text())["steps"]:
            for call in step.get("tool_calls") or []:
                if call["function_name"] != "edit_file":
                    continue
                args = call.get("arguments") or {}
                if "mandatory input parameters are not present" not in str(step.get("observation")):
                    ok += 1
                    continue
                fail += 1
                m = MARKER.search(" ".join(str(v) for v in args.values()))
                junk = [k for k in args if k not in ("filepath", "old_string", "new_string")]
                if m:
                    kinds[f"next key swallowed into a value, string closed by {m.group(1)!r}"] += 1
                elif junk:
                    kinds["value not opened by <|\"|>: bare-value split into junk keys"] += 1
                else:
                    kinds["argument simply absent"] += 1
    print(f"edit_file calls: {ok} parsed fine, {fail} missing an argument")
    for kind, n in kinds.most_common():
        print(f"  {n:4d}  {kind}")


def replay(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as zf:
        src = zf.read("vllm/tool_parsers/gemma4_tool_parser.py").decode()
    ns: dict = {"STRING_DELIM": D}
    # Run only the pure-Python parser functions from the official wheel (no torch/vllm import).
    exec(src[src.index("def _parse_gemma4_value"):src.index("def _parse_gemma4_array")], ns)  # noqa: S102
    parse = ns["_parse_gemma4_args"]
    new = "        if title_text is not None:\n            title_text.stylize_before(border_style)"
    old = "        if title_text is not None:\n            title_text.stylize_before(partial_border_style)"
    cases = {
        "well-formed": f"filepath:{D}rich/panel.py{D},new_string:{D}{new}{D},old_string:{D}{old}{D}",
        "strings closed by a backtick (as observed, rich_3718)":
            f"filepath:{D}rich/panel.py{D},new_string:{D}{new}`,old_string:{D}{old}`",
    }
    for name, text in cases.items():
        print(f"{name}:\n  {json.dumps(parse(text))}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("results", type=Path)
    ap.add_argument("--wheel", type=Path)
    args = ap.parse_args()
    classify(args.results)
    if args.wheel:
        replay(args.wheel)


if __name__ == "__main__":
    main()
