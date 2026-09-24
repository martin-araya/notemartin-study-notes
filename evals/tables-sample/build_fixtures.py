#!/usr/bin/env python3
"""build_fixtures.py — Generate synthetic fixtures for F23 eval.

Builds three PDFs:
  - large-table-fixture.pdf: 1 page, 35 rows × 5 columns, simple header.
  - merged-cells-fixture.pdf: 1 page, 5×5 with 3 merged cells (one rowspan,
    one colspan, one intersection).
  - cross-page-table-fixture.pdf: 2 pages, 24 rows (12+12) with header
    repeated on page 2.

Uses reportlab to draw clean tables with explicit coordinates.

Writes to evals/tables-sample/fixtures/.
"""

from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _draw_cell(c: canvas.Canvas, x: float, y: float, w: float, h: float, text: str, font_size: float = 10, bold: bool = False) -> None:
    if bold:
        c.setFont("Helvetica-Bold", font_size)
    else:
        c.setFont("Helvetica", font_size)
    c.drawString(x + 4, y + h / 2 - 3, text)


def _build_large_table() -> Path:
    out = FIXTURES / "large-table-fixture.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    headers = ["id", "name", "category", "price", "stock"]
    rows = 35
    x_start = 0.75 * inch
    y_start = 9.5 * inch
    col_widths = [0.6 * inch, 1.5 * inch, 1.0 * inch, 0.8 * inch, 0.6 * inch]
    row_height = 0.20 * inch

    c.setFont("Helvetica-Bold", 11)
    for i, h in enumerate(headers):
        x = x_start + sum(col_widths[:i])
        c.drawString(x + 4, y_start - row_height + 3, h)
    c.line(x_start, y_start - row_height, x_start + sum(col_widths), y_start - row_height)

    for r_idx in range(rows):
        y = y_start - (r_idx + 2) * row_height
        for c_idx, w in enumerate(col_widths):
            x = x_start + sum(col_widths[:c_idx])
            c.setFont("Helvetica", 9)
            value = f"r{r_idx + 1:02d}-c{c_idx + 1}"
            c.drawString(x + 4, y + 3, value)
        c.line(x_start, y, x_start + sum(col_widths), y)
    c.line(x_start, y_start, x_start, y_start - (rows + 2) * row_height)
    for i, w in enumerate(col_widths):
        x = x_start + sum(col_widths[:i + 1])
        c.line(x, y_start, x, y_start - (rows + 2) * row_height)

    c.showPage()
    c.save()
    return out


def _build_merged_cells() -> Path:
    out = FIXTURES / "merged-cells-fixture.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    headers = ["A", "B", "C", "D", "E"]
    rows = 5
    cols = 5
    x_start = 0.75 * inch
    y_start = 9.5 * inch
    cell_w = 1.0 * inch
    cell_h = 0.5 * inch

    grid: list[list[str]] = [
        ["Header A", "Combined Header (colspan 3)", "", "", "E"],
        ["", "", "", "", ""],
        ["Row 3", "B3", "C3", "D3", "E3"],
        ["Group X (rowspan 2)", "B4", "C4", "D4", "E4"],
        ["", "B5", "C5", "D5", "E5"],
    ]

    c.setFont("Helvetica-Bold", 11)
    for i, h in enumerate(headers):
        x = x_start + i * cell_w
        c.drawString(x + 4, y_start - cell_h + 3, h)

    for r_idx, row in enumerate(grid):
        y = y_start - (r_idx + 2) * cell_h
        for c_idx, text in enumerate(row):
            if not text:
                continue
            x = x_start + c_idx * cell_w
            c.setFont("Helvetica", 9)
            c.drawString(x + 4, y + cell_h - 14, text)

    merged_lines = [
        (0, 1, 1, 4),
        (3, 0, 5, 1),
    ]
    for r1, c1, r2, c2 in merged_lines:
        x1 = x_start + c1 * cell_w
        y1 = y_start - r1 * cell_h
        x2 = x_start + c2 * cell_w
        y2 = y_start - r2 * cell_h
        c.setLineWidth(2)
        c.setStrokeColorRGB(1, 0, 0)
        c.rect(x1, y2, x2 - x1, y1 - y2, stroke=1, fill=0)
        c.setLineWidth(1)
        c.setStrokeColorRGB(0, 0, 0)

    c.showPage()
    c.save()
    return out


def _draw_table_with_header(c: canvas.Canvas, page_num: int, headers: list[str], rows_data: list[list[str]], x_start: float, y_start: float, col_widths: list[float], row_height: float) -> None:
    c.setFont("Helvetica-Bold", 10)
    for i, h in enumerate(headers):
        x = x_start + sum(col_widths[:i])
        c.drawString(x + 4, y_start - row_height + 3, h)
    c.line(x_start, y_start - row_height, x_start + sum(col_widths), y_start - row_height)

    for r_idx, row in enumerate(rows_data):
        y = y_start - (r_idx + 2) * row_height
        for c_idx, val in enumerate(row):
            x = x_start + sum(col_widths[:c_idx])
            c.setFont("Helvetica", 9)
            c.drawString(x + 4, y + 3, val)
        c.line(x_start, y, x_start + sum(col_widths), y)
    c.line(x_start, y_start, x_start, y_start - (len(rows_data) + 2) * row_height)
    for i in range(len(col_widths)):
        x = x_start + sum(col_widths[:i + 1])
        c.line(x, y_start, x, y_start - (len(rows_data) + 2) * row_height)


def _build_cross_page_table() -> Path:
    out = FIXTURES / "cross-page-table-fixture.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    headers = ["id", "name", "category", "price"]
    rows_p1 = [[str(i), f"Item {i}", chr(65 + (i % 3)), f"{(i * 1.5):.2f}"] for i in range(1, 13)]
    rows_p2 = [[str(i), f"Item {i}", chr(65 + (i % 3)), f"{(i * 1.5):.2f}"] for i in range(13, 25)]

    c.setFont("Helvetica", 11)
    c.drawString(0.75 * inch, 10.5 * inch, "Product Catalog (continued across pages)")
    _draw_table_with_header(c, 1, headers, rows_p1, 0.75 * inch, 10.0 * inch, [0.6 * inch, 2.0 * inch, 1.2 * inch, 1.0 * inch], 0.30 * inch)
    c.showPage()

    c.setFont("Helvetica", 11)
    c.drawString(0.75 * inch, 10.5 * inch, "Product Catalog (continued from previous page)")
    _draw_table_with_header(c, 2, headers, rows_p2, 0.75 * inch, 10.0 * inch, [0.6 * inch, 2.0 * inch, 1.2 * inch, 1.0 * inch], 0.30 * inch)
    c.showPage()
    c.save()
    return out


def main() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    f1 = _build_large_table()
    print(f"Wrote {f1} ({f1.stat().st_size} bytes)")
    f2 = _build_merged_cells()
    print(f"Wrote {f2} ({f2.stat().st_size} bytes)")
    f3 = _build_cross_page_table()
    print(f"Wrote {f3} ({f3.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
