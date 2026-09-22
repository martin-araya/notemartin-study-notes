#!/usr/bin/env python3
"""build_hybrid.py — Generate the synthetic hybrid PDF fixture for F17.

Builds an 8-page PDF with three classes interleaved:
  - Pages 1-3: native_reliable (lots of text + fonts, no large images)
  - Pages 4-5: pure_scan (full-page image, no extractable text)
  - Pages 6-8: native_degraded (short text or noisy text, ≤ 1 font, but
               not image-dominated — different from pages 4-5)

Pattern: R R R S S D D D  (R=reliable, S=scan, D=degraded)

This guarantees ≥ 3 distinct plan ranges regardless of collapse logic.

Writes to evals/triage-sample/fixtures/hybrid-synthetic.pdf.

Requires reportlab (declared in build_hybrid.py docstring). pypdf is used by
triage.py to analyze the resulting file.
"""

from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "hybrid-synthetic.pdf"


def _add_native_reliable(c: canvas.Canvas, page_num: int) -> None:
    """Pages 1-3: lots of text, no large image, multiple fonts."""
    c.setFont("Helvetica-Bold", 24)
    c.drawString(1 * inch, 10 * inch, f"Chapter {page_num} — Native Reliable Page")
    c.setFont("Helvetica", 12)
    body = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
        "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
        "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris "
        "nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in "
        "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
        "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in "
        "culpa qui officia deserunt mollit anim id est laborum. Curabitur "
        "pretium tincidunt lacus. Nulla gravida orci a odio. Nullam varius, "
        "turpis et commodo pharetra, est eros bibendum elit, nec luctus magna "
        "felis sollicitudin mauris. Integer in mauris eu nibh euismod laoreet. "
    )
    y = 9 * inch
    for paragraph in range(4):
        c.setFont("Times-Roman" if paragraph % 2 == 0 else "Courier", 11)
        c.drawString(1 * inch, y, body[: 60 + paragraph * 200])
        y -= 0.5 * inch
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(1 * inch, 1 * inch, f"End of reliable page {page_num}.")
    c.showPage()


def _add_pure_scan(c: canvas.Canvas, page_num: int) -> None:
    """Pages 4-5: full-page image, no text.

    To make pypdf detect a high full_page_image_rate, embed an image with
    native pixel dimensions equal to the page dimensions. Pypdf computes
    image_area = Width * Height / page_area; if the image itself is 612x792,
    the ratio is 1.0 regardless of any transformation matrix reportlab applies.
    """
    w, h = LETTER
    from io import BytesIO
    from PIL import Image, ImageDraw
    from reportlab.lib.utils import ImageReader

    img = Image.new("RGB", (int(w), int(h)), color=(235, 235, 235))
    draw = ImageDraw.Draw(img)
    draw.line((0, 0, int(w) - 1, int(h) - 1), fill=(40, 40, 40), width=3)
    draw.line((int(w) - 1, 0, 0, int(h) - 1), fill=(40, 40, 40), width=3)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    c.drawImage(ImageReader(buf), 0, 0, width=w, height=h)
    c.showPage()


def _add_native_degraded(c: canvas.Canvas, page_num: int) -> None:
    """Pages 6-8: short text + 1 font, no image. Just enough chars to be
    classified as degraded (≥ degraded_min=100, < reliable_min=1000)."""
    c.setFont("Helvetica", 11)
    body = (
        "Short page. Limited content here. This page intentionally contains "
        "only a small amount of text to test the degraded classification. "
        f"Page number {page_num}. End of content for this degraded page."
    )
    c.drawString(1 * inch, 10 * inch, body)
    c.drawString(1 * inch, 9.5 * inch, "A second line with a few words.")
    c.drawString(1 * inch, 9 * inch, "And a third short line.")
    c.showPage()


def main() -> int:
    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(FIXTURE_PATH), pagesize=LETTER)
    # 1-3 reliable
    for p in (1, 2, 3):
        _add_native_reliable(c, p)
    # 4-5 pure scan
    for p in (4, 5):
        _add_pure_scan(c, p)
    # 6-8 degraded
    for p in (6, 7, 8):
        _add_native_degraded(c, p)
    c.save()
    print(f"Wrote {FIXTURE_PATH} ({FIXTURE_PATH.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
