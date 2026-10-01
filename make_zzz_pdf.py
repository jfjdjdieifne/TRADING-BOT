#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zzz.txt (long Arabic chat transcript dumped as plain text)  ->  readable, complete PDF.

  raw text -> parse into blocks (conversation header / lang tag / paragraph / ascii diagram)
           -> sanitize to the glyphs DejaVu really contains (fontTools cmap)
           -> fpdf2 + uharfbuzz text shaping (real Arabic joining, tashkeel, bidi)
           -> A4 PDF with cover, index (TOC) and PDF bookmarks
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

from fontTools.ttLib import TTFont
from fpdf import FPDF
from fpdf.enums import Align, WrapMode

SRC = Path("/home/user/TRADING-BOT/zzz.txt")
OUT = Path("/home/user/TRADING-BOT/zzz.pdf")
FDIR = Path("/usr/share/fonts/truetype/dejavu")
FONTS = {
    ("sans", ""): FDIR / "DejaVuSans.ttf",
    ("sans", "B"): FDIR / "DejaVuSans-Bold.ttf",
    ("mono", ""): FDIR / "DejaVuSansMono.ttf",
    ("mono", "B"): FDIR / "DejaVuSansMono-Bold.ttf",
}
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None

# ---------------------------------------------------------------- glyph coverage
def _cmap(path: Path) -> set[int]:
    return set(TTFont(str(path)).getBestCmap().keys())


GLYPH = {"sans": _cmap(FONTS[("sans", "")]), "mono": _cmap(FONTS[("mono", "")])}
for f in GLYPH.values():
    f.update({10, 32})

# DejaVu has no emoji: fold them into the nearest glyph it really draws.
SUB = {
    # invisible / zero-width
    "\ufe0f": "", "\ufe0e": "", "\u200d": "", "\u200b": "", "\ufeff": "", "\u00ad": "",
    "\u200e": "", "\u200f": "", "\u00a0": " ", "\u2028": " ", "\u2029": " ", "\u180e": "",
    # check / cross / checkboxes / bullets
    "\u2705": "\u2713", "\u2714": "\u2713", "\u2611": "\u2713", "\u274c": "\u2717",
    "\u2716": "\u2717", "\u2612": "\u2717", "\u26d4": "\u2717", "\u2b1c": "\u2610",
    "\u25fb": "\u2610", "\u2b1b": "\u25a0", "\u2610": "\u2610",
    # coloured circles / squares
    "\U0001f534": "\u25cf", "\U0001f7e1": "\u25d0", "\U0001f7e2": "\u25d0",
    "\U0001f535": "\u25cb", "\U0001f7e0": "\u25d1", "\U0001f7e3": "\u25d1",
    "\U0001f7e4": "\u25a0", "\U0001f7e5": "\u25a0", "\U0001f7e6": "\u25a1",
    "\U0001f7e7": "\u25a1", "\U0001f7e8": "\u25aa", "\U0001f7e9": "\u25aa",
    "\U0001f536": "\u25e6", "\U0001f537": "\u25e7", "\U0001f538": "\u2022",
    "\U0001f539": "\u2022", "\U0001f3af": "\u25ce", "\u23f3": "\u231b",
    # odds and ends
    "\U0001f4d1": "\u00bb", "\U0001f512": "\u2731", "\U0001f9e0": "\u2731",
    "\U0001f4a1": "\u2731", "\U0001f680": "\u2191", "\U0001f50d": "\u222b",
    "\U0001f4c1": "\u25a1", "\U0001f4cb": "\u2261", "\U0001f4da": "\u2756",
    "\U0001f4ac": "\u201d", "\U0001f44d": "+", "\U0001f44e": "\u2212",
    "\U0001f642": "\u263a", "\U0001f641": "\u2639", "\U0001f621": "\u2639",
    "\U0001f525": "!", "\u26a0": "\u26a0", "\U0001f6a9": "!", "\u2b50": "\u2605",
    "\u3003": "\u201d", "\u2033": "\u2032", "\u02c6": "^",
}
CJK = re.compile(r"[\u2e80-\u303f\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
SCRIPT = re.compile(r"[\U0001d400-\U0001d7ff]")
SCRIPT_PLAIN = {o: ord("a") + (o - 0x1D41A) % 26 for o in range(0x1D41A, 0x1D434)}
SCRIPT_PLAIN.update({o: ord("A") + (o - 0x1D400) % 26 for o in range(0x1D400, 0x1D41A)})

RTL = re.compile(r"[\u0590-\u08ff\ufb1d-\ufdfd\ufe70-\ufeff]")
BOX = re.compile(r"[\u2500-\u259f]")
ARROW = re.compile(r"[\u2190-\u21ff\u2b00-\u2bff]")


def prep(text: str, face: str = "sans") -> str:
    """NFC, tabs expanded, and every codepoint the chosen face cannot draw folded
    into something it can (so nothing shows up as a blank box)."""
    for k, v in SUB.items():
        if k in text:
            text = text.replace(k, v)
    text = unicodedata.normalize("NFC", text).replace("\t", "    ")
    text = SCRIPT.sub(lambda m: m.group().translate(SCRIPT_PLAIN), text)
    if not CJK.search(text):
        ok = GLYPH[face]
        if all(ord(c) in ok for c in text):
            return text
    out = []
    for ch in text:
        o = ord(ch)
        if o in GLYPH[face]:
            out.append(ch)
        elif o < 32:
            out.append(" ")
        elif unicodedata.category(ch).startswith("M"):
            continue
        else:
            alt = SUB.get(ch)
            out.append(alt if alt else "?")
    return "".join(out)


def pick_face(text: str) -> str:
    return "sans" if all(ord(c) in GLYPH["sans"] for c in text) else "mono"


# ---------------------------------------------------------------- parsing
UI_NOISE = {
    "New Chat", "Leaderboard", "Search", "Generating...", "Share", "Log out",
    "Terms of Use", "Privacy Policy", "Cookies",
}
HDR_RE = re.compile(r"^(?:مخ المشروع|gpt[\w.\-]*(?: instant| thinking)?|o[1-9]\w*|"
                    r"claude[\w.\- ]{0,14}|gemini[\w.\- ]{0,10})$")
LANG_RE = re.compile(r"^(?:text|txt|cmd|bash|sh|bat|json|ya?ml|toml|csv|tsv|python|py|sql|"
                     r"js|ts|html|css|xml|log|out|output|console|diff|ini|md|markdown|"
                     r"powershell|ps1|dockerfile)$", re.I)


class Block:
    __slots__ = ("kind", "lines")

    def __init__(self, kind: str, lines: list[str]):
        self.kind = kind
        self.lines = lines

    def text(self) -> str:
        return "\n".join(self.lines)


ART_CHARS = "/\\|_-+^<>=(){}[].~`"


def line_is_art(line: str) -> bool:
    """one line of preformatted content: indented drawing, arrows, symbol soup."""
    t = line.rstrip()
    if not t.strip():
        return False
    if t.startswith(("  ", "\t")):
        return True
    if len(BOX.findall(t)) + len(ARROW.findall(t)) >= 3:
        return True
    art = sum(t.count(c) for c in ART_CHARS)
    letters = sum(1 for c in t if c.isalpha() and not RTL.match(c))
    arabic = len(RTL.findall(t))
    if art >= 2 and letters + arabic == 0:      # pure symbols / digits (price ladders…)
        return True
    return len(t) < 72 and art >= 3 and art > 0.5 * (letters + arabic)


def parse(raw: str) -> list[Block]:
    blocks: list[Block] = []
    buf: list[str] = []

    def emit(body, art):
        if not body:
            return
        if art:
            blocks.append(Block("diag", body))
        else:
            b = Block("p", body)
            b.kind = classify(b)
            blocks.append(b)

    def flush():
        nonlocal buf
        body = [l for l in buf if l.strip()]
        buf = []
        if not body:
            return
        # split a paragraph into runs of "art" lines and "prose" lines so that
        # ascii drawings keep their columns while Arabic still flows RTL
        run, is_art = [body[0]], line_is_art(body[0])
        for l in body[1:]:
            if line_is_art(l) == is_art:
                run.append(l)
            else:
                emit(run, is_art)
                run, is_art = [l], line_is_art(l)
        emit(run, is_art)

    for line in raw.split("\n"):
        s = line.strip()
        if s in UI_NOISE:
            continue
        if HDR_RE.match(s):
            flush()
            blocks.append(Block("hdr", [s]))
            continue
        if not s:
            if buf:
                flush()
            continue
        if len(s) <= 12 and LANG_RE.match(s) and (not buf or not buf[-1].strip()):
            flush()
            blocks.append(Block("tag", [s]))
            continue
        buf.append(line.rstrip("\r"))
    flush()
    return blocks


ART_CHARS = "/\\|_-+^<>=(){}[].~`"


def is_art(lines: list[str], body: str) -> bool:
    """multi-line preformatted content: ascii art, trees, tables, shell dumps."""
    if len(lines) < 2:
        return False
    if sum(1 for l in lines if l.startswith(("  ", "\t"))) >= 2:      # indentation matters
        return True
    if len(BOX.findall(body)) + len(ARROW.findall(body)) >= 3:
        return True
    art = sum(body.count(c) for c in ART_CHARS)
    letters = sum(1 for c in body if c.isalpha() and not RTL.match(c))
    return len(lines) >= 3 and art > 0.18 * len(body) and art >= letters


def classify(b: Block) -> str:
    lines, body = b.lines, "".join(b.lines)
    n = len(body) or 1
    gfx = len(BOX.findall(body)) + len(ARROW.findall(body))
    if gfx and (gfx >= 3 or gfx / n > 0.02) and not RTL.search(body):
        return "diag"                      # pure art -> LTR mono, never reflowed
    if is_art(lines, body):
        return "diag"
    arabic = len(RTL.findall(body))
    if len(lines) >= 2 and arabic < 6 and body.count("{") >= 2 and "\": " in body:
        return "code"
    return "p"


# ---------------------------------------------------------------- PDF
BODY_SIZE, MONO_SIZE = 9.8, 8.1
LEAD, MONO_LEAD = 5.0, 3.6
GAP = 2.0
NAVY = (16, 26, 44)


class TranscriptPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_margins(14, 13, 14)
        self.set_auto_page_break(True, margin=15)
        for (fam, style), path in FONTS.items():
            self.add_font(fam, style, str(path))
        self.set_line_width(0.2)
        self.set_compression(True)
        self.set_text_shaping(True)

    def footer(self):
        if self.page_no() <= 2:
            return
        self.set_y(-11.5)
        self.set_text_shaping(True, direction="rtl")
        self.set_font("sans", "", 7.8)
        self.set_text_color(110, 110, 110)
        self.cell(0, 5, str(self.page_no()), align=Align.C)
        self.set_y(-18)
        self.set_font("sans", "", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 4, prep("سجل المحادثات — zzz.txt"), align=Align.C)

    def body_cell(self, text: str, face: str, size: float, lead: float,
                  align: Align, rtl: bool, fill: float | None = None) -> None:
        self.set_text_shaping(True, direction="rtl" if rtl else "ltr")
        if fill is not None:
            self.set_fill_color(*fill)
        self.set_font(face, "", size)
        self.set_text_color(22, 22, 22)
        self.multi_cell(0, lead, text, align=align, wrapmode=WrapMode.WORD,
                        new_x="LMARGIN", new_y="NEXT")


def cover(pdf: TranscriptPDF, stats: dict) -> None:
    pdf.add_page()
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, 210, 297, style="F")
    pdf.set_draw_color(90, 140, 220)
    pdf.set_line_width(0.8)
    pdf.set_y(89)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.set_text_shaping(True, direction="rtl")
    pdf.set_y(60)
    pdf.set_font("sans", "B", 30)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, prep("سجل المحادثات"), align=Align.C, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("sans", "", 12.5)
    pdf.set_text_color(196, 212, 238)
    pdf.cell(0, 9, prep("نسخة PDF كاملة من ملف zzz.txt — بدون حذف أو تعديل في النص"),
             align=Align.C, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("sans", "", 10)
    pdf.set_text_color(150, 172, 205)
    pdf.cell(0, 7, prep("كل الأسطر محفوظة، تغيّر التنسيق فقط — مع فهرس وترقيم صفحات وعلامات تنقّل"),
             align=Align.C, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_shaping(True, direction="ltr")
    pdf.set_y(101)
    pdf.set_font("mono", "", 9.6)
    pdf.set_text_color(228, 236, 248)
    for k, v in stats.items():
        pdf.set_x(46)
        pdf.cell(118, 7.4, f"{k:<8}: {v}", align=Align.L, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_shaping(True, direction="rtl")
    pdf.set_y(190)
    pdf.set_font("sans", "", 10.3)
    pdf.set_text_color(178, 196, 224)
    pdf.multi_cell(0, 6.4, prep(
        "الملف الأصلي هو نسخة نصية من محادثة طويلة: أسئلة المستخدم، أجوبة النموذج، رسوم نصية "
        "للحركة السعرية، ومخرجات تدقيق وأكواد. "
        "استُخدم خط DejaVu Sans للنص العربي والإنجليزي وDejaVu Sans Mono للرسوم النصية والأكواد "
        "حتى لا تتفكك المحاذاة، مع تشكيل الحروف العربية والتشكيل كاملاً. "
        "بعض الرموز التعبيرية (emoji) غير موجودة في الخط فاستُبدلت برموز مكافئة ✓ ✗ ● ★، "
        "ولم يُحذف أي كلام."
    ), align=Align.R, new_x="LMARGIN", new_y="NEXT")


TOC_ROW_H = 6.0
TOC_HEAD_H = 17.5            # title + subtitle + gap on the first index page
SAFETY = 2                   # spare rows per page, so the count never under-shoots


def toc_page_count(rows: int, usable: float, top_margin: float) -> int:
    """how many pages the index needs, with the exact geometry toc_render uses"""
    cap_first = max(1, int((usable - top_margin - TOC_HEAD_H) // TOC_ROW_H) - SAFETY)
    cap_rest = max(1, int((usable - top_margin) // TOC_ROW_H) - SAFETY)
    pages, left, cap = 1, rows, cap_first
    while left > 0:
        left -= cap
        if left > 0:
            pages += 1
            cap = cap_rest
    return pages


def toc_render(pdf: TranscriptPDF, outline) -> None:
    """index page(s): page number on the left, section label hugging the right margin"""
    usable = pdf.page_break_trigger
    y = pdf.get_y()
    pdf.set_text_shaping(True, direction="rtl")
    pdf.set_xy(14, y)
    pdf.set_font("sans", "B", 15)
    pdf.set_text_color(*NAVY)
    pdf.cell(182, 9, prep("الفهرس"), align=Align.R, new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(14, pdf.get_y())
    pdf.set_font("sans", "", 8.4)
    pdf.set_text_color(120, 125, 135)
    pdf.cell(182, 5, prep(f"عدد الأقسام: {len(outline)}  •  رقم الصفحة على اليسار"),
             align=Align.R, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.5)
    y = pdf.get_y()
    for sec in outline:
        if y + TOC_ROW_H > usable:
            pdf.add_page()
            y = pdf.get_y()
        label = prep(sec.name)
        pdf.set_font("sans", "B", 9.4)
        lw = pdf.get_string_width(label)
        if lw > 150:
            label = label[:60] + "\u2026"
            lw = pdf.get_string_width(label)
        label_x = 196 - lw
        pdf.set_xy(14, y)
        pdf.set_font("sans", "", 8.6)
        pdf.set_text_color(30, 60, 110)
        pdf.cell(15, 5.2, str(sec.page_number), align=Align.L)
        if label_x - 33 > 3:
            pdf.set_xy(31, y)
            pdf.set_text_color(165, 170, 180)
            dots = "\u00b7" * max(1, int((label_x - 33) / max(0.5, pdf.get_string_width("\u00b7"))))
            pdf.cell(label_x - 33, 5.2, dots, align=Align.L)
        pdf.set_font("sans", "B", 9.4)
        pdf.set_text_color(*NAVY)
        pdf.set_xy(label_x, y)
        pdf.cell(lw, 5.2, label, align=Align.L)
        pdf.set_draw_color(228, 230, 235)
        pdf.line(14, y + 5.4, 196, y + 5.4)
        y += TOC_ROW_H
        pdf.set_y(y)
    pdf.set_text_shaping(True, direction="ltr")


def emit_block(pdf: TranscriptPDF, b: Block, idx: int, hdr_no: list[int]) -> None:
    if b.kind == "hdr":
        if idx:
            pdf.ln(GAP + 1)
        if pdf.get_y() > 252:
            pdf.add_page()
        hdr_no[0] += 1
        pdf.start_section(f"{b.lines[0]} \u2014 {hdr_no[0]}", level=0)
        y = pdf.get_y()
        pdf.set_fill_color(*NAVY)
        pdf.rect(14, y, 182, 8.2, style="F")
        pdf.set_xy(17, y + 1.4)
        pdf.set_text_shaping(True, direction="rtl")
        pdf.set_font("sans", "B", 11.5)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 6, prep(b.lines[0]), align=Align.R)
        pdf.set_y(y + 8.2)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2.4)
        return

    if b.kind == "tag":
        pdf.set_text_shaping(True, direction="ltr")
        pdf.set_font("mono", "", 7.2)
        pdf.set_text_color(145, 145, 145)
        pdf.cell(0, 4.0, f"[{prep(b.lines[0], 'mono')}]", align=Align.R,
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        return

    raw = prep(b.text())
    if b.kind in ("diag", "code"):
        face, size, lead, align, rtl = "mono", MONO_SIZE, MONO_LEAD, Align.L, False
        if len(b.lines) > 1:
            # render the block line by line: keeps the column alignment of the art
            raw = "\n".join(l.rstrip() for l in raw.split("\n"))
    else:
        face = pick_face(raw)
        size, lead = (BODY_SIZE, LEAD) if face == "sans" else (MONO_SIZE, MONO_LEAD)
        rtl = bool(RTL.search(raw))
        align = Align.R if rtl else Align.L

    if len(raw.split("\n")) <= 2 and pdf.get_y() > 268:
        pdf.add_page()

    if b.kind in ("diag", "code"):
        nlines = raw.count("\n") + 1
        y0 = pdf.get_y()
        room = 282 - y0
        if 0 < room > lead * (min(nlines, 60) + 1.4):
            pdf.set_fill_color(244, 245, 248)
            pdf.rect(14, y0 - 1.0, 182, lead * (min(nlines, 60) + 0.8), style="F")

    pdf.body_cell(raw, face, size, lead, align, rtl)
    pdf.ln(GAP)


def main() -> None:
    raw = SRC.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    blocks = parse(raw)
    if LIMIT:
        blocks = blocks[:LIMIT]
    n_lines = len([l for l in raw.split("\n") if l.strip()])
    stats = {
        "FILE": "TRADING-BOT/zzz.txt",
        "SIZE": f"{SRC.stat().st_size / 1048576:.2f} MB",
        "LINES": f"{n_lines:,}".replace(",", "\u202f"),
        "CHARS": f"{len(raw):,}".replace(",", "\u202f"),
        "BLOCKS": f"{len(blocks):,}".replace(",", "\u202f"),
        "DATE": "2026-10-01",
    }
    pdf = TranscriptPDF()
    pdf.set_title("سجل المحادثات — zzz.txt")
    pdf.set_creator("Arena agent (fpdf2 + uharfbuzz + DejaVu)")
    pdf.set_subject("PDF export of zzz.txt")
    pdf.set_keywords("trading bot, MUF, field runner, transcript, BTC")
    pdf.set_lang("ar")
    cover(pdf, stats)
    pdf.add_page()
    # reserve exactly as many index pages as the section list needs, so the page
    # numbers written while rendering the body stay valid (no late page insertion)
    rows = sum(1 for b in blocks if b.kind == "hdr")
    toc_pages = toc_page_count(rows, pdf.page_break_trigger, pdf.t_margin)
    pdf.insert_toc_placeholder(toc_render, pages=toc_pages, allow_extra_pages=False)
    hdr_no = [0]
    for i, b in enumerate(blocks):
        emit_block(pdf, b, i, hdr_no)
    pdf.output(str(OUT))
    print(f"pages={pdf.page_no()} blocks={len(blocks)} size={OUT.stat().st_size/1048576:.2f}MB -> {OUT}")


if __name__ == "__main__":
    main()
