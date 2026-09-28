#!/usr/bin/env python3
"""Verificador de la Fase 93 — `Selector de tipo` [ref] [núcleo].

Ejecuta 6 sub-criterios sobre los deliverables de F93:

  C1 — `selector.md` existe, ≤ 500 líneas, contiene las 9 secciones canónicas.
  C2 — El fixture "Oracle" lista ≥ 3 tipos distintos — criterio ROADMAP #1.
  C3 — La tabla de cobertura en el doc tiene 0 celdas vacías — criterio #2.
  C4 — El doc tiene `## Reglas de desempate` con ≥ 3 reglas explícitas —
        criterio ROADMAP #3.
  C5 — Los 2 fixtures pasan `density_check.py --strict` con exit 0.
  C6 — `SKILL.md` §5.2 fila `selector` y
        `references/05-note-types/README.md` ya no marcan `[pendiente F93]`.

Uso:
    python3 evals/selector-sample/run_eval.py
    python3 evals/selector-sample/run_eval.py --regen

Salida esperada: PASS 6/6.

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skill" / "notemartin-study-notes"
DOC_PATH = SKILL_DIR / "references" / "05-note-types" / "selector.md"
DENSITY_CHECK_PATH = SKILL_DIR / "scripts" / "validate" / "density_check.py"
NOTES_DIR = Path(__file__).resolve().parent / "notes"
SKILL_MD_PATH = SKILL_DIR / "SKILL.md"
TYPES_README_PATH = SKILL_DIR / "references" / "05-note-types" / "README.md"
DOC_LINE_LIMIT = 500

EXPECTED_SECTIONS = (
    "## §1 · Propósito y alcance",
    "## §2 · Estructura de la nota",
    "## §3 · Componentes mínimos",
    "## §4 · Reglas de contenido",
    "## §5 · Activación por perfil",
    "## §6 · Checklist de cierre",
    "## §7 · Nota mínima viable",
    "## §8 · Wirings y referencias cruzadas",
    "## §9 · Verificación al cierre de la fase",
)

ALL_NOTES = (
    "oracle-concepts-ch1-selector.md",
    "postgresql-ch13-selector.md",
)


class EvalResult:
    def __init__(self) -> None:
        self.passed: List[str] = []
        self.failed: List[Tuple[str, str]] = []

    def ok(self, name: str) -> None:
        self.passed.append(name)

    def fail(self, name: str, detail: str) -> None:
        self.failed.append((name, detail))

    @property
    def total(self) -> int:
        return len(self.passed) + len(self.failed)

    @property
    def status(self) -> str:
        if not self.failed:
            return f"PASS {len(self.passed)}/{self.total}"
        return f"FAIL {len(self.failed)}/{self.total} (passed {len(self.passed)}/{self.total})"


def _split_into_sections(text: str) -> List[Tuple[str, str]]:
    sections: List[Tuple[str, str]] = []
    current_heading = ""
    current_body: List[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current_heading or current_body:
                sections.append((current_heading, "\n".join(current_body)))
            current_heading = line
            current_body = []
        else:
            current_body.append(line)
    if current_heading or current_body:
        sections.append((current_heading, "\n".join(current_body)))
    return sections


def _section_body_of(text: str, heading: str) -> str:
    sections = _split_into_sections(text)
    for h, b in sections:
        if h.strip() == heading:
            return b
    return ""


# ---------------------------------------------------------------------------
# C1 — doc existe, ≤ 500 líneas, contiene las 9 secciones canónicas
# ---------------------------------------------------------------------------

def c1_doc_structure(result: EvalResult) -> None:
    name = "C1-doc-structure"
    if not DOC_PATH.is_file():
        result.fail(name, f"{DOC_PATH} no existe")
        return
    line_count = sum(1 for _ in DOC_PATH.open("r", encoding="utf-8"))
    if line_count > DOC_LINE_LIMIT:
        result.fail(name, f"{line_count} líneas > {DOC_LINE_LIMIT}")
        return
    text = DOC_PATH.read_text(encoding="utf-8")
    missing = [s for s in EXPECTED_SECTIONS if s not in text]
    if missing:
        result.fail(name, f"faltan secciones: {missing}")
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C2 — Oracle produce ≥ 3 tipos distintos — criterio #1
# ---------------------------------------------------------------------------

def c2_oracle_distinct_types(result: EvalResult) -> None:
    name = "C2-oracle-distinct-types"
    note_path = NOTES_DIR / "oracle-concepts-ch1-selector.md"
    if not note_path.is_file():
        result.fail(name, "fixture no existe")
        return
    text = note_path.read_text(encoding="utf-8")
    # Buscar todos los `[[note:type-name]]` distintos en la sección "Tipos asignados"
    tipos_body = _section_body_of(text, "## Tipos asignados")
    if not tipos_body.strip():
        result.fail(name, "sin `## Tipos asignados`")
        return
    types_found = set(re.findall(r"\[\[note:([a-zA-Z0-9-]+)\]\]", tipos_body))
    # Excluir `selector` (backlink) del conteo.
    types_found.discard("selector")
    if len(types_found) < 3:
        result.fail(
            name, f"solo {len(types_found)} tipos distintos en Oracle fixture (≥ 3 requeridos): {sorted(types_found)}"
        )
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C3 — 0 celdas vacías en la cobertura — criterio #2
# ---------------------------------------------------------------------------

def c3_no_empty_cells(result: EvalResult) -> None:
    name = "C3-no-empty-cells"
    if not DOC_PATH.is_file():
        result.fail(name, "doc no existe")
        return
    text = DOC_PATH.read_text(encoding="utf-8")
    cobertura_body = _section_body_of(text, "## Cobertura de la matriz")
    if not cobertura_body.strip():
        result.fail(name, "sin `## Cobertura de la matriz`")
        return
    # Buscar filas de tabla y verificar que cada celda tenga contenido.
    rows = []
    for line in cobertura_body.splitlines():
        if line.strip().startswith("|"):
            if re.match(r"^\|[\s\-:|]+\|\s*$", line.strip()):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append(cells)
    if not rows:
        result.fail(name, "sin filas en `## Cobertura de la matriz`")
        return
    # Verificar 0 celdas vacías (excepto header).
    empty_cells = []
    for i, row in enumerate(rows[1:], start=1):
        for j, cell in enumerate(row):
            if not cell:
                empty_cells.append(f"fila {i} col {j}")
    if empty_cells:
        result.fail(name, f"celdas vacías: {empty_cells[:3]}")
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C4 — Reglas de desempate con ≥ 3 reglas — criterio #3
# ---------------------------------------------------------------------------

def c4_tiebreaker_rules(result: EvalResult) -> None:
    name = "C4-tiebreaker-rules"
    if not DOC_PATH.is_file():
        result.fail(name, "doc no existe")
        return
    text = DOC_PATH.read_text(encoding="utf-8")
    desempate_body = _section_body_of(text, "## Reglas de desempate")
    if not desempate_body.strip():
        result.fail(name, "sin `## Reglas de desempate`")
        return
    # Contar items numerados `1.`, `2.`, etc.
    items = re.findall(r"^\s*\d+\.\s+", desempate_body, re.MULTILINE)
    if len(items) < 3:
        result.fail(name, f"solo {len(items)} reglas de desempate (≥ 3 requeridas)")
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C5 — los 2 fixtures pasan density_check.py --strict
# ---------------------------------------------------------------------------

def c5_density_check(result: EvalResult) -> None:
    name = "C5-density-check"
    if not DENSITY_CHECK_PATH.is_file():
        result.fail(name, f"{DENSITY_CHECK_PATH} no existe")
        return
    failed = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed.append(f"{note_name} no existe")
            continue
        proc = subprocess.run(
            [sys.executable, str(DENSITY_CHECK_PATH), "--note", str(note_path), "--strict"],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            failed.append(f"{note_name}: exit {proc.returncode}\n{proc.stdout.strip()[:200]}")
    if failed:
        result.fail(name, "; ".join(failed))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C6 — wirings cerrados
# ---------------------------------------------------------------------------

def c6_wirings_closed(result: EvalResult) -> None:
    name = "C6-wirings-closed"
    failed = []
    if SKILL_MD_PATH.is_file():
        text = SKILL_MD_PATH.read_text(encoding="utf-8")
        if "[pendiente F93]" in text:
            failed.append("SKILL.md: aún contiene `[pendiente F93]`")
        elif not re.search(r"Seleccionar el tipo de nota `selector`.*\bF93\b", text):
            failed.append("SKILL.md: no se encontró la fila de `selector` cerrada")
    else:
        failed.append("SKILL.md no existe")
    if TYPES_README_PATH.is_file():
        text = TYPES_README_PATH.read_text(encoding="utf-8")
        if "`[pendiente F93]`" in text:
            failed.append("05-note-types/README.md: aún contiene `[pendiente F93]`")
    else:
        failed.append("05-note-types/README.md no existe")
    if failed:
        result.fail(name, "; ".join(failed))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regen", action="store_true",
                        help="Regenera fixtures antes de ejecutar")
    args = parser.parse_args()

    if args.regen:
        build_script = Path(__file__).resolve().parent / "build_fixtures.py"
        subprocess.run([sys.executable, str(build_script)], check=True)

    result = EvalResult()
    c1_doc_structure(result)
    c2_oracle_distinct_types(result)
    c3_no_empty_cells(result)
    c4_tiebreaker_rules(result)
    c5_density_check(result)
    c6_wirings_closed(result)

    print(result.status)
    for name in result.passed:
        print(f"  [PASS] {name}")
    for name, detail in result.failed:
        print(f"  [FAIL] {name}: {detail}")

    return 0 if not result.failed else 1


if __name__ == "__main__":
    sys.exit(main())
