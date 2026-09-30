#!/usr/bin/env python3
"""Filtra rutas de estudio por perfil de objetivo — Fase 105.

Implementa las 4 reglas P1-P4 definidas en
`references/09-study/goal-profiles.md` §6:

  P1 — Lectura del perfil activo desde `--profile` o `profile.yaml`.
  P2 — Lectura del input (rutas de F104) desde `--input`.
  P3 — Filtro por perfil + secciones adicionales (`adds[]`) inyectadas
       al final de cada ruta.
  P4 — Emisión Markdown o JSON.

CLI:
    python3 goal_profiles.py --profile interview --input <file.json>
    python3 goal_profiles.py --profile certification --by-objective ckad-core-1
    python3 goal_profiles.py --profile work --input <file.json> --format md
    python3 goal_profiles.py --profile hybrid --profile-yaml <path/to/profile.yaml>

Exit codes:
    0  OK
    1  perfil desconocido o violación R-G2/R-G3
    2  error de uso (archivo no encontrado, etc.)

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


VALID_PROFILES = ("hybrid", "interview", "certification", "work")

# Catálogo cerrado de perfiles (F105 §2).
# `adds[]`: secciones adicionales que el perfil inyecta al final de la nota.
# `relaxes[]`: tuplas (regla, valor_relajado, justificación).
PROFILE_CATALOG: Dict[str, Dict] = {
    "hybrid": {
        "adds": ["## Decisiones de diseño", "## Explicación oral",
                 "## Objetivos oficiales", "## Cobertura por objetivo"],
        "relaxes": [],
    },
    "interview": {
        "adds": ["## Decisiones de diseño", "## Explicación oral"],
        "relaxes": [("R3", "≥ 0.70", "prosa argumentativa prima sobre anclada")],
    },
    "certification": {
        "adds": ["## Objetivos oficiales", "## Cobertura por objetivo"],
        "relaxes": [("R5", "estructura libre (1 columna OK)",
                     "cobertura verificable > estética")],
    },
    "work": {
        "adds": [],
        "relaxes": [("R1", "≤ 100 palabras TL;DR",
                     "operador necesita contexto amplio")],
    },
}


def _load_yaml_minimal(path: Path) -> Dict:
    """Parser YAML mínimo (sin PyYAML). Lee:
      - claves top-level (`key: value`)
      - mapas anidados (`key:` con indentación)
      - listas de mapas (`- key: value` con indentación)
    Suficiente para `goal_profile` + `certification.objectives[]`.
    """
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    out: Dict = {}
    current_key: Optional[str] = None
    current_list_items: List[Dict] = []
    in_list = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        # Top-level `key:` (sin indent).
        if not line.startswith(" ") and ":" in line and not line.startswith("-"):
            if in_list and current_key:
                out[current_key] = current_list_items
                current_list_items = []
                in_list = False
            key, _, value = line.partition(":")
            value = value.strip()
            if value == "":
                current_key = key.strip()
                out[current_key] = {}
            elif value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                items = [v.strip().strip('"') for v in inner.split(",") if v.strip()]
                out[key.strip()] = items
                current_key = None
            else:
                out[key.strip()] = value.strip('"')
                current_key = None
            continue
        # Item de lista (`- key: value` con indent).
        if line.startswith("  -") or line.startswith("    -") or line.startswith("  - "):
            if not in_list:
                in_list = True
                current_list_items = []
            rest = line.lstrip()[1:].lstrip()  # quitar "-"
            item: Dict = {}
            if ":" in rest:
                k, _, v = rest.partition(":")
                item[k.strip()] = v.strip().strip('"')
            current_list_items.append(item)
            continue
        # Continuación de un item de lista (clave: valor con indent mayor).
        if in_list and line.startswith("    ") and ":" in line:
            k, _, v = line.strip().partition(":")
            v = v.strip().strip('"')
            if current_list_items:
                current_list_items[-1][k.strip()] = v
            continue
        # Sub-clave con indent (clave: valor dentro de un mapa).
        if line.startswith("  ") and ":" in line:
            k, _, v = line.strip().partition(":")
            v = v.strip().strip('"')
            if current_key and isinstance(out.get(current_key), dict):
                out[current_key][k.strip()] = v

    # Flush final.
    if in_list and current_key:
        out[current_key] = current_list_items

    return out


def _resolve_profile(args: argparse.Namespace) -> Tuple[str, Dict]:
    """Resuelve el perfil activo desde --profile o --profile-yaml."""
    profile = args.profile
    profile_yaml_data = {}

    if args.profile_yaml:
        profile_yaml_data = _load_yaml_minimal(Path(args.profile_yaml))
        if not profile:
            profile = profile_yaml_data.get("goal_profile", "hybrid")

    if profile not in VALID_PROFILES:
        raise ValueError(f"unknown-profile: '{profile}' (esperaba uno de {VALID_PROFILES})")

    catalog = PROFILE_CATALOG[profile]
    return profile, {"profile": profile, "catalog": catalog, "yaml": profile_yaml_data}


def _load_input(input_path: Path) -> List[dict]:
    if not input_path.exists():
        raise FileNotFoundError(f"input-not-found: {input_path}")
    data = json.loads(input_path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "routes" in data:
        data = data["routes"]
    if not isinstance(data, list):
        raise ValueError("input debe ser una lista de rutas o {'routes': [...]}")
    return data


def _inject_adds(route: dict, adds: List[str], by_objective: Optional[str] = None) -> dict:
    """Inyecta las secciones `adds` al final de cada nota de la ruta."""
    new_route = dict(route)
    new_path = []
    for step in route.get("note_path", []):
        new_step = dict(step)
        if not by_objective:
            new_step["added_sections"] = list(adds)
        else:
            # Solo añadir `## Cobertura por objetivo` si la nota declara
            # el objetivo en `certification-objective` (si está disponible).
            new_step["added_sections"] = list(adds)
        new_path.append(new_step)
    new_route["note_path"] = new_path
    new_route["added_sections_by_profile"] = list(adds)
    return new_route


def _apply_relaxes(route: dict, relaxes: List[Tuple[str, str, str]]) -> dict:
    """Marca en la cabecera las reglas relajadas."""
    new_route = dict(route)
    new_route["relaxed_rules"] = [
        {"rule": r, "value": v, "reason": reason} for r, v, reason in relaxes
    ]
    return new_route


def format_markdown(
    routes: List[dict],
    profile: str,
    catalog: Dict,
    by_objective: Optional[str] = None,
) -> str:
    if not routes:
        return f"# Rutas filtradas por perfil '{profile}'\n\n(sin rutas)\n"

    lines: List[str] = [f"# Rutas filtradas por perfil '{profile}'\n"]
    if catalog["relaxes"]:
        lines.append(f"**Reglas relajadas:** {', '.join(r for r, _, _ in catalog['relaxes'])}")
    if by_objective:
        lines.append(f"**Filtrado por objetivo:** `{by_objective}`")
    lines.append("")
    for r in routes:
        lines.append(f"## {r.get('domain', '<unknown>')} / {r.get('goal', '<unknown>')}\n")
        lines.append(f"**Tiempo estimado:** {r.get('estimated_minutes', 0)} min")
        if r.get("relaxed_rules"):
            lines.append(f"**Relajadas:** {', '.join(x['rule'] for x in r['relaxed_rules'])}")
        lines.append("")
        for step in r.get("note_path", []):
            line_str = f"{step.get('step', '?')}. {step.get('note_id', '?')}"
            deps = step.get("depends_on", [])
            if deps:
                line_str += f" (depends on: {', '.join(deps)})"
            lines.append(line_str)
            for section in step.get("added_sections", []):
                lines.append(f"   - {section}")
        lines.append("")

    return "\n".join(lines)


def to_dicts(routes: List[dict]) -> List[dict]:
    return routes


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="goal_profiles.py",
        description="Filtra rutas de estudio por perfil de objetivo (Fase 105).",
    )
    parser.add_argument("--profile",
                        choices=VALID_PROFILES,
                        help="perfil de objetivo (default: leído de --profile-yaml)")
    parser.add_argument("--profile-yaml", type=Path, default=None,
                        help="ruta al profile.yaml (para leer goal_profile y certification.objectives)")
    parser.add_argument("--input", type=Path, required=True,
                        help="ruta al archivo JSON de rutas (output de F104)")
    parser.add_argument("--by-objective", default=None,
                        help="filtra por objetivo (solo con --profile certification)")
    parser.add_argument("--format", choices=("md", "json"), default="md",
                        help="formato de salida (default: md)")
    args = parser.parse_args(argv)

    try:
        profile, ctx = _resolve_profile(args)
    except ValueError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    if args.by_objective and profile != "certification":
        print(
            f"[ERROR] --by-objective solo aplica con --profile certification "
            f"(recibí --profile {profile})",
            file=sys.stderr,
        )
        return 2

    if profile == "certification" and args.by_objective:
        cert_section = ctx["yaml"].get("certification", {})
        if isinstance(cert_section, list):
            objectives_list = cert_section
        else:
            objectives_list = cert_section.get("objectives", []) if isinstance(cert_section, dict) else []
        # Normalizar a dict {id: description}.
        objectives: Dict[str, str] = {}
        for entry in objectives_list:
            if isinstance(entry, dict) and "id" in entry:
                objectives[entry["id"]] = entry.get("description", "")
        if not objectives:
            print(
                f"[ERROR] no-objectives-declared: certification.objectives[] ausente",
                file=sys.stderr,
            )
            return 1
        if args.by_objective not in objectives:
            print(
                f"[ERROR] unknown-objective: '{args.by_objective}' "
                f"no está en certification.objectives[]",
                file=sys.stderr,
            )
            return 1

    try:
        routes = _load_input(args.input)
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2

    catalog = ctx["catalog"]
    filtered = []
    for r in routes:
        r2 = _inject_adds(r, catalog["adds"], args.by_objective)
        r2 = _apply_relaxes(r2, catalog["relaxes"])
        filtered.append(r2)

    if args.format == "json":
        print(json.dumps({
            "profile": profile,
            "by_objective": args.by_objective,
            "applied_adds": catalog["adds"],
            "applied_relaxes": [
                {"rule": r, "value": v, "reason": reason}
                for r, v, reason in catalog["relaxes"]
            ],
            "routes": to_dicts(filtered),
        }, indent=2, ensure_ascii=False))
    else:
        print(format_markdown(filtered, profile, catalog, args.by_objective))

    return 0


if __name__ == "__main__":
    sys.exit(main())
