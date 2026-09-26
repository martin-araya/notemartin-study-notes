#!/usr/bin/env python3
"""obsidian.py — F54 · Renderer Obsidian (L4).

Traduce el Note IR validado a Markdown nativo de Obsidian 1.5+. Implementa la
interfaz `render(ir, profile, matrix) → (artifacts, degradation_report)`
especificada en `references/08-render/contract.md` (F53).

Capacidades soportadas (per `references/08-render/capability-matrix.md` §2.1):
  Obsidian = ✅ excepto Celdas combinadas (❌ → degradación fila 1 de contract §6).

Detalles de mapeo:
  - admonition → callout nativo (severity → tipo canónico, tabla cerrada)
  - collapsible → callout plegable (> [!note]+ o > [!note]-)
  - link-note → wikilink con alias ([[target|alias]] o [[target]])
  - property-block → tabla local; globales → YAML frontmatter
  - diagram Mermaid → bloque ```mermaid
  - Dataview → opt-in con --enable-dataview; default degradación elegante

Idempotencia (RC-04): `ir_sha256` en frontmatter; dos renders del mismo IR
producen salida byte-idéntica módulo timestamp.

Reporte doble: `reports/render-degradation.{json,md}` siempre (RC-03).

KNOWN DISCREPANCY: contract.md F53 usa dialectos `notion_api`/`notion_md`/
`html_pdf`/`flashcards`; profile.schema.json F11 usa `notion`/`html`/`pdf`/
`anki`. F54 solo toca `obsidian` (consistente en ambos). La resolución se
difiere a un ADR futuro (ver §6 del plan F54).

Uso:
    python3 scripts/render/obsidian.py --ir <path> --profile <path> --out-dir <dir>
                                          [--matrix <path>] [--source-hash <hex64>]
                                          [--enable-dataview]
                                          [--renderer-version <semver>]

Dependencias: Python 3.9+ stdlib puro (sin paquetes externos).
Códigos de salida: 0 OK · 1 error fatal · 2 OK con advertencias.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import importlib.util as _importlib_util
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Comparte atomic_write_json / atomic_write_text con F38/F39.
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
# Constantes inline (no YAML externo)
# ---------------------------------------------------------------------------

# Tabla cerrada de severidades del IR → tipo de callout nativo Obsidian (13).
# Severidades no nativas se mapean al callout semánticamente más cercano.
SEVERITY_TO_CALLOUT: Dict[str, str] = {
    "note": "note",
    "tip": "tip",
    "info": "info",
    "warning": "warning",
    "caution": "caution",
    "danger": "danger",
    "example": "example",
    "question": "question",
    "success": "success",
    "failure": "failure",
    "bug": "bug",
    "quote": "quote",
    "abstract": "abstract",
    # Severidades no nativas → equivalente semántico (preserva INV-07).
    "security": "warning",
    "performance": "note",
    "version": "info",
    "deprecated": "warning",
    "conflict": "warning",
    "external": "quote",
}

# Los 13 tipos de callout soportados nativamente por Obsidian 1.5+.
NATIVE_CALLOUTS: frozenset = frozenset(
    {"note", "tip", "info", "warning", "caution", "danger", "example",
     "question", "success", "failure", "bug", "quote", "abstract"}
)

DEFAULT_SEVERITY = "note"

# Sufijos para callouts plegables: `+` = default open; `-` = default closed.
OPEN_SUFFIX = "+"
CLOSED_SUFFIX = "-"


# ---------------------------------------------------------------------------
# Utilidades de bajo nivel
# ---------------------------------------------------------------------------


def _now_utc_iso() -> str:
    """ISO 8601 UTC con sufijo Z (formato del contrato §7.1)."""
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_of_ir(ir_obj: Any) -> str:
    """sha256 hex de un IR serializado canónicamente.

    No es seguridad: es fingerprint para idempotencia (RC-04). Mismo IR
    ordenado siempre produce el mismo hash.
    """
    canonical = json.dumps(ir_obj, sort_keys=True, ensure_ascii=False)
    return _sha256_hex(canonical.encode("utf-8"))


def _ir_sha256_from_path(ir_path: Path) -> str:
    return _sha256_hex(ir_path.read_bytes())


# ---------------------------------------------------------------------------
# Mini-parser YAML para `profile.targets.obsidian.*`
# ---------------------------------------------------------------------------
# Solo necesita leer un subárbol escalar (string, bool). Stdlib puro, sin
# dependencias externas. Mantiene el principio F17/F38 (sin PyYAML obligatorio).


def _parse_minimal_yaml(text: str) -> Dict[str, Any]:
    """Parser YAML mínimo para subárbol escalar.

    Soporta solo:
      - pares `key: value` (value escalar: string, bool, número)
      - anidamiento por indentación de 2 espacios
      - listas con `- value`

    NO soporta: anclas, referencias, multi-doc, comillas escapadas complejas.
    Suficiente para leer `targets.obsidian.folder`, `vault`, `enabled`.
    """
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
            value = _coerce_scalar(value)
            if isinstance(parent, list):
                parent.append(value)
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if not value:
                # Anidamiento: el padre se convierte en dict/list en el siguiente nivel.
                new_dict: Dict[str, Any] = {}
                if isinstance(parent, dict):
                    parent[key] = new_dict
                stack.append((indent, new_dict))
            else:
                coerced = _coerce_scalar(value)
                if isinstance(parent, dict):
                    parent[key] = coerced
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
    # Quita comillas simples o dobles si las lleva.
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def _get_obsidian_config(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae `targets.obsidian` del perfil."""
    targets = profile.get("targets", {}) or {}
    obs = targets.get("obsidian", {}) or {}
    return obs if isinstance(obs, dict) else {}


# ---------------------------------------------------------------------------
# Carga de la matriz desde capability-matrix.md
# ---------------------------------------------------------------------------


def _load_matrix_from_md(path: Path) -> Dict[str, Dict[str, str]]:
    """Lee la tabla principal de capability-matrix.md y la expone como dict.

    Devuelve {capability: {target: estado}}.
    Estados: '✅', '⚠', '❌'.

    Implementación: regex sobre líneas que empiezan con `| **N. <name>** |`
    hasta la línea que empieza con `|---` después de la cabecera.
    """
    text = path.read_text(encoding="utf-8")
    table: Dict[str, Dict[str, str]] = {}

    # Cabecera de columnas: la fila de pipe inicial antes de los separadores.
    # Buscamos el patrón `| Capacidad | Obsidian | Notion API | ...`
    header_match = re.search(
        r"\|\s*Capacidad\s*\|[^\n]+\|",
        text,
    )
    if not header_match:
        return table
    header_line = header_match.group(0)
    # Extrae los nombres de las columnas (columnas 2..N).
    targets = [
        c.strip()
        for c in header_line.strip().strip("|").split("|")[1:]
        if c.strip()
    ]
    # Normaliza "Notion API" y "Notion import" a sus nombres canónicos del contrato.
    norm = {
        "Obsidian": "obsidian",
        "Notion API": "notion_api",
        "Notion import": "notion_md",
        "AppFlowy": "appflowy",
        "Markdown": "markdown",
        "HTML/PDF": "html_pdf",
        "Flashcards": "flashcards",
    }
    targets_canonical = [norm.get(t, t) for t in targets]

    # Filas de la tabla: líneas que empiezan con `| **N. <name>** |`.
    row_re = re.compile(
        r"\|\s*\*\*(\d+)\.\s*([^*]+?)\*\*\s*\|[^\n]+\|",
    )
    for m in row_re.finditer(text):
        cap_index = m.group(1)
        cap_name = m.group(2).strip()
        cells = [c.strip() for c in m.group(0).strip().strip("|").split("|")[1:]]
        if len(cells) < len(targets_canonical):
            continue
        per_target: Dict[str, str] = {}
        for tgt, cell in zip(targets_canonical, cells):
            if cell.startswith("✅"):
                per_target[tgt] = "✅"
            elif cell.startswith("⚠"):
                per_target[tgt] = "⚠"
            elif cell.startswith("❌"):
                per_target[tgt] = "❌"
            else:
                per_target[tgt] = "?"
        table[f"cap-{cap_index}"] = per_target
        table[f"cap-{cap_index}-name"] = {"_name": cap_name}  # type: ignore
    return table


def _resolve_capability_for_node(node: Dict[str, Any]) -> str:
    """Lee `node.capability` (string) del IR."""
    return str(node.get("capability", "") or "")


# ---------------------------------------------------------------------------
# Emisión de nodos IR → Markdown
# ---------------------------------------------------------------------------


def _escape_md(text: str) -> str:
    """Escapa caracteres que rompen Markdown estructural.

    Solo escapa lo mínimo necesario para que la salida sea Markdown válido
    sin destruir contenido fáctico (literales de la fuente, INV-09).
    """
    if not text:
        return ""
    # No escapamos `*`, `_`, `~`, `` ` `` inline porque pueden ser parte del texto.
    # Escapamos secuencias de cierre de bloque: `]`, `\`.
    return text.replace("\\", "\\\\").replace("]", "\\]")


def _emit_section(node: Dict[str, Any]) -> str:
    level = int(node.get("attrs", {}).get("level", 1) or 1)
    level = max(1, min(level, 6))
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


def _emit_table(node: Dict[str, Any]) -> str:
    """Tabla Markdown estándar.

    Para celdas combinadas (❌ en Obsidian), apply_degradations ya ha
    convertido el nodo en `table-merged-cells`; _emit_merged_table lo
    serializa. Aquí manejamos tablas simples (con `rows`).
    """
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


def _emit_merged_table(node: Dict[str, Any]) -> str:
    """Tabla con celdas combinadas (degradación fila 1 contract §6).

    Produce tres bloques:
      1. Tabla principal con celdas vacías replicando la estructura.
      2. Leyenda con section_path.
      3. <details> con la matriz completa (incluye rowspan/colspan).
    """
    attrs = node.get("attrs", {}) or {}
    headers = attrs.get("headers", []) or []
    cells = attrs.get("cells", []) or []
    matrix = attrs.get("matrix", []) or []
    section_path = attrs.get("section_path", "fuente")
    n_rows = len(cells) if cells else len(matrix)
    n_cols = max(len(row) for row in cells) if cells else (len(headers) if headers else 0)

    lines: List[str] = []
    # Bloque 1: tabla vacía.
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

    # Bloque 2: leyenda.
    lines.append("")
    lines.append(
        f"> [!warning] Estructura original con celdas combinadas "
        f"({n_rows} filas × {n_cols} cols) — ver fuente §{section_path}"
    )

    # Bloque 3: <details> con la matriz completa.
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
    lang = attrs.get("lang", "") or ""
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
    lines: List[str] = []
    if src.startswith(("http://", "https://", "/", "./", "../")):
        lines.append(f"![{alt}]({src})")
    else:
        # Asume asset local → wikilink.
        lines.append(f"![[{src}]]")
    if caption:
        lines.append(f"*{caption}*")
    return "\n".join(lines)


def _emit_diagram(node: Dict[str, Any]) -> str:
    attrs = node.get("attrs", {}) or {}
    kind = attrs.get("kind", "mermaid")
    text = attrs.get("text", "") or ""
    alt = attrs.get("alt", "") or ""
    if kind == "mermaid":
        block = f"```mermaid\n{text}\n```"
        if alt:
            block = f"<!-- {alt} -->\n{block}"
        return block
    # Otros kinds: bloque verbatim.
    return f"```{kind}\n{text}\n```"


def _emit_admonition(node: Dict[str, Any], degradations: List[Dict[str, Any]],
                     node_path: str) -> str:
    attrs = node.get("attrs", {}) or {}
    severity = str(attrs.get("severity", DEFAULT_SEVERITY) or DEFAULT_SEVERITY)
    title = str(attrs.get("title", "") or "")

    # Mapeo a callout nativo.
    callout_type = SEVERITY_TO_CALLOUT.get(severity)
    if callout_type is None:
        degradations.append({
            "node_path": node_path,
            "node_type": "admonition",
            "capability": "callout",
            "alternative": (
                f"callout nativo '{DEFAULT_SEVERITY}' (severity='{severity}' no en "
                f"SEVERITY_TO_CALLOUT; default aplicado)"
            ),
            "evidence": (
                f"rg '^> \\[!{DEFAULT_SEVERITY}\\]' <artifact>  exit 0; severidad "
                f"'{severity}' registrada en report"
            ),
            "content_intact": True,
        })
        callout_type = DEFAULT_SEVERITY
    elif callout_type not in NATIVE_CALLOUTS:
        # No debería ocurrir (SEVERITY_TO_CALLOUT ya mapea a nativos), pero defensa.
        degradations.append({
            "node_path": node_path,
            "node_type": "admonition",
            "capability": "callout",
            "alternative": f"callout nativo '{DEFAULT_SEVERITY}' (fallback defensivo)",
            "evidence": f"rg '^> \\[!{DEFAULT_SEVERITY}\\]' <artifact>  exit 0",
            "content_intact": True,
        })
        callout_type = DEFAULT_SEVERITY

    body = _emit_inline(node.get("children", []))
    title_line = f"{title}" if title else ""
    # Cuerpo: cada línea prefija con `> `. Si el cuerpo tiene líneas vacías,
    # se mantienen como `>` para preservar la estructura.
    body_lines: List[str] = []
    for ln in body.split("\n"):
        if ln == "":
            body_lines.append(">")
        else:
            body_lines.append(f"> {ln}")
    if not body_lines:
        body_lines = [">"]

    if title_line:
        first = f"> [!{callout_type}] {title_line}"
    else:
        first = f"> [!{callout_type}]"
    return "\n".join([first] + body_lines)


def _emit_collapsible(node: Dict[str, Any]) -> str:
    attrs = node.get("attrs", {}) or {}
    title = str(attrs.get("title", "Detalles") or "Detalles")
    default_open = bool(attrs.get("default_open", False))
    suffix = OPEN_SUFFIX if default_open else CLOSED_SUFFIX

    # Cuerpo del collapsible: puede contener bloque o inline.
    children = node.get("children", [])
    body_parts: List[str] = []
    for child in children:
        body_parts.append(_emit_node(child))
    body = "\n\n".join(p for p in body_parts if p)
    body_lines: List[str] = []
    for ln in body.split("\n"):
        if ln == "":
            body_lines.append(">")
        else:
            body_lines.append(f"> {ln}")
    return f"> [!note]{suffix} {title}\n" + "\n".join(body_lines)


def _emit_quote(node: Dict[str, Any]) -> str:
    attrs = node.get("attrs", {}) or {}
    cite = str(attrs.get("cite", "") or "")
    body = _emit_inline(node.get("children", []))
    lines = [f"> {ln}" if ln else ">" for ln in body.split("\n")]
    if cite:
        lines.append(f"> — {cite}")
    return "\n".join(lines)


def _emit_columns(node: Dict[str, Any]) -> str:
    """Concatenación vertical (Obsidian no soporta columnas nativas).

    No es una celda ❌ de F8 §2.1; se documenta inline.
    """
    parts: List[str] = []
    for child in node.get("children", []):
        parts.append(_emit_node(child))
    return "\n\n".join(p for p in parts if p)


def _emit_divider(_node: Dict[str, Any]) -> str:
    return "---"


def _emit_property_block(node: Dict[str, Any]) -> str:
    """Propiedad local → tabla Markdown simple."""
    attrs = node.get("attrs", {}) or {}
    name = str(attrs.get("name", "") or "")
    value = attrs.get("value", "")
    return f"| {name} | {value} |\n|---|---|"


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


def _emit_query(node: Dict[str, Any], enable_dataview: bool) -> str:
    """Tabla con filtro → degradación Dataview.

    Caso A (--enable-dataview false, default): admonition estática.
    Caso B (--enable-dataview true): bloque ```dataview en admonition.
    """
    attrs = node.get("attrs", {}) or {}
    query = str(attrs.get("query", "") or "")
    title = "Consulta dinámica (Dataview deshabilitado)"
    if enable_dataview:
        return (
            f"> [!info]+ {title.replace('(Dataview deshabilitado)', '(Dataview habilitado)')}\n"
            f"> ```dataview\n"
            f"> {query}\n"
            f"> ```"
        )
    return (
        f"> [!info]+ {title}\n"
        f"> Esta consulta requiere el plugin Dataview. Resultado estático de build-time:\n"
        f"> \n"
        f"> | Query | Resultado |\n"
        f"> |---|---|\n"
        f"> | `{query}` | (no resuelto en build; ejecutar Dataview para datos en vivo) |"
    )


# ---------------------------------------------------------------------------
# Inline nodes
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
    # Inline desconocido → texto literal preservado.
    return attrs.get("text", "") or ""


# ---------------------------------------------------------------------------
# Dispatch principal
# ---------------------------------------------------------------------------


_NODE_DISPATCH = {
    "section": _emit_section,
    "paragraph": _emit_paragraph,
    "list": _emit_list,
    "checklist": _emit_checklist,
    "table": _emit_table,
    "table-merged-cells": _emit_merged_table,
    "code": _emit_code,
    "console": _emit_console,
    "equation": _emit_equation,
    "figure": _emit_figure,
    "diagram": _emit_diagram,
    "admonition": None,  # necesita context
    "collapsible": _emit_collapsible,
    "quote": _emit_quote,
    "columns": _emit_columns,
    "divider": _emit_divider,
    "property-block": _emit_property_block,
    "question": _emit_question,
    "step": _emit_step,
    "parameter-table": _emit_parameter_table,
    "query": None,  # necesita context
}


def _emit_node(node: Dict[str, Any], degradations: Optional[List[Dict[str, Any]]] = None,
               node_path: str = "", enable_dataview: bool = False) -> str:
    kind = node.get("node", "")
    if kind == "admonition":
        assert degradations is not None
        return _emit_admonition(node, degradations, node_path)
    if kind == "query":
        return _emit_query(node, enable_dataview)
    fn = _NODE_DISPATCH.get(kind)
    if fn is None:
        # Nodo desconocido → texto vacío (preserva INV-07 al no inventar).
        return ""
    return fn(node)


# ---------------------------------------------------------------------------
# Recorrido del IR y resolución de capacidades
# ---------------------------------------------------------------------------


def traverse_ir(ir: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    """Depth-first traversal; yields (path, node) tuples."""
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


def resolve_capabilities(
    ir_nodes: List[Tuple[str, Dict[str, Any]]],
    matrix: Dict[str, Dict[str, str]],
    target: str = "obsidian",
) -> List[Tuple[str, str, str, str]]:
    """Devuelve (path, capability, node_type, status) por nodo."""
    out: List[Tuple[str, str, str, str]] = []
    for path, node in ir_nodes:
        cap = _resolve_capability_for_node(node)
        node_type = node.get("node", "")
        # Mapeo de capability (IR) a clave de matriz.
        # Simplificación: la capability del IR ya viene mapeada por F14.
        # Si la matriz no la tiene, status = "?" (no degradación).
        status = "?"
        for cap_key, per_target in matrix.items():
            if cap_key.endswith("-name"):
                continue
            if per_target.get("_name", "").lower() == cap.lower():
                status = per_target.get(target, "?")
                break
        out.append((path, cap, node_type, status))
    return out


def apply_degradations(
    ir_nodes: List[Tuple[str, Dict[str, Any]]],
    caps: List[Tuple[str, str, str, str]],
    matrix: Dict[str, Dict[str, str]],
    target: str,
    degradations: List[Dict[str, Any]],
    ir_obj: Dict[str, Any],
) -> None:
    """Aplica degradaciones al IR en memoria y registra entradas en `degradations`.

    Caso actual (Obsidian):
      - Celdas combinadas (❌) → tabla vacía + leyenda + <details>.
      - Consultas dinámicas (query con `--enable-dataview` false) →
        admonition estática con la query verbatim.
      - Consultas dinámicas (query con `--enable-dataview` true) →
        admonition con bloque ```dataview.

    La degradación se dispara por la capability declarada en el IR (no solo
    por el estado de la matriz), porque el IR es la fuente de verdad de la
    intención semántica (F14).
    """
    if target != "obsidian":
        return
    for (path, cap, node_type, status), (_np, n) in zip(caps, ir_nodes):
        # Celdas combinadas: capability = table-merged-cells O marker en attrs.
        if n.get("node") == "table" and (
            cap == "table-merged-cells"
            or any(
                k in (n.get("attrs", {}) or {})
                for k in ("rowspan", "colspan", "matrix", "cells_with_span")
            )
        ):
            attrs = n.setdefault("attrs", {})
            if "matrix" not in attrs:
                attrs["matrix"] = _build_matrix_from_table(n)
            n["node"] = "table-merged-cells"
            degradations.append({
                "node_path": path,
                "node_type": "table",
                "capability": "table-merged-cells",
                "alternative": (
                    "Tabla Markdown con celdas vacías + nota de leyenda + "
                    "<details> con la matriz completa (fila 1 contract §6)"
                ),
                "evidence": (
                    "rg '<details markdown' render/obsidian/<id>.md  exit 0; "
                    "rg 'Estructura original' render/obsidian/<id>.md  exit 0"
                ),
                "content_intact": True,
            })
            continue

        # Consultas dinámicas: capability = query → nodo `query` para que
        # _emit_node enrute a _emit_query (con su manejo de Dataview).
        if n.get("node") == "table" and cap == "query":
            n["node"] = "query"
            # No se registra entrada de degradación: para Obsidian con
            # --enable-dataview true la consulta se renderiza nativa; con
            # false se aplica la degradación elegante (admonition estática)
            # que también preserva el contenido.


def _build_matrix_from_table(table_node: Dict[str, Any]) -> List[List[Any]]:
    """Convierte un `table` IR en una matriz rectangular para el <details>.

    Si el IR trae `cells` (lista de filas × columnas), se respeta.
    Si trae `rows` (filas simples), se replica como matriz.
    Si trae `rowspan`/`colspan` (esquema), se expande a celdas placeholder.
    """
    attrs = table_node.get("attrs", {}) or {}
    if "cells" in attrs:
        return attrs["cells"]
    headers = attrs.get("headers", []) or []
    rows = attrs.get("rows", []) or []
    if rows:
        return [list(r) for r in rows]
    if headers:
        # Tabla sin filas; matriz 1×N.
        return [[h for h in headers]]
    return [[]]


# ---------------------------------------------------------------------------
# Resolución de enlaces (criterio 3: cero enlaces rotos)
# ---------------------------------------------------------------------------


def collect_link_targets(ir: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Recolecta todos los targets de `link-note` y `term-ref` del IR.

    Devuelve lista de (target, kind) donde kind ∈ {'note', 'term'}.
    """
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


def resolve_links(
    ir_list: List[Dict[str, Any]],
    note_ids: set,
    term_ids: set,
    degradations: List[Dict[str, Any]],
    workdir_irs: List[Dict[str, Any]],
) -> List[str]:
    """Detecta enlaces cuyo target no existe en el workdir.

    Devuelve la lista de `unresolved_targets` (strings). El wikilink
    permanece en la nota (no se omite; INV-07). Las entradas de degradación
    son informativas; `content_intact: true` siempre.
    """
    unresolved: List[str] = []
    for ir in ir_list:
        for tgt, kind in collect_link_targets(ir):
            if kind == "note" and tgt not in note_ids:
                unresolved.append(tgt)
                degradations.append({
                    "node_path": f"{ir.get('note_id', '?')}/link",
                    "node_type": "link-note",
                    "capability": "link-note",
                    "alternative": (
                        f"wikilink [[{tgt}]] intacto en la nota; target no resuelto "
                        f"en el workdir actual"
                    ),
                    "evidence": (
                        f"rg '\\[{2}{tgt}\\]{2}' render/obsidian/{ir.get('note_id', '?')}.md "
                        f"exit 0; target listado en report unresolved_targets[]"
                    ),
                    "content_intact": True,
                })
            elif kind == "term" and tgt not in term_ids:
                unresolved.append(f"term:{tgt}")
                degradations.append({
                    "node_path": f"{ir.get('note_id', '?')}/term",
                    "node_type": "term-ref",
                    "capability": "term-ref",
                    "alternative": (
                        f"wikilink [[term:{tgt}]] intacto en la nota; término no en glosario"
                    ),
                    "evidence": (
                        f"rg '\\[{2}term:{tgt}\\]{2}' render/obsidian/{ir.get('note_id', '?')}.md "
                        f"exit 0"
                    ),
                    "content_intact": True,
                })
    return unresolved


# ---------------------------------------------------------------------------
# Emisión del artefacto Markdown (con cabecera YAML contract §8)
# ---------------------------------------------------------------------------


def emit_artifact(
    ir_obj: Dict[str, Any],
    ir_sha256: str,
    source_hash: str,
    renderer_version: str,
    folder: str,
    out_dir: Path,
    degradations: List[Dict[str, Any]],
    enable_dataview: bool,
    matrix: Optional[Dict[str, Dict[str, str]]] = None,
) -> Path:
    """Genera el archivo Markdown de Obsidian; devuelve la ruta."""
    note_id = str(ir_obj.get("note_id", "note-unknown"))
    title = ir_obj.get("title", "") or ""

    # Cabecera YAML (contract §8).
    header = (
        "---\n"
        f'schema_version: "1.0.0"\n'
        f"target: obsidian\n"
        f'note_id: "{note_id}"\n'
        f'source_hash: "{source_hash}"\n'
        f'ir_sha256: "{ir_sha256}"\n'
        f'rendered_at: "{_now_utc_iso()}"\n'
        f'renderer_version: "{renderer_version}"\n'
        "---\n"
    )

    # Cuerpo: aplicar degradaciones primero.
    ir_nodes = traverse_ir(ir_obj)
    matrix = matrix if matrix is not None else {}
    caps = resolve_capabilities(ir_nodes, matrix, "obsidian")
    apply_degradations(
        ir_nodes, caps, matrix, "obsidian", degradations, ir_obj
    )

    body_parts: List[str] = []
    if title:
        body_parts.append(f"# {title}\n")
    for _path, node in ir_nodes:
        rendered = _emit_node(node, degradations=degradations, node_path=_path,
                              enable_dataview=enable_dataview)
        if rendered:
            body_parts.append(rendered)
    body = "\n\n".join(body_parts) + "\n"

    # Path final.
    target_dir = out_dir / "render" / "obsidian" / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / f"{note_id}.md"
    _atomic_write_text(out_path, header + body)
    return out_path


# ---------------------------------------------------------------------------
# Reporte de degradación (contract §7)
# ---------------------------------------------------------------------------


def build_report(
    source_hash: str,
    degradations: List[Dict[str, Any]],
    ir_node_count: int,
    unresolved_targets: List[str],
) -> Tuple[Dict[str, Any], str]:
    """Construye el par (json, md) del reporte de degradación (contract §7)."""
    content_loss = sum(1 for d in degradations if not d.get("content_intact", True))
    report = {
        "schema_version": "1.0.0",
        "target": "obsidian",
        "source_hash": source_hash,
        "generated_at": _now_utc_iso(),
        "totals": {
            "ir_nodes": ir_node_count,
            "degradations": len(degradations),
            "content_loss": content_loss,
        },
        "degradations": degradations,
        "unresolved_targets": sorted(set(unresolved_targets)),
    }
    md_lines: List[str] = [
        "# Reporte de degradación — Obsidian",
        "",
        f"- **schema_version:** {report['schema_version']}",
        f"- **source_hash:** `{source_hash}`",
        f"- **target:** obsidian",
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
        "",
    ]
    if degradations:
        md_lines.append("## Degradaciones")
        md_lines.append("")
        for i, d in enumerate(degradations, start=1):
            md_lines.append(f"### obsidian / {d.get('capability', '?')}")
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
    if unresolved_targets:
        md_lines.append("## Targets sin resolver")
        md_lines.append("")
        md_lines.append("Los siguientes wikilinks permanecen en las notas pero no "
                       "apuntan a IDs existentes en el workdir actual:")
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
# Carga de entradas
# ---------------------------------------------------------------------------


def load_ir(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_profile(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    return _parse_minimal_yaml(text)


def load_matrix(path: Path) -> Dict[str, Dict[str, str]]:
    return _load_matrix_from_md(path)


def collect_workdir_irs(ir_arg: Path) -> List[Path]:
    """Devuelve la lista de rutas IR a procesar (archivo o directorio)."""
    if ir_arg.is_dir():
        return sorted(ir_arg.glob("*.json"))
    return [ir_arg]


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
        prog="obsidian.py",
        description="Renderer Obsidian (L4) para el Note IR. Implementa el contrato F53.",
    )
    parser.add_argument("--ir", required=True, type=Path,
                        help="Ruta al IR (archivo .json o directorio de IRs).")
    parser.add_argument("--profile", required=True, type=Path,
                        help="Ruta al profile.yaml.")
    parser.add_argument("--out-dir", required=True, type=Path,
                        help="Raíz del workdir; renderer crea render/obsidian/ y reports/.")
    parser.add_argument("--matrix", type=Path,
                        default=(Path(__file__).resolve().parents[2] /
                                 "references" / "08-render" / "capability-matrix.md"),
                        help="Ruta al capability-matrix.md (default: 08-render/).")
    parser.add_argument("--source-hash", type=str, default=None,
                        help="sha256 hex 64 del SDM (override; si no, se lee de manifest.json).")
    parser.add_argument("--enable-dataview", action="store_true",
                        help="Permite bloques Dataview en admonition. Default: degradación estática.")
    parser.add_argument("--renderer-version", type=str, default="0.1.0",
                        help="Versión del renderer (entra en frontmatter).")

    args = parser.parse_args(argv)

    if not args.ir.exists():
        print(f"ERROR: IR no encontrado en {args.ir}", file=sys.stderr)
        return EXIT_FATAL
    if not args.profile.exists():
        print(f"ERROR: profile no encontrado en {args.profile}", file=sys.stderr)
        return EXIT_FATAL
    if not args.matrix.exists():
        print(f"ERROR: matrix no encontrada en {args.matrix}", file=sys.stderr)
        return EXIT_FATAL

    profile = load_profile(args.profile)
    obs_cfg = _get_obsidian_config(profile)
    folder = str(obs_cfg.get("folder", "notes/") or "notes/")
    folder = folder.rstrip("/") + "/"

    matrix = load_matrix(args.matrix)
    source_hash = derive_source_hash(args.out_dir, args.source_hash)
    if not re.match(r"^[0-9a-f]{64}$", source_hash):
        print(f"WARN: source_hash inválido ({source_hash!r}); usando zeros.",
              file=sys.stderr)
        source_hash = "0" * 64

    ir_paths = collect_workdir_irs(args.ir)
    if not ir_paths:
        print(f"ERROR: no hay IRs en {args.ir}", file=sys.stderr)
        return EXIT_FATAL

    degradations: List[Dict[str, Any]] = []
    note_ids: set = set()
    term_ids: set = set()
    ir_objs: List[Dict[str, Any]] = []
    total_nodes = 0
    warnings = 0

    # Pase 1: cargar todos los IRs y recolectar note_ids / term_ids.
    for ir_path in ir_paths:
        try:
            ir_obj = load_ir(ir_path)
        except (json.JSONDecodeError, OSError) as e:
            print(f"WARN: no se pudo cargar {ir_path}: {e}", file=sys.stderr)
            warnings += 1
            continue
        ir_objs.append(ir_obj)
        note_ids.add(ir_obj.get("note_id", ""))
        # Term ids desde term-ref en el IR.
        for tgt, kind in collect_link_targets(ir_obj):
            if kind == "term":
                term_ids.add(tgt)
        total_nodes += sum(1 for _ in traverse_ir(ir_obj))

    # Pase 2: renderizar cada IR.
    rendered_paths: List[Path] = []
    for ir_obj in ir_objs:
        ir_sha256 = _sha256_of_ir(ir_obj)
        try:
            out_path = emit_artifact(
                ir_obj=ir_obj,
                ir_sha256=ir_sha256,
                source_hash=source_hash,
                renderer_version=args.renderer_version,
                folder=folder,
                out_dir=args.out_dir,
                degradations=degradations,
                enable_dataview=args.enable_dataview,
                matrix=matrix,
            )
            rendered_paths.append(out_path)
        except OSError as e:
            print(f"ERROR: no se pudo escribir {ir_obj.get('note_id', '?')}: {e}",
                  file=sys.stderr)
            return EXIT_FATAL

    # Pase 3: resolver enlaces (criterio 3).
    unresolved = resolve_links(ir_objs, note_ids, term_ids, degradations, ir_objs)

    # Pase 4: construir y escribir reporte.
    report, report_md = build_report(
        source_hash=source_hash,
        degradations=degradations,
        ir_node_count=total_nodes,
        unresolved_targets=unresolved,
    )
    reports_dir = args.out_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(reports_dir / "render-degradation.json", report)
    _atomic_write_text(reports_dir / "render-degradation.md", report_md)

    # Salida legible.
    print(f"OK — {len(rendered_paths)} nota(s) renderizada(s) en "
          f"{args.out_dir / 'render' / 'obsidian' / folder}")
    print(f"     reporte: {reports_dir / 'render-degradation.json'}")
    if unresolved:
        print(f"WARN — {len(unresolved)} target(s) sin resolver (ver reporte).")
        return EXIT_WARN
    if warnings:
        return EXIT_WARN
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
