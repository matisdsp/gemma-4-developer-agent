"""Per-step decode latency vs batch size, local MLX (synthetic prompt, no competition data)."""
import sys, time, json, statistics as st
from mlx_lm import load, batch_generate
from mlx_lm.sample_utils import make_sampler
model_id = sys.argv[1]; gen = int(sys.argv[2])
model, tok = load(model_id)
msg = [{"role": "user", "content": "Write a very long, detailed Python tutorial about recursion with many code examples. Do not stop early."}]
base = tok.apply_chat_template(msg, add_generation_prompt=True)
sampler = make_sampler(temp=1.0)
batch_generate(model, tok, [base], max_tokens=32, sampler=sampler, verbose=False)  # warm-up
out = {}
for b in [1, 2, 4, 8, 16]:
    per_step = []
    for rep in range(3):
        t = time.time()
        r = batch_generate(model, tok, [base] * b, max_tokens=gen, sampler=sampler, verbose=False)
        dt = time.time() - t
        longest = max(len(tok.encode(x)) for x in r.texts)
        per_step.append(dt / max(longest, 1))
    out[b] = round(st.median(per_step) * 1000, 2)
    print(json.dumps({"batch": b, "ms_per_step_median": out[b], "rel_to_b1": round(out[b] / out[1], 2)}), flush=True)
print(json.dumps({"model": model_id, "max_new": gen, "ms_per_step": out}))
