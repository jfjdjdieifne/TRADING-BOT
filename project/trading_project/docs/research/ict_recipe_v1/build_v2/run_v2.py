#!/usr/bin/env python3
"""Runner: one variant, one month, one attempt.  No retry, no tuning, sha256 verified first.

    python3 run_v2.py --variant V2-A --month 2021-09 --out /tmp/build_v2/m1_V2A

Variants are declared in DECLARED_CHOICES_V2.md row A.  `v1` runs the frozen build_v1 code through
its own entry point so that the control is literally the v1 wrapper, not a re-implementation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "build_v1"))

from stream_v1 import load_bars  # noqa: E402

DATA_SHA256 = "38be0503fd56269686a6f3d25f5e537e2ac5682ea9a5d79af1765acd224a6ab4"
DATA_BYTES = 3175925
HISTORY_FROM = "2021-01-01"

VARIANTS = {
    "v1":     {"setup_frame": "5m", "target_frames": ("5m",), "session_filter": True, "code": "v1"},
    "V2-0":   {"setup_frame": "5m", "target_frames": ("5m",), "session_filter": True, "code": "v2"},
    "V2-A":   {"setup_frame": "15m", "target_frames": ("15m", "1h"), "session_filter": True, "code": "v2"},
    "V2-B":   {"setup_frame": "1h", "target_frames": ("1h",), "session_filter": True, "code": "v2"},
    "V2-A-OFF": {"setup_frame": "15m", "target_frames": ("15m", "1h"), "session_filter": False, "code": "v2"},
    "V2-B-OFF": {"setup_frame": "1h", "target_frames": ("1h",), "session_filter": False, "code": "v2"},
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_data(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"STOP: data file missing: {path}")
    got = sha256_file(path)
    if got != DATA_SHA256:
        raise SystemExit(f"STOP: sha256 mismatch\n  want {DATA_SHA256}\n  got  {got}")
    return {"path": str(path), "sha256": got, "bytes": path.stat().st_size}


def month_window(month: str) -> tuple[str, str]:
    year, mm = month.split("-")
    start = f"{month}-01"
    if mm == "12":
        end = f"{int(year) + 1}-01-01"
    else:
        end = f"{year}-{int(mm) + 1:02d}-01"
    return start, end


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True, choices=sorted(VARIANTS))
    ap.add_argument("--month", required=True, help="YYYY-MM, the decision month")
    ap.add_argument("--data", default="/tmp/hud_data/2021.csv.gz")
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    ap.add_argument("--max-decisions", type=int, default=None)
    args = ap.parse_args()

    data = verify_data(Path(args.data))
    decide_from, decide_to = month_window(args.month)
    bars = load_bars(Path(args.data), HISTORY_FROM, decide_to)
    spec = VARIANTS[args.variant]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    head = subprocess.run(["git", "-C", str(HERE.parents[4]), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    manifest = {
        "variant": args.variant, "spec": spec, "month": args.month,
        "decide_from": decide_from, "decide_to": decide_to,
        "history_from": HISTORY_FROM, "data": data, "bars_loaded": len(bars),
        "git_head": head, "label": args.label or ("IN_SAMPLE" if args.month == "2021-06" else "OUT_OF_SAMPLE"),
        "python": sys.version.split()[0],
    }
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")

    if spec["code"] == "v1":
        from wrapper_v1 import run_stream as run_v1_stream
        summary = run_v1_stream(bars, out_dir=out, label=args.label,
                                decide_from=datetime.fromisoformat(decide_from).replace(tzinfo=timezone.utc),
                                decide_to=datetime.fromisoformat(decide_to).replace(tzinfo=timezone.utc),
                                max_decisions=args.max_decisions)
        summary.setdefault("variant", "v1")
        (out / "run_summary.json").write_text(json.dumps(summary, indent=1, default=str),
                                              encoding="utf-8")
    else:
        from wrapper_v2 import run_stream_v2
        summary = run_stream_v2(
            bars, out_dir=out, variant=args.variant,
            setup_frame=spec["setup_frame"], target_frames=spec["target_frames"],
            session_filter=spec["session_filter"],
            decide_from=datetime.fromisoformat(decide_from).replace(tzinfo=timezone.utc),
            decide_to=datetime.fromisoformat(decide_to).replace(tzinfo=timezone.utc),
            max_decisions=args.max_decisions,
        )

    print(json.dumps({"variant": args.variant, "month": args.month,
                      "decisions": summary.get("decisions"),
                      "plans": summary.get("plans"),
                      "theses": summary.get("independent_theses"),
                      "elapsed": summary.get("elapsed_seconds"),
                      "peak_rss_kb": (summary.get("memory") or {}).get("peak_rss_kb"),
                      "stopped": summary.get("stopped")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
