#!/usr/bin/env python3
"""
validate_ledger.py — Validador del Coverage Ledger (F15).

Modos:
  --note <ledger.json>      valida un ledger.
  --notes-dir <dir>         itera archivos ledger*.json.
  --workdir <dir>           detecta knowledge/ledger.json.

Reglas:
  V-LED-01 must-keep en estado pending (no terminal)
  V-LED-02 discard_reason fuera de lista cerrada
  V-LED-03 target_note ausente en entry must-keep
  V-LED-04 unit_id duplicado
  V-LED-05 redundante redundante-with:<id> apunta a unit inexistente
  V-LED-06 source_block_ids vacío en must-keep

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

TERMINAL_STATES = {"kept", "discarded", "externalized"}
NON_TERMINAL_STATES = {"pending"}
CLOSED_DISCARD_REASONS = {
    "boilerplate", "navigation", "out-of-scope-by-user",
}

DISCARD_RE_RE = re.compile(
    r"^(redundant-with:[a-zA-Z0-9_-]+|boilerplate|navigation|out-of-scope-by-user)$"
)


def validate_ledger(path: Path, doc: dict, issues: list) -> None:
    rel = str(path)

    entries = doc.get("entries")
    if not isinstance(entries, list):
        issues.append({
            "rule_id": "V-LED-10",
            "severity": "error",
            "message": "entries ausente o no es lista",
            "file": rel, "node": "entries",
        })
        return

    seen_ids: set[str] = set()
    all_ids: set[str] = set()

    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            issues.append({
                "rule_id": "V-LED-11",
                "severity": "error",
                "message": f"entry #{i} no es objeto",
                "file": rel, "node": f"entries[{i}]",
            })
            continue

        unit_id = e.get("unit_id", "")
        node = f"entries[{i}]"

        # V-LED-04 duplicate.
        if unit_id:
                if unit_id in seen_ids:
                    issues.append({
                        "rule_id": "V-LED-04",
                        "severity": "error",
                        "message": f"unit_id duplicado: {unit_id!r}",
                        "file": rel, "node": f"{node}.unit_id",
                    })
                else:
                    seen_ids.add(unit_id)
                    all_ids.add(unit_id)

        state = e.get("state")
        criticity = e.get("criticity")
        discard_reason = e.get("discard_reason")
        target_note = e.get("target_note")
        source_blocks = e.get("source_block_ids") or []

        # V-LED-01 must-keep pending.
        if criticity == "must-keep" and state in NON_TERMINAL_STATES:
            issues.append({
                "rule_id": "V-LED-01",
                "severity": "error",
                "message": f"must-keep en estado no-terminal: {state!r}",
                "file": rel, "node": f"{node}.state",
                "fix_hint": "llevar a kept, discarded o externalized",
            })

        # V-LED-02 discard_reason fuera de lista cerrada.
        if discard_reason is not None and not DISCARD_RE_RE.match(discard_reason):
            issues.append({
                "rule_id": "V-LED-02",
                "severity": "error",
                "message": f"discard_reason fuera de lista cerrada: {discard_reason!r}",
                "file": rel, "node": f"{node}.discard_reason",
                "fix_hint": f"usa uno de: redundant-with:<id>, boilerplate, navigation, out-of-scope-by-user",
            })

        # V-LED-03 target_note ausente en must-keep.
        if criticity == "must-keep" and state == "kept" and not target_note:
            issues.append({
                "rule_id": "V-LED-03",
                "severity": "error",
                "message": "must-keep kept sin target_note",
                "file": rel, "node": f"{node}.target_note",
            })

        # V-LED-05 redundante apunta a id inexistente.
        if discard_reason and discard_reason.startswith("redundant-with:"):
            target = discard_reason.split(":", 1)[1]
            if target and target not in all_ids and target != unit_id:
                issues.append({
                    "rule_id": "V-LED-05",
                    "severity": "warning",
                    "message": f"redundant-with:{target} apunta a unit inexistente",
                    "file": rel, "node": f"{node}.discard_reason",
                })

        # V-LED-06 source_block_ids vacío en must-keep.
        if criticity == "must-keep" and not source_blocks:
            issues.append({
                "rule_id": "V-LED-06",
                "severity": "warning",
                "message": "must-keep sin source_block_ids",
                "file": rel, "node": f"{node}.source_block_ids",
            })


def build_report(target: str, issues: list, started: datetime, duration_ms: int) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "validator": "validate_ledger",
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
        return sorted(list(d.rglob("ledger*.json")) + list(d.rglob("coverage*.json"))), args.notes_dir
    d = Path(args.workdir)
    cand = []
    kd = d / "knowledge"
    if kd.is_dir():
        cand += list(kd.glob("ledger*.json"))
    cand += list(d.rglob("ledger*.json"))
    return sorted(set(cand)), args.workdir


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
    targets, label = collect_targets(args)

    if not targets:
        print(f"ERROR: no hay ledger en {label}", file=sys.stderr)
        return 3

    for p in targets:
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            issues.append({
                "rule_id": "V-LED-99",
                "severity": "error",
                "message": f"JSON inválido: {e}",
                "file": str(p), "node": "<root>",
            })
            continue
        validate_ledger(p, doc, issues)

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