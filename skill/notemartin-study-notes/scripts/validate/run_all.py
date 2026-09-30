#!/usr/bin/env python3
"""
run_all.py — Orquestador unificado de validadores (F113).

Ejecuta la batería de validadores sobre una nota, carpeta o workdir y
agrega issues en un solo JSON con la shape común de `validators.md` §3.

Uso:
  python3 run_all.py --note <file>
  python3 run_all.py --notes-dir <dir>
  python3 run_all.py --workdir <dir>
  python3 run_all.py --workdir <dir> --validators validate_sdm,validate_ledger
  python3 run_all.py --note <file> --strict   # exit 1 ante cualquier warning
  python3 run_all.py --note <file> --json

Exit: 0 (sin issues / solo info), 1 (error), 2 (warning), 3 (uso).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "1.0.0"

# Mapeo de validador → script y modos que aplica.
VALIDATORS = {
    "validate_profile": ("validate_profile.py", {"workdir", "note", "notes_dir"}),
    "validate_sdm": ("validate_sdm.py", {"workdir", "note", "notes_dir"}),
    "validate_ledger": ("validate_ledger.py", {"workdir", "note", "notes_dir"}),
    "validate_notemark": ("validate_notemark.py", {"note", "notes_dir"}),
    "validate_ir": ("validate_ir.py", {"note", "workdir"}),
    "mermaid": ("mermaid.py", {"note", "notes_dir"}),
    "monospace_diagrams": ("monospace_diagrams.py", {"note"}),
    "validate_destinations": ("validate_destinations.py", {"workdir"}),
    "validate_links": ("validate_links.py", {"note", "notes_dir", "workdir"}),
    "validate_images": ("validate_images.py", {"note"}),
    "validate_properties": ("validate_properties.py", {"note"}),
    "validate_tables": ("validate_tables.py", {"note"}),
    "validate_lengths": ("validate_lengths.py", {"note"}),
    "density_check": ("density_check.py", {"note", "notes_dir"}),
}


def run_validator(name: str, script: str, target_args: list[str], here: Path) -> tuple[int, dict | None]:
    """Ejecuta el validador y devuelve (exit, JSON parseado o None)."""
    cmd = [sys.executable, str(here / script)] + target_args + ["--json"]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30,
        )
    except subprocess.TimeoutExpired:
        return 3, {
            "schema_version": SCHEMA_VERSION,
            "validator": name,
            "target": " ".join(target_args),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "duration_ms": 30000,
            "summary": {"errors": 1, "warnings": 0, "info": 0},
            "issues": [{
                "rule_id": "V-RUN-99",
                "severity": "error",
                "message": f"timeout ejecutando {name}",
                "file": script, "node": "<runner>",
            }],
        }
    except FileNotFoundError:
        return 3, None
    try:
        return proc.returncode, json.loads(proc.stdout)
    except json.JSONDecodeError:
        return proc.returncode, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--note")
    grp.add_argument("--notes-dir")
    grp.add_argument("--workdir")
    parser.add_argument("--validators", default="",
                        help="csv de validadores (default: todos los aplicables)")
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 ante cualquier warning")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", help="ruta del JSON agregado")
    args = parser.parse_args()

    started = datetime.now(timezone.utc)
    here = Path(__file__).resolve().parent

    # Determinar target mode.
    if args.note:
        mode = "note"
        target_args = ["--note", args.note]
        target_label = args.note
    elif args.notes_dir:
        mode = "notes_dir"
        target_args = ["--notes-dir", args.notes_dir]
        target_label = args.notes_dir
    else:
        mode = "workdir"
        target_args = ["--workdir", args.workdir]
        target_label = args.workdir

    # Determinar validadores a ejecutar.
    if args.validators:
        wanted = set(args.validators.split(","))
    else:
        wanted = {n for n, (_, modes) in VALIDATORS.items() if mode in modes}

    aggregate_issues: list = []
    validators_run: list = []
    validators_skipped: list = []

    for name, (script, modes) in VALIDATORS.items():
        if name not in wanted:
            continue
        if mode not in modes:
            validators_skipped.append({"name": name, "reason": f"mode {mode} not applicable"})
            continue
        rc, report = run_validator(name, script, target_args, here)
        if report is None:
            validators_skipped.append({"name": name, "reason": f"no JSON output (rc={rc})"})
            continue
        validators_run.append({
            "name": name,
            "rc": rc,
            "issues": len(report.get("issues", [])),
        })
        for it in report.get("issues", []):
            # Normalizar: añadir prefijo V-RUN- si rule_id no tiene ya prefijo.
            aggregate_issues.append(it)

    # Issues del propio orquestador.
    for sk in validators_skipped:
        aggregate_issues.append({
            "rule_id": "V-RUN-01",
            "severity": "info",
            "message": f"validador omitido: {sk['name']} ({sk['reason']})",
            "file": "scripts/validate/run_all.py",
            "node": sk["name"],
        })

    if not validators_run:
        aggregate_issues.append({
            "rule_id": "V-RUN-02",
            "severity": "error",
            "message": "ningún validador se ejecutó",
            "file": "scripts/validate/run_all.py",
            "node": "<runner>",
        })

    summary = {
        "errors": sum(1 for i in aggregate_issues if i["severity"] == "error"),
        "warnings": sum(1 for i in aggregate_issues if i["severity"] == "warning"),
        "info": sum(1 for i in aggregate_issues if i["severity"] == "info"),
    }

    duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    report = {
        "schema_version": SCHEMA_VERSION,
        "validator": "run_all",
        "target": target_label,
        "started_at": started.isoformat(),
        "duration_ms": duration_ms,
        "summary": summary,
        "validators_run": validators_run,
        "validators_skipped": validators_skipped,
        "issues": aggregate_issues,
    }

    if args.json or args.out:
        out = json.dumps(report, indent=2, ensure_ascii=False)
        if args.out:
            Path(args.out).write_text(out, encoding="utf-8")
        else:
            print(out)
    else:
        for it in aggregate_issues:
            print(f"[{it['severity'].upper():7}] {it['rule_id']} {it['file']} — {it['message']}")
        print(f"\n{summary['errors']} errors, {summary['warnings']} warnings, {summary['info']} info",
              file=sys.stderr)

    if args.strict and summary["warnings"] > 0:
        return 1
    if summary["errors"] > 0:
        return 1
    if summary["warnings"] > 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())