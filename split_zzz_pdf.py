#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Split zzz.pdf into several self-contained volumes, each <= 90 pages:

  volume = 1 generated cover page (title + index of that volume) + the source pages
           of the conversations it contains.  Sections are never cut in the middle,
           page numbers in the index stay the ones of the full file (as printed in
           each page footer), and every volume gets its own PDF bookmarks.

  .venv/bin/python split_zzz_pdf.py [max_pages]     (default 90)
"""
from __future__ import annotations

import sys
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import Align
from pypdf import PdfReader, PdfWriter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_zzz_pdf import FONTS, NAVY, prep  # reuse fonts + glyph sanitizer

SRC = Path(__file__).resolve().parent / "zzz.pdf"
OUTDIR = Path(__file__).resolve().parent


def sections_of(reader: PdfReader) -> list[tuple[str, int]]:
    flat: list[tuple[str, int]] = []

    def walk(items):
        for it in items:
            if isinstance(it, list):
                walk(it)
            else:
                try:
                    flat.append((it.title, reader.get_destination_page_number(it)))
                except Exception:
                    pass

    walk(reader.outline or [])
    seen, out = set(), []
    for title, page in sorted(flat, key=lambda t: t[1]):      # order by page, not by title
        if (title, page) not in seen:
            seen.add((title, page))
            out.append((title, page))
    return out


def plan(total: int, front: int, secs: list[tuple[str, int]], cap: int) -> list[list]:
    """pack whole conversations into volumes of at most `cap` source pages"""
    budget = cap - 1                                  # one page goes to the cover
    parts: list[list] = [[0, front, []]]             # [start, end, [(title, page)]]
    for i, (title, page) in enumerate(secs):
        end = secs[i + 1][1] if i + 1 < len(secs) else total
        cur = parts[-1]
        if cur[2] and (cur[1] - cur[0]) + (end - page) > budget:
            parts.append([cur[1], end, [(title, page)]])
        else:
            cur[1] = end
            cur[2].append((title, page))
    if not parts[-1][2] and len(parts) > 1:           # nothing but front matter? merge back
        parts[-2][1] = parts[-1][1]
        parts.pop()
    return parts


class VolumeCover(FPDF):
    """single dark cover page, same look as the master document"""

    def __init__(self, rows: int):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_margins(14, 13, 14)
        self.set_auto_page_break(True, margin=14)
        for (fam, style), path in FONTS.items():
            self.add_font(fam, style, str(path))
        self.set_compression(True)
        self.set_text_shaping(True)
        self.rows = rows

    def render(self, index: int, count: int, first_page: int, last_page: int,
               full_pages: int, entries: list[tuple[str, int]]) -> None:
        self.add_page()
        self.set_fill_color(*NAVY)
        self.rect(0, 0, 210, 297, style="F")
        self.set_text_shaping(True, direction="rtl")
        self.set_y(24)
        self.set_font("sans", "B", 21)
        self.set_text_color(255, 255, 255)
        self.cell(0, 11, prep("سجل المحادثات — zzz.txt"), align=Align.C,
                  new_x="LMARGIN", new_y="NEXT")
        self.set_font("sans", "", 13)
        self.set_text_color(196, 212, 238)
        self.cell(0, 9, prep(f"الجزء {index} من {count}"), align=Align.C,
                  new_x="LMARGIN", new_y="NEXT")
        self.set_font("sans", "", 10.4)
        self.set_text_color(150, 172, 205)
        self.cell(0, 7, prep(f"الصفحات {first_page}–{last_page} من أصل {full_pages}"
                             f"  •  {len(entries)} محادثة"), align=Align.C,
                  new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(90, 140, 220)
        self.set_line_width(0.7)
        self.ln(3)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(5)

        # index of this volume (page numbers = the ones printed in the footers)
        for title, page in entries:
            if self.get_y() > 268:
                self.add_page()
                self.set_fill_color(*NAVY)
                self.rect(0, 0, 210, 297, style="F")
                self.set_text_color(255, 255, 255)
            label = prep(f"{title}")
            self.set_font("sans", "", 9)
            self.set_text_color(206, 220, 242)
            self.set_x(14)
            self.cell(150, 5.2, label, align=Align.R)
            self.set_x(164)
            self.set_font("sans", "B", 9)
            self.set_text_color(255, 255, 255)
            self.cell(32, 5.2, str(page + 1), align=Align.R,    # +1: 0-based -> printed number
                      new_x="LMARGIN", new_y="NEXT")
        self.set_y(276)
        self.set_font("sans", "", 8.2)
        self.set_text_color(150, 172, 205)
        self.cell(0, 6, prep("أرقام الصفحات هنا هي أرقام الملف الكامل — كل جزء مستقل بذاته"),
                  align=Align.C)


def build(index: int, count: int, reader: PdfReader, start: int, end: int,
          entries: list[tuple[str, int]], total_pages: int, out_path: Path) -> None:
    cover = VolumeCover(len(entries))
    cover.render(index, count, start + 1, end, total_pages, entries)
    tmp = out_path.with_suffix(".cover.pdf")
    cover.output(str(tmp))

    writer = PdfWriter()
    writer.append(str(tmp), import_outline=False)               # the volume cover page
    writer.append(reader, pages=(start, end), import_outline=False)  # 0-based, stop excluded
    for title, page in entries:
        local = 1 + (page - start)                              # +1 because of the cover page
        if 0 < local < len(writer.pages):
            writer.add_outline_item(title, local)
    writer.add_metadata({
        "/Title": f"سجل المحادثات — zzz.txt — الجزء {index} من {count}",
        "/Author": "Arena agent",
        "/Subject": f"pages {start + 1}-{end} of zzz.pdf",
        "/Creator": "fpdf2 + pypdf",
    })
    with open(out_path, "wb") as fh:
        writer.write(fh)
    tmp.unlink(missing_ok=True)


def main() -> None:
    cap = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 90
    reader = PdfReader(str(SRC))
    total = len(reader.pages)
    secs = sections_of(reader)
    if not secs:
        raise SystemExit("no bookmarks found in zzz.pdf")
    front = secs[0][1]
    parts = plan(total, front, secs, cap)
    if parts and parts[0][0] == 0:
        parts[0][0] = 1          # drop the master cover: each volume ships its own
    print(f"{total} pages, {len(secs)} conversations -> {len(parts)} volumes "
          f"(max {cap} pages each)")
    made = []
    for i, (start, end, entries) in enumerate(parts, 1):
        out = OUTDIR / f"zzz_part_{i:02d}.pdf"
        build(i, len(parts), reader, start, end, entries, total, out)
        pages = len(PdfReader(str(out)).pages)
        assert pages <= cap, (out, pages)
        made.append((out, pages, start + 1, end, len(entries)))
    for out, pages, a, b, n in made:
        print(f"  {out.name:20s} {pages:3d} pages | src {a:4d}-{b:4d} | {n:3d} محادثة | "
              f"{out.stat().st_size/1048576:.2f} MB")
    print(f"volumes in {OUTDIR}")


if __name__ == "__main__":
    main()
