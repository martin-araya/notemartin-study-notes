#!/usr/bin/env python3
"""triage.py — F17 L0 ingestion preflight classifier.

Clasifica una fuente (PDF, EPUB, DOCX, PPTX, HTML, Markdown, TXT o repositorio)
y emite un plan de ingesta por rangos de páginas o por unidad lógica.

Uso:
    python3 scripts/ingest/triage.py --source <ruta> --out-dir <dir>

Salidas (en --out-dir):
    triage.json — contrato para los extractores de L0 (F18–F29)
    triage.md   — resumen legible para humanos (omitido con --json-only)

Códigos de salida:
    0 — OK
    1 — Error fatal (formato no detectado, archivo ilegible)
    2 — OK con advertencias (p.ej. pypdf ausente → métricas reducidas)

Dependencias:
    - Python 3.9+ stdlib
    - PyYAML (recomendado; si falta, usa defaults internos)
    - pypdf (opcional; si falta, análisis PDF estructural reducido)

Documentación normativa: references/01-ingest/triage.md.
Umbrales: scripts/ingest/thresholds.yaml.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

try:
    import pypdf  # type: ignore
except ImportError:  # pragma: no cover
    pypdf = None  # type: ignore

SCHEMA_VERSION = "1.0.0"
DEFAULT_THRESHOLDS_PATH = Path(__file__).resolve().parent / "thresholds.yaml"


# ============================================================
# Default thresholds (used when thresholds YAML is unavailable)
# ============================================================

DEFAULT_THRESHOLDS: Dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "pdf": {
        "chars_per_page": {"reliable_min": 1000.0, "degraded_min": 100.0},
        "fonts": {"reliable_min": 1.0},
        "full_page_image": {"rate_scan_min": 0.9, "rate_hybrid_min": 0.5},
        "non_printable_ratio": {"degraded_min": 0.05},
        "global_classification": {"dominant_share": 0.8, "hybrid_min_classes": 2},
    },
    "non_pdf": {
        "html_tag_ratio_max": 0.3,
        "markdown_max_special_ratio": 0.15,
        "text_printable_min": 0.95,
        "repo_required_files": [".git", "README"],
    },
    "extractor_map": {
        "native_reliable": "pdf_native",
        "native_degraded": "pdf_native",
        "pure_scan": "ocr",
        "hybrid_page": "pdf_native",
        "html": "web_docs",
        "markdown": "text",
        "text": "text",
        "repository": "repo_tree",
        "epub": "other_formats",
        "docx": "other_formats",
        "pptx": "other_formats",
    },
    "confidence_expected": {
        "native_reliable": "high",
        "native_degraded": "medium",
        "pure_scan": "low",
        "hybrid_page": "medium",
        "html": "high",
        "markdown": "high",
        "text": "high",
        "repository": "high",
        "epub": "high",
        "docx": "medium",
        "pptx": "medium",
    },
}


def load_thresholds(path: Optional[Path]) -> Tuple[Dict[str, Any], List[str]]:
    """Load thresholds from YAML; fall back to defaults on any failure."""
    warnings: List[str] = []
    if path is None or not Path(path).exists():
        warnings.append(f"thresholds file not found: {path}; using built-in defaults")
        return DEFAULT_THRESHOLDS, warnings
    if yaml is None:
        warnings.append("PyYAML not available; using built-in defaults instead of thresholds file")
        return DEFAULT_THRESHOLDS, warnings
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:  # pragma: no cover - defensive
        warnings.append(f"failed to parse thresholds YAML ({e}); using built-in defaults")
        return DEFAULT_THRESHOLDS, warnings
    if not isinstance(data, dict):
        warnings.append("thresholds YAML root is not a mapping; using built-in defaults")
        return DEFAULT_THRESHOLDS, warnings
    if data.get("schema_version") != SCHEMA_VERSION:
        warnings.append(
            f"thresholds schema_version is {data.get('schema_version')!r}, expected {SCHEMA_VERSION!r}; using built-in defaults"
        )
        return DEFAULT_THRESHOLDS, warnings
    return data, warnings


# ============================================================
# Format detection
# ============================================================

PDF_MAGIC = b"%PDF-"


def detect_format(path: Path) -> str:
    """Detect top-level format. Returns one of: pdf, epub, docx, pptx, html,
    markdown, text, repository, unknown."""
    path = Path(path)
    if path.is_dir():
        if (path / ".git").is_dir():
            if any(path.glob("README*")):
                return "repository"
        return "unknown"

    raw = path.read_bytes()
    if raw.startswith(PDF_MAGIC):
        return "pdf"

    if raw.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(path) as z:
                names = set(z.namelist())
                if "mimetype" in names:
                    mime = z.read("mimetype")
                    if b"application/epub+zip" in mime:
                        return "epub"
                if "word/document.xml" in names:
                    return "docx"
                if "ppt/presentation.xml" in names:
                    return "pptx"
        except (zipfile.BadZipFile, OSError, KeyError, NotImplementedError):
            pass

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("latin-1")
        except Exception:
            return "unknown"

    head = text[:4096].lower()
    if re.search(r"<!doctype\s+html|<\s*html[\s>]", head):
        return "html"
    if path.suffix.lower() in (".md", ".markdown"):
        return "markdown"
    if path.suffix.lower() in (".txt", ".text"):
        return "text"

    total = len(text)
    if total >= 16:
        printable = sum(1 for c in text if c.isprintable() or c in "\n\r\t")
        if printable / total >= 0.95:
            return "text"

    return "unknown"


# ============================================================
# Helpers
# ============================================================

def non_printable_ratio(text: str) -> float:
    if not text:
        return 0.0
    np_count = 0
    for ch in text:
        if ch.isprintable() or ch in "\n\r\t":
            continue
        if unicodedata.category(ch) in ("Cc", "Cf"):
            np_count += 1
    return np_count / len(text)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


# ============================================================
# PDF analysis
# ============================================================

def _count_fonts_pypdf(page: Any) -> int:
    try:
        resources = page.get("/Resources") or {}
        fonts = resources.get("/Font", {})
    except Exception:
        return 0
    if isinstance(fonts, dict):
        return len(fonts)
    try:
        if hasattr(fonts, "keys"):
            return len(list(fonts.keys()))
    except Exception:
        return 0
    return 0


def _full_page_image_rate_pypdf(page: Any) -> Tuple[float, int]:
    try:
        resources = page.get("/Resources") or {}
        xobject = resources.get("/XObject", {})
    except Exception:
        return 0.0, 0
    if not xobject:
        return 0.0, 0
    try:
        media = page.mediabox
        w = float(media.width)
        h = float(media.height)
    except Exception:
        return 0.0, 0
    page_area = w * h
    if page_area <= 0:
        return 0.0, 0

    items = []
    try:
        items = list(xobject.keys()) if hasattr(xobject, "keys") else []
    except Exception:
        items = []

    total_area = 0.0
    count = 0
    for name in items:
        try:
            obj = xobject[name].get_object()
            if obj.get("/Subtype") == "/Image":
                count += 1
                iw = float(obj.get("/Width", 0))
                ih = float(obj.get("/Height", 0))
                total_area += iw * ih
        except Exception:
            continue
    rate = min(total_area / page_area, 1.0) if page_area > 0 else 0.0
    return rate, count


def analyze_pdf_with_pypdf(path: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    warnings: List[str] = []
    pages: List[Dict[str, Any]] = []
    reader = pypdf.PdfReader(str(path))  # type: ignore
    for i, page in enumerate(reader.pages, 1):
        try:
            text = page.extract_text() or ""
        except Exception as e:
            text = ""
            warnings.append(f"page {i}: extract_text failed: {e}")
        chars = len(text.strip())
        fonts = _count_fonts_pypdf(page)
        rate, images = _full_page_image_rate_pypdf(page)
        npr = non_printable_ratio(text)
        pages.append({
            "page": i,
            "chars": chars,
            "fonts": fonts,
            "full_page_image_rate": round(rate, 3),
            "images": images,
            "non_printable_ratio": round(npr, 3),
        })
    return pages, warnings


def analyze_pdf_bytes(raw: bytes) -> List[Dict[str, Any]]:
    """Byte-level fallback when pypdf is unavailable. Conservative estimates."""
    pages: List[Dict[str, Any]] = []
    page_starts = [m.start() for m in re.finditer(rb"/Type\s*/Page(?![sA-Za-z])", raw)]
    boundaries = page_starts + [len(raw)]
    for idx in range(len(page_starts)):
        chunk = raw[boundaries[idx]:boundaries[idx + 1]]
        text_chunks = re.findall(rb"BT\s+(.*?)\s+ET", chunk, flags=re.DOTALL)
        decoded: List[str] = []
        for tc in text_chunks:
            tj = re.search(rb"\((?:[^\\()]|\\.)*\)\s*Tj", tc)
            if tj:
                for ss in re.findall(rb"\((?:[^\\()]|\\.)*\)", tj.group(0)):
                    try:
                        decoded.append(ss[1:-1].decode("latin-1", errors="replace"))
                    except Exception:
                        pass
        joined = "".join(decoded)
        chars = len(joined.strip())
        fonts = len(set(re.findall(rb"/BaseFont\s*/([\w\-+]+)", chunk)))
        images = len(re.findall(rb"/Subtype\s*/Image", chunk))
        mbox = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*\]", chunk)
        page_area = float(mbox.group(1)) * float(mbox.group(2)) if mbox else 1.0  # noqa: F841
        rate = 1.0 if images > 0 else 0.0
        pages.append({
            "page": idx + 1,
            "chars": chars,
            "fonts": fonts,
            "full_page_image_rate": rate,
            "images": images,
            "non_printable_ratio": round(non_printable_ratio(joined), 3),
        })
    return pages


def analyze_pdf(path: Path, thresholds: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[str]]:  # noqa: ARG001
    if pypdf is not None:
        try:
            return analyze_pdf_with_pypdf(path)
        except Exception as e:
            raw = path.read_bytes()
            warnings = [f"pypdf failed ({e}); falling back to byte-level parsing"]
            return analyze_pdf_bytes(raw), warnings
    raw = path.read_bytes()
    warnings = ["pypdf not available; using byte-level analysis (less precise than pypdf path)"]
    return analyze_pdf_bytes(raw), warnings


# ============================================================
# Classification
# ============================================================

def classify_pdf_page(metrics: Dict[str, Any], thresholds: Dict[str, Any]) -> str:
    """Classify a single PDF page.

    Priority (in this order):
      1. pure_scan       — few chars AND high image coverage.
      2. native_reliable — text-rich page with at least one embedded font,
                           regardless of decorative figures.
      3. hybrid_page     — visible text coexisting with a dominant image.
      4. native_degraded — everything else: short text, no fonts, or noisy
                           non-printable ratio.
    """
    pdf_t = thresholds["pdf"]
    chars = float(metrics.get("chars", 0))
    fonts = float(metrics.get("fonts", 0))
    rate = float(metrics.get("full_page_image_rate", 0.0))
    npr = float(metrics.get("non_printable_ratio", 0.0))

    rel_chars = float(pdf_t["chars_per_page"]["reliable_min"])
    deg_chars = float(pdf_t["chars_per_page"]["degraded_min"])
    min_fonts = float(pdf_t["fonts"]["reliable_min"])
    scan_rate = float(pdf_t["full_page_image"]["rate_scan_min"])
    hybrid_rate = float(pdf_t["full_page_image"]["rate_hybrid_min"])
    deg_npr = float(pdf_t["non_printable_ratio"]["degraded_min"])

    if chars < deg_chars and rate >= scan_rate:
        return "pure_scan"
    if chars >= rel_chars and fonts >= min_fonts:
        return "native_reliable"
    if rate >= hybrid_rate and chars >= deg_chars:
        return "hybrid_page"
    if (deg_chars <= chars < rel_chars) or npr >= deg_npr or fonts < min_fonts:
        return "native_degraded"
    return "native_degraded"


def classify_pdf_global(pages: List[Dict[str, Any]], thresholds: Dict[str, Any]) -> str:
    pdf_t = thresholds["pdf"]
    if not pages:
        return "unknown"
    classes = [p["class"] for p in pages]
    counts = {c: classes.count(c) for c in set(classes)}
    dominant_share = float(pdf_t["global_classification"]["dominant_share"])
    hybrid_min = int(pdf_t["global_classification"]["hybrid_min_classes"])

    pure_share = counts.get("pure_scan", 0) / len(classes)
    rel_share = counts.get("native_reliable", 0) / len(classes)

    if pure_share >= dominant_share:
        return "pdf_pure_scan"
    if rel_share >= dominant_share:
        return "pdf_native_reliable"
    has_text = counts.get("native_reliable", 0) + counts.get("native_degraded", 0) + counts.get("hybrid_page", 0)
    has_scan = counts.get("pure_scan", 0)
    if has_text > 0 and has_scan > 0 and len(counts) >= hybrid_min:
        return "pdf_hybrid"
    return "pdf_native_degraded"


def build_plan(pages: List[Dict[str, Any]], thresholds: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not pages:
        return []
    extractor_map = thresholds.get("extractor_map", DEFAULT_THRESHOLDS["extractor_map"])
    confidence_map = thresholds.get("confidence_expected", DEFAULT_THRESHOLDS["confidence_expected"])

    annotated = []
    for p in pages:
        cls = p["class"]
        annotated.append({
            "page": p["page"],
            "class": cls,
            "extractor": extractor_map.get(cls, "pdf_native"),
            "ocr_required": cls == "pure_scan",
            "confidence_expected": confidence_map.get(cls, "medium"),
        })

    plan: List[Dict[str, Any]] = []
    if not annotated:
        return plan
    current_start = annotated[0]["page"]
    current_end = annotated[0]["page"]
    current_class = annotated[0]["class"]
    current_extractor = annotated[0]["extractor"]
    current_ocr = annotated[0]["ocr_required"]
    current_conf = annotated[0]["confidence_expected"]

    for p in annotated[1:]:
        same = (p["class"] == current_class and p["ocr_required"] == current_ocr and p["extractor"] == current_extractor)
        if same:
            current_end = p["page"]
        else:
            plan.append(_range_plan(current_start, current_end, current_class, current_extractor, current_ocr, current_conf))
            current_start = p["page"]
            current_end = p["page"]
            current_class = p["class"]
            current_extractor = p["extractor"]
            current_ocr = p["ocr_required"]
            current_conf = p["confidence_expected"]
    plan.append(_range_plan(current_start, current_end, current_class, current_extractor, current_ocr, current_conf))
    return plan


def _range_plan(start: int, end: int, cls: str, extractor: str, ocr: bool, conf: str) -> Dict[str, Any]:
    return {
        "pages": f"{start}-{end}" if start != end else f"{start}",
        "class": cls,
        "extractor": extractor,
        "ocr_required": ocr,
        "confidence_expected": conf,
    }


# ============================================================
# Non-PDF analysis (single page)
# ============================================================

def analyze_non_pdf(path: Path, fmt: str, thresholds: Dict[str, Any]) -> Dict[str, Any]:
    extractor_map = thresholds.get("extractor_map", DEFAULT_THRESHOLDS["extractor_map"])
    confidence_map = thresholds.get("confidence_expected", DEFAULT_THRESHOLDS["confidence_expected"])
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1", errors="replace")

    metrics = {
        "chars": len(text.strip()),
        "fonts": 0,
        "full_page_image_rate": 0.0,
        "images": 0,
        "non_printable_ratio": round(non_printable_ratio(text), 3),
    }
    pages = [{"page": 1, **metrics, "class": fmt}]
    plan = [{
        "pages": "1",
        "class": fmt,
        "extractor": extractor_map.get(fmt, "text"),
        "ocr_required": False,
        "confidence_expected": confidence_map.get(fmt, "high"),
    }]
    return {"pages": pages, "plan": plan}


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
    lines.append(f"# Triaje — `{payload['source']['path']}`")
    lines.append("")
    lines.append(f"- **Hash sha256:** `{payload['source']['hash']}`")
    lines.append(f"- **Tamaño:** {payload['source']['size_bytes']} bytes")
    lines.append(f"- **Formato detectado:** `{payload['source']['format']}`")
    lines.append(f"- **Clasificación global:** `{payload['format_classification']}`")
    lines.append(f"- **Páginas:** {payload['page_count']}")
    lines.append(f"- **Umbrales (versión):** `{payload['thresholds_version']}`")
    lines.append(f"- **Generado:** {payload['generated_at']}")
    if payload.get("warnings"):
        lines.append("")
        lines.append("## Advertencias")
        for w in payload["warnings"]:
            lines.append(f"- {w}")
    lines.append("")
    lines.append("## Plan de ingesta")
    lines.append("")
    lines.append("| Páginas | Clase | Extractor | OCR | Confianza esperada |")
    lines.append("|---|---|---|---|---|")
    for r in payload["plan"]:
        lines.append(f"| {r['pages']} | `{r['class']}` | `{r['extractor']}` | {'sí' if r['ocr_required'] else 'no'} | `{r['confidence_expected']}` |")
    if payload.get("pages"):
        lines.append("")
        lines.append("## Métricas por página")
        lines.append("")
        lines.append("| # | chars | fuentes | img_ratio | non_print | clase |")
        lines.append("|---|---|---|---|---|---|")
        for p in payload["pages"]:
            lines.append(
                f"| {p['page']} | {p['chars']} | {p['fonts']} | {p['full_page_image_rate']} | {p['non_printable_ratio']} | `{p['class']}` |"
            )
    return "\n".join(lines) + "\n"


# ============================================================
# Entry point
# ============================================================

def run(source: Path, out_dir: Path, thresholds_path: Optional[Path], force_format: Optional[str], json_only: bool = False) -> int:
    thresholds, threshold_warnings = load_thresholds(thresholds_path)
    source = Path(source).resolve()
    if not source.exists():
        print(f"ERROR: source not found: {source}", file=sys.stderr)
        return 1

    detected_format = force_format if force_format and force_format != "auto" else detect_format(source)
    if detected_format == "unknown":
        print(f"ERROR: could not detect format of {source}", file=sys.stderr)
        return 1

    sha = sha256_file(source)
    size = source.stat().st_size
    warnings: List[str] = list(threshold_warnings)

    if detected_format == "pdf":
        page_metrics, page_warnings = analyze_pdf(source, thresholds)
        warnings.extend(page_warnings)
        classified_pages = []
        for m in page_metrics:
            cls = classify_pdf_page(m, thresholds)
            classified_pages.append({**m, "class": cls})
        global_class = classify_pdf_global(classified_pages, thresholds)
        plan = build_plan(classified_pages, thresholds)
        page_count = len(classified_pages)
    else:
        analyzed = analyze_non_pdf(source, detected_format, thresholds)
        classified_pages = analyzed["pages"]
        plan = analyzed["plan"]
        page_count = 1
        global_class = detected_format

    payload = {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "path": str(source),
            "hash": sha,
            "size_bytes": size,
            "format": detected_format,
        },
        "thresholds_version": thresholds.get("schema_version", SCHEMA_VERSION),
        "format_classification": global_class,
        "page_count": page_count,
        "pages": classified_pages,
        "plan": plan,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_text(out_dir / "triage.json", json.dumps(payload, indent=2, ensure_ascii=False))
    if not json_only:
        atomic_write_text(out_dir / "triage.md", render_markdown(payload))

    return 2 if warnings else 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="triage.py",
        description="F17 — L0 ingestion preflight classifier (PDF/EPUB/DOCX/PPTX/HTML/MD/TXT/REPO).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Clases PDF (references/01-ingest/triage.md §3):
  native_reliable   capa de texto fiable
  native_degraded   capa presente pero ruidosa
  pure_scan         imagen a página completa, sin texto
  hybrid_page       texto nativo + imagen grande coexisten

Umbrales por defecto (scripts/ingest/thresholds.yaml):
  chars_per_page.reliable_min     = 1000
  chars_per_page.degraded_min     = 100
  fonts.reliable_min              = 1
  full_page_image.rate_scan_min   = 0.9
  full_page_image.rate_hybrid_min = 0.5
  non_printable_ratio.degraded_min= 0.05
  global_classification.dominant_share = 0.8

Códigos de salida:
  0 OK sin advertencias
  1 error fatal
  2 OK con advertencias (p.ej. pypdf ausente)
""",
    )
    parser.add_argument("--source", required=True, help="Ruta al archivo o directorio fuente")
    parser.add_argument("--out-dir", required=True, help="Directorio de salida (triage.json + triage.md)")
    parser.add_argument("--thresholds", default=str(DEFAULT_THRESHOLDS_PATH), help=f"Archivo YAML de umbrales (default: {DEFAULT_THRESHOLDS_PATH})")
    parser.add_argument("--format", default="auto", choices=["auto", "pdf", "epub", "docx", "pptx", "html", "markdown", "text", "repository"], help="Forzar formato (default: auto)")
    parser.add_argument("--json-only", action="store_true", help="Solo escribir triage.json (no triage.md)")
    args = parser.parse_args(argv)

    thresholds_path = Path(args.thresholds) if args.thresholds else None
    out_dir = Path(args.out_dir)
    code = run(Path(args.source), out_dir, thresholds_path, args.format, json_only=args.json_only)
    return code


if __name__ == "__main__":
    sys.exit(main())
