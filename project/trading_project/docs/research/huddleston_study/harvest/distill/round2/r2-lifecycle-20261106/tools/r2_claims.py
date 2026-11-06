#!/usr/bin/env python3
"""Append round-2 claims. Quote must be verbatim (lowercase+whitespace collapse) in the source file at /tmp/dr.
Ids: R2<Q>-#### numbered per question. Writes round2/<SID>/claims_r2.jsonl and a per-batch report."""
import json, os, re, sys, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r2_common import DR, OUT, HARVEST, show
sys.path.insert(0, os.path.join(HARVEST, "distill", "tools"))
from verify_claims import views

IDX, RIDX = {}, {}
for l in show("INDEX.jsonl").decode().splitlines():
    r = json.loads(l)
    if r.get("repo") and r.get("path"): IDX[(r["repo"], r["path"])] = r
    if r.get("repo"): RIDX.setdefault(r["repo"], r)
FLAG = {}
for line in show("distill/authorship_flags.tsv").decode().splitlines()[1:]:
    p = line.split("\t")
    if len(p) >= 2: FLAG[p[0]] = p[1]
def main():
    items = json.load(open(sys.argv[1]))
    out = os.path.join(OUT, "claims_r2.jsonl")
    rows = [json.loads(l) for l in open(out)] if os.path.exists(out) else []
    used = [c["claim_id"] for c in rows]
    ok = 0; fails = []
    for it in items:
        repo, path, q = it["repo"], it["path"], it["q"]
        p = os.path.join(DR, repo.replace("/", "__"), path)
        if not os.path.exists(p):
            fails.append((it["quote"][:60], "file not downloaded")); continue
        if len(it["quote"].split()) > 25:
            fails.append((it["quote"][:60], "quote >25 words")); continue
        qn = re.sub(r"\s+", " ", it["quote"].lower()).strip()
        if not any(qn in v.lower().replace("\u2019", "'") or qn in re.sub(r"\s+", " ", v.lower()) for v in views(p)):
            fails.append((it["quote"][:60], "quote not found verbatim")); continue
        meta = IDX.get((repo, path)) or RIDX.get(repo)
        if not meta:
            fails.append((it["quote"][:60], "path/repo not in harvest INDEX")); continue
        n = 1 + sum(1 for u in used if u.startswith(f"R2{q}-"))
        cid = f"R2{q}-{n:04d}"
        used.append(cid)
        rows.append(dict(claim_id=cid, q=q,
            source_label=f"{repo}@{meta['commit_sha'][:8]} | {path} | {meta['author']} | {meta['source_kind']} | {FLAG.get(repo,'NO_SIGNAL')}",
            repo=repo, path=path, commit_sha=meta["commit_sha"], source_kind=meta["source_kind"],
            authorship_flag=FLAG.get(repo, "NO_SIGNAL"), concept=it["concept"], statement=it["statement"],
            quote=it["quote"], location=it["location"], window_id=it.get("window_id", ""), type=it["type"],
            notes=it.get("notes", ""),
            file_sha256=hashlib.sha256(open(p, "rb").read()).hexdigest(),
            file_sha256_source="sha256 of /tmp re-download at pinned commit"))
        ok += 1
    with open(out, "w") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps(dict(input=len(items), appended=ok, rejected=len(fails), total_now=len(rows)), indent=1))
    for f in fails: print("REJECT:", f)
main()
