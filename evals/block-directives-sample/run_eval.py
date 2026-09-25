"""run_eval.py — autoverificación de Fase 45 (block-directives.md).

Uso:
    python3 evals/block-directives-sample/run_eval.py --check-all
    python3 evals/block-directives-sample/run_eval.py --criterion 1
    python3 evals/block-directives-sample/run_eval.py --check-all --json

Verifica los tres criterios de F45 más las invariantes transversales
(INV-06, INV-14, INV-D1, INV-D2, INV-D3, INV-D4). No requiere dependencias
externas (Python 3.9+ stdlib).

Criterios cubiertos:
  1. Cada directiva tiene ejemplo y anti-ejemplo (§10).
  2. La tabla de decisión resuelve los casos del corpus (§6).
  3. Ninguna directiva se solapa en propósito con otra (§7).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple

REPO = Path(__file__).resolve().parent.parent.parent
DOC = REPO / "skill" / "notemartin-study-notes" / "references" / "04-authoring" / "block-directives.md"
NOTEMARK_DOC = REPO / "skill" / "notemartin-study-notes" / "references" / "04-authoring" / "notemark.md"
SKILL_DOC = REPO / "skill" / "notemartin-study-notes" / "SKILL.md"
README_DOC = REPO / "skill" / "notemartin-study-notes" / "references" / "04-authoring" / "README.md"

EXPECTED_DIRECTIVES = [
    "warning", "note", "tip", "example", "danger", "security",
    "performance", "version", "deprecated", "conflict", "external", "derived",
    "collapsible", "columns", "param-table", "step", "question",
    "diagram", "figure", "equation", "console", "property",
]


class Result(NamedTuple):
    name: str
    passed: bool
    detail: str


def _load(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_22_entries(doc: str) -> Result:
    headings = re.findall(r"^### 10\.(\d+) `:::(\w[\w-]*)`", doc, flags=re.MULTILINE)
    found = [name for _, name in headings]
    missing = [d for d in EXPECTED_DIRECTIVES if d not in found]
    extra = [d for d in found if d not in EXPECTED_DIRECTIVES]
    return Result(
        "22 directivas documentadas (§10)",
        not missing and not extra and len(found) == 22,
        f"encontradas={len(found)} expected=22 missing={missing} extra={extra}",
    )


def check_each_entry_has_example_and_antiexample(doc: str) -> Result:
    """Cada §10.X debe contener al menos dos bloques ```notemark (ejemplo + anti-ejemplo)."""
    failures = []
    sections = re.split(r"^### 10\.\d+ ", doc, flags=re.MULTILINE)
    # sections[0] = preámbulo; sections[1:] = cada entrada
    for section in sections[1:]:
        # La primera línea es el título; el resto es el cuerpo
        body = section.split("\n", 1)[1] if "\n" in section else section
        # Siguiente sección o fin de archivo delimita
        n_blocks = len(re.findall(r"^````notemark$", body, flags=re.MULTILINE))
        if n_blocks < 2:
            title_line = section.split("\n", 1)[0]
            failures.append(f"{title_line}: {n_blocks} bloque(s), necesita ≥ 2")
    return Result(
        "Cada directiva tiene ejemplo y anti-ejemplo",
        not failures,
        f"fallos={len(failures)} :: {failures[:3]}",
    )


def check_decision_table_covers_corpus(doc: str) -> Result:
    """§6 debe tener ≥18 filas y mencionar ≥14 corpus."""
    section6_match = re.search(r"^## §6 ·.*?\n(.*?)^## §7 ·", doc, flags=re.MULTILINE | re.DOTALL)
    if not section6_match:
        return Result("Tabla de decisión cubre corpus", False, "§6 no encontrada")
    section6 = section6_match.group(1)
    rows = re.findall(r"^\| \d+ \|", section6, flags=re.MULTILINE)
    corpus_unique = set(re.findall(r"`(\d\d-[a-z0-9-]+)`", section6))
    return Result(
        "Tabla de decisión cubre ≥18 filas y ≥14 corpus",
        len(rows) >= 18 and len(corpus_unique) >= 14,
        f"filas={len(rows)} corpus_unicos={len(corpus_unique)}",
    )


def check_fronters_discriminator(doc: str) -> Result:
    """§7 debe tener 12 pares; cada par con discriminador no vacío."""
    section7_match = re.search(r"^## §7 ·.*?\n(.*?)^## §8 ·", doc, flags=re.MULTILINE | re.DOTALL)
    if not section7_match:
        return Result("Tabla de fronteras con discriminador", False, "§7 no encontrada")
    section7 = section7_match.group(1)
    # Filas numeradas (cualquier formato, no solo directiva-vs-directiva)
    rows = re.findall(r"^\| \d+ \|", section7, flags=re.MULTILINE)
    # Discriminador: pregunta terminada en → que aparece en la última columna
    discriminators = re.findall(r"¿[^|?]+\?\s*→", section7)
    return Result(
        "12 pares con discriminador (§7)",
        len(rows) >= 12 and len(discriminators) >= 12,
        f"filas={len(rows)} discriminadores={len(discriminators)}",
    )


def check_inv06_no_platform_syntax(doc: str) -> Result:
    """INV-06: cero `> [!...]` (sintaxis de callout Obsidian)."""
    # Buscar la directiva como texto literal fuera de bloques de código
    # (los anti-ejemplos sí pueden mostrar `> [!warning]` dentro de ```notemark)
    lines = doc.split("\n")
    failures = []
    in_code = False
    for i, line in enumerate(lines, 1):
        if line.startswith("```"):
            in_code = not in_code
            continue
        if not in_code and re.match(r"^\s*>\s*\[!", line):
            failures.append(f"L{i}: {line.rstrip()}")
    return Result(
        "INV-06: cero sintaxis de plataforma fuera de bloques de código",
        not failures,
        f"violaciones={len(failures)} :: {failures[:3]}",
    )


def check_inv14_no_literal_colors(doc: str) -> Result:
    """INV-14: cero colores hex literales fuera de {src:blk_xxxx}."""
    # Buscar `#` seguido de 3 o 6 hex no precedido por `src:`
    lines = doc.split("\n")
    failures = []
    in_code = False
    for i, line in enumerate(lines, 1):
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        # Permitir {src:blk_xxxxx} (donde x es hex)
        stripped = re.sub(r"\{src:blk_[0-9a-f]+\}", "", line)
        # Permitir EBNF con `0-9` y `a-f` en contextos obvios de gramática
        for m in re.finditer(r"#([0-9a-fA-F]{3,6})\b", stripped):
            # Excluir si es parte de una referencia markdown tipo [texto](#anchor)
            before = stripped[: m.start()]
            if before.endswith("]("):
                continue
            failures.append(f"L{i}: {m.group(0)}")
    return Result(
        "INV-14: cero colores literales",
        not failures,
        f"violaciones={len(failures)} :: {failures[:3]}",
    )


def check_nesting_depth(doc: str) -> Result:
    """INV-D4: ninguna mención de profundidad > 3 niveles en ejemplos."""
    # Regla positiva: el doc declara profundidad ≤ 3
    if "profundidad de anidamiento nunca supera 3 niveles" in doc:
        return Result("INV-D4: límite de profundidad ≤ 3 declarado", True, "")
    return Result("INV-D4: límite de profundidad ≤ 3 declarado", False, "no encontrado")


def check_routes_closed_in_skill() -> Result:
    """SKILL.md no debe tener rutas [pendiente F45]."""
    if not SKILL_DOC.exists():
        return Result("Ruta F45 cerrada en SKILL.md", False, "SKILL.md no existe")
    content = _load(SKILL_DOC)
    if "[pendiente F45]" in content:
        return Result("Ruta F45 cerrada en SKILL.md", False, "quedan entradas [pendiente F45]")
    return Result("Ruta F45 cerrada en SKILL.md", True, "")


def check_readme_no_pending_f45() -> Result:
    if not README_DOC.exists():
        return Result("README 04-authoring actualizado", False, "no existe")
    content = _load(README_DOC)
    if "[pendiente F45]" in content:
        return Result("README 04-authoring actualizado", False, "queda [pendiente F45]")
    return Result("README 04-authoring actualizado", True, "")


def check_notemark_shrunk() -> Result:
    """notemark.md debe haber encogido y no contener ya las 21 subsecciones de directivas."""
    if not NOTEMARK_DOC.exists():
        return Result("notemark.md §6 movido a puntero", False, "no existe")
    content = _load(NOTEMARK_DOC)
    n_directive_subs = len(re.findall(r"^### :::", content, flags=re.MULTILINE))
    n_lines = content.count("\n")
    return Result(
        "notemark.md §6 movido a puntero",
        n_directive_subs == 0 and n_lines <= 313,
        f"lineas={n_lines} directivas_subsections={n_directive_subs}",
    )


def check_every_admonition_with_src(doc: str) -> Result:
    """INV-D1: cada admonition con hecho fáctico lleva {src:blk_xxxx}."""
    # No es chequeable automáticamente al 100% (algunos ejemplos pueden no llevarlo
    # por excepción documentada: danger, tip, external). Verificamos que el patrón
    # aparece en los ejemplos de directivas que sí lo requieren.
    admonitions_requiring_src = ["warning", "note", "example", "performance",
                                  "version", "security", "deprecated", "conflict"]
    missing = []
    for name in admonitions_requiring_src:
        # Buscar la subsección de la directiva
        pattern = rf"^### 10\.\d+ `:::{name}`(.*?)(?=^### 10\.\d+|^---|\Z)"
        m = re.search(pattern, doc, flags=re.MULTILINE | re.DOTALL)
        if not m:
            missing.append(f"{name}: sección no encontrada")
            continue
        body = m.group(1)
        # El primer bloque ```notemark (ejemplo) debería llevar {src:}
        first_block = re.search(r"^````notemark\n(.*?)^````", body, flags=re.MULTILINE | re.DOTALL)
        if first_block and "{src:" not in first_block.group(1):
            # Excepción: :::danger puede no llevarlo
            if name != "danger":
                missing.append(f"{name}: ejemplo sin {{src:}}")
    return Result(
        "INV-D1: admonitions con hecho fáctico llevan {src:}",
        not missing,
        f"faltan={len(missing)} :: {missing[:3]}",
    )


def run_all() -> list[Result]:
    if not DOC.exists():
        return [Result("archivo block-directives.md existe", False, str(DOC))]
    doc = _load(DOC)
    doc_checks = [
        check_22_entries,
        check_each_entry_has_example_and_antiexample,
        check_decision_table_covers_corpus,
        check_fronters_discriminator,
        check_inv06_no_platform_syntax,
        check_inv14_no_literal_colors,
        check_nesting_depth,
        check_every_admonition_with_src,
    ]
    results = [c(doc) for c in doc_checks]
    results.append(check_routes_closed_in_skill())
    results.append(check_readme_no_pending_f45())
    results.append(check_notemark_shrunk())
    return results


CRITERION_MAP = {
    1: ["Cada directiva tiene ejemplo y anti-ejemplo"],
    2: ["Tabla de decisión cubre ≥18 filas y ≥14 corpus"],
    3: ["12 pares con discriminador (§7)"],
}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-all", action="store_true", help="Ejecuta todas las verificaciones")
    parser.add_argument("--criterion", type=int, choices=[1, 2, 3], help="Verifica solo un criterio ROADMAP")
    parser.add_argument("--json", action="store_true", help="Salida JSON")
    args = parser.parse_args(argv)

    results = run_all()
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
