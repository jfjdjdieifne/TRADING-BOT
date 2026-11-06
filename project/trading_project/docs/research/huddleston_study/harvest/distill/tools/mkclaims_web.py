#!/usr/bin/env python3
"""Add claims whose source is a harvest WEB RECORD (harvest/web/pages/*.md, committed at HARVEST_HASH).
Verifies the quote against the committed file read with `git show`, same lowercase+whitespace rule."""
import json, os, re, sys, subprocess, hashlib
HARVEST = "/home/user/TRADING-BOT/project/trading_project/docs/research/huddleston_study/harvest"
DISTILL = os.path.join(HARVEST, "distill")
H = "90629a8f97ec323d9c5430b61f0ca9b2d265f45b"
idx = {}
for l in open(os.path.join(HARVEST, "INDEX.jsonl"), encoding="utf-8"):
    r = json.loads(l)
    if r["id"].startswith("web"):
        idx[r["file"]] = r
def main():
    items = json.load(open(sys.argv[1]))
    out = os.path.join(DISTILL, "claims.jsonl")
    rows = [json.loads(l) for l in open(out, encoding="utf-8")]
    n = len(rows); ok = 0; fails = []
    for it in items:
        p = os.path.join(HARVEST, it["path"])
        b = subprocess.run(["git", "show", f"{H}:project/trading_project/docs/research/huddleston_study/harvest/{it['path']}"],
                           capture_output=True, check=True).stdout
        txt = re.sub(r"\s+", " ", b.decode("utf-8").lower())
        q = re.sub(r"\s+", " ", it["quote"].lower()).strip()
        if q not in txt:
            fails.append((it["quote"][:70], "not found")); continue
        if len(it["quote"].split()) > 25:
            fails.append((it["quote"][:70], "too long")); continue
        rec = idx[it["path"]]
        n += 1
        rows.append(dict(claim_id=f"CLM-{n:04d}",
            source_label=f"{rec['site']} (harvest web record) | {it['path']} | {rec.get('author','')} | {rec['source_kind']}",
            repo="web", path=it["path"], commit_sha=H, source_kind=rec["source_kind"], author=rec.get("author", ""),
            completeness="EXCERPT", concept=it["concept"], statement=it["statement"], quote=it["quote"],
            location=it["location"], type=it["type"], notes=it.get("notes", ""), file_sha256=rec["sha256"],
            file_sha256_source="harvest INDEX.jsonl (web record file)"))
        ok += 1
    open(out, "w", encoding="utf-8").write("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in rows))
    print(json.dumps({"input": len(items), "appended": ok, "rejected": len(fails), "total_now": len(rows)}, indent=1))
    for f in fails: print("REJECT:", f)
main()
