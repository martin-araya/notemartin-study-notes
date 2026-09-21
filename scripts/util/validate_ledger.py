#!/usr/bin/env python3
"""Valida ledgers contra `schemas/ledger.schema.json` y los criterios del roadmap.

Uso:
    python3 validate_ledger.py --validate <ledger.json> [<ledger.json> ...]
    python3 validate_ledger.py --coverage <ledger.json>
    python3 validate_ledger.py --query <ledger.json> <section_path>
    python3 validate_ledger.py --help

Modos:
    --validate   Schema + criterio 1 (must-keep terminal) + criterio 2 (discard_reason
                 en lista cerrada). Schema ya enforza criterio 2 vía regex; el script
                 añade mensaje claro en caso de fallo.
                 exit 0 + "OK <path>" por archivo si pasa.
                 exit 1 si falla.

    --coverage   Imprime reporte global / por estado / por motivo / top secciones
                 con must-keep pending.
                 exit 0.

    --query      Imprime las unidades cuya `source_section_path` empieza con el
                 argumento (prefijo, no igualdad exacta).
                 exit 0.

Dependencias: jsonschema.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = REPO_ROOT / "skill" / "notemartin-study-notes" / "schemas" / "ledger.schema.json"

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2

TERMINAL_STATES = {"written", "merged", "discarded"}
ALLOWED_DISCARD_REASONS = {
    "boilerplate",
    "navigation",
    "out-of-scope-by-user",
    "redundant-with",  # base motif; full form is "redundant-with:<unit_id>"
}


def _import_jsonschema():
    try:
        import jsonschema
        return jsonschema
    except ImportError:
        sys.stderr.write("Dependency missing: jsonschema. Install with `pip install jsonschema`.\n")
        sys.exit(EXIT_USAGE)


def load_schema(path: Path) -> dict:
    if not path.exists():
        sys.stderr.write(f"Schema not found: {path}\n")
        sys.exit(EXIT_USAGE)
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_ledger(path: Path) -> dict:
    if not path.exists():
        sys.stderr.write(f"Ledger not found: {path}\n")
        sys.exit(EXIT_USAGE)
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def check_criterion_1(ledger: dict) -> list[str]:
    """100 % de must-keep en estado terminal."""
    errors: list[str] = []
    for i, entry in enumerate(ledger.get("entries") or []):
        if entry.get("criticality") == "must-keep" and entry.get("state") not in TERMINAL_STATES:
            errors.append(
                f"  - entries[{i}] ({entry.get('unit_id')}): must-keep con state={entry.get('state')!r} (debe ser uno de {sorted(TERMINAL_STATES)})"
            )
    return errors


def check_criterion_2(ledger: dict) -> list[str]:
    """discard_reason dentro de la lista cerrada. El schema ya lo enforza; aquí
    añadimos mensaje explícito."""
    errors: list[str] = []
    for i, entry in enumerate(ledger.get("entries") or []):
        if entry.get("state") == "discarded":
            reason = entry.get("discard_reason")
            if reason is None:
                errors.append(
                    f"  - entries[{i}] ({entry.get('unit_id')}): state=discarded sin discard_reason"
                )
                continue
            # Parse motivo: puede ser "literal" o "redundant-with:xxx"
            base = reason.split(":", 1)[0] if ":" in reason else reason
            if base not in ALLOWED_DISCARD_REASONS:
                errors.append(
                    f"  - entries[{i}] ({entry.get('unit_id')}): discard_reason={reason!r} (base={base!r} no está en {sorted(ALLOWED_DISCARD_REASONS)})"
                )
    return errors


def cmd_validate(args: argparse.Namespace) -> int:
    jsonschema = _import_jsonschema()
    schema = load_schema(args.schema)
    any_fail = False
    for path in args.validate:
        errors: list[str] = []
        ledger = load_ledger(path)

        # Schema
        validator = jsonschema.Draft202012Validator(schema)
        schema_errors = sorted(validator.iter_errors(ledger), key=lambda e: list(e.absolute_path))
        for err in schema_errors:
            errors.append(f"  - schema: {err.message} (path={list(err.absolute_path)})")

        # Criterion 1
        errors.extend(check_criterion_1(ledger))
        # Criterion 2 (explicit message in addition to schema)
        errors.extend(check_criterion_2(ledger))

        if errors:
            any_fail = True
            sys.stderr.write(f"FAIL — {path}\n")
            for e in errors:
                sys.stderr.write(e + "\n")
        else:
            sys.stdout.write(f"OK — {path}\n")
    return EXIT_VALIDATION if any_fail else EXIT_OK


def cmd_coverage(args: argparse.Namespace) -> int:
    ledger_path = Path(args.coverage) if not isinstance(args.coverage, Path) else args.coverage
    ledger = load_ledger(ledger_path)
    entries = ledger.get("entries") or []
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

    sys.stdout.write(f"Coverage report: {args.coverage}\n")
    sys.stdout.write(f"\nGlobal\n")
    sys.stdout.write(f"  Total unidades: {len(entries)}\n")
    sys.stdout.write(f"  must-keep: {mk_terminal}/{mk_total} en estado terminal\n")
    sys.stdout.write(f"  context:   {cx_terminal}/{cx_total} en estado terminal\n")
    sys.stdout.write(f"\nPor estado\n")
    for s in ["pending", "written", "merged", "discarded"]:
        sys.stdout.write(f"  {s:10s}: {by_state.get(s, 0)}\n")
    sys.stdout.write(f"\nPor motivo de descarte\n")
    for r in sorted(ALLOWED_DISCARD_REASONS | set(by_reason.keys())):
        sys.stdout.write(f"  {r:30s}: {by_reason.get(r, 0)}\n")
    sys.stdout.write(f"\nTop secciones con must-keep pending\n")
    for section, n in sorted(pending_per_section.items(), key=lambda x: -x[1])[:5]:
        sys.stdout.write(f"  {section:40s}: {n}\n")
    return EXIT_OK


def cmd_query(args: argparse.Namespace) -> int:
    ledger_path = Path(args.query[0]) if not isinstance(args.query[0], Path) else args.query[0]
    section = args.query[1]
    ledger = load_ledger(ledger_path)
    entries = ledger.get("entries") or []
    matches = [
        e for e in entries
        if e.get("source_section_path", "").startswith(section)
    ]
    if not matches:
        sys.stdout.write(f"(sin resultados para {section!r})\n")
        return EXIT_OK
    sys.stdout.write(f"Section query: {section}\n")
    sys.stdout.write(f"  {len(matches)} match(es):\n")
    for e in matches:
        sys.stdout.write(
            f"    {e.get('unit_id')} | {e.get('criticality')} | {e.get('state')} | "
            f"target_note={e.get('target_note') or '-'} | source_section_path={e.get('source_section_path')}\n"
        )
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="validate_ledger.py",
        description="Valida ledgers contra ledger.schema.json y los criterios 1+2 del roadmap.",
    )
    p.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA,
                   help=f"Ruta al schema (default: {DEFAULT_SCHEMA.relative_to(REPO_ROOT)}).")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate", metavar="LEDGER", type=Path, nargs="+",
                      help="Valida uno o más ledgers.")
    mode.add_argument("--coverage", metavar="LEDGER", type=Path,
                      help="Imprime el reporte de cobertura.")
    mode.add_argument("--query", nargs=2, metavar=("LEDGER", "SECTION"),
                      help="Lista unidades cuya source_section_path comienza con SECTION.")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.validate:
        return cmd_validate(args)
    if args.coverage:
        return cmd_coverage(args)
    if args.query:
        return cmd_query(args)
    parser.print_help()
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
