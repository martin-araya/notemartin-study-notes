#!/usr/bin/env python3
"""Verificador de la Fase 78 — `concept` (tipo de nota).

Ejecuta 5 sub-criterios sobre los deliverables de F78:

  C1 — `concept.md` existe, ≤ 400 líneas, contiene las 9 secciones canónicas
       (introducción, estructura, componentes, reglas, perfil, checklist,
       ejemplo mínimo, wirings, verificación).
  C2 — Las 2 notas reales (db-mvcc, net-three-way-handshake) pasan
       `density_check.py --strict` con exit 0.
  C3 — Ambas notas contienen `## Límites y alternativas` con ≥ 1 fila tabular
       y ≥ 1 enlace `[[note:id]]` o `[[term:...]]` (criterio ROADMAP #2).
  C4 — Las 2 variantes `*-practice.md` contienen `## Práctica`; las 2 bases NO
       la contienen (criterio ROADMAP #3 — opcional por perfil).
  C5 — `SKILL.md` §5.2 fila `concept` y `references/05-note-types/README.md`
       ya no marcan `[pendiente F78]` (wiring cerrado).

Uso:
    python3 evals/concept-sample/run_eval.py           # ejecuta los 5 sub-criterios
    python3 evals/concept-sample/run_eval.py --regen   # regenera fixtures + ejecuta

Salida esperada: PASS 5/5.

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
DOC_PATH = SKILL_DIR / "references" / "05-note-types" / "concept.md"
DENSITY_CHECK_PATH = SKILL_DIR / "scripts" / "validate" / "density_check.py"
NOTES_DIR = Path(__file__).resolve().parent / "notes"
PROFILES_DIR = Path(__file__).resolve().parent / "profiles"
SKILL_MD_PATH = SKILL_DIR / "SKILL.md"
TYPES_README_PATH = SKILL_DIR / "references" / "05-note-types" / "README.md"
DOC_LINE_LIMIT = 400

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

BASE_NOTES = ("db-mvcc.md", "net-three-way-handshake.md")
PRACTICE_NOTES = ("db-mvcc-practice.md", "net-three-way-handshake-practice.md")


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


# ---------------------------------------------------------------------------
# C1 — doc existe, ≤ 400 líneas, contiene las 9 secciones canónicas
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
# C2 — notas reales pasan `density_check.py --strict`
# ---------------------------------------------------------------------------

def c2_density_check(result: EvalResult) -> None:
    name = "C2-density-check"
    if not DENSITY_CHECK_PATH.is_file():
        result.fail(name, f"{DENSITY_CHECK_PATH} no existe")
        return
    failed = []
    for note in BASE_NOTES:
        note_path = NOTES_DIR / note
        if not note_path.is_file():
            failed.append(f"{note} no existe")
            continue
        proc = subprocess.run(
            [sys.executable, str(DENSITY_CHECK_PATH), "--note", str(note_path), "--strict"],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            failed.append(f"{note}: exit {proc.returncode}\n{proc.stdout.strip()[:300]}")
    if failed:
        result.fail(name, "; ".join(failed))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C3 — ambas notas tienen `## Límites y alternativas` con fila + enlace
# ---------------------------------------------------------------------------

_RE_LINK = re.compile(r"\[\[(note|term):[^\]]+\]\]")
_RE_TABLE_ROW = re.compile(r"^\s*\|.+\|\s*$", re.MULTILINE)


def _section_body(text: str, heading: str) -> str:
    """Devuelve el texto entre `heading` y el siguiente `## ` del mismo nivel."""
    pattern = re.compile(
        rf"^{re.escape(heading)}\s*$",
        re.MULTILINE,
    )
    m = pattern.search(text)
    if not m:
        return ""
    rest = text[m.end():]
    next_h2 = re.search(r"^## ", rest, re.MULTILINE)
    return rest[: next_h2.start()] if next_h2 else rest


def _has_limits_section(note: Path, result: EvalResult, name: str) -> bool:
    text = note.read_text(encoding="utf-8")
    body = _section_body(text, "## Límites y alternativas")
    if not body.strip():
        result.fail(name, f"{note.name}: no contiene `## Límites y alternativas`")
        return False
    table_rows = _RE_TABLE_ROW.findall(body)
    # Si no hay tabla, al menos 1 bullet con link cuenta como "fila".
    has_row = len(table_rows) >= 2  # header + ≥ 1 fila
    has_link = bool(_RE_LINK.search(body))
    if not has_row and not has_link:
        result.fail(name, f"{note.name}: `## Límites y alternativas` sin fila ni enlace")
        return False
    if not has_link:
        result.fail(name, f"{note.name}: `## Límites y alternativas` sin enlace `[[note:id]]` o `[[term:]]`")
        return False
    return True


def c3_limits_alternatives(result: EvalResult) -> None:
    name = "C3-limits-alternatives"
    failed = []
    for note in BASE_NOTES:
        note_path = NOTES_DIR / note
        if not note_path.is_file():
            failed.append(f"{note} no existe")
            continue
        if not _has_limits_section(note_path, result, name):
            failed.append(note)
    if failed:
        if not result.failed or all(f[0] != name for f in result.failed):
            result.fail(name, f"fallaron: {failed}")
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C4 — variants con práctica / bases sin práctica
# ---------------------------------------------------------------------------

def c4_practice_optional(result: EvalResult) -> None:
    name = "C4-practice-optional"
    failed = []
    for note in PRACTICE_NOTES:
        note_path = NOTES_DIR / note
        if not note_path.is_file():
            failed.append(f"{note} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        if "## Práctica" not in text:
            failed.append(f"{note}: variante SIN `## Práctica`")
    for note in BASE_NOTES:
        note_path = NOTES_DIR / note
        text = note_path.read_text(encoding="utf-8")
        if "## Práctica" in text:
            failed.append(f"{note}: base CON `## Práctica` (debería omitirla)")
    if failed:
        result.fail(name, "; ".join(failed))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C5 — wirings cerrados (SKILL.md y 05-note-types/README.md)
# ---------------------------------------------------------------------------

def c5_wirings_closed(result: EvalResult) -> None:
    name = "C5-wirings-closed"
    failed = []
    if SKILL_MD_PATH.is_file():
        text = SKILL_MD_PATH.read_text(encoding="utf-8")
        # La fila 118 (en la versión previa) referenciaba concept con [pendiente F78].
        # Aceptamos tanto "F78" como "F78" en la fila.
        if re.search(r"Seleccionar el tipo de nota `concept`.*\bF78\b", text):
            pass
        elif "[pendiente F78]" in text:
            failed.append("SKILL.md: aún contiene `[pendiente F78]`")
        else:
            failed.append("SKILL.md: no se encontró la fila de `concept` cerrada")
    else:
        failed.append("SKILL.md no existe")
    if TYPES_README_PATH.is_file():
        text = TYPES_README_PATH.read_text(encoding="utf-8")
        if "`[pendiente F78]`" in text:
            failed.append("05-note-types/README.md: aún contiene `[pendiente F78]`")
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
                        help="Regenera fixtures antes de ejecutar (build_fixtures.py)")
    args = parser.parse_args()

    if args.regen:
        build_script = Path(__file__).resolve().parent / "build_fixtures.py"
        subprocess.run([sys.executable, str(build_script)], check=True)

    result = EvalResult()
    c1_doc_structure(result)
    c2_density_check(result)
    c3_limits_alternatives(result)
    c4_practice_optional(result)
    c5_wirings_closed(result)

    print(result.status)
    for name in result.passed:
        print(f"  [PASS] {name}")
    for name, detail in result.failed:
        print(f"  [FAIL] {name}: {detail}")

    return 0 if not result.failed else 1


if __name__ == "__main__":
    sys.exit(main())
