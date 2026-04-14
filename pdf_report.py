"""PDF report generator for CAPA Intelligence — professional, monochrome output."""

import io
import re
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Colour palette (monochrome) ───────────────────────────────────────────────
BLACK      = colors.HexColor("#000000")
DARK_GREY  = colors.HexColor("#1A1A1A")
MID_GREY   = colors.HexColor("#555555")
LIGHT_GREY = colors.HexColor("#CCCCCC")
RULE_GREY  = colors.HexColor("#AAAAAA")
HEADER_BG  = colors.HexColor("#EEEEEE")
WHITE      = colors.white

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm

# ── Styles ────────────────────────────────────────────────────────────────────
def _build_styles():
    base = getSampleStyleSheet()

    def s(name, **kw):
        return ParagraphStyle(name, **kw)

    return {
        "cover_title": s(
            "cover_title",
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=28,
            textColor=BLACK,
            alignment=TA_LEFT,
        ),
        "cover_sub": s(
            "cover_sub",
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            textColor=MID_GREY,
            alignment=TA_LEFT,
        ),
        "cover_meta": s(
            "cover_meta",
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=MID_GREY,
            alignment=TA_LEFT,
        ),
        "h1": s(
            "h1",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=18,
            textColor=BLACK,
            spaceBefore=10,
            spaceAfter=4,
        ),
        "h2": s(
            "h2",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=DARK_GREY,
            spaceBefore=8,
            spaceAfter=3,
        ),
        "h3": s(
            "h3",
            fontName="Helvetica-BoldOblique",
            fontSize=10,
            leading=14,
            textColor=DARK_GREY,
            spaceBefore=6,
            spaceAfter=2,
        ),
        "body": s(
            "body",
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=DARK_GREY,
            spaceAfter=4,
        ),
        "bullet": s(
            "bullet",
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=DARK_GREY,
            leftIndent=12,
            spaceAfter=2,
            bulletIndent=4,
        ),
        "table_header": s(
            "table_header",
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=BLACK,
            alignment=TA_LEFT,
        ),
        "table_cell": s(
            "table_cell",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=DARK_GREY,
            alignment=TA_LEFT,
            wordWrap="CJK",
        ),
        "footer": s(
            "footer",
            fontName="Helvetica",
            fontSize=7,
            textColor=RULE_GREY,
            alignment=TA_CENTER,
        ),
    }


STYLES = _build_styles()

# ── Helpers ───────────────────────────────────────────────────────────────────
_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001FFFF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]+",
    flags=re.UNICODE,
)


def _strip_emoji(text: str) -> str:
    return _EMOJI_RE.sub("", text)


def _md_inline(text: str) -> str:
    """Convert markdown inline formatting to reportlab XML."""
    text = _strip_emoji(text)
    # Escape XML special chars first (except & which we handle separately)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Bold+italic ***text***
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", text)
    # Bold **text**
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Italic *text* or _text_
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"_(.+?)_", r"<i>\1</i>", text)
    # Inline code `text`
    text = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", text)
    return text.strip()


def _para(text: str, style_key: str = "body") -> Paragraph:
    return Paragraph(_md_inline(text), STYLES[style_key])


def _hr() -> HRFlowable:
    return HRFlowable(width="100%", thickness=0.5, color=RULE_GREY, spaceAfter=4)


# ── Table builder ─────────────────────────────────────────────────────────────
def _build_table(rows: list[list[str]]) -> Table:
    """Build a reportlab Table from a list of row lists (first row = header)."""
    col_count = max(len(r) for r in rows)

    # Pad short rows
    padded = [r + [""] * (col_count - len(r)) for r in rows]

    # Convert cells to Paragraphs
    def cell(text, is_header):
        style = "table_header" if is_header else "table_cell"
        return Paragraph(_md_inline(text), STYLES[style])

    data = [
        [cell(c, i == 0) for c in row]
        for i, row in enumerate(padded)
    ]

    # Column widths — distribute evenly within available width
    available = PAGE_W - 2 * MARGIN
    col_w = available / col_count

    tbl = Table(data, colWidths=[col_w] * col_count, repeatRows=1)
    tbl.setStyle(
        TableStyle([
            # Header row
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, 0), 8),
            # All cells
            ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",   (0, 1), (-1, -1), 8),
            ("TEXTCOLOR",  (0, 0), (-1, -1), DARK_GREY),
            ("VALIGN",     (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
            # Grid
            ("GRID",       (0, 0), (-1, -1), 0.4, LIGHT_GREY),
            ("LINEBELOW",  (0, 0), (-1, 0),  0.8, BLACK),
            # Alternating row shading (very subtle)
            *[
                ("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F7F7F7"))
                for i in range(2, len(data), 2)
            ],
        ])
    )
    return tbl


# ── Markdown parser → flowables ───────────────────────────────────────────────
def _parse_markdown(md_text: str) -> list:
    """Parse markdown text and return a list of reportlab flowables."""
    flowables = []
    lines = md_text.splitlines()
    i = 0
    table_rows: list[list[str]] = []

    def flush_table():
        nonlocal table_rows
        if table_rows:
            flowables.append(Spacer(1, 2 * mm))
            flowables.append(_build_table(table_rows))
            flowables.append(Spacer(1, 3 * mm))
            table_rows = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip horizontal rules (--- or ***)
        if re.match(r"^[-*]{3,}$", stripped):
            flush_table()
            flowables.append(_hr())
            i += 1
            continue

        # Heading detection
        h_match = re.match(r"^(#{1,4})\s+(.*)", stripped)
        if h_match:
            flush_table()
            level = len(h_match.group(1))
            text = h_match.group(2)
            style = {1: "h1", 2: "h1", 3: "h2", 4: "h3"}.get(level, "h2")
            if level <= 2:
                flowables.append(Spacer(1, 3 * mm))
            flowables.append(_para(text, style))
            if level <= 2:
                flowables.append(_hr())
            i += 1
            continue

        # Table row
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            # Skip separator rows (|---|---|)
            if all(re.match(r"^[-:]+$", c.replace(" ", "")) for c in cells if c):
                i += 1
                continue
            table_rows.append(cells)
            i += 1
            continue

        # Non-table line encountered — flush pending table
        flush_table()

        # Blank line
        if not stripped:
            flowables.append(Spacer(1, 2 * mm))
            i += 1
            continue

        # Bullet / list item
        if re.match(r"^[-*+]\s+", stripped):
            text = re.sub(r"^[-*+]\s+", "", stripped)
            flowables.append(_para(f"- {text}", "bullet"))
            i += 1
            continue

        # Numbered list
        if re.match(r"^\d+\.\s+", stripped):
            text = re.sub(r"^\d+\.\s+", "", stripped)
            flowables.append(_para(f"- {text}", "bullet"))
            i += 1
            continue

        # Regular paragraph
        flowables.append(_para(stripped, "body"))
        i += 1

    flush_table()
    return flowables


# ── Cover page ────────────────────────────────────────────────────────────────
def _cover_page(
    incident_id: str,
    site: str,
    product: str,
    model: str,
    timestamp_utc: str,
    sha256: str,
) -> list:
    elements = []
    elements.append(Spacer(1, 18 * mm))
    elements.append(_para("CAPA Intelligence", "cover_title"))
    elements.append(_para("Root Cause Analysis &amp; Corrective Action Report", "cover_sub"))
    elements.append(Spacer(1, 6 * mm))
    elements.append(_hr())
    elements.append(Spacer(1, 4 * mm))

    meta_rows = [
        ["Incident ID",    incident_id or "—"],
        ["Site",           site or "—"],
        ["Product",        product or "—"],
        ["Analysis Model", model or "—"],
        ["Generated (UTC)", timestamp_utc or "—"],
        ["Record SHA-256", sha256[:32] + "…" if sha256 else "—"],
    ]

    meta_data = [
        [
            Paragraph(k, STYLES["table_header"]),
            Paragraph(_strip_emoji(v), STYLES["table_cell"]),
        ]
        for k, v in meta_rows
    ]

    available = PAGE_W - 2 * MARGIN
    meta_tbl = Table(meta_data, colWidths=[55 * mm, available - 55 * mm])
    meta_tbl.setStyle(
        TableStyle([
            ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE",      (0, 0), (-1, -1), 9),
            ("TEXTCOLOR",     (0, 0), (-1, -1), DARK_GREY),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
            ("LINEBELOW",     (0, 0), (-1, -1), 0.3, LIGHT_GREY),
            ("BACKGROUND",    (0, 0), (0, -1),  HEADER_BG),
        ])
    )

    elements.append(meta_tbl)
    elements.append(Spacer(1, 8 * mm))
    elements.append(_hr())
    elements.append(Spacer(1, 4 * mm))
    elements.append(
        _para(
            "This report was generated by an AI-assisted CAPA Intelligence system. "
            "All findings must be reviewed and approved by a qualified QA professional "
            "before use in regulated activities. The SHA-256 hash provides a tamper-evident "
            "record of this document's content under 21 CFR Part 11 and EU GMP Annex 11.",
            "cover_meta",
        )
    )
    return elements


# ── Page number callback ──────────────────────────────────────────────────────
def _add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(RULE_GREY)
    page_num = f"Page {doc.page}"
    canvas.drawRightString(PAGE_W - MARGIN, 10 * mm, page_num)
    canvas.drawString(
        MARGIN,
        10 * mm,
        "CAPA Intelligence  |  Biocon  |  Confidential — For Internal Use Only",
    )
    canvas.setStrokeColor(RULE_GREY)
    canvas.setLineWidth(0.3)
    canvas.line(MARGIN, 12 * mm, PAGE_W - MARGIN, 12 * mm)
    canvas.restoreState()


# ── Public API ────────────────────────────────────────────────────────────────
def generate_pdf(
    incident_id: str,
    site: str,
    product: str,
    model: str,
    rca_text: str,
    capa_text: str,
    timestamp_utc: str = "",
    sha256: str = "",
) -> bytes:
    """Return a PDF report as bytes."""
    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=18 * mm,
        title=f"CAPA Report — {incident_id}",
        author="CAPA Intelligence (AI-assisted)",
        subject="Root Cause Analysis and CAPA Action Plan",
    )

    story = []

    # Cover page
    story.extend(
        _cover_page(incident_id, site, product, model, timestamp_utc, sha256)
    )
    story.append(Spacer(1, 8 * mm))

    # RCA section
    story.append(_para("Root Cause Analysis", "h1"))
    story.append(_hr())
    story.extend(_parse_markdown(rca_text))

    # CAPA section
    story.append(Spacer(1, 6 * mm))
    story.append(_para("CAPA Action Plan", "h1"))
    story.append(_hr())
    story.extend(_parse_markdown(capa_text))

    doc.build(story, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    return buf.getvalue()
