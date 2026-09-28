#!/usr/bin/env python3
"""Verificador de la Fase 83 — `architecture` (tipo de nota).

Ejecuta 6 sub-criterios sobre los deliverables de F83:

  C1 — `architecture.md` existe, ≤ 500 líneas, contiene las 9 secciones canónicas.
  C2 — Tabla de componentes con responsabilidades en una frase ≤ 30 palabras —
        criterio ROADMAP #1.
  C3 — `## Flujo paso a paso` con ≥ 3 pasos numerados Y diagrama Mermaid
        `sequenceDiagram` — criterio ROADMAP #2.
  C4 — Cada `:::warning`/`:::danger` en `## Puntos de fallo` lleva `{src:blk_xxxx}`
        — criterio ROADMAP #3.
  C5 — Los 3 fixtures pasan `density_check.py --strict` con exit 0.
  C6 — `SKILL.md` §5.2 fila `architecture` y
        `references/05-note-types/README.md` ya no marcan `[pendiente F83]`.

Uso:
    python3 evals/architecture-sample/run_eval.py
    python3 evals/architecture-sample/run_eval.py --regen

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
DOC_PATH = SKILL_DIR / "references" / "05-note-types" / "architecture.md"
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
    "postgresql-architecture.md",
    "kubernetes-architecture.md",
    "docker-architecture.md",
)

RE_SRC = re.compile(r"\{src:blk_[0-9a-f]{12}\}")
RE_SEQUENCE_DIAGRAM = re.compile(r"sequenceDiagram", re.IGNORECASE)
RE_FLOWCHART = re.compile(r"flowchart|graph\s+(TD|LR|TB|RL)", re.IGNORECASE)
RE_DANGER = re.compile(r":::danger|:::warning")
RE_PASO = re.compile(r"^###\s+Paso\s+(\d+):", re.MULTILINE)
RE_H3 = re.compile(r"^###\s+\S")


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
    """Devuelve el body de la primera sección cuyo heading == `heading`."""
    sections = _split_into_sections(text)
    for h, b in sections:
        if h.strip() == heading:
            return b
    return ""


def _first_sentence(text: str) -> str:
    """Devuelve la primera frase de `text` (hasta `.` o `;` o `!` o `?`)."""
    m = re.match(r"^[^.;!?\n]+[.;!?]", text.strip())
    return m.group(0) if m else text.strip()


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
# C2 — tabla de componentes: primera frase ≤ 30 palabras
# ---------------------------------------------------------------------------

def _parse_components_table(body: str) -> List[Tuple[str, str]]:
    """Extrae la tabla de componentes (| Componente | Responsabilidad | ... |).

    Devuelve [(componente, responsabilidad), ...].
    """
    rows: List[Tuple[str, str]] = []
    header_seen = False
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:|]+\|\s*$", stripped):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not header_seen:
            header_seen = True
            continue
        if len(cells) >= 2:
            rows.append((cells[0], cells[1]))
    return rows


def c2_responsibility_one_sentence(result: EvalResult) -> None:
    name = "C2-responsibility-one-sentence"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        body = _section_body_of(text, "## Componentes y responsabilidades")
        if not body:
            failed_notes.append(f"{note_name}: sin `## Componentes y responsabilidades`")
            continue
        rows = _parse_components_table(body)
        if len(rows) < 3:
            failed_notes.append(
                f"{note_name}: solo {len(rows)} componentes (≥ 3 requeridos)"
            )
            continue
        long_resp = []
        for comp, resp in rows:
            first = _first_sentence(resp)
            wc = len(first.split())
            if wc > 30:
                long_resp.append(f"{comp}: {wc} palabras")
        if long_resp:
            failed_notes.append(
                f"{note_name}: responsabilidades con primera frase > 30 palabras: {long_resp[:2]}"
            )
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C3 — Flujo paso a paso con ≥ 3 pasos numerados + diagrama sequenceDiagram
# ---------------------------------------------------------------------------

def c3_flow_step_by_step(result: EvalResult) -> None:
    name = "C3-flow-step-by-step"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        text = note_path.read_text(encoding="utf-8")
        body = _section_body_of(text, "## Flujo paso a paso")
        if not body:
            failed_notes.append(f"{note_name}: sin `## Flujo paso a paso`")
            continue
        pasos = RE_PASO.findall(body)
        if len(pasos) < 3:
            failed_notes.append(
                f"{note_name}: solo {len(pasos)} pasos numerados (≥ 3 requeridos)"
            )
        if not RE_SEQUENCE_DIAGRAM.search(body):
            failed_notes.append(
                f"{note_name}: sin diagrama Mermaid `sequenceDiagram` en `## Flujo paso a paso`"
            )
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C4 — Cada :::warning/:::danger en Puntos de fallo lleva {src:}
# ---------------------------------------------------------------------------

def c4_failure_points_with_source(result: EvalResult) -> None:
    name = "C4-failure-points-with-source"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        text = note_path.read_text(encoding="utf-8")
        body = _section_body_of(text, "## Puntos de fallo")
        if not body:
            failed_notes.append(f"{note_name}: sin `## Puntos de fallo`")
            continue
        lines = body.splitlines()
        unsupported = []
        for i, line in enumerate(lines):
            if RE_DANGER.search(line):
                # Verificar respaldo en ventana ±2 líneas (el callout puede ser
                # multilínea).
                window = "\n".join(lines[max(0, i - 2): min(len(lines), i + 5)])
                if not RE_SRC.search(window):
                    unsupported.append(line.strip()[:60])
        if unsupported:
            failed_notes.append(
                f"{note_name}: {len(unsupported)} puntos de fallo sin `{{src:}}` (p.ej. {unsupported[:2]})"
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
        if "[pendiente F83]" in text:
            failed.append("SKILL.md: aún contiene `[pendiente F83]`")
        elif not re.search(r"Seleccionar el tipo de nota `architecture`.*\bF83\b", text):
            failed.append("SKILL.md: no se encontró la fila de `architecture` cerrada")
    else:
        failed.append("SKILL.md no existe")
    if TYPES_README_PATH.is_file():
        text = TYPES_README_PATH.read_text(encoding="utf-8")
        if "`[pendiente F83]`" in text:
            failed.append("05-note-types/README.md: aún contiene `[pendiente F83]`")
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
    c2_responsibility_one_sentence(result)
    c3_flow_step_by_step(result)
    c4_failure_points_with_source(result)
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
