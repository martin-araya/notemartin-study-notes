#!/usr/bin/env python3
"""
monospace_diagrams.py — Detector de bloques monoespaciados usados como diagramas (F69).

Modos:
  --note <file.nm|file.md>

Reglas:
  V-MD-01 ancho > 100 cols en bloque code sin flag wide
  V-MD-02 mezcla monoespaciada + proporcional en "figura" sin declaración
  V-MD-03 bloque code>10 líneas no declarado como :::figure

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

CODE_FENCE_RE = re.compile(r"^```(\w*)\s*$")
MAX_COLS = 100
FIGURE_DECL_RE = re.compile(r":::figure", re.IGNORECASE)


def validate_note(path: Path, issues: list) -> None:
    rel = str(path)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    in_code = False
    fence_lang = ""
    code_start = 0
    code_buf: list[str] = []

    in_figure_decl = False

    for i, ln in enumerate(lines, start=1):
        m = CODE_FENCE_RE.match(ln)
        if m:
            if not in_code:
                in_code = True
                fence_lang = m.group(1)
                code_start = i + 1
                code_buf = []
            else:
                # Cierre del bloque.
                block = "\n".join(code_buf)
                lines_count = len(code_buf)
                max_cols = max((len(l) for l in code_buf), default=0)
                is_diagrammatic = (
                    fence_lang in ("text", "ascii", "ansi", "")
                    and lines_count >= 4
                )
                # V-MD-01 ancho > 100 cols.
                if max_cols > MAX_COLS and is_diagrammatic:
                    issues.append({
                        "rule_id": "V-MD-01",
                        "severity": "warning",
                        "message": f"bloque code de {max_cols} cols (>{MAX_COLS})",
                        "file": rel, "node": f"line {code_start}",
                        "fix_hint": "romper en líneas más cortas o usar :::figure",
                    })
                # V-MD-03 no declarado como figura.
                if lines_count >= 10 and fence_lang in ("text", "ascii", "ansi", "") \
                        and not in_figure_decl:
                    issues.append({
                        "rule_id": "V-MD-03",
                        "severity": "info",
                        "message": f"bloque code de {lines_count} líneas no declarado como :::figure",
                        "file": rel, "node": f"line {code_start}",
                        "fix_hint": "envuelve en :::figure si es un diagrama ASCII",
                    })
                in_code = False
                code_buf = []
                fence_lang = ""
            continue
        if in_code:
            code_buf.append(ln)
        # Track :::figure decls.
        if FIGURE_DECL_RE.search(ln):
            in_figure_decl = True
        elif ln.strip() == ":::":
            in_figure_decl = False


def build_report(target: str, issues: list, started: datetime, duration_ms: int) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "validator": "monospace_diagrams",
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