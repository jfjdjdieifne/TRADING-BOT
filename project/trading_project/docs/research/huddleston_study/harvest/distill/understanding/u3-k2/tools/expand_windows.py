#!/usr/bin/env python3
"""Phase 1b: open +/-N words around shortlisted windows, log them, print them.
Only rows that (a) are in the shortlist, (b) are not already reduced, (c) carry a preference marker."""
import json, csv, os, re, sys, hashlib, argparse
O = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DR = "/tmp/dr"
ap = argparse.ArgumentParser()
ap.add_argument("--bucket", required=True)
ap.add_argument("--limit", type=int, default=6)
ap.add_argument("--ctx", type=int, default=300)
a = ap.parse_args()
MARK = ["better", "best", "ideal", "instead", "rather", "prefer", "most important", "first", "avoid",
        "wait", "don't want", "do not want", "not to", "want to be", "would"]
rows = list(csv.DictReader(open(O + "/comparisons/shortlist.tsv"), delimiter="\t"))
done = set()
for l in open(O + "/comparisons.jsonl"):
    done.add(json.loads(l)["claim_id"])
done_rows = {int(c.split("-")[1]) for c in done}
sel, seen_files = [], set()
for i, r in enumerate(rows):
    if r["bucket"] != a.bucket or i in done_rows: continue
    q = r["quote"].lower()
    if not any(m in q for m in MARK): continue
    key = (r["path"], int(r["word_index"]) // 400)          # do not read the same stretch twice
    if key in seen_files: continue
    seen_files.add(key); sel.append((i, r))
    if len(sel) >= a.limit: break
log = open(O + "/comparisons/read_log_1b.jsonl", "a")
print(f"\n#### bucket={a.bucket}  windows={len(sel)}  ctx=+/-{a.ctx} words")
for i, r in sel:
    p = os.path.join(DR, "newsqlguru__ict-index", r["path"])
    t = re.sub(r"\s+", " ", " ".join(str(x.get("Transcription", "")) for x in json.load(open(p))))
    w = t.split(); wi = int(r["word_index"]); lo, hi = max(0, wi - a.ctx), min(len(w), wi + a.ctx)
    print(f"\n--- R{i:03d} @{wi} [{lo}:{hi}] {r['path'].split('/')[-1][:52]}")
    print(" ".join(w[lo:hi]))
    log.write(json.dumps(dict(window_id=f"R{i:03d}", bucket=a.bucket, file="newsqlguru/ict-index::" + r["path"],
        word_range=[lo, hi], words=hi - lo, ctx=a.ctx,
        file_sha=hashlib.sha256(open(p, "rb").read()).hexdigest())) + "\n")
log.close()
