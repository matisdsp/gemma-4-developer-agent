"""Validate agent/ and write submissions/submission.zip. Submits nothing."""

import argparse
from pathlib import Path

from g4agent.package import build_zip, validate
from g4agent.paths import AGENT, SUBMISSIONS


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--agent-dir", type=Path, default=AGENT)
    ap.add_argument("--out", type=Path, default=SUBMISSIONS / "submission.zip")
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()

    model = validate(args.agent_dir)
    if args.check_only:
        print(f"{args.agent_dir}: valid, model {model}")
        return
    archive = build_zip(args.agent_dir, args.out)
    print(f"{archive}: {archive.stat().st_size / 2**20:.2f} MiB, model {model}")


if __name__ == "__main__":
    main()
