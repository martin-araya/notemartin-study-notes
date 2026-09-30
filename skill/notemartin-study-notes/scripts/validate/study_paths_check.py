#!/usr/bin/env python3
"""Validador de rutas de estudio — Fase 104.

Aplica las 4 reglas V1-V4 definidas en
`references/09-study/study-paths.md` §7 sobre un archivo JSON de rutas
generado por `study_paths.py`:

  V1 — ≥ 2 rutas por dominio (ROADMAP #1).
  V2 — Orden topológico respeta `depends_on[]` (ROADMAP #2).
  V3 — Cada ruta tiene ≥ 1 checkpoint (ROADMAP #3).
  V4 — Cada `note_id` en `note_path` existe en el note-plan
       (si se pasa `--note-plan`).

CLI:
    python3 study_paths_check.py --routes <path>            # markdown a stdout
    python3 study_paths_check.py --routes <path> --json     # JSON estructurado
    python3 study_paths_check.py --routes <path> --strict   # warnings → exit 1
    python3 study_paths_check.py --routes <path> --note-plan <path>

Exit codes:
    0  sin violaciones
    1  alguna violación (o warning si --strict)
    2  error de uso (archivo no encontrado, etc.)

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class Violation:
    rule: str
    severity: str
    location: str
    message: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "rule": self.rule,
            "severity": self.severity,
            "location": self.location,
            "message": self.message,
        }


@dataclass
class Report:
    violations: List[Violation] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(v.severity == "error" for v in self.violations)

    def to_dict(self) -> Dict[str, object]:
        return {
            "violations": [v.to_dict() for v in self.violations],
            "errors": sum(1 for v in self.violations if v.severity == "error"),
            "warnings": sum(1 for v in self.violations if v.severity == "warning"),
        }


def check_routes(
    routes: List[dict],
    note_plan: Optional[dict] = None,
    strict: bool = False,
) -> Report:
    report = Report()

    if not isinstance(routes, list):
        report.violations.append(Violation(
            "V0", "error", "/",
            f"el archivo JSON debe contener una lista de rutas, recibí {type(routes).__name__}",
        ))
        return report

    # V1: ≥ 2 rutas por dominio.
    by_domain: Dict[str, List[dict]] = {}
    for r in routes:
        if not isinstance(r, dict):
            continue
        domain = r.get("domain")
        if not domain:
            report.violations.append(Violation(
                "V0", "error", "/",
                "ruta sin campo `domain`",
            ))
            continue
        by_domain.setdefault(domain, []).append(r)

    for domain, dom_routes in by_domain.items():
        if len(dom_routes) < 2:
            report.violations.append(Violation(
                "V1", "error", f"domain={domain}",
                f"solo {len(dom_routes)} ruta(s); mínimo 2",
            ))

        # V3: cada ruta tiene ≥ 1 checkpoint.
        for r in dom_routes:
            goal = r.get("goal", "<unknown>")
            cps = r.get("checkpoints", [])
            if not cps:
                report.violations.append(Violation(
                    "V3", "error", f"domain={domain} goal={goal}",
                    "ruta sin checkpoints (R-P4)",
                ))

    # V2: orden topológico.
    for r in routes:
        if not isinstance(r, dict):
            continue
        domain = r.get("domain", "<unknown>")
        goal = r.get("goal", "<unknown>")
        note_path = r.get("note_path", [])
        if not isinstance(note_path, list):
            continue

        seen_steps: Dict[str, int] = {}
        for step in note_path:
            if not isinstance(step, dict):
                continue
            note_id = step.get("note_id", "")
            step_num = step.get("step", 0)
            deps = step.get("depends_on", [])
            seen_steps[note_id] = step_num
            for dep in deps:
                if dep not in seen_steps:
                    report.violations.append(Violation(
                        "V2", "error", f"domain={domain} goal={goal}",
                        f"paso {step_num} ({note_id}) depende de `{dep}` "
                        f"que aparece después o no existe",
                    ))

    # V4: notas en el note-plan.
    if note_plan is not None:
        plan_note_ids: set = set()
        for n in note_plan.get("notes", []):
            plan_note_ids.add(n.get("note_id"))
        for r in routes:
            if not isinstance(r, dict):
                continue
            domain = r.get("domain", "<unknown>")
            goal = r.get("goal", "<unknown>")
            for step in r.get("note_path", []):
                if not isinstance(step, dict):
                    continue
                nid = step.get("note_id", "")
                # Los "[error] X → Y" son notas de repasar; verificar Y.
                if nid.startswith("[error]"):
                    continue
                if nid and nid not in plan_note_ids:
                    report.violations.append(Violation(
                        "V4", "warning", f"domain={domain} goal={goal}",
                        f"`{nid}` no está en el note-plan",
                    ))

    return report


def format_markdown(report: Report) -> str:
    if not report.violations:
        return "# study_paths_check — sin violaciones\n"
    lines: List[str] = ["# study_paths_check — reporte\n"]
    for v in report.violations:
        icon = "❌" if v.severity == "error" else "⚠️"
        lines.append(f"- {icon} **{v.rule}** ({v.severity}) — {v.location}: {v.message}")
    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="study_paths_check.py",
        description="Validador de rutas de estudio (Fase 104).",
    )
    parser.add_argument("--routes", type=Path, required=True,
                        help="ruta al archivo JSON de rutas generadas")
    parser.add_argument("--note-plan", type=Path, default=None,
                        help="ruta opcional a note-plan.json (activa V4)")
    parser.add_argument("--json", action="store_true", help="salida JSON")
    parser.add_argument("--strict", action="store_true",
                        help="warnings se convierten en exit 1")
    args = parser.parse_args(argv)

    if not args.routes.exists():
        print(f"[ERROR] archivo no encontrado: {args.routes}", file=sys.stderr)
        return 2

    routes_data = json.loads(args.routes.read_text(encoding="utf-8"))
    if isinstance(routes_data, dict) and "routes" in routes_data:
        routes_list = routes_data["routes"]
    else:
        routes_list = routes_data

    note_plan_data = None
    if args.note_plan:
        if not args.note_plan.exists():
            print(f"[ERROR] archivo no encontrado: {args.note_plan}",
                  file=sys.stderr)
            return 2
        note_plan_data = json.loads(args.note_plan.read_text(encoding="utf-8"))

    report = check_routes(routes_list, note_plan_data, args.strict)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(format_markdown(report))

    if report.has_errors:
        return 1
    if args.strict and any(v.severity == "warning" for v in report.violations):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
