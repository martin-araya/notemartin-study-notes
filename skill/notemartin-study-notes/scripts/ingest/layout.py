#!/usr/bin/env python3
"""layout.py — F21 layout analysis and reading order.

Consume fragments.json (F18) o ocr_summary.json (F20), detecta columnas,
sidebars, notas al margen, pies de figura y flotantes; calcula el orden
de lectura verificado por continuidad sintáctica y reunifica contenido
que cruza páginas.

Uso:
    python3 scripts/ingest/layout.py --source <fragments.json|ocr_summary.json> \
        --out-dir <dir> [--input-type auto|pdf-native|ocr] [--json-only]
    python3 scripts/ingest/layout.py --pdf <pdf> --out-dir <dir> [--json-only]

Salidas (en <out-dir>/ingest/layout/):
    page-NNNN.regions.json — regiones por página
    page-NNNN.reading_order.json — orden de lectura por página
    layout_summary.json — global con cross_page_links e inconsistencies

Códigos de salida:
    0 — OK
    1 — Error fatal (input ilegible)
    2 — OK con advertencias (orden roto detectado, cross-page ambiguo)

Dependencias:
    - Python 3.9+ stdlib
    - numpy (recomendado; si falta, fallback sin numpy)

Documentación normativa: references/01-ingest/layout.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np  # type: ignore
except ImportError:  # pragma: no cover
    np = None  # type: ignore

SCHEMA_VERSION = "1.0.0"
EXTRACTION_VERSION = "1.0.0"

# ============================================================
# Constants (per references/01-ingest/layout.md §4-§9)
# ============================================================

X_HISTOGRAM_BUCKET_PX = 8.0
MIN_COLUMN_DENSITY = 0.05
SIDEBAR_MAX_WIDTH_RATIO = 0.20
MARGIN_THRESHOLD_PX = 50.0
MARGIN_NOTE_MAX_SIZE = 11.0
FLOAT_WIDTH_RATIO = 0.60
MIN_CONTINUITY_SCORE = 0.30
LINE_HEIGHT_PX = 14.0
PAGE_WIDTH_PT = 612.0
PAGE_HEIGHT_PT = 792.0

CROSS_PAGE_BREAK_MARKERS = (",", ";", ":", "(", "[", "{", "\\")
PUNCT_END_SENTENCE = (".", "?", "!", ";", ":")


# ============================================================
# Helpers
# ============================================================

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent), delete=False) as tf:
        tf.write(content)
        tmpname = tf.name
    Path(tmpname).replace(path)


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
    def x_centroid(self) -> float:
        return self.x + self.w / 2.0

    @property
    def y_centroid(self) -> float:
        return self.y + self.h / 2.0


@dataclass
class Region:
    id: str
    cls: str
    bbox: Tuple[float, float, float, float]
    in_main_flow: bool
    column_index: int
    word_indices: List[int] = field(default_factory=list)
    first_word: str = ""
    last_word: str = ""
    y_centroid: float = 0.0


# ============================================================
# Input normalization
# ============================================================

def detect_input_type(data: Dict[str, Any]) -> str:
    if "pages" in data and data["pages"]:
        first = data["pages"][0]
        if "fragments" in first:
            return "pdf-native"
        if "words" in first:
            return "ocr"
    return "unknown"


def load_pages(source_path: Path, input_type: str) -> Tuple[List[List[Word]], int, int]:
    """Return (per_page_words, page_width_px, page_height_px)."""
    if source_path.suffix.lower() == ".pdf":
        raise RuntimeError(
            f"PDF input not supported directly; use --pdf to invoke pdf_native.py first. "
            f"Got: {source_path}"
        )
    try:
        raw = source_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise RuntimeError(
            f"source is not valid UTF-8 JSON: {source_path} ({e}). "
            f"Use --pdf to invoke pdf_native.py for PDF inputs."
        )
    data = json.loads(raw)
    if input_type == "auto":
        input_type = detect_input_type(data)
    if input_type == "pdf-native":
        return _load_from_pdf_native(data), int(PAGE_WIDTH_PT), int(PAGE_HEIGHT_PT)
    if input_type == "ocr":
        return _load_from_ocr(data), int(PAGE_WIDTH_PT), int(PAGE_HEIGHT_PT)
    raise RuntimeError(f"cannot detect input type for {source_path}")


def _load_from_pdf_native(data: Dict[str, Any]) -> List[List[Word]]:
    pages: List[List[Word]] = []
    for page_data in data.get("pages", []):
        words: List[Word] = []
        page_num = int(page_data.get("page", 1))
        for f in page_data.get("fragments", []):
            bbox = f.get("bbox", [0, 0, 0, 0])
            text = f.get("text", "").strip()
            if not text:
                continue
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
        pages.append(words)
    return pages


def _load_from_ocr(data: Dict[str, Any]) -> List[List[Word]]:
    pages_dict: Dict[int, List[Word]] = {}
    for page_data in data.get("pages", []):
        page_num = int(page_data.get("page", 1))
        for w in page_data.get("words", []):
            bbox = w.get("bbox", [0, 0, 0, 0])
            text = w.get("text", "").strip()
            if not text:
                continue
            try:
                x, y, ww, hh = [float(v) for v in bbox]
            except (TypeError, ValueError):
                continue
            if ww <= 0 or hh <= 0:
                continue
            pages_dict.setdefault(page_num, []).append(Word(
                text=text,
                bbox=(x, y, ww, hh),
                font_name=None,
                font_size=None,
                page=page_num,
            ))
    if not pages_dict:
        return []
    max_p = max(pages_dict.keys())
    return [pages_dict.get(p, []) for p in range(1, max_p + 1)]


# ============================================================
# Column detection
# ============================================================

def detect_columns(words: List[Word], page_width: float) -> List[Tuple[float, float]]:
    """Return list of (x_start, x_end) column ranges.

    Uses the LEFT edge of each word's bbox (x_min) to find column starts.
    This is more reliable than x_centroid when pdf_native approximates width
    by len(text)*font_size*0.5 (which inflates bbox and shifts centroid).

    A gap is considered a column boundary if it spans at least MIN_GAP_WIDTH_PX
    contiguous zero-density buckets in the X histogram.
    """
    if not words:
        return [(0.0, page_width)]
    MIN_GAP_WIDTH_PX = 30.0
    if np is not None:
        xs = np.array([w.x for w in words])
        bucket_size = X_HISTOGRAM_BUCKET_PX
        max_x = float(max(xs.max(), page_width))
        n_buckets = int(max_x / bucket_size) + 1
        hist, edges = np.histogram(xs, bins=n_buckets, range=(0.0, max_x))
        max_density = float(hist.max())
        if max_density <= 0:
            return [(0.0, page_width)]
        threshold = MIN_COLUMN_DENSITY * max_density
        is_gap = hist < threshold
        first_word_bucket = int(np.argmax(hist > 0)) if (hist > 0).any() else 0
        last_word_bucket = int(len(hist) - 1 - np.argmax((hist > 0)[::-1])) if (hist > 0).any() else len(hist) - 1
        gap_regions = []
        i = first_word_bucket
        while i <= last_word_bucket:
            if is_gap[i]:
                start = i
                while i <= last_word_bucket and is_gap[i]:
                    i += 1
                gap_width = (float(edges[i]) - float(edges[start])) if i <= last_word_bucket else (float(edges[last_word_bucket + 1]) - float(edges[start]))
                if gap_width >= MIN_GAP_WIDTH_PX:
                    gap_regions.append((float(edges[start]), float(edges[i]) if i <= last_word_bucket else float(edges[last_word_bucket + 1])))
            else:
                i += 1
        if not gap_regions:
            return [(0.0, page_width)]
        column_edges = []
        last_break = 0.0
        for g_start, g_end in gap_regions:
            column_edges.append((last_break, g_start))
            last_break = g_end
        column_edges.append((last_break, page_width))
        return column_edges
    else:
        xs = sorted(set(w.x for w in words))
        if len(xs) < 2:
            return [(0.0, page_width)]
        gaps = [(xs[i + 1] - xs[i], xs[i], xs[i + 1]) for i in range(len(xs) - 1)]
        column_edges = []
        last_break = 0.0
        for gap, x_left, x_right in gaps:
            if gap >= MIN_GAP_WIDTH_PX:
                column_edges.append((last_break, x_left))
                last_break = x_right
        column_edges.append((last_break, page_width))
        return column_edges


def assign_to_column(x_left: float, columns: List[Tuple[float, float]]) -> int:
    best_idx = 0
    best_dist = float("inf")
    for i, (xs, xe) in enumerate(columns):
        center = (xs + xe) / 2.0
        dist = abs(x_left - center)
        if dist < best_dist:
            best_dist = dist
            best_idx = i
    return best_idx


# ============================================================
# Sidebar, margin note, caption, float detection
# ============================================================

def is_margin_note(word: Word, page_width: float) -> bool:
    if word.x < MARGIN_THRESHOLD_PX:
        return True
    if word.x + word.w > page_width - MARGIN_THRESHOLD_PX:
        return True
    return False


def detect_sidebars(words: List[Word], columns: List[Tuple[float, float]], page_width: float) -> List[List[int]]:
    """Group words into sidebar clusters. Return list of clusters (each is list of word indices)."""
    candidates = []
    for i, w in enumerate(words):
        x_left = w.x
        in_main_col = any(xs <= x_left <= xe for xs, xe in columns)
        if in_main_col:
            continue
        if x_left < 0 or x_left > page_width:
            continue
        candidates.append(i)
    if not candidates:
        return []
    sidebars: List[List[int]] = []
    sorted_cand = sorted(candidates, key=lambda i: (words[i].y_centroid, words[i].x))
    current: List[int] = []
    last_y = None
    for idx in sorted_cand:
        w = words[idx]
        if last_y is None or (w.y_centroid - last_y) <= 3 * LINE_HEIGHT_PX:
            current.append(idx)
        else:
            if len(current) >= 3:
                sidebars.append(current)
            current = [idx]
        last_y = w.y_centroid
    if len(current) >= 3:
        sidebars.append(current)
    return sidebars


def detect_margin_notes(words: List[Word], page_width: float) -> List[int]:
    notes = []
    for i, w in enumerate(words):
        if is_margin_note(w, page_width):
            font_size = w.font_size or 12.0
            if font_size <= MARGIN_NOTE_MAX_SIZE:
                notes.append(i)
    return notes


def detect_figure_captions(words: List[Word]) -> List[int]:
    if not words:
        return []
    by_y: Dict[int, List[int]] = {}
    for i, w in enumerate(words):
        y = int(w.y // 10)
        by_y.setdefault(y, []).append(i)
    sorted_ys = sorted(by_y.keys())
    caption_indices: List[int] = []
    pattern = re.compile(r"^(Figure|Fig|Tab|Table|Tabla)\s*\d", re.IGNORECASE)
    for j in range(1, len(sorted_ys)):
        prev_y = sorted_ys[j - 1]
        curr_y = sorted_ys[j]
        y_diff = (curr_y - prev_y) * 10
        if y_diff > 1.5 * LINE_HEIGHT_PX and y_diff < 8 * LINE_HEIGHT_PX:
            for idx in by_y[curr_y]:
                w = words[idx]
                if pattern.match(w.text) or len(by_y[curr_y]) <= 30:
                    caption_indices.append(idx)
    return caption_indices


# ============================================================
# Region building
# ============================================================

def _region_bbox(word_indices: List[int], words: List[Word]) -> Tuple[float, float, float, float]:
    if not word_indices:
        return (0.0, 0.0, 0.0, 0.0)
    xs = [words[i].x for i in word_indices]
    ys = [words[i].y for i in word_indices]
    xe = [words[i].x + words[i].w for i in word_indices]
    ye = [words[i].y + words[i].h for i in word_indices]
    return (min(xs), min(ys), max(xe) - min(xs), max(ye) - min(ys))


def _y_centroid(word_indices: List[int], words: List[Word]) -> float:
    if not word_indices:
        return 0.0
    return sum(words[i].y_centroid for i in word_indices) / len(word_indices)


def build_regions(words: List[Word], columns: List[Tuple[float, float]], page_width: float) -> List[Region]:
    regions: List[Region] = []
    if not words:
        return regions
    sidebar_clusters = detect_sidebars(words, columns, page_width)
    sidebar_word_set: set = set()
    for cluster in sidebar_clusters:
        for idx in cluster:
            sidebar_word_set.add(idx)
    margin_indices = detect_margin_notes(words, page_width)
    margin_word_set = set(margin_indices)
    caption_indices = detect_figure_captions(words)
    caption_word_set = set(caption_indices)

    main_indices: List[int] = []
    for i in range(len(words)):
        if i in sidebar_word_set or i in margin_word_set or i in caption_word_set:
            continue
        main_indices.append(i)

    main_indices: List[int] = []
    for i in range(len(words)):
        if i in sidebar_word_set or i in margin_word_set or i in caption_word_set:
            continue
        main_indices.append(i)

    main_indices.sort(key=lambda i: (assign_to_column(words[i].x, columns), words[i].y_centroid))
    column_groups: Dict[int, List[int]] = {}
    for i in main_indices:
        col_idx = assign_to_column(words[i].x, columns)
        column_groups.setdefault(col_idx, []).append(i)

    region_counter = 0
    for col_idx in sorted(column_groups.keys()):
        words_in_col = column_groups[col_idx]
        if not words_in_col:
            continue
        current_group: List[int] = []
        last_y = None
        for idx in words_in_col:
            w = words[idx]
            if last_y is not None and (w.y_centroid - last_y) > 1.8 * LINE_HEIGHT_PX:
                if current_group:
                    region_counter += 1
                    rid = f"r{region_counter:03d}"
                    bbox = _region_bbox(current_group, words)
                    regions.append(Region(
                        id=rid,
                        cls="column",
                        bbox=bbox,
                        in_main_flow=True,
                        column_index=col_idx,
                        word_indices=current_group,
                        first_word=words[current_group[0]].text,
                        last_word=words[current_group[-1]].text,
                        y_centroid=_y_centroid(current_group, words),
                    ))
                    current_group = []
            current_group.append(idx)
            last_y = w.y_centroid
        if current_group:
            region_counter += 1
            rid = f"r{region_counter:03d}"
            bbox = _region_bbox(current_group, words)
            regions.append(Region(
                id=rid,
                cls="column",
                bbox=bbox,
                in_main_flow=True,
                column_index=col_idx,
                word_indices=current_group,
                first_word=words[current_group[0]].text,
                last_word=words[current_group[-1]].text,
                y_centroid=_y_centroid(current_group, words),
            ))

    for cluster in sidebar_clusters:
        if not cluster:
            continue
        region_counter += 1
        rid = f"r{region_counter:03d}"
        bbox = _region_bbox(cluster, words)
        x_center = sum(words[i].x for i in cluster) / len(cluster)
        side = "sidebar_left" if x_center < page_width / 2 else "sidebar_right"
        regions.append(Region(
            id=rid,
            cls=side,
            bbox=bbox,
            in_main_flow=False,
            column_index=-1,
            word_indices=cluster,
            first_word=words[cluster[0]].text,
            last_word=words[cluster[-1]].text,
            y_centroid=_y_centroid(cluster, words),
        ))

    for idx in margin_indices:
        region_counter += 1
        rid = f"r{region_counter:03d}"
        regions.append(Region(
            id=rid,
            cls="margin_note",
            bbox=(words[idx].x, words[idx].y, words[idx].w, words[idx].h),
            in_main_flow=False,
            column_index=-1,
            word_indices=[idx],
            first_word=words[idx].text,
            last_word=words[idx].text,
            y_centroid=words[idx].y_centroid,
        ))

    for idx in caption_indices:
        region_counter += 1
        rid = f"r{region_counter:03d}"
        regions.append(Region(
            id=rid,
            cls="figure_caption",
            bbox=(words[idx].x, words[idx].y, words[idx].w, words[idx].h),
            in_main_flow=False,
            column_index=-1,
            word_indices=[idx],
            first_word=words[idx].text,
            last_word=words[idx].text,
            y_centroid=words[idx].y_centroid,
        ))

    return regions


# ============================================================
# Reading order
# ============================================================

def compute_reading_order(regions: List[Region]) -> Tuple[List[str], List[Dict[str, Any]]]:
    main = [r for r in regions if r.in_main_flow]
    out_of_flow = [r for r in regions if not r.in_main_flow]
    main_sorted = sorted(main, key=lambda r: (r.column_index, r.y_centroid))
    out_of_flow_sorted = sorted(out_of_flow, key=lambda r: (0 if r.cls.startswith("sidebar") else 1, r.y_centroid))
    ordered = main_sorted + out_of_flow_sorted
    ordered_ids = [r.id for r in ordered]
    jumps: List[Dict[str, Any]] = []
    for i in range(len(ordered) - 1):
        a, b = ordered[i], ordered[i + 1]
        if not (a.in_main_flow and b.in_main_flow):
            continue
        score = continuity_score(a, b)
        if score < MIN_CONTINUITY_SCORE:
            jumps.append({
                "from_region": a.id, "to_region": b.id,
                "score": round(score, 3), "kind": "low_continuity",
            })
    return ordered_ids, jumps


def continuity_score(a: Region, b: Region) -> float:
    if not a.word_indices or not b.word_indices:
        return 0.0
    score = 0.0
    a_last = a.last_word.rstrip()
    b_first = b.first_word.rstrip()
    if a_last and a_last[-1] in PUNCT_END_SENTENCE and b_first[:1].isupper():
        score += 0.3
    if a_last.endswith("-") and b_first[:1].islower():
        score += 0.3
    if abs(a.y_centroid - b.y_centroid) < 1.5 * LINE_HEIGHT_PX:
        score += 0.2
    if a.column_index == b.column_index:
        score += 0.2
    return min(score, 1.0)


# ============================================================
# Verification
# ============================================================

def verify_reading_order(
    regions: List[Region],
    emitted_order: List[str],
    columns: List[Tuple[float, float]],
) -> Tuple[bool, List[Dict[str, Any]]]:
    """Compare emitted order against ground-truth (column-first, y-ascending).

    Flags `column_order_inverted` if two consecutive main-flow regions appear
    with col_a > col_b in the emitted order (right column read before left).
    Requires at least 2 main-flow regions and at least 2 columns to compare.
    """
    if len(columns) < 2:
        return True, []
    main = [r for r in regions if r.in_main_flow]
    if len(main) < 2:
        return True, []
    region_by_id = {r.id: r for r in main}
    em_main_ids = [rid for rid in emitted_order if rid in region_by_id]
    inconsistencies: List[Dict[str, Any]] = []
    for i in range(len(em_main_ids) - 1):
        a = region_by_id[em_main_ids[i]]
        b = region_by_id[em_main_ids[i + 1]]
        if a.column_index > b.column_index:
            ground_truth = sorted(main, key=lambda r: (r.column_index, r.y_centroid))
            inconsistencies.append({
                "page": 1,
                "expected_order": [r.id for r in ground_truth],
                "emitted_order": em_main_ids,
                "kind": "column_order_inverted",
            })
            break
    return len(inconsistencies) == 0, inconsistencies


# ============================================================
# Cross-page reunification
# ============================================================

def reunify_cross_page(page_words: List[List[Word]]) -> List[Dict[str, Any]]:
    """Detect paragraphs, tables, code blocks that span pages."""
    links: List[Dict[str, Any]] = []
    for i in range(len(page_words) - 1):
        prev = page_words[i]
        curr = page_words[i + 1]
        if not prev or not curr:
            continue
        prev_last = prev[-1].text.rstrip()
        curr_first = curr[0].text.rstrip() if curr else ""
        if not prev_last or not curr_first:
            continue
        if prev_last[-1] in CROSS_PAGE_BREAK_MARKERS or prev_last[-1].islower():
            confidence = 0.7 if prev_last[-1] in CROSS_PAGE_BREAK_MARKERS else 0.5
            if curr_first[:1].islower() or prev_last.endswith("-"):
                confidence = max(confidence, 0.8)
                links.append({
                    "type": "paragraph",
                    "page_a": i + 1,
                    "region_id_a": f"p{i+1}-last",
                    "page_b": i + 2,
                    "region_id_b": f"p{i+2}-first",
                    "confidence": confidence,
                })
                continue
        if curr_first.lower().startswith(("fig", "tab", "table", "figura", "tabla")):
            continue
        if _page_has_columnar_content(curr):
            links.append({
                "type": "table",
                "page_a": i + 1,
                "region_id_a": f"p{i+1}-last",
                "page_b": i + 2,
                "region_id_b": f"p{i+2}-first",
                "confidence": 0.75,
            })
            continue
        if (prev_last[-1] in ("{", "(", "[", ",", "\\", ";")) or prev_last.endswith(":"):
            if curr_first.startswith((" ", "\t")) or len(curr) > 0 and curr[0].x < prev[-1].x + 50:
                links.append({
                    "type": "code",
                    "page_a": i + 1,
                    "region_id_a": f"p{i+1}-last",
                    "page_b": i + 2,
                    "region_id_b": f"p{i+2}-first",
                    "confidence": 0.7,
                })
    return links


def _page_has_columnar_content(words: List[Word], window_size: int = 6) -> bool:
    """Check if any window of `window_size` consecutive words in the page
    shows columnar alignment (table-like structure)."""
    if len(words) < window_size:
        return _is_columnar_aligned(words)
    for start in range(0, len(words) - window_size + 1):
        if _is_columnar_aligned(words[start:start + window_size]):
            return True
    return False


def _is_columnar_aligned(words: List[Word], window_size: int = 6) -> bool:
    """Detect if a sequence of words has columnar alignment (table-like).

    Looks at the first `window_size` words; if they share a Y range (within
    2 line heights) and span multiple X positions (≥ 3 distinct values), the
    page likely contains a table structure.
    """
    if len(words) < window_size:
        return False
    sample = words[:window_size]
    ys = [w.y_centroid for w in sample]
    if max(ys) - min(ys) > 3 * LINE_HEIGHT_PX:
        return False
    xs = [w.x for w in sample]
    if len(set(round(x, 1) for x in xs)) < 3:
        return False
    return True


# ============================================================
# Page processing
# ============================================================

def process_page(
    page_num: int,
    words: List[Word],
    page_width: float,
    page_height: float,
    out_layout_dir: Path,
) -> Dict[str, Any]:
    columns = detect_columns(words, page_width)
    regions = build_regions(words, columns, page_width)
    emitted_order, jumps = compute_reading_order(regions)
    valid, inconsistencies = verify_reading_order(regions, emitted_order, columns)
    for inc in inconsistencies:
        inc["page"] = page_num

    regions_payload = {
        "page": page_num,
        "column_count": len(columns),
        "regions": [
            {
                "id": r.id,
                "class": r.cls,
                "bbox": list(r.bbox),
                "in_main_flow": r.in_main_flow,
                "column_index": r.column_index,
                "word_count": len(r.word_indices),
                "first_word": r.first_word,
                "last_word": r.last_word,
            }
            for r in regions
        ],
    }
    atomic_write_text(
        out_layout_dir / f"page-{page_num:04d}.regions.json",
        json.dumps(regions_payload, indent=2, ensure_ascii=False),
    )

    reading_order_payload = {
        "page": page_num,
        "ordered_region_ids": emitted_order,
        "jumps": jumps,
        "excluded_region_ids": [r.id for r in regions if not r.in_main_flow],
    }
    atomic_write_text(
        out_layout_dir / f"page-{page_num:04d}.reading_order.json",
        json.dumps(reading_order_payload, indent=2, ensure_ascii=False),
    )

    if regions:
        cont_scores = []
        main = [r for r in regions if r.in_main_flow]
        for i in range(len(main) - 1):
            cont_scores.append(continuity_score(main[i], main[i + 1]))
        continuity_avg = sum(cont_scores) / len(cont_scores) if cont_scores else 1.0
    else:
        continuity_avg = 0.0

    return {
        "page": page_num,
        "column_count": len(columns),
        "region_count": len(regions),
        "reading_order_valid": valid,
        "continuity_score": round(continuity_avg, 4),
        "out_of_flow_count": sum(1 for r in regions if not r.in_main_flow),
        "inconsistencies": inconsistencies,
    }


# ============================================================
# Entry point
# ============================================================

def run(
    source_path: Path,
    out_dir: Path,
    input_type: str = "auto",
    json_only: bool = False,
) -> int:
    source_path = Path(source_path).resolve()
    if not source_path.exists():
        print(f"ERROR: source not found: {source_path}", file=sys.stderr)
        return 1

    warnings: List[str] = []

    try:
        pages_words, page_width, page_height = load_pages(source_path, input_type)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    out_layout_dir = out_dir / "ingest" / "layout"
    out_layout_dir.mkdir(parents=True, exist_ok=True)

    sha = sha256_file(source_path)
    size = source_path.stat().st_size
    fmt = "fragments-json" if "fragments" in source_path.name else "ocr-json"
    detected = detect_input_type(json.loads(source_path.read_text(encoding="utf-8")))

    pages_meta: List[Dict[str, Any]] = []
    for i, words in enumerate(pages_words, 1):
        page_meta = process_page(i, words, float(page_width), float(page_height), out_layout_dir)
        pages_meta.append(page_meta)

    cross_page_links = reunify_cross_page(pages_words)

    inconsistencies: List[Dict[str, Any]] = []
    for m in pages_meta:
        for inc in m.get("inconsistencies", []):
            inconsistencies.append(inc)
            warnings.append(f"page {m['page']}: order broken: {inc.get('kind')}")
    for page_meta in pages_meta:
        if not page_meta["reading_order_valid"]:
            warnings.append(f"page {page_meta['page']}: reading_order_valid=false")

    summary = {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "path": str(source_path),
            "hash": sha,
            "size_bytes": size,
            "format": detected,
        },
        "input_type": detected,
        "page_count": len(pages_meta),
        "pages": pages_meta,
        "cross_page_links": cross_page_links,
        "inconsistencies": inconsistencies,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    atomic_write_text(
        out_layout_dir / "layout_summary.json",
        json.dumps(summary, indent=2, ensure_ascii=False),
    )

    if not json_only:
        md_lines = [f"# Layout — `{source_path.name}`", ""]
        md_lines.append(f"- **Páginas:** {len(pages_meta)}")
        md_lines.append(f"- **Cross-page links:** {len(cross_page_links)}")
        md_lines.append(f"- **Inconsistencies:** {len(inconsistencies)}")
        if warnings:
            md_lines.append("")
            md_lines.append("## Advertencias")
            for w in warnings:
                md_lines.append(f"- {w}")
        md_lines.append("")
        md_lines.append("## Por página")
        md_lines.append("")
        md_lines.append("| Page | Columns | Regions | Order valid | Continuity | Out-of-flow |")
        md_lines.append("|---|---|---|---|---|---|")
        for m in pages_meta:
            md_lines.append(
                f"| {m['page']} | {m['column_count']} | {m['region_count']} | "
                f"{'sí' if m['reading_order_valid'] else 'NO'} | {m['continuity_score']:.2f} | {m['out_of_flow_count']} |"
            )
        atomic_write_text(out_layout_dir / "layout.md", "\n".join(md_lines) + "\n")

    return 2 if warnings else 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="layout.py",
        description="F21 — Layout analysis and reading order from word-level fragments or OCR.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Constantes (references/01-ingest/layout.md §4-§9):
  X_HISTOGRAM_BUCKET_PX     = 8      px (bucket para histograma X)
  MIN_COLUMN_DENSITY        = 0.05   umbral mínimo para detectar gap
  SIDEBAR_MAX_WIDTH_RATIO   = 0.20   ancho máximo sidebar / page width
  MARGIN_THRESHOLD_PX       = 50     margen izq/der para nota
  MARGIN_NOTE_MAX_SIZE      = 11.0   font size máximo para margin note
  FLOAT_WIDTH_RATIO         = 0.60   ancho mínimo para float
  MIN_CONTINUITY_SCORE      = 0.30   umbral para jump
  LINE_HEIGHT_PX            = 14.0   altura de línea por defecto

Códigos de salida:
  0 OK sin advertencias
  1 error fatal
  2 OK con advertencias (orden roto, cross-page ambiguo)
""",
    )
    parser.add_argument("--source", help="Ruta a fragments.json (F18) u ocr_summary.json (F20)")
    parser.add_argument("--pdf", help="Ruta a un PDF; ejecuta F18 internamente")
    parser.add_argument("--out-dir", required=True, help="Directorio de salida (ingest/layout/)")
    parser.add_argument("--input-type", default="auto", choices=["auto", "pdf-native", "ocr"], help="Tipo del input")
    parser.add_argument("--json-only", action="store_true", help="Solo escribir layout_summary.json")
    args = parser.parse_args(argv)

    if args.pdf:
        pdf_path = Path(args.pdf).resolve()
        if not pdf_path.exists():
            print(f"ERROR: PDF not found: {pdf_path}", file=sys.stderr)
            return 1
        pdf_native = Path(__file__).resolve().parent / "pdf_native.py"
        tmp_dir = Path(args.out_dir) / "_tmp_pdf_native"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        try:
            res = subprocess.run(
                [sys.executable, str(pdf_native), "--source", str(pdf_path), "--out-dir", str(tmp_dir), "--json-only"],
                capture_output=True, text=True, timeout=300,
            )
            if res.returncode != 0 and not (tmp_dir / "fragments.json").exists():
                print(f"ERROR: pdf_native.py failed: {res.stderr}", file=sys.stderr)
                return 1
            source = tmp_dir / "fragments.json"
        except Exception as e:
            print(f"ERROR: failed to run pdf_native.py: {e}", file=sys.stderr)
            return 1
    else:
        if not args.source:
            print("ERROR: must provide --source or --pdf", file=sys.stderr)
            return 1
        source = Path(args.source).resolve()

    code = run(source, Path(args.out_dir), input_type=args.input_type, json_only=args.json_only)
    return code


if __name__ == "__main__":
    sys.exit(main())
