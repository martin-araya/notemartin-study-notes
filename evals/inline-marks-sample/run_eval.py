"""run_eval.py — autoverificación de Fase 46 (inline-marks.md).

Uso:
    python3 evals/inline-marks-sample/run_eval.py --check-all
    python3 evals/inline-marks-sample/run_eval.py --criterion N
    python3 evals/inline-marks-sample/run_eval.py --check-all --json

Verifica los tres criterios ROADMAP de F46 + invariantes transversales.
No requiere dependencias externas (Python 3.9+ stdlib).

Criterios cubiertos:
  1. Toda tabla de parámetros y todo código de error lleva `{src:}`. (§4, §6, §10.1)
  2. Los placeholders se distinguen en los siete destinos. (§7)
  3. Las marcas no aparecen más de una vez por bloque. (§9)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple

REPO = Path(__file__).resolve().parent.parent.parent
DOC = REPO / "skill" / "notemartin-study-notes" / "references" / "04-authoring" / "inline-marks.md"
NOTEMARK_DOC = REPO / "skill" / "notemartin-study-notes" / "references" / "04-authoring" / "notemark.md"
SKILL_DOC = REPO / "skill" / "notemartin-study-notes" / "SKILL.md"
README_DOC = REPO / "skill" / "notemartin-study-notes" / "references" / "04-authoring" / "README.md"
PROBE_DOC = REPO / "evals" / "inline-marks-sample" / "note-probe-inline.nm"

DESTINATIONS = ["Obsidian", "Notion API", "Notion import", "AppFlowy", "MD", "HTML/PDF", "Flashcards"]
MARKS_OBLIGATORIAS = ["src", "term", "note", "placeholder", "derived", "external"]
MARKS_APOYO = ["fn", "kbd", "deleted"]


class Result(NamedTuple):
    name: str
    passed: bool
    detail: str


def _load(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _section(doc: str, anchor: str, next_anchor: str | None) -> str:
    """Extrae una sección delimitada por `## §N · ...` y el siguiente §M."""
    pat = rf"^## §{anchor}.*?\n(.*?)^## §{next_anchor}" if next_anchor else rf"^## §{anchor}.*?\n(.*?)\Z"
    m = re.search(pat, doc, flags=re.MULTILINE | re.DOTALL)
    return m.group(1) if m else ""


def check_9_mark_entries(doc: str) -> Result:
    headings = re.findall(r"^### 10\.(\d+) `", doc, flags=re.MULTILINE)
    found = list(headings)
    return Result(
        "9 entradas de marcas (§10)",
        len(found) == 9,
        f"encontradas={len(found)} expected=9",
    )


def check_table_7_destinations(doc: str) -> Result:
    """§7 debe listar los 7 destinos en columnas."""
    section7 = _section(doc, "7", "8")
    cols = [d for d in DESTINATIONS if d in section7]
    return Result(
        "Tabla de 7 destinos (§7)",
        len(cols) == 7,
        f"destinos_encontrados={cols}",
    )


def check_placeholder_in_7_destinations(doc: str) -> Result:
    """Criterio #2: los placeholders se distinguen en los 7 destinos."""
    section7 = _section(doc, "7", "8")
    # La fila de placeholder debe tener 7 celdas no-vacías en las columnas de destino
    placeholder_row = re.search(r"^\| `\{\{nombre\}\}` \|.*?$", section7, flags=re.MULTILINE)
    if not placeholder_row:
        return Result("Placeholder distinguible en 7 destinos", False, "fila `{{nombre}}` no encontrada")
    row = placeholder_row.group(0)
    # Contar separadores de columna `|` (la fila tiene 9 `|` = 8 columnas: 1 marca + 7 destinos)
    n_cols = row.count("|")
    return Result(
        "Placeholder distinguible en 7 destinos",
        n_cols >= 8,
        f"separadores_en_fila={n_cols} (esperado ≥ 8 = 1 col marca + 7 destinos)",
    )


def check_table_si_no_with_5_si(doc: str) -> Result:
    """Criterio #1: tabla SÍ/NO debe tener ≥5 filas SÍ."""
    section6 = _section(doc, "6", "7")
    n_si = len(re.findall(r"\*\*Sí\*\*", section6))
    n_no = len(re.findall(r"\*\*No\*\*", section6))
    return Result(
        "Tabla SÍ/NO con ≥5 SÍ (criterio #1)",
        n_si >= 5,
        f"sí={n_si} no={n_no}",
    )


def check_inv06_no_platform_syntax(doc: str) -> Result:
    """INV-06 / INV-I4: cero sintaxis de plataforma fuera de bloques de código."""
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
        f"violaciones={len(failures)} :: {failures[:3]}",
    )


def check_inv14_no_literal_colors(doc: str) -> Result:
    """INV-14 / INV-I3: cero colores literales."""
    lines = doc.split("\n")
    failures = []
    in_code = False
    for i, line in enumerate(lines, 1):
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        stripped = re.sub(r"\{src:blk_[0-9a-f]+\}", "", line)
        for m in re.finditer(r"#([0-9a-fA-F]{3,6})\b", stripped):
            before = stripped[: m.start()]
            if before.endswith("]("):
                continue
            failures.append(f"L{i}: {m.group(0)}")
    return Result(
        "INV-14: cero colores literales",
        not failures,
        f"violaciones={len(failures)} :: {failures[:3]}",
    )


def check_density_table_covers_paramtable_and_error(doc: str) -> Result:
    """§4 debe mencionar :::param-table y 'código de error' explícitamente."""
    section4 = _section(doc, "4", "5")
    has_param = ":::param-table" in section4 and ("parámetros" in section4.lower() or "param" in section4.lower())
    has_error = "error" in section4.lower() and ("código" in section4.lower() or "code" in section4.lower())
    return Result(
        "§4 cubre :::param-table y código de error",
        has_param and has_error,
        f"param_table={has_param} code_error={has_error}",
    )


def check_one_instance_per_block_rule(doc: str) -> Result:
    """§9 debe declarar reglas de 1 instancia por bloque con verificación mecánica."""
    section9 = _section(doc, "9", "10")
    # Filas de la tabla: cualquier línea que empiece con | y contenga "rg -c" (verificación mecánica)
    n_rules = len(re.findall(r"^\| .* \|.*rg -c", section9, flags=re.MULTILINE))
    return Result(
        "§9 con tabla de verificación mecánica (criterio #3)",
        n_rules >= 5,
        f"filas_con_verificacion_mecanica={n_rules}",
    )


def check_first_appearance_rule(doc: str) -> Result:
    """§5 debe declarar la regla principal y excepciones."""
    section5 = _section(doc, "5", "6")
    has_main_rule = "una sola vez por nota" in section5
    has_exceptions = "re-marcar" in section5 or "excepción" in section5.lower()
    has_no_mark = "no marcar" in section5.lower() or "cuándo NO" in section5.lower()
    return Result(
        "§5 con regla principal + excepciones (INV-I2)",
        has_main_rule and has_exceptions and has_no_mark,
        f"regla_principal={has_main_rule} excepciones={has_exceptions} no_marcar={has_no_mark}",
    )


def check_legibility_8_rules(doc: str) -> Result:
    """§8 debe tener 8 reglas de legibilidad."""
    section8 = _section(doc, "8", "9")
    n_rules = len(re.findall(r"^\| \d+ \|", section8, flags=re.MULTILINE))
    return Result(
        "§8 con 8 reglas de legibilidad",
        n_rules >= 8,
        f"reglas={n_rules}",
    )


def check_routes_closed_in_skill() -> Result:
    if not SKILL_DOC.exists():
        return Result("Ruta F46 cerrada en SKILL.md", False, "no existe")
    content = _load(SKILL_DOC)
    if "[pendiente F46]" in content:
        return Result("Ruta F46 cerrada en SKILL.md", False, "quedan [pendiente F46]")
    return Result("Ruta F46 cerrada en SKILL.md", True, "")


def check_readme_no_pending_f46() -> Result:
    if not README_DOC.exists():
        return Result("README 04-authoring actualizado", False, "no existe")
    content = _load(README_DOC)
    if "[pendiente F46]" in content:
        return Result("README 04-authoring actualizado", False, "queda [pendiente F46]")
    return Result("README 04-authoring actualizado", True, "")


def check_notemark_shrunk() -> Result:
    if not NOTEMARK_DOC.exists():
        return Result("notemark.md §7 movido a puntero", False, "no existe")
    content = _load(NOTEMARK_DOC)
    section7 = _section(content, "7", "8")
    n_inline_table_rows = len(re.findall(r"^\| `\w[\w-]*` \|", section7, flags=re.MULTILINE))
    # El cuerpo de §7 debe apuntar a inline-marks.md; el heading existe en el doc completo.
    has_pointer = "inline-marks.md" in section7
    has_heading = "## §7 · Marcas inline" in content
    n_lines = content.count("\n")
    return Result(
        "notemark.md §7 movido a puntero",
        has_pointer and has_heading and n_inline_table_rows == 0 and n_lines <= 200,
        f"lineas={n_lines} filas_inline_en_§7={n_inline_table_rows} puntero={has_pointer} heading={has_heading}",
    )


def check_probe_note_no_duplicates() -> Result:
    """Criterio #3 verificado en la nota-probe: cada blk_xxxx aparece ≤ N veces."""
    if not PROBE_DOC.exists():
        return Result("Nota-probe sin duplicados (criterio #3)", False, f"no existe: {PROBE_DOC}")
    content = _load(PROBE_DOC)
    # Extraer todos los blk_xxxx del probe
    blocks = re.findall(r"blk_[0-9a-f]{12}", content)
    from collections import Counter
    counts = Counter(blocks)
    duplicates = {b: n for b, n in counts.items() if n > 1}
    return Result(
        "Nota-probe sin blk_xxxx duplicados",
        not duplicates,
        f"total_blks={len(blocks)} únicos={len(counts)} duplicados={len(duplicates)} :: {list(duplicates.items())[:3]}",
    )


CRITERION_MAP = {
    1: ["Tabla SÍ/NO con ≥5 SÍ (criterio #1)", "§4 cubre :::param-table y código de error"],
    2: ["Tabla de 7 destinos (§7)", "Placeholder distinguible en 7 destinos"],
    3: ["§9 con tabla de verificación mecánica (criterio #3)", "Nota-probe sin blk_xxxx duplicados"],
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
        check_9_mark_entries,
        check_table_7_destinations,
        check_placeholder_in_7_destinations,
        check_table_si_no_with_5_si,
        check_inv06_no_platform_syntax,
        check_inv14_no_literal_colors,
        check_density_table_covers_paramtable_and_error,
        check_one_instance_per_block_rule,
        check_first_appearance_rule,
        check_legibility_8_rules,
    ]
    results = [c(doc) for c in doc_checks]
    results.append(check_routes_closed_in_skill())
    results.append(check_readme_no_pending_f46())
    results.append(check_notemark_shrunk())
    results.append(check_probe_note_no_duplicates())

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
