"""Eval — Fase 43: auditoría de no-pérdida.

Verifica los 3 criterios del roadmap + no-regresión F15/F37/F38/F39/F40/F41/F42:

1. Detecta una omisión inyectada deliberadamente.
2. El muestreo inverso tiene tamaño y método definidos.
3. No se puede cerrar el trabajo con la auditoría en rojo.

Exit codes: 0 PASS los 8, 1 FAIL, 2 usage.
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

COMPLETENESS = REPO / "skill" / "notemartin-study-notes" / "scripts" / "validate" / "completeness.py"
VALIDATE_LEDGER = REPO / "scripts" / "util" / "validate_ledger.py"
F37_EVAL = REPO / "evals" / "information-units-sample" / "run_eval.py"
F38_EVAL = REPO / "evals" / "ledger-operativo-sample" / "run_eval.py"
F39_EVAL = REPO / "evals" / "concept-graph-sample" / "run_eval.py"
F40_EVAL = REPO / "evals" / "terminology-sample" / "run_eval.py"
F41_EVAL = REPO / "evals" / "conflicts-sample" / "run_eval.py"
F42_EVAL = REPO / "evals" / "fidelity-sample" / "run_eval.py"


def _setup_workdir(name: str, sdm_name: str, ledger_name: str,
                   sample_rate: float = 0.10, seed: int = 0) -> Path:
    TMP.mkdir(parents=True, exist_ok=True)
    wd = TMP / name
    if wd.exists():
        shutil.rmtree(wd)
    wd.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIX / sdm_name, wd / "sdm.json")
    (wd / "knowledge").mkdir(parents=True, exist_ok=True)
    shutil.copy(FIX / ledger_name, wd / "knowledge" / "ledger.json")
    return wd


def _run(workdir: Path, subcommand: str = "audit",
         global_flags: dict | None = None,
         sub_flags: list[str] | None = None) -> subprocess.CompletedProcess:
    """Run completeness.py. global_flags go BEFORE subcommand; sub_flags go AFTER."""
    cmd = [sys.executable, str(COMPLETENESS)]
    if global_flags:
        for k, v in global_flags.items():
            cmd.append(f"--{k.replace('_', '-')}")
            cmd.append(str(v))
    cmd.extend(["--workdir", str(workdir), subcommand])
    if sub_flags:
        cmd.extend(sub_flags)
    return subprocess.run(cmd, capture_output=True, text=True)


def _load_report(r: subprocess.CompletedProcess) -> dict:
    return json.loads(r.stdout)


# -------------------------------------------------------------------
# Criterio 1: detecta omisión inyectada.
# -------------------------------------------------------------------

def check_omission_detected() -> tuple[bool, str]:
    """Ledger omite el block error-code; audit debe reportarlo."""
    wd = _setup_workdir("c1", "sdm-clean.json", "ledger-with-omission.json")
    r = _run(wd, "audit")
    exit_correct = r.returncode == 1
    try:
        report = _load_report(r)
    except Exception:
        return False, f"  [c1] FAIL (no se pudo parsear JSON): {r.stdout[:200]}"
    findings = report.get("findings", [])
    has_missing = any(f["category"] == "missing-backward" and f["severity"] == "critical" for f in findings)
    ok = exit_correct and has_missing
    detail = f"  [c1] exit={r.returncode} (esperado 1), missing-backward={has_missing}"
    return ok, detail + f" → {'PASS' if ok else 'FAIL'}"


def check_mutilation_detected() -> tuple[bool, str]:
    """parameter.name mutilado; audit debe reportarlo."""
    wd = _setup_workdir("c1-mut", "sdm-clean.json", "ledger-mutilated.json")
    r = _run(wd, "audit")
    exit_correct = r.returncode == 1
    report = _load_report(r)
    findings = report.get("findings", [])
    has_mutilated = any(f["category"] == "mutilated" and f["severity"] == "critical" for f in findings)
    ok = exit_correct and has_mutilated
    detail = f"  [c1-mut] exit={r.returncode} (esperado 1), mutilated={has_mutilated}"
    return ok, detail + f" → {'PASS' if ok else 'FAIL'}"


def check_pending_detected() -> tuple[bool, str]:
    """must-keep con state=pending; audit debe reportarlo."""
    wd = _setup_workdir("c1-pend", "sdm-clean.json", "ledger-pending.json")
    r = _run(wd, "audit")
    exit_correct = r.returncode == 1
    report = _load_report(r)
    findings = report.get("findings", [])
    has_pending = any(f["category"] == "pending-must-keep" and f["severity"] == "critical" for f in findings)
    ok = exit_correct and has_pending
    detail = f"  [c1-pend] exit={r.returncode} (esperado 1), pending-must-keep={has_pending}"
    return ok, detail + f" → {'PASS' if ok else 'FAIL'}"


# -------------------------------------------------------------------
# Criterio 2: muestreo inverso definido.
# -------------------------------------------------------------------

def check_inverse_sample_defined() -> tuple[bool, str]:
    """El reporte declara los tamaños del inverse sample (criterio 2)."""
    wd = _setup_workdir("c2", "sdm-context-rich.json", "ledger-context-rich-partial.json")
    r = _run(wd, "audit", global_flags={"sample_rate": 0.20, "seed": 0})
    try:
        report = _load_report(r)
    except Exception:
        return False, f"  [c2] FAIL (no se pudo parsear): {r.stdout[:200]}"
    sm = report.get("inverse_sample", {}).get("sample_metadata", {})
    has_total = "total_blocks" in sm
    has_must_keep = "must_keep_count" in sm
    has_sampled_mk = "sampled_must_keep" in sm
    has_sampled_context = "sampled_context" in sm
    has_pct = "sampled_context_pct" in sm
    has_seed = "seed" in sm
    has_sample_rate = "sample_rate" in sm

    fields_ok = all([has_total, has_must_keep, has_sampled_mk,
                     has_sampled_context, has_pct, has_seed, has_sample_rate])
    # must_keep_coverage_pct debe ser 100%.
    mk_cov_ok = sm.get("must_keep_coverage_pct") == 100.0

    ok = fields_ok and mk_cov_ok
    detail = (f"  [c2] fields_ok={fields_ok}, must_keep_coverage_pct={sm.get('must_keep_coverage_pct')}, "
              f"sampled_must_keep={sm.get('sampled_must_keep')}, "
              f"sampled_context={sm.get('sampled_context')}/{sm.get('context_pool_count')}")
    return ok, detail + f" → {'PASS' if ok else 'FAIL'}"


def check_sample_deterministic() -> tuple[bool, str]:
    """Dos corridas con mismo seed → mismo resultado."""
    wd1 = _setup_workdir("c2-det1", "sdm-context-rich.json", "ledger-context-rich-partial.json")
    wd2 = _setup_workdir("c2-det2", "sdm-context-rich.json", "ledger-context-rich-partial.json")
    r1 = _run(wd1, "audit", global_flags={"sample_rate": 0.50, "seed": 42})
    r2 = _run(wd2, "audit", global_flags={"sample_rate": 0.50, "seed": 42})
    rep1 = _load_report(r1)
    rep2 = _load_report(r2)
    sm1 = rep1.get("inverse_sample", {}).get("sample_metadata", {})
    sm2 = rep2.get("inverse_sample", {}).get("sample_metadata", {})
    ok = sm1.get("sampled_context") == sm2.get("sampled_context")
    detail = f"  [c2-det] run1.sampled={sm1.get('sampled_context')}, run2.sampled={sm2.get('sampled_context')}"
    return ok, detail + f" → {'PASS' if ok else 'FAIL'}"


# -------------------------------------------------------------------
# Criterio 3: exit 1 con auditoría en rojo.
# -------------------------------------------------------------------

def check_exit_code_red() -> tuple[bool, str]:
    """audit exit 1 con critical; check --strict exit 1."""
    wd = _setup_workdir("c3", "sdm-clean.json", "ledger-with-omission.json")
    r1 = _run(wd, "audit")
    exit_audit = r1.returncode == 1
    r2 = _run(wd, "check")
    exit_check = r2.returncode == 1
    r3 = _run(wd, "check", sub_flags=["--strict"])
    exit_check_strict = r3.returncode == 1

    ok = exit_audit and exit_check and exit_check_strict
    detail = (f"  [c3] audit-exit-1={exit_audit}, check-exit-1={exit_check}, "
              f"check--strict-exit-1={exit_check_strict}")
    return ok, detail + f" → {'PASS' if ok else 'FAIL'}"


def check_clean_passes() -> tuple[bool, str]:
    """audit sobre ledger limpio exit 0."""
    wd = _setup_workdir("c3-clean", "sdm-clean.json", "ledger-clean.json")
    r = _run(wd, "audit")
    ok = r.returncode == 0
    return ok, f"  [c3-clean] clean-exit-0={ok} → {'PASS' if ok else 'FAIL'}"


def check_actionable_list() -> tuple[bool, str]:
    """Cada finding tiene anchor + severity + category + fix."""
    wd = _setup_workdir("c-action", "sdm-clean.json", "ledger-with-omission.json")
    r = _run(wd, "audit")
    report = _load_report(r)
    findings = report.get("findings", [])
    if not findings:
        return False, "  [actionable] FAIL (sin findings para inspeccionar)"
    sample = findings[0]
    required = {"anchor", "severity", "category", "expected", "actual", "fix"}
    has_all = required.issubset(sample.keys())
    anchor_has_type_id = "type" in sample.get("anchor", {}) and "id" in sample.get("anchor", {})
    ok = has_all and anchor_has_type_id
    detail = f"  [actionable] required-fields={has_all}, anchor-shape={anchor_has_type_id}"
    return ok, detail + f" → {'PASS' if ok else 'FAIL'}"


# -------------------------------------------------------------------
# No-regresión.
# -------------------------------------------------------------------

def check_no_regression() -> list[bool]:
    results = []
    r = subprocess.run(
        [sys.executable, str(VALIDATE_LEDGER), "--validate",
         str(REPO / "evals" / "ledger-sample" / "full-coverage.json"),
         str(REPO / "evals" / "ledger-sample" / "mixed-states.json")],
        capture_output=True, text=True,
    )
    ok = r.returncode == 0
    print(f"  [F15] {'PASS' if ok else 'FAIL'}")
    results.append(ok)
    for label, script in [("F37", F37_EVAL), ("F38", F38_EVAL),
                          ("F39", F39_EVAL), ("F40", F40_EVAL),
                          ("F41", F41_EVAL), ("F42", F42_EVAL)]:
        r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
        ok = r.returncode == 0 and "RESULTADO: PASS" in r.stdout
        print(f"  [{label}] {'PASS' if ok else 'FAIL'}")
        results.append(ok)
    return results


def main() -> int:
    print("Fase 43 — eval: auditoría de no-pérdida")
    print()

    print("Criterio 1 — Detecta omisión inyectada:")
    o1, m1 = check_omission_detected()
    print(m1)
    o1m, m1m = check_mutilation_detected()
    print(m1m)
    o1p, m1p = check_pending_detected()
    print(m1p)
    c1_overall = o1 and o1m and o1p
    print(f"  criterio 1 overall: {'PASS' if c1_overall else 'FAIL'}")
    print()

    print("Criterio 2 — Muestreo inverso definido (tamaño y método):")
    o2, m2 = check_inverse_sample_defined()
    print(m2)
    o2d, m2d = check_sample_deterministic()
    print(m2d)
    c2_overall = o2 and o2d
    print(f"  criterio 2 overall: {'PASS' if c2_overall else 'FAIL'}")
    print()

    print("Criterio 3 — No se puede cerrar el trabajo con la auditoría en rojo:")
    o3, m3 = check_exit_code_red()
    print(m3)
    o3c, m3c = check_clean_passes()
    print(m3c)
    oa, ma = check_actionable_list()
    print(ma)
    c3_overall = o3 and o3c and oa
    print(f"  criterio 3 overall: {'PASS' if c3_overall else 'FAIL'}")
    print()

    print("No-regresión:")
    nr = check_no_regression()

    all_ok = c1_overall and c2_overall and c3_overall and all(nr)
    print()
    print(f"RESULTADO: {'PASS' if all_ok else 'FAIL'} "
          f"(c1={c1_overall} c2={c2_overall} c3={c3_overall} "
          f"nr={sum(nr)}/{len(nr)})")

    if TMP.exists():
        shutil.rmtree(TMP)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
