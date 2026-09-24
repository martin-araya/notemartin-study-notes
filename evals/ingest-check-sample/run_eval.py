#!/usr/bin/env python3
"""run_eval.py — F30 eval: validates the 3 criteria of the roadmap.

Uso:
    python3 evals/ingest-check-sample/run_eval.py

Criterios verificados:
  1. Detecta una página omitida deliberadamente.
  2. Lista secciones del índice ausentes en el SDM.
  3. La puerta bloquea con anomalías críticas.

Códigos de salida:
    0 — PASS los 3 criterios
    1 — Algún FAIL
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = ROOT / "evals" / "ingest-check-sample" / "scenarios"
EXPECTED = ROOT / "evals" / "ingest-check-sample" / "expected"
SCRIPT = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "validate" / "ingest_check.py"

PY = sys.executable


def _run_pipeline(scenario: Path, out_dir: Path, allow_critical: bool = False) -> Tuple[int, Dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    declared = scenario / "declared-index.json"
    cmd = [PY, str(SCRIPT), "--sdm", str(scenario),
           "--out-dir", str(out_dir), "--json-only"]
    if declared.exists():
        cmd += ["--declared-index", str(declared)]
    if allow_critical:
        cmd += ["--allow-critical", "--human-decision", "evaluated manually by reviewer"]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if res.returncode not in (0, 1, 2):
        raise RuntimeError(f"ingest_check failed (exit {res.returncode}): {res.stderr}")
    report_path = out_dir / "validation_report.json"
    return res.returncode, json.loads(report_path.read_text(encoding="utf-8"))


def _criterion_1_missing_page(work: Path) -> Tuple[bool, str]:
    expected = json.loads((EXPECTED / "missing-page.json").read_text(encoding="utf-8"))
    out = work / "missing-page"
    rc, report = _run_pipeline(SCENARIOS / "sdm-with-missing-page", out)
    expected_missing = expected["criterion_1_missing_page_detected"]["expected_missing_pages"]
    actual_missing = report.get("totals", {}).get("missing_pages", [])
    if actual_missing != expected_missing:
        return False, f"missing_pages mismatch: expected {expected_missing}, got {actual_missing}"
    msg = f"missing_pages correctly detected: {actual_missing}"
    return True, msg


def _criterion_2_missing_section(work: Path) -> Tuple[bool, str]:
    expected = json.loads((EXPECTED / "missing-section.json").read_text(encoding="utf-8"))
    out = work / "missing-section"
    rc, report = _run_pipeline(SCENARIOS / "sdm-with-missing-section", out)
    expected_missing = set(expected["criterion_2_missing_sections_listed"]["expected_missing_sections"])
    actual_missing = set(report.get("totals", {}).get("missing_sections", []))
    if not expected_missing.issubset(actual_missing):
        return False, f"missing_sections does not include {expected_missing}; got {actual_missing}"
    msg = f"missing_sections correctly listed: {sorted(actual_missing)}"
    return True, msg


def _criterion_3_blocking_gate(work: Path) -> Tuple[bool, str]:
    expected = json.loads((EXPECTED / "blocking.json").read_text(encoding="utf-8"))
    out = work / "critical"
    rc, report = _run_pipeline(SCENARIOS / "sdm-critical", out)
    expected_rc = expected["criterion_3_gate_blocks_critical"]["expected_exit_code"]
    if rc != expected_rc:
        return False, f"exit_code={rc} (expected {expected_rc})"
    critical_count = len(report.get("anomalies", {}).get("critical", []))
    if critical_count < 1:
        return False, f"no critical anomalies detected (got {critical_count})"
    msg = f"BLOCKED with exit={rc}, critical_count={critical_count}"
    return True, msg


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="F30 eval runner")
    args = parser.parse_args(argv)

    total_passed = 0
    total_failed = 0
    failed_msgs: List[str] = []

    with tempfile.TemporaryDirectory(prefix="ingest-check-eval-") as tmp:
        work = Path(tmp)
        for label, fn in (
            ("Criterion 1 (missing page detected)", _criterion_1_missing_page),
            ("Criterion 2 (missing sections listed)", _criterion_2_missing_section),
            ("Criterion 3 (gate blocks critical)", _criterion_3_blocking_gate),
        ):
            print(f"=== {label} ===")
            ok, msg = fn(work)
            tag = "PASS" if ok else "FAIL"
            print(f"  [{tag}] {msg}")
            if ok:
                total_passed += 1
            else:
                total_failed += 1
                failed_msgs.append(f"{label}: {msg}")

    print("")
    print(f"Resultado: {total_passed} PASS, {total_failed} FAIL")
    if failed_msgs:
        print("Fallos:")
        for f in failed_msgs:
            print(f"  - {f}")
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
