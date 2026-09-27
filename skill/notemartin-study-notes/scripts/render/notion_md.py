#!/usr/bin/env python3
"""notion_md.py — F56 · Renderer Notion por importación (L4).

Genera archivos Markdown optimizados para la importación a Notion vía UI
(Settings → Import → Markdown). Implementa la interfaz `render(ir, profile,
matrix) → (artifacts, degradation_report)` del contrato F53.

Capacidades (per `references/08-render/capability-matrix.md` §2.1):
  Notion import = 10 ✅ + 4 ❌ (Celdas combinadas, Callouts semánticos,
  Propiedades, Colores semánticos).

Detalles:
  - admonition → blockquote con emoji prefijo (no callout nativo)
  - collapsible → <details markdown="1"> (Notion importer convierte a toggle)
  - link-note → wikilink [[target|alias]]
  - propiedades → YAML frontmatter (no database properties)
  - diagram Mermaid → bloque ```mermaid
  - equation → $$ latex $$

Diferencias vs notion_api (F55): el reporte `render-degradation.json` incluye
un campo `vs_notion_api` por entrada + sección `cross_target_diff` que
documenta qué se degradó respecto a la ruta API.

Idempotencia (RC-04): `ir_sha256` en frontmatter; dos renders del mismo IR
producen salida byte-idéntica módulo timestamp.

Reporte doble: `reports/render-degradation.{json,md}` siempre (RC-03).

Uso:
    python3 scripts/render/notion_md.py --ir <path> --profile <path> --out-dir <dir>
                                          [--matrix <path>] [--source-hash <hex64>]
                                          [--renderer-version <semver>]
                                          [--include-import-instructions]

Dependencias: Python 3.9+ stdlib puro.
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
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Comparte atomic_write_json / atomic_write_text con F38/F39/F54/F55.
_IO_PATH = (
    Path(__file__).resolve().parent.parent / "util" / "_io.py"
)
_spec = _importlib_util.spec_from_file_location("_skill_io", _IO_PATH)
_io_mod = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_io_mod)
_atomic_write_json = _io_mod.atomic_write_json
_atomic_write_text = _io_mod.atomic_write_text

# Helper `## Cabecera` (F75): tabla GFM 2-col con los 5 campos canónicos.
_HEADER_SPEC = _importlib_util.spec_from_file_location(
    "scripts.render._header",
    Path(__file__).resolve().parent / "_header.py",
)
_header_mod = _importlib_util.module_from_spec(_HEADER_SPEC)
sys.modules.setdefault("scripts.render._header", _header_mod)
_HEADER_SPEC.loader.exec_module(_header_mod)
_emit_cabecera = _header_mod.emit_cabecera

# Tabla canónica severidad → estilo por destino (F73). El renderer consume
# solo el helper de icono (Notion import no soporta callouts nativos, solo
# blockquotes con emoji prefijo).
_STYLE_SPEC = _importlib_util.spec_from_file_location(
    "scripts.util.style_mapping",
    Path(__file__).resolve().parent.parent / "util" / "style_mapping.py",
)
sys.modules.setdefault("scripts.util.style_mapping",
                       _importlib_util.module_from_spec(_STYLE_SPEC))
_style_mod = _importlib_util.module_from_spec(_STYLE_SPEC)
_STYLE_SPEC.loader.exec_module(_style_mod)
icon_for = _style_mod.icon_for


EXIT_OK = 0
EXIT_FATAL = 1
EXIT_WARN = 2


# ---------------------------------------------------------------------------
# Constantes inline
# ---------------------------------------------------------------------------

# Severidad IR → emoji semántico (para blockquote prefijo): vive en
# scripts/util/style_mapping.py (F73). Notion import no soporta callouts
# nativos; solo blockquotes con emoji.

DEFAULT_SEVERITY = "note"
DEFAULT_EMOJI = "📝"

# Mapeo de lenguajes para bloques de código (compatible con Notion importer).
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
    "plain": "",
    "": "",
}


# ---------------------------------------------------------------------------
# Utilidades de bajo nivel
# ---------------------------------------------------------------------------


def _now_utc_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_of_ir(ir_obj: Any) -> str:
    canonical = json.dumps(ir_obj, sort_keys=True, ensure_ascii=False)
    return _sha256_hex(canonical.encode("utf-8"))


# ---------------------------------------------------------------------------
# Mini-parser YAML para `targets.notion_md.*` (acepta legacy `notion`)
# ---------------------------------------------------------------------------


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


def _get_notion_md_config(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Acepta `notion_md` (F53 canónico) o `notion` (F11 legacy)."""
    targets = profile.get("targets", {}) or {}
    return targets.get("notion_md") or targets.get("notion") or {}


# ---------------------------------------------------------------------------
# Recorrido del IR
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


# ---------------------------------------------------------------------------
# Emisión de nodos IR → Markdown
# ---------------------------------------------------------------------------


def _emit_section(node: Dict[str, Any]) -> str:
    level = int(node.get("attrs", {}).get("level", 1) or 1)
    level = max(1, min(level, 3))
    text = _emit_inline(node.get("children", []))
    return f"{'#' * level} {text}"


def _emit_paragraph(node: Dict[str, Any]) -> str:
    return _emit_inline(node.get("children", []))


def _emit_list(node: Dict[str, Any]) -> str:
    ordered = bool(node.get("attrs", {}).get("ordered", False))
    items = node.get("children", [])
    lines: List[str] = []
    for i, item in enumerate(items, start=1):
        marker = f"{i}." if ordered else "-"
        text = _emit_inline(item.get("children", []))
        lines.append(f"{marker} {text}")
    return "\n".join(lines)


def _emit_checklist(node: Dict[str, Any]) -> str:
    items = node.get("children", [])
    lines: List[str] = []
    for item in items:
        done = bool(item.get("attrs", {}).get("done", False))
        text = _emit_inline(item.get("children", []))
        marker = "[x]" if done else "[ ]"
        lines.append(f"- {marker} {text}")
    return "\n".join(lines)


def _emit_table_simple(node: Dict[str, Any]) -> str:
    attrs = node.get("attrs", {}) or {}
    headers = attrs.get("headers", []) or []
    rows = attrs.get("rows", []) or []
    if not rows and not headers:
        return ""
    lines: List[str] = []
    if headers:
        lines.append("| " + " | ".join(str(h) for h in headers) + " |")
        lines.append("|" + "|".join("---" for _ in headers) + "|")
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def _emit_table_merged(node: Dict[str, Any],
                       degradations: List[Dict[str, Any]],
                       node_path: str) -> str:
    """Celdas combinadas → fila 3 §6 contract."""
    attrs = node.get("attrs", {}) or {}
    headers = attrs.get("headers", []) or []
    cells = attrs.get("cells", []) or []
    matrix = attrs.get("matrix", []) or []
    section_path = attrs.get("section_path", "fuente")
    n_rows = len(cells) if cells else len(matrix)
    n_cols = max(len(r) for r in cells) if cells else (len(headers) if headers else 0)

    degradations.append({
        "id": f"deg-{_sha256_hex((node_path + 'merged').encode())[:12]}",
        "node_path": node_path,
        "node_type": "table",
        "capability": "table-merged-cells",
        "alternative": (
            "Markdown pipe table con celdas vacías + bloque <details> con la matriz "
            "completa (fila 3 §6 contract); Notion importer convierte <details> a toggle"
        ),
        "vs_notion_api": (
            "notion_api habría emitido block `table` con celdas vacías + callout "
            "nativo con icon y color"
        ),
        "evidence": "rg '<details' render/notion_md/<id>.md exit 0",
        "content_intact": True,
    })

    lines: List[str] = []
    if headers:
        lines.append("| " + " | ".join(str(h) for h in headers) + " |")
        lines.append("|" + "|".join("---" for _ in headers) + "|")
    for r in range(n_rows):
        cells_in_row = cells[r] if r < len(cells) else []
        row_repr = []
        for c in range(n_cols):
            v = cells_in_row[c] if c < len(cells_in_row) else ""
            row_repr.append(str(v) if v else "")
        lines.append("| " + " | ".join(row_repr) + " |")

    lines.append("")
    lines.append(
        f"> ⚠️ Estructura original con celdas combinadas "
        f"({n_rows} filas × {n_cols} cols) — ver fuente §{section_path}"
    )

    lines.append("")
    lines.append("<details markdown=\"1\">")
    lines.append(f"<summary>Matriz original con rowspan/colspan ({n_rows}×{n_cols})</summary>")
    lines.append("")
    lines.append("| Fila | Col | Valor |")
    lines.append("|---|---|---|")
    for r_idx, row in enumerate(matrix):
        for c_idx, cell in enumerate(row):
            val = cell if not isinstance(cell, dict) else cell.get("value", "")
            span = cell.get("span", "") if isinstance(cell, dict) else ""
            lines.append(f"| {r_idx} | {c_idx} | {val}{(' (' + span + ')') if span else ''} |")
    lines.append("")
    lines.append("</details>")

    return "\n".join(lines)


def _emit_code(node: Dict[str, Any]) -> str:
    attrs = node.get("attrs", {}) or {}
    lang_raw = (attrs.get("lang", "") or "").lower()
    lang = LANG_MAP.get(lang_raw, "")
    text = attrs.get("text", "") or ""
    return f"```{lang}\n{text}\n```"


def _emit_console(node: Dict[str, Any]) -> str:
    attrs = node.get("attrs", {}) or {}
    lines = attrs.get("lines", []) or []
    return "\n".join(f"$ {ln}" if not ln.startswith("$") else ln for ln in lines)


def _emit_equation(node: Dict[str, Any]) -> str:
    attrs = node.get("attrs", {}) or {}
    latex = attrs.get("latex", "") or ""
    display = bool(attrs.get("display", False))
    if display:
        return f"$$\n{latex}\n$$"
    return f"${latex}$"


def _emit_figure(node: Dict[str, Any]) -> str:
    attrs = node.get("attrs", {}) or {}
    src = attrs.get("src", "") or ""
    alt = attrs.get("alt", "") or ""
    caption = attrs.get("caption", "") or ""
    if src.startswith(("http://", "https://", "/", "./", "../")):
        block = f"![{alt}]({src})"
    else:
        block = f"![{alt}](file://{src})"
    if caption:
        block += f"\n*{caption}*"
    return block


def _emit_diagram(node: Dict[str, Any]) -> str:
    attrs = node.get("attrs", {}) or {}
    text = attrs.get("text", "") or ""
    alt = attrs.get("alt", "") or ""
    block = f"```mermaid\n{text}\n```"
    if alt:
        block = f"<!-- {alt} -->\n{block}"
    return block


def _emit_admonition(node: Dict[str, Any],
                     degradations: List[Dict[str, Any]],
                     node_path: str) -> str:
    """Admonition → blockquote con emoji prefijo (fila 11 §6 contract).

    Notion importer no soporta callouts nativos; solo blockquotes.
    """
    attrs = node.get("attrs", {}) or {}
    severity = str(attrs.get("severity", DEFAULT_SEVERITY) or DEFAULT_SEVERITY)
    title = str(attrs.get("title", "") or "")
    body = _emit_inline(node.get("children", []))

    try:
        emoji = icon_for(severity)
    except KeyError as e:
        degradations.append({
            "id": f"deg-{_sha256_hex((node_path + 'sev').encode())[:12]}",
            "node_path": node_path,
            "node_type": "admonition",
            "capability": "callout",
            "alternative": (
                f"blockquote con emoji '{DEFAULT_EMOJI}' prefijo ({e}; "
                f"default aplicado)"
            ),
            "vs_notion_api": (
                "notion_api habría emitido callout nativo con icon={emoji} y color={name}"
            ),
            "evidence": "rg '^> ' render/notion_md/<id>.md exit 0",
            "content_intact": True,
        })
        emoji = DEFAULT_EMOJI
    else:
        degradations.append({
            "id": f"deg-{_sha256_hex((node_path + 'sev').encode())[:12]}",
            "node_path": node_path,
            "node_type": "admonition",
            "capability": "callout",
            "alternative": (
                f"blockquote con emoji '{emoji}' prefijo + título + cuerpo "
                f"(sin color, sin icono nativo; fila 11 §6 contract)"
            ),
            "vs_notion_api": (
                "notion_api habría emitido callout nativo con icon={emoji} y "
                f"color={severity}"
            ),
            "evidence": f"rg '^> {emoji}' render/notion_md/<id>.md exit 0",
            "content_intact": True,
        })

    # Blockquote con emoji + título + cuerpo. Cada línea con prefijo "> ".
    header_line = f"{emoji} {title}".strip() if title else f"{emoji}"
    if body:
        lines = [f"> {header_line}", ">"]
        for ln in body.split("\n"):
            lines.append(f"> {ln}" if ln else ">")
    else:
        lines = [f"> {header_line}"]
    return "\n".join(lines)


def _emit_collapsible(node: Dict[str, Any]) -> str:
    """Collapsible → <details markdown="1"> (Notion importer convierte a toggle)."""
    attrs = node.get("attrs", {}) or {}
    title = str(attrs.get("title", "Detalles") or "Detalles")
    children = node.get("children", [])
    body_parts: List[str] = []
    for child in children:
        rendered = _emit_node(child)
        if rendered:
            body_parts.append(rendered)
    body = "\n\n".join(body_parts)
    return f"<details markdown=\"1\">\n<summary>{title}</summary>\n\n{body}\n\n</details>"


def _emit_quote(node: Dict[str, Any]) -> str:
    attrs = node.get("attrs", {}) or {}
    cite = str(attrs.get("cite", "") or "")
    body = _emit_inline(node.get("children", []))
    lines = [f"> {ln}" if ln else ">" for ln in body.split("\n")]
    if cite:
        lines.append(f"> — {cite}")
    return "\n".join(lines)


def _emit_columns(node: Dict[str, Any]) -> str:
    """Concatenación vertical: Notion importer no soporta columnas."""
    parts: List[str] = []
    for child in node.get("children", []):
        parts.append(_emit_node(child))
    return "\n\n".join(p for p in parts if p)


def _emit_divider(_node: Dict[str, Any]) -> str:
    return "---"


def _emit_property_block(node: Dict[str, Any],
                         degradations: List[Dict[str, Any]],
                         node_path: str) -> str:
    """Property-block → fila 15 §6 contract: se aplana como key: value en frontmatter."""
    attrs = node.get("attrs", {}) or {}
    name = str(attrs.get("name", "") or "")
    value = attrs.get("value", "")
    if not name:
        return ""
    degradations.append({
        "id": f"deg-{_sha256_hex((node_path + 'prop').encode())[:12]}",
        "node_path": node_path,
        "node_type": "property-block",
        "capability": "property-table",
        "alternative": (
            f"frontmatter YAML '{name}: {value}' (fila 15 §6 contract; Notion importer "
            f"preserva YAML como bloque de código, no como database property)"
        ),
        "vs_notion_api": (
            "notion_api habría emitido database property con tipo correcto "
            f"({attrs.get('type', 'string')} → notion_type via PROPERTY_TYPE_MAP)"
        ),
        "evidence": f"rg '^{name}:' render/notion_md/<id>.md exit 0",
        "content_intact": True,
    })
    return ""  # Se serializa en frontmatter, no en cuerpo.


def _emit_question(node: Dict[str, Any]) -> str:
    attrs = node.get("attrs", {}) or {}
    prompt = str(attrs.get("prompt", "") or "")
    body = _emit_inline(node.get("children", []))
    return f"**Pregunta:** {prompt}\n\n{body}"


def _emit_step(node: Dict[str, Any]) -> str:
    attrs = node.get("attrs", {}) or {}
    index = int(attrs.get("index", 1) or 1)
    body = _emit_inline(node.get("children", []))
    return f"**Paso {index}:** {body}"


def _emit_parameter_table(node: Dict[str, Any]) -> str:
    attrs = node.get("attrs", {}) or {}
    columns = attrs.get("columns", []) or []
    rows = attrs.get("rows", []) or []
    lines: List[str] = []
    if columns:
        lines.append("| " + " | ".join(str(c) for c in columns) + " |")
        lines.append("|" + "|".join("---" for _ in columns) + "|")
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def _emit_color_admonition_marker(node: Dict[str, Any],
                                  degradations: List[Dict[str, Any]],
                                  node_path: str) -> None:
    """Marca la degradación de color semántico (fila 19 §6 contract) si el nodo lleva color."""
    attrs = node.get("attrs", {}) or {}
    if attrs.get("color_token") or attrs.get("semantic_color"):
        degradations.append({
            "id": f"deg-{_sha256_hex((node_path + 'color').encode())[:12]}",
            "node_path": node_path,
            "node_type": "admonition",
            "capability": "semantic-color",
            "alternative": (
                "emoji semántico prefijo (fila 19 §6 contract; Notion importer no "
                "respeta CSS externo; el color se pierde como estilo, se preserva "
                "como emoji en el prefijo de admonition)"
            ),
            "vs_notion_api": (
                "notion_api habría emitido callout con color={color_name}"
            ),
            "evidence": "rg '^> (⚠️|ℹ️|❌|💡|✅)' render/notion_md/<id>.md exit 0",
            "content_intact": True,
        })


# ---------------------------------------------------------------------------
# Inline
# ---------------------------------------------------------------------------


def _emit_inline(children: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for child in children:
        parts.append(_emit_inline_node(child))
    return "".join(parts)


def _emit_inline_node(node: Dict[str, Any]) -> str:
    kind = node.get("node", "")
    attrs = node.get("attrs", {}) or {}
    if kind == "text":
        return attrs.get("text", "") or ""
    if kind == "strong":
        return "**" + _emit_inline(node.get("children", [])) + "**"
    if kind == "em":
        return "*" + _emit_inline(node.get("children", [])) + "*"
    if kind == "code-inline":
        return f"`{attrs.get('text', '') or ''}`"
    if kind == "link-external":
        text = attrs.get("text", "") or attrs.get("url", "")
        return f"[{text}]({attrs.get('url', '')})"
    if kind == "link-note":
        target = attrs.get("target", "") or ""
        text = attrs.get("text", "") or ""
        if text and text != target:
            return f"[[{target}|{text}]]"
        return f"[[{target}]]"
    if kind == "term-ref":
        term_id = attrs.get("term_id", "") or ""
        text = attrs.get("text", "") or term_id
        return f"[[term:{term_id}|{text}]]"
    if kind == "source-ref":
        block_id = attrs.get("block_id", "") or ""
        source_hash = attrs.get("source_hash", "") or ""
        short_hash = source_hash[:8] if source_hash else ""
        return f"<!-- src: {block_id} ({short_hash}) -->"
    if kind == "math-inline":
        return f"${attrs.get('latex', '') or ''}$"
    if kind == "footnote-ref":
        ref_id = attrs.get("ref_id", "") or ""
        text = attrs.get("text", "") or ""
        return f"[^{ref_id}]" + (f": {text}" if text else "")
    if kind == "keyboard":
        return f"`{attrs.get('text', '') or ''}`"
    if kind == "placeholder":
        return f"{{{{{attrs.get('text', '') or ''}}}}}"
    if kind == "deleted":
        return "~~" + _emit_inline(node.get("children", [])) + "~~"
    return attrs.get("text", "") or ""


# ---------------------------------------------------------------------------
# Dispatch principal
# ---------------------------------------------------------------------------


_NODE_DISPATCH = {
    "section": _emit_section,
    "paragraph": _emit_paragraph,
    "list": _emit_list,
    "checklist": _emit_checklist,
    "table": _emit_table_simple,
    "table-merged-cells": None,  # needs context
    "code": _emit_code,
    "console": _emit_console,
    "equation": _emit_equation,
    "figure": _emit_figure,
    "diagram": _emit_diagram,
    "admonition": None,           # needs context
    "collapsible": _emit_collapsible,
    "quote": _emit_quote,
    "columns": _emit_columns,
    "divider": _emit_divider,
    "property-block": None,        # needs context
    "question": _emit_question,
    "step": _emit_step,
    "parameter-table": _emit_parameter_table,
}


def _emit_node(node: Dict[str, Any],
               degradations: Optional[List[Dict[str, Any]]] = None,
               node_path: str = "") -> str:
    kind = node.get("node", "")
    # Detectar tablas con celdas combinadas (marcadas por attrs o capability).
    if kind == "table":
        attrs = node.get("attrs", {}) or {}
        cap = node.get("capability", "")
        is_merged = (
            cap == "table-merged-cells"
            or "matrix" in attrs
            or "cells_with_span" in attrs
            or "rowspan" in attrs
        )
        if is_merged:
            assert degradations is not None
            return _emit_table_merged(node, degradations, node_path)
    if kind == "admonition":
        assert degradations is not None
        return _emit_admonition(node, degradations, node_path)
    if kind == "property-block":
        assert degradations is not None
        return _emit_property_block(node, degradations, node_path)
    fn = _NODE_DISPATCH.get(kind)
    if fn is None:
        return ""
    return fn(node)


# ---------------------------------------------------------------------------
# Recolección de properties para el frontmatter
# ---------------------------------------------------------------------------


def _collect_frontmatter_props(ir: Dict[str, Any]) -> Dict[str, str]:
    """Recolecta property-blocks como `key: value` para el frontmatter."""
    out: Dict[str, str] = {}
    seen: set = set()

    def _walk(node: Any) -> None:
        if not isinstance(node, dict):
            return
        if node.get("node") == "property-block":
            attrs = node.get("attrs", {}) or {}
            name = attrs.get("name", "")
            value = attrs.get("value", "")
            if name and name not in seen:
                out[name] = _format_yaml_value(value)
                seen.add(name)
        for child in node.get("children", []) or []:
            _walk(child)

    _walk(ir)
    return out


def _format_yaml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value)
    if any(ch in s for ch in [":", "#", "{", "}", "[", "]", "&", "*", "!", "|",
                                ">", "'", "\"", "%", "@", "`"]):
        s = '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


# ---------------------------------------------------------------------------
# Emisión del artefacto Markdown
# ---------------------------------------------------------------------------


def emit_artifact(ir_obj: Dict[str, Any], ir_sha256: str,
                  source_hash: str, renderer_version: str,
                  out_dir: Path, degradations: List[Dict[str, Any]],
                  ir_node_count_holder: List[int]) -> Path:
    note_id = str(ir_obj.get("note_id", "note-unknown"))
    title = ir_obj.get("title", "") or ""

    # Cabecera YAML (contract §8) + properties del IR.
    frontmatter_props = _collect_frontmatter_props(ir_obj)
    auto_props = {
        "schema_version": '"1.0.0"',
        "target": "notion_md",
        f'note_id': f'"{note_id}"',
        "source_hash": f'"{source_hash}"',
        "ir_sha256": f'"{ir_sha256}"',
        "rendered_at": f'"{_now_utc_iso()}"',
        "renderer_version": f'"{renderer_version}"',
    }
    if title:
        auto_props["title"] = f'"{title}"'

    all_props = {**auto_props, **{k: v for k, v in frontmatter_props.items() if k not in auto_props}}
    header_lines = ["---"]
    for k, v in all_props.items():
        header_lines.append(f"{k}: {v}")
    header_lines.append("---")
    header_lines.append("")
    header = "\n".join(header_lines) + "\n"

    # Cuerpo.
    ir_nodes = traverse_ir(ir_obj)
    ir_node_count_holder[0] += len(ir_nodes)

    body_parts: List[str] = []
    if title:
        body_parts.append(f"# {title}\n")
    # Cabecera visual F75: tabla GFM con los 5 campos.
    cabecera_md = _emit_cabecera(ir_obj.get("frontmatter", {}) or {},
                                 dest="notion_md")
    if cabecera_md:
        body_parts.append(cabecera_md.rstrip())
    for path, node in ir_nodes:
        rendered = _emit_node(node, degradations=degradations, node_path=path)
        if rendered:
            body_parts.append(rendered)
    body = "\n\n".join(body_parts) + "\n"

    target_dir = out_dir / "render" / "notion_md"
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / f"{note_id}.md"
    _atomic_write_text(out_path, header + body)
    return out_path


# ---------------------------------------------------------------------------
# Reporte de degradación (contract §7 + §4 del plan)
# ---------------------------------------------------------------------------


CROSS_TARGET_DIFF = {
    "admonition": "notion_api: callout nativo con icon+color → notion_md: blockquote con emoji prefijo",
    "property-block": "notion_api: database property con tipo correcto → notion_md: frontmatter YAML (sin tipo)",
    "table-merged-cells": "notion_api: table con celdas vacías + callout matriz → notion_md: pipe table con celdas vacías + <details> matriz",
    "color-semantic": "notion_api: callout color semántico → notion_md: emoji semántico prefijo",
}


def build_report(source_hash: str, degradations: List[Dict[str, Any]],
                 ir_node_count: int, unresolved_targets: List[str],
                 published: Dict[str, str]) -> Tuple[Dict[str, Any], str]:
    content_loss = sum(1 for d in degradations if not d.get("content_intact", True))
    report = {
        "schema_version": "1.0.0",
        "target": "notion_md",
        "source_hash": source_hash,
        "generated_at": _now_utc_iso(),
        "totals": {
            "ir_nodes": ir_node_count,
            "degradations": len(degradations),
            "content_loss": content_loss,
        },
        "degradations": degradations,
        "unresolved_targets": sorted(set(unresolved_targets)),
        "published_pages": published,
        "cross_target_diff": {
            "vs_notion_api": CROSS_TARGET_DIFF,
            "note": (
                "Notion import (notion_md) usa solo el subconjunto Markdown que el "
                "importer de Notion convierte bien. notion_api (F55) tiene acceso "
                "completo al block model vía REST API. Diferencias resumidas arriba."
            )
        }
    }
    md_lines = [
        "# Reporte de degradación — Notion import (Markdown)",
        "",
        f"- **schema_version:** {report['schema_version']}",
        f"- **target:** notion_md",
        f"- **source_hash:** `{source_hash}`",
        f"- **generated_at:** {report['generated_at']}",
        "",
        "## Resumen",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        f"| Nodos IR totales | {ir_node_count} |",
        f"| Degradaciones | {len(degradations)} |",
        f"| Pérdida de contenido | {content_loss} |",
        f"| Targets sin resolver | {len(set(unresolved_targets))} |",
        f"| Notas publicadas | {len(published)} |",
        "",
        "## Diferencias vs notion_api (F55)",
        "",
        f"> {report['cross_target_diff']['note']}",
        "",
        "| Capacidad | notion_api (F55) | notion_md (F56) |",
        "|---|---|---|",
        "| admonition | callout nativo con icon+color | blockquote con emoji prefijo |",
        "| property-block | database property con tipo correcto | frontmatter YAML (sin tipo) |",
        "| table-merged-cells | table con celdas vacías + callout matriz | pipe table con celdas vacías + <details> matriz |",
        "| color semántico | callout color semántico | emoji semántico prefijo |",
        "",
    ]
    if degradations:
        md_lines.append("## Degradaciones")
        md_lines.append("")
        for i, d in enumerate(degradations, start=1):
            md_lines.append(f"### notion_md / {d.get('capability', '?')}")
            md_lines.append("")
            md_lines.append(f"- **node_path:** `{d.get('node_path')}`")
            md_lines.append(f"- **node_type:** `{d.get('node_type')}`")
            md_lines.append(f"- **alternative:** {d.get('alternative')}")
            md_lines.append(f"- **vs_notion_api:** {d.get('vs_notion_api', 'N/A')}")
            md_lines.append(f"- **evidence:** `{d.get('evidence')}`")
            md_lines.append(f"- **content_intact:** `{d.get('content_intact')}`")
            md_lines.append("")
    else:
        md_lines.append(
            "> Cero degradaciones en este destino. Esta sección se mantiene "
            "siempre para confirmar cobertura."
        )
        md_lines.append("")
    if unresolved_targets:
        md_lines.append("## Targets sin resolver")
        md_lines.append("")
        md_lines.append("Wikilinks que no apuntan a IDs existentes en el workdir:")
        md_lines.append("")
        for tgt in sorted(set(unresolved_targets)):
            md_lines.append(f"- `{tgt}`")
        md_lines.append("")
    md_lines.append("## Cobertura")
    md_lines.append("")
    md_lines.append(f"- Nodos contabilizados en el reporte: {len(degradations)}")
    md_lines.append(f"- Nodos IR totales: {ir_node_count}")
    md_lines.append(f"- content_loss: {content_loss} (debe ser 0; RC-01)")
    md = "\n".join(md_lines)
    return report, md


# ---------------------------------------------------------------------------
# Resolución de enlaces
# ---------------------------------------------------------------------------


def resolve_links(ir_list: List[Dict[str, Any]], note_ids: set,
                  term_ids: set, degradations: List[Dict[str, Any]]
                  ) -> List[str]:
    unresolved: List[str] = []
    for ir in ir_list:
        for tgt, kind in collect_link_targets(ir):
            if kind == "note" and tgt not in note_ids:
                unresolved.append(tgt)
                degradations.append({
                    "id": f"deg-{_sha256_hex((tgt + 'unr').encode())[:12]}",
                    "node_path": f"{ir.get('note_id', '?')}/link",
                    "node_type": "link-note",
                    "capability": "link-note",
                    "alternative": (
                        f"wikilink [[{tgt}]] intacto en el archivo; target no resuelto "
                        f"en el workdir actual (Notion importer dejará el wikilink "
                        f"como texto literal si la página no existe)"
                    ),
                    "vs_notion_api": (
                        "notion_api habría emitido mention.page si el target estaba "
                        "en el workdir, o wikilink literal si no (mismo comportamiento)"
                    ),
                    "evidence": f"rg '\\[{2}{tgt}\\]{2}' render/notion_md/<id>.md exit 0",
                    "content_intact": True,
                })
            elif kind == "term" and tgt not in term_ids:
                unresolved.append(f"term:{tgt}")
                degradations.append({
                    "id": f"deg-{_sha256_hex((tgt + 'unrterm').encode())[:12]}",
                    "node_path": f"{ir.get('note_id', '?')}/term",
                    "node_type": "term-ref",
                    "capability": "term-ref",
                    "alternative": (
                        f"wikilink [[term:{tgt}]] intacto; término no en glosario"
                    ),
                    "evidence": f"rg '\\[{2}term:{tgt}\\]{2}' render/notion_md/<id>.md exit 0",
                    "content_intact": True,
                })
    return unresolved


# ---------------------------------------------------------------------------
# Instrucciones de importación
# ---------------------------------------------------------------------------


def emit_import_instructions(workdir: Path, note_count: int,
                              renderer_version: str,
                              degradations_count: int) -> Path:
    target_dir = workdir / "render" / "notion_md"
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / "IMPORT_INSTRUCTIONS.md"
    content = textwrap.dedent(f"""\
        # Instrucciones de importación a Notion

        Esta carpeta contiene {note_count} nota(s) generada(s) por el renderer Notion-Markdown
        (`notion_md.py`, F56; renderer_version={renderer_version}). Para importarlas a Notion:

        ## Procedimiento

        1. Abre Notion (https://www.notion.so) y ve al workspace destino.
        2. En la barra lateral, click `•••` junto al workspace → **Import**.
        3. Selecciona formato **Markdown**.
        4. Sube cada archivo `<note-id>.md` individualmente, o arrastra la carpeta completa.
        5. Notion convierte automáticamente:
           - `# H1`, `## H2`, `### H3` → headings
           - `<details markdown="1">` → toggle blocks (preserva estructura)
           - ` ```mermaid ` → bloques Mermaid renderizados
           - `$$ ... $$` → equations (KaTeX)
           - `> ` → blockquotes
           - wikilinks `[[target]]` → page mentions (si la página existe en el workspace)
           - `- [ ]` / `- [x]` → to-do blocks
           - `| table |` → table blocks
        6. Tras la importación, repasa la página y mueve el bloque YAML frontmatter
           (si lo hay) a una sección "Metadatos" si quieres visibilidad separada.

        ## Limitaciones conocidas (vs. notion_api F55)

        Esta carpeta contiene {degradations_count} degradación(es) documentada(s) en
        `reports/render-degradation.md`. Las más relevantes:

        - **Callouts (admonitions)**: se importan como blockquotes con emoji prefijo.
          No conservan color ni icono nativo. Si necesitas callouts nativos,
          usa `scripts/render/notion_api.py` (F55) en su lugar.
        - **Propiedades de database**: el YAML frontmatter queda como bloque de código
          al inicio de la página; Notion import **no** lo convierte en database
          properties. Para properties tipadas, usa F55.
        - **Celdas combinadas**: la estructura se pierde; el contenido se preserva
          como tabla vacía + toggle con la matriz original.
        - **Colores semánticos**: solo emoji prefijo; sin CSS.

        Si encuentras bloques rotos o sintaxis cruda, **no los corrijas a mano**:
        re-renderiza con:

        ```bash
        python3 scripts/render/notion_md.py --ir <path> --profile <yaml> \\
                                            --out-dir <dir> \\
                                            --include-import-instructions
        ```

        ## Reportes

        - `reports/render-degradation.json`: machine-parseable, con `vs_notion_api`
          por entrada (qué habría hecho el renderer API).
        - `reports/render-degradation.md`: legible, con secciones por nota.
        """)
    _atomic_write_text(out_path, content)
    return out_path


# Necesario para emit_import_instructions.
import textwrap


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
        prog="notion_md.py",
        description="Renderer Notion import (Markdown) (L4) para el Note IR. F56.",
    )
    parser.add_argument("--ir", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--matrix", type=Path,
                        default=(Path(__file__).resolve().parents[2] /
                                 "references" / "08-render" / "capability-matrix.md"))
    parser.add_argument("--source-hash", type=str, default=None)
    parser.add_argument("--renderer-version", type=str, default="0.1.0")
    parser.add_argument("--include-import-instructions", action="store_true",
                        help="Escribe render/notion_md/IMPORT_INSTRUCTIONS.md con el "
                             "procedimiento manual de importación a Notion.")

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

    degradations: List[Dict[str, Any]] = []
    note_ids: set = set()
    term_ids: set = set()
    ir_objs: List[Dict[str, Any]] = []
    rendered_paths: Dict[str, str] = {}

    # Pase 1: cargar IRs.
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

    # Pase 2: renderizar.
    ir_node_count_holder: List[int] = [0]
    for ir_obj in ir_objs:
        ir_sha256 = _sha256_of_ir(ir_obj)
        try:
            out_path = emit_artifact(
                ir_obj=ir_obj,
                ir_sha256=ir_sha256,
                source_hash=source_hash,
                renderer_version=args.renderer_version,
                out_dir=args.out_dir,
                degradations=degradations,
                ir_node_count_holder=ir_node_count_holder,
            )
            rendered_paths[ir_obj.get("note_id", "?")] = str(out_path)
        except OSError as e:
            print(f"ERROR: no se pudo escribir {ir_obj.get('note_id', '?')}: {e}",
                  file=sys.stderr)
            return EXIT_FATAL

    # Pase 3: resolver enlaces.
    unresolved = resolve_links(ir_objs, note_ids, term_ids, degradations)

    # Pase 4: reporte.
    report, report_md = build_report(
        source_hash=source_hash,
        degradations=degradations,
        ir_node_count=ir_node_count_holder[0],
        unresolved_targets=unresolved,
        published=rendered_paths,
    )
    reports_dir = args.out_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(reports_dir / "render-degradation.json", report)
    _atomic_write_text(reports_dir / "render-degradation.md", report_md)

    # Instrucciones de importación.
    if args.include_import_instructions:
        emit_import_instructions(
            args.out_dir, len(ir_objs), args.renderer_version,
            len(degradations),
        )

    print(f"OK — {len(ir_objs)} nota(s) renderizada(s) en "
          f"{args.out_dir / 'render' / 'notion_md'}")
    print(f"     reporte: {reports_dir / 'render-degradation.json'}")
    if args.include_import_instructions:
        print(f"     instrucciones: {args.out_dir / 'render' / 'notion_md' / 'IMPORT_INSTRUCTIONS.md'}")
    if unresolved:
        print(f"WARN — {len(unresolved)} target(s) sin resolver (ver reporte).")
        return EXIT_WARN
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
