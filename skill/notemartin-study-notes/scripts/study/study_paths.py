#!/usr/bin/env python3
"""Generador de rutas de estudio — Fase 104.

Implementa las 6 reglas Q1-Q6 definidas en
`references/09-study/study-paths.md` §6:

  Q1 — Lectura del grafo: carga `knowledge/concept-graph.json` y extrae
       las rutas existentes (shortest + broadest) por dominio y
       `goal_concept_id`.
  Q2 — Lectura del note-plan: carga `knowledge/note-plan.json` y construye
       el mapa `concept_id → note_id` + `note_id → depends_on[]`.
  Q3 — Tiempo estimado: para cada `note_id` en el `note_path`, busca
       `reading-time-minutes` en `ir/<note_id>.json` o `notemark/<note-id>.nm`.
  Q4 — Emisión de las 3 rutas (`operate-hoy` | `entender-a-fondo` |
       `repasar`).
  Q5 — Puntos de verificación (R-P4): si el dominio tiene ≥ 1 nota
       `practice`, usa `type: practice`; si no, usa `type: auto-eval`.
  Q6 — Emisión Markdown o JSON estructurado.

CLI:
    python3 study_paths.py --domain postgresql --goal all
    python3 study_paths.py --domain docker --goal operate-hoy --format json
    python3 study_paths.py --domain all --goal repasar --workdir /path/to/workdir
    python3 study_paths.py --errors-dir /path/to/study/errors

Exit codes:
    0  OK (≥ 1 ruta emitida)
    1  rutas insuficientes o violación de strict
    2  error de uso o archivos no encontrados

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


VALID_GOALS = ("operate-hoy", "entender-a-fondo", "repasar")

ERROR_H3_RE = re.compile(r"^###\s+Error\s+([\w\-]+(?:-[\w\-]+)*)\s*$", re.MULTILINE)
REVIEW_NEXT_RE = re.compile(
    r"review-next:\s*(\d{4}-\d{2}-\d{2})",
    re.IGNORECASE,
)
NOTE_LINK_RE = re.compile(r"\[\[note:([a-z0-9][a-z0-9\-]*(?:#[\w\-§]+)?)\]\]")


@dataclass
class PathStep:
    note_id: str
    step: int
    depends_on: List[str] = field(default_factory=list)
    is_practice: bool = False
    has_autoeval: bool = False


@dataclass
class Checkpoint:
    after_step: int
    type: str  # "practice" | "auto-eval"
    note_id: str
    description: str = ""


@dataclass
class Route:
    domain: str
    goal: str
    note_path: List[PathStep] = field(default_factory=list)
    estimated_minutes: int = 0
    checkpoints: List[Checkpoint] = field(default_factory=list)
    coincides_with_shortest: bool = False


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _read_reading_time(workdir: Path, note_id: str) -> Optional[int]:
    """Busca `reading-time-minutes` en `ir/<note_id>.json` o `notemark/<note-id>.nm`.

    Returns el int si lo encuentra, None en caso contrario.
    """
    # IR JSON.
    ir_path = workdir / "ir" / f"{note_id}.json"
    if ir_path.exists():
        try:
            data = _load_json(ir_path)
            rtm = data.get("frontmatter", {}).get("reading-time-minutes")
            if rtm:
                return int(rtm)
        except (json.JSONDecodeError, ValueError):
            pass

    # NoteMark (.nm).
    for ext in (".nm", ".md"):
        nm_path = workdir / "notemark" / f"{note_id}{ext}"
        if nm_path.exists():
            fm = _parse_frontmatter_min(nm_path.read_text(encoding="utf-8"))
            rtm = fm.get("reading-time-minutes")
            if rtm:
                try:
                    return int(rtm)
                except ValueError:
                    pass

    return None


def _topological_sort(
    concepts: List[str],
    depends_on_map: Dict[str, List[str]],
) -> List[str]:
    """Ordena `concepts` por dependencias (topological sort con memoización).

    Si hay empate, desempata lexicográficamente.
    """
    visited: Dict[str, int] = {}  # 0 = visiting, 1 = done
    result: List[str] = []

    def visit(c: str) -> None:
        if visited.get(c) == 1:
            return
        if visited.get(c) == 0:
            # Ciclo: lo añadimos al final sin recursión.
            result.append(c)
            visited[c] = 1
            return
        visited[c] = 0
        for dep in sorted(depends_on_map.get(c, [])):
            if dep in concepts:
                visit(dep)
        visited[c] = 1
        result.append(c)

    for c in sorted(concepts):
        visit(c)

    return result


def _has_practice(workdir: Path, note_id: str) -> bool:
    """Verifica si una nota es de tipo `practice`."""
    for ext in (".nm", ".md"):
        nm_path = workdir / "notemark" / f"{note_id}{ext}"
        if nm_path.exists():
            fm = _parse_frontmatter_min(nm_path.read_text(encoding="utf-8"))
            if fm.get("note-type") == "practice":
                return True
    return False


def _has_autoeval(workdir: Path, note_id: str) -> bool:
    """Verifica si una nota tiene sección `## Autoevaluación`."""
    for ext in (".nm", ".md"):
        nm_path = workdir / "notemark" / f"{note_id}{ext}"
        if nm_path.exists():
            text = nm_path.read_text(encoding="utf-8")
            if re.search(r"^##\s+Autoevaluaci[oó]n\s*$", text, re.MULTILINE):
                return True
    return False


def _read_living_doc(errors_dir: Path, domain: str) -> Optional[dict]:
    """Lee `study/errors/<domain>.md` si existe.

    Returns dict con `entries` (lista de `{error_id, concepto,
    review_next, note_link}`) o None si no existe.
    """
    path = errors_dir / f"error-log-{domain}.md"
    if not path.exists():
        path = errors_dir / f"{domain}.md"
    if not path.exists():
        return None

    text = path.read_text(encoding="utf-8")
    entries = []
    matches = list(ERROR_H3_RE.finditer(text))
    for idx, m in enumerate(matches):
        error_id = m.group(1)
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        section = text[start:end]

        concepto_match = re.search(
            r"^####\s+Concepto\s*$(.*?)(?=^####\s+|^###\s+|\Z)",
            section, re.MULTILINE | re.DOTALL,
        )
        concepto = concepto_match.group(1).strip() if concepto_match else ""

        repaso_match = re.search(
            r"^####\s+Repaso\s*$(.*?)(?=^####\s+|^###\s+|\Z)",
            section, re.MULTILINE | re.DOTALL,
        )
        repaso = repaso_match.group(1) if repaso_match else ""
        review_match = REVIEW_NEXT_RE.search(repaso)
        review_next = review_match.group(1) if review_match else None

        correccion_match = re.search(
            r"^####\s+Correcci[oó]n\s*$(.*?)(?=^####\s+|^###\s+|\Z)",
            section, re.MULTILINE | re.DOTALL,
        )
        correccion = correccion_match.group(1) if correccion_match else ""
        note_match = NOTE_LINK_RE.search(correccion)
        note_link = note_match.group(1) if note_match else None

        entries.append({
            "error_id": error_id,
            "concepto": concepto,
            "review_next": review_next,
            "note_link": note_link,
        })
    return {"entries": entries}


def _build_route(
    domain: str,
    goal: str,
    concept_path: List[str],
    concept_to_note: Dict[str, str],
    note_meta: Dict[str, dict],
    workdir: Path,
    errors_dir: Path,
) -> Route:
    route = Route(domain=domain, goal=goal)

    if not concept_path:
        return route

    # Map concepts → notes; saltar concepts sin nota asignada.
    note_ids: List[str] = []
    skipped: List[str] = []
    for c in concept_path:
        nid = concept_to_note.get(c)
        if nid:
            note_ids.append(nid)
        else:
            skipped.append(c)

    # Topological sort con depends_on del note-plan.
    depends_on_map: Dict[str, List[str]] = {}
    for nid in note_ids:
        deps = note_meta.get(nid, {}).get("depends_on", [])
        depends_on_map[nid] = [d for d in deps if d in note_ids]

    ordered = _topological_sort(note_ids, depends_on_map)

    # Construir steps.
    total_minutes = 0
    for step_idx, nid in enumerate(ordered, 1):
        deps = depends_on_map.get(nid, [])
        step = PathStep(
            note_id=nid,
            step=step_idx,
            depends_on=deps,
            is_practice=_has_practice(workdir, nid),
            has_autoeval=_has_autoeval(workdir, nid),
        )
        route.note_path.append(step)

        rtm = _read_reading_time(workdir, nid)
        if rtm:
            total_minutes += rtm

    route.estimated_minutes = total_minutes

    # Checkpoints (R-P4).
    # 1) Buscar primer nodo con `practice`.
    practice_step = next(
        (s for s in route.note_path if s.is_practice), None
    )
    if practice_step:
        route.checkpoints.append(Checkpoint(
            after_step=practice_step.step,
            type="practice",
            note_id=practice_step.note_id,
            description=f"Ejecutar el lab en `notemark/{practice_step.note_id}.nm` antes de continuar.",
        ))
    else:
        # 2) Fallback a auto-eval (F102).
        autoeval_step = next(
            (s for s in route.note_path if s.has_autoeval), None
        )
        if autoeval_step:
            route.checkpoints.append(Checkpoint(
                after_step=autoeval_step.step,
                type="auto-eval",
                note_id=autoeval_step.note_id,
                description=f"Responder `## Autoevaluación` en `notemark/{autoeval_step.note_id}.nm` antes de continuar.",
            ))

    return route


def _build_repasar_route(
    domain: str,
    shortest_route: Route,
    living_doc: dict,
    concept_to_note: Dict[str, str],
    workdir: Path,
) -> Route:
    """Construye la ruta `repasar` a partir de la ruta shortest + entradas
    del living-doc intercaladas por `review-next` ascendente."""
    route = Route(domain=domain, goal="repasar")

    # Primero copiar la ruta shortest (solo note_id).
    base_steps = list(shortest_route.note_path)

    # Intercalar entradas del living-doc tras el último paso.
    entries = sorted(
        [e for e in living_doc["entries"] if e.get("note_link")],
        key=lambda e: e.get("review_next") or "9999-12-31",
    )

    if not entries:
        # Sin entradas válidas, emitir la misma ruta shortest con `goal: repasar`.
        route.note_path = list(base_steps)
        route.estimated_minutes = shortest_route.estimated_minutes
        route.checkpoints = list(shortest_route.checkpoints)
        route.coincides_with_shortest = True
        return route

    # Insertar entradas del living-doc como pasos adicionales con `note_id`
    # apuntando al `note_link` canónico y `step` incremental.
    next_step = max((s.step for s in base_steps), default=0) + 1
    for entry in entries:
        nid = entry["note_link"]
        if not nid or not _has_note(workdir, nid):
            continue
        step = PathStep(
            note_id=f"[error] {entry['error_id']} → {nid}",
            step=next_step,
            depends_on=[],
            is_practice=False,
            has_autoeval=False,
        )
        route.note_path.append(step)
        rtm = _read_reading_time(workdir, nid)
        if rtm:
            route.estimated_minutes += rtm
        next_step += 1

    # Copiar checkpoints de la ruta base.
    route.checkpoints = list(shortest_route.checkpoints)

    return route


def _has_note(workdir: Path, note_id: str) -> bool:
    for ext in (".nm", ".md"):
        if (workdir / "notemark" / f"{note_id}{ext}").exists():
            return True
    return False


def collect_routes(
    workdir: Path,
    domain_filter: Optional[str],
    goal_filter: str,
    errors_dir: Path,
) -> List[Route]:
    graph_path = workdir / "knowledge" / "concept-graph.json"
    plan_path = workdir / "knowledge" / "note-plan.json"

    if not graph_path.exists():
        print(f"[ERROR] no existe {graph_path}", file=sys.stderr)
        return []
    if not plan_path.exists():
        print(f"[ERROR] no existe {plan_path}", file=sys.stderr)
        return []

    graph = _load_json(graph_path)
    plan = _load_json(plan_path)

    # Q2: mapa concept → note.
    concept_to_note: Dict[str, str] = {}
    note_meta: Dict[str, dict] = {}
    for n in plan.get("notes", []):
        for cid in n.get("concept_ids", []):
            concept_to_note[cid] = n["note_id"]
        note_meta[n["note_id"]] = {
            "depends_on": n.get("depends_on", []),
            "study_path_goals": n.get("study-path-goals"),
            "note_type": n.get("note-type"),
        }

    # Q1: agrupar rutas del grafo por dominio.
    routes_by_domain: Dict[str, Dict[str, dict]] = {}
    for r in graph.get("routes", []):
        routes_by_domain.setdefault(r["domain"], {}).setdefault(
            r["strategy"], r
        )

    goals = VALID_GOALS if goal_filter == "all" else [goal_filter]
    domains = sorted(routes_by_domain.keys())
    if domain_filter and domain_filter != "all":
        domains = [domain_filter]

    out_routes: List[Route] = []
    for domain in domains:
        strat_map = routes_by_domain[domain]
        shortest = strat_map.get("shortest")
        broadest = strat_map.get("broadest")
        if not shortest:
            continue

        # Encontrar el `goal_concept_id` con mayor out_degree.
        goal_concept = shortest.get("goal_concept_id", "")
        concept_path = shortest.get("path", [])

        if "operate-hoy" in goals:
            r = _build_route(
                domain, "operate-hoy", concept_path,
                concept_to_note, note_meta, workdir, errors_dir,
            )
            out_routes.append(r)

        if "entender-a-fondo" in goals:
            if broadest and broadest.get("path") != shortest.get("path"):
                r = _build_route(
                    domain, "entender-a-fondo", broadest["path"],
                    concept_to_note, note_meta, workdir, errors_dir,
                )
            else:
                # Sin `broadest` distinto, usar `shortest` y marcarlo.
                r = _build_route(
                    domain, "entender-a-fondo", concept_path,
                    concept_to_note, note_meta, workdir, errors_dir,
                )
                r.coincides_with_shortest = True
            out_routes.append(r)

        if "repasar" in goals:
            living_doc = _read_living_doc(errors_dir, domain)
            if living_doc and living_doc.get("entries"):
                shortest_route = _build_route(
                    domain, "operate-hoy", concept_path,
                    concept_to_note, note_meta, workdir, errors_dir,
                )
                r = _build_repasar_route(
                    domain, shortest_route, living_doc,
                    concept_to_note, workdir,
                )
                out_routes.append(r)

    return out_routes


def format_markdown(routes: List[Route]) -> str:
    if not routes:
        return "(sin rutas)\n"

    lines: List[str] = []
    by_domain: Dict[str, List[Route]] = {}
    for r in routes:
        by_domain.setdefault(r.domain, []).append(r)

    for domain in sorted(by_domain.keys()):
        lines.append(f"# Rutas de estudio — {domain}\n")
        for r in by_domain[domain]:
            lines.append(f"## {r.goal}\n")
            lines.append(f"**Tiempo estimado:** {r.estimated_minutes} min\n")
            if r.coincides_with_shortest:
                lines.append("*Nota: este dominio no tiene ruta `broadest` distinta; se usa la misma ruta que `operate-hoy`.*\n")
            lines.append("")
            if not r.note_path:
                lines.append("_Sin notas en la ruta._\n")
                continue
            lines.append("1. " + r.note_path[0].note_id)
            for step in r.note_path[1:]:
                deps = ", ".join(step.depends_on) if step.depends_on else "—"
                lines.append(f"{step.step}. {step.note_id} (depends on: {deps})")
            lines.append("")
            if r.checkpoints:
                lines.append("**Checkpoints:**")
                for cp in r.checkpoints:
                    lines.append(f"- Tras paso {cp.after_step}: {cp.description}")
            else:
                lines.append("**Checkpoints:** _ninguno (warning R-P4)_")
            lines.append("")
    return "\n".join(lines)


def to_dicts(routes: List[Route]) -> List[dict]:
    out: List[dict] = []
    for r in routes:
        out.append({
            "domain": r.domain,
            "goal": r.goal,
            "note_path": [
                {
                    "note_id": s.note_id,
                    "step": s.step,
                    "depends_on": list(s.depends_on),
                }
                for s in r.note_path
            ],
            "estimated_minutes": r.estimated_minutes,
            "checkpoints": [
                {
                    "after_step": cp.after_step,
                    "type": cp.type,
                    "note_id": cp.note_id,
                    "description": cp.description,
                }
                for cp in r.checkpoints
            ],
            "coincides_with_shortest": r.coincides_with_shortest,
        })
    return out


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="study_paths.py",
        description="Genera rutas de estudio por dominio y objetivo (Fase 104).",
    )
    parser.add_argument("--domain", default="all",
                        help="dominio (kebab-case slug) o 'all'")
    parser.add_argument("--goal", default="all",
                        choices=("all",) + VALID_GOALS,
                        help="objetivo de la ruta")
    parser.add_argument("--workdir", type=Path, default=Path("."),
                        help="raíz del workdir (default: directorio actual)")
    parser.add_argument("--errors-dir", type=Path, default=Path("study/errors"),
                        help="directorio con living-docs de errores (default: study/errors/)")
    parser.add_argument("--format", choices=("md", "json"), default="md",
                        help="formato de salida (default: md)")
    args = parser.parse_args(argv)

    routes = collect_routes(
        args.workdir, args.domain, args.goal, args.errors_dir,
    )

    if args.format == "json":
        print(json.dumps(to_dicts(routes), indent=2, ensure_ascii=False))
    else:
        print(format_markdown(routes))

    if not routes:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
