#!/usr/bin/env python3
"""regions.py — F22 semantic region classifier.

Consume las regiones geométricas de F21 (`page-NNNN.regions.json`) y las
reclasifica en una de las 13 clases semánticas oficiales (text, heading,
table, figure, capture, diagram, code, console, formula, editorial_note,
syntax_diagram, footer, index) mediante 11 señales tipográficas / geométricas
con scoring numérico. Las regiones ambiguas se marcan con `semantic_class=null`
y `ambiguity=true`, nunca se fuerzan a una clase.

Uso:
    python3 scripts/ingest/regions.py \
        --source <regions_dir> --out-dir <dir> \
        [--fragments <fragments.json>] [--ocr <ocr_summary.json>] \
        [--class-profile <yaml>] [--json-only]

Salidas (en <out-dir>/ingest/regions/):
    page-NNNN.regions.json — copia enriquecida del output de F21
    regions_summary.json — global con class_distribution y ambiguous_count

Códigos de salida:
    0 — OK
    1 — Error fatal (input ilegible)
    2 — OK con advertencias (regiones ambiguas, falta fragments/ocr)

Dependencias:
    - Python 3.9+ stdlib

Documentación normativa: references/01-ingest/regions.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"

# ============================================================
# Constants (per references/01-ingest/regions.md §6)
# ============================================================

CLASS_MIN_THRESHOLD = 0.45
AMBIGUITY_MARGIN = 0.10

INDENT_MIN_PX = 20.0
INDENT_MAX_PX = 40.0
CENTER_TOL_PCT = 0.05
TOP_REGION_PCT = 0.10
BOTTOM_REGION_PCT = 0.10
SYMBOL_DENSITY_HIGH = 0.30
EMPTY_AREA_RATIO = 0.60
EDITORIAL_BOX_MAX_WORDS = 80
EDITORIAL_BOX_GAP_PX = 30.0
LARGE_FACTOR = 1.3

MONOSPACE_FONTS = (
    "courier", "consolas", "monaco", "menlo", "monospace",
    "liberation mono", "source code", "inconsolata",
    "fira mono", "ibm plex mono",
)

PATTERNS = [
    ("editorial_note", re.compile(r"^(Note|Tip|Warning|Caution|Important|See also|Example|NB|Remark):?", re.IGNORECASE), 1.0),
    ("caption", re.compile(r"^(Figure|Fig\.|Tab\.|Tabla|Listing|Snippet|Code)\s*\d", re.IGNORECASE), 0.7),
    ("index", re.compile(r"^(\d+\.)+\s+[A-Z]", re.IGNORECASE), 0.6),
    ("console", re.compile(r"^(\$\s|>\s|PS1=|>>>|>>)"), 0.7),
    ("syntax_diagram", re.compile(r"^(→|⇐|⇒|⟶|↓|↑)"), 0.8),
]

CLASSES = (
    "text", "heading", "table", "figure", "capture", "diagram",
    "code", "console", "formula", "editorial_note",
    "syntax_diagram", "footer", "index",
)
SIGNAL_NAMES = (
    "S_MONOSPACE", "S_BOLD", "S_ITALIC", "S_LARGE", "S_SYMBOL_DENSITY",
    "S_INDENT", "S_ALIGN_CENTER", "S_TABLE_GRID", "S_HAS_GAPS",
    "S_PATTERN", "S_TOP_BOTTOM",
)


# ============================================================
# Default profiles (per references/01-ingest/regions.md §5)
# ============================================================

DEFAULT_PROFILES: Dict[str, Dict[str, float]] = {
    "text":             {"S_MONOSPACE": 0.0, "S_BOLD": 0.0, "S_ITALIC": 0.0, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.0, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.0, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.0, "S_PATTERN": 0.0, "S_TOP_BOTTOM": 0.0},
    "heading":          {"S_MONOSPACE": 0.0, "S_BOLD": 0.85, "S_ITALIC": 0.0, "S_LARGE": 0.95, "S_SYMBOL_DENSITY": 0.0, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.5, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.0, "S_PATTERN": 0.4, "S_TOP_BOTTOM": 0.4},
    "table":            {"S_MONOSPACE": 0.0, "S_BOLD": 0.0, "S_ITALIC": 0.0, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.0, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.0, "S_TABLE_GRID": 0.95, "S_HAS_GAPS": 0.6, "S_PATTERN": 0.0, "S_TOP_BOTTOM": 0.0},
    "figure":           {"S_MONOSPACE": 0.0, "S_BOLD": 0.0, "S_ITALIC": 0.0, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.0, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.4, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.7, "S_PATTERN": 0.5, "S_TOP_BOTTOM": 0.3},
    "capture":          {"S_MONOSPACE": 0.0, "S_BOLD": 0.0, "S_ITALIC": 0.0, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.0, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.0, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.85, "S_PATTERN": 0.0, "S_TOP_BOTTOM": 0.0},
    "diagram":          {"S_MONOSPACE": 0.0, "S_BOLD": 0.0, "S_ITALIC": 0.0, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.4, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.3, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.5, "S_PATTERN": 0.3, "S_TOP_BOTTOM": 0.0},
    "code":             {"S_MONOSPACE": 0.95, "S_BOLD": 0.0, "S_ITALIC": 0.0, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.7, "S_INDENT": 0.6, "S_ALIGN_CENTER": 0.0, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.1, "S_PATTERN": 0.6, "S_TOP_BOTTOM": 0.0},
    "console":          {"S_MONOSPACE": 0.85, "S_BOLD": 0.0, "S_ITALIC": 0.0, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.4, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.0, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.1, "S_PATTERN": 0.7, "S_TOP_BOTTOM": 0.0},
    "formula":          {"S_MONOSPACE": 0.0, "S_BOLD": 0.0, "S_ITALIC": 0.6, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.85, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.4, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.3, "S_PATTERN": 0.5, "S_TOP_BOTTOM": 0.0},
    "editorial_note":   {"S_MONOSPACE": 0.0, "S_BOLD": 0.4, "S_ITALIC": 0.85, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.0, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.3, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.85, "S_PATTERN": 1.0, "S_TOP_BOTTOM": 0.0},
    "syntax_diagram":   {"S_MONOSPACE": 0.4, "S_BOLD": 0.0, "S_ITALIC": 0.0, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.85, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.5, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.4, "S_PATTERN": 0.8, "S_TOP_BOTTOM": 0.0},
    "footer":           {"S_MONOSPACE": 0.0, "S_BOLD": 0.0, "S_ITALIC": 0.0, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.0, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.0, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.0, "S_PATTERN": 0.5, "S_TOP_BOTTOM": 0.95},
    "index":            {"S_MONOSPACE": 0.0, "S_BOLD": 0.0, "S_ITALIC": 0.0, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.4, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.0, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.0, "S_PATTERN": 0.7, "S_TOP_BOTTOM": 0.6},
}


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
# Word source loading (fragments.json or ocr_summary.json)
# ============================================================

@dataclass
class Word:
    text: str
    page: int
    bbox: Tuple[float, float, float, float]
    font_name: Optional[str] = None
    font_size: Optional[float] = None

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


def _load_words(fragments_path: Optional[Path], ocr_path: Optional[Path]) -> Dict[int, List[Word]]:
    """Return per-page list of Words from fragments or ocr output."""
    pages: Dict[int, List[Word]] = {}
    if fragments_path and fragments_path.exists():
        try:
            data = json.loads(fragments_path.read_text(encoding="utf-8"))
        except Exception:
            data = None
        if data and "pages" in data:
            for page_data in data["pages"]:
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
                        page=page_num,
                        bbox=(x0, y0, x1 - x0, y1 - y0),
                        font_name=f.get("font_name"),
                        font_size=f.get("font_size"),
                    ))
                if words:
                    pages[page_num] = words
    if not pages and ocr_path and ocr_path.exists():
        try:
            data = json.loads(ocr_path.read_text(encoding="utf-8"))
        except Exception:
            data = None
        if data and "pages" in data:
            for page_data in data["pages"]:
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
                        page=page_num,
                        bbox=(x, y, ww, hh),
                        font_name=None,
                        font_size=None,
                    ))
                if words:
                    pages[page_num] = words
    return pages


# ============================================================
# Signal extractors
# ============================================================

def _font_name_for(word_indices: List[int], words: List[Word]) -> Optional[str]:
    if not word_indices:
        return None
    fns = [words[i].font_name for i in word_indices if words[i].font_name]
    if not fns:
        return None
    counts: Dict[str, int] = {}
    for f in fns:
        counts[f] = counts.get(f, 0) + 1
    return max(counts, key=counts.get)


def _font_size_for(word_indices: List[int], words: List[Word]) -> Optional[float]:
    if not word_indices:
        return None
    fzs = [words[i].font_size for i in word_indices if words[i].font_size]
    if not fzs:
        return None
    return sum(fzs) / len(fzs)


def _page_body_size(words: List[Word]) -> float:
    if not words:
        return 12.0
    sizes = [w.font_size for w in words if w.font_size and w.font_size > 0]
    if not sizes:
        return 12.0
    counts = Counter(sizes)
    return float(counts.most_common(1)[0][0])


def s_monospace(word_indices: List[int], words: List[Word], _ctx: Dict[str, Any]) -> Tuple[float, Optional[str]]:
    if not word_indices:
        return 0.0, None
    matched = 0
    for i in word_indices:
        fn = words[i].font_name or ""
        if any(tok in fn.lower() for tok in MONOSPACE_FONTS):
            matched += 1
    ratio = matched / len(word_indices)
    return ratio if ratio >= 0.8 else 0.0, "font_name contains monospace family"


def s_bold(word_indices: List[int], words: List[Word], _ctx: Dict[str, Any]) -> Tuple[float, Optional[str]]:
    if not word_indices:
        return 0.0, None
    matched = 0
    for i in word_indices:
        fn = words[i].font_name or ""
        if any(tok in fn for tok in ("Bold", "Black", "Heavy", "Demi")):
            matched += 1
    ratio = matched / len(word_indices)
    return ratio if ratio >= 0.8 else 0.0, "font_name contains Bold/Black/Heavy/Demi"


def s_italic(word_indices: List[int], words: List[Word], _ctx: Dict[str, Any]) -> Tuple[float, Optional[str]]:
    if not word_indices:
        return 0.0, None
    matched = 0
    for i in word_indices:
        fn = words[i].font_name or ""
        if any(tok in fn for tok in ("Italic", "Oblique")):
            matched += 1
    ratio = matched / len(word_indices)
    return ratio if ratio >= 0.8 else 0.0, "font_name contains Italic/Oblique"


def s_large(word_indices: List[int], words: List[Word], ctx: Dict[str, Any]) -> Tuple[float, Optional[str]]:
    fs = _font_size_for(word_indices, words)
    if fs is None:
        return 0.0, None
    body = ctx.get("body_size", 12.0)
    return 1.0 if fs >= LARGE_FACTOR * body else 0.0, f"font_size {fs:.1f} ≥ {LARGE_FACTOR}×{body:.1f}"


def s_symbol_density(word_indices: List[int], words: List[Word], _ctx: Dict[str, Any]) -> Tuple[float, Optional[str]]:
    if not word_indices:
        return 0.0, None
    text = " ".join(words[i].text for i in word_indices)
    if not text:
        return 0.0, None
    alnum = sum(1 for c in text if c.isalnum() or c.isspace())
    non_alnum = sum(1 for c in text if not c.isalnum() and not c.isspace())
    if alnum == 0:
        return 0.0, None
    ratio = non_alnum / alnum
    return min(ratio / SYMBOL_DENSITY_HIGH, 1.0), f"symbol ratio {ratio:.3f}"


def s_indent(word_indices: List[int], words: List[Word], _ctx: Dict[str, Any]) -> Tuple[float, Optional[str]]:
    if not word_indices:
        return 0.0, None
    xs = [words[i].x for i in word_indices]
    if not xs:
        return 0.0, None
    x_min = min(xs)
    in_band = sum(1 for x in xs if INDENT_MIN_PX <= (x - x_min) <= INDENT_MAX_PX * 3)
    ratio = in_band / len(xs)
    return ratio if ratio >= 0.8 else 0.0, f"indent ratio {ratio:.2f}"


def s_align_center(word_indices: List[int], words: List[Word], ctx: Dict[str, Any]) -> Tuple[float, Optional[str]]:
    if not word_indices:
        return 0.0, None
    xs = [words[i].x + words[i].w / 2.0 for i in word_indices]
    if not xs:
        return 0.0, None
    avg_x = sum(xs) / len(xs)
    column_center = ctx.get("column_center")
    column_width = ctx.get("column_width", 612.0)
    if column_center is None or column_width <= 0:
        return 0.0, None
    deviation = abs(avg_x - column_center) / column_width
    return 1.0 if deviation <= CENTER_TOL_PCT else 0.0, f"deviation {deviation:.3f}"


def s_table_grid(word_indices: List[int], words: List[Word], ctx: Dict[str, Any]) -> Tuple[float, Optional[str]]:
    return (1.0, "columnar alignment detected by F21") if ctx.get("table_grid", False) else (0.0, None)


def s_has_gaps(word_indices: List[int], words: List[Word], ctx: Dict[str, Any]) -> Tuple[float, Optional[str]]:
    if not word_indices:
        return 0.0, None
    if not ctx.get("region_bbox"):
        return 0.0, None
    bx0, by0, bw, bh = ctx["region_bbox"]
    bbox_area = bw * bh
    if bbox_area <= 0:
        return 0.0, None
    words_area = 0.0
    for i in word_indices:
        words_area += words[i].w * words[i].h
    fill_ratio = words_area / bbox_area
    empty = 1.0 - fill_ratio
    if empty < EMPTY_AREA_RATIO:
        return 0.0, None
    return min((empty - EMPTY_AREA_RATIO) / (1.0 - EMPTY_AREA_RATIO), 1.0), f"empty area {empty:.2f}"


def s_pattern(word_indices: List[int], words: List[Word], _ctx: Dict[str, Any]) -> Tuple[float, Optional[str]]:
    if not word_indices:
        return 0.0, None
    text = " ".join(words[i].text for i in word_indices)
    text = text.strip()
    if not text:
        return 0.0, None
    for _tag, pattern, weight in PATTERNS:
        if pattern.match(text):
            return weight, f"matched regex: {pattern.pattern}"
    return 0.0, None


def s_top_bottom(word_indices: List[int], words: List[Word], ctx: Dict[str, Any]) -> Tuple[float, Optional[str]]:
    if not word_indices:
        return 0.0, None
    ys = [(words[i].y + words[i].h / 2.0) for i in word_indices]
    if not ys:
        return 0.0, None
    avg_y = sum(ys) / len(ys)
    page_h = ctx.get("page_height", 792.0)
    if avg_y <= TOP_REGION_PCT * page_h or avg_y >= (1 - BOTTOM_REGION_PCT) * page_h:
        return 1.0, f"y={avg_y:.0f} in top/bottom band of {page_h:.0f}"
    return 0.0, None


SIGNAL_EXTRACTORS: Dict[str, Callable] = {
    "S_MONOSPACE": s_monospace,
    "S_BOLD": s_bold,
    "S_ITALIC": s_italic,
    "S_LARGE": s_large,
    "S_SYMBOL_DENSITY": s_symbol_density,
    "S_INDENT": s_indent,
    "S_ALIGN_CENTER": s_align_center,
    "S_TABLE_GRID": s_table_grid,
    "S_HAS_GAPS": s_has_gaps,
    "S_PATTERN": s_pattern,
    "S_TOP_BOTTOM": s_top_bottom,
}


# ============================================================
# Scoring
# ============================================================

def compute_signals(
    region: Dict[str, Any],
    word_indices: List[int],
    words: List[Word],
    ctx: Dict[str, Any],
) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
    signal_values: Dict[str, float] = {}
    signal_log: List[Dict[str, Any]] = []
    for name in SIGNAL_NAMES:
        value, detail = SIGNAL_EXTRACTORS[name](word_indices, words, ctx)
        signal_values[name] = value
        if value > 0.0 and detail:
            signal_log.append({"signal": name, "value": round(value, 3), "detail": detail})
    return signal_values, signal_log


def score_region(
    signal_values: Dict[str, float],
    profile: Dict[str, Dict[str, float]],
) -> Tuple[str, float, List[Tuple[str, float]]]:
    BASE_BIAS = {"text": 0.50}  # text gets a higher baseline so it wins on plain prose
    BASELINE = 0.30
    scores: Dict[str, float] = {}
    for cls in CLASSES:
        s = BASE_BIAS.get(cls, BASELINE)
        p = profile.get(cls, {})
        for sig_name, sig_value in signal_values.items():
            weight = p.get(sig_name, 0.0)
            s += sig_value * weight
        scores[cls] = round(s, 4)
    sorted_scores = sorted(scores.items(), key=lambda kv: -kv[1])
    best_cls, best_score = sorted_scores[0]
    second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0.0
    return best_cls, best_score, sorted_scores


# ============================================================
# Region loading
# ============================================================

def load_regions(source: Path) -> List[Dict[str, Any]]:
    """Load all page-NNNN.regions.json from source (file or directory)."""
    if source.is_file():
        paths = [source]
    elif source.is_dir():
        paths = sorted(source.glob("page-*.regions.json"))
    else:
        raise RuntimeError(f"source not found: {source}")
    pages: List[Dict[str, Any]] = []
    for p in paths:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            raise RuntimeError(f"failed to parse {p}: {e}")
        if "regions" not in data:
            continue
        pages.append(data)
    return pages


# ============================================================
# Page processing
# ============================================================

def _classify_region(
    region: Dict[str, Any],
    page_words: List[Word],
    page_height: float,
    page_width: float,
    profile: Dict[str, Dict[str, float]],
    warnings: List[str],
) -> Dict[str, Any]:
    valid_indices = _match_words_to_region(region, page_words)
    bbox = region.get("bbox", [0, 0, 0, 0])
    try:
        bbox_tuple = tuple(float(v) for v in bbox)
    except (TypeError, ValueError):
        bbox_tuple = (0.0, 0.0, 0.0, 0.0)
    ctx: Dict[str, Any] = {
        "body_size": _page_body_size(page_words),
        "page_height": page_height,
        "page_width": page_width,
        "region_bbox": bbox_tuple,
        "table_grid": region.get("class") == "column" and len(valid_indices) > 0 and _has_table_pattern(page_words, valid_indices),
    }
    xs = [page_words[i].x for i in valid_indices]
    if xs and (max(xs) - min(xs)) > 0:
        ctx["column_center"] = (min(xs) + max(xs)) / 2.0
        ctx["column_width"] = max(xs) - min(xs)
    else:
        ctx["column_center"] = None
        ctx["column_width"] = 0.0

    signal_values, signal_log = compute_signals(region, valid_indices, page_words, ctx)
    best_cls, best_score, sorted_scores = score_region(signal_values, profile)

    has_any_signal = any(v > 0.0 for v in signal_values.values())
    second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0.0
    if not has_any_signal:
        ambiguity = False
        best_cls = "text"
        best_score = 0.30
        sorted_scores = [("text", 0.30)] + [(c, s) for c, s in sorted_scores if c != "text"]
        alternative_classes = []
    else:
        ambiguity = (best_score < CLASS_MIN_THRESHOLD) or (best_score - second_score < AMBIGUITY_MARGIN)
        alternative_classes = []
        if ambiguity:
            best_cls_for_alt = best_cls
            for cls, sc in sorted_scores[:5]:
                if cls != best_cls_for_alt:
                    alternative_classes.append({"class": cls, "score": sc})
            alternative_classes = alternative_classes[:4]
            warnings.append(
                f"page {region.get('page', '?')} region {region.get('id', '?')}: ambiguous "
                f"(best={best_cls_for_alt}@{best_score:.3f}, second={second_score:.3f})"
            )

    alternative_classes = []
    semantic_class: Optional[str] = best_cls
    if not has_any_signal:
        semantic_class = "text"
        best_score = 0.30
    if ambiguity and has_any_signal:
        semantic_class = None
        for cls, sc in sorted_scores[:5]:
            if cls != best_cls:
                alternative_classes.append({"class": cls, "score": sc})
        alternative_classes = alternative_classes[:4]
        warnings.append(
            f"page {region.get('page', '?')} region {region.get('id', '?')}: ambiguous "
            f"(best={best_cls}@{best_score:.3f}, second={second_score:.3f})"
        )

    out_region = dict(region)
    out_region["semantic_class"] = semantic_class
    out_region["class_confidence"] = round(best_score, 3)
    out_region["ambiguity"] = ambiguity
    out_region["alternative_classes"] = alternative_classes
    out_region["signals"] = signal_log
    out_region["word_indices"] = valid_indices
    out_region["sub_kind"] = None
    if best_cls == "editorial_note" and not ambiguity:
        out_region["sub_kind"] = _detect_sub_kind(region, valid_indices, page_words)
    return out_region


def _match_words_to_region(region: Dict[str, Any], page_words: List[Word]) -> List[int]:
    """Match page words to a region by bbox overlap (since F21 layout output
    does not include word_indices)."""
    indices_attr = region.get("word_indices")
    if indices_attr:
        return [i for i in indices_attr if 0 <= i < len(page_words)]
    bbox = region.get("bbox", [0, 0, 0, 0])
    try:
        rx0, ry0, rw, rh = [float(v) for v in bbox]
    except (TypeError, ValueError):
        return []
    rx1, ry1 = rx0 + rw, ry0 + rh
    matched: List[int] = []
    for i, w in enumerate(page_words):
        wx0, wy0 = w.x, w.y
        wx1, wy1 = w.x + w.w, w.y + w.h
        cx = max(rx0, wx0)
        cy = max(ry0, wy0)
        ox = min(rx1, wx1) - cx
        oy = min(ry1, wy1) - cy
        if ox > 0 and oy > 0 and (ox * oy) >= 0.5 * (w.w * w.h):
            matched.append(i)
    return matched


def _has_table_pattern(words: List[Word], indices: List[int]) -> bool:
    """Detect columnar alignment in the region (proxy for F21's table_grid)."""
    if len(indices) < 4:
        return False
    xs = sorted(set(round(words[i].x, 0) for i in indices))
    if len(xs) < 3:
        return False
    ys = sorted(set(round(words[i].y, 0) for i in indices))
    if len(ys) < 2:
        return False
    return True


def _detect_sub_kind(region: Dict[str, Any], word_indices: List[int], words: List[Word]) -> str:
    """Detect 'box' (rodeado de gaps) vs 'inline' for editorial_note."""
    if not word_indices:
        return "inline"
    text_words = [words[i].text for i in word_indices]
    text = " ".join(text_words).strip()
    if len(text_words) > EDITORIAL_BOX_MAX_WORDS:
        return "inline"
    return "box"


# ============================================================
# Entry point
# ============================================================

def run(
    source: Path,
    out_dir: Path,
    fragments_path: Optional[Path],
    ocr_path: Optional[Path],
    profile_path: Optional[Path],
    json_only: bool = False,
) -> int:
    source = Path(source).resolve()
    if not source.exists():
        print(f"ERROR: source not found: {source}", file=sys.stderr)
        return 1

    warnings: List[str] = []
    pages = load_regions(source)
    if not pages:
        print(f"ERROR: no page-NNNN.regions.json found in {source}", file=sys.stderr)
        return 1

    profile = DEFAULT_PROFILES
    if profile_path and Path(profile_path).exists():
        try:
            import yaml
            with open(profile_path, "r", encoding="utf-8") as f:
                profile_data = yaml.safe_load(f)
            if isinstance(profile_data, dict):
                profile = profile_data
        except ImportError:
            warnings.append("PyYAML not available; using default profiles")
        except Exception as e:
            warnings.append(f"failed to parse class-profile YAML ({e}); using default profiles")

    words_by_page = _load_words(fragments_path, ocr_path)
    if not words_by_page:
        warnings.append("no fragments/ocr words available; signals may be missing")

    out_regions_dir = out_dir / "ingest" / "regions"
    out_regions_dir.mkdir(parents=True, exist_ok=True)

    all_classified: List[Dict[str, Any]] = []
    ambiguous_regions: List[Dict[str, Any]] = []
    class_distribution: Counter = Counter()

    for page_data in pages:
        page_num = int(page_data.get("page", 1))
        page_words = words_by_page.get(page_num, [])
        page_width = 612.0
        page_height = 792.0
        if page_words:
            xs = [w.x + w.w for w in page_words]
            ys = [w.y + w.h for w in page_words]
            if xs:
                page_width = max(page_width, max(xs))
            if ys:
                page_height = max(page_height, max(ys))

        new_regions = []
        for r in page_data.get("regions", []):
            new_r = _classify_region(r, page_words, page_height, page_width, profile, warnings)
            new_regions.append(new_r)
            all_classified.append(new_r)
            if new_r["semantic_class"] is None:
                ambiguous_regions.append({
                    "page": page_num,
                    "region_id": new_r.get("id"),
                    "alternative_classes": new_r["alternative_classes"],
                })
            else:
                class_distribution[new_r["semantic_class"]] += 1

        atomic_write_text(
            out_regions_dir / f"page-{page_num:04d}.regions.json",
            json.dumps({"page": page_num, "regions": new_regions}, indent=2, ensure_ascii=False),
        )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "layout_dir": str(source),
            "fragments_path": str(fragments_path) if fragments_path else None,
            "ocr_summary_path": str(ocr_path) if ocr_path else None,
            "hash": sha256_paths([Path(source)] + ([fragments_path] if fragments_path else []) + ([ocr_path] if ocr_path else [])),
        },
        "class_profile_version": "1.0.0",
        "page_count": len(pages),
        "class_distribution": dict(class_distribution),
        "ambiguous_count": len(ambiguous_regions),
        "ambiguous_regions": ambiguous_regions,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    atomic_write_text(
        out_regions_dir / "regions_summary.json",
        json.dumps(summary, indent=2, ensure_ascii=False),
    )

    if not json_only:
        md_lines = [f"# Regions — `{source.name}`", ""]
        md_lines.append(f"- **Páginas:** {len(pages)}")
        md_lines.append(f"- **Regiones clasificadas:** {len(all_classified)}")
        md_lines.append(f"- **Ambiguas:** {len(ambiguous_regions)}")
        if warnings:
            md_lines.append("")
            md_lines.append("## Advertencias")
            for w in warnings:
                md_lines.append(f"- {w}")
        md_lines.append("")
        md_lines.append("## Distribución por clase")
        md_lines.append("")
        md_lines.append("| Clase | Conteo |")
        md_lines.append("|---|---|")
        for cls in CLASSES:
            count = class_distribution.get(cls, 0)
            if count:
                md_lines.append(f"| `{cls}` | {count} |")
        atomic_write_text(out_regions_dir / "regions.md", "\n".join(md_lines) + "\n")

    return 2 if warnings else 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="regions.py",
        description="F22 — Semantic region classifier (13 classes × 11 signals, ambiguity-aware).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Constantes (references/01-ingest/regions.md §6):
  CLASS_MIN_THRESHOLD     = 0.45   umbral para asignar clase con confianza
  AMBIGUITY_MARGIN        = 0.10   margen mínimo top1-top2 para no marcar ambiguo
  LARGE_FACTOR            = 1.3    factor para detectar 'large' (heading)
  SYMBOL_DENSITY_HIGH     = 0.30   ratio para saturar señal S_SYMBOL_DENSITY
  EMPTY_AREA_RATIO        = 0.30   mínimo bbox vacío para S_HAS_GAPS
  CENTER_TOL_PCT          = 0.05   tolerancia para S_ALIGN_CENTER
  TOP_REGION_PCT          = 0.10   banda superior para S_TOP_BOTTOM
  BOTTOM_REGION_PCT       = 0.10   banda inferior para S_TOP_BOTTOM

Clases (13, oficiales):
  text, heading, table, figure, capture, diagram, code, console,
  formula, editorial_note, syntax_diagram, footer, index

Códigos de salida:
  0 OK sin advertencias
  1 error fatal
  2 OK con advertencias (regiones ambiguas, falta fragments/ocr)
""",
    )
    parser.add_argument("--source", required=True, help="Directorio con page-NNNN.regions.json (F21)")
    parser.add_argument("--out-dir", required=True, help="Directorio de salida (ingest/regions/)")
    parser.add_argument("--fragments", default=None, help="fragments.json (F18) opcional")
    parser.add_argument("--ocr", default=None, help="ocr_summary.json (F20) opcional")
    parser.add_argument("--class-profile", default=None, help="YAML con perfiles de clase (opcional)")
    parser.add_argument("--json-only", action="store_true", help="Solo escribir regions_summary.json (no regions.md)")
    args = parser.parse_args(argv)

    fragments_path = Path(args.fragments) if args.fragments else None
    ocr_path = Path(args.ocr) if args.ocr else None
    profile_path = Path(args.class_profile) if args.class_profile else None
    code = run(Path(args.source), Path(args.out_dir), fragments_path, ocr_path, profile_path, json_only=args.json_only)
    return code


if __name__ == "__main__":
    sys.exit(main())
