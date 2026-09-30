#!/usr/bin/env python3
"""cross_target.py — F63 · Verificación de equivalencia entre destinos.

Compara el contenido textual de cada IR con el artifact renderizado por cada
destino (obsidian, markdown, html_pdf, notion_md, appflowy, notion_api,
flashcards) y verifica que toda unidad del IR aparezca en el artifact, ya sea
directamente o cubierta por una degradación declarada (criterio 1).

Criterios cubiertos:
- C1: toda diferencia entre IR y artifact está justificada por una
  degradación en `reports/render-degradation.json` con `content_intact: true`.
- C2: cero pérdidas de unidad en cualquier destino (las unidades
  presentes en el IR aparecen en el artifact o están justificadas).
- C3: corre sobre los ejemplos de cada release (fixtures en
  `evals/cross-target-sample/fixtures/`).

Uso:
    python3 scripts/validate/cross_target.py --ir <path> --out-dir <dir>
                                            [--destinations <csv>]
                                            [--report-out <path>]

Dependencias: Python 3.9+ stdlib puro (sin HTTP).
Códigos de salida:
    0 — PASS (sin pérdidas reales).
    1 — FAIL (al menos 1 pérdida real detectada).
    2 — Uso incorrecto (paths faltantes, etc.).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import importlib.util as _importlib_util
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


# Comparte atomic_write_json con F38+.
_IO_PATH = (
    Path(__file__).resolve().parent.parent / "util" / "_io.py"
)
_spec = _importlib_util.spec_from_file_location("_skill_io", _IO_PATH)
_io_mod = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_io_mod)
_atomic_write_json = _io_mod.atomic_write_json


EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

# Tipos de nodo del IR que tienen contenido textual comparable.
COMPARABLE_NODE_KINDS: Set[str] = {
    "section", "paragraph", "list", "checklist", "table",
    "code", "equation", "quote", "callout", "admonition",
    "collapsible", "figure", "question", "step", "parameter-table",
}


# ---------------------------------------------------------------------------
# Modelo
# ---------------------------------------------------------------------------


@dataclass
class UnitStatus:
    node_path: str
    capability: str
    node_type: str
    canonical: str
    in_artifact: bool
    justified: bool
    degradation_id: Optional[str] = None


@dataclass
class CompareResult:
    destination: str
    note_id: str
    units_total: int
    units_present: int
    units_justified: int
    units_lost: int
    units: List[UnitStatus] = field(default_factory=list)


@dataclass
class CrossTargetReport:
    schema_version: str = "1.0.0"
    generated_at: str = ""
    destinations: List[str] = field(default_factory=list)
    notes: Dict[str, Dict[str, CompareResult]] = field(default_factory=dict)
    summary: Dict[str, int] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


def _now_utc_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_text(s: str) -> str:
    """Normaliza texto para comparación: lowercase, sin markup, sin espacios extra."""
    if not s:
        return ""
    # Remover tags HTML.
    s = re.sub(r"<[^>]+>", " ", s)
    # Remover fences markdown.
    s = re.sub(r"```[a-z]*\n?", "", s)
    # Remover emojis y símbolos decorativos.
    s = re.sub(r"[\U0001F000-\U0001FFFF]", " ", s)
    # Remover sintaxis markdown común.
    s = re.sub(r"[#*_>`~]+", " ", s)
    # Normalizar whitespace.
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def _canonical_text(node: Dict[str, Any]) -> str:
    """Extrae el texto canónico comparable de un nodo IR."""
    kind = node.get("node", "")

    if kind == "section":
        text = _flatten_inline_text(node.get("children", []))
        return _normalize_text(text)

    if kind == "paragraph":
        text = _flatten_inline_text(node.get("children", []))
        return _normalize_text(text)

    if kind in ("list", "checklist"):
        parts: List[str] = []
        for item in node.get("children", []):
            parts.append(_flatten_inline_text(item.get("children", [])))
        return _normalize_text(" ".join(parts))

    if kind == "table":
        parts = []
        for row in node.get("children", []) or []:
            row_text = []
            for cell in row.get("children", []) or []:
                row_text.append(_flatten_inline_text(cell.get("children", [])))
            parts.append(" ".join(row_text))
        return _normalize_text(" ".join(parts))

    if kind == "parameter-table":
        parts = []
        for row in node.get("children", []) or []:
            row_text = []
            for cell in row.get("children", []) or []:
                row_text.append(_flatten_inline_text(cell.get("children", [])))
            parts.append(" ".join(row_text))
        return _normalize_text(" ".join(parts))

    if kind == "code":
        return _normalize_text(attrs.get("text", "") or "")

    if kind == "equation":
        return _normalize_text(attrs.get("latex", "") or "")

    if kind == "quote":
        body = _flatten_inline_text(node.get("children", []))
        cite = (node.get("attrs", {}) or {}).get("cite", "") or ""
        return _normalize_text(f"{body} {cite}")

    if kind in ("callout", "admonition"):
        attrs = node.get("attrs", {}) or {}
        title = attrs.get("title", "") or ""
        body = _flatten_inline_text(node.get("children", []))
        return _normalize_text(f"{title} {body}")

    if kind == "collapsible":
        attrs = node.get("attrs", {}) or {}
        title = attrs.get("title", "") or ""
        body = _flatten_inline_text(node.get("children", []))
        return _normalize_text(f"{title} {body}")

    if kind == "figure":
        attrs = node.get("attrs", {}) or {}
        caption = attrs.get("caption", "") or ""
        return _normalize_text(caption)

    if kind == "question":
        prompt = attrs.get("prompt", "") or ""
        body = _flatten_inline_text(node.get("children", []))
        return _normalize_text(f"{prompt} {body}")

    if kind == "step":
        attrs = node.get("attrs", {}) or {}
        idx = attrs.get("index", "")
        body = _flatten_inline_text(node.get("children", []))
        return _normalize_text(f"Paso {idx} {body}")

    return ""


def _flatten_inline_text(children: List[Dict[str, Any]]) -> str:
    """Concatena texto inline preservando estructura básica."""
    parts: List[str] = []

    def _walk(node: Any) -> None:
        if not isinstance(node, dict):
            return
        kind = node.get("node", "")
        attrs = node.get("attrs", {}) or {}
        if kind == "text":
            parts.append(attrs.get("text", "") or "")
        elif kind == "code-inline":
            parts.append(f"`{attrs.get('text', '') or ''}`")
        elif kind == "link-external":
            parts.append(attrs.get("text", "") or "")
        elif kind == "link-note":
            parts.append(attrs.get("text", "") or attrs.get("target", ""))
        elif kind in ("strong", "em", "deleted"):
            inner = _flatten_inline_text(node.get("children", []))
            parts.append(inner)
        elif kind == "math-inline":
            parts.append(attrs.get("latex", "") or "")
        else:
            parts.append(attrs.get("text", "") or "")
        for child in node.get("children", []) or []:
            _walk(child)

    for c in children or []:
        _walk(c)
    return "".join(parts).strip()


def traverse_ir(ir: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    """Recorrido depth-first del IR; devuelve (path, node) para cada nodo."""
    out: List[Tuple[str, Dict[str, Any]]] = []

    def _walk(node: Any, path: str, idx: int) -> None:
        if not isinstance(node, dict):
            return
        child_path = f"{path}/{idx}"
        out.append((child_path, node))
        children = node.get("children", [])
        if isinstance(children, list):
            for i, child in enumerate(children):
                _walk(child, child_path, i)

    children = ir.get("children", [])
    if isinstance(children, list):
        for i, child in enumerate(children):
            _walk(child, "0", i)
    return out


def _node_in_artifact(canonical: str, artifact: str, min_match: float = 0.8) -> bool:
    """Verifica si el texto canónico del IR aparece en el artifact.

    Usa una heurística de match: el texto canónico normalizado debe aparecer
    como substring o con match ≥80% en el artifact normalizado.
    """
    if not canonical or not artifact:
        return False
    art_norm = _normalize_text(artifact)
    if canonical in art_norm:
        return True
    # Match por palabras: ≥80% de las palabras del IR aparecen en el artifact.
    ir_words = set(canonical.split())
    if not ir_words:
        return False
    art_words = set(art_norm.split())
    common = ir_words & art_words
    return len(common) / len(ir_words) >= min_match


def _degradation_covers(node_path: str, degradations: List[Dict[str, Any]]
                         ) -> Tuple[bool, Optional[str]]:
    """Verifica si una unidad está cubierta por una degradación declarada."""
    for d in degradations:
        if d.get("content_intact") is not True:
            continue
        d_path = d.get("node_path", "")
        # Match exacto o prefijo (la degradación cubre el nodo y sus hijos).
        if d_path == node_path or node_path.startswith(d_path + "/") or d_path.startswith(node_path):
            return True, d.get("id")
    return False, None


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------


def load_irs(ir_arg: Path) -> List[Dict[str, Any]]:
    if ir_arg.is_dir():
        return [json.loads(p.read_text(encoding="utf-8"))
                for p in sorted(ir_arg.glob("*.json"))]
    return [json.loads(ir_arg.read_text(encoding="utf-8"))]


def _destination_subdir(dest: str) -> Tuple[str, str]:
    """Mapeo destino → (subdir, extension).

    Cada destino tiene su propio subdir en `render/<dest>/`. Aunque obsidian
    y markdown producen archivos .md, cada renderer escribe a su propio
    subdir. Por tanto, cada destino tiene una ruta única.
    """
    if dest in ("obsidian", "notion_md", "appflowy", "markdown"):
        return dest, ".md"
    if dest == "html_pdf":
        return "html_pdf", ".html"
    if dest == "notion_api":
        return "notion_api/payloads", ".json"
    if dest == "flashcards":
        return "flashcards", ".csv"
    return "", ""


def _load_rendered_artifact(out_dir: Path, note_id: str,
                              destination: str) -> Optional[str]:
    subdir, ext = _destination_subdir(destination)
    if not subdir:
        return None
    path = out_dir / "render" / subdir / f"{note_id}{ext}"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def _load_degradation_report(out_dir: Path,
                              destination: str) -> List[Dict[str, Any]]:
    """Lee las degradaciones del report para el destino dado.

    Si el report tiene `target == destination`, lo usa directamente.
    Si tiene `target == "all"` o si no hay report específico, retorna las
    degradaciones como cobertura cross-destination (la degradación se
    aplica a cualquier destino que reciba el IR).
    """
    report_path = out_dir / "reports" / "render-degradation.json"
    if not report_path.exists():
        return []
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    target = data.get("target")
    # Si el target del report es "all" o coincide con el destino, retorna todo.
    if target == "all" or target == destination:
        return data.get("degradations", []) or []
    # Fallback: retorna las degradaciones (puede aplicarse cross-destination).
    return data.get("degradations", []) or []


# ---------------------------------------------------------------------------
# Comparación
# ---------------------------------------------------------------------------


def compare_ir_to_destination(
    ir_obj: Dict[str, Any],
    destination: str,
    artifact: Optional[str],
    degradations: List[Dict[str, Any]],
) -> CompareResult:
    """Compara un IR con el artifact renderizado para un destino."""
    note_id = str(ir_obj.get("note_id", ""))
    units: List[UnitStatus] = []
    for path, node in traverse_ir(ir_obj):
        kind = node.get("node", "")
        if kind not in COMPARABLE_NODE_KINDS:
            continue
        canonical = _canonical_text(node)
        if not canonical or len(canonical) < 3:
            continue  # Ignorar nodos sin texto o triviales.
        attrs = node.get("attrs", {}) or {}
        capability = attrs.get("capability", kind)
        in_artifact = _node_in_artifact(canonical, artifact) if artifact else False
        justified = False
        deg_id = None
        if not in_artifact:
            justified, deg_id = _degradation_covers(path, degradations)
        units.append(UnitStatus(
            node_path=path,
            capability=capability,
            node_type=kind,
            canonical=canonical,
            in_artifact=in_artifact,
            justified=justified,
            degradation_id=deg_id,
        ))

    units_present = sum(1 for u in units if u.in_artifact)
    units_justified = sum(1 for u in units if u.justified)
    units_lost = sum(1 for u in units if not u.in_artifact and not u.justified)

    return CompareResult(
        destination=destination,
        note_id=note_id,
        units_total=len(units),
        units_present=units_present,
        units_justified=units_justified,
        units_lost=units_lost,
        units=units,
    )


def build_cross_target_report(
    irs: List[Dict[str, Any]],
    destinations: List[str],
    out_dir: Path,
) -> CrossTargetReport:
    """Compara cada IR contra cada destino y agrega resultados."""
    notes_results: Dict[str, Dict[str, CompareResult]] = {}

    for ir in irs:
        note_id = str(ir.get("note_id", ""))
        notes_results[note_id] = {}
        for dest in destinations:
            artifact = _load_rendered_artifact(out_dir, note_id, dest)
            degradations = _load_degradation_report(out_dir, dest)
            result = compare_ir_to_destination(ir, dest, artifact, degradations)
            notes_results[note_id][dest] = result

    total = sum(r.units_total
                 for note in notes_results.values()
                 for r in note.values())
    present = sum(r.units_present
                  for note in notes_results.values()
                  for r in note.values())
    justified = sum(r.units_justified
                    for note in notes_results.values()
                    for r in note.values())
    lost = sum(r.units_lost
               for note in notes_results.values()
               for r in note.values())

    return CrossTargetReport(
        schema_version="1.0.0",
        generated_at=_now_utc_iso(),
        destinations=destinations,
        notes=notes_results,
        summary={
            "total_units": total,
            "units_present": present,
            "units_justified": justified,
            "units_lost": lost,
            "notes": len(notes_results),
            "destinations": len(destinations),
        }
    )


# ---------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------


def report_to_dict(report: CrossTargetReport) -> Dict[str, Any]:
    return {
        "schema_version": report.schema_version,
        "generated_at": report.generated_at,
        "destinations": report.destinations,
        "summary": report.summary,
        "notes": {
            note_id: {
                dest: {
                    "destination": r.destination,
                    "note_id": r.note_id,
                    "units_total": r.units_total,
                    "units_present": r.units_present,
                    "units_justified": r.units_justified,
                    "units_lost": r.units_lost,
                    "lost_units": [
                        {
                            "node_path": u.node_path,
                            "node_type": u.node_type,
                            "capability": u.capability,
                            "canonical": u.canonical[:80],
                            "in_artifact": u.in_artifact,
                            "justified": u.justified,
                        }
                        for u in r.units
                        if not u.in_artifact and not u.justified
                    ],
                }
                for dest, r in dests.items()
            }
            for note_id, dests in report.notes.items()
        }
    }


def report_to_markdown(report: CrossTargetReport) -> str:
    md = [
        "# Reporte de equivalencia cross-target — F63",
        "",
        f"- **schema_version:** {report.schema_version}",
        f"- **generated_at:** {report.generated_at}",
        f"- **destinations:** {', '.join(report.destinations)}",
        "",
        "## Resumen",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        f"| Notas | {report.summary.get('notes', 0)} |",
        f"| Destinos | {report.summary.get('destinations', 0)} |",
        f"| Unidades totales | {report.summary.get('total_units', 0)} |",
        f"| Presentes en artifact | {report.summary.get('units_present', 0)} |",
        f"| Cubiertas por degradación | {report.summary.get('units_justified', 0)} |",
        f"| Pérdidas reales (sin justificar) | {report.summary.get('units_lost', 0)} |",
        "",
    ]
    if report.summary.get("units_lost", 0) > 0:
        md.append("## Pérdidas reales detectadas")
        md.append("")
        for note_id, dests in report.notes.items():
            for dest, r in dests.items():
                for u in r.units:
                    if not u.in_artifact and not u.justified:
                        md.append(f"- `{note_id}` → `{dest}` ({u.node_type}/{u.capability}): `{u.canonical[:60]}`")
        md.append("")
    md.append("## Por nota y destino")
    md.append("")
    for note_id, dests in report.notes.items():
        md.append(f"### {note_id}")
        md.append("")
        md.append("| Destino | Total | Presentes | Justificadas | Pérdidas |")
        md.append("|---|---|---|---|---|")
        for dest, r in dests.items():
            md.append(f"| {dest} | {r.units_total} | {r.units_present} | "
                     f"{r.units_justified} | {r.units_lost} |")
        md.append("")
    return "\n".join(md)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_destinations(raw: str) -> List[str]:
    return [d.strip() for d in raw.split(",") if d.strip()]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cross_target.py",
        description="Verificación de equivalencia entre destinos (F63).",
    )
    parser.add_argument("--ir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path,
                        help="Directorio con render/<dest>/<note>.{md,html} y reports/render-degradation.json")
    parser.add_argument("--destinations", type=str,
                        default="obsidian,notion_api,notion_md,appflowy,markdown,html_pdf,flashcards",
                        help="CSV de destinos a verificar")
    parser.add_argument("--report-out", type=Path, default=None,
                        help="Path de salida del reporte (default: <out-dir>/reports/cross-target-report.json)")

    args = parser.parse_args(argv)

    if not args.ir.exists():
        print(f"ERROR: --ir no encontrado: {args.ir}", file=sys.stderr)
        return EXIT_USAGE
    if not args.out_dir.exists():
        print(f"ERROR: --out-dir no encontrado: {args.out_dir}", file=sys.stderr)
        return EXIT_USAGE

    irs = load_irs(args.ir)
    if not irs:
        print(f"ERROR: no hay IRs en {args.ir}", file=sys.stderr)
        return EXIT_USAGE

    destinations = _parse_destinations(args.destinations)
    if not destinations:
        print(f"ERROR: destinations vacío", file=sys.stderr)
        return EXIT_USAGE

    report = build_cross_target_report(irs, destinations, args.out_dir)

    report_path = args.report_out or (args.out_dir / "reports" / "cross-target-report.json")
    md_path = report_path.with_suffix(".md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(report_path, report_to_dict(report))
    md_path.write_text(report_to_markdown(report), encoding="utf-8")

    s = report.summary
    print(f"cross_target: total={s.get('total_units', 0)}, "
          f"present={s.get('units_present', 0)}, "
          f"justified={s.get('units_justified', 0)}, "
          f"lost={s.get('units_lost', 0)}")
    print(f"     reporte: {report_path}")
    if s.get("units_lost", 0) > 0:
        return EXIT_FAIL
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
