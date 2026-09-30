#!/usr/bin/env python3
"""Validador de perfiles de objetivo — Fase 105.

Aplica las 5 reglas V1-V5 definidas en
`references/09-study/goal-profiles.md` §7 sobre el corpus:

  V1 — No-reducción de cobertura (R-G3 + INV-GP1).
  V2 — Coherencia del reporte por objetivo (R-G7, solo con --profile certification).
  V3 — Notas en el note-plan (consistencia con F44).
  V4 — Validación de `adds[]` y `relaxes[]` del catálogo (R-G2).
  V5 — `goal_profile` ∈ enum cerrado (R-G1).

CLI:
    python3 goal_profile_check.py --profile interview --workdir <dir>
    python3 goal_profile_check.py --profile certification --by-objective <id>
    python3 goal_profile_check.py --profile hybrid --workdir <dir> --json
    python3 goal_profile_check.py --profile work --workdir <dir> --strict

Exit codes:
    0  sin violaciones
    1  alguna violación
    2  error de uso

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Tuple


VALID_PROFILES = ("hybrid", "interview", "certification", "work")

# Secciones obligatorias por note-type (F105 §3 + F78-F92).
MANDATORY_SECTIONS: Dict[str, Tuple[str, ...]] = {
    "concept": ("## TL;DR", "## Mecanismo"),
    "api-reference": ("## TL;DR", "## Parámetros", "## Respuesta"),
    "procedure": ("## TL;DR", "## Procedimiento"),
    "configuration": ("## TL;DR", "## Configuración"),
    "error-troubleshooting": ("## TL;DR", "## Síntomas", "## Causa raíz",
                              "## Diagnóstico ordenado", "## Solución"),
    "architecture": ("## TL;DR", "## Mecanismo", "## Decisiones de diseño"),
    "syntax": ("## TL;DR", "## Sintaxis"),
    "data-model": ("## TL;DR", "## Modelo"),
    "chapter-digest": ("## TL;DR", "## Puntos clave"),
    "comparison": ("## TL;DR", "## Escenario", "## Tabla", "## Veredicto"),
    "version-delta": ("## TL;DR", "## Cambios"),
    "glossary-term": ("## TL;DR",),
    "cheatsheet": ("## TL;DR", "## Comandos"),
    "index-moc": (),
    "practice": ("## TL;DR", "## Enunciado", "## Entorno", "## Limpieza"),
}

# Secciones que cada perfil declara en `adds[]` (F105 §2).
# `hybrid` es modo passthrough (S4): aplica los 3 perfiles canónicos
# en modo light; no falla V1 si las notas no tienen todas las secciones.
PROFILE_ADDS: Dict[str, Tuple[str, ...]] = {
    "hybrid": (),  # passthrough: no enforces adds.
    "interview": ("## Decisiones de diseño", "## Explicación oral"),
    "certification": ("## Objetivos oficiales", "## Cobertura por objetivo"),
    "work": (),
}


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
    notes_checked: int = 0

    @property
    def has_errors(self) -> bool:
        return any(v.severity == "error" for v in self.violations)

    def to_dict(self) -> Dict[str, object]:
        return {
            "notes_checked": self.notes_checked,
            "errors": sum(1 for v in self.violations if v.severity == "error"),
            "warnings": sum(1 for v in self.violations if v.severity == "warning"),
            "violations": [v.to_dict() for v in self.violations],
        }


def _parse_frontmatter_min(text: str) -> Dict[str, str]:
    fm: Dict[str, str] = {}
    if not text.startswith("---"):
        return fm
    end = text.find("\n---", 3)
    if end < 0:
        return fm
    fm_text = text[3:end].strip()
    for line in fm_text.splitlines():
        line = line.rstrip()
        if not line or ":" not in line or line.lstrip().startswith("#"):
            continue
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm


def _read_sections(text: str) -> set:
    """Devuelve el set de headings H2 encontrados en el texto."""
    return set(re.findall(r"^##\s+(.+)$", text, re.MULTILINE))


def _load_yaml_minimal(path: Path) -> Dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    out: Dict = {}
    for line in text.splitlines():
        line = line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if ":" in line and not line.startswith("-"):
            key, _, value = line.partition(":")
            value = value.strip()
            if value == "":
                continue
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                items = [v.strip().strip('"') for v in inner.split(",") if v.strip()]
                out[key.strip()] = items
            else:
                out[key.strip()] = value.strip('"')
    return out


def check_workdir(
    workdir: Path,
    profile: str,
    by_objective: Optional[str],
    strict: bool = False,
) -> Report:
    report = Report()

    if profile not in VALID_PROFILES:
        report.violations.append(Violation(
            "V5", "error", "--profile",
            f"unknown-profile: '{profile}' (esperaba uno de {VALID_PROFILES})",
        ))
        return report

    notemark_dir = workdir / "notemark"
    if not notemark_dir.exists():
        report.violations.append(Violation(
            "V1", "error", str(notemark_dir),
            f"directorio no encontrado: {notemark_dir}",
        ))
        return report

    profile_yaml_path = workdir / "profile.yaml"
    profile_yaml_data = _load_yaml_minimal(profile_yaml_path)

    # V5: goal_profile del profile.yaml debe ser canónico.
    yaml_profile = profile_yaml_data.get("goal_profile")
    if yaml_profile and yaml_profile not in VALID_PROFILES:
        report.violations.append(Violation(
            "V5", "error", str(profile_yaml_path),
            f"goal_profile no canónico: '{yaml_profile}' (esperaba uno de {VALID_PROFILES})",
        ))

    adds = PROFILE_ADDS[profile]

    # V4: validates adds / relaxes counts.
    if len(adds) > 2:
        report.violations.append(Violation(
            "V4", "error", "catalog",
            f"perfil '{profile}' tiene {len(adds)} adds; máximo 2 (R-G2)",
        ))

    # V2: certification --by-objective coherence.
    objectives: Dict[str, str] = {}
    if profile == "certification":
        cert = profile_yaml_data.get("certification", {})
        if isinstance(cert, dict):
            obj_list = cert.get("objectives", [])
            if isinstance(obj_list, list):
                for entry in obj_list:
                    if isinstance(entry, str) and ":" in entry:
                        oid, desc = entry.split(":", 1)
                        objectives[oid.strip()] = desc.strip()
            elif isinstance(obj_list, dict):
                objectives = obj_list

        if by_objective:
            if not objectives:
                report.violations.append(Violation(
                    "V2", "error", "profile.yaml",
                    "no-objectives-declared: certification.objectives[] ausente",
                ))
            elif by_objective not in objectives:
                report.violations.append(Violation(
                    "V2", "error", "--by-objective",
                    f"unknown-objective: '{by_objective}' no está en certification.objectives[]",
                ))

    # V3: notas en el note-plan.
    note_plan_path = workdir / "knowledge" / "note-plan.json"
    plan_note_ids: set = set()
    if note_plan_path.exists():
        try:
            plan_data = json.loads(note_plan_path.read_text(encoding="utf-8"))
            for n in plan_data.get("notes", []):
                plan_note_ids.add(n.get("note_id"))
        except json.JSONDecodeError:
            pass

    # V1 + V2 (per-objective): iterar las notas.
    notes_iter = sorted(notemark_dir.glob("*.nm")) + sorted(notemark_dir.glob("*.md"))
    for note_path in notes_iter:
        report.notes_checked += 1
        text = note_path.read_text(encoding="utf-8")
        fm = _parse_frontmatter_min(text)
        note_type = fm.get("note-type", "")
        override = fm.get("goal-profile-override")

        # El perfil efectivo es el override o el global.
        effective_profile = override or profile
        if effective_profile != profile:
            # V5: goal-profile-override debe ser canónico.
            if effective_profile not in VALID_PROFILES:
                report.violations.append(Violation(
                    "V5", "error", f"note={note_path.name}",
                    f"goal-profile-override no canónico: '{effective_profile}'",
                ))
                continue

        # V3: nota en el note-plan.
        note_id_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        # Fallback: usar el nombre del archivo.
        note_id = note_path.stem
        if plan_note_ids and note_id not in plan_note_ids:
            report.violations.append(Violation(
                "V3", "warning", f"note={note_id}",
                f"`{note_id}` no está en note-plan",
            ))

        # V1: no-reducción de cobertura.
        mandatory = MANDATORY_SECTIONS.get(note_type, ())
        if mandatory:
            sections = _read_sections(text)
            missing = [s for s in mandatory if not any(s.lstrip("#").strip() in sec for sec in sections)]
            if missing:
                report.violations.append(Violation(
                    "V1", "error", f"note={note_id}",
                    f"missing-mandatory-section: {missing} (note-type={note_type})",
                ))

        # V1: secciones `adds` del perfil activo deben estar presentes.
        effective_adds = PROFILE_ADDS.get(effective_profile, ())
        if effective_adds and effective_profile != "work":
            sections = _read_sections(text)
            for add in effective_adds:
                add_name = add.lstrip("#").strip()
                if not any(add_name in sec for sec in sections):
                    report.violations.append(Violation(
                        "V1", "error", f"note={note_id}",
                        f"missing-profile-section: '{add}' (perfil={effective_profile}, R-G4/R-G5)",
                    ))

        # V2: certification-objective coherente con el objetivo activo.
        if profile == "certification" and by_objective:
            cert_obj = fm.get("certification-objective", "")
            # Parse lista simple: puede ser "[a, b]" o "a, b" o ausente.
            items: List[str] = []
            cert_obj = cert_obj.strip()
            if cert_obj.startswith("[") and cert_obj.endswith("]"):
                items = [x.strip().strip('"').strip("'") for x in cert_obj[1:-1].split(",") if x.strip()]
            elif cert_obj:
                items = [x.strip() for x in cert_obj.split(",") if x.strip()]

            if by_objective in items:
                contribution = "covers"
            else:
                contribution = "partial"

            # Si el objetivo no está en items ni en objectives, es missing.
            if by_objective not in items:
                sev = "warning" if not strict else "error"
                report.violations.append(Violation(
                    "V2", sev, f"note={note_id}",
                    f"`{by_objective}` no está en certification-objective de la nota (contribution={contribution})",
                ))

    return report


def format_markdown(report: Report) -> str:
    if not report.violations:
        return f"# goal_profile_check — sin violaciones ({report.notes_checked} notas verificadas)\n"
    lines: List[str] = [
        f"# goal_profile_check — reporte ({report.notes_checked} notas verificadas)\n"
    ]
    for v in report.violations:
        icon = "❌" if v.severity == "error" else "⚠️"
        lines.append(f"- {icon} **{v.rule}** ({v.severity}) — {v.location}: {v.message}")
    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="goal_profile_check.py",
        description="Validador de perfiles de objetivo (Fase 105).",
    )
    parser.add_argument("--profile", choices=VALID_PROFILES, required=True,
                        help="perfil de objetivo a validar")
    parser.add_argument("--workdir", type=Path, default=Path("."),
                        help="raíz del workdir (default: directorio actual)")
    parser.add_argument("--by-objective", default=None,
                        help="objetivo (solo con --profile certification)")
    parser.add_argument("--json", action="store_true", help="salida JSON")
    parser.add_argument("--strict", action="store_true",
                        help="warnings → exit 1")
    args = parser.parse_args(argv)

    if args.by_objective and args.profile != "certification":
        print("[ERROR] --by-objective solo aplica con --profile certification",
              file=sys.stderr)
        return 2

    report = check_workdir(args.workdir, args.profile, args.by_objective, args.strict)

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
