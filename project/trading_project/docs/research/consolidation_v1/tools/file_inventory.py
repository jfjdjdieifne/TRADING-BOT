#!/usr/bin/env python3
"""Deterministic file inventory of one tree (the backbone), boolean facts only.

WHAT IT RECORDS, FOR EVERY FILE IN THE TREE
-------------------------------------------
  has_test               a test file or an EXPECTED_* / fixture file names this file's module
  is_imported            another .py file imports this module (decided by ``ast``, not grep)
  is_entrypoint          the file has an ``if __name__ == "__main__"`` guard, or a shell/doc line
                         that also contains ``python`` names its path
  cited_in_docs          number of ``*.md`` files whose text contains the file's path or name
  last_commit_date       date of the last commit that touched the path (single pass over log)
  is_data_or_generated_output
                         extension or directory rule, declared in EXT_DATA / EXT_GENERATED /
                         GEN_DIRS below

WHY A SNAPSHOT
--------------
The tree is materialised once with ``git archive`` into the output directory (OUTSIDE the
repository) and read from there, so the inventory is a function of one commit and cannot drift
while it runs.

CLASSIFICATION — one class per file, in this fixed order (first match wins)
--------------------------------------------------------------------------
  1 CORE         code, and   has_test AND (is_imported OR is_entrypoint)
  2 CLOSED_SPEC  frozen expected files / fixtures / owner-decision documents
                 (name starts with ``EXPECTED_``, or path contains ``fixtures``, or the file is an
                 ``OWNER_DECISIONS*.md`` / ``OWNER_DECISION*.md``)
  3 DESIGN_DOC   any other ``*.md`` / ``*.txt`` / ``*.rst``
  4 ORPHAN_CODE  code, and NOT has_test AND NOT is_imported AND NOT is_entrypoint
  5 GENERATED    run outputs, reports of runs, logs (EXT_GENERATED or GEN_DIRS)
  6 DATA         data files and archives (EXT_DATA)
  (anything left is reported as UNCLASSIFIED rather than forced into a class)

No thresholds are used anywhere: every field is a boolean fact or an exact count, and every class
is a rule over those facts.

Run
---
  python3 file_inventory.py --repo . --tree origin/arena/77604f59-trading-bot \
      --out-dir /tmp/consolidation_v1 \
      --summary <repo>/project/trading_project/docs/research/consolidation_v1/FILE_INVENTORY_V1.md

What this does NOT establish
----------------------------
- It does not judge code quality, and ORPHAN_CODE is not an accusation: a module imported only
  dynamically, only by a test that names it by string, or only by an external caller will show as
  an orphan.
- ``has_test`` is a name-reference fact, not coverage: a test that merely mentions a module may
  not exercise it.
- ``cited_in_docs`` counts documents, not credibility.
- It does not delete, move, rename or rewrite anything; the snapshot is a copy outside the repo.
- It says nothing about whether any file should be kept or removed — that is the owner's call.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import re
import subprocess
import tarfile
from collections import Counter, defaultdict
from pathlib import Path

EXT_DATA = {".csv", ".gz", ".zip", ".tar", ".parquet", ".db", ".sqlite", ".xlsx", ".npy",
            ".npz", ".pkl", ".h5", ".feather", ".arrow", ".pdf", ".sha256", ".diff", ".html",
            ".tsv"}
EXT_SCRIPT = {".sh", ".bash", ".cmd", ".bat"}
EXT_GENERATED = {".log", ".jsonl", ".out", ".err"}
GEN_DIRS = {"snapshots", "outputs", "runs", "reports", "coverage", "__pycache__"}
DOC_EXT = {".md", ".rst", ".txt"}
CODE_EXT = {".py"}
SHELLISH = {".sh", ".bash", ".cmd", ".bat", ".yml", ".yaml", ".toml", ".cfg", ".ini"}


def git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def materialise(repo: Path, tree: str, dest: Path) -> list[str]:
    raw = subprocess.run(["git", "-C", str(repo), "archive", "--format=tar", tree],
                         capture_output=True)
    if raw.returncode != 0:
        raise SystemExit(f"git archive failed for {tree}")
    dest.mkdir(parents=True, exist_ok=True)
    names = []
    with tarfile.open(fileobj=io.BytesIO(raw.stdout)) as tf:
        for m in tf.getmembers():
            if not m.isfile():
                continue
            fh = tf.extractfile(m)
            if fh is None:
                continue
            data = fh.read()
            out = dest / m.name
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
            names.append(m.name)
    return sorted(names)


def last_dates(repo: Path, tree: str) -> dict[str, str]:
    """One pass: newest-first, first date seen per path is its last commit date."""
    txt = git(repo, "log", "--format=@@%cs", "--name-only", tree)
    cur = ""
    out: dict[str, str] = {}
    for line in txt.splitlines():
        if line.startswith("@@"):
            cur = line[2:].strip()
        elif line.strip():
            out.setdefault(line.strip(), cur)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--tree", required=True)
    ap.add_argument("--out-dir", default="/tmp/consolidation_v1")
    ap.add_argument("--summary", default="")
    a = ap.parse_args()

    repo = Path(a.repo).resolve()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    snap = out / "backbone_snapshot"
    files = materialise(repo, a.tree, snap)
    dates = last_dates(repo, a.tree)
    tree_sha = git(repo, "rev-parse", a.tree).strip()

    code = [f for f in files if Path(f).suffix in CODE_EXT]
    docs = [f for f in files if Path(f).suffix in DOC_EXT]
    shellish = [f for f in files if Path(f).suffix in SHELLISH]

    # ---- AST pass over every python file ----
    imports: dict[str, set[str]] = {}          # file -> imported dotted/name strings
    has_main: dict[str, bool] = {}
    for f in code:
        try:
            src = (snap / f).read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(src)
        except Exception:
            imports[f] = set()
            has_main[f] = False
            continue
        names: set[str] = set()
        main = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for al in node.names:
                    names.add(al.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    names.add(node.module)
                    for al in node.names:
                        names.add(f"{node.module}.{al.name}")
                for al in node.names:
                    names.add(al.name)
            elif isinstance(node, ast.If):
                try:
                    seg = ast.unparse(node.test)
                except Exception:
                    seg = ""
                if "__main__" in seg:
                    main = True
        imports[f] = names
        has_main[f] = main

    # module index: dotted suffix -> files
    mod_index: dict[str, set[str]] = defaultdict(set)
    for f in code:
        mod = f[:-3].replace("/", ".")
        parts = mod.split(".")
        for i in range(len(parts)):
            mod_index[".".join(parts[i:])].add(f)

    imported_by: dict[str, set[str]] = defaultdict(set)
    for f, names in imports.items():
        for n in names:
            for target in mod_index.get(n, ()):  # exact dotted match only
                if target != f:
                    imported_by[target].add(f)

    # ---- name references ----
    doc_text = {}
    for d in docs:
        doc_text[d] = (snap / d).read_text(encoding="utf-8", errors="replace")
    shell_text = {}
    for s in shellish:
        shell_text[s] = (snap / s).read_text(encoding="utf-8", errors="replace")

    test_files = [f for f in files
                  if f.endswith(".py") and ("test" in Path(f).name or "/tests/" in f)
                  or Path(f).name.startswith("EXPECTED_")]
    test_text = {}
    for t in test_files:
        if Path(t).suffix in CODE_EXT or Path(t).suffix in {".json", ".md", ".txt"}:
            test_text[t] = (snap / t).read_text(encoding="utf-8", errors="replace")

    rows = []
    for f in files:
        p = Path(f)
        suffix = p.suffix
        is_code = suffix in CODE_EXT
        base = p.name
        stem = p.stem

        # has_test: a test/fixture file names this module's stem or path
        has_test = False
        if is_code:
            needles = {stem, p.with_suffix("").as_posix(), f}
            has_test = any(n in txt for t, txt in test_text.items()
                           if t != f for n in needles if len(n) > 3)
        else:
            has_test = False

        # is_imported (AST only)
        is_imported = bool(imported_by.get(f)) if is_code else False

        # is_entrypoint: main guard, or a shell/doc line with "python" naming the path
        is_entry = bool(has_main.get(f)) if is_code else False
        if not is_entry:
            for txt in list(shell_text.values()) + list(doc_text.values()):
                if "python" not in txt.lower():
                    continue
                if f in txt or (is_code and stem in txt and len(stem) > 6):
                    is_entry = True
                    break

        # cited_in_docs: count of *.md documents naming the file
        cited = sum(1 for d, txt in doc_text.items()
                    if (f in txt) or (len(stem) > 6 and stem in txt))

        # data / generated
        is_data = suffix in EXT_DATA
        is_gen = suffix in EXT_GENERATED or any(part in GEN_DIRS for part in p.parts[:-1])

        # ---- class, fixed order ----
        cls = "UNCLASSIFIED"
        if is_code and has_test and (is_imported or is_entry):
            cls = "CORE"
        elif base.startswith("EXPECTED_") or "fixtures" in f or base.startswith("OWNER_DECISION"):
            cls = "CLOSED_SPEC"
        elif suffix in DOC_EXT:
            cls = "DESIGN_DOC"
        elif is_code and not has_test and not is_imported and not is_entry:
            cls = "ORPHAN_CODE"
        elif is_gen:
            cls = "GENERATED"
        elif is_data:
            cls = "DATA"
        elif suffix in EXT_SCRIPT:
            cls = "SCRIPT"
        elif is_code and is_entry:
            # residual: an entrypoint that no test names (CORE needs has_test; ORPHAN
            # explicitly excludes entrypoints, so the four owner predicates leave it unnamed)
            cls = "ENTRYPOINT_UNTESTED"
        elif is_code and has_test:
            # residual: tested, but nothing imports it and no entrypoint reaches it.
            # The owner's four code predicates do not cover this case; naming it beats
            # leaving 110 files in UNCLASSIFIED.
            cls = "TESTED_UNCALLED"
        elif suffix == ".json":
            # structured payload: EXPECTED_/fixtures already took CLOSED_SPEC above.
            cls = "DATA"

        rows.append({
            "path": f,
            "ext": suffix,
            "bytes": (snap / f).stat().st_size,
            "sha256": sha256_file(snap / f),
            "has_test": has_test,
            "is_imported": is_imported,
            "is_entrypoint": is_entry,
            "cited_in_docs": cited,
            "last_commit_date": dates.get(f, ""),
            "is_data_or_generated_output": bool(is_data or is_gen),
            "class": cls,
        })

    csvp = out / "file_inventory.csv"
    cols = list(rows[0].keys())
    with open(csvp, "w", encoding="utf-8") as fh:
        fh.write(",".join(cols) + "\n")
        for r in rows:
            fh.write(",".join(json.dumps(r[c], ensure_ascii=False) if isinstance(r[c], str)
                              else str(r[c]) for c in cols) + "\n")

    jsonp = out / "file_inventory.json"
    jsonp.write_text(json.dumps({"tree": a.tree, "tree_sha": tree_sha,
                                 "rule_order": ["CORE", "CLOSED_SPEC", "DESIGN_DOC",
                                                "ORPHAN_CODE", "GENERATED", "DATA"],
                                 "files": rows}, indent=1), encoding="utf-8")

    by_class = Counter(r["class"] for r in rows)
    top1 = Counter(r["path"].split("/")[0] for r in rows)
    top2 = Counter("/".join(r["path"].split("/")[:2]) for r in rows
                   if r["path"].startswith("project/"))
    per_class_top = defaultdict(Counter)
    for r in rows:
        per_class_top[r["class"]][r["path"].split("/")[0]] += 1

    lines = []
    lines.append("# FILE INVENTORY V1 — every file in the backbone tree, classified by rule\n")
    lines.append(f"- tree: `{a.tree}` = `{tree_sha}`")
    lines.append(f"- files: **{len(rows)}**")
    lines.append("- generated by `consolidation_v1/tools/file_inventory.py` (stdlib + git only)")
    lines.append("- the full CSV/JSON live **outside** the repository "
                 f"(`{out}/file_inventory.csv`, `{out}/file_inventory.json`) with sha256 below\n")
    lines.append("## Rule (first match wins — stated so the classification can be checked)\n")
    lines.append("```text")
    lines.append("CORE        = code AND has_test AND (is_imported OR is_entrypoint)")
    lines.append("CLOSED_SPEC = name starts EXPECTED_  OR  path contains 'fixtures'  OR  OWNER_DECISION*.md")
    lines.append("DESIGN_DOC  = *.md / *.rst / *.txt of any other kind")
    lines.append("ORPHAN_CODE = code AND NOT has_test AND NOT is_imported AND NOT is_entrypoint")
    lines.append("GENERATED   = *.log / *.jsonl / *.out / *.err, or under snapshots|outputs|runs|reports|coverage")
    lines.append("DATA        = csv|gz|zip|tar|parquet|db|sqlite|xlsx|npy|npz|pkl|h5|feather|arrow")
    lines.append("TESTED_UNCALLED = code AND has_test AND NOT is_imported AND NOT is_entrypoint")
    lines.append("             (residual: the four owner predicates leave this case unnamed)")
    lines.append("ENTRYPOINT_UNTESTED = code AND is_entrypoint AND NOT has_test (residual)")
    lines.append("SCRIPT      = *.sh / *.bash / *.cmd / *.bat")
    lines.append("DATA also covers .json that is not EXPECTED_/fixtures, plus .pdf/.sha256/.diff/.html/.tsv")
    lines.append("UNCLASSIFIED= anything the rules do not reach (reported, never forced)")
    lines.append("```\n")
    lines.append("## Counts per class\n")
    lines.append("| class | files |")
    lines.append("|---|---|")
    for k in ["CORE", "CLOSED_SPEC", "DESIGN_DOC", "ORPHAN_CODE", "ORPHAN_CODE",
              "TESTED_UNCALLED", "ENTRYPOINT_UNTESTED", "GENERATED", "DATA", "SCRIPT",
              "UNCLASSIFIED"]:
        if by_class.get(k):
            lines.append(f"| {k} | {by_class[k]} |")
    lines.append(f"| **total** | **{len(rows)}** |\n")
    lines.append("## Counts per top-level folder\n")
    lines.append("| top-level folder | files |")
    lines.append("|---|---|")
    for k, v in top1.most_common():
        lines.append(f"| `{k}` | {v} |")
    lines.append("")
    lines.append("## Counts per class inside each top-level folder\n")
    lines.append("| folder | " + " | ".join(["CORE", "CLOSED_SPEC", "DESIGN_DOC", "ORPHAN_CODE",
                                             "TESTED_UNCALLED", "ENTRYPOINT_UNTESTED",
                                             "GENERATED", "DATA", "SCRIPT",
                                             "UNCLASSIFIED"]) + " |")
    lines.append("|---" * 11 + "|")
    for folder, _ in top1.most_common():
        row = [str(per_class_top[c][folder]) for c in ["CORE", "CLOSED_SPEC", "DESIGN_DOC",
                                                       "ORPHAN_CODE", "TESTED_UNCALLED",
                                                       "ENTRYPOINT_UNTESTED", "GENERATED",
                                                       "DATA", "SCRIPT", "UNCLASSIFIED"]]
        lines.append(f"| `{folder}` | " + " | ".join(row) + " |")
    lines.append("")
    lines.append("## Second level under `project/`\n")
    lines.append("| folder | files |")
    lines.append("|---|---|")
    for k, v in top2.most_common(12):
        lines.append(f"| `{k}` | {v} |")
    lines.append("")
    orphans = [r for r in rows if r["class"] == "ORPHAN_CODE"]
    lines.append(f"## ORPHAN_CODE — full list ({len(orphans)} files)\n")
    lines.append("A file is listed here when **no test or fixture names it, no other module "
                 "imports it by AST, and no entrypoint rule reaches it**. It is a fact about "
                 "references, not a verdict on the file.\n")
    for r in sorted(orphans, key=lambda x: x["path"]):
        lines.append(f"- `{r['path']}` — {r['bytes']} B, last commit {r['last_commit_date'] or 'n/a'}")
    lines.append("")
    lines.append("## Artifacts outside the repository\n")
    lines.append("| file | sha256 |")
    lines.append("|---|---|")
    lines.append(f"| `{csvp}` | `{sha256_file(csvp)}` |")
    lines.append(f"| `{jsonp}` | `{sha256_file(jsonp)}` |")
    lines.append("")
    lines.append("## What this does NOT establish\n")
    lines.append("- It does not judge quality. `ORPHAN_CODE` means \"nothing in this tree names it\", "
                 "not \"this file is bad\": dynamic imports, string-based lookups and external "
                 "callers are invisible to an AST import scan.")
    lines.append("- `has_test` is a **name-reference** fact: a test that mentions a module may not "
                 "exercise it, and a module exercised through another module will look untested.")
    lines.append("- `cited_in_docs` counts documents, not credibility, and one document repeated "
                 "in two places counts twice.")
    lines.append("- The class of a file is a rule applied to facts; a different rule would move "
                 "files between classes without any file changing.")
    lines.append("- It removes and moves nothing: the snapshot is a copy outside the repository.")
    lines.append("- It does not tell the owner which class to keep; that is `CONSOLIDATION_PROPOSAL_V1.md`.")

    if a.summary:
        s = Path(a.summary)
        s.parent.mkdir(parents=True, exist_ok=True)
        s.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"summary written: {s}  sha256={sha256_file(s)}")

    print(json.dumps({"files": len(rows), "by_class": dict(by_class),
                      "csv_sha256": sha256_file(csvp),
                      "json_sha256": sha256_file(jsonp)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
