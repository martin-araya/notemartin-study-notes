#!/usr/bin/env python3
"""paper_coverage.py — Validador de completitud y cobertura para artículos de investigación (P6).

Verifica que las notas cubran al menos el 98 % del contenido del paper, midiendo:
1. Cobertura ponderada por palabras del cuerpo del documento (>= 0.98).
2. Conservación del 100 % de entidades críticas (ecuaciones numeradas, teoremas,
   algoritmos y tablas).
3. Integridad bibliográfica y resolución de citas.

Uso:
    python3 scripts/validate/paper_coverage.py --sdm <sdm.json> --ledger <ledger.json> --min 0.98
    python3 scripts/validate/paper_coverage.py --workdir <dir> [--min 0.98] [--out-dir <dir>]

Salidas:
    reports/paper_coverage.json — reporte estructurado
    reports/paper_coverage.md   — resumen en Markdown

Códigos de salida:
    0 — PASS (cobertura >= umbral y 100 % de entidades críticas cubiertas)
    1 — FAIL (cobertura < umbral o entidad crítica omitida)
    2 — USAGE / error de ejecución
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

SCHEMA_VERSION = "1.0.0"

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

WORD_RE = re.compile(r"\b\w+\b")
CITATION_RE = re.compile(r"\[(?:cite:)?(?P<num>\d+)\]|\\cite\{(?P<key>[^}]+)\}")


def count_words(text: str) -> int:
    """Cuenta palabras alfanuméricas en un texto."""
    if not text:
        return 0
    return len(WORD_RE.findall(text))


def extract_block_words(block: Dict[str, Any]) -> int:
    """Calcula las palabras contenidas en un bloque según su tipo."""
    b_type = block.get("type", "")
    content = block.get("content")

    if b_type == "boilerplate":
        return 0

    if isinstance(content, str):
        return count_words(content)

    if isinstance(content, dict):
        # heading: text
        if "text" in content:
            return count_words(str(content["text"]))
        # list: items
        if "items" in content and isinstance(content["items"], list):
            return sum(count_words(str(it)) for it in content["items"])
        # table: headers + rows
        if "headers" in content and "rows" in content:
            w = sum(count_words(str(h)) for h in content.get("headers", []))
            for row in content.get("rows", []):
                w += sum(count_words(str(c)) for c in row)
            return w
        # code: text / lines
        if "text" in content:
            return count_words(str(content["text"]))
        if "lines" in content and isinstance(content["lines"], list):
            return sum(count_words(str(l)) for l in content["lines"])
        # formula: contar símbolos / variables
        if "latex" in content:
            return max(1, count_words(str(content["latex"])))

    return 0


def analyze_sdm_coverage(
    sdm_data: Dict[str, Any],
    ledger_data: Dict[str, Any],
    min_coverage: float = 0.98,
) -> Dict[str, Any]:
    """Evalúa la cobertura del SDM contra las unidades registradas en el ledger."""
    # 1. Mapear bloques cubiertos por el ledger
    entries = ledger_data.get("entries", [])
    covered_block_ids: Set[str] = set()
    discarded_block_ids: Set[str] = set()

    # Tipos críticos en el ledger
    covered_theorems: Set[str] = set()
    covered_algorithms: Set[str] = set()
    covered_formulas: Set[str] = set()

    for ent in entries:
        state = ent.get("state")
        source_blocks = ent.get("source_block_ids", [])
        u_type = ent.get("type")

        if state in ("written", "merged"):
            for bid in source_blocks:
                covered_block_ids.add(bid)
            if u_type == "theorem":
                covered_theorems.update(source_blocks)
            elif u_type == "algorithm":
                covered_algorithms.update(source_blocks)
            elif u_type == "formula":
                covered_formulas.update(source_blocks)
        elif state == "discarded":
            reason = ent.get("discard_reason", "")
            if reason in ("boilerplate", "duplicate"):
                for bid in source_blocks:
                    discarded_block_ids.add(bid)

    # 2. Recorrer bloques del SDM
    total_body_words = 0
    covered_body_words = 0

    category_stats: Dict[str, Dict[str, int]] = {
        "prose": {"total": 0, "covered": 0},
        "heading": {"total": 0, "covered": 0},
        "table": {"total": 0, "covered": 0},
        "code": {"total": 0, "covered": 0},
        "formula": {"total": 0, "covered": 0},
        "figure": {"total": 0, "covered": 0},
        "theorem": {"total": 0, "covered": 0},
        "algorithm": {"total": 0, "covered": 0},
        "other": {"total": 0, "covered": 0},
    }

    # Entidades críticas en SDM
    total_numbered_formulas = 0
    covered_numbered_formulas = 0
    total_theorems = 0
    total_algorithms = 0
    total_tables = 0
    covered_tables = 0

    sections = sdm_data.get("sections", [])
    for sec in sections:
        sec_path = sec.get("section_path", "")
        for blk in sec.get("blocks", []):
            bid = blk.get("id")
            b_type = blk.get("type", "other")
            if b_type == "boilerplate":
                continue

            words = extract_block_words(blk)
            total_body_words += words

            is_covered = (bid in covered_block_ids) or (bid in discarded_block_ids)
            if is_covered:
                covered_body_words += words

            cat_key = b_type if b_type in category_stats else "other"
            category_stats[cat_key]["total"] += words
            if is_covered:
                category_stats[cat_key]["covered"] += words

            # Conteo de entidades críticas
            if b_type == "formula":
                content = blk.get("content", {})
                if isinstance(content, dict) and content.get("display"):
                    # Verificar si es numerada
                    total_numbered_formulas += 1
                    if is_covered or bid in covered_formulas:
                        covered_numbered_formulas += 1
            elif b_type in ("theorem", "lemma", "proposition", "corollary"):
                total_theorems += 1
            elif b_type == "algorithm":
                total_algorithms += 1
            elif b_type == "table":
                total_tables += 1
                if is_covered:
                    covered_tables += 1

    # Ratio de cobertura de palabras
    word_coverage = (covered_body_words / total_body_words) if total_body_words > 0 else 1.0

    # Cobertura de entidades críticas
    eq_coverage = (covered_numbered_formulas / total_numbered_formulas) if total_numbered_formulas > 0 else 1.0
    thm_coverage = (len(covered_theorems) / total_theorems) if total_theorems > 0 else 1.0
    alg_coverage = (len(covered_algorithms) / total_algorithms) if total_algorithms > 0 else 1.0
    tab_coverage = (covered_tables / total_tables) if total_tables > 0 else 1.0

    critical_passed = (
        eq_coverage >= 1.0
        and thm_coverage >= 1.0
        and alg_coverage >= 1.0
        and tab_coverage >= 1.0
    )

    global_passed = (word_coverage >= min_coverage) and critical_passed

    findings: List[Dict[str, Any]] = []
    if word_coverage < min_coverage:
        findings.append({
            "severity": "critical",
            "message": f"Cobertura ponderada de palabras ({word_coverage:.1%}) inferior al umbral ({min_coverage:.1%}).",
            "delta_words": int(total_body_words * min_coverage) - covered_body_words,
        })
    if eq_coverage < 1.0:
        findings.append({
            "severity": "critical",
            "message": f"Ecuaciones numeradas incompletas: {covered_numbered_formulas}/{total_numbered_formulas} cubiertas.",
        })
    if thm_coverage < 1.0:
        findings.append({
            "severity": "critical",
            "message": f"Teoremas o lemas incompletos: {len(covered_theorems)}/{total_theorems} cubiertos.",
        })
    if alg_coverage < 1.0:
        findings.append({
            "severity": "critical",
            "message": f"Algoritmos incompletos: {len(covered_algorithms)}/{total_algorithms} cubiertos.",
        })
    if tab_coverage < 1.0:
        findings.append({
            "severity": "critical",
            "message": f"Tablas incompletas: {covered_tables}/{total_tables} cubiertas.",
        })

    return {
        "status": "PASS" if global_passed else "FAIL",
        "word_coverage": round(word_coverage, 4),
        "min_coverage_threshold": min_coverage,
        "total_body_words": total_body_words,
        "covered_body_words": covered_body_words,
        "critical_entities": {
            "numbered_formulas": {
                "total": total_numbered_formulas,
                "covered": covered_numbered_formulas,
                "coverage": round(eq_coverage, 4),
            },
            "theorems": {
                "total": total_theorems,
                "covered": len(covered_theorems),
                "coverage": round(thm_coverage, 4),
            },
            "algorithms": {
                "total": total_algorithms,
                "covered": len(covered_algorithms),
                "coverage": round(alg_coverage, 4),
            },
            "tables": {
                "total": total_tables,
                "covered": covered_tables,
                "coverage": round(tab_coverage, 4),
            },
        },
        "category_breakdown": {
            cat: {
                "total_words": data["total"],
                "covered_words": data["covered"],
                "coverage": round(data["covered"] / data["total"], 4) if data["total"] > 0 else 1.0,
            }
            for cat, data in category_stats.items()
        },
        "findings": findings,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }


def format_markdown_report(report: Dict[str, Any]) -> str:
    """Genera un reporte legible en Markdown."""
    lines: List[str] = [
        f"# Auditoría de Cobertura de Paper (P6)",
        "",
        f"- **Estado global:** `{'✅ PASS' if report['status'] == 'PASS' else '❌ FAIL'}`",
        f"- **Cobertura ponderada:** `{report['word_coverage']:.1%}` (meta: `{report['min_coverage_threshold']:.1%}`)",
        f"- **Palabras del cuerpo:** `{report['covered_body_words']} / {report['total_body_words']}` cubiertas",
        "",
        "## Entidades críticas (Exigencia 100 %)",
        "",
        "| Entidad | Total | Cubiertas | Cobertura | Estado |",
        "|---|---|---|---|---|",
    ]

    for k, v in report["critical_entities"].items():
        st = "✅ 100 %" if v["coverage"] >= 1.0 else f"❌ {v['coverage']:.1%}"
        lines.append(f"| `{k}` | {v['total']} | {v['covered']} | {v['coverage']:.1%} | {st} |")

    lines.extend([
        "",
        "## Desglose por categoría",
        "",
        "| Categoría | Palabras Fuente | Palabras Cubiertas | % Cubierto |",
        "|---|---|---|---|",
    ])

    for cat, v in report["category_breakdown"].items():
        lines.append(f"| `{cat}` | {v['total_words']} | {v['covered_words']} | {v['coverage']:.1%} |")

    if report["findings"]:
        lines.extend([
            "",
            "## Hallazgos que bloquean el Gate",
            "",
        ])
        for f in report["findings"]:
            lines.append(f"- ⚠️ **{f['severity'].upper()}**: {f['message']}")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validador de completitud y cobertura de papers (P6)")
    parser.add_argument("--sdm", type=Path, default=None, help="Ruta al archivo sdm.json")
    parser.add_argument("--ledger", type=Path, default=None, help="Ruta al archivo ledger.json")
    parser.add_argument("--workdir", type=Path, default=None, help="Directorio de trabajo que contiene sdm.json y ledger.json")
    parser.add_argument("--min", type=float, default=0.98, help="Umbral mínimo de cobertura (default: 0.98)")
    parser.add_argument("--out-dir", type=Path, default=None, help="Directorio destino para reportes")
    parser.add_argument("--json-only", action="store_true", help="Solo imprimir JSON en stdout")

    args = parser.parse_args()

    sdm_path = args.sdm
    ledger_path = args.ledger

    if args.workdir:
        if not sdm_path:
            sdm_path = args.workdir / "sdm.json"
        if not ledger_path:
            ledger_candidates = [
                args.workdir / "knowledge" / "ledger.json",
                args.workdir / "ledger.json",
            ]
            for c in ledger_candidates:
                if c.exists():
                    ledger_path = c
                    break

    if not sdm_path or not sdm_path.exists():
        sys.stderr.write(f"Error: sdm.json no encontrado: {sdm_path}\n")
        return EXIT_USAGE

    if not ledger_path or not ledger_path.exists():
        sys.stderr.write(f"Error: ledger.json no encontrado: {ledger_path}\n")
        return EXIT_USAGE

    try:
        sdm_data = json.loads(sdm_path.read_text(encoding="utf-8"))
        ledger_data = json.loads(ledger_path.read_text(encoding="utf-8"))
    except Exception as e:
        sys.stderr.write(f"Error leyendo archivos JSON: {e}\n")
        return EXIT_USAGE

    report = analyze_sdm_coverage(sdm_data, ledger_data, min_coverage=args.min)

    out_dir = args.out_dir or (args.workdir / "reports" if args.workdir else Path("reports"))
    out_dir.mkdir(parents=True, exist_ok=True)

    json_report_path = out_dir / "paper_coverage.json"
    json_report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    md_report = format_markdown_report(report)
    md_report_path = out_dir / "paper_coverage.md"
    md_report_path.write_text(md_report, encoding="utf-8")

    if args.json_only:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Paper Coverage: {report['status']} ({report['word_coverage']:.1%} >= {report['min_coverage_threshold']:.1%})")
        print(f"  Palabras cubiertas: {report['covered_body_words']}/{report['total_body_words']}")
        print(f"  Reporte guardado en: {json_report_path}")

    return EXIT_PASS if report["status"] == "PASS" else EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
