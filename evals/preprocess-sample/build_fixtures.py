#!/usr/bin/env python3
"""build_fixtures.py — Generate synthetic fixtures for F19 eval.

Builds:
  - rotated-test.pdf: 3 pages with controlled rotations 0°, +3°, -5°
  - blank-test.pdf: 5 pages (2 with text, 3 blank)
  - hostile-scan.png: PNG with rotation 3° + noise + spine shadow

Uses reportlab for the PDF builder, Pillow + numpy for the PNG fixture.

Writes to evals/preprocess-sample/fixtures/.
"""

from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _build_rotated_test() -> Path:
    """3 pages with text rotated by 0°, +3°, -5° via reportlab canvas.rotate()."""
    out = FIXTURES / "rotated-test.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    rotations = [0.0, 3.0, -5.0]
    for i, angle in enumerate(rotations, 1):
        w, h = LETTER
        c.saveState()
        c.translate(w / 2.0, h / 2.0)
        c.rotate(angle)
        c.translate(-w / 2.0, -h / 2.0)
        c.setFont("Helvetica-Bold", 36)
        c.drawString(1 * inch, 10 * inch, f"Page {i} (target rotation: {angle:+.0f})")
        c.setFont("Helvetica", 12)
        body = (
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
            "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris "
            "nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in "
            "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
            "pariatur. Excepteur sint occaecat cupidatat non proident."
        )
        y = 9 * inch
        for line in body.split(". "):
            c.drawString(1 * inch, y, line + ".")
            y -= 0.4 * inch
        c.restoreState()
        c.showPage()
    c.save()
    return out


def _build_blank_test() -> Path:
    """5 pages: 2 with substantial text (pages 1 and 3), 3 blank."""
    out = FIXTURES / "blank-test.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    has_text_pages = {1, 3}
    body = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
        "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
        "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris "
        "nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in "
        "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
        "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in "
        "culpa qui officia deserunt mollit anim id est laborum."
    )
    for page_num in range(1, 6):
        if page_num in has_text_pages:
            c.setFont("Helvetica-Bold", 24)
            c.drawString(1 * inch, 10 * inch, f"Page {page_num} — Content")
            c.setFont("Helvetica", 11)
            y = 9.5 * inch
            for _ in range(20):
                c.drawString(1 * inch, y, body)
                y -= 0.25 * inch
        c.showPage()
    c.save()
    return out


def _build_hostile_scan() -> Path:
    """Single PNG with rotation 3° + Gaussian noise + spine shadow.

    Built at 150 DPI (smaller than 300 to keep size modest for eval).
    """
    out = FIXTURES / "hostile-scan.png"
    dpi = 150
    w_in, h_in = 8.5, 11
    w_px, h_px = int(w_in * dpi), int(h_in * dpi)
    img = Image.new("RGB", (w_px, h_px), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)

    text_lines = [
        "HOSTILE SCAN TEST PAGE",
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
        "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        "Ut enim ad minim veniam, quis nostrud exercitation.",
        "Duis aute irure dolor in reprehenderit in voluptate.",
        "Excepteur sint occaecat cupidatat non proident, sunt in culpa.",
        "Curabitur pretium tincidunt lacus. Nulla gravida orci a odio.",
        "Nullam varius, turpis et commodo pharetra, est eros bibendum elit.",
        "Integer in mauris eu nibh euismod laoreet.",
        "Praesent dapibus turpis eu ipsum. Suspendisse potenti.",
        "Fusce sagittis, libero nonummy malesuada, lorem ipsum.",
        "Aliquam erat volutpat. Sed in dolor nec turpis.",
    ]
    y = 1.0 * inch * dpi / 72
    for line in text_lines:
        draw.text((1.2 * inch * dpi / 72, y), line, fill=(20, 20, 20))
        y += 0.5 * inch * dpi / 72

    spine_w = int(0.6 * inch * dpi / 72)
    for x in range(spine_w):
        factor = (spine_w - x) / spine_w
        shade = int(245 - 90 * factor)
        for yy in range(h_px):
            r, g, b = img.getpixel((x, yy))
            img.putpixel((x, yy), (min(r, shade), min(g, shade), min(b, shade)))

    rng = np.random.default_rng(seed=42)
    arr = np.array(img, dtype=np.int16)
    noise = rng.normal(0, 25, arr.shape).astype(np.int16)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr, mode="RGB")

    img = img.rotate(3, resample=Image.BICUBIC, fillcolor=(245, 245, 245))

    img.save(out, format="PNG", optimize=True)
    return out


def main() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    rt = _build_rotated_test()
    print(f"Wrote {rt} ({rt.stat().st_size} bytes)")
    bt = _build_blank_test()
    print(f"Wrote {bt} ({bt.stat().st_size} bytes)")
    hs = _build_hostile_scan()
    print(f"Wrote {hs} ({hs.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
