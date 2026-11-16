#!/usr/bin/env python3
"""Run the session-pattern XAUUSD profile discovered from causal replay.

The profile is intentionally simple and predeclared:

* LONG only during the UTC NY window 13:00-19:59;
* SHORT only during the UTC London window 07:00-12:59;
* all existing causal sweep/S+1/first-target rules remain active;
* one position is allowed globally.

The filter is based on a pattern that was positive in both Jan-Jun and Jul-Dec
2021 for XAUUSD in the exploratory ledger. It is still a historical research
candidate, not a claim that future sessions will repeat it.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import run_2021_account as account

HERE = Path(__file__).resolve().parent


def session_filter(signal) -> bool:
    value = datetime.fromisoformat(signal.displacement_time)
    hour = value.hour
    return (
        signal.side == "SHORT" and 7 <= hour < 13
    ) or (
        signal.side == "LONG" and 13 <= hour < 20
    )


account.RESULTS = HERE / "results_2021_session_profile"
account.CONFIG = account.StrategyConfig(
    name="XAU_SESSION_LONDON_SHORT_NY_LONG",
    require_fvg=False,
    large_mode="none",
    large_percentile=80.0,
    min_body_fraction=0.0,
    stop_buffer=0.001,
    horizon_bars=3,
)
account.RISK_PCTS = (0.002, 0.0025, 0.003, 0.005)
account.BASE_RISK_PCT = 0.003
account.MAX_ACCEPTABLE_DD_PCT = 5.0
account.SIGNAL_FILTER = session_filter
account.SIGNAL_FILTER_DESCRIPTION = (
    "XAUUSD UTC: SHORT في London 07:00-12:59، LONG في New York 13:00-19:59"
)
account.PROFILE_NOTE = (
    "هذا فلتر جلسات تاريخي: تم الإبقاء على النمط لأنه موجب في نصفي 2021، "
    "لكن البيانات gross بلا spread/commission ولا يوجد ضمان لتكراره."
)


if __name__ == "__main__":
    account.main()
