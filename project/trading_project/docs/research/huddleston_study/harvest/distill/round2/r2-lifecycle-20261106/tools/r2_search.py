#!/usr/bin/env python3
"""Question-driven search: patterns derived from the assignment wording + existing claims.
Writes search_log.tsv (question, pattern, file, hits) and search_report.txt (ranked per question)."""
import sys, os, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r2_common import corpus, OUT
Q = {
 "QA": ["stop loss", "stop above", "stop below", "where's your stop", "buffer", "how many pips", "invalidation"],
 "QB": ["limit order", "market order", "resting order", "buy stop", "sell stop", "fill", "entry price"],
 "QC": ["position size", "risk per trade", "percent", "one percent", "drawdown", "lot size", "how much risk"],
 "QD": ["anticipat", "not forcing", "wait for", "confirmation", "wait until", "patience"],
 "QE": ["stopped out", "goes against you", "reassess", "trade goes", "underwater", "cut it", "invalidat"],
 "QF": ["killzone", "kill zone", "session", "new york time", "london open", "time zone", "8:00", "10:00"],
 "QG": ["fair value gap", "displacement", "imbalance", "impulsive", "energetic"],
 "QH": ["order block", "fair value gap", "overlap", "confluence", "which one"],
 "QI": ["change of character", "choch", "market structure shift", "break of structure", "mss", "bos"],
 "QJ": ["consequent encroachment", "50%", "midpoint", "equilibrium", "premium", "discount", "half"],
 "QK": ["lower time frame", "lower timeframe", "ltf", "one minute", "five minute", "15 minute"],
 "QL": ["let's look at", "recap", "weekly bias", "daily bias", "market review", "if i could go back", "chart"],
 "QM": ["dealing range", "premium", "discount", "range high", "range low", "equilibrium"],
}
def main():
    corp = corpus()
    log = open(os.path.join(OUT, "search_log.tsv"), "w")
    log.write("question\tpattern\tfile\thits\n")
    rep = open(os.path.join(OUT, "search_report.txt"), "w")
    rep.write(f"# corpus: {len(corp)} files with text (all /tmp/dr downloads)\n")
    for q, pats in Q.items():
        agg = collections.Counter()
        for pat in pats:
            rx = re.compile(re.escape(pat), re.I)
            for key, p, t in corp:
                n = len(rx.findall(t))
                if n:
                    agg[key] += n
                    log.write(f"{q}\t{pat}\t{key}\t{n}\n")
        rep.write(f"\n## {q}\n")
        for key, n in agg.most_common(12):
            rep.write(f"{n}\t{key}\n")
    log.close(); rep.close()
    print("files with text:", len(corp))
main()
