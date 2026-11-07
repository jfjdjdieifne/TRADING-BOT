#!/usr/bin/env python3
"""التحقق الحرفي من اقتباسات حصاد ك٥؛ لا ينزّل أي مصدر."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def transcript_text(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"صيغة تفريغ غير متوقعة: {path}")
    return normalise(" ".join(str(item.get("Transcription", "")) for item in data if isinstance(item, dict)))


def main() -> int:
    parser = argparse.ArgumentParser(description="فحص اقتباسات المستوى الأول والثاني")
    parser.add_argument("--corpus-root", required=True, help="مجلد المتن المفكوك أو جذر مستودع المتن")
    parser.add_argument("--tier2-root", required=True, help="مجلد نسخ الصفحات المحفوظة خارج المستودع")
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("claims.jsonl"))
    args = parser.parse_args()
    corpus = Path(args.corpus_root)
    if not (corpus / "transcriptions").is_dir() and (corpus / "newsqlguru__ict-index" / "transcriptions").is_dir():
        corpus = corpus / "newsqlguru__ict-index"
    pages = Path(args.tier2_root)
    records = [json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    totals = {"TIER1": [0, 0], "TIER2": [0, 0]}
    errors = []
    page_cache = {}
    transcript_cache = {}
    for claim in records:
        tier = claim["tier"]
        totals[tier][1] += 1
        quote = normalise(claim["quote"])
        if len(quote.split()) > 25:
            errors.append(f"{claim['claim_id']}: الاقتباس يتجاوز ٢٥ كلمة")
            continue
        try:
            if tier == "TIER1":
                p = corpus / claim["transcript_id"]
                if p not in transcript_cache:
                    transcript_cache[p] = transcript_text(p)
                text = transcript_cache[p]
                found = text.find(quote)
                ok = found >= 0 and found == claim["position"]
                if found >= 0 and found != claim["position"]:
                    errors.append(f"{claim['claim_id']}: الاقتباس موجود لكن الإزاحة المسجلة {claim['position']} والصحيحة {found}")
            elif tier == "TIER2":
                p = pages / claim["page_copy"]
                raw = p.read_bytes()
                digest = hashlib.sha256(raw).hexdigest()
                if digest != claim["page_sha256"]:
                    errors.append(f"{claim['claim_id']}: بصمة نسخة الصفحة مختلفة")
                    ok = False
                else:
                    if p not in page_cache:
                        page_cache[p] = normalise(raw.decode("utf-8"))
                    ok = quote in page_cache[p]
            else:
                errors.append(f"{claim['claim_id']}: مستوى مصدر غير معروف")
                ok = False
        except Exception as exc:
            errors.append(f"{claim['claim_id']}: تعذر التحقق: {exc}")
            ok = False
        if ok:
            totals[tier][0] += 1
        else:
            errors.append(f"{claim['claim_id']}: لم يُطابق الاقتباس حرفياً")
    for tier in ("TIER1", "TIER2"):
        passed, total = totals[tier]
        print(f"{tier}: {passed}/{total}")
    if errors:
        print("الإخفاقات:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("اجتاز التحقق كل الاقتباسات وبصمات نسخ الصفحات.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
