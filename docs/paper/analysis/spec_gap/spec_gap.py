"""Spec gap: which identifiers do the hidden tests use that the fix introduces, and does the issue name them?"""
import json, re, sys, collections
tasks = [json.loads(l) for l in open(sys.argv[1])]
ID = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")
def added(patch, test=False):
    out, cur = [], None
    for line in patch.splitlines():
        if line.startswith("+++ "): cur = line[6:] if line.startswith("+++ b/") else line[4:]
        elif line.startswith("+") and not line.startswith("+++"): out.append((cur, line[1:]))
    return out
def removed(patch):
    return [l[1:] for l in patch.splitlines() if l.startswith("-") and not l.startswith("---")]
DEF = re.compile(r"^\s*(?:async\s+)?(?:def|class)\s+([A-Za-z_]\w*)|^\s*([A-Za-z_]\w*)\s*(?::[^=]+)?=\s*[^=]")
KW = re.compile(r"[\(,]\s*([a-z_][a-z0-9_]*)\s*(?::\s*[^=,)]+)?=")
stats = collections.Counter(); rows = []
for t in tasks:
    src_add = added(t["patch"]); src_rem = " ".join(removed(t["patch"]))
    new_names = set()
    for f, l in src_add:
        m = DEF.match(l)
        if m: new_names.add(m.group(1) or m.group(2))
        for k in KW.findall(l): new_names.add(k)
    # keep only names that do not appear in removed lines (truly new to the code at this site)
    new_names = {n for n in new_names if n not in src_rem and len(n) > 3 and not n.startswith("_")}
    test_ids = set(ID.findall(" ".join(l for f, l in added(t["test_patch"]))))
    needed = new_names & test_ids
    issue = t["problem_statement"]
    named = {n for n in needed if re.search(r"\b" + re.escape(n) + r"\b", issue)}
    rows.append({"id": t["instance_id"], "needed": sorted(needed), "named_in_issue": sorted(named)})
    stats["tasks"] += 1
    if needed: stats["tests_use_new_names"] += 1
    if needed and needed - named: stats["some_needed_name_absent_from_issue"] += 1
    if needed and not named: stats["no_needed_name_in_issue"] += 1
print(dict(stats))
json.dump(rows, open(sys.argv[2], "w"), indent=1)
