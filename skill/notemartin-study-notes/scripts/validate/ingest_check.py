#!/usr/bin/env python3
"""ingest_check.py — F30 ingest verification (gate to L2).

Detecta anomalías en la ingesta (páginas omitidas, secciones del índice
ausentes, saltos de numeración, bloques vacíos, densidad anómala) y emite un
reporte con las anomalías categorizadas en critical (bloquean L2) y warnings.

Uso:
    python3 scripts/validate/ingest_check.py \
        --sdm <path> \
        --declared-index <path> \
        --out-dir <dir> \
        [--allow-critical] [--human-decision "..."] [--json-only]

Salidas (en <out-dir>/):
    validation_report.json — reporte con anomalies (critical + warnings)
    decision_log.json — registro de overrides humanos (opcional)

Códigos de salida:
    0 — OK (sin anomalías o override humano aplicado)
    1 — BLOQUEADO (anomalías críticas sin override)
    2 — Warnings sin críticas (gate abierto)

Dependencias:
    - Python 3.9+ stdlib

Documentación normativa: references/01-ingest/ingest-check.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"

# ============================================================
# Constants (per references/01-ingest/ingest-check.md)
# ============================================================

MIN_WORDS_PER_BLOCK = 3
MAX_WORDS_PER_BLOCK = 5000
MAX_NUMBERING_JUMP_FOR_WARNING = 1
MAX_NUMBERING_JUMP_FOR_CRITICAL = 100

HEADING_CLASSES = frozenset({
    "heading", "heading_1", "heading_2", "heading_3", "heading_4", "heading_5",
    "heading_6", "title", "section_header",
})


# ============================================================
# Helpers
# ============================================================

def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent), delete=False) as tf:
        tf.write(content)
        tmpname = tf.name
    Path(tmpname).replace(path)


def word_count(text: str) -> int:
    if not text:
        return 0
    return len(text.split())


def parse_section_number(num: str) -> Optional[Tuple[int, ...]]:
    """Parses '1.2.3' to (1, 2, 3). Returns None if not a valid dotted number."""
    if not num:
        return None
    parts = num.split(".")
    if not all(p.isdigit() for p in parts):
        return None
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return None


# ============================================================
# Loading
# ============================================================

def load_sdm(sdm_path: Path) -> Dict[str, Any]:
    """Load SDM from file or directory. Returns normalized structure."""
    if sdm_path.is_file():
        data = json.loads(sdm_path.read_text(encoding="utf-8"))
    elif sdm_path.is_dir():
        region_files = sorted(sdm_path.glob("page-*.regions.json"))
        if not region_files:
            raise RuntimeError(f"no page-*.regions.json files found in {sdm_path}")
        all_regions = []
        for rf in region_files:
            page_data = json.loads(rf.read_text(encoding="utf-8"))
            page_num = page_data.get("page", 1)
            for r in page_data.get("regions", []):
                r.setdefault("page", page_num)
                all_regions.append(r)
        data = {"regions": all_regions}
    else:
        raise RuntimeError(f"sdm path not found: {sdm_path}")
    if not isinstance(data, dict):
        raise RuntimeError(f"SDM file does not contain a JSON object: {sdm_path}")
    regions = data.get("regions", [])
    if not regions and "pages" in data:
        regions = [{"page": p.get("page", i + 1), "text": p.get("text", "")} for i, p in enumerate(data["pages"])]
    return {"regions": regions, "data": data}


def load_declared_index(declared_path: Optional[Path]) -> Dict[str, Any]:
    """Load declared index. Returns empty dict if path is None or file missing."""
    if declared_path is None or not declared_path.exists():
        return {"sections": [], "pages": []}
    return json.loads(declared_path.read_text(encoding="utf-8"))


# ============================================================
# Validations
# ============================================================

def validate_pages(sdm: Dict[str, Any], declared: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Detect missing pages. Anomaly: critical."""
    sdm_pages = {r["page"] for r in sdm["regions"] if "page" in r}
    declared_pages = set(declared.get("pages", []))
    if not declared_pages:
        return []
    missing = sorted(declared_pages - sdm_pages)
    return [
        {"type": "missing_page", "page": p, "reason": f"page {p} declared but not in SDM"}
        for p in missing
    ]


def validate_sections(sdm: Dict[str, Any], declared: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Detect missing/extra sections. Anomaly: critical for missing, info for extra."""
    sdm_sections = {r.get("number") for r in sdm["regions"] if r.get("number")}
    declared_sections = [s for s in declared.get("sections", []) if s.get("number")]
    declared_numbers = {s["number"] for s in declared_sections}
    missing = sorted(declared_numbers - sdm_sections)
    extra = sorted(sdm_sections - declared_numbers)
    missing_anomalies = [
        {"type": "missing_section", "section": n, "reason": f"section {n} declared in index but not found in SDM"}
        for n in missing
    ]
    extra_info = [
        {"type": "extra_section", "section": n, "reason": f"section {n} in SDM but not in declared index"}
        for n in extra
    ]
    return missing_anomalies, extra_info


def validate_numbering_jumps(sdm: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Detect numbering jumps. Anomaly: warning if jump <= 100, critical if > 100."""
    warnings: List[Dict[str, Any]] = []
    sdm_section_numbers = [r.get("number") for r in sdm["regions"] if r.get("number")]
    parsed = [(n, parse_section_number(n)) for n in sdm_section_numbers]
    parsed = [(n, p) for n, p in parsed if p is not None]
    parsed.sort(key=lambda x: x[1])
    for i in range(len(parsed) - 1):
        n_a, p_a = parsed[i]
        n_b, p_b = parsed[i + 1]
        if len(p_a) != len(p_b):
            continue
        if all(p_b[j] >= p_a[j] for j in range(len(p_a))):
            if len(p_a) >= 2:
                last = p_a[-1]
                next_first = p_b[-1]
                skip_count = next_first - last - 1
                if skip_count > 0 and skip_count <= MAX_NUMBERING_JUMP_FOR_WARNING:
                    warnings.append({
                        "type": "numbering_jump",
                        "from": n_a,
                        "to": n_b,
                        "skipped": f"{'.'.join(map(str, p_a[:-1]))}.{last + 1}",
                        "reason": f"consecutive number gap ({skip_count} skipped)",
                    })
                elif skip_count > MAX_NUMBERING_JUMP_FOR_CRITICAL:
                    warnings.append({
                        "type": "missing_branch",
                        "from": n_a,
                        "to": n_b,
                        "skipped": skip_count,
                        "reason": f"large numbering gap ({skip_count} sections skipped)",
                        "critical": True,
                    })
    return warnings


def validate_blocks(sdm: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Detect empty blocks and anomalous density. Anomaly: critical for empty headings."""
    warnings: List[Dict[str, Any]] = []
    for r in sdm["regions"]:
        text = (r.get("text") or "").strip()
        sem = r.get("semantic_class", "")
        wc = word_count(text)
        if not text:
            if sem in HEADING_CLASSES or sem.startswith("heading") or r.get("level"):
                warnings.append({
                    "type": "empty_heading",
                    "block_id": r.get("id", "?"),
                    "page": r.get("page"),
                    "reason": f"heading block empty: {r.get('text', '')[:50]}",
                    "critical": True,
                })
            else:
                warnings.append({
                    "type": "empty_block",
                    "block_id": r.get("id", "?"),
                    "page": r.get("page"),
                    "reason": "block text is empty",
                })
            continue
        if wc < MIN_WORDS_PER_BLOCK:
            warnings.append({
                "type": "too_short",
                "block_id": r.get("id", "?"),
                "page": r.get("page"),
                "wc": wc,
                "reason": f"word_count={wc} < MIN_WORDS_PER_BLOCK={MIN_WORDS_PER_BLOCK}",
            })
        elif wc > MAX_WORDS_PER_BLOCK:
            warnings.append({
                "type": "too_long",
                "block_id": r.get("id", "?"),
                "page": r.get("page"),
                "wc": wc,
                "reason": f"word_count={wc} > MAX_WORDS_PER_BLOCK={MAX_WORDS_PER_BLOCK}",
            })
    return warnings


# ============================================================
# Main
# ============================================================

def build_report(
    sdm: Dict[str, Any],
    declared: Dict[str, Any],
    sdm_path: Path,
    declared_path: Optional[Path],
) -> Dict[str, Any]:
    """Build the validation_report.json structure."""
    all_anomalies: List[Dict[str, Any]] = []
    all_anomalies.extend(validate_pages(sdm, declared))
    missing_secs, extra_secs = validate_sections(sdm, declared)
    all_anomalies.extend(missing_secs)
    numbering_anomalies = validate_numbering_jumps(sdm)
    all_anomalies.extend(numbering_anomalies)
    block_anomalies = validate_blocks(sdm)
    all_anomalies.extend(block_anomalies)

    critical: List[Dict[str, Any]] = []
    warnings_only: List[Dict[str, Any]] = []
    info: List[Dict[str, Any]] = []

    for a in all_anomalies:
        if a.pop("critical", False):
            critical.append(a)
        else:
            warnings_only.append(a)
    for a in extra_secs:
        a.pop("critical", False)
        info.append(a)

    sdm_pages = sorted({r["page"] for r in sdm["regions"] if "page" in r})
    declared_pages = sorted(set(declared.get("pages", [])))
    sdm_section_numbers = sorted({r.get("number") for r in sdm["regions"] if r.get("number")}, key=lambda x: parse_section_number(x) or (99999,))
    declared_section_numbers = sorted({s.get("number") for s in declared.get("sections", []) if s.get("number")}, key=lambda x: parse_section_number(x) or (99999,))

    return {
        "schema_version": SCHEMA_VERSION,
        "sdm_path": str(sdm_path),
        "declared_index_path": str(declared_path) if declared_path else None,
        "totals": {
            "pages_in_sdm": len(sdm_pages),
            "pages_declared": len(declared_pages),
            "missing_pages": sorted(set(declared_pages) - set(sdm_pages)),
            "sections_declared": len(declared_section_numbers),
            "sections_present": len(set(sdm_section_numbers) & set(declared_section_numbers)),
            "missing_sections": sorted(set(declared_section_numbers) - set(sdm_section_numbers)),
            "extra_sections": sorted(set(sdm_section_numbers) - set(declared_section_numbers)),
        },
        "anomalies": {
            "critical": critical,
            "warnings": warnings_only,
        },
        "info": info,
        "human_decision": None,
        "validated_at": datetime.now(timezone.utc).isoformat(),
    }


def run(
    sdm_path: Path,
    declared_path: Optional[Path],
    out_dir: Path,
    allow_critical: bool = False,
    human_decision: Optional[str] = None,
    json_only: bool = False,
) -> int:
    sdm_path = sdm_path.resolve()
    if not sdm_path.exists():
        print(f"ERROR: sdm path not found: {sdm_path}", file=sys.stderr)
        return 1

    sdm = load_sdm(sdm_path)
    declared = load_declared_index(declared_path)

    report = build_report(sdm, declared, sdm_path, declared_path)
    critical_count = len(report["anomalies"]["critical"])

    if critical_count > 0 and allow_critical:
        if not human_decision:
            print("ERROR: --allow-critical requires --human-decision with reason", file=sys.stderr)
            return 1
        report["human_decision"] = "override"
        report["human_decision_reason"] = human_decision
        decision_log = {
            "decisions": [
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "decision": "override",
                    "critical_count": critical_count,
                    "reason": human_decision,
                }
            ]
        }
        out_dir.mkdir(parents=True, exist_ok=True)
        atomic_write_text(out_dir / "validation_report.json",
                           json.dumps(report, indent=2, ensure_ascii=False))
        atomic_write_text(out_dir / "decision_log.json",
                           json.dumps(decision_log, indent=2, ensure_ascii=False))
    else:
        out_dir.mkdir(parents=True, exist_ok=True)
        atomic_write_text(out_dir / "validation_report.json",
                           json.dumps(report, indent=2, ensure_ascii=False))

    if not json_only:
        md_lines = [f"# Ingest Check — `{sdm_path.name}`", ""]
        md_lines.append(f"- **SDM:** {sdm_path}")
        if declared_path:
            md_lines.append(f"- **Declared index:** {declared_path}")
        md_lines.append(f"- **Total regions:** {len(sdm['regions'])}")
        md_lines.append(f"- **Critical anomalies:** {critical_count}")
        md_lines.append(f"- **Warnings:** {len(report['anomalies']['warnings'])}")
        md_lines.append(f"- **Info:** {len(report['info'])}")
        if report["human_decision"]:
            md_lines.append(f"- **Human decision:** {report['human_decision']} ({report.get('human_decision_reason', '')})")
        if critical_count > 0 and not allow_critical:
            md_lines.append("")
            md_lines.append("## BLOCKED")
            md_lines.append("")
            md_lines.append("Critical anomalies detected. Use --allow-critical --human-decision \"reason\" to override.")
        atomic_write_text(out_dir / "ingest_check.md", "\n".join(md_lines) + "\n")

    if critical_count > 0 and not allow_critical:
        return 1
    if report["anomalies"]["warnings"]:
        return 2
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ingest_check.py",
        description="F30 — Ingest verification (gate to L2).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Constantes (references/01-ingest/ingest-check.md):
  MIN_WORDS_PER_BLOCK             = 3      palabras mínimas para bloque válido
  MAX_WORDS_PER_BLOCK             = 5000   palabras máximas
  MAX_NUMBERING_JUMP_FOR_WARNING  = 1      saltos consecutivos permitidos
  MAX_NUMBERING_JUMP_FOR_CRITICAL = 100    saltos grandes son críticos

Tipos de anomalías:
  critical:
    - missing_page        — página del input ausente en SDM
    - missing_section     — sección del índice no encontrada
    - missing_branch      — rama entera ausente (salto > 100)
    - empty_heading       — heading sin contenido
  warnings:
    - empty_block         — bloque no-heading con texto vacío
    - too_short / too_long — word_count fuera de rango
    - numbering_jump      — salto consecutivo (no crítico)
  info:
    - extra_section       — sección en SDM no presente en índice

Códigos de salida:
  0 OK (sin anomalías o override humano aplicado)
  1 BLOQUEADO (anomalías críticas sin override)
  2 OK con warnings (gate abierto)
""",
    )
    parser.add_argument("--sdm", required=True, help="Ruta al SDM (file o directory con page-*.regions.json)")
    parser.add_argument("--declared-index", default=None, help="Ruta al índice declarado (TOC JSON)")
    parser.add_argument("--out-dir", required=True, help="Directorio de salida")
    parser.add_argument("--allow-critical", action="store_true", help="Permite override de anomalías críticas (requiere --human-decision)")
    parser.add_argument("--human-decision", default=None, help="Razón del override humano")
    parser.add_argument("--json-only", action="store_true", help="Solo escribir JSON (no ingest_check.md)")
    args = parser.parse_args(argv)

    code = run(
        Path(args.sdm),
        Path(args.declared_index) if args.declared_index else None,
        Path(args.out_dir),
        allow_critical=args.allow_critical,
        human_decision=args.human_decision,
        json_only=args.json_only,
    )
    return code


if __name__ == "__main__":
    sys.exit(main())
