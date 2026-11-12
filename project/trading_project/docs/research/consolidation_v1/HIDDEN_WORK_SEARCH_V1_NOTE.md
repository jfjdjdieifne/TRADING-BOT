# HIDDEN WORK SEARCH V1 — why "683" and "84" are different numbers

This note answers one question about `HIDDEN_WORK_SEARCH_V1.md` and changes nothing in it.

## 1. The two numbers measure different things

| | per-concept table ("ONLY on other branches") | "ONLY on other branches — full rows" |
|---|---|---|
| unit | a **symbol name**, per concept | an **implementation** = (path, symbol, blob), once |
| test for "absent from the backbone" | is this **name** nowhere among the backbone's `def`/`class` names? | is this **file's bytes** (`blob`) absent at the same path on the backbone? |
| counted in | `len({h["symbol"] for h in ch if not h["symbol_on_backbone"]})` | `only = [k for k in only_keys if only_syms.get(k)]` |
| sum / count | **683** | **84** |

The table is generated in `tools/hidden_work_search.py` with

```python
off_b = {h["symbol"] for h in ch if not h["symbol_on_backbone"]}
L.append(f"| {concept} | {len(on_b)} | {len(off_b)} |")
```

so a single name that matches four concept keywords adds four to the 683, and the same name appearing
in five different files adds one. A single implementation therefore contributes between 1 and 19 to the
table, and exactly 1 row to the list. That alone accounts for most of the gap.

The two tests also disagree in both directions:

- a **drifted copy** (same function name as the backbone, different bytes) is **listed** — new blob, old name;
- a **new name inside a file whose bytes already exist on the backbone** is counted in the table's
  column — new name, old blob — and is **not listed**.

## 2. The 84-row list is incomplete, and this is the filter that drops rows

```python
only_keys = sorted({k for k, _ in groups.items()
                    if not next(h for h in hits
                                if (h["path"], h["symbol"], h["blob"]) == k)["same_blob_on_backbone"]}, ...)
only_syms: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
for h in hits:
    k = (h["path"], h["symbol"], h["blob"])
    if k in set(only_keys) and h["signature"]:      # <-- the filter
        only_syms[k].append(h)
only = [k for k in only_keys if only_syms.get(k)]
```

`h["signature"]` is the enclosing `def`/`class` signature parsed from the blob. It is the empty string
when **every** keyword hit in that file sits at module level — a constant, an assignment, an import, a
comment, a decorator or a type alias. Such an implementation is off-backbone and is counted in the
per-concept column, but it never reaches the rows list.

So: **the filter is "the implementation must have at least one parsed `def`/`class` signature"**, and
the 84-row list is a list of *callables*, not of *all off-backbone implementations*.

## 3. The rows this filter dropped under `src/trading_system/` or `engine_v1/`

| path | symbol |
|---|---|
| `project/trading_project/docs/research/huddleston_study/engine_v1/c1_catalog/common.py` | `common` |

That is the whole list: one implementation, present with identical bytes (`ffea4dee…`) on two branch
tips (`arena/27cad7fe-trading-bot`, `arena/e7e64fc5-trading-bot`), absent from the backbone
`fd43dc29`, and whose every concept-keyword hit is at module level, so it has no enclosing signature
and no row in the 84. Nothing under `src/trading_system/` was dropped.

## 4. How this list was produced, and its limits

- The raw hit payload of the published search (`/tmp/consolidation_v1/hidden_hits.json`, sha256
  `c1c31681…`) lived in `/tmp` and did not survive the sandbox restart, so it could not be re-read.
- The one row above was therefore **recomputed**, not recovered: for each of the current 39
  `origin/arena/*` tips, every `*.py` under the two prefixes was compared blob-for-blob with the
  backbone, the tool's own `CONCEPTS` regexes were re-applied, and an implementation was kept only if
  every hit in it was module level. A rerun of the whole tool was started twice; the run from the
  repository root was still climbing after thirty minutes (its per-blob `git rev-parse` cache is not
  warm) and was stopped — so the 340,980-hit totals of the original run are **not** reproduced here
  and the published numbers stand as published.
- Consequence: the count of 683 and the count of 84 remain what the original run found. This note
  explains their relationship and identifies the filter; it does not re-audit every one of the 84 rows.

## What this does NOT establish

- It does not establish that the 84 rows are wrong, only that they are *callables-only*, and that the
  683 column is a per-concept name count that cannot be compared with them.
- It does not establish that any dropped implementation is valuable: one file matching a keyword at
  module level is the weakest possible form of a hit.
- It does not re-derive the original run's totals; the raw payload is lost, and no number above is an
  estimate of it.
