#!/usr/bin/env python3
"""markdown.py — F58 · Renderer Markdown estándar (L4).

Genera archivos Markdown GFM (GitHub-Flavored Markdown) optimizados para
visualización en GitHub. Implementa la interfaz `render(ir, profile, matrix) →
(artifacts, degradation_report)` del contrato F53
(`references/08-render/contract.md`).

Capacidades (per `references/08-render/capability-matrix.md` §2.1):
  Markdown = 9 ✅ + 5 ❌ (Celdas combinadas, Callouts, Backlinks,
  Consultas dinámicas, Colores semánticos).

Detalles:
  - admonition → blockquote con emoji + CSS class (`> [!note]+ ⚠️`)
  - collapsible → <details markdown="1"> con <summary>
  - link-note → [text](<note-id>.md) (ruta relativa, criterio 3)
  - propiedades → YAML frontmatter (key: value)
  - diagram → ```mermaid block (GitHub nativo) + imagen pre-renderizada (F68 opt-in)
  - backlinks → sección "## Referenciado por" al final (fila 7 §6)
  - queries → tabla estática "## Consultas habituales" (fila 16 §6)

Idempotencia (RC-04): `ir_sha256` en frontmatter; dos renders del mismo IR
producen salida byte-idéntica módulo timestamp.

Reporte doble: `reports/render-degradation.{json,md}` siempre (RC-03).

Uso:
    python3 scripts/render/markdown.py --ir <path> --profile <path> --out-dir <dir>
                                        [--matrix <path>] [--source-hash <hex64>]
                                        [--renderer-version <semver>]
                                        [--base-url <url>]
                                        [--generate-backlinks]
                                        [--generate-queries-table]
                                        [--pre-render-diagrams]

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
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


# Comparte atomic_write_json / atomic_write_text con F38/F39/F54/F55/F56/F57.
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

SEVERITY_TO_EMOJI: Dict[str, str] = {
    "note": "📝",
    "tip": "💡",
    "info": "ℹ️",
    "warning": "⚠️",
    "caution": "⚠️",
    "danger": "🚫",
    "example": "📋",
    "question": "❓",
    "success": "✅",
    "failure": "❌",
    "bug": "🐛",
    "quote": "💬",
    "abstract": "📑",
    "security": "🔒",
    "performance": "⚡",
    "version": "🏷️",
    "deprecated": "⛔",
    "conflict": "⚠️",
    "external": "🔗",
}

DEFAULT_SEVERITY = "note"
DEFAULT_EMOJI = "📝"

SEMANTIC_TOKENS: Dict[str, str] = {
    "warning": "warning",
    "danger": "danger",
    "info": "info",
    "success": "success",
    "tip": "tip",
}

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

BACKLINK_HEADING = "## Referenciado por"
QUERIES_HEADING = "## Consultas habituales"


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


def _get_markdown_config(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Acepta `markdown` (F11/F53) o `markdown_std`."""
    targets = profile.get("targets", {}) or {}
    return targets.get("markdown") or targets.get("markdown_std") or {}


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
    """Resuelve wikilinks cruzados y reporta los no resueltos.

    Devuelve lista de (source_note_id, target_note_id) para generar la
    sección "## Referenciado por" en cada destino.
    """
    edges: List[Tuple[str, str]] = []
    unresolved: List[str] = []
    for ir in ir_list:
        src = ir.get("note_id", "")
        for tgt, kind in collect_link_targets(ir):
            if kind == "note":
                if tgt in note_ids:
                    edges.append((src, tgt))
                else:
                    unresolved.append(tgt)
                    degradations.append({
                        "id": f"deg-{_sha256_hex((tgt + 'unr').encode())[:12]}",
                        "node_path": f"{src}/link",
                        "node_type": "link-note",
                        "capability": "link-note",
                        "alternative": (
                            f"link [text](<target>.md) o URL absoluta con "
                            f"--base-url; target no resuelto en el workdir actual"
                        ),
                        "evidence": f"rg '\\[{2}{tgt}\\]{2}|\\({tgt}\\.md\\)' render/markdown/<id>.md exit 0",
                        "content_intact": True,
                    })
            elif kind == "term":
                if tgt not in term_ids:
                    unresolved.append(f"term:{tgt}")
                    degradations.append({
                        "id": f"deg-{_sha256_hex((tgt + 'unrterm').encode())[:12]}",
                        "node_path": f"{src}/term",
                        "node_type": "term-ref",
                        "capability": "term-ref",
                        "alternative": (
                            f"link al término [[term:{tgt}]] (literal); glosario no contiene '{tgt}'"
                        ),
                        "evidence": f"rg '\\[{2}term:{tgt}\\]{2}' render/markdown/<id>.md exit 0",
                        "content_intact": True,
                    })
    return edges


def build_backlinks_section(note_id: str,
                            edges: List[Tuple[str, str]],
                            base_url: str = "") -> Optional[str]:
    """Genera la sección `## Referenciado por` para una nota.

    Devuelve None si no hay backlinks.
    """
    incoming = sorted({src for src, tgt in edges if tgt == note_id and src != note_id})
    if not incoming:
        return None
    lines = [BACKLINK_HEADING, ""]
    for src in incoming:
        if base_url:
            lines.append(f"- [{src}]({base_url.rstrip('/')}/{src}.md)")
        else:
            lines.append(f"- [{src}]({src}.md)")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Pre-render de diagramas (F68 opcional)
# ---------------------------------------------------------------------------


def _pre_render_diagram(text: str, out_path: Path) -> Optional[str]:
    f70 = Path(__file__).resolve().parent / "diagram_image.py"
    if not f70.exists():
        return None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".mmd",
                                         delete=False, encoding="utf-8") as f:
            f.write(text)
            in_path = Path(f.name)
        try:
            cmd = [sys.executable, str(f70),
                   "--input", str(in_path),
                   "--output", str(out_path),
                   "--format", "svg"]
            subprocess.run(cmd, capture_output=True, timeout=30, check=True)
            if out_path.exists():
                return str(out_path)
        finally:
            try:
                in_path.unlink()
            except OSError:
                pass
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None
    return None


# ---------------------------------------------------------------------------
# Emisión de nodos IR → Markdown GFM
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
    """Fila 5 §6 contract."""
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
            "Markdown pipe table con celdas vacías + bloque <details> con la "
            "matriz completa (fila 5 §6 contract); GitHub renderiza <details> "
            "como disclosure widget"
        ),
        "evidence": "rg '<details markdown' render/markdown/<id>.md exit 0",
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
        f"> ⚠️ **Estructura original con celdas combinadas "
        f"({n_rows} filas × {n_cols} cols)** — ver fuente §{section_path}"
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


def _emit_figure(node: Dict[str, Any], out_dir: Path, note_id: str
                 ) -> str:
    """Figura con ruta relativa (criterio 3)."""
    attrs = node.get("attrs", {}) or {}
    src = attrs.get("src", "") or ""
    alt = attrs.get("alt", "") or ""
    caption = attrs.get("caption", "") or ""

    if src.startswith(("http://", "https://")):
        url = src
    elif src.startswith("/"):
        url = src  # absoluto del repo
    else:
        # Local → ruta relativa al markdown de salida.
        # Por convención: assets en `render/markdown/assets/<note-id>/<src>`.
        url = f"assets/{note_id}/{src.lstrip('./')}"

    block = f"![{alt}]({url})"
    if caption:
        block += f"\n*{caption}*"
    return block


def _emit_diagram(node: Dict[str, Any], note_id: str, idx: int,
                  pre_render: bool, out_dir: Path,
                  degradations: List[Dict[str, Any]],
                  node_path: str) -> str:
    """Diagrama Mermaid: bloque ```mermaid + imagen de respaldo."""
    attrs = node.get("attrs", {}) or {}
    text = attrs.get("text", "") or ""
    alt = attrs.get("alt", "") or ""

    parts: List[str] = [f"```mermaid\n{text}\n```"]

    if pre_render:
        diag_dir = out_dir / "render" / "markdown" / "diagrams"
        img_path = diag_dir / f"{note_id}-{idx}.svg"
        rendered = _pre_render_diagram(text, img_path)
        if rendered:
            degradations.append({
                "id": f"deg-{_sha256_hex((node_path + 'pr').encode())[:12]}",
                "node_path": node_path,
                "node_type": "diagram",
                "capability": "diagram-mermaid-block",
                "alternative": (
                    f"bloque ```mermaid (GitHub nativo) + imagen pre-renderizada "
                    f"de respaldo ({img_path.name}); el bloque es la fuente de "
                    f"verdad en GitHub, la imagen es fallback offline"
                ),
                "evidence": "test -f render/markdown/diagrams/<note>-<idx>.svg exit 0",
                "content_intact": True,
            })
            parts.append("")
            parts.append(f"![{alt or 'diagram'}](diagrams/{img_path.name})")
            return "\n".join(parts)

    degradations.append({
        "id": f"deg-{_sha256_hex((node_path + 'pr').encode())[:12]}",
        "node_path": node_path,
        "node_type": "diagram",
        "capability": "diagram-mermaid-block",
        "alternative": (
            "bloque ```mermaid nativo (GitHub renderiza); sin imagen de respaldo "
            "porque F68 no está disponible o flag --pre-render-diagrams inactivo"
        ),
        "evidence": "rg '^```mermaid' render/markdown/<id>.md exit 0",
        "content_intact": True,
    })
    return parts[0]


def _emit_callout(node: Dict[str, Any],
                   degradations: List[Dict[str, Any]],
                   node_path: str) -> str:
    """Admonition → blockquote con emoji + CSS class (fila 12 §6)."""
    attrs = node.get("attrs", {}) or {}
    severity = str(attrs.get("severity", DEFAULT_SEVERITY) or DEFAULT_SEVERITY)
    title = str(attrs.get("title", "") or "")
    body = _emit_inline(node.get("children", []))
    semantic_token = attrs.get("semantic_token") or attrs.get("color_token")
    css_class = SEMANTIC_TOKENS.get(semantic_token or severity, severity)

    emoji = SEVERITY_TO_EMOJI.get(severity)
    if emoji is None:
        degradations.append({
            "id": f"deg-{_sha256_hex((node_path + 'sev').encode())[:12]}",
            "node_path": node_path,
            "node_type": "admonition",
            "capability": "callout",
            "alternative": (
                f"blockquote con emoji '{DEFAULT_EMOJI}' prefijo + CSS class "
                f"'callout-{DEFAULT_SEVERITY}' (severity='{severity}' no en "
                f"SEVERITY_TO_EMOJI; default aplicado)"
            ),
            "vs_notion_api": "notion_api emite callout nativo con icon+color",
            "evidence": "rg '^> ' render/markdown/<id>.md exit 0",
            "content_intact": True,
        })
        emoji = DEFAULT_EMOJI
        css_class = DEFAULT_SEVERITY
    else:
        degradations.append({
            "id": f"deg-{_sha256_hex((node_path + 'sev').encode())[:12]}",
            "node_path": node_path,
            "node_type": "admonition",
            "capability": "callout",
            "alternative": (
                f"blockquote con emoji '{emoji}' prefijo + título + CSS class "
                f"'callout-{css_class}' (fila 12 §6 contract; GitHub no renderiza "
                f"callouts nativos; la CSS class funciona con theme custom)"
            ),
            "vs_notion_api": "notion_api emite callout nativo con icon+color",
            "evidence": f"rg '^> .*{emoji}' render/markdown/<id>.md exit 0",
            "content_intact": True,
        })
        if severity == "warning" or severity == "danger":
            degradations.append({
                "id": f"deg-{_sha256_hex((node_path + 'color').encode())[:12]}",
                "node_path": node_path,
                "node_type": "admonition",
                "capability": "semantic-color",
                "alternative": (
                    f"emoji semántico '{emoji}' prefijo + CSS class "
                    f"'semantic-{css_class}' inline (fila 20 §6 contract; "
                    f"GFM no soporta color directo)"
                ),
                "evidence": f"rg '^> .*{emoji}' render/markdown/<id>.md exit 0",
                "content_intact": True,
            })

    title_line = f" {title}" if title else ""
    header = f"> [!{severity}]+ {emoji}{title_line}".rstrip() + " {.callout-" + css_class + "}"
    lines: List[str] = [header]
    for ln in body.split("\n"):
        lines.append(f"> {ln}" if ln else ">")
    return "\n".join(lines)


def _emit_collapsible(node: Dict[str, Any]) -> str:
    attrs = node.get("attrs", {}) or {}
    title = str(attrs.get("title", "Detalles") or "Detalles")
    children = node.get("children", [])
    body_parts: List[str] = []
    for child in children:
        rendered = _emit_node(child, note_id="", out_dir=Path())
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
    parts: List[str] = []
    for child in node.get("children", []):
        parts.append(_emit_node(child))
    return "\n\n".join(p for p in parts if p)


def _emit_divider(_node: Dict[str, Any]) -> str:
    return "---"


def _emit_property_block(node: Dict[str, Any]) -> str:
    """Property se aplana en frontmatter."""
    return ""


def _emit_query(node: Dict[str, Any]) -> str:
    """Tabla estática con la query verbatim (fila 16 §6 contract)."""
    attrs = node.get("attrs", {}) or {}
    query = str(attrs.get("query", "") or "")
    return (
        f"{QUERIES_HEADING}\n\n"
        f"> ℹ️ Esta consulta requiere un motor de queries (Dataview/Obsidian, "
        f"database views). Resultado estático de build-time:\n\n"
        f"| Query | Resultado |\n"
        f"|---|---|\n"
        f"| `{query}` | (no resuelto en build; ejecutar Dataview para datos en vivo) |"
    )


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
        text = attrs.get("text", "") or target
        # GitHub no soporta wikilinks nativamente; emitimos como
        # [text](<target>.md) (ruta relativa, criterio 3).
        return f"[{text}]({target}.md)"
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


def _collect_frontmatter_props(ir: Dict[str, Any]) -> Dict[str, str]:
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


def _emit_node(node: Dict[str, Any], note_id: str = "", idx: int = 0,
               degradations: Optional[List[Dict[str, Any]]] = None,
               out_dir: Optional[Path] = None,
               pre_render: bool = False,
               node_path: str = "") -> str:
    kind = node.get("node", "")
    if kind == "table":
        attrs = node.get("attrs", {}) or {}
        cap = node.get("capability", "")
        # Detectar tabla con celdas combinadas.
        is_merged = (
            cap == "table-merged-cells"
            or "matrix" in attrs
            or "cells_with_span" in attrs
            or "rowspan" in attrs
        )
        if is_merged:
            assert degradations is not None
            return _emit_table_merged(node, degradations, node_path)
        # Detectar tabla con query (consulta dinámica, fila 16 §6).
        if cap == "query" or "query" in attrs:
            return _emit_query({"attrs": attrs})
    if kind == "admonition":
        assert degradations is not None
        return _emit_callout(node, degradations, node_path)
    if kind == "diagram":
        assert degradations is not None and out_dir is not None
        return _emit_diagram(node, note_id, idx, pre_render, out_dir,
                             degradations, node_path)
    if kind == "figure" and out_dir is not None:
        return _emit_figure(node, out_dir, note_id)
    fn = {
        "section": _emit_section,
        "paragraph": _emit_paragraph,
        "list": _emit_list,
        "checklist": _emit_checklist,
        "table": _emit_table_simple,
        "code": _emit_code,
        "console": _emit_console,
        "equation": _emit_equation,
        "collapsible": _emit_collapsible,
        "quote": _emit_quote,
        "columns": _emit_columns,
        "divider": _emit_divider,
        "property-block": _emit_property_block,
        "query": _emit_query,
        "question": _emit_question,
        "step": _emit_step,
        "parameter-table": _emit_parameter_table,
    }.get(kind)
    if fn is None:
        return ""
    return fn(node)


# ---------------------------------------------------------------------------
# Emisión del artefacto Markdown
# ---------------------------------------------------------------------------


def emit_artifact(ir_obj: Dict[str, Any], ir_sha256: str,
                  source_hash: str, renderer_version: str,
                  out_dir: Path, degradations: List[Dict[str, Any]],
                  pre_render: bool, base_url: str,
                  edges: List[Tuple[str, str]],
                  generate_backlinks: bool,
                  generate_queries_table: bool,
                  ir_node_count_holder: List[int]) -> Path:
    note_id = str(ir_obj.get("note_id", "note-unknown"))
    title = ir_obj.get("title", "") or ""

    # Frontmatter.
    frontmatter_props = _collect_frontmatter_props(ir_obj)
    auto_props = {
        "schema_version": '"1.0.0"',
        "target": "markdown",
        "note_id": f'"{note_id}"',
        "source_hash": f'"{source_hash}"',
        "ir_sha256": f'"{ir_sha256}"',
        "rendered_at": f'"{_now_utc_iso()}"',
        "renderer_version": f'"{renderer_version}"',
    }
    if title:
        auto_props["title"] = f'"{title}"'

    all_props = {**auto_props, **{k: v for k, v in frontmatter_props.items()
                                  if k not in auto_props}}
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
    for path, node in ir_nodes:
        rendered = _emit_node(
            node, note_id=note_id, idx=len(body_parts),
            degradations=degradations, out_dir=out_dir,
            pre_render=pre_render, node_path=path,
        )
        if rendered:
            body_parts.append(rendered)

    # Sección de backlinks.
    if generate_backlinks:
        backlinks = build_backlinks_section(note_id, edges, base_url)
        if backlinks:
            body_parts.append(backlinks)

    body = "\n\n".join(body_parts) + "\n"

    target_dir = out_dir / "render" / "markdown"
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / f"{note_id}.md"
    _atomic_write_text(out_path, header + body)
    return out_path


# ---------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------


def build_report(source_hash: str, degradations: List[Dict[str, Any]],
                 ir_node_count: int, unresolved: List[str],
                 published: Dict[str, str], diagram_strategy: str
                 ) -> Tuple[Dict[str, Any], str]:
    content_loss = sum(1 for d in degradations if not d.get("content_intact", True))
    report = {
        "schema_version": "1.0.0",
        "target": "markdown",
        "source_hash": source_hash,
        "generated_at": _now_utc_iso(),
        "totals": {
            "ir_nodes": ir_node_count,
            "degradations": len(degradations),
            "content_loss": content_loss,
        },
        "degradations": degradations,
        "unresolved_targets": sorted(set(unresolved)),
        "published_pages": published,
        "diagram_strategy": diagram_strategy,
        "cross_target_diff": {
            "vs_obsidian": "sin callouts nativos (usa blockquote + CSS class); sin Mermaid Live Preview (usa ```mermaid + MathJax server-side); propiedades en frontmatter",
            "vs_appflowy": "sin callout [!type] nativos; usa blockquote con emoji + CSS class",
            "vs_html_pdf": "GFM estándar en lugar de HTML; sin sintaxis HTML nativa"
        }
    }
    md_lines = [
        "# Reporte de degradación — Markdown estándar",
        "",
        f"- **schema_version:** {report['schema_version']}",
        f"- **target:** markdown",
        f"- **source_hash:** `{source_hash}`",
        f"- **generated_at:** {report['generated_at']}",
        f"- **diagram_strategy:** {diagram_strategy}",
        "",
        "## Resumen",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        f"| Nodos IR totales | {ir_node_count} |",
        f"| Degradaciones | {len(degradations)} |",
        f"| Pérdida de contenido | {content_loss} |",
        f"| Targets sin resolver | {len(set(unresolved))} |",
        f"| Notas publicadas | {len(published)} |",
        "",
        "## Diferencias vs otros destinos",
        "",
        f"- **vs obsidian (F54):** {report['cross_target_diff']['vs_obsidian']}",
        f"- **vs appflowy (F57):** {report['cross_target_diff']['vs_appflowy']}",
        f"- **vs html_pdf (F59):** {report['cross_target_diff']['vs_html_pdf']}",
        "",
    ]
    if degradations:
        md_lines.append("## Degradaciones")
        md_lines.append("")
        for i, d in enumerate(degradations, start=1):
            md_lines.append(f"### markdown / {d.get('capability', '?')}")
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
    if unresolved:
        md_lines.append("## Targets sin resolver")
        md_lines.append("")
        for tgt in sorted(set(unresolved)):
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
        prog="markdown.py",
        description="Renderer Markdown estándar (GFM, GitHub-compatible) (L4) para el Note IR. F58.",
    )
    parser.add_argument("--ir", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--matrix", type=Path,
                        default=(Path(__file__).resolve().parents[2] /
                                 "references" / "08-render" / "capability-matrix.md"))
    parser.add_argument("--source-hash", type=str, default=None)
    parser.add_argument("--renderer-version", type=str, default="0.1.0")
    parser.add_argument("--base-url", type=str, default="",
                        help="Prefijo URL absoluto para wikilinks resueltos (e.g. "
                             "'https://github.com/user/repo/blob/main/').")
    parser.add_argument("--generate-backlinks", dest="generate_backlinks",
                        action="store_true", default=True,
                        help="Inserta sección '## Referenciado por' (fila 7 §6).")
    parser.add_argument("--no-generate-backlinks", dest="generate_backlinks",
                        action="store_false",
                        help="No insertar backlinks.")
    parser.add_argument("--generate-queries-table", dest="generate_queries_table",
                        action="store_true", default=True,
                        help="Inserta tabla '## Consultas habituales' para queries (fila 16 §6).")
    parser.add_argument("--no-generate-queries-table", dest="generate_queries_table",
                        action="store_false",
                        help="No insertar tabla de queries.")
    parser.add_argument("--pre-render-diagrams", action="store_true",
                        help="Pre-renderiza Mermaid a SVG vía F68 si está disponible.")

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
    note_ids: Set[str] = set()
    term_ids: Set[str] = set()
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

    # Pase 2: resolver enlaces cruzados (criterio 3: rutas relativas).
    edges = resolve_links(ir_objs, note_ids, term_ids, degradations)

    # Estrategia de diagramas.
    f70 = Path(__file__).resolve().parent / "diagram_image.py"
    diagram_strategy = (
        "mermaid + image-fallback (F68 active)" if args.pre_render_diagrams and f70.exists()
        else "mermaid-only (no pre-render)"
    )

    # Pase 3: renderizar.
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
                pre_render=args.pre_render_diagrams,
                base_url=args.base_url,
                edges=edges,
                generate_backlinks=args.generate_backlinks,
                generate_queries_table=args.generate_queries_table,
                ir_node_count_holder=ir_node_count_holder,
            )
            rendered_paths[ir_obj.get("note_id", "?")] = str(out_path)
        except OSError as e:
            print(f"ERROR: no se pudo escribir {ir_obj.get('note_id', '?')}: {e}",
                  file=sys.stderr)
            return EXIT_FATAL

    # Pase 4: reporte.
    unresolved = list({d.get("alternative", "").split("[[")[1].split("]]")[0]
                       for d in degradations
                       if "no resuelto" in d.get("alternative", "")
                       and "[[" in d.get("alternative", "")})
    report, report_md = build_report(
        source_hash=source_hash,
        degradations=degradations,
        ir_node_count=ir_node_count_holder[0],
        unresolved=unresolved,
        published=rendered_paths,
        diagram_strategy=diagram_strategy,
    )
    reports_dir = args.out_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(reports_dir / "render-degradation.json", report)
    _atomic_write_text(reports_dir / "render-degradation.md", report_md)

    print(f"OK — {len(ir_objs)} nota(s) renderizada(s) en "
          f"{args.out_dir / 'render' / 'markdown'}")
    print(f"     reporte: {reports_dir / 'render-degradation.json'}")
    print(f"     diagram_strategy: {diagram_strategy}")
    if unresolved:
        print(f"WARN — {len(unresolved)} target(s) sin resolver (ver reporte).")
        return EXIT_WARN
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
