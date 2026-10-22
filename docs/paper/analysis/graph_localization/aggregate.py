"""Aggregate per-task JSON into tables (out/summary.md, out/summary.json, out/task_table.csv)."""
import collections
import csv
import glob
import json
import statistics as st
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402

OUT = lib.OUT
UNIT_METHODS = ["GREP", "BM25", "SEEDS", "G1", "G2", "G1x", "G2x", "EMB", "G1_s3", "EMB_s3", "HYBn", "HYB"]
EXPANSIONS = ["SEEDS", "G1", "G2", "G1x", "G2x", "EMB", "G1_s3", "EMB_s3", "HYBn"]
FILE_METHODS = ["GREPf", "GREP", "BM25", "SEEDS", "G1", "G2", "EMB", "HYB"]


def kn(k, n):
    return f"{k}/{n}" + (f" ({100 * k / n:.0f}%)" if n else "")


def med(x):
    return st.median(x) if x else float("nan")


def load():
    R = [json.load(open(f)) for f in sorted(glob.glob(str(OUT / "per_task" / "*.json")))]
    return R


def fn_metrics(R, m):
    n = len(R)
    a5 = sum(1 for r in R if (r["methods"][m]["first_gold"] or 10**9) <= 5)
    a10 = sum(1 for r in R if (r["methods"][m]["first_gold"] or 10**9) <= 10)
    rec = np.mean([r["methods"][m]["n_gold_top10"] / r["n_gold_units"] for r in R]) if n else float("nan")
    hit = sum(1 for r in R if r["methods"][m]["n_gold_set"] > 0)
    ne = sum(1 for r in R if r["methods"][m]["n"] > 0)
    ne_r = [r for r in R if r["methods"][m]["n"] > 0]
    sizes = [r["methods"][m]["n"] for r in ne_r]
    tok = [r["methods"][m]["tok_set"] for r in ne_r]
    tok10 = [r["methods"][m]["tok_top10"] for r in ne_r]
    return dict(n=n, a5=a5, a10=a10, rec10=float(rec), hit_set=hit, nonempty=ne, med_set=med(sizes),
                mean_set=float(np.mean(sizes)) if sizes else float("nan"),
                med_tok_set=med(tok), med_tok_top10=med(tok10))


def file_metrics(R, m):
    n = len(R)
    f = [r["methods"][m]["first_gold_file"] for r in R]
    return dict(n=n, a1=sum(1 for x in f if x is not None and x <= 1), a5=sum(1 for x in f if x is not None and x <= 5))


def table_fn(R, methods=UNIT_METHODS):
    lines = ["| method | Acc@5 | Acc@10 | Recall@10 | gold in set | non-empty | med \|set\| (non-empty) | med tokens(set) (non-empty) | med tokens(top10) (non-empty) |",
             "|---|---|---|---|---|---|---|---|---|"]
    out = {}
    for m in methods:
        d = fn_metrics(R, m)
        out[m] = d
        lines.append(f"| {m} | {kn(d['a5'], d['n'])} | {kn(d['a10'], d['n'])} | {d['rec10']:.3f} | {kn(d['hit_set'], d['n'])} | "
                     f"{kn(d['nonempty'], d['n'])} | {d['med_set']:.0f} | {d['med_tok_set']:.0f} | {d['med_tok_top10']:.0f} |")
    return "\n".join(lines), out


def table_file(R, methods=FILE_METHODS):
    lines = ["| method | file Acc@1 | file Acc@5 |", "|---|---|---|"]
    out = {}
    for m in methods:
        d = file_metrics(R, m)
        out[m] = d
        lines.append(f"| {m} | {kn(d['a1'], d['n'])} | {kn(d['a5'], d['n'])} |")
    return "\n".join(lines), out


def marginal(E):
    miss = [r for r in E if (r["methods"]["GREP"]["first_gold"] or 10**9) > 10]
    hit = [r for r in E if (r["methods"]["GREP"]["first_gold"] or 10**9) <= 10]
    lines = [f"Tasks where GREP top-10 misses all gold units: {len(miss)}/{len(E)}; GREP top-10 hit: {len(hit)}/{len(E)}", "",
             "| expansion | recovers in top-10 (of grep-misses) | gold anywhere in set | non-empty set | med \\|set\\| (non-empty) | med tokens(set) (non-empty) | med tokens(set) (recovered) | med tokens(top10) (recovered in top-10) | merged-10 hit among grep-misses | displaces grep hit (merged-10 loses, of grep-hits) |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    out = {}
    for m in EXPANSIONS + ["BM25"]:
        rec10 = [r for r in miss if (r["methods"][m]["first_gold"] or 10**9) <= 10]
        recset = [r for r in miss if r["methods"][m]["n_gold_set"] > 0]
        nem = [r for r in miss if r["methods"][m]["n"] > 0]
        tok_all = [r["methods"][m]["tok_set"] for r in nem]
        tok_rec = [r["methods"][m]["tok_set"] for r in recset]
        tok10_rec = [r["methods"][m]["tok_top10"] for r in rec10]
        sz = [r["methods"][m]["n"] for r in nem]
        if m != "BM25":
            mrg = sum(1 for r in miss if r["methods"][m]["merged10_hit"])
            disp = sum(1 for r in hit if not r["methods"][m]["merged10_hit"])
            mrg_s, disp_s = kn(mrg, len(miss)), kn(disp, len(hit))
        else:
            mrg, disp, mrg_s, disp_s = None, None, "-", "-"
        lines.append(f"| {m} | {kn(len(rec10), len(miss))} | {kn(len(recset), len(miss))} | {kn(len(nem), len(miss))} | {med(sz):.0f} | {med(tok_all):.0f} | "
                     f"{med(tok_rec):.0f} | {med(tok10_rec):.0f} | {mrg_s} | {disp_s} |")
        out[m] = dict(miss=len(miss), rec10=len(rec10), recset=len(recset), merged=mrg, displaced=disp, hits=len(hit),
                      med_tok_all=med(tok_all), med_tok_rec=med(tok_rec), med_tok10_rec=med(tok10_rec), med_set=med(sz), nonempty=len(nem),
                      rec_ids=[r["iid"] for r in recset])
    # union
    anyg = [r for r in miss if any((r["methods"][m]["first_gold"] or 10**9) <= 10 for m in ("G1x", "G2x", "EMB", "HYBn"))]
    anyset = [r for r in miss if any(r["methods"][m]["n_gold_set"] > 0 for m in ("G1x", "G2x", "EMB", "HYBn"))]
    lines.append("")
    lines.append(f"Union of expansion-only lists (G1x, G2x, EMB, HYBn): top-10 recovers {kn(len(anyg), len(miss))}, anywhere in set {kn(len(anyset), len(miss))} of grep-misses.")
    out["union_expansion_only"] = dict(top10=len(anyg), anyset=len(anyset), miss=len(miss), ids=[r["iid"] for r in anyset])
    # gold not even graph node among grep misses
    gn = sum(1 for r in miss if not any(r["gold"]["gold_units_in_graph"]))
    lines.append(f"Among grep-misses, tasks where no gold unit is a graph node: {kn(gn, len(miss))}.")
    out["miss_no_gold_node"] = gn
    return "\n".join(lines), out


def reach_table(E):
    lines = ["| source of seeds | no seeds | gold not a graph node | dist 0 | dist 1 | dist 2 | dist 3+ | unreachable | reachable <=1 | reachable <=2 |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    out = {}
    for key, label in (("reach_all", "issue-token seeds (all)"), ("reach_s3", "issue-token seeds (<=3 nodes)"),
                       ("reach_grep3", "grep top-3 units")):
        c = collections.Counter()
        for r in E:
            d = r[key]["dists"]
            if all(x is None for x in d):
                c["no_seeds"] += 1
                continue
            nums = [x for x in d if isinstance(x, int)]
            if nums:
                m = min(nums)
                c[str(m) if m <= 2 else "3+"] += 1
            elif all(x == "no_node" for x in d):
                c["not_node"] += 1
            else:
                c["unreach"] += 1
        n = len(E)
        le1 = c["0"] + c["1"]
        le2 = le1 + c["2"]
        lines.append(f"| {label} | {kn(c['no_seeds'], n)} | {kn(c['not_node'], n)} | {kn(c['0'], n)} | {kn(c['1'], n)} | {kn(c['2'], n)} | "
                     f"{kn(c['3+'], n)} | {kn(c['unreach'], n)} | {kn(le1, n)} | {kn(le2, n)} |")
        out[key] = dict(c, n=n, le1=le1, le2=le2)
    return "\n".join(lines), out


def emb_lex(R):
    out = {}
    lines = ["| subset | pairs | Spearman(cos, text-Jaccard) | Spearman(cos, name-Jaccard) | frac text-Jaccard=0 | median per-graph rho (text) [IQR] |",
             "|---|---|---|---|---|---|"]
    seen = set()
    U = []
    for r in R:  # one entry per distinct graph
        if r["stem"] in seen:
            continue
        seen.add(r["stem"])
        U.append(r)

    def block(label, ck, jk, nk, rows):
        c = np.concatenate([np.array(r["emb_lex"][ck]) for r in rows]) if rows else np.array([])
        j = np.concatenate([np.array(r["emb_lex"][jk]) for r in rows]) if rows else np.array([])
        nn = np.concatenate([np.array(r["emb_lex"][nk]) for r in rows]) if rows else np.array([])
        per = []
        for r in rows:
            cc, jj = r["emb_lex"][ck], r["emb_lex"][jk]
            if len(cc) >= 30:
                v = lib.spearman(cc, jj)
                if v == v:
                    per.append(v)
        rho = lib.spearman(c, j) if len(c) > 2 else float("nan")
        rhon = lib.spearman(c, nn) if len(c) > 2 else float("nan")
        z = float((j == 0).mean()) if len(j) else float("nan")
        q = np.percentile(per, [25, 75]) if per else [float("nan")] * 2
        lines.append(f"| {label} | {len(c)} | {rho:.3f} | {rhon:.3f} | {z:.3f} | {med(per):.3f} [{q[0]:.3f}, {q[1]:.3f}] |")
        out[label] = dict(pairs=int(len(c)), rho_text=rho, rho_name=rhon, frac_zero=z, per_graph_med=med(per))

    block("random node pairs (all graphs)", "rand_cos", "rand_jt", "rand_jn", U)
    for repo in ("fastapi", "rich", "requests", "httpx"):
        block(f"random pairs, {repo}", "rand_cos", "rand_jt", "rand_jn", [r for r in U if r["repo"] == repo])
    block("seed->emb-neighbour pairs (all tasks)", "nb_cos", "nb_jt", "nb_jn", R)
    for repo in ("fastapi", "rich", "requests"):
        block(f"seed-neighbour pairs, {repo}", "nb_cos", "nb_jt", "nb_jn", [r for r in R if r["repo"] == repo])
    ov = [o for r in R for o in r["emb_lex"]["overlap"]]
    if ov:
        n10 = np.mean([o["ov10"] for o in ov]) / 10
        n50 = np.mean([o["ov50"] for o in ov]) / 10
        rnd = np.mean([10 / o["n"] * 10 / 10 for o in ov])
        lines.append("")
        lines.append(f"Embedding top-10 vs lexical (text-Jaccard) rankings over {len(ov)} seeds: mean overlap with lexical top-10 = {n10:.3f} of the 10 embedding neighbours; "
                     f"inside lexical top-50 = {n50:.3f}; random-chance overlap with a top-10 = {rnd:.4f}. "
                     f"Mean text-Jaccard of the lexical top-10 neighbours = {np.mean([o['jac_top10_mean'] for o in ov]):.3f}.")
        out["overlap"] = dict(n=len(ov), ov10=float(n10), ov50=float(n50), chance10=float(rnd))
    lines.append("")
    lines.append("What cosine encodes (one entry per distinct graph; mean / median cosine; random pairs above):")
    lines.append("")
    lines.append("| pair type | n pairs | mean cos | median cos | P(cos > random-pair cos) |")
    lines.append("|---|---|---|---|---|")
    rc = np.concatenate([np.array(r["emb_lex"]["rand_cos"]) for r in U])
    rcs = np.sort(rc)
    for lab, key in (("random", None), ("call-edge endpoints", "cos_edge"), ("same file", "cos_same_file"),
                     ("same short name", "cos_same_name"), ("identical node text", "cos_same_text")):
        arr = rc if key is None else np.concatenate([np.array(r["emb_struct"][key]) for r in U])
        if len(arr) == 0:
            continue
        auc = float(np.searchsorted(rcs, arr, side="left").mean() / len(rcs) + 0.0)
        lines.append(f"| {lab} | {len(arr)} | {arr.mean():.3f} | {np.median(arr):.3f} | {auc:.3f} |")
        out["struct_" + lab] = dict(n=int(len(arr)), mean=float(arr.mean()), median=float(np.median(arr)), auc=auc)
    nd = sum(r["emb_struct"]["n_nodes_dup_text"] for r in U)
    nn = sum(r["emb_struct"]["n"] for r in U)
    lines.append("")
    lines.append(f"Nodes whose exact text is shared with another node: {kn(nd, nn)}.")
    comp = collections.Counter()
    for r in R:
        comp.update(r["emb_nb_comp"])
    t = comp["total"]
    if t:
        lines.append(f"Composition of the embedding top-10 neighbours of issue seeds ({t} neighbours over {sum(1 for r in R if r['emb_nb_comp'])} tasks): "
                     + ", ".join(f"{k[4:]} {kn(v, t)}" for k, v in sorted(comp.items()) if k.startswith("cat_"))
                     + f"; same short name as the seed {kn(comp['same_name'], t)}; same file {kn(comp['same_file'], t)}; identical text {kn(comp['same_text'], t)}; text-Jaccard>=0.8 {kn(comp['jt_ge_08'], t)}.")
        out["nb_comp"] = dict(comp)
    cos_all = np.concatenate([np.array(r["emb_lex"]["rand_cos"]) for r in U])
    cos_nb = np.concatenate([np.array(r["emb_lex"]["nb_cos"]) for r in R]) if R else np.array([])
    lines.append(f"Cosine: random pairs mean {cos_all.mean():.3f} (p5 {np.percentile(cos_all,5):.3f}, p95 {np.percentile(cos_all,95):.3f}); "
                 f"seed-neighbour pairs mean {cos_nb.mean():.3f} (p5 {np.percentile(cos_nb,5):.3f}, p95 {np.percentile(cos_nb,95):.3f}).")
    return "\n".join(lines), out


def schema(R):
    seen, U = set(), []
    for r in R:
        if r["stem"] not in seen:
            seen.add(r["stem"])
            U.append(r)
    S = [r["schema"] for r in U]
    out = {"n_graphs": len(U)}
    L = []
    L.append(f"Distinct graphs: {len(U)} (tasks: {len(R)}); per-repo: {dict(collections.Counter(r['repo'] for r in U))}")
    for repo in ("fastapi", "rich", "requests", "httpx"):
        s = [r["schema"] for r in U if r["repo"] == repo]
        if not s:
            continue
        L.append(f"- {repo}: nodes median {med([x['n_nodes'] for x in s]):.0f} (min {min(x['n_nodes'] for x in s)}, max {max(x['n_nodes'] for x in s)}), "
                 f"edges median {med([x['n_edges'] for x in s]):.0f}, deg-0 fraction median {med([x['deg0_frac'] for x in s]):.3f}, "
                 f"mean degree-0 (min..max) {min(x['deg0_frac'] for x in s):.3f}..{max(x['deg0_frac'] for x in s):.3f}")
    et = collections.Counter()
    for s in S:
        et.update(s["edge_types"])
    L.append(f"Edge types (all graphs): {dict(et)}; self-loops total {sum(s['self_loops'] for s in S)}; unresolved edge endpoints {sum(s['unresolved_edges'] for s in S)}; "
             f"edges with key>0 (parallel edges) {sum(s['dup_edge_keys'] for s in S)}")
    tot_n = sum(s["n_nodes"] for s in S)
    tot_e = sum(s["n_edges"] for s in S)
    L.append(f"Total nodes {tot_n}, edges {tot_e}; deg-0 nodes {sum(s['deg0'] for s in S)} ({100*sum(s['deg0'] for s in S)/tot_n:.1f}%); class nodes {sum(s['n_class_nodes'] for s in S)} ({100*sum(s['n_class_nodes'] for s in S)/tot_n:.1f}%); nodes without embedding {sum(s['emb_missing'] for s in S)}")
    stc = collections.Counter()
    for s in S:
        stc.update(s["status"])
    mapped = sum(s["n_mapped"] for s in S)
    L.append(f"Node->(file,lines) mapping: {mapped}/{tot_n} ({100*mapped/tot_n:.2f}%) via ast. Status: {dict(stc)}")
    L.append(f"Node file root (resolved file under): {dict(sum((collections.Counter(s['node_root']) for s in S), collections.Counter()))}")
    nc = sum((collections.Counter(s["node_cat"]) for s in S), collections.Counter())
    L.append(f"Nodes by file category: {dict(nc)}")
    ut = sum((collections.Counter(s["units_total_by_cat"]) for s in S), collections.Counter())
    uc = sum((collections.Counter(s["units_covered_by_cat"]) for s in S), collections.Counter())
    L.append("Coverage of snapshot code units (function/method/class incl. nested-in-function folded into parent) by graph nodes, by category: "
             + ", ".join(f"{c}: {kn(uc[c], ut[c])}" for c in sorted(ut)))
    ft = sum((collections.Counter(s["files_total_by_cat"]) for s in S), collections.Counter())
    fc = sum((collections.Counter(s["files_covered_by_cat"]) for s in S), collections.Counter())
    L.append("Coverage of .py files (>=1 node): " + ", ".join(f"{c}: {kn(fc[c], ft[c])}" for c in sorted(ft)))
    L.append(f"Async functions (async def) covered by a node: {kn(sum(s['async_units_covered'] for s in S), sum(s['async_units_total'] for s in S))}; "
             f"sync def covered: {kn(sum(s['sync_func_units_covered'] for s in S), sum(s['sync_func_units_total'] for s in S))}")
    L.append(f"Main-package (non-test, non-docs) units covered: async {kn(sum(s['pkg_async_covered'] for s in S), sum(s['pkg_async_total'] for s in S))}, "
             f"sync def {kn(sum(s['pkg_sync_covered'] for s in S), sum(s['pkg_sync_total'] for s in S))}, "
             f"class {kn(sum(s['pkg_class_covered'] for s in S), sum(s['pkg_class_total'] for s in S))}")
    sh = sum(s["n_ids_with_shared_name"] for s in S)
    L.append(f"Ambiguous short names: nodes whose last component is shared with >=1 other node {kn(sh, tot_n)}; node ids are unique (duplicates: 0 by construction of the id list)")
    for repo in ("fastapi", "rich", "requests", "httpx"):
        s = [r["schema"] for r in U if r["repo"] == repo]
        if s:
            L.append(f"  - {repo}: {kn(sum(x['n_ids_with_shared_name'] for x in s), sum(x['n_nodes'] for x in s))} nodes share a short name")
    out.update(totals=dict(nodes=tot_n, edges=tot_e, mapped=mapped), status=dict(stc), node_cat=dict(nc), units=dict(total=dict(ut), covered=dict(uc)))
    return "\n".join(L), out


def gold_table(R):
    n = len(R)
    c = collections.Counter()
    gu = 0
    gin = 0
    gasync = 0
    gasync_in = 0
    kinds = collections.Counter()
    cats = collections.Counter()
    for r in R:
        g = r["gold"]
        c["with_gold_unit"] += bool(g["gold_units"])
        c["with_gold_file"] += bool(g["gold_files"])
        c["only_new_files"] += g["only_new_files"]
        c["any_new_file"] += bool(g["new_files"])
        c["any_module_level"] += bool(g["module_level_files"])
        c["gold_file_but_only_module_level"] += bool(g["gold_files"]) and not g["gold_units"]
        c["all_gold_in_graph"] += bool(g["gold_units"]) and all(g["gold_units_in_graph"])
        c["any_gold_in_graph"] += any(g["gold_units_in_graph"])
        c["none_gold_in_graph"] += bool(g["gold_units"]) and not any(g["gold_units_in_graph"])
        gu += len(g["gold_units"])
        gin += sum(g["gold_units_in_graph"])
        for k, a, i in zip(g["gold_units_kind"], g.get("gold_units_async", [False] * len(g["gold_units"])), g["gold_units_in_graph"]):
            kinds[k] += 1
            if a:
                gasync += 1
                gasync_in += i
        cats.update(g["gold_file_cats"])
    L = [f"Tasks: {n}. With >=1 gold unit in existing non-test .py: {kn(c['with_gold_unit'], n)}; with >=1 gold file: {kn(c['with_gold_file'], n)}; "
         f"patch only adds new .py files (no base location): {kn(c['only_new_files'], n)}; any new .py file: {kn(c['any_new_file'], n)}; "
         f"any module-level hunk: {kn(c['any_module_level'], n)}; gold file but only module-level hunks: {kn(c['gold_file_but_only_module_level'], n)}.",
         f"Gold units total {gu} (kinds {dict(kinds)}); in graph {kn(gin, gu)}; async gold units {gasync}, of which graph nodes {gasync_in}. "
         f"Tasks with all/any/none of their gold units as graph nodes (of tasks with gold units): {c['all_gold_in_graph']}/{c['any_gold_in_graph']}/{c['none_gold_in_graph']} of {c['with_gold_unit']}.",
         f"Gold file categories (file-level, non-test existing): {dict(cats)}"]
    return "\n".join(L)


def strat(E, key):
    vals = sorted({r[key] for r in E})
    L = []
    out = {}
    for v in vals:
        sub = [r for r in E if r[key] == v]
        t, o = table_fn(sub, ["GREP", "BM25", "SEEDS", "G1", "G2", "EMB", "HYB"])
        mt, mo = marginal(sub)
        tf, of = table_file(sub, ["GREPf", "GREP", "BM25", "G2", "EMB", "HYB"])
        L.append(f"#### {key} = {v} (n={len(sub)})\n\n{t}\n\n{tf}\n\n{mt}\n")
        out[v] = dict(fn=o, file=of, marginal={k: x for k, x in mo.items() if isinstance(x, dict) and "rec_ids" not in x}, n=len(sub))
    return "\n".join(L), out


def main():
    R = load()
    E = [r for r in R if r["n_gold_units"] > 0]
    F = [r for r in R if r["n_gold_files"] > 0]
    md = []
    summ = {}
    md.append("# Offline analysis: what does the code graph / embedding add beyond grep?\n")
    md.append(f"Tasks: {len(R)}. Eval set E (>=1 gold function/method/class unit in an existing non-test .py file): {len(E)}. File-level set F (>=1 gold non-test .py file existing in base): {len(F)}.\n")
    md.append("## 1. Schema audit\n")
    t, o = schema(R); md.append(t + "\n"); summ["schema"] = o
    md.append("## 2. Gold locations\n")
    md.append(gold_table(R) + "\n")
    md.append("## 3. Localizer metrics (function-level, set E)\n")
    t, o = table_fn(E); md.append(t + "\n"); summ["fn_E"] = o
    md.append("File-level on E:\n")
    t, o = table_file(E); md.append(t + "\n"); summ["file_E"] = o
    md.append(f"File-level on F (n={len(F)}):\n")
    t, o = table_file(F); md.append(t + "\n"); summ["file_F"] = o
    md.append("Seeds / graph coverage on E:\n")
    ns = sum(1 for r in E if r["seeds"]["n_seed_nodes"] > 0)
    nt = sum(1 for r in E if r["issue"]["n_plain"] + r["issue"]["n_dotted"] > 0)
    md.append(f"- tasks with >=1 issue token surviving filters: {kn(nt, len(E))}; with >=1 graph seed node: {kn(ns, len(E))}; "
              f"median seed nodes (among tasks with seeds): {med([r['seeds']['n_seed_nodes'] for r in E if r['seeds']['n_seed_nodes']]):.0f}; "
              f"max {max(r['seeds']['n_seed_nodes'] for r in E)}\n")
    md.append("## 4. Marginal value of graph / embedding over grep (set E)\n")
    t, o = marginal(E); md.append(t + "\n"); summ["marginal_E"] = o
    md.append("### Reachability upper bound (min undirected graph distance from seeds to any gold unit, set E)\n")
    t, o = reach_table(E); md.append(t + "\n"); summ["reach_E"] = o
    md.append("### Embedding cosine vs lexical overlap\n")
    t, o = emb_lex(R); md.append(t + "\n"); summ["emb_lex"] = o
    md.append("## 5. Stratification (set E)\n")
    t, o = strat(E, "repo"); md.append(t); summ["by_repo"] = o
    t, o = strat(E, "year"); md.append(t); summ["by_year"] = o
    (OUT / "summary.md").write_text("\n".join(md).replace(" nan ", " - "))
    (OUT / "summary.json").write_text(json.dumps(summ, indent=1, default=str))
    with open(OUT / "task_table.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["iid", "repo", "year", "in_E", "n_gold_units", "gold_in_graph", "n_seed_nodes",
                    "grep_first", "bm25_first", "seeds_first", "g1_first", "g2_first", "emb_first", "hyb_set_hit",
                    "grep_file", "gold_units"])
        for r in R:
            m = r["methods"]
            w.writerow([r["iid"], r["repo"], r["year"], int(r["n_gold_units"] > 0), r["n_gold_units"],
                        sum(r["gold"]["gold_units_in_graph"]), r["seeds"]["n_seed_nodes"],
                        m["GREP"]["first_gold"], m["BM25"]["first_gold"], m["SEEDS"]["first_gold"], m["G1"]["first_gold"],
                        m["G2"]["first_gold"], m["EMB"]["first_gold"], int(m["HYB"]["n_gold_set"] > 0),
                        m["GREPf"]["first_gold_file"], ";".join(r["gold"]["gold_units"])])
    print("wrote", OUT / "summary.md")


if __name__ == "__main__":
    main()
