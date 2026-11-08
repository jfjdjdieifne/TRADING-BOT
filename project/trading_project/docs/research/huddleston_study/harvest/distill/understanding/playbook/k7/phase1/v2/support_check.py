#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
قاعدة الفحص قبل التشغيل:

كل كلمة محتوى في الحقول المضافة يجب أن تظهر في الاقتباس، أو في نافذة مدخلين قبل وبعد مدخل البداية، أو تكون مدعومة باقتباس دليل.
الناتج: مدعوم أو كلمات غير مدعومة
قرار هندسي: هذه القاعدة تطبق على كل الحقول المضافة بعد الاقتباس ولا تغير الاقتباس نفسه. السبب هو منع إضافة جار أو غير مدعوم كما كشفه التدقيق حيث كان ١٦٫٤٪ غير مدعوم و٢٦٫٦٪ من الجار.

تعريف كلمة المحتوى: كل رمز يطابق [^\W_]+ بعد تطبيع البحث مع إزالة كلمات التوقف العربية والإنجليزية الشائعة
نافذة المدخلين: المدخلان السابقان والتاليان لمدخل البداية حسب خريطة المواضع
"""
import re
import json
import pathlib
import sys

TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)

STOPWORDS = set("""
a an and are as at be been being by can could did do does for from had has have he her his i if in is it its may might must not of on or our shall should that the their there they this to was we were will with you your
في من على إلى عن مع أن إن كان كانت يكون تكون هذا هذه ذلك تلك الذي التي الذين اللتان هنا هناك ثم أو أم بل لكن حتى إذا لو عندما حيث كيف لم لن لا ما ماذا هل كل بعض غير بين قبل بعد تحت فوق مع دون
""".split())

def tokens(text):
    if not text:
        return []
    # normalize: lower, keep letters/digits
    text = text.lower()
    toks = TOKEN_RE.findall(text)
    return [t for t in toks if t not in STOPWORDS and len(t) > 1]

def check_one(quote, added_text, window_texts, evidence_text):
    """
    quote: str
    added_text: str (concatenated added fields)
    window_texts: list of str (texts of +/-2 entries)
    evidence_text: str or None
    returns (status, unsupported_words)
    """
    q_toks = set(tokens(quote))
    win_toks = set()
    for wt in window_texts:
        win_toks.update(tokens(wt))
    ev_toks = set(tokens(evidence_text)) if evidence_text else set()
    added_toks = tokens(added_text)
    unsupported = []
    for at in added_toks:
        if at in q_toks or at in win_toks or at in ev_toks:
            continue
        # also allow if at appears as substring in any evidence? already token check
        unsupported.append(at)
    if unsupported:
        return "UNSUPPORTED_WORDS", unsupported
    else:
        return "SUPPORTED", []

def main():
    # This script is generic; for calibration run, see run_calibration.py logic
    print("support_check.py loaded — rule declared before run")
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        # simple manual check
        quote = sys.argv[2]
        added = sys.argv[3]
        status, uw = check_one(quote, added, [], None)
        print(status, uw)

if __name__ == "__main__":
    main()
