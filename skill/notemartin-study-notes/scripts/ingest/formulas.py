#!/usr/bin/env python3
"""formulas.py — F24 formula OCR.

Consume regiones `semantic_class = "formula"` de F22 (con fallback geométrico
desde fragments) y emite LaTeX validado por un verificador regex. Las fórmulas
inválidas se marcan como `pending` con imagen recortada (cuando hay imagen) o
bbox referencial (cuando es PDF-only). Preserva la numeración de la fuente.

Uso:
    python3 scripts/ingest/formulas.py \
        --source <regions_dir> --out-dir <dir> \
        [--fragments <fragments.json>] [--ocr <ocr_summary.json>] \
        [--images-dir <images_dir>] [--json-only]

Salidas (en <out-dir>/ingest/formulas/):
    page-NNNN.formulas.json — fórmulas por página
    formulas_summary.json — global con equation_index
    images/page-NNNN/<id>.formula.png — recortes de pendientes (opcional)

Códigos de salida:
    0 — OK
    1 — Error fatal
    2 — OK con advertencias (pending, numeración faltante)

Dependencias:
    - Python 3.9+ stdlib
    - Pillow (opcional; solo si --images-dir se pasa y hay pendientes)

Documentación normativa: references/01-ingest/formulas.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"

# ============================================================
# Constants (per references/01-ingest/formulas.md §5-§6)
# ============================================================

LATEX_MAX_NESTED_BRACES = 5
INLINE_MAX_HEIGHT_PX = 30.0
INLINE_MAX_WIDTH_RATIO = 0.5
DEFAULT_PAGE_WIDTH = 612.0
DEFAULT_PAGE_HEIGHT = 792.0

LATEX_KNOWN_COMMANDS = frozenset({
    "frac", "sum", "int", "sqrt", "prod", "coprod",
    "alpha", "beta", "gamma", "delta", "epsilon", "varepsilon", "zeta", "eta",
    "theta", "vartheta", "iota", "kappa", "lambda", "mu", "nu", "xi",
    "pi", "varpi", "rho", "varrho", "sigma", "varsigma", "tau",
    "upsilon", "phi", "varphi", "chi", "psi", "omega",
    "Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Upsilon",
    "Phi", "Psi", "Omega",
    "infty", "partial", "nabla", "forall", "exists", "nexists",
    "cdot", "times", "div", "pm", "mp", "ast", "star",
    "cup", "cap", "setminus", "setminus",
    "subset", "supset", "subseteq", "supseteq", "in", "ni", "notin",
    "leq", "le", "geq", "ge", "neq", "ne", "approx", "equiv",
    "sim", "simeq", "cong", "propto",
    "to", "rightarrow", "leftarrow", "Rightarrow", "Leftarrow",
    "leftrightarrow", "Leftrightarrow", "mapsto", "hookrightarrow",
    "uparrow", "downarrow",
    "lim", "liminf", "limsup", "sup", "inf", "max", "min", "arg", "gcd",
    "det", "Pr", "bmod", "pmod",
    "bar", "hat", "tilde", "vec", "dot", "ddot",
    "widehat", "widetilde",
    "overline", "underline",
    "overbrace", "underbrace",
    "text", "mathrm", "mathbf", "mathit", "mathcal", "mathbb", "mathfrak",
    "begin", "end", "left", "right", "big", "Big", "bigg", "Bigg",
    "mathrm",
    "label", "ref", "tag",
    "quad", "qquad",
    "binom", "tbinom",
    "substack",
    "xleftarrow", "xrightarrow",
    "overset", "underset",
    "stackrel",
    "boxed",
})

LATEX_KNOWN_ENVIRONMENTS = frozenset({
    "equation", "equation*",
    "align", "align*", "aligned",
    "matrix", "pmatrix", "bmatrix", "vmatrix", "Vmatrix", "smallmatrix",
    "cases", "gathered", "alignat", "split", "eqnarray", "eqnarray*", "multline",
})

NUMBER_PATTERN = re.compile(r"\(\s*(\d+(?:\.\d+)?)\s*\)")
TAG_PATTERN = re.compile(r"\\tag\s*\{([^}]+)\}")
LABEL_PATTERN = re.compile(r"\\label\s*\{([^}]+)\}")
COMMAND_PATTERN = re.compile(r"\\([a-zA-Z]+)")
ENV_PATTERN = re.compile(r"\\begin\s*\{([^}]+)\}|\\end\s*\{([^}]+)\}")


# ============================================================
# Data structures
# ============================================================

@dataclass
class FormulaRecord:
    id: str
    page: int
    latex: str
    latex_compiled: bool
    compile_errors: List[str] = field(default_factory=list)
    number: Optional[str] = None
    inline: bool = False
    pending: bool = False
    image_path: Optional[str] = None
    bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    dwell_ms: int = 0


# ============================================================
# LaTeX Validator
# ============================================================

class LaTeXValidator:
    def validate(self, text: str) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        if not text or not text.strip():
            return False, ["empty formula"]

        brace_err = self._check_braces(text)
        if brace_err:
            errors.append(brace_err)

        nesting_err = self._check_nesting(text)
        if nesting_err:
            errors.append(nesting_err)

        env_err = self._check_environments(text)
        if env_err:
            errors.extend(env_err)

        orphan_err = self._check_orphans(text)
        if orphan_err:
            errors.extend(orphan_err)

        unknown_cmds = self._check_unknown_commands(text)
        if unknown_cmds:
            errors.extend(unknown_cmds)

        return (len(errors) == 0), errors

    def _check_unknown_commands(self, text: str) -> List[str]:
        errors: List[str] = []
        for m in COMMAND_PATTERN.finditer(text):
            cmd = m.group(1)
            if cmd not in LATEX_KNOWN_COMMANDS:
                errors.append(f"unknown command: \\{cmd}")
        return errors

    def _check_braces(self, text: str) -> Optional[str]:
        depth = 0
        for i, ch in enumerate(text):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth < 0:
                    return f"unbalanced braces: extra }} at position {i}"
        if depth != 0:
            return f"unbalanced braces: depth={depth} at end"

        bracket_depth = 0
        for i, ch in enumerate(text):
            if ch == "[":
                bracket_depth += 1
            elif ch == "]":
                bracket_depth -= 1
                if bracket_depth < 0:
                    return f"unbalanced brackets: extra ] at position {i}"
        if bracket_depth != 0:
            return f"unbalanced brackets: depth={bracket_depth} at end"
        return None

    def _check_nesting(self, text: str) -> Optional[str]:
        depth = 0
        max_depth = 0
        for ch in text:
            if ch == "{":
                depth += 1
                if depth > max_depth:
                    max_depth = depth
            elif ch == "}":
                depth -= 1
        if max_depth > LATEX_MAX_NESTED_BRACES:
            return f"nesting too deep: {max_depth} > {LATEX_MAX_NESTED_BRACES}"
        return None

    def _check_environments(self, text: str) -> List[str]:
        errors: List[str] = []
        stack: List[str] = []
        for m in ENV_PATTERN.finditer(text):
            begin_name = m.group(1)
            end_name = m.group(2)
            if begin_name is not None:
                if begin_name not in LATEX_KNOWN_ENVIRONMENTS:
                    errors.append(f"unknown environment: {begin_name}")
                stack.append(begin_name)
            elif end_name is not None:
                if not stack:
                    errors.append(f"unmatched \\end{{{end_name}}} (no matching \\begin)")
                elif stack[-1] != end_name:
                    errors.append(f"mismatched environments: \\begin{{{stack[-1]}}} closed by \\end{{{end_name}}}")
                    stack.pop()
                else:
                    stack.pop()
        if stack:
            errors.append(f"unclosed environments: {stack}")
        return errors

    def _check_orphans(self, text: str) -> List[str]:
        errors: List[str] = []
        if text.startswith("_") or text.startswith("^"):
            errors.append(f"orphan special at start: {text[:3]!r}")
        for i, ch in enumerate(text):
            if ch in "_^":
                if i == 0:
                    errors.append(f"orphan special at position 0")
                    continue
                prev = text[i - 1]
                if prev in "=+-*/,;([{" or prev.isspace():
                    errors.append(f"orphan {ch} at position {i} (preceded by {prev!r})")
        return errors


# ============================================================
# Helper functions
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


def detect_number(text: str) -> Optional[str]:
    """Extract equation number from text (looks for (N) or (N.M) at the end)."""
    matches = list(NUMBER_PATTERN.finditer(text))
    if not matches:
        return None
    last = matches[-1]
    if last.end() >= len(text) - 2:
        return last.group(0)
    return None


def is_inline(bbox: Tuple[float, float, float, float], page_width: float) -> bool:
    x, y, w, h = bbox
    return h <= INLINE_MAX_HEIGHT_PX and w < INLINE_MAX_WIDTH_RATIO * page_width


def words_in_region_bbox(words: List[Dict[str, Any]], bbox: List[float]) -> List[Dict[str, Any]]:
    if not words or len(bbox) < 4:
        return []
    rx0, ry0, rw, rh = [float(v) for v in bbox]
    rx1, ry1 = rx0 + rw, ry0 + rh
    out: List[Dict[str, Any]] = []
    for w in words:
        wx0, wy0 = w["bbox"][0], w["bbox"][1]
        wx1, wy1 = wx0 + (w["bbox"][2] - w["bbox"][0]), wy0 + (w["bbox"][3] - wy0)
        ox = min(rx1, wx1) - max(rx0, wx0)
        oy = min(ry1, wy1) - max(ry0, wy0)
        if ox >= 0 and oy >= 0:
            out.append(w)
    return out


def extract_text_from_words(words: List[Dict[str, Any]]) -> str:
    """Concatenate words in reading order (top-to-bottom, left-to-right within row)."""
    if not words:
        return ""
    sorted_words = sorted(words, key=lambda w: (-w["bbox"][1], w["bbox"][0]))
    parts: List[str] = []
    last_y = None
    for w in sorted_words:
        y = w["bbox"][1]
        if last_y is not None and abs(y - last_y) > 5:
            parts.append(" ")
        parts.append(w["text"])
        last_y = y
    text = "".join(parts).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def crop_image_to_bbox(image_path: Path, bbox: List[float], output_path: Path) -> bool:
    """Crop a region from an image and save to output_path. Returns True on success."""
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
    rx0, ry0, rw, rh = [int(round(float(v))) for v in bbox[:4]]
    w, h = img.size
    rx1 = min(w, rx0 + rw)
    ry1 = min(h, ry0 + rh)
    if rx0 >= w or ry0 >= h or rx0 < 0 or ry0 < 0 or rx1 <= rx0 or ry1 <= ry0:
        return False
    try:
        cropped = img.crop((rx0, ry0, rx1, ry1))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cropped.save(output_path, format="PNG")
        return True
    except Exception:
        return False


# ============================================================
# Page processing
# ============================================================

def extract_formula_from_region(
    region: Dict[str, Any],
    page_words: List[Dict[str, Any]],
    formula_counter: int,
    images_dir: Optional[Path],
    page_num: int,
    warnings: List[str],
    page_width: float = DEFAULT_PAGE_WIDTH,
) -> FormulaRecord:
    bbox = region.get("bbox", [0.0, 0.0, 0.0, 0.0])
    if isinstance(bbox, list) and len(bbox) == 4:
        bbox_tuple: Tuple[float, float, float, float] = (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
    else:
        bbox_tuple = (0.0, 0.0, 0.0, 0.0)

    words_in_bbox = words_in_region_bbox(page_words, list(bbox_tuple))
    raw_text = extract_text_from_words(words_in_bbox)
    if not raw_text:
        return FormulaRecord(
            id=f"f{formula_counter:03d}",
            page=page_num,
            latex="",
            latex_compiled=False,
            compile_errors=["empty formula"],
            pending=True,
            bbox=bbox_tuple,
        )

    number = detect_number(raw_text)
    latex_text = raw_text

    validator = LaTeXValidator()
    compiled, errors = validator.validate(latex_text)

    inline = is_inline(bbox_tuple, page_width)
    pending = not compiled

    image_path: Optional[str] = None
    if pending and images_dir is not None:
        out_image = images_dir / f"page-{page_num:04d}" / f"f{formula_counter:03d}.formula.png"
        for ext_img in [".png", ".jpg", ".jpeg"]:
            src = images_dir / f"page-{page_num:04d}.processed{ext_img}"
            if not src.exists():
                src = images_dir / f"page-{page_num:04d}{ext_img}"
            if src.exists() and crop_image_to_bbox(src, list(bbox_tuple), out_image):
                image_path = str(out_image)
                break

    return FormulaRecord(
        id=f"f{formula_counter:03d}",
        page=page_num,
        latex=latex_text,
        latex_compiled=compiled,
        compile_errors=errors,
        number=number,
        inline=inline,
        pending=pending,
        image_path=image_path,
        bbox=bbox_tuple,
    )


# ============================================================
# Entry point
# ============================================================

def run(
    source: Path,
    out_dir: Path,
    fragments_path: Optional[Path],
    ocr_path: Optional[Path],
    images_dir: Optional[Path],
    json_only: bool = False,
) -> int:
    source = Path(source).resolve()
    if not source.exists():
        print(f"ERROR: source not found: {source}", file=sys.stderr)
        return 1

    warnings: List[str] = []
    regions = _load_regions(source) if source.exists() else []
    formula_regions = [r for r in regions if r.get("semantic_class") == "formula"]

    page_words: Dict[int, List[Dict[str, Any]]] = {}
    if fragments_path and fragments_path.exists():
        page_words = _load_words_from_fragments(fragments_path)
    if not page_words and ocr_path and ocr_path.exists():
        page_words = _load_words_from_ocr(ocr_path)

    out_formulas_dir = out_dir / "ingest" / "formulas"
    out_formulas_dir.mkdir(parents=True, exist_ok=True)

    all_formulas: List[FormulaRecord] = []
    counter = 1
    formulas_by_page: Dict[int, List[FormulaRecord]] = {}

    if formula_regions:
        regions_by_page: Dict[int, List[Dict[str, Any]]] = {}
        for r in formula_regions:
            regions_by_page.setdefault(int(r["page"]), []).append(r)
        for page_num in sorted(regions_by_page.keys()):
            page_w = page_words.get(page_num, [])
            for region in regions_by_page[page_num]:
                formula = extract_formula_from_region(
                    region, page_w, counter, images_dir, page_num, warnings,
                )
                formulas_by_page.setdefault(page_num, []).append(formula)
                all_formulas.append(formula)
                counter += 1
    elif page_words:
        for page_num, words in page_words.items():
            warnings.append(f"page {page_num}: F22 had no formula regions; autodetecting")
            autodetected = _autodetect_formula_regions(words, page_num)
            for region in autodetected:
                formula = extract_formula_from_region(
                    region, words, counter, images_dir, page_num, warnings,
                )
                formulas_by_page.setdefault(page_num, []).append(formula)
                all_formulas.append(formula)
                counter += 1

    for page_num, page_formulas in formulas_by_page.items():
        atomic_write_text(
            out_formulas_dir / f"page-{page_num:04d}.formulas.json",
            json.dumps({
                "page": page_num,
                "formulas": [
                    {
                        "id": f.id,
                        "latex": f.latex,
                        "latex_compiled": f.latex_compiled,
                        "compile_errors": f.compile_errors,
                        "number": f.number,
                        "inline": f.inline,
                        "pending": f.pending,
                        "image_path": f.image_path,
                        "bbox": list(f.bbox),
                        "page": f.page,
                        "dwell_ms": f.dwell_ms,
                    }
                    for f in page_formulas
                ],
            }, indent=2, ensure_ascii=False),
        )

    compiled_count = sum(1 for f in all_formulas if f.latex_compiled)
    pending_count = sum(1 for f in all_formulas if f.pending)
    equation_index = [
        {"number": f.number, "region_id": f.id, "page": f.page}
        for f in all_formulas
        if f.number is not None
    ]
    pending_formulas = [
        {"page": f.page, "region_id": f.id, "image_path": f.image_path}
        for f in all_formulas
        if f.pending
    ]

    summary = {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "regions_dir": str(source),
            "fragments_path": str(fragments_path) if fragments_path else None,
            "ocr_summary_path": str(ocr_path) if ocr_path else None,
            "images_dir": str(images_dir) if images_dir else None,
            "hash": sha256_paths([source] + ([fragments_path] if fragments_path else []) + ([ocr_path] if ocr_path else [])),
        },
        "formula_count": len(all_formulas),
        "compiled_count": compiled_count,
        "pending_count": pending_count,
        "equation_index": equation_index,
        "pending_formulas": pending_formulas,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    atomic_write_text(
        out_formulas_dir / "formulas_summary.json",
        json.dumps(summary, indent=2, ensure_ascii=False),
    )

    if not json_only:
        md_lines = [f"# Formulas — `{source.name}`", ""]
        md_lines.append(f"- **Fórmulas:** {len(all_formulas)}")
        md_lines.append(f"- **Compilan:** {compiled_count}")
        md_lines.append(f"- **Pendientes:** {pending_count}")
        md_lines.append(f"- **Numeradas:** {len(equation_index)}")
        if warnings:
            md_lines.append("")
            md_lines.append("## Advertencias")
            for w in warnings:
                md_lines.append(f"- {w}")
        atomic_write_text(out_formulas_dir / "formulas.md", "\n".join(md_lines) + "\n")

    return 2 if warnings else 0


def _load_regions(source: Path) -> List[Dict[str, Any]]:
    if source.is_dir():
        paths = sorted(source.glob("page-*.regions.json"))
    elif source.is_file():
        paths = [source]
    else:
        return []
    pages: List[Dict[str, Any]] = []
    for p in paths:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        page_num = int(data.get("page", 1))
        for r in data.get("regions", []):
            pages.append({
                "page": page_num,
                "region_id": r.get("id"),
                "semantic_class": r.get("semantic_class"),
                "bbox": r.get("bbox", [0, 0, 0, 0]),
            })
    return pages


def _load_words_from_fragments(fragments_path: Path) -> Dict[int, List[Dict[str, Any]]]:
    if not fragments_path.exists():
        return {}
    try:
        data = json.loads(fragments_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    pages: Dict[int, List[Dict[str, Any]]] = {}
    for page_data in data.get("pages", []):
        page_num = int(page_data.get("page", 1))
        words: List[Dict[str, Any]] = []
        for f in page_data.get("fragments", []):
            text = f.get("text", "").strip()
            if not text:
                continue
            bbox = f.get("bbox", [0, 0, 0, 0])
            words.append({"text": text, "bbox": bbox})
        if words:
            pages[page_num] = words
    return pages


def _load_words_from_ocr(ocr_path: Path) -> Dict[int, List[Dict[str, Any]]]:
    if not ocr_path.exists():
        return {}
    try:
        data = json.loads(ocr_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    pages: Dict[int, List[Dict[str, Any]]] = {}
    for page_data in data.get("pages", []):
        page_num = int(page_data.get("page", 1))
        words: List[Dict[str, Any]] = []
        for w in page_data.get("words", []):
            text = w.get("text", "").strip()
            if not text:
                continue
            bbox = w.get("bbox", [0, 0, 0, 0])
            words.append({"text": text, "bbox": bbox})
        if words:
            pages[page_num] = words
    return pages


def _autodetect_formula_regions(words: List[Dict[str, Any]], page_num: int) -> List[Dict[str, Any]]:
    """Detect formula candidates by clustering high-symbol-density words into bbox regions."""
    if len(words) < 2:
        return []
    formula_words: List[Dict[str, Any]] = []
    for w in words:
        text = w.get("text", "")
        if not text:
            continue
        non_alnum = sum(1 for ch in text if not ch.isalnum() and not ch.isspace())
        alnum = sum(1 for ch in text if ch.isalnum())
        if alnum == 0:
            continue
        density = non_alnum / alnum
        if density >= 0.20:
            formula_words.append(w)
    if not formula_words:
        return []
    formula_words.sort(key=lambda w: (-w["bbox"][1], w["bbox"][0]))
    clusters: List[List[Dict[str, Any]]] = []
    current: List[Dict[str, Any]] = []
    last_y = None
    for w in formula_words:
        y = w["bbox"][1]
        if last_y is None or abs(y - last_y) <= 30:
            current.append(w)
        else:
            if current:
                clusters.append(current)
            current = [w]
        last_y = y
    if current:
        clusters.append(current)
    regions: List[Dict[str, Any]] = []
    for idx, cluster in enumerate(clusters):
        x0 = min(w["bbox"][0] for w in cluster)
        y0 = min(w["bbox"][1] for w in cluster)
        x1 = max(w["bbox"][0] + (w["bbox"][2] - w["bbox"][0]) for w in cluster)
        y1 = max(w["bbox"][1] + (w["bbox"][3] - w["bbox"][1]) for w in cluster)
        regions.append({
            "page": page_num,
            "region_id": f"autodetect_formula_p{page_num}_c{idx}",
            "semantic_class": "formula",
            "bbox": [x0, y0, x1 - x0, y1 - y0],
        })
    return regions


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="formulas.py",
        description="F24 — Formula OCR (LaTeX validation, pending fallback, numbered preservation).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Constantes (references/01-ingest/formulas.md §5-§6):
  LATEX_MAX_NESTED_BRACES     = 5      profundidad máxima de llaves
  INLINE_MAX_HEIGHT_PX        = 30.0    px (umbral bloque vs inline)
  INLINE_MAX_WIDTH_RATIO      = 0.5     ancho inline máximo
  LATEX_KNOWN_COMMANDS        = ~ 80 macros (frac, sum, alpha, ...)
  LATEX_KNOWN_ENVIRONMENTS    = 14 entornos (equation, align, matrix, ...)

Códigos de salida:
  0 OK sin advertencias
  1 error fatal
  2 OK con advertencias (pending, numeración faltante)
""",
    )
    parser.add_argument("--source", required=True, help="Directorio con page-NNNN.regions.json (F22)")
    parser.add_argument("--out-dir", required=True, help="Directorio de salida (ingest/formulas/)")
    parser.add_argument("--fragments", default=None, help="fragments.json (F18) opcional")
    parser.add_argument("--ocr", default=None, help="ocr_summary.json (F20) opcional")
    parser.add_argument("--images-dir", default=None, help="Directorio de imágenes preprocesadas (F19) para recortes")
    parser.add_argument("--json-only", action="store_true", help="Solo escribir formulas_summary.json (no formulas.md)")
    args = parser.parse_args(argv)

    fragments_path = Path(args.fragments) if args.fragments else None
    ocr_path = Path(args.ocr) if args.ocr else None
    images_dir = Path(args.images_dir) if args.images_dir else None
    code = run(Path(args.source), Path(args.out_dir), fragments_path, ocr_path, images_dir, json_only=args.json_only)
    return code


if __name__ == "__main__":
    sys.exit(main())
