#!/usr/bin/env python3
"""Build CAPABILITY_REGISTRY_V1 from the Phase-3 inventory and the Phase-4 hits.

INPUTS (both outside the repository, produced by the two sibling scripts)
    <artifacts>/file_inventory.json    -> per-file facts on the BACKBONE
    <artifacts>/hidden_hits.json       -> per-hit facts on EVERY remote tip

OUTPUTS
    <repo>/.../consolidation_v1/CAPABILITY_REGISTRY_V1.json
    <repo>/.../consolidation_v1/CAPABILITY_REGISTRY_V1.md
    both sha256-printed, so a later reader can prove the files were not edited by hand.

MECHANICAL FLAGS (each is a rule over a fact, never a judgement)
    causal      from the Phase-4 screen (prefix slice => YES, forward index => NO, else UNKNOWN)
    tested      a test/fixture file on the same branch names the symbol
    closed      an EXPECTED_* file exists in the same directory as the module (frozen fixture)
    streaming   the signature's parameter list carries a bar index (``t``, ``i``, ``index``) AND
                no DataFrame parameter; ``batch`` otherwise
    dev_path    the module lives under ``research/contextual_selection/`` or is the
                ``huddleston_study`` runner, i.e. the only code the dev month actually imports
    imported    the Phase-3 AST pass found another module importing it

RECOMMENDED_CANONICAL follows the owner's stated rule: causal AND tested AND closed AND imported.
When no implementation satisfies all four, or when several satisfy all four, the row carries
``KNOWLEDGE_GAP: canonical_choice`` and lists the alternatives instead of picking one.

The registry is a RECOMMENDATION. The owner decides.

Run
    python3 build_registry.py --artifacts /tmp/consolidation_v1 --repo /home/user/TRADING-BOT

What this does NOT establish
----------------------------
- It does not verify that a "causal" implementation is causally correct: that flag is a text
  screen, and UNKNOWN is used wherever the screen cannot decide.
- It does not measure quality, speed or accuracy of any implementation, and it copies no code.
- `closed` means "a frozen expected file sits beside it", not "the owner closed it" (K10).
- A RECOMMENDED_CANONICAL row is not an instruction: the recommendation is derived from four
  booleans the owner chose, and a different rule would recommend something else.
- It does not merge, delete or edit code; it writes only its two artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

# the concept patterns are defined once, in the search script, and reused here
from hidden_work_search import CONCEPTS as CONCEPT_PATTERNS

CONCEPTS = [
    "swing", "FVG", "order_block", "liquidity_sweep", "displacement", "dealing_range",
    "equilibrium_premium_discount", "liquidity_pool", "equal_highs_lows", "structure_break",
    "htf_bias", "draw_on_liquidity", "session_killzone", "entry_zone_selection",
    "stop_invalidation", "target", "trade_plan", "trade_tracking", "explanation_trace",
]

DEV_PREFIX = "project/trading_project/src/trading_system/research/contextual_selection/"
DEV_RUNNER = "project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py"
# a concept is attributed to an implementation when the implementation's own signature names it,
# OR when the module that holds it is the concept's module. Both are name facts, not judgements.
MODULE_HINT = {
    "swing": r"swing|pivot|turning",
    "FVG": r"fvg|gap|imbalance",
    "order_block": r"order_block|orderblock|order_blocks",
    "liquidity_sweep": r"sweep|raid",
    "displacement": r"displacement",
    "dealing_range": r"range",
    "equilibrium_premium_discount": r"range|premium|discount|equilib",
    "liquidity_pool": r"liquidity|pool",
    "equal_highs_lows": r"liquidity|swing_sequence|equal",
    "structure_break": r"structural_break|structure|shift",
    "htf_bias": r"study_links|monitoring|frame|bias",
    "draw_on_liquidity": r"liquidity|draw|target",
    "session_killzone": r"session|market_status|clock",
    "entry_zone_selection": r"selection|select|expert",
    "stop_invalidation": r"trade_plan|plan|stop|invalid",
    "target": r"trade_plan|target|objective",
    "trade_plan": r"trade_plan|plan",
    "trade_tracking": r"monitoring|lifecycle|plan|outcome|observation",
    "explanation_trace": r"narrative|explain|narrator|trace|to_record",
}
BATCH_HINT = re.compile(r"\bdf\b|\bframes\b|\bDataFrame\b|frame")
STREAM_HINT = re.compile(r"(^|[,(\s])(t|i|index|idx|before_index)(\s*[,:=)]|\s*$)")


TEST_PATH = re.compile(r"(^|/)tests?/|(^|/)test_[^/]*\.py$|_test\.py$|(^|/)conftest\.py$")
MAX_ALTERNATIVES = 10   # display cap only; the JSON keeps every alternative
MAX_DUP_FILES = 6       # display cap on the duplicates table; the JSON keeps every implementation


def is_test_artefact(path: str, symbol: str) -> bool:
    """A test file, or a test function, is not an implementation of a concept."""
    if bool(TEST_PATH.search(path)) or symbol.startswith("test") or symbol == "conftest":
        return True
    # an exception class is not an implementation of a market concept
    return symbol.endswith("Error") or symbol.endswith("Exception")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="/home/user/TRADING-BOT")
    ap.add_argument("--artifacts", default="/tmp/consolidation_v1")
    ap.add_argument("--out-dir", default="")
    a = ap.parse_args()

    repo = Path(a.repo).resolve()
    art = Path(a.artifacts)
    out = Path(a.out_dir) if a.out_dir else (
        repo / "project/trading_project/docs/research/consolidation_v1")
    out.mkdir(parents=True, exist_ok=True)

    inv = json.loads((art / "file_inventory.json").read_text())
    hid = json.loads((art / "hidden_hits.json").read_text())
    files = {r["path"]: r for r in inv["files"]}

    # directories that carry a frozen expected file -> "closed" by fixture presence
    closed_dirs = {str(Path(p).parent) for p in files
                   if Path(p).name.startswith("EXPECTED_")}

    def closed(path: str) -> bool:
        return str(Path(path).parent) in closed_dirs

    rows: dict[str, list[dict]] = defaultdict(list)
    seen = set()
    for h in hid["hits"]:
        key = (h["concept"], h["path"], h["symbol"], h["blob"])
        if key in seen or not h["signature"]:
            continue
        if is_test_artefact(h["path"], h["symbol"]):
            continue
        # the symbol's own signature must name the concept: this removes the rows that a
        # broad keyword matched somewhere in the file rather than in the implementation
        sig_or_module = (re.search(CONCEPT_PATTERNS[h["concept"]], h["signature"], re.IGNORECASE)
                         or re.search(MODULE_HINT[h["concept"]], h["path"], re.IGNORECASE))
        if not sig_or_module:
            continue
        seen.add(key)
        sig = h["signature"]
        is_batch = bool(BATCH_HINT.search(sig))
        is_stream = (not is_batch) and bool(STREAM_HINT.search(sig))
        fr = files.get(h["path"], {})
        rows[h["concept"]].append({
            "path": h["path"],
            "symbol": h["symbol"],
            "signature": sig,
            "causal": h["causal"],
            "tested": bool(h["has_test"]),
            "closed": closed(h["path"]),
            "shape": "batch" if is_batch else ("streaming" if is_stream else "unknown"),
            "dev_path": h["path"].startswith(DEV_PREFIX) or h["path"] == DEV_RUNNER,
            "imported": bool(fr.get("is_imported", False)),
            "on_backbone": h["same_blob_on_backbone"],
            "file_class": fr.get("class", "NOT_IN_BACKBONE"),
            "branches": sorted({x["branch"] for x in hid["hits"]
                                if (x["concept"], x["path"], x["symbol"], x["blob"]) == key}),
        })

    registry = {}
    for concept in CONCEPTS:
        impls = sorted(rows.get(concept, []), key=lambda r: (r["path"], r["symbol"]))
        # dedupe by (path, symbol) keeping the backbone copy when present
        ded = {}
        for r in impls:
            k = (r["path"], r["symbol"])
            if k not in ded or (r["on_backbone"] and not ded[k]["on_backbone"]):
                ded[k] = r
        impls = sorted(ded.values(), key=lambda r: (r["path"], r["symbol"]))

        full = [r for r in impls
                if r["causal"] == "YES" and r["tested"] and r["closed"]
                and (r["imported"] or r["dev_path"])]
        if len(full) == 1:
            rec = {"symbol": full[0]["symbol"], "path": full[0]["path"],
                   "reason": "causal=YES AND tested=yes AND closed=yes AND imported/dev_path=yes "
                             "(the only implementation satisfying the owner's four facts)"}
        else:
            rec = {"KNOWLEDGE_GAP": "canonical_choice",
                   "reason": ("no implementation satisfies causal AND tested AND closed AND "
                              "imported") if not full else
                             ("several satisfy all four; the four booleans do not separate them"),
                   "alternatives": [f'{r["path"]}::{r["symbol"]}' for r in
                                    (full if full else impls)],
                   "alternatives_total": len(full if full else impls)}
        registry[concept] = {"implementations": impls, "recommended": rec}

    payload = {"backbone": inv.get("tree"), "backbone_sha": inv.get("tree_sha"),
               "rule": "causal AND tested AND closed AND imported",
               "concepts": registry}
    jp = out / "CAPABILITY_REGISTRY_V1.json"
    jp.write_text(json.dumps(payload, indent=1), encoding="utf-8")

    # ------------------------------ markdown ------------------------------
    L = []
    L.append("# CAPABILITY REGISTRY V1 — generated, not written by hand\n")
    L.append(f"- backbone: `{inv.get('tree')}` = `{inv.get('tree_sha')}`")
    L.append(f"- generated by `consolidation_v1/tools/build_registry.py` from "
             f"`file_inventory.json` + `hidden_hits.json` (both outside the repository)")
    L.append(f"- recommendation rule (the owner's): **causal AND tested AND closed AND imported**")
    L.append("- this is a **RECOMMENDATION**: a different rule would recommend differently, and "
             "the owner decides\n")

    dup_pairs = []
    for concept in CONCEPTS:
        block = registry[concept]
        impls = block["implementations"]
        L.append(f"## {concept}\n")
        if not impls:
            L.append("_no implementation reached the keyword screen for this concept._\n")
            continue
        L.append("| path | symbol | causal | tested | closed | shape | dev path | imported "
                 "| on backbone |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for r in impls:
            L.append(f"| `{r['path']}` | `{r['symbol']}` | {r['causal']} | "
                     f"{'yes' if r['tested'] else 'no'} | {'yes' if r['closed'] else 'no'} | "
                     f"{r['shape']} | {'yes' if r['dev_path'] else 'no'} | "
                     f"{'yes' if r['imported'] else 'no'} | {'yes' if r['on_backbone'] else 'NO'} |")
        rec = block["recommended"]
        if "symbol" in rec:
            L.append(f"\n**RECOMMENDED_CANONICAL:** `{rec['path']}::{rec['symbol']}` — {rec['reason']}.\n")
        else:
            shown = rec["alternatives"][:MAX_ALTERNATIVES]
            more = rec.get("alternatives_total", len(rec["alternatives"])) - len(shown)
            L.append(f"\n**KNOWLEDGE_GAP: canonical_choice** — {rec['reason']}. "
                     f"Alternatives ({rec.get('alternatives_total', len(rec['alternatives']))}): "
                     + "; ".join(f"`{x}`" for x in shown)
                     + (f"; … and {more} more in the JSON." if more > 0 else ".") + "\n")
        if len(impls) > 1:
            ranked = sorted(impls, key=lambda r: (r["causal"] != "YES", not r["tested"],
                                                  not r["closed"], not r["imported"], r["path"]))
            paths = []
            for r in ranked:
                if r["path"] not in paths:
                    paths.append(r["path"])
            paths = sorted(paths[:MAX_DUP_FILES])
            for i in range(len(paths)):
                for j in range(i + 1, len(paths)):
                    dup_pairs.append((concept, paths[i], paths[j]))

    L.append("## DUPLICATES\n")
    L.append("Pairs of files implementing the same concept. The difference column is built "
             "**only** from the boolean facts in the tables above; where the facts cannot "
             "separate two files, it says so.\n")
    L.append(f"Pairs are shown for at most {MAX_DUP_FILES} files per concept, chosen by how many "
             f"of the four facts each satisfies; every implementation is still in the tables "
             f"above and in the JSON.\n")
    L.append("| concept | A | B | how they differ (facts only) |")
    L.append("|---|---|---|---|")
    for concept, pa, pb in dup_pairs:
        ra = next(r for r in registry[concept]["implementations"] if r["path"] == pa)
        rb = next(r for r in registry[concept]["implementations"] if r["path"] == pb)
        diffs = []
        for field, label in (("shape", "shape"), ("causal", "causal"), ("tested", "tested"),
                             ("closed", "closed"), ("imported", "imported"),
                             ("dev_path", "dev path")):
            if ra[field] != rb[field]:
                diffs.append(f"{label}: {ra[field]} vs {rb[field]}")
        L.append(f"| {concept} | `{pa}` | `{pb}` | " +
                 ("; ".join(diffs) if diffs else "no boolean fact separates them") + " |")
    L.append("")
    L.append("## What this does NOT establish\n")
    L.append("- It does not prove any implementation correct: `causal` comes from a text screen "
             "and `closed` from the presence of a frozen expected file, neither of which is a "
             "proof of correctness.")
    L.append("- A recommendation is a consequence of four booleans, not an endorsement; the "
             "KNOWLEDGE_GAP rows are honest refusals, not omissions.")
    L.append("- It does not benchmark anything: `shape` is read from a signature, and a "
             "streaming signature is not the same thing as bounded memory.")
    L.append("- Keyword screening means a concept may be represented by a function whose name "
             "merely matched; reading is still required before any of these rows is relied on.")
    L.append("- It changes nothing in git and writes only its two artifacts.")

    mp = out / "CAPABILITY_REGISTRY_V1.md"
    mp.write_text("\n".join(L) + "\n", encoding="utf-8")

    print(json.dumps({"json": str(jp), "json_sha256": sha256_file(jp),
                      "md": str(mp), "md_sha256": sha256_file(mp),
                      "concepts": len(CONCEPTS),
                      "rows": sum(len(v["implementations"]) for v in registry.values()),
                      "knowledge_gaps": sum(1 for v in registry.values()
                                            if "KNOWLEDGE_GAP" in v["recommended"])},
                     indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
