"""Write a private Kaggle kernel that evaluates agent variants on the public tasks.

    # which public tasks the subprocess sandbox can score at all (CPU, reference patches)
    uv run python scripts/make_eval_kernel.py --mode gold --slug g4agent-gold
    # variants side by side on 4xL4, interleaved, same vLLM server as the scorer
    uv run python scripts/make_eval_kernel.py --variant v1=agent --variant v2=variants/v2 \
        --tasks reports/gold_ok.txt --concurrency 4 --slug g4agent-eval
    kaggle kernels push -p submissions/<slug>
    kaggle kernels output matisdespujols/<slug> -p results/kaggle/<slug>

Nothing leaves Kaggle: the kernel is private, internet off, and only reads the competition data,
the official wheelhouse and the official model weights.
"""

import argparse
import json
from pathlib import Path

from g4agent.package import validate
from g4agent.paths import ROOT, SUBMISSIONS


def model_source(model: str) -> str:
    return f"google/gemma-4/Other/{model}/2"


def read_variant(path: Path) -> dict[str, str]:
    validate(path)
    return {p.relative_to(path).as_posix(): p.read_text("utf-8")
            for p in sorted(path.rglob("*")) if p.is_file()}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=["gold", "agent"], default="agent")
    ap.add_argument("--variant", action="append", default=[], help="name=agent_dir")
    ap.add_argument("--tasks", type=Path, help="file with one instance_id per line")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--deadline-hours", type=float, default=10.5)
    ap.add_argument("--slug", default="g4agent-eval")
    args = ap.parse_args()

    variants = dict(v.split("=", 1) for v in (args.variant or ["v1=agent"]))
    config = {
        "mode": args.mode,
        "variants": {name: read_variant(ROOT / d) for name, d in variants.items()},
        "task_ids": ([t.strip() for t in args.tasks.read_text().split() if t.strip()]
                     if args.tasks else None),
        "concurrency": args.concurrency,
        "repeats": args.repeats,
        "deadline_hours": args.deadline_hours,
    }
    out = SUBMISSIONS / args.slug
    out.mkdir(parents=True, exist_ok=True)
    runner = (ROOT / "kaggle" / "runner.py").read_text()
    (out / "run.py").write_text(f"CONFIG = {json.dumps(config)!r}\nimport json as _j\n"
                                f"CONFIG = _j.loads(CONFIG)\n\n{runner}")
    gpu = args.mode == "agent"
    meta = {
        "id": f"matisdespujols/{args.slug}",
        "title": args.slug,
        "code_file": "run.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": gpu,
        "enable_tpu": False,
        "enable_internet": False,
        "dataset_sources": ["metric/gemma-4-developer-agent-wheelhouse"],
        "competition_sources": ["gemma-4-developer-agent"],
        "kernel_sources": [],
        "model_sources": sorted({model_source(validate(ROOT / d)) for d in variants.values()})
        if gpu else [],
    }
    if gpu:
        meta["machine_shape"] = "NvidiaL4"
    (out / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    n = len(config["task_ids"]) if config["task_ids"] else "all"
    print(f"{out}: mode {args.mode}, variants {list(variants)}, tasks {n}, "
          f"concurrency {args.concurrency}, private")


if __name__ == "__main__":
    main()
