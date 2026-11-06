# ruff: noqa: F821, BLE001, ASYNC230  (CONFIG is prepended by scripts/make_eval_kernel.py)
# Kaggle-side evaluation runner. scripts/make_eval_kernel.py prepends `CONFIG = {...}` to this
# file and pushes the result as a private kernel. Two modes:
#   gold  : verify the reference patch of each public task in the subprocess sandbox (CPU only).
#           Tells which tasks this environment can score at all.
#   agent : serve the declared model with vLLM exactly as the scorer does (TP 4, 32k, gemma4
#           parsers) and run one or more agent variants on the same tasks, interleaved, so that
#           variants share the same load. Results go to /kaggle/working/results/<variant>/.
# CONFIG keys: mode, variants {name: {relpath: text}}, task_ids (list or None), concurrency,
#              deadline_hours (no new task after this), repeats.
import asyncio
import glob
import json
import logging
import os
import random
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

T0 = time.time()
WORK = Path(os.environ.get("G4_WORK", "/kaggle/working"))
INPUT = os.environ.get("G4_INPUT", "/kaggle/input")
OUT = WORK / "results"
OUT.mkdir(parents=True, exist_ok=True)


# Adds an unrelated file. A task whose hidden tests pass with it does not discriminate.
NOOP_PATCH = ("diff --git a/NOOP_CHECK.txt b/NOOP_CHECK.txt\nnew file mode 100644\n"
              "index 0000000..e69de29\n--- /dev/null\n+++ b/NOOP_CHECK.txt\n@@ -0,0 +1 @@\n+noop\n")


def log(msg):
    line = f"[{(time.time() - T0) / 60:7.1f} min] {msg}"
    print(line, flush=True)
    with open(OUT / "runner.log", "a") as f:
        f.write(line + "\n")


for k, v in {
    "TRANSFORMERS_NO_TF": "1", "TRANSFORMERS_NO_FLAX": "1", "TRANSFORMERS_OFFLINE": "1",
    "VLLM_NO_USAGE_STATS": "1", "VLLM_WORKER_MULTIPROC_METHOD": "spawn",
    "VLLM_ENGINE_READY_TIMEOUT_S": "3600", "VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS": "1",
    "NCCL_DEBUG": "WARN", "LITELLM_LOCAL_MODEL_COST_MAP": "True", "LITELLM_TELEMETRY": "False",
    "LITELLM_LOG": "WARNING", "OPENAI_API_KEY": "EMPTY", "LOCAL_API_KEY": "EMPTY",
    "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True", "OTEL_SDK_DISABLED": "true",
    "OTEL_PYTHON_DISABLED": "true",
}.items():
    os.environ.setdefault(k, v)


def find_dir(marker, pattern):
    hits = sorted(glob.glob(f"{INPUT}/**/{marker}", recursive=True))
    hits = [h for h in hits if pattern in h] or hits
    if not hits:
        raise SystemExit(f"cannot find {marker} under {INPUT}")
    return Path(hits[0]).parent


def install_wheelhouse():
    if os.environ.get("G4_SKIP_INSTALL"):  # Modal: the image already has the stack
        return
    wheel_dirs = [Path(p).parent for p in glob.glob("/kaggle/input/**/swegemma*.whl", recursive=True)]
    if not wheel_dirs:
        raise SystemExit("wheelhouse dataset not attached")
    src = wheel_dirs[0]
    for pattern in ("/usr/local/lib/python*/dist-packages/*cutlass*.pth",
                    "/usr/local/lib/python*/site-packages/*cutlass*.pth"):
        for pth in glob.glob(pattern):
            try:
                os.unlink(pth)
            except OSError:
                pass
    tmp = Path("/tmp/wheelhouse")
    tmp.mkdir(parents=True, exist_ok=True)
    for w in src.glob("*.whl"):
        if "cutlass" in w.name.lower():
            continue
        name = w.name.replace("cu128", "+cu128") if ("cu128" in w.name and "+" not in w.name) else w.name
        target = tmp / name
        if not target.exists():
            try:
                os.symlink(w, target)
            except OSError:
                shutil.copyfile(w, target)
    wheels = sorted(str(w) for w in tmp.glob("*.whl"))
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--no-deps",
                    "--force-reinstall", *wheels], check=True)
    log(f"installed {len(wheels)} wheels from {src}")


def quiet_logs():
    for name in ("LiteLLM", "LiteLLM Router", "LiteLLM Proxy", "litellm", "httpx", "httpcore",
                 "openai", "urllib3", "opentelemetry", "opentelemetry.context"):
        lg = logging.getLogger(name)
        lg.setLevel(logging.WARNING)
        if "litellm" in name.lower():
            lg.propagate = False
            lg.handlers.clear()


def write_variants():
    dirs = {}
    for name, files in CONFIG["variants"].items():
        d = WORK / "agents" / name
        shutil.rmtree(d, ignore_errors=True)
        for rel, text in files.items():
            p = d / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        dirs[name] = d
    return dirs


def eval_section(agent_dir):
    import yaml
    f = agent_dir / "eval_config.yaml"
    raw = (yaml.safe_load(f.read_text()) or {}) if f.is_file() else {}
    return raw.get("evaluation", raw)


def make_config(agent_dir, models, data_dir, results_dir):
    from google.adk.agents.context_cache_config import ContextCacheConfig
    from google.adk.apps._configs import EventsCompactionConfig
    from swegemma.config import EvalConfig, build_submission_limits
    ev = eval_section(agent_dir)
    limits, constraints = build_submission_limits()
    turns = ev.get("max_turns", ev.get("max_llm_calls"))
    return EvalConfig(
        tasks_path=data_dir / "tasks.jsonl",
        snapshots_dir=data_dir / "snapshots",
        results_dir=results_dir,
        submission_dir=agent_dir,
        models=models,
        sandbox="subprocess",
        timeout_seconds=int(ev.get("timeout_seconds", 300)),
        verification_timeout_seconds=300,
        max_time_minutes=float(ev.get("max_time_minutes", 60.0)),
        max_tool_calls=int(ev.get("max_tool_calls", 100)),
        max_turns=int(turns) if turns is not None else None,
        limits=limits,
        generation_constraints=constraints,
        context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=1800, cache_intervals=10),
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=15, overlap_size=2, token_threshold=14336, event_retention_size=5),
        graph_dir=str(data_dir / "graphs"),
        embeddings_dir=str(data_dir / "embeddings"),
        wheels_dir=data_dir / "wheels",
        verbose=False,
        display_mode="quiet",
    )


def start_vllm(agent_dir):
    import litellm
    import torch
    from adk_submission import VllmConfig, VllmServer, discover_adapters
    from adk_submission.discovery import discover_declared_models
    from swegemma.config import ALLOWED_ADAPTER_EXTENSIONS
    litellm.drop_params = True
    model = next(iter(discover_declared_models(agent_dir)))
    paths = glob.glob(f"{INPUT}/**/{model}/*/config.json", recursive=True) + \
        glob.glob(f"{INPUT}/**/{model}/config.json", recursive=True)
    if not paths:
        raise SystemExit(f"weights for {model} not attached")
    model_path = Path(paths[0]).parent
    # The first read of the weights from /kaggle/input can be very slow (a first run timed out
    # at "Loading safetensors 0/1" after 20 min). Stream them once, logging throughput.
    t = time.time()
    total = 0
    for f in sorted(model_path.rglob("*")):
        if f.is_file():
            with open(f, "rb") as fh:
                while chunk := fh.read(64 << 20):
                    total += len(chunk)
            log(f"read {f.name}: {total / 2**30:.1f} GiB in {time.time() - t:.0f}s")
    adapters = discover_adapters(str(agent_dir), adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
    amap = getattr(adapters, "adapters", None) or {}
    ranks = [r for i in amap.values() if (r := getattr(i, "rank", None))]
    extra = {"gemma-4-12b-it-qat-w4a16-ct": (
        "--hf-overrides", '{"architectures": ["Gemma4ForCausalLM"], "model_type": "gemma4"}')}
    cfg = VllmConfig(
        model=str(model_path), port=8000, host="127.0.0.1", tool_call_parser="gemma4",
        reasoning_parser="gemma4", max_model_len=32768,
        dtype="bfloat16" if (torch.cuda.is_available() and torch.cuda.is_bf16_supported()) else "auto",
        gpu_memory_utilization=0.90, enable_auto_tool_choice=True, enable_lora=bool(amap),
        max_loras=max(1, len(amap)), max_lora_rank=max(ranks) if ranks else 128,
        scheduler_reserve_full_isl=False, tensor_parallel_size=min(4, max(1, torch.cuda.device_count())),
        startup_timeout=60 * 60, extra_args=extra.get(model, ()),
    )
    server = VllmServer(cfg, adapter_manifest=adapters)
    server.start()
    log(f"vLLM up: {model} from {model_path}")
    models = server.create_model_registry(aliases=[model], model_prefix="openai/", api_key="EMPTY")
    return server, models, adapters


def decode_bench():
    """Latency of n identical concurrent requests (256 tokens) on the live server: decode cost
    of batching on the scorer's setup. Results in results/decode_bench.json."""
    import concurrent.futures
    import urllib.request
    base = "http://127.0.0.1:8000/v1"
    with urllib.request.urlopen(base + "/models", timeout=30) as r:
        model_id = json.load(r)["data"][0]["id"]
    body = json.dumps({"model": model_id, "prompt": "Write a long story about a lighthouse keeper.",
                       "max_tokens": 256, "min_tokens": 256, "temperature": 0.0}).encode()

    def one(_):
        req = urllib.request.Request(base + "/completions", data=body,
                                     headers={"Content-Type": "application/json"})
        t = time.time()
        with urllib.request.urlopen(req, timeout=600) as r:
            out = json.load(r)
        return time.time() - t, out["usage"]["completion_tokens"]

    one(0)  # warm-up
    rows = []
    for n in (1, 2, 4, 8):
        t = time.time()
        with concurrent.futures.ThreadPoolExecutor(n) as ex:
            res = list(ex.map(one, range(n)))
        wall = time.time() - t
        toks = res[0][1]
        rows.append({"concurrent": n, "wall_s": round(wall, 2), "tokens_each": toks,
                     "ms_per_step": round(1000 * max(r[0] for r in res) / max(1, toks), 1),
                     "raw": [[round(r[0], 3), r[1]] for r in res]})
        log(f"decode bench {rows[-1]}")
    (OUT / "decode_bench.json").write_text(json.dumps(rows, indent=2))


async def run_jobs(jobs, concurrency, deadline):
    sem = asyncio.Semaphore(concurrency)
    done = 0
    broken = []  # fail fast when the stack is broken (no tool call at all in the first jobs)

    async def one(job):
        nonlocal done
        variant, evaluator, task, rep, rdir = job
        async with sem:
            if time.time() > deadline or (len(broken) >= 4 and all(broken[:4])):
                return
            from swegemma.context import SwegemmaContext
            ctx = SwegemmaContext(
                docker_manager=evaluator.docker, container_id="",
                problem_statement=task.problem_statement,
                hints_text=getattr(task, "hints_text", "") or "", task=task, repo=task.repo,
                graph_dir=evaluator.config.graph_dir, embeddings_dir=evaluator.config.embeddings_dir,
                budget=evaluator.config.budget, harness=evaluator.config.harness)
            t = time.time()
            rec = {"variant": variant, "instance_id": task.instance_id, "repo": task.repo, "rep": rep}
            try:
                res = await evaluator.evaluate_task(task=task, task_index=1, total_tasks=1, context=ctx)
                patch = res.agent_patch or ""
                rec.update(resolved=bool(res.resolved), patch_chars=len(patch),
                           exit_code=res.test_exit_code, error=(res.error or "")[:500],
                           tool_calls=ctx.tool_calls_used, llm_calls=ctx.llm_calls_used,
                           agent_s=round(ctx.agent_elapsed_seconds, 1))
                (rdir / "patches").mkdir(exist_ok=True)
                (rdir / "patches" / f"{task.instance_id}.r{rep}.patch").write_text(patch)
                trace = Path(res.trace_json_path) if getattr(res, "trace_json_path", None) else None
                if trace is None or not trace.is_file():
                    trace = rdir / "traces" / f"trace_{task.instance_id}.json"
                if trace.is_file():  # keep one trace per repeat; the harness reuses the name
                    kept = trace.with_name(f"trace_{task.instance_id}.r{rep}.json")
                    trace.rename(kept)
                    rec["trace"] = str(kept.relative_to(OUT))
                (rdir / "test_outputs").mkdir(exist_ok=True)
                (rdir / "test_outputs" / f"{task.instance_id}.r{rep}.log").write_text(
                    (res.test_output or "")[-20000:])
            except Exception as e:  # keep going: one broken task must not kill the run
                rec.update(resolved=False, error=f"runner: {type(e).__name__}: {e}"[:500])
                traceback.print_exc()
            rec["wall_s"] = round(time.time() - t, 1)
            with open(rdir / "results.jsonl", "a") as f:
                f.write(json.dumps(rec) + "\n")
            done += 1
            if CONFIG["mode"] == "agent":
                broken.append(not rec.get("tool_calls") and not rec.get("patch_chars"))
            log(f"{done}/{len(jobs)} {variant} {task.instance_id} r{rep} "
                f"resolved={rec.get('resolved')} patch={rec.get('patch_chars')} "
                f"calls={rec.get('tool_calls')} agent={rec.get('agent_s')}s wall={rec['wall_s']}s "
                f"{rec.get('error', '')[:120]}")

    await asyncio.gather(*(one(j) for j in jobs))


def summarize():
    rows = []
    for f in OUT.glob("*/results.jsonl"):
        rows += [json.loads(line) for line in f.read_text().splitlines() if line.strip()]
    summary = {}
    for v in sorted({r["variant"] for r in rows}):
        rs = [r for r in rows if r["variant"] == v]
        agent = sorted(r.get("agent_s") or 0 for r in rs)
        summary[v] = {
            "n": len(rs), "resolved": sum(r["resolved"] for r in rs),
            "empty_patch": sum(1 for r in rs if not r.get("patch_chars")),
            "mean_agent_s": round(sum(agent) / max(1, len(agent)), 1),
            "p90_agent_s": agent[int(0.9 * (len(agent) - 1))] if agent else None,
            "mean_wall_s": round(sum(r["wall_s"] for r in rs) / max(1, len(rs)), 1),
            "mean_tool_calls": round(sum(r.get("tool_calls") or 0 for r in rs) / max(1, len(rs)), 1),
        }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    log("summary " + json.dumps(summary))


def main():
    install_wheelhouse()
    quiet_logs()
    from swegemma.evaluate import Evaluator
    from swegemma.models import load_tasks
    data_dir = find_dir("tasks.jsonl", "gemma-4-developer-agent")
    tasks = load_tasks(data_dir / "tasks.jsonl")
    if CONFIG.get("task_ids"):
        by_id = {t.instance_id: t for t in tasks}
        tasks = [by_id[i] for i in CONFIG["task_ids"] if i in by_id]
    log(f"{len(tasks)} tasks, mode {CONFIG['mode']}")
    dirs = write_variants()
    deadline = T0 + CONFIG.get("deadline_hours", 10.5) * 3600

    if CONFIG["mode"] in ("gold", "noop"):
        from adk_eval_core.tracing import SessionTrace
        from adk_submission import ModelRegistry
        name, agent_dir = next(iter(dirs.items()))
        rdir = OUT / CONFIG["mode"]
        rdir.mkdir(parents=True, exist_ok=True)
        ev = Evaluator(make_config(agent_dir, ModelRegistry(), data_dir, rdir))
        patches = {t.instance_id: t.patch if CONFIG["mode"] == "gold" else NOOP_PATCH for t in tasks}

        async def gold(task, snapshot_path, *a, **kw):
            return patches[task.instance_id], None, SessionTrace()
        ev._run_agent_sandbox = gold
        jobs = [(CONFIG["mode"], ev, t, 0, rdir) for t in tasks]
        asyncio.run(run_jobs(jobs, CONFIG.get("concurrency", 2), deadline))
    else:
        first = next(iter(dirs.values()))
        server, models, _ = start_vllm(first)
        if CONFIG.get("bench"):
            try:
                decode_bench()
            except Exception as e:
                log(f"decode bench failed: {e}")
        evs = {}
        for name, d in dirs.items():
            rdir = OUT / name
            rdir.mkdir(parents=True, exist_ok=True)
            evs[name] = (Evaluator(make_config(d, models, data_dir, rdir)), rdir)
        jobs = []
        only = {tuple(x) for x in CONFIG.get("only") or []}  # (variant, instance_id, rep) to run
        for rep in range(CONFIG.get("repeats", 1)):
            for t in tasks:
                for name, (ev, rdir) in evs.items():
                    if not only or (name, t.instance_id, rep) in only:
                        jobs.append((name, ev, t, rep, rdir))
        if CONFIG.get("shuffle_seed") is not None:  # no configuration always runs first on a task
            random.Random(CONFIG["shuffle_seed"]).shuffle(jobs)
        log(f"{len(jobs)} jobs")
        try:
            asyncio.run(run_jobs(jobs, CONFIG.get("concurrency", 2), deadline))
        finally:
            server.stop()
    summarize()


main()
