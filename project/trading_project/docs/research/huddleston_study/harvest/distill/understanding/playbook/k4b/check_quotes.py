#!/usr/bin/env python3
"""Verify every quoted excerpt in the K4b claim and trace ledgers."""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
from pathlib import Path


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def read_jsonl(path: Path):
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}:{line_no}: JSON غير صالح: {exc}") from exc
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="التحقق الحرفي من شواهد الاقتباس")
    parser.add_argument("--corpus-root", default=os.environ.get("K4_CORPUS_ROOT"),
                        help="مجلد corpus المستخرج خارج المستودع")
    args = parser.parse_args()
    if not args.corpus_root:
        print("يلزم تمرير --corpus-root أو ضبط K4_CORPUS_ROOT.", file=sys.stderr)
        return 2
    corpus = Path(args.corpus_root).resolve()
    root = Path(__file__).resolve().parent
    ledgers = [("claims.jsonl", "claim_id"), ("traces.jsonl", "trace_id")]
    checked = 0
    failures = []
    cache: dict[str, str] = {}
    for ledger_name, id_field in ledgers:
        for row in read_jsonl(root / ledger_name):
            quote = row.get("quote")
            if not quote:
                # NOT_FOUND and NOT_STATED records intentionally carry no quote.
                continue
            checked += 1
            ident = row.get(id_field, "غير معروف")
            transcript_id = row.get("transcript_id")
            source = (corpus / transcript_id).resolve()
            if corpus not in source.parents:
                failures.append(f"{ident}: مسار المصدر يتجاوز مجلد المتن")
                continue
            if transcript_id not in cache:
                if not source.is_file():
                    failures.append(f"{ident}: ملف المصدر غير موجود: {transcript_id}")
                    continue
                segments = json.loads(source.read_text(encoding="utf-8"))
                cache[transcript_id] = " ".join(
                    str(segment.get("Transcription", "")) for segment in segments
                )
            transcript = cache.get(transcript_id)
            if transcript is None or normalized(quote) not in normalized(transcript):
                failures.append(f"{ident}: الاقتباس غير موجود حرفياً بعد توحيد المسافات")
            if len(quote.split()) > 25:
                failures.append(f"{ident}: الاقتباس يتجاوز خمسة وعشرين كلمة")
    if failures:
        print(f"نتيجة التحقق: {checked - len(failures)}/{checked} اقتباساً ناجحاً")
        for failure in failures:
            print("إخفاق: " + failure)
        return 1
    print(f"نتيجة التحقق: {checked}/{checked} اقتباساً ناجحاً؛ جميعها موجودة حرفياً بعد توحيد المسافات.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
