#!/usr/bin/env python3
"""Verificador de la Fase 97 — `comparisons` (5 formas canónicas + marcas derivadas).

Ejecuta 18 sub-criterios sobre los deliverables de F97:

  ROADMAP (3):
    C1 — `comparisons.md` existe, ≤ 600 líneas, contiene las 13 secciones canónicas.
    C2 — §3 tiene ≥ 3 plantillas (DB / protocolos / arquitectura) con sus 5
         formas canónicas (F1-F5).
    C3 — §4 incluye tabla lado a lado con regla de fila decisiva (`:::tip`) +
         regla de paralelismo.

  Positivos (4):
    C4 — §6 incluye matriz de decisión por escenario con ≥ 3 filas.
    C5 — §7 incluye tabla de trade-offs con ≥ 3 filas.
    C6 — Las 4 notas base tienen **una tabla** que va seguida de **un párrafo
         de síntesis** ≥ 2 similitudes + 1 diferencia (criterio #1).
    C7 — Las 4 notas base declaran `:::derived` o `:::external` cuando la
         comparación la construye el agente (criterio #2).

  Reglas (4):
    C8 — `cmp-sql-vs-nosql-hierarchy.md` contiene jerarquía por relajación
         con ≥ 3 niveles (criterio #3 ROADMAP).
    C9 — Wirings cerrados.
    C10 — Las 4 notas base pasan `density_check.py --strict` exit 0.
    C11 — `anti-missing-sintesis.md` falla C6 a propósito (test negativo).
    C12 — `cmp-mono-vs-micro.md` tiene ≥ 1 matriz de decisión de ejemplo técnico.

  Derivados (6):
    D1 — `wc -l comparisons.md` ≤ 600.
    D2 — 13 secciones canónicas §1-§13 presentes.
    D3 — §5 jerarquía por relajación tiene ≥ 3 niveles.
    D4 — §11 tiene ≥ 8 señales algorítmicas D1-D10.
    D5 — Wirings cerrados (alias C9).
    D6 — `density_check` (alias C10).

Uso:
    python3 evals/comparisons-sample/build_fixtures.py --force
    python3 evals/comparisons-sample/run_eval.py

Salida esperada: PASS 18/18.

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
DOC_PATH = SKILL_DIR / "references" / "06-writing" / "comparisons.md"
WRITING_README = SKILL_DIR / "references" / "06-writing" / "README.md"
SKILL_MD_PATH = SKILL_DIR / "SKILL.md"
NOTES_DIR = Path(__file__).resolve().parent / "notes"
DENSITY_CHECK = SKILL_DIR / "scripts" / "validate" / "density_check.py"
DOC_LINE_LIMIT = 600

EXPECTED_SECTIONS = (
    "## §1 · Propósito y alcance",
    "## §2 · Las 5 formas canónicas",
    "## §3 · Plantillas canónicas",
    "## §4 · Tabla lado a lado",
    "## §5 · Jerarquía por relajación de restricciones",
    "## §6 · Matriz de decisión por escenario",
    "## §7 · Tabla de trade-offs",
    "## §8 · Párrafo de síntesis obligatorio",
    "## §9 · Marcado de comparaciones derivadas",
    "## §10 · Anti-patrones",
    "## §11 · Señales de diagnóstico",
    "## §12 · Wirings y referencias cruzadas",
    "## §13 · Verificación al cierre de la fase",
)

POSITIVE_NOTES = (
    "cmp-db-postgres-vs-mysql.md",
    "cmp-rest-vs-grpc.md",
    "cmp-mono-vs-micro.md",
    "cmp-sql-vs-nosql-hierarchy.md",
)
NEGATIVE_NOTE = "anti-missing-sintesis.md"


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


def _section_text(text: str, header_prefix: str) -> str:
    """Devuelve el texto de la sección H2/H3 que empieza con header_prefix.

    Ignora headers dentro de code fences (``` o ~~~).
    """
    lines = text.split("\n")
    start = None
    start_level = 2
    for i, line in enumerate(lines):
        stripped = line.lstrip("#").strip()
        if (line.startswith("## ") or line.startswith("### ")) and stripped.startswith(header_prefix):
            start = i
            start_level = len(line) - len(line.lstrip("#"))
            break
    if start is None:
        return ""
    end = len(lines)
    in_fence = False
    fence_marker = None
    for j in range(start + 1, len(lines)):
        stripped = lines[j].lstrip()
        if not in_fence:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = True
                fence_marker = stripped[:3]
                continue
            if lines[j].startswith("#"):
                level = len(lines[j]) - len(lines[j].lstrip("#"))
                if level <= start_level:
                    end = j
                    break
        else:
            if stripped.startswith(fence_marker):
                in_fence = False
    return "\n".join(lines[start:end])


def check_c1_doc_structure(result: EvalResult) -> None:
    if not DOC_PATH.exists():
        result.fail("C1-doc-structure", f"no existe {DOC_PATH}")
        return
    text = DOC_PATH.read_text(encoding="utf-8")
    n = sum(1 for _ in DOC_PATH.open(encoding="utf-8"))
    if n > DOC_LINE_LIMIT:
        result.fail("C1-doc-structure", f"{n} líneas > {DOC_LINE_LIMIT}")
        return
    for header in EXPECTED_SECTIONS:
        if header not in text:
            result.fail("C1-doc-structure", f"falta sección {header}")
            return
    result.ok("C1-doc-structure")


def check_c2_templates(result: EvalResult) -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    sec3 = _section_text(text, "§3")
    if not sec3:
        result.fail("C2-templates", "no se encontró §3")
        return
    for sub in ("§3.1", "§3.2", "§3.3"):
        if not re.search(rf"###\s+{re.escape(sub)}\b", sec3):
            result.fail("C2-templates", f"falta plantilla {sub}")
            return
    result.ok("C2-templates")


def check_c3_side_by_side(result: EvalResult) -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    sec4 = _section_text(text, "§4")
    if not sec4:
        result.fail("C3-side-by-side", "no se encontró §4")
        return
    # Regla de fila decisiva con `:::tip`.
    if ":::tip" not in sec4:
        result.fail("C3-side-by-side", "§4 no menciona `:::tip` (fila decisiva)")
        return
    # Regla de paralelismo (criterio #3 de F87).
    if not re.search(r"paralel|criterio\s+#?3", sec4, re.IGNORECASE):
        result.fail("C3-side-by-side", "§4 no menciona la regla de paralelismo")
        return
    result.ok("C3-side-by-side")


def check_c4_decision_matrix(result: EvalResult) -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    sec6 = _section_text(text, "§6")
    if not sec6:
        result.fail("C4-decision-matrix", "no se encontró §6")
        return
    # ≥ 3 filas de escenarios en la plantilla.
    scenarios = re.findall(r"Escenario\s+\d", sec6)
    if len(scenarios) < 3:
        result.fail("C4-decision-matrix", f"§6 menciona {len(scenarios)} escenarios (esperaba ≥ 3)")
        return
    result.ok("C4-decision-matrix")


def check_c5_tradeoffs(result: EvalResult) -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    sec7 = _section_text(text, "§7")
    if not sec7:
        result.fail("C5-tradeoffs", "no se encontró §7")
        return
    # ≥ 3 filas de trade-offs en la plantilla.
    if not re.search(r"Consistencia\s+vs\s+disponibilidad|Madurez\s+vs\s+innovaci[oó]n", sec7):
        result.fail("C5-tradeoffs", "§7 no tiene ≥ 3 filas de trade-offs en la plantilla")
        return
    result.ok("C5-tradeoffs")


def _has_synthesis(text: str) -> bool:
    """Detecta que la nota tiene `## Síntesis` con ≥ 2 similitudes + 1 diferencia."""
    # El helper _section_text toma el prefijo sin `## `; "Síntesis" encuentra el H2.
    sec = _section_text(text, "Síntesis")
    if not sec:
        return False
    # ≥ 30 palabras
    words = len(sec.split())
    if words < 30:
        return False
    # ≥ 2 similitudes (comparten / ambas / también / igual)
    sims = re.findall(r"comparten|ambas|tambi[ée]n|igual", sec, re.IGNORECASE)
    if len(sims) < 2:
        return False
    # ≥ 1 diferencia clave (diferencia / mientras / frente a / a diferencia de)
    diff = re.findall(r"diferencia\s+clave|mientras|frente\s+a|a\s+diferencia\s+de", sec, re.IGNORECASE)
    if len(diff) < 1:
        return False
    return True


def _has_derived_or_external(text: str) -> bool:
    return ":::derived" in text or ":::external" in text or "{external}" in text or "{derived}" in text


def check_c6_synthesis_positive(result: EvalResult) -> None:
    for fname in POSITIVE_NOTES:
        path = NOTES_DIR / fname
        if not path.exists():
            result.fail("C6-synthesis-positive", f"falta {path}")
            return
        text = path.read_text(encoding="utf-8")
        if not _has_synthesis(text):
            result.fail(
                "C6-synthesis-positive",
                f"{fname}: '## Síntesis' ausente o < 30 palabras o < 2 similitudes + 1 diferencia",
            )
            return
    result.ok("C6-synthesis-positive")


def check_c7_derived_mark(result: EvalResult) -> None:
    """Las 4 notas base declaran `:::derived` o `:::external` (criterio #2)."""
    for fname in POSITIVE_NOTES:
        path = NOTES_DIR / fname
        text = path.read_text(encoding="utf-8")
        if not _has_derived_or_external(text):
            result.fail(
                "C7-derived-mark",
                f"{fname}: falta marca `:::derived` o `:::external` (comparación derivada)",
            )
            return
    result.ok("C7-derived-mark")


def check_c8_hierarchy_levels(result: EvalResult) -> None:
    """cmp-sql-vs-nosql-hierarchy.md tiene ≥ 3 niveles en la jerarquía."""
    path = NOTES_DIR / "cmp-sql-vs-nosql-hierarchy.md"
    if not path.exists():
        result.fail("C8-hierarchy", f"falta {path}")
        return
    text = path.read_text(encoding="utf-8")
    # Contar filas `| 0 |`, `| 1 |`, `| 2 |`, `| 3 |` en tablas.
    levels = re.findall(r"\|\s*([0-3])\s*\|", text)
    unique = sorted(set(levels))
    if len(unique) < 3:
        result.fail(
            "C8-hierarchy",
            f"cmp-sql-vs-nosql-hierarchy.md tiene {len(unique)} niveles (esperaba ≥ 3): {unique}",
        )
        return
    result.ok("C8-hierarchy")


def check_c9_wirings_closed(result: EvalResult) -> None:
    if not WRITING_README.exists():
        result.fail("C9-wirings-closed", f"no existe {WRITING_README}")
        return
    rread = WRITING_README.read_text(encoding="utf-8")
    if re.search(r"\[pendiente\s+F97\]", rread):
        result.fail("C9-wirings-closed", "06-writing/README.md sigue marcando [pendiente F97]")
        return
    if "comparisons.md" not in rread:
        result.fail("C9-wirings-closed", "06-writing/README.md no menciona comparisons.md")
        return
    if not SKILL_MD_PATH.exists():
        result.fail("C9-wirings-closed", f"no existe {SKILL_MD_PATH}")
        return
    if "comparisons.md" not in SKILL_MD_PATH.read_text(encoding="utf-8"):
        result.fail("C9-wirings-closed", "SKILL.md no menciona comparisons.md")
        return
    result.ok("C9-wirings-closed")


def check_c10_density(result: EvalResult) -> None:
    if not DENSITY_CHECK.exists():
        result.fail("C10-density", f"no existe {DENSITY_CHECK}")
        return
    failed = []
    for fname in POSITIVE_NOTES:
        path = NOTES_DIR / fname
        try:
            proc = subprocess.run(
                ["python3", str(DENSITY_CHECK), "--note", str(path), "--strict"],
                capture_output=True, text=True, timeout=30,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            result.fail("C10-density", f"density_check falló para {fname}: {e}")
            return
        if proc.returncode != 0:
            failed.append(f"{fname} (exit {proc.returncode})")
    if failed:
        result.fail("C10-density", f"density_check --strict falla en: {', '.join(failed)}")
        return
    result.ok("C10-density")


def check_c11_synthesis_negative(result: EvalResult) -> None:
    path = NOTES_DIR / NEGATIVE_NOTE
    if not path.exists():
        result.fail("C11-synthesis-negative", f"falta {path}")
        return
    text = path.read_text(encoding="utf-8")
    if _has_synthesis(text):
        result.fail(
            "C11-synthesis-negative",
            f"{NEGATIVE_NOTE}: el fixture NEGATIVO no debe tener síntesis (rompe el test)",
        )
        return
    result.ok("C11-synthesis-negative")


def check_c12_micro_matrix(result: EvalResult) -> None:
    """cmp-mono-vs-micro.md tiene matriz de decisión `Escenario / Mejor opción / Justificación`."""
    path = NOTES_DIR / "cmp-mono-vs-micro.md"
    if not path.exists():
        result.fail("C12-micro-matrix", f"falta {path}")
        return
    text = path.read_text(encoding="utf-8")
    if not re.search(r"\|\s*Escenario\s*\|\s*Mejor\s+opci[oó]n\s*\|", text):
        result.fail(
            "C12-micro-matrix",
            "cmp-mono-vs-micro.md: no tiene tabla con header Escenario / Mejor opción",
        )
        return
    # ≥ 3 filas de escenarios — buscar en la sección '## Matriz de decisión'.
    sec = _section_text(text, "Matriz de decisión")
    if not sec:
        # Fallback: cualquier sección que contenga la tabla.
        sec = text
    filas = re.findall(r"\|\s*(Startup|Empresa|Compliance|Carga)\b", sec)
    if len(filas) < 3:
        result.fail(
            "C12-micro-matrix",
            f"cmp-mono-vs-micro.md: solo {len(filas)} filas de escenarios (esperaba ≥ 3)",
        )
        return
    result.ok("C12-micro-matrix")


def check_d1_line_limit(result: EvalResult) -> None:
    if not DOC_PATH.exists():
        result.fail("D1-line-limit", f"no existe {DOC_PATH}")
        return
    n = sum(1 for _ in DOC_PATH.open(encoding="utf-8"))
    if n > DOC_LINE_LIMIT:
        result.fail("D1-line-limit", f"{n} líneas > {DOC_LINE_LIMIT}")
        return
    result.ok("D1-line-limit")


def check_d2_sections(result: EvalResult) -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    missing = [h for h in EXPECTED_SECTIONS if h not in text]
    if missing:
        result.fail("D2-sections", f"faltan {len(missing)} secciones")
        return
    result.ok("D2-sections")


def check_d3_hierarchy_section(result: EvalResult) -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    sec5 = _section_text(text, "§5")
    if not sec5:
        result.fail("D3-hierarchy-section", "no se encontró §5")
        return
    # ≥ 3 niveles en la plantilla de §5.1.
    levels = re.findall(r"\|\s*([0-3])\s*\|", sec5)
    if len(set(levels)) < 3:
        result.fail(
            "D3-hierarchy-section",
            f"§5 menciona {len(set(levels))} niveles (esperaba ≥ 3)",
        )
        return
    result.ok("D3-hierarchy-section")


def check_d4_signals(result: EvalResult) -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    sec11 = _section_text(text, "§11")
    if not sec11:
        result.fail("D4-signals", "no se encontró §11")
        return
    sigs = re.findall(r"\*\*D(\d+)\*\*", sec11)
    if len(set(sigs)) < 8:
        result.fail("D4-signals", f"§11 lista {len(set(sigs))} señales D* (esperaba ≥ 8)")
        return
    if not re.search(r"regex|conteo|presencia|ratio", sec11, re.IGNORECASE):
        result.fail("D4-signals", "§11 no menciona métodos algorítmicos")
        return
    result.ok("D4-signals")


def check_d5_wirings_alias(result: EvalResult) -> None:
    check_c9_wirings_closed(result)
    if result.passed and result.passed[-1] == "C9-wirings-closed":
        result.passed[-1] = "D5-wirings-alias"
    elif result.failed and result.failed[-1][0] == "C9-wirings-closed":
        name, detail = result.failed[-1]
        result.failed[-1] = ("D5-wirings-alias", detail)


def check_d6_density_alias(result: EvalResult) -> None:
    check_c10_density(result)
    if result.passed and result.passed[-1] == "C10-density":
        result.passed[-1] = "D6-density-alias"
    elif result.failed and result.failed[-1][0] == "C10-density":
        name, detail = result.failed[-1]
        result.failed[-1] = ("D6-density-alias", detail)


CHECKS = (
    check_c1_doc_structure,
    check_c2_templates,
    check_c3_side_by_side,
    check_c4_decision_matrix,
    check_c5_tradeoffs,
    check_c6_synthesis_positive,
    check_c7_derived_mark,
    check_c8_hierarchy_levels,
    check_c9_wirings_closed,
    check_c10_density,
    check_c11_synthesis_negative,
    check_c12_micro_matrix,
    check_d1_line_limit,
    check_d2_sections,
    check_d3_hierarchy_section,
    check_d4_signals,
    check_d5_wirings_alias,
    check_d6_density_alias,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    args = parser.parse_args()

    result = EvalResult()
    for fn in CHECKS:
        fn(result)

    for name in result.passed:
        print(f"[PASS] {name}")
    for name, detail in result.failed:
        print(f"[FAIL] {name}: {detail}")
    print(f"\n{result.status}")
    return 0 if not result.failed else 1


if __name__ == "__main__":
    sys.exit(main())
