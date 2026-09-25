"""run_eval.py — autoverificación de Fase 47 (properties.md).

Uso:
    python3 evals/properties-sample/run_eval.py --check-all
    python3 evals/properties-sample/run_eval.py --criterion N
    python3 evals/properties-sample/run_eval.py --check-all --json

Verifica los tres criterios ROADMAP de F47 + invariantes transversales.
No requiere dependencias externas (Python 3.9+ stdlib).

Criterios cubiertos:
  1. Cada propiedad tiene tipo y mapeo en los siete destinos. (§5)
  2. Los campos obligatorios por tipo están declarados. (§6)
  3. Un destino sin propiedades las renderiza de forma legible. (§7)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple

REPO = Path(__file__).resolve().parent.parent.parent
DOC = REPO / "skill" / "notemartin-study-notes" / "references" / "04-authoring" / "properties.md"
NOTEMARK_DOC = REPO / "skill" / "notemartin-study-notes" / "references" / "04-authoring" / "notemark.md"
SKILL_DOC = REPO / "skill" / "notemartin-study-notes" / "SKILL.md"
README_DOC = REPO / "skill" / "notemartin-study-notes" / "references" / "04-authoring" / "README.md"

DESTINATIONS = ["Obsidian", "Notion API", "Notion import", "AppFlowy", "MD", "HTML/PDF", "Flashcards"]
PROPERTIES = [
    "title", "note-type", "status", "tags", "source", "source-type",
    "vendor", "product", "product-version", "source-anchor", "source-url",
    "retrieved", "language", "coverage", "difficulty", "review-next",
    "aliases", "related",
]
TYPES = [
    "concept", "api-reference", "procedure", "configuration",
    "error-troubleshooting", "architecture", "syntax", "data-model",
    "chapter-digest", "comparison", "version-delta", "glossary-term",
    "cheatsheet", "index-moc", "practice",
]
UNIVERSAL = ["title", "note-type", "status"]


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


def check_18_properties_in_section5(doc: str) -> Result:
    section5 = _section(doc, "5", "6")
    found = []
    for prop in PROPERTIES:
        # La subsección de cada propiedad empieza con `### 5.N ``prop``
        pat = rf"^### 5\.\d+ `?{re.escape(prop)}`?"
        if re.search(pat, section5, flags=re.MULTILINE):
            found.append(prop)
    missing = [p for p in PROPERTIES if p not in found]
    return Result(
        "18 propiedades documentadas en §5 (criterio #1)",
        len(found) == 18,
        f"encontradas={len(found)} expected=18 missing={missing}",
    )


def check_each_property_has_7_destinations(doc: str) -> Result:
    """Cada propiedad en §5 debe tener los 7 destinos en su sección."""
    section5 = _section(doc, "5", "6")
    failures = []
    for prop in PROPERTIES:
        # Extraer la subsección de esta propiedad
        start_pat = rf"^### 5\.\d+ `?{re.escape(prop)}`?"
        start_match = re.search(start_pat, section5, flags=re.MULTILINE)
        if not start_match:
            failures.append(f"{prop}: sección no encontrada")
            continue
        # Encontrar el final (próximo ### 5.N+1)
        rest = section5[start_match.end():]
        end_match = re.search(r"^### 5\.\d+ ", rest, flags=re.MULTILINE)
        body = rest[: end_match.start()] if end_match else rest
        missing_dest = [d for d in DESTINATIONS if d not in body]
        if missing_dest:
            failures.append(f"{prop}: faltan destinos {missing_dest}")
    return Result(
        "Cada propiedad mapea a 7 destinos (criterio #1)",
        not failures,
        f"fallos={len(failures)} :: {failures[:3]}",
    )


def check_15_types_in_section6(doc: str) -> Result:
    section6 = _section(doc, "6", "7")
    found = []
    for t in TYPES:
        if re.search(rf"^### 6\.\d+ `?{re.escape(t)}`?", section6, flags=re.MULTILINE):
            found.append(t)
    missing = [t for t in TYPES if t not in found]
    return Result(
        "15 tipos de nota documentados en §6 (criterio #2)",
        len(found) == 15,
        f"encontrados={len(found)} expected=15 missing={missing}",
    )


def check_universals_in_all_types(doc: str) -> Result:
    """Las 3 universales (title, note-type, status) deben mencionarse en cada tipo."""
    section6 = _section(doc, "6", "7")
    failures = []
    for t in TYPES:
        start_pat = rf"^### 6\.\d+ `?{re.escape(t)}`?"
        start_match = re.search(start_pat, section6, flags=re.MULTILINE)
        if not start_match:
            failures.append(f"{t}: sección no encontrada")
            continue
        rest = section6[start_match.end():]
        end_match = re.search(r"^### 6\.\d+ ", rest, flags=re.MULTILINE)
        body = rest[: end_match.start()] if end_match else rest
        for u in UNIVERSAL:
            if u not in body:
                failures.append(f"{t}: falta universal `{u}`")
    return Result(
        "Las 3 universales aparecen en los 15 tipos (criterio #2)",
        not failures,
        f"fallos={len(failures)} :: {failures[:3]}",
    )


def check_section7_fallback_strategy(doc: str) -> Result:
    """§7 debe definir estrategia de fallback legible."""
    section7 = _section(doc, "7", "8")
    has_metadata_section = "## Metadata" in section7 or "`## Metadata`" in section7
    has_table = "| propiedad |" in section7 or "| propiedad | valor |" in section7 or "| propiedad " in section7
    has_html_pdf = "HTML/PDF" in section7
    has_example = "```markdown" in section7 or "Ejemplo generado" in section7
    return Result(
        "§7 define render legible con § Metadata (criterio #3)",
        has_metadata_section and has_table and has_html_pdf and has_example,
        f"metadata={has_metadata_section} tabla={has_table} html_pdf={has_html_pdf} ejemplo={has_example}",
    )


def check_section8_custom_namespaces(doc: str) -> Result:
    section8 = _section(doc, "8", "9")
    has_x = "x-*" in section8 or "`x-*`" in section8
    has_user = "user-*" in section8 or "`user-*`" in section8
    return Result(
        "§8 cubre propiedades personalizadas x-* / user-*",
        has_x and has_user,
        f"x_namespace={has_x} user_namespace={has_user}",
    )


def check_inv06_no_platform_syntax(doc: str) -> Result:
    lines = doc.split("\n")
    failures = []
    in_code = False
    for i, line in enumerate(lines, 1):
        if line.startswith("```"):
            in_code = not in_code
            continue
        if not in_code and re.match(r"^\s*>\s*\[!", line):
            failures.append(f"L{i}")
    return Result(
        "INV-06: cero sintaxis de plataforma",
        not failures,
        f"violaciones={len(failures)}",
    )


def check_inv14_no_literal_colors(doc: str) -> Result:
    lines = doc.split("\n")
    failures = []
    in_code = False
    for i, line in enumerate(lines, 1):
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        for m in re.finditer(r"#([0-9a-fA-F]{3,6})\b", line):
            before = line[: m.start()]
            if before.endswith("]("):
                continue
            failures.append(f"L{i}: {m.group(0)}")
    return Result(
        "INV-14: cero colores literales",
        not failures,
        f"violaciones={len(failures)}",
    )


def check_routes_closed_in_skill() -> Result:
    if not SKILL_DOC.exists():
        return Result("Ruta F47 cerrada en SKILL.md", False, "no existe")
    content = _load(SKILL_DOC)
    if "[pendiente F47]" in content:
        return Result("Ruta F47 cerrada en SKILL.md", False, "quedan [pendiente F47]")
    return Result("Ruta F47 cerrada en SKILL.md", True, "")


def check_readme_no_pending_f47() -> Result:
    if not README_DOC.exists():
        return Result("README 04-authoring actualizado", False, "no existe")
    content = _load(README_DOC)
    if "[pendiente F47]" in content:
        return Result("README 04-authoring actualizado", False, "queda [pendiente F47]")
    return Result("README 04-authoring actualizado", True, "")


def check_notemark_shrunk() -> Result:
    if not NOTEMARK_DOC.exists():
        return Result("notemark.md §8 movido a puntero", False, "no existe")
    content = _load(NOTEMARK_DOC)
    section8 = _section(content, "8", "9")
    has_pointer = "properties.md" in section8
    n_lines = content.count("\n")
    return Result(
        "notemark.md §8 movido a puntero",
        has_pointer and n_lines <= 200,
        f"lineas={n_lines} puntero={has_pointer}",
    )


def check_minimum_size(doc: str) -> Result:
    n = doc.count("\n")
    return Result(
        "Tamaño entre 600 y 900 líneas",
        600 <= n <= 900,
        f"lineas={n}",
    )


CRITERION_MAP = {
    1: ["18 propiedades documentadas en §5 (criterio #1)", "Cada propiedad mapea a 7 destinos (criterio #1)"],
    2: ["15 tipos de nota documentados en §6 (criterio #2)", "Las 3 universales aparecen en los 15 tipos (criterio #2)"],
    3: ["§7 define render legible con § Metadata (criterio #3)"],
}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-all", action="store_true")
    parser.add_argument("--criterion", type=int, choices=[1, 2, 3])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if not DOC.exists():
        print(f"ERROR: {DOC} no existe", file=sys.stderr)
        return 2
    doc = _load(DOC)

    doc_checks = [
        check_minimum_size,
        check_18_properties_in_section5,
        check_each_property_has_7_destinations,
        check_15_types_in_section6,
        check_universals_in_all_types,
        check_section7_fallback_strategy,
        check_section8_custom_namespaces,
        check_inv06_no_platform_syntax,
        check_inv14_no_literal_colors,
    ]
    results = [c(doc) for c in doc_checks]
    results.append(check_routes_closed_in_skill())
    results.append(check_readme_no_pending_f47())
    results.append(check_notemark_shrunk())

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
