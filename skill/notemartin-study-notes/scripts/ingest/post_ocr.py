#!/usr/bin/env python3
"""post_ocr.py — F27 deterministic post-OCR correction.

Aplica correcciones deterministas (R001-R010) y un diccionario técnico auditable
sobre la salida de F22/F23/F24/F25. NUNCA modifica código ni tablas. Cada
corrección tiene un `correction_id` único y es individualmente revertible vía
`--revert <correction_id>`.

Uso:
    python3 scripts/ingest/post_ocr.py \
        --source <ingest_dir> --out-dir <dir> \
        [--dictionary <dictionary.yaml>] [--json-only]

    # Revertir una corrección específica:
    python3 scripts/ingest/post_ocr.py --source <dir> --out-dir <dir> --revert <correction_id>

    # Revertir todas:
    python3 scripts/ingest/post_ocr.py --source <dir> --out-dir <dir> --revert-all

Salidas (en <out-dir>/ingest/post_ocr/):
    page-NNNN.post_ocr.json — regiones con original_text, corrected_text, corrections[]
    post_ocr_summary.json — global con rule/dict distribution, revertible
    audit_log.json — registro de applies y reverts

Códigos de salida:
    0 — OK
    1 — Error fatal
    2 — OK con advertencias (correcciones parciales, regiones saltadas)

Dependencias:
    - Python 3.9+ stdlib

Documentación normativa: references/01-ingest/post-ocr.md.
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
from typing import Any, Callable, Dict, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"

# ============================================================
# Constants (per references/01-ingest/post-ocr.md §3-§7)
# ============================================================

INDENT_PRESERVE_MIN = 4
MAX_CORRECTIONS_PER_REGION = 50
MAX_DICTIONARY_ENTRIES = 1000
MAX_AUDIT_LOG_ENTRIES = 1000

LIGATURES = {
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
}

SKIP_NEXT_CHARS = set("[({<0123456789")

PROSE_CLASSES = frozenset({
    "text", "heading", "caption", "figure_caption", "index", "editorial_note",
})
SKIP_CLASSES = frozenset({"code", "console", "table", "syntax_diagram"})
FORMULA_CLASS = "formula"

DEFAULT_DICTIONARY = [
    {"id": "D001", "original": "PostgresQL", "corrected": "PostgreSQL", "case_sensitive": True, "scope": "prose"},
    {"id": "D002", "original": "Javascript", "corrected": "JavaScript", "case_sensitive": False, "scope": "prose"},
    {"id": "D003", "original": "mySQL", "corrected": "MySQL", "case_sensitive": True, "scope": "prose"},
    {"id": "D004", "original": "Typescript", "corrected": "TypeScript", "case_sensitive": True, "scope": "prose"},
    {"id": "D005", "original": "pyhton", "corrected": "python", "case_sensitive": False, "scope": "prose"},
]


# ============================================================
# Helpers
# ============================================================

def sha256_paths(paths: List[Path]) -> str:
    h = hashlib.sha256()
    for p in sorted(paths):
        if not p.exists():
            continue
        if p.is_file():
            h.update(_sha256_file(p).encode("utf-8"))
        elif p.is_dir():
            for child in sorted(p.rglob("*")):
                if child.is_file():
                    h.update(_sha256_file(child).encode("utf-8"))
    return h.hexdigest()


def _sha256_file(path: Path) -> str:
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


def atomic_write_json(path: Path, data: Any) -> None:
    atomic_write_text(path, json.dumps(data, indent=2, ensure_ascii=False))


# ============================================================
# Dictionary loading
# ============================================================

def load_dictionary(path: Optional[Path]) -> List[Dict[str, Any]]:
    if path is None or not path.exists():
        return list(DEFAULT_DICTIONARY)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return list(DEFAULT_DICTIONARY)
    entries = data.get("entries", [])
    if not isinstance(entries, list):
        return list(DEFAULT_DICTIONARY)
    valid: List[Dict[str, Any]] = []
    seen_ids = set()
    for e in entries:
        if not isinstance(e, dict):
            continue
        if e.get("id") in seen_ids:
            continue
        if e.get("original") == e.get("corrected"):
            continue
        if not e.get("original") or not e.get("corrected"):
            continue
        seen_ids.add(e.get("id"))
        valid.append(e)
    if len(valid) > MAX_DICTIONARY_ENTRIES:
        valid = valid[:MAX_DICTIONARY_ENTRIES]
    return valid if valid else list(DEFAULT_DICTIONARY)


# ============================================================
# Rule engine
# ============================================================

def _is_url_context(text: str, pos: int) -> bool:
    window = text[pos:pos + 30]
    return "://" in window or ".com" in window or ".org" in window


def _apply_rule(rule_id: str, text: str, pattern: str, repl: str) -> Tuple[str, List[Dict[str, Any]]]:
    """Apply a regex rule and return (new_text, corrections[])."""
    corrections: List[Dict[str, Any]] = []
    out_parts: List[str] = []
    last = 0
    for m in re.finditer(pattern, text):
        original = m.group(0)
        replacement = repl if isinstance(repl, str) else repl(m)
        if original == replacement:
            continue
        out_parts.append(text[last:m.start()])
        out_parts.append(replacement)
        last = m.end()
        corrections.append({
            "correction_id": None,  # set later
            "rule_id": rule_id,
            "dict_id": None,
            "char_pos": m.start(),
            "char_end": m.end(),
            "original": original,
            "corrected": replacement,
            "applied_at": datetime.now(timezone.utc).isoformat(),
        })
    out_parts.append(text[last:])
    new_text = "".join(out_parts)
    return new_text, corrections


def apply_rules(text: str) -> Tuple[str, List[Dict[str, Any]]]:
    """Apply R001-R010 in order. Returns (new_text, corrections)."""
    corrections: List[Dict[str, Any]] = []

    if not text:
        return text, corrections

    new_text = text

    new_text, c = _apply_rule(
        "R002", new_text,
        r"\n{3,}", "\n\n",
    )
    corrections.extend(c)

    new_text, c = _apply_rule(
        "R003", new_text,
        r"(?m)^( +)\1+ +", r"\1 ",
    )
    corrections.extend(c)

    new_text, c = _apply_rule(
        "R003", new_text,
        r"(?<!^) {2,}(?!$)", " ",
    )
    corrections.extend(c)

    new_text, c = _apply_rule(
        "R004", new_text,
        r"(?m)^( +)\t", lambda m: m.group(1) + "    ",
    )
    corrections.extend(c)

    for ligature, replacement in LIGATURES.items():
        c = list(re.finditer(re.escape(ligature), new_text))
        if not c:
            continue
        filtered: List[Dict[str, Any]] = []
        out_parts: List[str] = []
        last_pos = 0
        for m in c:
            if _is_url_context(new_text, m.start()):
                out_parts.append(new_text[last_pos:m.end()])
            else:
                out_parts.append(new_text[last_pos:m.start()])
                out_parts.append(replacement)
                filtered.append({
                    "correction_id": None,
                    "rule_id": f"R00{5 + list(LIGATURES.keys()).index(ligature)}",
                    "dict_id": None,
                    "char_pos": m.start(),
                    "char_end": m.end(),
                    "original": m.group(0),
                    "corrected": replacement,
                    "applied_at": datetime.now(timezone.utc).isoformat(),
                })
            last_pos = m.end()
        out_parts.append(new_text[last_pos:])
        new_text = "".join(out_parts)
        corrections.extend(filtered)

    new_text, c = _apply_rule(
        "R009", new_text,
        r"(\d{1,3})\.\s+([A-Z][a-z]+)",
        lambda m: m.group(1) + ".\n\n" + m.group(2),
    )
    corrections.extend(c)

    new_text, c = _apply_rule(
        "R001", new_text,
        r"(\S)\n([a-z][^(\[{<\d])",
        lambda m: m.group(1) + "\n" + m.group(2),
    )
    corrections.extend(c)

    new_text, c = _apply_rule(
        "R010", new_text,
        r"(?m)^(\([0-9]+\)|\[[0-9]+\])\s+",
        lambda m: m.group(1) + "\n",
    )
    corrections.extend(c)

    return new_text, corrections


def apply_dictionary(text: str, dictionary: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
    corrections: List[Dict[str, Any]] = []
    if not text or not dictionary:
        return text, corrections
    new_text = text
    for entry in dictionary:
        original = entry.get("original", "")
        corrected = entry.get("corrected", "")
        if not original or not corrected or original == corrected:
            continue
        case_sensitive = entry.get("case_sensitive", False)
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.escape(original)
        new_text, cs = _apply_rule_dict(
            pattern, new_text, corrected, flags, entry.get("id"),
        )
        corrections.extend(cs)
    return new_text, corrections


def _apply_rule_dict(
    pattern: str,
    text: str,
    replacement: str,
    flags: int,
    dict_id: str,
) -> Tuple[str, List[Dict[str, Any]]]:
    corrections: List[Dict[str, Any]] = []
    out_parts: List[str] = []
    last = 0
    for m in re.finditer(pattern, text, flags=flags):
        original = m.group(0)
        out_parts.append(text[last:m.start()])
        out_parts.append(replacement)
        last = m.end()
        corrections.append({
            "correction_id": None,
            "rule_id": None,
            "dict_id": dict_id,
            "char_pos": m.start(),
            "char_end": m.end(),
            "original": original,
            "corrected": replacement,
            "applied_at": datetime.now(timezone.utc).isoformat(),
        })
    out_parts.append(text[last:])
    return "".join(out_parts), corrections


# ============================================================
# Region processing
# ============================================================

def should_skip_class(semantic_class: Optional[str]) -> bool:
    return semantic_class in SKIP_CLASSES


def should_apply_full_rules(semantic_class: Optional[str]) -> bool:
    return semantic_class in PROSE_CLASSES


def process_region(
    region: Dict[str, Any],
    dictionary: List[Dict[str, Any]],
    counter: List[int],
    page_num: int,
) -> Dict[str, Any]:
    semantic_class = region.get("semantic_class")
    original_text = region.get("text", "") or ""
    region_id = region.get("id", "?")

    if should_skip_class(semantic_class):
        return {
            "id": region_id,
            "semantic_class": semantic_class,
            "original_text": original_text,
            "corrected_text": original_text,
            "corrections": [],
            "skipped": True,
            "skip_reason": "code_or_table_intact",
        }

    if semantic_class == FORMULA_CLASS:
        corrected, corrections = apply_dictionary(original_text, dictionary)
    elif should_apply_full_rules(semantic_class):
        corrected, corrections = apply_rules(original_text)
        corrected, dict_corrections = apply_dictionary(corrected, dictionary)
        corrections.extend(dict_corrections)
    else:
        corrected, corrections = apply_dictionary(original_text, dictionary)

    if len(corrections) > MAX_CORRECTIONS_PER_REGION:
        corrections = corrections[:MAX_CORRECTIONS_PER_REGION]

    for c in corrections:
        c["correction_id"] = f"c-{counter[0]:04d}"
        counter[0] += 1

    return {
        "id": region_id,
        "semantic_class": semantic_class,
        "original_text": original_text,
        "corrected_text": corrected,
        "corrections": corrections,
        "skipped": False,
        "skip_reason": None,
    }


# ============================================================
# Region loading
# ============================================================

def load_regions(source: Path) -> List[Tuple[int, Dict[str, Any]]]:
    """Returns list of (page_num, region) tuples from regions.json files."""
    regions_dir = source / "ingest" / "regions"
    if not regions_dir.exists():
        return []
    results: List[Tuple[int, Dict[str, Any]]] = []
    for p in sorted(regions_dir.glob("page-*.regions.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        page_num = int(data.get("page", 1))
        for r in data.get("regions", []):
            text_parts = []
            first = r.get("first_word", "")
            last = r.get("last_word", "")
            if first:
                text_parts.append(first)
            if last and last != first:
                text_parts.append(last)
            text = " ".join(text_parts) if text_parts else ""
            explicit_text = r.get("text")
            if explicit_text:
                text = explicit_text
            results.append((page_num, {
                "id": r.get("id", "?"),
                "page": page_num,
                "semantic_class": r.get("semantic_class"),
                "text": text,
            }))
    return results


# ============================================================
# Audit log
# ============================================================

class AuditLog:
    def __init__(self, max_entries: int = MAX_AUDIT_LOG_ENTRIES) -> None:
        self.entries: List[Dict[str, Any]] = []
        self.max_entries = max_entries

    def add(self, action: str, correction_id: str, region_id: str, source: Optional[str]) -> None:
        entry = {
            "action": action,
            "correction_id": correction_id,
            "region_id": region_id,
            "applied_at": datetime.now(timezone.utc).isoformat(),
        }
        if source:
            entry["source"] = source
        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]

    def dump(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "entries": list(self.entries),
        }


# ============================================================
# Revert
# ============================================================

def perform_revert(source: Path, out_dir: Path, correction_id: str, audit_log: AuditLog) -> Tuple[int, int]:
    """Revert a specific correction_id. Returns (reverted_count, exit_code)."""
    reverted = 0
    post_dir = out_dir / "ingest" / "post_ocr"
    for p in sorted(post_dir.glob("page-*.post_ocr.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        modified = False
        for region in data.get("regions", []):
            corrections = region.get("corrections", [])
            new_corrections: List[Dict[str, Any]] = []
            for c in corrections:
                if c.get("correction_id") == correction_id:
                    original = c.get("original", "")
                    region["corrected_text"] = region["corrected_text"].replace(c.get("corrected", ""), original, 1)
                    audit_log.add("revert", correction_id, region.get("id", "?"), c.get("rule_id") or c.get("dict_id"))
                    reverted += 1
                    modified = True
                else:
                    new_corrections.append(c)
            region["corrections"] = new_corrections
        if modified:
            atomic_write_json(p, data)
    return reverted, (0 if reverted > 0 else 1)


def perform_revert_all(source: Path, out_dir: Path, audit_log: AuditLog) -> Tuple[int, int]:
    reverted = 0
    post_dir = out_dir / "ingest" / "post_ocr"
    for p in sorted(post_dir.glob("page-*.post_ocr.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        modified = False
        for region in data.get("regions", []):
            corrections = region.get("corrections", [])
            if not corrections:
                continue
            for c in corrections:
                original = c.get("original", "")
                region["corrected_text"] = region["corrected_text"].replace(c.get("corrected", ""), original, 1)
                audit_log.add("revert", c.get("correction_id", "?"), region.get("id", "?"), c.get("rule_id") or c.get("dict_id"))
                reverted += 1
            region["corrections"] = []
            modified = True
        if modified:
            atomic_write_json(p, data)
    return reverted, (0 if reverted > 0 else 1)


# ============================================================
# Entry point
# ============================================================

def run(
    source: Path,
    out_dir: Path,
    dictionary_path: Optional[Path],
    revert_id: Optional[str],
    revert_all: bool,
    json_only: bool,
) -> int:
    source = Path(source).resolve()
    if not source.exists():
        print(f"ERROR: source not found: {source}", file=sys.stderr)
        return 1

    warnings: List[str] = []
    dictionary = load_dictionary(dictionary_path)

    regions = load_regions(source)
    if not regions:
        warnings.append("no regions found")

    audit_log = AuditLog()
    counter = [1]

    out_post = out_dir / "ingest" / "post_ocr"
    out_post.mkdir(parents=True, exist_ok=True)

    if revert_id:
        reverted, rc = perform_revert(source, out_dir, revert_id, audit_log)
        atomic_write_json(out_post / "audit_log.json", audit_log.dump())
        if reverted == 0:
            print(f"WARNING: correction_id {revert_id} not found", file=sys.stderr)
            return 1
        return rc

    if revert_all:
        reverted, rc = perform_revert_all(source, out_dir, audit_log)
        atomic_write_json(out_post / "audit_log.json", audit_log.dump())
        if reverted == 0:
            print(f"WARNING: no corrections to revert", file=sys.stderr)
            return 1
        return rc

    by_page: Dict[int, List[Dict[str, Any]]] = {}
    skipped_count = 0
    modified_count = 0
    total_corrections = 0
    rule_dist: Counter = Counter()
    dict_dist: Counter = Counter()

    for page_num, region in regions:
        annotated = process_region(region, dictionary, counter, page_num)
        by_page.setdefault(page_num, []).append(annotated)
        if annotated["skipped"]:
            skipped_count += 1
        if annotated["corrections"]:
            modified_count += 1
            total_corrections += len(annotated["corrections"])
            for c in annotated["corrections"]:
                if c.get("rule_id"):
                    rule_dist[c["rule_id"]] += 1
                if c.get("dict_id"):
                    dict_dist[c["dict_id"]] += 1
                audit_log.add("apply", c["correction_id"], annotated["id"], c.get("rule_id") or c.get("dict_id"))

    for page_num, regs in by_page.items():
        atomic_write_json(
            out_post / f"page-{page_num:04d}.post_ocr.json",
            {"page": page_num, "regions": regs},
        )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "ingest_dir": str(source),
            "dictionary_path": str(dictionary_path) if dictionary_path else None,
            "hash": sha256_paths([source] + ([dictionary_path] if dictionary_path else [])),
        },
        "total_regions": len(regions),
        "modified_regions": modified_count,
        "skipped_regions_count": skipped_count,
        "rule_distribution": dict(rule_dist),
        "dict_distribution": dict(dict_dist),
        "total_corrections": total_corrections,
        "revertible": True,
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    atomic_write_json(out_post / "post_ocr_summary.json", summary)
    atomic_write_json(out_post / "audit_log.json", audit_log.dump())

    if not json_only:
        md_lines = [f"# Post-OCR — `{source.name}`", ""]
        md_lines.append(f"- **Total regiones:** {len(regions)}")
        md_lines.append(f"- **Modificadas:** {modified_count}")
        md_lines.append(f"- **Saltadas (código/tabla):** {skipped_count}")
        md_lines.append(f"- **Total correcciones:** {total_corrections}")
        if rule_dist:
            md_lines.append(f"- **Por regla:** {dict(rule_dist)}")
        if dict_dist:
            md_lines.append(f"- **Por diccionario:** {dict(dict_dist)}")
        atomic_write_text(out_post / "post_ocr.md", "\n".join(md_lines) + "\n")

    return 2 if warnings else 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="post_ocr.py",
        description="F27 — Deterministic post-OCR correction with revertible per-correction tracking.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Constantes (references/01-ingest/post-ocr.md §3-§7):
  INDENT_PRESERVE_MIN          = 4      espacios para preservar indentación
  MAX_CORRECTIONS_PER_REGION   = 50     máximo de correcciones por región
  MAX_DICTIONARY_ENTRIES       = 1000   máximo de entradas en dictionary.yaml
  MAX_AUDIT_LOG_ENTRIES        = 1000   máximo de entradas en audit_log

Reglas (10):
  R001  espacio después de \\n si la siguiente palabra no es mayúscula/dígito/[({<
  R002  colapsa \\n{3,} a \\n\\n
  R003  colapsa espacios dobles (preserva indentación ≥ 4)
  R004  convierte tabs a espacios
  R005-R008  ligaduras ﬁ, ﬂ, ﬃ, ﬄ → fi, fl, ffi, ffl
  R009  numeración incrustada → \\n\\n después del número
  R010  marcadores (N) o [N] → línea propia

Diccionario default (5 entradas): PostgreSQL, JavaScript, TypeScript, python, mySQL.

Regiones saltadas: code, console, table, syntax_diagram.
Regiones con solo diccionario: formula.

Códigos de salida:
  0 OK sin advertencias
  1 error fatal
  2 OK con advertencias (regiones saltadas, parcial)
""",
    )
    parser.add_argument("--source", required=True, help="Directorio raíz (contiene ingest/)")
    parser.add_argument("--out-dir", required=True, help="Directorio de salida (ingest/post_ocr/)")
    parser.add_argument("--dictionary", default=None, help="Diccionario YAML opcional (default: 5 entradas comunes)")
    parser.add_argument("--revert", default=None, help="correction_id a revertir (modo revert)")
    parser.add_argument("--revert-all", action="store_true", help="Revierte todas las correcciones del último run")
    parser.add_argument("--json-only", action="store_true", help="Solo escribir JSON (no post_ocr.md)")
    args = parser.parse_args(argv)

    dictionary_path = Path(args.dictionary) if args.dictionary else None
    code = run(
        Path(args.source),
        Path(args.out_dir),
        dictionary_path,
        args.revert,
        args.revert_all,
        args.json_only,
    )
    return code


if __name__ == "__main__":
    sys.exit(main())
