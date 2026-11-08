#!/usr/bin/env python3
"""تحقق حرفي من الاقتباسات المسجلة في K6_QUOTES.jsonl."""
import argparse
import json
import re
import sys
from pathlib import Path


def read_segments(path: Path):
    obj = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(obj, dict):
        obj = obj.get("transcription", obj.get("Transcription", []))
    if not isinstance(obj, list):
        raise ValueError("صيغة ملف غير متوقعة")
    return [row for row in obj if isinstance(row, dict) and isinstance(row.get("Transcription"), str)]


def main():
    parser = argparse.ArgumentParser(description="التحقق الحرفي من ملفات الاقتباس")
    parser.add_argument("--corpus-root", required=True, help="مجلد يحتوي transcriptions أو مجلد transcriptions مباشرة")
    parser.add_argument("--quotes", default=str(Path(__file__).with_name("K6_QUOTES.jsonl")))
    args = parser.parse_args()
    root = Path(args.corpus_root)
    transcriptions = root / "transcriptions" if (root / "transcriptions").is_dir() else root
    rows = [json.loads(line) for line in Path(args.quotes).read_text(encoding="utf-8").splitlines() if line.strip()]
    good = 0
    errors = []
    for row in rows:
        path = transcriptions / row["source_file"]
        try:
            segs = read_segments(path)
            start = int(row["start_segment"]) - 1
            end = int(row["end_segment"])
            excerpt = " ".join(s["Transcription"] for s in segs[start:end])
            valid = (0 <= start < end <= len(segs) and row["quote"] in excerpt
                     and len(re.findall(r"\S+", row["quote"])) <= 25
                     and int(segs[start].get("offsetMS", -1)) == int(row["offset_ms"]))
            if valid:
                good += 1
            else:
                errors.append(f"{row['quote_id']}: نص أو موضع أو حد الكلمات غير مطابق")
        except Exception as exc:
            errors.append(f"{row.get('quote_id','؟')}: تعذر التحقق: {exc}")
    print(f"النتيجة: {good}/{len(rows)} اقتباس مطابق حرفياً")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
