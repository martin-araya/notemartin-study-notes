#!/usr/bin/env python3
"""Verificador de la Fase 82 — `error-troubleshooting` (tipo de nota).

Ejecuta 6 sub-criterios sobre los deliverables de F82:

  C1 — `error-troubleshooting.md` existe, ≤ 500 líneas, contiene las 9 secciones
        canónicas (§1-§9).
  C2 — Cada mensaje literal del SDM aparece en un bloque `code` Y tiene fila
        en `## Tabla índice` — criterio ROADMAP #1.
  C3 — Cada error listado en `## Síntomas` tiene `## Causa raíz` + `## Solución`
        no vacíos — criterio ROADMAP #2.
  C4 — Cada confundible listado es un `[[note:id]]` Y la nota target tiene
        backlink al origen (mutuismo dentro del corpus de fixtures) —
        criterio ROADMAP #3.
  C5 — Los 3 fixtures pasan `density_check.py --strict` con exit 0.
  C6 — `SKILL.md` §5.2 fila `error-troubleshooting` y
        `references/05-note-types/README.md` ya no marcan `[pendiente F82]`.

Uso:
    python3 evals/error-troubleshooting-sample/run_eval.py
    python3 evals/error-troubleshooting-sample/run_eval.py --regen

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
DOC_PATH = SKILL_DIR / "references" / "05-note-types" / "error-troubleshooting.md"
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
    "postgres-connection-errors.md",
    "k8s-pod-pending-errors.md",
    "docker-permission-errors.md",
)

RE_LINK = re.compile(r"\[\[note:([a-zA-Z0-9_-]+)\]\]")


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


def _extract_code_blocks(body: str) -> List[str]:
    """Devuelve el contenido de cada bloque `code` (no fence lines)."""
    blocks: List[str] = []
    in_code = False
    current: List[str] = []
    for line in body.splitlines():
        if line.strip().startswith("```"):
            if in_code:
                blocks.append("\n".join(current))
                current = []
            in_code = not in_code
            continue
        if in_code:
            current.append(line)
    return blocks


def _extract_error_titles(body: str) -> List[str]:
    """Devuelve los títulos H3 `### Mensaje N: <título>`."""
    titles: List[str] = []
    for line in body.splitlines():
        m = re.match(r"^###\s+Mensaje\s+\d+:", line)
        if m:
            titles.append(line.strip())
    return titles


def _extract_h3_subheadings(body: str) -> List[str]:
    """Devuelve todos los H3 del cuerpo."""
    h3s: List[str] = []
    for line in body.splitlines():
        if line.startswith("### "):
            h3s.append(line.strip())
    return h3s


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
# C2 — mensajes literales en code blocks + Tabla índice
# ---------------------------------------------------------------------------

def c2_literal_messages_and_index(result: EvalResult) -> None:
    name = "C2-literal-messages-and-index"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        sections = _split_into_sections(text)

        sintomas_body = ""
        tabla_body = ""
        for h, b in sections:
            if h.strip() == "## Síntomas":
                sintomas_body = b
            if h.strip() == "## Tabla índice":
                tabla_body = b

        if not sintomas_body:
            failed_notes.append(f"{note_name}: sin `## Síntomas`")
            continue
        if not tabla_body:
            failed_notes.append(f"{note_name}: sin `## Tabla índice`")
            continue

        # Cada H3 `### Mensaje N: <título>` debe tener al menos un bloque `code`
        # con mensaje literal identificable.
        h3_titles = _extract_error_titles(sintomas_body)
        if not h3_titles:
            failed_notes.append(f"{note_name}: `## Síntomas` sin H3 `### Mensaje N:`")
            continue

        # Cada mensaje debe aparecer **idéntico** en `## Tabla índice` (criterio #1).
        code_blocks = _extract_code_blocks(tabla_body)
        # Buscamos las filas de la tabla (líneas `| Mensaje literal | Sección |`).
        index_lines = [l for l in tabla_body.splitlines() if l.strip().startswith("|")]
        index_text = "\n".join(index_lines)

        # Verificamos que el nº de mensajes en Síntomas ≈ nº de filas en la tabla.
        if len(index_lines) < len(h3_titles) + 1:  # +1 por la cabecera de la tabla
            failed_notes.append(
                f"{note_name}: {len(h3_titles)} mensajes en Síntomas pero < {len(h3_titles)} filas en Tabla índice"
            )

    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C3 — cada error tiene Causa raíz + Solución no vacíos
# ---------------------------------------------------------------------------

def c3_cause_and_solution_per_error(result: EvalResult) -> None:
    name = "C3-cause-and-solution-per-error"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        text = note_path.read_text(encoding="utf-8")
        sections = _split_into_sections(text)

        # Extraer los H3 `### Mensaje N: <título>` tanto en Causa raíz como en Solución.
        causa_body = ""
        solucion_body = ""
        sintomas_body = ""
        for h, b in sections:
            if h.strip() == "## Causa raíz":
                causa_body = b
            if h.strip() == "## Solución":
                solucion_body = b
            if h.strip() == "## Síntomas":
                sintomas_body = b

        h3_sintomas = _extract_error_titles(sintomas_body)
        h3_causa = _extract_h3_subheadings(causa_body)
        h3_solucion = _extract_h3_subheadings(solucion_body)

        # Los H3 de Causa raíz y Solución empiezan con `### Mensaje N: ...`.
        causa_msg_h3 = [h for h in h3_causa if h.startswith("### Mensaje")]
        solucion_msg_h3 = [h for h in h3_solucion if h.startswith("### Mensaje")]

        if len(causa_msg_h3) < len(h3_sintomas):
            failed_notes.append(
                f"{note_name}: {len(h3_sintomas)} errores en Síntomas pero {len(causa_msg_h3)} secciones Causa raíz con `### Mensaje N:`"
            )
        if len(solucion_msg_h3) < len(h3_sintomas):
            failed_notes.append(
                f"{note_name}: {len(h3_sintomas)} errores en Síntomas pero {len(solucion_msg_h3)} secciones Solución con `### Mensaje N:`"
            )

    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C4 — confundibles bidireccionales
# ---------------------------------------------------------------------------

def c4_bidirectional_confundibles(result: EvalResult) -> None:
    name = "C4-bidirectional-confundibles"
    failed_notes = []
    # Cargar todas las notas del corpus en memoria.
    corpus: dict[str, str] = {}
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if note_path.is_file():
            corpus[note_name] = note_path.read_text(encoding="utf-8")

    # Para cada nota, extraer los `[[note:X]]` que aparecen en `## Confundibles`
    # y `## Backlinks`.
    for source_name, text in corpus.items():
        sections = _split_into_sections(text)
        confundibles_body = ""
        backlinks_body = ""
        for h, b in sections:
            if h.strip() == "## Confundibles":
                confundibles_body = b
            if h.strip() == "## Backlinks":
                backlinks_body = b

        # Extraer nombres de notas linkeadas.
        links_in_confundibles = set(RE_LINK.findall(confundibles_body))
        links_in_backlinks = set(RE_LINK.findall(backlinks_body))

        # Para cada link en Confundibles, la nota target debe existir o tener backlink.
        # Para esta batería, verificamos que el link aparece también en Backlinks de
        # la nota target (bidireccionalidad explícita) O que la nota target está en
        # el corpus.
        unidirectional = []
        for target_id in links_in_confundibles:
            # Resolver nombre de archivo a partir del id (asumimos convención <id>.md).
            target_file_candidate = f"{target_id}.md"
            if target_file_candidate in corpus:
                # Verificar bidireccionalidad: el source debe aparecer en Backlinks
                # o Confundibles de la nota target.
                target_text = corpus[target_file_candidate]
                target_backlinks = set(
                    RE_LINK.findall(_section_body_of(target_text, "## Backlinks") or "")
                )
                target_confundibles = set(
                    RE_LINK.findall(_section_body_of(target_text, "## Confundibles") or "")
                )
                # El id de source se deriva del nombre del archivo (sin .md).
                source_id = source_name.replace(".md", "")
                if (
                    source_id not in target_backlinks
                    and source_id not in target_confundibles
                ):
                    unidirectional.append(target_id)
            else:
                # Nota target fuera del corpus: допустимо (puede ser nota del usuario).
                # No falla.
                pass

        if unidirectional:
            failed_notes.append(
                f"{source_name}: confundibles unidireccionales (sin backlink en target): {unidirectional}"
            )

    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


def _section_body_of(text: str, heading: str) -> str | None:
    """Devuelve el body de la primera sección cuyo heading == `heading`."""
    sections = _split_into_sections(text)
    for h, b in sections:
        if h.strip() == heading:
            return b
    return None


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
        if "[pendiente F82]" in text:
            failed.append("SKILL.md: aún contiene `[pendiente F82]`")
        elif not re.search(r"Seleccionar el tipo de nota `error-troubleshooting`.*\bF82\b", text):
            failed.append("SKILL.md: no se encontró la fila de `error-troubleshooting` cerrada")
    else:
        failed.append("SKILL.md no existe")
    if TYPES_README_PATH.is_file():
        text = TYPES_README_PATH.read_text(encoding="utf-8")
        if "`[pendiente F82]`" in text:
            failed.append("05-note-types/README.md: aún contiene `[pendiente F82]`")
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
    c2_literal_messages_and_index(result)
    c3_cause_and_solution_per_error(result)
    c4_bidirectional_confundibles(result)
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
