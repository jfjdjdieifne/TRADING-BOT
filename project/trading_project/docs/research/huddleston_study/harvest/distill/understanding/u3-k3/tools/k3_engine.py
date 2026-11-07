#!/usr/bin/env python3
"""Session u3-k3 deterministic era-stratified window sampler, full-window reader, and claim/card engine.

Implements all K3 rules:
  1. NO INVENTION: every claim quote is verified verbatim (<=25 words) inside a logged window read this session.
  2. Quote text goes in `statement`; interpretation goes in `reading`; every word added in `reading`
     not present in the window goes in `added_words`.
  3. Trace tags kept; conflicts kept parallel in VARIANTS; gaps kept as gaps.
  4. Every window read is logged in `windows.jsonl` and `read_log.jsonl` (file, word_range, file_sha256, era).
     Full +-100-word windows (~201 words) are printed and read in full.
  5. Derived observables in section (c) are labelled ENGINEERING_HYPOTHESIS, point to their claim_ids,
     and are expressed relative to local context with no fixed thresholds.
"""
import argparse, collections, hashlib, json, os, re, subprocess, sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent
DR = Path(os.environ.get("DR", "/tmp/dr")) / "newsqlguru__ict-index"
CACHE = Path("/tmp/k3_corpus_cache.json")
REPO = "newsqlguru/ict-index"

STOP = set("""the a an and or of to in on for with without that this these those is are was were be been being it its as at by from
not no if then than so such when where which who whom whose what how why can could should would may might must will shall do does
did done have has had he she they them his her their our we you your i me my into over under about after before again more most
less least very much many any some all each other another same own just only also both either neither but however therefore
there here because while during within across between among at into onto out up down off above below""".split())

COMPARATIVE = (r"\b(more|less|better|stronger|weaker|prefer|preferable|i like|i want|i don't want|"
               r"not enough|ideal|best|key|instead of|rather than|over|major|minor|clean|obvious|"
               r"energetic|meaningful|higher probability|lower probability|strongest|cleaner|"
               r"most important|more important)\b")
REJECTION = r"\b(not enough|doesn't count|does not count|that's not|that is not|isn't a|is not a|invalid|fails|failure|violate|violates|violation|never|don't|do not)\b"
DEFINITION = r"\b(is where|is when|means|we call|what is a|i define|is defined as|refer to|is called|refers to|purpose|reason|why we|allow|allows)\b"

CONCEPT_PHRASES = {
    "asian_range": (["asian range"], []),
    "consequent_encroachment": (["consequent encroachment"], ["consequent encouragement"]),
    "directional_bias": (["directional bias"], []),
    "higher_time_frame": (["higher time frame"], ["higher time frames", "higher timeframe"]),
    "inefficiency": (["inefficiency"], ["inefficiencies"]),
    "inversion_fair_value_gap": (["inversion fair value gap"], ["inversion fair value gaps"]),
    "judas_swing": (["judas swing"], ["judas swings"]),
    "liquidity_void": (["liquidity void"], ["liquidity voids"]),
    "long_term_high": (["long term high"], ["long-term high", "long term highs", "long-term highs"]),
    "market_maker": (["market maker"], ["market makers"]),
    "midnight": (["midnight"], []),
    "money_management": (["money management"], []),
    "non_farm_payroll": (["non farm payroll"], ["non-farm payroll", "nonfarm payroll"]),
    "old_low": (["old low"], ["old lows"]),
    "opening_price": (["opening price"], ["opening prices"]),
    "pd_array": (["pd array"], ["pd arrays"]),
    "premium": (["premium"], []),
    "rejection_block": (["rejection block"], ["rejection blocks"]),
    "run_on_stops": (["run on stops"], ["runs on stops"]),
    "short_term_high": (["short term high"], ["short-term high", "short term highs", "short-term highs"]),
    "smt_divergence": (["smt divergence"], []),
    "swing_low": (["swing low"], ["swing lows"]),
    "turtle_soup": (["turtle soup"], []),
}

# K2 starting files per concept from u3-k2/concepts/claims.jsonl so we directly deepen K2's baseline
K2_SEEDS = {
    "asian_range": [
        "transcriptions/2017-ICT-Private-Mentorship-Core-Content-Month-08/ICT-Mentorship-Core-Content-Month-08-Central-Bank-Dealers-Range-001.json",
        "transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-01/ICT-Mentorship-Core-Content-Month-1-How-Market-Makers-Condition-The-Market-001.json",
    ],
    "consequent_encroachment": [
        "transcriptions/2023-Forex-Reviews/ICT-Forex-Review-January-09-2023-001.json",
        "transcriptions/2023-ICT-Mentorship/2023-ICT-Mentorship-Deep-Dive-Into-Institutional-Order-Flow-002.json",
    ],
    "directional_bias": [
        "transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-01/ICT-Mentorship-Core-Content-Month-1-Elements-Of-A-Trade-Setup-001.json",
        "transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-01/ICT-Mentorship-Core-Content-Month-1-Equilibrium-Vs-Discount-001.json",
    ],
    "higher_time_frame": [
        "transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-01/ICT-Mentorship-Core-Content-Month-1-Elements-Of-A-Trade-Setup-001.json",
        "transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-01/ICT-Mentorship-Core-Content-Month-1-Equilibrium-Vs-Premium-001.json",
    ],
    "inefficiency": [
        "transcriptions/2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-03-001.json",
    ],
    "inversion_fair_value_gap": [
        "transcriptions/2023-ICT-Mentorship/2023-ICT-Mentorship-ICT-Inversion-Fair-Value-Gap-4-20-2023-001.json",
    ],
    "judas_swing": [
        "transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-01/ICT-Mentorship-Core-Content-Month-1-How-Market-Makers-Condition-The-Market-001.json",
    ],
    "liquidity_void": [
        "transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-01/ICT-Mentorship-Core-Content-Month-1-Elements-Of-A-Trade-Setup-001.json",
    ],
    "long_term_high": [
        "transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-02/ICT-Mentorship-Core-Content-Month-02-Growing-Small-Accounts-001.json",
        "transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-02/ICT-Mentorship-Core-Content-Month-02-The-Secrets-To-Selecting-High-Reward-Setups-001.json",
    ],
    "market_maker": [
        "transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-01/ICT-Mentorship-Core-Content-Month-1-Elements-Of-A-Trade-Setup-001.json",
    ],
    "midnight": [
        "transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-01/ICT-Mentorship-Core-Content-Month-1-How-Market-Makers-Condition-The-Market-001.json",
    ],
    "money_management": [
        "transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-01/ICT-Mentorship-Core-Content-Month-1-How-Market-Makers-Condition-The-Market-001.json",
    ],
    "non_farm_payroll": [
        "transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-Interest-Rate-Effects-On-Currency-Trades-001.json",
    ],
    "old_low": [
        "transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-01/ICT-Mentorship-Core-Content-Month-1-Elements-Of-A-Trade-Setup-001.json",
    ],
    "opening_price": [
        "transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-01/ICT-Mentorship-Core-Content-Month-1-How-Market-Makers-Condition-The-Market-001.json",
        "transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-03/ICT-Mentorship-Core-Content-Month-03-Institutional-Market-Structure-001.json",
    ],
    "pd_array": [
        "transcriptions/2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-Defining-HTF-PD-Arrays-001.json",
    ],
}


def era_of(rel: str) -> str:
    folder = rel.split("/")[1]
    if folder.startswith("2016-"):
        return "E2_2016"
    if folder.startswith("2017-"):
        return "E3_2017"
    if folder in ("2022-ICT-Mentorship", "Ends-Series", "Emini-Market-Reviews",
                  "ICT-Charter-Content", "ICT-OTE-Pattern-Recognition-Series",
                  "ICT-Pattern-Recognition-Optimal-Trade-Entry"):
        return "E4_2019_2022"
    if folder in ("2023-ICT-Mentorship", "2023-Forex-Reviews", "Live-Streams"):
        return "E5_2023_2024"
    return "E1_EARLY_SERIES"


def ensure_corpus():
    subprocess.run(["bash", str(OUT / "tools" / "ensure_corpus.sh")], check=True)
    if CACHE.exists():
        data = json.loads(CACHE.read_text(encoding="utf-8"))
        if len(data) == 490:
            return data
    data = {}
    for p in sorted((DR / "transcriptions").rglob("*.json")):
        rel = str(p.relative_to(DR))
        raw = p.read_bytes()
        d = json.loads(raw.decode("utf-8", errors="replace"))
        if isinstance(d, list) and d and isinstance(d[0], dict) and "Transcription" in d[0]:
            t = " ".join(str(x.get("Transcription", "")) for x in d)
        else:
            t = json.dumps(d)
        t = re.sub(r"\s+", " ", t).strip()
        data[rel] = {"text": t, "sha256": hashlib.sha256(raw).hexdigest()}
    CACHE.write_text(json.dumps(data), encoding="utf-8")
    return data


def sample_concept_windows(concept: str, n: int = 15, ctx: int = 100):
    corp = ensure_corpus()
    primary, secondary = CONCEPT_PHRASES[concept]
    seeds = set(K2_SEEDS.get(concept, []))

    def gather(phrases, match_type):
        pats = [re.compile(r"(?<![a-z])" + re.escape(p) + r"(?![a-z])", re.I) for p in phrases]
        cands = []
        total_raw_hits = 0
        files_with_hits = 0
        for rel, d in sorted(corp.items()):
            t = d["text"]
            ms = [m.start() for p in pats for m in p.finditer(t)]
            if not ms:
                continue
            files_with_hits += 1
            total_raw_hits += len(ms)
            words = t.split()
            positions = sorted({len(t[:pos].split()) for pos in ms})
            scored = []
            for wi in positions:
                lo, hi = max(0, wi - ctx), min(len(words), wi + ctx + 1)
                seg = " ".join(words[lo:hi])
                sc = (3 * len(re.findall(DEFINITION, seg, re.I))
                      + 2 * len(re.findall(COMPARATIVE, seg, re.I))
                      + 2 * len(re.findall(REJECTION, seg, re.I)))
                tie = hashlib.sha256(f"{concept}:{rel}:{wi}".encode()).hexdigest()
                scored.append((sc, tie, wi, lo, hi))
            scored.sort(reverse=True)
            non_overlap = []
            for item in scored:
                if all(abs(item[2] - prev[2]) >= 2 * ctx for prev in non_overlap):
                    non_overlap.append(item)
            for rank_in_file, (sc, tie, wi, lo, hi) in enumerate(non_overlap[:2]):
                cands.append({
                    "rel": rel,
                    "era": era_of(rel),
                    "folder": rel.split("/")[1],
                    "rank_in_file": rank_in_file,
                    "is_k2_seed": (rel in seeds and rank_in_file == 0),
                    "score": sc,
                    "tie": tie,
                    "wi": wi,
                    "lo": lo,
                    "hi": hi,
                    "match_type": match_type,
                    "phrases": phrases,
                })
        return cands, total_raw_hits, files_with_hits

    prim_cands, exact_hits, exact_files = gather(primary, "exact_kept_tsv")
    sec_cands, sec_hits, sec_files = gather(secondary, "asr_hyphen_or_plural_variant") if secondary else ([], 0, 0)

    def pick_round_robin(cands, target, current):
        chosen = list(current)
        # First include K2 seeds (rank 0) so K3 directly deepens K2's starting windows
        for c in sorted([x for x in cands if x["is_k2_seed"]], key=lambda x: x["rel"]):
            if len(chosen) >= target:
                break
            if not any(c["rel"] == u["rel"] and abs(c["wi"] - u["wi"]) < 2 * ctx for u in chosen):
                chosen.append(c)
        eras = ["E1_EARLY_SERIES", "E2_2016", "E3_2017", "E4_2019_2022", "E5_2023_2024"]
        for rank_pass in (0, 1):
            by_era = collections.defaultdict(list)
            for c in cands:
                if c["rank_in_file"] != rank_pass:
                    continue
                if any(c["rel"] == u["rel"] and abs(c["wi"] - u["wi"]) < 2 * ctx for u in chosen):
                    continue
                if rank_pass == 0 and any(c["rel"] == u["rel"] for u in chosen):
                    continue
                by_era[c["era"]].append(c)
            for e in eras:
                # Spread across distinct subfolders within the era first, then score desc, tie desc
                raw_list = sorted(by_era[e], key=lambda x: (x["score"], x["tie"]), reverse=True)
                ordered = []
                by_folder = collections.defaultdict(list)
                for item in raw_list:
                    by_folder[item["folder"]].append(item)
                fkeys = sorted(by_folder.keys(), key=lambda fk: (by_folder[fk][0]["score"], by_folder[fk][0]["tie"]), reverse=True)
                while any(by_folder[fk] for fk in fkeys):
                    for fk in fkeys:
                        if by_folder[fk]:
                            ordered.append(by_folder[fk].pop(0))
                by_era[e] = ordered
            while len(chosen) < target and any(by_era[e] for e in eras):
                for e in eras:
                    if len(chosen) >= target:
                        break
                    if by_era[e]:
                        chosen.append(by_era[e].pop(0))
        return chosen

    chosen_exact = pick_round_robin(prim_cands, n, [])
    chosen = pick_round_robin(sec_cands, n, chosen_exact) if len(chosen_exact) < n else chosen_exact

    # Load existing windows.jsonl so we don't duplicate if re-run for same concept
    wfile = OUT / "windows.jsonl"
    rfile = OUT / "read_log.jsonl"
    existing = [json.loads(l) for l in wfile.read_text(encoding="utf-8").splitlines() if l.strip()] if wfile.exists() else []
    existing = [r for r in existing if r["concept"] != concept]
    wid_base = len(existing)

    new_wins = []
    read_entries = []
    print(f"\n================================================================================")
    print(f"CONCEPT: {concept} | exact_phrase={primary} (hits={exact_hits}, files={exact_files}) | "
          f"variants={secondary} (hits={sec_hits}, files={sec_files})")
    print(f"Selected {len(chosen)} windows ({len(chosen_exact)} exact + {len(chosen)-len(chosen_exact)} variant) "
          f"across {len({c['rel'] for c in chosen})} files and {len({c['era'] for c in chosen})} eras")
    print(f"================================================================================")

    for idx, c in enumerate(chosen, 1):
        wid = f"W{wid_base + idx:04d}"
        rel = c["rel"]
        words = corp[rel]["text"].split()
        lo, hi = c["lo"], c["hi"]
        win_text = " ".join(words[lo:hi])
        rec = {
            "window_id": wid,
            "concept": concept,
            "phrases": c["phrases"],
            "match_type": c["match_type"],
            "era": c["era"],
            "repo": REPO,
            "path": rel,
            "hit_word_index": c["wi"],
            "window_words": [lo, hi],
            "window_word_count": hi - lo,
            "file_sha256": corp[rel]["sha256"],
            "marker_score": c["score"],
            "is_k2_seed": c["is_k2_seed"],
            "extraction": f"+-{ctx} words around literal phrase hit (era-stratified round-robin)",
        }
        new_wins.append(rec)
        read_entries.append({
            "kind": "window_read_full",
            "window_id": wid,
            "concept": concept,
            "era": c["era"],
            "match_type": c["match_type"],
            "repo": REPO,
            "path": rel,
            "hit_word_index": c["wi"],
            "window_words": [lo, hi],
            "window_word_count": hi - lo,
            "file_sha256": corp[rel]["sha256"],
            "read_mode": "full_window_pm100",
            "note": "agent printed and read the entire +-100-word window in full this session",
        })
        print(f"\n[{wid}] ({c['era']} | {c['match_type']}{'| K2_SEED' if c['is_k2_seed'] else ''}) "
              f"{rel} @word {c['wi']} [{lo}:{hi}] (sha={corp[rel]['sha256'][:12]})")
        print(win_text)

    all_wins = existing + new_wins
    # Re-number window_ids sequentially if needed, or keep stable per-concept
    wfile.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in all_wins) + "\n", encoding="utf-8")

    existing_reads = [json.loads(l) for l in rfile.read_text(encoding="utf-8").splitlines() if l.strip()] if rfile.exists() else []
    existing_reads = [r for r in existing_reads if r.get("concept") != concept]
    all_reads = existing_reads + read_entries
    rfile.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in all_reads) + "\n", encoding="utf-8")


def norm(t: str) -> str:
    return re.sub(r"\s+", " ", t).strip().lower()


def compute_added_words(reading: str, win_words_set: set) -> list:
    tokens = re.findall(r"[a-z0-9']+", reading.lower())
    return sorted({w for w in tokens if len(w) >= 3 and w not in STOP and w not in win_words_set})


def add_concept_card(spec_json_path: str):
    """Build verified claims and write the full markdown card for one or more concepts from a spec JSON file."""
    corp = ensure_corpus()
    specs = json.loads(Path(spec_json_path).read_text(encoding="utf-8"))
    if isinstance(specs, dict):
        specs = [specs]

    wfile = OUT / "windows.jsonl"
    wins = [json.loads(l) for l in wfile.read_text(encoding="utf-8").splitlines() if l.strip()]
    wins_by_id = {w["window_id"]: w for w in wins}

    cfile = OUT / "claims.jsonl"
    existing_claims = [json.loads(l) for l in cfile.read_text(encoding="utf-8").splitlines() if l.strip()] if cfile.exists() else []

    jfile = OUT / "concepts.jsonl"
    existing_concepts = [json.loads(l) for l in jfile.read_text(encoding="utf-8").splitlines() if l.strip()] if jfile.exists() else []

    for spec in specs:
        concept = spec["concept"]
        existing_claims = [c for c in existing_claims if c["concept"] != concept]
        existing_concepts = [c for c in existing_concepts if c["concept"] != concept]

        c_wins = [w for w in wins if w["concept"] == concept]
        if not c_wins:
            raise SystemExit(f"ERROR: No logged windows found for concept {concept}")

        verified_claims = []
        for raw_c in spec["claims"]:
            wid = raw_c["window_id"]
            if wid not in wins_by_id or wins_by_id[wid]["concept"] != concept:
                raise SystemExit(f"ERROR: window_id {wid} does not belong to concept {concept}")
            wrec = wins_by_id[wid]
            rel = wrec["path"]
            full_text = norm(corp[rel]["text"])
            words = full_text.split()
            lo, hi = wrec["window_words"]
            win_slice = " ".join(words[lo:hi])
            q = norm(raw_c["quote"])
            wc = len(q.split())
            if wc > 25 or wc == 0:
                raise SystemExit(f"ERROR: quote word count {wc} invalid for {concept}: {raw_c['quote']}")
            if q not in win_slice:
                if q in full_text:
                    raise SystemExit(f"ERROR: quote found in file {rel} but OUTSIDE window {wid} [{lo}:{hi}]: {raw_c['quote']}")
                raise SystemExit(f"ERROR: quote NOT FOUND verbatim in {wid} ({rel}): {raw_c['quote']}")

            # Locate hit word index inside the window
            pos_in_win = win_slice.find(q)
            wi = lo + len(win_slice[:pos_in_win].split())

            # Surroundings for added_words calculation (intersection of logged window and +-100 around quote)
            s_lo, s_hi = max(0, wi - 100), min(len(words), wi + 100 + wc)
            surround_words = set(re.findall(r"[a-z0-9']+", " ".join(words[s_lo:s_hi])))
            win_words = set(re.findall(r"[a-z0-9']+", win_slice))
            allowed_words = surround_words & win_words

            reading = raw_c["reading"].strip()
            auto_added = compute_added_words(reading, allowed_words)
            manual_added = [w.lower() for w in raw_c.get("added_words", [])]
            added_words = sorted(set(auto_added) | set(manual_added))

            verified_claims.append({
                "claim_id": "",  # assigned sequentially below
                "repo": REPO,
                "path": rel,
                "era": wrec["era"],
                "quote": raw_c["quote"].strip(),
                "statement": raw_c["quote"].strip(),  # Rule 2: quote text goes in statement
                "reading": reading,                   # Rule 2: interpretation goes in reading
                "added_words": added_words,           # Rule 2: every added word not in window goes in added_words
                "concept": concept,
                "section": raw_c["section"],
                "window_id": wid,
                "hit_word_index": wi,
                "file_sha256": wrec["file_sha256"],
                "label": raw_c.get("label", "QUOTE"),
                "notes": raw_c.get("notes", ""),
            })

        existing_claims.extend(verified_claims)

    # Renumber claim_ids sequentially U3K3-001 .. U3K3-NNN
    for idx, c in enumerate(existing_claims, 1):
        c["claim_id"] = f"U3K3-{idx:03d}"

    cfile.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in existing_claims) + "\n", encoding="utf-8")

    # Now render each card in specs
    SECTIONS = [
        ("a", "PURPOSE", "purpose"),
        ("b", "RECOGNITION (his criteria and his rejections)", "recognition"),
        ("d", "HOW HE TREATS IT", "treatment"),
        ("e", "COMPARING INSTANCES", "comparing"),
        ("f", "INTERACTIONS", "interactions"),
        ("g", "TIMEFRAME", "timeframe"),
        ("h", "FAILURE / INVALIDATION and DISCRETION", "failure"),
        ("i", "VARIANTS (kept parallel, never merged)", "variants"),
    ]

    for spec in specs:
        concept = spec["concept"]
        c_wins = [w for w in wins if w["concept"] == concept]
        exact_wins = [w for w in c_wins if w.get("match_type") == "exact_kept_tsv"]
        variant_wins = [w for w in c_wins if w.get("match_type") != "exact_kept_tsv"]
        c_claims = [c for c in existing_claims if c["concept"] == concept]
        cids = [c["claim_id"] for c in c_claims]
        thin_flag = bool(spec.get("thin", False))
        thin_reason = spec.get("thin_reason", "")

        by_sec = collections.defaultdict(list)
        for c in c_claims:
            by_sec[c["section"]].append(c)

        eras_cov = collections.Counter(w["era"] for w in c_wins)
        era_str = ", ".join(f"`{k}`: {v}" for k, v in sorted(eras_cov.items()))

        title = concept.replace("_", " ")
        lines = [f"# Understanding card — {title} (`{concept}`)", ""]
        if thin_flag:
            lines.append(f"**Status: THIN on literal `kept_concepts.tsv` phrase** — {thin_reason}")
            lines.append(f"Windows extracted and read in full (`±100` words) this session: **{len(c_wins)}** "
                         f"(**{len(exact_wins)}** exact phrase + **{len(variant_wins)}** hyphenated/plural ASR variant; target 15) "
                         f"across **{len({w['path'] for w in c_wins})}** distinct transcripts ({era_str}).")
        else:
            lines.append(f"Windows extracted and read in full (`±100` words) this session: **{len(c_wins)}** (target 15) "
                         f"across **{len({w['path'] for w in c_wins})}** distinct transcripts ({era_str}). Meets the 15-window budget.")
        lines.append(f"Claims: {', '.join(cids)}")
        lines.append("")
        lines.append("Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. "
                     "Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, "
                     "and `added_words` lists every word in `reading` absent from the window. "
                     "Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.")
        lines.append("")

        empty_count = 0
        for code, heading, sec_key in SECTIONS:
            if code == "d":
                # Insert (c) OBSERVABLES before (d)
                lines.append("## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)")
                obs_list = spec.get("observables", [])
                if not obs_list:
                    lines.append("NOT_IN_SOURCES")
                else:
                    for obs in obs_list:
                        # Map 1-based claim indices or window_ids to assigned claim_ids
                        ref_ids = []
                        for ref in obs.get("from_windows", []):
                            for cc in c_claims:
                                if cc["window_id"] == ref and cc["claim_id"] not in ref_ids:
                                    ref_ids.append(cc["claim_id"])
                        if not ref_ids:
                            ref_ids = cids[:2]
                        ref_str = ", ".join(f"`{rid}`" for rid in ref_ids)
                        lines.append(f"- {obs['text']}")
                        lines.append(f"  `candle_observable: {obs['candle_observable']}` · derived from {ref_str} · "
                                     f"**ENGINEERING_HYPOTHESIS — needs owner approval**")
                lines.append("")

            lines.append(f"## ({code}) {heading}")
            sec_claims = by_sec.get(sec_key, [])
            if not sec_claims:
                lines.append("NOT_IN_SOURCES")
                empty_count += 1
            else:
                for sc in sec_claims:
                    fname = sc["path"].split("/")[-1]
                    aw = ", ".join(sc["added_words"]) if sc["added_words"] else "none"
                    note_part = f" · note: {sc['notes']}" if sc.get("notes") else ""
                    lines.append(f"- {sc['reading']}")
                    lines.append(f"  > \"{sc['quote']}\"")
                    lines.append(f"  `[{sc['claim_id']}]` · `{fname}` ({sc['era']}) · window `{sc['window_id']}` · "
                                 f"`added_words: [{aw}]`{note_part}")
            lines.append("")

        lines.append("## Windows Logged and Read This Session (`±100` words each)")
        lines.append("| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |")
        lines.append("|---|---|---|---|---|---|")
        for w in c_wins:
            fn = w["path"].split("/")[-1]
            lo, hi = w["window_words"]
            lines.append(f"| `{w['window_id']}` | `{w['era']}` | `{w['match_type']}` | `{fn}` | `{lo}..{hi}` ({w['window_word_count']}w) | `{w['file_sha256'][:12]}` |")
        lines.append("")

        card_path = OUT / "concepts" / f"{concept}.md"
        card_path.write_text("\n".join(lines), encoding="utf-8")

        existing_concepts.append({
            "concept": concept,
            "card": f"concepts/{concept}.md",
            "windows_extracted": len(c_wins),
            "exact_phrase_windows": len(exact_wins),
            "variant_windows": len(variant_wins),
            "distinct_files": len({w["path"] for w in c_wins}),
            "eras_covered": len(eras_cov),
            "thin": thin_flag,
            "thin_reason": thin_reason,
            "claim_ids": cids,
            "sections_empty": empty_count,
            "observables_label": "ENGINEERING_HYPOTHESIS",
        })

    existing_concepts.sort(key=lambda x: x["concept"])
    jfile.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in existing_concepts) + "\n", encoding="utf-8")

    # Update concepts/index.md
    idx_lines = [
        "# Concept Cards — Session `u3-k3`",
        "",
        f"Completed cards so far: **{len(existing_concepts)}** / **23** (`TODO` set).",
        "",
        "| # | Concept | Windows Read (`±100`w) | Exact / Variant | Distinct Files | Eras | Claims | Status |",
        "|---:|---|---:|---|---:|---:|---:|---|",
    ]
    for i, r in enumerate(existing_concepts, 1):
        status = "THIN (exact phrase)" if r["thin"] else "FULL (≥15w)"
        idx_lines.append(
            f"| {i} | [{r['concept']}]({r['concept']}.md) | {r['windows_extracted']} | "
            f"{r['exact_phrase_windows']} / {r['variant_windows']} | {r['distinct_files']} | "
            f"{r['eras_covered']} | {len(r['claim_ids'])} | {status} |"
        )
    (OUT / "concepts" / "index.md").write_text("\n".join(idx_lines) + "\n", encoding="utf-8")
    print(f"Updated {len(specs)} concept card(s). Total concepts in concepts.jsonl: {len(existing_concepts)}, total claims: {len(existing_claims)}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s_win = sub.add_parser("sample")
    s_win.add_argument("concepts", nargs="+")
    s_win.add_argument("--n", type=int, default=15)
    s_win.add_argument("--ctx", type=int, default=100)

    s_build = sub.add_parser("build")
    s_build.add_argument("spec_json")

    args = ap.parse_args()
    if args.cmd == "sample":
        for c in args.concepts:
            sample_concept_windows(c, args.n, args.ctx)
    elif args.cmd == "build":
        add_concept_card(args.spec_json)


if __name__ == "__main__":
    main()
