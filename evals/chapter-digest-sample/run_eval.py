#!/usr/bin/env python3
"""Verificador de la Fase 86 — `chapter-digest` (tipo [núcleo]).

Ejecuta 6 sub-criterios sobre los deliverables de F86:

  C1 — `chapter-digest.md` existe, ≤ 600 líneas, contiene las 9 secciones canónicas.
  C2 — `## Continuidad` tiene sub-secciones `### Hacia atrás` Y `### Hacia adelante`
        con enlaces — criterio ROADMAP #1.
  C3 — Cada concepto en `## Conceptos nuevos` tiene `[[note:id]]` o `[[term:nombre]]`
        — criterio ROADMAP #2.
  C4 — `## Resumen ejecutivo` + `## Puntos clave` cubren los argumentos principales
        del SDM (cobertura de keywords) — criterio ROADMAP #3.
  C5 — Los 3 fixtures pasan `density_check.py --strict` con exit 0.
  C6 — `SKILL.md` §5.2 fila `chapter-digest` y
        `references/05-note-types/README.md` ya no marcan `[pendiente F86]`.

Uso:
    python3 evals/chapter-digest-sample/run_eval.py
    python3 evals/chapter-digest-sample/run_eval.py --regen

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
DOC_PATH = SKILL_DIR / "references" / "05-note-types" / "chapter-digest.md"
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
    "postgresql-chapter-13-digest.md",
    "kubernetes-pod-spec-digest.md",
    "rfc-7231-chapter-4-digest.md",
)

# Keywords mínimos por fixture para verificar criterio #3 (cobertura).
REQUIRED_KEYWORDS = {
    "postgresql-chapter-13-digest.md": ["MVCC", "xmin", "xmax", "snapshot", "isolation", "VACUUM"],
    "kubernetes-pod-spec-digest.md": ["containers", "resources", "QoS", "tolerations", "priorityClassName"],
    "rfc-7231-chapter-4-digest.md": ["GET", "POST", "safe", "idempotent", "CONNECT", "OPTIONS"],
}

RE_LINK = re.compile(r"\[\[(note|term):([a-zA-Z0-9_-]+)\]\]")


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
# C2 — Continuidad en ambos sentidos — criterio #1
# ---------------------------------------------------------------------------

def c2_continuity_both_directions(result: EvalResult) -> None:
    name = "C2-continuity-both-directions"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        cont_body = _section_body_of(text, "## Continuidad")
        if not cont_body.strip():
            failed_notes.append(f"{note_name}: sin `## Continuidad`")
            continue
        # Verificar sub-secciones `### Hacia atrás` y `### Hacia adelante`.
        has_back = bool(re.search(r"^###\s+Hacia atr", cont_body, re.MULTILINE))
        has_forward = bool(re.search(r"^###\s+Hacia ade", cont_body, re.MULTILINE))
        if not (has_back and has_forward):
            missing = []
            if not has_back:
                missing.append("Hacia atrás")
            if not has_forward:
                missing.append("Hacia adelante")
            failed_notes.append(
                f"{note_name}: `## Continuidad` sin sub-secciones: {missing}"
            )
            continue
        # Cada sub-sección debe tener ≥ 1 enlace.
        for direction in ("atr", "ade"):
            sub = re.search(
                rf"^###\s+Hacia {direction}.*?\n(.*?)(?=^### |\Z)",
                cont_body,
                re.MULTILINE | re.DOTALL,
            )
            if sub and not RE_LINK.search(sub.group(1)):
                failed_notes.append(
                    f"{note_name}: `### Hacia {'atrás' if direction == 'atr' else 'adelante'}` sin `[[note:]]` o `[[term:]]`"
                )
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C3 — Conceptos nuevos con [[note:id]] o [[term:nombre]] — criterio #2
# ---------------------------------------------------------------------------

def c3_concepts_with_notes(result: EvalResult) -> None:
    name = "C3-concepts-with-notes"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        concepts_body = _section_body_of(text, "## Conceptos nuevos")
        if not concepts_body.strip():
            failed_notes.append(f"{note_name}: sin `## Conceptos nuevos`")
            continue
        # Buscar filas de tabla; cada celda de la columna 2 debe tener un [[note:]] o [[term:]].
        in_table = False
        header_seen = False
        rows_without_link: List[str] = []
        for line in concepts_body.splitlines():
            stripped = line.strip()
            if not stripped.startswith("|"):
                continue
            if re.match(r"^\|[\s\-:|]+\|\s*$", stripped):
                in_table = True
                continue
            if in_table:
                cells = [c.strip() for c in stripped.strip("|").split("|")]
                if not header_seen:
                    header_seen = True
                    continue
                if len(cells) >= 2 and not RE_LINK.search(cells[1]):
                    rows_without_link.append(cells[0])
        if rows_without_link:
            failed_notes.append(
                f"{note_name}: conceptos sin `[[note:]]` o `[[term:]]`: {rows_without_link}"
            )
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C4 — Cobertura de keywords — criterio #3
# ---------------------------------------------------------------------------

def c4_keyword_coverage(result: EvalResult) -> None:
    name = "C4-keyword-coverage"
    failed_notes = []
    for note_name, keywords in REQUIRED_KEYWORDS.items():
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        resumen = _section_body_of(text, "## Resumen ejecutivo")
        puntos = _section_body_of(text, "## Puntos clave")
        combined = resumen + "\n" + puntos
        missing = [kw for kw in keywords if kw.lower() not in combined.lower()]
        coverage = 1.0 - (len(missing) / len(keywords))
        if coverage < 0.6:  # al menos 60% de keywords presentes
            failed_notes.append(
                f"{note_name}: cobertura {coverage:.0%} ({len(keywords) - len(missing)}/{len(keywords)} keywords), faltan: {missing}"
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
        if "[pendiente F86]" in text:
            failed.append("SKILL.md: aún contiene `[pendiente F86]`")
        elif not re.search(r"Seleccionar el tipo de nota `chapter-digest`.*\bF86\b", text):
            failed.append("SKILL.md: no se encontró la fila de `chapter-digest` cerrada")
    else:
        failed.append("SKILL.md no existe")
    if TYPES_README_PATH.is_file():
        text = TYPES_README_PATH.read_text(encoding="utf-8")
        if "`[pendiente F86]`" in text:
            failed.append("05-note-types/README.md: aún contiene `[pendiente F86]`")
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
    c2_continuity_both_directions(result)
    c3_concepts_with_notes(result)
    c4_keyword_coverage(result)
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
