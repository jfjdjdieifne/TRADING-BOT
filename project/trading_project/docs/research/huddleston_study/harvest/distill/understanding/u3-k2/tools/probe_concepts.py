#!/usr/bin/env python3
"""Phase 2 probe: for each assigned concept, print up to N windows of +/-ctx words from distinct files."""
import json, os, re, sys, argparse, hashlib
O = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DR = "/tmp/dr/newsqlguru__ict-index"
ap = argparse.ArgumentParser(); ap.add_argument("--ctx", type=int, default=90)
ap.add_argument("--per", type=int, default=2); ap.add_argument("--only", default=None)
a = ap.parse_args()
concepts = json.load(open("/tmp/k2_even.json"))
if a.only: concepts = [c for c in concepts if c["concept"] in a.only.split(",")]
files = []
for r, _, fs in os.walk(DR + "/transcriptions"):
    for f in fs:
        if f.endswith(".json"): files.append(os.path.join(r, f))
files.sort()
log = open(O + "/concepts/read_log.jsonl", "a") if os.path.isdir(O + "/concepts") else None
for c in concepts:
    pat = re.compile(re.escape(c["phrase"]), re.I)
    shown = 0
    print(f"\n########## {c['concept']}  (phrase '{c['phrase']}', corpus hits {c['probe_count']})")
    for p in files:
        if shown >= a.per: break
        try:
            d = json.load(open(p)); t = re.sub(r"\s+", " ", " ".join(str(x.get("Transcription", "")) for x in d))
        except Exception: continue
        m = pat.search(t)
        if not m: continue
        w = t.split(); wi = len(t[:m.start()].split()); lo, hi = max(0, wi - a.ctx), min(len(w), wi + a.ctx)
        rel = os.path.relpath(p, DR)
        print(f"\n--- {c['concept']} @{wi} {rel.split('/')[-1][:56]}")
        print(" ".join(w[lo:hi]))
        shown += 1
        if log:
            log.write(json.dumps(dict(concept=c["concept"], file="newsqlguru/ict-index::" + rel,
                word_range=[lo, hi], ctx=a.ctx, file_sha=hashlib.sha256(open(p, "rb").read()).hexdigest())) + "\n")
if log: log.close()
