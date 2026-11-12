#!/usr/bin/env python3
"""Append authored claims to distill/claims.jsonl, but only those whose quote is found
verbatim (lowercase + whitespace collapse only) in the re-downloaded source file.

Input: a JSON list. Each item: repo, path, concept, statement, quote, location, type, notes.
claim_id is assigned automatically as CLM-####. source_label is built from repo@commit + path +
author + source_kind taken from harvest INDEX.jsonl, so the trace tag cannot drift from the index.
"""
import json, os, re, sys, hashlib

HARVEST = "/home/user/TRADING-BOT/project/trading_project/docs/research/huddleston_study/harvest"
DISTILL = os.path.join(HARVEST, "distill")
DR = "/tmp/dr"
sys.path.insert(0, os.path.join(DISTILL, "tools"))
from verify_claims import views

def load_index():
    idx = {}
    for l in open(os.path.join(HARVEST, "INDEX.jsonl"), encoding="utf-8"):
        r = json.loads(l)
        if r.get("repo") and r.get("path"):
            idx[(r["repo"], r["path"])] = r
    return idx

IDX = load_index()

REPO_IDX = {}
def load_repo_index():
    for l in open(os.path.join(HARVEST, "INDEX.jsonl"), encoding="utf-8"):
        r = json.loads(l)
        if r.get("repo"):
            REPO_IDX.setdefault(r["repo"], r)   # first row for the repo carries repo-level metadata

def label(repo, path):
    """Per-file row if the file was individually indexed; otherwise the repo-level row
    (which pins the commit, the author handle and the source_kind for every file in it)."""
    r = IDX.get((repo, path))
    if not r:
        r = REPO_IDX.get(repo)
        if not r:
            return None, None
    return f"{repo}@{r['commit_sha'][:8]} | {path} | {r['author']} | {r['source_kind']}", r

def main():
    load_repo_index()
    src = sys.argv[1]
    items = json.load(open(src))
    out = os.path.join(DISTILL, "claims.jsonl")
    existing = [json.loads(l) for l in open(out, encoding="utf-8")] if os.path.exists(out) else []
    seen = {c["claim_id"] for c in existing}
    n = len(existing)
    ok = fail = 0
    fails = []
    for it in items:
        repo, path = it["repo"], it["path"]
        p = os.path.join(DR, repo.replace("/", "__"), path)
        if not os.path.exists(p):
            fail += 1; fails.append((it.get("quote", "")[:60], "file not downloaded")); continue
        vs = views(p)
        q = re.sub(r"\s+", " ", it["quote"].lower()).strip()
        if not any(q in v for v in vs):
            fail += 1; fails.append((it["quote"][:70], "quote not found verbatim")); continue
        if len(it["quote"].split()) > 25:
            fail += 1; fails.append((it["quote"][:70], f"{len(it['quote'].split())} words")); continue
        lab, rec = label(repo, path)
        if lab is None:
            fail += 1; fails.append((it["quote"][:70], "path not in harvest INDEX")); continue
        n += 1
        cid = f"CLM-{n:04d}"
        while cid in seen:
            n += 1; cid = f"CLM-{n:04d}"
        seen.add(cid)
        existing.append({
            "claim_id": cid, "source_label": lab, "repo": repo, "path": path,
            "commit_sha": rec["commit_sha"], "source_kind": rec["source_kind"], "author": rec["author"],
            "completeness": rec["completeness"], "concept": it["concept"], "statement": it["statement"],
            "quote": it["quote"], "location": it["location"], "type": it["type"],
            "notes": it.get("notes", ""),
            "file_sha256": (rec.get("sha256") if IDX.get((repo, path)) else hashlib.sha256(open(p,"rb").read()).hexdigest()),
            "file_sha256_source": ("harvest INDEX.jsonl" if IDX.get((repo, path)) else "computed in this session from codeload tarball at pinned commit")})
        ok += 1
    with open(out, "w", encoding="utf-8") as f:
        for c in existing: f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(json.dumps({"input": len(items), "appended": ok, "rejected": fail, "total_now": len(existing)}, indent=1))
    for f in fails: print("REJECT:", f)

if __name__ == "__main__":
    main()
