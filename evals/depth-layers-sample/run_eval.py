"""run_eval.py — autoverificación de Fase 51 (depth-layers.md).

Uso:
    python3 evals/depth-layers-sample/run_eval.py --check-all
    python3 evals/depth-layers-sample/run_eval.py --criterion N

Verifica los 3 criterios ROADMAP de F51 + cobertura estructural del doc.

Sin dependencias externas (Python 3.9+ stdlib).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple

REPO = Path(__file__).resolve().parent.parent.parent
DOC = REPO / "skill" / "notemartin-study-notes" / "references" / "04-authoring" / "depth-layers.md"
NOTEMARK_DOC = REPO / "skill" / "notemartin-study-notes" / "references" / "04-authoring" / "notemark.md"
FIXTURES = REPO / "evals" / "depth-layers-sample" / "fixtures"


class Result(NamedTuple):
    name: str
    passed: bool
    detail: str


def _load(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _section(doc: str, anchor: str, next_anchor: str | None) -> str:
    pat = rf"^## §{anchor}.*?\n(.*?)^## §{next_anchor}" if next_anchor else rf"^## §{anchor}.*?\n(.*?)\Z"
    m = re.search(pat, doc, flags=re.MULTILINE | re.DOTALL)
    return m.group(1) if m else ""


def check_doc_exists() -> Result:
    if not DOC.exists():
        return Result("depth-layers.md existe", False, str(DOC))
    return Result("depth-layers.md existe", True, "")


def check_doc_size() -> Result:
    n = DOC.read_text(encoding="utf-8").count("\n")
    return Result(
        "Tamaño entre 400 y 700 líneas",
        400 <= n <= 700,
        f"lineas={n}",
    )


def check_3_capas_documented() -> Result:
    """Criterio #1 parte 1: las 3 capas están documentadas."""
    doc = _load(DOC)
    l1 = bool(re.search(r"^### 3\.1 L1", doc, flags=re.MULTILINE))
    l2 = bool(re.search(r"^### 3\.2 L2", doc, flags=re.MULTILINE))
    l3 = bool(re.search(r"^### 3\.3 L3", doc, flags=re.MULTILINE))
    return Result(
        "Las 3 capas (L1/L2/L3) documentadas (§3)",
        l1 and l2 and l3,
        f"L1={l1} L2={l2} L3={l3}",
    )


def check_sintaxis_notemark() -> Result:
    """La sintaxis `{layer:lX}` está documentada con ejemplo."""
    doc = _load(DOC)
    n_mentions = doc.count("{layer:")
    has_example = "```notemark" in doc or "```\n# Título" in doc
    return Result(
        "Sintaxis {layer:lX} documentada con ejemplo",
        n_mentions >= 3 and has_example,
        f"menciones={n_mentions} ejemplo={has_example}",
    )


def check_15_tipos_table() -> Result:
    """§7 tiene los 15 tipos cerrados."""
    doc = _load(DOC)
    section7 = _section(doc, "7", "8")
    types = [
        "concept", "api-reference", "procedure", "configuration",
        "error-troubleshooting", "architecture", "syntax", "data-model",
        "chapter-digest", "comparison", "version-delta", "glossary-term",
        "cheatsheet", "index-moc", "practice",
    ]
    found = sum(1 for t in types if f"`{t}`" in section7)
    return Result(
        "§7 cubre los 15 tipos de nota",
        found == 15,
        f"encontrados={found} expected=15",
    )


def check_l1_max_size() -> Result:
    """Criterio #2: L1 ≤ 60 palabras, autonomía, comprensión correcta."""
    doc = _load(DOC)
    # Buscar el threshold explícito (≤ 60 palabras) y la lista de contenido obligatorio.
    has_threshold = bool(re.search(r"\u2264 60 palabras", doc)) or "≤ 60 palabras" in doc
    has_definition = "Definición del concepto" in doc
    has_proposito = "Propósito principal" in doc
    has_ejemplo = "Ejemplo mínimo" in doc
    has_caso = "Caso de uso" in doc
    return Result(
        "L1: ≤ 60 palabras + 4 elementos obligatorios (definición, propósito, ejemplo, caso de uso)",
        has_threshold and has_definition and has_proposito and has_ejemplo and has_caso,
        f"threshold={has_threshold} def={has_definition} prop={has_proposito} ej={has_ejemplo} caso={has_caso}",
    )


def check_extraction_threshold() -> Result:
    """§5 documenta threshold > 100 líneas o > 30%."""
    doc = _load(DOC)
    section5 = _section(doc, "5", "6")
    has_threshold_100 = "100 líneas" in section5
    has_threshold_30 = "30%" in section5
    has_back_link = "[[note:" in section5 and "back-link" in section5.lower()
    return Result(
        "§5: threshold > 100 líneas o 30%, back-link obligatorio",
        has_threshold_100 and has_threshold_30 and has_back_link,
        f"100_lineas={has_threshold_100} 30%={has_threshold_30} back_link={has_back_link}",
    )


def check_ledger_preservation() -> Result:
    """Criterio #3: regla de no-decremento del ledger."""
    doc = _load(DOC)
    section6 = _section(doc, "6", "7")
    has_rule = "no decrementa" in section6.lower() or "n_must_keep_terminal" in section6
    has_invariant = ">=" in section6 and "before" in section6
    return Result(
        "§6: regla de no-decremento del must-keep",
        has_rule and has_invariant,
        f"regla={has_rule} invariante={has_invariant}",
    )


def check_notemark_pointer() -> Result:
    """notemark.md §9 ahora apunta a depth-layers.md."""
    content = _load(NOTEMARK_DOC)
    has_pointer = "depth-layers.md" in content and "F51" in content
    return Result(
        "notemark.md §9 → depth-layers.md (F51)",
        has_pointer,
        f"puntero={has_pointer}",
    )


def check_extensa_with_3_layers() -> Result:
    """Fixture: nota extensa con tipo architecture tiene 3 capas asignadas."""
    fx = FIXTURES / "extensa-3capas.note-ir.json"
    if not fx.exists():
        return Result("Fixture: extensa con 3 capas", False, "fixture no existe")
    ir = json.loads(fx.read_text(encoding="utf-8"))
    layers_found = set()
    def walk(n):
        if isinstance(n, dict):
            layer = n.get("attrs", {}).get("layer")
            if layer:
                layers_found.add(layer)
            layer_top = n.get("layer")
            if layer_top:
                layers_found.add(layer_top)
            for c in n.get("children", []) or []:
                walk(c)
    walk({"children": ir.get("blocks", [])})
    found = {"l1", "l2", "l3"}.issubset(layers_found)
    return Result(
        "Fixture: extensa architecture con L1+L2+L3",
        found,
        f"layers={sorted(layers_found)}",
    )


def check_corta_solo_l2() -> Result:
    """Fixture: nota corta (no architecture) no requiere 3 capas."""
    fx = FIXTURES / "corta-l2.note-ir.json"
    if not fx.exists():
        return Result("Fixture: corta solo L2", False, "fixture no existe")
    ir = json.loads(fx.read_text(encoding="utf-8"))
    layers = set()
    def walk(n):
        if isinstance(n, dict):
            layer = n.get("attrs", {}).get("layer")
            if layer:
                layers.add(layer)
            for c in n.get("children", []) or []:
                walk(c)
    walk({"children": ir.get("blocks", [])})
    # No requiere las 3 capas; tener solo L2 está OK.
    return Result(
        "Fixture: corta solo L2 (sin requerir 3 capas)",
        len(layers) > 0,
        f"layers={sorted(layers)}",
    )


CRITERION_MAP = {
    1: ["Las 3 capas (L1/L2/L3) documentadas (§3)",
        "§7 cubre los 15 tipos de nota",
        "Fixture: extensa architecture con L1+L2+L3"],
    2: ["L1 ≤ 60 palabras documentadas",
        "Sintaxis {layer:lX} documentada con ejemplo"],
    3: ["§6: regla de no-decremento del must-keep",
        "Fixture: corta solo L2 (sin requerir 3 capas)"],
}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-all", action="store_true")
    parser.add_argument("--criterion", type=int, choices=[1, 2, 3])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    checks = [
        check_doc_exists,
        check_doc_size,
        check_3_capas_documented,
        check_sintaxis_notemark,
        check_15_tipos_table,
        check_l1_max_size,
        check_extraction_threshold,
        check_ledger_preservation,
        check_notemark_pointer,
        check_extensa_with_3_layers,
        check_corta_solo_l2,
    ]
    results = [c() for c in checks]

    if args.criterion:
        wanted = CRITERION_MAP[args.criterion]
        results = [r for r in results if r.name in wanted]

    if args.json:
        print(json.dumps([r._asdict() for r in results], indent=2, ensure_ascii=False))
    else:
        width = max(len(r.name) for r in results) + 2
        for r in results:
            mark = "PASS" if r.passed else "FAIL"
            print(f"  [{mark}] {r.name.ljust(width)} {r.detail}")
        n_pass = sum(1 for r in results if r.passed)
        n_total = len(results)
        print(f"\n  Resultado: {n_pass}/{n_total} verde")

    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
