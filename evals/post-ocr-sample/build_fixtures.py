#!/usr/bin/env python3
"""build_fixtures.py — Generate synthetic fixtures for F27 eval.

Builds four PDFs and a dictionary.yaml:
  - prose-fixture.pdf: 1 page with prose that activates R001, R002, R005, D001.
  - code-fixture.pdf: 1 page with Python code (must NOT be modified).
  - table-fixture.pdf: 1 page with a 4×4 table (must NOT be modified).
  - revert-fixture.pdf: 1 page with prose activable for revert test.

Writes to evals/post-ocr-sample/fixtures/.
"""

from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

FIXTURES = Path(__file__).resolve().parent / "fixtures"

MONO_FONT = "Courier"
BODY_FONT = "Helvetica"


def _draw_prose() -> Path:
    """Prose with line-break missing space (R001), multiple newlines (R002),
    ligature ﬁ (R005), PostgresQL typo (D001)."""
    out = FIXTURES / "prose-fixture.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    c.setFont(BODY_FONT, 11)
    c.drawString(0.75 * inch, 10.5 * inch, "PostgresQL is a database")
    c.drawString(0.75 * inch, 10.3 * inch, "that handles JSON.")
    c.drawString(0.75 * inch, 10.0 * inch, "It has many features")
    c.drawString(0.75 * inch, 9.8 * inch, "including transactions.")
    c.showPage()
    c.save()
    return out


def _draw_code() -> Path:
    """Python code with 4-space indentation (must NOT be modified)."""
    out = FIXTURES / "code-fixture.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    c.setFont(MONO_FONT, 10)
    lines = [
        "def hello():",
        "    print('hi')",
        "    return 0",
        "",
        "def add(a, b):",
        "    return a + b",
    ]
    y = 10.0 * inch
    for line in lines:
        c.drawString(0.75 * inch, y, line)
        y -= 0.18 * inch
    c.showPage()
    c.save()
    return out


def _draw_table() -> Path:
    """Table 4x4 (must NOT be modified)."""
    out = FIXTURES / "table-fixture.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    c.setFont(MONO_FONT, 10)
    headers = ["id", "name", "qty", "price"]
    data = [
        ["1", "Widget", "100", "$10.00"],
        ["2", "Gadget", "50", "$20.00"],
        ["3", "Gizmo", "75", "$15.00"],
    ]
    x_start = 0.75 * inch
    y = 10.0 * inch
    col_widths = [0.6 * inch, 1.2 * inch, 0.6 * inch, 0.8 * inch]
    for i, h in enumerate(headers):
        c.drawString(x_start + sum(col_widths[:i]), y, h)
    y -= 0.25 * inch
    for row in data:
        for c_idx, val in enumerate(row):
            c.drawString(x_start + sum(col_widths[:c_idx]), y, val)
        y -= 0.22 * inch
    c.showPage()
    c.save()
    return out


def _draw_revert() -> Path:
    """Prose with R002 activable for revert test."""
    out = FIXTURES / "revert-fixture.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    c.setFont(BODY_FONT, 11)
    c.drawString(0.75 * inch, 10.5 * inch, "Para uno.")
    c.drawString(0.75 * inch, 10.3 * inch, "")
    c.drawString(0.75 * inch, 10.1 * inch, "")
    c.drawString(0.75 * inch, 9.9 * inch, "")
    c.drawString(0.75 * inch, 9.7 * inch, "Para dos.")
    c.showPage()
    c.save()
    return out


def main() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for fn in (_draw_prose, _draw_code, _draw_table, _draw_revert):
        p = fn()
        print(f"Wrote {p} ({p.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
