#!/usr/bin/env python3
"""CLI operativo del Coverage Ledger — Fase 38.

Mantiene `knowledge/ledger.json` desde L2: inicializa, añade entradas,
transiciona estados, genera el reporte de cobertura, detecta huérfanos
y gaps, y sincroniza `manifest.json`.

Complementa a `validate_ledger.py` (F15), que sigue siendo el linter
read-only para CI. Justificación: docs/adr/ADR-0002-ledger-split.md.

Spec normativa: `references/03-knowledge/ledger-operativo.md`.

Uso:
    python3 ledger.py --workdir PATH <subcommand> [args]
    python3 ledger.py init [--sdm PATH] [--ledger PATH] [--force]
    python3 ledger.py add --unit-id ID --source-block-ids ID[,ID...]
        --type TYPE [--content JSON] [--section-path PATH]
        [--criticality {must-keep,context}] [--rationale STR]
    python3 ledger.py mark UNIT_ID --state {written,merged,discarded}
        [--target-note NOTE] [--target-section SECTION]
        [--discard-reason REASON]
    python3 ledger.py report
    python3 ledger.py check [--strict] [--include-prose]
    python3 ledger.py manifest [--dry-run]

Códigos:
    0 = OK
    1 = validación (schema, invariantes, --strict)
    2 = uso (paths faltantes, argumentos inválidos)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Ruta del módulo unit_rules (F37/F38 compartido).
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from unit_rules import is_must_keep  # noqa: E402

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2

TERMINAL_STATES = {"written", "merged", "discarded"}
ALLOWED_DISCARD_REASONS = {
    "boilerplate",
    "navigation",
    "out-of-scope-by-user",
    "redundant-with",
}

ALLOWED_TYPES = {
    "definition",
    "mechanism",
    "parameter",
    "default",
    "constraint",
    "step",
    "example",
    "warning",
    "error-code",
    "tradeoff",
    "version-note",
    "syntax-rule",
    "cross-reference",
    "formula",
}


# -------------------------------------------------------------------
# Utilidades I/O con escritura atómica (invariante L-04).
# Compartido con concept_graph.py (F39) vía scripts/util/_io.py.
# -------------------------------------------------------------------

import importlib.util as _importlib_util
_IO_PATH = Path(__file__).resolve().parent / "_io.py"
_spec = _importlib_util.spec_from_file_location("_skill_io", _IO_PATH)
_io_mod = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_io_mod)
_atomic_write_json = _io_mod.atomic_write_json


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_path(path: Path, what: str) -> None:
    if not path.exists():
        sys.stderr.write(f"FAIL: {what} no encontrado: {path}\n")
        sys.exit(EXIT_USAGE)


# -------------------------------------------------------------------
# Resolución de paths.
# -------------------------------------------------------------------

def _resolve_paths(args: argparse.Namespace) -> dict[str, Path]:
    workdir = Path(args.workdir).resolve()
    sdm = Path(args.sdm).resolve() if args.sdm else workdir / "sdm.json"
    ledger = Path(args.ledger).resolve() if args.ledger else workdir / "knowledge" / "ledger.json"
    manifest = (
        Path(args.manifest).resolve()
        if args.manifest
        else workdir / "manifest.json"
    )
    return {"workdir": workdir, "sdm": sdm, "ledger": ledger, "manifest": manifest}


# -------------------------------------------------------------------
# Validación opcional contra schemas/ledger.schema.json.
# -------------------------------------------------------------------

def _validate_ledger(payload: dict) -> list[str]:
    """Valida `payload` contra schemas/ledger.schema.json si jsonschema
    está disponible. Devuelve lista de errores (vacía si OK)."""
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return []  # sin jsonschema, validación opcional

    schema_path = (
        Path(__file__).resolve().parents[3]
        / "schemas"
        / "ledger.schema.json"
    )
    if not schema_path.exists():
        return []
    schema = _read_json(schema_path)
    errors: list[str] = []
    validator = jsonschema.Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(payload), key=lambda e: list(e.absolute_path)):
        errors.append(f"  - schema: {err.message} (path={list(err.absolute_path)})")
    return errors


# -------------------------------------------------------------------
# Subcomando: init
# -------------------------------------------------------------------

def cmd_init(args: argparse.Namespace) -> int:
    paths = _resolve_paths(args)
    _require_path(paths["sdm"], "sdm.json")

    if paths["ledger"].exists() and not args.force:
        sys.stderr.write(f"FAIL: ledger ya existe en {paths['ledger']} (usa --force para sobrescribir)\n")
        return EXIT_VALIDATION

    sdm = _read_json(paths["sdm"])
    source = sdm.get("source", {})

    payload = {
        "schema_version": "2.0.0",
        "source": {
            "id": source.get("id", "<unknown>"),
            "hash": source.get("hash", "0" * 64),
        },
        "entries": [],
    }

    errors = _validate_ledger(payload)
    if errors:
        for e in errors:
            sys.stderr.write(e + "\n")
        return EXIT_VALIDATION

    _atomic_write_json(paths["ledger"], payload)
    sys.stdout.write(f"OK — init {paths['ledger']} (source.id={payload['source']['id']!r}, entries=[])\n")
    return EXIT_OK


# -------------------------------------------------------------------
# Subcomando: add
# -------------------------------------------------------------------

def _parse_block_ids(raw: str) -> list[str]:
    ids = [s.strip() for s in raw.split(",") if s.strip()]
    for bid in ids:
        if not (len(bid) == 12 and all(c in "0123456789abcdef" for c in bid)):
            raise ValueError(f"block_id inválido (sha1 hex 12): {bid!r}")
    return ids


def cmd_add(args: argparse.Namespace) -> int:
    paths = _resolve_paths(args)
    _require_path(paths["ledger"], "ledger.json")

    if args.type not in ALLOWED_TYPES:
        sys.stderr.write(f"FAIL: --type {args.type!r} no está en enum cerrado de 14 tipos\n")
        return EXIT_VALIDATION

    try:
        block_ids = _parse_block_ids(args.source_block_ids)
    except ValueError as e:
        sys.stderr.write(f"FAIL: {e}\n")
        return EXIT_USAGE

    try:
        content = json.loads(args.content) if args.content else {}
    except json.JSONDecodeError as e:
        sys.stderr.write(f"FAIL: --content no es JSON válido: {e}\n")
        return EXIT_USAGE

    unit = {
        "unit_id": args.unit_id,
        "source_block_ids": block_ids,
        "source_section_path": args.section_path or "",
        "type": args.type,
        "content": content,
        "criticality": args.criticality or "context",
        "state": "pending",
    }

    # Aplicación mecánica de R1–R5 (F38 §8).
    rule = is_must_keep(unit)
    if rule and unit["criticality"] != "must-keep":
        if not args.rationale:
            sys.stderr.write(
                f"FAIL: tipo {unit['type']!r} activa regla {rule} → "
                f"criticality debe ser 'must-keep' (o usa --rationale para override)\n"
            )
            return EXIT_VALIDATION
        sys.stderr.write(
            f"WARNING: tipo {unit['type']!r} activa {rule} pero declaraste "
            f"criticality=context con rationale={args.rationale!r} (override aceptado)\n"
        )
        unit["criticality_rationale"] = args.rationale
    elif rule and unit["criticality"] == "must-keep":
        unit["criticality_rationale"] = rule
    elif not rule and unit["criticality"] == "must-keep":
        if not args.rationale:
            sys.stderr.write(
                f"WARNING: tipo {unit['type']!r} no activa regla automática pero "
                f"declaraste must-keep sin --rationale (elevación sin justificación)\n"
            )
        unit["criticality_rationale"] = args.rationale

    ledger = _read_json(paths["ledger"])
    if any(e["unit_id"] == unit["unit_id"] for e in ledger.get("entries", [])):
        sys.stderr.write(f"FAIL: unit_id {unit['unit_id']!r} ya existe en el ledger\n")
        return EXIT_VALIDATION
    ledger.setdefault("entries", []).append(unit)

    errors = _validate_ledger(ledger)
    if errors:
        for e in errors:
            sys.stderr.write(e + "\n")
        return EXIT_VALIDATION

    _atomic_write_json(paths["ledger"], ledger)
    sys.stdout.write(f"OK — add {unit['unit_id']} (type={unit['type']}, criticality={unit['criticality']})\n")
    return EXIT_OK


# -------------------------------------------------------------------
# Subcomando: mark
# -------------------------------------------------------------------

def _validate_discard_reason(reason: str) -> Optional[str]:
    base = reason.split(":", 1)[0] if ":" in reason else reason
    if base not in ALLOWED_DISCARD_REASONS:
        return f"motivo base {base!r} no está en lista cerrada {sorted(ALLOWED_DISCARD_REASONS)}"
    if base == "redundant-with" and ":" not in reason:
        return "redundant-with requiere formato 'redundant-with:<unit_id>'"
    return None


def cmd_mark(args: argparse.Namespace) -> int:
    paths = _resolve_paths(args)
    _require_path(paths["ledger"], "ledger.json")

    if args.state not in {"pending", "written", "merged", "discarded"}:
        sys.stderr.write(f"FAIL: --state {args.state!r} no válido\n")
        return EXIT_VALIDATION

    ledger = _read_json(paths["ledger"])
    target = next((e for e in ledger.get("entries", []) if e["unit_id"] == args.unit_id), None)
    if target is None:
        sys.stderr.write(f"FAIL: unit_id {args.unit_id!r} no encontrado en el ledger\n")
        return EXIT_VALIDATION

    target["state"] = args.state
    if args.state == "discarded":
        if not args.discard_reason:
            sys.stderr.write("FAIL: --state discarded requiere --discard-reason\n")
            return EXIT_VALIDATION
        err = _validate_discard_reason(args.discard_reason)
        if err:
            sys.stderr.write(f"FAIL: discard-reason inválido: {err}\n")
            return EXIT_VALIDATION
        target["discard_reason"] = args.discard_reason
    elif "discard_reason" in target:
        del target["discard_reason"]

    if args.target_note is not None:
        target["target_note"] = args.target_note or None
    if args.target_section is not None:
        target["target_section"] = args.target_section or None

    if target["criticality"] == "must-keep" and target["state"] in TERMINAL_STATES:
        if not target.get("target_note"):
            sys.stderr.write(
                f"FAIL: must-keep en estado terminal sin target_note (L-05)\n"
            )
            return EXIT_VALIDATION

    errors = _validate_ledger(ledger)
    if errors:
        for e in errors:
            sys.stderr.write(e + "\n")
        return EXIT_VALIDATION

    _atomic_write_json(paths["ledger"], ledger)
    sys.stdout.write(f"OK — mark {args.unit_id} → state={args.state}\n")
    return EXIT_OK


# -------------------------------------------------------------------
# Subcomando: report
# -------------------------------------------------------------------

def cmd_report(args: argparse.Namespace) -> int:
    paths = _resolve_paths(args)
    _require_path(paths["ledger"], "ledger.json")
    ledger = _read_json(paths["ledger"])
    entries = ledger.get("entries", []) or []

    by_state: Counter = Counter()
    by_crit_state: Counter = Counter()
    by_reason: Counter = Counter()
    pending_per_section: Counter = Counter()
    mk_total = mk_terminal = 0
    cx_total = cx_terminal = 0

    for e in entries:
        s = e.get("state")
        c = e.get("criticality")
        by_state[s] += 1
        by_crit_state[(c, s)] += 1
        if c == "must-keep":
            mk_total += 1
            if s in TERMINAL_STATES:
                mk_terminal += 1
            elif s == "pending":
                pending_per_section[e.get("source_section_path", "<no-section>")] += 1
        elif c == "context":
            cx_total += 1
            if s in TERMINAL_STATES:
                cx_terminal += 1
        if s == "discarded":
            by_reason[e.get("discard_reason", "<none>")] += 1

    sys.stdout.write(f"Coverage report: {paths['ledger']}\n\n")
    sys.stdout.write("Global\n")
    sys.stdout.write(f"  Total unidades: {len(entries)}\n")
    sys.stdout.write(f"  must-keep: {mk_terminal}/{mk_total} en estado terminal\n")
    sys.stdout.write(f"  context:   {cx_terminal}/{cx_total} en estado terminal\n\n")
    sys.stdout.write("Por estado\n")
    for s in ["pending", "written", "merged", "discarded"]:
        sys.stdout.write(f"  {s:10s}: {by_state.get(s, 0)}\n")
    sys.stdout.write("\nPor motivo de descarte\n")
    for r in sorted(ALLOWED_DISCARD_REASONS | set(by_reason.keys())):
        sys.stdout.write(f"  {r:30s}: {by_reason.get(r, 0)}\n")
    sys.stdout.write("\nTop secciones con must-keep pending\n")
    for section, n in sorted(pending_per_section.items(), key=lambda x: -x[1])[:5]:
        sys.stdout.write(f"  {section:40s}: {n}\n")
    return EXIT_OK


# -------------------------------------------------------------------
# Subcomando: check
# -------------------------------------------------------------------

def _collect_sdm_block_ids(sdm: dict, include_prose: bool) -> set[str]:
    ids: set[str] = set()
    for section in sdm.get("sections", []):
        for block in section.get("blocks", []):
            if not include_prose and block.get("type") == "prose":
                continue
            ids.add(block["id"])
    return ids


def _collect_ledger_block_ids(ledger: dict) -> set[str]:
    ids: set[str] = set()
    for entry in ledger.get("entries", []):
        for bid in entry.get("source_block_ids", []):
            ids.add(bid)
    return ids


def cmd_check(args: argparse.Namespace) -> int:
    paths = _resolve_paths(args)
    _require_path(paths["sdm"], "sdm.json")
    _require_path(paths["ledger"], "ledger.json")

    sdm = _read_json(paths["sdm"])
    ledger = _read_json(paths["ledger"])

    sdm_ids = _collect_sdm_block_ids(sdm, args.include_prose)
    ledger_ids = _collect_ledger_block_ids(ledger)

    orphans: list[tuple[str, str]] = []  # (unit_id, block_id)
    for entry in ledger.get("entries", []):
        for bid in entry.get("source_block_ids", []):
            if bid not in sdm_ids:
                orphans.append((entry["unit_id"], bid))

    gaps = sorted(sdm_ids - ledger_ids)

    sys.stdout.write(f"Check report: {paths['ledger']} vs {paths['sdm']}\n")
    sys.stdout.write(f"  Huérfanas (entries con block_id inexistente en SDM): {len(orphans)}\n")
    for unit_id, bid in orphans:
        sys.stdout.write(f"    - {unit_id} → {bid}\n")
    sys.stdout.write(f"  Sin respaldo (bloques del SDM sin entry): {len(gaps)}\n")
    for bid in gaps:
        sys.stdout.write(f"    - {bid}\n")

    has_issues = bool(orphans) or bool(gaps)
    if has_issues and args.strict:
        sys.stdout.write("\nFAIL: --strict activado y hay desviaciones\n")
        return EXIT_VALIDATION
    return EXIT_OK


# -------------------------------------------------------------------
# Subcomando: manifest
# -------------------------------------------------------------------

def cmd_manifest(args: argparse.Namespace) -> int:
    paths = _resolve_paths(args)
    _require_path(paths["ledger"], "ledger.json")
    _require_path(paths["manifest"], "manifest.json")

    ledger = _read_json(paths["ledger"])
    manifest = _read_json(paths["manifest"])

    units_processed = sum(
        1 for e in ledger.get("entries", []) if e.get("state") in TERMINAL_STATES
    )
    last_modified = datetime.now(timezone.utc).isoformat()

    patch = {
        "units_processed": units_processed,
        "last_modified": last_modified,
    }

    if args.dry_run:
        sys.stdout.write(f"Manifest patch (dry-run) sobre {paths['manifest']}:\n")
        for k, v in patch.items():
            old = manifest.get(k, "<ausente>")
            sys.stdout.write(f"  {k}: {old!r} → {v!r}\n")
        return EXIT_OK

    manifest.update(patch)
    _atomic_write_json(paths["manifest"], manifest)
    sys.stdout.write(
        f"OK — manifest actualizado: units_processed={units_processed}, last_modified={last_modified}\n"
    )
    return EXIT_OK


# -------------------------------------------------------------------
# Parser CLI
# -------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ledger.py",
        description="CLI operativo del Coverage Ledger (Fase 38). Mantiene knowledge/ledger.json desde L2.",
    )
    p.add_argument("--workdir", default=".", help="Raíz del workdir (default: directorio actual).")
    p.add_argument("--sdm", help="Override de la ruta a sdm.json (relativa a --workdir o absoluta).")
    p.add_argument("--ledger", help="Override de la ruta a knowledge/ledger.json.")
    p.add_argument("--manifest", help="Override de la ruta a manifest.json.")

    sub = p.add_subparsers(dest="subcommand", required=True)

    p_init = sub.add_parser("init", help="Crea ledger.json vacío a partir del SDM.")
    p_init.add_argument("--force", action="store_true", help="Sobrescribe si ya existe.")
    p_init.set_defaults(func=cmd_init)

    p_add = sub.add_parser("add", help="Añade una entrada al ledger.")
    p_add.add_argument("--unit-id", required=True)
    p_add.add_argument("--source-block-ids", required=True,
                       help="Lista separada por comas de block_id sha1 hex 12.")
    p_add.add_argument("--type", required=True, choices=sorted(ALLOWED_TYPES))
    p_add.add_argument("--content", help="JSON con el contenido de la unidad.")
    p_add.add_argument("--section-path", help="Ruta canónica de la sección.")
    p_add.add_argument("--criticality", choices=["must-keep", "context"])
    p_add.add_argument("--rationale", help="Texto libre (obligatorio en override de regla automática o elevación).")
    p_add.set_defaults(func=cmd_add)

    p_mark = sub.add_parser("mark", help="Transiciona el estado de una entrada.")
    p_mark.add_argument("unit_id")
    p_mark.add_argument("--state", required=True, choices=["pending", "written", "merged", "discarded"])
    p_mark.add_argument("--target-note", help="Asigna target_note (vacío para limpiar).")
    p_mark.add_argument("--target-section", help="Asigna target_section (vacío para limpiar).")
    p_mark.add_argument("--discard-reason",
                        help="Motivo del descarte (lista cerrada; 'redundant-with:<unit_id>' para fusionar).")
    p_mark.set_defaults(func=cmd_mark)

    p_report = sub.add_parser("report", help="Imprime el reporte de cobertura.")
    p_report.set_defaults(func=cmd_report)

    p_check = sub.add_parser("check", help="Detecta huérfanos y contenido sin respaldo.")
    p_check.add_argument("--strict", action="store_true", help="Exit 1 si hay desviaciones.")
    p_check.add_argument("--include-prose", action="store_true",
                         help="Cuenta bloques 'prose' como gap potencial.")
    p_check.set_defaults(func=cmd_check)

    p_manifest = sub.add_parser("manifest", help="Parchea manifest.json con units_processed + last_modified.")
    p_manifest.add_argument("--dry-run", action="store_true", help="Imprime el patch sin escribir.")
    p_manifest.set_defaults(func=cmd_manifest)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
