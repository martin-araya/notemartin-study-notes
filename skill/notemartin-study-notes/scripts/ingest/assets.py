#!/usr/bin/env python3
"""assets.py — F33 Asset Catalog.

Lee el SDM producido por F31 (`build_sdm.py`), toma cada bloque `figure`,
auto-extrae los bytes de imagen desde el archivo fuente (PDF vía pypdfium2;
EPUB vía ebooklib), aplica dedup por hash sha256, clasifica cada asset en
`diagram_conceptual | screenshot | data_figure | decorative`, valida alt text,
y actualiza el SDM en sitio con la ruta determinista del asset. Emite un
catálogo `assets.json` + resumen `assets_summary.json`.

Uso:
    python3 scripts/ingest/assets.py \
        --sdm <sdm.json> --source-file <pdf|epub> --out-dir <dir> \
        [--out-sdm <path>] [--classify <yaml>] \
        [--min-width 256] [--min-height 256] [--json-only]

Salidas (en <out-dir>/assets/):
    assets/<source_id>/<sha256[:16]>.<ext>     — un archivo por hash único
    assets.json                                — catálogo completo
    assets_summary.json                        — counts + warnings + discarded
    assets.md                                  — resumen legible (omitido con --json-only)
    sdm.json (en --out-sdm o sobreescritura)    — figure.content.src actualizado

Códigos de salida:
    0 — OK
    1 — Error fatal (input ausente, dependencia faltante, source file ilegible)
    2 — OK con advertencias (missing_alt, low_resolution, classification
         heuristica con needs_review, format_not_supported en figuras HTML)

Dependencias:
    - Python 3.9+ stdlib
    - Pillow ≥ 10 (clasificación + decodificación de bytes)  — obligatorio
    - pypdfium2 ≥ 4 (auto-extracción PDF)                    — opcional PDF
    - ebooklib + lxml (auto-extracción EPUB)                 — opcional EPUB

Si la dep opcional falta según el formato del source file, exit 1 con
instrucción de instalación (comportamiento coherente con F17-F32).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import tempfile
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"

# ============================================================
# Constants (per plan D5/D7/D12)
# ============================================================

MIN_DIMMENSION_PX = 32
MIN_WIDTH_PX = 256
MIN_HEIGHT_PX = 256
DECORATIVE_AREA_RATIO = 0.05
SCREENSHOT_ASPECTS = [(16, 9), (16, 10), (4, 3), (3, 2)]
ASPECT_TOLERANCE = 0.05
EDGE_DENSITY_MIN = 0.04
COLOR_BUCKETS_MIN = 4
MAX_LARGE_BYTES = 50 * 1024 * 1024  # 50 MB

CLASSES = ("diagram_conceptual", "screenshot", "data_figure", "decorative")

# ============================================================
# Helpers
# ============================================================


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=str(path.parent), delete=False
    ) as tf:
        tf.write(content)
        tmpname = tf.name
    Path(tmpname).replace(path)


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "wb", dir=str(path.parent), delete=False
    ) as tf:
        tf.write(data)
        tmpname = tf.name
    Path(tmpname).replace(path)


def atomic_write_json(path: Path, payload: Any) -> None:
    atomic_write_text(
        path,
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
    )


def sha256_hex(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def _detect_mime_ext(data: bytes) -> Tuple[str, str]:
    """Detect mime + extension from magic bytes. Returns (mime, ext).
    Falls back to ('image/png', '.png') if unrecognized."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ("image/png", ".png")
    if data.startswith(b"\xff\xd8\xff"):
        return ("image/jpeg", ".jpg")
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return ("image/gif", ".gif")
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return ("image/webp", ".webp")
    if data.startswith(b"%PDF-"):
        # Mistaken for PDF — not actually an image; reject
        return ("", "")
    return ("image/png", ".png")  # fallback


def _load_yaml_or_die(path: Path) -> Dict[str, Any]:
    try:
        import yaml
    except ImportError:
        sys.stderr.write(
            "PyYAML required for --classify. Install with `pip install pyyaml`.\n"
        )
        sys.exit(1)
    if not path.exists():
        sys.stderr.write(f"classify yaml not found: {path}\n")
        sys.exit(1)
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


# ============================================================
# Image classification (D5 / T5)
# ============================================================


def _classify_image(
    img_bytes: bytes, override: Optional[Dict[str, str]] = None,
    vendor: str = "", product: str = "",
) -> Dict[str, Any]:
    """Return dict with {class, classification_source, confidence, needs_review}.
    Heuristic via Pillow; override via vendor/product first."""
    # Step 1: vendor/product override
    if override:
        for key in (f"{vendor}/{product}", vendor, product):
            cls = override.get(key)
            if cls in CLASSES:
                return {
                    "class": cls,
                    "classification_source": "override",
                    "confidence": 1.0,
                    "needs_review": False,
                }

    try:
        from PIL import Image, ImageFilter
    except ImportError:
        return {
            "class": "decorative",
            "classification_source": "fallback",
            "confidence": 0.0,
            "needs_review": True,
            "_error": "Pillow not installed",
        }

    try:
        img = Image.open(io.BytesIO(img_bytes))
        img.load()
    except Exception as e:
        return {
            "class": "decorative",
            "classification_source": "fallback",
            "confidence": 0.0,
            "needs_review": True,
            "_error": f"unreadable_image:{e!r}",
        }

    w, h = img.size
    if w == 0 or h == 0:
        return {
            "class": "decorative",
            "classification_source": "fallback",
            "confidence": 0.0,
            "needs_review": True,
            "_error": "zero_dimension",
        }

    # Step 2: heuristic — decorative (size / aspect / uniform)
    min_wh = min(w, h)
    max_wh = max(w, h)
    aspect = max_wh / min_wh if min_wh > 0 else 999.0

    # Convert to RGB for histogram
    rgb = img.convert("RGB")

    # Histogram-based color diversity
    hist = rgb.histogram()
    # Each R/G/B is 256 buckets; total = 768. Count non-empty buckets across R/G/B.
    distinct_color_buckets = sum(1 for x in hist if x > 0)

    # Edge density (FIND_EDGES counts axis-aligned boundaries)
    edges = rgb.convert("L").filter(ImageFilter.FIND_EDGES)
    edge_hist = edges.histogram()
    edge_pixels = sum(c for v, c in enumerate(edge_hist) if v > 32)
    edge_density = edge_pixels / float(w * h) if w * h > 0 else 0.0

    if min_wh < MIN_DIMMENSION_PX or aspect >= 8.0 or aspect <= 1.0 / 8.0:
        return {
            "class": "decorative",
            "classification_source": "heuristic",
            "confidence": 0.7,
            "needs_review": False,
            "_reason": "tiny_or_extreme_aspect",
        }

    if distinct_color_buckets <= 2:
        return {
            "class": "decorative",
            "classification_source": "heuristic",
            "confidence": 0.6,
            "needs_review": False,
            "_reason": "monochrome",
        }

    # Step 3: heuristic — diagram_conceptual (high edge density beats screen-aspect)
    # Diagrams can have 4:3 aspect; classify by structure (edges + colors) first.
    if edge_density >= EDGE_DENSITY_MIN and distinct_color_buckets >= 8:
        return {
            "class": "diagram_conceptual",
            "classification_source": "heuristic",
            "confidence": 0.75,
            "needs_review": False,
            "_reason": "edges_and_colors",
        }

    # Step 4: heuristic — screenshot (screen aspect ratio)
    for a, b in SCREENSHOT_ASPECTS:
        target = a / b
        if abs(aspect - target) / target <= ASPECT_TOLERANCE:
            return {
                "class": "screenshot",
                "classification_source": "heuristic",
                "confidence": 0.75,
                "needs_review": False,
                "_reason": f"screen_aspect_{a}_{b}",
            }

    # Step 5: heuristic — data_figure (multi-color, fewer edges)
    if (
        edge_density < EDGE_DENSITY_MIN
        and distinct_color_buckets >= COLOR_BUCKETS_MIN
        and 0.5 <= aspect <= 2.0
    ):
        return {
            "class": "data_figure",
            "classification_source": "heuristic",
            "confidence": 0.65,
            "needs_review": False,
            "_reason": "multi_hue_charts",
        }

    # Step 6: default → decorative with needs_review
    return {
        "class": "decorative",
        "classification_source": "heuristic",
        "confidence": 0.0,
        "needs_review": True,
        "_reason": "no_rule_matched",
    }


# ============================================================
# Auto-extraction: PDF (pypdfium2) + EPUB (ebooklib)
# ============================================================


def _extract_pdf_figure(
    source_file: Path, page: int, bbox: Optional[List[float]],
) -> Optional[bytes]:
    """Rasterize one page of a PDF, optionally crop to bbox. Returns PNG bytes."""
    try:
        import pypdfium2 as pdfium
    except ImportError:
        sys.stderr.write(
            "pypdfium2 required for PDF extraction. Install with `pip install pypdfium2`.\n"
        )
        sys.exit(1)
    try:
        pdf = pdfium.PdfDocument(str(source_file))
    except Exception as e:
        sys.stderr.write(f"failed to open PDF: {e}\n")
        return None
    try:
        if page < 1 or page > len(pdf):
            return None
        p = pdf[page - 1]
        pil_img = p.render(scale=1.0).to_pil()
        if bbox and len(bbox) == 4:
            x, y, w, h = bbox
            # pypdfium2 renders top-left origin, y increases downward; bbox is
            # already in those coords (we trust F22/F18 to provide correct ones).
            x = max(0, int(x))
            y = max(0, int(y))
            w = max(1, int(w))
            h = max(1, int(h))
            pil_img = pil_img.crop((x, y, x + w, y + h))
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        return buf.getvalue()
    finally:
        try:
            pdf.close()
        except Exception:
            pass


def _extract_pdf_full_page(source_file: Path, page: int) -> Optional[bytes]:
    """Fallback: rasterize an entire page without cropping."""
    return _extract_pdf_figure(source_file, page, None)


def _epub_list_images(epub_path: Path) -> List[Tuple[str, bytes]]:
    """Return list of (filename, image_bytes) for all images inside an EPUB.
    EPUB is just a zip; we read IMAGE entries directly without ebooklib."""
    out: List[Tuple[str, bytes]] = []
    try:
        with zipfile.ZipFile(epub_path, "r") as zf:
            for name in zf.namelist():
                low = name.lower()
                if low.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
                    try:
                        with zf.open(name) as f:
                            out.append((name, f.read()))
                    except Exception:
                        continue
    except Exception as e:
        sys.stderr.write(f"failed to read EPUB: {e}\n")
    return out


def _epub_resolve(src_hint: str, images: List[Tuple[str, bytes]]) -> Optional[bytes]:
    """Match a figure.content.src hint to an EPUB image. Returns bytes or None."""
    if not src_hint:
        return None
    hint_name = src_hint.split("/")[-1].split("?")[0].lower()
    for name, data in images:
        if name.lower().endswith(hint_name):
            return data
    # Heuristic: same basename
    hint_base = hint_name.rsplit(".", 1)[0]
    for name, data in images:
        if hint_base and hint_base in name.lower():
            return data
    return None


def _epub_fallback_image(images: List[Tuple[str, bytes]]) -> Optional[bytes]:
    """Pick the first image as a fallback. Used when src doesn't match anything."""
    if images:
        return images[0][1]
    return None


# ============================================================
# Main pipeline
# ============================================================


def _walk_figure_blocks(sdm: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for sec in sdm.get("sections", []):
        for b in sec.get("blocks", []):
            if b.get("type") == "figure":
                out.append(b)
    return out


def _resolve_image_bytes(
    source_file: Path,
    fmt: str,
    block: Dict[str, Any],
    page_index_by_id: Dict[str, int],
    epub_images: Optional[List[Tuple[str, bytes]]] = None,
) -> Tuple[Optional[bytes], List[str]]:
    """Return (bytes, warnings) for a figure block."""
    warnings: List[str] = []
    bid = block.get("id")
    content = block.get("content") or {}
    src_hint = content.get("src", "")
    anchor = block.get("anchor") or {}
    page = anchor.get("page")
    bbox = anchor.get("bbox")

    if fmt == "pdf":
        if not isinstance(page, int):
            warnings.append(f"figure {bid}: page is null/unknown; cannot extract from PDF")
            return None, warnings
        data = _extract_pdf_figure(source_file, page, bbox)
        if data is None:
            warnings.append(f"figure {bid}: PDF extraction returned no data (page={page})")
        return data, warnings

    if fmt == "epub":
        if epub_images is None:
            epub_images = _epub_list_images(source_file)
        data = _epub_resolve(src_hint, epub_images)
        if data is None:
            data = _epub_fallback_image(epub_images)
            if data is not None:
                warnings.append(
                    f"figure {bid}: src {src_hint!r} did not match any EPUB image; "
                    f"using first image as fallback ({len(epub_images)} total)"
                )
        if data is None:
            warnings.append(f"figure {bid}: no images found in EPUB")
        return data, warnings

    warnings.append(f"figure {bid}: format {fmt!r} not supported by F33 (auto-extract)")
    return None, warnings


def run(
    sdm_path: Path,
    source_file: Path,
    out_dir: Path,
    out_sdm: Optional[Path],
    classify_path: Optional[Path],
    min_width: int,
    min_height: int,
    json_only: bool,
) -> int:
    sdm_path = Path(sdm_path).resolve()
    source_file = Path(source_file).resolve()
    out_dir = Path(out_dir).resolve()

    if not sdm_path.exists():
        sys.stderr.write(f"sdm not found: {sdm_path}\n")
        return 1
    if not source_file.exists():
        sys.stderr.write(f"source file not found: {source_file}\n")
        return 1
    suffix = source_file.suffix.lower()
    if suffix == ".pdf":
        fmt = "pdf"
    elif suffix == ".epub":
        fmt = "epub"
    else:
        sys.stderr.write(
            f"unsupported source format: {suffix!r}; F33 supports .pdf and .epub\n"
        )
        return 1

    try:
        sdm = json.loads(sdm_path.read_text(encoding="utf-8"))
    except Exception as e:
        sys.stderr.write(f"failed to parse sdm: {e}\n")
        return 1

    override: Dict[str, str] = {}
    if classify_path is not None:
        cfg = _load_yaml_or_die(Path(classify_path))
        rules = cfg.get("rules") or cfg.get("overrides") or cfg
        if isinstance(rules, dict):
            for k, v in rules.items():
                if v in CLASSES:
                    override[k] = v

    vendor = (sdm.get("source") or {}).get("vendor", "") or ""
    product = (sdm.get("source") or {}).get("product", "") or ""
    source_id = (sdm.get("source") or {}).get("id", "unknown")

    figures = _walk_figure_blocks(sdm)
    if not figures:
        sys.stderr.write("sdm has no figure blocks; nothing to catalog\n")

    epub_images: Optional[List[Tuple[str, bytes]]] = None

    catalog: Dict[str, Dict[str, Any]] = {}
    block_to_hash: Dict[str, str] = {}
    block_to_meta: Dict[str, Dict[str, Any]] = {}
    warnings: List[str] = []
    discarded: List[Dict[str, Any]] = []
    large_assets: List[str] = []
    missing_alt: List[str] = []
    decorative_with_alt: List[str] = []
    no_bbox_for_crop: List[str] = []
    format_not_supported: List[str] = []

    assets_root = out_dir / "assets"

    for blk in figures:
        bid = blk.get("id") or ""
        anchor = blk.get("anchor") or {}
        bbox = anchor.get("bbox")
        page = anchor.get("page")
        content = blk.get("content") or {}
        alt = (content.get("alt") or "").strip()
        src_hint = content.get("src", "")

        # Resolve bytes
        data, warns = _resolve_image_bytes(
            source_file, fmt, blk, page_index_by_id={}, epub_images=epub_images,
        )
        warnings.extend(warns)
        if data is None:
            # Could not extract: catalogue as missing
            missing_alt.append(bid)  # repurposed: list of "missing asset"
            format_not_supported.append(bid)
            continue

        if not bbox:
            no_bbox_for_crop.append(bid)

        # sha256 / dedup
        sha = sha256_hex(data)
        block_to_hash[bid] = sha

        # Already cataloged? just append referenced_by.
        if sha in catalog:
            cat = catalog[sha]
            cat["referenced_by"].append(bid)
            # update the figure's src in the SDM
            content["src"] = str((assets_root / cat["path"]).resolve())
            continue

        mime, ext = _detect_mime_ext(data)
        if not mime:
            warnings.append(f"figure {bid}: unrecognized image bytes; skipped")
            continue

        if len(data) > MAX_LARGE_BYTES:
            large_assets.append(bid)
            warnings.append(
                f"figure {bid}: large asset ({len(data)} bytes > {MAX_LARGE_BYTES})"
            )

        # Decode dimensions (optional but useful for catalog)
        width = height = 0
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(data))
            width, height = img.size
        except Exception:
            pass

        # Classification
        cls_info = _classify_image(
            data, override=override, vendor=vendor, product=product,
        )

        # Alt text rules
        if cls_info["class"] == "decorative":
            if alt:
                decorative_with_alt.append(bid)
        else:
            if len(alt) < 3:
                missing_alt.append(bid)

        # Resolution check
        if width and height and (width < min_width or height < min_height):
            warnings.append(
                f"figure {bid}: low_resolution ({width}x{height} < {min_width}x{min_height})"
            )

        # Write asset file
        rel = f"{source_id}/{sha[:16]}{ext}"
        out_path = assets_root / rel
        atomic_write_bytes(out_path, data)

        # Record catalog entry
        catalog[sha] = {
            "sha256": sha,
            "path": rel,
            "absolute_path": str(out_path.resolve()),
            "mime": mime,
            "ext": ext,
            "bytes": len(data),
            "width": width,
            "height": height,
            "class": cls_info["class"],
            "classification_source": cls_info["classification_source"],
            "confidence": cls_info["confidence"],
            "needs_review": cls_info.get("needs_review", False),
            "_reason": cls_info.get("_reason"),
            "_error": cls_info.get("_error"),
            "alt": alt,
            "referenced_by": [bid],
        }
        block_to_meta[bid] = catalog[sha]

        # Discarded = decorative
        if cls_info["class"] == "decorative":
            discarded.append({"block_id": bid, "sha256": sha, "reason": "decorative"})

        # Update SDM figure block's src to deterministic path
        content["src"] = str(out_path.resolve())
        blk["content"] = content

    # Build assets.json
    assets_catalog = {
        "schema_version": SCHEMA_VERSION,
        "source_id": source_id,
        "vendor": vendor,
        "product": product,
        "format": fmt,
        "assets": list(catalog.values()),
    }
    atomic_write_json(assets_root / "assets.json", assets_catalog)

    # Summary
    by_class = Counter(c["class"] for c in catalog.values())
    total_figure_blocks = len(figures)
    total_unique_assets = len(catalog)
    dedup_count = total_figure_blocks - total_unique_assets
    summary = {
        "schema_version": SCHEMA_VERSION,
        "source_id": source_id,
        "format": fmt,
        "total_figure_blocks": total_figure_blocks,
        "total_unique_assets": total_unique_assets,
        "dedup_count": dedup_count,
        "by_class": dict(by_class),
        "discarded": discarded,
        "missing_alt": missing_alt,
        "decorative_with_alt": decorative_with_alt,
        "format_not_supported": format_not_supported,
        "no_bbox_for_crop": no_bbox_for_crop,
        "large_assets": large_assets,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    atomic_write_json(assets_root / "assets_summary.json", summary)

    if not json_only:
        md = [
            f"# Assets catalog — `{source_id}`",
            "",
            f"- **Source format:** {fmt}",
            f"- **Figure blocks:** {total_figure_blocks}",
            f"- **Unique assets:** {total_unique_assets}",
            f"- **Dedup'd:** {dedup_count}",
            f"- **By class:** {dict(by_class)}",
            f"- **Discarded (decorative):** {len(discarded)}",
            f"- **Missing alt:** {len(missing_alt)}",
            f"- **Format not supported:** {len(format_not_supported)}",
        ]
        if warnings:
            md.append("")
            md.append("## Warnings")
            for w in warnings[:50]:
                md.append(f"- {w}")
        atomic_write_text(assets_root / "assets.md", "\n".join(md) + "\n")

    # Persist updated SDM
    out_sdm_path = Path(out_sdm).resolve() if out_sdm else sdm_path
    atomic_write_json(out_sdm_path, sdm)

    # Exit code: errors only on hard fails; warnings always exit 2.
    if not catalog and figures:
        # Found figures but couldn't extract any
        return 1
    if warnings or missing_alt or decorative_with_alt:
        return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="assets.py",
        description="F33 — Asset catalog (extract, dedup, classify, alt-validate).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Constantes (per plan F33 / D5/D7/D12):
  MIN_DIMMENSION_PX          = 32    tiny_or_extreme_aspect -> decorative
  MIN_WIDTH_PX               = 256   low_resolution warning
  MIN_HEIGHT_PX              = 256   low_resolution warning
  DECORATIVE_AREA_RATIO      = 0.05
  SCREENSHOT_ASPECTS         = [(16,9),(16,10),(4,3),(3,2)] +/- 5%
  EDGE_DENSITY_MIN           = 0.04  diagram_conceptual floor
  COLOR_BUCKETS_MIN          = 4     data_figure floor
  MAX_LARGE_BYTES            = 50 MB warning

Formatos soportados:
  pdf     via pypdfium2 (rasteriza página, crop por anchor.bbox)
  epub    via lectura ZIP directa (sin ebooklib)

Clases (4 oficiales):
  diagram_conceptual | screenshot | data_figure | decorative

Códigos de salida:
  0 OK sin advertencias
  1 error fatal (input ausente, dep faltante, source ilegible)
  2 OK con advertencias (missing_alt, low_resolution, format_not_supported)
""",
    )
    p.add_argument("--sdm", required=True, type=Path, help="Ruta a sdm.json (F31 output)")
    p.add_argument("--source-file", required=True, type=Path,
                   help="Archivo fuente original (PDF o EPUB)")
    p.add_argument("--out-dir", required=True, type=Path,
                   help="Directorio de salida (assets/ dentro)")
    p.add_argument("--out-sdm", type=Path, default=None,
                   help="Ruta para el SDM con figure.content.src actualizado (default: sobreescribe --sdm)")
    p.add_argument("--classify", type=Path, default=None,
                   help="YAML con overrides vendor/product -> class")
    p.add_argument("--min-width", type=int, default=MIN_WIDTH_PX,
                   help=f"Resolución mínima de ancho (default {MIN_WIDTH_PX})")
    p.add_argument("--min-height", type=int, default=MIN_HEIGHT_PX,
                   help=f"Resolución mínima de alto (default {MIN_HEIGHT_PX})")
    p.add_argument("--json-only", action="store_true",
                   help="Omitir assets.md")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return run(
        sdm_path=Path(args.sdm),
        source_file=Path(args.source_file),
        out_dir=Path(args.out_dir),
        out_sdm=Path(args.out_sdm) if args.out_sdm else None,
        classify_path=Path(args.classify) if args.classify else None,
        min_width=args.min_width,
        min_height=args.min_height,
        json_only=args.json_only,
    )


if __name__ == "__main__":
    sys.exit(main())
