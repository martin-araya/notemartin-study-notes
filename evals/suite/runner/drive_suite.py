#!/usr/bin/env python3
"""drive_suite.py — Lanza los 6 casos de la suite y emite report.json

Forma de uso:
  python3 drive_suite.py --run-id 2026-09-30-r118-001 [--model-id X] [--dry-run]

Ejecuta run_case.py y check_assertions.py sobre los 6 casos en
evals/suite/cases/ y agrega los resultados en report.json siguiendo
evals/suite/SCHEMA.md §3.

Por defecto en --dry-run. Sin agente en producción, los workdirs quedan
con placeholders y las aserciones automáticas se marcan pending o fail
(según haya workdir real o no).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SUITE_ROOT = REPO_ROOT / "evals" / "suite"
RUNS_ROOT = REPO_ROOT / "evals" / "runs"

CASES = [
    "case-01-postgresql-select",
    "case-02-database-internals-concept",
    "case-03-rfc-7231-concurrency",
    "case-04-arxiv-two-column-arch",
    "case-05-iso-sql-tables-config",
    "case-13-internet-archive-scan",
]


def _run(cmd: list[str]) -> tuple[int, str, str]:
    r = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=600)
    return r.returncode, r.stdout, r.stderr


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Lanza la suite completa")
    p.add_argument("--run-id", required=True)
    p.add_argument("--model-id", default="unknown")
    p.add_argument("--agent-command", default=None)
    p.add_argument("--dry-run", action="store_true", default=True)
    args = p.parse_args(argv)

    run_root = RUNS_ROOT / args.run_id
    run_root.mkdir(parents=True, exist_ok=True)

    report_cases: list[dict] = []
    for cid in CASES:
        case_yaml = SUITE_ROOT / "cases" / f"{cid}.yaml"
        if not case_yaml.exists():
            print(f"WARN: caso no encontrado, saltando: {case_yaml}", file=sys.stderr)
            continue
        cmd_run = [
            "python3",
            str(SUITE_ROOT / "runner" / "run_case.py"),
            "--case",
            str(case_yaml),
            "--run-id",
            args.run_id,
            "--model-id",
            args.model_id,
        ]
        if args.agent_command:
            cmd_run += ["--agent-command", args.agent_command]
        else:
            cmd_run += ["--dry-run"]
        rc, out, err = _run(cmd_run)
        print(f"run_case {cid}: exit={rc}")
        if rc != 0:
            print(f"  stderr: {err.strip()[:500]}", file=sys.stderr)

        cmd_check = [
            "python3",
            str(SUITE_ROOT / "runner" / "check_assertions.py"),
            "--case",
            str(case_yaml),
            "--run-dir",
            str(run_root),
        ]
        rc, out, err = _run(cmd_check)
        print(f"check_assertions {cid}: exit={rc}")

        # Cargar assertions.json para el reporte.
        aj = run_root / "cases" / cid / "assertions.json"
        auto = []
        if aj.exists():
            auto = json.loads(aj.read_text(encoding="utf-8")).get("automatic", [])
        report_cases.append(
            {
                "case_id": cid,
                "automatic_pass": sum(1 for a in auto if a.get("passed")),
                "automatic_total": len(auto),
                "automatic_pending": sum(1 for a in auto if a.get("status") == "pending"),
                "human_pending": True,
                "approved": None,
                "notes": "(human evaluation pending; run apply_rubric.py and complete human.json)",
            }
        )

    auto_pass_total = sum(c["automatic_pass"] for c in report_cases)
    auto_total_total = sum(c["automatic_total"] for c in report_cases)
    auto_pending_total = sum(c["automatic_pending"] for c in report_cases)

    report = {
        "schema_version": "1.0.0",
        "run_id": args.run_id,
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "skill_version": _subprocess_git_sha(),
        "model_id": args.model_id,
        "agent_command": args.agent_command or "(dry-run)",
        "dry_run": bool(args.dry_run or not args.agent_command),
        "cases": report_cases,
        "summary": {
            "cases_total": len(report_cases),
            "cases_approved": 0,
            "cases_human_pending": len(report_cases),
            "automatic_pass_rate": (auto_pass_total / auto_total_total) if auto_total_total else 0.0,
            "automatic_pending": auto_pending_total,
        },
    }
    out_path = run_root / "report.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"OK report → {out_path}")
    return 0


def _subprocess_git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(REPO_ROOT),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
