#!/usr/bin/env python3
"""
validate_links.py — Validador de enlaces entre notas (F61/F100).

Modos:
  --note <file.nm>           valida enlaces de una nota.
  --notes-dir <dir>          itera *.nm/*.md; verifica resolución + bidireccionalidad.
  --workdir <dir>            detecta notes/.

Reglas:
  V-LK-01 target [[note:id]] no existe en el corpus
  V-LK-02 sin frase introductoria ≥ 5 palabras antes del [[note:id]] (F100 AP7)
  V-LK-03 backlink ausente en target (target no enlaza de vuelta)
  V-LK-04 link circular de 2 nodos sin flag

Exit: 0/2/1/3.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "1.0.0"

NOTE_LINK_RE = re.compile(r"\[\[note:([a-zA-Z0-9_\-]+)\]\]")
H2_RE = re.compile(r"^##\s+(.+?)\s*$")
WORD_RE = re.compile(r"\w+")


def parse_note(path: Path) -> tuple[set[str], set[str], list[tuple[str, str]]]:
    """Devuelve (backlinks_a_otros, h2_headings, lista_de_(linea, link_target))."""
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"^---$", text, maxsplit=2, flags=re.MULTILINE)
    body = parts[2] if len(parts) >= 3 else text
    h2s: set[str] = set()
    links: list[tuple[str, str]] = []
    cur_h2 = "<root>"
    for ln in body.splitlines():
        m = H2_RE.match(ln)
        if m:
            cur_h2 = m.group(1)
            h2s.add(cur_h2)
        for m in NOTE_LINK_RE.finditer(ln):
            links.append((cur_h2, m.group(1)))
    targets = {t for _, t in links}
    return targets, h2s, links


def intros_ok(path: Path, min_words: int = 5) -> list[tuple[int, str]]:
    """Devuelve lista de (linea, target) sin frase introductoria ≥ min_words."""
    bad: list[tuple[int, str]] = []
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"^---$", text, maxsplit=2, flags=re.MULTILINE)
    body = parts[2] if len(parts) >= 3 else text
    for i, ln in enumerate(body.splitlines(), start=1):
        for m in NOTE_LINK_RE.finditer(ln):
            pre = ln[: m.start()].rstrip()
            words = WORD_RE.findall(pre)
            if len(words) < min_words:
                bad.append((i, m.group(1)))
    return bad


def find_cycles(edges: dict[str, set[str]]) -> list[tuple[str, str]]:
    """Detecta ciclos de 2 nodos (a↔b sin tercer nodo)."""
    cycles: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for a, bs in edges.items():
        for b in bs:
            pair = (a, b)
            if pair in seen:
                continue
            seen.add(pair)
            if a in edges.get(b, set()):
                cycles.append((a, b))
    return cycles


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

    if args.note:
        notes_root = Path(args.note).parent
        targets_files = [Path(args.note)]
        label = args.note
    elif args.notes_dir:
        notes_root = Path(args.notes_dir)
        targets_files = sorted(
            list(notes_root.rglob("*.nm")) + list(notes_root.rglob("*.md"))
        )
        label = args.notes_dir
    else:
        wd = Path(args.workdir)
        notes_root = wd / "notes"
        targets_files = sorted(
            list(notes_root.rglob("*.nm")) + list(notes_root.rglob("*.md"))
        ) if notes_root.is_dir() else []
        label = args.workdir

    # First pass: gather all note ids and outbound links.
    note_ids: dict[Path, str] = {}
    edges: dict[str, set[str]] = defaultdict(set)
    for p in targets_files:
        try:
            targets, h2s, links = parse_note(p)
        except Exception as e:
            issues.append({
                "rule_id": "V-LK-99",
                "severity": "error",
                "message": f"error leyendo {p}: {e}",
                "file": str(p), "node": "<root>",
            })
            continue
        nid = p.stem
        note_ids[p] = nid
        for _, tgt in links:
            edges[nid].add(tgt)

    # Second pass: checks.
    all_ids = set(note_ids.values())
    for p, nid in note_ids.items():
        try:
            targets, h2s, links = parse_note(p)
        except Exception:
            continue

        # V-LK-01 target no existe.
        for h2, tgt in links:
            if tgt not in all_ids:
                sev = "info" if not all_ids else "error"
                issues.append({
                    "rule_id": "V-LK-01",
                    "severity": sev,
                    "message": f"target [[note:{tgt}]] no existe en el corpus",
                    "file": str(p), "node": h2,
                    "fix_hint": "verifica el id o crea la nota target",
                })

        # V-LK-02 sin frase introductoria.
        for line_no, tgt in intros_ok(p):
            issues.append({
                "rule_id": "V-LK-02",
                "severity": "warning",
                "message": f"[[note:{tgt}]] sin frase introductoria ≥ 5 palabras (F100 AP7)",
                "file": str(p), "node": f"line {line_no}",
                "fix_hint": "añade ≥ 5 palabras antes del [[note:id]]",
            })

        # V-LK-03 backlink ausente en target (cuando hay corpus completo).
        if all_ids:
            outgoing = {t for _, t in links}
            for tgt in outgoing:
                if tgt in all_ids:
                    target_p = next((q for q, n in note_ids.items() if n == tgt), None)
                    if target_p:
                        try:
                            t_targs, _, _ = parse_note(target_p)
                        except Exception:
                            continue
                        if nid not in t_targs:
                            issues.append({
                                "rule_id": "V-LK-03",
                                "severity": "info",
                                "message": f"target [[note:{tgt}]] no enlaza de vuelta a {nid}",
                                "file": str(p), "node": tgt,
                            })

    # V-LK-04 ciclos de 2.
    for a, b in find_cycles(edges):
        pa = next((q for q, n in note_ids.items() if n == a), None)
        if pa:
            issues.append({
                "rule_id": "V-LK-04",
                "severity": "warning",
                "message": f"ciclo de 2 nodos: {a}↔{b}",
                "file": str(pa), "node": a,
                "fix_hint": "añade un tercer nodo o marca como circular intencional",
            })

    duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    report = {
        "schema_version": SCHEMA_VERSION,
        "validator": "validate_links",
        "target": label,
        "started_at": started.isoformat(),
        "duration_ms": duration_ms,
        "summary": {
            "errors": sum(1 for i in issues if i["severity"] == "error"),
            "warnings": sum(1 for i in issues if i["severity"] == "warning"),
            "info": sum(1 for i in issues if i["severity"] == "info"),
        },
        "issues": issues,
    }

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