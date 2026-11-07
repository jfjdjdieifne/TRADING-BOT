#!/usr/bin/env python3
"""Print compact reading windows around topic hits, and log exactly what was read
into distill/read_log.jsonl (file, topic, hit offsets, words shown)."""
import json, re, sys, os, argparse, hashlib

HARVEST = "/home/user/TRADING-BOT/project/trading_project/docs/research/huddleston_study/harvest"
DISTILL = os.path.join(HARVEST, "distill")
sys.path.insert(0, os.path.join(DISTILL, "tools"))
from phase2_select import TOPICS, text_of  # reuse extraction + regexes

DR = "/tmp/dr"

def resolve(key):
    repo, rel = key.split("::", 1)
    if repo == "newsqlguru/ict-index": return os.path.join(DR, "newsqlguru__ict-index", rel)
    return os.path.join(DR, repo.replace("/", "__"), rel)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True)
    ap.add_argument("--files", nargs="+", required=True)
    ap.add_argument("--hits", type=int, default=2)
    ap.add_argument("--ctx", type=int, default=45)
    ap.add_argument("--win", type=int, default=400, help="words kept in the stored window")
    ap.add_argument("--offset-hits", type=int, default=0, help="skip the first N hits")
    a = ap.parse_args()
    pat = TOPICS[a.topic]
    log = open(os.path.join(DISTILL, "read_log.jsonl"), "a")
    for key in a.files:
        p = resolve(key)
        t = re.sub(r"\s+", " ", text_of(p))
        hits = [m.start() for m in re.finditer(pat, t, re.I)][a.offset_hits: a.offset_hits + a.hits]
        print(f"\n===== {key}  ({len(t)} chars) =====")
        words = t.split()
        for h in hits:
            pre = t[:h]
            wi = len(pre.split())
            lo = max(0, wi - a.ctx); hi = min(len(words), wi + a.ctx)
            print(f"[hit@{wi}] ...{' '.join(words[lo:hi])}...")
            log.write(json.dumps(dict(file=key, topic=a.topic, hit_word_index=wi,
                window_words=[lo, hi], chars=t and len(t), file_sha=hashlib.sha256(open(p,'rb').read()).hexdigest())) + "\n")
    log.close()

if __name__ == "__main__":
    main()
