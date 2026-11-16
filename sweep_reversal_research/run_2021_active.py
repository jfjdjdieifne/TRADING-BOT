#!/usr/bin/env python3
"""Run the higher-frequency causal profile on the full 2021 replay.

This is deliberately a separate candidate from the strict FVG account replay.
It removes only the two frequency bottlenecks (FVG and P80/body size) while
keeping the causal sweep, S+1 direction, first prior opposite-swing target,
1m outcome path, and one-global-position rule unchanged.

The base account risk is 0.15% of current equity.  That is a research sizing
choice selected before this profile's full-year account calculation to keep the
historical drawdown below the user's 5% ceiling; it is not a forward guarantee.
The 0.10% and 0.20% curves are sensitivity checks, and the latter is expected
to be rejected if its historical drawdown exceeds 5%.
"""

from __future__ import annotations

from pathlib import Path

import run_2021_account as account
from strategy import StrategyConfig

HERE = Path(__file__).resolve().parent

account.RESULTS = HERE / "results_2021_active"
account.CONFIG = StrategyConfig(
    name="DIRECTION_NO_SIZE_NO_FVG",
    require_fvg=False,
    large_mode="none",
    large_percentile=80.0,
    min_body_fraction=0.0,
    stop_buffer=0.001,
    horizon_bars=3,
)
account.RISK_PCTS = (0.001, 0.0015, 0.002)
account.BASE_RISK_PCT = 0.0015
account.MAX_ACCEPTABLE_DD_PCT = 5.0
account.PROFILE_NOTE = (
    "المنحنى الأساسي 0.15% اختير لأنه بقي تحت حد السحب التاريخي 5%؛ "
    "منحنى 0.20% حساس فقط وقد يتجاوز الحد، ولا يُعتمد للتشغيل."
)


if __name__ == "__main__":
    account.main()
