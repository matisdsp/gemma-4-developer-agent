"""Per-task analysis: schema audit, gold, localizers, raw metrics, embedding-vs-lexical pairs."""
import collections
import json
import math
import random
import re
import sys
import zlib
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402
from lib import (DATA, ENGLISH_STOP, PY_BUILTIN, BM25, Repo, _IDENT, compute_gold, extract_tokens,  # noqa: E402
                 clean_path_tokens, map_nodes, split_ident_words)

DF_MAX_FRAC = 0.05  # identifiers appearing in >5% of all code units are "very common names"
K_LIST = 10


def load_task(iid):
    for l in open(DATA / "tasks.jsonl"):
        t = json.loads(l)
        if t["instance_id"] == iid:
            return t
    raise KeyError(iid)


def category(rel):
    parts = rel.split("/")
    if lib.is_test_path(rel):
        return "tests"
    top = parts[0]
    if top in ("docs_src", "docs", "scripts", "examples", "benchmarks", "tools", "docs_src"):
        return top
    return "package"


def bfs(adj, sources, maxd):
    dist = np.full(len(adj), -1, dtype=np.int32)
    q = collections.deque()
    for s in sources:
        if dist[s] < 0:
            dist[s] = 0
            q.append(s)
    while q:
        x = q.popleft()
        if dist[x] >= maxd:
            continue
        for y in adj[x]:
            if dist[y] < 0:
                dist[y] = dist[x] + 1
                q.append(y)
    return dist


def jacc(a, b):
    if not a and not b:
        return 0.0
    i = len(a & b)
    return i / (len(a) + len(b) - i)


def analyze(iid):
    T = load_task(iid)
    short = T["repo"].split("/")[1]
    stem = f"{short}_{T['base_commit']}"
    repo = Repo(iid)
    res = {"iid": iid, "repo": short, "year": T["created_at"][:4], "created_at": T["created_at"], "stem": stem}
    units = repo.units
    pool = [u for u in units if not u.is_test]
    pool_ids = [u.uid for u in pool]

    # ---------------- graph + embeddings
    g = json.load(open(DATA / "graphs" / f"{stem}.json"))
    nodes, edges = g["nodes"], g["edges"]
    N = len(nodes)
    nid = {n["id"]: i for i, n in enumerate(nodes)}
    ids = [n["id"] for n in nodes]
    z = np.load(DATA / "embeddings" / f"{stem}.npz")
    emb_keys = set(z.files)
    M = np.stack([z[i] if i in emb_keys else np.zeros(256, np.float32) for i in ids]).astype(np.float32)
    nrm = np.linalg.norm(M, axis=1, keepdims=True)
    nrm[nrm == 0] = 1.0
    M = M / nrm

    adj = [set() for _ in range(N)]
    deg = np.zeros(N, dtype=np.int64)
    etypes = collections.Counter()
    selfl = 0
    unresolved_edges = 0
    for e in edges:
        etypes[e["type"]] += 1
        a, b = nid.get(e["source"]), nid.get(e["target"])
        if a is None or b is None:
            unresolved_edges += 1
            continue
        if a == b:
            selfl += 1
        deg[a] += 1
        deg[b] += 1
        adj[a].add(b)
        adj[b].add(a)
    adj = [sorted(s) for s in adj]

    node_unit, node_status = map_nodes(repo, nodes)
    node_cat = []
    node_root = []
    for u in node_unit:
        if u is None:
            node_cat.append(None)
            node_root.append(None)
        else:
            f = units[u].file
            node_cat.append(category(f))
            node_root.append(f.split("/")[0] if f.split("/")[0] in ("src", "docs_src") else ".")
    unit_nodes = collections.defaultdict(list)
    for i, u in enumerate(node_unit):
        if u is not None:
            unit_nodes[u].append(i)

    # ---------------- schema audit
    last = [i.split(".")[-1] for i in ids]
    lc = collections.Counter(last)
    unit_cat = collections.Counter(category(u.file) for u in units)
    unit_cat_cov = collections.Counter(category(u.file) for u in units if u.uid in unit_nodes)
    files_cat = collections.Counter(category(rel) for rel in repo.files)
    files_cat_cov = collections.Counter(category(rel) for rel in repo.files
                                        if any(u in unit_nodes for u in repo.file_units[rel]))
    res["schema"] = {
        "n_nodes": N, "n_edges": len(edges), "edge_types": dict(etypes),
        "deg0_frac": float((deg == 0).mean()) if N else 0.0, "deg0": int((deg == 0).sum()),
        "self_loops": selfl, "unresolved_edges": unresolved_edges,
        "n_class_nodes": sum(1 for n in nodes if re.match(r"(@[^\n]*\n)*\s*class ", n["text"])),
        "status": dict(collections.Counter(node_status)),
        "n_mapped": sum(1 for u in node_unit if u is not None),
        "node_cat": dict(collections.Counter(c for c in node_cat if c)),
        "node_root": dict(collections.Counter(r for r in node_root if r)),
        "n_ids_with_shared_name": sum(1 for x in last if lc[x] > 1),
        "n_distinct_shared_names": sum(1 for x, c in lc.items() if c > 1),
        "n_units_mapped_distinct": len(unit_nodes),
        "units_total_by_cat": dict(unit_cat), "units_covered_by_cat": dict(unit_cat_cov),
        "files_total_by_cat": dict(files_cat), "files_covered_by_cat": dict(files_cat_cov),
        "n_units": len(units), "n_pool_units": len(pool),
        "async_units_total": sum(1 for u in units if u.is_async),
        "async_units_covered": sum(1 for u in units if u.is_async and u.uid in unit_nodes),
        "sync_func_units_total": sum(1 for u in units if u.kind == "func" and not u.is_async),
        "sync_func_units_covered": sum(1 for u in units if u.kind == "func" and not u.is_async and u.uid in unit_nodes),
        "pkg_async_total": sum(1 for u in units if u.is_async and category(u.file) == "package"),
        "pkg_async_covered": sum(1 for u in units if u.is_async and category(u.file) == "package" and u.uid in unit_nodes),
        "pkg_sync_total": sum(1 for u in units if u.kind == "func" and not u.is_async and category(u.file) == "package"),
        "pkg_sync_covered": sum(1 for u in units if u.kind == "func" and not u.is_async and category(u.file) == "package" and u.uid in unit_nodes),
        "pkg_class_total": sum(1 for u in units if u.kind == "class" and category(u.file) == "package"),
        "pkg_class_covered": sum(1 for u in units if u.kind == "class" and category(u.file) == "package" and u.uid in unit_nodes),
        "emb_missing": sum(1 for i in ids if i not in emb_keys),
        "emb_dim": int(M.shape[1]),
        "dup_edge_keys": sum(1 for e in edges if e.get("key", 0) != 0),
    }

    # ---------------- gold
    gold = compute_gold(repo, T["patch"])
    gold_units = [u for u in gold["gold_units"] if not units[u].is_test]
    gset = set(gold_units)
    res["gold"] = {
        "files_changed": gold["files_changed"], "gold_files": gold["gold_files"],
        "gold_units": [units[u].file + "::" + units[u].qn for u in gold_units],
        "gold_units_in_graph": [bool(unit_nodes.get(u)) for u in gold_units],
        "gold_units_kind": [units[u].kind for u in gold_units],
        "gold_units_async": [units[u].is_async for u in gold_units],
        "module_level_files": gold["module_level_files"], "new_files": gold["new_files"],
        "test_files": gold["test_files"], "nonpy_files": gold["nonpy_files"],
        "deleted_files": gold["deleted_files"],
        "only_new_files": bool(gold["new_files"]) and not gold["gold_files"],
        "gold_file_cats": [category(f) for f in gold["gold_files"]],
    }
    gold_files = set(gold["gold_files"])

    # ---------------- vocab statistics
    df_all = collections.Counter()
    for u in units:
        df_all.update(u.idents)
    NU = len(units)

    def idf(t):
        return math.log((NU + 1) / (df_all.get(t, 0) + 1))

    toks, raw_paths = extract_tokens(T["problem_statement"])
    path_tokens = clean_path_tokens(raw_paths)
    plain, dotted = [], []
    for t, kinds in toks.items():
        if "." in t:
            last_c = t.split(".")[-1]
            if len(last_c) >= 3 and last_c.lower() not in ENGLISH_STOP and last_c not in PY_BUILTIN \
                    and df_all.get(last_c, 0) / NU <= DF_MAX_FRAC and df_all.get(last_c, 0) > 0:
                dotted.append(t)
            continue
        if len(t) < 3 or t.lower() in ENGLISH_STOP or t in PY_BUILTIN:
            continue
        if df_all.get(t, 0) == 0 or df_all[t] / NU > DF_MAX_FRAC:
            continue
        plain.append(t)
    res["issue"] = {"n_raw_tokens": len(toks), "n_plain": len(plain), "n_dotted": len(dotted),
                    "plain": plain[:40], "dotted": dotted[:20], "paths": path_tokens[:10],
                    "len_chars": len(T["problem_statement"])}
    plain_set = set(plain)
    dot_last = {d.split(".")[-1] for d in dotted}

    # ---------------- (a) GREP
    inv = collections.defaultdict(list)
    for u in pool:
        for t in plain:
            if t in u.idents:
                inv[t].append(u.uid)
    uscore = {}
    for t in plain:
        for uid in inv[t]:
            d = uscore.setdefault(uid, [0, 0.0])
            d[0] += 1
            d[1] += idf(t)
    for d in dotted:
        for u in pool:
            if d in u.text:
                e = uscore.setdefault(u.uid, [0, 0.0])
                e[0] += 1
                e[1] += idf(d.split(".")[-1])
    for uid in list(uscore):
        u = units[uid]
        if u.name in plain_set or u.name in dot_last:
            uscore[uid][0] += 3
    grep_units = sorted(uscore, key=lambda x: (-uscore[x][0], -uscore[x][1], units[x].file, units[x].start))
    # file grep
    fscore = {}
    for rel in sorted(repo.files):
        if lib.is_test_path(rel):
            continue
        fi = repo.files[rel]
        fid = set(_IDENT.findall(fi.src))
        m = [t for t in plain if t in fid]
        md = [d for d in dotted if d in fi.src]
        sc = len(m) + len(md)
        ids_ = sum(idf(t) for t in m) + sum(idf(d.split(".")[-1]) for d in md)
        names = {units[x].name for x in repo.file_units[rel]}
        sc += 3 * sum(1 for t in plain_set if t in names)
        base = rel.split("/")[-1]
        for p in path_tokens:
            if "/" in p:
                if rel.endswith(p):
                    sc += 3
                    break
            elif base == p:
                sc += 3
                break
        if sc > 0:
            fscore[rel] = (sc, ids_)
    grep_files = sorted(fscore, key=lambda r: (-fscore[r][0], -fscore[r][1], r))

    # ---------------- (b) BM25
    docs = [lib.split_ident_words(u.text) for u in pool]
    bm = BM25(docs)
    qterms = [w for w in lib.split_ident_words(lib._RE_URL.sub(" ", T["problem_statement"])) if w not in ENGLISH_STOP]
    bsc = bm.scores(qterms)
    bm_score = {pool[i].uid: float(bsc[i]) for i in range(len(pool))}
    order = sorted((i for i in range(len(pool)) if bsc[i] > 0), key=lambda i: (-bsc[i], pool[i].uid))
    bm25_units = [pool[i].uid for i in order]

    def bm_key(uid):
        return (-bm_score.get(uid, 0.0), uid)

    # ---------------- seeds
    last_idx = collections.defaultdict(list)
    for i, l in enumerate(last):
        last_idx[l].append(i)
    seeds_by_token = collections.OrderedDict()
    for t in plain:
        c = last_idx.get(t, [])
        if c:
            seeds_by_token[t] = c
    for d in dotted:
        c = [i for i in last_idx.get(d.split(".")[-1], []) if ids[i] == d or ids[i].endswith("." + d)]
        if c:
            seeds_by_token[d] = c
    seed_nodes = sorted({i for c in seeds_by_token.values() for i in c})
    # S3: <=3 seed nodes, most specific tokens first, prefer non-test
    s3 = []
    for t, c in sorted(seeds_by_token.items(), key=lambda kv: (len(kv[1]), list(seeds_by_token).index(kv[0]))):
        cc = sorted(c, key=lambda i: (lib.is_test_path(units[node_unit[i]].file) if node_unit[i] is not None else True, ids[i]))
        if cc[0] not in s3:
            s3.append(cc[0])
        if len(s3) == 3:
            break
    res["seeds"] = {"n_tokens_with_node": len(seeds_by_token), "n_seed_nodes": len(seed_nodes),
                    "n_seed_nodes_nontest": sum(1 for i in seed_nodes if node_unit[i] is not None and not units[node_unit[i]].is_test),
                    "s3": [ids[i] for i in s3], "tok_nodes": {t: len(c) for t, c in list(seeds_by_token.items())[:15]}}

    def unit_dist(srcs, maxd):
        dist = bfs(adj, srcs, maxd)
        ud = {}
        for i in range(N):
            if dist[i] >= 0 and node_unit[i] is not None:
                u = node_unit[i]
                if u not in ud or dist[i] < ud[u]:
                    ud[u] = int(dist[i])
        return ud

    def nontest(uid):
        return not units[uid].is_test

    def graph_lists(srcs):
        if not srcs:
            return {k: [] for k in ("SEEDS", "G1", "G2", "G1x", "G2x")}, {}
        ud = unit_dist(srcs, 2)
        c = {u: d for u, d in ud.items() if nontest(u)}
        key = lambda u: (c[u], bm_key(u))  # noqa: E731
        out = {}
        out["SEEDS"] = sorted([u for u in c if c[u] == 0], key=bm_key)
        out["G1"] = sorted([u for u in c if c[u] <= 1], key=key)
        out["G2"] = sorted([u for u in c if c[u] <= 2], key=key)
        out["G1x"] = sorted([u for u in c if c[u] == 1], key=bm_key)
        out["G2x"] = sorted([u for u in c if 1 <= c[u] <= 2], key=key)
        return out, c

    def emb_list(srcs):
        if not srcs:
            return [], {}
        S = M[srcs]
        sims = S @ M.T  # (S, N)
        best = {}
        topn = {}
        seed_units = {node_unit[i] for i in srcs if node_unit[i] is not None}
        for r, s in enumerate(srcs):
            row = sims[r].copy()
            row[s] = -9
            idx = np.argsort(-row, kind="stable")[:K_LIST]
            topn[s] = [int(i) for i in idx]
            for i in idx:
                u = node_unit[i]
                if u is None or not nontest(u) or u in seed_units:
                    continue
                v = float(row[i])
                if u not in best or v > best[u]:
                    best[u] = v
        lst = sorted(best, key=lambda u: (-best[u], u))
        return lst, topn

    GL, cdist = graph_lists(seed_nodes)
    GL3, cdist3 = graph_lists(s3)
    EMB, emb_top = emb_list(seed_nodes)
    EMB3, _ = emb_list(s3)

    # (e) hybrid: neighbours of grep top-3 functions
    top3 = grep_units[:3]
    hyb_nodes = [i for u in top3 for i in unit_nodes.get(u, [])]
    hyb = {}
    for i in hyb_nodes:
        for j in adj[i]:
            u = node_unit[j]
            if u is not None and nontest(u) and u not in set(grep_units[:K_LIST]):
                hyb[u] = 1
    HYBn = sorted(hyb, key=bm_key)

    lists = collections.OrderedDict()
    lists["GREP"] = grep_units
    lists["BM25"] = bm25_units
    lists["SEEDS"] = GL["SEEDS"]
    lists["G1"] = GL["G1"]
    lists["G2"] = GL["G2"]
    lists["G1x"] = GL["G1x"]
    lists["G2x"] = GL["G2x"]
    lists["EMB"] = EMB
    lists["G1_s3"] = GL3["G1"]
    lists["EMB_s3"] = EMB3
    lists["HYBn"] = HYBn
    lists["HYB"] = grep_units[:K_LIST] + HYBn

    def file_order(lst):
        out, seen = [], set()
        for u in lst:
            f = units[u].file
            if f not in seen:
                seen.add(f)
                out.append(f)
        return out

    def cost(lst):
        return sum(len(units[u].text) for u in lst) / 4.0

    def merged10(x):
        out, seen = [], set()
        a, b = grep_units, x
        i = j = 0
        while len(out) < K_LIST and (i < len(a) or j < len(b)):
            if i < len(a):
                if a[i] not in seen:
                    seen.add(a[i]); out.append(a[i])
                i += 1
            if len(out) < K_LIST and j < len(b):
                if b[j] not in seen:
                    seen.add(b[j]); out.append(b[j])
                j += 1
        return out

    gset_s = gset
    methods = {}
    for name, lst in lists.items():
        d = {"n": len(lst), "tok_set": cost(lst), "tok_top10": cost(lst[:K_LIST])}
        pos = [i + 1 for i, u in enumerate(lst) if u in gset_s]
        d["gold_ranks"] = pos[:20]
        d["first_gold"] = pos[0] if pos else None
        d["n_gold_top5"] = sum(1 for p in pos if p <= 5)
        d["n_gold_top10"] = sum(1 for p in pos if p <= 10)
        d["n_gold_set"] = len(pos)
        fl = file_order(lst)
        fp = [i + 1 for i, f in enumerate(fl) if f in gold_files]
        d["first_gold_file"] = fp[0] if fp else None
        d["n_files"] = len(fl)
        if name not in ("GREP", "BM25", "HYB"):
            m10 = merged10(lst)
            d["merged10_hit"] = any(u in gset_s for u in m10)
            d["merged10_ngold"] = sum(1 for u in m10 if u in gset_s)
        methods[name] = d
    # file-level grep
    fp = [i + 1 for i, f in enumerate(grep_files) if f in gold_files]
    methods["GREPf"] = {"first_gold_file": fp[0] if fp else None, "n_files": len(grep_files)}
    res["methods"] = methods

    # reachability: min graph distance from seeds (undirected) to gold units
    def reach(srcs):
        if not srcs:
            return {"dists": [None] * len(gold_units)}
        dist = bfs(adj, srcs, 10)
        out = []
        for u in gold_units:
            ns = unit_nodes.get(u, [])
            if not ns:
                out.append("no_node")
                continue
            ds = [int(dist[i]) for i in ns if dist[i] >= 0]
            out.append(min(ds) if ds else "unreachable")
        return {"dists": out}

    res["reach_all"] = reach(seed_nodes)
    res["reach_s3"] = reach(s3)
    res["reach_grep3"] = reach(hyb_nodes)

    # token counts to give context
    res["grep_n_units"] = len(grep_units)
    res["n_gold_units"] = len(gold_units)
    res["n_gold_files"] = len(gold_files)

    # sanity listings
    def names(lst, k=10):
        return [units[u].file + "::" + units[u].qn for u in lst[:k]]
    res["top"] = {k: names(v) for k, v in lists.items() if k != "HYB"}
    res["top"]["GREPf"] = grep_files[:10]

    # ---------------- embedding vs lexical
    rng = random.Random(zlib.crc32(iid.encode()))
    tcache = {}

    def toks_text(i):
        if i not in tcache:
            tcache[i] = frozenset(split_ident_words(nodes[i]["text"]))
        return tcache[i]

    ncache = {}

    def toks_name(i):
        if i not in ncache:
            ncache[i] = frozenset(split_ident_words(ids[i]))
        return ncache[i]

    cr, jr, nr = [], [], []
    if N > 5:
        for _ in range(3000):
            a = rng.randrange(N)
            b = rng.randrange(N)
            if a == b:
                continue
            cr.append(float(M[a] @ M[b]))
            jr.append(jacc(toks_text(a), toks_text(b)))
            nr.append(jacc(toks_name(a), toks_name(b)))
    cs, js, ns = [], [], []
    for s in seed_nodes[:20]:
        for j in emb_top.get(s, []):
            cs.append(float(M[s] @ M[j]))
            js.append(jacc(toks_text(s), toks_text(j)))
            ns.append(jacc(toks_name(s), toks_name(j)))
    # overlap of embedding top-10 with lexical top-10 / top-50 (text Jaccard) for up to 5 seeds
    post = None
    ov = []
    for s in seed_nodes[:5]:
        if post is None:
            post_d = collections.defaultdict(list)
            for i in range(N):
                for t in toks_text(i):
                    post_d[t].append(i)
            post = {t: np.array(v) for t, v in post_d.items()}
            sizes = np.array([len(toks_text(i)) for i in range(N)], dtype=np.float64)
        ts = toks_text(s)
        inter = np.zeros(N)
        for t in ts:
            if t in post:
                inter[post[t]] += 1
        jac = inter / np.maximum(1e-9, len(ts) + sizes - inter)
        jac[s] = -1
        lex = np.argsort(-jac, kind="stable")[:50]
        e10 = set(emb_top[s])
        ov.append({"ov10": len(e10 & set(int(i) for i in lex[:10])), "ov50": len(e10 & set(int(i) for i in lex[:50])),
                   "jac_top10_mean": float(jac[lex[:10]].mean()), "n": N})
    # --- what does the embedding encode? cosine of structurally related pairs vs random
    def mean_pairs(prs):
        return [round(float(M[a] @ M[b]), 5) for a, b in prs]

    uniq_edges = sorted({(min(a, b), max(a, b)) for a in range(N) for b in adj[a] if a != b})
    ep = rng.sample(uniq_edges, min(2000, len(uniq_edges))) if uniq_edges else []

    def group_pairs(keyf, k=2000):
        grp = collections.defaultdict(list)
        for i in range(N):
            kk = keyf(i)
            if kk is not None:
                grp[kk].append(i)
        gl = [v for _, v in sorted(grp.items(), key=lambda kv: str(kv[0])) if len(v) > 1]
        out = []
        if gl:
            for _ in range(k):
                v = rng.choice(gl)
                a, b = rng.sample(v, 2)
                out.append((a, b))
        return out, sum(len(v) for v in gl)

    sf_pairs, _ = group_pairs(lambda i: units[node_unit[i]].file if node_unit[i] is not None else None)
    sn_pairs, n_sharedname = group_pairs(lambda i: last[i])
    it_pairs, n_duptext = group_pairs(lambda i: nodes[i]["text"])
    res["emb_struct"] = {
        "cos_edge": mean_pairs(ep), "cos_same_file": mean_pairs(sf_pairs), "cos_same_name": mean_pairs(sn_pairs),
        "cos_same_text": mean_pairs(it_pairs), "n_nodes_dup_text": n_duptext, "n": N,
    }
    comp = collections.Counter()
    for s_ in seed_nodes[:20]:
        for j in emb_top.get(s_, []):
            comp["total"] += 1
            c_ = node_cat[j] if node_cat[j] else "unmapped"
            comp["cat_" + c_] += 1
            comp["same_name"] += last[j] == last[s_]
            comp["same_file"] += (node_unit[j] is not None and node_unit[s_] is not None
                                   and units[node_unit[j]].file == units[node_unit[s_]].file)
            comp["same_text"] += nodes[j]["text"] == nodes[s_]["text"]
            comp["jt_ge_08"] += jacc(toks_text(s_), toks_text(j)) >= 0.8
    res["emb_nb_comp"] = dict(comp)
    res["emb_lex"] = {
        "rand_cos": [round(x, 5) for x in cr], "rand_jt": [round(x, 5) for x in jr], "rand_jn": [round(x, 5) for x in nr],
        "nb_cos": [round(x, 5) for x in cs], "nb_jt": [round(x, 5) for x in js], "nb_jn": [round(x, 5) for x in ns],
        "overlap": ov,
    }
    return res


if __name__ == "__main__":
    import time
    iid = sys.argv[1]
    t = time.time()
    r = analyze(iid)
    print(time.time() - t)
    print(json.dumps({k: v for k, v in r.items() if k not in ("emb_lex",)}, indent=1)[:6000])
