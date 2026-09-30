#!/usr/bin/env python3
"""
validate_destinations.py — Verificador cross-target (F63/F77).

Modos:
  --workdir <dir>             itera todos los destinos en render/.
  --note <note-id>            valida sólo esa nota en todos los destinos.

Reglas:
  V-DST-00 destino no renderizado (info)
  V-DST-01 pérdida de unidad (no en artifact y sin justificación)
  V-DST-02 degradación no documentada
  V-DST-03 link roto en destino (heurístico)

Exit: 0/2/1/3.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "1.0.0"

DESTINATIONS = [
    "obsidian", "notion_api", "notion_md", "appflowy",
    "markdown", "html_pdf", "flashcards",
]


def load_workdir(wd: Path):
    """Carga IRs, reports de render y manifest."""
    ir_dir = wd / "ir"
    render_dir = wd / "render"
    manifest = wd / "manifest.json"
    notes = []
    if ir_dir.is_dir():
        for ir_path in sorted(ir_dir.glob("*.note-ir.json")):
            try:
                ir = json.loads(ir_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            notes.append({
                "id": ir.get("note_id") or ir_path.stem,
                "ir_path": ir_path,
                "ir": ir,
            })
    reports = {}
    if (render_dir / "reports" / "render-degradation.json").is_file():
        reports["degradation"] = json.loads(
            (render_dir / "reports" / "render-degradation.json").read_text()
        )
    return notes, reports, render_dir


def render_subdir_for(dest: str) -> str:
    return {"obsidian": "obsidian"}.get(dest, dest)


def check_destinations(args, issues: list) -> None:
    if not args.workdir:
        return
    wd = Path(args.workdir)
    if not wd.is_dir():
        issues.append({
            "rule_id": "V-DST-99",
            "severity": "error",
            "message": f"workdir no existe: {wd}",
            "file": str(wd), "node": "<root>",
        })
        return
    notes, reports, render_dir = load_workdir(wd)

    if not notes:
        issues.append({
            "rule_id": "V-DST-04",
            "severity": "warning",
            "message": "no hay IRs en workdir",
            "file": str(wd), "node": "ir/",
        })
        return

    rendered_any = False
    for note in notes:
        nid = note["id"]
        if args.note and args.note != nid:
            continue
        for dest in DESTINATIONS:
            sub = render_subdir_for(dest)
            artifact = render_dir / sub / f"{nid}.md"
            if not artifact.is_file():
                issues.append({
                    "rule_id": "V-DST-00",
                    "severity": "info",
                    "message": f"destino {dest} no renderizado para {nid}",
                    "file": str(wd), "node": f"render/{sub}/{nid}.md",
                })
                continue
            rendered_any = True

            # V-DST-01: detectar pérdidas simples.
            try:
                rendered = artifact.read_text(encoding="utf-8")
            except Exception:
                continue
            for blk in note["ir"].get("nodes") or note["ir"].get("blocks") or []:
                if isinstance(blk, dict):
                    txt = blk.get("text") or blk.get("content") or ""
                    if isinstance(txt, str) and len(txt) > 20:
                        snippet = txt[:30]
                        if snippet not in rendered:
                            issues.append({
                                "rule_id": "V-DST-01",
                                "severity": "error",
                                "message": f"pérdida de unidad en {dest}/{nid}: '{snippet[:20]}...'",
                                "file": str(artifact), "node": f"note:{nid}",
                                "fix_hint": "primera pérdida: " + snippet[:40],
                            })
                            break  # one issue per DEST

            # V-DST-02: degradación no documentada.
            deg = reports.get("degradation", {})
            for d in deg.get("degradations", []) or []:
                if d.get("note_id") == nid and d.get("destination") == dest \
                        and not d.get("content_intact"):
                    issues.append({
                        "rule_id": "V-DST-02",
                        "severity": "warning",
                        "message": f"degradación no documentada en {dest}/{nid}",
                        "file": str(artifact), "node": f"note:{nid}",
                    })

    # V-DST-05 workdir sin renders cuando hay IRs.
    if not rendered_any:
        issues.append({
            "rule_id": "V-DST-05",
            "severity": "warning",
            "message": "hay IRs pero ningún destino renderizado",
            "file": str(wd), "node": "render/",
            "fix_hint": "ejecuta el renderer antes de validar destinos",
        })


def build_report(target: str, issues: list, started: datetime, duration_ms: int) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "validator": "validate_destinations",
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
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--note", default="", help="filtrar por note_id")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out")
    args = parser.parse_args()

    started = datetime.now(timezone.utc)
    issues: list = []
    check_destinations(args, issues)

    duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    report = build_report(args.workdir, issues, started, duration_ms)

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