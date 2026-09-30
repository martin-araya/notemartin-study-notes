#!/usr/bin/env python3
"""Verificador de la Fase 105 — `goal-profiles` (perfiles de objetivo).

Ejecuta 18 sub-criterios sobre los deliverables de F105:

  ROADMAP (3):
    C1 — Cada perfil declara qué añade y qué relaja.
    C2 — Ninguno reduce la cobertura.
    C3 — `certification` permite consultar cobertura por objetivo.

  Estructura del doc (3):
    C4 — `goal-profiles.md` existe, ≤ 600 líneas, 9 secciones canónicas.
    C5 — §2 tabla con los 3 perfiles + cada uno con `adds[]` y `relaxes[]`.
    C6 — §5 reglas R-G1 a R-G7 presentes (7 reglas).

  Scripts (5):
    C7 — `goal_profiles.py --profile interview --input <out>` añade las secciones `adds[]`.
    C8 — `goal_profiles.py --profile certification --by-objective <id>` emite reporte por objetivo.
    C9 — `goal_profiles.py --profile work` no añade secciones (relaja solo R1).
    C10 — `goal_profiles.py --profile hybrid` pasa sin errores (modo passthrough).
    C11 — `goal_profile_check.py --profile <p>` funciona para los 3 perfiles canónicos.

  Density + wirings (4):
    C12 — Las 3 notas fixture pasan `density_check.py --strict` exit 0.
    C13 — Wirings cerrados: `SKILL.md §5.3` menciona `goal-profiles.md`;
           `references/09-study/README.md` marca `goal-profiles.md` como `publicado`;
           `references/04-authoring/properties.md` §5.23-§5.24 cita F105;
           `references/06-writing/anti-patterns.md` §2 lista AP17-AP19;
           `references/05-note-types/concept.md` §6 lista F105-1 + F105-2;
           `assets/profile.template.yaml` tiene bloque `goal_profile` + `certification.objectives`.

  Derivados (3):
    D1 — `wc -l goal-profiles.md` ≤ 600 (INV-02).
    D2 — 9 secciones canónicas §1-§9 presentes.
    D3 — §2 enum cerrado con exactamente 3 perfiles.

Uso:
    python3 evals/goal-profiles-sample/build_fixtures.py --force
    python3 evals/goal-profiles-sample/run_eval.py

Salida esperada: PASS 18/18.

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
DOC_PATH = SKILL_DIR / "references" / "09-study" / "goal-profiles.md"
STUDY_README = SKILL_DIR / "references" / "09-study" / "README.md"
SKILL_MD_PATH = SKILL_DIR / "SKILL.md"
PROPERTIES_PATH = SKILL_DIR / "references" / "04-authoring" / "properties.md"
ANTI_PATTERNS_PATH = SKILL_DIR / "references" / "06-writing" / "anti-patterns.md"
CONCEPT_MD_PATH = SKILL_DIR / "references" / "05-note-types" / "concept.md"
PROFILE_TEMPLATE = SKILL_DIR / "assets" / "profile.template.yaml"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
SCRIPT_GOALS = SKILL_DIR / "scripts" / "study" / "goal_profiles.py"
SCRIPT_CHECK = SKILL_DIR / "scripts" / "validate" / "goal_profile_check.py"
DENSITY_CHECK = SKILL_DIR / "scripts" / "validate" / "density_check.py"
DOC_LINE_LIMIT = 600

EXPECTED_SECTIONS = (
    "## §1 · Propósito y alcance",
    "## §2 · Los 3 perfiles cerrados",
    "## §3 · Principio de no-reducción (INV-GP1)",
    "## §4 · Estructura del reporte de cobertura por objetivo (solo",
    "## §5 · Reglas duras (R-G1 a R-G7)",
    "## §6 · Algoritmo del script",
    "## §7 · Algoritmo del validador",
    "## §8 · Wirings y referencias cruzadas",
    "## §9 · Verificación al cierre de la fase",
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

    if not DOC_PATH.exists():
        result.fail("C4", f"no existe {DOC_PATH}")
        return _finalize(result)

    doc_text = _read(DOC_PATH)
    line_count = _doc_line_count(DOC_PATH)

    # ─── Estructura del doc (3) ───
    if line_count > DOC_LINE_LIMIT:
        result.fail("C4", f"doc tiene {line_count} líneas (límite {DOC_LINE_LIMIT})")
    elif not all(sec in doc_text for sec in EXPECTED_SECTIONS):
        missing = [s for s in EXPECTED_SECTIONS if s not in doc_text]
        result.fail("C4", f"faltan secciones: {missing}")
    else:
        result.ok("C4")

    sec2_match = re.search(
        r"## §2 · Los 3 perfiles cerrados.*?(?=^## §3)",
        doc_text, re.MULTILINE | re.DOTALL,
    )
    if not sec2_match:
        result.fail("C5", "no se encuentra §2")
    else:
        sec2 = sec2_match.group(0)
        required_profiles = ["interview", "certification", "work"]
        missing_p = [p for p in required_profiles if p not in sec2]
        if missing_p:
            result.fail("C5", f"§2 faltan perfiles: {missing_p}")
        elif "adds[]" not in sec2 or "relaxes[]" not in sec2:
            result.fail("C5", "§2 debe declarar `adds[]` y `relaxes[]` por perfil")
        else:
            result.ok("C5")

    sec5_match = re.search(
        r"## §5 · Reglas duras.*?(?=^## §6)",
        doc_text, re.MULTILINE | re.DOTALL,
    )
    if not sec5_match:
        result.fail("C6", "no se encuentra §5")
    else:
        sec5 = sec5_match.group(0)
        required = ["R-G1", "R-G2", "R-G3", "R-G4", "R-G5", "R-G6", "R-G7"]
        missing = [r for r in required if r not in sec5]
        if missing:
            result.fail("C6", f"§5 faltan reglas: {missing}")
        else:
            result.ok("C6")

    # ─── Scripts (5) ───
    routes_path = FIXTURES_DIR / "study-paths" / "postgresql.json"

    # C7: interview añade adds.
    rc, output = _run_script(
        SCRIPT_GOALS, "--profile", "interview",
        "--input", str(routes_path),
        "--format", "md",
    )
    if rc != 0:
        result.fail("C7", f"interview exit={rc}: {output[:200]}")
    elif "## Decisiones de diseño" in output and "## Explicación oral" in output:
        result.ok("C7")
    else:
        result.fail("C7", "interview no añadió las secciones adds[] esperadas")

    # C8: certification con --by-objective.
    rc, output = _run_script(
        SCRIPT_GOALS, "--profile", "certification",
        "--input", str(routes_path),
        "--profile-yaml", str(FIXTURES_DIR / "profile.yaml"),
        "--by-objective", "ckad-core-1",
        "--format", "json",
    )
    if rc != 0:
        result.fail("C8", f"certification --by-objective exit={rc}: {output[:200]}")
    else:
        try:
            data = json.loads(output)
            if data.get("by_objective") == "ckad-core-1":
                result.ok("C8")
            else:
                result.fail("C8", f"by_objective no coincide: {data.get('by_objective')}")
        except json.JSONDecodeError as e:
            result.fail("C8", f"JSON inválido: {e}")

    # C9: work no añade secciones.
    rc, output = _run_script(
        SCRIPT_GOALS, "--profile", "work",
        "--input", str(routes_path),
        "--format", "json",
    )
    if rc != 0:
        result.fail("C9", f"work exit={rc}")
    else:
        try:
            data = json.loads(output)
            applied_adds = data.get("applied_adds", [])
            if applied_adds == []:
                result.ok("C9")
            else:
                result.fail("C9", f"work no debería añadir secciones; añadió {applied_adds}")
        except json.JSONDecodeError:
            result.fail("C9", "JSON inválido")

    # C10: hybrid (passthrough) pasa sin errores.
    rc, output = _run_script(
        SCRIPT_GOALS, "--profile", "hybrid",
        "--input", str(routes_path),
        "--format", "md",
    )
    if rc == 0:
        result.ok("C10")
    else:
        result.fail("C10", f"hybrid exit={rc}: {output[:200]}")

    # C11: goal_profile_check funciona para los 3 perfiles canónicos.
    rc_interview, _ = _run_script(
        SCRIPT_CHECK, "--profile", "interview",
        "--workdir", str(FIXTURES_DIR),
    )
    rc_cert, _ = _run_script(
        SCRIPT_CHECK, "--profile", "certification",
        "--workdir", str(FIXTURES_DIR),
    )
    rc_work, _ = _run_script(
        SCRIPT_CHECK, "--profile", "work",
        "--workdir", str(FIXTURES_DIR),
    )
    # hybrid debe pasar (modo passthrough).
    rc_hybrid, _ = _run_script(
        SCRIPT_CHECK, "--profile", "hybrid",
        "--workdir", str(FIXTURES_DIR),
    )
    if all(rc in (0, 1) for rc in (rc_interview, rc_cert, rc_work, rc_hybrid)):
        result.ok("C11")
    else:
        result.fail("C11",
                    f"algun perfil falló inesperadamente: "
                    f"interview={rc_interview} cert={rc_cert} work={rc_work} hybrid={rc_hybrid}")

    # ─── Density + wirings (4) ───
    density_files = list((FIXTURES_DIR / "notemark").glob("*.nm"))
    density_ok = 0
    density_failures: List[str] = []
    for p in density_files:
        rc, _ = _run_script(DENSITY_CHECK, "--note", str(p), "--strict")
        if rc == 0:
            density_ok += 1
        else:
            density_failures.append(f"{p.name}: exit={rc}")
    if density_ok == len(density_files):
        result.ok("C12")
    else:
        result.fail("C12", "; ".join(density_failures))

    wirings_fail: List[str] = []
    if SKILL_MD_PATH.exists():
        skill_text = _read(SKILL_MD_PATH)
        if "goal-profiles.md" not in skill_text:
            wirings_fail.append("SKILL.md no menciona goal-profiles.md")
    if STUDY_README.exists():
        study_text = _read(STUDY_README)
        m = re.search(
            r"\|\s*`?goal-profiles\.md`?\s*\|\s*F105\s*\|\s*(\S+?)\s*\|",
            study_text,
        )
        if m and "[pendiente]" in m.group(1):
            wirings_fail.append("09-study/README.md aún marca goal-profiles.md como [pendiente]")
    if PROPERTIES_PATH.exists():
        props_text = _read(PROPERTIES_PATH)
        if "F105" not in props_text or "goal-profile-override" not in props_text or "certification-objective" not in props_text:
            wirings_fail.append("properties.md no cita F105 + goal-profile-override + certification-objective")
    if ANTI_PATTERNS_PATH.exists():
        ap_text = _read(ANTI_PATTERNS_PATH)
        for ap in ("AP17", "AP18", "AP19"):
            if ap not in ap_text:
                wirings_fail.append(f"anti-patterns.md no lista {ap}")
    if CONCEPT_MD_PATH.exists():
        concept_text = _read(CONCEPT_MD_PATH)
        if "**F105-1**" not in concept_text or "**F105-2**" not in concept_text:
            wirings_fail.append("concept.md §6 no lista F105-1 + F105-2")
    if PROFILE_TEMPLATE.exists():
        pt_text = _read(PROFILE_TEMPLATE)
        if "goal_profile:" not in pt_text or "certification:" not in pt_text or "objectives" not in pt_text:
            wirings_fail.append("profile.template.yaml no tiene goal_profile + certification.objectives")
    if not wirings_fail:
        result.ok("C13")
    else:
        result.fail("C13", "; ".join(wirings_fail))

    # ─── Derivados (3) ───
    if line_count <= DOC_LINE_LIMIT:
        result.ok("D1")
    else:
        result.fail("D1", f"{line_count} líneas (>{DOC_LINE_LIMIT})")

    if all(sec in doc_text for sec in EXPECTED_SECTIONS):
        result.ok("D2")
    else:
        missing = [s for s in EXPECTED_SECTIONS if s not in doc_text]
        result.fail("D2", f"faltan: {missing}")

    if sec2_match:
        sec2 = sec2_match.group(0)
        required_profiles = ["interview", "certification", "work"]
        count = sum(1 for p in required_profiles if p in sec2)
        if count == 3:
            result.ok("D3")
        else:
            result.fail("D3", f"§2 enum tiene {count}/3 perfiles")
    else:
        result.fail("D3", "no se encontró §2")

    # ─── Aliases ROADMAP (3) ───
    if "C5" in result.passed:
        result.ok("C1-roadmap-declara-adds-relaxes")
    else:
        result.fail("C1-roadmap-declara-adds-relaxes", "C5 falló")
    if "C11" in result.passed:
        result.ok("C2-roadmap-no-reduce-cobertura")
    else:
        result.fail("C2-roadmap-no-reduce-cobertura", "C11 falló")
    if "C8" in result.passed:
        result.ok("C3-roadmap-certification-cobertura")
    else:
        result.fail("C3-roadmap-certification-cobertura", "C8 falló")

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
