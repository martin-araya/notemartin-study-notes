#!/usr/bin/env python3
"""build_fixtures.py — Generate synthetic fixtures for F20 eval.

Builds three PNGs at high contrast:
  - ocr-fixture.png: simple English text (PostgreSQL chapter intro)
  - bilingual-fixture.png: Spanish + English mixed text
  - low-confidence-fixture.png: noisy / low-contrast version that
    produces mean_conf < 0.70 with Tesseract to exercise retry path

Uses Pillow directly (no reportlab dependency) so fixtures are
self-contained and reproducible.

Writes to evals/ocr-sample/fixtures/.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FIXTURES = Path(__file__).resolve().parent / "fixtures"

W_PX, H_PX = 1700, 2200  # 8.5"×11" at 200 DPI


def _find_font(prefer_size: int) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, prefer_size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_lines(out: Image.Image, lines: List[Tuple[str, int]], start_y: int = 200) -> int:
    draw = ImageDraw.Draw(out)
    y = start_y
    for text, size in lines:
        font = _find_font(size)
        draw.text((150, y), text, fill=(20, 20, 20), font=font)
        y += int(size * 1.6)
    return y


def _build_ocr_fixture() -> Path:
    out = FIXTURES / "ocr-fixture.png"
    img = Image.new("RGB", (W_PX, H_PX), color=(255, 255, 255))
    lines = [
        ("PostgreSQL 16 Documentation", 44),
        ("", 18),
        ("The SQL Language", 30),
        ("", 18),
        ("This chapter describes the SQL language in PostgreSQL.", 22),
        ("It covers data definition, manipulation, and queries.", 22),
        ("Tables, indexes, and constraints are explained.", 22),
        ("", 18),
        ("SELECT statements retrieve data from tables.", 22),
        ("INSERT statements add new rows to a table.", 22),
        ("UPDATE statements modify existing rows.", 22),
        ("DELETE statements remove rows from a table.", 22),
        ("", 18),
        ("Every command follows standard SQL syntax.", 22),
    ]
    _draw_lines(img, lines, start_y=200)
    img.save(out, format="PNG", optimize=True)
    return out


def _build_bilingual_fixture() -> Path:
    out = FIXTURES / "bilingual-fixture.png"
    img = Image.new("RGB", (W_PX, H_PX), color=(255, 255, 255))
    lines = [
        ("PostgreSQL y el lenguaje SQL", 36),
        ("", 18),
        ("Esta guía explica cómo usar SQL en PostgreSQL.", 22),
        ("Incluye SELECT, INSERT, UPDATE y DELETE.", 22),
        ("", 18),
        ("Tables and indexes are core concepts in SQL.", 22),
        ("Each table has columns and rows of data.", 22),
        ("", 18),
        ("Las consultas (queries) leen datos de las tablas.", 22),
        ("You can use SELECT to retrieve specific columns.", 22),
        ("", 18),
        ("Filters allow you to retrieve only specific rows.", 22),
        ("Los filtros WHERE limitan los resultados.", 22),
        ("", 18),
        ("Sorting and grouping are also supported.", 22),
        ("El agrupamiento se hace con GROUP BY.", 22),
        ("", 18),
        ("Las funciones de agregación son COUNT, SUM, AVG.", 22),
        ("Aggregate functions compute over multiple rows.", 22),
        ("", 18),
        ("For more details, consult the official documentation.", 22),
    ]
    _draw_lines(img, lines, start_y=200)
    img.save(out, format="PNG", optimize=True)
    return out


def _build_low_confidence_fixture() -> Path:
    out = FIXTURES / "low-confidence-fixture.png"
    img = Image.new("RGB", (W_PX, H_PX), color=(210, 210, 210))
    draw = ImageDraw.Draw(img)
    y = 200
    text_lines = [
        ("Documentation is essential for understanding systems.", 22),
        ("Reading guides helps new users learn the basics quickly.", 22),
        ("Examples illustrate how commands work in practice.", 22),
        ("Each command has a specific purpose and syntax.", 22),
        ("Tables store rows of related data with named columns.", 22),
        ("Queries retrieve data matching user-specified criteria.", 22),
        ("Indexes speed up data retrieval for large tables.", 22),
        ("Constraints enforce data integrity at all times.", 22),
        ("Transactions ensure atomic operations on the database.", 22),
        ("Concurrency control prevents data corruption issues.", 22),
    ]
    for text, size in text_lines:
        font = _find_font(size)
        draw.text((150, y), text, fill=(160, 160, 160), font=font)
        y += int(size * 1.6)
    arr = np.array(img, dtype=np.int16)
    noise = np.random.default_rng(seed=42).normal(0, 35, arr.shape).astype(np.int16)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr, mode="RGB")
    img.save(out, format="PNG")
    return out


def main() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    f1 = _build_ocr_fixture()
    print(f"Wrote {f1} ({f1.stat().st_size} bytes)")
    f2 = _build_bilingual_fixture()
    print(f"Wrote {f2} ({f2.stat().st_size} bytes)")
    f3 = _build_low_confidence_fixture()
    print(f"Wrote {f3} ({f3.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
