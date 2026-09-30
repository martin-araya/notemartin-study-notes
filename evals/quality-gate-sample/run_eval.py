#!/usr/bin/env python3
"""
run_eval.py — Eval F115 (puerta de calidad y reporte).

Criterios:
  C1 — clean/promote exit 0 + frontmatter status pasa de "published" a "verified".
  C2 — with-errors/promote exit 1 + ningún frontmatter modificado.
  C3 — with-incomplete-coverage/report tiene not_covered no vacío.
  C4 — with-debt/report lista las 2 entradas del registry.
  C5 — clean/report produce JSON con shape mínima válida.

Exit 0 si los 5 PASS; 1 en otro caso.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIX = ROOT / "fixtures"
QG = Path("/Users/martin/Desktop/projects/notemartin-study-notes/skill/notemartin-study-notes/scripts/quality_gate.py")


def run_qg(workdir: Path, *args: str) -> tuple[int, dict | None]:
    cmd = [sys.executable, str(QG), "--workdir", str(workdir), *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    try:
        return proc.returncode, json.loads(proc.stdout)
    except json.JSONDecodeError:
        return proc.returncode, None


def check_c1() -> tuple[bool, str]:
    """clean/promote --yes: exit 0 + al menos 1 nota a verified."""
    wd = FIX / "clean"
    # Reset state (delete any prior promote output).
    for nm in wd.glob("notemark/*.nm"):
        bak = nm.with_suffix(nm.suffix + ".bak")
        if bak.is_file():
            nm.write_text(bak.read_text(encoding="utf-8"), encoding="utf-8")
            bak.unlink()
    rc, _ = run_qg(wd, "--yes", "promote")
    if rc != 0:
        return False, f"clean/promote exit {rc}"
    # Verify frontmatter.
    verified = 0
    for nm in (wd / "notemark").glob("*.nm"):
        text = nm.read_text(encoding="utf-8")
        if "status: verified" in text:
            verified += 1
    if verified == 0:
        return False, f"0 notas promovidas a verified"
    return True, f"{verified} notas promovidas"


def check_c2() -> tuple[bool, str]:
    """with-errors/promote --yes: exit 1 + ningún frontmatter modificado."""
    wd = FIX / "with-errors"
    # Reset from .bak if exists.
    for nm in wd.glob("notemark/*.nm"):
        bak = nm.with_suffix(nm.suffix + ".bak")
        if bak.is_file():
            nm.write_text(bak.read_text(encoding="utf-8"), encoding="utf-8")
            bak.unlink()
    rc, _ = run_qg(wd, "--yes", "promote")
    if rc == 0:
        return False, "with-errors/promote exitó 0 (esperaba 1)"
    # Verify NO .nm was modified.
    for nm in (wd / "notemark").glob("*.nm"):
        text = nm.read_text(encoding="utf-8")
        if "status: verified" in text:
            return False, f"{nm.name} fue modificado a verified (no debería)"
    return True, "promote bloqueado, sin mutaciones"


def check_c3() -> tuple[bool, str]:
    """with-incomplete-coverage/report tiene not_covered no vacío."""
    wd = FIX / "with-incomplete-coverage"
    rc, rep = run_qg(wd, "--json", "report")
    if rep is None:
        return False, "no JSON"
    nc = rep.get("not_covered", [])
    if not nc:
        return False, f"not_covered vacío (esperaba ≥ 1)"
    return True, f"not_covered tiene {len(nc)} entradas"


def check_c4() -> tuple[bool, str]:
    """with-debt/report lista las 2 entradas del registry."""
    wd = FIX / "with-debt"
    rc, rep = run_qg(wd, "--json", "report")
    if rep is None:
        return False, "no JSON"
    debt = rep.get("debt_registry", [])
    if len(debt) != 2:
        return False, f"debt_registry tiene {len(debt)} entradas (esperaba 2)"
    return True, f"debt_registry tiene {len(debt)} entradas"


def check_c5() -> tuple[bool, str]:
    """clean/report produce JSON con campos requeridos."""
    wd = FIX / "clean"
    rc, rep = run_qg(wd, "--json", "report")
    if rep is None:
        return False, "no JSON"
    required = ["schema_version", "workdir", "summary", "blocking",
                "coverage", "rubric", "not_covered", "debt_registry", "sources"]
    missing = [r for r in required if r not in rep]
    if missing:
        return False, f"faltan campos: {missing}"
    if rep["summary"].get("errors", 0) > 0:
        return False, f"errors no esperado en clean"
    return True, "shape JSON válida"


def main() -> int:
    print("=== C1 — clean/promote promueve a verified ===")
    c1_ok, c1 = check_c1()
    print(f"  {c1}  PASS={c1_ok}")
    print("\n=== C2 — with-errors/promote bloqueado ===")
    c2_ok, c2 = check_c2()
    print(f"  {c2}  PASS={c2_ok}")
    print("\n=== C3 — with-incomplete-coverage/report not_covered no vacío ===")
    c3_ok, c3 = check_c3()
    print(f"  {c3}  PASS={c3_ok}")
    print("\n=== C4 — with-debt/report lista ambas entradas ===")
    c4_ok, c4 = check_c4()
    print(f"  {c4}  PASS={c4_ok}")
    print("\n=== C5 — clean/report JSON shape válida ===")
    c5_ok, c5 = check_c5()
    print(f"  {c5}  PASS={c5_ok}")

    overall = c1_ok and c2_ok and c3_ok and c4_ok and c5_ok
    print("\n=== Summary ===")
    for name, ok in [("C1", c1_ok), ("C2", c2_ok), ("C3", c3_ok),
                      ("C4", c4_ok), ("C5", c5_ok)]:
        print(f"  {name}: {'PASS' if ok else 'FAIL'}")
    print(f"  Overall: {'PASS' if overall else 'FAIL'}")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())