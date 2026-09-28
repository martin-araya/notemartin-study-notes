#!/usr/bin/env python3
"""Verificador de la Fase 80 — `procedure` (tipo de nota).

Ejecuta 6 sub-criterios sobre los deliverables de F80:

  C1 — `procedure.md` existe, ≤ 500 líneas, contiene las 9 secciones canónicas.
  C2 — Cada paso (`### Paso N:`) lleva `**Verificación:**` explícita — criterio
        ROADMAP #1.
  C3 — `## Impacto y reversibilidad` contiene columna Rollback **o** declaración
        de irreversibilidad — criterio ROADMAP #2.
  C4 — Cada paso destructivo (palabras clave: `DROP`, `DELETE`, `rm -rf`, etc.)
        está envuelto en `:::danger` — criterio ROADMAP #3.
  C5 — Los 3 fixtures pasan `density_check.py --strict` con exit 0.
  C6 — `SKILL.md` §5.2 fila `procedure` y `references/05-note-types/README.md`
        ya no marcan `[pendiente F80]`.

Uso:
    python3 evals/procedure-sample/run_eval.py          # ejecuta los 6 sub-criterios
    python3 evals/procedure-sample/run_eval.py --regen  # regenera fixtures + ejecuta

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
DOC_PATH = SKILL_DIR / "references" / "05-note-types" / "procedure.md"
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

ALL_NOTES = ("postgresql-backup-restore.md", "nginx-logrotate.md", "k8s-rolling-restart.md")

# Palabras clave que indican un paso destructivo.
DESTRUCTIVE_KEYWORDS = (
    "DROP ", "DROP\t", "DROP\n",
    "DELETE ",
    "TRUNCATE ",
    "rm -rf",
    "kubectl delete",
    "kubectl drain",
    "kubectl cordon",
    "terraform destroy",
    "--force",
    "DROP DATABASE",
    "DROP TABLE",
    "DELETE FROM",
    "kubectl delete pod",
)

RE_PASO = re.compile(r"^### Paso (\d+):", re.MULTILINE)
RE_VERIFICACION = re.compile(r"\*\*Verificación:\*\*", re.MULTILINE)
RE_ROLLBACK = re.compile(r"^\|.*Rollback.*\|", re.MULTILINE | re.IGNORECASE)
RE_IRREVERSIBLE = re.compile(r"irreversib", re.IGNORECASE)
RE_DANGER_BLOCK = re.compile(r":::danger", re.MULTILINE)


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
    """Divide el texto en bloques (heading, body) por encabezados H2.

    Solo se divide por `## ` (no por `# `) para evitar confundir el H1 del
    título del documento y los comentarios de shell `# {src:blk_...}` que el
    post-procesador inserta dentro de bloques de código.
    """
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
# C2 — cada paso lleva **Verificación:** explícita
# ---------------------------------------------------------------------------

def _section_after(sections: List[Tuple[str, str]], heading: str) -> str:
    """Devuelve el body de la primera sección cuyo heading == `heading`."""
    for h, body in sections:
        if h.strip() == heading:
            return body
    return ""


def c2_step_verifications(result: EvalResult) -> None:
    name = "C2-step-verifications"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        sections = _split_into_sections(text)
        proc_body = _section_after(sections, "## Procedimiento")
        pasos = RE_PASO.findall(proc_body)
        verifs = RE_VERIFICACION.findall(proc_body)
        if not pasos:
            failed_notes.append(f"{note_name}: sin `### Paso N:` en `## Procedimiento`")
            continue
        if len(verifs) < len(pasos):
            failed_notes.append(
                f"{note_name}: {len(pasos)} pasos pero solo {len(verifs)} con `**Verificación:**`"
            )
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C3 — Impacto y reversibilidad: Rollback o declaración de irreversibilidad
# ---------------------------------------------------------------------------

def c3_rollback_present(result: EvalResult) -> None:
    name = "C3-rollback-present"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        text = note_path.read_text(encoding="utf-8")
        sections = _split_into_sections(text)
        impact_body = _section_after(sections, "## Impacto y reversibilidad")
        if not impact_body:
            failed_notes.append(f"{note_name}: sin `## Impacto y reversibilidad`")
            continue
        has_rollback_row = bool(RE_ROLLBACK.search(impact_body))
        has_irreversible = bool(RE_IRREVERSIBLE.search(impact_body))
        if not (has_rollback_row or has_irreversible):
            failed_notes.append(
                f"{note_name}: `## Impacto y reversibilidad` sin columna Rollback ni declaración de irreversibilidad"
            )
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C4 — pasos destructivos están envueltos en :::danger
# ---------------------------------------------------------------------------

def c4_danger_for_destructive(result: EvalResult) -> None:
    name = "C4-danger-for-destructive"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        text = note_path.read_text(encoding="utf-8")
        sections = _split_into_sections(text)
        proc_body = _section_after(sections, "## Procedimiento")
        if not proc_body:
            failed_notes.append(f"{note_name}: sin `## Procedimiento`")
            continue

        # Identificar líneas destructivas SOLO dentro de bloques de código de
        # `## Procedimiento` (no en prosa descriptiva como "DROP DATABASE borra...").
        destructive_lines: List[Tuple[int, str]] = []
        in_code = False
        for i, line in enumerate(text.splitlines(), start=1):
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if in_code and any(kw in line for kw in DESTRUCTIVE_KEYWORDS):
                destructive_lines.append((i, line.strip()))

        # Buscar `:::danger` con proximity ±5 líneas.
        danger_lines = set()
        for m in RE_DANGER_BLOCK.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            for offset in range(-5, 6):
                danger_lines.add(line_no + offset)

        unprotected = [
            dline[:60] for lineno, dline in destructive_lines
            if lineno not in danger_lines
        ]
        if unprotected:
            failed_notes.append(
                f"{note_name}: {len(unprotected)} pasos destructivos en código sin `:::danger` (p.ej. {unprotected[:2]})"
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
        if "[pendiente F80]" in text:
            failed.append("SKILL.md: aún contiene `[pendiente F80]`")
        elif not re.search(r"Seleccionar el tipo de nota `procedure`.*\bF80\b", text):
            failed.append("SKILL.md: no se encontró la fila de `procedure` cerrada")
    else:
        failed.append("SKILL.md no existe")
    if TYPES_README_PATH.is_file():
        text = TYPES_README_PATH.read_text(encoding="utf-8")
        if "`[pendiente F80]`" in text:
            failed.append("05-note-types/README.md: aún contiene `[pendiente F80]`")
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
    c2_step_verifications(result)
    c3_rollback_present(result)
    c4_danger_for_destructive(result)
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
