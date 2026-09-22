#!/usr/bin/env python3
"""build_fixtures.py — Generate the synthetic fixtures for F18 eval.

Builds two PDFs:
  - boilerplate-test.pdf: 10 pages with repeated header/footer and a unique
    body paragraph per page. Validates that header/footer are detected as
    boilerplate (is_boilerplate=true) without affecting body content.
  - outline-test.pdf: 5 pages with PDF outline markers injected. Validates
    that headings are detected and outline entries are matched.

Uses reportlab (same dependency as F17 hybrid builder). pypdf is used to
inject the PDF outline in outline-test.pdf.

Writes to evals/pdf-native-sample/fixtures/.
"""

from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _build_boilerplate_test() -> Path:
    """10 pages with header + fixed footer line + per-page page-number footer
    + body unique per page. Header is detected as boilerplate (10/10 pages);
    footer line is also boilerplate; body is preserved without flag."""
    out = FIXTURES / "boilerplate-test.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    for page_num in range(1, 11):
        c.setFont("Helvetica", 9)
        c.drawString(1 * inch, 10.5 * inch, "Confidential Draft v1")
        c.setFont("Helvetica", 9)
        c.drawString(1 * inch, 0.5 * inch, "Internal Distribution Only")
        c.setFont("Helvetica", 9)
        c.drawString(5 * inch, 0.5 * inch, f"Page {page_num}")
        c.setFont("Times-Roman", 12)
        body_lines = [
            f"Body paragraph for page {page_num}.",
            "This is the main content of the document.",
            "It should remain in fragments.json without boilerplate flag.",
            "Each page has unique text here to ensure body is preserved.",
            "The header at top and footer at bottom are the boilerplate.",
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            "Sed do eiusmod tempor incididunt ut labore et dolore magna.",
        ]
        y = 9.5 * inch
        for line in body_lines:
            c.drawString(1 * inch, y, line)
            y -= 0.3 * inch
        c.showPage()
    c.save()
    return out


def _build_outline_test() -> Path:
    """5 pages with PDF outline. Chapter 1 spans pages 1-2 with sub-headings;
    Chapter 2 spans pages 3-5 with sub-headings."""
    out = FIXTURES / "outline-test.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    pages_content = [
        # page 1: Chapter 1 — Introduction
        [
            ("Chapter 1 — Introduction", "h1", 24),
            ("This is the introduction of the document.", "body", 12),
            ("It explains the purpose and scope.", "body", 12),
        ],
        # page 2: Chapter 1 — Background
        [
            ("Background", "h2", 18),
            ("Historical context and prior work.", "body", 12),
            ("We cite references here.", "body", 12),
        ],
        # page 3: Chapter 2 — Methods
        [
            ("Chapter 2 — Methods", "h1", 24),
            ("Our experimental setup is described here.", "body", 12),
            ("Tools and materials are listed.", "body", 12),
        ],
        # page 4: Chapter 2 — Results
        [
            ("Results", "h2", 18),
            ("Outcome of the experiments is shown.", "body", 12),
            ("Statistics and metrics follow.", "body", 12),
        ],
        # page 5: Chapter 2 — Conclusions
        [
            ("Conclusions", "h2", 18),
            ("We summarize the findings and discuss future work.", "body", 12),
            ("End of outline test document.", "body", 12),
        ],
    ]
    for page_lines in pages_content:
        y = 10 * inch
        for text, role, size in page_lines:
            if role == "h1":
                c.setFont("Helvetica-Bold", size)
            elif role == "h2":
                c.setFont("Helvetica-Bold", size)
            else:
                c.setFont("Times-Roman", size)
            c.drawString(1 * inch, y, text)
            y -= 0.5 * inch
        c.showPage()
    c.save()

    # Inject PDF outline using pypdf
    import pypdf
    reader = pypdf.PdfReader(str(out))
    writer = pypdf.PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    ch1_intro = writer.add_outline_item("Chapter 1 — Introduction", 0)
    writer.add_outline_item("Background", 1, parent=ch1_intro)
    ch2_methods = writer.add_outline_item("Chapter 2 — Methods", 2)
    writer.add_outline_item("Results", 3, parent=ch2_methods)
    writer.add_outline_item("Conclusions", 4, parent=ch2_methods)
    with open(out, "wb") as f:
        writer.write(f)
    return out


def main() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    bp = _build_boilerplate_test()
    print(f"Wrote {bp} ({bp.stat().st_size} bytes)")
    ot = _build_outline_test()
    print(f"Wrote {ot} ({ot.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
