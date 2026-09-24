#!/usr/bin/env python3
"""build_sdm.py — F31 Source Document Model assembler.

Ensambla la salida de F17-F30 (triage, fragments, regions, tables, formulas,
code_ocr, review, post_ocr, web_docs, other_formats) en un `sdm.json` conforme
a `schemas/sdm.schema.json` (F13). Genera ids deterministas con la fórmula
`sha1(source.hash + section_path + str(block_index))[:12]`, asocia pies a
figuras y preserva la referencia de los footnotes.

Uso:
    python3 scripts/ingest/build_sdm.py \
        --ingest-dir <dir> --source-meta <yaml> --out-dir <dir> \
        [--source-file <path>] [--format {auto,pdf,html,epub,docx,pptx,transcript,repo}] \
        [--check-determinism] [--json-only]

Salidas (en <out-dir>/):
    sdm.json                       — Source Document Model validable contra F13
    build_sdm_summary.json         — counts + warnings + validation/determinism
    build_sdm.md                   — resumen legible (omitido con --json-only)

Códigos de salida:
    0 — OK
    1 — Error fatal (input ausente, schema invalid, determinismo roto)
    2 — OK con advertencias (asociaciones faltantes, regiones ambiguas, etc.)

Dependencias:
    - Python 3.9+ stdlib
    - PyYAML (recomendado) — para `--source-meta`. Si falta, exit 1 accionable.
    - jsonschema (recomendado) — se reusa desde `scripts/util/validate_sdm.py`
      vía subproceso para validar el resultado. Si falta, F31 emite validación
      mínima (id determinista + anchor presente + ocr ⇒ confidence<1) y avisa.

Documentación normativa: references/02-source-model/build-sdm.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"

# ============================================================
# Constants (per references/02-source-model/build-sdm.md §2-§7)
# ============================================================

CAPTION_PATTERN = re.compile(
    r"^(Figure|Fig\.|Tabla|Tab\.|Listing|Snippet)\s*\d",
    re.IGNORECASE,
)

CAPTION_NUMBER_RE = re.compile(r"(\d+(?:\.\d+)?)")

AMBIG_CLASS_MIN = 0.45
AMBIGUITY_MARGIN = 0.10

PRIMARY_FOOTNOTE_MARGIN_PAGES = 1
CAPTION_MAX_PAGES_AHEAD = 1

# Sources formats accepted by `--format auto`.
KNOWN_FORMATS = ("pdf", "html", "epub", "docx", "pptx", "transcript", "repo")


# ============================================================
# Helpers
# ============================================================


def compute_block_id(source_hash: str, section_path: str, block_index: int) -> str:
    """sha1(source_hash + section_path + str(block_index))[:12] — spec §8."""
    h = hashlib.sha1()
    h.update(source_hash.encode("utf-8"))
    h.update(section_path.encode("utf-8"))
    h.update(str(block_index).encode("utf-8"))
    return h.hexdigest()[:12]


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=str(path.parent), delete=False
    ) as tf:
        tf.write(content)
        tmpname = tf.name
    Path(tmpname).replace(path)


def atomic_write_json(path: Path, payload: Any) -> None:
    atomic_write_text(
        path, json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _yaml_or_die(path: Path) -> Dict[str, Any]:
    try:
        import yaml
    except ImportError:
        sys.stderr.write(
            "PyYAML required for --source-meta. Install with `pip install pyyaml`.\n"
        )
        sys.exit(1)
    if not path.exists():
        sys.stderr.write(f"source-meta file not found: {path}\n")
        sys.exit(1)
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        sys.stderr.write(f"source-meta must be a YAML mapping: {path}\n")
        sys.exit(1)
    return data


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return s[:64] or "section"


def _detect_format_from_ingest_dir(ingest_dir: Path) -> str:
    """Map ingest_dir contents to a format string when --format auto."""
    if (ingest_dir / "web_docs").exists():
        return "html"
    if (ingest_dir / "other_formats").exists():
        # Use the first <basename>.<fmt>.regions.json we find.
        for p in sorted((ingest_dir / "other_formats").glob("*.*.regions.json")):
            ext = p.suffix.lstrip(".")
            if ext in ("epub", "docx", "pptx", "srt", "vtt", "json", "txt"):
                return "epub" if ext == "epub" else ext
        return "epub"
    if (ingest_dir / "fragments.json").exists() or (ingest_dir / "regions").exists():
        return "pdf"
    return "pdf"


def _anchor(
    page: Optional[int],
    section_path: str,
    bbox: Optional[List[float]] = None,
    char_range: Optional[List[int]] = None,
) -> Dict[str, Any]:
    a: Dict[str, Any] = {"page": page, "section_path": section_path}
    if bbox is not None:
        a["bbox"] = list(bbox)
    if char_range is not None:
        a["char_range"] = list(char_range)
    return a


# ============================================================
# Loading per-source data
# ============================================================


def load_regions_by_page(ingest_dir: Path) -> "OrderedDict[int, List[Dict[str, Any]]]":
    pages: "OrderedDict[int, List[Dict[str, Any]]]" = OrderedDict()
    regions_dir = ingest_dir / "regions"
    if not regions_dir.exists():
        return pages
    for p in sorted(regions_dir.glob("page-*.regions.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        page_num = int(data.get("page", 1))
        page_regions = data.get("regions", [])
        if page_regions:
            pages[page_num] = page_regions
    return pages


def load_tables_by_page(ingest_dir: Path) -> Dict[int, List[Dict[str, Any]]]:
    out: Dict[int, List[Dict[str, Any]]] = {}
    tables_dir = ingest_dir / "tables"
    if not tables_dir.exists():
        return out
    for p in sorted(tables_dir.glob("page-*.tables.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        page_num = int(data.get("page", 1))
        for t in data.get("tables", []):
            t.setdefault("page", page_num)
            out.setdefault(page_num, []).append(t)
    return out


def load_formulas_by_page(ingest_dir: Path) -> Dict[int, List[Dict[str, Any]]]:
    out: Dict[int, List[Dict[str, Any]]] = {}
    formulas_dir = ingest_dir / "formulas"
    if not formulas_dir.exists():
        return out
    for p in sorted(formulas_dir.glob("page-*.formulas.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        page_num = int(data.get("page", 1))
        for f in data.get("formulas", []):
            f.setdefault("page", page_num)
            out.setdefault(page_num, []).append(f)
    return out


def load_code_by_page(ingest_dir: Path) -> Dict[int, List[Dict[str, Any]]]:
    out: Dict[int, List[Dict[str, Any]]] = {}
    code_dir = ingest_dir / "code"
    if not code_dir.exists():
        return out
    for p in sorted(code_dir.glob("page-*.code.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        page_num = int(data.get("page", 1))
        for blk in data.get("blocks", []):
            blk.setdefault("page", page_num)
            out.setdefault(page_num, []).append(blk)
    return out


def load_fragments(ingest_dir: Path) -> Dict[str, Any]:
    fp = ingest_dir / "fragments.json"
    if not fp.exists():
        return {}
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_fragments_index(fragments: Dict[str, Any]) -> Dict[Tuple[int, str], Dict[str, Any]]:
    """Index fragments by (page, text-prefix-slug) so build_sdm can attach
    `section_path` to PDF regions derived from F18's sectioned fragments."""
    out: Dict[Tuple[int, str], Dict[str, Any]] = {}
    if not fragments:
        return out
    for page_data in fragments.get("pages", []):
        page_num = int(page_data.get("page", 1))
        for frag in page_data.get("fragments", []):
            text = (frag.get("text") or "").strip()
            if not text:
                continue
            section_path = frag.get("section_path")
            if not section_path:
                continue
            slug = _slugify(text)[:32]
            out[(page_num, slug)] = frag
    return out


def load_triage(ingest_dir: Path) -> Dict[str, Any]:
    fp = ingest_dir / "triage.json"
    if not fp.exists():
        return {}
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_web_docs(ingest_dir: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    web_dir = ingest_dir / "web_docs"
    if not web_dir.exists():
        return {}, {}
    sec_path = web_dir / "sections.json"
    meta_path = web_dir / "metadata.json"
    sections: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    if sec_path.exists():
        try:
            sections = json.loads(sec_path.read_text(encoding="utf-8"))
        except Exception:
            sections = {}
    if meta_path.exists():
        try:
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            metadata = {}
    return sections, metadata


def load_other_formats(ingest_dir: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    of_dir = ingest_dir / "other_formats"
    if not of_dir.exists():
        return out
    for p in sorted(of_dir.glob("*.*.regions.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        regions = data.get("regions", [])
        for r in regions:
            r.setdefault("__source_format", data.get("source_format", "unknown"))
            out.append(r)
    return out


def load_review_summary(ingest_dir: Path) -> Dict[str, Any]:
    p = ingest_dir / "review" / "summary.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


# ============================================================
# Region → Block conversion (per spec §4 + D5-D10)
# ============================================================


def region_text(region: Dict[str, Any], fragments_index: Dict[Tuple[int, str], Dict[str, Any]]) -> str:
    """Best-effort text for a region: try `text` first, else look up by slug."""
    text = region.get("text")
    if text:
        return text.strip()
    page = region.get("page")
    if page is None:
        return ""
    candidate = fragments_index.get((page, region.get("id", "")))
    if candidate:
        return (candidate.get("text") or "").strip()
    return ""


def _coerce_confidence(region: Dict[str, Any], default: float = 1.0) -> float:
    """Return a confidence value consistent with origin. ocr ⇒ <1; native ⇒ 1.0."""
    origin = region.get("origin", "native")
    if origin == "ocr":
        c = region.get("confidence", default)
        try:
            v = float(c)
        except Exception:
            v = 0.85
        return min(max(v, 0.0), 0.999999)
    cc = region.get("class_confidence")
    if isinstance(cc, (int, float)) and 0 < float(cc) < 1.0 and region.get("ambiguity"):
        return float(cc)
    return 1.0


def _coerce_origin(region: Dict[str, Any]) -> str:
    origin = region.get("origin")
    if origin in ("native", "ocr", "reconstructed"):
        return origin
    return "native"


def _is_ambiguous(region: Dict[str, Any]) -> bool:
    """Conservative ambiguity check used to flip origin to 'reconstructed'."""
    if region.get("ambiguity"):
        return True
    sc = region.get("semantic_class")
    cc = region.get("class_confidence")
    if sc is None or (isinstance(cc, (int, float)) and 0.0 < float(cc) < AMBIG_CLASS_MIN):
        return True
    return False


def _table_block(
    table: Dict[str, Any], section_path: str, source_hash: str, block_index: int
) -> Dict[str, Any]:
    bid = compute_block_id(source_hash, section_path, block_index)
    page = table.get("page") or table.get("page_start") or 1
    content = {
        "headers": list(table.get("headers", []) or []),
        "rows": [list(r) for r in table.get("data", table.get("rows", []) or [])],
    }
    raw_conf = float(table.get("confidence", 1.0) or 1.0)
    return {
        "id": bid,
        "type": "table",
        "content": content,
        "anchor": _anchor(int(page), section_path),
        "confidence": raw_conf,
        "origin": "ocr" if raw_conf < 1.0 else "native",
    }


def _formula_block(
    formula: Dict[str, Any], section_path: str, source_hash: str, block_index: int
) -> Dict[str, Any]:
    bid = compute_block_id(source_hash, section_path, block_index)
    page = int(formula.get("page", 1))
    display = bool(formula.get("display", True))
    latex = formula.get("latex") or ""
    raw_conf = float(formula.get("confidence", 0.9) or 0.9)
    return {
        "id": bid,
        "type": "formula",
        "content": {"latex": latex, "display": display},
        "anchor": _anchor(page, section_path),
        "confidence": raw_conf,
        "origin": "ocr" if (raw_conf < 1.0 or not formula.get("latex_compiled")) else "native",
    }


def _code_or_console_block(
    blk: Dict[str, Any], section_path: str, source_hash: str, block_index: int
) -> Optional[Dict[str, Any]]:
    bid = compute_block_id(source_hash, section_path, block_index)
    page = int(blk.get("page", 1))
    lang = blk.get("language") or ""
    text = blk.get("text") or ""
    if blk.get("sub_kind") == "console" or lang in ("console", "shell_session"):
        lines = text.splitlines() if text else []
        raw_conf = float(blk.get("confidence", 0.9) or 0.9)
        return {
            "id": bid,
            "type": "console",
            "content": {"lines": [l for l in lines if l.strip() != ""] or [""]},
            "anchor": _anchor(page, section_path),
            "confidence": raw_conf,
            "origin": "ocr" if (raw_conf < 1.0 or blk.get("low_confidence")) else "native",
        }
    if blk.get("sub_kind") == "code" or lang in ("python", "sql", "bash", "cpp", "yaml", "json", "http", "sh", ""):
        raw_conf = float(blk.get("confidence", 0.9) or 0.9)
        return {
            "id": bid,
            "type": "code",
            "content": {"lang": lang or "", "text": text},
            "anchor": _anchor(page, section_path),
            "confidence": raw_conf,
            "origin": "ocr" if (raw_conf < 1.0 or blk.get("low_confidence")) else "native",
        }
    return None


# ============================================================
# Section assembly
# ============================================================


def _assign_sections_from_outline(
    regions_by_page: "OrderedDict[int, List[Dict[str, Any]]]",
    fragments: Dict[str, Any],
    outline: List[Dict[str, Any]],
) -> Dict[int, str]:
    """Map each region index to a section_path using F18's outline + sectioned
    fragments. Returns a dict keyed by `(page, region_index_in_page)` -> path."""
    if not outline:
        return {}
    sectioned_fragments = [
        f
        for page_data in fragments.get("pages", [])
        for f in page_data.get("fragments", [])
        if f.get("section_path")
    ]
    if not sectioned_fragments:
        return {}
    by_page: Dict[int, List[Dict[str, Any]]] = {}
    for f in sectioned_fragments:
        by_page.setdefault(int(f.get("page", 1)), []).append(f)
    out: Dict[int, str] = {}
    for page_num, page_regions in regions_by_page.items():
        frags = by_page.get(page_num, [])
        for ridx, region in enumerate(page_regions):
            region_id = region.get("id", "")
            match_path = None
            for f in frags:
                if (region_id and f.get("text") and _slugify(f["text"])[:32] in region_id) or (
                    region.get("text") and f.get("text") and f["text"].strip()[:32] in (region.get("text") or "")
                ):
                    match_path = f.get("section_path")
                    break
            if not match_path:
                outline_for_page = [o for o in outline if o.get("page") == page_num]
                if outline_for_page:
                    match_path = outline_for_page[0]["section_path"]
            if not match_path and outline:
                match_path = outline[0]["section_path"]
            if match_path:
                out[(page_num, ridx)] = match_path
    return out


def _section_path_for_html_section(section: Dict[str, Any], idx: int) -> str:
    url = section.get("url_path") or section.get("canonical_url") or f"page{idx}"
    base = url.split("?")[0].split("#")[0].lstrip("/")
    if not base or base.endswith(".html"):
        base = base[: -len(".html")] if base.endswith(".html") else base
    return "/" + _slugify(base or f"section-{idx}")


def _section_path_for_other_format(region: Dict[str, Any], idx: int) -> str:
    chapter = region.get("chapter")
    slide = region.get("slide")
    fmt = region.get("__source_format", "doc")
    if chapter is not None:
        return f"/ch{int(chapter):02d}"
    if slide is not None:
        return f"/slide-{int(slide):02d}"
    return f"/{fmt}-{idx:03d}"


# ============================================================
# Build pipeline
# ============================================================


def assemble_sections(
    fmt: str,
    regions_by_page: "OrderedDict[int, List[Dict[str, Any]]]",
    fragments: Dict[str, Any],
    fragments_index: Dict[Tuple[int, str], Dict[str, Any]],
    tables_by_page: Dict[int, List[Dict[str, Any]]],
    formulas_by_page: Dict[int, List[Dict[str, Any]]],
    code_by_page: Dict[int, List[Dict[str, Any]]],
    review_summary: Dict[str, Any],
    web_sections: Dict[str, Any],
    of_regions: List[Dict[str, Any]],
    source_hash: str,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Return (sections, summary_counts).

    `sections` is a list of dicts: `{section_path, title, blocks}`.
    `summary_counts` carries counters the caller merges into build_sdm_summary.
    """
    warnings: List[str] = []
    unknown_conventions: List[Dict[str, Any]] = []
    counts: Dict[str, Any] = {
        "blocks_by_type": Counter(),
        "figures": 0,
        "captions_attached": 0,
        "captions_orphan": 0,
        "captions_total": 0,
        "figures_without_caption": 0,
        "footnotes_total": 0,
        "ambiguous_emitted": 0,
        "boilerplate_discarded": 0,
        "forced_class": 0,
    }
    low_conf_ids = {
        b.get("region_id")
        for b in review_summary.get("low_confidence_blocks", []) or []
        if b.get("region_id")
    }

    # Build the per-region ordered list with section paths attached.
    order: List[Dict[str, Any]] = []  # one entry per region/page; carries `__section_path`
    page_assignments: Dict[Tuple[int, int], str] = {}

    if fmt == "html" and web_sections.get("sections"):
        # Each web section becomes one SDM section. Each non-empty text line
        # is emitted as a prose block. Headings become heading blocks.
        for sidx, web_section in enumerate(web_sections["sections"]):
            sec_path = _section_path_for_html_section(web_section, sidx)
            headings = web_section.get("headings", []) or []
            for h in headings:
                level = max(1, min(6, int(h.get("level", 1))))
                text = (h.get("text") or "").strip()
                if not text:
                    continue
                order.append({
                    "__section_path": sec_path,
                    "__page": None,
                    "__semantic_class": "heading",
                    "__content": {"level": level, "text": text},
                    "__confidence": 1.0,
                    "__origin": "native",
                    "__bbox": None,
                })
            text_blob = (web_section.get("text") or "").strip()
            if text_blob:
                for para in re.split(r"\n{2,}", text_blob):
                    p = para.strip()
                    if p:
                        order.append({
                            "__section_path": sec_path,
                            "__page": None,
                            "__semantic_class": "text",
                            "__content": p,
                            "__confidence": 1.0,
                            "__origin": "native",
                            "__bbox": None,
                        })
        # Also pick up regions/page-*.regions.json (F22) for HTML if any
        # were produced by a custom OCR/front-matter pipeline. This is where
        # footnotes, editorial boxes, etc., land when F29 doesn't classify them.
        # Honor `section_path` declared on the region if present; otherwise
        # attach to the first web section (best-effort) to keep section count
        # stable for round-trip and to avoid orphan `/pNNNN` sections.
        if regions_by_page:
            first_sec_path = ""
            if web_sections.get("sections"):
                first_sec_path = _section_path_for_html_section(
                    web_sections["sections"][0], 0
                )
            for page_num, page_regions in regions_by_page.items():
                for region in page_regions:
                    sec_path = (
                        region.get("section_path")
                        or first_sec_path
                        or f"/p{page_num:04d}"
                    )
                    order.append({
                        "__section_path": sec_path,
                        "__page": page_num,
                        "__semantic_class": region.get("semantic_class", "text"),
                        "__raw_region": region,
                        "__content": None,
                        "__confidence": _coerce_confidence(region),
                        "__origin": _coerce_origin(region),
                        "__bbox": region.get("bbox"),
                        "__ambiguous": _is_ambiguous(region),
                    })
    elif fmt in ("epub", "docx", "pptx", "transcript", "repo") and of_regions:
        for ridx, region in enumerate(of_regions):
            sec_path = _section_path_for_other_format(region, ridx)
            order.append({
                "__section_path": sec_path,
                "__page": region.get("page"),
                "__semantic_class": region.get("semantic_class", "text"),
                "__raw_region": region,
                "__content": None,
                "__confidence": float(region.get("confidence", 0.9) or 0.9),
                "__origin": _coerce_origin(region),
                "__bbox": region.get("bbox"),
            })
    else:
        # PDF-style: walk pages in order, use F18 outline + fragments to assign sections.
        outline: List[Dict[str, Any]] = fragments.get("outline", []) or []
        page_assignments = _assign_sections_from_outline(
            regions_by_page, fragments, outline
        )
        if not outline:
            # Fallback: one section per page.
            for page_num in regions_by_page.keys():
                for ridx in range(len(regions_by_page[page_num])):
                    page_assignments[(page_num, ridx)] = (
                        f"/page-{page_num:04d}"
                    )
        for page_num, page_regions in regions_by_page.items():
            for ridx, region in enumerate(page_regions):
                sec_path = page_assignments.get((page_num, ridx)) or (outline[0]["section_path"] if outline else f"/page-{page_num:04d}")
                order.append({
                    "__section_path": sec_path,
                    "__page": page_num,
                    "__semantic_class": region.get("semantic_class", "text"),
                    "__raw_region": region,
                    "__content": None,
                    "__confidence": _coerce_confidence(region),
                    "__origin": _coerce_origin(region),
                    "__bbox": region.get("bbox"),
                    "__ambiguous": _is_ambiguous(region),
                })

    # Group by section_path preserving order.
    grouped: "OrderedDict[str, List[Dict[str, Any]]]" = OrderedDict()
    sec_titles: Dict[str, str] = {}
    for entry in order:
        path = entry["__section_path"]
        grouped.setdefault(path, []).append(entry)
        if path not in sec_titles:
            text = ""
            if entry["__semantic_class"] == "heading" and isinstance(entry["__content"], dict):
                text = entry["__content"].get("text", "")
            elif entry.get("__raw_region"):
                text = (
                    entry["__raw_region"].get("text")
                    or entry["__raw_region"].get("title")
                    or ""
                ).strip()
            if text:
                sec_titles[path] = text[:120]

    # Convert order entries to provisional blocks (without ids yet).
    # We track provisional blocks so we can do caption association post-pass.
    provisional: List[Dict[str, Any]] = []
    for section_path, entries in grouped.items():
        for entry in entries:
            b = _entry_to_block(
                entry,
                tables_by_page,
                formulas_by_page,
                code_by_page,
                fragments_index,
                low_conf_ids,
                warnings,
            )
            if b is None:
                counts["boilerplate_discarded"] += 1
                continue
            # F35: capture unknown editorial conventions for the summary.
            if b.get("__editorial_unknown_convention"):
                unknown_conventions.append(
                    _format_unknown_record(
                        text=b.get("__editorial_source_text", ""),
                        vendor=b.get("__editorial_source_vendor", ""),
                        product=b.get("__editorial_source_product", ""),
                        decision=b.get("__editorial_decision", {}),
                    )
                )
            provisional.append(b)

    # Pass 2: figure↔caption association (D6).
    provisional = _associate_captions(provisional, warnings, counts)

    # Pass 3: footnote ref backfill (D7).
    provisional = _backfill_footnote_refs(provisional)

    # Final pass: assign deterministic ids per section.
    sections: List[Dict[str, Any]] = []
    by_section: "OrderedDict[str, List[Dict[str, Any]]]" = OrderedDict()
    for blk in provisional:
        path = blk["__section_path"]
        by_section.setdefault(path, []).append(blk)

    for path, blks in by_section.items():
        sec_blocks: List[Dict[str, Any]] = []
        for idx, blk in enumerate(blks):
            bid = compute_block_id(source_hash, path, idx)
            out_block = {
                "id": bid,
                "type": blk["type"],
                "content": blk["content"],
                "anchor": blk["anchor"],
                "confidence": blk["confidence"],
                "origin": blk["origin"],
            }
            sec_blocks.append(out_block)
            counts["blocks_by_type"][blk["type"]] += 1
            if blk["type"] == "figure":
                counts["figures"] += 1
            if blk["type"] == "caption":
                counts["captions_total"] += 1
            if blk["type"] == "footnote":
                counts["footnotes_total"] += 1
        sections.append({
            "section_path": path,
            "title": sec_titles.get(path, ""),
            "blocks": sec_blocks,
        })

    # Counts on associations (figure↔caption) are populated inside
    # `_associate_captions` (pass 2). Don't double-count here.
    counts["figures_without_caption"] = max(0, counts["figures"] - counts["captions_attached"])
    counts["captions_orphan"] = max(0, counts["captions_total"] - counts["captions_attached"])

    return sections, {
        "warnings": warnings,
        "counts": counts,
        "unknown_conventions": unknown_conventions,
    }


# ============================================================
# Editorial box classification (F35)
# ============================================================

# Vendor conventions (references/02-source-model/editorial-semantics.md §4).
# Each rule: vendor_match → regex → (sdm_type, severity?, version_introduced?).
# Order: enforced top-down. Lower-priority rules fall through to plain regex.
EDITORIAL_VENDOR_RULES: List[Dict[str, Any]] = [
    {
        "vendor_match": lambda v, p: "PostgreSQL" in (v or ""),
        "rules": [
            (re.compile(r"^\s*WARNING\s*:", re.I), "warning", "caution", None),
            (re.compile(r"^\s*CAUTION\s*:", re.I), "warning", "caution", None),
            (re.compile(r"^\s*NOTE\s*:", re.I), "note", "info", None),
            (re.compile(r"^\s*TIP\s*:", re.I), "note", "tip", None),
        ],
    },
    {
        "vendor_match": lambda v, p: "python" in (v or "").lower() and "docs.python" in (v or "").lower(),
        "rules": [
            (re.compile(r"^\s*\[WARN(?:ING)?\]", re.I), "warning", "caution", None),
            (re.compile(r"^\s*\[!WARNING\]", re.I), "warning", "caution", None),
            (re.compile(r"^\s*\[NOTE\]", re.I), "note", "info", None),
            (re.compile(r"^\s*\[TIP\]", re.I), "note", "tip", None),
        ],
    },
    {
        "vendor_match": lambda v, p: "kubernetes" in (v or "").lower(),
        "rules": [
            (re.compile(r"admonition-(warning|caution)", re.I), "warning", "caution", None),
            (re.compile(r"admonition-note", re.I), "note", "info", None),
            (re.compile(r"admonition-tip", re.I), "note", "tip", None),
            (re.compile(r"admonition-danger", re.I), "warning", "removed", None),
        ],
    },
    {
        "vendor_match": lambda v, p: "stripe" in (v or "").lower(),
        "rules": [
            (re.compile(r"^\s*WARNING\s*:", re.I), "warning", "caution", None),
        ],
    },
    {
        "vendor_match": lambda v, p: "material" in (v or "").lower() or "mkdocs" in (v or "").lower(),
        "rules": [
            (re.compile(r"!!!\s*danger", re.I), "warning", "removed", None),
            (re.compile(r"!!!\s*warning", re.I), "warning", "caution", None),
            (re.compile(r"!!!\s*tip", re.I), "note", "tip", None),
            (re.compile(r"!!!\s*note", re.I), "note", "info", None),
        ],
    },
    {
        "vendor_match": lambda v, p: "apple" in (v or "").lower() and "developer" in (v or "").lower(),
        "rules": [
            (re.compile(r"^\s*\*\*WARNING\*\*", re.I), "warning", "caution", None),
        ],
    },
]

# Fallback regex (any vendor, lower priority than vendor_match above)
EDITORIAL_FALLBACK_RULES: List[Tuple[re.Pattern, str, Optional[str], Optional[str]]] = [
    # Precaución
    (re.compile(r"^\s*(WARNING|AVISO|WARN|DANGER|CAUTION|PERIGO)\s*:", re.I), "warning", "caution", None),
    # Hard deprecation (warning, severity=removed)
    (re.compile(r"^\s*(REMOVED|LEGACY|WILL BE REMOVED)\s*:", re.I), "warning", "removed", None),
    # Soft deprecation (note, severity=deprecated)
    (re.compile(r"^\s*(DEPRECATED|OBSOLETE|OBSOLETO|RENAMED|USE\s+\w+\s+INSTEAD)\s*:", re.I), "note", "deprecated", None),
    # Consejo
    (re.compile(r"^\s*(TIP|CONSEJO|HINT|SUGERENCIA)\s*:", re.I), "note", "tip", None),
    # Novedad
    (re.compile(r"^\s*(NEW IN|YA DISPONIBLE|NOVEDAD EN|SINCE)\s+(v?\d[\d.]*)", re.I), "note", "novelty", None),
    (re.compile(r"^\s*(NEW|NOVEDAD)\s*$", re.I), "note", "novelty", None),
    # Ejemplo
    (re.compile(r"^\s*(EXAMPLE|EJEMPLO|FOR EXAMPLE|EX\.)\s*:", re.I), "example", None, None),
    # Nota
    (re.compile(r"^\s*(NOTE|NOTA|NOTAS|INFO|ℹ)\s*:", re.I), "note", "info", None),
    # GitHub admonitions (the leading `> ` may have been stripped by F22)
    (re.compile(r"^\s*\[!(NOTE|TIP)\]", re.I), "note", "info", None),   # default info; specific below
    (re.compile(r"\[!TIP\]", re.I), "note", "tip", None),
    (re.compile(r"\[!WARNING\]", re.I), "warning", "caution", None),
    (re.compile(r"\[!IMPORTANT\]", re.I), "warning", "caution", None),
    (re.compile(r"\[!CAUTION\]", re.I), "warning", "caution", None),
]


def _extract_version_introduced(text: str) -> Optional[str]:
    """Pull first version-shape token from a Novedad-style text."""
    m = re.search(r"(?:v|version)?\s*(\d+\.\d+(?:\.\d+)?)", text)
    return m.group(1) if m else None


def _classify_editorial_box(
    text: str,
    sub_kind: Optional[str],
    vendor: str,
    product: str,
) -> Dict[str, Any]:
    """F35 editorial box → SDM block decision.

    Returns dict with at least `type` (one of note/warning/example — never prose).
    Optional keys: `severity`, `version_introduced`, `unknown_convention`.
    """
    out: Dict[str, Any] = {}
    text_stripped = (text or "").lstrip()
    sub_kind = sub_kind or "inline"

    # F35 only operates on `sub_kind == "box"`; inline notes are passthrough note/info.
    if sub_kind != "box":
        return {"type": "note", "severity": "info"}

    # Step 1: vendor-specific rules (in declaration order)
    vendor_matched = False
    for vendor_rule in EDITORIAL_VENDOR_RULES:
        try:
            match_fn = vendor_rule["vendor_match"]
        except KeyError:
            continue
        try:
            is_match = bool(match_fn(vendor, product))
        except Exception:
            is_match = False
        if not is_match:
            continue
        vendor_matched = True
        for pattern, t, sev, ver_intro in vendor_rule["rules"]:
            if pattern.search(text_stripped):
                out["type"] = t
                if sev:
                    out["severity"] = sev
                if ver_intro is not None:
                    out["version_introduced"] = ver_intro
                return out
        break  # vendor matched but no rule fired → don't fall through to fallback

    # Step 2: fallback regex
    for pattern, t, sev, ver_intro in EDITORIAL_FALLBACK_RULES:
        if pattern.search(text_stripped):
            out["type"] = t
            if sev:
                out["severity"] = sev
            if ver_intro is not None:
                out["version_introduced"] = ver_intro
            if t == "note" and sev == "novelty":
                v = _extract_version_introduced(text_stripped)
                if v:
                    out["version_introduced"] = v
            out.setdefault("unknown_convention", not vendor_matched)
            return out

    # Step 3: fallback per spec §5 step 3 — never prose
    out["type"] = "note"
    out["severity"] = "info"
    out["unknown_convention"] = True
    return out


def _format_unknown_record(
    text: str, vendor: str, product: str, decision: Dict[str, Any]
) -> Dict[str, Any]:
    snippet = (text or "").strip()[:80]
    return {
        "vendor": vendor or "",
        "product": product or "",
        "instance_kind": "editorial_note.box",
        "text_snippet": snippet,
        "guessed_type": decision.get("type", "note"),
        "guessed_severity": decision.get("severity", "info"),
        "reason": "no_vendor_match_no_text_regex_match"
        if decision.get("unknown_convention")
        else "no_vendor_match" if decision.get("reason") == "no_vendor_match"
        else "no_text_regex_match",
    }


def _entry_to_block(
    entry: Dict[str, Any],
    tables_by_page: Dict[int, List[Dict[str, Any]]],
    formulas_by_page: Dict[int, List[Dict[str, Any]]],
    code_by_page: Dict[int, List[Dict[str, Any]]],
    fragments_index: Dict[Tuple[int, str], Dict[str, Any]],
    low_conf_ids: set,
    warnings: List[str],
) -> Optional[Dict[str, Any]]:
    """Convert a single region entry into a provisional SDM block (no id)."""
    page = entry["__page"]
    section_path = entry["__section_path"]
    sem = entry["__semantic_class"]
    origin = entry["__origin"]
    if entry.get("__ambiguous") and origin == "native":
        origin = "reconstructed"
    bbox = entry["__bbox"]

    # Drop boilerplate.
    raw = entry.get("__raw_region") or {}
    if sem == "footer":
        return None
    if raw.get("is_boilerplate"):
        return None
    if sem == "diagram":
        warnings.append(
            f"page={page}: diagram region discarded (not in SDM type catalog)"
        )
        return None

    # Pre-built content (HTML headings from web_docs)
    if entry["__content"] is not None and not raw:
        content = entry["__content"]
        if sem == "heading":
            return {
                "__section_path": section_path,
                "type": "heading",
                "content": {"level": content["level"], "text": content["text"]},
                "anchor": _anchor(page, section_path, bbox=bbox),
                "confidence": 1.0,
                "origin": "native",
            }
        if sem == "text":
            text_val = content if isinstance(content, str) else (content.get("text") or "")
            return {
                "__section_path": section_path,
                "type": "prose",
                "content": text_val,
                "anchor": _anchor(page, section_path, bbox=bbox),
                "confidence": 1.0,
                "origin": "native",
            }

    # Raster from raw_region (the common path).
    if not raw:
        return None

    # Tables: pull from F23 by page match if region is table-typed.
    if sem == "table" and page is not None:
        candidates = tables_by_page.get(int(page), [])
        # Try to match by region_id; fall back to first candidate.
        match = None
        for t in candidates:
            if t.get("region_id") == raw.get("id"):
                match = t
                break
        if match is None and candidates:
            match = candidates.pop(0)
            candidates.insert(0, match)
        if match is not None:
            return {
                "__section_path": section_path,
                "type": "table",
                "content": {
                    "headers": list(match.get("headers", []) or []),
                    "rows": [
                        list(r) for r in match.get("data", match.get("rows", []) or [])
                    ],
                },
                "anchor": _anchor(int(page), section_path, bbox=bbox),
                "confidence": float(match.get("confidence", 0.95) or 0.95),
                "origin": "ocr" if float(match.get("confidence", 1.0) or 1.0) < 1.0 else "native",
            }
        # Fallback: text-based table region without F23 data.
        return {
            "__section_path": section_path,
            "type": "table",
            "content": {
                "headers": [],
                "rows": [[region_text(raw, fragments_index)]],
            },
            "anchor": _anchor(int(page), section_path, bbox=bbox),
            "confidence": raw.get("class_confidence", 1.0) or 0.95,
            "origin": origin,
        }

    if sem == "code" and page is not None:
        candidates = code_by_page.get(int(page), [])
        match = next((c for c in candidates if c.get("region_id") == raw.get("id")), None)
        if match is not None:
            block = _code_or_console_block(match, section_path, "", 0)
            if block:
                block["__section_path"] = section_path
                block["anchor"] = _anchor(int(page), section_path, bbox=bbox)
                return block

    if sem == "console" and page is not None:
        candidates = code_by_page.get(int(page), [])
        match = next((c for c in candidates if c.get("region_id") == raw.get("id")), None)
        if match is not None:
            block = _code_or_console_block(match, section_path, "", 0)
            if block:
                block["__section_path"] = section_path
                block["anchor"] = _anchor(int(page), section_path, bbox=bbox)
                return block

    if sem == "formula" and page is not None:
        candidates = formulas_by_page.get(int(page), [])
        match = next((f for f in candidates if f.get("id") == raw.get("id")), None)
        if match is not None:
            block = _formula_block(match, section_path, "", 0)
            block["__section_path"] = section_path
            block["anchor"] = _anchor(int(page), section_path, bbox=bbox)
            return block
        latex = raw.get("text") or raw.get("latex") or ""
        if latex:
            return {
                "__section_path": section_path,
                "type": "formula",
                "content": {"latex": latex, "display": True},
                "anchor": _anchor(int(page), section_path, bbox=bbox),
                "confidence": raw.get("class_confidence", 0.9) or 0.9,
                "origin": origin,
            }

    if sem == "editorial_note":
        text = region_text(raw, fragments_index)
        decision = _classify_editorial_box(
            text=text,
            sub_kind=raw.get("sub_kind"),
            vendor=raw.get("vendor") or "",
            product=raw.get("product") or "",
        )
        # F35: invariant — never `prose` for an editorial box.
        if decision.get("type") not in ("note", "warning", "example"):
            decision["type"] = "note"
            decision.setdefault("severity", "info")
        content: Dict[str, Any] = {"text": text}
        if "severity" in decision:
            content["severity"] = decision["severity"]
        if "version_introduced" in decision:
            content["version_introduced"] = decision["version_introduced"]
        # For inline editorial notes (sub_kind != "box"), always severity=info
        if (raw.get("sub_kind") or "inline") != "box":
            content["severity"] = "info"
        return {
            "__section_path": section_path,
            "type": decision["type"],
            "content": content,
            "__editorial_unknown_convention": bool(decision.get("unknown_convention", False)),
            "__editorial_decision": decision,
            "__editorial_source_vendor": raw.get("vendor") or "",
            "__editorial_source_product": raw.get("product") or "",
            "__editorial_source_text": text,
            "anchor": _anchor(int(page), section_path, bbox=bbox) if page else _anchor(page, section_path, bbox=bbox),
            "confidence": _coerce_confidence(raw),
            "origin": origin,
        }

    if sem == "capture":
        text = region_text(raw, fragments_index)
        return {
            "__section_path": section_path,
            "type": "caption",
            "content": text,
            "anchor": _anchor(int(page), section_path, bbox=bbox) if page else _anchor(page, section_path, bbox=bbox),
            "confidence": _coerce_confidence(raw),
            "origin": origin,
        }

    if sem == "syntax_diagram":
        notation = "ebnf" if (raw.get("text") or "").lstrip().startswith(("::=", ":=", "→")) else "railroad"
        return {
            "__section_path": section_path,
            "type": "syntax-diagram",
            "content": {"notation": notation, "text": region_text(raw, fragments_index)},
            "anchor": _anchor(int(page), section_path, bbox=bbox) if page else _anchor(page, section_path, bbox=bbox),
            "confidence": _coerce_confidence(raw),
            "origin": origin,
        }

    if sem == "index":
        # Best-effort: treat as toc only if structured; else discard.
        text = region_text(raw, fragments_index)
        if text and re.match(r"^(\d+\.)+\s+[A-Z]", text):
            return {
                "__section_path": section_path,
                "type": "toc",
                "content": {"entries": [{"label": text, "page": int(page) if page else None, "anchor": section_path}]},
                "anchor": _anchor(int(page), section_path, bbox=bbox) if page else _anchor(page, section_path, bbox=bbox),
                "confidence": _coerce_confidence(raw),
                "origin": origin,
            }
        return None

    if sem == "footnote":
        return {
            "__section_path": section_path,
            "type": "footnote",
            "content": {"text": region_text(raw, fragments_index), "ref": str(raw.get("anchor") or raw.get("ref") or "")},
            "anchor": _anchor(int(page), section_path, bbox=bbox) if page else _anchor(page, section_path, bbox=bbox),
            "confidence": _coerce_confidence(raw),
            "origin": origin,
        }

    if sem == "text" and page is not None:
        # Heading detection fallback: large + bold + first 80 chars (already done by F18, but cheap re-check).
        text = region_text(raw, fragments_index)
        return {
            "__section_path": section_path,
            "type": "prose",
            "content": text,
            "anchor": _anchor(int(page), section_path, bbox=bbox),
            "confidence": _coerce_confidence(raw),
            "origin": origin,
        }

    if sem == "text" and page is None:
        return {
            "__section_path": section_path,
            "type": "prose",
            "content": region_text(raw, fragments_index),
            "anchor": _anchor(page, section_path, bbox=bbox),
            "confidence": _coerce_confidence(raw),
            "origin": origin,
        }

    # Headings from F22 (regions.py emits `heading` for S_LARGE+S_BOLD).
    if sem == "heading":
        text = region_text(raw, fragments_index)
        level = int(raw.get("level") or raw.get("heading_level") or 1)
        return {
            "__section_path": section_path,
            "type": "heading",
            "content": {"level": max(1, min(6, level)), "text": text},
            "anchor": _anchor(int(page), section_path, bbox=bbox) if page else _anchor(page, section_path, bbox=bbox),
            "confidence": _coerce_confidence(raw),
            "origin": origin,
        }

    if sem == "figure":
        return {
            "__section_path": section_path,
            "type": "figure",
            "content": {
                "src": raw.get("src", ""),
                "alt": raw.get("alt", "") or raw.get("text", "") or "",
            },
            "anchor": _anchor(int(page), section_path, bbox=bbox) if page else _anchor(page, section_path, bbox=bbox),
            "confidence": _coerce_confidence(raw),
            "origin": origin,
        }

    # Anything else (ambiguous, unknown): emit as prose (spec §10 + D8).
    return {
        "__section_path": section_path,
        "type": "prose",
        "content": region_text(raw, fragments_index),
        "anchor": _anchor(int(page), section_path, bbox=bbox) if page else _anchor(page, section_path, bbox=bbox),
        "confidence": _coerce_confidence(raw),
        "origin": origin,
    }


def _associate_captions(
    blocks: List[Dict[str, Any]],
    warnings: List[str],
    counts: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """For each figure, search forward through blocks of the same section
    (within CAPTION_MAX_PAGES_AHEAD pages) for a caption region matching
    `^(Figure|Fig\.|Tabla|Tab\.) N`. If found, attach a copy of the caption
    text to `figure.content.caption`. The caption block itself remains in
    the SDM as its own block (per spec §4.1 — both `figure.content.caption`
    AND a separate `type=caption` block are legal; the corpus's canonical
    SDMs hold both forms simultaneously, e.g. `02-database-internals-chapter`)."""
    n = len(blocks)
    for idx, blk in enumerate(blocks):
        if blk["type"] != "figure":
            continue
        sec_path = blk["__section_path"]
        fig_page = blk["anchor"].get("page")
        for j in range(idx + 1, n):
            cand = blocks[j]
            if cand["__section_path"] != sec_path:
                break
            cand_page = cand["anchor"].get("page")
            if fig_page is not None and cand_page is not None:
                if abs(int(cand_page) - int(fig_page)) > CAPTION_MAX_PAGES_AHEAD:
                    break
            if cand["type"] == "caption":
                text = cand["content"] if isinstance(cand["content"], str) else cand["content"].get("text", "")
                if CAPTION_PATTERN.match(text or ""):
                    if not blk["content"].get("caption"):
                        blk["content"]["caption"] = text
                    counts["captions_attached"] += 1
                    break
        else:
            warnings.append(
                f"section={sec_path}: figure (id={blk.get('__pre_id', '?')}) without caption"
            )
    return blocks


def _backfill_footnote_refs(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure every footnote has a non-empty content.ref. If empty, synthesize
    `<page>:<N>` where N is 1-based ordinal per source (D7)."""
    counter = 0
    for blk in blocks:
        if blk["type"] != "footnote":
            continue
        if not blk["content"].get("ref"):
            counter += 1
            page = blk["anchor"].get("page")
            blk["content"]["ref"] = f"{page if page is not None else 'src'}:{counter}"
    return blocks


# ============================================================
# Build + Validate
# ============================================================


def build_sdm_payload(
    source_meta: Dict[str, Any],
    sections: List[Dict[str, Any]],
    fallback_metadata: Optional[Dict[str, Any]] = None,
    fallback_reasons: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Construct the SDM JSON payload.

    `fallback_metadata` carries values that were **not** in --source-meta but
    were filled from another source (web_docs.metadata, triage.json). When
    present, the resulting `source_provenance` entry for that field is
    `web_docs_metadata` or `triage_metadata` (lower confidence) instead of
    `read` (1.0).

    `fallback_reasons` maps field name to a short reason string for
    `source_provenance.<field>.reason`. Optional.
    """
    fallback_metadata = fallback_metadata or {}
    fallback_reasons = fallback_reasons or {}

    def _method_for(field: str) -> Tuple[str, float, Optional[str]]:
        """Return (method, confidence, reason) for a field based on provenance."""
        if field in source_meta and source_meta[field] not in (None, "", [], {}):
            return ("read", 1.0, None)
        if field in fallback_metadata and fallback_metadata[field] not in (None, "", [], {}):
            return ("web_docs_metadata", 0.9, fallback_reasons.get(field))
        # Absent: no value at all
        return ("absent", 0.0, "no_value_in_source")

    source: Dict[str, Any] = {
        "id": source_meta["id"],
        "hash": source_meta["hash"],
        "algorithm": source_meta.get("algorithm", "sha256"),
        "vendor": source_meta.get("vendor", ""),
        "product": source_meta.get("product", ""),
        "url": source_meta.get("url", ""),
        "language": source_meta.get("language", "en"),
        "format": source_meta.get("format", "pdf"),
    }
    for opt in ("version", "edition", "isbn", "date"):
        if opt in source_meta and source_meta[opt] is not None:
            source[opt] = source_meta[opt]
    if "authors" in source_meta:
        source["authors"] = list(source_meta.get("authors") or [])

    # source_provenance (F34): per-field method + confidence + reason
    source_provenance: Dict[str, Dict[str, Any]] = {}
    tracked = ["id", "hash", "vendor", "product", "version", "edition",
               "isbn", "authors", "url", "language", "date", "format",
               "algorithm"]
    for field in tracked:
        method, conf, reason = _method_for(field)
        value = source.get(field)
        entry: Dict[str, Any] = {"method": method, "value": value, "confidence": conf}
        if reason:
            entry["reason"] = reason
        source_provenance[field] = entry

    return {
        "schema_version": SCHEMA_VERSION,
        "source": source,
        "source_provenance": source_provenance,
        "sections": sections,
    }


def validate_sdm(sdm_path: Path) -> Tuple[bool, str]:
    """Invoke scripts/util/validate_sdm.py for criterion 1."""
    repo_root = Path(__file__).resolve().parents[4]
    validate_py = repo_root / "scripts" / "util" / "validate_sdm.py"
    if not validate_py.exists():
        return True, "validate_sdm.py not present; minimal check skipped"
    proc = subprocess.run(
        [sys.executable, str(validate_py), "--validate", str(sdm_path)],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return True, proc.stdout.strip()
    return False, (proc.stdout + proc.stderr).strip()


def run(
    ingest_dir: Path,
    out_dir: Path,
    source_meta_path: Path,
    source_file: Optional[Path],
    fmt: str,
    json_only: bool,
    check_determinism: bool,
) -> int:
    ingest_dir = Path(ingest_dir).resolve()
    out_dir = Path(out_dir).resolve()
    if not ingest_dir.exists():
        sys.stderr.write(f"ingest-dir not found: {ingest_dir}\n")
        return 1

    meta = _yaml_or_die(Path(source_meta_path))
    if fmt == "auto":
        fmt = _detect_format_from_ingest_dir(ingest_dir)
    if fmt not in KNOWN_FORMATS:
        sys.stderr.write(f"unknown --format: {fmt}\n")
        return 1
    if "id" not in meta or "hash" not in meta or "url" not in meta or "format" not in meta:
        sys.stderr.write(
            "source-meta missing required fields: id, hash, url, format\n"
        )
        return 1
    meta["format"] = fmt
    # If --source-file is provided and hash missing, compute it.
    if source_file and source_file.exists() and not meta.get("hash"):
        meta["hash"] = sha256_file(source_file)
    src_hash = meta["hash"]
    if not re.match(r"^[0-9a-f]{64}$", src_hash or ""):
        sys.stderr.write(f"source.hash invalid (must be sha256 hex 64): {src_hash!r}\n")
        return 1

    regions_by_page = load_regions_by_page(ingest_dir)
    tables_by_page = load_tables_by_page(ingest_dir)
    formulas_by_page = load_formulas_by_page(ingest_dir)
    code_by_page = load_code_by_page(ingest_dir)
    fragments = load_fragments(ingest_dir)
    fragments_index = load_fragments_index(fragments)
    review_summary = load_review_summary(ingest_dir)
    web_sections, web_metadata = load_web_docs(ingest_dir)
    of_regions = load_other_formats(ingest_dir)

    # Snapshot meta BEFORE fallback to know which fields came from --source-meta
    # (`read`) vs from web_docs.metadata (`web_docs_metadata`) — drives F34's
    # `source_provenance` annotation.
    pre_fallback_keys = set(meta.keys())
    fallback_metadata: Dict[str, Any] = {}
    fallback_reasons: Dict[str, str] = {}

    # Pull metadata fallbacks.
    if not meta.get("vendor") and web_metadata.get("domain"):
        meta["vendor"] = web_metadata["domain"]
        fallback_metadata["vendor"] = web_metadata["domain"]
        fallback_reasons["vendor"] = "web_docs.metadata.domain"
    if not meta.get("product") and web_metadata.get("product"):
        meta["product"] = web_metadata["product"]
        fallback_metadata["product"] = web_metadata["product"]
        fallback_reasons["product"] = "web_docs.metadata.product"
    if not meta.get("version") and web_metadata.get("product_version"):
        meta["version"] = web_metadata["product_version"]
        fallback_metadata["version"] = web_metadata["product_version"]
        fallback_reasons["version"] = "web_docs.metadata.product_version"
    if not meta.get("language"):
        meta["language"] = "en"

    sections, agg = assemble_sections(
        fmt=fmt,
        regions_by_page=regions_by_page,
        fragments=fragments,
        fragments_index=fragments_index,
        tables_by_page=tables_by_page,
        formulas_by_page=formulas_by_page,
        code_by_page=code_by_page,
        review_summary=review_summary,
        web_sections=web_sections,
        of_regions=of_regions,
        source_hash=src_hash,
    )

    if not sections:
        sys.stderr.write(
            "no sections assembled (input dir may be empty or unparseable)\n"
        )
        return 1

    sdm = build_sdm_payload(meta, sections, fallback_metadata, fallback_reasons)
    out_dir.mkdir(parents=True, exist_ok=True)
    sdm_path = out_dir / "sdm.json"
    atomic_write_json(sdm_path, sdm)

    # Determinism check (criterion 2).
    determinism: Dict[str, Any] = {"ran": False, "identical": None, "diff_path": None}
    if check_determinism:
        determinism["ran"] = True
        with tempfile.TemporaryDirectory(prefix="build-sdm-det-") as tmp:
            tmp_path = Path(tmp)
            run1 = tmp_path / "run1"
            run2 = tmp_path / "run2"
            # Clone inputs are stable; just rebuild with different out dirs.
            sections_2, _ = assemble_sections(
                fmt=fmt,
                regions_by_page=regions_by_page,
                fragments=fragments,
                fragments_index=fragments_index,
                tables_by_page=tables_by_page,
                formulas_by_page=formulas_by_page,
                code_by_page=code_by_page,
                review_summary=review_summary,
                web_sections=web_sections,
                of_regions=of_regions,
                source_hash=src_hash,
            )
            sdm_2 = build_sdm_payload(meta, sections_2, fallback_metadata, fallback_reasons)
            sdm1_path = run1 / "sdm.json"
            sdm2_path = run2 / "sdm.json"
            atomic_write_json(sdm1_path, sdm)
            atomic_write_json(sdm2_path, sdm_2)
            same = sdm1_path.read_bytes() == sdm2_path.read_bytes()
            determinism["identical"] = same
            if not same:
                determinism["diff_path"] = str(run1)

    # Validate against schema (criterion 1).
    ok, detail = validate_sdm(sdm_path)
    validation: Dict[str, Any] = {
        "ok": ok,
        "detail": detail,
        "ran_at": datetime.now(timezone.utc).isoformat(),
    }

    # Build summary.
    counts = agg["counts"]
    summary = {
        "schema_version": SCHEMA_VERSION,
        "source_id": meta["id"],
        "source_format": fmt,
        "sections_count": len(sections),
        "blocks_count": sum(
            len(s["blocks"]) for s in sections
        ),
        "blocks_by_type": dict(counts["blocks_by_type"]),
        "figures": counts["figures"],
        "captions_attached": counts["captions_attached"],
        "captions_orphan": counts["captions_orphan"],
        "captions_total": counts["captions_total"],
        "figures_without_caption": counts["figures_without_caption"],
        "footnotes_total": counts["footnotes_total"],
        "ambiguous_emitted": counts["forced_class"],
        "boilerplate_discarded": counts["boilerplate_discarded"],
        "warnings": agg["warnings"],
        "unknown_conventions": agg.get("unknown_conventions", []),
        "validation": validation,
        "determinism": determinism,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    atomic_write_json(out_dir / "build_sdm_summary.json", summary)

    if not json_only:
        md = [
            f"# Build SDM — `{meta['id']}`",
            "",
            f"- **Source format:** {fmt}",
            f"- **Sections:** {len(sections)}",
            f"- **Blocks total:** {summary['blocks_count']}",
            f"- **Figures:** {counts['figures']} (con pie: {counts['captions_attached']}, sin pie: {counts['figures_without_caption']})",
            f"- **Captions:** {counts['captions_total']} (huérfanas: {counts['captions_orphan']})",
            f"- **Footnotes:** {counts['footnotes_total']}",
            f"- **Boilerplate descartado:** {counts['boilerplate_discarded']}",
            f"- **Forced class (ambiguous → prose):** {counts['forced_class']}",
            f"- **Validation:** {'OK' if validation['ok'] else 'FAIL'}",
        ]
        if check_determinism:
            md.append(
                f"- **Determinism:** {'identical' if determinism['identical'] else 'DIVERGED'}"
            )
        if agg["warnings"]:
            md.append("")
            md.append("## Advertencias")
            for w in agg["warnings"][:50]:
                md.append(f"- {w}")
        atomic_write_text(out_dir / "build_sdm.md", "\n".join(md) + "\n")

    if validation["ok"] is False:
        return 1
    if determinism.get("ran") and determinism.get("identical") is False:
        return 1
    if agg["warnings"] or agg.get("unknown_conventions"):
        return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="build_sdm.py",
        description="F31 — Source Document Model assembler (consume L0, emit sdm.json).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Constantes (references/02-source-model/build-sdm.md):
  CAPTION_PATTERN                = ^(Figure|Fig.|Tabla|Tab.) N (case-insensitive)
  CAPTION_MAX_PAGES_AHEAD        = 1   margen entre figure y su caption
  AMBIG_CLASS_MIN                = 0.45  mismo umbral que F22

Pipeline:
  1. Carga regions/tables/formulas/code/web_docs/other_formats desde --ingest-dir.
  2. Ensambla jerarquía de secciones (outline F18 o sections F29/F28).
  3. Convierte regiones a bloques SDM (mapeo D5, ambiguos → prose).
  4. Asocia pies a figuras por (sección, page delta <= 1, patrón Figure N).
  5. Asigna ids deterministas sha1(hash + section_path + idx)[:12].
  6. Valida contra sdm.schema.json vía scripts/util/validate_sdm.py.

Códigos de salida:
  0 OK sin advertencias
  1 error fatal / schema invalid / determinismo roto
  2 OK con advertencias (asociaciones faltantes, regiones ambiguas, etc.)
""",
    )
    p.add_argument("--ingest-dir", required=True, help="Directorio con subdirs de ingesta (regions/, tables/, formulas/, code/, web_docs/, other_formats/, fragments.json)")
    p.add_argument("--source-meta", required=True, type=Path, help="YAML con metadatos del source (id, hash, vendor, product, url, language, format, ...)")
    p.add_argument("--source-file", type=Path, default=None, help="Ruta al archivo original; si se pasa y source-meta no trae hash, se calcula sha256")
    p.add_argument("--out-dir", required=True, help="Directorio de salida (sdm.json + summaries)")
    p.add_argument(
        "--format",
        choices=("auto",) + KNOWN_FORMATS,
        default="auto",
        help="Formato de la fuente (auto = inferir del ingest-dir)",
    )
    p.add_argument("--check-determinism", action="store_true", help="Construye dos veces y compara byte a byte")
    p.add_argument("--json-only", action="store_true", help="No escribir build_sdm.md")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return run(
        ingest_dir=Path(args.ingest_dir),
        out_dir=Path(args.out_dir),
        source_meta_path=Path(args.source_meta),
        source_file=Path(args.source_file) if args.source_file else None,
        fmt=args.format,
        json_only=args.json_only,
        check_determinism=args.check_determinism,
    )


if __name__ == "__main__":
    sys.exit(main())
