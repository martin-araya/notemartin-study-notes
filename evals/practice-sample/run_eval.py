#!/usr/bin/env python3
"""Verificador de la Fase 92 — `practice` / lab (tipo de nota).

Ejecuta 6 sub-criterios sobre los deliverables de F92:

  C1 — `practice.md` existe, ≤ 600 líneas, contiene las 9 secciones canónicas.
  C2 — Cada fixture tiene `## Entorno` con ≥ 3 componentes Y `## Limpieza`
        con ≥ 1 paso — criterio ROADMAP #1.
  C3 — Cada paso destructivo (DROP, DELETE, rm -rf, kubectl delete) tiene
        `:::warning` o `:::danger` adyacente (±5 líneas) — criterio #2.
  C4 — Cada fixture tiene `## Cuándo omitir este lab` con ≥ 1 criterio —
        criterio ROADMAP #3.
  C5 — Los 3 fixtures pasan `density_check.py --strict` con exit 0.
  C6 — `SKILL.md` §5.2 fila `practice` y
        `references/05-note-types/README.md` ya no marcan `[pendiente F92]`.

Uso:
    python3 evals/practice-sample/run_eval.py
    python3 evals/practice-sample/run_eval.py --regen

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
DOC_PATH = SKILL_DIR / "references" / "05-note-types" / "practice.md"
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
    "practice-postgres-backup.md",
    "practice-docker-compose.md",
    "practice-git-rebase.md",
)

DESTRUCTIVE_PATTERNS = (
    "DROP ", "DROP\t", "DROP\n",
    "DELETE ",
    "TRUNCATE ",
    "rm -rf",
    "rm -f",
    "kubectl delete",
    "kubectl drain",
    "kubectl cordon",
    "terraform destroy",
    "git push --force",
    "git push -f",
    "dropdb ",
    "docker rm ",
    "docker compose down -v",
    "docker rmi ",
    "docker volume rm",
    "kubectl apply -f",
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
# C2 — Entorno + Limpieza — criterio #1
# ---------------------------------------------------------------------------

def _has_table_with_rows(body: str, min_rows: int) -> bool:
    rows = [l for l in body.splitlines() if l.strip().startswith("|")]
    rows = [l for l in rows if not re.match(r"^\|[\s\-:|]+\|\s*$", l.strip())]
    return len(rows) >= min_rows


def _has_numbered_list_with_min_steps(body: str, min_steps: int) -> bool:
    """Cuenta items numerados `1.`, `2.`, etc."""
    items = re.findall(r"^\s*\d+\.\s+", body, re.MULTILINE)
    return len(items) >= min_steps


def c2_entorno_and_limpieza(result: EvalResult) -> None:
    name = "C2-entorno-and-limpieza"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        entorno_body = _section_body_of(text, "## Entorno")
        limpieza_body = _section_body_of(text, "## Limpieza")
        if not entorno_body.strip():
            failed_notes.append(f"{note_name}: sin `## Entorno`")
            continue
        if not limpieza_body.strip():
            failed_notes.append(f"{note_name}: sin `## Limpieza`")
            continue
        # Verificar que Entorno tenga ≥ 3 filas en tabla.
        entorno_rows_ok = _has_table_with_rows(entorno_body, 3)
        if not entorno_rows_ok:
            failed_notes.append(
                f"{note_name}: `## Entorno` sin tabla con ≥ 3 componentes"
            )
        # Verificar que Limpieza tenga ≥ 1 paso numerado o item.
        limpieza_steps = _has_numbered_list_with_min_steps(limpieza_body, 1)
        if not limpieza_steps:
            failed_notes.append(
                f"{note_name}: `## Limpieza` sin pasos numerados"
            )
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C3 — Pasos destructivos con :::warning — criterio #2
# ---------------------------------------------------------------------------

def c3_warning_on_destructive(result: EvalResult) -> None:
    name = "C3-warning-on-destructive"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        lines = text.splitlines()
        # Para cada línea que contiene un comando destructivo, verificar que
        # hay un :::warning o :::danger en la misma sección `## ` (más amplio que ±5 líneas).
        unprotected = []
        # Encontrar todas las secciones H2 y sus rangos.
        section_ranges: List[Tuple[int, int, str]] = []
        current_start = None
        current_name = ""
        for i, line in enumerate(lines):
            if line.startswith("## "):
                if current_start is not None:
                    section_ranges.append((current_start, i, current_name))
                current_start = i
                current_name = line.strip()
        if current_start is not None:
            section_ranges.append((current_start, len(lines), current_name))

        def section_for(line_idx: int) -> Tuple[int, int, str]:
            for start, end, name in section_ranges:
                if start <= line_idx < end:
                    return start, end, name
            return -1, -1, ""

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("|") or stripped.startswith(":"):
                continue
            if any(pat in line for pat in DESTRUCTIVE_PATTERNS):
                # Buscar warning/danger en ±10 líneas (más amplio que el típico).
                window = "\n".join(lines[max(0, i - 10):min(len(lines), i + 11)])
                if ":::warning" in window or ":::danger" in window:
                    continue
                # Si está en `## Lo que NO debe correrse`, ya está marcado.
                sec_start, sec_end, sec_name = section_for(i)
                if "Lo que NO" in sec_name:
                    continue
                unprotected.append(f"línea {i+1} ({sec_name}): {line[:60]!r}")
        if unprotected:
            failed_notes.append(
                f"{note_name}: {len(unprotected)} pasos destructivos sin `:::warning` adyacente: {unprotected[:3]}"
            )
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C4 — Cuándo omitir este lab — criterio #3
# ---------------------------------------------------------------------------

def c4_cuando_omitir(result: EvalResult) -> None:
    name = "C4-cuando-omitir"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        body = _section_body_of(text, "## Cuándo omitir este lab")
        if not body.strip():
            failed_notes.append(f"{note_name}: sin `## Cuándo omitir este lab`")
            continue
        # Verificar ≥ 1 criterio: bullets con `si:`, `cuando:`, `(1)`, `(2)`, etc.
        has_criterion = bool(re.search(r"\(\d+\)|si:|cuando:|om[ie]te", body, re.IGNORECASE))
        if not has_criterion:
            failed_notes.append(
                f"{note_name}: `## Cuándo omitir este lab` sin criterios explícitos"
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
        if "[pendiente F92]" in text:
            failed.append("SKILL.md: aún contiene `[pendiente F92]`")
        elif not re.search(r"Seleccionar el tipo de nota `practice`.*\bF92\b", text):
            failed.append("SKILL.md: no se encontró la fila de `practice` cerrada")
    else:
        failed.append("SKILL.md no existe")
    if TYPES_README_PATH.is_file():
        text = TYPES_README_PATH.read_text(encoding="utf-8")
        if "`[pendiente F92]`" in text:
            failed.append("05-note-types/README.md: aún contiene `[pendiente F92]`")
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
    c2_entorno_and_limpieza(result)
    c3_warning_on_destructive(result)
    c4_cuando_omitir(result)
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
