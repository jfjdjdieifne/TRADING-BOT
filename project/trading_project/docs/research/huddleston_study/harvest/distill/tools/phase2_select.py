#!/usr/bin/env python3
"""Phase 2: mechanical keyword-density selection of files per topic.
Writes selection.md and /tmp/selection.json (path -> topic ranks). No judgement here:
a file is ranked only by the number of regex hits of the topic's keyword set."""
import json, os, re, glob, collections

HARVEST = "/home/user/TRADING-BOT/project/trading_project/docs/research/huddleston_study/harvest"
DISTILL = os.path.join(HARVEST, "distill")
DR = "/tmp/dr"

TOPICS = {
 "liquidity_draw": r"(liquidity|draw on liquidity|draws? on|liquidity pool|stop ?run|stop hunt)",
 "target_selection": r"(target|objective|draw on liquidity|next liquidity|take profit|exit)",
 "stop_invalidation": r"(invalidation|invalidate|stop ?loss|\bstop\b|protected low|protected high|swing (?:low|high))",
 "entry_zones": r"(fair value gap|\bfvg\b|order block|\bob\b|breaker|inversion fvg|\bifvg\b|mitigation block|pd array)",
 "after_sweep": r"(after the sweep|sweep\w* (?:then|and)|raid\w*|liquidity grab|wait for|confirmation)",
 "htf_ltf": r"(higher timeframe|lower timeframe|htf|ltf|multi[- ]?timeframe|top[- ]down|bias)",
 "dealing_range": r"(dealing range|premium|discount|equilibrium|range (?:high|low)|50%|midpoint)",
 "time_of_day": r"(kill ?zone|london open|new york open|ny open|silver bullet|macro|judas|session|8:30|9:30|10:00)",
 "no_trade": r"(no[- ]?trade|stand aside|sit on (?:my|your) hands|do not trade|don't trade|avoid trading|no setup)",
 "being_wrong": r"(being wrong|i was wrong|wrong\b|accept\w* (?:the )?loss|take the loss|mistake)",
 "structure": r"(market structure|market structure shift|\bmss\b|\bchoch\b|change of character|break of structure|\bbos\b|displacement)",
}

def text_of(path):
    ext = os.path.splitext(path)[1].lower()
    try: raw = open(path, "rb").read()
    except Exception: return ""
    try: s = raw.decode("utf-8")
    except UnicodeDecodeError: s = raw.decode("latin-1", "replace")
    if ext in (".json", ".jsonl"):
        # transcript files: keep the speech text only, in file order
        try:
            d = json.loads(s)
            if isinstance(d, list) and d and isinstance(d[0], dict) and "Transcription" in d[0]:
                return re.sub(r"\s+", " ", " ".join(str(x.get("Transcription", "")) for x in d))
        except Exception:
            pass
        try:
            out = []
            def walk(x):
                if isinstance(x, str): out.append(x)
                elif isinstance(x, dict):
                    for v in x.values(): walk(v)
                elif isinstance(x, list):
                    for v in x: walk(v)
            walk(json.loads(s)); s = " ".join(out)
        except Exception: pass
    if ext in (".html", ".htm"):
        s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
        s = re.sub(r"<[^>]+>", " ", s)
    return s

def corpus():
    items = []
    # transcripts
    for p in sorted(glob.glob(os.path.join(DR, "newsqlguru__ict-index/transcriptions/**/*.json"), recursive=True)):
        items.append(("TRANSCRIPT", "newsqlguru/ict-index", os.path.relpath(p, os.path.join(DR, "newsqlguru__ict-index")), p))
    # non-transcript prose from the six excerpt repos
    for repo, exts in [("SrsBlack__ict-knowledge-library", (".md",)),
                       ("Klout9__ict-strat", (".md", ".txt")),
                       ("Rouen007__ict-2022-study-room", (".md",)),
                       ("Kyle2077__ict-2022-skill-bundle", (".md", ".txt")),
                       ("Yousef-Diab__the-algorithm", (".md", ".html")),
                       ("noahbate__ict-forum-time-wisdom", (".md",)),
                       ("alptheexplorer__ICT-2024-MENTORSHIP", (".pdf",))]:
        for p in sorted(glob.glob(os.path.join(DR, repo, "**/*"), recursive=True)):
            if os.path.isfile(p) and os.path.splitext(p)[1].lower() in exts:
                items.append(("NON_TRANSCRIPT", repo.replace("__", "/", 1), os.path.relpath(p, os.path.join(DR, repo)), p))
    return items

def main():
    items = corpus()
    scores = collections.defaultdict(dict)
    sizes = {}
    for kind, repo, rel, p in items:
        t = text_of(p)
        if len(t) < 400: continue
        key = f"{repo}::{rel}"
        sizes[key] = len(t)
        for topic, pat in TOPICS.items():
            n = len(re.findall(pat, t, re.I))
            if n: scores[topic][key] = n
    sel = {}
    for topic in TOPICS:
        ranked = sorted(scores[topic].items(), key=lambda x: -x[1])
        tr = [(k, v) for k, v in ranked if k.startswith("newsqlguru/ict-index::")][:25]
        nt = [(k, v) for k, v in ranked if not k.startswith("newsqlguru/ict-index::")][:15]
        sel[topic] = {"transcripts": tr, "non_transcripts": nt}
    json.dump({"selection": sel, "sizes": sizes, "n_items": len(items)}, open("/tmp/selection.json", "w"), indent=1)
    L = ["# PHASE 2 — mechanical selection (keyword density only)\n",
         f"Corpus scanned: {len(items)} files ({sum(1 for i in items if i[0]=='TRANSCRIPT')} transcripts + "
         f"{sum(1 for i in items if i[0]!='TRANSCRIPT')} non-transcript files), files <400 chars skipped. "
         "Ranking = number of regex hits per file; no semantic scoring.\n"]
    for topic, d in sel.items():
        L.append(f"\n## {topic}\n\nregex: `{TOPICS[topic]}`\n")
        L.append("| rank | transcript (hits) | non-transcript (hits) |")
        L.append("|---|---|---|")
        for i in range(max(len(d["transcripts"]), len(d["non_transcripts"]))):
            a = f"{d['transcripts'][i][0].split('::',1)[1]} ({d['transcripts'][i][1]})" if i < len(d["transcripts"]) else ""
            b = f"{d['non_transcripts'][i][0].split('::',1)[1]} ({d['non_transcripts'][i][1]})" if i < len(d["non_transcripts"]) else ""
            L.append(f"| {i+1} | {a} | {b} |")
    open(os.path.join(DISTILL, "selection.md"), "w").write("\n".join(L) + "\n")
    print("files scored:", len(sizes), "topics:", len(sel))
    for t in ("liquidity_draw", "target_selection", "no_trade", "being_wrong"):
        print(t, "->", sel[t]["transcripts"][:3])

if __name__ == "__main__":
    main()
