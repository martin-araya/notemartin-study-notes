#!/usr/bin/env python3
"""Verificador de la Fase 90 — `cheatsheet` (tipo de nota).

Ejecuta 6 sub-criterios sobre los deliverables de F90:

  C1 — `cheatsheet.md` existe, ≤ 500 líneas, contiene las 5 secciones canónicas.
  C2 — Cada fila de las tablas principales tiene `[[note:id]]` o `[[term:X]]`
        apuntando a una nota — criterio ROADMAP #1 y #2.
  C3 — Las tablas tienen ≥ 10 filas — F75 §6.13.
  C4 — Sin párrafos narrativos > 50 palabras (criterio #3).
  C5 — Los 3 fixtures pasan `density_check.py --strict` con exit 0.
  C6 — `SKILL.md` §5.2 fila `cheatsheet` y
        `references/05-note-types/README.md` ya no marcan `[pendiente F90]`.

Uso:
    python3 evals/cheatsheet-sample/run_eval.py
    python3 evals/cheatsheet-sample/run_eval.py --regen

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
DOC_PATH = SKILL_DIR / "references" / "05-note-types" / "cheatsheet.md"
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
    "postgres-cheatsheet.md",
    "docker-cheatsheet.md",
    "git-cheatsheet.md",
)

MIN_COMANDOS_ROWS = 10
MIN_ATAJOS_ROWS = 5
MAX_PROSE_WORDS = 50


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


def _parse_table_rows(body: str) -> List[List[str]]:
    """Devuelve las filas de las tablas GFM."""
    rows: List[List[str]] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:|]+\|\s*$", stripped):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        rows.append(cells)
    return rows


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
# C2 — Cada fila tiene [[note:id]] o [[term:X]] — criterios #1 y #2
# ---------------------------------------------------------------------------

def c2_each_row_has_link(result: EvalResult) -> None:
    """Verifica que las filas de `## Comandos` tengan enlaces (criterios #1 y #2).

    `## Atajos` se exenta: los atajos triviales (`\dt`, `-it`) son self-explanatory
    y no requieren enlace a nota.
    """
    name = "C2-each-row-has-link"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        # Solo `## Comandos` requiere enlaces por fila.
        comandos_body = _section_body_of(text, "## Comandos")
        if not comandos_body:
            failed_notes.append(f"{note_name}: sin `## Comandos`")
            continue
        rows = _parse_table_rows(comandos_body)
        if not rows:
            failed_notes.append(f"{note_name}: `## Comandos` sin filas")
            continue
        # Skip header row.
        rows_without_link = []
        for i, row in enumerate(rows[1:], start=1):
            row_text = " ".join(row)
            if not re.search(r"\[\[(note|term):", row_text):
                rows_without_link.append(f"row {i}: {row[0][:30] if row else '?'}")
        if rows_without_link:
            failed_notes.append(
                f"{note_name}: {len(rows_without_link)} filas en `## Comandos` sin `[[note:]]`/`[[term:]]`: {rows_without_link[:3]}"
            )
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C3 — Las tablas tienen ≥ 10 filas — F75 §6.13
# ---------------------------------------------------------------------------

def c3_min_rows_in_table(result: EvalResult) -> None:
    name = "C3-min-rows-in-table"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_name in ALL_NOTES:
            continue
        text = note_path.read_text(encoding="utf-8")
        comandos_body = _section_body_of(text, "## Comandos")
        if not comandos_body:
            failed_notes.append(f"{note_name}: sin `## Comandos`")
            continue
        rows = _parse_table_rows(comandos_body)
        # Restar la fila de header.
        data_rows = len(rows) - 1 if rows else 0
        if data_rows < MIN_COMANDOS_ROWS:
            failed_notes.append(
                f"{note_name}: `## Comandos` tiene {data_rows} filas (≥ {MIN_COMANDOS_ROWS} requeridas)"
            )
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C4 — Sin párrafos narrativos > 50 palabras — criterio #3
# ---------------------------------------------------------------------------

def c4_no_long_prose(result: EvalResult) -> None:
    name = "C4-no-long-prose"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        text = note_path.read_text(encoding="utf-8")
        # Buscar párrafos narrativos (no tablas, no callouts, no listas) > 50 palabras.
        sections = _split_into_sections(text)
        long_paragraphs = []
        for h, b in sections:
            for paragraph in b.split("\n\n"):
                # Saltar párrafos que sean tablas (contienen `|` en cada línea).
                lines = paragraph.splitlines()
                if not lines:
                    continue
                if all("|" in l for l in lines if l.strip()):
                    continue
                # Saltar párrafos de callouts.
                if any(l.strip().startswith(":::") for l in lines):
                    continue
                # Saltar listas (líneas que empiezan con `-`, `*`, `1.`, `2.`).
                if all(l.strip().startswith(("-", "*", "1", "2", "3", "4", "5")) or not l.strip() for l in lines):
                    continue
                # Saltar párrafos que son solo títulos/labels.
                if all(l.strip().startswith("#") for l in lines if l.strip()):
                    continue
                # Contar palabras.
                paragraph_text = " ".join(l.strip() for l in lines if l.strip())
                wc = len(paragraph_text.split())
                if wc > MAX_PROSE_WORDS:
                    long_paragraphs.append(f"{h}: {wc} palabras: {paragraph_text[:80]!r}")
        if long_paragraphs:
            failed_notes.append(
                f"{note_name}: {len(long_paragraphs)} párrafos > {MAX_PROSE_WORDS} palabras: {long_paragraphs[:2]}"
            )
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C5 — los 3 fixtures pasan density_check.py --strict
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
        if "[pendiente F90]" in text:
            failed.append("SKILL.md: aún contiene `[pendiente F90]`")
        elif not re.search(r"Seleccionar el tipo de nota `cheatsheet`.*\bF90\b", text):
            failed.append("SKILL.md: no se encontró la fila de `cheatsheet` cerrada")
    else:
        failed.append("SKILL.md no existe")
    if TYPES_README_PATH.is_file():
        text = TYPES_README_PATH.read_text(encoding="utf-8")
        if "`[pendiente F90]`" in text:
            failed.append("05-note-types/README.md: aún contiene `[pendiente F90]`")
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
    c2_each_row_has_link(result)
    c3_min_rows_in_table(result)
    c4_no_long_prose(result)
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
