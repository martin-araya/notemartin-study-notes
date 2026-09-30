#!/usr/bin/env python3
"""Verificador de la Fase 104 — `study-paths` (rutas de estudio).

Ejecuta 16 sub-criterios sobre los deliverables de F104:

  ROADMAP (3):
    C1 — Cada dominio tiene al menos dos rutas.
    C2 — Respetan el orden de prerrequisitos.
    C3 — Cada ruta tiene puntos de verificación explícitos.

  Estructura del doc (3):
    C4 — `study-paths.md` existe, ≤ 600 líneas, 9 secciones canónicas.
    C5 — §2 tabla con los 3 objetivos cerrados.
    C6 — §5 reglas R-P1 a R-P7 presentes (7 reglas).

  Scripts (5):
    C7 — `study_paths.py --domain postgresql --goal all` emite ≥ 2 rutas.
    C8 — Las rutas emitidas respetan el orden de prerrequisitos (topological sort).
    C9 — Las rutas emitidas tienen ≥ 1 punto de verificación explícito.
    C10 — Cada dominio del fixture tiene ≥ 2 rutas.
    C11 — `study_paths.py --format json` emite JSON válido con el shape esperado.
    C12 — `study_paths_check.py --routes <out> --note-plan <plan>` pasa sin violaciones.

  Density + wirings (3):
    C13 — Las 10 notas fixture + living-doc pasan `density_check.py --strict`.
    C14 — Wirings cerrados: SKILL.md §5.3 menciona study-paths.md;
           09-study/README.md marca study-paths.md como publicado;
           properties.md §5.22 cita F104; concept-graph.md R5 cita F104;
           schemas/concept-graph.schema.json tiene los campos nuevos.

  Derivados (3):
    D1 — `wc -l study-paths.md` ≤ 600 (INV-02).
    D2 — 9 secciones canónicas §1-§9 presentes.
    D3 — §4 enum cerrado con exactamente 3 objetivos.

Uso:
    python3 evals/study-paths-sample/build_fixtures.py --force
    python3 evals/study-paths-sample/run_eval.py

Salida esperada: PASS 16/16.

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skill" / "notemartin-study-notes"
DOC_PATH = SKILL_DIR / "references" / "09-study" / "study-paths.md"
STUDY_README = SKILL_DIR / "references" / "09-study" / "README.md"
SKILL_MD_PATH = SKILL_DIR / "SKILL.md"
PROPERTIES_PATH = SKILL_DIR / "references" / "04-authoring" / "properties.md"
CONCEPT_GRAPH_MD = SKILL_DIR / "references" / "03-knowledge" / "concept-graph.md"
CONCEPT_GRAPH_SCHEMA = SKILL_DIR / "schemas" / "concept-graph.schema.json"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
SCRIPT_PATHS = SKILL_DIR / "scripts" / "study" / "study_paths.py"
SCRIPT_CHECK = SKILL_DIR / "scripts" / "validate" / "study_paths_check.py"
DENSITY_CHECK = SKILL_DIR / "scripts" / "validate" / "density_check.py"
DOC_LINE_LIMIT = 600

EXPECTED_SECTIONS = (
    "## §1 · Propósito y alcance",
    "## §2 · Los 3 objetivos cerrados",
    "## §3 · Estructura de una ruta",
    "## §4 · Lista cerrada de los 3 objetivos",
    "## §5 · Reglas duras (R-P1 a R-P7)",
    "## §6 · Algoritmo del script",
    "## §7 · Algoritmo del validador",
    "## §8 · Wirings y referencias cruzadas",
    "## §9 · Verificación al cierre de la fase",
)

EXPECTED_DOMAINS = ("postgresql", "docker")


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

    # ─── Pre-check ───
    if not DOC_PATH.exists():
        result.fail("C4", f"no existe {DOC_PATH}")
        return _finalize(result)

    doc_text = _read(DOC_PATH)
    line_count = _doc_line_count(DOC_PATH)

    # ─── Estructura del doc (3) ───
    # C4: doc ≤ 600 + 9 secciones canónicas.
    if line_count > DOC_LINE_LIMIT:
        result.fail("C4", f"doc tiene {line_count} líneas (límite {DOC_LINE_LIMIT})")
    elif not all(sec in doc_text for sec in EXPECTED_SECTIONS):
        missing = [s for s in EXPECTED_SECTIONS if s not in doc_text]
        result.fail("C4", f"faltan secciones: {missing}")
    else:
        result.ok("C4")

    # C5: §2 tabla con los 3 objetivos cerrados.
    sec2_match = re.search(
        r"## §2 · Los 3 objetivos.*?(?=^## §3)",
        doc_text, re.MULTILINE | re.DOTALL,
    )
    if not sec2_match:
        result.fail("C5", "no se encuentra §2")
    else:
        sec2 = sec2_match.group(0)
        required = ["operar-hoy", "entender-a-fondo", "repasar"]
        missing = [r for r in required if r not in sec2]
        if missing:
            result.fail("C5", f"§2 faltan objetivos: {missing}")
        else:
            result.ok("C5")

    # C6: §5 reglas R-P1 a R-P7.
    sec5_match = re.search(
        r"## §5 · Reglas duras.*?(?=^## §6)",
        doc_text, re.MULTILINE | re.DOTALL,
    )
    if not sec5_match:
        result.fail("C6", "no se encuentra §5")
    else:
        sec5 = sec5_match.group(0)
        required = ["R-P1", "R-P2", "R-P3", "R-P4", "R-P5", "R-P6", "R-P7"]
        missing = [r for r in required if r not in sec5]
        if missing:
            result.fail("C6", f"§5 faltan reglas: {missing}")
        else:
            result.ok("C6")

    # ─── Scripts (5) ───
    # C7-C10: emitir rutas y validar.
    routes_json_path = FIXTURES_DIR / "study-paths-routes.json"
    rc, output = _run_script(
        SCRIPT_PATHS, "--domain", "all", "--goal", "all",
        "--workdir", str(FIXTURES_DIR),
        "--errors-dir", str(FIXTURES_DIR / "study" / "errors"),
        "--format", "json",
    )
    routes_json_path.write_text(output, encoding="utf-8")

    if rc != 0:
        result.fail("C7", f"study_paths.py exit={rc}: {output[:200]}")
        return _finalize(result)

    try:
        routes_data = json.loads(output)
    except json.JSONDecodeError as e:
        result.fail("C11", f"JSON inválido: {e}")
        return _finalize(result)

    result.ok("C7")
    result.ok("C11")

    # C10: cada dominio tiene ≥ 2 rutas.
    by_domain: dict[str, list] = {}
    for r in routes_data:
        by_domain.setdefault(r.get("domain"), []).append(r)

    missing_domains = [d for d in EXPECTED_DOMAINS if len(by_domain.get(d, [])) < 2]
    if missing_domains:
        result.fail("C10", f"dominios con < 2 rutas: {missing_domains}")
    else:
        result.ok("C10")

    # C8: orden topológico correcto (V2 del validador).
    rc, _ = _run_script(
        SCRIPT_CHECK,
        "--routes", str(routes_json_path),
        "--note-plan", str(FIXTURES_DIR / "knowledge" / "note-plan.json"),
    )
    if rc != 0:
        result.fail("C8", f"study_paths_check exit={rc} (orden topológico o V4 falla)")
    else:
        result.ok("C8")

    # C9: cada ruta tiene ≥ 1 checkpoint.
    no_checkpoint = []
    for r in routes_data:
        if not r.get("checkpoints"):
            no_checkpoint.append(f"{r.get('domain')}/{r.get('goal')}")
    if no_checkpoint:
        result.fail("C9", f"rutas sin checkpoints: {no_checkpoint}")
    else:
        result.ok("C9")

    # C12: el validador funciona con el archivo generado.
    rc, _ = _run_script(
        SCRIPT_CHECK,
        "--routes", str(routes_json_path),
        "--note-plan", str(FIXTURES_DIR / "knowledge" / "note-plan.json"),
    )
    if rc == 0:
        result.ok("C12")
    else:
        result.fail("C12", f"study_paths_check exit={rc}")

    # ─── Density + wirings (3) ───
    # C13: las notas fixture + living-doc pasan density_check --strict.
    density_files = (
        list((FIXTURES_DIR / "notemark").glob("*.nm"))
        + [FIXTURES_DIR / "study" / "errors" / "error-log-postgresql.md"]
    )
    density_ok = 0
    density_failures: List[str] = []
    for p in density_files:
        rc, _ = _run_script(DENSITY_CHECK, "--note", str(p), "--strict")
        if rc == 0:
            density_ok += 1
        else:
            density_failures.append(f"{p.name}: exit={rc}")
    if density_ok == len(density_files):
        result.ok("C13")
    else:
        result.fail("C13", "; ".join(density_failures))

    # C14: wirings cerrados.
    wirings_fail: List[str] = []
    if SKILL_MD_PATH.exists():
        skill_text = _read(SKILL_MD_PATH)
        if "study-paths.md" not in skill_text:
            wirings_fail.append("SKILL.md no menciona study-paths.md")
    else:
        wirings_fail.append("SKILL.md no existe")
    if STUDY_README.exists():
        study_text = _read(STUDY_README)
        m = re.search(
            r"\|\s*`?study-paths\.md`?\s*\|\s*F104\s*\|\s*(\S+?)\s*\|",
            study_text,
        )
        if m and "[pendiente]" in m.group(1):
            wirings_fail.append("09-study/README.md aún marca study-paths.md como [pendiente]")
    else:
        wirings_fail.append("09-study/README.md no existe")
    if PROPERTIES_PATH.exists():
        props_text = _read(PROPERTIES_PATH)
        if "F104" not in props_text or "study-path-goals" not in props_text:
            wirings_fail.append("properties.md no cita F104 o study-path-goals")
    if CONCEPT_GRAPH_MD.exists():
        cg_text = _read(CONCEPT_GRAPH_MD)
        if "F104" not in cg_text:
            wirings_fail.append("concept-graph.md no cita F104")
    if CONCEPT_GRAPH_SCHEMA.exists():
        schema_text = _read(CONCEPT_GRAPH_SCHEMA)
        if '"goal"' not in schema_text or '"estimated_minutes"' not in schema_text:
            wirings_fail.append("concept-graph.schema.json no tiene goal + estimated_minutes")
    if not wirings_fail:
        result.ok("C14")
    else:
        result.fail("C14", "; ".join(wirings_fail))

    # ─── Derivados (3) ───
    # D1: doc ≤ 600 líneas.
    if line_count <= DOC_LINE_LIMIT:
        result.ok("D1")
    else:
        result.fail("D1", f"{line_count} líneas (>{DOC_LINE_LIMIT})")

    # D2: 9 secciones canónicas presentes.
    if all(sec in doc_text for sec in EXPECTED_SECTIONS):
        result.ok("D2")
    else:
        missing = [s for s in EXPECTED_SECTIONS if s not in doc_text]
        result.fail("D2", f"faltan: {missing}")

    # D3: §4 enum cerrado con exactamente 3 objetivos.
    sec4_match = re.search(
        r"## §4 · Lista cerrada.*?(?=^## §5)",
        doc_text, re.MULTILINE | re.DOTALL,
    )
    if not sec4_match:
        result.fail("D3", "no se encontró §4")
    else:
        sec4 = sec4_match.group(0)
        required = ["operar-hoy", "entender-a-fondo", "repasar"]
        count = sum(1 for r in required if r in sec4)
        if count != 3:
            result.fail("D3", f"§4 enum tiene {count}/3 objetivos")
        else:
            result.ok("D3")

    # ─── Aliases de los 3 criterios ROADMAP (3) ───
    if "C10" in result.passed:
        result.ok("C1-roadmap-dominios-2-rutas")
    else:
        result.fail("C1-roadmap-dominios-2-rutas", "C10 falló")
    if "C8" in result.passed:
        result.ok("C2-roadmap-prerrequisitos")
    else:
        result.fail("C2-roadmap-prerrequisitos", "C8 falló")
    if "C9" in result.passed:
        result.ok("C3-roadmap-checkpoints")
    else:
        result.fail("C3-roadmap-checkpoints", "C9 falló")

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
