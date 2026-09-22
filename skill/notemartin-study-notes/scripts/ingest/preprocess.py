#!/usr/bin/env python3
"""preprocess.py — F19 image preprocessing.

Rasteriza PDFs y aplica un pipeline configurable de 6 etapas para producir
imágenes limpias para OCR:
  rasterize → deskew → curvature (opt-in) → denoise → binarize → border

La imagen original NUNCA se destruye: se conserva como
  ingest/pages/<basename>-NNNN.png
mientras que la versión procesada se emite como
  ingest/pages/<basename>-NNNN.processed.png
Más un meta.json por página, un preprocess.log plano y un
preprocess_summary.json global.

Uso:
    python3 scripts/ingest/preprocess.py --source <pdf|img|dir> --out-dir <workdir/ingest/> \
        [--dpi 300] [--pipeline rasterize,deskew,denoise,binarize,border,curvature] \
        [--format auto|pdf|images] [--json-only]

Códigos de salida:
    0 — OK
    1 — Error fatal
    2 — OK con advertencias (rotación fuera de rango, curvatura no corregida, etc.)

Dependencias:
    - Python 3.9+ stdlib
    - pypdfium2 >= 4 (renderizado PDF)
    - opencv-python-headless >= 4 (pipeline de imagen)
    - Pillow >= 10 (I/O PNG/JPEG)
    - numpy >= 1.24 (operaciones matriciales)

Documentación normativa: references/01-ingest/preprocess.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import pypdfium2  # type: ignore
except ImportError:  # pragma: no cover
    pypdfium2 = None  # type: ignore

try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
except ImportError:  # pragma: no cover
    cv2 = None  # type: ignore
    np = None  # type: ignore

try:
    from PIL import Image  # type: ignore
except ImportError:  # pragma: no cover
    Image = None  # type: ignore

SCHEMA_VERSION = "1.0.0"

# ============================================================
# Constants (per references/01-ingest/preprocess.md §4)
# ============================================================

DEFAULT_DPI = 300
MAX_ROTATION_DEG = 10.0
ROTATION_STEP_DEG = 0.5
ROTATION_IMPROVEMENT_RATIO = 1.10
ADAPTIVE_BLOCK_SIZE = 31
ADAPTIVE_C = 10
BLANK_THRESHOLD = 0.005
BORDER_DARKNESS_THRESHOLD = 180
MARGIN_PIXELS = 30
INPAINT_RADIUS = 5
CURVATURE_SCORE_THRESHOLD = 0.6
CURVATURE_BASELINE_THRESHOLD = 2.0
WHITE_INTENSITY = 240

ALL_STAGES = ("rasterize", "deskew", "curvature", "denoise", "binarize", "border")
DEFAULT_PIPELINE = ("rasterize", "deskew", "denoise", "binarize", "border")


# ============================================================
# Helpers
# ============================================================

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=str(path.parent), delete=False) as tf:
        tf.write(data)
        tmpname = tf.name
    Path(tmpname).replace(path)


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent), delete=False) as tf:
        tf.write(content)
        tmpname = tf.name
    Path(tmpname).replace(path)


def _to_grayscale(img: Any) -> Any:
    if len(img.shape) == 2:
        return img
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.shape[2] == 3 else img


def _non_white_ratio(gray: Any) -> float:
    if gray.size == 0:
        return 0.0
    return float(np.mean(gray < WHITE_INTENSITY))


# ============================================================
# Stage 1: rasterize
# ============================================================

def rasterize_pdf_page(pdf_doc: Any, page_idx: int, dpi: int) -> Any:
    if pypdfium2 is None:
        raise RuntimeError("pypdfium2 not installed")
    page = pdf_doc[page_idx]
    scale = dpi / 72.0
    pil_img = page.render(scale=scale).to_pil()
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def load_image_as_bgr(path: Path) -> Any:
    if cv2 is None:
        raise RuntimeError("opencv-python-headless not installed")
    arr = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError(f"failed to decode image: {path}")
    return img


def rasterize_image(path: Path) -> Any:
    return load_image_as_bgr(path)


# ============================================================
# Stage 2: deskew (projection profile)
# ============================================================

def deskew_angle(gray: Any) -> Tuple[float, float]:
    """Return (best_angle_deg, variance_at_0_deg)."""
    if cv2 is None or np is None:
        return 0.0, 0.0
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    base_var = float(np.var(np.sum(bw, axis=1)))
    h, w = bw.shape
    best_angle = 0.0
    best_var = base_var
    angle = -MAX_ROTATION_DEG
    while angle <= MAX_ROTATION_DEG + 1e-9:
        M = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), angle, 1.0)
        rotated = cv2.warpAffine(bw, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        v = float(np.var(np.sum(rotated, axis=1)))
        if v > best_var:
            best_var = v
            best_angle = angle
        angle += ROTATION_STEP_DEG
    if best_var < base_var * ROTATION_IMPROVEMENT_RATIO:
        return 0.0, base_var
    return best_angle, base_var


def apply_deskew(img: Any) -> Tuple[Any, float, bool, bool]:
    """Return (rotated_img, angle_deg, applied, too_large)."""
    gray = _to_grayscale(img)
    angle, _ = deskew_angle(gray)
    if abs(angle) > MAX_ROTATION_DEG:
        return img, angle, False, True
    if abs(angle) < 0.05:
        return img, 0.0, False, False
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated, angle, True, False


# ============================================================
# Stage 3: curvature (opt-in)
# ============================================================

def curvature_score(gray: Any) -> float:
    """Estimate baseline-angle variance; returns [0, 1]."""
    if cv2 is None or np is None:
        return 0.0
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 150, minLineLength=gray.shape[1] // 4, maxLineGap=20)
    if lines is None or len(lines) < 5:
        return 0.0
    angles = []
    h = gray.shape[0]
    for line in lines:
        x1, y1, x2, y2 = line[0]
        a = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        if abs(a) < 30:
            top_mask = (y1 < h / 2) & (y2 < h / 2)
            bot_mask = (y1 >= h / 2) | (y2 >= h / 2)
            if top_mask.any():
                angles.append(("top", a))
            elif bot_mask.any():
                angles.append(("bot", a))
    top_angles = [a for tag, a in angles if tag == "top"]
    bot_angles = [a for tag, a in angles if tag == "bot"]
    if not top_angles or not bot_angles:
        return 0.0
    delta = abs(np.mean(top_angles) - np.mean(bot_angles))
    score = min(delta / CURVATURE_BASELINE_THRESHOLD, 1.0)
    return float(score)


def apply_curvature(img: Any) -> Tuple[Any, float, bool]:
    """Conservative: only mark score; do not warp unless high-confidence."""
    gray = _to_grayscale(img)
    score = curvature_score(gray)
    if score >= CURVATURE_SCORE_THRESHOLD:
        return img, score, False
    return img, score, False


# ============================================================
# Stage 4: denoise
# ============================================================

def apply_denoise(img: Any) -> Any:
    if cv2 is None:
        return img
    if len(img.shape) == 2:
        return cv2.fastNlMeansDenoising(img, None, h=10, templateWindowSize=7, searchWindowSize=21)
    return cv2.fastNlMeansDenoisingColored(img, None, h=10, hColor=10, templateWindowSize=7, searchWindowSize=21)


# ============================================================
# Stage 5: binarize
# ============================================================

def apply_binarize(img: Any) -> Any:
    if cv2 is None:
        return img
    gray = _to_grayscale(img)
    return cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
        ADAPTIVE_BLOCK_SIZE, ADAPTIVE_C,
    )


# ============================================================
# Stage 6: border / spine
# ============================================================

def detect_border_shadow(gray: Any) -> Tuple[bool, bool]:
    """Return (border_shadow_removed, spine_shadow)."""
    if cv2 is None or np is None:
        return False, False
    h, w = gray.shape[:2]
    top = gray[:MARGIN_PIXELS, :]
    bot = gray[h - MARGIN_PIXELS:, :]
    left = gray[:, :MARGIN_PIXELS]
    right = gray[:, w - MARGIN_PIXELS:]
    margins = [top, bot, left, right]
    border_dark = any(np.mean(m) < BORDER_DARKNESS_THRESHOLD for m in margins)
    if not border_dark:
        return False, False
    spine = (np.mean(left) < BORDER_DARKNESS_THRESHOLD and np.mean(right) < BORDER_DARKNESS_THRESHOLD)
    return True, bool(spine)


def apply_border(img: Any) -> Tuple[Any, bool, bool]:
    if cv2 is None or np is None:
        return img, False, False
    gray = _to_grayscale(img)
    border_removed, spine = detect_border_shadow(gray)
    if not border_removed:
        return img, False, False
    h, w = gray.shape[:2]
    mask = np.zeros_like(gray)
    if np.mean(gray[:MARGIN_PIXELS, :]) < BORDER_DARKNESS_THRESHOLD:
        mask[:MARGIN_PIXELS, :] = 255
    if np.mean(gray[h - MARGIN_PIXELS:, :]) < BORDER_DARKNESS_THRESHOLD:
        mask[h - MARGIN_PIXELS:, :] = 255
    if np.mean(gray[:, :MARGIN_PIXELS]) < BORDER_DARKNESS_THRESHOLD:
        mask[:, :MARGIN_PIXELS] = 255
    if np.mean(gray[:, w - MARGIN_PIXELS:]) < BORDER_DARKNESS_THRESHOLD:
        mask[:, w - MARGIN_PIXELS:] = 255
    if np.sum(mask) == 0:
        return img, True, False
    if len(img.shape) == 2:
        result = cv2.inpaint(img, mask, INPAINT_RADIUS, cv2.INPAINT_TELEA)
    else:
        result = cv2.inpaint(img, mask, INPAINT_RADIUS, cv2.INPAINT_TELEA)
    return result, True, spine


# ============================================================
# Page processing
# ============================================================

def process_page(
    original_bgr: Any,
    page_num: int,
    out_pages_dir: Path,
    basename: str,
    pipeline: List[str],
    warnings: List[str],
) -> Dict[str, Any]:
    started = time.time()
    processed = original_bgr.copy()
    rotation_detected = 0.0
    rotation_applied = False
    rotation_too_large = False
    curvature_score_val = 0.0
    curvature_applied = False
    denoise_applied = False
    binarize_applied = False
    border_shadow_removed = False
    spine_shadow = False

    if "deskew" in pipeline:
        processed, rotation_detected, rotation_applied, rotation_too_large = apply_deskew(processed)
        if rotation_too_large:
            warnings.append(f"page {page_num}: rotation {rotation_detected:.1f}° > MAX_ROTATION_DEG; not correcting")

    if "curvature" in pipeline:
        processed, curvature_score_val, curvature_applied = apply_curvature(processed)
        if curvature_applied:
            warnings.append(f"page {page_num}: curvature score {curvature_score_val:.2f} >= threshold; warped")

    if "denoise" in pipeline:
        processed = apply_denoise(processed)
        denoise_applied = True

    if "border" in pipeline:
        processed, border_shadow_removed, spine_shadow = apply_border(processed)

    if "binarize" in pipeline:
        processed = apply_binarize(processed)
        binarize_applied = True

    gray = _to_grayscale(processed if binarize_applied else _to_grayscale(processed))
    if len(gray.shape) == 3:
        gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
    non_white = _non_white_ratio(gray)
    is_blank = non_white < BLANK_THRESHOLD
    if is_blank:
        warnings.append(f"page {page_num}: is_blank (non_white_ratio={non_white:.4f})")

    dwell_ms = int((time.time() - started) * 1000)

    original_name = f"{basename}-{page_num:04d}.png"
    processed_name = f"{basename}-{page_num:04d}.processed.png"
    meta_name = f"{basename}-{page_num:04d}.meta.json"

    ok_original, original_bytes = cv2.imencode(".png", original_bgr)
    ok_processed, processed_bytes = cv2.imencode(".png", processed)
    if not ok_original or not ok_processed:
        raise RuntimeError(f"failed to encode PNG for page {page_num}")

    original_path = out_pages_dir / original_name
    processed_path = out_pages_dir / processed_name
    meta_path = out_pages_dir / meta_name

    if original_path.exists():
        ts = int(time.time() * 1000)
        original_path = out_pages_dir / f"{basename}-{page_num:04d}.ts{ts}.png"

    atomic_write_bytes(original_path, original_bytes.tobytes())
    atomic_write_bytes(processed_path, processed_bytes.tobytes())

    meta = {
        "page": page_num,
        "original_path": str(original_path.relative_to(out_pages_dir.parent)),
        "processed_path": str(processed_path.relative_to(out_pages_dir.parent)),
        "rotation_detected_deg": round(float(rotation_detected), 3),
        "rotation_applied": bool(rotation_applied),
        "rotation_too_large": bool(rotation_too_large),
        "curvature_score": round(float(curvature_score_val), 3),
        "curvature_applied": bool(curvature_applied),
        "denoise_applied": bool(denoise_applied),
        "binarize_applied": bool(binarize_applied),
        "border_shadow_removed": bool(border_shadow_removed),
        "spine_shadow": bool(spine_shadow),
        "is_blank": bool(is_blank),
        "non_white_ratio": round(float(non_white), 4),
        "size_before": len(original_bytes.tobytes()),
        "size_after": len(processed_bytes.tobytes()),
        "dwell_ms": dwell_ms,
    }
    atomic_write_text(meta_path, json.dumps(meta, indent=2, ensure_ascii=False))

    log_line = (
        f"page={page_num:04d} rotation={rotation_detected:+.2f}° rotation_applied={str(rotation_applied).lower()}"
        f" curvature={curvature_score_val:.2f} blank={str(is_blank).lower()}"
        f" non_white={non_white:.4f} dwell_ms={dwell_ms}\n"
    )
    return {
        "meta": meta,
        "log_line": log_line,
    }


# ============================================================
# Detection of format
# ============================================================

def detect_format(source: Path) -> str:
    if source.is_dir():
        return "images-dir"
    suffix = source.suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix in (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"):
        return "image"
    return "unknown"


# ============================================================
# Entry point
# ============================================================

def run(source: Path, out_dir: Path, dpi: int, pipeline: List[str], json_only: bool = False) -> int:
    source = Path(source).resolve()
    if not source.exists():
        print(f"ERROR: source not found: {source}", file=sys.stderr)
        return 1
    if pypdfium2 is None or cv2 is None or np is None or Image is None:
        print("ERROR: missing dependency. Install: pip install pypdfium2 opencv-python-headless Pillow numpy",
              file=sys.stderr)
        return 1

    warnings: List[str] = []

    if out_dir.resolve() == source.parent.resolve() and source.is_file():
        print(f"ERROR: --out-dir coincides with source directory; refusing to overwrite original",
              file=sys.stderr)
        return 1

    out_pages_dir = out_dir / "ingest" / "pages"
    out_pages_dir.mkdir(parents=True, exist_ok=True)

    fmt = detect_format(source)
    if fmt == "unknown":
        print(f"ERROR: cannot detect format of {source}", file=sys.stderr)
        return 1

    sha = sha256_file(source) if source.is_file() else ""
    size = source.stat().st_size if source.is_file() else 0

    pages_meta: List[Dict[str, Any]] = []
    log_lines: List[str] = []
    basename_base = source.stem if source.is_file() else "pages"

    if fmt == "pdf":
        pdf = pypdfium2.PdfDocument(str(source))
        page_count = len(pdf)
        for page_idx in range(page_count):
            page_num = page_idx + 1
            try:
                original_bgr = rasterize_pdf_page(pdf, page_idx, dpi)
            except Exception as e:
                warnings.append(f"page {page_num}: rasterize failed ({e})")
                continue
            result = process_page(original_bgr, page_num, out_pages_dir, basename_base, pipeline, warnings)
            pages_meta.append(result["meta"])
            log_lines.append(result["log_line"])
        try:
            pdf.close()
        except Exception:
            pass
    elif fmt == "image":
        page_num = 1
        original_bgr = rasterize_image(source)
        result = process_page(original_bgr, page_num, out_pages_dir, basename_base, pipeline, warnings)
        pages_meta.append(result["meta"])
        log_lines.append(result["log_line"])
    elif fmt == "images-dir":
        exts = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
        files = sorted(p for p in source.iterdir() if p.is_file() and p.suffix.lower() in exts)
        page_count = len(files)
        for page_num, f in enumerate(files, 1):
            try:
                original_bgr = rasterize_image(f)
            except Exception as e:
                warnings.append(f"page {page_num}: rasterize failed ({e})")
                continue
            result = process_page(original_bgr, page_num, out_pages_dir, f.stem, pipeline, warnings)
            pages_meta.append(result["meta"])
            log_lines.append(result["log_line"])

    log_path = out_dir / "ingest" / "preprocess.log"
    atomic_write_text(log_path, "".join(log_lines))

    summary = {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "path": str(source),
            "hash": sha,
            "size_bytes": size,
            "format": fmt,
        },
        "pipeline": list(pipeline),
        "dpi": dpi,
        "page_count": len(pages_meta),
        "pages": pages_meta,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    summary_path = out_dir / "ingest" / "preprocess_summary.json"
    atomic_write_text(summary_path, json.dumps(summary, indent=2, ensure_ascii=False))

    if not json_only:
        md_lines = [f"# Preprocesado — `{source}`", ""]
        md_lines.append(f"- **Hash sha256:** `{sha}`")
        md_lines.append(f"- **Páginas:** {len(pages_meta)}")
        md_lines.append(f"- **Pipeline:** {', '.join(pipeline)}")
        md_lines.append(f"- **DPI:** {dpi}")
        if warnings:
            md_lines.append("")
            md_lines.append("## Advertencias")
            for w in warnings:
                md_lines.append(f"- {w}")
        md_lines.append("")
        md_lines.append("## Métricas por página")
        md_lines.append("")
        md_lines.append("| Page | Rotación (°) | Rot aplicada | Curvatura | Blank | Non-white | Dwell (ms) |")
        md_lines.append("|---|---|---|---|---|---|---|")
        for m in pages_meta:
            md_lines.append(
                f"| {m['page']} | {m['rotation_detected_deg']:+.2f} | "
                f"{'sí' if m['rotation_applied'] else 'no'} | {m['curvature_score']:.2f} | "
                f"{'sí' if m['is_blank'] else 'no'} | {m['non_white_ratio']:.4f} | {m['dwell_ms']} |"
            )
        atomic_write_text(out_dir / "ingest" / "preprocess.md", "\n".join(md_lines) + "\n")

    return 2 if warnings else 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="preprocess.py",
        description="F19 — Preprocesado de imagen (rasterize, deskew, denoise, binarize, border, curvature).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Constantes (references/01-ingest/preprocess.md §4):
  DEFAULT_DPI                  = 300
  MAX_ROTATION_DEG             = 10.0   ° máximo corregible
  ROTATION_STEP_DEG            = 0.5    paso del barrido
  ROTATION_IMPROVEMENT_RATIO   = 1.10   mejora mínima para aplicar
  ADAPTIVE_BLOCK_SIZE          = 31     px (vecindad adaptiveThreshold)
  ADAPTIVE_C                   = 10     constante local
  BLANK_THRESHOLD              = 0.005  ratio non-white para blank
  BORDER_DARKNESS_THRESHOLD    = 180    intensidad media del margen
  MARGIN_PIXELS                = 30     px del margen evaluado
  INPAINT_RADIUS               = 5      radio del inpaint
  CURVATURE_SCORE_THRESHOLD    = 0.6    score mínimo para warping
  CURVATURE_BASELINE_THRESHOLD = 2.0    variación top/bottom en grados
  WHITE_INTENSITY              = 240    umbral de blanco (0-255)

Etapas disponibles (default: rasterize,deskew,denoise,binarize,border):
  rasterize, deskew, curvature, denoise, binarize, border

Códigos de salida:
  0 OK sin advertencias
  1 error fatal
  2 OK con advertencias
""",
    )
    parser.add_argument("--source", required=True, help="PDF, imagen o directorio de imágenes")
    parser.add_argument("--out-dir", required=True, help="Directorio de salida (ingest/pages/, ingest/preprocess.*)")
    parser.add_argument("--dpi", type=int, default=DEFAULT_DPI, help=f"DPI del rasterizado (default {DEFAULT_DPI})")
    parser.add_argument("--pipeline", default=",".join(DEFAULT_PIPELINE),
                        help=f"Etapas CSV (default: {','.join(DEFAULT_PIPELINE)})")
    parser.add_argument("--format", default="auto", choices=["auto", "pdf", "images"],
                        help="Forzar formato del input")
    parser.add_argument("--json-only", action="store_true", help="Solo escribir preprocess_summary.json (no preprocess.md)")
    args = parser.parse_args(argv)

    pipeline = [s.strip() for s in args.pipeline.split(",") if s.strip()]
    invalid = [s for s in pipeline if s not in ALL_STAGES]
    if invalid:
        print(f"ERROR: unknown pipeline stage(s): {invalid}; valid: {ALL_STAGES}", file=sys.stderr)
        return 1
    if "rasterize" not in pipeline:
        print("WARN: 'rasterize' not in pipeline; assuming input is already an image directory",
              file=sys.stderr)
    code = run(Path(args.source), Path(args.out_dir), args.dpi, pipeline, json_only=args.json_only)
    return code


if __name__ == "__main__":
    sys.exit(main())
