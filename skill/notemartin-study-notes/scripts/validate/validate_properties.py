#!/usr/bin/env python3
"""
validate_properties.py — Validador de frontmatter / propiedades (F47).

Modos:
  --note <file.nm|file.md>    valida frontmatter YAML.

Reglas:
  V-PR-01 frontmatter ausente
  V-PR-02 key desconocido (fuera de la whitelist de 20 propiedades F47)
  V-PR-03 valor fuera de enum (status, note-type)
  V-PR-04 campo obligatorio ausente en status=published
  V-PR-05 tags no es lista
  V-PR-06 reading-time-minutes no es entero ≥ 1
  V-PR-07 summary > 200 chars

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

# Whitelist F47 §3 (20 propiedades canónicas).
KNOWN_KEYS = {
    "title", "note-type", "status", "summary", "reading-time-minutes",
    "tags", "source", "source-type", "source-anchor", "source-url",
    "retrieved", "product", "product-version", "vendor",
    "related", "difficulty", "coverage", "certification-objective",
    "goal-profile-override", "language",
}

KNOWN_STATUS = {"draft", "published"}
KNOWN_NOTE_TYPES = {
    "concept", "api-reference", "procedure", "configuration",
    "error-troubleshooting", "architecture", "syntax", "data-model",
    "chapter-digest", "comparison", "version-delta", "glossary-term",
    "cheatsheet", "index-moc", "practice",
}
KNOWN_SOURCE_TYPES = {
    "book", "docs", "api", "rfc", "transcription", "article", "release-notes", "other",
}

REQUIRED_ON_PUBLISHED = {"title", "note-type", "status", "summary", "reading-time-minutes"}


def split_fm(text: str) -> tuple[dict, bool]:
    if not text.startswith("---"):
        return {}, False
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, False
    raw = parts[1].strip()
    try:
        import yaml  # type: ignore
        return (yaml.safe_load(raw) or {}), True
    except ImportError:
        return _mini_yaml(raw), True
    except Exception:
        return {}, True


def _mini_yaml(raw: str) -> dict:
    out: dict = {}
    cur_list_key: str | None = None
    for line in raw.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.startswith("  - ") or line.startswith("  -"):
            if cur_list_key:
                out.setdefault(cur_list_key, []).append(line.strip().lstrip("-").strip())
            continue
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            k = k.strip()
            v = v.strip()
            if not v:
                cur_list_key = k
                out.setdefault(k, [])
            else:
                cur_list_key = None
                out[k] = v.strip('"').strip("'")
    return out


def validate_note(path: Path, issues: list) -> None:
    rel = str(path)
    text = path.read_text(encoding="utf-8")
    fm, has_fm = split_fm(text)

    if not has_fm:
        issues.append({
            "rule_id": "V-PR-01",
            "severity": "error",
            "message": "frontmatter ausente",
            "file": rel, "node": "<frontmatter>",
        })
        return

    # V-PR-02 keys desconocidos.
    for k in fm.keys():
        if k not in KNOWN_KEYS:
            issues.append({
                "rule_id": "V-PR-02",
                "severity": "error",
                "message": f"key desconocida en frontmatter: {k!r}",
                "file": rel, "node": f"frontmatter.{k}",
                "fix_hint": f"usa una de {sorted(KNOWN_KEYS)}",
            })

    # V-PR-03 enums.
    if "status" in fm and fm["status"] not in KNOWN_STATUS:
        issues.append({
            "rule_id": "V-PR-03",
            "severity": "error",
            "message": f"status fuera de enum: {fm['status']!r}",
            "file": rel, "node": "frontmatter.status",
            "fix_hint": f"usa uno de {sorted(KNOWN_STATUS)}",
        })

    if "note-type" in fm and fm["note-type"] not in KNOWN_NOTE_TYPES:
        issues.append({
            "rule_id": "V-PR-03",
            "severity": "error",
            "message": f"note-type fuera de enum: {fm['note-type']!r}",
            "file": rel, "node": "frontmatter.note-type",
            "fix_hint": f"usa uno de {sorted(KNOWN_NOTE_TYPES)}",
        })

    if "source-type" in fm and fm["source-type"] not in KNOWN_SOURCE_TYPES:
        issues.append({
            "rule_id": "V-PR-03",
            "severity": "warning",
            "message": f"source-type fuera de enum: {fm['source-type']!r}",
            "file": rel, "node": "frontmatter.source-type",
            "fix_hint": f"usa uno de {sorted(KNOWN_SOURCE_TYPES)}",
        })

    # V-PR-04 required on published.
    if fm.get("status") == "published":
        for key in REQUIRED_ON_PUBLISHED:
            if key not in fm or not fm[key]:
                issues.append({
                    "rule_id": "V-PR-04",
                    "severity": "error",
                    "message": f"campo obligatorio ausente en published: {key}",
                    "file": rel, "node": f"frontmatter.{key}",
                })

    # V-PR-05 tags list.
    if "tags" in fm and not isinstance(fm["tags"], list):
        issues.append({
            "rule_id": "V-PR-05",
            "severity": "warning",
            "message": "tags no es lista",
            "file": rel, "node": "frontmatter.tags",
            "fix_hint": "formato: tags: [type/<tipo>, domain/<x>]",
        })

    # V-PR-06 reading-time-minutes int ≥ 1.
    rtm = fm.get("reading-time-minutes")
    if rtm is not None:
        try:
            n = int(str(rtm))
            if n < 1:
                raise ValueError
        except (ValueError, TypeError):
            issues.append({
                "rule_id": "V-PR-06",
                "severity": "error",
                "message": f"reading-time-minutes no es entero ≥ 1: {rtm!r}",
                "file": rel, "node": "frontmatter.reading-time-minutes",
            })

    # V-PR-07 summary > 200.
    summary = fm.get("summary")
    if summary and len(str(summary)) > 200:
        issues.append({
            "rule_id": "V-PR-07",
            "severity": "warning",
            "message": f"summary > 200 chars ({len(str(summary))})",
            "file": rel, "node": "frontmatter.summary",
            "fix_hint": "recortar a 1 línea ≤ 200 chars",
        })


def build_report(target: str, issues: list, started: datetime, duration_ms: int) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "validator": "validate_properties",
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