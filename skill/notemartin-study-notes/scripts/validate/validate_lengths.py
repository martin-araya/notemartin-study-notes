#!/usr/bin/env python3
"""
validate_lengths.py — Validador de longitudes (F75 §6.X + F76 R1).

Modos:
  --note <file.nm|file.md>
  --type <note-type>          para reglas que dependen del tipo

Reglas:
  V-LEN-01 TL;DR > 60 palabras (default; cheatsheet 30; chapter-digest 120)
  V-LEN-02 cheatsheet > 80 líneas
  V-LEN-03 glossary-term > 30 líneas
  V-LEN-04 index-moc > 200 líneas
  V-LEN-05 chapter-digest TL;DR > 120 palabras
  V-LEN-06 sección ## sin contenido sustantivo (≥ 30 chars)

Exit: 0/2/1/3.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "1.0.0"

H2_RE = __import__("re").compile(r"^##\s+(.+?)\s*$")
H3_RE = __import__("re").compile(r"^###\s+")


def split_fm(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text
    return parts[1].strip(), parts[2]


def get_note_type(text: str) -> str:
    fm, _ = split_fm(text)
    for line in fm.splitlines():
        if line.startswith("note-type:"):
            return line.split(":", 1)[1].strip()
    return ""


def count_words(s: str) -> int:
    return len([w for w in s.split() if w])


def validate_note(path: Path, note_type: str, issues: list) -> None:
    rel = str(path)
    text = path.read_text(encoding="utf-8")
    fm, body = split_fm(text)

    lines = body.splitlines()
    total_lines = len([l for l in lines if l.strip()])

    # Find TL;DR section.
    tldr_words = 0
    in_tldr = False
    for ln in lines:
        if H2_RE.match(ln):
            title = H2_RE.match(ln).group(1).strip().lower()
            in_tldr = title in ("tl;dr", "tldr")
            continue
        if H3_RE.match(ln):
            in_tldr = False
            continue
        if in_tldr and ln.strip():
            tldr_words += count_words(ln)

    # V-LEN-01 default 60 / cheatsheet 30 / chapter-digest 120.
    tldr_limit = 60
    if note_type == "cheatsheet":
        tldr_limit = 30
    if note_type == "chapter-digest":
        tldr_limit = 120
    if tldr_words > tldr_limit and tldr_words > 0:
        rule = "V-LEN-05" if note_type == "chapter-digest" else "V-LEN-01"
        issues.append({
            "rule_id": rule,
            "severity": "warning",
            "message": f"TL;DR = {tldr_words} palabras (límite {tldr_limit})",
            "file": rel, "node": "## TL;DR",
            "fix_hint": f"recortar a {tldr_limit} palabras",
        })

    # V-LEN-02 cheatsheet > 80.
    if note_type == "cheatsheet" and total_lines > 80:
        issues.append({
            "rule_id": "V-LEN-02",
            "severity": "error",
            "message": f"cheatsheet = {total_lines} líneas (límite 80)",
            "file": rel, "node": "<root>",
            "fix_hint": "≤ 80 líneas = ≤ 2 pantallas",
        })

    # V-LEN-03 glossary-term > 30.
    if note_type == "glossary-term" and total_lines > 30:
        issues.append({
            "rule_id": "V-LEN-03",
            "severity": "error",
            "message": f"glossary-term = {total_lines} líneas (límite 30)",
            "file": rel, "node": "<root>",
            "fix_hint": "≤ 30 líneas (F75 §6.12 anti-patrón duro)",
        })

    # V-LEN-04 index-moc > 200.
    if note_type == "index-moc" and total_lines > 200:
        issues.append({
            "rule_id": "V-LEN-04",
            "severity": "warning",
            "message": f"index-moc = {total_lines} líneas (límite 200)",
            "file": rel, "node": "<root>",
            "fix_hint": "≤ 200 líneas",
        })

    # V-LEN-06 sección ## vacía.
    cur_title = ""
    cur_body_chars = 0
    last_h2_line = 0
    for i, ln in enumerate(lines, start=1):
        m = H2_RE.match(ln)
        if m:
            # Emitir issue si la anterior quedó vacía.
            if cur_title and cur_body_chars < 30:
                issues.append({
                    "rule_id": "V-LEN-06",
                    "severity": "warning",
                    "message": f"sección `## {cur_title}` casi vacía ({cur_body_chars} chars)",
                    "file": rel, "node": f"line {last_h2_line}",
                    "fix_hint": "≥ 1 párrafo sustantivo ≥ 30 chars",
                })
            cur_title = m.group(1).strip()
            cur_body_chars = 0
            last_h2_line = i
            continue
        if H3_RE.match(ln):
            cur_body_chars += 50  # las sub-secciones agregan contenido
            continue
        if cur_title:
            cur_body_chars += len(ln)
    # Última sección.
    if cur_title and cur_body_chars < 30:
        issues.append({
            "rule_id": "V-LEN-06",
            "severity": "warning",
            "message": f"sección `## {cur_title}` casi vacía ({cur_body_chars} chars)",
            "file": rel, "node": f"line {last_h2_line}",
        })


def build_report(target: str, issues: list, started: datetime, duration_ms: int) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "validator": "validate_lengths",
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
    parser.add_argument("--type", default="", help="note-type (auto-detect si vacío)")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out")
    args = parser.parse_args()

    started = datetime.now(timezone.utc)
    issues: list = []
    p = Path(args.note)
    if not p.is_file():
        print(f"ERROR: no existe {p}", file=sys.stderr)
        return 3
    text = p.read_text(encoding="utf-8")
    note_type = args.type or get_note_type(text)
    validate_note(p, note_type, issues)

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