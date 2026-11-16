#!/usr/bin/env python3
"""ONE command for everything: the strategy, the strong tests, the positive
results, and the free launch.

    python3 run_strategy.py             # card + real results + how to launch
    python3 run_strategy.py --test      # re-run BOTH strong tests
    python3 run_strategy.py --launch    # launch the free paper bot on all coins
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def banner(t):
    print("\n" + "=" * 88)
    print(t)
    print("=" * 88)


def show_card():
    p = HERE / "STRATEGY.md"
    txt = p.read_text()
    # compact: title + rules only (before the separation/evidence section)
    cut = txt.find("## 2)")
    print(txt[:cut if cut > 0 else 4000])


def show_results():
    import json
    h = HERE / "outputs/horizons_summary.json"
    m = HERE / "outputs/momentum_walkforward_summary.json"
    if not h.exists():
        subprocess.run([sys.executable, str(HERE / "run_horizons.py")], check=True)
    if not m.exists():
        subprocess.run([sys.executable, str(HERE / "run_momentum.py")], check=True)
    hz = json.loads(h.read_text())
    mo = json.loads(m.read_text())
    banner("نتائج مفصولة — ليست كلها MOMENTUM-X")
    print("V8.3 (استراتيجية منفصلة) — تجميع تاريخي لـ net-R حسب يوم/أسبوع/شهر الخروج:")
    for k, label in (("DAY", "يوم"), ("WEEK", "أسبوع"), ("MONTH", "شهر"), ("YEAR", "سنة")):
        s = hz[k]
        print(f"  {label:6} فترات={s['periods']:>4}  إيجابي={s['positive']:>4} "
              f"({s['positive_pct']:>5.1f}%)  المجموع={s['total_r']:>+8.1f}R  "
              f"أفضل={s['best_r']:>+6.1f}R  متوسط الفوز={s['avg_positive_r']:>+5.2f}R  "
              f"أسوأ={s['worst_r']:>+6.1f}R")
    print("\nمرجع زخم يومي منفصل (run_momentum.py) — Walk-Forward خارج العينة (2020→2026):")
    for name, s in mo.items():
        print(f"  {name:12} إجمالي={s['total_pct']:>+8.1f}%  t={s['t_stat']:>5}  "
              f"DD={s['max_dd_pct']:>5}%  $100→${s['final_100usd']:>8}  "
              f"أفضل أسبوع={s['best_week_pct']:>+6.1f}%  أفضل شهر={s['best_month_pct']:>+6.1f}%")
    print("\n  الأرقام كاملة: STRATEGY.md · RESULTS.md · outputs/*.csv")


def retest():
    banner("اختبار مرجعي 1/2 — Walk-Forward زخم يومي (2020→2026)")
    subprocess.run([sys.executable, str(HERE / "run_momentum.py")], check=True)
    banner("اختبار مرجعي 2/2 — تجميع V8.3 التاريخي حسب اليوم/الأسبوع/الشهر")
    subprocess.run([sys.executable, str(HERE / "run_horizons.py")], check=True)


def launch():
    banner("إطلاق البوت الورقي — ببلاش، ولا ليرة، ولا إيداع")
    print("python3 -m live.live_bot --mode paper --scan --top 8 "
          "--entry-mode momentum --min-confluence 0.4 --market futures")
    print("(Ctrl+C للإيقاف. paper_only=true ⇒ ما في أي طلب حقيقي.)")
    sys.argv = ["live.live_bot", "--mode", "paper", "--scan", "--top", "8",
                "--entry-mode", "momentum", "--min-confluence", "0.4",
                "--market", "futures"]
    from live.live_bot import main
    main()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--launch", action="store_true")
    a = ap.parse_args()
    show_card()
    if a.test:
        retest()
    show_results()
    banner("ببلاش؟ نعم — وين الاستراتيجية؟")
    print("  الاستراتيجية = STRATEGY.md + strategy.py (12 شرط، زخم، كل العملات).")
    print("  ببلاش: run_demo.py (بلا حساب/إنترنت)  |  --mode paper --market futures "
          "(داتا Binance العامة، بلا مفاتيح/إيداع).")
    print("  Testnet خيار منفصل لتجربة الأوامر في بيئة افتراضية؛ لا يلزم للـ paper.")
    print("  MOMENTUM-X مرشح 5m لم يُثبت بعد على كامل Binance USDT-M؛ النتائج أعلاه "
          "لمرجع يومي وV8.3 منفصلين.")
    if a.launch:
        launch()


if __name__ == "__main__":
    main()
