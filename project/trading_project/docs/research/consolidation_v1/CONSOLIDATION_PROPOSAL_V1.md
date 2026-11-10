# CONSOLIDATION PROPOSAL V1

**Status: PROPOSAL ONLY.** Nothing in this document has been executed. No branch was merged, no
file was deleted, no code was moved, and nothing outside `docs/research/consolidation_v1/` was
edited. Every number below is copied from the four artifacts beside this file; each claim names
the artifact it comes from.

Owner of the decision: **the repository owner**. A recommendation here is an input, not an
instruction.

---

## 1. The three facts that decide everything

| fact | value | source |
|---|---|---|
| remote branches | **39** (= 1 backbone + 14 with no merge-base + 16 behind-only + 7 ahead + `main`) | `BRANCH_CENSUS_V1.md` |
| branches with **no merge-base** with the backbone | **14** arena branches (+ `main`), i.e. they can be read but never merged | `BRANCH_CENSUS_V1.md` |
| branches **ahead** of the backbone | **7** (max `5b5d18f2` +33 commits, 38 added files) | `BRANCH_CENSUS_V1.md` |
| branches **behind only** (shared history, zero additions) | **16** | `BRANCH_CENSUS_V1.md` |
| files on the backbone | **1,537** | `FILE_INVENTORY_V1.md` |
| of those, design documents | **912** (59%) | `FILE_INVENTORY_V1.md` |
| orphan code (not imported, not a test, not an entrypoint) | **31** | `FILE_INVENTORY_V1.md` |
| entrypoints with no test | **104** | `FILE_INVENTORY_V1.md` |
| files the four predicates do not classify | **8** | `FILE_INVENTORY_V1.md` |
| concept implementations found across all 39 tips | **2,205** | `HIDDEN_WORK_SEARCH_V1.md` |
| implementations present **only off the backbone** | **84** (20 with a name absent from the backbone; 64 drifted copies) | `HIDDEN_WORK_SEARCH_V1.md` |
| concepts with a defensible canonical implementation | **3** (`swing_at`, `fvg_at`, `displacement_at`) | `CAPABILITY_REGISTRY_V1.md` |
| concepts that remain an explicit knowledge gap | **16** | `CAPABILITY_REGISTRY_V1.md` |

Three consequences, stated plainly:

1. **The repository is not a code base with some duplication; it is a research archive with a
   working engine inside it.** 912 of 1,537 files are documents. Any consolidation that starts by
   touching code is starting in the wrong 41%.
2. **The duplication is real but it is not "hidden work" in the way the word suggests.** Of 2,205
   implementations, 84 are absent from the backbone and only 20 carry a name the backbone has
   never had. The rest are copies: identical bytes, or a drifted older copy of a file the backbone
   already has. A bulk merge would therefore merge twenty functions and 2,000 copies.
3. **Sixteen branches can be decided without reading a line of code**: they share the backbone's
   history but add nothing (0 added files, ahead = 0), so there is nothing in them to consolidate.
   Fourteen more have no merge-base at all — they can be read but never merged — and `origin/main`
   is a dead-end stub (no merge-base, 1,134 deletions against the backbone). The seven branches
   that are ahead are the only ones where a merge is even a question.

---

## 2. What this proposal does

Four stages. Each stage has a **gate**: it does not begin until the owner answers the question in
its "gate" line. Stages A and B change no code at all.

### Stage A — fix the reference point (no code)

Publish the backbone choice as a decision, so later comparisons stop drifting:

- reference tree: `origin/arena/77604f59-trading-bot` = `fd43dc29a9139aa088724b0e0f11b3d97cba431f`
- the three canonical implementations are declared canonical **for the development path only**
  (`engine_v1/b1_candles/swing.py::swing_at`, `engine_v1/b1_candles/fvg.py::fvg_at`,
  `engine_v1/c1_catalog/displacement.py::displacement_at`);
- the other implementations are **not** deprecated by this act. They stay where they are; nothing
  is deleted.

Deliverable: one paragraph in `PATCH_LOG`-style form, plus the four already-present artifacts.

**Gate A:** does the owner confirm `77604f59` / `fd43dc29` as the reference point?
*Default if unanswered: yes — it is the branch the dev month already runs from.*

### Stage B — adjudicate the 16 gaps by reading, one row at a time (no code)

The registry produces `KNOWLEDGE_GAP: canonical_choice` for 16 concepts because no implementation
satisfies *causal AND tested AND closed AND imported*. The four booleans cannot separate them;
only reading can. The proposal is to adjudicate **at most one concept per sitting**, writing the
outcome as one line in a decisions file (`CONSOLIDATION_DECISIONS_001.md`), in the shape:

```
concept: order_block
candidates: ict_engine/order_blocks.py::OrderBlockVariant | zones/order_blocks.py::_validate | ...
decision: KEEP_BOTH | PREFER <x> BECAUSE <fact> | WAITING
```

`WAITING` is a legitimate outcome and is expected for most rows: this project already records an
explicit "waiting" set of 46 concepts.

**Gate B:** begin with `order_block`, the first gap in the registry order?
*Default if unanswered: no — the gaps stay open, which is the present, honest state.*

### Stage C — extract the twenty new symbols, byte-for-byte (code, one at a time)

Only the 20 symbols in `HIDDEN_WORK_SEARCH_V1.md` whose name exists nowhere on the backbone are
candidates. Each extraction is:

1. the file copied **verbatim** from the branch that holds it (no rewrite, no reformatting),
2. a provenance record: branch, path, blob sha, byte count, sha256,
3. a test run **before** the copy is relied on,
4. one commit per symbol, naming the branch it came from.

Symbols that are visible in that list but are obviously not market logic — `cover`, `prep`,
`toc_render`, `line_is_art` (a PDF layout helper), `_fake_dec`, `_fake_study`, `check_v2`,
`gate_v1_legacy` (test doubles and superseded gates) — are **not** proposed for extraction. That
leaves a much shorter list to read first; the list is the input, not the work.

**Gate C:** does the owner want any of the 20 at all?
*Default if unanswered: no extraction; the search stands as a map.*

### Stage D — nothing is deleted

The 39 tips are already preserved by the 39 annotated tags `archive/<branch>/<tip-date>` pushed to
`origin` (78 refs including peeled). That is the consolidation's safety net: **branch deletion
becomes unnecessary**. If the owner later wants the branch list shortened, the tags keep every
commit reachable, and that is a separate decision made with that fact in hand.

---

## 3. What this proposal does NOT recommend

- **No bulk merge.** 16 branches would contribute nothing, 14 have no merge-base (a merge is
  impossible, only a read), and the 7 that are ahead contribute at most 38 added files each —
  while importing their whole history, including the 244–996 deletions each of them carries.
- **No deduplication by deletion.** The registry's duplicate table is a reading list. Deleting the
  non-canonical copy of `zones/fvg.py` would remove the only implementation the development path
  actually imports (`scan_fvgs` lives in `contextual_selection/connected_readings.py`).
- **No reformatting of the minified modules.** `zones/fvg.py` is written with one-space indents
  and multiple statements per line. Reformatting it would break byte-level provenance and make
  every future comparison a judgement call.
- **No re-run of the development month** before Stage B and the open memory item are settled: the
  earlier attempt reached 3,870,276 kB of a 3,939 MB container and produced no result.
- **No `git clean`, no `reset --hard`, no unproven `checkout --`.** Nothing in this document needs
  them, and the earlier loss of two working commits is the reason the rule exists.

---

## 4. Open questions for the owner

1. **Reference point** — confirm `77604f59` / `fd43dc29` (default: yes).
2. **The 16 gaps** — adjudicate now, or leave them open and honest (default: leave open).
3. **The 20 new symbols** — extract any, or keep the search as a map only (default: map only).
4. **The 912 design documents** — should they be swept into a single index (a reading aid, no
   deletion), or left as they are (default: left as they are)?
5. **K10 / "CLOSED_SPEC"** — six files are marked closed by the inventory; the owner's own viewing
   state is recorded as `UNKNOWN`. Is `CLOSED_SPEC` binding, or only descriptive (default:
   descriptive, until the owner says otherwise)?

---

## 5. Reproduction

Every artifact in this folder can be regenerated from a clean clone; nothing was typed by hand
except this proposal.

```bash
python3 consolidation_v1/tools/branch_census.py     --repo . --out-dir /tmp/consolidation_v1
python3 consolidation_v1/tools/file_inventory.py    --repo . --out-dir /tmp/consolidation_v1
python3 consolidation_v1/tools/hidden_work_search.py --repo . --out-dir /tmp/consolidation_v1 \
        --summary .../HIDDEN_WORK_SEARCH_V1.md
python3 consolidation_v1/tools/build_registry.py    --repo . --artifacts /tmp/consolidation_v1
```

Two facts a future reader needs and will not find in the scripts:

- `hidden_work_search.py` takes **~27 minutes** single-threaded (340,980 matching lines, one
  `ast.parse` per distinct blob, one tree walk per hit). It is correct but not cheap; an indexed
  rewrite (precomputed `(start, end, depth)` per tree, bisect per line) would cut the walk cost
  and is the obvious next optimisation if the search is to be run again.
- Two defects were found and fixed while producing these artifacts, and they matter for
  reproduction: `\b` in a POSIX ERE does not break at `_`, so `detect_fvg` was invisible to
  `\bfvg`; and a signature cache keyed by blob made every line of a file inherit the *first*
  hit's enclosing function. Both are fixed in the committed scripts; anyone re-deriving this from
  an older copy should expect different (wrong) numbers.

## 6. Artifact manifest

| artifact | sha256 (start) |
|---|---|
| `BRANCH_CENSUS_V1.md` | `9973ba3f7842888c2f2f71a8db3e281ea5c2aec1926215cebff05118ef0d478d` |
| `FILE_INVENTORY_V1.md` | `4de6c83eed1952a1ec5a2f284f2bf6f2d0794d8f004c2b2694f2d59295e9a86e` |
| `HIDDEN_WORK_SEARCH_V1.md` | `0496b8b5b46dd86ab4840c37d58fc47fb088147bdea139a64e36bd16db83b4d4` |
| `CAPABILITY_REGISTRY_V1.md` | `41c741d830c354d04e5d516224268b1c2f3bfd3d2214309cc510e7ebd1c36831` |
| `CAPABILITY_REGISTRY_V1.json` | `65239f3d4fd26baa089afe8a7e89089efb395654f72b3919bb7a0d20036b49f9` |

The hashes above are the values at the time this proposal was written, computed with
`sha256sum` over the four files; regenerating any artifact changes its hash, and that is the point
of recording them. The raw hit dump
(`hidden_hits.json`, 340,980 rows) lives outside the repository at
`/tmp/consolidation_v1/` and is deliberately **not** committed.
