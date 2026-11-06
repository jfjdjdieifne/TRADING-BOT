#!/usr/bin/env python3
"""Print +-N-word windows around pattern hits in downloaded files; log every window to round2/read_log.jsonl.
Usage: r2_windows.py --ctx 200 --spec "QL|time frame|newsqlguru/ict-index::transcriptions/....json|2" [--spec ...]
Window id = W### assigned in print order; the same id goes into the log so a claim can cite it."""
import sys, os, re, json, hashlib, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r2_common import DR, OUT, text_of_file
ap = argparse.ArgumentParser()
ap.add_argument("--ctx", type=int, default=200, help="words each side (window = 2*ctx)")
ap.add_argument("--spec", action="append", required=True, help="QUESTION|pattern|filekey|nhits")
ap.add_argument("--start", type=int, default=0, help="skip first N hits per spec")
a = ap.parse_args()
logp = os.path.join(OUT, "read_log.jsonl")
n0 = sum(1 for _ in open(logp)) if os.path.exists(logp) else 0
log = open(logp, "a")
for spec in a.spec:
    q, pat, key, nh = spec.split("|")
    repo, rel = key.split("::", 1)
    p = os.path.join(DR, repo.replace("/", "__"), rel)
    if not os.path.exists(p):
        print(f"!! missing {key}"); continue
    t = re.sub(r"\s+", " ", text_of_file(p))
    raw = [m.start() for m in re.finditer(re.escape(pat), t, re.I)][a.start:]
    hits, lastw = [], -10**9
    for h in raw:                      # skip hits that fall inside the window just printed
        wi = len(t[:h].split())
        if wi - lastw >= a.ctx: hits.append(h); lastw = wi
        if len(hits) >= int(nh): break
    w = t.split()
    print(f"\n===== [{q}] {key} :: '{pat}' hits={len(hits)} words={len(w)} =====")
    for h in hits:
        wi = len(t[:h].split())
        lo, hi = max(0, wi - a.ctx), min(len(w), wi + a.ctx)
        n0 += 1
        wid = f"W{n0:03d}"
        print(f"\n--- {wid} @word {wi} [{lo}:{hi}] ---")
        print(" ".join(w[lo:hi]))
        log.write(json.dumps(dict(window_id=wid, question=q, pattern=pat, file=key, hit_word_index=wi,
            window_words=[lo, hi], words=hi - lo, file_sha=hashlib.sha256(open(p, "rb").read()).hexdigest())) + "\n")
log.close()
