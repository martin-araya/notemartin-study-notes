#!/usr/bin/env python3
"""Verificador de la Fase 91 — `index-moc` (tipo [núcleo]).

Ejecuta 6 sub-criterios sobre los deliverables de F91:

  C1 — `index-moc.md` existe, ≤ 600 líneas, contiene las 9 secciones canónicas.
  C2 — Cada `[[note:id]]` tiene descripción de ≥ 1 palabra después del link
        — criterio ROADMAP #1.
  C3 — Cada `[[note:id]]` en el MOC existe en `notes/` o `phantom-notes/`
        (filesystem check) — criterio ROADMAP #2.
  C4 — Existe `## Cobertura de la fuente` con keywords "cubre" + "no cubre"
        — criterio ROADMAP #3.
  C5 — Los 3 fixtures pasan `density_check.py --strict` con exit 0.
  C6 — `SKILL.md` §5.2 fila `index-moc` y
        `references/05-note-types/README.md` ya no marcan `[pendiente F91]`.

Uso:
    python3 evals/index-moc-sample/run_eval.py
    python3 evals/index-moc-sample/run_eval.py --regen

Salida esperada: PASS 6/6.

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skill" / "notemartin-study-notes"
DOC_PATH = SKILL_DIR / "references" / "05-note-types" / "index-moc.md"
DENSITY_CHECK_PATH = SKILL_DIR / "scripts" / "validate" / "density_check.py"
NOTES_DIR = Path(__file__).resolve().parent / "notes"
PHANTOM_DIR = Path(__file__).resolve().parent / "phantom-notes"
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
    "postgresql-index.md",
    "docker-index.md",
    "rust-index.md",
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


def _all_note_files() -> Set[str]:
    """Devuelve el set de nombres de archivo de notas disponibles (sin extensión).

    Combina `notes/` y `phantom-notes/` para que las phantom notes cuenten
    como notas existentes.
    """
    files: Set[str] = set()
    for note_dir in (NOTES_DIR, PHANTOM_DIR):
        if note_dir.is_dir():
            for p in note_dir.glob("*.md"):
                files.add(p.stem)
    return files


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
# C2 — Cada [[note:id]] tiene descripción de ≥ 1 palabra — criterio #1
# ---------------------------------------------------------------------------

def c2_links_have_descriptions(result: EvalResult) -> None:
    name = "C2-links-have-descriptions"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        # Buscar todos los `[[note:id]]` en la nota.
        # Excluir los `[[note:id]]` que están dentro de `[[note:...]]` (los `[[term:]]` están excluidos).
        link_pattern = re.compile(r"\[\[note:([a-zA-Z0-9_-]+)\]\]")
        links = link_pattern.findall(text)
        if not links:
            failed_notes.append(f"{note_name}: sin `[[note:]]`")
            continue
        # Verificar que cada `[[note:id]]` tenga texto posterior (descripción).
        # Buscar la línea que contiene el link y verificar la cantidad de palabras después.
        lines = text.splitlines()
        links_without_desc = []
        for line in lines:
            for match in link_pattern.finditer(line):
                # El texto después del link completo `[[note:id]]`.
                idx = match.end()
                after = line[idx:].strip()
                # Strip leading punctuation/whitespace.
                after = re.sub(r"^[\s\-—:]+", "", after)
                if not after:
                    links_without_desc.append(f"line: {line[:80]!r}")
                    continue
                # Contar palabras.
                wc = len(after.split())
                if wc < 1:
                    links_without_desc.append(f"line: {line[:80]!r}")
        # Dedupe.
        links_without_desc = list(set(links_without_desc))
        if links_without_desc:
            failed_notes.append(
                f"{note_name}: {len(links_without_desc)} enlaces sin descripción: {links_without_desc[:2]}"
            )
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C3 — Cada [[note:id]] existe en notes/ — criterio #2
# ---------------------------------------------------------------------------

def c3_links_point_to_existing_notes(result: EvalResult) -> None:
    name = "C3-links-point-to-existing-notes"
    available = _all_note_files()
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        link_pattern = re.compile(r"\[\[note:([a-zA-Z0-9_-]+)\]\]")
        target_ids = set(link_pattern.findall(text))
        missing = sorted(target_ids - available)
        if missing:
            failed_notes.append(
                f"{note_name}: {len(missing)} enlaces a notas inexistentes: {missing[:3]}"
            )
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C4 — Cobertura de la fuente con keywords — criterio #3
# ---------------------------------------------------------------------------

def c4_coverage_section_present(result: EvalResult) -> None:
    name = "C4-coverage-section-present"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        body = _section_body_of(text, "## Cobertura de la fuente")
        if not body.strip():
            failed_notes.append(f"{note_name}: sin `## Cobertura de la fuente`")
            continue
        # Verificar keywords "cubre" y "no cubre" (case-insensitive).
        body_lower = body.lower()
        has_cubre = "cubre" in body_lower
        has_no_cubre = "no cubre" in body_lower or "no se cubre" in body_lower
        if not (has_cubre and has_no_cubre):
            missing = []
            if not has_cubre:
                missing.append("'cubre'")
            if not has_no_cubre:
                missing.append("'no cubre'")
            failed_notes.append(
                f"{note_name}: keywords faltantes en `## Cobertura de la fuente`: {missing}"
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
        if "[pendiente F91]" in text:
            failed.append("SKILL.md: aún contiene `[pendiente F91]`")
        elif not re.search(r"Seleccionar el tipo de nota `index-moc`.*\bF91\b", text):
            failed.append("SKILL.md: no se encontró la fila de `index-moc` cerrada")
    else:
        failed.append("SKILL.md no existe")
    if TYPES_README_PATH.is_file():
        text = TYPES_README_PATH.read_text(encoding="utf-8")
        if "`[pendiente F91]`" in text:
            failed.append("05-note-types/README.md: aún contiene `[pendiente F91]`")
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
    c2_links_have_descriptions(result)
    c3_links_point_to_existing_notes(result)
    c4_coverage_section_present(result)
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
