#!/usr/bin/env python3
"""build_fixtures.py — Generate synthetic fixtures for F24 eval.

Builds three PDFs:
  - latex-fixture.pdf: 1 page with 4 valid block formulas + 2 valid inline
    formulas. All formulas compile under the F24 regex validator.
  - pending-fixture.pdf: 1 page with 1 invalid formula (`\\fract{1}{2}` with typo).
  - numbered-equations-fixture.pdf: 2 pages with 2 numbered formulas (1.1) and
    (1.2) plus a text reference "see eq. (1.1)" adjacent.

Uses reportlab to draw LaTeX-like text. Note: reportlab does NOT render LaTeX
glyphs; we draw the LaTeX source as plain text in a monospaced font, simulating
how F18 would extract the LaTeX source from a PDF written by LaTeX.

Writes to evals/formulas-sample/fixtures/.
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


def _build_latex_fixture() -> Path:
    """4 valid block formulas + 2 valid inline formulas."""
    out = FIXTURES / "latex-fixture.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    c.setFont(BODY_FONT, 11)
    c.drawString(0.75 * inch, 10.5 * inch, "Formulas (all valid LaTeX):")
    c.setFont(MONO_FONT, 11)

    block_formulas = [
        r"\frac{\partial L}{\partial \theta} = \sum_{i=1}^{n} x_i - \mu",
        r"\int_{a}^{b} f(x) \, dx = F(b) - F(a)",
        r"\sqrt{x^2 + y^2} = \sqrt{r^2}",
        r"\binom{n}{k} = \frac{n!}{k!(n-k)!}",
    ]
    y = 10 * inch
    for formula in block_formulas:
        c.drawString(0.75 * inch, y, formula)
        y -= 0.45 * inch

    c.setFont(BODY_FONT, 11)
    c.drawString(0.75 * inch, y - 0.1 * inch, "Inline formulas in prose:")
    c.setFont(MONO_FONT, 11)
    y -= 0.6 * inch

    inline_lines = [
        r"The function f(x) = \alpha x + \beta is linear.",
        r"The limit \lim_{n \to \infty} 1/n = 0.",
    ]
    for line in inline_lines:
        c.drawString(0.75 * inch, y, line)
        y -= 0.35 * inch

    c.showPage()
    c.save()
    return out


def _build_pending_fixture() -> Path:
    """1 invalid formula (typo)."""
    out = FIXTURES / "pending-fixture.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    c.setFont(BODY_FONT, 11)
    c.drawString(0.75 * inch, 10.5 * inch, "Formula with typo (invalid):")
    c.setFont(MONO_FONT, 11)
    invalid_formula = r"\fract{1}{2} + \sqrt{3}"
    c.drawString(0.75 * inch, 10 * inch, invalid_formula)
    c.showPage()
    c.save()
    return out


def _build_numbered_equations() -> Path:
    """2 numbered formulas (1.1) and (1.2) plus a text reference."""
    out = FIXTURES / "numbered-equations-fixture.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)

    c.setFont(BODY_FONT, 11)
    c.drawString(0.75 * inch, 10.5 * inch, "Equations")
    c.setFont(MONO_FONT, 11)

    c.drawString(0.75 * inch, 10 * inch, r"E = mc^2")
    c.setFont(BODY_FONT, 11)
    c.drawString(6.0 * inch, 10 * inch, "(1.1)")

    c.setFont(MONO_FONT, 11)
    c.drawString(0.75 * inch, 9.5 * inch, r"F = ma")
    c.setFont(BODY_FONT, 11)
    c.drawString(6.0 * inch, 9.5 * inch, "(1.2)")

    c.setFont(BODY_FONT, 11)
    c.drawString(0.75 * inch, 8.5 * inch, "From the relation (1.1) we can derive the energy formula.")
    c.showPage()

    c.setFont(BODY_FONT, 11)
    c.drawString(0.75 * inch, 10.5 * inch, "Continued")
    c.setFont(MONO_FONT, 11)
    c.drawString(0.75 * inch, 10 * inch, r"\nabla \cdot E = 0")
    c.setFont(BODY_FONT, 11)
    c.drawString(6.0 * inch, 10 * inch, "(1.3)")
    c.showPage()
    c.save()
    return out


def main() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    f1 = _build_latex_fixture()
    print(f"Wrote {f1} ({f1.stat().st_size} bytes)")
    f2 = _build_pending_fixture()
    print(f"Wrote {f2} ({f2.stat().st_size} bytes)")
    f3 = _build_numbered_equations()
    print(f"Wrote {f3} ({f3.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
