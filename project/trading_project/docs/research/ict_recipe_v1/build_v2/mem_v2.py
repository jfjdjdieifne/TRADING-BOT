#!/usr/bin/env python3
"""Synthetic memory re-check for v2: 3x the real run's decision boundaries, RSS must flatten.

    python3 mem_v2.py --variant V2-A --decisions 19008 --out /tmp/build_v2/synth_A
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "build_v1"))
from run_v1 import synthetic_bars                   # noqa: E402  (declared generator, reused)
from wrapper_v2 import run_stream_v2               # noqa: E402

SEED = 20261109


def bars_from(n: int):
    return synthetic_bars(n, SEED)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="V2-A")
    ap.add_argument("--decisions", type=int, default=19008)
    ap.add_argument("--out", default="/tmp/build_v2/synth")
    args = ap.parse_args()
    frames = {"V2-0": ("5m", ("5m",)), "V2-A": ("15m", ("15m", "1h")), "V2-B": ("1h", ("1h",))}
    setup, targets = frames[args.variant]
    bars = bars_from(args.decisions + 5760)
    summary = run_stream_v2(bars, out_dir=Path(args.out), variant=args.variant,
                            setup_frame=setup, target_frames=targets, session_filter=True,
                            max_decisions=args.decisions)
    curve = summary["memory"]["rss_curve"]
    rss = [c["rss_kb"] for c in curve]
    q = max(1, len(rss) // 4)
    print(json.dumps({"variant": args.variant, "decisions": summary["decisions"],
                      "plans": summary["plans"], "rss_first": rss[0], "rss_last": rss[-1],
                      "rss_min": min(rss), "rss_max": max(rss),
                      "mean_first_quarter": sum(rss[:q]) / q,
                      "mean_last_quarter": sum(rss[-q:]) / q,
                      "peak_kb": summary["memory"]["peak_rss_kb"],
                      "cap_kb": summary["memory"]["cap_kb"],
                      "stopped": summary["stopped"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
