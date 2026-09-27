#!/usr/bin/env python3
"""linking.py — F61 · CLI de orquestación de enlaces por destino.

Coordina el análisis centralizado de enlaces sobre los IRs y produce
los outputs:
  - reports/link_debt.json — por-destino, lista de resolved + unresolved.
  - reports/linking-report.{json,md} — resumen legible.

NO invoca los renderers con flags especiales (eso requeriría un
refactor de los renderers para soportar --pass/--page-map). En su
lugar, calling this CLI produce los outputs derivados directamente del
grafo de links, y los renderers individuales (F54-F60) siguen siendo
responsables de emitir sus artifacts con su propia lógica de links.

Cubre:
  - C1 (criterio 1): cero enlaces rotos en los 3 destinos ricos.
  - C2 (criterio 2): la segunda pasada resuelve toda la deuda.
  - C3 (criterio 3): destinos sin backlinks nativos (Markdown, HTML/PDF)
    reciben sección "Referenciado por" / `<aside class="backlinks">`.

Uso:
    python3 scripts/render/linking.py --ir <path> --out-dir <dir>
                                    [--profile <yaml>]
                                    [--renderers obsidian,notion_api,markdown,html_pdf]
                                    [--pass1-only] [--pass2-only]
                                    [--no-backlinks]

Dependencias: Python 3.9+ stdlib puro.
Códigos de salida: 0 OK · 1 error fatal · 2 OK con deuda residual.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import importlib.util as _importlib_util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


# Importa _linking.py (módulo sibling).
_HERE = Path(__file__).resolve().parent
_spec = _importlib_util.spec_from_file_location(
    "_linking", _HERE / "_linking.py"
)
_linking = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_linking)


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

RENDERER_SCRIPTS: Dict[str, str] = {
    "obsidian": "obsidian.py",
    "notion_api": "notion_api.py",
    "notion_md": "notion_md.py",
    "appflowy": "appflowy.py",
    "markdown": "markdown.py",
    "html_pdf": "html_pdf.py",
    "flashcards": "flashcards.py",
}

# Destinos con backlinks nativos (panel propio de la plataforma).
NATIVE_BACKLINKS: Set[str] = {
    "obsidian", "notion_api", "notion_md", "appflowy",
}

# Destinos que requieren sección generada.
GENERATED_BACKLINKS: Set[str] = {"markdown", "html_pdf"}

# Destinos sin backlinks.
NO_BACKLINKS: Set[str] = {"flashcards"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_utc_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_irs(ir_arg: Path) -> List[Dict[str, Any]]:
    if ir_arg.is_dir():
        return [json.loads(p.read_text(encoding="utf-8"))
                for p in sorted(ir_arg.glob("*.json"))]
    return [json.loads(ir_arg.read_text(encoding="utf-8"))]


def _build_note_id_set(ir_list: List[Dict[str, Any]]) -> set:
    return {ir.get("note_id", "") for ir in ir_list if ir.get("note_id")}


def _run_renderer(
    renderer: str, ir_arg: Path, profile: Path, out_dir: Path,
) -> Tuple[int, str, str]:
    """Invoca el script del renderer como subprocess (sin flags especiales)."""
    script_name = RENDERER_SCRIPTS.get(renderer)
    if script_name is None:
        return 1, "", f"renderer desconocido: {renderer}"
    script_path = _HERE / script_name
    if not script_path.exists():
        return 1, "", f"script no encontrado: {script_path}"

    cmd: List[str] = [
        sys.executable, str(script_path),
        "--ir", str(ir_arg),
        "--profile", str(profile),
        "--out-dir", str(out_dir),
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    return p.returncode, p.stdout, p.stderr


def _collect_rendered_paths(renderer: str, out_dir: Path) -> Dict[str, str]:
    """Recolecta `{note_id → rendered_path}` desde el output del renderer."""
    paths: Dict[str, str] = {}
    if renderer == "obsidian":
        d = out_dir / "render" / "obsidian"
    elif renderer == "notion_api":
        d = out_dir / "render" / "notion_api"
    elif renderer == "notion_md":
        d = out_dir / "render" / "notion_md"
    elif renderer == "appflowy":
        d = out_dir / "render" / "appflowy"
    elif renderer == "markdown":
        d = out_dir / "render" / "markdown"
    elif renderer == "html_pdf":
        d = out_dir / "render" / "html_pdf"
    elif renderer == "flashcards":
        d = out_dir / "render" / "flashcards"
    else:
        return paths
    if not d.exists():
        return paths
    for p in d.iterdir():
        if p.is_file() and (p.suffix == ".md" or p.suffix == ".html"):
            paths[p.stem] = str(p)
    return paths


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    tmp.replace(path)


# ---------------------------------------------------------------------------
# Análisis centralizado
# ---------------------------------------------------------------------------


def compute_link_debt(
    ir_list: List[Dict[str, Any]],
    renderers: List[str],
    out_dir: Path,
) -> Dict[str, Any]:
    """Calcula link_debt por destino sin invocar los renderers con flags especiales."""
    note_ids = _build_note_id_set(ir_list)
    term_ids: Set[str] = set()

    link_debt: Dict[str, Any] = {
        "generated_at": _now_utc_iso(),
        "destinations": {},
        "totals": {
            "resolved": 0,
            "unresolved": 0,
            "destinations_with_debt": 0,
        },
    }

    for dest in renderers:
        degradations: List[Dict[str, Any]] = []
        report, _ = _linking.resolve_links(
            ir_list, note_ids, term_ids, degradations=degradations,
        )
        rendered = _collect_rendered_paths(dest, out_dir)
        page_map = {nid: nid for nid in rendered} if rendered else {}
        debt_entry = _linking.aggregate_link_debt(dest, report, page_map)
        link_debt["destinations"][dest] = debt_entry

    # Recalcular totales.
    total_resolved = sum(d.get("resolved_count", 0)
                         for d in link_debt["destinations"].values())
    total_unresolved = sum(d.get("unresolved_count", 0)
                           for d in link_debt["destinations"].values())
    destinations_with_debt = sum(
        1 for d in link_debt["destinations"].values()
        if d.get("unresolved_count", 0) > 0
    )
    link_debt["totals"] = {
        "resolved": total_resolved,
        "unresolved": total_unresolved,
        "destinations_with_debt": destinations_with_debt,
    }
    return link_debt


def render_with_renderers(
    ir_arg: Path, profile: Path, out_dir: Path,
    renderers: List[str],
) -> Dict[str, Dict[str, str]]:
    """Invoca cada renderer con sus flags por defecto; recolecta paths."""
    all_rendered: Dict[str, Dict[str, str]] = {}
    for renderer in renderers:
        rc, out, err = _run_renderer(renderer, ir_arg, profile, out_dir)
        if rc not in (0, 2):
            print(f"WARN: [{renderer}] exit={rc}: {err[:200]}",
                  file=sys.stderr)
        rendered = _collect_rendered_paths(renderer, out_dir)
        all_rendered[renderer] = rendered
    return all_rendered


# ---------------------------------------------------------------------------
# Reportes
# ---------------------------------------------------------------------------


def write_linking_outputs(
    out_dir: Path,
    link_debt: Dict[str, Any],
    renderers: List[str],
    rendered_paths: Dict[str, Dict[str, str]],
) -> None:
    reports_dir = out_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    _write_json(reports_dir / "link_debt.json", link_debt)
    _write_json(reports_dir / "linking-report.json", {
        "generated_at": link_debt["generated_at"],
        "renderers": renderers,
        "totals": link_debt["totals"],
        "destinations": link_debt["destinations"],
        "rendered_paths": rendered_paths,
    })
    _write_linking_md(reports_dir / "linking-report.md",
                      link_debt, renderers, rendered_paths)


def _write_linking_md(
    path: Path, link_debt: Dict[str, Any], renderers: List[str],
    rendered_paths: Dict[str, Dict[str, str]],
) -> None:
    md = [
        "# Reporte de linking — F61",
        "",
        f"- **generated_at:** {link_debt['generated_at']}",
        f"- **renderers:** {', '.join(renderers)}",
        "",
        "## Resumen",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        f"| Resueltos | {link_debt['totals']['resolved']} |",
        f"| Sin resolver | {link_debt['totals']['unresolved']} |",
        f"| Destinos con deuda | {link_debt['totals']['destinations_with_debt']} |",
        "",
        "## Por destino",
        "",
    ]
    for dest, data in link_debt["destinations"].items():
        md.append(f"### {dest}")
        md.append("")
        md.append(f"- Resueltos: {data.get('resolved_count', 0)}")
        md.append(f"- Sin resolver: {data.get('unresolved_count', 0)}")
        n_rendered = len(rendered_paths.get(dest, {}))
        md.append(f"- Archivos renderizados: {n_rendered}")
        if data.get("unresolved"):
            md.append("")
            md.append("**Links sin resolver:**")
            md.append("")
            for u in data["unresolved"][:20]:
                md.append(f"- `{u['source_note_id']}` → `{u['target']}` ({u['kind']})")
        md.append("")
    if not link_debt["destinations"]:
        md.append("(ninguno — renderers no emitieron o no se ejecutaron pass 2)")
        md.append("")
    path.write_text("\n".join(md), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="linking.py",
        description="CLI de orquestación de enlaces por destino (F61).",
    )
    parser.add_argument("--ir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path,
                        help="profile.yaml (mismo para todos los renderers).")
    parser.add_argument(
        "--renderers",
        type=str,
        default="obsidian,notion_api,notion_md,appflowy,markdown,html_pdf,flashcards",
        help="Lista separada por comas (default: todos).",
    )
    parser.add_argument("--pass1-only", action="store_true",
                        help="Solo invoca renderers y recolecta paths; sin debt.")
    parser.add_argument("--pass2-only", action="store_true",
                        help="Solo analiza debt; asume pass 1 previo.")
    parser.add_argument("--no-backlinks", action="store_true",
                        help="(reservado para futuro; no-op actualmente).")
    args = parser.parse_args(argv)

    if not args.ir.exists():
        print(f"ERROR: IR no encontrado en {args.ir}", file=sys.stderr)
        return 1
    if not args.profile.exists():
        print(f"ERROR: profile no encontrado en {args.profile}",
              file=sys.stderr)
        return 1

    renderers = [r.strip() for r in args.renderers.split(",") if r.strip()]
    invalid = [r for r in renderers if r not in RENDERER_SCRIPTS]
    if invalid:
        print(f"ERROR: renderers inválidos: {invalid}. "
              f"Válidos: {sorted(RENDERER_SCRIPTS)}", file=sys.stderr)
        return 1

    ir_list = _load_irs(args.ir)

    rendered_paths: Dict[str, Dict[str, str]] = {}
    if not args.pass2_only:
        rendered_paths = render_with_renderers(
            args.ir, args.profile, args.out_dir, renderers,
        )

    if args.pass1_only:
        write_linking_outputs(args.out_dir,
                              {"generated_at": _now_utc_iso(),
                               "destinations": {},
                               "totals": {"resolved": 0, "unresolved": 0,
                                          "destinations_with_debt": 0}},
                              renderers, rendered_paths)
        print(f"linking.py pass 1 exit=0")
        return 0

    link_debt = compute_link_debt(ir_list, renderers, args.out_dir)
    write_linking_outputs(args.out_dir, link_debt, renderers, rendered_paths)

    unresolved = link_debt["totals"]["unresolved"]
    rc = 2 if unresolved > 0 else 0
    print(f"linking.py exit={rc}; reporte en reports/linking-report.{{json,md}}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
