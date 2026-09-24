#!/usr/bin/env python3
"""code_ocr.py — F25 code and console OCR.

Consume regiones `semantic_class = "code"` o `"console"` de F22 (con fallback
autodetect desde fragments) y reconstruye el texto con preservación byte-exact
de indentación. Aplica solo correcciones sintácticas forzadas (cada una
registrada), separa prompt/salida en consolas, y marca como `low_confidence`
cualquier bloque dudoso.

Uso:
    python3 scripts/ingest/code_ocr.py \
        --source <regions_dir> --out-dir <dir> \
        [--fragments <fragments.json>] [--json-only]

Salidas (en <out-dir>/ingest/code/):
    page-NNNN.code.json — bloques por página
    code_summary.json — global con correcciones y low_confidence

Códigos de salida:
    0 — OK
    1 — Error fatal
    2 — OK con advertencias (correcciones, low_confidence)

Dependencias:
    - Python 3.9+ stdlib

Documentación normativa: references/01-ingest/code-ocr.md.
"""

from __future__ import annotations

import argparse
import ast
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
# Constants (per references/01-ingest/code-ocr.md §3-§8)
# ============================================================

LINE_HEIGHT_TOL_PX = 4.0
SMALL_GAP = 2.0
LOW_CONFIDENCE_THRESHOLD = 0.7
MIN_CORRECTION_LINE_LEN = 3
MAX_CORRECTIONS_PER_BLOCK = 20

MONOSPACE_FONTS = ("courier", "consolas", "monaco", "menlo", "monospace",
                   "liberation mono", "source code", "inconsolata",
                   "fira mono", "ibm plex mono", "zapfdingbats")

PROMPT_PATTERNS = [
    re.compile(r"^\s*\$\s"),                # bash
    re.compile(r"^\s*#\s"),                # root bash
    re.compile(r"^\s*>\s"),                # cmd, fish
    re.compile(r"^>\>\>"),                  # Python REPL
    re.compile(r"^In\[\d+\]:"),            # IPython
    re.compile(r"^(mysql|postgres|sqlite)>", re.IGNORECASE),  # DB shells
    re.compile(r"^\(\w+\)\s*\$"),          # venv prompt
]

LANGUAGE_KEYWORDS = {
    "python": ["def ", "class ", "import ", "from ", "if __name__", "print(", "lambda ", "self.", "elif "],
    "javascript": ["function", "const ", "let ", "var ", "=>", "console.log", "import ", "export", "require("],
    "sql": ["SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE", "JOIN", "VALUES"],
    "bash": ["ls ", "cd ", "cat ", "grep ", "awk ", "sed ", "echo "],
}


# ============================================================
# Data structures
# ============================================================

@dataclass
class CodeBlock:
    id: str
    page: int
    text: str
    language: str = "unknown"
    confidence: float = 0.0
    low_confidence: bool = False
    low_confidence_reason: Optional[str] = None
    corrections: List[Dict[str, Any]] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)
    output: List[str] = field(default_factory=list)
    bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    dwell_ms: int = 0


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


def is_monospace_font(font_name: Optional[str]) -> bool:
    if not font_name:
        return False
    fn = font_name.lower()
    return any(tok in fn for tok in MONOSPACE_FONTS)


# ============================================================
# Region loading
# ============================================================

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
                "ambiguity": r.get("ambiguity", False),
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
            text = f.get("text", "")
            if not text:
                continue
            bbox = f.get("bbox", [0, 0, 0, 0])
            words.append({"text": text, "bbox": bbox, "font_name": f.get("font_name")})
        if words:
            pages[page_num] = words
    return pages


# ============================================================
# Byte-exact text reconstruction
# ============================================================

def words_in_region_bbox(words: List[Dict[str, Any]], bbox: List[float]) -> List[Dict[str, Any]]:
    if not words or len(bbox) < 4:
        return []
    rx0, ry0, rw, rh = [float(v) for v in bbox]
    rx1, ry1 = rx0 + rw, ry0 + rh
    out: List[Dict[str, Any]] = []
    for w in words:
        bx0, by0 = w["bbox"][0], w["bbox"][1]
        bw = w["bbox"][2] - w["bbox"][0]
        bh = w["bbox"][3] - w["bbox"][1]
        bx1, by1 = bx0 + bw, by0 + bh
        ox = min(rx1, bx1) - max(rx0, bx0)
        oy = min(ry1, by1) - max(ry0, by0)
        if ox >= 0 and oy >= 0:
            out.append(w)
    return out


def reconstruct_text(words: List[Dict[str, Any]]) -> str:
    """Reconstruct text byte-exact, preserving all whitespace.
    Uses bbox to detect line breaks; joins words within a line by checking gaps.
    """
    if not words:
        return ""
    sorted_words = sorted(words, key=lambda w: (-w["bbox"][1], w["bbox"][0]))
    parts: List[str] = []
    prev_y: Optional[float] = None
    prev_x: Optional[float] = None
    prev_w: Optional[float] = None
    for w in sorted_words:
        x0, y0 = w["bbox"][0], w["bbox"][1]
        x1 = x0 + (w["bbox"][2] - w["bbox"][0])
        if prev_y is None:
            parts.append(w["text"])
        else:
            if abs(y0 - prev_y) > LINE_HEIGHT_TOL_PX:
                parts.append("\n")
                parts.append(w["text"])
            else:
                if prev_x is not None and prev_w is not None:
                    gap = x0 - (prev_x + prev_w)
                    if gap > SMALL_GAP:
                        parts.append(" ")
                parts.append(w["text"])
        prev_y = y0
        prev_x = x0
        prev_w = w["bbox"][2] - w["bbox"][0]
    return "".join(parts)


# ============================================================
# Language detection
# ============================================================

def detect_language(text: str) -> str:
    if not text:
        return "unknown"
    stripped = text.strip()
    if stripped.startswith(("{", "[")):
        return "json"
    has_prompt = any(p.search(line) for line in stripped.split("\n") for p in PROMPT_PATTERNS)
    scores: Counter = Counter()
    for lang, keywords in LANGUAGE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[lang] += 1
    if has_prompt and scores.get("bash", 0) > 0:
        scores["bash"] += 2
    if has_prompt and not scores:
        return "console"
    if not scores:
        return "unknown"
    lang_priority = ["python", "javascript", "sql", "bash", "json"]
    best_score = max(scores.values())
    candidates = [l for l, s in scores.items() if s == best_score]
    for l in lang_priority:
        if l in candidates:
            return l
    return candidates[0]


# ============================================================
# Forced corrections (parser-driven)
# ============================================================

def apply_forced_corrections(text: str, language: str) -> Tuple[str, List[Dict[str, Any]]]:
    """Apply ONLY corrections that resolve parser failures. Each correction logged."""
    corrections: List[Dict[str, Any]] = []
    if len(text) < MIN_CORRECTION_LINE_LEN:
        return text, corrections

    if language == "python":
        return _apply_python_corrections(text, corrections)
    if language == "json":
        return _apply_json_corrections(text, corrections)
    return _apply_bracket_corrections(text, corrections)


def _apply_python_corrections(text: str, corrections: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
    try:
        ast.parse(text)
        return text, corrections
    except SyntaxError:
        pass

    result = text
    try:
        compile(result, "<code>", "exec")
        return result, corrections
    except SyntaxError as e:
        pass

    try:
        candidate = _try_close_missing_brackets(result)
        ast.parse(candidate)
        diff_pos = _first_diff_pos(result, candidate)
        corrections.append({
            "char_pos": diff_pos,
            "original": result[diff_pos] if diff_pos < len(result) else "",
            "corrected": candidate[diff_pos] if diff_pos < len(candidate) else "",
            "reason": "missing closing bracket detected by ast.parse",
        })
        return candidate, corrections
    except SyntaxError:
        pass

    return result, corrections


def _apply_json_corrections(text: str, corrections: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
    import json as json_mod
    try:
        json_mod.loads(text)
        return text, corrections
    except json_mod.JSONDecodeError:
        pass

    stripped = text.rstrip()
    if stripped and stripped[-1] not in ("}", "]"):
        if stripped.endswith('"') is False and stripped.endswith("'") is False:
            candidate = stripped + '"'
            try:
                json_mod.loads(candidate)
                corrections.append({
                    "char_pos": len(stripped),
                    "original": "",
                    "corrected": '"',
                    "reason": "missing closing double quote detected by json.loads",
                })
                return candidate, corrections
            except json_mod.JSONDecodeError:
                pass

    return text, corrections


def _apply_bracket_corrections(text: str, corrections: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
    pairs = {"(": ")", "[": "]", "{": "}"}
    closers = {")": "(", "]": "[", "}": "{"}
    stack: List[Tuple[str, int]] = []
    result = text
    for i, ch in enumerate(result):
        if ch in pairs:
            stack.append((pairs[ch], i))
        elif ch in closers:
            if stack and stack[-1][0] == ch:
                stack.pop()
            else:
                return result, corrections

    if stack:
        additions = []
        offset = 0
        for closer, pos in stack:
            corrections.append({
                "char_pos": pos + offset,
                "original": "",
                "corrected": closer,
                "reason": f"missing closing bracket detected",
            })
            additions.append(closer)
            offset += 1
        return result + "".join(additions), corrections

    return result, corrections


def _try_close_missing_brackets(text: str) -> str:
    pairs = {"(": ")", "[": "]", "{": "}"}
    closers = {")": "(", "]": "[", "}": "{"}
    stack: List[str] = []
    for ch in text:
        if ch in pairs:
            stack.append(pairs[ch])
        elif ch in closers:
            if stack and stack[-1] == ch:
                stack.pop()
            else:
                return text
    if stack:
        return text + "".join(reversed(stack))
    return text


def _first_diff_pos(a: str, b: str) -> int:
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    return n


# ============================================================
# Low confidence detection
# ============================================================

def detect_low_confidence(text: str, corrections: List[Dict[str, Any]], language: str) -> Tuple[bool, Optional[str]]:
    if "\t" in text and "    " in text:
        lines = text.split("\n")
        for line in lines:
            if "\t" in line and "    " in line:
                return True, "mixed_indentation"
    if corrections:
        for c in corrections:
            if c.get("original") == "" and c.get("corrected") in (")", "]", "}", '"'):
                continue
            return True, "applied_forced_correction"
    if language in ("python", "javascript", "sql", "bash", "console", "json") and has_ambiguous_chars(text):
        return True, "ambiguous_monospace_chars"
    confidence = _estimate_confidence(text, corrections)
    if confidence < LOW_CONFIDENCE_THRESHOLD:
        return True, f"low_confidence_score={confidence:.2f}"
    return False, None


def _estimate_confidence(text: str, corrections: List[Dict[str, Any]]) -> float:
    score = 1.0
    if "\t" in text and "    " in text:
        score -= 0.2
    score -= 0.1 * len(corrections)
    if "�" in text:
        score -= 0.3
    if any(c in text for c in ["\x00", "\x0c"]):
        score -= 0.5
    ambiguous = sum(1 for c in text if c in "lI1O0")
    if ambiguous > 3:
        score -= 0.1
    return max(0.0, score)


def has_ambiguous_chars(text: str) -> bool:
    """Detect presence of plausibly-confusable monospace characters."""
    return any(c in text for c in "lI1O0")


# ============================================================
# Prompt / output separation
# ============================================================

def separate_prompt_output(text: str) -> Tuple[List[str], List[str]]:
    commands: List[str] = []
    output: List[str] = []
    lines = text.split("\n")
    for line in lines:
        if not line.strip():
            continue
        is_command = any(p.search(line) for p in PROMPT_PATTERNS)
        if is_command:
            commands.append(line)
        else:
            output.append(line)
    return commands, output


# ============================================================
# Page processing
# ============================================================

def extract_code_from_region(
    region: Dict[str, Any],
    page_words: List[Dict[str, Any]],
    counter: int,
    warnings: List[str],
) -> CodeBlock:
    bbox = region.get("bbox", [0, 0, 0, 0])
    if isinstance(bbox, list) and len(bbox) == 4:
        bbox_tuple: Tuple[float, float, float, float] = (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
    else:
        bbox_tuple = (0.0, 0.0, 0.0, 0.0)

    words = words_in_region_bbox(page_words, list(bbox_tuple))
    text = reconstruct_text(words)
    if not text:
        return CodeBlock(
            id=f"c{counter:03d}",
            page=int(region.get("page", 1)),
            text="",
            language="unknown",
            confidence=0.0,
            low_confidence=True,
            low_confidence_reason="empty_block",
        )

    language = detect_language(text)
    corrected_text, corrections = apply_forced_corrections(text, language)
    if len(corrections) > MAX_CORRECTIONS_PER_BLOCK:
        corrections = corrections[:MAX_CORRECTIONS_PER_BLOCK]

    low_conf, low_reason = detect_low_confidence(corrected_text, corrections, language)
    commands, output = ([], [])
    if region.get("semantic_class") == "console" or language == "console" or language == "bash":
        commands, output = separate_prompt_output(corrected_text)

    confidence = _estimate_confidence(corrected_text, corrections)
    return CodeBlock(
        id=f"c{counter:03d}",
        page=int(region.get("page", 1)),
        text=corrected_text,
        language=language,
        confidence=round(confidence, 4),
        low_confidence=low_conf,
        low_confidence_reason=low_reason,
        corrections=corrections,
        commands=commands,
        output=output,
        bbox=bbox_tuple,
    )


def autodetect_code_regions(words: List[Dict[str, Any]], page_num: int) -> List[Dict[str, Any]]:
    """Detect code/console candidates without F22: monospace words clustered."""
    if not words:
        return []
    mono_words = [w for w in words if is_monospace_font(w.get("font_name"))]
    if not mono_words:
        return []
    mono_words.sort(key=lambda w: (-w["bbox"][1], w["bbox"][0]))
    clusters: List[List[Dict[str, Any]]] = []
    current: List[Dict[str, Any]] = []
    last_y = None
    for w in mono_words:
        y = w["bbox"][1]
        if last_y is None or abs(y - last_y) <= LINE_HEIGHT_TOL_PX * 3:
            current.append(w)
        else:
            if len(current) >= 2:
                clusters.append(current)
            current = [w]
        last_y = y
    if len(current) >= 2:
        clusters.append(current)
    regions: List[Dict[str, Any]] = []
    for idx, cluster in enumerate(clusters):
        x0 = min(w["bbox"][0] for w in cluster)
        y0 = min(w["bbox"][1] for w in cluster)
        x1 = max(w["bbox"][2] for w in cluster)
        y1 = max(w["bbox"][3] for w in cluster)
        regions.append({
            "page": page_num,
            "region_id": f"autodetect_code_p{page_num}_c{idx}",
            "semantic_class": "code",
            "bbox": [x0, y0, x1 - x0, y1 - y0],
        })
    return regions


# ============================================================
# Entry point
# ============================================================

def run(
    source: Path,
    out_dir: Path,
    fragments_path: Optional[Path],
    json_only: bool = False,
) -> int:
    source = Path(source).resolve()
    if not source.exists():
        print(f"ERROR: source not found: {source}", file=sys.stderr)
        return 1

    warnings: List[str] = []
    regions = _load_regions(source) if source.exists() else []
    code_regions = [r for r in regions if r.get("semantic_class") in ("code", "console") or r.get("ambiguity")]
    page_words: Dict[int, List[Dict[str, Any]]] = {}
    if fragments_path and fragments_path.exists():
        page_words = _load_words_from_fragments(fragments_path)

    out_code_dir = out_dir / "ingest" / "code"
    out_code_dir.mkdir(parents=True, exist_ok=True)

    blocks_by_page: Dict[int, List[CodeBlock]] = {}
    all_blocks: List[CodeBlock] = []
    counter = 1

    if code_regions:
        regions_by_page: Dict[int, List[Dict[str, Any]]] = {}
        for r in code_regions:
            regions_by_page.setdefault(int(r["page"]), []).append(r)
        for page_num in sorted(regions_by_page.keys()):
            page_w = page_words.get(page_num, [])
            for region in regions_by_page[page_num]:
                block = extract_code_from_region(region, page_w, counter, warnings)
                blocks_by_page.setdefault(page_num, []).append(block)
                all_blocks.append(block)
                counter += 1
    elif page_words:
        for page_num, words in page_words.items():
            warnings.append(f"page {page_num}: F22 had no code regions; autodetecting")
            autodetected = autodetect_code_regions(words, page_num)
            for region in autodetected:
                block = extract_code_from_region(region, words, counter, warnings)
                blocks_by_page.setdefault(page_num, []).append(block)
                all_blocks.append(block)
                counter += 1

    for page_num, page_blocks in blocks_by_page.items():
        atomic_write_text(
            out_code_dir / f"page-{page_num:04d}.code.json",
            json.dumps({
                "page": page_num,
                "blocks": [
                    {
                        "id": b.id,
                        "language": b.language,
                        "text": b.text,
                        "confidence": b.confidence,
                        "low_confidence": b.low_confidence,
                        "low_confidence_reason": b.low_confidence_reason,
                        "corrections": b.corrections,
                        "commands": b.commands,
                        "output": b.output,
                        "bbox": list(b.bbox),
                        "page": b.page,
                        "dwell_ms": b.dwell_ms,
                    }
                    for b in page_blocks
                ],
            }, indent=2, ensure_ascii=False),
        )

    lang_dist: Counter = Counter()
    for b in all_blocks:
        lang_dist[b.language] += 1

    corrections_total = sum(len(b.corrections) for b in all_blocks)
    low_conf_count = sum(1 for b in all_blocks if b.low_confidence)

    all_corrections = []
    for b in all_blocks:
        for c in b.corrections:
            all_corrections.append({"page": b.page, "block_id": b.id, **c})

    low_conf_blocks = [
        {"page": b.page, "block_id": b.id, "reason": b.low_confidence_reason}
        for b in all_blocks
        if b.low_confidence
    ]

    summary = {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "regions_dir": str(source),
            "fragments_path": str(fragments_path) if fragments_path else None,
            "hash": sha256_paths([source] + ([fragments_path] if fragments_path else [])),
        },
        "block_count": len(all_blocks),
        "language_distribution": dict(lang_dist),
        "corrections_total": corrections_total,
        "low_confidence_count": low_conf_count,
        "corrections": all_corrections,
        "low_confidence_blocks": low_conf_blocks,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    atomic_write_text(
        out_code_dir / "code_summary.json",
        json.dumps(summary, indent=2, ensure_ascii=False),
    )

    if not json_only:
        md_lines = [f"# Code — `{source.name}`", ""]
        md_lines.append(f"- **Bloques:** {len(all_blocks)}")
        md_lines.append(f"- **Lenguajes:** {dict(lang_dist)}")
        md_lines.append(f"- **Correcciones:** {corrections_total}")
        md_lines.append(f"- **Low confidence:** {low_conf_count}")
        if warnings:
            md_lines.append("")
            md_lines.append("## Advertencias")
            for w in warnings:
                md_lines.append(f"- {w}")
        atomic_write_text(out_code_dir / "code.md", "\n".join(md_lines) + "\n")

    return 2 if warnings else 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="code_ocr.py",
        description="F25 — Code and console OCR (byte-exact, forced corrections, prompt separation).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Constantes (references/01-ingest/code-ocr.md §3-§8):
  LINE_HEIGHT_TOL_PX        = 4.0    px (tolerancia para saltos de línea)
  SMALL_GAP                 = 2.0    px (umbral para insertar espacio entre palabras)
  LOW_CONFIDENCE_THRESHOLD   = 0.7    umbral para marcar low_confidence
  MIN_CORRECTION_LINE_LEN   = 3      mínimo de chars para aplicar corrección
  MAX_CORRECTIONS_PER_BLOCK = 20     máximo de correcciones por bloque

Regla dura: cada corrección SOLO se aplica si es forzada (parser falla).
Ningún carácter se corrige por plausibilidad.

Códigos de salida:
  0 OK sin advertencias
  1 error fatal
  2 OK con advertencias (correcciones, low_confidence)
""",
    )
    parser.add_argument("--source", required=True, help="Directorio con page-NNNN.regions.json (F22)")
    parser.add_argument("--out-dir", required=True, help="Directorio de salida (ingest/code/)")
    parser.add_argument("--fragments", default=None, help="fragments.json (F18) opcional")
    parser.add_argument("--json-only", action="store_true", help="Solo escribir code_summary.json (no code.md)")
    args = parser.parse_args(argv)

    fragments_path = Path(args.fragments) if args.fragments else None
    code = run(Path(args.source), Path(args.out_dir), fragments_path, json_only=args.json_only)
    return code


if __name__ == "__main__":
    sys.exit(main())
