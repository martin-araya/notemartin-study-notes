#!/usr/bin/env python3
"""
validate_sdm.py — Validador del Source Document Model (F13/F31).

Modos:
  --note <sdm.json>            valida un SDM.
  --notes-dir <dir>            itera archivos *.json.
  --workdir <dir>              detecta sdm.json en el workdir.

Reglas:
  V-SDM-01 id no determinista (longitud ≠ 12 o no hex)
  V-SDM-02 anchor sin page
  V-SDM-03 duplicate id dentro del SDM
  V-SDM-04 block sin `source`
  V-SDM-05 block con source=ocr sin confidence
  V-SDM-06 content.type no soportado
  V-SDM-07 hash fuente no hex 64

Exit: 0 sin issues / 2 warnings / 1 errors / 3 uso.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "1.0.0"

VALID_TYPES = {
    "prose", "heading", "list", "table", "code", "console",
    "formula", "figure", "caption", "note", "warning",
    "example", "syntax-diagram", "footnote", "toc", "boilerplate",
}

ID_RE = re.compile(r"^[0-9a-f]{12}$")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def validate_sdm(path: Path, doc: dict, issues: list) -> None:
    rel = str(path)

    # V-SDM-07 hash fuente.
    src = doc.get("source") or {}
    if not isinstance(src, dict):
        issues.append({
            "rule_id": "V-SDM-08",
            "severity": "error",
            "message": "campo `source` ausente o no es objeto",
            "file": rel, "node": "source",
            "fix_hint": "añade source: {hash: '<sha256 64 hex>', ...}",
        })
    else:
        h = src.get("hash")
        if h and not HASH_RE.match(str(h)):
            issues.append({
                "rule_id": "V-SDM-07",
                "severity": "error",
                "message": f"hash de fuente no es sha256 hex (64): {h!r}",
                "file": rel, "node": "source.hash",
            })

    sections = doc.get("sections") or []
    if not isinstance(sections, list):
        issues.append({
            "rule_id": "V-SDM-09",
            "severity": "error",
            "message": "sections ausente o no es lista",
            "file": rel, "node": "sections",
        })
        return

    seen_ids: set[str] = set()
    for sec_i, sec in enumerate(sections):
        if not isinstance(sec, dict):
            issues.append({
                "rule_id": "V-SDM-10",
                "severity": "error",
                "message": f"sección #{sec_i} no es objeto",
                "file": rel, "node": f"sections[{sec_i}]",
            })
            continue
        sec_id = sec.get("id", "")
        if sec_id and not ID_RE.match(sec_id):
            issues.append({
                "rule_id": "V-SDM-01",
                "severity": "error",
                "message": f"section id malformado: {sec_id!r}",
                "file": rel, "node": f"sections[{sec_i}].id",
                "fix_hint": "espera 12 hex chars (sha1 truncado)",
            })
        for blk_i, blk in enumerate(sec.get("blocks") or []):
            if not isinstance(blk, dict):
                continue
            blk_id = blk.get("id", "")
            node = f"sections[{sec_i}].blocks[{blk_i}]"

            # V-SDM-01 id malformado.
            if blk_id and not ID_RE.match(blk_id):
                issues.append({
                    "rule_id": "V-SDM-01",
                    "severity": "error",
                    "message": f"block id malformado: {blk_id!r}",
                    "file": rel, "node": f"{node}.id",
                    "fix_hint": "espera 12 hex chars",
                })

            # V-SDM-03 duplicate.
            if blk_id:
                if blk_id in seen_ids:
                    issues.append({
                        "rule_id": "V-SDM-03",
                        "severity": "error",
                        "message": f"block id duplicado: {blk_id!r}",
                        "file": rel, "node": f"{node}.id",
                    })
                else:
                    seen_ids.add(blk_id)

            # V-SDM-02 anchor sin page.
            anchor = blk.get("anchor") or {}
            if isinstance(anchor, dict):
                page = anchor.get("page")
                section_path = anchor.get("section_path")
                if page is None and not section_path:
                    issues.append({
                        "rule_id": "V-SDM-02",
                        "severity": "error",
                        "message": "anchor sin page ni section_path",
                        "file": rel, "node": f"{node}.anchor",
                    })

            # V-SDM-04 source ausente.
            if not blk.get("source"):
                issues.append({
                    "rule_id": "V-SDM-04",
                    "severity": "warning",
                    "message": "block sin campo `source`",
                    "file": rel, "node": f"{node}.source",
                    "fix_hint": "asigna `source` ∈ {native, ocr, reconstructed}",
                })

            # V-SDM-05 ocr sin confidence.
            if blk.get("source") == "ocr" and blk.get("confidence") is None:
                issues.append({
                    "rule_id": "V-SDM-05",
                    "severity": "warning",
                    "message": "block con source=ocr sin confidence",
                    "file": rel, "node": f"{node}.confidence",
                })

            # V-SDM-06 content.type no soportado.
            content = blk.get("content") or {}
            if isinstance(content, dict):
                ctype = content.get("type")
                if ctype and ctype not in VALID_TYPES:
                    issues.append({
                        "rule_id": "V-SDM-06",
                        "severity": "error",
                        "message": f"content.type no soportado: {ctype!r}",
                        "file": rel, "node": f"{node}.content.type",
                        "fix_hint": f"usa uno de {sorted(VALID_TYPES)}",
                    })


def build_report(target: str, issues: list, started: datetime, duration_ms: int) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "validator": "validate_sdm",
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


def collect_targets(args) -> tuple[list[Path], str]:
    if args.note:
        return [Path(args.note)], args.note
    if args.notes_dir:
        d = Path(args.notes_dir)
        return sorted(d.rglob("*.json")), args.notes_dir
    d = Path(args.workdir)
    sdm = d / "sdm.json"
    return ([sdm] if sdm.is_file() else []), args.workdir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--note")
    grp.add_argument("--notes-dir")
    grp.add_argument("--workdir")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out")
    args = parser.parse_args()

    started = datetime.now(timezone.utc)
    issues: list = []
    targets, target_label = collect_targets(args)

    if not targets:
        print(f"ERROR: no hay SDM en {target_label}", file=sys.stderr)
        return 3

    for p in targets:
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            issues.append({
                "rule_id": "V-SDM-99",
                "severity": "error",
                "message": f"JSON inválido: {e}",
                "file": str(p), "node": "<root>",
            })
            continue
        validate_sdm(p, doc, issues)

    duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    report = build_report(target_label, issues, started, duration_ms)

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