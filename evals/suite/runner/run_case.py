#!/usr/bin/env python3
"""run_case.py — Ejecuta un caso de la suite de evals de la skill

Uso:
    python3 run_case.py --case <case.yaml> --run-id <id> [--agent-command <cmd>] [--workdir-root <p>] [--dry-run]

Crea la estructura runs/<run-id>/cases/<case-id>/ con:
  - prompt.txt      copia del prompt enviado
  - stdout.txt      salida cruda del agente (vacío en --dry-run)
  - workdir/        copia del .notes-work/<hash>/ del agente (placeholder en --dry-run)
  - meta.json       run-level metadata

Modos:
  --agent-command CMD   Ejecuta el agente con el prompt; captura stdout; copia workdir.
  --dry-run             No ejecuta agente; crea placeholders. Útil cuando se hace la
                        suite sin tener el agente en producción.

Exit codes:
  0  OK
  1  case YAML inválido
  2  error de ejecución (no se pudo crear el directorio, agente falló, etc.)

Dependencias: PyYAML (rec).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
SUITE_ROOT = REPO_ROOT / "evals" / "suite"
RUNS_ROOT = REPO_ROOT / "evals" / "runs"
WORKDIR_PARENT = REPO_ROOT / ".notes-work"


EXIT_OK = 0
EXIT_USAGE = 1
EXIT_RUNTIME = 2


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        print("ERROR: PyYAML no disponible.", file=sys.stderr)
        sys.exit(EXIT_RUNTIME)
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _validate_case(case: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("id", "corpus_source", "profile", "prompt", "assertions"):
        if key not in case:
            errors.append(f"falta clave obligatoria '{key}'")
    if case.get("profile") not in {"study", "reference", "hybrid"}:
        errors.append(f"profile inválido: {case.get('profile')}")
    a = case.get("assertions") or {}
    auto = a.get("automatic") or []
    if not auto:
        errors.append("assertions.automatic vacío")
    for i, item in enumerate(auto):
        for key in ("id", "type", "spec", "threshold", "validator"):
            if key not in item:
                errors.append(f"assertion automatic[{i}] falta '{key}'")
    return errors


def _prompt_workdir_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


def _skill_fingerprint() -> dict[str, str]:
    skill_root = REPO_ROOT / "skill" / "notemartin-study-notes"

    def _hash_file(p: Path) -> str:
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _hash_dir(p: Path) -> str:
        if not p.exists():
            return ""
        h = hashlib.sha256()
        for f in sorted(p.rglob("*")):
            if f.is_file():
                h.update(f.relative_to(p).as_posix().encode("utf-8"))
                h.update(_hash_file(f).encode("utf-8"))
        return h.hexdigest()

    parts = {
        "skill_md_sha256": _hash_file(skill_root / "SKILL.md"),
        "references_sha256": _hash_dir(skill_root / "references"),
        "schemas_sha256": _hash_dir(skill_root / "schemas"),
        "scripts_sha256": _hash_dir(REPO_ROOT / "scripts"),
    }
    composite = hashlib.sha256("".join(parts.values()).encode("utf-8")).hexdigest()
    parts["composite_sha256"] = composite
    parts["computed_at"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
    return parts


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ejecuta un caso de la suite de evals")
    p.add_argument("--case", required=True, help="Ruta al YAML del caso")
    p.add_argument("--run-id", required=True, help="ID del run (ej. 2026-09-30-r118-001)")
    p.add_argument(
        "--agent-command",
        default=None,
        help="Comando que invoca al agente (recibe el prompt como argumento). "
        "Si falta, modo --dry-run.",
    )
    p.add_argument(
        "--workdir-root",
        default=str(WORKDIR_PARENT),
        help=f"Directorio donde el agente deposita .notes-work/<hash>/ (default {WORKDIR_PARENT})",
    )
    p.add_argument("--model-id", default="unknown", help="Identificador del modelo del agente")
    p.add_argument("--dry-run", action="store_true", help="No invocar agente")
    args = p.parse_args(argv)

    case_path = Path(args.case)
    if not case_path.exists():
        print(f"ERROR: case no encontrado: {case_path}", file=sys.stderr)
        return EXIT_RUNTIME
    case = _load_yaml(case_path)
    errs = _validate_case(case)
    if errs:
        for e in errs:
            print(f"ERROR case: {e}", file=sys.stderr)
        return EXIT_USAGE

    case_id = case["id"]
    run_root = RUNS_ROOT / args.run_id
    case_dir = run_root / "cases" / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    prompt_text = case["prompt"].strip()
    (case_dir / "prompt.txt").write_text(prompt_text + "\n", encoding="utf-8")

    fingerprint = _skill_fingerprint()
    (run_root / "skill_fingerprint.json").write_text(
        json.dumps(fingerprint, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    meta = {
        "run_id": args.run_id,
        "case_id": case_id,
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "skill_version": _git_sha(),
        "model_id": args.model_id,
        "agent_command": args.agent_command or "(dry-run)",
        "dry_run": bool(args.dry_run or not args.agent_command),
    }
    (case_dir / "meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    workdir_dst = case_dir / "workdir"
    if args.agent_command and not args.dry_run:
        cmd_parts = args.agent_command.split() + [prompt_text]
        try:
            result = subprocess.run(
                cmd_parts,
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=600,
            )
            (case_dir / "stdout.txt").write_text(
                (result.stdout or "") + "\n--- stderr ---\n" + (result.stderr or ""),
                encoding="utf-8",
            )
        except subprocess.TimeoutExpired:
            print("ERROR: agente excedió 600s", file=sys.stderr)
            return EXIT_RUNTIME
        except FileNotFoundError as e:
            print(f"ERROR: comando del agente no encontrado: {e}", file=sys.stderr)
            return EXIT_RUNTIME

        expected_workdir = Path(args.workdir_root) / _prompt_workdir_hash(prompt_text)
        if expected_workdir.exists():
            shutil.copytree(expected_workdir, workdir_dst, dirs_exist_ok=True)
        else:
            print(
                f"WARN: workdir esperado no existe: {expected_workdir}",
                file=sys.stderr,
            )
            workdir_dst.mkdir(exist_ok=True)
            (workdir_dst / "MISSING.txt").write_text(
                f"Esperado en: {expected_workdir}\n", encoding="utf-8"
            )
    else:
        workdir_dst.mkdir(exist_ok=True)
        (workdir_dst / "DRY_RUN.txt").write_text(
            "Workdir no producido: --dry-run o sin --agent-command.\n"
            "Para evaluar este caso, coloque manualmente el workdir del agente en "
            "este directorio siguiendo la estructura .notes-work/<hash>/.\n",
            encoding="utf-8",
        )
        (case_dir / "stdout.txt").write_text("(dry-run; no agent executed)\n", encoding="utf-8")

    print(f"OK case={case_id} run={args.run_id} dir={case_dir}")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
