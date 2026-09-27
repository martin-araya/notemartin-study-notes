#!/usr/bin/env python3
"""Verificador de la Fase 76 — Densidad y jerarquía.

Ejecuta 5 sub-criterios sobre los deliverables de F76:

  C1 — `density.md` existe, ≤ 500 líneas, contiene la tabla cerrada R1-R8.
  C2 — `density_check.py --note r2-violation.md` emite Issue con `code="R2"`.
  C3 — `density_check.py --note r4-violation.md` emite Issue con `code="R4"`.
  C4 — `density_check.py --note glossary.md` (tipo exento) NO emite R3 ni R6.
  C5 — `density_check.py --note compliant.md` retorna exit 0 (sin violaciones).

Uso:
    python3 evals/density-sample/run_eval.py
    python3 evals/density-sample/run_eval.py --regen

Salida esperada: PASS 5/5.

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skill" / "notemartin-study-notes"
DOC_PATH = SKILL_DIR / "references" / "07-visual" / "density.md"
DENSITY_CHECK_PATH = SKILL_DIR / "scripts" / "validate" / "density_check.py"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "notes"
DOC_LINE_LIMIT = 500

# Códigos de regla R1-R8.
R_CODES = ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8")


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

    def summary(self) -> str:
        if not self.failed:
            return f"PASS {len(self.passed)}/{self.total}"
        return f"FAIL {len(self.failed)}/{self.total} (passed {len(self.passed)}/{self.total})"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, mod)
    spec.loader.exec_module(mod)
    return mod


def c1_doc_has_8_rules(result: EvalResult) -> None:
    if not DOC_PATH.is_file():
        result.fail("C1-doc-8-rules", f"{DOC_PATH} no existe")
        return
    n = sum(1 for _ in DOC_PATH.open("r", encoding="utf-8"))
    if n > DOC_LINE_LIMIT:
        result.fail("C1-doc-8-rules", f"{n} líneas > {DOC_LINE_LIMIT}")
        return
    text = DOC_PATH.read_text(encoding="utf-8")
    # Cuenta referencias a R1-R8 (en la tabla §2 con `**R[1-8]**` y §9 con `| R[1-8] |`).
    table2 = re.findall(r"\*\*R[1-8]\*\*", text)
    table9 = re.findall(r"\| R[1-8] \|", text)
    if not table2 or not table9:
        result.fail("C1-doc-8-rules",
                    f"tablas R1-R8 incompletas: §2={len(table2)}, §9={len(table9)}")
        return
    if len(table2) < 8 or len(table9) < 8:
        result.fail("C1-doc-8-rules",
                    f"faltan reglas: §2={len(table2)}/8, §9={len(table9)}/8")
        return
    result.ok(
        f"C1-doc-8-rules ({n} líneas ≤ {DOC_LINE_LIMIT}; "
        f"§2 tabla={len(table2)} reglas, §9 tabla={len(table9)} reglas)"
    )


def _run_density_check(note_path: Path) -> Tuple[int, str, str]:
    """Ejecuta density_check.py sobre una nota; retorna (exit, stdout, stderr)."""
    proc = subprocess.run(
        [sys.executable, str(DENSITY_CHECK_PATH), "--note", str(note_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def c2_r2_violation_detected(result: EvalResult) -> None:
    path = FIXTURES_DIR / "r2-violation.md"
    if not path.is_file():
        result.fail("C2-r2-detected", f"{path} no existe")
        return
    exit_code, stdout, stderr = _run_density_check(path)
    if "R2" not in stdout:
        result.fail("C2-r2-detected", f"R2 no detectado en output: {stdout[:200]}")
        return
    if exit_code != 1:
        result.fail("C2-r2-detected", f"exit={exit_code} (esperado 1)")
        return
    result.ok("C2-r2-detected (R2 detectado, exit=1)")


def c3_r4_violation_detected(result: EvalResult) -> None:
    path = FIXTURES_DIR / "r4-violation.md"
    if not path.is_file():
        result.fail("C3-r4-detected", f"{path} no existe")
        return
    exit_code, stdout, stderr = _run_density_check(path)
    if "R4" not in stdout:
        result.fail("C3-r4-detected", f"R4 no detectado en output: {stdout[:200]}")
        return
    if exit_code != 1:
        result.fail("C3-r4-detected", f"exit={exit_code} (esperado 1)")
        return
    result.ok("C3-r4-detected (R4 detectado, exit=1)")


def c4_glossary_exempt(result: EvalResult) -> None:
    """glossary-term está exenta de R3 y R6; la nota tiene 8 bullets en sección
    única, lo que sin exención dispararía R6."""
    path = FIXTURES_DIR / "glossary.md"
    if not path.is_file():
        result.fail("C4-glossary-exempt", f"{path} no existe")
        return
    exit_code, stdout, stderr = _run_density_check(path)
    # R3 y R6 no deben aparecer en la salida.
    if "R3" in stdout or "R6" in stdout:
        result.fail("C4-glossary-exempt",
                    f"R3 o R6 detectado en glossary (no debería): {stdout[:200]}")
        return
    if exit_code != 0:
        result.fail("C4-glossary-exempt", f"exit={exit_code} (esperado 0)")
        return
    result.ok("C4-glossary-exempt (R3+R6 exentos; exit=0)")


def c5_compliant_no_violations(result: EvalResult) -> None:
    path = FIXTURES_DIR / "compliant.md"
    if not path.is_file():
        result.fail("C5-compliant", f"{path} no existe")
        return
    exit_code, stdout, stderr = _run_density_check(path)
    # Errores (severity=error): no debe haber ninguno.
    if "### Errores" in stdout:
        result.fail("C5-compliant", f"errores en compliant: {stdout[:200]}")
        return
    if exit_code != 0:
        result.fail("C5-compliant", f"exit={exit_code} (esperado 0)")
        return
    result.ok("C5-compliant (0 errores, exit=0)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regen", action="store_true",
                        help="No usado; los fixtures son commiteados.")
    args = parser.parse_args()

    result = EvalResult()
    c1_doc_has_8_rules(result)
    c2_r2_violation_detected(result)
    c3_r4_violation_detected(result)
    c4_glossary_exempt(result)
    c5_compliant_no_violations(result)

    print("=" * 60)
    print("Fase 76 — Densidad y jerarquía")
    print("=" * 60)
    for name in result.passed:
        print(f"  PASS  {name}")
    for name, detail in result.failed:
        print(f"  FAIL  {name}\n        {detail}")
    print("=" * 60)
    print(result.summary())
    return 0 if not result.failed else 1


if __name__ == "__main__":
    sys.exit(main())
