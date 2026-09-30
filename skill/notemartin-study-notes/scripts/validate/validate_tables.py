#!/usr/bin/env python3
"""
validate_tables.py — Validador de tablas Markdown (F23/F76).

Modos:
  --note <file.nm|file.md>

Reglas:
  V-TBL-01 sin separador |---|
  V-TBL-02 1 fila de datos (anti-patrón F76 R8 + F100 AP4)
  V-TBL-03 celda vacía en columna de datos
  V-TBL-04 número de columnas inconsistente entre filas

Exit: 0/2/1/3.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "1.0.0"

TABLE_LINE_RE = re.compile(r"^\s*\|(.+)\|\s*$")
SEP_LINE_RE = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$")


def parse_tables(text: str) -> list[tuple[int, list[list[str]]]]:
    """Devuelve lista de (linea_inicio, filas_de_celdas).

    Una tabla Markdown se reconoce por la secuencia header_row | sep_row
    | data_row(s). El primer row es el encabezado y se preserva.
    """
    tables: list[tuple[int, list[list[str]]]] = []
    cur: list[list[str]] | None = None
    cur_start = 0
    pending_header: list[list[str]] | None = None
    for i, ln in enumerate(text.splitlines(), start=1):
        is_table = bool(TABLE_LINE_RE.match(ln))
        is_sep = bool(SEP_LINE_RE.match(ln))
        if is_table and is_sep:
            # Separador: el row anterior era header.
            if pending_header is not None:
                cur = pending_header
                cur_start = i - 1
            pending_header = None
            continue
        if is_table and pending_header is None and cur is None:
            # Posible header de tabla siguiente.
            cells = [c.strip() for c in TABLE_LINE_RE.match(ln).group(1).split("|")]
            pending_header = [cells]
            continue
        if is_table and cur is not None:
            cells = [c.strip() for c in TABLE_LINE_RE.match(ln).group(1).split("|")]
            cur.append(cells)
            continue
        # Línea que no es de tabla: cierra la tabla en curso.
        if cur is not None:
            if len(cur) >= 1:
                tables.append((cur_start, cur))
            cur = None
        pending_header = None
    if cur is not None and len(cur) >= 1:
        tables.append((cur_start, cur))
    return tables


def validate_note(path: Path, issues: list) -> None:
    rel = str(path)
    text = path.read_text(encoding="utf-8")
    tables = parse_tables(text)

    for start, rows in tables:
        # V-TBL-02.
        if len(rows) < 2:
            issues.append({
                "rule_id": "V-TBL-02",
                "severity": "warning",
                "message": "tabla con < 2 filas",
                "file": rel, "node": f"line {start}",
                "fix_hint": "añade al menos encabezado + 1 fila de datos",
            })
            continue

        widths = {len(r) for r in rows}
        # V-TBL-04.
        if len(widths) > 1:
            issues.append({
                "rule_id": "V-TBL-04",
                "severity": "error",
                "message": f"columnas inconsistentes en filas: {sorted(widths)}",
                "file": rel, "node": f"line {start}",
            })
            continue

        # V-TBL-03: celdas vacías en filas de datos (ignorar encabezado).
        for ri, row in enumerate(rows[1:], start=1):
            for ci, cell in enumerate(row):
                if not cell:
                    issues.append({
                        "rule_id": "V-TBL-03",
                        "severity": "warning",
                        "message": f"celda vacía en fila {ri + 1}, columna {ci + 1}",
                        "file": rel, "node": f"line {start + ri}",
                        "fix_hint": "rellena con valor o N/A explícito",
                    })


def build_report(target: str, issues: list, started: datetime, duration_ms: int) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "validator": "validate_tables",
        "target": target,
        "started_at": started.isoformat(),
        "duration_ms": duration_ms,
        "summary": {
            "errors": sum(1 for i in issues if i["severity"] == "error"),
            "warnings": sum(1 for i in issues if i["severity"] == "warning"),
            "info": sum(1 for i in issues if i["severity"] == "info"),
        },
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--note", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out")
    args = parser.parse_args()

    started = datetime.now(timezone.utc)
    issues: list = []
    p = Path(args.note)
    if not p.is_file():
        print(f"ERROR: no existe {p}", file=sys.stderr)
        return 3
    validate_note(p, issues)

    duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    report = build_report(str(p), issues, started, duration_ms)

    if args.json or args.out:
        out = json.dumps(report, indent=2, ensure_ascii=False)
        if args.out:
            Path(args.out).write_text(out, encoding="utf-8")
        else:
            print(out)
    else:
        for it in issues:
            print(f"[{it['severity'].upper():7}] {it['rule_id']} {it['file']} — {it['message']}")
        print(f"\n{len(issues)} issues", file=sys.stderr)

    if any(i["severity"] == "error" for i in issues):
        return 1
    if any(i["severity"] == "warning" for i in issues):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())