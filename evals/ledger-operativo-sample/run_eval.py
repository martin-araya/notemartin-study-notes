"""Eval — Fase 38: ledger operativo.

Verifica los 3 criterios del roadmap + no-regresión de F15/F37:
1. El reporte se genera en cualquier punto del proceso.
2. Detecta huérfanos y contenido sin respaldo.
3. El estado persiste en el manifiesto.
4. No-regresión F15 (validate_ledger.py contra fixtures regenerados).
5. No-regresión F37 (information-units-sample eval).

Exit codes: 0 PASS, 1 FAIL (con detalle), 2 usage.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
FIX = HERE / "fixtures"
EXP = HERE / "expected"
TMP = HERE / "tmp_workdir"
LEDGER_SCRIPT = REPO / "skill" / "notemartin-study-notes" / "scripts" / "util" / "ledger.py"
VALIDATE_LEDGER = REPO / "scripts" / "util" / "validate_ledger.py"
F37_EVAL = REPO / "evals" / "information-units-sample" / "run_eval.py"


def _setup_workdir(name: str, sdm_name: str, ledger_name: str | None = None,
                   manifest_name: str | None = None) -> Path:
    """Crea un workdir sintético en tmp_workdir/<name> con sdm + ledger + manifest.

    Cada llamada opera en su propio subdirectorio; no borra el resto. El
    caller conserva el Path devuelto y debe invocarlo antes de que otra
    llamada con el mismo `name` lo recree.
    """
    TMP.mkdir(parents=True, exist_ok=True)
    wd = TMP / name
    if wd.exists():
        shutil.rmtree(wd)
    wd.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIX / sdm_name, wd / "sdm.json")
    if ledger_name:
        (wd / "knowledge").mkdir(parents=True, exist_ok=True)
        shutil.copy(FIX / ledger_name, wd / "knowledge" / "ledger.json")
    if manifest_name:
        shutil.copy(FIX / manifest_name, wd / "manifest.json")
    return wd


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(LEDGER_SCRIPT)] + args,
        capture_output=True, text=True, cwd=cwd,
    )


def _check_criterion_1() -> tuple[bool, str]:
    """report sobre ledger parcialmente lleno emite las 4 vistas."""
    wd = _setup_workdir("criterion-1", "sdm-A.json", "ledger-A-ok.json")
    r = _run(["--workdir", str(wd), "report"])
    ok = (
        r.returncode == 0
        and "Coverage report:" in r.stdout
        and "must-keep:" in r.stdout
        and "Por estado" in r.stdout
        and "Por motivo de descarte" in r.stdout
        and "Top secciones con must-keep pending" in r.stdout
    )
    return ok, f"  [criterio 1] report rc={r.returncode}, vistas presentes: {ok} → {'PASS' if ok else 'FAIL'}"


def _check_criterion_2() -> tuple[bool, str]:
    """check detecta huérfanos y gaps."""
    # Orphan check.
    wd1 = _setup_workdir("criterion-2a", "sdm-A.json", "ledger-A-orphan.json")
    r1 = _run(["--workdir", str(wd1), "check"])
    expected_orphans = json.loads((EXP / "orphans.json").read_text())
    orphans_ok = (
        r1.returncode == 0
        and all(
            f"{o['unit_id']} → {o['block_id']}" in r1.stdout
            for o in expected_orphans
        )
        and "Huérfanas (entries con block_id inexistente en SDM): 1" in r1.stdout
    )

    # Gap check (default sin prose).
    wd2 = _setup_workdir("criterion-2b", "sdm-A.json", "ledger-A-gap.json")
    r2 = _run(["--workdir", str(wd2), "check"])
    expected_gaps = json.loads((EXP / "gaps.json").read_text())
    gaps_ok = (
        r2.returncode == 0
        and all(g in r2.stdout for g in expected_gaps)
        and "Sin respaldo (bloques del SDM sin entry): 2" in r2.stdout
    )

    # Gap check con --include-prose.
    r3 = _run(["--workdir", str(wd2), "check", "--include-prose"])
    expected_gaps_with_prose = json.loads((EXP / "gaps-include-prose.json").read_text())
    gaps_prose_ok = (
        r3.returncode == 0
        and all(g in r3.stdout for g in expected_gaps_with_prose)
        and "Sin respaldo (bloques del SDM sin entry): 3" in r3.stdout
    )

    # --strict rompe con desviaciones.
    r4 = _run(["--workdir", str(wd1), "check", "--strict"])
    strict_ok = r4.returncode == 1

    ok = orphans_ok and gaps_ok and gaps_prose_ok and strict_ok
    detail = (
        f"  [criterio 2a] orphans={'PASS' if orphans_ok else 'FAIL'} | "
        f"2b gaps={'PASS' if gaps_ok else 'FAIL'} | "
        f"2b gaps+prose={'PASS' if gaps_prose_ok else 'FAIL'} | "
        f"strict={'PASS' if strict_ok else 'FAIL'}"
    )
    return ok, detail + f" → {'PASS' if ok else 'FAIL'}"


def _check_criterion_3() -> tuple[bool, str]:
    """manifest --dry-run muestra el patch correcto; con escritura, no toca otros campos."""
    wd = _setup_workdir("criterion-3", "sdm-A.json", "ledger-A-ok.json", "manifest-A.json")
    r1 = _run(["--workdir", str(wd), "manifest", "--dry-run"])
    expected = json.loads((EXP / "manifest-patch.json").read_text())
    dry_ok = (
        r1.returncode == 0
        and f"units_processed: 0 → {expected['units_processed']}" in r1.stdout
    )

    # Verifica que tras --dry-run, manifest.json NO cambió.
    after_dry = json.loads((wd / "manifest.json").read_text())
    no_write_during_dry = after_dry.get("units_processed") == 0

    # Aplica el patch real.
    r2 = _run(["--workdir", str(wd), "manifest"])
    after = json.loads((wd / "manifest.json").read_text())
    patched = (
        r2.returncode == 0
        and after["units_processed"] == expected["units_processed"]
        and after["last_modified"] != "2026-09-24T00:00:00+00:00"
    )

    # No se tocaron otros campos.
    preserved = (
        after.get("glossary") == {"view": "Vista materializada"}
        and after.get("naming_decisions") == [{"entity": "note-id", "decision": "kebab-case"}]
        and after.get("stage_progress") == {"l0": "done", "l1": "done", "l2": "in_progress", "l3": "pending", "l4": "pending"}
    )

    ok = dry_ok and no_write_during_dry and patched and preserved
    detail = (
        f"  [criterio 3] dry-run={'PASS' if dry_ok else 'FAIL'} | "
        f"no-write-during-dry={'PASS' if no_write_during_dry else 'FAIL'} | "
        f"patched={'PASS' if patched else 'FAIL'} | "
        f"preserved-other-fields={'PASS' if preserved else 'FAIL'}"
    )
    return ok, detail + f" → {'PASS' if ok else 'FAIL'}"


def _check_no_regression_f15() -> tuple[bool, str]:
    r = subprocess.run(
        [sys.executable, str(VALIDATE_LEDGER), "--validate",
         str(FIX.parent.parent / "ledger-sample" / "full-coverage.json"),
         str(FIX.parent.parent / "ledger-sample" / "mixed-states.json"),
         str(FIX.parent.parent / "ledger-sample" / "section-query.json")],
        capture_output=True, text=True,
    )
    ok = r.returncode == 0 and "OK —" in r.stdout
    return ok, f"  [no-regresión F15] rc={r.returncode} → {'PASS' if ok else 'FAIL'}\n    {r.stdout.strip()[:200]}"


def _check_no_regression_f37() -> tuple[bool, str]:
    r = subprocess.run([sys.executable, str(F37_EVAL)], capture_output=True, text=True)
    ok = r.returncode == 0 and "RESULTADO: PASS" in r.stdout
    return ok, f"  [no-regresión F37] rc={r.returncode} → {'PASS' if ok else 'FAIL'}"


def main() -> int:
    print("Fase 38 — eval: ledger operativo")
    print()

    print("Criterio 1 — El reporte se genera en cualquier punto del proceso:")
    ok1, msg1 = _check_criterion_1()
    print(msg1)
    print()

    print("Criterio 2 — Detecta huérfanos y contenido sin respaldo:")
    ok2, msg2 = _check_criterion_2()
    print(msg2)
    print()

    print("Criterio 3 — El estado persiste en el manifiesto:")
    ok3, msg3 = _check_criterion_3()
    print(msg3)
    print()

    print("No-regresión:")
    ok4, msg4 = _check_no_regression_f15()
    print(msg4)
    ok5, msg5 = _check_no_regression_f37()
    print(msg5)
    print()

    all_ok = ok1 and ok2 and ok3 and ok4 and ok5
    print(f"RESULTADO: {'PASS' if all_ok else 'FAIL'} (c1={ok1} c2={ok2} c3={ok3} F15={ok4} F37={ok5})")

    # Cleanup tmp workdir.
    if TMP.exists():
        shutil.rmtree(TMP)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
