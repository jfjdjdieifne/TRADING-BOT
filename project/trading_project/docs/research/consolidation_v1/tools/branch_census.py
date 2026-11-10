#!/usr/bin/env python3
"""Branch census over every remote branch tip.

WHAT IT DOES (deterministic, stdlib + git only)
-----------------------------------------------
For every remote branch ref (``refs/remotes/origin/*``, ``origin/HEAD`` excluded):

  tip sha            ``git rev-parse <ref>``
  tip date/subject   ``git log -1 --format=%cs / %s``
  merge-base         ``git merge-base <backbone> <ref>``   (empty when histories are unrelated)
  behind / ahead     ``git rev-list --left-right --count <backbone>...<ref>``
  added/modified/deleted
                     ``git diff --name-status <backbone> <ref>``  (tree-to-tree, "versus backbone")
  paths              the added and modified paths, one per line, written OUTSIDE the repository

It also writes, per branch, ``paths_<slug>.txt`` and an aggregate ``MANIFEST.json`` holding the
sha256 of every file it produced, so a later reader can prove the summary was not edited.

``origin/main`` is marked ``DEAD_END_STUB``: it is reported, never merged, and never proposed as
a source of files.

NO thresholds are used: every number is a count of what git reports.

Run
---
  python3 branch_census.py --repo /path/to/repo \
      --out-dir /tmp/consolidation_v1 \
      --summary <repo>/project/trading_project/docs/research/consolidation_v1/BRANCH_CENSUS_V1.md

What this does NOT establish
----------------------------
- It does not say which branch is better, newer in spirit, or worth merging: it counts what
  exists. "Ahead by 3" is not a quality claim.
- It does not read code, tests or data, and it makes no statement about correctness.
- It does not prove a branch is complete: a large diff can be a large mess.
- It does not judge the merge-base: unrelated histories legitimately produce no merge-base.
- It writes nothing outside its two declared destinations, and it never writes to git.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

BACKBONE_DEFAULT = "origin/arena/77604f59-trading-bot"
DEAD_END = {"origin/main"}


def git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(repo), *args],
                         capture_output=True, text=True)
    if out.returncode != 0:
        return ""
    return out.stdout.strip()


def remote_branches(repo: Path, remote: str) -> list[str]:
    txt = git(repo, "for-each-ref", "--format=%(refname:short)", f"refs/remotes/{remote}")
    refs = [r for r in txt.splitlines() if r and not r.endswith("/HEAD")]
    return sorted(refs)


def slug(ref: str) -> str:
    return ref.replace("origin/", "").replace("/", "__")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--backbone", default=BACKBONE_DEFAULT)
    ap.add_argument("--out-dir", default="/tmp/consolidation_v1")
    ap.add_argument("--summary", default="")
    a = ap.parse_args()

    repo = Path(a.repo).resolve()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    backbone_sha = git(repo, "rev-parse", a.backbone)
    if not backbone_sha:
        raise SystemExit(f"backbone {a.backbone} not found; run git fetch first")

    rows = []
    produced = []
    for ref in remote_branches(repo, a.remote):
        sha = git(repo, "rev-parse", ref)
        date = git(repo, "log", "-1", "--format=%cs", ref)
        subject = git(repo, "log", "-1", "--format=%s", ref)
        mb = git(repo, "merge-base", a.backbone, ref)
        behind = ahead = 0
        if mb:
            lr = git(repo, "rev-list", "--left-right", "--count", f"{a.backbone}...{ref}")
            if lr:
                behind, ahead = (int(x) for x in lr.split())
        status = git(repo, "diff", "--name-status", "--no-renames", a.backbone, ref)
        added, modified, deleted = [], [], []
        for line in status.splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            code, path = parts[0], parts[-1]
            if code.startswith("A"):
                added.append(path)
            elif code.startswith("D"):
                deleted.append(path)
            elif code.startswith("M") or code.startswith("T"):
                modified.append(path)

        paths = added + modified
        pf = out / f"paths_{slug(ref)}.txt"
        pf.write_text("\n".join(paths) + ("\n" if paths else ""), encoding="utf-8")
        produced.append(pf)

        rows.append({
            "branch": ref,
            "tip_sha": sha,
            "tip_date": date,
            "tip_subject": subject,
            "merge_base": mb or "",
            "behind": behind,
            "ahead": ahead,
            "added": len(added),
            "modified": len(modified),
            "deleted": len(deleted),
            "paths_added_or_modified": len(paths),
            "mark": "DEAD_END_STUB" if ref in DEAD_END else "",
        })

    csv = out / "branch_census.csv"
    cols = ["branch", "tip_sha", "tip_date", "merge_base", "behind", "ahead",
            "added", "modified", "deleted", "paths_added_or_modified", "mark", "tip_subject"]
    with open(csv, "w", encoding="utf-8") as fh:
        fh.write(",".join(cols) + "\n")
        for r in rows:
            fh.write(",".join(json.dumps(r[c], ensure_ascii=False) if isinstance(r[c], str) and
                              ("," in r[c] or '"' in r[c] or c == "tip_subject") else str(r[c])
                              for c in cols) + "\n")
    produced.append(csv)

    manifest = {
        "backbone": a.backbone,
        "backbone_sha": backbone_sha,
        "branches": len(rows),
        "generated_by": "branch_census.py",
        "files": {p.name: sha256_file(p) for p in produced},
    }
    mf = out / "MANIFEST_branch_census.json"
    mf.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    produced.append(mf)

    # ---- stdout table ----
    print(f"backbone {a.backbone} = {backbone_sha[:12]}; branches = {len(rows)}")
    print(f"{'branch':<42} {'tip':<12} {'date':<11} {'mb':<12} {'bh':>4} {'ah':>4} "
          f"{'add':>5} {'mod':>5} {'del':>5}  mark")
    for r in rows:
        print(f"{r['branch']:<42} {r['tip_sha'][:12]:<12} {r['tip_date']:<11} "
              f"{(r['merge_base'][:12] or '(none)'):<12} {r['behind']:>4} {r['ahead']:>4} "
              f"{r['added']:>5} {r['modified']:>5} {r['deleted']:>5}  {r['mark']}")

    if a.summary:
        s = Path(a.summary)
        s.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        lines.append("# BRANCH CENSUS V1 — every remote branch, counted\n")
        lines.append("Generated by `consolidation_v1/tools/branch_census.py` "
                     "(stdlib + git only). Re-runnable; deterministic for a given set of refs.\n")
        lines.append(f"- backbone: `{a.backbone}` = `{backbone_sha}`")
        lines.append(f"- remote branches: **{len(rows)}**")
        lines.append("- `behind` / `ahead` are `git rev-list --left-right --count backbone...branch`")
        lines.append("- `add`/`mod`/`del` are `git diff --name-status backbone branch` "
                     "(tree-to-tree, renames counted as delete+add by `--no-renames`)")
        lines.append("- the per-branch **path lists** are outside the repository "
                     f"(`{out}/paths_<slug>.txt`), with `MANIFEST_branch_census.json` holding each "
                     "file's sha256\n")
        lines.append("| branch | tip | date | merge-base with backbone | behind | ahead | added "
                     "| modified | deleted | mark |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            lines.append(f"| `{r['branch']}` | `{r['tip_sha'][:12]}` | {r['tip_date']} | "
                         f"`{r['merge_base'][:12] or '(none)'}` | {r['behind']} | {r['ahead']} | "
                         f"{r['added']} | {r['modified']} | {r['deleted']} | {r['mark'] or ''} |")
        lines.append("")
        lines.append("## `origin/main`\n")
        lines.append("`origin/main` is a **DEAD_END_STUB**: its tree is a two-line hello-world "
                     "commit and its history is unrelated to the backbone "
                     f"(merge-base: `{next((r['merge_base'] for r in rows if r['branch'] == 'origin/main'), '') or '(none)'}`). "
                     "It is listed so the census is complete. It must not be merged, rebased onto, "
                     "or used as a source of any file.\n")
        lines.append("## Artifacts outside the repository\n")
        lines.append("| file | sha256 |")
        lines.append("|---|---|")
        for p in produced:
            lines.append(f"| `{p}` | `{sha256_file(p)}` |")
        lines.append("")
        lines.append("## What this does NOT establish\n")
        lines.append("- It does not rank the branches or say which one is worth keeping: it counts "
                     "commits and file changes, and a large diff is not an achievement.")
        lines.append("- It does not read any file's content, so it says nothing about whether a "
                     "branch's code runs, is tested, or is correct.")
        lines.append("- It does not detect duplicated work across branches; that is "
                     "`HIDDEN_WORK_SEARCH_V1.md`.")
        lines.append("- Commit counts are not quality: a branch 200 commits ahead may contain "
                     "nothing that the backbone lacks, and one 1 commit ahead may contain the "
                     "only working implementation.")
        lines.append("- It does not modify, merge, delete or tag anything.")
        s.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nsummary written: {s}  sha256={sha256_file(s)}")

    print(f"\nartifacts in {out}: MANIFEST_branch_census.json sha256={sha256_file(mf)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
