#!/usr/bin/env python3
"""Phase 1 reducer: classify u2's 3,000 raw degree-word windows into decision buckets,
dedupe, and shortlist the ones that can carry a comparison record.
Markers are taken only from the assignment wording and from u2's concept names.
Outputs comparisons/shortlist.tsv + counts, and prints a compact reading list."""
import json, re, os, sys, collections
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = "/tmp/u2_comparisons_raw.jsonl"
MARK = {
 "priority": ["first", "most important", "before anything else", "priority", "rather than", "instead of",
              "better than", "worse than", "more important", "above all", "number one"],
 "target":   ["draw on liquidity", "liquidity pool", "target", "objective", "take profit", "partial",
              "old high", "old low", "previous high", "previous low", "next level"],
 "entry":    ["fair value gap", "order block", "breaker", "entry", "retracement", "retrace", "fill",
              "imbalance", "premium", "discount", "equilibrium"],
 "stop":     ["stop loss", "stop", "invalidation", "risk", "wrong", "failure", "failed"],
 "timeframe":["time frame", "timeframe", "higher time", "lower time", "monthly", "weekly", "daily",
              "four hour", "hourly", "fifteen minute", "five minute", "one minute", "minute chart"],
 "standaside":["don't trade", "do not trade", "avoid", "no trade", "stand aside", "sit on", "wait",
               "not trading", "stay out", "no setups"],
}
BUCKET_OF = {"priority":"priority","target":"target_choice","entry":"entry_choice","stop":"stop_choice",
             "timeframe":"timeframe_choice","standaside":"stand_aside"}
def main():
    rows = [json.loads(l) for l in open(RAW)]
    seen, out = set(), []
    for r in rows:
        q = r["quote"].lower()
        hit = [k for k, ms in MARK.items() if any(m in q for m in ms)]
        if not hit: continue
        # priority markers outrank topical ones only when the marker is an explicit ranking phrase
        b = "priority" if "priority" in hit else hit[0]
        key = (r["path"], r["word_index"] // 60)
        if (b, key) in seen: continue
        seen.add((b, key))
        out.append(dict(bucket=BUCKET_OF[b], path=r["path"], word_index=r["word_index"],
                        degree=r["degree_word"], quote=r["quote"], sha=r["file_sha256"]))
    order = ["priority","target_choice","entry_choice","stop_choice","timeframe_choice","stand_aside"]
    c = collections.Counter(x["bucket"] for x in out)
    caps = {"priority":60,"target_choice":40,"entry_choice":40,"stop_choice":35,"timeframe_choice":35,"stand_aside":30}
    keep = []
    for b in order:
        items = [x for x in out if x["bucket"] == b][:caps[b]]
        keep += items
    with open(os.path.join(OUT, "comparisons", "shortlist.tsv"), "w") as f:
        f.write("bucket\tpath\tword_index\tquote\n")
        for x in keep:
            f.write(f"{x['bucket']}\t{x['path']}\t{x['word_index']}\t{x['quote']}\n")
    print(json.dumps({"raw": len(rows), "classified": len(out), "kept": len(keep),
                      "by_bucket": {b: c[b] for b in order},
                      "kept_by_bucket": {b: sum(1 for x in keep if x['bucket']==b) for b in order},
                      "not_reduced": len(rows) - len(keep)}, indent=1))
main()
