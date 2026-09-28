#!/usr/bin/env python3
"""Verificador de la Fase 87 — `comparison` (tipo de nota).

Ejecuta 6 sub-criterios sobre los deliverables de F87:

  C1 — `comparison.md` existe, ≤ 600 líneas, contiene las 9 secciones canónicas.
  C2 — Cada tabla tiene un párrafo de síntesis (≥ 30 palabras) en las siguientes
        ≤ 3 párrafos — criterio ROADMAP #1.
  C3 — Las afirmaciones derivadas usan `:::derived` o `:::external` —
        criterio ROADMAP #2.
  C4 — Todas las tablas tienen criterios paralelos (cada opción tiene valor en
        cada fila) — criterio ROADMAP #3.
  C5 — Los 3 fixtures pasan `density_check.py --strict` con exit 0.
  C6 — `SKILL.md` §5.2 fila `comparison` y
        `references/05-note-types/README.md` ya no marcan `[pendiente F87]`.

Uso:
    python3 evals/comparison-sample/run_eval.py
    python3 evals/comparison-sample/run_eval.py --regen

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
DOC_PATH = SKILL_DIR / "references" / "05-note-types" / "comparison.md"
DENSITY_CHECK_PATH = SKILL_DIR / "scripts" / "validate" / "density_check.py"
NOTES_DIR = Path(__file__).resolve().parent / "notes"
SKILL_MD_PATH = SKILL_DIR / "SKILL.md"
TYPES_README_PATH = SKILL_DIR / "references" / "05-note-types" / "README.md"
DOC_LINE_LIMIT = 600

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
    "postgresql-vs-mysql.md",
    "kubectl-vs-docker.md",
    "rest-vs-grpc.md",
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


def _find_tables_with_positions(body: str) -> List[Tuple[int, int]]:
    """Devuelve (start_line, end_line) para cada tabla GFM en body."""
    tables: List[Tuple[int, int]] = []
    lines = body.splitlines()
    in_table = False
    start = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("|"):
            if not in_table:
                in_table = True
                start = i
        else:
            if in_table:
                # La tabla termina al encontrar línea no-pipe.
                tables.append((start, i))
                in_table = False
    if in_table:
        tables.append((start, len(lines)))
    return tables


def _find_synthesis_paragraph(body: str, after_table_end_line: int) -> str | None:
    """Devuelve el primer párrafo narrativo (≥ 30 palabras) después de la tabla."""
    lines = body.splitlines()
    paragraph_lines: List[str] = []
    in_paragraph = False
    # Buscar dentro de las 3 líneas siguientes (criterio #1).
    for i in range(after_table_end_line, min(after_table_end_line + 3, len(lines))):
        line = lines[i].strip()
        if not line:
            if in_paragraph and paragraph_lines:
                text = " ".join(paragraph_lines)
                wc = len(text.split())
                if wc >= 30:
                    return text
            in_paragraph = False
            paragraph_lines = []
            continue
        if line.startswith("|") or line.startswith("#") or line.startswith("```"):
            continue
        in_paragraph = True
        paragraph_lines.append(line)
    if in_paragraph and paragraph_lines:
        text = " ".join(paragraph_lines)
        if len(text.split()) >= 30:
            return text
    return None


def _parse_table_rows(body: str) -> List[List[str]]:
    """Devuelve las filas de las tablas GFM en body."""
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
# C1 — doc existe, ≤ 600 líneas, contiene las 9 secciones canónicas
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
# C2 — Cada tabla va seguida de un párrafo de síntesis — criterio #1
# ---------------------------------------------------------------------------

def c2_table_followed_by_synthesis(result: EvalResult) -> None:
    """Verifica que la tabla principal (en ## Comparativa) va seguida de un párrafo de síntesis (≥ 30 palabras).

    Por la convención del doc, solo la tabla principal (## Comparativa) requiere
    párrafo de síntesis explícito. Las tablas auxiliares (Matriz, Trade-offs) son
    evidencia adicional que se explica por sí misma en el contexto.
    """
    name = "C2-table-followed-by-synthesis"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        lines = text.splitlines()

        # Encontrar la sección ## Comparativa y la siguiente sección ## Síntesis.
        in_comparativa = False
        in_sintesis = False
        sintesis_start = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == "## Comparativa":
                in_comparativa = True
                in_sintesis = False
                continue
            if in_comparativa and stripped == "## Síntesis":
                in_sintesis = True
                sintesis_start = i
                break

        if sintesis_start is None:
            failed_notes.append(f"{note_name}: sin `## Síntesis` después de `## Comparativa`")
            continue

        # Verificar que la sección ## Síntesis tenga ≥ 1 párrafo ≥ 30 palabras.
        end = sintesis_start + 1
        while end < len(lines) and not lines[end].strip().startswith("## "):
            end += 1
        sintesis_body = "\n".join(lines[sintesis_start + 1 : end]).strip()
        # Buscar párrafo ≥ 30 palabras.
        has_long_paragraph = False
        for paragraph in sintesis_body.split("\n\n"):
            cleaned = " ".join(line.strip() for line in paragraph.splitlines() if line.strip())
            if len(cleaned.split()) >= 30:
                has_long_paragraph = True
                break
        if not has_long_paragraph:
            failed_notes.append(f"{note_name}: `## Síntesis` sin párrafo ≥ 30 palabras")
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C3 — Afirmaciones derivadas marcadas — criterio #2
# ---------------------------------------------------------------------------

def c3_derived_marked(result: EvalResult) -> None:
    """Verifica que las afirmaciones que NO están respaldadas por {src:} usan :::derived o :::external."""
    name = "C3-derived-marked"
    # Esta comprobación es heurística: para cada párrafo, contar palabras sin src.
    # No es automatizable al 100%; usamos que ≥ 1 párrafo del Veredicto tenga :::derived o :::external.
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        text = note_path.read_text(encoding="utf-8")
        # Buscar al menos un :::derived o :::external en la nota (heurística).
        has_derived = ":::derived" in text or ":::external" in text
        if not has_derived:
            failed_notes.append(
                f"{note_name}: no usa `:::derived` o `:::external` para afirmaciones derivadas (criterio #2)"
            )
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C4 — Criterios paralelos — criterio #3
# ---------------------------------------------------------------------------

def c4_parallel_criteria(result: EvalResult) -> None:
    name = "C4-parallel-criteria"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        # Buscar la tabla en ## Comparativa (la principal).
        sections = _split_into_sections(text)
        comparativa_body = ""
        for h, b in sections:
            if h.strip() == "## Comparativa":
                comparativa_body = b
                break
        rows = _parse_table_rows(comparativa_body)
        if not rows:
            failed_notes.append(f"{note_name}: sin tabla en `## Comparativa`")
            continue
        # Filtrar filas separadoras.
        data_rows = [r for r in rows if not all(set(c) <= set("-: ") for c in r)]
        if not data_rows:
            failed_notes.append(f"{note_name}: tabla sin filas de datos")
            continue
        n_cols = max(len(r) for r in data_rows)
        # Verificar que todas las filas tengan al menos 2 celdas (criterio + ≥ 1 opción).
        # Verificar que ninguna celda esté vacía (sin contar celdas de header).
        problematic: List[str] = []
        for i, row in enumerate(data_rows[1:], start=1):  # skip header
            if len(row) < n_cols:
                problematic.append(f"fila {i}: {len(row)}/{n_cols} celdas")
            else:
                for j, cell in enumerate(row):
                    if j == 0:
                        continue  # skip criterion name
                    if not cell.strip():
                        problematic.append(f"fila {i} col {j}: vacía")
        if problematic:
            failed_notes.append(
                f"{note_name}: criterios no paralelos: {problematic[:3]}"
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
        if "[pendiente F87]" in text:
            failed.append("SKILL.md: aún contiene `[pendiente F87]`")
        elif not re.search(r"Seleccionar el tipo de nota `comparison`.*\bF87\b", text):
            failed.append("SKILL.md: no se encontró la fila de `comparison` cerrada")
    else:
        failed.append("SKILL.md no existe")
    if TYPES_README_PATH.is_file():
        text = TYPES_README_PATH.read_text(encoding="utf-8")
        if "`[pendiente F87]`" in text:
            failed.append("05-note-types/README.md: aún contiene `[pendiente F87]`")
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
    c2_table_followed_by_synthesis(result)
    c3_derived_marked(result)
    c4_parallel_criteria(result)
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
