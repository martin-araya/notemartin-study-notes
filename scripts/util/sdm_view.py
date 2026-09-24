#!/usr/bin/env python3
"""sdm_view.py — F36 SDM HTML viewer.

Genera un archivo HTML self-contained que sirve como visor del SDM producido
por F31. Muestra la jerarquía de secciones, los bloques con metadatos (id,
type, confidence, origin, anchor.page, anchor.section_path), recortes de
imagen cuando están disponibles, y un sumario con conteos por tipo y un
histograma de confianza. Filtros interactivos en client-side (JavaScript
inline): dropdown por tipo, input numérico para umbral mínimo de confianza
(criterio 3), checkbox Hide boilerplate.

Uso:
    python3 scripts/util/sdm_view.py --sdm <path> --out <html>
    python3 scripts/util/sdm_view.py --sdm <path> --out <html> --no-include-images

Salida: HTML self-contained (CSS + JS inline). Sin assets externos.
Filtros funcionan offline (un click en el input `confidence` aplica el filtro;
no requiere backend).

Códigos de salida:
    0 — OK
    1 — Error fatal (sdm no encontrado o inválido)
    2 — OK con advertencias (imágenes referenciadas ausentes, etc.)

Dependencias: Python 3.9+ stdlib (`html`, `json`, `base64`, `pathlib`).
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BLOCK_TYPES = (
    "prose", "heading", "list", "table", "code", "console", "formula",
    "figure", "caption", "note", "warning", "example", "syntax-diagram",
    "footnote", "toc", "boilerplate",
)

CSS = """
:root {
  --bg: #f6f7f9; --fg: #212429; --muted: #6c757d;
  --accent: #2563eb; --border: #e1e4e8; --warn: #d97706;
  --lowconf: #b91c1c; --ok: #15803d;
}
* { box-sizing: border-box; }
body { margin: 0; font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--fg); background: var(--bg); display: grid; grid-template-columns: 280px 1fr; min-height: 100vh; }
header.top { grid-column: 1 / -1; background: #212429; color: white; padding: 12px 24px; display: flex; gap: 24px; align-items: center; }
header.top h1 { font-size: 1.05rem; margin: 0; font-weight: 600; }
header.top .meta { color: #cbd5e1; font-size: 0.85rem; }
aside.hierarchy { background: white; border-right: 1px solid var(--border); padding: 16px; overflow-y: auto; max-height: calc(100vh - 60px); }
aside.hierarchy h2 { font-size: 0.95rem; margin: 0 0 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }
aside.hierarchy ol { list-style: none; padding: 0; margin: 0; }
aside.hierarchy li.section { padding: 6px 0; border-bottom: 1px solid var(--border); }
aside.hierarchy li.section a { color: var(--fg); text-decoration: none; font-weight: 500; }
aside.hierarchy li.section a:hover { color: var(--accent); }
aside.hierarchy .counts { font-size: 0.8rem; color: var(--muted); margin-top: 4px; display: flex; flex-wrap: wrap; gap: 4px; }
aside.hierarchy .counts span { padding: 1px 6px; background: var(--bg); border-radius: 999px; }
section.blocks { padding: 24px; max-width: 100%; overflow-x: auto; }
.filters { background: white; border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px; display: flex; gap: 16px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }
.filters label { font-size: 0.85rem; color: var(--muted); display: flex; align-items: center; gap: 6px; }
.filters input[type=number], .filters select { padding: 4px 6px; border: 1px solid var(--border); border-radius: 4px; font: inherit; }
.filters .summary { margin-left: auto; font-size: 0.85rem; color: var(--muted); }
ol.block-list { list-style: none; padding: 0; margin: 0; display: grid; gap: 12px; }
li.block { background: white; border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; }
li.block[data-lowconf="true"] { border-left: 4px solid var(--lowconf); }
.block-head { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-bottom: 8px; }
.badge { display: inline-block; padding: 2px 8px; font-size: 0.75rem; border-radius: 999px; font-weight: 600; }
.badge-type { background: #e0e7ff; color: #1e3a8a; }
.badge-origin-native { background: #dcfce7; color: var(--ok); }
.badge-origin-ocr { background: #fef3c7; color: #92400e; }
.badge-origin-reconstructed { background: #f3e8ff; color: #6b21a8; }
.badge-lowconf { background: var(--lowconf); color: white; }
.block-id { font-family: ui-monospace, Menlo, monospace; font-size: 0.75rem; color: var(--muted); }
.conf-bar { flex: 0 0 100px; background: var(--bg); border-radius: 999px; height: 8px; overflow: hidden; }
.conf-bar .fill { height: 100%; background: var(--ok); }
.content { background: var(--bg); border-radius: 4px; padding: 10px 12px; font-family: ui-monospace, Menlo, monospace; font-size: 0.85rem; white-space: pre-wrap; word-break: break-word; max-height: 320px; overflow-y: auto; }
.content.prose { font-family: inherit; }
.content.heading { font-weight: 600; }
.image-placeholder { padding: 12px; border: 1px dashed var(--border); color: var(--muted); border-radius: 4px; }
img.figure { max-width: 100%; height: auto; border-radius: 4px; display: block; }
.src-link { font-size: 0.8rem; color: var(--accent); margin-top: 6px; display: inline-block; }
tr.table-row:nth-child(even) { background: var(--bg); }
table { border-collapse: collapse; margin: 0; }
th, td { padding: 4px 8px; border: 1px solid var(--border); text-align: left; }
.hidden { display: none !important; }
section.summary { background: white; border: 1px solid var(--border); border-radius: 8px; padding: 16px; margin-bottom: 16px; }
section.summary h2 { margin: 0 0 12px; font-size: 1rem; }
.histogram { display: flex; align-items: end; gap: 4px; height: 60px; margin: 12px 0; }
.histogram .col { background: var(--accent); width: 24px; border-radius: 3px 3px 0 0; min-height: 1px; position: relative; }
.histogram .col .label { position: absolute; bottom: -18px; left: 0; right: 0; text-align: center; font-size: 0.65rem; color: var(--muted); }
.types-table { margin-top: 8px; }
"""

JS = """
(function () {
  var filters = document.querySelectorAll('.filters [data-filter]');
  var blocks = document.querySelectorAll('.block-list li.block');
  function applyFilters() {
    var type = document.querySelector('[data-filter=type]').value;
    var conf = parseFloat(document.querySelector('[data-filter=confidence]').value || '0');
    var hideBoilerplate = document.querySelector('[data-filter=boilerplate]').checked;
    var hidden = 0;
    blocks.forEach(function (b) {
      var btype = b.getAttribute('data-type');
      var bconf = parseFloat(b.getAttribute('data-confidence') || '0');
      var hide = false;
      if (type !== 'all' && btype !== type) hide = true;
      if (conf > 0 && bconf >= conf) hide = true;
      if (hideBoilerplate && btype === 'boilerplate') hide = true;
      if (hide) {
        b.classList.add('hidden');
        hidden += 1;
      } else {
        b.classList.remove('hidden');
      }
    });
    var summary = document.querySelector('.filters .summary');
    if (summary) {
      summary.textContent = blocks.length - hidden + ' / ' + blocks.length + ' blocks visible';
    }
  }
  filters.forEach(function (el) {
    el.addEventListener('input', applyFilters);
    el.addEventListener('change', applyFilters);
  });
  applyFilters();
  // Low-confidence one-click: a button next to the input sets the threshold.
  var lcBtn = document.querySelector('[data-action=low-confidence]');
  if (lcBtn) {
    lcBtn.addEventListener('click', function () {
      var input = document.querySelector('[data-filter=confidence]');
      input.value = '0.7';
      applyFilters();
    });
  }
})();
"""


# ============================================================
# Helpers
# ============================================================


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=str(path.parent), delete=False
    ) as tf:
        tf.write(content)
        tmpname = tf.name
    Path(tmpname).replace(path)


def _confidence_class(c: float) -> str:
    if c >= 0.85:
        return "ok"
    if c >= 0.7:
        return ""
    return "lowconf"


def _origin_class(o: str) -> str:
    if o in ("native", "ocr", "reconstructed"):
        return f"badge-origin-{o}"
    return f"badge-origin-{o or 'native'}"


def _esc(text: str) -> str:
    return html.escape(text or "", quote=True)


def _short(text: str, n: int = 200) -> str:
    text = text or ""
    if len(text) <= n:
        return text
    return text[: n - 1] + "…"


def _anchor_url(block: Dict[str, Any], source: Dict[str, Any]) -> Optional[str]:
    """Return a URL to the source page when possible (best-effort)."""
    url = source.get("url") or ""
    if not url:
        return None
    return url


def _render_block_content(
    blk: Dict[str, Any], sdm_dir: Path, include_images: bool
) -> str:
    btype = blk.get("type")
    content = blk.get("content", {})
    if isinstance(content, str):
        text = content
    else:
        text = json.dumps(content, indent=2, ensure_ascii=False)

    # Tables: render as a real HTML table from content.headers/rows.
    if btype == "table" and isinstance(content, dict):
        headers = content.get("headers") or []
        rows = content.get("rows") or []
        if headers or rows:
            html_t = ['<table>', '<thead><tr>']
            for h in headers:
                html_t.append(f"<th>{_esc(str(h))}</th>")
            html_t.append("</tr></thead><tbody>")
            for row in rows:
                html_t.append("<tr" + (' class="table-row"' if rows.index(row) % 2 == 1 else "") + ">")
                for c in row:
                    html_t.append(f"<td>{_esc(str(c))}</td>")
                html_t.append("</tr>")
            html_t.append("</tbody></table>")
            text = "".join(html_t)

    # Figures: inline the image (or render placeholder).
    if btype == "figure" and isinstance(content, dict):
        src = content.get("src", "")
        alt = content.get("alt", "")
        caption = content.get("caption", "")
        target = None
        if src.startswith("data:"):
            target = src
        elif include_images and src:
            try:
                p = Path(src)
                if p.is_absolute() and p.exists():
                    target = "file://" + str(p.resolve())
                elif (sdm_dir / src).exists():
                    target = "file://" + str((sdm_dir / src).resolve())
            except Exception:
                target = None
        img = (
            f'<img class="figure" src="{_esc(target or src)}" alt="{_esc(alt)}"/>'
            if target
            else f'<div class="image-placeholder">[figure — image asset not resolved] {src}</div>'
        )
        cap_html = (
            f'<div class="content caption">↳ {_esc(caption)}</div>' if caption else ""
        )
        return img + cap_html

    # Headings render the level too.
    if btype == "heading" and isinstance(content, dict):
        level = content.get("level", 1)
        text = f"{'#' * max(1, min(6, level))}  {content.get('text', '')}"

    if btype in ("note", "warning", "example", "syntax-diagram"):
        # For real HTML rendering, surface the severity (F35).
        sev = ""
        if isinstance(content, dict):
            sev = content.get("severity") or ""
            sev = f"  [{sev}]" if sev else ""
        text = f"{btype}{sev}: " + text

    return f'<div class="content {btype}">{text}</div>'


def _render_block(
    blk: Dict[str, Any], source: Dict[str, Any], sdm_dir: Path, include_images: bool
) -> str:
    btype = blk.get("type", "")
    bid = blk.get("id", "")
    conf = float(blk.get("confidence") or 0.0)
    origin = blk.get("origin", "")
    anchor = blk.get("anchor") or {}
    page = anchor.get("page")
    section_path = anchor.get("section_path", "")
    lowconf = "true" if conf < 0.7 else "false"
    src_url = _anchor_url(blk, source)
    pid = ""
    if isinstance(page, int):
        pid = f"#{bid}-{page}"
    html_block = [
        f'<li class="block" data-type="{btype}" data-confidence="{conf:.3f}" data-lowconf="{lowconf}" id="{bid}-row">',
        '<div class="block-head">',
        f'<span class="badge badge-type">{_esc(btype)}</span>',
        f'<span class="block-id">{_esc(bid[:12])}</span>',
        f'<div class="conf-bar" title="confidence = {conf:.2f}"><div class="fill" style="width:{conf * 100:.1f}%"/></div></div>',
        f'<span class="badge { _origin_class(origin) }">{_esc(origin)}</span>',
    ]
    if lowconf == "true":
        html_block.append('<span class="badge badge-lowconf">low confidence</span>')
    if section_path:
        html_block.append(
            f'<span class="block-id">{_esc(section_path)}</span>'
        )
    if isinstance(page, int):
        html_block.append(f'<span class="block-id">page {page}</span>')
    html_block.append('</div>')
    html_block.append(_render_block_content(blk, sdm_dir, include_images))
    if src_url and isinstance(page, int):
        html_block.append(
            f'<a class="src-link" href="{_esc(src_url)}" target="_blank" rel="noopener">→ go to source (page {page})</a>'
        )
    elif src_url:
        html_block.append(
            f'<a class="src-link" href="{_esc(src_url)}" target="_blank" rel="noopener">→ go to source</a>'
        )
    html_block.append('</li>')
    return "".join(html_block)


def _render_summary(sdm: Dict[str, Any]) -> str:
    blocks: List[Dict[str, Any]] = []
    for sec in sdm.get("sections", []):
        blocks.extend(sec.get("blocks", []) or [])
    if not blocks:
        return ""
    type_counts: Counter = Counter()
    conf_buckets: Counter = Counter()
    for b in blocks:
        type_counts[b.get("type", "?")] += 1
        c = b.get("confidence") or 0.0
        bucket = int(float(c) * 10)
        bucket = max(0, min(9, bucket))
        conf_buckets[bucket] += 1
    rows: List[str] = []
    for t in BLOCK_TYPES:
        if type_counts[t]:
            rows.append(f"<tr><td>{_esc(t)}</td><td>{type_counts[t]}</td></tr>")
    hist_cells: List[str] = []
    total = max(len(blocks), 1)
    for i in range(10):
        n = conf_buckets[i]
        h = max(1, int(round(40 * n / total)))
        hist_cells.append(
            f'<div class="col" style="height:{h}px" title="{i*10}-{(i+1)*10}%: {n}">'
            f'<div class="label">{i*10}-{(i+1)*10}%</div></div>'
        )
    return (
        '<section class="summary">'
        '<h2>Summary</h2>'
        f'<p><strong>{len(blocks)}</strong> blocks across '
        f'<strong>{len(sdm.get("sections", []))}</strong> sections '
        f'from <code>{_esc((sdm.get("source") or {}).get("id", "?"))}</code>.</p>'
        f'<div class="histogram">{"".join(hist_cells)}</div>'
        '<table class="types-table">' + "".join(rows) + '</table>'
        '</section>'
    )


def _render_hierarchy(sdm: Dict[str, Any]) -> str:
    out = ['<aside class="hierarchy"><h2>Hierarchy</h2><ol>']
    for sec in sdm.get("sections", []):
        path = sec.get("section_path", "/")
        title = sec.get("title", "") or path
        block_count = len(sec.get("blocks", []) or [])
        type_set: Counter = Counter()
        for b in sec.get("blocks", []) or []:
            type_set[b.get("type", "?")] += 1
        cid = path.strip("/").replace("/", "-") or "root"
        out.append(
            f'<li class="section"><a href="#{cid}">{_esc(title)}</a>'
            f'<div class="counts">'
            + "".join(
                f"<span>{_esc(t)}:{n}</span>" for t, n in sorted(type_set.items())
            )
            + f'<span style="background:#dbeafe">total:{block_count}</span></div>'
            f'</li>'
        )
    out.append("</ol></aside>")
    return "".join(out)


def _render_filters(all_types: List[str]) -> str:
    options = ['<option value="all">all types</option>']
    for t in all_types:
        options.append(f'<option value="{_esc(t)}">{_esc(t)}</option>')
    return (
        '<div class="filters">'
        '<label>Type: <select data-filter="type">' + "".join(options) + '</select></label>'
        '<label>Min confidence: '
        '<input type="number" data-filter="confidence" min="0" max="1" step="0.05" value="0" placeholder="0.0" style="width:80px"/>'
        '</label>'
        '<button data-action="low-confidence" type="button" style="padding:4px 8px;cursor:pointer">Show only low-confidence (&lt; 0.7)</button>'
        '<label><input type="checkbox" data-filter="boilerplate" checked/> Hide boilerplate</label>'
        '<span class="summary"></span>'
        '</div>'
    )


def render_html(sdm: Dict[str, Any], *, include_images: bool,
                sdm_dir: Optional[Path] = None) -> str:
    sdm_dir = sdm_dir or Path.cwd()
    body_blocks: List[str] = []
    type_set: List[str] = []
    for sec in sdm.get("sections", []):
        cid = sec.get("section_path", "/").strip("/").replace("/", "-") or "root"
        body_blocks.append(
            f'<section id="{cid}"><h2>{_esc(sec.get("title", "") or sec.get("section_path", ""))}</h2>'
            '<ol class="block-list">'
        )
        for blk in sec.get("blocks", []) or []:
            body_blocks.append(_render_block(blk, sdm.get("source", {}), sdm_dir, include_images))
            t = blk.get("type")
            if t and t not in type_set:
                type_set.append(t)
        body_blocks.append("</ol></section>")
    full = (
        '<!DOCTYPE html>\n'
        '<html lang="en"><head>'
        '<meta charset="utf-8">'
        f'<title>SDM Viewer — {_esc((sdm.get("source") or {}).get("id", "?"))}</title>'
        f'<style>{CSS}</style>'
        '</head><body>'
        f'<header class="top"><h1>SDM Viewer</h1><span class="meta">source = {_esc((sdm.get("source") or {}).get("id", "?"))}</span></header>'
        + _render_hierarchy(sdm)
        + '<section class="blocks">'
        + _render_summary(sdm)
        + _render_filters(sorted(type_set))
        + "".join(body_blocks)
        + '</section>'
        + f'<script>{JS}</script>'
        + '</body></html>'
    )
    return full


# ============================================================
# CLI
# ============================================================


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sdm_view.py",
        description="F36 — SDM HTML viewer (self-contained).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Generates one HTML file with CSS + JS inline, no external assets.

Criterios cubiertos:
  - Filtro por tipo (dropdown).
  - Filtro por umbral de confianza (input número).
  - Botón "Show only low-confidence (< 0.7)" — 1 click (criterio 3).
  - Hide boilerplate checkbox.
  - Enlace "go to source" cuando sdm.source.url existe.

Códigos de salida:
  0 OK · 1 sdm no encontrado / inválido · 2 warnings (imágenes no resueltas, etc.)
""",
    )
    p.add_argument("--sdm", required=True, type=Path, help="Ruta a sdm.json (F31 output)")
    p.add_argument("--out", required=True, type=Path, help="Ruta destino del HTML")
    p.add_argument("--no-include-images", action="store_true",
                   help="No intentes resolver file:// de figure.content.src")
    return p


def run(args: argparse.Namespace) -> int:
    sdm_path = Path(args.sdm).resolve()
    out_path = Path(args.out).resolve()
    if not sdm_path.exists():
        sys.stderr.write(f"sdm not found: {sdm_path}\n")
        return 1
    try:
        sdm = json.loads(sdm_path.read_text(encoding="utf-8"))
    except Exception as e:
        sys.stderr.write(f"failed to parse sdm.json: {e}\n")
        return 1
    html_str = render_html(
        sdm,
        include_images=not args.no_include_images,
        sdm_dir=sdm_path.parent,
    )
    try:
        _atomic_write_text(out_path, html_str)
    except Exception as e:
        sys.stderr.write(f"failed to write HTML: {e}\n")
        return 1
    sys.stdout.write(f"wrote {out_path}\n")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
