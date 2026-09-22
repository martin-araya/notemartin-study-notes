#!/usr/bin/env python3
"""ocr.py — F20 multilingual OCR engine.

Ejecuta OCR sobre las imágenes preprocesadas por F19 con Tesseract como motor
principal y EasyOCR como alternativo. Implementa la interfaz OCREngine,
reintentos en cascada cuando la confianza media cae bajo el umbral, y
producción de words[] con bbox + confianza por palabra.

Uso:
    python3 scripts/ingest/ocr.py --source <dir|img> --out-dir <dir> \
        [--languages "spa+eng"] [--engine tesseract|easyocr|auto] \
        [--user-words <path>] [--user-patterns <path>] [--json-only]

Salidas (en <out-dir>/ingest/ocr/):
    ocr_summary.json — resumen global con retries y configuración
    ocr_pages/<basename>-NNNN.json — palabras por página

Códigos de salida:
    0 — OK
    1 — Error fatal (motor no instalado, imagen ilegible)
    2 — OK con advertencias (reintentos disparados, motor alternativo usado, etc.)

Dependencias:
    - Python 3.9+ stdlib
    - pytesseract >= 0.3.10 (recomendado; motor Tesseract)
    - Tesseract 5.x binario (externo; ver ocr-engines.md §6)
    - easyocr (opcional; motor alternativo, lazy import)

Documentación normativa: references/01-ingest/ocr-engines.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from PIL import Image  # type: ignore
except ImportError:  # pragma: no cover
    Image = None  # type: ignore

try:
    import pytesseract  # type: ignore
except ImportError:  # pragma: no cover
    pytesseract = None  # type: ignore

try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
except ImportError:  # pragma: no cover
    cv2 = None  # type: ignore
    np = None  # type: ignore

SCHEMA_VERSION = "1.0.0"

# ============================================================
# Constants (per references/01-ingest/ocr-engines.md)
# ============================================================

OCR_RETRY_THRESHOLD = 0.70
OCR_MIN_WORDS = 5
OCR_MAX_RETRIES = 3
OCR_DEFAULT_LANGS = "spa+eng"
OCR_DEFAULT_PSM = 6
OCR_SPARSE_PSM = 11
OCR_CONFIDENCE_NEG_SENTINEL = -1
OCR_BBOX_MIN_PX = 1


# ============================================================
# Helpers
# ============================================================

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def sha256_dir_or_file(path: Path) -> str:
    if path.is_file():
        return sha256_file(path)
    h = hashlib.sha256()
    for p in sorted(path.iterdir()):
        if p.is_file():
            h.update(sha256_file(p).encode("utf-8"))
    return h.hexdigest()


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent), delete=False) as tf:
        tf.write(content)
        tmpname = tf.name
    Path(tmpname).replace(path)


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=str(path.parent), delete=False) as tf:
        tf.write(data)
        tmpname = tf.name
    Path(tmpname).replace(path)


def invert_image_inplace(path: Path) -> Path:
    """Write an inverted copy and return its path."""
    if cv2 is None or np is None:
        return path
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return path
    inv = cv2.bitwise_not(img)
    out_path = path.with_name(path.stem + ".inverted" + path.suffix)
    cv2.imwrite(str(out_path), inv)
    return out_path


def is_blank_from_meta(meta_path: Optional[Path]) -> bool:
    if meta_path is None or not meta_path.exists():
        return False
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        return bool(meta.get("is_blank", False))
    except Exception:
        return False


# ============================================================
# OCR Engine interface
# ============================================================

class OCREngine(ABC):
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def available(self) -> bool: ...

    @abstractmethod
    def recognize(
        self,
        image_path: Path,
        languages: List[str],
        user_words_path: Optional[Path],
        user_patterns_path: Optional[Path],
        psm: int,
    ) -> Dict[str, Any]: ...


# ============================================================
# Tesseract engine
# ============================================================

class TesseractEngine(OCREngine):
    def name(self) -> str:
        return "tesseract"

    def available(self) -> bool:
        if pytesseract is None:
            return False
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def recognize(
        self,
        image_path: Path,
        languages: List[str],
        user_words_path: Optional[Path],
        user_patterns_path: Optional[Path],
        psm: int,
    ) -> Dict[str, Any]:
        if pytesseract is None:
            raise RuntimeError("pytesseract not installed")
        if Image is None:
            raise RuntimeError("Pillow not installed")
        img = Image.open(image_path)
        lang_str = "+".join(languages) if languages else "eng"
        config_parts = [f"--psm {psm}"]
        if user_words_path and user_words_path.exists():
            config_parts.append(f"--user-words {str(user_words_path)}")
        if user_patterns_path and user_patterns_path.exists():
            config_parts.append(f"--user-patterns {str(user_patterns_path)}")
        config = " ".join(config_parts)
        try:
            data = pytesseract.image_to_data(
                img, lang=lang_str, config=config,
                output_type=pytesseract.Output.DICT,
            )
        except pytesseract.TesseractError as e:
            return {
                "words": [],
                "mean_conf": 0.0,
                "engine": self.name(),
                "lang_used": lang_str,
                "error": str(e),
                "dwell_ms": 0,
            }
        words: List[Dict[str, Any]] = []
        confs: List[float] = []
        n = len(data.get("text", []))
        for i in range(n):
            text = (data["text"][i] or "").strip()
            if not text:
                continue
            try:
                conf = float(data["conf"][i])
            except (TypeError, ValueError):
                continue
            if conf < 0:
                continue
            left = int(data["left"][i])
            top = int(data["top"][i])
            width = int(data["width"][i])
            height = int(data["height"][i])
            if width < OCR_BBOX_MIN_PX or height < OCR_BBOX_MIN_PX:
                continue
            words.append({
                "text": text,
                "bbox": [left, top, width, height],
                "conf": round(conf, 2),
                "page": int(data["page_num"][i]) or 1,
                "block": int(data["block_num"][i]) or 0,
                "par": int(data["par_num"][i]) or 0,
                "line": int(data["line_num"][i]) or 0,
                "word": int(data["word_num"][i]) or 0,
            })
            confs.append(conf)
        mean_conf = round(sum(confs) / len(confs) / 100.0, 4) if confs else 0.0
        return {
            "words": words,
            "mean_conf": mean_conf,
            "engine": self.name(),
            "lang_used": lang_str,
            "dwell_ms": 0,
        }


# ============================================================
# EasyOCR engine (lazy)
# ============================================================

class EasyOCREngine(OCREngine):
    def __init__(self) -> None:
        self._reader = None
        self._languages: List[str] = []

    def name(self) -> str:
        return "easyocr"

    def available(self) -> bool:
        try:
            import easyocr  # type: ignore # noqa: F401
            return True
        except ImportError:
            return False

    def _ensure_reader(self, languages: List[str]) -> None:
        if self._reader is not None and self._languages == languages:
            return
        import easyocr  # type: ignore
        lang_map = {"spa": "es", "eng": "en", "deu": "de", "fra": "fr", "ita": "it", "por": "pt"}
        mapped = [lang_map.get(l.lower(), l.lower()) for l in languages]
        self._reader = easyocr.Reader(mapped, gpu=False, verbose=False)
        self._languages = list(languages)

    def recognize(
        self,
        image_path: Path,
        languages: List[str],
        user_words_path: Optional[Path],
        user_patterns_path: Optional[Path],
        psm: int,
    ) -> Dict[str, Any]:
        self._ensure_reader(languages)
        if self._reader is None:
            raise RuntimeError("easyocr reader not initialized")
        started = time.time()
        results = self._reader.readtext(str(image_path), detail=1, paragraph=False)
        words: List[Dict[str, Any]] = []
        confs: List[float] = []
        for idx, item in enumerate(results, 1):
            if len(item) != 3:
                continue
            bbox_pts, text, conf = item
            text = (text or "").strip()
            if not text or conf is None:
                continue
            xs = [p[0] for p in bbox_pts]
            ys = [p[1] for p in bbox_pts]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            width = int(x_max - x_min)
            height = int(y_max - y_min)
            if width < OCR_BBOX_MIN_PX or height < OCR_BBOX_MIN_PX:
                continue
            words.append({
                "text": text,
                "bbox": [int(x_min), int(y_min), width, height],
                "conf": round(float(conf) * 100.0, 2),
                "page": 1,
                "block": 1, "par": 1, "line": 1, "word": idx,
            })
            confs.append(float(conf))
        mean_conf = round(sum(confs) / len(confs), 4) if confs else 0.0
        dwell_ms = int((time.time() - started) * 1000)
        return {
            "words": words,
            "mean_conf": mean_conf,
            "engine": self.name(),
            "lang_used": ",".join(languages),
            "dwell_ms": dwell_ms,
        }


# ============================================================
# Retry logic
# ============================================================

def run_with_retries(
    image_path: Path,
    primary: OCREngine,
    alt: Optional[OCREngine],
    languages: List[str],
    user_words_path: Optional[Path],
    user_patterns_path: Optional[Path],
    warnings: List[str],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Run OCR with cascading retries. Returns (best_result, retries_list)."""
    retries: List[Dict[str, Any]] = []
    candidates: List[Tuple[str, Dict[str, Any]]] = []

    started_initial = time.time()
    initial = primary.recognize(image_path, languages, user_words_path, user_patterns_path, OCR_DEFAULT_PSM)
    initial.setdefault("dwell_ms", int((time.time() - started_initial) * 1000))
    candidates.append(("initial", initial))

    initial_conf = initial.get("mean_conf", 0.0)
    initial_words_count = len(initial.get("words", []))
    if initial_conf >= OCR_RETRY_THRESHOLD or initial_words_count <= OCR_MIN_WORDS:
        return initial, []

    retries.append({
        "page": 1, "attempt": 1,
        "reason": f"mean_conf={initial_conf:.4f} < {OCR_RETRY_THRESHOLD}",
        "action": "invert", "resulting_mean_conf": 0.0, "succeeded": False,
    })
    warnings.append(f"retry 1: mean_conf={initial_conf:.4f} < threshold; trying invert")
    inverted_path = invert_image_inplace(image_path)
    try:
        started = time.time()
        inv_result = primary.recognize(inverted_path, languages, user_words_path, user_patterns_path, OCR_DEFAULT_PSM)
        inv_result.setdefault("dwell_ms", int((time.time() - started) * 1000))
        candidates.append(("invert", inv_result))
        retries[-1]["resulting_mean_conf"] = inv_result.get("mean_conf", 0.0)
        retries[-1]["succeeded"] = inv_result.get("mean_conf", 0.0) >= OCR_RETRY_THRESHOLD
    finally:
        try:
            inverted_path.unlink()
        except FileNotFoundError:
            pass

    if alt is not None and alt.available():
        retries.append({
            "page": 1, "attempt": 2,
            "reason": f"mean_conf<{OCR_RETRY_THRESHOLD} after invert",
            "action": "alternative_engine", "resulting_mean_conf": 0.0, "succeeded": False,
        })
        warnings.append(f"retry 2: trying alternative engine {alt.name()}")
        try:
            started = time.time()
            alt_result = alt.recognize(image_path, languages, user_words_path, user_patterns_path, OCR_DEFAULT_PSM)
            alt_result.setdefault("dwell_ms", int((time.time() - started) * 1000))
            candidates.append(("alternative", alt_result))
            retries[-1]["resulting_mean_conf"] = alt_result.get("mean_conf", 0.0)
            retries[-1]["succeeded"] = alt_result.get("mean_conf", 0.0) >= OCR_RETRY_THRESHOLD
        except Exception as e:
            warnings.append(f"alternative engine failed: {e}")
    else:
        warnings.append(f"retry 2: alternative engine {alt.name() if alt else 'none'} not available; skipping")

    if not any(c[1].get("mean_conf", 0.0) >= OCR_RETRY_THRESHOLD for c in candidates):
        retries.append({
            "page": 1, "attempt": 3,
            "reason": f"mean_conf<{OCR_RETRY_THRESHOLD} after invert+alt",
            "action": "sparse_psm", "resulting_mean_conf": 0.0, "succeeded": False,
        })
        warnings.append(f"retry 3: trying sparse_psm={OCR_SPARSE_PSM}")
        try:
            started = time.time()
            sparse_result = primary.recognize(image_path, languages, user_words_path, user_patterns_path, OCR_SPARSE_PSM)
            sparse_result.setdefault("dwell_ms", int((time.time() - started) * 1000))
            candidates.append(("sparse_psm", sparse_result))
            retries[-1]["resulting_mean_conf"] = sparse_result.get("mean_conf", 0.0)
            retries[-1]["succeeded"] = sparse_result.get("mean_conf", 0.0) >= OCR_RETRY_THRESHOLD
        except Exception as e:
            warnings.append(f"sparse_psm retry failed: {e}")

    best_name, best_result = max(candidates, key=lambda c: c[1].get("mean_conf", 0.0))
    if best_result.get("mean_conf", 0.0) < OCR_RETRY_THRESHOLD and len(best_result.get("words", [])) > OCR_MIN_WORDS:
        warnings.append(f"no retry reached threshold; using best={best_result.get('mean_conf', 0.0):.4f}")
    return best_result, retries


# ============================================================
# Page processing
# ============================================================

def process_image(
    image_path: Path,
    page_num: int,
    out_pages_dir: Path,
    primary: OCREngine,
    alt: Optional[OCREngine],
    languages: List[str],
    user_words_path: Optional[Path],
    user_patterns_path: Optional[Path],
    warnings: List[str],
) -> Dict[str, Any]:
    if is_blank_from_meta(image_path.with_name(image_path.stem.replace(".processed", "") + ".meta.json")):
        return {
            "page": page_num,
            "is_blank": True,
            "words": [],
            "mean_conf": 0.0,
            "engine_used": primary.name(),
            "retries_for_page": 0,
            "dwell_ms": 0,
        }

    best, retries = run_with_retries(
        image_path, primary, alt, languages, user_words_path, user_patterns_path, warnings,
    )
    page_words = best.get("words", [])

    page_json = {
        "page": page_num,
        "is_blank": False,
        "words": page_words,
        "mean_conf": round(best.get("mean_conf", 0.0) * 100.0, 2),
        "engine_used": best.get("engine", primary.name()),
        "retries_for_page": len(retries),
        "dwell_ms": best.get("dwell_ms", 0),
    }
    for r in retries:
        r["page"] = page_num

    page_path = out_pages_dir / f"{image_path.stem}.json"
    atomic_write_text(page_path, json.dumps(page_json, indent=2, ensure_ascii=False))

    return page_json | {"retries": retries}


# ============================================================
# Format detection
# ============================================================

def detect_format(source: Path) -> str:
    if source.is_dir():
        return "images-dir"
    suffix = source.suffix.lower()
    if suffix in (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"):
        return "image"
    return "unknown"


# ============================================================
# CLI helpers
# ============================================================

def load_wordlist(path: Path) -> Optional[Path]:
    if path.exists() and path.is_file():
        return path
    return None


# ============================================================
# Entry point
# ============================================================

def run(
    source: Path,
    out_dir: Path,
    languages: List[str],
    engine_name: str,
    user_words_path: Optional[Path],
    user_patterns_path: Optional[Path],
    json_only: bool = False,
) -> int:
    source = Path(source).resolve()
    if not source.exists():
        print(f"ERROR: source not found: {source}", file=sys.stderr)
        return 1
    if source.is_file() and source.suffix.lower() == ".pdf":
        print("ERROR: PDF input not supported; F19 rasterizes to PNG. Run F19 first or pass a PNG/JPEG.",
              file=sys.stderr)
        return 1

    warnings: List[str] = []

    primary: OCREngine
    alt: Optional[OCREngine]
    if engine_name == "auto":
        tess = TesseractEngine()
        easy = EasyOCREngine()
        if tess.available():
            primary = tess
            alt = easy if easy.available() else None
        elif easy.available():
            primary = easy
            alt = None
            warnings.append("Tesseract not available; using EasyOCR as primary")
        else:
            print("ERROR: no OCR engine available. Install Tesseract (see references/01-ingest/ocr-engines.md §6).",
                  file=sys.stderr)
            return 1
    elif engine_name == "tesseract":
        tess = TesseractEngine()
        if not tess.available():
            print("ERROR: Tesseract not available. See references/01-ingest/ocr-engines.md §6.",
                  file=sys.stderr)
            return 1
        primary = tess
        easy = EasyOCREngine()
        alt = easy if easy.available() else None
    elif engine_name == "easyocr":
        easy = EasyOCREngine()
        if not easy.available():
            print("ERROR: EasyOCR not available. Install: pip install easyocr", file=sys.stderr)
            return 1
        primary = easy
        alt = None
    else:
        print(f"ERROR: unknown engine: {engine_name}", file=sys.stderr)
        return 1

    out_ocr_dir = out_dir / "ingest" / "ocr"
    out_pages_dir = out_ocr_dir / "ocr_pages"
    out_pages_dir.mkdir(parents=True, exist_ok=True)

    sha = sha256_dir_or_file(source)
    size = source.stat().st_size if source.is_file() else sum(p.stat().st_size for p in source.rglob("*") if p.is_file())

    fmt = detect_format(source)
    if fmt == "unknown":
        print(f"ERROR: cannot detect format of {source}", file=sys.stderr)
        return 1

    images: List[Tuple[int, Path]] = []
    if fmt == "image":
        images.append((1, source))
    else:
        exts = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
        processed_files = sorted(p for p in source.iterdir() if p.is_file() and p.name.endswith(".processed.png"))
        for page_idx, p in enumerate(processed_files, 1):
            images.append((page_idx, p))
        if not processed_files:
            other_files = sorted(p for p in source.iterdir() if p.is_file() and p.suffix.lower() in exts)
            for page_idx, p in enumerate(other_files, 1):
                images.append((page_idx, p))

    pages_meta: List[Dict[str, Any]] = []
    all_retries: List[Dict[str, Any]] = []

    for page_num, img_path in images:
        try:
            result = process_image(
                img_path, page_num, out_pages_dir, primary, alt, languages,
                user_words_path, user_patterns_path, warnings,
            )
        except Exception as e:
            warnings.append(f"page {page_num}: OCR failed ({e})")
            result = {
                "page": page_num, "is_blank": False, "words": [], "mean_conf": 0.0,
                "engine_used": primary.name(), "retries_for_page": 0, "dwell_ms": 0,
            }
        page_retries = result.pop("retries", [])
        pages_meta.append(result)
        all_retries.extend(page_retries)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "path": str(source),
            "hash": sha,
            "size_bytes": size,
            "format": fmt,
        },
        "engine": primary.name(),
        "languages": languages,
        "user_words_applied": user_words_path is not None and user_words_path.exists(),
        "user_patterns_applied": user_patterns_path is not None and user_patterns_path.exists(),
        "retries": all_retries,
        "page_count": len(pages_meta),
        "pages": pages_meta,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    summary_path = out_ocr_dir / "ocr_summary.json"
    atomic_write_text(summary_path, json.dumps(summary, indent=2, ensure_ascii=False))

    if not json_only:
        md_lines = [f"# OCR — `{source}`", ""]
        md_lines.append(f"- **Motor:** `{primary.name()}`")
        md_lines.append(f"- **Idiomas:** {', '.join(languages)}")
        md_lines.append(f"- **Páginas:** {len(pages_meta)}")
        md_lines.append(f"- **Reintentos:** {len(all_retries)}")
        if warnings:
            md_lines.append("")
            md_lines.append("## Advertencias")
            for w in warnings:
                md_lines.append(f"- {w}")
        md_lines.append("")
        md_lines.append("## Resumen por página")
        md_lines.append("")
        md_lines.append("| Page | is_blank | mean_conf | engine | retries | words |")
        md_lines.append("|---|---|---|---|---|---|")
        for p in pages_meta:
            md_lines.append(
                f"| {p['page']} | {'sí' if p['is_blank'] else 'no'} | "
                f"{p['mean_conf']:.2f} | `{p['engine_used']}` | {p['retries_for_page']} | {len(p['words'])} |"
            )
        atomic_write_text(out_ocr_dir / "ocr.md", "\n".join(md_lines) + "\n")

    return 2 if warnings else 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ocr.py",
        description="F20 — Motor OCR multilingüe (Tesseract primary, EasyOCR alternative, retries automáticos).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Constantes (references/01-ingest/ocr-engines.md):
  OCR_RETRY_THRESHOLD    = 0.70   umbral para disparar reintento
  OCR_MIN_WORDS          = 5      mínimo de palabras para reintentar
  OCR_MAX_RETRIES        = 3      invert → alternative engine → sparse_psm
  OCR_DEFAULT_PSM        = 6      uniform block of text
  OCR_SPARSE_PSM         = 11     sparse text (sin orden particular)
  OCR_DEFAULT_LANGS      = spa+eng idiomas por defecto

Idiomas (CSV):
  "spa+eng"   Tesseract style (default)
  "es,en"     EasyOCR style (auto-detectado)

Códigos de salida:
  0 OK sin advertencias
  1 error fatal (motor no instalado, imagen ilegible, PDF input)
  2 OK con advertencias (reintentos, motor alternativo, blank)
""",
    )
    parser.add_argument("--source", required=True, help="Imagen o directorio de imágenes PNG/JPEG")
    parser.add_argument("--out-dir", required=True, help="Directorio de salida (ingest/ocr/)")
    parser.add_argument("--languages", default=OCR_DEFAULT_LANGS, help=f"Idiomas CSV (default: {OCR_DEFAULT_LANGS})")
    parser.add_argument("--engine", default="auto", choices=["auto", "tesseract", "easyocr"], help="Motor OCR")
    parser.add_argument("--user-words", default=None, help="Archivo de palabras del dominio (Tesseract)")
    parser.add_argument("--user-patterns", default=None, help="Archivo de patrones regex del dominio (Tesseract)")
    parser.add_argument("--json-only", action="store_true", help="Solo escribir ocr_summary.json (no ocr.md)")
    args = parser.parse_args(argv)

    if args.engine == "tesseract" and not shutil.which("tesseract") and pytesseract is None:
        print("ERROR: Tesseract not installed. See references/01-ingest/ocr-engines.md §6.",
              file=sys.stderr)
        return 1

    if args.languages and "," in args.languages:
        langs = [l.strip() for l in args.languages.split(",") if l.strip()]
    else:
        langs = [l.strip() for l in args.languages.split("+") if l.strip()]

    user_words_path = load_wordlist(Path(args.user_words)) if args.user_words else None
    user_patterns_path = load_wordlist(Path(args.user_patterns)) if args.user_patterns else None
    if args.user_words and user_words_path is None:
        print(f"WARN: --user-words file not found: {args.user_words}; ignoring", file=sys.stderr)
    if args.user_patterns and user_patterns_path is None:
        print(f"WARN: --user-patterns file not found: {args.user_patterns}; ignoring", file=sys.stderr)

    code = run(
        Path(args.source), Path(args.out_dir), langs, args.engine,
        user_words_path, user_patterns_path, json_only=args.json_only,
    )
    return code


if __name__ == "__main__":
    sys.exit(main())
