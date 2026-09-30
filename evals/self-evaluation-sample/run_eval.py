#!/usr/bin/env python3
"""Verificador de la Fase 102 — `self-evaluation` (autoevaluación por tipo).

Ejecuta 14 sub-criterios sobre los deliverables de F102:

  ROADMAP (3):
    C1 — `self-evaluation.md` existe, ≤ 600 líneas, 8 secciones canónicas.
    C2 — §3 tabla cerrada con 15 filas × 5 columnas (criterio #1 ROADMAP).
    C3 — §5 plantilla NoteMark con `:::collapsible{default_open=false}` +
         `> Fundamento: …` (criterio #2 ROADMAP).

  Positivos (4):
    C4 — §6 V4 menciona Jaccard ≤ 0.8 sobre palabras no técnicas
         (criterio #3 ROADMAP).
    C5 — Las 4 notas positivas pasan `self_eval_check.py --strict` exit 0.
    C6 — Las 4 notas negativas son detectadas (V1/V2/V3/V4/V6).
    C7 — `concept.md §6` lista los 2 items `**F102-1**` y `**F102-2**`.

  Reglas y wirings (4):
    C8 — Los 15 archivos de `05-note-types/` declaran `### Autoevaluación`
         con tabla de tipos asignados copiada de §3.
    C9 — `properties.md §5.21` cita F102 + propiedad `self-evaluation-types`.
    C10 — `anti-patterns.md §2` lista AP13, AP14, AP15.
    C11 — Wirings cerrados: `SKILL.md §5.3` menciona `self-evaluation.md`;
          `references/09-study/README.md` no marca `[pendiente F102]`.

  Derivados (3):
    D1 — `wc -l self-evaluation.md` ≤ 600 (INV-02).
    D2 — 8 secciones canónicas §1-§8 presentes.
    D3 — Las 8 notas fixture pasan `density_check.py --strict` exit 0
         (R1-R8 F76).

Uso:
    python3 evals/self-evaluation-sample/build_fixtures.py --force
    python3 evals/self-evaluation-sample/run_eval.py

Salida esperada: PASS 14/14.

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skill" / "notemartin-study-notes"
DOC_PATH = SKILL_DIR / "references" / "09-study" / "self-evaluation.md"
STUDY_README = SKILL_DIR / "references" / "09-study" / "README.md"
SKILL_MD_PATH = SKILL_DIR / "SKILL.md"
PROPERTIES_PATH = SKILL_DIR / "references" / "04-authoring" / "properties.md"
ANTI_PATTERNS_PATH = SKILL_DIR / "references" / "06-writing" / "anti-patterns.md"
CONCEPT_MD_PATH = SKILL_DIR / "references" / "05-note-types" / "concept.md"
NOTE_TYPES_DIR = SKILL_DIR / "references" / "05-note-types"
NOTES_DIR = Path(__file__).resolve().parent / "notes"
SELF_EVAL_CHECK = SKILL_DIR / "scripts" / "validate" / "self_eval_check.py"
DENSITY_CHECK = SKILL_DIR / "scripts" / "validate" / "density_check.py"
DOC_LINE_LIMIT = 600

EXPECTED_SECTIONS = (
    "## §1 · Propósito y alcance",
    "## §2 · Los 5 tipos de pregunta (catálogo cerrado)",
    "## §3 · Mapeo cerrado tipo-de-nota × tipos-de-pregunta",
    "## §4 · Regla de referencia pura",
    "## §5 · Forma canónica de la pregunta y la respuesta",
    "## §6 · Algoritmo del validador",
    "## §7 · Wirings y referencias cruzadas",
    "## §8 · Verificación al cierre de la fase",
)

EXPECTED_NOTE_TYPES = (
    "concept", "api-reference", "procedure", "configuration",
    "error-troubleshooting", "architecture", "syntax", "data-model",
    "chapter-digest", "comparison", "version-delta", "glossary-term",
    "cheatsheet", "index-moc", "practice",
)

QUESTION_TYPES = ("Recuerdo", "Aplicación", "Diagnóstico", "Decisión", "Predicción")

POSITIVE_NOTES = (
    "self-eval-good-1-concept.md",
    "self-eval-good-2-procedure.md",
    "self-eval-good-3-error-troubleshooting.md",
    "self-eval-good-4-glossary-term.md",
)
NEGATIVE_NOTES = (
    "self-eval-bad-1-no-fundamento.md",
    "self-eval-bad-2-copiada.md",
    "self-eval-bad-3-recuerdo-en-referencia.md",
    "self-eval-bad-4-index-moc-con-seccion.md",
)
ALL_NOTES = POSITIVE_NOTES + NEGATIVE_NOTES


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


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _doc_line_count(path: Path) -> int:
    return sum(1 for _ in path.open(encoding="utf-8"))


def _run_script(script: Path, *args: str) -> Tuple[int, str]:
    proc = subprocess.run(
        ["python3", str(script), *args],
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def main() -> int:
    result = EvalResult()

    # ─── Pre-checks: deliverables existen ───
    if not DOC_PATH.exists():
        result.fail("C1", f"no existe {DOC_PATH}")
        return _finalize(result)
    doc_text = _read(DOC_PATH)

    # ─── ROADMAP (3) ───
    # C1: doc ≤ 600 líneas + 8 secciones canónicas.
    line_count = _doc_line_count(DOC_PATH)
    if line_count > DOC_LINE_LIMIT:
        result.fail("C1", f"doc tiene {line_count} líneas (límite {DOC_LINE_LIMIT})")
    elif not all(sec in doc_text for sec in EXPECTED_SECTIONS):
        missing = [s for s in EXPECTED_SECTIONS if s not in doc_text]
        result.fail("C1", f"faltan secciones: {missing}")
    else:
        result.ok("C1")

    # C2: §3 tabla cerrada con 15 filas × 5 columnas.
    sec3_match = re.search(
        r"## §3 · Mapeo cerrado.*?(?=^## §4)",
        doc_text, re.MULTILINE | re.DOTALL,
    )
    if not sec3_match:
        result.fail("C2", "no se encuentra §3")
    else:
        sec3 = sec3_match.group(0)
        # Contar filas con tipo de nota (formato `| `concept` (F78) | …`).
        rows = re.findall(
            r"^\|\s*`(\w[\w\-]*)`\s*\(F\d+\)\s*\|",
            sec3, re.MULTILINE,
        )
        note_type_rows = [r for r in rows if r in EXPECTED_NOTE_TYPES]
        if len(set(note_type_rows)) != 15:
            result.fail("C2", f"§3 tabla tiene {len(set(note_type_rows))} tipos (esperados 15): {note_type_rows}")
        else:
            # Verificar que las 5 columnas de tipos aparecen en el header.
            header_row = next(
                (ln for ln in sec3.splitlines()
                 if ln.startswith("|") and "note-type" in ln.lower()),
                "",
            )
            missing_qt = [qt for qt in QUESTION_TYPES if qt not in header_row]
            if missing_qt:
                result.fail("C2", f"§3 header faltan tipos: {missing_qt}")
            else:
                result.ok("C2")

    # C3: §5 plantilla NoteMark con `:::collapsible{default_open=false}` y
    # `> Fundamento:`.
    sec5_match = re.search(
        r"## §5 · Forma canónica.*?(?=^## §6)",
        doc_text, re.MULTILINE | re.DOTALL,
    )
    if not sec5_match:
        result.fail("C3", "no se encuentra §5")
    else:
        sec5 = sec5_match.group(0)
        has_collapsible = ":::collapsible{default_open=false}" in sec5
        has_fundamento = "Fundamento:" in sec5
        if not (has_collapsible and has_fundamento):
            result.fail("C3", f"§5 falta collapsible={not has_collapsible}, fundamento={not has_fundamento}")
        else:
            result.ok("C3")

    # ─── Positivos (4) ───
    # C4: §6 V4 menciona Jaccard ≤ 0.8 + lista F101 §3.
    sec6_match = re.search(
        r"## §6 · Algoritmo del validador.*?(?=^## §7)",
        doc_text, re.MULTILINE | re.DOTALL,
    )
    if not sec6_match:
        result.fail("C4", "no se encuentra §6")
    else:
        sec6 = sec6_match.group(0)
        if "Jaccard" not in sec6 or "0.8" not in sec6 or "F101 §3" not in sec6 and "F101" not in sec6:
            result.fail("C4", "§6 no menciona Jaccard ≤ 0.8 sobre palabras no técnicas")
        else:
            result.ok("C4")

    # C5: las 4 notas positivas pasan self_eval_check --strict.
    positive_ok = 0
    positive_failures: List[str] = []
    for name in POSITIVE_NOTES:
        path = NOTES_DIR / name
        if not path.exists():
            positive_failures.append(f"{name}: no existe")
            continue
        rc, _ = _run_script(SELF_EVAL_CHECK, "--note", str(path), "--strict")
        if rc == 0:
            positive_ok += 1
        else:
            positive_failures.append(f"{name}: exit={rc}")
    if positive_ok == len(POSITIVE_NOTES):
        result.ok("C5")
    else:
        result.fail("C5", "; ".join(positive_failures))

    # C6: las 4 notas negativas son detectadas (V1/V2/V3/V4/V6).
    negative_ok = 0
    negative_failures: List[str] = []
    for name in NEGATIVE_NOTES:
        path = NOTES_DIR / name
        if not path.exists():
            negative_failures.append(f"{name}: no existe")
            continue
        rc, _ = _run_script(SELF_EVAL_CHECK, "--note", str(path), "--strict")
        if rc != 0:
            negative_ok += 1
        else:
            negative_failures.append(f"{name}: exit=0 (debería fallar)")
    if negative_ok == len(NEGATIVE_NOTES):
        result.ok("C6")
    else:
        result.fail("C6", "; ".join(negative_failures))

    # C7: concept.md §6 lista F102-1 y F102-2.
    if not CONCEPT_MD_PATH.exists():
        result.fail("C7", f"no existe {CONCEPT_MD_PATH}")
    else:
        concept_text = _read(CONCEPT_MD_PATH)
        if "**F102-1**" in concept_text and "**F102-2**" in concept_text:
            result.ok("C7")
        else:
            result.fail("C7", "concept.md §6 no lista F102-1 + F102-2")

    # ─── Reglas y wirings (4) ───
    # C8: los 15 archivos de 05-note-types declaran ### Autoevaluación.
    missing_ae: List[str] = []
    for nt in EXPECTED_NOTE_TYPES:
        path = NOTE_TYPES_DIR / f"{nt}.md"
        if not path.exists():
            missing_ae.append(f"{nt}.md: no existe")
            continue
        text = _read(path)
        if not re.search(r"^###\s+(?:§\S+\s+·\s+)?Autoevaluaci[oó]n", text, re.MULTILINE):
            missing_ae.append(f"{nt}.md")
    if not missing_ae:
        result.ok("C8")
    else:
        result.fail("C8", f"faltan sección: {missing_ae}")

    # C9: properties.md §5 cita F102 + propiedad self-evaluation-types.
    if not PROPERTIES_PATH.exists():
        result.fail("C9", f"no existe {PROPERTIES_PATH}")
    else:
        properties_text = _read(PROPERTIES_PATH)
        if "F102" in properties_text and "self-evaluation-types" in properties_text:
            result.ok("C9")
        else:
            result.fail("C9", "properties.md no cita F102 + self-evaluation-types")

    # C10: anti-patterns.md §2 lista AP13, AP14, AP15.
    if not ANTI_PATTERNS_PATH.exists():
        result.fail("C10", f"no existe {ANTI_PATTERNS_PATH}")
    else:
        ap_text = _read(ANTI_PATTERNS_PATH)
        missing_ap = [ap for ap in ("AP13", "AP14", "AP15") if ap not in ap_text]
        if missing_ap:
            result.fail("C10", f"faltan: {missing_ap}")
        else:
            result.ok("C10")

    # C11: wirings cerrados.
    wirings_fail: List[str] = []
    if SKILL_MD_PATH.exists():
        skill_text = _read(SKILL_MD_PATH)
        if "self-evaluation.md" not in skill_text:
            wirings_fail.append("SKILL.md no menciona self-evaluation.md")
    else:
        wirings_fail.append("SKILL.md no existe")
    if STUDY_README.exists():
        study_text = _read(STUDY_README)
        if "[pendiente F102]" in study_text:
            wirings_fail.append("09-study/README.md aún marca [pendiente F102]")
    else:
        wirings_fail.append("09-study/README.md no existe")
    if not wirings_fail:
        result.ok("C11")
    else:
        result.fail("C11", "; ".join(wirings_fail))

    # ─── Derivados (3) ───
    # D1: wc -l doc ≤ 600.
    if line_count <= DOC_LINE_LIMIT:
        result.ok("D1")
    else:
        result.fail("D1", f"{line_count} líneas (>{DOC_LINE_LIMIT})")

    # D2: 8 secciones canónicas presentes.
    if all(sec in doc_text for sec in EXPECTED_SECTIONS):
        result.ok("D2")
    else:
        missing = [s for s in EXPECTED_SECTIONS if s not in doc_text]
        result.fail("D2", f"faltan: {missing}")

    # D3: las 8 notas fixture pasan density_check --strict.
    density_ok = 0
    density_failures: List[str] = []
    for name in ALL_NOTES:
        path = NOTES_DIR / name
        if not path.exists():
            density_failures.append(f"{name}: no existe")
            continue
        rc, _ = _run_script(DENSITY_CHECK, "--note", str(path), "--strict")
        if rc == 0:
            density_ok += 1
        else:
            density_failures.append(f"{name}: exit={rc}")
    if density_ok == len(ALL_NOTES):
        result.ok("D3")
    else:
        result.fail("D3", "; ".join(density_failures))

    return _finalize(result)


def _finalize(result: EvalResult) -> int:
    total = result.total
    passed = len(result.passed)
    failed = len(result.failed)
    print(f"PASS {passed}/{total}")
    for name in result.passed:
        print(f"  [PASS] {name}")
    for name, detail in result.failed:
        print(f"  [FAIL] {name}: {detail}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
