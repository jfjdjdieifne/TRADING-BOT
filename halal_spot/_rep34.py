"""v34 report builder - reads the lab artefacts, prints every table the
brief asks for. Nothing here re-runs the engine: every number below is
traceable to results/lab_v34_*.json, results/statement_v34_*.json or
results/trades_v34_*.csv.

    python3 _rep34.py tables     # the three report tables
    python3 _rep34.py audit      # deployment / 2:1 / swap / identity proofs
"""
import glob
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
R = HERE / "results"
ARMS = ["V33_TEL_3S_3R", "S1_TEL_3R", "S1_TEL_2R", "S1_TEL_2R_BRIDGE",
        "S1_TEL_2R_SWAP", "S1_FAST_2R_HARVEST"]
WINS = ("W1", "W2")
# the shipped v33 TEL book, digit for digit (results/lab_v33_TEL_*.json)
V33_TEL = {"W1": (357, 128.4592, 130.8101, -5.774),
           "W2": (265, 105.7958, 121.6540, -5.921)}


def load():
    lab, st = {}, {}
    for a in ARMS:
        for w in WINS:
            lab[(a, w)] = json.loads((R / f"lab_v34_{a}_{w}.json").read_text())
            f = R / f"statement_v34_{a}_{w}.json"
            st[(a, w)] = json.loads(f.read_text()) if f.exists() else None
    return lab, st


def chained(lab, a):
    w1 = lab[(a, "W1")]["end_equity"]
    w2 = lab[(a, "W2")]["end_equity"]
    return w1, w2, (w1 / 100.0) * (w2 / 100.0) - 1.0


def table1(lab):
    print("\n=== TABLE 1 - the six arms, both windows ======================")
    hdr = (f"{'arm':21s}|{'w':3s}|{'n':>4s}|{'W':>4s}{'BE':>5s}{'L':>5s}"
           f"|{'WR%':>6s}|{'totR':>9s}|{'net$':>9s}|{'end$':>9s}|{'PF':>5s}"
           f"|{'DD%':>8s}|{'maxR':>7s}|{'extra2R':>8s}|{'slotFull':>9s}"
           f"|{'SWAP':>5s}|{'<$10':>5s}|{'s':>5s}")
    print(hdr)
    print("-" * len(hdr))
    for a in ARMS:
        for w in WINS:
            d = lab[(a, w)]
            c = d["counters"]
            print(f"{a:21s}|{w:3s}|{d['n']:4d}|{d['wins']:4d}{d['be']:5d}"
                  f"{d['losses']:5d}|{d['wr']:6.2f}|{d['totR']:9.2f}"
                  f"|{d['net']:9.2f}|{d['end_equity']:9.2f}|{d['pf']:5.2f}"
                  f"|{d['maxDD_pct']:8.3f}|{d['maxR']:7.2f}"
                  f"|{c.get('v34_extra_2r_opportunities', 0):8d}"
                  f"|{c.get('slot_full_rejects', 0):9d}"
                  f"|{c.get('v34_stale_swap_exit', 0):5d}"
                  f"|{c.get('fill_below_exchange_min', 0):5d}"
                  f"|{d['seconds']:5.0f}")
    print("\nchained return = (W1end/100)*(W2end/100)-1")
    for a in ARMS:
        w1, w2, ch = chained(lab, a)
        print(f"  {a:21s} ${w1:8.2f} -> ${w2:8.2f}   {ch*100:+8.2f}%")
    print("\nidentity test (arm 1 must equal the shipped v33 TEL book):")
    for w in WINS:
        d = lab[("V33_TEL_3S_3R", w)]
        got = (d["n"], d["totR"], d["end_equity"], d["maxDD_pct"])
        exp = V33_TEL[w]
        ok = all(abs(g - e) < 5e-4 for g, e in zip(got, exp))
        print(f"  {w}: got {got}  expected {exp}  -> {'MATCH' if ok else 'DRIFT'}")


def table2(lab, st):
    print("\n=== TABLE 2 - month 1..6 in $ and %, EVERY arm, both windows ===")
    for a in ARMS:
        for w in WINS:
            s = st[(a, w)]
            if s is None:
                print(f"  {a} {w}: statement missing")
                continue
            rows = s["monthly"]
            print(f"\n  -- {a} {w} ({s['window']}), final ${s['final_equity']}"
                  f", maxDD {s['maxDD_pct']}%")
            print(f"     {'m':>3s} {'bucket':8s} {'n':>4s} {'W/BE/L':>11s}"
                  f" {'WR%':>6s} {'totR':>8s} {'net$':>8s} {'month%':>8s}"
                  f" {'end$':>9s} {'PF':>5s}")
            prev = float(s["capital"])
            for i, r in enumerate(rows, start=1):
                end = r["end_balance$"]
                pct = 100.0 * (end / prev - 1.0) if prev else float("nan")
                pf = r["PF"] if r["PF"] is not None else float("nan")
                wr = r["WR%"] if r["WR%"] is not None else float("nan")
                print(f"     M{i:<2d} {r['bucket']:8s} {r['n']:4d}"
                      f" {str(r['W'])+'/'+str(r['BE'])+'/'+str(r['L']):>11s}"
                      f" {wr:6.1f} {r['totR']:8.2f} {r['net$']:8.2f}"
                      f" {pct:8.2f} {end:9.2f} {pf:5.2f}")
                prev = end


def table3(lab, st, winner):
    print(f"\n=== TABLE 3 - week 1..26 for the winning arm {winner} ==========")
    best_m, best_w = [], []
    for w in WINS:
        s = st[(winner, w)]
        rows = s["weekly"]
        print(f"\n  -- {winner} {w}: {len(rows)} weeks, final"
              f" ${s['final_equity']}, maxDD {s['maxDD_pct']}%")
        print(f"     {'wk':>4s} {'start':11s} {'n':>4s} {'W/BE/L':>11s}"
              f" {'WR%':>6s} {'totR':>8s} {'net$':>8s} {'week%':>8s}"
              f" {'end$':>9s}")
        prev = float(s["capital"])
        for i, r in enumerate(rows, start=1):
            end = r["end_balance$"]
            pct = 100.0 * (end / prev - 1.0) if prev else float("nan")
            wr = r["WR%"] if r["WR%"] is not None else float("nan")
            star = " *" if r["net$"] > 0 else "  "
            print(f"     W{i:<3d}{r['bucket'][4:]:11s} {r['n']:4d}"
                  f" {str(r['W'])+'/'+str(r['BE'])+'/'+str(r['L']):>11s}"
                  f" {wr:6.1f} {r['totR']:8.2f} {r['net$']:8.2f}"
                  f" {pct:8.2f} {end:9.2f}{star}")
            prev = end
            best_w.append((r["net$"], pct, f"{w} W{i:02d} {r['bucket'][4:]}"))
        mp = float(s["capital"])
        for i, r in enumerate(s["monthly"], start=1):
            e = r["end_balance$"]
            best_m.append((r["net$"], 100.0 * (e / mp - 1.0),
                           f"{w} M{i} {r['bucket']}"))
            mp = e
    print("\n  best 5 single months ($ , %):")
    for v, p, lab in sorted(best_m, reverse=True)[:5]:
        print(f"     {lab:22s} {v:+9.2f}$  {p:+8.2f}%")
    print("  worst 3 single months:")
    for v, p, lab in sorted(best_m)[:3]:
        print(f"     {lab:22s} {v:+9.2f}$  {p:+8.2f}%")
    print("\n  best 10 single weeks ($ , %):")
    for v, p, lab in sorted(best_w, reverse=True)[:10]:
        print(f"     {lab:22s} {v:+9.2f}$  {p:+8.2f}%")
    print("  worst 5 single weeks:")
    for v, p, lab in sorted(best_w)[:5]:
        print(f"     {lab:22s} {v:+9.2f}$  {p:+8.2f}%")


def audit(lab):
    print("\n=== AUDIT 1 - 100% cash deployment, no dust, no leverage ======")
    for a in ARMS:
        for w in WINS:
            d = pd.read_csv(R / f"trades_v34_{a}_{w}.csv")
            nt = d.notional.astype(float)
            c = lab[(a, w)]["counters"]
            print(f"  {a:21s}{w} n={len(d):4d} min=${nt.min():7.2f}"
                  f" median=${nt.median():8.2f} max=${nt.max():8.2f}"
                  f" fills<$10={int((nt < 10).sum())}"
                  f" (counter={c.get('fill_below_exchange_min', 0)})"
                  f" deploy_ok={c.get('v34_deploy_full_ok', 0)}"
                  f" topped_up={c.get('v34_deploy_topped_up', 0)}"
                  f" over={c.get('v34_deploy_over_budget', 0)}")

    print("\n=== AUDIT 2 - what the 2:1 gate actually admitted ===============")
    for a in ARMS:
        for w in WINS:
            d = pd.read_csv(R / f"trades_v34_{a}_{w}.csv")
            t = d.entry_target_R.astype(float)
            flag = (d["v34_extra_2r"].astype(str).str.lower() == "true").sum() \
                if "v34_extra_2r" in d.columns else 0
            cnt = lab[(a, w)]["counters"].get("v34_extra_2r_opportunities", 0)
            band = int(((t >= 2.0) & (t < 3.0)).sum())
            # entry_target_R is ROUNDED to 2dp in the book while the flag is
            # computed on the unrounded distance at fill time, so a target at
            # 2.997R books as 3.00. flag == counter is the exact test; the
            # rounded band is only a cross-check and may sit 1 lower (it does,
            # in exactly the three W1 2:1 arms - one AVAXUSDT fill on
            # 2023-10-11 18:15 whose target is 2.9977R).
            print(f"  {a:21s}{w} target_R min={t.min():5.2f} median="
                  f"{t.median():5.2f} | rounded band [2,3)R={band:3d}"
                  f" | v34_extra_2r flag={flag:3d} counter={cnt:3d}"
                  f" {'EXACT' if flag == cnt else 'MISMATCH'}"
                  f" (band diff {flag - band})")

    print("\n=== AUDIT 3 - the single seat: rejects and stale swaps =========")
    print("    _v34_stale_reason() tests in this order: locked (>= +LOCK_R,"
          " never evicted) -> young (< STALE_HOURS) -> profit_ok (>= +"
          "STALE_MAX_R) -> STALE. So 'kept=locked' does not imply age >= 12h.")
    for a in ARMS:
        for w in WINS:
            c = lab[(a, w)]["counters"]
            d = pd.read_csv(R / f"trades_v34_{a}_{w}.csv",
                            parse_dates=["entry_time", "exit_time"])
            h = (d.exit_time - d.entry_time).dt.total_seconds() / 3600.0
            keep = {k.replace("v34_swap_kept_", ""): v
                    for k, v in c.items() if k.startswith("v34_swap_kept_")}
            print(f"  {a:21s}{w} slot_full_rejects={c.get('slot_full_rejects', 0):4d}"
                  f" swaps_checked={c.get('v34_swap_checked_not_stale', 0):4d}"
                  f" EVICTIONS={c.get('v34_stale_swap_exit', 0):3d}"
                  f" kept={keep or '-'}"
                  f" | hold_h median={h.median():5.2f} max={h.max():6.1f}"
                  f" >=12h={int((h >= 12).sum()):3d}"
                  f" >=12h&R<0.8={int(((h >= 12) & (d.R.astype(float) < 0.8)).sum()):3d}")

    print("\n=== AUDIT 4 - the lock moved to +2.00R and wins are wins =========")
    import lab_v34_single_slot_2r as L
    for a in ARMS:
        for w in WINS:
            lockr = float(L.COMBOS[a].get("LOCK_R", L.BASE["LOCK_R"]))
            d = pd.read_csv(R / f"trades_v34_{a}_{w}.csv")
            Rr = d.R.astype(float)
            cls = d["class"].astype(str)
            band = d[(Rr >= lockr - 1e-6) & (Rr < 3.0 - 1e-6)]
            win_in_band = int((band["class"].astype(str) == "WIN").sum())
            lock = sorted(d.entry_lock_R.astype(float).unique())
            print(f"  {a:21s}{w} LOCK_R={lockr:.1f} entry_lock_R"
                  f" min={lock[0]:.2f} max={lock[-1]:.2f}"
                  f" | closes in [{lockr:.1f},3)R={len(band):3d}"
                  f" classified WIN={win_in_band:3d}"
                  f" {'OK' if win_in_band == len(band) else 'BAD'}"
                  f" | exits={dict(pd.Series(d.exit_reason).value_counts())}")

    print("\n=== AUDIT 5 - the pass2 counter patch is telemetry-only ==========")
    # pass 1 ran before v34_extra_2r / v34_swap_kept_* existed. Its four
    # summary numbers per run are still in results/_batch34.log, so all 12
    # runs can be compared, and the three 2:1 arms additionally have their
    # whole pass1 book archived for a column-by-column diff.
    log = (R / "_batch34.log").read_text().splitlines()
    p1 = {}
    for i, ln in enumerate(log):
        if ln.startswith("##### LIVE ENGINE combo="):
            key = tuple(ln.split("combo=")[1].split()[:2])
            for j in range(i + 1, min(i + 5, len(log))):
                if log[j].lstrip().startswith("n="):
                    f = log[j].split()
                    p1[key] = (int(f[0][2:]), float(f[1].split("=")[1]),
                               float(f[2].split("=$")[1]),
                               float(f[3].split("=")[1].rstrip("%")))
                    break
    for a in ARMS:
        for w in WINS:
            d = lab[(a, w)]
            got = (d["n"], d["totR"], d["end_equity"], d["maxDD_pct"])
            exp = p1.get((a, w))
            same = exp is not None and all(
                abs(g - e) < 5e-4 for g, e in zip(got, exp))
            print(f"  {a:21s}{w} pass2 {got} vs pass1 {exp}"
                  f" -> {'IDENTICAL' if same else 'DRIFT'}")
    for a in ARMS:
        for w in WINS:
            f1 = R / f"pass1_trades_v34_{a}_{w}.csv"
            if not f1.exists():
                continue
            x = pd.read_csv(f1)
            y = pd.read_csv(R / f"trades_v34_{a}_{w}.csv")
            shared = [c for c in x.columns if c in y.columns]
            same = x[shared].astype(str).equals(y[shared].astype(str))
            print(f"  book diff {a:21s}{w} n={len(x)}/{len(y)} net="
                  f"{x.net_pnl.astype(float).sum():10.4f}/"
                  f"{y.net_pnl.astype(float).sum():10.4f}"
                  f" identical_on_{len(shared)}_cols={same}"
                  f" new_cols={[c for c in y.columns if c not in x.columns]}")


def main():
    lab, st = load()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "tables"
    if cmd in ("tables", "all"):
        table1(lab)
        table2(lab, st)
        rank = sorted(ARMS, key=lambda a: -chained(lab, a)[2])
        print(f"\nranking by chained return: {rank}")
        table3(lab, st, rank[0])
    if cmd in ("audit", "all"):
        audit(lab)


if __name__ == "__main__":
    main()
