#!/usr/bin/env python3
"""Verificador de la Fase 88 — `version-delta` (tipo de nota).

Ejecuta 6 sub-criterios sobre los deliverables de F88:

  C1 — `version-delta.md` existe, ≤ 500 líneas, contiene las 9 secciones canónicas.
  C2 — Cada fila de `## Cambios` tiene Versión exacta con formato semver —
        criterio ROADMAP #1.
  C3 — `## Cambios de default` existe como sección separada con ≥ 1 cambio —
        criterio ROADMAP #2.
  C4 — `## Notas afectadas` lista ≥ 2 notas con `[[note:id]]` y documenta la
        convención de backlink — criterio ROADMAP #3.
  C5 — Los 3 fixtures pasan `density_check.py --strict` con exit 0.
  C6 — `SKILL.md` §5.2 fila `version-delta` y
        `references/05-note-types/README.md` ya no marcan `[pendiente F88]`.

Uso:
    python3 evals/version-delta-sample/run_eval.py
    python3 evals/version-delta-sample/run_eval.py --regen

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
DOC_PATH = SKILL_DIR / "references" / "05-note-types" / "version-delta.md"
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
    "postgresql-16-changelog-delta.md",
    "kubernetes-1-30-changelog-delta.md",
    "docker-25-changelog-delta.md",
)

SEMVER_RE = re.compile(r"^\d+\.\d+(\.\d+)?(-[a-zA-Z0-9.]+)?$")


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
# C2 — Cada fila tiene Versión exacta con formato semver — criterio #1
# ---------------------------------------------------------------------------

def c2_exact_version_column(result: EvalResult) -> None:
    name = "C2-exact-version-column"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        cambios_body = _section_body_of(text, "## Cambios")
        if not cambios_body:
            failed_notes.append(f"{note_name}: sin `## Cambios`")
            continue
        rows = _parse_table_rows(cambios_body)
        if len(rows) < 2:  # header + ≥ 1 row
            failed_notes.append(f"{note_name}: tabla en `## Cambios` con < 2 filas")
            continue
        # Header debe tener columna "Versión exacta" (idx 0).
        header = [c.strip() for c in rows[0]]
        if "versión exacta" not in header[0].lower():
            failed_notes.append(
                f"{note_name}: columna 1 no es 'Versión exacta' (es {header[0]!r})"
            )
            continue
        # Cada fila de datos tiene versión en semver.
        bad_versions = []
        for i, row in enumerate(rows[1:], start=1):
            if len(row) < 1:
                continue
            version = row[0].strip()
            if not SEMVER_RE.match(version):
                bad_versions.append(f"fila {i+1}: {version!r}")
        if bad_versions:
            failed_notes.append(
                f"{note_name}: versiones no semver: {bad_versions[:3]}"
            )
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C3 — Cambios de default en sección separada — criterio #2
# ---------------------------------------------------------------------------

def c3_default_changes_section(result: EvalResult) -> None:
    name = "C3-default-changes-section"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        cambios_default_body = _section_body_of(text, "## Cambios de default")
        if not cambios_default_body.strip():
            failed_notes.append(f"{note_name}: sin `## Cambios de default`")
            continue
        # Verificar que tenga ≥ 1 fila de datos con Default anterior/nuevo.
        rows = _parse_table_rows(cambios_default_body)
        if len(rows) < 2:
            failed_notes.append(
                f"{note_name}: `## Cambios de default` sin tabla de cambios"
            )
            continue
        # Verificar que el header tenga columnas Default anterior/nuevo.
        header = " ".join(rows[0]).lower()
        if "anterior" not in header or "nuevo" not in header:
            failed_notes.append(
                f"{note_name}: `## Cambios de default` sin columnas Default anterior/nuevo"
            )
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C4 — Notas afectadas con [[note:id]] — criterio #3
# ---------------------------------------------------------------------------

def c4_affected_notes_with_links(result: EvalResult) -> None:
    name = "C4-affected-notes-with-links"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        notas_body = _section_body_of(text, "## Notas afectadas")
        if not notas_body.strip():
            failed_notes.append(f"{note_name}: sin `## Notas afectadas`")
            continue
        # Contar `[[note:...]]` en la sección.
        links = re.findall(r"\[\[note:([a-zA-Z0-9_-]+)\]\]", notas_body)
        if len(links) < 2:
            failed_notes.append(
                f"{note_name}: `## Notas afectadas` con {len(links)} enlaces (≥ 2 requeridos)"
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
        if "[pendiente F88]" in text:
            failed.append("SKILL.md: aún contiene `[pendiente F88]`")
        elif not re.search(r"Seleccionar el tipo de nota `version-delta`.*\bF88\b", text):
            failed.append("SKILL.md: no se encontró la fila de `version-delta` cerrada")
    else:
        failed.append("SKILL.md no existe")
    if TYPES_README_PATH.is_file():
        text = TYPES_README_PATH.read_text(encoding="utf-8")
        if "`[pendiente F88]`" in text:
            failed.append("05-note-types/README.md: aún contiene `[pendiente F88]`")
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
    c2_exact_version_column(result)
    c3_default_changes_section(result)
    c4_affected_notes_with_links(result)
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
