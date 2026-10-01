#!/usr/bin/env python3
"""capture.py — Genera capturas SVG (sintéticas) + PNG (Playwright opcional)

Forma de uso:
  python examples/capture.py --render-dir examples/01-postgresql-chapter/render --note-id 01-postgresql-chapter-main
  python examples/capture.py --render-dir examples/01-postgresql-chapter/render --note-id 01-postgresql-chapter-main --real-captures

Por cada destino con un render válido, genera:
  - <destino>/captures/<note-id>.svg   (siempre; sintético)
  - <destino>/captures/<note-id>.png   (si --real-captures y Playwright disponible)

Las plantillas SVG están en examples/assets/captures/<destino>.tmpl y son
archivos de texto con placeholders {{key}}. Sin Jinja2.

Exit codes:
  0  capturas generadas (al menos los SVG)
  1  error fatal
  2  args inválidos

Dependencias: stdlib puro + opcional Playwright + opcional cairosvg.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

EXAMPLES_ROOT = Path(__file__).resolve().parent
ASSETS_ROOT = EXAMPLES_ROOT / "assets" / "captures"

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

DESTINATIONS = ["obsidian", "notion_api", "notion_md", "appflowy", "html_pdf"]


def _read_template(dest: str) -> str:
    """Lee la plantilla para un destino. Usa .tmpl (no Jinja2)."""
    p = ASSETS_ROOT / f"{dest}.tmpl"
    if not p.exists():
        raise FileNotFoundError(f"plantilla no encontrada: {p}")
    return p.read_text(encoding="utf-8")


def _render_template(tmpl: str, ctx: dict[str, Any]) -> str:
    """Reemplaza {{key}} con ctx[key]. Sin Jinja2 (zero deps)."""
    def repl(m: "re.Match[str]") -> str:
        key = m.group(1).strip()
        return str(ctx.get(key, m.group(0)))
    return re.sub(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", repl, tmpl)


def _extract_metadata(render_dir: Path, note_id: str) -> dict[str, Any]:
    """Lee los artefactos del render para extraer metadatos."""
    ctx: dict[str, Any] = {
        "title": note_id,
        "note_id": note_id,
        "blocks_count": 0,
        "admonitions": 0,
        "tables": 0,
        "code_blocks": 0,
        "callouts": 0,
        "wikilinks": 0,
        "properties": "",
        "mermaid_blocks": 0,
        "collapsibles": 0,
        "schema_version": "1.0.0",
        "source_hash": "synthetic",
    }

    # Contar bloques en el markdown principal si existe.
    for dest in DESTINATIONS:
        dest_dir = render_dir / dest
        for ext in ("md", "html"):
            md = dest_dir / f"{note_id}.{ext}"
            if md.exists():
                text = md.read_text(encoding="utf-8", errors="replace")
                ctx["blocks_count"] = text.count("\n## ")
                ctx["admonitions"] = len(re.findall(r"^:::(note|warning|tip|danger|example)", text, re.MULTILINE))
                ctx["tables"] = text.count("|---")
                ctx["code_blocks"] = text.count("```")
                ctx["callouts"] = len(re.findall(r"^>\s*\[!", text, re.MULTILINE))
                ctx["wikilinks"] = len(re.findall(r"\[\[[^\]]+\]\]", text))
                ctx["mermaid_blocks"] = len(re.findall(r"```mermaid", text))
                ctx["collapsibles"] = text.count("<details")
                ctx["title"] = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
                ctx["title"] = ctx["title"].group(1) if ctx["title"] else note_id
                break

    return ctx


def _try_real_capture(svg_path: Path, png_path: Path) -> bool:
    """Intenta rasterizar SVG a PNG con Playwright o cairosvg. Devuelve True si OK."""
    if not svg_path.exists():
        return False
    # Opción 1: Playwright.
    try:
        from playwright.sync_api import sync_playwright  # type: ignore

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1024, "height": 1200})
            page.goto(f"file://{svg_path.absolute()}")
            page.wait_for_load_state("networkidle", timeout=5000)
            page.screenshot(path=str(png_path), full_page=True)
            browser.close()
        return True
    except (ImportError, Exception):
        pass
    # Opción 2: cairosvg.
    try:
        import cairosvg  # type: ignore

        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=1024)
        return True
    except (ImportError, Exception):
        return False


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Genera capturas SVG (+ opcional PNG) por destino")
    p.add_argument("--render-dir", required=True, help="Directorio render/ del ejemplo")
    p.add_argument("--note-id", required=True, help="ID de la nota a capturar")
    p.add_argument("--real-captures", action="store_true", help="Genera PNG con Playwright o cairosvg")
    args = p.parse_args(argv)

    render_dir = Path(args.render_dir)
    if not render_dir.exists():
        print(f"ERROR: render-dir no existe: {render_dir}", file=sys.stderr)
        return EXIT_USAGE

    ctx = _extract_metadata(render_dir, args.note_id)

    generated = 0
    for dest in DESTINATIONS:
        dest_dir = render_dir / dest
        if not dest_dir.exists():
            continue
        captures_dir = dest_dir / "captures"
        captures_dir.mkdir(parents=True, exist_ok=True)
        try:
            tmpl = _read_template(dest)
            svg_text = _render_template(tmpl, ctx)
        except FileNotFoundError as e:
            print(f"  WARN {dest}: {e}", file=sys.stderr)
            continue

        svg_path = captures_dir / f"{args.note_id}.svg"
        svg_path.write_text(svg_text, encoding="utf-8")
        generated += 1

        if args.real_captures:
            png_path = captures_dir / f"{args.note_id}.png"
            if _try_real_capture(svg_path, png_path):
                generated += 1

        print(f"  {dest}/captures/{args.note_id}.svg")

    if generated == 0:
        print("ERROR: ninguna captura generada", file=sys.stderr)
        return EXIT_FAIL
    print(f"OK {generated} capturas generadas")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
