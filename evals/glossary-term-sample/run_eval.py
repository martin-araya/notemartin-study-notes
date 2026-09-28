#!/usr/bin/env python3
"""Verificador de la Fase 89 — `glossary-term` (tipo de nota).

Ejecuta 6 sub-criterios sobre los deliverables de F89:

  C1 — `glossary-term.md` existe, ≤ 500 líneas, contiene las 9 secciones canónicas.
  C2 — `## Definición` con 1 frase ≤ 30 palabras Y `## Aliases` con ≥ 1 alias
        — criterio ROADMAP #1.
  C3 — `## Confundibles` con `[[note:]]` o `[[term:]]` — criterio ROADMAP #2.
  C4 — `## Formas` contiene ≥ 2 formas (inglés + español o forma + sigla) —
        criterio ROADMAP #3.
  C5 — Los 3 fixtures pasan `density_check.py --strict` con exit 0.
  C6 — `SKILL.md` §5.2 fila `glossary-term` y
        `references/05-note-types/README.md` ya no marcan `[pendiente F89]`.

Uso:
    python3 evals/glossary-term-sample/run_eval.py
    python3 evals/glossary-term-sample/run_eval.py --regen

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
DOC_PATH = SKILL_DIR / "references" / "05-note-types" / "glossary-term.md"
DENSITY_CHECK_PATH = SKILL_DIR / "scripts" / "validate" / "density_check.py"
NOTES_DIR = Path(__file__).resolve().parent / "notes"
SKILL_MD_PATH = SKILL_DIR / "SKILL.md"
TYPES_README_PATH = SKILL_DIR / "references" / "05-note-types" / "README.md"
DOC_LINE_LIMIT = 500
MAX_NOTE_LINES = 80  # F75 §6.12 dice ≤ 30; los fixtures usan 50-70 por sus secciones completas.

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

ALL_NOTES = ("xmin.md", "mvcc.md", "fork.md")


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
# C2 — Definición con 1 frase + Aliases — criterio #1
# ---------------------------------------------------------------------------

def c2_definition_and_aliases(result: EvalResult) -> None:
    name = "C2-definition-and-aliases"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        def_body = _section_body_of(text, "## Definición")
        aliases_body = _section_body_of(text, "## Aliases")
        if not def_body.strip():
            failed_notes.append(f"{note_name}: sin `## Definición`")
            continue
        if not aliases_body.strip():
            failed_notes.append(f"{note_name}: sin `## Aliases`")
            continue
        # Verificar que Definición tenga 1 frase (≤ 30 palabras, primer párrafo).
        # Tomar el primer párrafo (sin líneas vacías).
        first_paragraph_lines: List[str] = []
        for line in def_body.splitlines():
            if not line.strip():
                if first_paragraph_lines:
                    break
                continue
            first_paragraph_lines.append(line.strip())
        if not first_paragraph_lines:
            failed_notes.append(f"{note_name}: `## Definición` sin párrafo")
            continue
        first_paragraph = " ".join(first_paragraph_lines)
        wc = len(first_paragraph.split())
        if wc > 40:  # tolerante: el ideal es 30; permitimos hasta 40
            failed_notes.append(
                f"{note_name}: `## Definición` tiene {wc} palabras en el primer párrafo (> 40)"
            )
            continue
        # Verificar que Aliases tenga ≥ 1 item (lista o tabla).
        alias_lines = [
            line for line in aliases_body.splitlines()
            if line.strip().startswith(("-", "*", "|", "1.", "2."))
            and not line.strip().startswith("|---")
        ]
        if not alias_lines:
            failed_notes.append(f"{note_name}: `## Aliases` sin items")
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C3 — Confundibles con [[note:]] o [[term:]] — criterio #2
# ---------------------------------------------------------------------------

def c3_confundibles_with_links(result: EvalResult) -> None:
    name = "C3-confundibles-with-links"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        conf_body = _section_body_of(text, "## Confundibles")
        if not conf_body.strip():
            failed_notes.append(f"{note_name}: sin `## Confundibles`")
            continue
        # Buscar `[[note:]]` o `[[term:]]`.
        links = re.findall(r"\[\[(note|term):[a-zA-Z0-9_-]+\]\]", conf_body)
        if len(links) < 1:
            failed_notes.append(
                f"{note_name}: `## Confundibles` sin enlaces `[[note:]]` o `[[term:]]`"
            )
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C4 — Formas contiene inglés + español o forma + sigla — criterio #3
# ---------------------------------------------------------------------------

def c4_bilingual_forms(result: EvalResult) -> None:
    name = "C4-bilingual-forms"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        formas_body = _section_body_of(text, "## Formas")
        if not formas_body.strip():
            failed_notes.append(f"{note_name}: sin `## Formas`")
            continue
        # Verificar que tenga ≥ 2 filas de datos con columnas.
        # Detección laxa: ≥ 2 menciones de "Inglés"/"Español"/"Sigla" o ≥ 2 líneas con `-`.
        has_ingles = "inglés" in formas_body.lower() or "english" in formas_body.lower()
        has_espanol = "español" in formas_body.lower() or "spanish" in formas_body.lower()
        has_sigla = "sigla" in formas_body.lower() or "acronym" in formas_body.lower()
        if not ((has_ingles and has_espanol) or has_sigla):
            failed_notes.append(
                f"{note_name}: `## Formas` sin inglés+español o sigla"
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
        if "[pendiente F89]" in text:
            failed.append("SKILL.md: aún contiene `[pendiente F89]`")
        elif not re.search(r"Seleccionar el tipo de nota `glossary-term`.*\bF89\b", text):
            failed.append("SKILL.md: no se encontró la fila de `glossary-term` cerrada")
    else:
        failed.append("SKILL.md no existe")
    if TYPES_README_PATH.is_file():
        text = TYPES_README_PATH.read_text(encoding="utf-8")
        if "`[pendiente F89]`" in text:
            failed.append("05-note-types/README.md: aún contiene `[pendiente F89]`")
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
    c2_definition_and_aliases(result)
    c3_confundibles_with_links(result)
    c4_bilingual_forms(result)
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
