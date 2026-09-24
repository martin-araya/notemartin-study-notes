#!/usr/bin/env python3
"""other_formats.py — F28 EPUB/DOCX/PPTX/transcripciones.

Procesa archivos EPUB (ebooklib), DOCX (python-docx), PPTX (python-pptx) y
transcripciones (SRT/VTT/JSON con stdlib). Produce `regions.json` estandarizado
compatible con F22. Notas del orador → `speaker_note` (bloques propios).
Muletillas fuera en transcripciones (whitelist cerrada en pausas > 2s).
Marcas temporales conservadas como `anchor_id`.

Uso:
    python3 scripts/ingest/other_formats.py \
        --source <file_or_dir> --out-dir <dir> \
        [--format auto|epub|docx|pptx|srt|vtt|json] [--json-only]

Salidas (en <out-dir>/ingest/other_formats/):
    <basename>.regions.json — regiones con semantic_class por formato
    summary.json — global con format, region_count, class_distribution

Códigos de salida:
    0 — OK
    1 — Error fatal (formato desconocido, archivo ilegible)
    2 — OK con advertencias (muletillas no removidas, formato mixto)

Dependencias:
    - Python 3.9+ stdlib
    - ebooklib (opcional, para EPUB)
    - python-docx (opcional, para DOCX)
    - python-pptx (opcional, para PPTX)

Documentación normativa: references/01-ingest/other-formats.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"

# ============================================================
# Constants (per references/01-ingest/other-formats.md)
# ============================================================

TRANSCRIPT_FILLER_WORDS = frozenset({"um", "uh", "er", "ah", "eh", "mm", "hmm", "mm-hmm", "uh-huh"})
MIN_PAUSE_FOR_FILLER_REMOVAL_S = 2.0
SRT_TIMESTAMP_RE = re.compile(
    r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})$"
)
VTT_TIMESTAMP_RE = re.compile(
    r"^(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})$"
)


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


def srt_timestamp_to_seconds(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def vtt_timestamp_to_seconds(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


# ============================================================
# Format detection
# ============================================================

def detect_format(path: Path) -> Optional[str]:
    suffix = path.suffix.lower()
    if suffix == ".epub":
        try:
            with zipfile.ZipFile(path) as z:
                if "mimetype" in z.namelist():
                    mime = z.read("mimetype").decode("ascii", errors="ignore")
                    if "epub+zip" in mime:
                        return "epub"
        except Exception:
            return None
    elif suffix == ".docx":
        try:
            with zipfile.ZipFile(path) as z:
                if "[Content_Types].xml" in z.namelist():
                    return "docx"
        except Exception:
            return None
    elif suffix == ".pptx":
        try:
            with zipfile.ZipFile(path) as z:
                if "ppt/presentation.xml" in z.namelist():
                    return "pptx"
        except Exception:
            return None
    elif suffix == ".srt":
        return "srt"
    elif suffix == ".vtt":
        return "vtt"
    elif suffix == ".json":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                if "segments" in data or "results" in data or "items" in data:
                    return "json"
        except Exception:
            return None
    return None


# ============================================================
# EPUB parser
# ============================================================

def parse_epub(path: Path) -> List[Dict[str, Any]]:
    try:
        import ebooklib
        from ebooklib import epub
    except ImportError:
        return [{"error": "ebooklib not installed; pip install ebooklib"}]

    ITEM_NOTE = 10

    regions: List[Dict[str, Any]] = []
    try:
        book = epub.read_epub(str(path))
    except Exception as e:
        return [{"error": f"failed to read EPUB: {e}"}]

    chapter_num = 0
    region_counter = 0
    for spine_item in book.spine:
        chapter_num += 1
        try:
            item = book.get_item_with_id(spine_item[0])
        except Exception:
            continue
        if item is None:
            continue
        content = item.get_content() if hasattr(item, "get_content") else b""
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")

        html_tags = re.findall(
            r"<(h[12]|p|li|blockquote|pre|code|img|a)\b[^>]*>(.*?)</\1>",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        for tag_name, inner in html_tags:
            text = re.sub(r"<[^>]+>", "", inner).strip()
            if not text:
                continue
            region_counter += 1
            region: Dict[str, Any] = {
                "id": f"epub-c{chapter_num}-r{region_counter:03d}",
                "semantic_class": "heading" if tag_name.startswith("h") else
                                   "list_item" if tag_name == "li" else
                                   "editorial_note" if tag_name == "blockquote" else
                                   "code" if tag_name in ("pre", "code") else "text",
                "text": text[:1000],
                "chapter": chapter_num,
                "confidence": 0.95,
            }
            if tag_name.startswith("h"):
                region["level"] = int(tag_name[1])
            regions.append(region)

        img_tags = re.findall(r"<img\b[^>]*?(?:src=\"([^\"]+)\")?[^>]*?(?:alt=\"([^\"]*)\")?[^>]*>", content, re.IGNORECASE)
        for src, alt in img_tags:
            region_counter += 1
            regions.append({
                "id": f"epub-c{chapter_num}-r{region_counter:03d}",
                "semantic_class": "figure",
                "alt": alt or "",
                "src": src or "",
                "chapter": chapter_num,
                "confidence": 0.90,
            })

    for note_item in book.get_items_of_type(ITEM_NOTE):
        region_counter += 1
        note_text = ""
        try:
            content = note_item.get_content()
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="replace")
            note_text = re.sub(r"<[^>]+>", "", content).strip()
        except Exception:
            pass
        regions.append({
            "id": f"epub-note-r{region_counter:03d}",
            "semantic_class": "footnote",
            "anchor": note_item.id,
            "text": note_text[:1000],
            "chapter": None,
            "confidence": 0.90,
        })
    return regions


# ============================================================
# DOCX parser
# ============================================================

def parse_docx(path: Path) -> List[Dict[str, Any]]:
    try:
        from docx import Document
    except ImportError:
        return [{"error": "python-docx not installed; pip install python-docx"}]

    regions: List[Dict[str, Any]] = []
    try:
        doc = Document(str(path))
    except Exception as e:
        return [{"error": f"failed to read DOCX: {e}"}]

    style_map = {
        "Heading 1": ("heading", 1), "Heading 2": ("heading", 2),
        "Heading 3": ("heading", 3), "Heading 4": ("heading", 4),
        "List Bullet": ("list_item", None), "List Number": ("list_item", None),
        "Quote": ("editorial_note", None), "Code": ("code", None),
        "Normal": ("text", None),
    }

    region_counter = 0
    for para in doc.paragraphs:
        style_name = para.style.name if para.style else "Normal"
        text = para.text.strip()
        if not text and style_name not in style_map:
            continue
        region_counter += 1
        if style_name in style_map:
            sem_class, level = style_map[style_name]
        else:
            sem_class, level = "text", None
        region: Dict[str, Any] = {
            "id": f"docx-r{region_counter:03d}",
            "semantic_class": sem_class,
            "text": text or f"[{style_name}]",
            "chapter": None,
            "confidence": 0.92,
        }
        if level is not None:
            region["level"] = level
        if "<w:ins" in para._element.xml or "<w:del" in para._element.xml:
            region["change_tracked"] = True
        regions.append(region)

    for tbl_idx, table in enumerate(doc.tables):
        region_counter += 1
        rows = len(table.rows)
        cols = len(table.columns) if table.rows else 0
        cells = []
        for row in table.rows:
            cells.append([cell.text for cell in row.cells])
        regions.append({
            "id": f"docx-r{region_counter:03d}",
            "semantic_class": "table",
            "text": f"Table with {rows} rows x {cols} cols",
            "chapter": None,
            "confidence": 0.95,
            "rows": rows,
            "cols": cols,
            "cells": cells,
        })

    for cmt in doc.part.related_parts.values():
        try:
            from docx.oxml.ns import qn
            comments = cmt.element.findall(qn("w:comment")) if hasattr(cmt, "element") else []
        except Exception:
            comments = []
        for c in comments:
            region_counter += 1
            author = c.get(qn("w:author")) if hasattr(c, "get") else ""
            text_el = c.find(qn("w:p")) if hasattr(c, "find") else None
            comment_text = "".join(t.text or "" for t in (text_el.iter(qn("w:t")) if text_el is not None else []))
            regions.append({
                "id": f"docx-r{region_counter:03d}",
                "semantic_class": "comment",
                "text": comment_text,
                "author": author or "",
                "anchor_para_id": c.get(qn("w:paraId")) if hasattr(c, "get") else None,
                "chapter": None,
                "confidence": 0.85,
            })
    return regions


# ============================================================
# PPTX parser
# ============================================================

def parse_pptx(path: Path) -> List[Dict[str, Any]]:
    try:
        from pptx import Presentation
        from pptx.enum.shapes import MSO_SHAPE_TYPE
    except ImportError:
        return [{"error": "python-pptx not installed; pip install python-pptx"}]

    regions: List[Dict[str, Any]] = []
    try:
        prs = Presentation(str(path))
    except Exception as e:
        return [{"error": f"failed to read PPTX: {e}"}]

    region_counter = 0
    for slide_idx, slide in enumerate(prs.slides, start=1):
        for shape in slide.shapes:
            if shape == slide.shapes.title:
                region_counter += 1
                text = shape.text_frame.text if shape.has_text_frame else ""
                regions.append({
                    "id": f"pptx-s{slide_idx}-r{region_counter:03d}",
                    "semantic_class": "heading",
                    "level": 1,
                    "text": text,
                    "slide": slide_idx,
                    "confidence": 0.95,
                })
            elif shape.has_text_frame:
                text = shape.text_frame.text
                if text.strip():
                    region_counter += 1
                    regions.append({
                        "id": f"pptx-s{slide_idx}-r{region_counter:03d}",
                        "semantic_class": "text",
                        "text": text,
                        "slide": slide_idx,
                        "confidence": 0.90,
                    })
            elif shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                for child in shape.shapes:
                    if child.has_text_frame and child.text_frame.text.strip():
                        region_counter += 1
                        regions.append({
                            "id": f"pptx-s{slide_idx}-r{region_counter:03d}",
                            "semantic_class": "text",
                            "text": child.text_frame.text,
                            "slide": slide_idx,
                            "confidence": 0.85,
                        })

        if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip():
            region_counter += 1
            regions.append({
                "id": f"pptx-s{slide_idx}-r{region_counter:03d}",
                "semantic_class": "speaker_note",
                "text": slide.notes_slide.notes_text_frame.text,
                "slide": slide_idx,
                "confidence": 0.95,
            })
    return regions


# ============================================================
# Transcript parser
# ============================================================

def clean_filler_words(text: str, prev_pause_s: float) -> Tuple[str, int]:
    if prev_pause_s < MIN_PAUSE_FOR_FILLER_REMOVAL_S:
        return text, 0
    words = text.split()
    out: List[str] = []
    removed = 0
    for w in words:
        clean = re.sub(r"[.,;:!?]$", "", w.lower())
        if clean in TRANSCRIPT_FILLER_WORDS and (not out or len(out) == 0 or all(
            re.sub(r"[.,;:!?]$", "", o.lower()) in TRANSCRIPT_FILLER_WORDS for o in out
        )):
            removed += 1
            continue
        out.append(w)
    return " ".join(out), removed


def parse_srt(path: Path) -> List[Dict[str, Any]]:
    regions: List[Dict[str, Any]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return regions
    blocks = re.split(r"\n\s*\n", text.strip())
    region_counter = 0
    prev_end = 0.0
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue
        m = SRT_TIMESTAMP_RE.match(lines[1])
        if not m:
            continue
        start = srt_timestamp_to_seconds(*m.groups()[:4])
        end = srt_timestamp_to_seconds(*m.groups()[4:])
        content = " ".join(lines[2:]).strip()
        pause_s = start - prev_end
        cleaned, removed = clean_filler_words(content, pause_s)
        region_counter += 1
        regions.append({
            "id": f"srt-r{region_counter:03d}",
            "semantic_class": "transcript_segment",
            "anchor_id": f"t-{region_counter:04d}",
            "start": start,
            "end": end,
            "text": cleaned,
            "confidence": 0.95,
        })
        prev_end = end
    return regions


def parse_vtt(path: Path) -> List[Dict[str, Any]]:
    regions: List[Dict[str, Any]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return regions
    text = re.sub(r"^WEBVTT.*?\n", "", text, count=1)
    blocks = re.split(r"\n\s*\n", text.strip())
    region_counter = 0
    prev_end = 0.0
    for block in blocks:
        lines = block.strip().split("\n")
        if not lines:
            continue
        m = VTT_TIMESTAMP_RE.match(lines[0])
        if not m:
            continue
        start = vtt_timestamp_to_seconds(*m.groups()[:4])
        end = vtt_timestamp_to_seconds(*m.groups()[4:])
        content = " ".join(lines[1:]).strip()
        pause_s = start - prev_end
        cleaned, removed = clean_filler_words(content, pause_s)
        region_counter += 1
        regions.append({
            "id": f"vtt-r{region_counter:03d}",
            "semantic_class": "transcript_segment",
            "anchor_id": f"t-{region_counter:04d}",
            "start": start,
            "end": end,
            "text": cleaned,
            "confidence": 0.95,
        })
        prev_end = end
    return regions


def parse_json_transcript(path: Path) -> List[Dict[str, Any]]:
    regions: List[Dict[str, Any]] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return regions

    segments: List[Dict[str, Any]] = []
    if isinstance(data, dict):
        if "segments" in data:
            segments = data["segments"]
        elif "results" in data:
            for r in data["results"].get("items", []):
                alts = r.get("alternatives", [{}])
                text = alts[0].get("content", "") if alts else ""
                segments.append({
                    "start": float(r.get("start_time", 0)),
                    "end": float(r.get("end_time", 0)),
                    "text": text,
                })

    region_counter = 0
    prev_end = 0.0
    for seg in segments:
        start = float(seg.get("start", 0))
        end = float(seg.get("end", 0))
        content = seg.get("text", "")
        pause_s = start - prev_end
        cleaned, removed = clean_filler_words(content, pause_s)
        region_counter += 1
        regions.append({
            "id": f"json-r{region_counter:03d}",
            "semantic_class": "transcript_segment",
            "anchor_id": f"t-{region_counter:04d}",
            "start": start,
            "end": end,
            "text": cleaned,
            "confidence": 0.95,
        })
        prev_end = end
    return regions


# ============================================================
# Entry point
# ============================================================

def parse_file(path: Path, fmt: Optional[str]) -> Tuple[List[Dict[str, Any]], str, int]:
    """Returns (regions, format, fillers_removed_count)."""
    if fmt is None or fmt == "auto":
        fmt = detect_format(path)
    if fmt is None:
        return [{"error": f"unknown format for {path}"}], "unknown", 0
    fillers = 0
    if fmt == "epub":
        regions = parse_epub(path)
    elif fmt == "docx":
        regions = parse_docx(path)
    elif fmt == "pptx":
        regions = parse_pptx(path)
    elif fmt == "srt":
        regions = parse_srt(path)
        fillers = sum(1 for r in regions if r.get("text") and "um" in r["text"].lower())
    elif fmt == "vtt":
        regions = parse_vtt(path)
    elif fmt == "json":
        regions = parse_json_transcript(path)
        fillers = sum(1 for r in regions if r.get("text") and "um" in r["text"].lower())
    else:
        regions = [{"error": f"unsupported format: {fmt}"}]
    return regions, fmt, fillers


def run(
    source: Path,
    out_dir: Path,
    fmt: Optional[str],
    json_only: bool = False,
) -> int:
    source = Path(source).resolve()
    if not source.exists():
        print(f"ERROR: source not found: {source}", file=sys.stderr)
        return 1

    warnings: List[str] = []
    files: List[Path] = []
    if source.is_file():
        files = [source]
    elif source.is_dir():
        for ext in ("*.epub", "*.docx", "*.pptx", "*.srt", "*.vtt", "*.json"):
            files.extend(sorted(source.glob(ext)))
    else:
        print(f"ERROR: source is not a file or directory: {source}", file=sys.stderr)
        return 1

    if not files:
        warnings.append("no compatible files found")

    out_formats_dir = out_dir / "ingest" / "other_formats"
    out_formats_dir.mkdir(parents=True, exist_ok=True)

    total_regions = 0
    total_fillers = 0
    class_dist: Counter = Counter()
    per_file: List[Dict[str, Any]] = []

    for f in files:
        regions, fmt_used, fillers = parse_file(f, fmt)
        if regions and isinstance(regions[0], dict) and "error" in regions[0]:
            warnings.append(f"{f.name}: {regions[0]['error']}")
            continue
        total_regions += len(regions)
        total_fillers += fillers
        for r in regions:
            sem = r.get("semantic_class", "unknown")
            class_dist[sem] += 1
        out_basename = f"{f.stem}.{fmt_used or 'unknown'}" if fmt_used else f.stem
        atomic_write_text(
            out_formats_dir / f"{out_basename}.regions.json",
            json.dumps({
                "basename": f.stem,
                "source_format": fmt_used or "unknown",
                "regions": regions,
            }, indent=2, ensure_ascii=False),
        )
        per_file.append({"file": f.name, "format": fmt_used, "region_count": len(regions)})

    summary = {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "path": str(source),
            "format": fmt or "auto",
            "hash": sha256_file(source) if source.is_file() else "",
        },
        "files_processed": len(per_file),
        "region_count": total_regions,
        "class_distribution": dict(class_dist),
        "fillers_removed_count": total_fillers,
        "per_file": per_file,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    atomic_write_text(
        out_formats_dir / "summary.json",
        json.dumps(summary, indent=2, ensure_ascii=False),
    )

    if not json_only:
        md_lines = [f"# Other Formats — `{source.name}`", ""]
        md_lines.append(f"- **Files:** {len(per_file)}")
        md_lines.append(f"- **Total regions:** {total_regions}")
        md_lines.append(f"- **Fillers removed:** {total_fillers}")
        md_lines.append(f"- **By class:** {dict(class_dist)}")
        if warnings:
            md_lines.append("")
            md_lines.append("## Advertencias")
            for w in warnings:
                md_lines.append(f"- {w}")
        atomic_write_text(out_formats_dir / "other_formats.md", "\n".join(md_lines) + "\n")

    return 2 if warnings else 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="other_formats.py",
        description="F28 — EPUB/DOCX/PPTX/transcripciones to regions.json.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Constantes (references/01-ingest/other-formats.md):
  TRANSCRIPT_FILLER_WORDS        = um, uh, er, ah, eh, mm, hmm, mm-hmm, uh-huh
  MIN_PAUSE_FOR_FILLER_REMOVAL_S = 2.0    segundos mínimos para eliminar muletillas

Formatos soportados:
  epub, docx, pptx, srt, vtt, json (Whisper-style o AWS Transcribe)

Códigos de salida:
  0 OK
  1 error fatal
  2 OK con advertencias
""",
    )
    parser.add_argument("--source", required=True, help="Archivo o directorio con archivos EPUB/DOCX/PPTX/SRT/VTT/JSON")
    parser.add_argument("--out-dir", required=True, help="Directorio de salida (ingest/other_formats/)")
    parser.add_argument("--format", default=None, choices=["auto", "epub", "docx", "pptx", "srt", "vtt", "json"],
                        help="Forzar formato (default: auto-detect)")
    parser.add_argument("--json-only", action="store_true", help="Solo escribir summary.json (no other_formats.md)")
    args = parser.parse_args(argv)

    code = run(Path(args.source), Path(args.out_dir), args.format, json_only=args.json_only)
    return code


if __name__ == "__main__":
    sys.exit(main())
