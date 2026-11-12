#!/usr/bin/env python3
"""Stage-5 / Stage-6 runner: synthetic memory proof, then the single real-data run.

    python3 run_v1.py --synthetic --decisions 19008 --out /tmp/build_v1/synthetic
    python3 run_v1.py --real --data /tmp/hud_data/2021.csv.gz \
        --from 2021-01-01 --decide-from 2021-06-01 --decide-to 2021-07-01 \
        --out /tmp/build_v1/real_2021_06

The real mode verifies the input file's sha256 against the value recorded in dev_month_v0 **before**
reading a bar, and writes a MANIFEST with the input hash, the window size, the declared numbers and
the repository HEAD.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from stream_v1 import Bar, load_bars, WINDOW_BARS            # noqa: E402
from wrapper_v1 import run_stream                            # noqa: E402

UTC = timezone.utc
RECORDED_SHA256 = "38be0503fd56269686a6f3d25f5e537e2ac5682ea9a5d79af1765acd224a6ab4"
TASK_SCALE_BOUNDARIES_PER_MONTH = 6336   # ~22 trading days x 288 bars; used only to size the
                                         # synthetic run (3x this many decisions)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=HERE,
                              capture_output=True, text=True).stdout.strip()
    except Exception:
        return "UNKNOWN"


def bars_from_frame(df) -> list[Bar]:
    out = []
    for stamp, row in df.iterrows():
        out.append(Bar(
            start=stamp.to_pydatetime() if hasattr(stamp, "to_pydatetime") else stamp,
            bid_open=float(row.BidOpen), bid_high=float(row.BidHigh),
            bid_low=float(row.BidLow), bid_close=float(row.BidClose),
            bid_volume=float(row.BidVolume),
            ask_open=float(row.AskOpen), ask_high=float(row.AskHigh),
            ask_low=float(row.AskLow), ask_close=float(row.AskClose),
            ask_volume=float(row.AskVolume),
            spread_open=float(row.SpreadOpen), spread_open_pips=float(row.SpreadOpenPips),
            spread_high=float(row.SpreadHigh), spread_high_pips=float(row.SpreadHighPips),
            spread_low=float(row.SpreadLow), spread_low_pips=float(row.SpreadLowPips),
            spread_close=float(row.SpreadClose), spread_close_pips=float(row.SpreadClosePips),
        ))
    return out


def synthetic_bars(n_bars: int, seed: int) -> list[Bar]:
    """Reuse the declared generator in MEMORY_PROBE_FIXTURE_V0.py (no new numbers)."""

    path = HERE.parent / "MEMORY_PROBE_FIXTURE_V0.py"
    spec = importlib.util.spec_from_file_location("memory_probe_fixture_v0", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    df = module.synth_bidask(n_bars, seed=seed)
    return bars_from_frame(df)


def manifest(*, mode: str, out: Path, **extra) -> dict:
    record = {
        "mode": mode,
        "created_utc": datetime.now(UTC).isoformat(),
        "git_head": git_head(),
        "window_bars": WINDOW_BARS,
        "python": sys.version.split()[0],
        "declared_choices": "DECLARED_CHOICES.md (19 rows, tags SOURCE_NUMBER / ENGINEERING_CHOICE / KNOWLEDGE_GAP)",
        **extra,
    }
    (out / "MANIFEST.json").write_text(json.dumps(record, indent=1, default=str))
    return record


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--data", default="")
    ap.add_argument("--from", dest="t0", default="2021-01-01")
    ap.add_argument("--decide-from", default="")
    ap.add_argument("--decide-to", default="")
    ap.add_argument("--to", dest="t1", default="")
    ap.add_argument("--decisions", type=int, default=TASK_SCALE_BOUNDARIES_PER_MONTH * 3)
    ap.add_argument("--seed", type=int, default=20261109)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    if args.synthetic and args.real:
        raise SystemExit("choose one mode")

    if args.synthetic:
        n_bars = args.decisions + WINDOW_BARS
        bars = synthetic_bars(n_bars, args.seed)
        summary = run_stream(bars, out_dir=out, decide_from=bars[WINDOW_BARS].start,
                             max_decisions=args.decisions,
                             label=args.label or f"synthetic_{args.decisions}_decisions")
        manifest(mode="synthetic", out=out, seed=args.seed, n_bars=len(bars),
                 generator="MEMORY_PROBE_FIXTURE_V0.synth_bidask (reused, no new numbers)",
                 summary=summary)
        print(json.dumps(summary, indent=1, default=str)[:4000])
        return 0

    if not args.real:
        raise SystemExit("choose --synthetic or --real")
    data = Path(args.data)
    if not data.exists():
        raise SystemExit(f"data file not found: {data}")
    digest = sha256_file(data)
    if digest != RECORDED_SHA256:
        raise SystemExit(f"INPUT SHA256 MISMATCH: {digest} != recorded {RECORDED_SHA256}")
    t1 = args.t1 or args.decide_to or "2021-07-01"
    bars = load_bars(data, args.t0, t1)
    decide_from = (datetime.fromisoformat(args.decide_from).replace(tzinfo=UTC)
                   if args.decide_from else None)
    decide_to = (datetime.fromisoformat(args.decide_to).replace(tzinfo=UTC)
                 if args.decide_to else None)
    summary = run_stream(bars, out_dir=out, decide_from=decide_from, decide_to=decide_to,
                         label=args.label or "EURUSD_5m_2021-06")
    manifest(mode="real", out=out, data=str(data), data_sha256=digest,
             recorded_sha256=RECORDED_SHA256, bars_loaded=len(bars),
             from_=args.t0, decide_from=args.decide_from, decide_to=args.decide_to,
             to=t1, summary=summary)
    print(json.dumps(summary, indent=1, default=str)[:4000])
    return 0 if not summary.get("stopped") else 3


if __name__ == "__main__":
    raise SystemExit(main())
