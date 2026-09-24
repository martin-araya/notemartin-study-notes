#!/usr/bin/env python3
"""tables.py — F23 table extractor.

Detecta y extrae tablas a partir de las regiones marcadas como `table` por F22
(o, en fallback, desde fragments/words de F18/F20). Clusterización geométrica
por filas y columnas, detección de celdas combinadas (rowspan/colspan),
encabezados multinivel y reunión cross-page. Verificación dura de integridad.

Uso:
    python3 scripts/ingest/tables.py \
        --source <regions_dir> --out-dir <dir> \
        [--fragments <fragments.json>] [--ocr <ocr_summary.json>] \
        [--json-only]

Salidas (en <out-dir>/ingest/tables/):
    page-NNNN.tables.json — tablas por página
    tables_summary.json — global con cross-page merged

Códigos de salida:
    0 — OK
    1 — Error fatal
    2 — OK con advertencias (low_confidence, cross-page reunión ambigua)

Dependencias:
    - Python 3.9+ stdlib

Documentación normativa: references/01-ingest/tables.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"

# ============================================================
# Constants (per references/01-ingest/tables.md §4-§8)
# ============================================================

ROW_BAND_TOL_PX = 4.0
COL_BAND_TOL_PX = 6.0
HEADER_MAX_ROWS = 3
HEADER_FONT_SIZE_FACTOR = 1.10
CROSS_PAGE_HEADER_MATCH_THRESHOLD = 0.80
CROSS_PAGE_HEADER_LOW_THRESHOLD = 0.60
MERGED_CELL_FACTOR = 4.0
LOW_CONFIDENCE_MIN_ROWS = 3
WORD_BBOX_INTERSECT_TOL_PX = 5.0


# ============================================================
# Data structures
# ============================================================

@dataclass
class Word:
    text: str
    bbox: Tuple[float, float, float, float]  # x, y, w, h
    font_name: Optional[str] = None
    font_size: Optional[float] = None
    page: int = 1

    @property
    def x(self) -> float:
        return self.bbox[0]

    @property
    def y(self) -> float:
        return self.bbox[1]

    @property
    def w(self) -> float:
        return self.bbox[2]

    @property
    def h(self) -> float:
        return self.bbox[3]

    @property
    def x_center(self) -> float:
        return self.x + self.w / 2.0

    @property
    def y_center(self) -> float:
        return self.y + self.h / 2.0


@dataclass
class TableRecord:
    id: str
    region_id: Optional[str]
    page_start: int
    page_end: int
    rows: int
    cols: int
    headers: List[List[str]] = field(default_factory=list)
    data: List[List[str]] = field(default_factory=list)
    merged_cells: List[Dict[str, Any]] = field(default_factory=list)
    cross_page_continued: bool = False
    confidence: float = 0.0
    low_confidence: bool = False
    warnings: List[str] = field(default_factory=list)
    dwell_ms: int = 0


# ============================================================
# Helpers
# ============================================================

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def sha256_paths(paths: List[Path]) -> str:
    h = hashlib.sha256()
    for p in sorted(paths):
        if not p.exists():
            continue
        if p.is_file():
            h.update(sha256_file(p).encode("utf-8"))
        elif p.is_dir():
            for child in sorted(p.rglob("*")):
                if child.is_file():
                    h.update(sha256_file(child).encode("utf-8"))
    return h.hexdigest()


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent), delete=False) as tf:
        tf.write(content)
        tmpname = tf.name
    Path(tmpname).replace(path)


# ============================================================
# Word loading
# ============================================================

def _load_words_from_fragments(fragments_path: Path) -> Dict[int, List[Word]]:
    if not fragments_path.exists():
        return {}
    try:
        data = json.loads(fragments_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    pages: Dict[int, List[Word]] = {}
    for page_data in data.get("pages", []):
        page_num = int(page_data.get("page", 1))
        words: List[Word] = []
        for f in page_data.get("fragments", []):
            text = f.get("text", "").strip()
            if not text:
                continue
            bbox = f.get("bbox", [0, 0, 0, 0])
            try:
                x0, y0, x1, y1 = [float(v) for v in bbox]
            except (TypeError, ValueError):
                continue
            if x1 <= x0 or y1 <= y0:
                continue
            words.append(Word(
                text=text,
                bbox=(x0, y0, x1 - x0, y1 - y0),
                font_name=f.get("font_name"),
                font_size=f.get("font_size"),
                page=page_num,
            ))
        if words:
            pages[page_num] = words
    return pages


def _load_words_from_ocr(ocr_path: Path) -> Dict[int, List[Word]]:
    if not ocr_path.exists():
        return {}
    try:
        data = json.loads(ocr_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    pages: Dict[int, List[Word]] = {}
    for page_data in data.get("pages", []):
        page_num = int(page_data.get("page", 1))
        words: List[Word] = []
        for w in page_data.get("words", []):
            text = w.get("text", "").strip()
            if not text:
                continue
            bbox = w.get("bbox", [0, 0, 0, 0])
            try:
                x, y, ww, hh = [float(v) for v in bbox]
            except (TypeError, ValueError):
                continue
            if ww <= 0 or hh <= 0:
                continue
            words.append(Word(
                text=text,
                bbox=(x, y, ww, hh),
                font_name=None,
                font_size=None,
                page=page_num,
            ))
        if words:
            pages[page_num] = words
    return pages


def load_words(fragments_path: Optional[Path], ocr_path: Optional[Path]) -> Dict[int, List[Word]]:
    words = _load_words_from_fragments(fragments_path) if fragments_path else {}
    if not words and ocr_path:
        words = _load_words_from_ocr(ocr_path)
    return words


# ============================================================
# Region loading
# ============================================================

def load_regions(source: Path) -> List[Dict[str, Any]]:
    """Load regions; each entry has page, region_id, semantic_class, bbox, word_indices."""
    if source.is_dir():
        paths = sorted(source.glob("page-*.regions.json"))
    elif source.is_file():
        paths = [source]
    else:
        return []
    pages: List[Dict[str, Any]] = []
    for p in paths:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        page_num = int(data.get("page", 1))
        for r in data.get("regions", []):
            pages.append({
                "page": page_num,
                "region_id": r.get("id"),
                "semantic_class": r.get("semantic_class"),
                "bbox": r.get("bbox", [0, 0, 0, 0]),
                "ambiguity": r.get("ambiguity", False),
                "word_indices": r.get("word_indices", []),
            })
    return pages


def autodetect_table_regions(page_words: List[Word], page: int) -> List[Dict[str, Any]]:
    """Detect candidate table regions without F22: ≥ 3 X alignments × ≥ 3 Y alignments."""
    if len(page_words) < 9:
        return []
    xs_starts = sorted(set(round(w.x, 0) for w in page_words))
    ys_starts = sorted(set(round(w.y, 0) for w in page_words))
    x_clusters: List[float] = []
    for x in xs_starts:
        if not x_clusters or abs(x - x_clusters[-1]) > COL_BAND_TOL_PX:
            x_clusters.append(x)
    y_clusters: List[float] = []
    for y in ys_starts:
        if not y_clusters or abs(y - y_clusters[-1]) > ROW_BAND_TOL_PX:
            y_clusters.append(y)
    if len(x_clusters) < 3 or len(y_clusters) < 3:
        return []
    if xs_starts[-1] - xs_starts[0] < 100:
        return []
    if ys_starts[-1] - ys_starts[0] < 50:
        return []
    x_min = min(w.x for w in page_words)
    x_max = max(w.x + w.w for w in page_words)
    y_min = min(w.y for w in page_words)
    y_max = max(w.y + w.h for w in page_words)
    region_id = f"autodetect_p{page}"
    return [{
        "page": page,
        "region_id": region_id,
        "semantic_class": "table",
        "bbox": [x_min, y_min, x_max - x_min, y_max - y_min],
        "ambiguity": False,
        "word_indices": list(range(len(page_words))),
    }]


# ============================================================
# Word-region matching
# ============================================================

def words_in_region(words: List[Word], bbox: List[float]) -> List[Word]:
    if len(words) == 0 or len(bbox) < 4:
        return []
    try:
        rx0, ry0, rw, rh = [float(v) for v in bbox]
    except (TypeError, ValueError):
        return []
    rx1, ry1 = rx0 + rw, ry0 + rh
    out: List[Word] = []
    for w in words:
        wx0, wy0 = w.x, w.y
        wx1, wy1 = w.x + w.w, w.y + w.h
        ox = min(rx1, wx1) - max(rx0, wx0)
        oy = min(ry1, wy1) - max(ry0, wy0)
        if ox >= 0 and oy >= 0:
            out.append(w)
    return out


# ============================================================
# Clustering
# ============================================================

def cluster_by_axis(values: List[Tuple[int, float]], tol: float) -> List[List[int]]:
    """Group indices by value proximity. Returns list of index groups."""
    if not values:
        return []
    sorted_pairs = sorted(values, key=lambda x: x[1])
    groups: List[List[int]] = []
    current: List[int] = [sorted_pairs[0][0]]
    current_val = sorted_pairs[0][1]
    for idx, val in sorted_pairs[1:]:
        if abs(val - current_val) <= tol:
            current.append(idx)
        else:
            groups.append(current)
            current = [idx]
            current_val = val
    groups.append(current)
    return groups


def cluster_by_y(words: List[Word]) -> List[List[Word]]:
    pairs = [(i, w.y_center) for i, w in enumerate(words)]
    groups = cluster_by_axis(pairs, ROW_BAND_TOL_PX)
    return [[words[i] for i in g] for g in groups]


def cluster_by_x(words_in_row: List[Word]) -> List[List[Word]]:
    pairs = [(i, w.x) for i, w in enumerate(words_in_row)]
    groups = cluster_by_axis(pairs, COL_BAND_TOL_PX)
    return [[words_in_row[i] for i in g] for g in groups]


# ============================================================
# Table extraction
# ============================================================

def extract_table_from_region(
    region: Dict[str, Any],
    page_words: List[Word],
    table_counter: int,
) -> Optional[TableRecord]:
    bbox = region.get("bbox", [0, 0, 0, 0])
    words = words_in_region(page_words, bbox)
    if len(words) < 4:
        return None

    row_groups = cluster_by_y(words)
    if len(row_groups) < 2:
        return None

    row_groups.sort(key=lambda r: -r[0].y_center)

    grid: List[List[List[Word]]] = []
    for row_words in row_groups:
        col_groups = cluster_by_x(row_words)
        grid.append(col_groups)

    cols = max((len(r) for r in grid), default=0)
    if cols == 0:
        return None
    rows = len(grid)

    cell_text: List[List[str]] = []
    for r in grid:
        row_cells: List[str] = []
        for col_words in r:
            text = " ".join(w.text.strip() for w in col_words).strip()
            row_cells.append(text)
        while len(row_cells) < cols:
            row_cells.append("")
        cell_text.append(row_cells)

    body_size = _page_body_size(page_words)
    header_row_count = _detect_header_rows(grid, body_size)

    headers: List[List[str]] = []
    data: List[List[str]] = []
    if header_row_count > 0:
        headers = cell_text[:header_row_count]
        data = cell_text[header_row_count:]
        for h in headers:
            while len(h) < cols:
                h.append("")
    else:
        for r_idx in range(min(HEADER_MAX_ROWS, rows)):
            row = cell_text[r_idx]
            if all(not cell.strip() for cell in row):
                continue
        data = cell_text

    merged_cells = detect_merged_cells(grid, page_words)

    warnings: List[str] = []
    if len(data) < LOW_CONFIDENCE_MIN_ROWS and header_row_count == 0:
        warnings.append("low_confidence: < 3 rows and no header detected")

    cell_lengths = [len(r) for r in data]
    if len(set(cell_lengths)) > 1:
        warnings.append(f"inconsistent row lengths: {cell_lengths}")

    confidence = 0.92 if not warnings else 0.60
    low_confidence = bool(warnings)

    return TableRecord(
        id=f"t{table_counter:03d}",
        region_id=region.get("region_id"),
        page_start=region.get("page", 1),
        page_end=region.get("page", 1),
        rows=rows - header_row_count,
        cols=cols,
        headers=headers,
        data=data,
        merged_cells=merged_cells,
        confidence=confidence,
        low_confidence=low_confidence,
        warnings=warnings,
    )


def _page_body_size(words: List[Word]) -> float:
    if not words:
        return 12.0
    from collections import Counter
    sizes = [w.font_size for w in words if w.font_size and w.font_size > 0]
    if not sizes:
        return 12.0
    return float(Counter(sizes).most_common(1)[0][0])


def _detect_header_rows(grid: List[List[List[Word]]], body_size: float) -> int:
    """Detect how many top rows are headers based on font size / bold."""
    if not grid:
        return 0
    header_count = 0
    for r_idx, row in enumerate(grid):
        if r_idx >= HEADER_MAX_ROWS:
            break
        is_header = False
        for col_words in row:
            for w in col_words:
                fn = w.font_name or ""
                fs = w.font_size or 0
                if any(tok in fn for tok in ("Bold", "Black", "Heavy", "Demi")):
                    is_header = True
                    break
                if fs > 0 and fs >= HEADER_FONT_SIZE_FACTOR * body_size:
                    is_header = True
                    break
            if is_header:
                break
        if is_header:
            header_count += 1
        else:
            break
    return header_count


# ============================================================
# Merged cell detection
# ============================================================

def detect_merged_cells(grid: List[List[List[Word]]], page_words: List[Word]) -> List[Dict[str, Any]]:
    if not grid:
        return []
    rows = len(grid)
    cols = max((len(r) for r in grid), default=0)
    if cols == 0:
        return []

    row_heights: List[float] = []
    for r_idx, row in enumerate(grid):
        heights = []
        for col_words in row:
            for w in col_words:
                heights.append(w.h)
        row_heights.append(sum(heights) / len(heights) if heights else 0)
    avg_row_h = sum(row_heights) / len(row_heights) if row_heights else 1

    col_widths: List[float] = [0.0] * cols
    for r_idx, row in enumerate(grid):
        for c_idx, col_words in enumerate(row):
            if c_idx >= cols:
                continue
            widths = [w.w for w in col_words]
            if widths:
                col_widths[c_idx] = max(col_widths[c_idx], sum(widths) / len(widths))
    non_zero_col_widths = [w for w in col_widths if w > 0]
    median_col_w = sorted(non_zero_col_widths)[len(non_zero_col_widths) // 2] if non_zero_col_widths else 1.0
    avg_col_w = sum(non_zero_col_widths) / len(non_zero_col_widths) if non_zero_col_widths else 1.0
    effective_col_w = min(median_col_w, avg_col_w * 1.2)

    merged: List[Dict[str, Any]] = []
    for r_idx, row in enumerate(grid):
        for c_idx, col_words in enumerate(row):
            if not col_words:
                continue
            min_x = min(w.x for w in col_words)
            max_x = max(w.x + w.w for w in col_words)
            min_y = min(w.y for w in col_words)
            max_y = max(w.y + w.h for w in col_words)
            width = max_x - min_x
            height = max_y - min_y
            text = " ".join(w.text.strip() for w in col_words).strip()
            if not text:
                continue

            is_colspan = width > MERGED_CELL_FACTOR * effective_col_w and not _has_words_between(min_x, max_x, grid, r_idx, exclude_idx=(r_idx, c_idx))
            is_rowspan = height > MERGED_CELL_FACTOR * avg_row_h

            if is_colspan or is_rowspan:
                colspan = max(1, round(width / max(effective_col_w, 1))) if is_colspan else 1
                rowspan = max(1, round(height / max(avg_row_h, 1))) if is_rowspan else 1
                merged.append({
                    "r": r_idx,
                    "c": c_idx,
                    "rowspan": int(rowspan),
                    "colspan": int(colspan),
                    "value": text,
                })
    return merged


def _has_words_between(min_x: float, max_x: float, grid: List[List[List[Word]]], r_idx: int, exclude_idx: Optional[Tuple[int, int]] = None) -> bool:
    """Check if other words (excluding the cell at exclude_idx) exist in the same
    row within the X range. Used to confirm that a wide cell actually spans columns
    rather than being a long text in a narrow column.
    """
    if r_idx >= len(grid):
        return False
    for c_idx, col_words in enumerate(grid[r_idx]):
        if exclude_idx is not None and (r_idx, c_idx) == exclude_idx:
            continue
        for w in col_words:
            cx = w.x + w.w / 2
            if min_x < cx < max_x:
                return True
    return False


# ============================================================
# Page processing
# ============================================================

def process_page(
    page: int,
    regions: List[Dict[str, Any]],
    page_words: List[Word],
    table_counter_start: int,
) -> Tuple[List[TableRecord], int]:
    tables: List[TableRecord] = []
    counter = table_counter_start
    for region in regions:
        if region.get("semantic_class") != "table":
            continue
        if region.get("page") != page:
            continue
        table = extract_table_from_region(region, page_words, counter)
        if table is None:
            continue
        tables.append(table)
        counter += 1
    return tables, counter


# ============================================================
# Cross-page meeting
# ============================================================

def string_match_ratio(a: str, b: str) -> float:
    """Ratio of character matches at same positions / max(len)."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    sm = SequenceMatcher(None, a, b)
    matches = sum(block.size for block in sm.get_matching_blocks())
    return matches / max(len(a), len(b))


def merge_cross_page_tables(tables: List[TableRecord]) -> List[TableRecord]:
    if len(tables) < 2:
        return tables
    merged: List[TableRecord] = []
    i = 0
    while i < len(tables):
        current = tables[i]
        if i + 1 < len(tables):
            nxt = tables[i + 1]
            if current.page_end + 1 == nxt.page_start and current.cols == nxt.cols and len(nxt.headers) > 0 and len(current.data) > 0 and len(nxt.data) > 0:
                last_header_cur = " ".join(current.headers[-1]) if current.headers else " ".join(current.data[-1])
                first_header_nxt = " ".join(nxt.headers[-1]) if nxt.headers else " ".join(nxt.data[0])
                ratio = string_match_ratio(first_header_nxt, last_header_cur)
                if ratio >= CROSS_PAGE_HEADER_MATCH_THRESHOLD:
                    merged_table = TableRecord(
                        id=current.id,
                        region_id=current.region_id,
                        page_start=current.page_start,
                        page_end=nxt.page_end,
                        rows=current.rows + nxt.rows,
                        cols=current.cols,
                        headers=current.headers,
                        data=current.data + nxt.data,
                        merged_cells=current.merged_cells + nxt.merged_cells,
                        cross_page_continued=True,
                        confidence=min(current.confidence, nxt.confidence),
                        low_confidence=current.low_confidence or nxt.low_confidence,
                        warnings=current.warnings + nxt.warnings,
                        dwell_ms=current.dwell_ms + nxt.dwell_ms,
                    )
                    merged_table.warnings.append(
                        f"cross-page merged: header ratio={ratio:.3f}"
                    )
                    merged.append(merged_table)
                    i += 2
                    continue
                elif ratio >= CROSS_PAGE_HEADER_LOW_THRESHOLD:
                    current.warnings.append(
                        f"cross-page header match ambiguous (ratio={ratio:.3f}); not merged"
                    )
        merged.append(current)
        i += 1
    return merged


# ============================================================
# Entry point
# ============================================================

def run(
    source: Path,
    out_dir: Path,
    fragments_path: Optional[Path],
    ocr_path: Optional[Path],
    json_only: bool = False,
) -> int:
    source = Path(source).resolve()
    if not source.exists():
        print(f"ERROR: source not found: {source}", file=sys.stderr)
        return 1

    warnings: List[str] = []
    regions = load_regions(source) if source.exists() else []
    table_regions: List[Dict[str, Any]] = [r for r in regions if r.get("semantic_class") == "table"]
    words_by_page = load_words(fragments_path, ocr_path)
    if not words_by_page:
        warnings.append("no fragments/ocr words available")

    out_tables_dir = out_dir / "ingest" / "tables"
    out_tables_dir.mkdir(parents=True, exist_ok=True)

    pages_with_tables: Dict[int, List[Dict[str, Any]]] = {}
    all_tables: List[TableRecord] = []
    counter = 1

    if table_regions:
        regions_by_page: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for r in table_regions:
            regions_by_page[r["page"]].append(r)
        for page_num in sorted(regions_by_page.keys()):
            page_words = words_by_page.get(page_num, [])
            tables, counter = process_page(page_num, regions_by_page[page_num], page_words, counter)
            for t in tables:
                pages_with_tables.setdefault(page_num, []).append({
                    "id": t.id,
                    "region_id": t.region_id,
                    "page_start": t.page_start,
                    "page_end": t.page_end,
                    "rows": t.rows,
                    "cols": t.cols,
                    "headers": t.headers,
                    "data": t.data,
                    "merged_cells": t.merged_cells,
                    "cross_page_continued": t.cross_page_continued,
                    "confidence": t.confidence,
                    "low_confidence": t.low_confidence,
                    "warnings": t.warnings,
                    "dwell_ms": t.dwell_ms,
                })
                all_tables.append(t)
    elif words_by_page:
        for page_num, page_words in words_by_page.items():
            autodetected = autodetect_table_regions(page_words, page_num)
            if not autodetected:
                continue
            warnings.append(f"page {page_num}: F22 had no table regions; autodetected {len(autodetected)}")
            tables, counter = process_page(page_num, autodetected, page_words, counter)
            for t in tables:
                pages_with_tables.setdefault(page_num, []).append({
                    "id": t.id,
                    "region_id": t.region_id,
                    "page_start": t.page_start,
                    "page_end": t.page_end,
                    "rows": t.rows,
                    "cols": t.cols,
                    "headers": t.headers,
                    "data": t.data,
                    "merged_cells": t.merged_cells,
                    "cross_page_continued": t.cross_page_continued,
                    "confidence": t.confidence,
                    "low_confidence": t.low_confidence,
                    "warnings": t.warnings,
                    "dwell_ms": t.dwell_ms,
                })
                all_tables.append(t)

    merged_tables = merge_cross_page_tables(all_tables)

    for page_num, page_tables in pages_with_tables.items():
        atomic_write_text(
            out_tables_dir / f"page-{page_num:04d}.tables.json",
            json.dumps({"page": page_num, "tables": page_tables}, indent=2, ensure_ascii=False),
        )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "regions_dir": str(source) if regions else None,
            "fragments_path": str(fragments_path) if fragments_path else None,
            "ocr_summary_path": str(ocr_path) if ocr_path else None,
            "hash": sha256_paths([source] + ([fragments_path] if fragments_path else []) + ([ocr_path] if ocr_path else [])),
        },
        "table_count": len(merged_tables),
        "tables": [
            {
                "id": t.id,
                "page_start": t.page_start,
                "page_end": t.page_end,
                "rows": t.rows,
                "cols": t.cols,
                "cross_page_continued": t.cross_page_continued,
                "confidence": t.confidence,
                "low_confidence": t.low_confidence,
                "warnings": t.warnings,
            }
            for t in merged_tables
        ],
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    atomic_write_text(
        out_tables_dir / "tables_summary.json",
        json.dumps(summary, indent=2, ensure_ascii=False),
    )

    if not json_only:
        md_lines = [f"# Tables — `{source.name}`", ""]
        md_lines.append(f"- **Tables:** {len(merged_tables)}")
        md_lines.append(f"- **Cross-page merged:** {sum(1 for t in merged_tables if t.cross_page_continued)}")
        if warnings:
            md_lines.append("")
            md_lines.append("## Advertencias")
            for w in warnings:
                md_lines.append(f"- {w}")
        md_lines.append("")
        md_lines.append("## Resumen de tablas")
        md_lines.append("")
        md_lines.append("| ID | Pages | Rows | Cols | Cross-page | Confidence |")
        md_lines.append("|---|---|---|---|---|---|")
        for t in merged_tables:
            md_lines.append(
                f"| `{t.id}` | {t.page_start}–{t.page_end} | {t.rows} | {t.cols} | "
                f"{'sí' if t.cross_page_continued else 'no'} | {t.confidence:.2f} |"
            )
        atomic_write_text(out_tables_dir / "tables.md", "\n".join(md_lines) + "\n")

    return 2 if warnings else 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tables.py",
        description="F23 — Table extractor (rows × cols, merged cells, multi-level headers, cross-page meeting).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Constantes (references/01-ingest/tables.md §4-§8):
  ROW_BAND_TOL_PX                       = 4.0    px (cluster Y para filas)
  COL_BAND_TOL_PX                       = 6.0    px (cluster X para columnas)
  HEADER_MAX_ROWS                       = 3      máximo de filas en header multinivel
  HEADER_FONT_SIZE_FACTOR               = 1.10   factor para detectar 'large' (header)
  CROSS_PAGE_HEADER_MATCH_THRESHOLD     = 0.80   similitud mínima para merge cross-page
  CROSS_PAGE_HEADER_LOW_THRESHOLD       = 0.60   similitud mínima para warning ambiguo
  MERGED_CELL_FACTOR                    = 4.0    ratio para detectar rowspan/colspan
  LOW_CONFIDENCE_MIN_ROWS               = 3      mínimo de filas para confianza plena

Códigos de salida:
  0 OK sin advertencias
  1 error fatal
  2 OK con advertencias (low_confidence, cross-page ambiguo)
""",
    )
    parser.add_argument("--source", required=True, help="Directorio con page-NNNN.regions.json (F22)")
    parser.add_argument("--out-dir", required=True, help="Directorio de salida (ingest/tables/)")
    parser.add_argument("--fragments", default=None, help="fragments.json (F18) opcional")
    parser.add_argument("--ocr", default=None, help="ocr_summary.json (F20) opcional")
    parser.add_argument("--json-only", action="store_true", help="Solo escribir tables_summary.json (no tables.md)")
    args = parser.parse_args(argv)

    fragments_path = Path(args.fragments) if args.fragments else None
    ocr_path = Path(args.ocr) if args.ocr else None
    code = run(Path(args.source), Path(args.out_dir), fragments_path, ocr_path, json_only=args.json_only)
    return code


if __name__ == "__main__":
    sys.exit(main())
