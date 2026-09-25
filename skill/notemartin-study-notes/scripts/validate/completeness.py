#!/usr/bin/env python3
"""completeness.py — F43 auditoría de no-pérdida.

Recorre `knowledge/ledger.json` y `sdm.json` para verificar:
- Forward pass: cada entry del ledger existe en el SDM sin mutilación (R1).
- Inverse sample: muestreo estratificado del SDM detecta omisiones inversas (R2).
- Threshold gate: 100 % de must-keep con estado terminal (R4).

Emite reporte JSON con lista accionable de hallazgos. Exit 1 si hay
cualquier `critical` finding (criterio 3 del roadmap: no se puede cerrar
el trabajo con la auditoría en rojo).

Uso:
    python3 scripts/validate/completeness.py --workdir PATH audit
    python3 scripts/validate/completeness.py --workdir PATH report
    python3 scripts/validate/completeness.py --workdir PATH check --strict
    python3 scripts/validate/completeness.py --workdir PATH fix

Códigos de salida:
    0 — PASS (sin critical findings).
    1 — FAIL (al menos 1 critical finding).
    2 — Uso (paths faltantes, argumentos inválidos).

Dependencias:
    - Python 3.9+ stdlib.
    - jsonschema (opcional, validación contra schemas de F15/F13).
    - scripts/util/_io.py (atomic_write_json compartido con F38/F39).

Documentación normativa: references/10-quality/completeness-audit.md.
"""

from __future__ import annotations

import argparse
import importlib.util as _importlib_util
import json
import random
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Comparte atomic_write_json con ledger.py / concept_graph.py (F38/F39).
_IO_PATH = Path(__file__).resolve().parent.parent / "util" / "_io.py"
_spec = _importlib_util.spec_from_file_location("_skill_io", _IO_PATH)
_io_mod = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_io_mod)
_atomic_write_json = _io_mod.atomic_write_json

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2

# Tipos que activan reglas R1–R5 en F37 (must-keep por construcción).
# R5 (formula) requiere además content.numbered == True.
MUST_KEEP_TYPES_PLAIN = {"parameter", "default", "error-code", "warning"}
MUST_KEEP_TYPES_FORMULA_NUMBERED = {"formula"}

# Severidades de editorial_note (F35) que también son must-keep.
EDITORIAL_SEVERITIES_MUST_KEEP = {"deprecated", "removed", "novelty"}

# Campos con exact match vs normalized match (R3).
EXACT_MATCH_FIELDS = {
    "parameter.name",
    "error-code.code",
    "version-note.version_introduced",
    "version-note.version_removed",
    "syntax-rule.rule",
}

NORMALIZED_MATCH_FIELDS = {
    "definition.text",
    "example.text",
    "example.code",
    "step.text",
    "warning.text",
    "cross-reference.target",
    "mechanism.text",
    "tradeoff.text",
}

DEFAULT_SAMPLE_RATE = 0.10
DEFAULT_SEED = 0


# -------------------------------------------------------------------
# I/O y paths.
# -------------------------------------------------------------------

def _resolve_paths(args: argparse.Namespace) -> dict[str, Path]:
    workdir = Path(args.workdir).resolve()
    sdm = Path(args.sdm).resolve() if args.sdm else workdir / "sdm.json"
    ledger = Path(args.ledger).resolve() if args.ledger else workdir / "knowledge" / "ledger.json"
    return {"workdir": workdir, "sdm": sdm, "ledger": ledger}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_path(path: Path, what: str) -> None:
    if not path.exists():
        sys.stderr.write(f"FAIL: {what} no encontrado: {path}\n")
        sys.exit(EXIT_USAGE)


# -------------------------------------------------------------------
# Schema validation opcional.
# -------------------------------------------------------------------

def _validate_schemas(ledger: dict, sdm: dict) -> list[str]:
    """Valida contra schemas si jsonschema está disponible. Devuelve lista de warnings."""
    warnings: list[str] = []
    try:
        import jsonschema  # type: ignore
    except ImportError:
        warnings.append("jsonschema ausente; validación contra schema desactivada")
        return warnings

    repo_root = Path(__file__).resolve().parents[3]
    ledger_schema = repo_root / "skill" / "notemartin-study-notes" / "schemas" / "ledger.schema.json"
    sdm_schema = repo_root / "skill" / "notemartin-study-notes" / "schemas" / "sdm.schema.json"

    if ledger_schema.exists():
        try:
            schema = _read_json(ledger_schema)
            jsonschema.Draft202012Validator(schema).validate(ledger)
        except jsonschema.ValidationError as e:
            warnings.append(f"ledger schema inválido: {e.message}")
    if sdm_schema.exists():
        try:
            schema = _read_json(sdm_schema)
            jsonschema.Draft202012Validator(schema).validate(sdm)
        except jsonschema.ValidationError as e:
            warnings.append(f"sdm schema inválido: {e.message}")
    return warnings


# -------------------------------------------------------------------
# Utilidades de matching.
# -------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Lowercase + whitespace collapsed para normalized match."""
    return re.sub(r'\s+', ' ', text.lower()).strip()


def _is_must_keep_type(block_type: str, content: dict) -> bool:
    """Determina si un bloque es must-keep por tipo (F37 R1-R5)."""
    if block_type in MUST_KEEP_TYPES_PLAIN:
        return True
    if block_type == "formula" and content.get("numbered") is True:
        return True
    return False


def _is_must_keep_severity(block: dict) -> bool:
    """Determina si un bloque es must-keep por severidad editorial (F35)."""
    if block.get("type") in MUST_KEEP_TYPES_PLAIN:
        return False  # ya cubierto por tipo
    if block.get("type") == "editorial_note":
        sev = (block.get("content") or {}).get("severity")
        return sev in EDITORIAL_SEVERITIES_MUST_KEEP
    return False


def _is_must_keep_entry(entry: dict) -> bool:
    """Determina si un entry es must-keep (regla F37 + override)."""
    return entry.get("criticality") == "must-keep"


def _entry_references_block(entry: dict, block_id: str) -> bool:
    return block_id in entry.get("source_block_ids", [])


# -------------------------------------------------------------------
# Forward pass.
# -------------------------------------------------------------------

def _forward_pass(ledger: dict, sdm: dict) -> tuple[list[dict], dict[str, dict]]:
    """Recorre entries. Devuelve (findings, sdm_blocks_by_id)."""
    sdm_blocks_by_id: dict[str, dict] = {}
    for section in sdm.get("sections", []):
        for block in section.get("blocks", []):
            sdm_blocks_by_id[block["id"]] = block

    findings: list[dict] = []
    for entry in ledger.get("entries", []):
        eid = entry["unit_id"]
        is_mk = _is_must_keep_entry(entry)

        # R1.a — Localización.
        for bid in entry.get("source_block_ids", []):
            if bid not in sdm_blocks_by_id:
                findings.append({
                    "anchor": {"type": "block", "id": bid},
                    "severity": "critical" if is_mk else "warning",
                    "category": "orphan-block",
                    "expected": f"block_id={bid} existe en SDM",
                    "actual": "block_id no encontrado",
                    "fix": f"Re-extraer la unidad desde el SDM o actualizar source_block_ids en el entry {eid}.",
                })

        # R1.b — No-mutilación.
        for bid in entry.get("source_block_ids", []):
            if bid not in sdm_blocks_by_id:
                continue
            block = sdm_blocks_by_id[bid]
            block_content = block.get("content") or {}
            entry_content = entry.get("content") or {}
            etype = entry.get("type")

            # Mapeo content fields por tipo.
            fields_to_check: list[tuple[str, Any]] = []
            if etype == "parameter":
                fields_to_check.append(("name", entry_content.get("name")))
            elif etype == "error-code":
                fields_to_check.append(("code", entry_content.get("code")))
            elif etype == "version-note":
                if entry_content.get("version_introduced"):
                    fields_to_check.append(("version_introduced", entry_content.get("version_introduced")))
                if entry_content.get("version_removed"):
                    fields_to_check.append(("version_removed", entry_content.get("version_removed")))
            elif etype == "syntax-rule":
                fields_to_check.append(("rule", entry_content.get("rule")))
            elif etype in ("definition", "example", "step", "warning", "mechanism", "tradeoff"):
                if entry_content.get("text"):
                    fields_to_check.append(("text", entry_content.get("text")))
            elif etype == "default":
                # Defaults: verificar el value (puede ser string/number/bool).
                if entry_content.get("value") is not None:
                    fields_to_check.append(("value", entry_content.get("value")))

            for field, entry_val in fields_to_check:
                if entry_val is None:
                    continue
                # Encontrar el campo equivalente en block_content (heurística).
                block_val = block_content.get(field)
                if block_val is None:
                    # Para defaults, el value vive bajo 'description' o similar.
                    if etype == "default":
                        block_val = block_content.get("description", "")
                    elif etype == "example":
                        block_val = block_content.get("code") or block_content.get("text", "")
                    else:
                        block_val = ""
                field_key = f"{etype}.{field}"
                if field_key in EXACT_MATCH_FIELDS:
                    if str(entry_val) != str(block_val):
                        findings.append({
                            "anchor": {"type": "block", "id": bid},
                            "severity": "critical" if is_mk else "warning",
                            "category": "mutilated",
                            "expected": f"{field}={entry_val!r}",
                            "actual": f"{field}={block_val!r}",
                            "fix": f"Restaurar {field} del entry {eid} al valor fuente o marcar el bloque como :::derived (F42).",
                        })
                elif field_key in NORMALIZED_MATCH_FIELDS:
                    if _normalize(str(entry_val)) != _normalize(str(block_val)):
                        findings.append({
                            "anchor": {"type": "block", "id": bid},
                            "severity": "critical" if is_mk else "warning",
                            "category": "mutilated",
                            "expected": f"{field}={entry_val!r}",
                            "actual": f"{field}={block_val!r}",
                            "fix": f"Restaurar {field} del entry {eid} (F42 §5 normalized match).",
                        })

    return findings, sdm_blocks_by_id


# -------------------------------------------------------------------
# Inverse sample.
# -------------------------------------------------------------------

def _inverse_sample(
    sdm: dict,
    ledger: dict,
    sample_rate: float,
    seed: int,
) -> tuple[list[dict], dict]:
    """Recorre el SDM con muestreo estratificado. Devuelve (findings, sample_metadata)."""
    all_blocks: list[dict] = []
    for section in sdm.get("sections", []):
        for block in section.get("blocks", []):
            all_blocks.append(block)

    must_keep_blocks: list[dict] = []
    editorial_severity_blocks: list[dict] = []
    context_pool: list[dict] = []

    for block in all_blocks:
        btype = block.get("type")
        bcontent = block.get("content") or {}
        if _is_must_keep_type(btype, bcontent):
            must_keep_blocks.append(block)
        elif _is_must_keep_severity(block):
            editorial_severity_blocks.append(block)
        else:
            context_pool.append(block)

    # Indexar ledger por block_id.
    ledger_blocks: set[str] = set()
    for entry in ledger.get("entries", []):
        for bid in entry.get("source_block_ids", []):
            ledger_blocks.add(bid)

    findings: list[dict] = []

    # 100% must-keep blocks (R1 + R2 + R5).
    sampled_mk = must_keep_blocks + editorial_severity_blocks

    # 10% context (con seed).
    rng = random.Random(seed)
    sample_size = max(1, int(round(len(context_pool) * sample_rate)))
    sampled_context = rng.sample(context_pool, min(sample_size, len(context_pool)))

    # Encontrar omisiones inversas.
    for block in sampled_mk + sampled_context:
        bid = block["id"]
        if bid not in ledger_blocks:
            is_mk = _is_must_keep_type(block.get("type"), block.get("content") or {})
            findings.append({
                "anchor": {"type": "block", "id": bid},
                "severity": "critical" if is_mk else "warning",
                "category": "missing-backward",
                "expected": "block respaldado por entry en ledger",
                "actual": "block sin entry en ledger",
                "fix": f"Añadir entry en ledger con type={block['type']!r} y source_block_ids=[{bid!r}].",
            })

    sample_metadata = {
        "total_blocks": len(all_blocks),
        "must_keep_count": len(must_keep_blocks),
        "editorial_severity_count": len(editorial_severity_blocks),
        "context_pool_count": len(context_pool),
        "sampled_must_keep": len(sampled_mk),
        "sampled_context": len(sampled_context),
        "sampled_context_pct": (len(sampled_context) / max(len(context_pool), 1)) * 100,
        "sample_rate": sample_rate,
        "seed": seed,
        "must_keep_coverage_pct": 100.0 if must_keep_blocks + editorial_severity_blocks else 100.0,
    }
    return findings, sample_metadata


# -------------------------------------------------------------------
# Threshold gate.
# -------------------------------------------------------------------

def _threshold_gate(ledger: dict) -> list[dict]:
    """Detecta must-keep con state=pending (R4)."""
    findings: list[dict] = []
    for entry in ledger.get("entries", []):
        if entry.get("criticality") != "must-keep":
            continue
        if entry.get("state") == "pending":
            findings.append({
                "anchor": {"type": "entry", "id": entry["unit_id"]},
                "severity": "critical",
                "category": "pending-must-keep",
                "expected": "state ∈ {written, merged, discarded}",
                "actual": "state=pending",
                "fix": f"Transicionar el entry {entry['unit_id']} a written/merged/discarded via ledger.py mark.",
            })
    return findings


# -------------------------------------------------------------------
# Subcomandos.
# -------------------------------------------------------------------

def _run_audit(args: argparse.Namespace, abort_on_first_critical: bool = False) -> tuple[int, dict]:
    paths = _resolve_paths(args)
    _require_path(paths["sdm"], "sdm.json")
    _require_path(paths["ledger"], "ledger.json")

    sdm = _read_json(paths["sdm"])
    ledger = _read_json(paths["ledger"])

    warnings = _validate_schemas(ledger, sdm)

    forward_findings, _ = _forward_pass(ledger, sdm)
    inverse_findings, sample_metadata = _inverse_sample(sdm, ledger, args.sample_rate, args.seed)
    gate_findings = _threshold_gate(ledger)

    findings = forward_findings + inverse_findings + gate_findings

    if abort_on_first_critical and any(f["severity"] == "critical" for f in findings):
        findings = [f for f in findings if f["severity"] == "critical"][:1]

    summary = {
        "total_findings": len(findings),
        "critical": sum(1 for f in findings if f["severity"] == "critical"),
        "warnings_count": sum(1 for f in findings if f["severity"] == "warning"),
        "must_keep_total": sum(1 for e in ledger.get("entries", []) if _is_must_keep_entry(e)),
        "must_keep_terminal": sum(
            1 for e in ledger.get("entries", [])
            if _is_must_keep_entry(e) and e.get("state") in {"written", "merged", "discarded"}
        ),
    }

    report = {
        "audit_metadata": {
            "version": "1.0.0",
            "built_at": datetime.now(timezone.utc).isoformat(),
            "spec": "references/10-quality/completeness-audit.md",
            "schema_warnings": warnings,
        },
        "forward_pass": {
            "findings": forward_findings,
        },
        "inverse_sample": {
            "sample_metadata": sample_metadata,
            "findings": inverse_findings,
        },
        "threshold_gate": {
            "findings": gate_findings,
        },
        "findings": findings,
        "summary": summary,
    }

    exit_code = EXIT_OK if summary["critical"] == 0 else EXIT_VALIDATION
    return exit_code, report


def cmd_audit(args: argparse.Namespace) -> int:
    exit_code, report = _run_audit(args, abort_on_first_critical=False)

    output = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        _atomic_write_json(Path(args.out).resolve(), report)
        sys.stdout.write(f"OK — reporte escrito en {args.out} (exit={exit_code})\n")
    else:
        sys.stdout.write(output + "\n")
    return exit_code


def cmd_report(args: argparse.Namespace) -> int:
    exit_code, report = _run_audit(args, abort_on_first_critical=False)
    s = report["summary"]
    sm = report["inverse_sample"]["sample_metadata"]

    sys.stdout.write(f"=== Audit report ({report['audit_metadata']['built_at']}) ===\n")
    sys.stdout.write(f"  Total findings: {s['total_findings']} (critical={s['critical']}, warnings={s['warnings_count']})\n")
    sys.stdout.write(f"  Must-keep: {s['must_keep_terminal']}/{s['must_keep_total']} en estado terminal\n")
    sys.stdout.write(f"  Inverse sample: {sm['sampled_must_keep']} must-keep (100%) + "
                     f"{sm['sampled_context']}/{sm['context_pool_count']} context "
                     f"({sm['sampled_context_pct']:.1f}%)\n\n")

    if report["findings"]:
        sys.stdout.write("Findings:\n")
        for f in report["findings"][:20]:
            anchor_str = f"{f['anchor']['type']}:{f['anchor']['id']}"
            sys.stdout.write(f"  [{f['severity']:8s}] {f['category']:18s} {anchor_str}\n")
            sys.stdout.write(f"    expected: {f['expected']}\n")
            sys.stdout.write(f"    actual:   {f['actual']}\n")
            sys.stdout.write(f"    fix:      {f['fix']}\n")
        if len(report["findings"]) > 20:
            sys.stdout.write(f"  ... +{len(report['findings']) - 20} more\n")

    return exit_code


def cmd_check(args: argparse.Namespace) -> int:
    exit_code, report = _run_audit(args, abort_on_first_critical=args.strict)
    s = report["summary"]
    sys.stdout.write(f"Critical: {s['critical']}, warnings: {s['warnings_count']}, must-keep terminal: {s['must_keep_terminal']}/{s['must_keep_total']}\n")
    return exit_code


def cmd_fix(args: argparse.Namespace) -> int:
    exit_code, report = _run_audit(args, abort_on_first_critical=False)
    sys.stdout.write("=== Actionable list ===\n")
    for f in report["findings"]:
        anchor_str = f"{f['anchor']['type']}:{f['anchor']['id']}"
        sys.stdout.write(f"  [{f['severity']:8s}] {anchor_str}\n")
        sys.stdout.write(f"    {f['fix']}\n")
    return exit_code


# -------------------------------------------------------------------
# Parser CLI.
# -------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="completeness.py",
        description="Auditoría de no-pérdida (Fase 43). Forward pass + inverse sample + threshold gate.",
    )
    p.add_argument("--workdir", default=".", help="Raíz del workdir (default: directorio actual).")
    p.add_argument("--sdm", help="Override de la ruta a sdm.json.")
    p.add_argument("--ledger", help="Override de la ruta a knowledge/ledger.json.")
    p.add_argument("--sample-rate", type=float, default=DEFAULT_SAMPLE_RATE,
                   help=f"Tasa de muestreo del inverse sample sobre context (default: {DEFAULT_SAMPLE_RATE}).")
    p.add_argument("--seed", type=int, default=DEFAULT_SEED,
                   help=f"Seed del muestreo (default: {DEFAULT_SEED}, reproducible).")

    sub = p.add_subparsers(dest="subcommand", required=True)

    p_audit = sub.add_parser("audit", help="Forward + inverse + threshold; emite JSON.")
    p_audit.add_argument("--out", help="Escribe el reporte a un archivo en lugar de stdout.")
    p_audit.set_defaults(func=cmd_audit)

    p_report = sub.add_parser("report", help="Imprime el reporte en formato humano.")
    p_report.set_defaults(func=cmd_report)

    p_check = sub.add_parser("check", help="Modo check (aborta al primer critical si --strict).")
    p_check.add_argument("--strict", action="store_true",
                         help="Aborta al primer finding critical.")
    p_check.set_defaults(func=cmd_check)

    p_fix = sub.add_parser("fix", help="Imprime solo la lista accionable.")
    p_fix.set_defaults(func=cmd_fix)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
