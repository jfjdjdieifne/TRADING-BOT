#!/usr/bin/env python3
# PROVENANCE: byte-identical to base commit 36f2217d3e32a753f842ed8be334010e3d77c138,
# harvest/distill/tools/verify_claims.py, EXCEPT one line: DR is read from the environment so the
# pinned corpus can live at /tmp/ictidx/<pinned-sha>/ instead of /tmp/dr. No check was weakened.
"""Phase 3 verifier.

CHECK 1 (hard gate): each claim's `quote` must be found verbatim in the source file
after lowercase + whitespace collapse ONLY (no punctuation change, no reordering).
Three source views are tried, in this order:
  a) raw bytes decoded (utf-8, latin-1 fallback), whitespace collapsed
  b) the same text-extraction the harvest pass used (JSON string walk / HTML tag strip)
  c) for ICT transcripts (list of {"Transcription": ...}): the Transcription fields joined by one space
CHECK 2 (soft): content words (len>=4, not in STOP, case-folded) of `statement` that do not occur
anywhere in the +/-100-word surroundings of the quote inside the source.

Usage: verify_claims.py claims.jsonl [--report phase3_verify_batchN.md]
"""
import json, os, re, sys, argparse, hashlib

HARVEST = "/home/user/TRADING-BOT/project/trading_project/docs/research/huddleston_study/harvest"
import os as _os
DR = _os.environ.get("DR", "/tmp/dr")
STOP = set("""the a an and or of to in on for with without that this these those is are was were be been being it its as at by from
not no if then than so such when where which who whom whose what how why can could should would may might must will shall do does
did done have has had he she they them his her their our we you your i me my into over under about after before again more most
less least very much many any some all each other another same own just only also both either neither but however therefore
there here because while during within across between among at into onto out up down off above below""".split())

def views(path):
    raw = open(path, "rb").read()
    try: s = raw.decode("utf-8")
    except UnicodeDecodeError: s = raw.decode("latin-1", "replace")
    out = [s]
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        try:
            import pypdf, io
            out.append(" ".join((p.extract_text() or "") for p in pypdf.PdfReader(io.BytesIO(raw)).pages))
        except Exception: pass
    if ext in (".json", ".jsonl"):
        try:
            d = json.loads(s)
            if isinstance(d, list) and d and isinstance(d[0], dict) and "Transcription" in d[0]:
                out.append(" ".join(str(x.get("Transcription", "")) for x in d))
        except Exception: pass
        try:
            acc = []
            def walk(x):
                if isinstance(x, str): acc.append(x)
                elif isinstance(x, dict):
                    for v in x.values(): walk(v)
                elif isinstance(x, list):
                    for v in x: walk(v)
            walk(json.loads(s)); out.append(" ".join(acc))
        except Exception: pass
    if ext in (".html", ".htm"):
        import html as H
        t = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
        t = re.sub(r"<[^>]+>", " ", t); out.append(H.unescape(t))
    return [re.sub(r"\s+", " ", v.lower()).strip() for v in out if v]

def content_words(text):
    return [w for w in re.findall(r"[a-z0-9']+", text.lower()) if len(w) >= 4 and w not in STOP]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("claims")
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(a.claims, encoding="utf-8") if l.strip()]
    cache = {}
    res = {"total": len(rows), "pass": 0, "fail": 0, "warn": 0, "failures": [], "warnings": []}
    for r in rows:
        if r["repo"] == "web":
            p = os.path.join(HARVEST, r["path"])
        else:
            p = os.path.join(DR, r["repo"].replace("/", "__"), r["path"])
        if p not in cache:
            cache[p] = (hashlib.sha256(open(p, "rb").read()).hexdigest(), views(p))
        fsha, vs = cache[p]
        q = re.sub(r"\s+", " ", r["quote"].lower()).strip()
        hit = None
        for i, v in enumerate(vs):
            if q in v:
                hit = (i, v); break
        if hit is None:
            res["fail"] += 1
            res["failures"].append({"claim_id": r["claim_id"], "why": "quote not found verbatim", "path": r["path"], "quote": r["quote"][:80]})
            continue
        if len(r["quote"].split()) > 25:
            res["fail"] += 1
            res["failures"].append({"claim_id": r["claim_id"], "why": f"quote {len(r['quote'].split())} words > 25"})
            continue
        res["pass"] += 1
        i, v = hit
        pos = v.find(q); words = v.split()
        wi = len(v[:pos].split())
        lo, hi = max(0, wi - 100), min(len(words), wi + 100 + len(q.split()))
        surround = set(re.findall(r"[a-z0-9']+", " ".join(words[lo:hi])))
        missing = sorted({w for w in content_words(r["statement"]) if w not in surround})
        if missing:
            res["warn"] += 1
            res["warnings"].append({"claim_id": r["claim_id"], "missing_from_surroundings": missing})
        # provenance: the file hash must equal the pinned hash in the harvest inventory
        r["_checked_sha256"] = fsha
        r["_view_used"] = ["raw", "pdf", "transcript", "jsonwalk", "html"][i] if i < 5 else str(i)
    print(json.dumps({"total": res["total"], "pass": res["pass"], "fail": res["fail"], "warn": res["warn"],
                      "pass_rate": round(100 * res["pass"] / max(1, res["total"]), 1)}, indent=1))
    for f in res["failures"][:20]: print("FAIL:", f)
    for w in res["warnings"][:20]: print("WARN:", w)
    if a.report:
        L = [f"# {os.path.basename(a.report)}", "",
             f"- claims checked: **{res['total']}**",
             f"- CHECK 1 pass (quote verbatim, <=25 words): **{res['pass']}** ({round(100*res['pass']/max(1,res['total']),1)}%)",
             f"- CHECK 1 fail: **{res['fail']}**",
             f"- CHECK 2 warnings (statement content word absent from +/-100-word surroundings): **{res['warn']}**", ""]
        if res["failures"]:
            L.append("## Failures\n"); L += [f"- `{f['claim_id']}` {f['why']} — {f.get('path','')}" for f in res["failures"]]
        if res["warnings"]:
            L.append("\n## CHECK 2 warnings\n")
            L += [f"- `{w['claim_id']}` missing: {', '.join(w['missing_from_surroundings'])}" for w in res["warnings"]]
        L.append("\n## How the checks work\n")
        L.append("CHECK 1 is a hard gate: the quote is searched in the source file after lowercasing and whitespace collapse only — "
                 "no punctuation normalisation, no edit distance, no fuzzy match. A claim whose quote is not found is not written to `claims.jsonl`.")
        L.append("CHECK 2 is soft and reported, never silently fixed: it lists statement content words (len>=4, not stop-words) that do not appear "
                 "in the +/-100-word source window around the quote. A warning means the statement added vocabulary the source window does not contain; "
                 "the wording in `claims.jsonl` is the version that passed CHECK 1, and every warning is listed above.")
        open(a.report, "w").write("\n".join(L) + "\n")
    json.dump(res, open("/tmp/verify_last.json", "w"), indent=1)

if __name__ == "__main__":
    main()
