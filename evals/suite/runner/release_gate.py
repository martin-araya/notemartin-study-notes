#!/usr/bin/env python3
"""release_gate.py — Evalúa si un release cumple las 4 condiciones del gate (F119)

Forma de uso:
  python3 release_gate.py \
    --candidate runs/v0.1.0/report.json \
    --baseline runs/v0.0.0/report.json \
    --variance runs/v0.1.0/variance.json \
    --regression-set evals/regression/SET.md \
    --out runs/v0.1.0/gate.json

Las 4 condiciones (variance.md §6):
  1. variance.json.summary.cases_fail == 0
  2. variance.json.summary.blocking_failures == []
  3. compare_runs(candidate, baseline): ningún caso del set pasa approved=true -> approved=false
  4. candidate.report.json.cases_human_pending == 0

Exit codes:
  0  PASS — todas las condiciones satisfechas
  1  FAIL — alguna condición violada
  2  error de uso / archivos faltantes

Dependencias: PyYAML (rec); stdlib puro para el resto.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
SUITE_ROOT = REPO_ROOT / "evals" / "suite"

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2


def _load(path: Path) -> Any:
    if not path.exists():
        print(f"ERROR: archivo no encontrado: {path}", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _set_of_case_ids(regression_set_md: Path) -> set[str]:
    """Lee SET.md y extrae los case_id de la tabla §1."""
    if not regression_set_md.exists():
        return set()
    text = regression_set_md.read_text(encoding="utf-8")
    ids: set[str] = set()
    for m in __import__("re").finditer(r"\|\s*`(case-[a-z0-9-]+)`\s*\|", text):
        ids.add(m.group(1))
    return ids


def _index_report(report: dict) -> dict[str, dict]:
    return {c["case_id"]: c for c in report.get("cases", [])}


def _compare_runs(candidate_path: Path, baseline_path: Path, out_dir: Path) -> dict:
    """Invoca compare_runs.py (F118) y devuelve el diff."""
    cmd = [
        "python3",
        str(SUITE_ROOT / "runner" / "compare_runs.py"),
        str(baseline_path.parent),
        str(candidate_path.parent),
    ]
    r = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        print(f"WARN: compare_runs exit={r.returncode}: {r.stderr.strip()[:200]}", file=sys.stderr)
    diff_path = out_dir / "diff.json"
    if diff_path.exists():
        with diff_path.open(encoding="utf-8") as f:
            return json.load(f)
    return {}


def _condition_variance(variance: dict) -> tuple[bool, str]:
    s = variance.get("summary", {})
    if s.get("cases_fail", 0) != 0:
        return False, f"condition 1 (variance_within_threshold): cases_fail={s.get('cases_fail')}"
    return True, "variance_within_threshold OK"


def _condition_blocking(variance: dict) -> tuple[bool, str]:
    s = variance.get("summary", {})
    bf = s.get("blocking_failures", [])
    if bf:
        return False, f"condition 2 (no_blocking_failures): {bf}"
    return True, "no_blocking_failures OK"


def _condition_no_regression(
    diff: dict, regression_set_ids: set[str], cand_idx: dict, base_idx: dict
) -> tuple[bool, str]:
    if not regression_set_ids:
        return True, "no_regression_flip OK (sin set de regresión declarado)"
    for cid in regression_set_ids:
        base = base_idx.get(cid)
        cand = cand_idx.get(cid)
        if base is None or cand is None:
            continue  # caso nuevo en candidate, no es flip
        if base.get("approved") is True and cand.get("approved") is False:
            return False, f"condition 3 (no_regression_flip): {cid} pasó approved=true → false"
    return True, "no_regression_flip OK"


def _condition_no_human_pending(report: dict) -> tuple[bool, str]:
    pending = report.get("summary", {}).get("cases_human_pending", 0)
    if pending > 0:
        return False, f"condition 4 (no_human_pending): {pending} casos sin evaluación humana"
    return True, "no_human_pending OK"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Evalúa el gate de release")
    p.add_argument("--candidate", required=True, help="Ruta a runs/<tag>/report.json")
    p.add_argument("--baseline", required=False, default=None, help="Ruta a runs/<prev>/report.json (opcional para primer release)")
    p.add_argument("--variance", required=True, help="Ruta a runs/<tag>/variance.json")
    p.add_argument("--regression-set", default=str(REPO_ROOT / "evals" / "regression" / "SET.md"))
    p.add_argument("--out", required=True, help="Ruta donde escribir gate.json")
    args = p.parse_args(argv)

    cand_report_path = Path(args.candidate)
    baseline_report_path = Path(args.baseline) if args.baseline else None
    variance_path = Path(args.variance)
    out_path = Path(args.out)

    def _to_rel(p: Path) -> str:
        try:
            return str(p.relative_to(REPO_ROOT))
        except ValueError:
            return p.as_posix()

    cand_report = _load(cand_report_path)
    variance = _load(variance_path)
    base_report = _load(baseline_report_path) if baseline_report_path else None

    regression_ids = _set_of_case_ids(Path(args.regression_set))

    # Condición 3: comparar contra baseline si existe.
    if base_report is not None and baseline_report_path is not None:
        diff = _compare_runs(cand_report_path, baseline_report_path, cand_report_path.parent)
        base_idx = _index_report(base_report)
    else:
        diff = {}
        base_idx = {}

    cand_idx = _index_report(cand_report)

    checks = []
    checks.append(_condition_variance(variance))
    checks.append(_condition_blocking(variance))
    checks.append(_condition_no_regression(diff, regression_ids, cand_idx, base_idx))
    checks.append(_condition_no_human_pending(cand_report))

    reasons = []
    passed = True
    for ok, msg in checks:
        if not ok:
            passed = False
            reasons.append(msg)
    status = "pass" if passed else "fail"

    gate = {
        "schema_version": "1.0.0",
        "candidate": _to_rel(cand_report_path),
        "baseline": _to_rel(baseline_report_path) if baseline_report_path else None,
        "variance": _to_rel(variance_path),
        "status": status,
        "checks": [{"ok": ok, "message": msg} for ok, msg in checks],
        "reasons": reasons,
        "regression_set_size": len(regression_ids),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(gate, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"gate: {status} → {out_path}")
    for ok, msg in checks:
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {msg}")

    return EXIT_OK if passed else EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
