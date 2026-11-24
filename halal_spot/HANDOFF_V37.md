# HANDOFF v37

Branch: `arena/d2e74635-trading-bot`. Tip at start of v37: `01ec6e7`.

## 1. What happened to the sandbox (read this first)

The v36 working tree was **not** on the branch tip — Arena reset the session to the
branch's base commit `9aeb82d`. The session memory described v36 as local, but
`git ls-tree HEAD` showed only the pre-v18 project. **Nothing was lost**: commits
`042e9f8` (v35), `87ff01e`, `7a78281`, `01ec6e7` (v36) were all intact on
`origin/arena/d2e74635-trading-bot`, which is a strict descendant of `9aeb82d`.
Recovery was `git reset --hard origin/arena/d2e74635-trading-bot`.

**The price archives were NOT recoverable.** `halal_spot/data/binance_5m/` and
`binance_5m_oos/` were in `.gitignore` by an old owner order ("code only is
pushed"), so they lived only in the old sandbox's filesystem. `/home/user/k1m`
was gone too. They were **rebuilt from scratch** in v37 (see §2).

**THAT ORDER IS NOW REVERSED (2026-11-23).** The owner's instruction is that
everything must live in GitHub so nothing is ever lost again to an ephemeral
sandbox — and, critically, so that `git clone` + run works with no fetch step.
The archives are now **committed**: 8 coins x 47 months, 376 files, 51 MB,
largest file 190 KB. `.gitignore` carries a comment explaining why.

Two separate histories were also merged in (`main` had 184 Huddleston research
files but ZERO `halal_spot` files; the v37 branch had the opposite). Neither
branch alone could be cloned and run. See `RUN_FROM_GITHUB.md` at the repo root.

**Verified after all of it:** a plain `git clone` of `main`, empty state, no
fetch step → `python lab_v37_anti_fragile.py run B0 --window W1` →
`n=181 end=$158.024 PF=1.706 DD=-14.064% mo+=5/6`.

## 2. The data rebuild — and the bar-label bug that broke it the first time

`_fetch_v37.sh` sparse-clones the 8 GitHub 1m repos (`/1m/<Y>/<M>/`, 47 months
each, 2023-01..2026-11) into `/home/user/k1m/<SYM>/`. 376 files, ~2.3 GB.
`data.binance.vision` is still blocked in this sandbox (curl → HTTP 000), so the
GitHub repos remain the only source.

`_build_v37_data.py` resamples 1m → 5m into `data/binance_5m/<SYM>_5m/`.

**THE BUG, and it cost a full 6-minute run to find:** `resample_causal_tf()`
returns bars indexed by `end_time` (the 00:00–00:05 block becomes index 00:05),
because the engine needs end-time *availability* for causality. Binance's own
archives — and therefore the original `data/binance_5m` that v32..v36 measured —
label that same bar at its **start** (00:00). Writing end-labelled `Datetime`
into the archive shifted every 5m bar one stamp later and silently broke the
5m↔15m/1h/4h alignment: W1 came out **n=159 / $160.87** instead of **n=181 /
$158.02**. The fix is one line (`Datetime = b["start_time"]`), and the archive
must always carry start-labelled bars; the engine re-derives end-labelling
itself. **Any future data builder inherits this trap.**

Verification of the rebuild (this is the gate — do not skip it):

| check | result |
|---|---|
| Bar values vs original Binance 5m (BTC 2024-01 00:00) | O/H/L/C/V **exact**, incl. V=155.25731 |
| W1 engine re-run | n=181, totR **+227.8481**, end **$158.024**, DD **−14.064%** |
| W1 tape vs committed v36 tape, 181 rows | **all 181 match**, max \|Δ\| on net_pnl / exit_price / mfe_R / entry_price = **0.0000000000**, exit_reason and exit_time identical |

## 3. Where the brief's premises do NOT match the shipped engine

The v37 brief was written from an assumption about how the champion works. Four
of its premises are wrong in ways that change what should be built. All four were
checked against the code and against v36's 1,560 committed trades.

**(a) `LOCK_3R_BE` / `pos.locked_3r` do not exist.** `grep` over
`strategy_v36_ict_champion.py` finds neither. The real mechanics: `lock_line`
(entry+3R+fees) and `floor_line` (entry+`LOCK_ARM_R`+fees) are computed at entry;
`_manage` sets `self.ratchet=True` and raises `stop_px` to `lock_line` on the
first 5m **close** above it. There is no "wait 24h for a 4H fractal at 0.00R".
The $0.00 round-trip exit is labelled **`BREAKEVEN`** (238 of them in MODERN).

**(b) BREAKEVEN is not a post-3R giveback trap.** Of MODERN's 238 BREAKEVEN
exits, **only 52 ever reached +3R**; median peak MFE is **1.80R** (min 0.14).
These are trades that died at the +2R-ish be-armed line, not +10R runners
walked back. In the whole of MODERN only 17 trades were ever structurally
trailed (`v31_struct_trailed`), so the "+3R then trail 4H" story is a rarity.

**(c) `STOP_BLUE` is the INITIAL structural stop, not a 4H trail.** Same
evidence: `v31_struct_trailed` is True in 17/627 modern trades. So
`TRAIL_4H_ONLY_AFTER_3R` is irrelevant to the MODERN bleed — the 312 `STOP_BLUE`
exits are stops being hit *before* any lock arms. This is why "why did STOP_BLUE
lose under TRAIL_4H_ONLY_AFTER_3R" has no answer: that flag was never in play.

**(d) The Part-4 "bug" cannot occur.** `is_be = (… and R >= -0.05)` rewrites the
reason to `BREAKEVEN` and `net > 0 or …`; a `LOCK_3R_BE` exit that nets a cent
negative is classified BREAKEVEN, and classification — not `net` — drives the
streak. Harmless even so: `PER_COIN_COOLDOWN=2` means a coin is quarantined for
14 days after 2 losses and `COOLDOWN_NEEDS_BOS=True` lifts it on a real BOS, so
a −$0.01 scratch cannot "falsely ban" anything meaningfully.

## 4. The finding that matters more than any knob

Across all five windows, the edge is a **handful of trades**, and the distribution
is the same everywhere:

| window | flow | n | net $ | net minus top-3 | median trade | WR% |
|---|---|---|---|---|---|---|
| W1 | BEAR | 146 | +49.00 | +1.15 | −0.362 | 11.0 |
| W1 | BULL | 35 | +9.03 | −17.02 | −0.377 | 5.7 |
| W2 | BEAR | 103 | +32.41 | +3.43 | −0.003 | 20.4 |
| W2 | BULL | 42 | +61.97 | +2.88 | −0.000 | 19.0 |
| FULL15 | BEAR | 312 | +14.58 | −13.34 | −0.315 | 10.6 |
| FULL15 | BULL | 100 | +56.34 | −2.16 | −0.298 | 12.0 |
| OLD7 | BEAR | 139 | −9.53 | −31.64 | −0.360 | 7.9 |
| OLD7 | BULL | 56 | +16.17 | −2.61 | −0.000 | 12.5 |
| MODERN | BEAR | 466 | −32.03 | −118.36 | −0.621 | 8.6 |
| MODERN | BULL | 161 | +64.82 | −23.29 | −0.000 | 12.4 |
| **TOTAL** | **BEAR** | 1160 | **+54.43** | **−158.77** | | |
| **TOTAL** | **BULL** | 394 | **+208.32** | **−42.19** | | |

Four consequences:

1. **Every bucket's median trade is negative.** The 4H-BULL filter is positive in
   5/5 windows and is the single best-behaved cut found — but strip three trades
   per window and it is −$42.19. Gates that raise the median toward zero are
   worth testing; gates that only add polish on top of a few winners are not.
2. **A 4H-BEAR entry ban is a real candidate** (it removes the −$32 MODERN bleed
   and the −$9.53 OLD7 bleed) but it is NOT regime-robust by itself: in W1 it
   carried +$49.00, so the ban costs money in the bull windows. Expected, since
   these are counter-trend sweep reversals — the trade type is *designed* to buy
   in bear flow. It must be measured in the engine, not asserted.
3. **Stop-width bands are not a usable filter.** Only `0.45–0.75%` is positive in
   all five windows, and that is simply where the winners sit; `<0.20%` made
   +$28 in W1 and −$10.76 in MODERN. The brief's hypothesis that thin stops are
   destroyed by 0.20% fees is **not supported** by the bands as measured.
4. `nar_flow_4h` is BULL in only 394 of 1554 trades (25%): the engine is
   structurally a counter-trend/bear-flow buyer, which is exactly the behaviour
   that dies in a persistent downtrend like MOD_Y2.

## 5. State at handoff (UPDATED at the end of v37 — the §5 written mid-run is below)

**FINAL STATE OF v37**

- Engine: `strategy_v36_ict_champion.py` **with the four v37 knobs added, all
  OFF by default** (`POST_3R_RATCHET`, `HTF_ENTRY_GATE`, `COOLDOWN_BOS_TF`,
  `FIX_BE_COOLDOWN_BUG`, plus `EXIT_SLIPPAGE_BPS`). Defaults reproduce the v36
  champion bit-for-bit: B0 on W1 = **n=181 / $158.024 / PF 1.706 / DD −14.064%**,
  and on W2 = **$194.3751**.
- **VERDICT: no v37 knob ships.** See `results/REPORT_AR_v37.md` §10.
  `RATCHET_2R` is the only serious candidate and is offered to the owner as a
  RISK PROFILE, not an improvement.
- Data: committed to the repo (8 coins x 47 months, 376 files, 51 MB) so a
  `git clone` runs with no fetch step. See `RUN_FROM_GITHUB.md`.
- All measurement is DONE: the 10-arm gate matrix, the 6-window matrix, the
  46-month ledger (`results/_v37_46months.txt`), and the slippage ladder
  0/1/2/3/5 bps. Nothing is still running.
- Python: on this host use **`/home/user/.venv_v38/bin/python`** (pandas 3.1.1,
  numpy 2.4.6). The v37 sandbox's `/home/user/.venv_v37` does NOT survive.
- Still never run two engine processes at once; one W1 run is ~6-7 min,
  FULL15 ~25 min, MODERN ~32 min.

### what §5 said mid-run (kept for the record, now stale)

- Engine: `strategy_v36_ict_champion.py` unchanged from v36 (no v37 knobs added yet).
- Running: `_batch_v37_verify.sh` — W2 / OLD7 / FULL15 / MODERN re-runs.

---

## 6. v39 (THE GOLDEN SNIPER) — added 2026-11-17

The owner's thesis: *"sniping 1-2 golden trades a week beats taking 10 where 2
are golden and 8 are breakeven/stops that bleed fees and tie up the single cash
slot."* Full report: `results/REPORT_AR_v39.md`. Raw output:
`results/_audit_v39_full.txt` (257 lines), `results/_v39_step2_table.txt`,
`results/_v39_matrix.log`.

**The measurement that settles it** — the chaff does NOT block the slot:

| class | n (5 windows pooled) | median hold |
|---|---|---|
| GOLDEN | 123 | **8.58 h** |
| DEAD_BE | 328 | **0.33 h** |
| STOP_LOSS | 568 | **0.33 h** |

Slot occupancy is only **9.3%–16.5%** of each window, and just **0.3%–2.3%** of
trades ever hold >2h without reaching +1R. The seat is empty 83–91% of the
time; there is nothing to evict and no blocked signal to free.

**Two harness bugs found in v39's own code and fixed (both are recurring
traps, do not repeat them):**
1. `_assert_wired` counted knob names in the RAW source, so a name appearing
   only in a header COMMENT passed. `TRAIL_ANCHOR` did exactly that and
   returned `$158.0240` — B0 to the cent. The check now strips `#` comments.
2. The "wins" column seeded its baseline from whichever arm ran first, so only
   W1 had a B0 and every other window was scored against W1's $158.02. Baseline
   now comes from the five committed v37 tapes:
   `W1=158.024 W2=194.3751 OLD7=89.5031 MOD_Y1=326.61 MOD_Y2=107.5696`.

**Engine state:** 5 new knobs, all default OFF —
`MIN_BOX_AGE_BARS=0`, `TRAIL_ANCHOR=""`, `HTF_DEMAND_GATE=""`,
`TIME_STOP_BARS=0`, `TIME_STOP_R=1.0`. B0 W1 re-verified after the edits:
**n=181 / $158.0240 / PF 1.706 / DD −14.064%** — unchanged.

**VERDICT: no v39 knob ships.** 0 of 10 arms won 5/5. The best-shaped arm
(AGE12) delivered exactly what was asked — 1.17–2.15 trades/week, fees
$22.81→$4.01, PF 1.706→2.518, lower DD in all five windows — and **lost money
in all five**, because it kept only 42.3% of the golden trades and gave back
$691.84 of golden profit to save $322.12 of fees.

**The root cause worth remembering:** with one slot and 100% deploy, the real
cost is not the fee — it is *the golden trade you did not take*. Every
trade-count filter cuts the golden cohort by roughly the same fraction it cuts
the book, because golden-ness is not concentrated in a pre-entry subset. It
appears after the fill, not before.

**Still open (the only live lead):** `exec_tf = 1h` is far and away the best
quality bucket — 20.2% golden and $1.027/trade vs 8.3% and $0.308 for 5min —
on 89 trades across five windows. Turning the engine into a 1H-only book has
never been tested as an arm and is the recommended next round.

**Not measurable on this build:** "Weapon A vs B". `v29_arm`, `v31_brain` and
`s1_kind` are CONSTANT in every tape (`seam`/`sniper`/`BOX_STACK`). A split
table would be fabrication; a second weapon must be built before the question
can be asked.

**Python:** `/home/user/.venv_v39/bin/python` (pandas 3.1.1, numpy 2.4.6).
The venv does NOT survive a sandbox reset — recreate it.
