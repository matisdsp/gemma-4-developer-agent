"""Write a private Kaggle script kernel that rebuilds agent/ as submission.zip.

This is a code competition: a submission is the `submission.zip` output of a notebook run, not
an uploaded file. The kernel embeds every file of agent/ (validated first) and writes the zip to
/kaggle/working. CPU only, internet off, competition attached, always private.

    uv run python scripts/make_kernel.py            # writes submissions/kernel/
    kaggle kernels push -p submissions/kernel        # new private version, runs in ~1 min
    kaggle kernels status matisdespujols/g4agent-submission
    kaggle competitions submit gemma-4-developer-agent -k matisdespujols/g4agent-submission \
        -v <version> -f submission.zip -m "<message>"
"""

import argparse
import json
from pathlib import Path

from g4agent.package import validate
from g4agent.paths import AGENT, SUBMISSIONS

KERNEL_ID = "matisdespujols/g4agent-submission"

TEMPLATE = '''"""Writes submission.zip for the Gemma 4 Developer Agent competition (generated file)."""
import hashlib
import json
import zipfile
from pathlib import Path

FILES = json.loads(%r)

out = Path("/kaggle/working") if Path("/kaggle/working").is_dir() else Path.cwd()
zip_path = out / "submission.zip"
with zipfile.ZipFile(zip_path, "w") as zf:
    for name, content in sorted(FILES.items()):
        info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        zf.writestr(info, content.encode("utf-8"))
with zipfile.ZipFile(zip_path) as zf:
    assert zf.testzip() is None and set(zf.namelist()) == set(FILES)
    for name, content in FILES.items():
        assert zf.read(name) == content.encode("utf-8")
print("files:", sorted(FILES))
print("sha256:", hashlib.sha256(zip_path.read_bytes()).hexdigest())
'''


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--agent-dir", type=Path, default=AGENT)
    ap.add_argument("--out", type=Path, default=SUBMISSIONS / "kernel")
    ap.add_argument("--title", default="g4agent submission")
    args = ap.parse_args()

    model = validate(args.agent_dir)
    files = {}
    for path in sorted(args.agent_dir.rglob("*")):
        if path.is_file():
            if path.suffix == ".safetensors":
                raise SystemExit("adapters cannot be embedded in a script; upload a dataset")
            files[path.relative_to(args.agent_dir).as_posix()] = path.read_text("utf-8")

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "submission.py").write_text(TEMPLATE % json.dumps(files, sort_keys=True))
    meta = {
        "id": KERNEL_ID,
        "title": args.title,
        "code_file": "submission.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": False,
        "enable_tpu": False,
        "enable_internet": False,
        "dataset_sources": [],
        "competition_sources": ["gemma-4-developer-agent"],
        "kernel_sources": [],
        "model_sources": [],
    }
    (args.out / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"{args.out}: {len(files)} files, model {model}, kernel {KERNEL_ID} (private)")


if __name__ == "__main__":
    main()
