"""Regression tests for the direction-gate fix and causal next_open
fills (Builder branch unification).

Runs with plain python3 (no pytest):  python3 test_forex_direction_gate_fix.py

Covers:
  * module-level interpretation-direction helper (_intended_direction);
  * the REAL decision gate inside run_phase (called through the real
    run_phase path with fakes for data): the legacy bug compared the
    FVG direction against the raw CONTEXT direction and blocked
    profitable reversals — the fixed gate compares against the INTENDED
    trade direction (continuation = context side, reversal = opposite);
  * next_open fills apply to BOTH entry and exit (next 5m bar open
    strictly after the event; long entry/short exit at ask, short
    entry/long exit at bid) and are the DEFAULT;
  * bar_close remains available as an explicitly labeled NON-CAUSAL
    comparison mode;
  * intrabar stop/target double-touch stays AMBIGUOUS_CENSORED (never
    resolved in favour of the trade).
"""
import ast as _ast
import importlib.util
import json
import sys
import tempfile
import types
from pathlib import Path

_HERE = Path(__file__).resolve()
_MOD_PATH = (_HERE.parents[1] / "docs" / "research" / "huddleston_study"
             / "run_forex_intraday_v1.py")

try:
    import pandas as pd
    _HAS_PANDAS = True
except ImportError:            # this sandbox: no pandas; DO NOT install
    pd = None
    _HAS_PANDAS = False


class _Skip(Exception):
    """Raised by a test whose runtime dependency is unavailable."""


def _load_module():
    if _HAS_PANDAS:
        spec = importlib.util.spec_from_file_location(
            "run_forex_intraday_v1", _MOD_PATH)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    # pandas absent: still execute the REAL pure-python helper from the
    # module source (ast extraction — no import of pandas-dependent
    # module code) so its semantics are tested even here.
    tree = _ast.parse(_MOD_PATH.read_text())
    fn = next(n for n in tree.body
              if isinstance(n, _ast.FunctionDef)
              and n.name == "_intended_direction")
    ns = {}
    exec(compile(_ast.Module([fn], []), str(_MOD_PATH), "exec"), ns)
    return types.SimpleNamespace(_intended_direction=ns["_intended_direction"])


mod = _load_module()


def _needs_pandas():
    if not _HAS_PANDAS:
        raise _Skip("pandas is not installed in this interpreter and "
                    "installing packages is forbidden by instruction")


# ---------------------------------------------------------------------
# 1. interpretation-direction helper (module level)
# ---------------------------------------------------------------------
def test_intended_direction_mapping():
    assert mod._intended_direction("I-primary", "up") == "up"
    assert mod._intended_direction("I-primary", "down") == "down"
    assert mod._intended_direction("I-scenario", "up") == "up"
    assert mod._intended_direction("I-scenario", "down") == "down"
    # I-alt is reversal: ctx up -> trade down
    assert mod._intended_direction("I-alt", "up") == "down"
    assert mod._intended_direction("I-alt", "down") == "up"
    # unknown -> None (no determinable intended direction, no silent
    # fallback to the context direction)
    assert mod._intended_direction("I-unknown", "up") is None
    assert mod._intended_direction(None, "up") is None
    assert mod._intended_direction("I-primary", "sideways") is None
    assert mod._intended_direction("I-primary", None) is None


# ---------------------------------------------------------------------
# fake two-sided 5m quote data
# ---------------------------------------------------------------------
def _mk_bidask(start="2025-03-03 10:00", periods=40, freq="5min",
               base=1.10):
    """Two-sided 5m rows with distinct open/close values per bar so
    fill-price assertions are exact."""
    idx = pd.date_range(start, periods=periods, freq=freq, tz="UTC")
    rows = []
    for i, t in enumerate(idx):
        px = base + 0.001 * i
        rows.append({
            "BidOpen": px, "BidHigh": px + 0.0006,
            "BidLow": px - 0.0006, "BidClose": px + 0.0002,
            "BidVolume": 10.0,
            "AskOpen": px + 0.0010, "AskHigh": px + 0.0016,
            "AskLow": px - 0.0000, "AskClose": px + 0.0012,
            "AskVolume": 10.0,
            "SpreadOpen": 0.0010, "SpreadOpenPips": 1.0,
            "SpreadHigh": 0.0010, "SpreadHighPips": 1.0,
            "SpreadLow": 0.0010, "SpreadLowPips": 1.0,
            "SpreadClose": 0.0010, "SpreadClosePips": 1.0,
        })
    return pd.DataFrame(rows, index=idx)


def _fake_plan(entry_ts, exit_ts, state_exit="PLAN_INVALIDATED",
               levels=None, objective_seen=False):
    entry_state = mod.PLAN_HYPOTHETICAL_ENTRY_MET
    versions = [
        {"state": entry_state, "as_of_time": str(entry_ts),
         "scenario": "continuation", "direction": "up"},
        {"state": state_exit, "as_of_time": str(exit_ts),
         "scenario": "continuation", "direction": "up"},
    ]
    cur = types.SimpleNamespace(state=state_exit,
                                levels=levels or {
                                    "reference": {"level": 0.5},
                                    "leg_end": {"level": 9.5}})
    return types.SimpleNamespace(to_record=lambda: {"versions": versions},
                                 current=cur,
                                 objective_seen=objective_seen)


# ---------------------------------------------------------------------
# 2. next_open fills: BOTH entry and exit, exact sides, causality
# ---------------------------------------------------------------------
def test_next_open_entry_and_exit_sides():
    _needs_pandas()
    bidask = _mk_bidask(start="2025-03-03 10:00", periods=30)
    ts = pd.Timestamp("2025-03-03 10:05", tz="UTC")   # event bar
    nxt = pd.Timestamp("2025-03-03 10:10", tz="UTC")  # next bar
    row = bidask.loc[nxt]
    # long entry -> ASK open of the NEXT bar
    px, t = mod.fill_price_next_open(bidask, ts, "up", side="entry")
    assert px == pytest_approx(row.AskOpen) and t == str(nxt)
    # long exit -> BID open of the NEXT bar (after the exit event)
    px, t = mod.fill_price_next_open(bidask, ts, "up", side="exit")
    assert px == pytest_approx(row.BidOpen) and t == str(nxt)
    # short entry -> BID open; short exit -> ASK open
    px, _ = mod.fill_price_next_open(bidask, ts, "down", side="entry")
    assert px == pytest_approx(row.BidOpen)
    px, _ = mod.fill_price_next_open(bidask, ts, "down", side="exit")
    assert px == pytest_approx(row.AskOpen)


def pytest_approx(x):
    return x  # exact float equality holds for values read back from the
              # same frame; kept as a named seam for future tolerance


def test_next_open_is_causal_and_gap_tolerant():
    _needs_pandas()
    bidask = _mk_bidask(start="2025-03-03 10:00", periods=4)
    # fill bar must be STRICTLY after ts (never the event bar itself)
    ts = pd.Timestamp("2025-03-03 10:00", tz="UTC")
    px, t = mod.fill_price_next_open(bidask, ts, "up", side="entry")
    assert t == "2025-03-03 10:05:00+00:00"
    # gap handling: next AVAILABLE row (here after a data gap)
    gappy = bidask.drop(pd.Timestamp("2025-03-03 10:05", tz="UTC"))
    px, t = mod.fill_price_next_open(
        gappy, pd.Timestamp("2025-03-03 10:00", tz="UTC"),
        "up", side="entry")
    assert t == "2025-03-03 10:10:00+00:00"
    # no row after ts -> no fill (never the event bar's close)
    px, t = mod.fill_price_next_open(
        bidask, pd.Timestamp("2025-03-03 10:20", tz="UTC"),
        "up", side="entry")
    assert px is None and t is None


# ---------------------------------------------------------------------
# 3. outcome_for: next_open is the DEFAULT and applies to both legs
# ---------------------------------------------------------------------
def test_outcome_for_next_open_default_both_legs():
    _needs_pandas()
    bidask = _mk_bidask(start="2025-03-03 10:00", periods=40)
    t_entry = pd.Timestamp("2025-03-03 10:05", tz="UTC")
    t_exit = pd.Timestamp("2025-03-03 11:05", tz="UTC")
    plan = _fake_plan(t_entry, t_exit,
                      levels={"reference": {"level": 0.5},
                              "leg_end": {"level": 9.5}})
    out = mod.outcome_for(plan, bidask, "up")     # DEFAULT = next_open
    assert out["fill_mode"] == "next_open"
    nxt_entry = bidask.loc[pd.Timestamp("2025-03-03 10:10", tz="UTC")]
    nxt_exit = bidask.loc[pd.Timestamp("2025-03-03 11:10", tz="UTC")]
    assert out["entry_fill"] == nxt_entry.AskOpen   # long entry = ask
    assert out["exit_fill"] == nxt_exit.BidOpen     # long exit = bid
    assert out["fill_time"] == "2025-03-03 10:10:00+00:00"
    exp_pips = round((nxt_exit.BidOpen - nxt_entry.AskOpen) * 1e4, 2)
    assert out["pips_gross"] == exp_pips
    assert out["ambiguity_same_bar_touch"] is False
    assert any("causal next_open" in n for n in out["notes"])


def test_outcome_for_bar_close_labeled_non_causal():
    _needs_pandas()
    bidask = _mk_bidask(start="2025-03-03 10:00", periods=40)
    t_entry = pd.Timestamp("2025-03-03 10:05", tz="UTC")
    t_exit = pd.Timestamp("2025-03-03 11:05", tz="UTC")
    plan = _fake_plan(t_entry, t_exit,
                      levels={"reference": {"level": 0.5},
                              "leg_end": {"level": 9.5}})
    out = mod.outcome_for(plan, bidask, "up",
                          fill_mode="bar_close")
    assert out["fill_mode"] == "bar_close"
    ebar = bidask.loc[t_entry]
    xbar = bidask.loc[t_exit]
    assert out["entry_fill"] == ebar.AskClose      # event-bar close
    assert out["exit_fill"] == xbar.BidClose
    assert any("NON-CAUSAL" in n for n in out["notes"])


# ---------------------------------------------------------------------
# 4. intrabar stop/target double-touch stays ambiguous
# ---------------------------------------------------------------------
def test_intrabar_double_touch_is_ambiguous():
    _needs_pandas()
    bidask = _mk_bidask(start="2025-03-03 10:00", periods=40)
    t_entry = pd.Timestamp("2025-03-03 10:05", tz="UTC")
    t_exit = pd.Timestamp("2025-03-03 11:05", tz="UTC")
    # FIXTURE FIX (2026-11-05): both levels must lie inside the SAME 1h
    # evaluation batch (the 10:00 task bar).  The engine resolves
    # stop/target at the task-bar CLOSE (trade_plan.py definitions:
    # "the first completed task-scale bar whose CLOSE is strictly
    # beyond ..."), so two 5m touches inside ONE batch cannot be
    # ordered -> ambiguous.  The earlier fixture took its extremes from
    # a window spanning TWO 1h batches (monotonic series), so no single
    # batch touched both levels and the rule correctly stayed silent.
    batch = bidask[(bidask.index > t_entry)
                   & (bidask.index
                      < pd.Timestamp("2025-03-03 11:00", tz="UTC"))]
    lo = float(batch.BidLow.min())
    hi = float(batch.AskHigh.max())
    plan = _fake_plan(t_entry, t_exit,
                      levels={"reference": {"level": lo},
                              "leg_end": {"level": hi}},
                      objective_seen=True)
    out = mod.outcome_for(plan, bidask, "up")
    assert out["ambiguity_same_bar_touch"] is True
    assert out["outcome"] == "AMBIGUOUS_CENSORED"
    # control case (kept from the in-memory verification, now as an
    # assertion): when EVERY 1h batch spans both levels, the rule fires
    # as well and the outcome stays censored-ambiguous.
    flat = bidask.copy()
    flat["BidLow"] = 1.0
    flat["BidHigh"] = 2.0
    flat["AskLow"] = 1.0
    flat["AskHigh"] = 2.0
    out2 = mod.outcome_for(plan, flat, "up")
    assert out2["ambiguity_same_bar_touch"] is True
    assert out2["outcome"] == "AMBIGUOUS_CENSORED"


# ---------------------------------------------------------------------
# 5. REAL decision gate through the REAL run_phase path (fakes for data)
# ---------------------------------------------------------------------
class _FakeStudy:
    """Only the surface run_phase and the real gate consume."""

    def __init__(self, region_direction):
        reg = types.SimpleNamespace(direction=region_direction)
        self.readings = types.SimpleNamespace(
            tasks={
                "RT-REF-REVIEW": types.SimpleNamespace(
                    conclusion={"status": "OK"}),
                "T1": types.SimpleNamespace(
                    conclusion={"status": "EVIDENCE_PREFERRED",
                                "preferred": "FVG1"}),
            },
            regions={"FVG1": reg})
        self.hf_context = {"trend": "down"}

    def on_boundary(self, *a, **k):
        return []

    def on_observation(self, *a, **k):
        return []

    def on_readings_boundary(self, *a, **k):
        return []


def _fake_decide(**kw):
    return types.SimpleNamespace(
        decision_id="DEC-FAKE-0001",
        primary_is_baseline=False,
        state="SCENARIO_DEVELOPING",
        primary_interpretation_id="I-primary",
        context={"direction": "up"},
        next_discriminating_observation="the next completed bar")


def _run_gate_case(tmpdir, region_direction):
    """Drive the REAL run_phase (real loop/engine/plan layer) with fakes
    for data, decision input and the readings layer; return (cases,
    summary)."""
    saved = {name: getattr(mod, name) for name in
             ("load_bidask", "decide", "StudyReasoningLayer")}
    try:
        bidask = _mk_bidask(start="2025-03-03 00:00", periods=288 * 3,
                            base=1.10)
        mod.load_bidask = (lambda d, t0, t1:
                           bidask[(bidask.index >= pd.Timestamp(t0, tz="UTC"))
                                  & (bidask.index < pd.Timestamp(t1, tz="UTC"))])
        mod.decide = _fake_decide
        mod.StudyReasoningLayer = (lambda **kw: _FakeStudy(region_direction))
        model_path = Path(tmpdir) / "model.json"
        model_path.write_text(json.dumps(
            {"kind": "context-event-model-v1", "counts": [],
             "n_episodes": 0, "trained_through": None}))
        out_dir = Path(tmpdir) / "out"
        args = {"bidask_dir": str(Path(tmpdir) / "unused"),
                "from": "2025-03-03", "to": "2025-03-06",
                "model": str(model_path), "out_dir": str(out_dir),
                "gate": "v1"}
        mod.run_phase(args, "eval")
        cases = [json.loads(l) for l in
                 (out_dir / "cases_eval_v1.jsonl").read_text().splitlines()]
        summary = json.loads((out_dir / "summary_eval_v1.json").read_text())
        return cases, summary
    finally:
        for name, val in saved.items():
            setattr(mod, name, val)


def test_real_gate_holds_on_opposing_fvg():
    _needs_pandas()
    with tempfile.TemporaryDirectory() as tmp:
        cases, summary = _run_gate_case(tmp, "downward")  # opposes up
    held = [c for c in cases
            if "opposing the intended direction" in str(c.get("gate_reason"))]
    assert held, "the real gate must hold attempts on opposing FVG"
    # the reason names the intended direction and its interpretation
    assert any("from pid=I-primary ctx=up" in c["gate_reason"]
               for c in held)
    assert summary["fill_mode"] == "next_open"        # default recorded
    assert summary["gate_stats"]["decisions"] > 0


def test_real_gate_passes_when_fvg_aligns():
    _needs_pandas()
    with tempfile.TemporaryDirectory() as tmp:
        cases, summary = _run_gate_case(tmp, "upward")  # aligns with up
    assert not any("opposing the intended direction"
                   in str(c.get("gate_reason")) for c in cases)
    allowed = [c for c in cases
               if "do not contradict" in str(c.get("gate_reason"))]
    assert allowed, "aligned evidence must let the gate pass the attempt"
    assert summary["gate_stats"]["gate_pass"] > 0


# ---------------------------------------------------------------------
# plain-python3 runner (pytest is not installed; do not install)
# ---------------------------------------------------------------------
if __name__ == "__main__":
    tests = [v for k, v in list(globals().items())
             if k.startswith("test_") and callable(v)]
    failed = skipped = 0
    for fn in tests:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except _Skip as exc:
            skipped += 1
            print(f"SKIP {fn.__name__}: {exc}")
        except Exception as exc:  # noqa: BLE001 — report and continue
            failed += 1
            print(f"FAIL {fn.__name__}: {type(exc).__name__}: {exc}")
    print(f"{len(tests) - failed - skipped}/{len(tests)} passed, "
          f"{skipped} skipped, {failed} failed")
    if skipped:
        print("NOTE: skipped tests exercise pandas-dependent code "
              "(fills, outcome harness, real run_phase gate path); "
              "pandas was not installed here and packages must not be "
              "installed — rerun under an interpreter with pandas to "
              "execute them.")
    sys.exit(1 if failed else 0)
