#!/usr/bin/env python3
"""html_pdf.py — F59 · Renderer HTML y PDF (L4).

Genera archivos HTML5 autocontenidos (CSS inline, sin recursos externos)
a partir del Note IR validado. Implementa la interfaz `render(ir, profile,
matrix) → (artifacts, degradation_report)` del contrato F53
(`references/08-render/contract.md`).

Capacidades (per `references/08-render/capability-matrix.md` §2.1):
  HTML/PDF = 12 ✅ + 2 ❌ (Backlinks → <aside>, Consultas dinámicas → <section>).

Detalles:
  - admonition → <aside class="callout callout-<severity>">
  - collapsible → <details><summary>title</summary>...</details>
  - link-note → <a href="<note-id>.html">text</a> (path relativo, criterio 1)
  - diagram → <figure><svg>...</svg></figure> inline (con F70) o <pre class="mermaid">
  - quote → <blockquote><cite>...</cite>body</blockquote> (criterio 3)
  - table con rowspan/colspan → <table> nativo HTML (sin degradación)
  - backlinks → <aside class="backlinks"> al final (fila 8 §6)
  - queries → <section class="queries"> (fila 17 §6)

CSS: lee `references/08-render/html_pdf.template.css` y lo inlinea en
cada `<style>`. Self-contained: sin @import, sin url(http), sin <link>.

PDF: opcional via weasyprint (soft-dep). Sin weasyprint, exit 0 con
HTML + archivo PRINT_INSTRUCTIONS.md.

Idempotencia (RC-04): timestamp en <head> + sha256 en cabecera.

Uso:
    python3 scripts/render/html_pdf.py --ir <path> --profile <path> --out-dir <dir>
                                        [--matrix <path>] [--source-hash <hex64>]
                                        [--renderer-version <semver>]
                                        [--no-pdf] [--print-instructions]
                                        [--pre-render-diagrams]

Dependencias: Python 3.9+ stdlib puro; weasyprint opcional para PDF.
Códigos de salida: 0 OK · 1 error fatal · 2 OK con advertencias.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import importlib.util as _importlib_util
import json
import re
import sys
import textwrap
from html import escape as _html_escape
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


# Comparte atomic_write_json / atomic_write_text con F38/F39/F54-F58.
_IO_PATH = (
    Path(__file__).resolve().parent.parent / "util" / "_io.py"
)
_spec = _importlib_util.spec_from_file_location("_skill_io", _IO_PATH)
_io_mod = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_io_mod)
_atomic_write_json = _io_mod.atomic_write_json
_atomic_write_text = _io_mod.atomic_write_text


EXIT_OK = 0
EXIT_FATAL = 1
EXIT_WARN = 2


# ---------------------------------------------------------------------------
# Constantes inline
# ---------------------------------------------------------------------------

SEVERITY_TO_CSS_CLASS: Dict[str, str] = {
    "note": "note", "tip": "tip", "info": "info",
    "warning": "warning", "caution": "warning", "danger": "danger",
    "example": "example", "question": "question", "success": "success",
    "failure": "danger", "bug": "danger",
    "quote": "note", "abstract": "note",
    "security": "danger", "performance": "warning", "version": "info",
    "deprecated": "warning", "conflict": "warning", "external": "info",
}
DEFAULT_SEVERITY = "note"

SEVERITY_TO_EMOJI: Dict[str, str] = {
    "note": "📝", "tip": "💡", "info": "ℹ️",
    "warning": "⚠️", "caution": "⚠️", "danger": "🚫",
    "example": "📋", "question": "❓", "success": "✅",
    "failure": "❌", "bug": "🐛",
    "quote": "💬", "abstract": "📑",
    "security": "🔒", "performance": "⚡", "version": "🏷️",
    "deprecated": "⛔", "conflict": "⚠️", "external": "🔗",
}
DEFAULT_EMOJI = "📝"

LANG_MAP: Dict[str, str] = {
    "python": "python", "py": "python",
    "javascript": "javascript", "js": "javascript",
    "typescript": "typescript", "ts": "typescript",
    "bash": "bash", "sh": "bash", "shell": "bash",
    "json": "json",
    "yaml": "yaml", "yml": "yaml",
    "sql": "sql",
    "html": "html",
    "css": "css",
    "rust": "rust",
    "go": "go",
    "java": "java",
    "kotlin": "kotlin",
    "swift": "swift",
    "ruby": "ruby",
    "c": "c",
    "cpp": "c++", "c++": "c++",
    "csharp": "c#", "c#": "c#",
    "php": "php",
    "scala": "scala",
    "mermaid": "mermaid",
    "plain": "plaintext",
    "": "plaintext",
}


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


def _now_utc_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_of_ir(ir_obj: Any) -> str:
    canonical = json.dumps(ir_obj, sort_keys=True, ensure_ascii=False)
    return _sha256_hex(canonical.encode("utf-8"))


def _parse_minimal_yaml(text: str) -> Dict[str, Any]:
    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Any]] = [(-1, root)]
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1] if stack else root
        if line.startswith("- "):
            value = line[2:].strip()
            if isinstance(parent, list):
                parent.append(_coerce_scalar(value))
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if not value:
                new_dict: Dict[str, Any] = {}
                if isinstance(parent, dict):
                    parent[key] = new_dict
                stack.append((indent, new_dict))
            else:
                if isinstance(parent, dict):
                    parent[key] = _coerce_scalar(value)
    return root


def _coerce_scalar(value: str) -> Any:
    if value in ("true", "True", "yes"):
        return True
    if value in ("false", "False", "no"):
        return False
    if value in ("null", "None", "~"):
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def _get_html_pdf_config(profile: Dict[str, Any]) -> Dict[str, Any]:
    targets = profile.get("targets", {}) or {}
    return (targets.get("html_pdf") or targets.get("html")
            or targets.get("pdf") or {})


def _load_css_template() -> str:
    p = (Path(__file__).resolve().parents[2]
         / "references" / "08-render" / "html_pdf.template.css")
    return p.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Recorrido del IR y resolución de enlaces
# ---------------------------------------------------------------------------


def traverse_ir(ir: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
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


def collect_link_targets(ir: Dict[str, Any]) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []

    def _walk(node: Any) -> None:
        if not isinstance(node, dict):
            return
        kind = node.get("node", "")
        attrs = node.get("attrs", {}) or {}
        if kind == "link-note":
            tgt = attrs.get("target", "")
            if tgt:
                out.append((tgt, "note"))
        elif kind == "term-ref":
            tgt = attrs.get("term_id", "")
            if tgt:
                out.append((tgt, "term"))
        for child in node.get("children", []) or []:
            _walk(child)

    for child in ir.get("children", []) or []:
        _walk(child)
    return out


def resolve_links(ir_list: List[Dict[str, Any]], note_ids: Set[str],
                  term_ids: Set[str], degradations: List[Dict[str, Any]]
                  ) -> List[Tuple[str, str]]:
    edges: List[Tuple[str, str]] = []
    for ir in ir_list:
        src = ir.get("note_id", "")
        for tgt, kind in collect_link_targets(ir):
            if kind == "note":
                if tgt in note_ids:
                    edges.append((src, tgt))
                else:
                    degradations.append({
                        "id": f"deg-{_sha256_hex((tgt + 'unr').encode())[:12]}",
                        "node_path": f"{src}/link",
                        "node_type": "link-note",
                        "capability": "link-note",
                        "alternative": (
                            f"link <a href='<target>.html'>; target no resuelto en el workdir"
                        ),
                        "evidence": f"rg 'href=\"{tgt}\\.html\"' render/html_pdf/<id>.html exit 0",
                        "content_intact": True,
                    })
            elif kind == "term" and tgt not in term_ids:
                degradations.append({
                    "id": f"deg-{_sha256_hex((tgt + 'unrterm').encode())[:12]}",
                    "node_path": f"{src}/term",
                    "node_type": "term-ref",
                    "capability": "term-ref",
                    "alternative": f"link al término [[term:{tgt}]] (literal); glosario no contiene '{tgt}'",
                    "evidence": f"rg 'term:{tgt}' render/html_pdf/<id>.html exit 0",
                    "content_intact": True,
                })
    return edges


# ---------------------------------------------------------------------------
# Pre-render de diagramas (F70 opcional)
# ---------------------------------------------------------------------------


def _pre_render_diagram(text: str, out_path: Path) -> Optional[str]:
    f70 = Path(__file__).resolve().parent / "diagram_image.py"
    if not f70.exists():
        return None
    try:
        import subprocess as _sp
        import tempfile as _tf
        with _tf.NamedTemporaryFile("w", suffix=".mmd",
                                    delete=False, encoding="utf-8") as f:
            f.write(text)
            in_path = Path(f.name)
        try:
            cmd = [sys.executable, str(f70),
                   "--input", str(in_path),
                   "--output", str(out_path),
                   "--format", "svg"]
            _sp.run(cmd, capture_output=True, timeout=30, check=True)
            if out_path.exists():
                return str(out_path)
        finally:
            try:
                in_path.unlink()
            except OSError:
                pass
    except Exception:
        return None
    return None


# ---------------------------------------------------------------------------
# Emisión de nodos IR → HTML
# ---------------------------------------------------------------------------


def _attr(name: str, value: Any) -> str:
    return f' {name}="{_html_escape(str(value), quote=True)}"'


def _emit_section(node: Dict[str, Any], note_id: str) -> str:
    level = int(node.get("attrs", {}).get("level", 1) or 1)
    level = max(1, min(level, 6))
    text = _emit_inline(node.get("children", []))
    anchor = f"{note_id}-h{level}-{node.get('_seq', 0)}"
    return f'<h{level} id="{_html_escape(anchor)}">{text}</h{level}>'


def _emit_paragraph(node: Dict[str, Any]) -> str:
    body = _emit_inline(node.get("children", []))
    return f"<p>{body}</p>" if body else ""


def _emit_list(node: Dict[str, Any]) -> str:
    ordered = bool(node.get("attrs", {}).get("ordered", False))
    tag = "ol" if ordered else "ul"
    items = node.get("children", [])
    inner = "\n".join(f"  <li>{_emit_inline(item.get('children', []))}</li>"
                       for item in items)
    return f"<{tag}>\n{inner}\n</{tag}>"


def _emit_checklist(node: Dict[str, Any]) -> str:
    items = node.get("children", [])
    parts = ['<ul class="checklist">']
    for item in items:
        done = bool(item.get("attrs", {}).get("done", False))
        cls = " class=\"done\"" if done else ""
        text = _emit_inline(item.get("children", []))
        parts.append(f"  <li{cls}>{text}</li>")
    parts.append("</ul>")
    return "\n".join(parts)


def _emit_table(node: Dict[str, Any]) -> str:
    """Tabla HTML con rowspan/colspan nativos (HTML/PDF es ✅)."""
    attrs = node.get("attrs", {}) or {}
    headers = attrs.get("headers", []) or []
    rows = attrs.get("rows", []) or []
    if not rows and not headers:
        return ""
    out = ["<table>", "  <thead>", "    <tr>"]
    for h in headers:
        out.append(f"      <th>{_html_escape(str(h))}</th>")
    out.append("    </tr>")
    out.append("  </thead>")
    out.append("  <tbody>")
    for row in rows:
        out.append("    <tr>")
        for c in row:
            if isinstance(c, dict):
                v = c.get("value", "")
                rowspan = c.get("rowspan")
                colspan = c.get("colspan")
                extra = ""
                if rowspan:
                    extra += f' rowspan="{rowspan}"'
                if colspan:
                    extra += f' colspan="{colspan}"'
                out.append(f"      <td{extra}>{_html_escape(str(v))}</td>")
            else:
                out.append(f"      <td>{_html_escape(str(c))}</td>")
        out.append("    </tr>")
    out.append("  </tbody>")
    out.append("</table>")
    return "\n".join(out)


def _emit_code(node: Dict[str, Any]) -> str:
    attrs = node.get("attrs", {}) or {}
    lang_raw = (attrs.get("lang", "") or "").lower()
    lang = LANG_MAP.get(lang_raw, "plaintext")
    text = attrs.get("text", "") or ""
    return f'<pre><code class="language-{lang}">{_html_escape(text)}</code></pre>'


def _emit_console(node: Dict[str, Any]) -> str:
    attrs = node.get("attrs", {}) or {}
    lines = attrs.get("lines", []) or []
    body = "\n".join(f"$ {ln}" if not str(ln).startswith("$") else str(ln)
                     for ln in lines)
    return f'<pre><code class="language-bash">{_html_escape(body)}</code></pre>'


def _emit_equation(node: Dict[str, Any]) -> str:
    attrs = node.get("attrs", {}) or {}
    latex = attrs.get("latex", "") or ""
    display = bool(attrs.get("display", False))
    cls = "math-display" if display else "math"
    safe = _html_escape(latex)
    return f'<span class="{cls}" data-latex="{safe}">{safe}</span>'


def _emit_figure(node: Dict[str, Any], out_dir: Path, note_id: str) -> str:
    attrs = node.get("attrs", {}) or {}
    src = attrs.get("src", "") or ""
    alt = attrs.get("alt", "") or ""
    caption = attrs.get("caption", "") or ""

    if src.startswith(("http://", "https://")):
        url = src
    elif src.startswith("/"):
        url = src
    else:
        url = f"assets/{note_id}/{src.lstrip('./')}"

    parts = ["<figure>"]
    parts.append(f'  <img src="{_html_escape(url, quote=True)}" alt="{_html_escape(alt, quote=True)}" loading="lazy">')
    if caption:
        parts.append(f"  <figcaption>{_html_escape(caption)}</figcaption>")
    parts.append("</figure>")
    return "\n".join(parts)


def _emit_diagram(node: Dict[str, Any], note_id: str, idx: int,
                  pre_render: bool, out_dir: Path,
                  degradations: List[Dict[str, Any]],
                  node_path: str) -> str:
    attrs = node.get("attrs", {}) or {}
    text = attrs.get("text", "") or ""
    alt = attrs.get("alt", "") or ""

    if pre_render:
        diag_dir = out_dir / "render" / "html_pdf" / "diagrams"
        img_path = diag_dir / f"{note_id}-{idx}.svg"
        rendered = _pre_render_diagram(text, img_path)
        if rendered:
            degradations.append({
                "id": f"deg-{_sha256_hex((node_path + 'pr').encode())[:12]}",
                "node_path": node_path,
                "node_type": "diagram",
                "capability": "diagram-mermaid-block",
                "alternative": (
                    f"<figure><svg>...</svg></figure> inline (SVG pre-renderizado "
                    f"por F70 en {img_path.name})"
                ),
                "evidence": f"test -f render/html_pdf/diagrams/{note_id}-{idx}.svg exit 0",
                "content_intact": True,
            })
            svg_content = img_path.read_text(encoding="utf-8", errors="replace")
            return (
                "<figure class=\"diagram\">\n"
                f"  {svg_content}\n"
                + (f"  <figcaption>{_html_escape(alt)}</figcaption>\n" if alt else "")
                + "</figure>"
            )

    degradations.append({
        "id": f"deg-{_sha256_hex((node_path + 'pr').encode())[:12]}",
        "node_path": node_path,
        "node_type": "diagram",
        "capability": "diagram-mermaid-block",
        "alternative": (
            "<pre class='mermaid'> con código fuente Mermaid verbatim "
            "(F70 ausente o flag --pre-render-diagrams inactivo)"
        ),
        "evidence": "rg 'class=\"mermaid\"' render/html_pdf/<id>.html exit 0",
        "content_intact": True,
    })
    return f'<figure class="diagram"><pre class="mermaid">{_html_escape(text)}</pre></figure>'


def _emit_admonition(node: Dict[str, Any],
                      degradations: List[Dict[str, Any]],
                      node_path: str) -> str:
    attrs = node.get("attrs", {}) or {}
    severity = str(attrs.get("severity", DEFAULT_SEVERITY) or DEFAULT_SEVERITY)
    title = str(attrs.get("title", "") or "")
    body = _emit_inline(node.get("children", []))

    css_class = SEVERITY_TO_CSS_CLASS.get(severity, DEFAULT_SEVERITY)
    emoji = SEVERITY_TO_EMOJI.get(severity, DEFAULT_EMOJI)

    if severity not in SEVERITY_TO_CSS_CLASS:
        degradations.append({
            "id": f"deg-{_sha256_hex((node_path + 'sev').encode())[:12]}",
            "node_path": node_path,
            "node_type": "admonition",
            "capability": "callout",
            "alternative": (
                f"<aside class='callout callout-{DEFAULT_SEVERITY}'> con emoji "
                f"'{DEFAULT_EMOJI}' (severity='{severity}' no en SEVERITY_TO_CSS_CLASS)"
            ),
            "evidence": "rg 'class=\"callout' render/html_pdf/<id>.html exit 0",
            "content_intact": True,
        })

    parts = [f'<aside class="callout callout-{css_class}">',
             f'  <span class="emoji">{emoji}</span>',
             '  <div class="body">']
    if title:
        parts.append(f"    <strong>{_html_escape(title)}</strong>")
    parts.append(f"    {body}" if body else "    ")
    parts.append("  </div>")
    parts.append("</aside>")
    return "\n".join(parts)


def _emit_collapsible(node: Dict[str, Any], note_id: str) -> str:
    attrs = node.get("attrs", {}) or {}
    title = str(attrs.get("title", "Detalles") or "Detalles")
    body_parts: List[str] = []
    for child in node.get("children", []):
        rendered = _emit_node(child, note_id=note_id)
        if rendered:
            body_parts.append(rendered)
    body = "\n".join(body_parts)
    return f"<details>\n  <summary>{_html_escape(title)}</summary>\n\n{body}\n\n</details>"


def _emit_quote(node: Dict[str, Any]) -> str:
    attrs = node.get("attrs", {}) or {}
    cite = attrs.get("cite", "")
    body = _emit_inline(node.get("children", []))
    cite_html = f'<cite>{_html_escape(str(cite))}</cite>' if cite else ""
    return f"<blockquote>\n  {body}\n  {cite_html}\n</blockquote>"


def _emit_columns(node: Dict[str, Any], note_id: str) -> str:
    """Concatenación vertical; CSS colapsa a vertical en print."""
    parts = ['<div class="columns">']
    for child in node.get("children", []):
        parts.append(_emit_node(child, note_id=note_id))
    parts.append("</div>")
    return "\n".join(parts)


def _emit_divider(_node: Dict[str, Any]) -> str:
    return "<hr>"


def _emit_property_block(node: Dict[str, Any], note_id: str,
                          in_head: bool = False) -> str:
    """Si in_head, emite <meta>; si no, emite <dl class='properties'>."""
    attrs = node.get("attrs", {}) or {}
    name = str(attrs.get("name", "") or "")
    value = attrs.get("value", "")
    if not name:
        return ""
    if in_head:
        return f'<meta name="property-{_html_escape(name)}" content="{_html_escape(str(value))}">'
    return f'<dt>{_html_escape(name)}</dt><dd>{_html_escape(str(value))}</dd>'


def _emit_query(node: Dict[str, Any], note_id: str) -> str:
    attrs = node.get("attrs", {}) or {}
    query = str(attrs.get("query", "") or "")
    return (
        '<section class="queries">\n'
        '  <h2>Consultas habituales</h2>\n'
        '  <p><em>Esta consulta requiere un motor de queries. Resultado estático de build-time:</em></p>\n'
        f'  <pre><code class="language-dataview">{_html_escape(query)}</code></pre>\n'
        '</section>'
    )


def _emit_question(node: Dict[str, Any]) -> str:
    attrs = node.get("attrs", {}) or {}
    prompt = str(attrs.get("prompt", "") or "")
    body = _emit_inline(node.get("children", []))
    return (
        f'<details class="question">\n'
        f'  <summary><strong>Pregunta:</strong> {_html_escape(prompt)}</summary>\n'
        f'  {body}\n'
        f'</details>'
    )


def _emit_step(node: Dict[str, Any]) -> str:
    attrs = node.get("attrs", {}) or {}
    index = int(attrs.get("index", 1) or 1)
    body = _emit_inline(node.get("children", []))
    return f'<li value="{index}">{body}</li>'


def _emit_parameter_table(node: Dict[str, Any]) -> str:
    attrs = node.get("attrs", {}) or {}
    columns = attrs.get("columns", []) or []
    rows = attrs.get("rows", []) or []
    out = ['<table class="parameter-table">', "  <thead>", "    <tr>"]
    for c in columns:
        out.append(f"      <th>{_html_escape(str(c))}</th>")
    out.append("    </tr>")
    out.append("  </thead>")
    out.append("  <tbody>")
    for row in rows:
        out.append("    <tr>")
        for c in row:
            out.append(f"      <td>{_html_escape(str(c))}</td>")
        out.append("    </tr>")
    out.append("  </tbody>")
    out.append("</table>")
    return "\n".join(parts_str for parts_str in out)


# ---------------------------------------------------------------------------
# Inline
# ---------------------------------------------------------------------------


def _emit_inline(children: List[Dict[str, Any]]) -> str:
    return "".join(_emit_inline_node(c) for c in children)


def _emit_inline_node(node: Dict[str, Any]) -> str:
    kind = node.get("node", "")
    attrs = node.get("attrs", {}) or {}
    if kind == "text":
        return _html_escape(attrs.get("text", "") or "")
    if kind == "strong":
        return f"<strong>{_emit_inline(node.get('children', []))}</strong>"
    if kind == "em":
        return f"<em>{_emit_inline(node.get('children', []))}</em>"
    if kind == "code-inline":
        return f"<code>{_html_escape(attrs.get('text', '') or '')}</code>"
    if kind == "link-external":
        text = attrs.get("text", "") or attrs.get("url", "")
        url = attrs.get("url", "")
        return f'<a href="{_html_escape(url, quote=True)}">{_html_escape(text)}</a>'
    if kind == "link-note":
        target = attrs.get("target", "") or ""
        text = attrs.get("text", "") or target
        return f'<a href="{_html_escape(target)}.html" data-note-id="{_html_escape(target)}">{_html_escape(text)}</a>'
    if kind == "term-ref":
        term_id = attrs.get("term_id", "") or ""
        text = attrs.get("text", "") or term_id
        return f'<span class="term-ref" data-term-id="{_html_escape(term_id)}">{_html_escape(text)}</span>'
    if kind == "source-ref":
        block_id = attrs.get("block_id", "") or ""
        source_hash = attrs.get("source_hash", "") or ""
        short_hash = source_hash[:8] if source_hash else ""
        return f'<span class="source-ref" data-block-id="{_html_escape(block_id)}" data-source-hash-short="{_html_escape(short_hash)}"></span>'
    if kind == "math-inline":
        latex = attrs.get("latex", "") or ""
        return f'<span class="math" data-latex="{_html_escape(latex)}">{_html_escape(latex)}</span>'
    if kind == "footnote-ref":
        ref_id = attrs.get("ref_id", "") or ""
        text = attrs.get("text", "") or ""
        return f'<sup id="fnref-{_html_escape(ref_id)}"><a href="#fn-{_html_escape(ref_id)}">{_html_escape(text or ref_id)}</a></sup>'
    if kind == "keyboard":
        return f"<kbd>{_html_escape(attrs.get('text', '') or '')}</kbd>"
    if kind == "placeholder":
        return f'<span class="placeholder">{{{{{_html_escape(attrs.get("text", "") or "")}}}}}</span>'
    if kind == "deleted":
        return f"<del>{_emit_inline(node.get('children', []))}</del>"
    return _html_escape(attrs.get("text", "") or "")


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


def _emit_node(node: Dict[str, Any], note_id: str = "", idx: int = 0,
               degradations: Optional[List[Dict[str, Any]]] = None,
               out_dir: Optional[Path] = None,
               pre_render: bool = False,
               node_path: str = "") -> str:
    kind = node.get("node", "")
    # Detectar tabla con query (consulta dinámica, fila 17 §6).
    if kind == "table":
        attrs = node.get("attrs", {}) or {}
        cap = node.get("capability", "")
        if cap == "query" or "query" in attrs:
            return _emit_query(node, note_id)
    if kind == "admonition":
        assert degradations is not None
        return _emit_admonition(node, degradations, node_path)
    if kind == "diagram":
        assert degradations is not None and out_dir is not None
        return _emit_diagram(node, note_id, idx, pre_render, out_dir,
                             degradations, node_path)
    if kind == "query":
        return _emit_query(node, note_id)
    if kind == "figure" and out_dir is not None:
        return _emit_figure(node, out_dir, note_id)
    if kind == "step":
        # Los steps se agrupan en un <ol class="steps"> fuera de aquí.
        return _emit_step(node)
    fn_map: Dict[str, Any] = {
        "section": lambda n: _emit_section(n, note_id),
        "paragraph": _emit_paragraph,
        "list": _emit_list,
        "checklist": _emit_checklist,
        "table": _emit_table,
        "code": _emit_code,
        "console": _emit_console,
        "equation": _emit_equation,
        "collapsible": lambda n: _emit_collapsible(n, note_id),
        "quote": _emit_quote,
        "columns": lambda n: _emit_columns(n, note_id),
        "divider": _emit_divider,
        "property-block": lambda n: _emit_property_block(n, note_id),
        "question": _emit_question,
        "parameter-table": _emit_parameter_table,
    }
    fn = fn_map.get(kind)
    if fn is None:
        return ""
    return fn(node)


# ---------------------------------------------------------------------------
# TOC y backlinks
# ---------------------------------------------------------------------------


def _build_toc(ir_obj: Dict[str, Any], note_id: str) -> str:
    """Genera TOC <nav> con headings del IR."""
    items: List[Tuple[int, str]] = []

    def _walk(node: Any) -> None:
        if not isinstance(node, dict):
            return
        if node.get("node") == "section":
            level = int(node.get("attrs", {}).get("level", 1) or 1)
            text = _flatten_inline_text(node.get("children", []))
            if text and level <= 3:
                items.append((level, text))
        for child in node.get("children", []) or []:
            _walk(child)

    _walk(ir_obj)
    if not items:
        return ""
    parts = ['<nav id="toc">', '  <h2>Índice</h2>', "  <ol>"]
    for level, text in items:
        anchor = text.replace(" ", "-").lower()[:50]
        indent = "    " * (level - 1)
        parts.append(f'{indent}<li><a href="#{_html_escape(anchor)}">{_html_escape(text)}</a></li>')
    parts.append("  </ol>")
    parts.append("</nav>")
    return "\n".join(parts)


def _flatten_inline_text(children: List[Dict[str, Any]]) -> str:
    out: List[str] = []

    def _walk(node: Any) -> None:
        if not isinstance(node, dict):
            return
        kind = node.get("node", "")
        attrs = node.get("attrs", {}) or {}
        if kind == "text":
            out.append(attrs.get("text", "") or "")
        elif kind in ("strong", "em", "deleted"):
            _walk_each(node.get("children", []))
        elif kind == "code-inline":
            out.append(attrs.get("text", "") or "")
        elif kind == "link-note":
            out.append(attrs.get("text", "") or attrs.get("target", ""))
        elif kind == "link-external":
            out.append(attrs.get("text", "") or "")
        else:
            out.append(attrs.get("text", "") or "")

    def _walk_each(chs: List[Any]) -> None:
        for c in chs:
            _walk(c)

    _walk_each(children)
    return "".join(out)


def _build_backlinks_section(note_id: str,
                              edges: List[Tuple[str, str]]) -> Optional[str]:
    incoming = sorted({src for src, tgt in edges if tgt == note_id and src != note_id})
    if not incoming:
        return None
    items = "\n".join(f'    <li><a href="{_html_escape(src)}.html" data-note-id="{_html_escape(src)}">{_html_escape(src)}</a></li>'
                      for src in incoming)
    return (
        '<aside class="backlinks">\n'
        '  <h2>Referenciado por</h2>\n'
        '  <ul>\n'
        f'{items}\n'
        '  </ul>\n'
        '</aside>'
    )


# ---------------------------------------------------------------------------
# Emisión del artefacto HTML
# ---------------------------------------------------------------------------


def _collect_properties_for_meta(ir: Dict[str, Any]) -> str:
    """<meta> tags para properties."""
    parts: List[str] = []
    seen: Set[str] = set()

    def _walk(node: Any) -> None:
        if not isinstance(node, dict):
            return
        if node.get("node") == "property-block":
            attrs = node.get("attrs", {}) or {}
            name = str(attrs.get("name", "") or "")
            value = attrs.get("value", "")
            if name and name not in seen:
                parts.append(f'<meta name="property-{_html_escape(name)}" content="{_html_escape(str(value))}">')
                seen.add(name)
        for child in node.get("children", []) or []:
            _walk(child)

    _walk(ir)
    return "\n".join(parts)


def _collect_properties_for_body(ir: Dict[str, Any]) -> str:
    parts: List[str] = []
    seen: Set[str] = set()

    def _walk(node: Any) -> None:
        if not isinstance(node, dict):
            return
        if node.get("node") == "property-block":
            attrs = node.get("attrs", {}) or {}
            name = str(attrs.get("name", "") or "")
            value = attrs.get("value", "")
            if name and name not in seen:
                parts.append(f'<dt>{_html_escape(name)}</dt><dd>{_html_escape(str(value))}</dd>')
                seen.add(name)
        for child in node.get("children", []) or []:
            _walk(child)

    _walk(ir)
    if not parts:
        return ""
    return "<dl class=\"properties\">\n" + "\n".join(parts) + "\n</dl>"


def emit_artifact(ir_obj: Dict[str, Any], ir_sha256: str,
                  source_hash: str, renderer_version: str,
                  out_dir: Path, degradations: List[Dict[str, Any]],
                  pre_render: bool, edges: List[Tuple[str, str]],
                  css_template: str,
                  ir_node_count_holder: List[int]) -> Path:
    note_id = str(ir_obj.get("note_id", "note-unknown"))
    title = ir_obj.get("title", "") or note_id

    toc_html = _build_toc(ir_obj, note_id)
    ir_nodes = traverse_ir(ir_obj)
    ir_node_count_holder[0] += len(ir_nodes)

    # Backlinks al final.
    backlinks = _build_backlinks_section(note_id, edges)

    body_parts: List[str] = []
    if title:
        body_parts.append(f'<header class="note-meta" data-note-id="{_html_escape(note_id)}">')
        body_parts.append("  <dl>")
        body_parts.append(f"    <dt>title</dt><dd>{_html_escape(title)}</dd>")
        body_parts.append(f"    <dt>note_id</dt><dd>{_html_escape(note_id)}</dd>")
        body_parts.append(f"    <dt>source_hash</dt><dd>{_html_escape(source_hash[:16])}…</dd>")
        body_parts.append(f"    <dt>ir_sha256</dt><dd>{_html_escape(ir_sha256[:16])}…</dd>")
        body_parts.append(f"    <dt>rendered_at</dt><dd>{_html_escape(_now_utc_iso())}</dd>")
        body_parts.append(f"    <dt>renderer_version</dt><dd>{_html_escape(renderer_version)}</dd>")
        body_parts.append("  </dl>")
        body_parts.append("</header>")

    body_parts.append(f'<h1 data-note-id="{_html_escape(note_id)}">{_html_escape(title)}</h1>')

    props_html = _collect_properties_for_body(ir_obj)
    if props_html:
        body_parts.append("<section class=\"properties-section\">")
        body_parts.append("  <h2>Propiedades</h2>")
        body_parts.append("  " + props_html)
        body_parts.append("</section>")

    for path, node in ir_nodes:
        rendered = _emit_node(node, note_id=note_id, idx=len(body_parts),
                              degradations=degradations, out_dir=out_dir,
                              pre_render=pre_render, node_path=path)
        if rendered:
            body_parts.append(rendered)

    if backlinks:
        body_parts.append(backlinks)

    body_html = "\n".join(body_parts)

    layout_open = '<div class="layout">'
    layout_close = '</div>'
    main_html = (
        f"{layout_open}\n"
        f'{toc_html if toc_html else "<!-- no toc -->"}\n'
        f'<main>\n{body_html}\n</main>\n'
        f"{layout_close}"
    )

    # <head>
    meta_props = _collect_properties_for_meta(ir_obj)
    html_doc = (
        "<!DOCTYPE html>\n"
        '<html lang="es">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'  <meta name="schema_version" content="1.0.0">\n'
        f'  <meta name="target" content="html_pdf">\n'
        f'  <meta name="note_id" content="{_html_escape(note_id)}">\n'
        f'  <meta name="source_hash" content="{_html_escape(source_hash)}">\n'
        f'  <meta name="ir_sha256" content="{_html_escape(ir_sha256)}">\n'
        f'  <meta name="rendered_at" content="{_html_escape(_now_utc_iso())}">\n'
        f'  <meta name="renderer_version" content="{_html_escape(renderer_version)}">\n'
        f'  <title>{_html_escape(title)}</title>\n'
        f'  {meta_props}\n'
        f'  <style>{css_template}</style>\n'
        "</head>\n"
        "<body>\n"
        f"{main_html}\n"
        "</body>\n"
        "</html>\n"
    )

    target_dir = out_dir / "render" / "html_pdf"
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / f"{note_id}.html"
    _atomic_write_text(out_path, html_doc)
    return out_path


# ---------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------


def build_report(source_hash: str, degradations: List[Dict[str, Any]],
                 ir_node_count: int, published: Dict[str, str],
                 pdf_status: str) -> Tuple[Dict[str, Any], str]:
    content_loss = sum(1 for d in degradations if not d.get("content_intact", True))
    report = {
        "schema_version": "1.0.0",
        "target": "html_pdf",
        "source_hash": source_hash,
        "generated_at": _now_utc_iso(),
        "totals": {
            "ir_nodes": ir_node_count,
            "degradations": len(degradations),
            "content_loss": content_loss,
        },
        "degradations": degradations,
        "published_pages": published,
        "pdf_status": pdf_status,
        "cross_target_diff": {
            "vs_markdown": "HTML permite callouts nativos (<aside>), table con rowspan/colspan nativos, backlinks via <aside>; pierde portabilidad de texto plano",
            "vs_obsidian": "HTML self-contained; Obsidian usa wikilinks [[id]] y callout syntax [!type]",
            "vs_appflowy": "HTML <aside class='callout-*'>; AppFlowy usa > [!type] en Markdown"
        }
    }
    md_lines = [
        "# Reporte de degradación — HTML/PDF",
        "",
        f"- **schema_version:** {report['schema_version']}",
        f"- **target:** html_pdf",
        f"- **source_hash:** `{source_hash}`",
        f"- **generated_at:** {report['generated_at']}",
        f"- **pdf_status:** {pdf_status}",
        "",
        "## Resumen",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        f"| Nodos IR totales | {ir_node_count} |",
        f"| Degradaciones | {len(degradations)} |",
        f"| Pérdida de contenido | {content_loss} |",
        f"| Notas publicadas | {len(published)} |",
        f"| PDF status | {pdf_status} |",
        "",
        "## Diferencias vs otros destinos",
        "",
        f"- **vs markdown (F58):** {report['cross_target_diff']['vs_markdown']}",
        f"- **vs obsidian (F54):** {report['cross_target_diff']['vs_obsidian']}",
        f"- **vs appflowy (F57):** {report['cross_target_diff']['vs_appflowy']}",
        "",
    ]
    if degradations:
        md_lines.append("## Degradaciones")
        md_lines.append("")
        for d in degradations:
            md_lines.append(f"### html_pdf / {d.get('capability', '?')}")
            md_lines.append("")
            md_lines.append(f"- **node_path:** `{d.get('node_path')}`")
            md_lines.append(f"- **node_type:** `{d.get('node_type')}`")
            md_lines.append(f"- **alternative:** {d.get('alternative')}")
            md_lines.append(f"- **evidence:** `{d.get('evidence')}`")
            md_lines.append(f"- **content_intact:** `{d.get('content_intact')}`")
            md_lines.append("")
    else:
        md_lines.append(
            "> Cero degradaciones en este destino. Esta sección se mantiene "
            "siempre para confirmar cobertura."
        )
        md_lines.append("")
    md_lines.append("## Cobertura")
    md_lines.append("")
    md_lines.append(f"- Nodos contabilizados: {len(degradations)}")
    md_lines.append(f"- Nodos IR totales: {ir_node_count}")
    md_lines.append(f"- content_loss: {content_loss} (debe ser 0; RC-01)")
    return report, "\n".join(md_lines)


# ---------------------------------------------------------------------------
# PDF generation (opcional via weasyprint)
# ---------------------------------------------------------------------------


def _try_generate_pdfs(html_paths: List[Path],
                        degradations: List[Dict[str, Any]]) -> Tuple[str, List[Path]]:
    """Intenta generar PDFs via weasyprint (soft dep).

    Devuelve (status, paths). Status ∈ {'generated', 'skipped'}.
    """
    try:
        import weasyprint  # type: ignore
    except ImportError:
        degradations.append({
            "id": "deg-pdf-skipped-weasyprint-missing",
            "node_path": "renderer/pdf",
            "node_type": "pdf",
            "capability": "pdf-export",
            "alternative": (
                "PDF no generado (weasyprint no instalado). HTML producido como "
                "alternativa; usuario puede `pip install weasyprint` y re-renderizar, "
                "o usar browser print-to-PDF con la CSS @media print"
            ),
            "evidence": "python3 -c 'import weasyprint' → ImportError",
            "content_intact": True,
        })
        return "skipped: weasyprint not installed", []

    pdf_paths: List[Path] = []
    for html_path in html_paths:
        pdf_path = html_path.with_suffix(".pdf")
        try:
            weasyprint.HTML(filename=str(html_path)).write_pdf(target=str(pdf_path))
            pdf_paths.append(pdf_path)
        except Exception as e:
            degradations.append({
                "id": f"deg-pdf-error-{_sha256_hex(html_path.name.encode())[:12]}",
                "node_path": str(html_path),
                "node_type": "pdf",
                "capability": "pdf-export",
                "alternative": f"PDF para {html_path.name} no generado (error: {e})",
                "evidence": f"weasyprint.HTML({html_path.name}).write_pdf",
                "content_intact": True,
            })
    return ("generated" if pdf_paths else "skipped: pdf errors"), pdf_paths


# ---------------------------------------------------------------------------
# Print instructions
# ---------------------------------------------------------------------------


def emit_print_instructions(workdir: Path, note_count: int) -> Path:
    p = workdir / "render" / "html_pdf" / "PRINT_INSTRUCTIONS.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    content = textwrap.dedent(f"""\
        # Instrucciones para generar PDF

        Esta carpeta contiene {note_count} nota(s) en HTML (`render/html_pdf/*.html`).
        El renderer F59 ha intentado generar PDF automáticamente; si
        `weasyprint` no estaba instalado, los PDF no se han producido.

        ## Opción A — Instalar weasyprint y re-renderizar

        ```bash
        pip install weasyprint
        python3 scripts/render/html_pdf.py --ir <path> --profile <yaml> \\
                                            --out-dir <dir>
        ```

        weasyprint respeta las reglas `@page` (A4 con encabezado de
        procedencia y numeración) y `@media print` (no partir tablas
        ni código por la mitad; ocultar TOC).

        ## Opción B — Browser print-to-PDF

        1. Abre `<note-id>.html` en Chrome o Firefox (file://).
        2. `Ctrl+P` (o Cmd+P en macOS).
        3. Destino: "Guardar como PDF".
        4. Márgenes: personalizados (2cm arriba/abajo, 1.5cm izq/der).
        5. Activar "Gráficos de fondo" para preservar el CSS.

        El browser no respeta `@page` (encabezado/numeración via CSS
        paged-media), pero sí aplica los page-break rules del `@media
        print` block. La numeración se puede activar manualmente en el
        diálogo de impresión.
        """)
    _atomic_write_text(p, content)
    return p


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------


def load_ir(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_profile(path: Path) -> Dict[str, Any]:
    return _parse_minimal_yaml(path.read_text(encoding="utf-8"))


def derive_source_hash(out_dir: Path, override: Optional[str]) -> str:
    if override:
        return override
    manifest = out_dir / "manifest.json"
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            sh = data.get("source", {}).get("hash") if isinstance(data, dict) else None
            if isinstance(sh, str) and re.match(r"^[0-9a-f]{64}$", sh):
                return sh
        except (json.JSONDecodeError, OSError):
            pass
    return "0" * 64


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="html_pdf.py",
        description="Renderer HTML y PDF (L4) para el Note IR. F59.",
    )
    parser.add_argument("--ir", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--matrix", type=Path,
                        default=(Path(__file__).resolve().parents[2] /
                                 "references" / "08-render" / "capability-matrix.md"))
    parser.add_argument("--source-hash", type=str, default=None)
    parser.add_argument("--renderer-version", type=str, default="0.1.0")
    parser.add_argument("--no-pdf", action="store_true",
                        help="Solo HTML; no intentar generar PDF.")
    parser.add_argument("--print-instructions", action="store_true",
                        help="Escribe PRINT_INSTRUCTIONS.md.")
    parser.add_argument("--pre-render-diagrams", action="store_true",
                        help="Pre-renderiza Mermaid a SVG vía F70 si está disponible.")

    args = parser.parse_args(argv)

    if not args.ir.exists():
        print(f"ERROR: IR no encontrado en {args.ir}", file=sys.stderr)
        return EXIT_FATAL
    if not args.profile.exists():
        print(f"ERROR: profile no encontrado en {args.profile}", file=sys.stderr)
        return EXIT_FATAL

    profile = load_profile(args.profile)
    source_hash = derive_source_hash(args.out_dir, args.source_hash)
    if not re.match(r"^[0-9a-f]{64}$", source_hash):
        source_hash = "0" * 64

    if args.ir.is_dir():
        ir_paths = sorted(args.ir.glob("*.json"))
    else:
        ir_paths = [args.ir]
    if not ir_paths:
        print(f"ERROR: no hay IRs en {args.ir}", file=sys.stderr)
        return EXIT_FATAL

    css_template = _load_css_template()

    degradations: List[Dict[str, Any]] = []
    note_ids: Set[str] = set()
    term_ids: Set[str] = set()
    ir_objs: List[Dict[str, Any]] = []
    rendered_paths: Dict[str, str] = {}

    for ir_path in ir_paths:
        try:
            ir_obj = load_ir(ir_path)
        except (json.JSONDecodeError, OSError) as e:
            print(f"WARN: no se pudo cargar {ir_path}: {e}", file=sys.stderr)
            continue
        ir_objs.append(ir_obj)
        note_ids.add(ir_obj.get("note_id", ""))
        for tgt, kind in collect_link_targets(ir_obj):
            if kind == "term":
                term_ids.add(tgt)

    edges = resolve_links(ir_objs, note_ids, term_ids, degradations)

    ir_node_count_holder: List[int] = [0]
    for ir_obj in ir_objs:
        ir_sha256 = _sha256_of_ir(ir_obj)
        try:
            out_path = emit_artifact(
                ir_obj=ir_obj, ir_sha256=ir_sha256,
                source_hash=source_hash, renderer_version=args.renderer_version,
                out_dir=args.out_dir, degradations=degradations,
                pre_render=args.pre_render_diagrams,
                edges=edges, css_template=css_template,
                ir_node_count_holder=ir_node_count_holder,
            )
            rendered_paths[ir_obj.get("note_id", "?")] = str(out_path)
        except OSError as e:
            print(f"ERROR: no se pudo escribir {ir_obj.get('note_id', '?')}: {e}",
                  file=sys.stderr)
            return EXIT_FATAL

    pdf_status = "skipped: --no-pdf flag"
    pdf_paths: List[Path] = []
    if not args.no_pdf:
        html_paths = [Path(p) for p in rendered_paths.values()]
        pdf_status, pdf_paths = _try_generate_pdfs(html_paths, degradations)
        for pdf in pdf_paths:
            rendered_paths[pdf.stem + "_pdf"] = str(pdf)

    report, report_md = build_report(
        source_hash=source_hash, degradations=degradations,
        ir_node_count=ir_node_count_holder[0],
        published=rendered_paths, pdf_status=pdf_status,
    )
    reports_dir = args.out_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(reports_dir / "render-degradation.json", report)
    _atomic_write_text(reports_dir / "render-degradation.md", report_md)

    if args.print_instructions:
        emit_print_instructions(args.out_dir, len(ir_objs))

    print(f"OK — {len(ir_objs)} nota(s) HTML renderizada(s) en "
          f"{args.out_dir / 'render' / 'html_pdf'}")
    print(f"     pdf_status: {pdf_status}")
    if pdf_paths:
        print(f"     pdf_paths: {[p.name for p in pdf_paths]}")
    if pdf_status.startswith("skipped"):
        return EXIT_WARN
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
