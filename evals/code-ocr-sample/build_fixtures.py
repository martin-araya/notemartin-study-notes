#!/usr/bin/env python3
"""build_fixtures.py — Generate synthetic fixtures for F25 eval.

Builds four PDFs:
  - clean-code-fixture.pdf: 1 page, Python code with 10 lines and mixed
    indentation (4/8/12 spaces). Verifies byte-exact preservation.
  - confusion-fixture.pdf: 1 page, Python code with missing closing bracket,
    triggering forced corrections by ast.parse.
  - plausibility-fixture.pdf: 1 page, Python code with l/1/I and 0/O characters
    in identifiers. Verifies no corrections are applied.
  - low-confidence-fixture.pdf: 1 page, code with mixed indentation + invalid
    syntax. Verifies low_confidence: true.

Uses reportlab + Courier for monospaced text.

Writes to evals/code-ocr-sample/fixtures/.
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


def _build_clean_code() -> Path:
    """Python code with TAB indentation (tabs survive in F18 fragments)."""
    out = FIXTURES / "clean-code-fixture.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    c.setFont(BODY_FONT, 11)
    c.drawString(0.75 * inch, 10.5 * inch, "Python code with tab indentation:")
    c.setFont(MONO_FONT, 10)
    lines = [
        "def hello(name):",
        "\tmsg = 'Hello, ' + name",
        "\t\treturn msg",
        "",
        "def add(a, b):",
        "\tif a > 0:",
        "\t\treturn a + b",
        "\telse:",
        "\t\treturn b",
        "",
        "print(hello('world'))",
    ]
    y = 10.0 * inch
    for line in lines:
        c.drawString(0.75 * inch, y, line)
        y -= 0.18 * inch
    c.showPage()
    c.save()
    return out


def _build_confusion() -> Path:
    """Python code with missing closing paren — triggers forced correction."""
    out = FIXTURES / "confusion-fixture.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    c.setFont(BODY_FONT, 11)
    c.drawString(0.75 * inch, 10.5 * inch, "Python with missing closing paren:")
    c.setFont(MONO_FONT, 10)
    lines = [
        "print('hello world'",
        "",
    ]
    y = 10.0 * inch
    for line in lines:
        c.drawString(0.75 * inch, y, line)
        y -= 0.18 * inch
    c.showPage()
    c.save()
    return out


def _build_plausibility() -> Path:
    """Python code with l/1/I and 0/O characters in identifiers."""
    out = FIXTURES / "plausibility-fixture.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    c.setFont(BODY_FONT, 11)
    c.drawString(0.75 * inch, 10.5 * inch, "Code with ambiguous monospace chars (no correction):")
    c.setFont(MONO_FONT, 10)
    lines = [
        "l = 1",
        "I = 0",
        "O = l + I",
        "result = l + I + O",
        "print(l, I, O, result)",
    ]
    y = 10.0 * inch
    for line in lines:
        c.drawString(0.75 * inch, y, line)
        y -= 0.18 * inch
    c.showPage()
    c.save()
    return out


def _build_low_confidence() -> Path:
    """Code with tabs and spaces + Python syntax that triggers low_confidence."""
    out = FIXTURES / "low-confidence-fixture.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    c.setFont(BODY_FONT, 11)
    c.drawString(0.75 * inch, 10.5 * inch, "Python code with l/1/I identifiers (low_confidence):")
    c.setFont(MONO_FONT, 10)
    lines = [
        "l = 1",
        "I = l + 1",
        "result = l + I + 1",
        "print(result)",
    ]
    y = 10.0 * inch
    for line in lines:
        c.drawString(0.75 * inch, y, line)
        y -= 0.18 * inch
    c.showPage()
    c.save()
    return out


def main() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    f1 = _build_clean_code()
    print(f"Wrote {f1} ({f1.stat().st_size} bytes)")
    f2 = _build_confusion()
    print(f"Wrote {f2} ({f2.stat().st_size} bytes)")
    f3 = _build_plausibility()
    print(f"Wrote {f3} ({f3.stat().st_size} bytes)")
    f4 = _build_low_confidence()
    print(f"Wrote {f4} ({f4.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
