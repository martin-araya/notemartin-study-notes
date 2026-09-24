#!/usr/bin/env python3
"""build_fixtures.py — Generate synthetic fixtures for F26 eval.

Builds two PDFs and a small ingest directory layout:
  - degraded-source-fixture.pdf: 1 page with code + table + formula + text
    (mixed confidence, used to verify image+text side-by-side).
  - blocked-source-fixture.pdf: 1 page with 4 critical regions (code, table,
    formula, syntax_diagram) all marked low_confidence, used to verify the
    blocking policy.

Also produces a fake ingest/ directory tree so the script has inputs to read.

Writes to evals/review-sample/fixtures/.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

FIXTURES = Path(__file__).resolve().parent / "fixtures"

MONO_FONT = "Courier"
BODY_FONT = "Helvetica"


def _draw_clean_pdf() -> Path:
    """1-page PDF with code + table + formula + text (degraded but parseable)."""
    out = FIXTURES / "degraded-source-fixture.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    c.setFont(BODY_FONT, 11)
    c.drawString(0.75 * inch, 10.5 * inch, "Mixed-content source page (some low confidence):")
    c.setFont(MONO_FONT, 9)

    c.drawString(0.75 * inch, 10.0 * inch, "def hello():")
    c.drawString(0.75 * inch, 9.8 * inch, "    pass")
    c.drawString(0.75 * inch, 9.5 * inch, "id | name | price")
    c.drawString(0.75 * inch, 9.3 * inch, "1  | Widget | 10.00")
    c.drawString(0.75 * inch, 9.1 * inch, "2  | Gadget | 20.00")
    c.setFont(BODY_FONT, 11)
    c.drawString(0.75 * inch, 8.7 * inch, "Inline formula: f(x) = \\alpha x + \\beta")
    c.drawString(0.75 * inch, 8.4 * inch, "Some prose paragraph with normal text and minor OCR noise.")
    c.showPage()
    c.save()
    return out


def _draw_blocked_pdf() -> Path:
    """1-page PDF that triggers 4 critical low_confidence regions."""
    out = FIXTURES / "blocked-source-fixture.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    c.setFont(BODY_FONT, 11)
    c.drawString(0.75 * inch, 10.5 * inch, "Very degraded source (BLOCKED):")
    c.setFont(MONO_FONT, 9)

    c.drawString(0.75 * inch, 10.0 * inch, "def foo():")
    c.drawString(0.75 * inch, 9.8 * inch, "    pass")
    c.drawString(0.75 * inch, 9.5 * inch, "id | name | price")
    c.drawString(0.75 * inch, 9.3 * inch, "1  | W | 10")
    c.drawString(0.75 * inch, 9.1 * inch, "2  | G | 20")
    c.setFont(BODY_FONT, 11)
    c.drawString(0.75 * inch, 8.7 * inch, "f(x) = \\fract{1}{2}")
    c.drawString(0.75 * inch, 8.4 * inch, "if (a): x = 1")
    c.showPage()
    c.save()
    return out


def main() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    p1 = _draw_clean_pdf()
    print(f"Wrote {p1} ({p1.stat().st_size} bytes)")
    p2 = _draw_blocked_pdf()
    print(f"Wrote {p2} ({p2.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
