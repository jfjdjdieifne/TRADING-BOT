#!/usr/bin/env python3
"""Shared helpers for round-2 mining. Reads ONLY from the base commit (git show) and /tmp re-downloads."""
import json, os, re, subprocess, hashlib
BASE = "462bb61068e6b184478b831dd8295a189dfeabc5"
REPO = "/home/user/TRADING-BOT"
HARVEST_REL = "project/trading_project/docs/research/huddleston_study/harvest"
HARVEST = os.path.join(REPO, HARVEST_REL)
SID = "r2-lifecycle-20261106"
OUT = os.path.join(HARVEST, "distill", "round2", SID)
DR = "/tmp/dr"
CACHE = "/tmp/r2/text"

def show(path):
    """bytes of a harvest-relative path at the BASE commit."""
    return subprocess.run(["git", "-C", REPO, "show", f"{BASE}:{HARVEST_REL}/{path}"],
                          capture_output=True, check=True).stdout

def index_rows():
    for l in show("INDEX.jsonl").decode().splitlines():
        yield json.loads(l)

def text_of_file(p):
    ext = os.path.splitext(p)[1].lower()
    raw = open(p, "rb").read()
    try: s = raw.decode("utf-8")
    except UnicodeDecodeError: s = raw.decode("latin-1", "replace")
    if ext in (".json", ".jsonl"):
        try:
            d = json.loads(s)
            if isinstance(d, list) and d and isinstance(d[0], dict) and "Transcription" in d[0]:
                return " ".join(str(x.get("Transcription", "")) for x in d)
            if isinstance(d, dict):
                return " ".join(str(v) for v in d.values() if isinstance(v, str))
        except Exception:
            pass
    if ext in (".html", ".htm"):
        s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S | re.I)
        s = re.sub(r"<[^>]+>", " ", s)
    return s

def corpus():
    """[(key, path, text)] over every downloaded file in /tmp/dr, text cached."""
    os.makedirs(CACHE, exist_ok=True)
    out = []
    for root, _, files in os.walk(DR):
        for f in files:
            if os.path.splitext(f)[1].lower() not in (".md", ".txt", ".json", ".jsonl", ".html"):
                continue
            p = os.path.join(root, f)
            rel = os.path.relpath(p, DR)
            key = rel.split(os.sep, 1)[0].replace("__", "/", 1) + "::" + rel.split(os.sep, 1)[1]
            h = hashlib.sha1(p.encode()).hexdigest()[:16]
            cf = os.path.join(CACHE, h + ".txt")
            if not os.path.exists(cf):
                try: open(cf, "w").write(re.sub(r"\s+", " ", text_of_file(p)))
                except Exception: continue
            out.append((key, p, open(cf).read()))
    out.sort(key=lambda x: x[0])
    return out
