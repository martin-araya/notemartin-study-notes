#!/usr/bin/env python3
"""run_regression.py — Ejecuta N veces cada caso del set de regresión y mide varianza

Forma de uso:
  python3 run_regression.py \
    --case-dir evals/regression/cases/ \
    --n-runs 5 \
    --agent-command "<cmd>" \
    --thresholds evals/regression/variance_thresholds.yaml \
    --release-tag v0.1.0 \
    --out-dir evals/runs/v0.1.0/

Por cada caso en --case-dir, invoca --run-case.py (F118) con --run-suffix -i
para producir ejecuciones aisladas. Después evalúa métricas y compara contra
los umbrales. Emite --out-dir/variance.json con la forma canónica de
evals/regression/variance.md §5.

Modos:
  --dry-run             No invoca el agente; emite variance.json con métricas
                        en null y approved_rate = 0. Útil para CI sin agente.

Exit codes:
  0  variance dentro de umbral
  1  alguna métrica cae fuera (candidates fail)
  2  error de uso / case inválido
  3  error de runtime (validator no encontrado, etc.)

Dependencias: PyYAML (rec); invoca run_case.py / check_assertions.py /
apply_rubric.py de F118 vía subprocess.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
SUITE_ROOT = REPO_ROOT / "evals" / "suite"
DEFAULT_CASE_DIR = REPO_ROOT / "evals" / "regression" / "cases"
DEFAULT_THRESHOLDS = REPO_ROOT / "evals" / "regression" / "variance_thresholds.yaml"

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2
EXIT_RUNTIME = 3


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        print("ERROR: PyYAML no disponible.", file=sys.stderr)
        sys.exit(EXIT_RUNTIME)
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _save_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def _resolve_case_path(case_yaml: Path) -> tuple[Path, dict]:
    """Devuelve (ruta al caso efectivo a ejecutar, dict del caso). Si es un
    .ref.yaml, desreferencia y carga el caso referenciado."""
    case = _load_yaml(case_yaml)
    if "ref" in case and isinstance(case["ref"], dict):
        ref_path = REPO_ROOT / case["ref"]["case_yaml"]
        if not ref_path.exists():
            raise FileNotFoundError(f"referenced case no encontrado: {ref_path}")
        return ref_path, _load_yaml(ref_path)
    return case_yaml, case


def _invoke(cmd: list[str], timeout: int = 600) -> tuple[int, str, str]:
    r = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _stats(values: list[float]) -> dict[str, Any]:
    """mean, stdev, min, max, range para una lista de valores."""
    if not values:
        return {"values": [], "mean": None, "stdev": None, "min": None, "max": None, "range": None}
    n = len(values)
    mean = sum(values) / n
    if n > 1:
        var = sum((v - mean) ** 2 for v in values) / (n - 1)
        stdev = var ** 0.5
    else:
        stdev = 0.0
    mn = min(values)
    mx = max(values)
    return {
        "values": values,
        "mean": round(mean, 4),
        "stdev": round(stdev, 4),
        "min": mn,
        "max": mx,
        "range": round(mx - mn, 4),
    }


def _extract_metrics(run_dir: Path, case_id: str) -> dict[str, Any]:
    """Lee los artefactos de una ejecución y extrae las 5 métricas."""
    workdir = run_dir / "cases" / case_id / "workdir"
    metrics: dict[str, Any] = {
        "coverage_must_keep_terminal": None,
        "notes_planned": None,
        "ir_node_count": 0,
        "human_global": None,
        "approved": False,
    }

    # M1: coverage_must_keep_terminal desde ledger.
    ledger_path = workdir / "knowledge" / "ledger.json"
    if ledger_path.exists():
        try:
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            entries = ledger.get("entries") or []
            must_keep = [e for e in entries if e.get("criticality") == "must-keep"]
            terminal = [e for e in must_keep if e.get("state") in {"written", "merged", "discarded"}]
            total = len(must_keep)
            if total:
                metrics["coverage_must_keep_terminal"] = round(len(terminal) / total, 4)
        except (json.JSONDecodeError, OSError):
            pass

    # M2: notes_planned desde note-plan.json (F44).
    note_plan = workdir / "knowledge" / "note-plan.json"
    if note_plan.exists():
        try:
            plan = json.loads(note_plan.read_text(encoding="utf-8"))
            notes = plan.get("notes") or []
            metrics["notes_planned"] = len(notes)
        except (json.JSONDecodeError, OSError):
            pass

    # M3: ir_node_count = suma de nodos en ir/*.json.
    ir_files = list((workdir / "ir").glob("*.json")) if (workdir / "ir").exists() else []
    total_nodes = 0
    for f in ir_files:
        try:
            ir = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(ir, list):
                total_nodes += len(ir)
            elif isinstance(ir, dict):
                # Convenciones: blocks | nodes | entries.
                for key in ("blocks", "nodes", "entries"):
                    if key in ir and isinstance(ir[key], list):
                        total_nodes += len(ir[key])
                        break
                else:
                    total_nodes += 1
        except (json.JSONDecodeError, OSError):
            pass
    metrics["ir_node_count"] = total_nodes

    # M4: human_global desde human.json.
    human_path = run_dir / "cases" / case_id / "human.json"
    if human_path.exists():
        try:
            h = json.loads(human_path.read_text(encoding="utf-8"))
            metrics["human_global"] = h.get("global_score")
            metrics["approved"] = bool(h.get("approved"))
        except (json.JSONDecodeError, OSError):
            pass

    return metrics


def _within_threshold(metric: str, stats: dict, threshold_cfg: dict) -> bool:
    """Compara las stats de una métrica contra su threshold del YAML."""
    stdev = stats.get("stdev")
    mean = stats.get("mean")
    if metric == "coverage_must_keep_terminal":
        return stdev is not None and stdev <= float(threshold_cfg.get("max_stdev", 0.05))
    if metric == "notes_planned":
        return stdev is not None and stdev <= float(threshold_cfg.get("max_stdev", 1))
    if metric == "ir_node_count":
        if mean is None or stdev is None or mean == 0:
            return True
        ratio = stdev / mean
        return ratio <= float(threshold_cfg.get("max_stdev_ratio", 0.10))
    if metric == "human_global_avg":
        return stdev is not None and stdev <= float(threshold_cfg.get("max_stdev", 0.5))
    if metric == "approved_rate":
        v = stats.get("mean")
        return v is not None and v >= float(threshold_cfg.get("min_value", 1.0))
    return False


def _run_single(
    case_yaml: Path,
    case_id: str,
    run_id: str,
    i: int,
    agent_command: str | None,
    dry_run: bool,
) -> dict[str, Any]:
    """Ejecuta el caso una vez y devuelve las métricas."""
    suffix_run_id = f"{run_id}-run-{i}"
    cmd_run = [
        "python3",
        str(SUITE_ROOT / "runner" / "run_case.py"),
        "--case",
        str(case_yaml),
        "--run-id",
        suffix_run_id,
        "--model-id",
        "regression-eval",
    ]
    if agent_command and not dry_run:
        cmd_run += ["--agent-command", agent_command]
    else:
        cmd_run += ["--dry-run"]

    rc, _, err = _invoke(cmd_run)
    if rc != 0:
        print(f"  WARN run-{i} exit={rc}: {err.strip()[:200]}", file=sys.stderr)

    cmd_check = [
        "python3",
        str(SUITE_ROOT / "runner" / "check_assertions.py"),
        "--case",
        str(case_yaml),
        "--run-dir",
        str(REPO_ROOT / "evals" / "runs" / suffix_run_id),
    ]
    _invoke(cmd_check)  # exit != 0 es normal en dry-run

    cmd_rubric = [
        "python3",
        str(SUITE_ROOT / "runner" / "apply_rubric.py"),
        "--case",
        str(case_yaml),
        "--rubric",
        str(REPO_ROOT / "evals" / "rubric.md"),
        "--out",
        str(REPO_ROOT / "evals" / "runs" / suffix_run_id / "cases" / case_id / "human.json"),
    ]
    _invoke(cmd_rubric)

    metrics = _extract_metrics(REPO_ROOT / "evals" / "runs" / suffix_run_id, case_id)
    return metrics


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ejecuta el set de regresión N veces y mide varianza")
    p.add_argument("--case-dir", default=str(DEFAULT_CASE_DIR), help="Directorio con YAMLs de casos")
    p.add_argument("--thresholds", default=str(DEFAULT_THRESHOLDS))
    p.add_argument("--n-runs", type=int, default=None, help="Override de n_runs (default: YAML)")
    p.add_argument("--release-tag", required=True, help="Tag del release (e.g. v0.1.0)")
    p.add_argument("--out-dir", required=True, help="Directorio donde emitir variance.json")
    p.add_argument("--agent-command", default=None)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--keep-runs", action="store_true", help="No borrar runs/<release-tag>-run-N tras medir")
    args = p.parse_args(argv)

    case_dir = Path(args.case_dir)
    if not case_dir.exists():
        print(f"ERROR: case-dir no existe: {case_dir}", file=sys.stderr)
        return EXIT_USAGE

    thresholds_path = Path(args.thresholds)
    if not thresholds_path.exists():
        print(f"ERROR: thresholds no existe: {thresholds_path}", file=sys.stderr)
        return EXIT_USAGE
    thresholds = _load_yaml(thresholds_path)
    n_runs = args.n_runs if args.n_runs is not None else int(thresholds.get("n_runs", 5))

    case_files = sorted(case_dir.glob("*.yaml"))
    if not case_files:
        print(f"ERROR: sin casos en {case_dir}", file=sys.stderr)
        return EXIT_USAGE

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cases_results: list[dict] = []
    summary = {"cases_total": 0, "cases_pass": 0, "cases_fail": 0, "blocking_failures": []}

    for cf in case_files:
        try:
            effective_case_yaml, case_obj = _resolve_case_path(cf)
        except (FileNotFoundError, OSError) as e:
            print(f"ERROR: {cf}: {e}", file=sys.stderr)
            return EXIT_RUNTIME

        case_id = case_obj.get("id", cf.stem)
        print(f"[{case_id}]")

        per_run_metrics: list[dict] = []
        for i in range(1, n_runs + 1):
            m = _run_single(
                effective_case_yaml,
                case_id,
                args.release_tag,
                i,
                args.agent_command,
                args.dry_run,
            )
            per_run_metrics.append(m)
            print(
                f"  run-{i}: cov={m['coverage_must_keep_terminal']} "
                f"notes={m['notes_planned']} ir={m['ir_node_count']} "
                f"human={m['human_global']} approved={m['approved']}"
            )

        # Calcular stats por métrica.
        threshold_cfg = thresholds.get("metrics", {})
        metric_results: dict[str, Any] = {}
        within_flags: list[bool] = []
        for metric_name in [
            "coverage_must_keep_terminal",
            "notes_planned",
            "ir_node_count",
            "human_global_avg",
            "approved_rate",
        ]:
            if metric_name == "approved_rate":
                vals = [1.0 if m["approved"] else 0.0 for m in per_run_metrics]
            elif metric_name == "human_global_avg":
                vals = [m["human_global"] if m["human_global"] is not None else 0.0 for m in per_run_metrics]
            else:
                vals = [m[metric_name] if m[metric_name] is not None else 0.0 for m in per_run_metrics]
            stats = _stats(vals)
            cfg = threshold_cfg.get(metric_name, {})
            within = _within_threshold(metric_name, stats, cfg)
            within_flags.append(within)
            stats["within_threshold"] = within
            stats["threshold"] = cfg
            metric_results[metric_name] = stats

        passes = all(within_flags)
        approved_values = [bool(m["approved"]) for m in per_run_metrics]
        approved_rate = sum(approved_values) / len(approved_values) if approved_values else 0.0

        cases_results.append(
            {
                "case_id": case_id,
                "metrics": metric_results,
                "approved": approved_values,
                "approved_rate": round(approved_rate, 4),
                "passes_regression": passes,
            }
        )
        summary["cases_total"] += 1
        if passes:
            summary["cases_pass"] += 1
        else:
            summary["cases_fail"] += 1
            summary["blocking_failures"].append(case_id)
        print(f"  → passes_regression={passes}")

    payload = {
        "schema_version": "1.0.0",
        "release_tag": args.release_tag,
        "n_runs": n_runs,
        "thresholds_applied": _hash_file(thresholds_path),
        "thresholds_path": str(thresholds_path.relative_to(REPO_ROOT)),
        "dry_run": bool(args.dry_run or not args.agent_command),
        "cases": cases_results,
        "summary": summary,
    }
    out_path = out_dir / "variance.json"
    _save_json(out_path, payload)
    print(f"\nOK variance → {out_path}")
    print(f"   cases_total={summary['cases_total']} pass={summary['cases_pass']} fail={summary['cases_fail']}")
    return EXIT_OK if summary["cases_fail"] == 0 else EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
