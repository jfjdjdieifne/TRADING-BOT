# HIDDEN WORK SEARCH V1 — every concept, every remote tip

- searched trees: **39** remote branch tips (`git grep` over `*.py`)
- backbone: `origin/arena/77604f59-trading-bot` = `fd43dc29a9139aa088724b0e0f11b3d97cba431f`
- raw hits: `/tmp/consolidation_v1/hidden_hits.json` (sha256 `c1c31681eee420bc779b8d7b76ef2393f910f74d2bfcd65185d278cba68ed667`), outside the repository
- hits: **340980**, distinct (path, symbol, blob) implementations: **2205**
- `same blob on backbone` is a hash comparison; a copied file is not hidden work

## Table — implementations per concept

| concept | on backbone (path+blob) | ONLY on other branches |
|---|---|---|
| swing | 129 | 15 |
| FVG | 255 | 67 |
| order_block | 352 | 86 |
| liquidity_sweep | 12 | 11 |
| displacement | 91 | 30 |
| dealing_range | 97 | 23 |
| equilibrium_premium_discount | 20 | 14 |
| liquidity_pool | 70 | 18 |
| equal_highs_lows | 363 | 120 |
| structure_break | 142 | 28 |
| htf_bias | 104 | 19 |
| draw_on_liquidity | 30 | 18 |
| session_killzone | 129 | 43 |
| entry_zone_selection | 4 | 3 |
| stop_invalidation | 125 | 21 |
| target | 311 | 46 |
| trade_plan | 33 | 7 |
| trade_tracking | 223 | 46 |
| explanation_trace | 250 | 68 |

## ONLY on other branches — full rows

An implementation is listed here when **no file with the same path AND the same blob sha exists on the backbone** (the owner's definition). The column `name on backbone` separates two very different cases: `no` is genuinely new code whose name appears nowhere in the backbone; `yes` is a **drifted copy** — the same function name exists on the backbone with different bytes. A drifted copy is not new work until someone reads what changed.

| concept | symbol | name on backbone | file(s) | branches | signature | causal (screen) | has test |
|---|---|---|---|---|---|---|---|
| FVG | `check_v2` | **no** | `b1_teacher_test/run_teacher.py` | `arena/e2c9bda8-trading-bot` | `def check_v2(outcome, status, wanted_bounds=None, candidate=None, fvg=False, side=None, source_values=None):` | NO | yes |
| swing | `main` | yes | `b1_teacher_test/run_teacher.py` | `arena/e2c9bda8-trading-bot` | `def main():` | NO | yes |
| swing | `source_rule_for_swing` | **no** | `b1_teacher_test/run_teacher.py` | `arena/e2c9bda8-trading-bot` | `def source_rule_for_swing(case, side, candidate):` | NO | yes |
| FVG | `teacher_fvg_relation` | **no** | `b1_teacher_test/run_teacher.py` | `arena/e2c9bda8-trading-bot` | `def teacher_fvg_relation(case, outcome):` | NO | yes |
| equal_highs_lows | `_runner_python_files` | yes | `field_runner/runner_tests/test_runner_guards.py` | `arena/01a0f676-trading-bot` | `def _runner_python_files():` | UNKNOWN | yes |
| FVG | `test_closed_project_manifest_untouched` | yes | `field_runner/runner_tests/test_runner_guards.py` | `arena/01a0f676-trading-bot` | `def test_closed_project_manifest_untouched():` | UNKNOWN | yes |
| draw_on_liquidity | `cover` | **no** | `make_zzz_pdf.py` | `arena/01a0f676-trading-bot` | `def cover(pdf: TranscriptPDF, stats: dict) -> None:` | UNKNOWN | yes |
| draw_on_liquidity | `flush` | yes | `make_zzz_pdf.py` | `arena/01a0f676-trading-bot` | `def flush():` | UNKNOWN | no |
| draw_on_liquidity | `line_is_art` | **no** | `make_zzz_pdf.py` | `arena/01a0f676-trading-bot` | `def line_is_art(line: str) -> bool:` | UNKNOWN | no |
| draw_on_liquidity | `prep` | **no** | `make_zzz_pdf.py` | `arena/01a0f676-trading-bot` | `def prep(text: str, face: str='sans') -> str:` | UNKNOWN | yes |
| draw_on_liquidity | `toc_render` | **no** | `make_zzz_pdf.py` | `arena/01a0f676-trading-bot` | `def toc_render(pdf: TranscriptPDF, outline) -> None:` | UNKNOWN | no |
| FVG | `gate_v1` | yes | `project/trading_project/docs/research/dev_month_v0/run_dev_month_v0.py` | `arena/f75dc3c4-trading-bot` | `def gate_v1(dec, study) -> tuple:` | UNKNOWN | no |
| trade_plan | `main` | yes | `project/trading_project/docs/research/dev_month_v0/run_dev_month_v0.py` | `arena/f75dc3c4-trading-bot` | `def main(argv=None) -> int:` | UNKNOWN | yes |
| target | `_record` | yes | `project/trading_project/docs/research/huddleston_study/engine_v1/c1_catalog/displacement.py` | `arena/27cad7fe-trading-bot`, `arena/e7e64fc5-trading-bot` | `def _record(**kwargs):` | YES | yes |
| displacement | `_source_numbers_for` | yes | `project/trading_project/docs/research/huddleston_study/engine_v1/c1_catalog/displacement.py` | `arena/27cad7fe-trading-bot`, `arena/e7e64fc5-trading-bot` | `def _source_numbers_for(variant, window=None):` | YES | no |
| displacement | `displacement_at` | yes | `project/trading_project/docs/research/huddleston_study/engine_v1/c1_catalog/displacement.py` | `arena/27cad7fe-trading-bot`, `arena/e7e64fc5-trading-bot` | `def displacement_at(candles, t, variant, previous_window=None):` | YES | yes |
| liquidity_sweep | `_evaluate` | yes | `project/trading_project/docs/research/huddleston_study/engine_v1/c1_catalog/liquidity_sweep.py` | `arena/27cad7fe-trading-bot`, `arena/e7e64fc5-trading-bot` | `def _evaluate(rows, t, side, level, variant, level_basis, swing_index):` | UNKNOWN | yes |
| liquidity_sweep | `_record` | yes | `project/trading_project/docs/research/huddleston_study/engine_v1/c1_catalog/liquidity_sweep.py` | `arena/27cad7fe-trading-bot`, `arena/e7e64fc5-trading-bot` | `def _record(**kwargs):` | UNKNOWN | yes |
| swing | `_swing_at` | yes | `project/trading_project/docs/research/huddleston_study/engine_v1/c1_catalog/liquidity_sweep.py` | `arena/27cad7fe-trading-bot`, `arena/e7e64fc5-trading-bot` | `def _swing_at():` | UNKNOWN | no |
| liquidity_sweep | `_validate` | yes | `project/trading_project/docs/research/huddleston_study/engine_v1/c1_catalog/liquidity_sweep.py` | `arena/27cad7fe-trading-bot`, `arena/e7e64fc5-trading-bot` | `def _validate(rows, t, side, variant):` | UNKNOWN | yes |
| swing | `latest_swing_level` | yes | `project/trading_project/docs/research/huddleston_study/engine_v1/c1_catalog/liquidity_sweep.py` | `arena/27cad7fe-trading-bot`, `arena/e7e64fc5-trading-bot` | `def latest_swing_level(candles, before_index, side):` | UNKNOWN | no |
| liquidity_sweep | `sweep_at` | yes | `project/trading_project/docs/research/huddleston_study/engine_v1/c1_catalog/liquidity_sweep.py` | `arena/27cad7fe-trading-bot`, `arena/e7e64fc5-trading-bot` | `def sweep_at(candles, t, side, level, variant):` | UNKNOWN | yes |
| swing | `sweep_at_swing_level` | yes | `project/trading_project/docs/research/huddleston_study/engine_v1/c1_catalog/liquidity_sweep.py` | `arena/27cad7fe-trading-bot`, `arena/e7e64fc5-trading-bot` | `def sweep_at_swing_level(candles, t, side, variant):` | UNKNOWN | yes |
| displacement | `_record` | yes | `project/trading_project/docs/research/huddleston_study/engine_v1/c1_catalog/order_block.py` | `arena/27cad7fe-trading-bot`, `arena/e7e64fc5-trading-bot` | `def _record(**kwargs) -> dict:` | UNKNOWN | yes |
| order_block | `order_block_at` | yes | `project/trading_project/docs/research/huddleston_study/engine_v1/c1_catalog/order_block.py` | `arena/27cad7fe-trading-bot`, `arena/e7e64fc5-trading-bot` | `def order_block_at(candles, displacement_start_index, direction, boundaries=None, mean_threshold_basis=None, entry_level=None, inv` | UNKNOWN | yes |
| equal_highs_lows | `main` | yes | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k4a/verify_k4a.py` | `arena/ad9c5dec-trading-bot` | `def main():` | YES | yes |
| explanation_trace | `main` | yes | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k4b/check_quotes.py` | `arena/c59ec6a3-trading-bot` | `def main() -> int:` | UNKNOWN | yes |
| equal_highs_lows | `main` | yes | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k7/phase1/B21/verify_pilot.py` | `arena/acde8869-trading-bot`, `arena/fbd58b68-trading-bot` | `def main():` | UNKNOWN | yes |
| draw_on_liquidity | `main` | yes | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k7/phase1/B30/audit/make_sample.py` | `arena/5b5d18f2-trading-bot`, `arena/acde8869-trading-bot` | `def main():` | UNKNOWN | yes |
| order_block | `load_entries` | **no** | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k7/scripts/k7_corpus.py` | `arena/5b5d18f2-trading-bot`, `arena/acde8869-trading-bot`, `arena/efbf666d-trading-bot`, `arena/fbd58b68-trading-bot` | `def load_entries(path):` | UNKNOWN | no |
| target | `pack` | **no** | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k7/scripts/k7_phase0.py` | `arena/5b5d18f2-trading-bot`, `arena/acde8869-trading-bot`, `arena/efbf666d-trading-bot`, `arena/fbd58b68-trading-bot` | `def pack(chs, word_target, chunk_cap):` | NO | yes |
| equal_highs_lows | `step_dups` | **no** | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k7/scripts/k7_phase0.py` | `arena/5b5d18f2-trading-bot`, `arena/acde8869-trading-bot`, `arena/efbf666d-trading-bot`, `arena/fbd58b68-trading-bot` | `def step_dups(args):` | NO | no |
| order_block | `step_probe` | **no** | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k7/scripts/k7_phase0.py` | `arena/5b5d18f2-trading-bot`, `arena/acde8869-trading-bot`, `arena/efbf666d-trading-bot`, `arena/fbd58b68-trading-bot` | `def step_probe(args):` | NO | no |
| equal_highs_lows | `step_timeline` | **no** | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k7/scripts/k7_phase0.py` | `arena/5b5d18f2-trading-bot`, `arena/acde8869-trading-bot`, `arena/efbf666d-trading-bot`, `arena/fbd58b68-trading-bot` | `def step_timeline(args):` | NO | no |
| equal_highs_lows | `main` | yes | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k7/scripts/k7_reports.py` | `arena/5b5d18f2-trading-bot`, `arena/acde8869-trading-bot`, `arena/efbf666d-trading-bot`, `arena/fbd58b68-trading-bot` | `def main():` | UNKNOWN | yes |
| equal_highs_lows | `main` | yes | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k7/scripts/k7_verify.py` | `arena/5b5d18f2-trading-bot`, `arena/acde8869-trading-bot`, `arena/efbf666d-trading-bot`, `arena/fbd58b68-trading-bot` | `def main():` | UNKNOWN | yes |
| explanation_trace | `add_claims` | yes | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/u3-k1/tools/corpus_engine.py` | `arena/bd0f0622-trading-bot` | `def add_claims(new):` | UNKNOWN | no |
| target | `windows_for` | yes | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/u3-k1/tools/corpus_engine.py` | `arena/bd0f0622-trading-bot` | `def windows_for(phrases, n, per_file, concept, nex=2):` | UNKNOWN | no |
| order_block | `main` | yes | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/u3-k1/tools/probe_terms.py` | `arena/bd0f0622-trading-bot` | `def main():` | UNKNOWN | yes |
| explanation_trace | `main` | yes | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/u3-k1/tools/verify_claims.py` | `arena/bd0f0622-trading-bot` | `def main():` | UNKNOWN | yes |
| explanation_trace | `add_claims` | yes | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/u3-k2/tools/corpus_engine.py` | `arena/e91e69b1-trading-bot` | `def add_claims(new):` | UNKNOWN | no |
| target | `windows_for` | yes | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/u3-k2/tools/corpus_engine.py` | `arena/e91e69b1-trading-bot` | `def windows_for(phrases, n, per_file, concept, nex=2):` | UNKNOWN | no |
| order_block | `main` | yes | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/u3-k2/tools/probe_terms.py` | `arena/e91e69b1-trading-bot` | `def main():` | UNKNOWN | yes |
| target | `main` | yes | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/u3-k2/tools/reduce_comparisons.py` | `arena/e91e69b1-trading-bot` | `def main():` | UNKNOWN | yes |
| explanation_trace | `main` | yes | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/u3-k2/tools/verify_claims.py` | `arena/e91e69b1-trading-bot` | `def main():` | UNKNOWN | yes |
| order_block | `main` | yes | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/u3-k3/tools/build_cards.py` | `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def main():` | UNKNOWN | yes |
| explanation_trace | `add_claims` | yes | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/u3-k3/tools/corpus_engine.py` | `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def add_claims(new):` | UNKNOWN | no |
| target | `windows_for` | yes | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/u3-k3/tools/corpus_engine.py` | `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def windows_for(phrases, n, per_file, concept, nex=2):` | UNKNOWN | no |
| order_block | `add_concept_card` | **no** | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/u3-k3/tools/k3_engine.py` | `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def add_concept_card(spec_json_path: str):` | UNKNOWN | no |
| target | `pick_round_robin` | **no** | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/u3-k3/tools/k3_engine.py` | `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def pick_round_robin(cands, target, current):` | UNKNOWN | no |
| session_killzone | `sample_concept_windows` | **no** | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/u3-k3/tools/k3_engine.py` | `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def sample_concept_windows(concept: str, n: int=15, ctx: int=100):` | UNKNOWN | no |
| order_block | `main` | yes | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/u3-k3/tools/probe_terms.py` | `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def main():` | UNKNOWN | yes |
| session_killzone | `detect` | yes | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/u3-k3/tools/task3_pairing.py` | `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def detect():` | UNKNOWN | yes |
| explanation_trace | `main` | yes | `project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/u3-k3/tools/verify_claims.py` | `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def main():` | UNKNOWN | yes |
| trade_plan | `_intended_direction` | yes | `project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py` | `arena/5eee9692-trading-bot` | `def _intended_direction(pid: str \| None, ctx_dir: str \| None) -> str \| None:` | YES | yes |
| equal_highs_lows | `fill_price` | yes | `project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py` | `arena/a41fd997-trading-bot`, `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/bd0f0622-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def fill_price(bidask, ts, direction, side='entry'):` | YES | yes |
| equal_highs_lows | `fill_price` | yes | `project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py` | `arena/5eee9692-trading-bot` | `def fill_price(bidask, ts, direction, side='entry'):` | YES | no |
| equal_highs_lows | `gate_b0` | yes | `project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py` | `arena/5eee9692-trading-bot` | `def gate_b0(dec, study) -> tuple:` | YES | no |
| equal_highs_lows | `gate_b0` | yes | `project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py` | `arena/a41fd997-trading-bot`, `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/bd0f0622-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def gate_b0(dec, study) -> tuple:` | YES | no |
| FVG | `gate_v1` | yes | `project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py` | `arena/a41fd997-trading-bot`, `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/bd0f0622-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def gate_v1(dec, study) -> tuple:` | YES | no |
| FVG | `gate_v1` | yes | `project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py` | `arena/5eee9692-trading-bot` | `def gate_v1(dec, study) -> tuple:` | YES | no |
| FVG | `gate_v1_legacy` | **no** | `project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py` | `arena/5eee9692-trading-bot` | `def gate_v1_legacy(dec, study) -> tuple:` | YES | no |
| equal_highs_lows | `main` | yes | `project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py` | `arena/a41fd997-trading-bot`, `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/bd0f0622-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def main(argv=None) -> int:` | YES | yes |
| target | `outcome_for` | yes | `project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py` | `arena/5eee9692-trading-bot` | `def outcome_for(plan, bidask, direction, fill_convention='close'):` | YES | no |
| equal_highs_lows | `outcome_for` | yes | `project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py` | `arena/a41fd997-trading-bot`, `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/bd0f0622-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def outcome_for(plan, bidask, direction, fill_mode='next_open'):` | YES | yes |
| FVG | `pause_and_step` | yes | `project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py` | `arena/a41fd997-trading-bot`, `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/bd0f0622-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def pause_and_step(args) -> int:` | YES | no |
| FVG | `pause_and_step` | yes | `project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py` | `arena/5eee9692-trading-bot` | `def pause_and_step(args) -> int:` | YES | no |
| trade_plan | `run_phase` | yes | `project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py` | `arena/5eee9692-trading-bot` | `def run_phase(args, phase: str) -> int:` | YES | no |
| trade_plan | `run_phase` | yes | `project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py` | `arena/a41fd997-trading-bot`, `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/bd0f0622-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def run_phase(args, phase: str) -> int:` | YES | yes |
| stop_invalidation | `same_bar_ambiguity` | yes | `project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py` | `arena/5eee9692-trading-bot` | `def same_bar_ambiguity(bidask, t_entry, t_exit, level_a, level_b):` | YES | yes |
| stop_invalidation | `same_bar_ambiguity` | yes | `project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py` | `arena/a41fd997-trading-bot`, `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/bd0f0622-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def same_bar_ambiguity(bidask, t_entry, t_exit, level_a, level_b):` | YES | yes |
| equal_highs_lows | `main` | yes | `project/trading_project/docs/research/ict_recipe_v1/MEMORY_PROBE_FIXTURE_V0.py` | `arena/f75dc3c4-trading-bot` | `def main() -> int:` | UNKNOWN | yes |
| FVG | `__init__` | yes | `project/trading_project/tests/test_forex_direction_gate_fix.py` | `arena/a41fd997-trading-bot`, `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/bd0f0622-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def __init__(self, region_direction):` | UNKNOWN | yes |
| equal_highs_lows | `_fake_dec` | **no** | `project/trading_project/tests/test_forex_direction_gate_fix.py` | `arena/5eee9692-trading-bot` | `def _fake_dec(pid, ctx_dir):` | UNKNOWN | yes |
| equal_highs_lows | `_fake_decide` | yes | `project/trading_project/tests/test_forex_direction_gate_fix.py` | `arena/a41fd997-trading-bot`, `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/bd0f0622-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def _fake_decide(**kw):` | UNKNOWN | yes |
| target | `_fake_plan` | yes | `project/trading_project/tests/test_forex_direction_gate_fix.py` | `arena/a41fd997-trading-bot`, `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/bd0f0622-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def _fake_plan(entry_ts, exit_ts, state_exit='PLAN_INVALIDATED', levels=None, objective_seen=False):` | UNKNOWN | yes |
| FVG | `_fake_study` | **no** | `project/trading_project/tests/test_forex_direction_gate_fix.py` | `arena/5eee9692-trading-bot` | `def _fake_study(direction):` | UNKNOWN | yes |
| FVG | `test_continuation_bull_passes` | **no** | `project/trading_project/tests/test_forex_direction_gate_fix.py` | `arena/5eee9692-trading-bot` | `def test_continuation_bull_passes():` | UNKNOWN | yes |
| target | `test_intrabar_double_touch_is_ambiguous` | yes | `project/trading_project/tests/test_forex_direction_gate_fix.py` | `arena/a41fd997-trading-bot`, `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/bd0f0622-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def test_intrabar_double_touch_is_ambiguous():` | UNKNOWN | yes |
| trade_tracking | `test_outcome_for_bar_close_labeled_non_causal` | yes | `project/trading_project/tests/test_forex_direction_gate_fix.py` | `arena/a41fd997-trading-bot`, `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/bd0f0622-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def test_outcome_for_bar_close_labeled_non_causal():` | UNKNOWN | yes |
| trade_tracking | `test_outcome_for_next_open_default_both_legs` | yes | `project/trading_project/tests/test_forex_direction_gate_fix.py` | `arena/a41fd997-trading-bot`, `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/bd0f0622-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def test_outcome_for_next_open_default_both_legs():` | UNKNOWN | yes |
| FVG | `test_real_gate_holds_on_opposing_fvg` | yes | `project/trading_project/tests/test_forex_direction_gate_fix.py` | `arena/a41fd997-trading-bot`, `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/bd0f0622-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def test_real_gate_holds_on_opposing_fvg():` | UNKNOWN | yes |
| FVG | `test_real_gate_passes_when_fvg_aligns` | yes | `project/trading_project/tests/test_forex_direction_gate_fix.py` | `arena/a41fd997-trading-bot`, `arena/ad9c5dec-trading-bot`, `arena/b662648b-trading-bot`, `arena/bd0f0622-trading-bot`, `arena/c59ec6a3-trading-bot`, `arena/f3ca06dd-trading-bot` | `def test_real_gate_passes_when_fvg_aligns():` | UNKNOWN | yes |
| draw_on_liquidity | `render` | **no** | `split_zzz_pdf.py` | `arena/01a0f676-trading-bot` | `def render(self, index: int, count: int, first_page: int, last_page: int, full_pages: int, entries: list[tuple[str, int]]) -> None` | NO | no |

**Summary of the ONLY list:** 84 implementations; of these **20** have a name that exists nowhere on the backbone (`_fake_dec`, `_fake_study`, `add_concept_card`, `check_v2`, `cover`, `gate_v1_legacy`, `line_is_art`, `load_entries`, `pack`, `pick_round_robin`, `prep`, `render`, `sample_concept_windows`, `source_rule_for_swing`, `step_dups`, `step_probe`, `step_timeline`, `teacher_fvg_relation`, `test_continuation_bull_passes`, `toc_render`), and 64 are drifted copies of a backbone symbol.

## What this does NOT establish

- It does not judge quality or correctness, and it copies no code: only paths, signatures and hashes are recorded.
- A hit is a keyword match; the signature column is parsed, but a concept named in a docstring still produces a row until a human reads it.
- `causal` is a mechanical screen over the file's text (prefix slice vs forward index); UNKNOWN means the screen could not decide, and no value here is a proof.
- "Only on other branches" is a statement about this commit's hashes. It does not mean the branch is newer, better, or worth salvaging.
- It changes no branch, merges nothing, deletes nothing.
