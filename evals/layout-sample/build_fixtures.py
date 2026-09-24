#!/usr/bin/env python3
"""build_fixtures.py — Generate synthetic fixtures for F21 eval.

Builds three PDFs with clean layout structure:
  - two-column-fixture.pdf: 2 pages, two columns with 3 paragraphs each (no
    figures/equations that confuse column detection)
  - cross-page-table.pdf: 2 pages, table with 12 rows (6+6) and 4 columns
  - broken-order-fixture.pdf: 2 pages; page 1 has correct 2-col order;
    page 2 has regions inverted

Uses reportlab to draw text at deterministic positions.

Writes to evals/layout-sample/fixtures/.
"""

from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _draw_two_columns(c: canvas.Canvas, paragraphs_left: list, paragraphs_right: list) -> None:
    """Draw two columns of paragraphs at fixed x positions."""
    c.setFont("Helvetica", 11)
    left_x = 0.75 * inch
    right_x = 4.25 * inch
    column_width = 3.25 * inch
    line_height = 0.20 * inch

    y = 10 * inch
    for para in paragraphs_left:
        for line in para.split(". "):
            line = line.strip()
            if not line:
                continue
            if not line.endswith("."):
                line += "."
            c.drawString(left_x, y, line)
            y -= line_height
        y -= line_height * 0.5

    y = 10 * inch
    for para in paragraphs_right:
        for line in para.split(". "):
            line = line.strip()
            if not line:
                continue
            if not line.endswith("."):
                line += "."
            c.drawString(right_x, y, line)
            y -= line_height
        y -= line_height * 0.5


def _build_two_column() -> Path:
    out = FIXTURES / "two-column-fixture.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    left_p = [
        "Databases organize information into structured tables with rows and columns of related data",
        "Each table has a unique name within a schema and a defined set of columns with types",
        "Indexes are auxiliary data structures that allow efficient lookup of rows matching criteria",
    ]
    right_p = [
        "Queries retrieve rows matching user-specified conditions and project selected columns from them",
        "Constraints enforce data integrity by rejecting inserts and updates that violate business rules",
        "Transactions group multiple statements into a single atomic unit with all-or-nothing semantics",
    ]
    _draw_two_columns(c, left_p, right_p)
    c.showPage()

    left_p2 = [
        "The first section introduced tables as the primary unit of storage",
        "The second section covered indexes for performance",
        "The third section will explain joins across multiple tables",
    ]
    right_p2 = [
        "Reads and writes use the same SQL syntax across the database engine",
        "Foreign keys reference rows in other tables to enforce referential integrity",
        "Materialized views precompute expensive aggregations to accelerate reporting queries",
    ]
    _draw_two_columns(c, left_p2, right_p2)
    c.showPage()
    c.save()
    return out


def _draw_table(c: canvas.Canvas, x: float, y: float, rows: int, cols: int, col_width: float, row_height: float, headers: list, data: list) -> float:
    c.setFont("Helvetica-Bold", 10)
    for i, header in enumerate(headers):
        c.drawString(x + i * col_width + 5, y - row_height + 3, header)
    c.setFont("Helvetica", 10)
    for r in range(rows):
        for i, value in enumerate(data[r]):
            c.drawString(x + i * col_width + 5, y - (r + 2) * row_height + 3, value)
    return y - (rows + 2) * row_height


def _build_cross_page_table() -> Path:
    out = FIXTURES / "cross-page-table.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    headers = ["id", "name", "category", "price"]
    data_p1 = [
        ["1", "Widget", "A", "10.00"],
        ["2", "Gadget", "B", "20.00"],
        ["3", "Gizmo", "A", "15.00"],
        ["4", "Doohickey", "C", "5.00"],
        ["5", "Thingamajig", "B", "25.00"],
        ["6", "Whatchamacallit", "C", "30.00"],
    ]
    data_p2 = [
        ["7", "Contraption", "A", "12.00"],
        ["8", "Doohickey2", "B", "18.00"],
        ["9", "Apparatus", "C", "22.00"],
        ["10", "Mechanism", "A", "8.00"],
        ["11", "Contraption2", "B", "16.00"],
        ["12", "Gadget2", "C", "28.00"],
    ]
    c.setFont("Helvetica", 11)
    c.drawString(0.75 * inch, 10.5 * inch, "Product Catalog (continued across pages)")
    _draw_table(c, 0.75 * inch, 10.0 * inch, 6, 4, 1.4 * inch, 0.30 * inch, headers, data_p1)
    c.showPage()
    c.setFont("Helvetica", 11)
    c.drawString(0.75 * inch, 10.5 * inch, "Product Catalog (continued from previous page)")
    _draw_table(c, 0.75 * inch, 10.0 * inch, 6, 4, 1.4 * inch, 0.30 * inch, headers, data_p2)
    c.showPage()
    c.save()
    return out


def _build_broken_order() -> Path:
    """Page 1: correct 2-col order. Page 2: regions emitted in inverted order."""
    out = FIXTURES / "broken-order-fixture.pdf"
    c = canvas.Canvas(str(out), pagesize=LETTER)
    left_p = [
        "The first chapter describes the architecture of the system",
        "Components interact via message passing with strict contracts",
    ]
    right_p = [
        "Reliability is achieved through redundancy and automatic failover",
        "Performance benchmarks show linear scaling with node count",
    ]
    _draw_two_columns(c, left_p, right_p)
    c.showPage()

    right_p_inv = [
        "Reliability is achieved through redundancy and automatic failover",
        "Performance benchmarks show linear scaling with node count",
    ]
    left_p_inv = [
        "The first chapter describes the architecture of the system",
        "Components interact via message passing with strict contracts",
    ]
    _draw_two_columns(c, left_p_inv, right_p_inv)
    c.showPage()
    c.save()
    return out


def main() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    f1 = _build_two_column()
    print(f"Wrote {f1} ({f1.stat().st_size} bytes)")
    f2 = _build_cross_page_table()
    print(f"Wrote {f2} ({f2.stat().st_size} bytes)")
    f3 = _build_broken_order()
    print(f"Wrote {f3} ({f3.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
