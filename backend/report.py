"""
PDF report: turns an analysis result into a downloadable PDF.

The LLM writes Markdown (bullets, bold, headings), so each section is converted
Markdown -> HTML -> PDF with fpdf2. A bundled Unicode font (DejaVu Sans) is used
because PDF's built-in fonts can't print characters like ’ “ ” – ₹.
"""

import os
import re
from datetime import date

import markdown
from fpdf import FPDF
from fpdf.fonts import TextStyle

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(BASE_DIR, "assets", "fonts")
FONT = "DejaVu"

ACCENT = (184, 91, 36)  # same orange as the app, darkened for print
TEXT = (33, 31, 29)
MUTED = (115, 109, 102)
RULE = (222, 216, 208)

# Headings inside the LLM's Markdown sit *under* our section headings, so keep them small
TAG_STYLES = {
    "h1": TextStyle(font_style="B", font_size_pt=13, color=TEXT, t_margin=4, b_margin=1),
    "h2": TextStyle(font_style="B", font_size_pt=12, color=TEXT, t_margin=4, b_margin=1),
    "h3": TextStyle(font_style="B", font_size_pt=11, color=TEXT, t_margin=3, b_margin=1),
    "h4": TextStyle(font_style="B", font_size_pt=10.5, color=TEXT, t_margin=3, b_margin=1),
    "p": TextStyle(font_size_pt=10.5, color=TEXT, t_margin=1.5, b_margin=1.5),
    # List text takes its style from the ul/ol tag in fpdf2, so all three are set
    "ul": TextStyle(font_size_pt=10.5, color=TEXT, t_margin=1, b_margin=1),
    "ol": TextStyle(font_size_pt=10.5, color=TEXT, t_margin=1, b_margin=1),
    "li": TextStyle(font_size_pt=10.5, color=TEXT, t_margin=1, l_margin=6),  # 6 mm per nesting level
    "code": TextStyle(font_size_pt=10, color=TEXT),
}


class ReportPDF(FPDF):
    def footer(self):
        self.set_y(-14)
        self.set_font(FONT, "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 6, f"Meeting Assistant report  ·  page {self.page_no()} of {{nb}}", align="C")


def _new_pdf(title: str) -> ReportPDF:
    pdf = ReportPDF(format="A4")
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(True, margin=20)
    pdf.add_font(FONT, "", os.path.join(FONT_DIR, "DejaVuSans.ttf"))
    pdf.add_font(FONT, "B", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"))
    pdf.add_font(FONT, "I", os.path.join(FONT_DIR, "DejaVuSans-Oblique.ttf"))
    pdf.add_font(FONT, "BI", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"))
    pdf.set_title(title)
    pdf.set_creator("Meeting Assistant")
    pdf.add_page()
    return pdf


def _section_heading(pdf: FPDF, text: str):
    # Don't leave a heading alone at the bottom of a page
    if pdf.get_y() > pdf.h - pdf.b_margin - 35:
        pdf.add_page()
    pdf.ln(4)
    pdf.set_font(FONT, "B", 14)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 9, text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*RULE)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(2)


def _fix_list_indent(text: str) -> str:
    """LLMs indent nested lists by 2-3 spaces, but Markdown needs 4 - round up to multiples of 4."""
    return re.sub(
        r"^( +)(?=(?:[-*+]|\d+[.)]) )",
        lambda m: " " * (-(-len(m.group(1)) // 4) * 4),
        text,
        flags=re.MULTILINE,
    )


def _markdown_block(pdf: FPDF, text: str):
    """Renders LLM Markdown; falls back to plain text if the HTML can't be laid out."""
    html = markdown.markdown(_fix_list_indent(text or ""), extensions=["sane_lists"])
    # fpdf2 reads line spacing from a line-height attribute on these tags
    html = re.sub(r"<(p|ul|ol)>", r'<\1 line-height="1.3">', html)
    # List text uses the current font rather than a tag style, so reset it to body text
    pdf.set_font(FONT, "", 10.5)
    pdf.set_text_color(*TEXT)
    try:
        pdf.write_html(
            html,
            font_family=FONT,
            tag_styles=TAG_STYLES,
            li_prefix_color=ACCENT,
            warn_on_tags_not_matching=False,
        )
    except Exception:
        _plain_block(pdf, text)


def _plain_block(pdf: FPDF, text: str, size: float = 10.5):
    pdf.set_font(FONT, "", size)
    pdf.set_text_color(*TEXT)
    pdf.multi_cell(0, size * 0.55, text or "", align="L", new_x="LMARGIN", new_y="NEXT")


def build_pdf_report(result: dict, meta: dict | None = None) -> bytes:
    """Returns the full analysis (title, summary, insights, transcript) as PDF bytes."""
    meta = meta or {}
    title = result.get("title") or "Meeting report"
    pdf = _new_pdf(title)

    # Title block
    details = [meta.get("source"), meta.get("engine"),
               f"{meta['words']:,} words" if meta.get("words") else None,
               date.today().strftime("%d %b %Y")]
    pdf.set_font(FONT, "", 9)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 6, "  ·  ".join(d for d in details if d), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(FONT, "B", 20)
    pdf.set_text_color(*TEXT)
    pdf.multi_cell(0, 9.5, title, align="L", new_x="LMARGIN", new_y="NEXT")

    for heading, key in [
        ("Summary", "summary"),
        ("Action items", "action_items"),
        ("Key decisions", "key_decisions"),
        ("Open questions", "open_questions"),
    ]:
        _section_heading(pdf, heading)
        _markdown_block(pdf, result.get(key, ""))

    # Transcript is plain speech-to-text output, not Markdown
    _section_heading(pdf, "Transcript")
    _plain_block(pdf, result.get("transcript", ""), size=9.5)

    return bytes(pdf.output())
