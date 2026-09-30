#!/usr/bin/env python3
"""
validate_notemark.py — Validador de sintaxis NoteMark (F12).

Modos:
  --note <file.nm|file.md>    valida una nota NoteMark.
  --notes-dir <dir>           itera *.nm/*.md.

Reglas:
  V-NM-01 frontmatter no es YAML / no presente
  V-NM-02 campo frontmatter obligatorio ausente
  V-NM-03 directiva :::tipo desconocida
  V-NM-04 callout no balanceado (sin ::: de cierre)
  V-NM-05 marca {src:blk_xxxx} con id no hex 12
  V-NM-06 marca [[term:nombre]] malformada
  V-NM-07 marca [[note:id]] malformada
  V-NM-08 layer marker {layer:l1|l2|l3} con valor inválido
  V-NM-09 placeholder {{...}} malformado

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

KNOWN_DIRECTIVES = {
    "warning", "note", "tip", "example", "danger", "security",
    "performance", "version", "deprecated", "conflict", "external",
    "collapsible", "columns", "param-table", "step", "question",
    "diagram", "figure", "equation", "console",
}
REQUIRED_FRONTMATTER = {"title", "note-type", "status"}
VALID_LAYERS = {"l1", "l2", "l3"}

ID_RE = re.compile(r"^[0-9a-f]{12}$")
DIRECTIVE_OPEN_RE = re.compile(r"^:::([a-z\-]+)(\s|$)")
SRC_MARK_RE = re.compile(r"\{src:(blk_[0-9a-f]{12})\}")
SRC_BAD_RE = re.compile(r"\{src:([^}]+)\}")
TERM_MARK_RE = re.compile(r"\[\[term:([^\]]+)\]\]")
TERM_BAD_MARKER = re.compile(r"\[\[term:[^\]]*$")
NOTE_MARK_RE = re.compile(r"\[\[note:([a-zA-Z0-9_\-]+)\]\]")
LAYER_MARK_RE = re.compile(r"\{layer:([^}]+)\}")
PLACEHOLDER_RE = re.compile(r"\{\{([^}]*)\}\}")


def split_frontmatter(text: str) -> tuple[dict, str, bool]:
    """Devuelve (frontmatter_dict, body, has_frontmatter)."""
    if not text.startswith("---"):
        return {}, text, False
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text, False
    fm_raw = parts[1].strip()
    body = parts[2]
    try:
        import yaml  # type: ignore
        fm = yaml.safe_load(fm_raw) or {}
    except ImportError:
        fm = _mini_yaml(fm_raw)
    except Exception:
        fm = {}
    return fm, body, True


def _mini_yaml(raw: str) -> dict:
    out: dict = {}
    for line in raw.splitlines():
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            v = v.strip().strip('"').strip("'")
            out[k.strip()] = v
    return out


def validate_note(path: Path, issues: list) -> None:
    rel = str(path)
    text = path.read_text(encoding="utf-8")

    fm, body, has_fm = split_frontmatter(text)

    # V-NM-01 frontmatter ausente.
    if not has_fm:
        issues.append({
            "rule_id": "V-NM-01",
            "severity": "error",
            "message": "frontmatter ausente (no empieza por ---)",
            "file": rel, "node": "<frontmatter>",
            "fix_hint": "añade bloque YAML al inicio con title, note-type, status",
        })
        return

    # V-NM-02 campos obligatorios.
    for key in REQUIRED_FRONTMATTER:
        if key not in fm:
            issues.append({
                "rule_id": "V-NM-02",
                "severity": "error",
                "message": f"frontmatter sin campo obligatorio: {key}",
                "file": rel, "node": f"frontmatter.{key}",
            })

    # V-NM-03 directivas.
    for i, ln in enumerate(body.splitlines(), start=1):
        m = DIRECTIVE_OPEN_RE.match(ln.strip())
        if m and m.group(1) not in KNOWN_DIRECTIVES:
            issues.append({
                "rule_id": "V-NM-03",
                "severity": "error",
                "message": f"directiva desconocida: :::{m.group(1)}",
                "file": rel, "node": f"line {i}",
                "fix_hint": f"usa una de {sorted(KNOWN_DIRECTIVES)}",
            })

    # V-NM-04 callouts no balanceados.
    open_counts: dict[str, int] = {}
    for i, ln in enumerate(body.splitlines(), start=1):
        s = ln.strip()
        if s.startswith(":::"):
            m = re.match(r"^:::([a-z\-]+)\s*(\{[^}]*\})?\s*$", s)
            if m:
                # apertura
                open_counts[m.group(1)] = open_counts.get(m.group(1), 0) + 1
            elif re.match(r"^:::\s*$", s):
                # cierre genérico
                for k in list(open_counts.keys()):
                    if open_counts[k] > 0:
                        open_counts[k] -= 1
                        break
    for kind, cnt in open_counts.items():
        if cnt > 0:
            issues.append({
                "rule_id": "V-NM-04",
                "severity": "error",
                "message": f"directiva :::{kind} abierta {cnt}× sin cierre",
                "file": rel, "node": f"directive::{kind}",
            })

    # V-NM-05 src marks.
    for i, ln in enumerate(body.splitlines(), start=1):
        for m in SRC_BAD_RE.finditer(ln):
            val = m.group(1)
            if not val.startswith("blk_"):
                continue
            id_part = val[len("blk_"):]
            if not ID_RE.match(id_part):
                issues.append({
                    "rule_id": "V-NM-05",
                    "severity": "error",
                    "message": f"{{src:{val}}} id no hex 12",
                    "file": rel, "node": f"line {i}",
                    "fix_hint": "formato: {src:blk_<12 hex>}",
                })

    # V-NM-06/07 term/note marks.
    for i, ln in enumerate(body.splitlines(), start=1):
        if TERM_BAD_MARKER.search(ln):
            issues.append({
                "rule_id": "V-NM-06",
                "severity": "warning",
                "message": "marca [[term:...]] malformada (falta ]])",
                "file": rel, "node": f"line {i}",
            })
        for m in NOTE_MARK_RE.finditer(ln):
            if not m.group(1):
                issues.append({
                    "rule_id": "V-NM-07",
                    "severity": "error",
                    "message": "[[note:<id>]] con id vacío",
                    "file": rel, "node": f"line {i}",
                })

    # V-NM-08 layer markers.
    for i, ln in enumerate(body.splitlines(), start=1):
        for m in LAYER_MARK_RE.finditer(ln):
            v = m.group(1).strip()
            if v not in VALID_LAYERS:
                issues.append({
                    "rule_id": "V-NM-08",
                    "severity": "error",
                    "message": f"{{layer:{v}}} valor inválido",
                    "file": rel, "node": f"line {i}",
                    "fix_hint": f"usa uno de {sorted(VALID_LAYERS)}",
                })

    # V-NM-09 placeholders.
    for i, ln in enumerate(body.splitlines(), start=1):
        for m in PLACEHOLDER_RE.finditer(ln):
            v = m.group(1).strip()
            if not v:
                issues.append({
                    "rule_id": "V-NM-09",
                    "severity": "warning",
                    "message": "placeholder {{}} vacío",
                    "file": rel, "node": f"line {i}",
                })


def build_report(target: str, issues: list, started: datetime, duration_ms: int) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "validator": "validate_notemark",
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
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--note")
    grp.add_argument("--notes-dir")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out")
    args = parser.parse_args()

    started = datetime.now(timezone.utc)
    issues: list = []
    if args.note:
        targets = [Path(args.note)]
        label = args.note
    else:
        d = Path(args.notes_dir)
        targets = sorted(list(d.rglob("*.nm")) + list(d.rglob("*.md")))
        label = args.notes_dir

    if not targets:
        print(f"ERROR: no hay notas en {label}", file=sys.stderr)
        return 3

    for p in targets:
        validate_note(p, issues)

    duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    report = build_report(label, issues, started, duration_ms)

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