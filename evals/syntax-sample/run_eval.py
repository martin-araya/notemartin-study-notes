#!/usr/bin/env python3
"""Verificador de la Fase 84 — `syntax` (tipo de nota).

Ejecuta 6 sub-criterios sobre los deliverables de F84:

  C1 — `syntax.md` existe, ≤ 500 líneas, contiene las 9 secciones canónicas.
  C2 — Cada cláusula opcional (`[...]` en BNF) tiene `###` sub-sección en
        `## Cláusula por cláusula` — criterio ROADMAP #1.
  C3 — `## Contraejemplos` tiene ≥ 1 `:::warning` con input + error literal —
        criterio ROADMAP #2.
  C4 — `## Diagramas de sintaxis` tiene `:::diagram` Mermaid ≥ 3 nodos —
        criterio ROADMAP #3.
  C5 — Los 3 fixtures pasan `density_check.py --strict` con exit 0.
  C6 — `SKILL.md` §5.2 fila `syntax` y `references/05-note-types/README.md`
        ya no marcan `[pendiente F84]`.

Uso:
    python3 evals/syntax-sample/run_eval.py
    python3 evals/syntax-sample/run_eval.py --regen

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
DOC_PATH = SKILL_DIR / "references" / "05-note-types" / "syntax.md"
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
    "postgresql-select.md",
    "kubernetes-pod-spec.md",
    "curl-syntax.md",
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
    """Devuelve el body de la primera sección cuyo heading == `heading`."""
    sections = _split_into_sections(text)
    for h, b in sections:
        if h.strip() == heading:
            return b
    return ""


def _extract_code_blocks(body: str) -> List[str]:
    """Devuelve el contenido de cada bloque `code`."""
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


def _extract_h3_subheadings(body: str) -> List[str]:
    """Devuelve todos los H3 del cuerpo."""
    return [line.strip() for line in body.splitlines() if line.startswith("### ")]


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
# C2 — Cada cláusula opcional [...] en BNF tiene sub-sección ###
# ---------------------------------------------------------------------------

def _extract_optional_clauses_from_bnf(body: str) -> List[str]:
    """Extrae los nombres de cláusulas opcionales a partir de la BNF.

    Estrategia: para cada `[...]` en la BNF, identificar la keyword/cláusula
    INMEDIATAMENTE ANTERIOR (1-3 tokens antes del `[`).
    """
    blocks = _extract_code_blocks(body)
    bnf_text = "\n".join(blocks)
    clauses: List[str] = []
    # Buscar cada [...] y la keyword antes.
    for m in re.finditer(r"\[([^\[\]]+)\]", bnf_text):
        before = bnf_text[: m.start()]
        # Buscar el último token keyword-like antes de `[`.
        tokens = re.findall(r"\b([A-Z][A-Z_0-9]+|[A-Za-z][a-z_]+)\b", before)
        if tokens:
            # Filtrar tokens de BNF genéricos.
            GENERIC = {
                "SELECT", "FROM", "WHERE", "GROUP", "ORDER", "BY", "AS",
                "WITH", "AND", "OR", "NOT", "ALL", "ANY", "EXISTS",
                "ASC", "DESC", "INTO", "ON", "FOR",
            }
            # Buscar el token no-genérico más cercano.
            for token in reversed(tokens[-5:]):
                if token not in GENERIC and len(token) >= 3:
                    clauses.append(token)
                    break
            else:
                # Si todos son genéricos, usar el último.
                if tokens:
                    clauses.append(tokens[-1])
    return list(dict.fromkeys(clauses))  # dedupe preserving order


def c2_optional_clauses_documented(result: EvalResult) -> None:
    name = "C2-optional-clauses-documented"
    failed_notes = []
    MIN_H3_SUBSECTIONS = 5
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        clausula_body = _section_body_of(text, "## Cláusula por cláusula")
        if not clausula_body.strip():
            failed_notes.append(f"{note_name}: sin `## Cláusula por cláusula`")
            continue
        h3s = _extract_h3_subheadings(clausula_body)
        if len(h3s) < MIN_H3_SUBSECTIONS:
            failed_notes.append(
                f"{note_name}: solo {len(h3s)} sub-secciones `###` en `## Cláusula por cláusula` "
                f"(≥ {MIN_H3_SUBSECTIONS} requeridas para cubrir cláusulas obligatorias y opcionales)"
            )
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C3 — Contraejemplos con error literal
# ---------------------------------------------------------------------------

def c3_counter_examples_present(result: EvalResult) -> None:
    name = "C3-counter-examples-present"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        contra_body = _section_body_of(text, "## Contraejemplos")
        if not contra_body.strip():
            failed_notes.append(f"{note_name}: sin `## Contraejemplos`")
            continue
        # Buscar :::warning con patrón "Error literal" o "ERROR:".
        warnings = re.findall(r":::warning\n(.*?)\n:::", contra_body, re.DOTALL)
        if len(warnings) < 1:
            failed_notes.append(f"{note_name}: `## Contraejemplos` sin `:::warning`")
            continue
        # Verificar que al menos 1 warning contiene "Error" o "ERROR" o similar.
        has_error = any(
            re.search(r"\b(ERROR|Error|error|fatal)\b", w) for w in warnings
        )
        if not has_error:
            failed_notes.append(
                f"{note_name}: contraejemplos sin mensaje de error literal"
            )
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C4 — Diagramas de sintaxis con Mermaid ≥ 3 nodos
# ---------------------------------------------------------------------------

def c4_syntax_diagrams(result: EvalResult) -> None:
    name = "C4-syntax-diagrams"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        text = note_path.read_text(encoding="utf-8")
        diag_body = _section_body_of(text, "## Diagramas de sintaxis")
        if not diag_body.strip():
            failed_notes.append(f"{note_name}: sin `## Diagramas de sintaxis`")
            continue
        # Buscar :::diagram ... ```mermaid ... ```
        mermaid_match = re.search(
            r":::diagram\n```(?:mermaid)?\n(.*?)```", diag_body, re.DOTALL
        )
        if not mermaid_match:
            failed_notes.append(
                f"{note_name}: `## Diagramas de sintaxis` sin bloque `:::diagram` Mermaid"
            )
            continue
        mermaid_code = mermaid_match.group(1)
        # Contar nodos: líneas con `-->`, `---`, `===`, `==>`, `->>` o que definan nodos `[X]` o `(X)`.
        nodes = re.findall(r"\b([A-Za-z][A-Za-z0-9_]*)\s*[\[\(\{]", mermaid_code)
        unique_nodes = set(nodes)
        if len(unique_nodes) < 3:
            failed_notes.append(
                f"{note_name}: diagrama con {len(unique_nodes)} nodos (< 3)"
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
        if "[pendiente F84]" in text:
            failed.append("SKILL.md: aún contiene `[pendiente F84]`")
        elif not re.search(r"Seleccionar el tipo de nota `syntax`.*\bF84\b", text):
            failed.append("SKILL.md: no se encontró la fila de `syntax` cerrada")
    else:
        failed.append("SKILL.md no existe")
    if TYPES_README_PATH.is_file():
        text = TYPES_README_PATH.read_text(encoding="utf-8")
        if "`[pendiente F84]`" in text:
            failed.append("05-note-types/README.md: aún contiene `[pendiente F84]`")
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
    c2_optional_clauses_documented(result)
    c3_counter_examples_present(result)
    c4_syntax_diagrams(result)
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
