#!/usr/bin/env python3
"""Verificador de la Fase 81 — `configuration` (tipo de nota).

Ejecuta 6 sub-criterios sobre los deliverables de F81:

  C1 — `configuration.md` existe, ≤ 500 líneas, contiene las 9 secciones canónicas.
  C2 — Toda fila de toda tabla canónica 8-col tiene `Default` y `Ámbito` no
        vacíos — criterio ROADMAP #1.
  C3 — `## Interacciones` existe y tiene ≥ 1 fila — criterio ROADMAP #2.
  C4 — Ninguna recomendación sin respaldo: regex sobre
        `recomendamos|sugerido|usar N` exige `{src:}` o `:::external` adyacente —
        criterio ROADMAP #3.
  C5 — Los 3 fixtures pasan `density_check.py --strict` con exit 0.
  C6 — `SKILL.md` §5.2 fila `configuration` y `references/05-note-types/README.md`
        ya no marcan `[pendiente F81]`.

Uso:
    python3 evals/configuration-sample/run_eval.py          # ejecuta los 6 sub-criterios
    python3 evals/configuration-sample/run_eval.py --regen  # regenera fixtures + ejecuta

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
DOC_PATH = SKILL_DIR / "references" / "05-note-types" / "configuration.md"
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

EXPECTED_HEADER = (
    "Parámetro",
    "Ámbito",
    "Tipo",
    "Default",
    "Rango",
    "Hot reload",
    "Reinicio",
    "Versión",
    "Impacto",
)

ALL_NOTES = ("postgresql-conf.md", "nginx-conf.md", "k8s-pod-resources.md")

# Regex que captura recomendaciones: "recomendamos", "sugerimos", "usar N",
# "incrementar X a Y", "setear X a Y", "lo correcto es N".
RE_RECOMMENDATION = re.compile(
    r"\b(recomendamos|sugerimos|sugerido|recomendado|usar\s+\d|incrementar|setear|"
    r"lo correcto es|se recomienda|valor recomendado)\b",
    re.IGNORECASE,
)
RE_SRC = re.compile(r"\{src:blk_[0-9a-f]{12}\}")
RE_EXTERNAL = re.compile(r":::external")


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


def _parse_table_rows(body: str) -> List[List[str]]:
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


def _find_canonical_tables(text: str) -> List[Tuple[str, List[List[str]]]]:
    """Encuentra todas las tablas 8-col en el texto y devuelve (header_text, rows)."""
    tables: List[Tuple[str, List[List[str]]]] = []
    in_table = False
    header_cells: List[str] = []
    current_rows: List[List[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and not re.match(r"^\|[\s\-:|]+\|\s*$", stripped):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if not in_table:
                in_table = True
                header_cells = cells
                current_rows = []
            else:
                current_rows.append(cells)
        elif re.match(r"^\|[\s\-:|]+\|\s*$", stripped):
            continue
        else:
            if in_table:
                if tuple(header_cells) == EXPECTED_HEADER:
                    tables.append(("8col", current_rows))
                in_table = False
                header_cells = []
                current_rows = []
    if in_table and tuple(header_cells) == EXPECTED_HEADER:
        tables.append(("8col", current_rows))
    return tables


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
# C2 — toda fila de tabla 8-col tiene Default y Ámbito no vacíos
# ---------------------------------------------------------------------------

def c2_table_completeness(result: EvalResult) -> None:
    name = "C2-table-completeness"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        tables = _find_canonical_tables(text)
        if not tables:
            failed_notes.append(f"{note_name}: ninguna tabla 8-col canónica encontrada")
            continue
        issues = []
        for table_kind, rows in tables:
            for i, row in enumerate(rows):
                if len(row) < len(EXPECTED_HEADER):
                    issues.append(f"fila {i+1}: {len(row)} celdas, esperaba {len(EXPECTED_HEADER)}")
                    continue
                # Default (idx 3) y Ámbito (idx 1) son obligatorios.
                if not row[1].strip():
                    issues.append(f"fila {i+1} (Ámbito vacío): {row[0][:30]}")
                if not row[3].strip():
                    issues.append(f"fila {i+1} (Default vacío): {row[0][:30]}")
        if issues:
            failed_notes.append(f"{note_name}: {len(issues)} problemas (p.ej. {issues[:2]})")
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C3 — Interacciones presente con ≥ 1 fila
# ---------------------------------------------------------------------------

def c3_interactions_present(result: EvalResult) -> None:
    name = "C3-interactions-present"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        text = note_path.read_text(encoding="utf-8")
        sections = _split_into_sections(text)
        body = ""
        for h, b in sections:
            if h.strip() == "## Interacciones":
                body = b
                break
        if not body.strip():
            failed_notes.append(f"{note_name}: sin `## Interacciones`")
            continue
        # Contar filas en tabla O bullets.
        table_rows = _parse_table_rows(body)
        bullet_count = len(re.findall(r"^\s*[-*]\s+", body, re.MULTILINE))
        total = len(table_rows) + bullet_count
        if total < 1:
            failed_notes.append(f"{note_name}: `## Interacciones` sin filas")
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C4 — Ninguna recomendación sin respaldo (criterio #3)
# ---------------------------------------------------------------------------

def c4_no_unsupported_recommendations(result: EvalResult) -> None:
    name = "C4-no-unsupported-recommendations"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        text = note_path.read_text(encoding="utf-8")
        lines = text.splitlines()

        # Encontrar todas las líneas con una recomendación, EXCLUYENDO filas
        # de tabla (las descripciones de celdas no son "recomendaciones" en el
        # sentido del criterio #3).
        rec_lines: List[int] = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("|"):
                continue
            if RE_RECOMMENDATION.search(line):
                rec_lines.append(i)

        # Para cada recomendación, verificar respaldo (±5 líneas: cubre párrafos
        # cortos y tablas adyacentes).
        unsupported = []
        for lineno in rec_lines:
            window = "\n".join(lines[max(0, lineno - 5): min(len(lines), lineno + 6)])
            if not (RE_SRC.search(window) or RE_EXTERNAL.search(window)):
                unsupported.append(lines[lineno][:80])

        if unsupported:
            failed_notes.append(
                f"{note_name}: {len(unsupported)} recomendaciones sin respaldo (p.ej. {unsupported[:2]})"
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
        if "[pendiente F81]" in text:
            failed.append("SKILL.md: aún contiene `[pendiente F81]`")
        elif not re.search(r"Seleccionar el tipo de nota `configuration`.*\bF81\b", text):
            failed.append("SKILL.md: no se encontró la fila de `configuration` cerrada")
    else:
        failed.append("SKILL.md no existe")
    if TYPES_README_PATH.is_file():
        text = TYPES_README_PATH.read_text(encoding="utf-8")
        if "`[pendiente F81]`" in text:
            failed.append("05-note-types/README.md: aún contiene `[pendiente F81]`")
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
    c2_table_completeness(result)
    c3_interactions_present(result)
    c4_no_unsupported_recommendations(result)
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
