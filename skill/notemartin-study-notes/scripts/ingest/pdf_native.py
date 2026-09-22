#!/usr/bin/env python3
"""pdf_native.py — F18 PDF native extraction.

Extrae runs de texto de un PDF con capa de texto (no escaneado), con sus
coordenadas, fuente y tamaño. Detecta encabezados por tipografía, marca
boilerplate por repetición posicional entre páginas y reconstruye el índice
desde los marcadores PDF cuando existen.

Uso:
    python3 scripts/ingest/pdf_native.py --source <pdf> --out-dir <dir> [--plan <triage.json>]

Salidas (en --out-dir):
    fragments.json — contrato para F31 (build_sdm)
    extraction.md — resumen legible para humanos (omitido con --json-only)

Códigos de salida:
    0 — OK
    1 — Error fatal (PDF ilegible, formato no PDF)
    2 — OK con advertencias (outline ausente, pure_scan ranges saltadas, etc.)

Dependencias:
    - Python 3.9+ stdlib
    - pypdf >= 4 (recomendado; si falta, el script rechaza con error claro)

Documentación normativa: references/01-ingest/pdf-native.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import pypdf  # type: ignore
except ImportError:  # pragma: no cover
    pypdf = None  # type: ignore

SCHEMA_VERSION = "1.0.0"
EXTRACTION_VERSION = "1.0.0"

# ============================================================
# Constants (per references/01-ingest/pdf-native.md §4-§5)
# ============================================================

HEADER_BAND_RATIO = 0.08
FOOTER_BAND_RATIO = 0.08
BOILERPLATE_PAGE_RATIO = 0.30
BOILERPLATE_BBOX_TOLERANCE = 0.05
HEADING_SIZE_GAP_PT = 0.5
HEADING_FREQ_MAX = 0.20
INLINE_BOILERPLATE_MAX_CHARS = 30
TEXT_WIDTH_FACTOR = 0.5  # approx char width as fraction of font_size


# ============================================================
# Helpers
# ============================================================

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "section"


def fragment_id(page: int, bbox: List[float], text: str) -> str:
    serialized = f"{page}::{bbox[0]:.2f}::{bbox[1]:.2f}::{bbox[2]:.2f}::{bbox[3]:.2f}::{text[:64]}"
    return hashlib.sha1(serialized.encode("utf-8")).hexdigest()[:12]


def parse_range_string(s: str) -> Tuple[int, int]:
    if "-" in s:
        a, b = s.split("-", 1)
        return int(a), int(b)
    n = int(s)
    return n, n


def expand_ranges(ranges: List[str]) -> set:
    pages = set()
    for r in ranges:
        a, b = parse_range_string(r)
        for p in range(a, b + 1):
            pages.add(p)
    return pages


def normalize_font_name(font_dict: Optional[Dict[str, Any]]) -> str:
    if not font_dict:
        return "Unknown"
    base = font_dict.get("/BaseFont", "Unknown")
    if isinstance(base, str) and base.startswith("/"):
        base = base[1:]
    return str(base)


def approx_text_width(text: str, font_size: float) -> float:
    return max(len(text) * font_size * TEXT_WIDTH_FACTOR, font_size)


# ============================================================
# Fragment extraction (per page)
# ============================================================

def extract_page_fragments(page: Any, page_num: int, warnings: List[str]) -> List[Dict[str, Any]]:
    """Extract text fragments with bbox + font + size from a single page."""
    fragments: List[Dict[str, Any]] = []
    try:
        mediabox = page.mediabox
        page_width = float(mediabox.width)
        page_height = float(mediabox.height)
    except Exception:
        page_width = 612.0
        page_height = 792.0

    if pypdf is None:
        warnings.append("pypdf not available; cannot extract fragments")
        return fragments

    def visitor_text(text: str, cm: Any, tm: Any, font_dict: Optional[Dict[str, Any]], font_size: float) -> str:
        if not text or not text.strip():
            return text
        try:
            x = float(tm[4])
            y = float(tm[5])
        except (TypeError, IndexError, ValueError):
            return text
        try:
            fs = float(font_size)
        except (TypeError, ValueError):
            fs = 0.0
        if fs <= 0:
            return text
        text_clean = text.replace("\n", " ").strip()
        if not text_clean:
            return text
        width = approx_text_width(text_clean, fs)
        bbox = [round(x, 3), round(y, 3), round(x + width, 3), round(y + fs, 3)]
        fragments.append({
            "page": page_num,
            "bbox": bbox,
            "font_name": normalize_font_name(font_dict),
            "font_size": round(fs, 3),
            "text": text_clean,
        })
        return text

    try:
        page.extract_text(visitor_text=visitor_text)
    except Exception as e:
        warnings.append(f"page {page_num}: visitor_text failed ({e}); falling back to per-page")
        try:
            text = page.extract_text() or ""
            if text.strip():
                fragments.append({
                    "page": page_num,
                    "bbox": [0.0, 0.0, round(page_width, 3), round(page_height, 3)],
                    "font_name": "Unknown",
                    "font_size": 0.0,
                    "text": text.strip(),
                })
        except Exception as e2:
            warnings.append(f"page {page_num}: fallback extract_text failed ({e2})")

    return fragments


# ============================================================
# Heading detection (per spec §4)
# ============================================================

def detect_body_size(fragments: List[Dict[str, Any]]) -> float:
    """Return the modal font_size across all fragments (per spec §4.1)."""
    if not fragments:
        return 12.0
    counter: Counter = Counter()
    for f in fragments:
        if f.get("font_size", 0) > 0:
            counter[f["font_size"]] += 1
    if not counter:
        return 12.0
    return float(counter.most_common(1)[0][0])


def detect_heading_levels(fragments: List[Dict[str, Any]], body_size: float) -> Dict[float, int]:
    """Return a mapping {font_size: heading_level} (per spec §4.2)."""
    if not fragments:
        return {}
    total = sum(1 for f in fragments if f.get("font_size", 0) > 0)
    if total == 0:
        return {}

    counter: Counter = Counter()
    for f in fragments:
        fs = f.get("font_size", 0)
        if fs > body_size and fs > 0:
            counter[fs] += 1

    candidates = []
    for fs, count in counter.items():
        if count / total <= HEADING_FREQ_MAX:
            candidates.append(fs)

    candidates.sort(reverse=True)
    levels: Dict[float, int] = {}
    used_level = 0
    last_size: Optional[float] = None
    for fs in candidates:
        if last_size is not None and (last_size - fs) < HEADING_SIZE_GAP_PT:
            continue
        used_level += 1
        levels[fs] = used_level
        last_size = fs
    return levels


def apply_heading_roles(fragments: List[Dict[str, Any]], body_size: float, heading_levels: Dict[float, int]) -> None:
    """Mutate fragments in place: set role and heading_level based on typography."""
    for f in fragments:
        fs = f.get("font_size", 0)
        if fs <= 0:
            f["role"] = "unknown"
            f["heading_level"] = None
            continue
        font = f.get("font_name", "")
        is_italic = any(tok in font for tok in ("Italic", "Oblique"))
        is_bold = any(tok in font for tok in ("Bold", "Black", "Heavy", "Demi"))

        if fs in heading_levels:
            level = heading_levels[fs]
            if is_bold:
                level = max(1, level - 1)
            f["role"] = "heading"
            f["heading_level"] = level
        elif fs > body_size:
            f["role"] = "body"
            f["heading_level"] = None
        elif fs < body_size:
            f["role"] = "footnote"
            f["heading_level"] = None
        else:
            f["role"] = "body"
            f["heading_level"] = None
        if is_italic and f["role"] == "body":
            f["role"] = "caption"


# ============================================================
# Boilerplate detection (per spec §5)
# ============================================================

def detect_boilerplate(all_page_fragments: List[List[Dict[str, Any]]], page_height: float) -> Tuple[Dict[str, List[str]], set]:
    """Detect boilerplate by positional repetition across pages.

    Returns (summary_dict, set_of_fragment_ids_marked_as_boilerplate).
    """
    page_count = len(all_page_fragments)
    if page_count == 0:
        return {"header_texts": [], "footer_texts": [], "repeated_inline": []}, set()

    min_repeat = max(2, int(page_count * BOILERPLATE_PAGE_RATIO))
    header_threshold_y = page_height * (1 - HEADER_BAND_RATIO)
    footer_threshold_y = page_height * FOOTER_BAND_RATIO

    header_counter: Counter = Counter()
    footer_counter: Counter = Counter()
    inline_counter: Counter = Counter()
    header_pages: Dict[str, set] = {}
    footer_pages: Dict[str, set] = {}
    inline_pages: Dict[str, set] = {}

    for page_num, frags in enumerate(all_page_fragments, 1):
        for f in frags:
            text = f.get("text", "").strip()
            if not text:
                continue
            bbox = f.get("bbox", [0, 0, 0, 0])
            cy = (bbox[1] + bbox[3]) / 2.0
            if cy >= header_threshold_y:
                header_counter[text] += 1
                header_pages.setdefault(text, set()).add(page_num)
            elif cy <= footer_threshold_y:
                footer_counter[text] += 1
                footer_pages.setdefault(text, set()).add(page_num)
            elif len(text) <= INLINE_BOILERPLATE_MAX_CHARS:
                fs = f.get("font_size", 0)
                if fs > 0 and (text.isdigit() or text.lower().startswith("page")):
                    inline_counter[text] += 1
                    inline_pages.setdefault(text, set()).add(page_num)

    boilerplate_ids = set()
    boilerplate_texts = {"header": set(), "footer": set(), "inline": set()}

    for text, count in header_counter.items():
        if count >= min_repeat and len(header_pages.get(text, set())) >= min_repeat:
            boilerplate_texts["header"].add(text)
    for text, count in footer_counter.items():
        if count >= min_repeat and len(footer_pages.get(text, set())) >= min_repeat:
            boilerplate_texts["footer"].add(text)
    for text, count in inline_counter.items():
        if count >= min_repeat and len(inline_pages.get(text, set())) >= min_repeat:
            boilerplate_texts["inline"].add(text)

    for page_num, frags in enumerate(all_page_fragments, 1):
        for f in frags:
            text = f.get("text", "").strip()
            if not text:
                continue
            bbox = f.get("bbox", [0, 0, 0, 0])
            cy = (bbox[1] + bbox[3]) / 2.0
            fs = f.get("font_size", 0)
            if cy >= header_threshold_y and text in boilerplate_texts["header"]:
                f["role"] = "header"
                f["is_boilerplate"] = True
                boilerplate_ids.add(f.get("__id", ""))
            elif cy <= footer_threshold_y and text in boilerplate_texts["footer"]:
                f["role"] = "footer"
                f["is_boilerplate"] = True
                boilerplate_ids.add(f.get("__id", ""))
            elif (
                len(text) <= INLINE_BOILERPLATE_MAX_CHARS
                and text in boilerplate_texts["inline"]
                and fs > 0
            ):
                f["role"] = "page_number"
                f["is_boilerplate"] = True
                boilerplate_ids.add(f.get("__id", ""))

    summary = {
        "header_texts": sorted(boilerplate_texts["header"]),
        "footer_texts": sorted(boilerplate_texts["footer"]),
        "repeated_inline": sorted(boilerplate_texts["inline"]),
    }
    return summary, boilerplate_ids


# ============================================================
# Outline / section_path reconstruction (per spec §6)
# ============================================================

def walk_outline(reader: Any, items: List[Any], level: int = 1, parent_path: str = "", seen_titles: Optional[Counter] = None) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if seen_titles is None:
        seen_titles = Counter()
    for item in items or []:
        if isinstance(item, list):
            out.extend(walk_outline(reader, item, level + 1, parent_path, seen_titles))
            continue
        try:
            title = item.title if hasattr(item, "title") else str(item)
            page_num = reader.get_destination_page_number(item)
        except Exception:
            continue
        if page_num is None:
            continue
        page_num_1indexed = page_num + 1
        base_slug = slugify(title)
        seen_titles[base_slug] += 1
        suffix = "" if seen_titles[base_slug] == 1 else f"-{seen_titles[base_slug]}"
        section_path = f"{parent_path}/{base_slug}{suffix}".rstrip("/") or "/"
        out.append({
            "level": level,
            "title": title,
            "page": page_num_1indexed,
            "section_path": section_path,
        })
        if hasattr(item, "kids") and item.kids:
            out.extend(walk_outline(reader, item.kids, level + 1, section_path, seen_titles))
    return out


def extract_outline(reader: Any, warnings: List[str]) -> List[Dict[str, Any]]:
    try:
        outline = reader.outline if hasattr(reader, "outline") else []
    except Exception as e:
        warnings.append(f"failed to read outline ({e}); using heading-level fallback")
        return []
    if not outline:
        warnings.append("outline not present; using heading-level fallback")
        return []
    flat: List[Any] = []
    def _flatten(items):
        for it in items or []:
            if isinstance(it, list):
                _flatten(it)
            else:
                flat.append(it)
    _flatten(outline)
    return walk_outline(reader, outline)


def assign_section_paths(all_page_fragments: List[List[Dict[str, Any]]], outline: List[Dict[str, Any]]) -> None:
    if not outline:
        return
    by_page: Dict[int, List[Dict[str, Any]]] = {}
    for frags in all_page_fragments:
        for f in frags:
            by_page.setdefault(f["page"], []).append(f)

    for entry in outline:
        page = entry["page"]
        title = entry["title"]
        title_prefix = title[:30].strip()
        for f in by_page.get(page, []):
            if f.get("role") != "heading":
                continue
            text = f.get("text", "").strip()
            if text.startswith(title_prefix) or text == title.strip():
                f["section_path"] = entry["section_path"]
                f["heading_level"] = min(f.get("heading_level") or entry["level"], entry["level"])
                break


def fallback_hierarchy(all_page_fragments: List[List[Dict[str, Any]]], warnings: List[str]) -> List[Dict[str, Any]]:
    if any(f.get("section_path") for frags in all_page_fragments for f in frags if f.get("role") == "heading"):
        return []
    path_stack: List[Tuple[int, str]] = []
    seen_slugs: Counter = Counter()
    outline_entries: List[Dict[str, Any]] = []
    for frags in all_page_fragments:
        for f in frags:
            if f.get("role") != "heading":
                continue
            level = f.get("heading_level") or 1
            title = f.get("text", "").strip()
            while path_stack and path_stack[-1][0] >= level:
                path_stack.pop()
            base_slug = slugify(title)
            seen_slugs[base_slug] += 1
            suffix = "" if seen_slugs[base_slug] == 1 else f"-{seen_slugs[base_slug]}"
            section_path = "/".join([p[1] for p in path_stack] + [f"{base_slug}{suffix}"])
            f["section_path"] = section_path
            path_stack.append((level, f"{base_slug}{suffix}"))
            outline_entries.append({
                "level": level,
                "title": title,
                "page": f["page"],
                "section_path": section_path,
            })
    return outline_entries


# ============================================================
# Output
# ============================================================

def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent), delete=False) as tf:
        tf.write(content)
        tmpname = tf.name
    Path(tmpname).replace(path)


def render_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"# Extracción PDF nativo — `{payload['source']['path']}`")
    lines.append("")
    lines.append(f"- **Hash sha256:** `{payload['source']['hash']}`")
    lines.append(f"- **Tamaño:** {payload['source']['size_bytes']} bytes")
    lines.append(f"- **Páginas:** {payload['page_count']}")
    lines.append(f"- **Scope:** `{payload['scope']['type']}`")
    if payload["scope"].get("ranges"):
        lines.append(f"  - rangos: {payload['scope']['ranges']}")
    lines.append(f"- **Generado:** {payload['generated_at']}")
    if payload["warnings"]:
        lines.append("")
        lines.append("## Advertencias")
        for w in payload["warnings"]:
            lines.append(f"- {w}")
    lines.append("")
    lines.append("## Outline")
    lines.append("")
    if payload["outline"]:
        lines.append("| Nivel | Título | Página | section_path |")
        lines.append("|---|---|---|---|")
        for o in payload["outline"]:
            lines.append(f"| {o['level']} | {o['title']} | {o['page']} | `{o['section_path']}` |")
    else:
        lines.append("(vacío)")
    lines.append("")
    lines.append("## Boilerplate detectado")
    lines.append("")
    bs = payload["boilerplate_summary"]
    lines.append(f"- **Header:** {bs['header_texts'] or '(ninguno)'}")
    lines.append(f"- **Footer:** {bs['footer_texts'] or '(ninguno)'}")
    lines.append(f"- **Inline repetido:** {bs['repeated_inline'] or '(ninguno)'}")
    lines.append("")
    lines.append("## Fragmentos por página")
    lines.append("")
    lines.append("| Page | Role | Heading lvl | Font size | Font | x0,y0 | x1,y1 | boiler | text (60 chars) |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for p in payload["pages"]:
        for f in p["fragments"]:
            b = f["bbox"]
            text = f["text"][:60] + ("…" if len(f["text"]) > 60 else "")
            lines.append(
                f"| {f['page']} | `{f['role']}` | {f.get('heading_level') or '-'} | "
                f"{f['font_size']} | `{f['font_name']}` | {b[0]},{b[1]} | {b[2]},{b[3]} | "
                f"{'sí' if f.get('is_boilerplate') else 'no'} | {text} |"
            )
    return "\n".join(lines) + "\n"


# ============================================================
# Entry point
# ============================================================

def run(source: Path, out_dir: Path, plan_path: Optional[Path], json_only: bool = False) -> int:
    source = Path(source).resolve()
    if not source.exists():
        print(f"ERROR: source not found: {source}", file=sys.stderr)
        return 1
    if not source.is_file():
        print(f"ERROR: source is not a file: {source}", file=sys.stderr)
        return 1
    if not source.suffix.lower() == ".pdf":
        print(f"ERROR: source is not a PDF: {source}", file=sys.stderr)
        return 1

    raw = source.read_bytes()
    if not raw.startswith(b"%PDF-"):
        print(f"ERROR: file does not have PDF magic bytes: {source}", file=sys.stderr)
        return 1

    if pypdf is None:
        print("ERROR: pypdf is required. Install with: pip install pypdf", file=sys.stderr)
        return 1

    warnings: List[str] = []

    sha = sha256_file(source)
    size = source.stat().st_size

    scope_pages: Optional[set] = None
    scope_ranges: List[str] = []
    if plan_path:
        plan_path = Path(plan_path).resolve()
        if not plan_path.exists():
            warnings.append(f"plan file not found: {plan_path}; extracting all pages")
        else:
            try:
                plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
                native_classes = {"native_reliable", "native_degraded"}
                for r in plan_data.get("plan", []):
                    if r.get("class") in native_classes and not r.get("ocr_required"):
                        rng = r.get("pages", "")
                        if rng:
                            scope_ranges.append(rng)
                            a, b = parse_range_string(rng)
                            if scope_pages is None:
                                scope_pages = set()
                            for p in range(a, b + 1):
                                scope_pages.add(p)
                if scope_pages is None:
                    warnings.append("plan has no native_reliable/native_degraded ranges; extracting all pages")
                    scope_pages = None
                else:
                    warnings.append(f"plan restricts extraction to ranges: {scope_ranges}")
            except Exception as e:
                warnings.append(f"failed to parse plan ({e}); extracting all pages")
                scope_pages = None
                scope_ranges = []

    try:
        reader = pypdf.PdfReader(str(source))
    except Exception as e:
        print(f"ERROR: failed to open PDF: {e}", file=sys.stderr)
        return 1

    page_count = len(reader.pages)
    if page_count == 0:
        warnings.append("PDF has 0 pages")
    page_height = 792.0
    if page_count > 0:
        try:
            page_height = float(reader.pages[0].mediabox.height)
        except Exception:
            pass

    all_page_fragments: List[List[Dict[str, Any]]] = []
    skipped_pure_scan = 0

    for page_idx in range(page_count):
        page_num = page_idx + 1
        if scope_pages is not None and page_num not in scope_pages:
            continue
        page = reader.pages[page_idx]
        page_warnings: List[str] = []
        fragments = extract_page_fragments(page, page_num, page_warnings)
        for w in page_warnings:
            warnings.append(f"page {page_num}: {w}")
        for f in fragments:
            if f.get("font_size", 0) == 0:
                warnings.append(f"page {page_num}: fragment without font_size; role=unknown")
        if not fragments:
            warnings.append(f"page {page_num}: 0 fragments extracted")
        all_page_fragments.append(fragments)

    flat = [f for frags in all_page_fragments for f in frags]
    body_size = detect_body_size(flat)
    heading_levels = detect_heading_levels(flat, body_size)
    for frags in all_page_fragments:
        apply_heading_roles(frags, body_size, heading_levels)

    boilerplate_summary, _boilerplate_ids = detect_boilerplate(all_page_fragments, page_height)

    outline = extract_outline(reader, warnings)
    assign_section_paths(all_page_fragments, outline)
    if not outline:
        fb = fallback_hierarchy(all_page_fragments, warnings)
        if fb:
            outline = fb

    payload_pages: List[Dict[str, Any]] = []
    for frags in all_page_fragments:
        page_num = frags[0]["page"] if frags else None
        if page_num is None:
            continue
        annotated: List[Dict[str, Any]] = []
        for f in frags:
            f_id = fragment_id(f["page"], f["bbox"], f["text"])
            annotated.append({
                "id": f_id,
                "page": f["page"],
                "bbox": f["bbox"],
                "font_name": f["font_name"],
                "font_size": f["font_size"],
                "text": f["text"],
                "role": f.get("role", "unknown"),
                "heading_level": f.get("heading_level"),
                "section_path": f.get("section_path"),
                "is_boilerplate": bool(f.get("is_boilerplate", False)),
            })
        payload_pages.append({"page": page_num, "fragments": annotated})

    payload = {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "path": str(source),
            "hash": sha,
            "size_bytes": size,
            "format": "pdf",
        },
        "extraction_version": EXTRACTION_VERSION,
        "page_count": page_count,
        "scope": {
            "type": "ranges" if scope_ranges else "all",
            "ranges": scope_ranges,
        },
        "pages": payload_pages,
        "outline": outline,
        "boilerplate_summary": boilerplate_summary,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_text(out_dir / "fragments.json", json.dumps(payload, indent=2, ensure_ascii=False))
    if not json_only:
        atomic_write_text(out_dir / "extraction.md", render_markdown(payload))

    return 2 if warnings else 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pdf_native.py",
        description="F18 — Extracción de PDF nativo (runs de texto con bbox, fuente, tamaño).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Constantes (references/01-ingest/pdf-native.md §4-§5):
  HEADER_BAND_RATIO         = 0.08   top 8% de página → header
  FOOTER_BAND_RATIO         = 0.08   bottom 8% → footer
  BOILERPLATE_PAGE_RATIO    = 0.30   ≥ 30% de páginas para marcar boilerplate
  BOILERPLATE_BBOX_TOLERANCE= 0.05   ± 5% del centroide de banda
  HEADING_FREQ_MAX          = 0.20   tamaño heading ≤ 20% de fragmentos
  HEADING_SIZE_GAP_PT       = 0.5    pt mínimo entre niveles
  INLINE_BOILERPLATE_MAX    = 30     chars para page numbers inline

Códigos de salida:
  0 OK sin advertencias
  1 error fatal
  2 OK con advertencias (outline ausente, pure_scan saltadas, etc.)
""",
    )
    parser.add_argument("--source", required=True, help="Ruta al PDF")
    parser.add_argument("--out-dir", required=True, help="Directorio de salida (fragments.json + extraction.md)")
    parser.add_argument("--plan", default=None, help="Ruta a triage.json para limitar extracción a rangos nativos")
    parser.add_argument("--json-only", action="store_true", help="Solo escribir fragments.json (no extraction.md)")
    args = parser.parse_args(argv)

    plan_path = Path(args.plan) if args.plan else None
    code = run(Path(args.source), Path(args.out_dir), plan_path, json_only=args.json_only)
    return code


if __name__ == "__main__":
    sys.exit(main())
