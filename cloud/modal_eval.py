"""Off-Kaggle evaluation on Modal: the official harness in one x86 container, subprocess sandbox.

Same runner as the Kaggle kernels (kaggle/runner.py, with CONFIG prepended by
scripts/make_eval_kernel.py), but the stack comes from the image and the competition data from
a private Volume. E4B/E2B on one L4 only.

    uv run python scripts/make_eval_kernel.py --mode gold --tasks reports/modal_pool_40.txt --slug m-gold
    modal run cloud/modal_eval.py --run submissions/m-gold/run.py --run-id gold1 --cpu-only
    modal run cloud/modal_eval.py --run submissions/m-e4b/run.py --run-id e4b1
    modal volume get g4agent-data work/<run-id> results/modal/

Data layout on the Volume `g4agent-data` (uploaded by cloud/upload.sh, deleted after use):
    /input/comp/gemma-4-developer-agent/{tasks.jsonl,snapshots/,wheels/}
    /input/models/gemma-4-e4b-it-qat-w4a16-ct/{config.json,model.safetensors,...}
    /work/<run-id>/results/...
"""

import subprocess
import sys
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[1]
WHEELHOUSE = ROOT / "data" / "modal" / "wheelhouse"

# Test-only packages the hidden-test runner needs and the Kaggle image lacks (fastapi's tests
# import inline_snapshot / dirty_equals / sqlmodel; requests' tests need the httpbin fixture).
TEST_EXTRAS = [
    "pytest", "inline-snapshot", "dirty-equals", "sqlmodel", "python-multipart", "email-validator",
    "orjson", "ujson", "pyjwt", "passlib", "pytest-httpbin", "trustme", "flask", "pyyaml",
    "typer", "jinja2", "attrs", "pytest-mock", "pytest-asyncio", "coverage",
]

KAGGLE_PINS = [
    "starlette==0.52.1", "fastapi==0.136.1", "pydantic==2.12.3", "pydantic_core==2.41.4",
    "Pygments==2.20.0", "markdown-it-py==4.0.0", "mdurl==0.1.2", "anyio==4.13.0", "pytest==8.4.2",
    "rich==13.9.4", "typing_extensions==4.15.0", "SQLAlchemy==2.0.49", "python-multipart==0.0.26",
    "requests==2.32.4", "urllib3==2.5.0", "httpx==0.28.1", "idna==3.13", "certifi==2026.4.22",
    "charset-normalizer==3.4.7", "orjson==3.11.8", "ujson==5.13.0", "Jinja2==3.1.6", "attrs==26.1.0",
]

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "patch", "procps")
    .add_local_dir(WHEELHOUSE, "/wheelhouse", copy=True)
    .run_commands(
        # Kaggle datasets strip the '+' of local versions: restore '+cu128' as the notebook does.
        "mkdir -p /wheels && for w in /wheelhouse/*.whl; do n=$(basename $w); "
        "case $n in *cutlass*) continue;; esac; "
        "case $n in *+*) ;; *cu128*) n=$(echo $n | sed 's/cu128/+cu128/');; esac; "
        "cp $w /wheels/$n; done",
        # The wheelhouse is meant for `pip install --no-deps` on top of the Kaggle image, and its
        # pins conflict (google-adk wants starlette<1, vLLM's instrumentator starlette>=1).
        # Resolve vLLM's deps first, then the harness's, then overlay the exact wheels.
        "pip install --no-cache-dir --find-links /wheels /wheels/vllm-*.whl",
        "pip install --no-cache-dir --find-links /wheels /wheels/swegemma-*.whl "
        "/wheels/adk_submission-*.whl /wheels/adk_eval_core-*.whl /wheels/google_adk-*.whl litellm",
        "pip install --no-cache-dir --no-deps --force-reinstall /wheels/*.whl",
    )
    .pip_install(*TEST_EXTRAS)
    # Match the Kaggle image (cloud/kaggle_image_freeze.txt, pip freeze of the pinned notebook
    # image) for everything the tasks' tests import, so the sandbox behaves like the notebooks:
    # starlette 1.x breaks older fastapi (Router(on_startup=...)), pygments changes rich output.
    .run_commands("pip install --no-cache-dir --no-deps " + " ".join(KAGGLE_PINS))
    .env({"G4_SKIP_INSTALL": "1", "G4_INPUT": "/data/input", "VLLM_NO_USAGE_STATS": "1"})
)

app = modal.App("g4agent-eval", image=image)
volume = modal.Volume.from_name("g4agent-data", create_if_missing=True)


def _run(run_py: str, run_id: str) -> str:
    work = Path("/data/work") / run_id
    work.mkdir(parents=True, exist_ok=True)
    script = work / "run.py"
    script.write_text(run_py)
    env = {"G4_WORK": str(work)}
    import os
    proc = subprocess.run([sys.executable, str(script)], env={**os.environ, **env},
                          capture_output=True, text=True, check=False)
    (work / "stdout.log").write_text(proc.stdout[-2_000_000:])
    (work / "stderr.log").write_text(proc.stderr[-2_000_000:])
    volume.commit()
    summary = work / "results" / "summary.json"
    return (summary.read_text() if summary.exists() else "") + f"\nexit {proc.returncode}\n" + \
        proc.stderr[-3000:]


@app.function(gpu="L4", cpu=8, memory=32768, timeout=4 * 3600, volumes={"/data": volume})
def run_gpu(run_py: str, run_id: str) -> str:
    return _run(run_py, run_id)


@app.function(cpu=8, memory=16384, timeout=3 * 3600, volumes={"/data": volume})
def run_cpu(run_py: str, run_id: str) -> str:
    return _run(run_py, run_id)


@app.function(cpu=2, memory=4096, timeout=900)
def env_check() -> str:
    code = ("import torch, vllm, swegemma, adk_submission, google.adk, litellm, inline_snapshot, "
            "pytest, starlette; import vllm.entrypoints.openai.api_server; "
            "print(torch.__version__, torch.version.cuda, vllm.__version__, google.adk.__version__, "
            "starlette.__version__)")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    return out.stdout + out.stderr[-3000:]


@app.local_entrypoint()
def main(run: str = "", run_id: str = "", cpu_only: bool = False, check: bool = False):
    if check:
        print(env_check.remote())
        return
    text = Path(run).read_text()
    fn = run_cpu if cpu_only else run_gpu
    print(fn.remote(text, run_id))
