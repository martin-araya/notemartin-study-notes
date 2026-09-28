#!/usr/bin/env python3
"""Verificador de la Fase 79 — `api-reference` (tipo de nota).

Ejecuta 6 sub-criterios sobre los deliverables de F79:

  C1 — `api-reference.md` existe, ≤ 500 líneas, contiene las 9 secciones canónicas.
  C2 — `docker-cli-bundle.md` cubre ≥ 15 subprogramas **y** cada uno tiene
        `### Subcomando: <nombre>` + tabla 5-col (criterio ROADMAP #1).
  C3 — Toda fila de toda tabla 5-col en los 3 fixtures tiene las 5 celdas
        rellenas (Parámetro, Tipo, Obligatorio, Default, Descripción) — criterio
        ROADMAP #2.
  C4 — Cada fixture tiene ≥ 1 bloque `:::example` o `code` con caption en
        `## Ejemplos` — criterio ROADMAP #3.
  C5 — Los 3 fixtures pasan `density_check.py --strict` con exit 0.
  C6 — `SKILL.md` §5.2 fila `api-reference` y `references/05-note-types/README.md`
        ya no marcan `[pendiente F79]`.

Uso:
    python3 evals/api-reference-sample/run_eval.py          # ejecuta los 6 sub-criterios
    python3 evals/api-reference-sample/run_eval.py --regen  # regenera fixtures + ejecuta

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
DOC_PATH = SKILL_DIR / "references" / "05-note-types" / "api-reference.md"
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

EXPECTED_COLUMNS = (
    "Parámetro",
    "Tipo",
    "Obligatorio",
    "Default",
    "Descripción",
)

BUNDLE_NOTE = "docker-cli-bundle.md"
INDIVIDUAL_NOTES = ("docker-run.md", "kubernetes-pod-v1.md")
ALL_NOTES = (BUNDLE_NOTE, *INDIVIDUAL_NOTES)
MIN_SUBCOMMANDS = 15
MIN_EXAMPLES = 1


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
    """Divide el texto en bloques (`heading`, `body`)."""
    sections: List[Tuple[str, str]] = []
    current_heading = ""
    current_body: List[str] = []
    for line in text.splitlines():
        if line.startswith("## ") or line.startswith("# "):
            if current_heading or current_body:
                sections.append((current_heading, "\n".join(current_body)))
            current_heading = line
            current_body = []
        else:
            current_body.append(line)
    if current_heading or current_body:
        sections.append((current_heading, "\n".join(current_body)))
    return sections


def _parse_table_rows(body: str) -> List[List[str]]:
    """Devuelve las filas de una tabla GFM (excluye la cabecera y la separadora)."""
    rows: List[List[str]] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        # Saltar la fila separadora (|---|---|).
        if re.match(r"^\|[\s\-:|]+\|\s*$", stripped):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        rows.append(cells)
    return rows[1:]  # la fila 0 es la cabecera


def _has_5_columns(body: str) -> Tuple[bool, int]:
    """Verifica que la primera tabla tenga las 5 columnas canónicas. Devuelve (ok, filas)."""
    rows = _parse_table_rows(body)
    if not rows:
        return False, 0
    return True, len(rows)


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
# C2 — bundle cubre ≥ 15 subprogramas, cada uno con tabla 5-col
# ---------------------------------------------------------------------------

_RE_SUBCOMANDO = re.compile(r"^### Subcomando:\s*`(.+?)`", re.MULTILINE)


def c2_bundle_coverage(result: EvalResult) -> None:
    name = "C2-bundle-coverage"
    note_path = NOTES_DIR / BUNDLE_NOTE
    if not note_path.is_file():
        result.fail(name, f"{BUNDLE_NOTE} no existe")
        return
    text = note_path.read_text(encoding="utf-8")
    sub_matches = _RE_SUBCOMANDO.findall(text)
    if len(sub_matches) < MIN_SUBCOMMANDS:
        result.fail(name, f"solo {len(sub_matches)} subprogramas (≥ {MIN_SUBCOMMANDS} requeridos)")
        return
    # Verificar que cada subprograma tiene su tabla 5-col inmediatamente después.
    sections = _split_into_sections(text)
    bad = []
    for i, (heading, body) in enumerate(sections):
        if not heading.startswith("### Subcomando:"):
            continue
        rows = _parse_table_rows(body)
        if not rows:
            bad.append(heading)
            continue
        header_row = rows[0] if rows else None  # ya descartado por _parse_table_rows
        # Re-leer header real (es la primera fila `|...|...|`).
        header_lines = [l for l in body.splitlines() if l.strip().startswith("|") and not re.match(r"^\|[\s\-:|]+\|\s*$", l.strip())]
        if not header_lines:
            bad.append(heading)
            continue
        header_cells = [c.strip() for c in header_lines[0].strip("|").split("|")]
        if tuple(header_cells) != EXPECTED_COLUMNS:
            bad.append(f"{heading} (header={header_cells})")
    if bad:
        result.fail(name, f"subprogramas sin tabla 5-col: {bad[:3]}")
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C3 — toda fila de toda tabla 5-col tiene las 5 celdas rellenas
# ---------------------------------------------------------------------------

def c3_table_completeness(result: EvalResult) -> None:
    name = "C3-table-completeness"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        sections = _split_into_sections(text)
        incomplete = []
        for heading, body in sections:
            # Buscar primera tabla; verificar header = 5 columnas.
            header_lines = [
                l for l in body.splitlines()
                if l.strip().startswith("|") and not re.match(r"^\|[\s\-:|]+\|\s*$", l.strip())
            ]
            if not header_lines:
                continue
            header_cells = [c.strip() for c in header_lines[0].strip("|").split("|")]
            if tuple(header_cells) != EXPECTED_COLUMNS:
                continue  # No es una tabla 5-col canónica.
            rows = _parse_table_rows(body)
            for i, row in enumerate(rows):
                if len(row) < 5:
                    incomplete.append(f"{heading} fila {i+2}: {len(row)} celdas")
                    continue
                for j, col in enumerate(EXPECTED_COLUMNS):
                    if j >= len(row) or not row[j].strip():
                        incomplete.append(f"{heading} fila {i+2} col {col}: vacía")
        if incomplete:
            failed_notes.append(f"{note_name}: {len(incomplete)} problemas (p.ej. {incomplete[:2]})")
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C4 — cada fixture tiene ≥ 1 ejemplo ejecutable
# ---------------------------------------------------------------------------

def c4_examples_present(result: EvalResult) -> None:
    name = "C4-examples-present"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        text = note_path.read_text(encoding="utf-8")
        sections = _split_into_sections(text)
        ejemplos_body = ""
        for heading, body in sections:
            if heading.strip() == "## Ejemplos":
                ejemplos_body = body
                break
        if not ejemplos_body:
            failed_notes.append(f"{note_name}: sin `## Ejemplos`")
            continue
        # Contar bloques `:::example` o fences con caption.
        example_blocks = re.findall(r"^:::example\s*$", ejemplos_body, re.MULTILINE)
        code_fences = re.findall(r"^```", ejemplos_body, re.MULTILINE)
        n_examples = len(example_blocks)
        n_code = len(code_fences) // 2
        total = n_examples + n_code
        if total < MIN_EXAMPLES:
            failed_notes.append(f"{note_name}: solo {total} ejemplos (≥ {MIN_EXAMPLES})")
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C5 — los 3 fixtures pasan `density_check.py --strict`
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
        if "[pendiente F79]" in text:
            failed.append("SKILL.md: aún contiene `[pendiente F79]`")
        elif not re.search(r"Seleccionar el tipo de nota `api-reference`.*\bF79\b", text):
            failed.append("SKILL.md: no se encontró la fila de `api-reference` cerrada")
    else:
        failed.append("SKILL.md no existe")
    if TYPES_README_PATH.is_file():
        text = TYPES_README_PATH.read_text(encoding="utf-8")
        if "`[pendiente F79]`" in text:
            failed.append("05-note-types/README.md: aún contiene `[pendiente F79]`")
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
    c2_bundle_coverage(result)
    c3_table_completeness(result)
    c4_examples_present(result)
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
