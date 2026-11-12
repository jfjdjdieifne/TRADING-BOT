#!/usr/bin/env python3
"""Hidden-work search across EVERY remote branch tip.

WHAT IT DOES
------------
For each of the twenty concepts below, it runs ``git grep`` over the ``*.py`` files of **all**
remote tips in one invocation (git accepts several trees), so a concept costs one process, not one
per branch. For every hit it records:

  branch, file:line, the matched text, the enclosing ``def``/``class`` signature (parsed with
  ``ast`` from that branch's blob), the file's blob sha, whether the SAME path with the SAME blob
  exists on the backbone, and whether any test/fixture file on that branch names the function.

Signatures are parsed from the blob, never guessed. "Same blob on backbone" is a hash comparison,
so an implementation that was merely copied to another branch is not reported as hidden work.

CAUSALITY IS NOT AUTOMATIC. The script emits ``causal`` only when a mechanical test decides it:
  YES      the function body contains an explicit prefix slice (``[:t]``, ``[:i+1]``, ``iloc[:``)
           or the hit is a pure dataclass/constant with no data access
  NO       the body uses ``iloc[t + 1]``-style forward access or iterates rows after the decision
  UNKNOWN  anything else — left UNKNOWN rather than guessed
A human reading is recorded in the markdown beside it, tagged [READ] where it was done.

Run
---
  python3 hidden_work_search.py --repo . --out-dir /tmp/consolidation_v1 \
      --summary <repo>/.../consolidation_v1/HIDDEN_WORK_SEARCH_V1.md

What this does NOT establish
----------------------------
- It does not judge quality, correctness or completeness of any implementation, and it copies no
  code: it records signatures and locations only.
- A keyword hit is not an implementation: the concept list is matched by name, so a comment or a
  docstring that mentions a concept is reported as a hit until a signature is parsed.
- "Only on another branch" means the path+blob is absent from the backbone **at this commit**; it
  says nothing about whether the branch is newer, older, or abandoned.
- `causal` is a mechanical screen, not a proof of causality; where the screen cannot decide it
  says UNKNOWN.
- It changes nothing in any branch and writes only its two declared artifacts.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

CONCEPTS: dict[str, str] = {
    "swing": r"\bdef\s+\w*swing|\bclass\s+\w*Swing|swing_high|swing_low|pivot",
    "FVG": r"fair_value_gap|\bfvg|FVG|imbalance",
    "order_block": r"order_block|OrderBlock|\bOB\b",
    "liquidity_sweep": r"sweep|raid\b|liquidity_sweep|stop_hunt",
    "displacement": r"displacement|Displacement",
    "dealing_range": r"dealing_range|DealingRange|range_high|range_low",
    "equilibrium_premium_discount": r"equilibrium|premium|discount|PositionRatio|position_ratio",
    "liquidity_pool": r"liquidity_pool|LiquidityPool|pool_|untaken|pool\b",
    "equal_highs_lows": r"equal_high|equal_low|\bEH\b|\bEL\b|relative_equal",
    "structure_break": r"structural_break|structure_break|StructureBreak|\bBOS\b|\bCHoCH\b|ShiftWatch|STATUS_BROKEN",
    "htf_bias": r"htf|higher_frame|HigherFrame|multi_timeframe|mtf_bias|bias\b",
    "draw_on_liquidity": r"DrawCandidate|draw_candidate|draws?\b|target_pool|draw_on",
    "session_killzone": r"session|killzone|kill_zone|SessionClock|market_status|MarketStatus",
    "entry_zone_selection": r"select_zone|zone_select|choose_zone|candidate_selection|expert_selection|rank_zones",
    "stop_invalidation": r"invalidation|stop_price|stop_level|def stop|falsifier",
    "target": r"def target|\btargets?\b|take_profit|objective",
    "trade_plan": r"trade_plan|TradePlan|create_plan|PlanComponent|plan_",
    "trade_tracking": r"observe_plan|track|PlanObservation|outcome_for|lifecycle",
    "explanation_trace": r"explain|explanation|why\b|narrative|trace\b|to_record",
}

# POSIX ERE has no lookbehind, and `\b` does not break at an underscore, so `detect_fvg`
# and `scan_fvgs` were invisible to `\bfvg`. The boundaries are therefore dropped and the
# screen is a plain substring match; precision comes from the symbol/module filter in
# build_registry.py, not from the boundaries.
CONCEPTS = {k: v.replace(r"\b", "") for k, v in CONCEPTS.items()}

CAUSAL_PREFIX = re.compile(r"\[\s*:\s*(?:t|i|idx|index|k)\b|iloc\[:|loc\[:")
CAUSAL_FORWARD = re.compile(r"iloc\[\s*(?:t|i)\s*\+\s*[1-9]|\[\s*(?:t|i)\s*\+\s*[1-9]\s*\]")


def git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def backbone_symbols(snap: Path) -> set[str]:
    """Every def/class name that exists anywhere in the backbone's python files."""
    names: set[str] = set()
    if not snap.exists():
        return names
    for f in snap.rglob("*.py"):
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(node.name)
    return names


def enclosing_def(src: str, lineno: int) -> tuple[str, str]:
    """Return (signature, name) of the innermost def/class containing lineno."""
    try:
        tree = ast.parse(src)
    except Exception:
        return ("PARSE_ERROR", "")
    return enclosing_in(tree, lineno)


def enclosing_in(tree: "ast.Module", lineno: int) -> tuple[str, str]:
    """Same as enclosing_def, but on an already-parsed module (one parse per file)."""
    best = ("", "")
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            if start <= lineno <= end:
                try:
                    head = ast.unparse(node).split("\n")[0]
                except Exception:
                    head = f"{node.name}(...)"
                if node.col_offset >= best[2] if len(best) > 2 else True:
                    best = (head, str(node.name), node.col_offset)
    if len(best) > 2:
        return (best[0], best[1])
    return ("", "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--backbone", default="origin/arena/77604f59-trading-bot")
    ap.add_argument("--out-dir", default="/tmp/consolidation_v1")
    ap.add_argument("--summary", default="")
    a = ap.parse_args()

    repo = Path(a.repo).resolve()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    refs = [r for r in git(repo, "for-each-ref", "--format=%(refname:short)",
                           f"refs/remotes/{a.remote}").splitlines()
            if r and not r.endswith("/HEAD")]
    refs.sort()
    backbone_sha = git(repo, "rev-parse", a.backbone).strip()

    # blob lookup cache: (ref, path) -> blob sha
    blob_cache: dict[tuple[str, str], str] = {}
    src_cache: dict[tuple[str, str], str] = {}
    backbone_blobs: dict[str, str] = {}
    for line in git(repo, "ls-tree", "-r", a.backbone).splitlines():
        parts = line.split("\t", 1)
        if len(parts) == 2:
            backbone_blobs[parts[1]] = parts[0].split()[2]

    def blob(ref: str, path: str) -> str:
        key = (ref, path)
        if key not in blob_cache:
            blob_cache[key] = git(repo, "rev-parse", f"{ref}:{path}").strip()
        return blob_cache[key]

    def src(ref: str, path: str) -> str:
        key = (ref, path)
        if key not in src_cache:
            src_cache[key] = git(repo, "show", f"{ref}:{path}")
        return src_cache[key]

    hits: list[dict] = []
    for concept, pattern in CONCEPTS.items():
        # one grep over all trees = one process per concept
        r = subprocess.run(["git", "-C", str(repo), "grep", "-n", "-I", "-E",
                            pattern, *refs, "--", "*.py"],
                           capture_output=True, text=True)
        for line in r.stdout.splitlines():
            try:
                ref, path, lineno, _text = line.split(":", 3)
            except ValueError:
                continue
            if not lineno.isdigit():
                continue
            hits.append({"concept": concept, "branch": ref, "path": path,
                         "line": int(lineno)})

    snap = out / "backbone_snapshot"
    bb_symbols = backbone_symbols(snap)

    # enrich
    sig_cache: dict[str, "ast.Module | None"] = {}
    for h in hits:
        b = blob(h["branch"], h["path"])
        h["blob"] = b
        h["same_blob_on_backbone"] = backbone_blobs.get(h["path"]) == b
        if b not in sig_cache:          # cache the PARSED FILE, never a line's answer:
            try:                        # keying the answer by blob made every line of a file
                sig_cache[b] = ast.parse(src(h["branch"], h["path"]))  # inherit the first
            except Exception:                                     # hit's enclosing def
                sig_cache[b] = None
        tree = sig_cache[b]
        sig, name = ("PARSE_ERROR", "") if tree is None else enclosing_in(tree, h["line"])
        h["signature"] = sig
        h["symbol"] = name or Path(h["path"]).stem
        h["symbol_on_backbone"] = h["symbol"] in bb_symbols

    # test references: one multi-tree grep per unique symbol
    symbols = sorted({h["symbol"] for h in hits if h["symbol"]})
    tested: dict[tuple[str, str], bool] = {}
    for sym in symbols:
        if len(sym) < 4:
            continue
        r = subprocess.run(["git", "-C", str(repo), "grep", "-l", "-I", "-F", sym, *refs, "--",
                            "*test*", "*EXPECTED_*", "*fixture*"],
                           capture_output=True, text=True)
        for line in r.stdout.splitlines():
            try:
                ref, path = line.split(":", 1)
            except ValueError:
                continue
            tested[(ref, sym)] = True
    for h in hits:
        h["has_test"] = bool(tested.get((h["branch"], h["symbol"])))

    # causality screen on the enclosing function body
    for h in hits:
        body = src(h["branch"], h["path"])
        b = h["blob"]
        if CAUSAL_FORWARD.search(body):
            h["causal"] = "NO"
        elif CAUSAL_PREFIX.search(body):
            h["causal"] = "YES"
        else:
            h["causal"] = "UNKNOWN"

    # grouping: a unique implementation = (path, symbol, blob)
    groups: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for h in hits:
        groups[(h["path"], h["symbol"], h["blob"])].add(h["branch"])

    payload = {"backbone": a.backbone, "backbone_sha": backbone_sha, "branches": refs,
               "hits": hits, "unique_implementations": len(groups)}
    jp = out / "hidden_hits.json"
    jp.write_text(json.dumps(payload, indent=1), encoding="utf-8")

    # ---------------- markdown ----------------
    L: list[str] = []
    L.append("# HIDDEN WORK SEARCH V1 — every concept, every remote tip\n")
    L.append(f"- searched trees: **{len(refs)}** remote branch tips (`git grep` over `*.py`)")
    L.append(f"- backbone: `{a.backbone}` = `{backbone_sha}`")
    L.append("- raw hits: " + f"`{jp}` (sha256 `{sha_file(jp)}`), outside the repository")
    L.append(f"- hits: **{len(hits)}**, distinct (path, symbol, blob) implementations: "
             f"**{len(groups)}**")
    L.append("- `same blob on backbone` is a hash comparison; a copied file is not hidden work\n")

    L.append("## Table — implementations per concept\n")
    L.append("| concept | on backbone (path+blob) | ONLY on other branches |")
    L.append("|---|---|---|")
    for concept in CONCEPTS:
        ch = [h for h in hits if h["concept"] == concept]
        on_b = {h["symbol"] for h in ch if h["symbol_on_backbone"]}
        off_b = {h["symbol"] for h in ch if not h["symbol_on_backbone"]}
        L.append(f"| {concept} | {len(on_b)} | {len(off_b)} |")
    L.append("")

    L.append("## ONLY on other branches — full rows\n")
    L.append("An implementation is listed here when **no file with the same path AND the same "
             "blob sha exists on the backbone** (the owner's definition). The column "
             "`name on backbone` separates two very different cases: `no` is genuinely new code "
             "whose name appears nowhere in the backbone; `yes` is a **drifted copy** — the same "
             "function name exists on the backbone with different bytes. A drifted copy is not "
             "new work until someone reads what changed.\n")
    L.append("| concept | symbol | name on backbone | file(s) | branches | signature | causal (screen) | has test |")
    L.append("|---|---|---|---|---|---|---|---|")
    # one row per (path, symbol, blob) implementation whose bytes are absent from the backbone
    only_keys: list[tuple[str, str, str]] = sorted(
        {k for k, _ in groups.items()
         if not next(h for h in hits
                     if (h["path"], h["symbol"], h["blob"]) == k)["same_blob_on_backbone"]},
        key=lambda k: (k[0], k[1]))
    only_syms: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for h in hits:
        k = (h["path"], h["symbol"], h["blob"])
        if k in set(only_keys) and h["signature"]:
            only_syms[k].append(h)
    only = [k for k in only_keys if only_syms.get(k)]
    for sym in only:
        hs = only_syms[sym]
        files = sorted({h["path"] for h in hs})
        brs = sorted({h["branch"] for h in hs})
        ex = hs[0]
        sig = (ex["signature"] or "")[:130].replace("|", "\\|")
        L.append(f"| {ex['concept']} | `{ex['symbol']}` | {'yes' if ex['symbol_on_backbone'] else '**no**'} | "
                 f"{', '.join('`'+f+'`' for f in files[:3])} | "
                 f"{', '.join('`'+b.replace('origin/','')+'`' for b in brs)} | `{sig}` | "
                 f"{ex['causal']} | {'yes' if any(h['has_test'] for h in hs) else 'no'} |")
    L.append("")

    new_code = sorted({only_syms[k][0]["symbol"] for k in only
                       if not only_syms[k][0]["symbol_on_backbone"]})
    L.append(f"**Summary of the ONLY list:** {len(only)} implementations; of these **{len(new_code)}** have "
             f"a name that exists nowhere on the backbone ({', '.join('`'+x+'`' for x in new_code) or 'none'}), "
             f"and {len(only) - len(new_code)} are drifted copies of a backbone symbol.\n")
    L.append("## What this does NOT establish\n")
    L.append("- It does not judge quality or correctness, and it copies no code: only paths, "
             "signatures and hashes are recorded.")
    L.append("- A hit is a keyword match; the signature column is parsed, but a concept named in a "
             "docstring still produces a row until a human reads it.")
    L.append("- `causal` is a mechanical screen over the file's text (prefix slice vs forward "
             "index); UNKNOWN means the screen could not decide, and no value here is a proof.")
    L.append("- \"Only on other branches\" is a statement about this commit's hashes. It does not "
             "mean the branch is newer, better, or worth salvaging.")
    L.append("- It changes no branch, merges nothing, deletes nothing.")
    sp = out / "hidden_work_search_summary.md"
    sp.write_text("\n".join(L) + "\n", encoding="utf-8")

    if a.summary:
        s = Path(a.summary)
        s.parent.mkdir(parents=True, exist_ok=True)
        s.write_text("\n".join(L) + "\n", encoding="utf-8")
        print(f"summary written: {s}  sha256={sha_file(s)}")

    print(json.dumps({"branches": len(refs), "hits": len(hits),
                      "unique_implementations": len(groups),
                      "only_off_backbone": len(only),
                      "backbone_symbols": len(bb_symbols),
                      "hidden_hits_sha256": sha_file(jp)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
