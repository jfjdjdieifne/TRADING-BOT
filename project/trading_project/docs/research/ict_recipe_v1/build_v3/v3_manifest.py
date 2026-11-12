#!/usr/bin/env python3
"""Run facts + sha256 manifest of every V3 output (kept outside the repo)."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path("/tmp/build_v3")
OUT = Path(__file__).resolve().parent / "REPORT_V3"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    lines = ["# V3 run facts (generated)", "```",
             f"{'run':22s} {'decisions':>9s} {'plans':>6s} {'cxl':>4s} {'exp':>4s} {'settled':>7s} "
             f"{'rss_kb':>8s} {'secs':>6s} stopped"]
    manifest = []
    for run_dir in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        summary_path = run_dir / "run_summary.json"
        if not summary_path.exists():
            continue
        s = json.loads(summary_path.read_text())
        rss = (s.get("memory") or {}).get("peak_rss_kb")
        lines.append(f"{run_dir.name:22s} {s.get('decisions', 0):9d} {s.get('plans', 0):6d} "
                     f"{s.get('cancelled', 0):4d} {s.get('expired', 0):4d} {s.get('settled', 0):7d} "
                     f"{str(rss):>8s} {s.get('elapsed_seconds', 0):6.1f} {s.get('stopped')}")
        for name in ("run_summary.json", "plans_final.jsonl", "plans.jsonl", "decisions.jsonl"):
            path = run_dir / name
            if path.exists():
                manifest.append(f"{sha(path)}  {path}")
    lines.append("```")
    (OUT / "RUN_FACTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT / "RUN_OUTPUT_SHA256.txt").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    print(json.dumps({"runs": sum(1 for _ in ROOT.glob("*/run_summary.json")), "files": len(manifest)}))


if __name__ == "__main__":
    main()
