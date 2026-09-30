#!/usr/bin/env python3
"""
validate_images.py — Validador de imágenes y figuras (F12/F45/F65).

Modos:
  --note <file.nm|file.md>   valida ![alt](path) y bloques :::figure.

Reglas:
  V-IMG-01 ![alt](path) sin alt-text
  V-IMG-02 path no resoluble desde la nota
  V-IMG-03 tamaño > 10 MB sin flag (límite duro)
  V-IMG-04 formato no soportado por destinos activos
  V-IMG-05 bloque :::figure sin ![alt](path) o sin caption

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

IMG_INLINE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
FIGURE_BLOCK_RE = re.compile(r":::figure\s*$", re.MULTILINE)

MAX_BYTES_DEFAULT = 10 * 1024 * 1024  # 10 MB

SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif"}


def validate_note(path: Path, issues: list) -> None:
    rel = str(path)
    text = path.read_text(encoding="utf-8")

    # V-IMG-01/02 inline.
    for i, ln in enumerate(text.splitlines(), start=1):
        for m in IMG_INLINE_RE.finditer(ln):
            alt = m.group(1).strip()
            img_path = m.group(2).strip()
            if not alt:
                issues.append({
                    "rule_id": "V-IMG-01",
                    "severity": "error",
                    "message": "imagen sin alt-text",
                    "file": rel, "node": f"line {i}",
                    "fix_hint": "añade descripción entre []",
                })
            # Skip remote URLs.
            if img_path.startswith(("http://", "https://", "data:")):
                continue
            # Resolve relative to the note file.
            target = (path.parent / img_path).resolve()
            if not target.is_file():
                issues.append({
                    "rule_id": "V-IMG-02",
                    "severity": "error",
                    "message": f"path no resoluble: {img_path}",
                    "file": rel, "node": f"line {i}",
                    "fix_hint": "verifica que el archivo existe en el workdir",
                })
                continue
            # V-IMG-03 tamaño.
            try:
                size = target.stat().st_size
            except OSError:
                continue
            if size > MAX_BYTES_DEFAULT:
                issues.append({
                    "rule_id": "V-IMG-03",
                    "severity": "warning",
                    "message": f"imagen > 10 MB ({size} bytes): {img_path}",
                    "file": rel, "node": f"line {i}",
                    "fix_hint": "comprime o convierte a formato más ligero",
                })
            # V-IMG-04 formato.
            ext = target.suffix.lower()
            if ext not in SUPPORTED_FORMATS:
                issues.append({
                    "rule_id": "V-IMG-04",
                    "severity": "warning",
                    "message": f"formato no soportado: {ext}",
                    "file": rel, "node": f"line {i}",
                    "fix_hint": f"usa uno de {sorted(SUPPORTED_FORMATS)}",
                })

    # V-IMG-05 :::figure sin cuerpo.
    in_figure = False
    fig_start = 0
    for i, ln in enumerate(text.splitlines(), start=1):
        if FIGURE_BLOCK_RE.match(ln.strip()):
            in_figure = True
            fig_start = i
            continue
        if in_figure and ln.strip() == ":::":
            block = text.splitlines()[fig_start - 1: i]
            has_img = any(IMG_INLINE_RE.search(b) for b in block)
            has_caption = any(re.match(r"^[A-Z].{5,80}\.?$", b.strip()) for b in block if b.strip())
            if not has_img:
                issues.append({
                    "rule_id": "V-IMG-05",
                    "severity": "warning",
                    "message": ":::figure sin ![alt](path)",
                    "file": rel, "node": f"line {fig_start}",
                })
            if not has_caption:
                issues.append({
                    "rule_id": "V-IMG-05",
                    "severity": "info",
                    "message": ":::figure sin caption explícito",
                    "file": rel, "node": f"line {fig_start}",
                })
            in_figure = False


def build_report(target: str, issues: list, started: datetime, duration_ms: int) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "validator": "validate_images",
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