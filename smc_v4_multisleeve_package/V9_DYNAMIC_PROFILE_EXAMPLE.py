"""Small offline example for the V9 signal layer.

Run from the repository root:
    .venv/bin/python smc_v4_multisleeve_package/V9_DYNAMIC_PROFILE_EXAMPLE.py

It intentionally uses synthetic bars only. It demonstrates how a consumer must
supply executed spot-flow evidence instead of pretending OHLCV is CVD.
"""

from __future__ import annotations

import sys
from pathlib import Path

PKG = Path(__file__).resolve().parent
if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

from engine.dynamic_profile import Bar, DynamicProfileConfig, DynamicProfileEngine


bars = [
    Bar(i, 100.0 + i, 101.0 + i, 99.0 + i, 100.5 + i, 1.0, spot_cvd_delta=1.0)
    for i in range(120)
]
engine = DynamicProfileEngine(DynamicProfileConfig())
results = engine.scan(bars)
print(f"bars={len(results)}")
print("No order is expected from this smooth synthetic stream:", sum(r.plan is not None for r in results))
print("The V9 engine is a causal planner; it does not submit broker orders.")
