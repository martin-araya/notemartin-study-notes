#!/usr/bin/env python3
"""review_report.py — F26 confidence and human review.

Genera un reporte HTML interactivo con recortes de imagen y texto lado a lado,
agrega umbrales de confianza por tipo de región, bloquea si hay demasiadas
regiones críticas dudosas, y propaga correcciones humanas a regiones con el
mismo error.

Uso:
    python3 scripts/ingest/review_report.py \
        --source <ingest_dir> --images-dir <images_dir> --out-dir <dir> \
        [--corrections <corrections.json>] [--json-only]

Salidas (en <out-dir>/ingest/review/):
    report.html — reporte HTML interactivo con filter bar JS
    summary.json — machine-readable con umbrales, blocked, correcciones
    crops/page-NNNN/<id>.png — recortes para regiones low_confidence o críticas

Códigos de salida:
    0 — OK (reporte generado, sin bloqueo)
    1 — BLOQUEADO (≥ 3 regiones críticas low_confidence)
    2 — OK con advertencias (correcciones propagadas, low_confidence no-crítica)

Dependencias:
    - Python 3.9+ stdlib
    - Pillow (opcional; solo si se recortan imágenes)

Documentación normativa: references/01-ingest/confidence.md.
"""

from __future__ import annotations

import argparse
import html
import hashlib
import json
import re
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"

# ============================================================
# Constants (per references/01-ingest/confidence.md §2-§5)
# ============================================================

MAX_LOW_CONF_CRITICAL = 3
CROP_PADDING_PX = 5
PROPAGATION_MIN_LENGTH = 5
MIN_REGION_AREA_PX = 100

THRESHOLDS_BY_CLASS: Dict[str, float] = {
    "code": 0.90,
    "console": 0.90,
    "table": 0.85,
    "formula": 0.75,
    "syntax_diagram": 0.75,
    "heading": 0.70,
    "caption": 0.70,
    "figure_caption": 0.70,
    "index": 0.70,
    "editorial_note": 0.65,
    "text": 0.60,
    "figure": 0.50,
    "capture": 0.50,
    "diagram": 0.50,
    "unknown": 0.60,
}

CRITICAL_CLASSES = frozenset({"code", "console", "table", "formula", "syntax_diagram"})


# ============================================================
# Data structures
# ============================================================

@dataclass
class RegionReview:
    id: str
    page: int
    region_class: str
    text: str
    confidence: float
    low_confidence: bool
    bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    crop_path: Optional[str] = None
    human_corrected: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# Helpers
# ============================================================

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
# Region collection
# ============================================================

def _load_file(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def collect_regions(source: Path) -> List[RegionReview]:
    """Collect all regions from F22/F23/F24/F25 outputs under <source>/ingest/."""
    ingest_dir = source / "ingest"
    regions: List[RegionReview] = []

    pages_regions = ingest_dir / "regions"
    if pages_regions.exists():
        for p in sorted(pages_regions.glob("page-*.regions.json")):
            data = _load_file(p)
            for r in data.get("regions", []):
                sem = r.get("semantic_class")
                if not sem or sem == "unknown":
                    continue
                conf = r.get("class_confidence", 1.0)
                low = r.get("ambiguity", False) or r.get("low_confidence", False)
                signals = r.get("signals", [])
                if signals:
                    max_signal = max(s.get("value", 0.0) for s in signals)
                    conf = max(conf, max_signal)
                regions.append(RegionReview(
                    id=r.get("id", "?"),
                    page=int(r.get("page", 1)),
                    region_class=sem,
                    text=r.get("first_word", "") + " ... " + r.get("last_word", ""),
                    confidence=conf,
                    low_confidence=low,
                    bbox=tuple(r.get("bbox", [0, 0, 0, 0])),
                ))

    pages_tables = ingest_dir / "tables"
    if pages_tables.exists():
        for p in sorted(pages_tables.glob("page-*.tables.json")):
            data = _load_file(p)
            for t in data.get("tables", []):
                cells = t.get("data", [])
                first_row = cells[0] if cells else []
                last_row = cells[-1] if cells else []
                header_rows = t.get("headers", [])
                text = " | ".join(" | ".join(r) for r in (header_rows + [first_row])[:3])
                regions.append(RegionReview(
                    id=t.get("id", "?"),
                    page=int(t.get("page_start", t.get("page_end", 1))),
                    region_class="table",
                    text=text[:500],
                    confidence=t.get("confidence", 1.0),
                    low_confidence=t.get("low_confidence", False),
                    bbox=tuple(t.get("bbox", [0, 0, 0, 0])),
                ))

    pages_formulas = ingest_dir / "formulas"
    if pages_formulas.exists():
        for p in sorted(pages_formulas.glob("page-*.formulas.json")):
            data = _load_file(p)
            for f in data.get("formulas", []):
                regions.append(RegionReview(
                    id=f.get("id", "?"),
                    page=int(f.get("page", 1)),
                    region_class="formula",
                    text=f.get("latex", ""),
                    confidence=f.get("confidence", 1.0),
                    low_confidence=f.get("pending", False),
                    bbox=tuple(f.get("bbox", [0, 0, 0, 0])),
                ))

    pages_code = ingest_dir / "code"
    if pages_code.exists():
        for p in sorted(pages_code.glob("page-*.code.json")):
            data = _load_file(p)
            for b in data.get("blocks", []):
                regions.append(RegionReview(
                    id=b.get("id", "?"),
                    page=int(b.get("page", 1)),
                    region_class=b.get("language", "code"),
                    text=b.get("text", ""),
                    confidence=b.get("confidence", 1.0),
                    low_confidence=b.get("low_confidence", False),
                    bbox=tuple(b.get("bbox", [0, 0, 0, 0])),
                    extra={"corrections": b.get("corrections", [])},
                ))

    return regions


# ============================================================
# Image cropping
# ============================================================

def crop_image(image_path: Path, bbox: Tuple[float, float, float, float], output_path: Path) -> bool:
    try:
        from PIL import Image
    except ImportError:
        return False
    if not image_path.exists():
        return False
    try:
        img = Image.open(image_path)
    except Exception:
        return False
    bx0, by0, bw, bh = bbox
    w, h = img.size
    x0 = max(0, int(bx0) - CROP_PADDING_PX)
    y0 = max(0, int(by0) - CROP_PADDING_PX)
    x1 = min(w, int(bx0 + bw) + CROP_PADDING_PX)
    y1 = min(h, int(by0 + bh) + CROP_PADDING_PX)
    if x1 <= x0 or y1 <= y0:
        return False
    if (x1 - x0) * (y1 - y0) < MIN_REGION_AREA_PX:
        return False
    try:
        cropped = img.crop((x0, y0, x1, y1))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cropped.save(output_path, format="PNG")
        return True
    except Exception:
        return False


def crop_regions(regions: List[RegionReview], images_dir: Optional[Path], out_dir: Path) -> None:
    if images_dir is None or not images_dir.exists():
        return
    crops_dir = out_dir / "crops"
    for r in regions:
        if not (r.low_confidence or r.region_class in CRITICAL_CLASSES):
            continue
        if not r.bbox or r.bbox[2] <= 0 or r.bbox[3] <= 0:
            continue
        src = images_dir / f"page-{r.page:04d}.processed.png"
        if not src.exists():
            continue
        out = crops_dir / f"page-{r.page:04d}" / f"{r.id}.png"
        if crop_image(src, r.bbox, out):
            r.crop_path = str(out.relative_to(out_dir))


# ============================================================
# Human corrections + propagation
# ============================================================

def apply_human_corrections(
    regions: List[RegionReview],
    corrections_path: Optional[Path],
    warnings: List[str],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    applied: List[Dict[str, Any]] = []
    propagated: List[Dict[str, Any]] = []
    if not corrections_path or not corrections_path.exists():
        return applied, propagated
    try:
        data = json.loads(corrections_path.read_text(encoding="utf-8"))
    except Exception as e:
        warnings.append(f"failed to parse corrections.json: {e}")
        return applied, propagated
    corrections = data.get("corrections", [])

    by_id = {r.id: r for r in regions}
    by_original = {}
    for r in regions:
        if r.text and len(r.text) >= PROPAGATION_MIN_LENGTH:
            by_original.setdefault(r.text, []).append(r)

    for c in corrections:
        rid = c.get("region_id")
        original = c.get("original_text", "")
        corrected = c.get("corrected_text", "")
        applied_at = c.get("applied_at", "")
        reason = c.get("reason", "")
        if rid in by_id:
            by_id[rid].text = corrected
            by_id[rid].human_corrected = True
            by_id[rid].low_confidence = False
            applied.append({
                "region_id": rid,
                "original": original,
                "corrected": corrected,
                "applied_at": applied_at,
                "reason": reason,
            })
        for r in by_original.get(original, []):
            if r.id == rid:
                continue
            r.text = corrected
            r.human_corrected = True
            r.low_confidence = False
            propagated.append({
                "region_id": r.id,
                "applied_correction": {"original": original, "corrected": corrected},
            })
    return applied, propagated


# ============================================================
# Blocking decision
# ============================================================

def should_block(regions: List[RegionReview]) -> Tuple[bool, Optional[str]]:
    critical_low = sum(
        1 for r in regions
        if r.low_confidence and r.region_class in CRITICAL_CLASSES
    )
    if critical_low >= MAX_LOW_CONF_CRITICAL:
        return True, "too_many_low_confidence_critical_regions"
    return False, None


# ============================================================
# HTML rendering
# ============================================================

def render_html(
    regions: List[RegionReview],
    summary: Dict[str, Any],
    out_dir: Path,
) -> str:
    sorted_regions = sorted(regions, key=lambda r: (r.page, -r.bbox[1] if r.bbox else 0))
    rows_html = []
    for r in sorted_regions:
        img_src = r.crop_path if r.crop_path else ""
        img_html = f'<img src="{html.escape(img_src)}" alt="crop" loading="lazy">' if img_src else '<span class="no-crop">(crop unavailable)</span>'
        text_safe = html.escape(r.text)
        confidence_pct = f"{r.confidence * 100:.0f}%"
        threshold_pct = f"{THRESHOLDS_BY_CLASS.get(r.region_class, 0.60) * 100:.0f}%"
        low_class = "low" if r.low_confidence else "ok"
        rows_html.append(
            f'<tr class="region-row" data-class="{html.escape(r.region_class)}" '
            f'data-page="{r.page}" data-confidence="{r.confidence:.3f}" '
            f'data-block="{low_class}">'
            f'<td class="region-id">{html.escape(r.id)}</td>'
            f'<td class="region-page">{r.page}</td>'
            f'<td class="region-class">{html.escape(r.region_class)}</td>'
            f'<td class="region-confidence">{confidence_pct}</td>'
            f'<td class="region-threshold">{threshold_pct}</td>'
            f'<td class="region-low">{low_class}</td>'
            f'<td class="region-image">{img_html}</td>'
            f'<td><pre class="region-text">{text_safe[:1000]}</pre></td>'
            f'</tr>'
        )

    rows_joined = "\n".join(rows_html) if rows_html else '<tr><td colspan="8" style="text-align:center;">No regions found</td></tr>'

    blocked_class = "blocked" if summary.get("blocked") else "ok"
    blocked_reason = summary.get("blocked_reason", "")
    blocked_banner = ""
    if summary.get("blocked"):
        blocked_banner = f'<div class="banner blocked-banner">BLOCKED: {html.escape(blocked_reason)}</div>'

    classes_options = "\n".join(
        f'<option value="{html.escape(cls)}">{html.escape(cls)}</option>'
        for cls in sorted(THRESHOLDS_BY_CLASS.keys())
    )

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Reporte de revisión — {html.escape(summary['source'].get('ingest_dir', ''))}</title>
  <style>
    body {{ font-family: -apple-system, sans-serif; margin: 20px; }}
    h1 {{ margin-bottom: 8px; }}
    .summary {{ background: #f5f5f5; padding: 12px; border-radius: 4px; margin-bottom: 16px; }}
    .summary .stat {{ display: inline-block; margin-right: 24px; font-weight: bold; }}
    .banner {{ padding: 12px; border-radius: 4px; margin-bottom: 16px; }}
    .blocked-banner {{ background: #fee; color: #c00; border: 2px solid #c00; font-weight: bold; }}
    .filters {{ background: #fafafa; padding: 12px; border-radius: 4px; margin-bottom: 16px; }}
    .filters label {{ margin-right: 16px; }}
    table.regions {{ width: 100%; border-collapse: collapse; }}
    table.regions th, table.regions td {{ border: 1px solid #ccc; padding: 8px; vertical-align: top; }}
    table.regions th {{ background: #eee; }}
    table.regions img {{ max-width: 400px; max-height: 300px; }}
    table.regions pre {{ margin: 0; white-space: pre-wrap; font-family: monospace; font-size: 12px; }}
    .low {{ background: #fee; }}
    .ok {{ background: #efe; }}
    .region-class {{ font-weight: bold; }}
  </style>
</head>
<body>
  <h1>Reporte de revisión</h1>
  <div class="summary">
    <p><strong>Source:</strong> {html.escape(summary['source'].get('ingest_dir', ''))}</p>
    <p>
      <span class="stat">Total: {summary['total_regions']}</span>
      <span class="stat">Low-confidence: {summary['low_confidence_count']}</span>
      <span class="stat">Critical low-conf: {summary['critical_low_confidence_count']}</span>
      <span class="stat">Applied: {len(summary.get('applied_corrections', []))}</span>
      <span class="stat">Propagated: {len(summary.get('propagated_corrections', []))}</span>
    </p>
    <p><strong>Generated:</strong> {summary['generated_at']}</p>
  </div>
  {blocked_banner}
  <div class="filters">
    <label>Class: <select id="filter-class"><option value="">all</option>{classes_options}</select></label>
    <label>Page: <input type="number" id="filter-page" min="1" placeholder="all"></label>
    <label>Min confidence: <input type="range" id="filter-confidence" min="0" max="100" value="0"><span id="confidence-value">0</span>%</label>
    <label>Block: <select id="filter-block"><option value="">all</option><option value="true">low_confidence</option><option value="false">ok</option></select></label>
    <button id="reset-filters">Reset</button>
  </div>
  <table class="regions">
    <thead>
      <tr>
        <th>Region ID</th>
        <th>Page</th>
        <th>Class</th>
        <th>Confidence</th>
        <th>Threshold</th>
        <th>Status</th>
        <th>Image</th>
        <th>Text</th>
      </tr>
    </thead>
    <tbody>
      {rows_joined}
    </tbody>
  </table>
  <script>
    const classFilter = document.getElementById('filter-class');
    const pageFilter = document.getElementById('filter-page');
    const confFilter = document.getElementById('filter-confidence');
    const confValue = document.getElementById('confidence-value');
    const blockFilter = document.getElementById('filter-block');
    function applyFilters() {{
      confValue.textContent = confFilter.value;
      const rows = document.querySelectorAll('tr.region-row');
      rows.forEach(row => {{
        let show = true;
        if (classFilter.value && row.dataset.class !== classFilter.value) show = false;
        if (pageFilter.value && parseInt(row.dataset.page) !== parseInt(pageFilter.value)) show = false;
        if (parseInt(confFilter.value) > 0 && parseFloat(row.dataset.confidence) * 100 < parseInt(confFilter.value)) show = false;
        if (blockFilter.value) {{
          if (blockFilter.value === 'true' && row.dataset.block !== 'low') show = false;
          if (blockFilter.value === 'false' && row.dataset.block !== 'ok') show = false;
        }}
        row.style.display = show ? '' : 'none';
      }});
    }}
    [classFilter, pageFilter, confFilter, blockFilter].forEach(el => el.addEventListener('input', applyFilters));
    document.getElementById('reset-filters').addEventListener('click', () => {{
      classFilter.value = '';
      pageFilter.value = '';
      confFilter.value = '0';
      blockFilter.value = '';
      applyFilters();
    }});
  </script>
</body>
</html>
"""
    return html_content


# ============================================================
# Entry point
# ============================================================

def run(
    source: Path,
    out_dir: Path,
    images_dir: Optional[Path],
    corrections_path: Optional[Path],
    json_only: bool = False,
) -> int:
    source = Path(source).resolve()
    if not source.exists():
        print(f"ERROR: source not found: {source}", file=sys.stderr)
        return 1

    warnings: List[str] = []
    regions = collect_regions(source)
    if not regions:
        warnings.append("no regions found in ingest dir; report will be empty")

    applied, propagated = apply_human_corrections(regions, corrections_path, warnings)
    crop_regions(regions, images_dir, out_dir)

    blocked, blocked_reason = should_block(regions)
    low_count = sum(1 for r in regions if r.low_confidence)
    critical_low = sum(1 for r in regions if r.low_confidence and r.region_class in CRITICAL_CLASSES)
    class_distribution = Counter(r.region_class for r in regions)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "ingest_dir": str(source),
            "images_dir": str(images_dir) if images_dir else None,
            "corrections_path": str(corrections_path) if corrections_path else None,
            "hash": sha256_paths([source] + ([images_dir] if images_dir else []) + ([corrections_path] if corrections_path else [])),
        },
        "blocked": blocked,
        "blocked_reason": blocked_reason or "",
        "total_regions": len(regions),
        "low_confidence_count": low_count,
        "critical_low_confidence_count": critical_low,
        "class_distribution": dict(class_distribution),
        "class_thresholds": dict(THRESHOLDS_BY_CLASS),
        "applied_corrections": applied,
        "propagated_corrections": propagated,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    out_review = out_dir / "ingest" / "review"
    out_review.mkdir(parents=True, exist_ok=True)
    atomic_write_text(
        out_review / "summary.json",
        json.dumps(summary, indent=2, ensure_ascii=False),
    )

    if not json_only:
        html_content = render_html(regions, summary, out_review)
        atomic_write_text(out_review / "report.html", html_content)

    if blocked:
        return 1
    return 2 if warnings or applied or propagated else 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="review_report.py",
        description="F26 — Confidence aggregation, HTML review report, and human-correction propagation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Constantes (references/01-ingest/confidence.md §2-§5):
  MAX_LOW_CONF_CRITICAL    = 3      regiones críticas dudosas que disparan bloqueo
  CROP_PADDING_PX          = 5      px alrededor del bbox al recortar
  PROPAGATION_MIN_LENGTH   = 5      chars mínimo para propagar correcciones
  MIN_REGION_AREA_PX       = 100    mínimo para recortar imagen

Umbrales por tipo (THRESHOLDS_BY_CLASS):
  code/console       ≥ 0.90
  table              ≥ 0.85
  formula/syntax_dgm ≥ 0.75
  heading/caption    ≥ 0.70
  editorial_note     ≥ 0.65
  text               ≥ 0.60
  figure/capture/dgm ≥ 0.50

Regiones críticas: code, console, table, formula, syntax_diagram.

Códigos de salida:
  0 OK sin advertencias
  1 BLOQUEADO (≥ MAX_LOW_CONF_CRITICAL regiones críticas dudosas)
  2 OK con advertencias (correcciones propagadas, low_confidence no-crítica)
""",
    )
    parser.add_argument("--source", required=True, help="Directorio raíz (contiene ingest/)")
    parser.add_argument("--images-dir", default=None, help="Directorio con page-NNNN.processed.png de F19 (opcional)")
    parser.add_argument("--corrections", default=None, help="Corrections JSON opcional (propaga a regiones con mismo original_text)")
    parser.add_argument("--out-dir", required=True, help="Directorio de salida (ingest/review/)")
    parser.add_argument("--json-only", action="store_true", help="Solo escribir summary.json (no report.html)")
    args = parser.parse_args(argv)

    images_dir = Path(args.images_dir) if args.images_dir else None
    corrections_path = Path(args.corrections) if args.corrections else None
    code = run(Path(args.source), Path(args.out_dir), images_dir, corrections_path, json_only=args.json_only)
    return code


if __name__ == "__main__":
    sys.exit(main())
