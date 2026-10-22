"""Shared library: code units, node->unit mapping, gold parsing, localizers, metrics.

Offline only. Standard library + numpy. Deterministic (no reliance on set/dict hash order).
"""
import ast
import collections
import json
import math
import os
import re
import random
from pathlib import Path

import numpy as np

DATA = Path(__file__).resolve().parents[4] / "data"  # repo data/ (gitignored)
ANALYSIS = Path(__file__).resolve().parent
SNAP = ANALYSIS / "snap"
OUT = ANALYSIS / "out"

# ----------------------------------------------------------------------------------------
# word lists
# ----------------------------------------------------------------------------------------
ENGLISH_STOP = set("""
a about above after again against all also am an and any are aren't as at be because been before being below
between both but by can can't cannot could couldn't did didn't do does doesn't doing don't down during each few
for from further get got had hadn't has hasn't have haven't having he her here hers herself him himself his how
i if in into is isn't it it's its itself just let me more most my myself no nor not now of off on once only or
other ought our ours ourselves out over own same shall she should shouldn't so some such than that the their
theirs them themselves then there these they this those through to too under until up very was wasn't we were
weren't what when where which while who whom why will with won't would wouldn't you your yours yourself
yourselves also however thus therefore etc eg ie via per like use used using uses want need needs see seen
should would may might must one two three first second new old issue bug error errors expected actual
behavior behaviour problem fix fixed fixes please thanks thank example following above below run running
works work working worked doesnt dont cant wont isnt version versions python pip install installed code
output result results case cases make makes made way ways thing things something anything nothing
""".split())
PY_BUILTIN = set("""
False None True and as assert async await break class continue def del elif else except finally for from global if
import in is lambda nonlocal not or pass raise return try while with yield self cls print len str int float bool
list dict set tuple object type range enumerate zip map filter sorted reversed sum min max abs any all open super
isinstance issubclass getattr setattr hasattr callable property staticmethod classmethod Exception ValueError
TypeError KeyError AttributeError RuntimeError OSError IOError ImportError NotImplementedError StopIteration
args kwargs bytes repr format id iter next input exit main test tests assert_eq pytest foo bar baz
""".split())
STOP_TOKENS = ENGLISH_STOP | PY_BUILTIN


def is_test_path(rel):
    parts = rel.split("/")
    base = parts[-1]
    if any(p in ("tests", "test") for p in parts[:-1]):
        return True
    return base.startswith("test_") or base.endswith("_test.py") or base == "conftest.py"


# ----------------------------------------------------------------------------------------
# tokenisation
# ----------------------------------------------------------------------------------------
_CAMEL1 = re.compile(r"([a-z0-9])([A-Z])")
_CAMEL2 = re.compile(r"([A-Z]+)([A-Z][a-z])")
_WORD = re.compile(r"[A-Za-z0-9]+")
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def split_ident_words(text):
    """Lower-cased sub-tokens of all identifiers/words in text (snake and camel case split)."""
    out = []
    for w in _WORD.findall(text):
        w = _CAMEL2.sub(r"\1 \2", _CAMEL1.sub(r"\1 \2", w))
        for p in w.split():
            p = p.lower()
            if len(p) >= 2 and not p.isdigit():
                out.append(p)
    return out


# ----------------------------------------------------------------------------------------
# units (function / method / class) from ast
# ----------------------------------------------------------------------------------------
class Unit:
    __slots__ = ("uid", "file", "qn", "name", "kind", "start", "end", "text", "parent", "idents", "is_test", "_children", "is_async")

    def __init__(self, uid, file, qn, name, kind, start, end, parent):
        self.uid, self.file, self.qn, self.name, self.kind = uid, file, qn, name, kind
        self.start, self.end, self.parent = start, end, parent
        self.text = ""
        self.idents = frozenset()
        self.is_test = is_test_path(file)
        self.is_async = False


class FileInfo:
    """Parsed python file: units, def entries (for node mapping) and line->unit map."""

    def __init__(self, rel, src):
        self.rel = rel
        self.src = src
        self.lines = src.split("\n")
        self.units = []  # Unit objects (file-local order = preorder)
        self.line2unit = [None] * (len(self.lines) + 2)  # index = line number (1-based)
        self.defs_full = collections.defaultdict(list)  # full qualname -> [(start,def_lineno,end)]
        self.defs_cls = collections.defaultdict(list)  # class-only qualname -> [...]
        self.defs_name = collections.defaultdict(list)  # bare name -> [...]
        self.ok = True
        try:
            self.tree = ast.parse(src)
        except Exception:
            self.ok = False
            self.tree = None
            return
        self._collect()

    @staticmethod
    def _sub_bodies(node):
        for f in ("body", "orelse", "finalbody"):
            b = getattr(node, f, None)
            if isinstance(b, list):
                yield b
        for h in getattr(node, "handlers", []) or []:
            yield h.body
        for c in getattr(node, "cases", []) or []:
            yield c.body

    def _start(self, node):
        s = node.lineno
        for d in getattr(node, "decorator_list", []):
            s = min(s, d.lineno)
        return s

    def _collect(self):
        mod = self.rel[:-3].replace("/", ".")
        mod = re.sub(r"\.__init__$", "", mod)
        self.mod = mod

        def walk_units(body, qual_prefix, parent):
            for node in body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    qn = (qual_prefix + "." if qual_prefix else "") + node.name
                    u = Unit(len(self.units), self.rel, qn, node.name, "func", self._start(node), node.end_lineno, parent)
                    u.is_async = isinstance(node, ast.AsyncFunctionDef)
                    self.units.append(u)
                elif isinstance(node, ast.ClassDef):
                    qn = (qual_prefix + "." if qual_prefix else "") + node.name
                    u = Unit(len(self.units), self.rel, qn, node.name, "class", self._start(node), node.end_lineno, parent)
                    self.units.append(u)
                    first_child = len(self.units)
                    walk_units(node.body, qn, u.uid)
                    # own lines of class = range minus direct children ranges
                    u._children = [c for c in self.units[first_child:] if c.parent == u.uid]
                else:
                    for b in self._sub_bodies(node):
                        walk_units(b, qual_prefix, parent)

        walk_units(self.tree.body, "", None)
        # line -> innermost unit (preorder: later = deeper)
        for u in self.units:
            for ln in range(u.start, min(u.end, len(self.lines)) + 1):
                self.line2unit[ln] = u.uid
        for u in self.units:
            if u.kind == "class":
                excl = set()
                for c in u._children:
                    excl.update(range(c.start, c.end + 1))
                own = [self.lines[ln - 1] for ln in range(u.start, min(u.end, len(self.lines)) + 1) if ln not in excl]
                u.text = "\n".join(own)
            else:
                u.text = "\n".join(self.lines[u.start - 1:u.end])
            u.idents = frozenset(_IDENT.findall(u.text))
        # def entries (all defs, incl nested) for graph node mapping
        # class-only qualname must skip function scopes: handle by custom recursion
        def walk2(node, full, cls):
            for ch in ast.iter_child_nodes(node):
                if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    is_cls = isinstance(ch, ast.ClassDef)
                    f = (full + "." if full else "") + ch.name
                    c = (cls + "." if cls else "") + ch.name
                    ent = (self._start(ch), ch.lineno, ch.end_lineno)
                    self.defs_full[f].append(ent)
                    self.defs_cls[c].append(ent)
                    self.defs_name[ch.name].append(ent)
                    walk2(ch, f, c if is_cls else cls)
                else:
                    walk2(ch, full, cls)
        walk2(self.tree, "", "")

    def unit_at(self, ln):
        if ln < 1 or ln >= len(self.line2unit):
            return None
        return self.line2unit[ln]


def load_snapshot(iid):
    """Return dict rel -> FileInfo for all .py files (global unit ids assigned later)."""
    root = SNAP / iid
    files = {}
    for dp, dn, fn in os.walk(root):
        dn.sort()
        for f in sorted(fn):
            if not f.endswith(".py"):
                continue
            p = Path(dp) / f
            rel = str(p.relative_to(root))
            try:
                src = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            files[rel] = FileInfo(rel, src)
    return files


class Repo:
    """All units of a snapshot with global ids; module index for graph node mapping."""

    def __init__(self, iid):
        self.iid = iid
        self.files = load_snapshot(iid)
        self.units = []  # global list
        self.file_units = {}
        for rel in sorted(self.files):
            fi = self.files[rel]
            base = len(self.units)
            for u in fi.units:
                gu = u
                gu.uid = base + u.uid  # global id; .parent stays file-local
                self.units.append(gu)
            fi.base = base
            self.file_units[rel] = list(range(base, base + len(fi.units)))
        self.index = collections.defaultdict(list)  # dotted key -> [rel]
        for rel in sorted(self.files):
            m = rel[:-3].replace("/", ".")
            keys = {m}
            if m.endswith(".__init__"):
                keys.add(m[: -len(".__init__")])
            for k in list(keys):
                first, _, rest = k.partition(".")
                if first in ("docs_src", "src") and rest:
                    keys.add(rest)
                    if first == "docs_src":  # ids sometimes root deeper inside docs_src
                        sub = rest.split(".")
                        for j in range(1, len(sub) - 1):
                            keys.add(".".join(sub[j:]))
            for k in sorted(keys):
                self.index[k].append(rel)

    def unit_global(self, rel, local_uid):
        return None if local_uid is None else self.files[rel].base + local_uid


def _head(text):
    for ln in text.split("\n"):
        s = ln.strip()
        if s.startswith(("def ", "async def ", "class ")):
            return re.sub(r"\s+", " ", s)
    return ""


def map_nodes(repo, nodes):
    """Map graph nodes -> global unit id. Returns (list of unit-id-or-None per node, status list, stats)."""
    res, status = [], []
    for n in nodes:
        parts = n["id"].split(".")
        found = None
        st = "no_module"
        for i in range(len(parts), 0, -1):
            key = ".".join(parts[:i])
            if key not in repo.index:
                continue
            qual = ".".join(parts[i:])
            if not qual:
                st = "module_node"
                found = None
                break
            cands = []
            for rel in repo.index[key]:
                fi = repo.files[rel]
                if not fi.ok:
                    continue
                ents = fi.defs_full.get(qual) or fi.defs_cls.get(qual) or []
                for ent in ents:
                    cands.append((rel, ent))
            if not cands:
                # fallback: unique bare-name match whose head line equals the node head
                nh0 = _head(n["text"])
                for rel in repo.index[key]:
                    fi = repo.files[rel]
                    if not fi.ok:
                        continue
                    for ent in fi.defs_name.get(parts[-1], []):
                        if _head("\n".join(fi.lines[ent[1] - 1:ent[1]])) == nh0:
                            cands.append((rel, ent))
                if cands:
                    best = cands[0]
                    rel, ent = best
                    fi = repo.files[rel]
                    lu = fi.unit_at(ent[1])
                    found = None if lu is None else fi.base + lu
                    st = "ok_name_fallback" if len(cands) == 1 else "ok_name_fallback_multi"
                    break
                st = "no_qualname"
                continue
            nh = _head(n["text"])
            best = None
            exact = [c for c in cands if _head("\n".join(repo.files[c[0]].lines[c[1][1] - 1:c[1][1]])) == nh]
            if len(cands) == 1:
                best, st = cands[0], ("ok_verified" if exact else "ok_head_mismatch")
            elif exact:
                best, st = exact[0], ("ok_disambiguated" if len(exact) < len(cands) else "ok_ambiguous_same_head")
            else:
                best, st = cands[0], "ok_ambiguous_mismatch"
            rel, ent = best
            fi = repo.files[rel]
            lu = fi.unit_at(ent[1])
            if lu is None:
                st = "no_unit"
                found = None
            else:
                found = fi.base + lu
            break
        res.append(found)
        status.append(st)
    return res, status


# ----------------------------------------------------------------------------------------
# gold from patch
# ----------------------------------------------------------------------------------------
_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def parse_patch(patch):
    """-> list of dict(old, new, deleted_lines:set, insertions:list[int p]) per file."""
    files = []
    lines = patch.split("\n")
    i = 0
    cur = None
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("--- ") and i + 1 < len(lines) and lines[i + 1].startswith("+++ "):
            old = ln[4:].split("\t")[0].strip()
            new = lines[i + 1][4:].split("\t")[0].strip()
            old = None if old == "/dev/null" else re.sub(r"^a/", "", old)
            new = None if new == "/dev/null" else re.sub(r"^b/", "", new)
            cur = {"old": old, "new": new, "deleted": set(), "insertions": []}
            files.append(cur)
            i += 2
            continue
        m = _HUNK.match(ln)
        if m and cur is not None:
            old_ln = int(m.group(1))
            ocount = int(m.group(2)) if m.group(2) is not None else 1
            ncount = int(m.group(4)) if m.group(4) is not None else 1
            if ocount == 0:
                old_ln += 1  # hunk header gives line before insertion when count==0
            i += 1
            o_rem, n_rem = ocount, ncount
            block_minus, block_plus, block_p = [], 0, None

            def flush():
                nonlocal block_minus, block_plus, block_p
                if block_minus:
                    cur["deleted"].update(block_minus)
                elif block_plus:
                    cur["insertions"].append(block_p)
                block_minus, block_plus, block_p = [], 0, None

            while i < len(lines) and (o_rem > 0 or n_rem > 0):
                l = lines[i]
                if l.startswith("\\"):
                    i += 1
                    continue
                c = l[:1]
                if c == "-":
                    if block_p is None:
                        block_p = old_ln - 1
                    block_minus.append(old_ln)
                    old_ln += 1
                    o_rem -= 1
                elif c == "+":
                    if block_p is None:
                        block_p = old_ln - 1
                    block_plus += 1
                    n_rem -= 1
                else:
                    flush()
                    old_ln += 1
                    o_rem -= 1
                    n_rem -= 1
                i += 1
            flush()
            continue
        i += 1
    return files


def compute_gold(repo, patch):
    """Gold info: files (non-test, existing in base .py), gold units, module-level flags, new-only flag."""
    pf = parse_patch(patch)
    info = {"files_changed": [], "gold_files": [], "gold_units": [], "module_level_files": [],
            "new_files": [], "test_files": [], "nonpy_files": [], "deleted_files": [], "unparsable": []}
    gold_units = collections.OrderedDict()
    for f in pf:
        path = f["new"] or f["old"]
        info["files_changed"].append(path)
        if not path.endswith(".py"):
            info["nonpy_files"].append(path)
            continue
        if is_test_path(path):
            info["test_files"].append(path)
            continue
        if f["old"] is None:
            info["new_files"].append(path)
            continue
        if f["new"] is None:
            info["deleted_files"].append(path)
        rel = f["old"]
        fi = repo.files.get(rel)
        if fi is None:  # path absent from the base snapshot -> effectively a new file
            info["new_files"].append(path)
            continue
        if not fi.ok:
            info["unparsable"].append(rel)
            continue
        info["gold_files"].append(rel)
        scopes = []  # list of unit local ids or None (module)
        for ln in sorted(f["deleted"]):
            scopes.append(fi.unit_at(ln))
        for p in f["insertions"]:
            a = fi.unit_at(p) if p >= 1 else None
            b = fi.unit_at(p + 1) if p + 1 <= len(fi.lines) else None
            # deepest common ancestor-or-self
            def chain(x):
                out = []
                while x is not None:
                    out.append(x)
                    x = fi.units[x].parent
                return out
            ca, cb = chain(a), chain(b)
            common = [x for x in ca if x in cb]
            scopes.append(common[0] if common else None)
        for sc in scopes:
            if sc is None:
                if rel not in info["module_level_files"]:
                    info["module_level_files"].append(rel)
            else:
                gold_units[fi.base + sc] = rel
    info["gold_units"] = list(gold_units.keys())
    return info


# ----------------------------------------------------------------------------------------
# issue token extraction (GREP)
# ----------------------------------------------------------------------------------------
_RE_FENCE = re.compile(r"```.*?```", re.S)
_RE_INLINE = re.compile(r"`([^`\n]+)`")
_RE_DOTTED = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+")
_RE_CAMEL = re.compile(r"\b[A-Z][a-z0-9]+(?:[A-Z][a-zA-Z0-9]*)+\b|\b[A-Z]{2,}[a-z][A-Za-z0-9]*\b")
_RE_SNAKE = re.compile(r"\b_*[A-Za-z][A-Za-z0-9]*(?:_+[A-Za-z0-9]+)+_*\b|\b_[A-Za-z][A-Za-z0-9]*\b")
_RE_CALL = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
_RE_TB = re.compile(r'File "([^"]+\.py)", line \d+, in ([A-Za-z_][A-Za-z0-9_]*)')
_RE_PATH = re.compile(r"[\w./-]*[\w-]+\.py\b")


_RE_URL = re.compile(r"https?://\S+")


def extract_tokens(text):
    """-> (ordered dict token->kinds, path_tokens). Tokens are raw (unfiltered by frequency)."""
    text = _RE_URL.sub(" ", text)
    toks = collections.OrderedDict()

    def add(t, kind):
        if t not in toks:
            toks[t] = set()
        toks[t].add(kind)

    for m in _RE_INLINE.finditer(text):
        span = m.group(1)
        for d in _RE_DOTTED.findall(span):
            add(d, "dotted")
        for w in _IDENT.findall(span):
            add(w, "backtick")
    for d in _RE_DOTTED.findall(text):
        add(d, "dotted")
    for w in _RE_CAMEL.findall(text):
        add(w, "camel")
    for w in _RE_SNAKE.findall(text):
        add(w, "snake")
    for w in _RE_CALL.findall(text):
        add(w, "call")
    paths = []
    for m in _RE_TB.finditer(text):
        paths.append(m.group(1))
        add(m.group(2), "traceback")
    for m in _RE_PATH.finditer(text):
        paths.append(m.group(0))
    # components of dotted names
    for t in list(toks):
        if "dotted" in toks[t] and "." in t:
            for c in t.split("."):
                add(c, "dotted_part")
    return toks, paths


def clean_path_tokens(paths):
    out = []
    for p in paths:
        p = p.replace("\\", "/")
        if "site-packages/" in p:
            p = p.split("site-packages/", 1)[1]
        p = p.lstrip("./")
        if p.endswith(".py") and p not in out:
            out.append(p)
    return out


# ----------------------------------------------------------------------------------------
# BM25
# ----------------------------------------------------------------------------------------
class BM25:
    def __init__(self, docs, k1=1.2, b=0.75):
        self.N = len(docs)
        self.k1, self.b = k1, b
        self.dl = np.array([len(d) for d in docs], dtype=np.float64)
        self.avg = self.dl.mean() if self.N else 1.0
        post = collections.defaultdict(list)
        for i, d in enumerate(docs):
            for t, c in collections.Counter(d).items():
                post[t].append((i, c))
        self.post = {}
        self.idf = {}
        for t in sorted(post):
            lst = post[t]
            ids = np.array([x[0] for x in lst], dtype=np.int64)
            tfs = np.array([x[1] for x in lst], dtype=np.float64)
            self.post[t] = (ids, tfs)
            df = len(lst)
            self.idf[t] = math.log(1 + (self.N - df + 0.5) / (df + 0.5))

    def scores(self, qterms):
        s = np.zeros(self.N)
        for t in sorted(set(qterms)):
            if t not in self.post:
                continue
            ids, tfs = self.post[t]
            denom = tfs + self.k1 * (1 - self.b + self.b * self.dl[ids] / self.avg)
            s[ids] += self.idf[t] * tfs * (self.k1 + 1) / denom
        return s


def rankavg(x):
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    order = np.argsort(x, kind="mergesort")
    xs = x[order]
    flag = np.r_[True, xs[1:] != xs[:-1]]
    idx = np.flatnonzero(flag)
    ends = np.r_[idx[1:], n]
    avg = (idx + ends - 1) / 2.0 + 1
    grp = np.cumsum(flag) - 1
    r = np.empty(n)
    r[order] = avg[grp]
    return r


def spearman(x, y):
    x, y = np.asarray(x), np.asarray(y)
    if len(x) < 3:
        return float("nan")
    rx, ry = rankavg(x), rankavg(y)
    rx -= rx.mean()
    ry -= ry.mean()
    d = math.sqrt((rx @ rx) * (ry @ ry))
    return float((rx @ ry) / d) if d > 0 else float("nan")
