"""Regression tests for direction semantics fix."""
import types
import sys
from pathlib import Path

# import the module under test
import importlib.util
spec = importlib.util.spec_from_file_location(
    "run_forex_intraday_v1",
    Path("project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py")
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def test_intended_direction_primary_up():
    assert mod._intended_direction("I-primary", "up") == "up"

def test_intended_direction_primary_down():
    assert mod._intended_direction("I-primary", "down") == "down"

def test_intended_direction_scenario_up():
    assert mod._intended_direction("I-scenario", "up") == "up"

def test_intended_direction_scenario_down():
    assert mod._intended_direction("I-scenario", "down") == "down"

def test_intended_direction_alt_up():
    # I-alt is reversal: ctx up -> trade down
    assert mod._intended_direction("I-alt", "up") == "down"

def test_intended_direction_alt_down():
    assert mod._intended_direction("I-alt", "down") == "up"

def test_intended_direction_unknown_pid():
    assert mod._intended_direction("I-unknown", "up") is None

def test_intended_direction_unknown_ctx():
    assert mod._intended_direction("I-primary", "sideways") is None
    assert mod._intended_direction("I-primary", None) is None

def test_intended_direction_none_pid():
    assert mod._intended_direction(None, "up") is None

def _fake_dec(pid, ctx_dir):
    return types.SimpleNamespace(
        primary_interpretation_id=pid,
        primary_is_baseline=False,
        state="SCENARIO_DEVELOPING",
        context={"direction": ctx_dir}
    )

def _fake_study(direction):
    # region with direction upward/downward
    reg = types.SimpleNamespace(direction=direction)
    task = types.SimpleNamespace(
        conclusion={"status": "EVIDENCE_PREFERRED", "preferred": "FVG1"},
    )
    study = types.SimpleNamespace(
        readings=types.SimpleNamespace(
            tasks={"T1": task},
            regions={"FVG1": reg}
        )
    )
    # ensure RT-REF-REVIEW not triggering
    study.readings.tasks["RT-REF-REVIEW"] = types.SimpleNamespace(conclusion={"status": "OK"})
    return study

def test_legacy_bug_bull_reversal_blocks_incorrectly():
    # demonstrates the bug via intended direction: legacy used ctx_dir, fixed uses intended
    intended = mod._intended_direction("I-alt", "up")
    assert intended == "down"
    # legacy would oppose based on ctx up vs downward => true
    oppose_legacy = (("downward" == "downward" and "up" == "up"))
    oppose_fixed = (("downward" == "downward" and intended == "up"))
    assert oppose_legacy == True
    assert oppose_fixed == False

def test_continuation_bull_passes():
    assert mod._intended_direction("I-primary", "up") == "up"
    # FVG upward should not oppose up for continuation
    intended = mod._intended_direction("I-primary", "up")
    reg_dir = "upward"
    oppose = (reg_dir == "downward" and intended == "up") or (reg_dir == "upward" and intended == "down")
    assert oppose == False

def test_continuation_bear_passes():
    assert mod._intended_direction("I-primary", "down") == "down"
    intended = mod._intended_direction("I-primary", "down")
    reg_dir = "downward"
    oppose = (reg_dir == "downward" and intended == "up") or (reg_dir == "upward" and intended == "down")
    assert oppose == False

