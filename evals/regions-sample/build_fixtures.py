#!/usr/bin/env python3
"""build_fixtures.py — Generate synthetic fixtures for F22 eval.

Builds three PDFs:
  - code-vs-text-fixture.pdf: 2 pp, left column normal prose, right column
    monospaced code blocks (with curly braces, semicolons, indentation).
  - editorial-boxes-fixture.pdf: 2 pp, 3 short editorial boxes (Note/Tip/
    Warning) per page, each surrounded by large vertical gaps.
  - ambiguous-region-fixture.pdf: 1 p, a single region with conflicting
    signals: monospaced font, large font_size, and centered alignment —
    no class should reach CLASS_MIN_THRESHOLD with AMBIGUITY_MARGIN.

Uses reportlab; the Menlo.ttc font is registered for monospace.

Writes to evals/regions-sample/fixtures/.
"""

from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

FIXTURES = Path(__file__).resolve().parent / "fixtures"

MONO_FONT = "Menlo"
MONO_PATH = "/System/Library/Fonts/Menlo.ttc"


def _register_mono() -> None:
    try:
        pdfmetrics.registerFont(TTFont(MONO_FONT, MONO_PATH, subfontIndex=0))
    except Exception:
        # Fallback: use Courier built-in
        pass


def _draw_normal_text(c: canvas.Canvas, x: float, y: float, text: str, lines: int = 8) -> float:
    c.setFont("Helvetica", 11)
    y -= 0.25 * inch
    for i, line in enumerate(text.split(". ")[:lines]):
        if not line.strip():
            continue
        if not line.strip().endswith("."):
            line += "."
        c.drawString(x, y, line)
        y -= 0.20 * inch
    return y


def _draw_code(c: canvas.Canvas, x: float, y: float, code: str) -> float:
    c.setFont(MONO_FONT, 9)
    y -= 0.25 * inch
    for line in code.split("\n"):
        c.drawString(x, y, line)
        y -= 0.15 * inch
    return y


def _build_code_vs_text() -> Path:
    out = FIXTURES / "code-vs-text-fixture.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    left_x = 0.75 * inch
    right_x = 4.25 * inch
    text_prose = (
        "Databases are essential for storing structured information. "
        "Each table has a unique name and a defined set of columns. "
        "Indexes accelerate data retrieval by avoiding full table scans. "
        "Queries allow selective reading of rows matching user criteria. "
        "Constraints enforce data integrity at all times. "
        "Transactions group operations into atomic units of work. "
        "Foreign keys reference rows in other tables. "
        "Materialized views precompute expensive aggregations."
    )
    code_block = """def fetch_user(id):
    user = db.query("SELECT * FROM users WHERE id = ?", id)
    if user is None:
        raise NotFound("user not found")
    return user

class UserService:
    def __init__(self, db):
        self.db = db

    def list(self):
        return db.query("SELECT id, name FROM users")
"""
    y_left = 10 * inch
    y_left = _draw_normal_text(c, left_x, y_left, text_prose, lines=4)
    y_left -= 0.3 * inch
    c.setFont("Helvetica-Bold", 13)
    c.drawString(left_x, y_left, "Indexes improve query speed")
    y_left -= 0.3 * inch
    y_left = _draw_normal_text(c, left_x, y_left, text_prose, lines=4)
    y_right = 10 * inch
    y_right = _draw_code(c, right_x, y_right, code_block)
    c.showPage()

    text_prose2 = (
        "Stored procedures encapsulate business logic on the server. "
        "Triggers execute automatically in response to data changes. "
        "Views provide named queries that simplify complex joins. "
        "Roles and grants control access to sensitive data. "
        "Audit logs record who changed what and when. "
        "Backups must be tested regularly for recoverability. "
        "Replication distributes reads across multiple replicas. "
        "Sharding partitions data across machines."
    )
    code_block2 = """async def get_user(id):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, name FROM users WHERE id = $1", id
        )
        if not row:
            raise HTTPError(404)
        return dict(row)
"""
    y_left = 10 * inch
    y_left = _draw_normal_text(c, left_x, y_left, text_prose2, lines=4)
    y_left -= 0.3 * inch
    c.setFont("Helvetica-Bold", 13)
    c.drawString(left_x, y_left, "Stored procedures and triggers")
    y_left -= 0.3 * inch
    y_left = _draw_normal_text(c, left_x, y_left, text_prose2, lines=4)
    y_right = 10 * inch
    y_right = _draw_code(c, right_x, y_right, code_block2)
    c.showPage()
    c.save()
    return out


def _build_editorial_boxes() -> Path:
    out = FIXTURES / "editorial-boxes-fixture.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    boxes_p1 = [
        ("Note:", "This is a note about something important. The author wants to call attention to a specific detail that might be overlooked by readers who skim through the chapter."),
        ("Tip:", "A useful tip for the reader. Save this for later reference because it contains a shortcut that will save you time when working with the system in production environments."),
        ("Warning:", "Be careful with this configuration. If you set this value incorrectly, the system will refuse to start and you may lose access to your data. Always test before deploying."),
    ]
    y = 10 * inch
    for tag, body in boxes_p1:
        c.setFont("Helvetica", 11)
        c.drawString(0.75 * inch, y, "Body text between editorial boxes provides context.")
        y -= 0.4 * inch
        c.setFont("Helvetica-Oblique", 11)
        c.drawString(0.75 * inch, y, tag + " " + body[:50])
        y -= 0.20 * inch
        rest = body[50:200]
        c.drawString(0.75 * inch, y, rest)
        y -= 0.6 * inch
    c.showPage()

    boxes_p2 = [
        ("Caution:", "Modifying this table requires downtime. Plan your maintenance window carefully and notify all stakeholders at least 24 hours in advance."),
        ("Important:", "The schema change is irreversible once applied. Make sure you have a tested backup before proceeding with the migration in production."),
        ("See also:", "The documentation chapter on caching strategies for additional context on how this interacts with the query planner."),
    ]
    y = 10 * inch
    for tag, body in boxes_p2:
        c.setFont("Helvetica", 11)
        c.drawString(0.75 * inch, y, "Body text between editorial boxes provides context.")
        y -= 0.4 * inch
        c.setFont("Helvetica-Oblique", 11)
        c.drawString(0.75 * inch, y, tag + " " + body[:50])
        y -= 0.20 * inch
        rest = body[50:200]
        c.drawString(0.75 * inch, y, rest)
        y -= 0.6 * inch
    c.showPage()
    c.save()
    return out


def _build_ambiguous_region() -> Path:
    """A region with conflicting signals that produce multiple competitive scores.

    Uses Helvetica (NOT monospace), centered, with math-like symbols to trigger
    S_SYMBOL_DENSITY + S_ALIGN_CENTER, while keeping the region between two
    strong class profiles (formula vs syntax_diagram). The font_size is mildly
    large but not headline-grade.
    """
    out = FIXTURES / "ambiguous-region-fixture.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    c.setFont("Helvetica", 16)
    text = "f(x) := x^2 + 2x + 1 → g(x) = ∑ xi + ∏ yj"
    text_w = pdfmetrics.stringWidth(text, "Helvetica", 16)
    page_w = LETTER[0]
    c.drawString((page_w - text_w) / 2, 5 * inch, text)
    c.showPage()
    c.save()
    return out


def main() -> int:
    _register_mono()
    FIXTURES.mkdir(parents=True, exist_ok=True)
    f1 = _build_code_vs_text()
    print(f"Wrote {f1} ({f1.stat().st_size} bytes)")
    f2 = _build_editorial_boxes()
    print(f"Wrote {f2} ({f2.stat().st_size} bytes)")
    f3 = _build_ambiguous_region()
    print(f"Wrote {f3} ({f3.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
