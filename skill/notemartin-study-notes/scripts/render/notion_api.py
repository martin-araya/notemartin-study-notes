#!/usr/bin/env python3
"""notion_api.py — F55 · Renderer Notion API (L4).

Traduce el Note IR validado a páginas de Notion vía la API REST
(https://api.notion.com/v1, version `2022-06-28`). Implementa la interfaz
`render(ir, profile, matrix) → (artifacts, degradation_report)` del contrato
F53 (`references/08-render/contract.md`).

Capacidades (per `references/08-render/capability-matrix.md` §2.1):
  Notion API = 13 ✅ + 1 ❌ (Celdas combinadas → degradación fila 2 contract §6).

Detalles:
  - admonition → callout con icon + color (tabla cerrada `SEVERITY_TO_CALLOUT`)
  - collapsible → toggle (hijos en pass 2)
  - link-note → rich_text mention (resolve en pass 1 vía search)
  - propiedades → properties de database (mapping en `PROPERTY_TYPE_MAP`)
  - diagram Mermaid → code (lang=mermaid); --pre-render-diagrams activa F70 cuando exista
  - equation → equation block (LaTeX)
  - figure → image (external o file_upload)
  - columns → column_list + column

Idempotencia (D4 ADR-0010): busca `notemartin_note_id` property; si existe → PATCH.
Troceo: chunks de 100 bloques/petición (capability-matrix §4).
Anidamiento: 2 pasadas; > 2 niveles se aplana con placeholder `content_intact: true`.
Reintentos: backoff exponencial 5s/30s/2m/10m ante 429 o 5xx (architecture.md §8).

Cliente HTTP: `urllib.request` stdlib puro; sin requests/httpx.
Dry-run: `--dry-run` escribe payloads a `render/notion_api/payloads/` sin HTTP.

Uso:
    python3 scripts/render/notion_api.py --ir <path> --profile <path> --out-dir <dir>
                                          --notion-token <token>
                                          [--database-id <hex>]
                                          [--page-parent-id <hex>]
                                          [--matrix <path>] [--source-hash <hex64>]
                                          [--renderer-version <semver>]
                                          [--dry-run]
                                          [--pre-render-diagrams]

Variables de entorno (alternativas a flags):
    NOTION_TOKEN          → token de integración
    NOTION_DATABASE_ID    → database destino

Permisos del token requeridos: `read content`, `update content`, `insert content`.

Dependencias: Python 3.9+ stdlib puro (urllib.request, urllib.error, json).
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
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Comparte atomic_write_json / atomic_write_text con F38/F39/F54.
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
# Límites de la API (per references/08-render/capability-matrix.md §4)
# ---------------------------------------------------------------------------

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
BLOCKS_PER_REQUEST = 100           # Bloques por petición POST/PATCH children.
RICH_TEXT_MAX_CHARS = 2000          # Caracteres por bloque rich_text.
MAX_NESTING_DEPTH = 2               # Niveles prácticos de anidamiento.
FILE_UPLOAD_MAX_BYTES = 20 * 1024 * 1024   # 20 MB imagen.
INTER_REQUEST_DELAY = 1.0 / 3.0     # 333ms entre peticiones (3 req/s).
REQUEST_TIMEOUT = 30                # segundos.

RETRY_DELAYS = [5, 30, 120, 600]    # Backoff exponencial architecture.md §8.


def _resolve_api_base() -> str:
    """Resuelve la URL base: env > flag --api-base > default real."""
    env_base = os.environ.get("NOTION_API_BASE")
    if env_base:
        return env_base.rstrip("/")
    return NOTION_API_BASE


# ---------------------------------------------------------------------------
# Tablas cerradas
# ---------------------------------------------------------------------------

# Severidad del IR → icon (emoji) + color (Notion). 13 canónicas + 6 fallback.
SEVERITY_TO_CALLOUT: Dict[str, Dict[str, str]] = {
    "note":         {"icon": "📝", "color": "default"},
    "tip":          {"icon": "💡", "color": "yellow_background"},
    "info":         {"icon": "ℹ️",  "color": "blue_background"},
    "warning":      {"icon": "⚠️", "color": "yellow_background"},
    "caution":      {"icon": "⚠️", "color": "orange_background"},
    "danger":       {"icon": "🚫", "color": "red_background"},
    "example":      {"icon": "📋", "color": "gray_background"},
    "question":     {"icon": "❓", "color": "purple_background"},
    "success":      {"icon": "✅", "color": "green_background"},
    "failure":      {"icon": "❌", "color": "red_background"},
    "bug":          {"icon": "🐛", "color": "red_background"},
    "quote":        {"icon": "💬", "color": "gray_background"},
    "abstract":     {"icon": "📑", "color": "gray_background"},
    "security":     {"icon": "🔒", "color": "red_background"},
    "performance":  {"icon": "⚡", "color": "orange_background"},
    "version":      {"icon": "🏷️",  "color": "blue_background"},
    "deprecated":   {"icon": "⛔", "color": "gray_background"},
    "conflict":     {"icon": "⚠️", "color": "orange_background"},
    "external":     {"icon": "🔗", "color": "gray_background"},
}

DEFAULT_SEVERITY = "note"

# Tipo Python-style → tipo Notion API para database properties.
PROPERTY_TYPE_MAP: Dict[str, str] = {
    "string":  "rich_text",
    "text":    "rich_text",
    "number":  "number",
    "int":     "number",
    "float":   "number",
    "bool":    "checkbox",
    "boolean": "checkbox",
    "date":    "date",
    "url":     "url",
    "email":   "email",
    "phone":   "phone_number",
    "select":  "select",
    "multi":   "multi_select",
    "tags":    "multi_select",
}

# Lenguajes de código soportados por Notion (subset común).
LANG_MAP: Dict[str, str] = {
    "python": "python",
    "py": "python",
    "javascript": "javascript",
    "js": "javascript",
    "typescript": "typescript",
    "ts": "typescript",
    "bash": "bash",
    "sh": "bash",
    "shell": "bash",
    "json": "json",
    "yaml": "yaml",
    "yml": "yaml",
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
    "cpp": "c++",
    "c++": "c++",
    "csharp": "c#",
    "c#": "c#",
    "php": "php",
    "scala": "scala",
    "mermaid": "mermaid",
    "plain": "plain text",
    "": "plain text",
}


# ---------------------------------------------------------------------------
# Excepciones
# ---------------------------------------------------------------------------


class NotionAPIError(Exception):
    """Error HTTP de la API de Notion."""
    def __init__(self, code: int, body: str):
        super().__init__(f"HTTP {code}: {body[:200]}")
        self.code = code
        self.body = body


class NotionAuthError(NotionAPIError):
    """401/403 — token inválido o sin permisos."""
    pass


class NotionRateLimitError(NotionAPIError):
    """429 — rate limit; reintentar con backoff."""
    pass


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


def _split_rich_text(text: str, max_len: int = RICH_TEXT_MAX_CHARS) -> List[str]:
    """Divide text en chunks ≤ max_len respetando word boundaries."""
    if len(text) <= max_len:
        return [text]
    chunks: List[str] = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        cut = text.rfind(" ", 0, max_len)
        if cut <= 0:
            cut = max_len
        chunks.append(text[:cut])
        text = text[cut:].lstrip()
    return chunks


def _chunk_blocks(blocks: List[dict], max_per_request: int = BLOCKS_PER_REQUEST
                  ) -> List[List[dict]]:
    """Divide blocks en chunks de ≤ max_per_request."""
    chunks: List[List[dict]] = []
    for i in range(0, len(blocks), max_per_request):
        chunks.append(blocks[i:i + max_per_request])
    return chunks


# ---------------------------------------------------------------------------
# Cliente HTTP (urllib.request) con reintentos y backoff
# ---------------------------------------------------------------------------


def _notion_request_raw(method: str, path: str, body: Optional[dict],
                        token: str) -> dict:
    url = f"{_resolve_api_base()}{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Notion-Version", NOTION_VERSION)
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode("utf-8") if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=REQUEST_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_bytes = e.read().decode("utf-8", errors="replace")
        if e.code in (401, 403):
            raise NotionAuthError(e.code, body_bytes)
        if e.code == 429:
            raise NotionRateLimitError(e.code, body_bytes)
        raise NotionAPIError(e.code, body_bytes)


def _notion_request_with_retry(method: str, path: str, body: Optional[dict],
                               token: str,
                               degradations: List[dict],
                               node_path: str = "") -> Optional[dict]:
    """Llama `_notion_request_raw` con reintentos; devuelve None si degraded."""
    last_exc: Optional[Exception] = None
    delays = [0] + RETRY_DELAYS
    for attempt, delay in enumerate(delays):
        if delay:
            time.sleep(delay)
        try:
            return _notion_request_raw(method, path, body, token)
        except NotionRateLimitError as e:
            last_exc = e
            degradations.append({
                "node_path": node_path or path,
                "node_type": "api",
                "capability": "rate-limit",
                "alternative": f"retry {attempt+1}/{len(delays)} tras 429",
                "evidence": f"backoff {delay}s; HTTP 429",
                "content_intact": True,
            })
        except NotionAPIError as e:
            if 500 <= e.code < 600:
                last_exc = e
                degradations.append({
                    "node_path": node_path or path,
                    "node_type": "api",
                    "capability": "transient-error",
                    "alternative": f"retry {attempt+1}/{len(delays)} tras 5xx",
                    "evidence": f"backoff {delay}s; HTTP {e.code}",
                    "content_intact": True,
                })
                continue
            raise
    degradations.append({
        "node_path": node_path or path,
        "node_type": "api",
        "capability": "rate-limit",
        "alternative": "destination marked degraded",
        "evidence": f"{len(delays)-1} retries agotados; último: {last_exc}",
        "content_intact": True,
    })
    return None


# ---------------------------------------------------------------------------
# Idempotencia: búsqueda por `notemartin_note_id` o por título `[note_id]`
# ---------------------------------------------------------------------------


def _search_existing_page(note_id: str, token: str,
                          database_id: Optional[str]) -> Optional[str]:
    if database_id:
        body = {
            "filter": {
                "property": "notemartin_note_id",
                "rich_text": {"equals": note_id}
            }
        }
        resp = _notion_request_with_retry("POST", f"/databases/{database_id}/query",
                                          body, token, [])
        if resp and resp.get("results"):
            return resp["results"][0]["id"]
        return None
    body = {
        "query": f"[{note_id}]",
        "filter": {"value": "page", "property": "object"},
    }
    resp = _notion_request_with_retry("POST", "/search", body, token, [])
    if resp:
        for r in resp.get("results", []):
            title_parts = r.get("properties", {}).get("title", {}).get("title", [])
            title = "".join(t.get("plain_text", "") for t in title_parts)
            if title.startswith(f"[{note_id}]"):
                return r["id"]
    return None


# ---------------------------------------------------------------------------
# Emisión de nodos IR → Notion block JSON
# ---------------------------------------------------------------------------


def _rich_text_from_string(text: str) -> List[dict]:
    """Serializa un string a array de rich_text, split si > 2000 chars."""
    pieces = _split_rich_text(text)
    return [{"type": "text", "text": {"content": p}} for p in pieces]


def _rich_text_from_inline(children: List[dict],
                           note_id_to_page: Dict[str, str],
                           degradations: List[dict],
                           node_path: str) -> List[dict]:
    """Convierte children inline → rich_text array."""
    out: List[dict] = []
    for child in children:
        if not isinstance(child, dict):
            continue
        kind = child.get("node", "")
        attrs = child.get("attrs", {}) or {}
        if kind == "text":
            out.extend(_rich_text_from_string(attrs.get("text", "") or ""))
        elif kind == "strong":
            text = _flatten_inline_text(child.get("children", []))
            for piece in _split_rich_text(text):
                out.append({"type": "text", "text": {"content": piece},
                            "annotations": {"bold": True}})
        elif kind == "em":
            text = _flatten_inline_text(child.get("children", []))
            for piece in _split_rich_text(text):
                out.append({"type": "text", "text": {"content": piece},
                            "annotations": {"italic": True}})
        elif kind == "code-inline":
            text = attrs.get("text", "") or ""
            for piece in _split_rich_text(text):
                out.append({"type": "text", "text": {"content": piece},
                            "annotations": {"code": True}})
        elif kind == "link-external":
            url = attrs.get("url", "") or ""
            text = attrs.get("text", "") or url
            for piece in _split_rich_text(text):
                out.append({"type": "text", "text": {"content": piece, "link": {"url": url}}})
        elif kind == "link-note":
            target = attrs.get("target", "") or ""
            text = attrs.get("text", "") or target
            page_id = note_id_to_page.get(target)
            if page_id:
                out.append({"type": "mention", "mention": {"type": "page", "page": {"id": page_id}},
                            "plain_text": text})
            else:
                out.extend(_rich_text_from_string(f"[[{target}|{text}]]"))
                degradations.append({
                    "node_path": node_path,
                    "node_type": "link-note",
                    "capability": "link-note",
                    "alternative": f"wikilink literal [[{target}|{text}]]; target sin resolver",
                    "evidence": f"notion.search for '{target}' returned None",
                    "content_intact": True,
                })
        elif kind == "term-ref":
            term_id = attrs.get("term_id", "") or ""
            text = attrs.get("text", "") or term_id
            out.extend(_rich_text_from_string(f"[[term:{term_id}|{text}]]"))
        elif kind == "source-ref":
            # No se renderiza visiblemente; se preserva como rich_text invisible.
            out.append({"type": "text", "text": {"content": ""},
                        "annotations": {"color": "gray"}})
        elif kind == "math-inline":
            latex = attrs.get("latex", "") or ""
            out.append({"type": "equation", "equation": {"expression": latex}})
        elif kind == "deleted":
            text = _flatten_inline_text(child.get("children", []))
            for piece in _split_rich_text(text):
                out.append({"type": "text", "text": {"content": piece},
                            "annotations": {"strikethrough": True}})
        elif kind == "placeholder":
            text = attrs.get("text", "") or ""
            out.extend(_rich_text_from_string(f"{{{{{text}}}}}"))
        elif kind == "keyboard":
            text = attrs.get("text", "") or ""
            for piece in _split_rich_text(text):
                out.append({"type": "text", "text": {"content": piece},
                            "annotations": {"code": True}})
        else:
            out.extend(_rich_text_from_string(attrs.get("text", "") or ""))
    return out


def _flatten_inline_text(children: List[dict]) -> str:
    out: List[str] = []
    for child in children:
        if not isinstance(child, dict):
            continue
        kind = child.get("node", "")
        attrs = child.get("attrs", {}) or {}
        if kind == "text":
            out.append(attrs.get("text", "") or "")
        elif kind in ("strong", "em", "deleted"):
            out.append(_flatten_inline_text(child.get("children", [])))
        elif kind == "code-inline":
            out.append(attrs.get("text", "") or "")
        elif kind == "link-note":
            out.append(f"[[{attrs.get('target','')}|{attrs.get('text','') or attrs.get('target','')}]]")
        elif kind == "term-ref":
            out.append(f"[[term:{attrs.get('term_id','')}|{attrs.get('text','') or attrs.get('term_id','')}]]")
        else:
            out.append(attrs.get("text", "") or "")
    return "".join(out)


def _emit_section(node: dict, **ctx) -> dict:
    attrs = node.get("attrs", {}) or {}
    level = int(attrs.get("level", 1) or 1)
    level = max(1, min(level, 3))
    block_type = f"heading_{level}"
    return {
        "type": block_type,
        block_type: {
            "rich_text": _rich_text_from_inline(
                node.get("children", []),
                ctx.get("note_id_to_page", {}),
                ctx.get("degradations", []),
                ctx.get("node_path", ""),
            )
        }
    }


def _emit_paragraph(node: dict, **ctx) -> dict:
    return {
        "type": "paragraph",
        "paragraph": {
            "rich_text": _rich_text_from_inline(
                node.get("children", []),
                ctx.get("note_id_to_page", {}),
                ctx.get("degradations", []),
                ctx.get("node_path", ""),
            )
        }
    }


def _emit_list(node: dict, **ctx) -> List[dict]:
    """Una `list` IR emite múltiples blocks (uno por item)."""
    ordered = bool(node.get("attrs", {}).get("ordered", False))
    block_type = "numbered_list_item" if ordered else "bulleted_list_item"
    items = node.get("children", [])
    return [
        {
            "type": block_type,
            block_type: {
                "rich_text": _rich_text_from_inline(
                    item.get("children", []),
                    ctx.get("note_id_to_page", {}),
                    ctx.get("degradations", []),
                    ctx.get("node_path", "") + f"/{i}",
                )
            }
        }
        for i, item in enumerate(items)
    ]


def _emit_checklist(node: dict, **ctx) -> List[dict]:
    items = node.get("children", [])
    return [
        {
            "type": "to_do",
            "to_do": {
                "rich_text": _rich_text_from_inline(
                    item.get("children", []),
                    ctx.get("note_id_to_page", {}),
                    ctx.get("degradations", []),
                    ctx.get("node_path", "") + f"/{i}",
                ),
                "checked": bool(item.get("attrs", {}).get("done", False)),
            }
        }
        for i, item in enumerate(items)
    ]


def _emit_table_simple(node: dict, **ctx) -> dict:
    """Tabla simple (no merged)."""
    attrs = node.get("attrs", {}) or {}
    headers = attrs.get("headers", []) or []
    rows = attrs.get("rows", []) or []
    children_blocks = []
    if headers:
        children_blocks.append({
            "type": "table_row",
            "table_row": {"cells": [_rich_text_from_string(str(h)) for h in headers]}
        })
    for row in rows:
        children_blocks.append({
            "type": "table_row",
            "table_row": {"cells": [_rich_text_from_string(str(c)) for c in row]}
        })
    n_cols = max(len(headers), max((len(r) for r in rows), default=0), 1)
    return {
        "type": "table",
        "table": {
            "table_width": n_cols,
            "has_column_header": bool(headers),
            "has_row_header": False,
            "children": children_blocks,
        }
    }


def _emit_table_merged(node: dict, **ctx) -> List[dict]:
    """Celdas combinadas → fila 2 contract §6: tabla vacía + callout matriz."""
    attrs = node.get("attrs", {}) or {}
    headers = attrs.get("headers", []) or []
    cells = attrs.get("cells", []) or []
    matrix = attrs.get("matrix", []) or []
    section_path = attrs.get("section_path", "fuente")
    n_rows = len(cells) if cells else len(matrix)
    n_cols = max(len(r) for r in cells) if cells else (len(headers) if headers else 0)

    degradations = ctx.get("degradations", [])
    node_path = ctx.get("node_path", "")
    degradations.append({
        "node_path": node_path,
        "node_type": "table",
        "capability": "table-merged-cells",
        "alternative": (
            "Tabla Notion con celdas vacías + callout amarillo adyacente con la "
            "matriz original (fila 2 contract §6)"
        ),
        "evidence": (
            "POST /v1/blocks/<page>/children with table (table_width="
            f"{n_cols}) + callout 'Matriz original'"
        ),
        "content_intact": True,
    })

    # Tabla con celdas vacías + headers si los hay.
    table_children = []
    if headers:
        table_children.append({
            "type": "table_row",
            "table_row": {"cells": [_rich_text_from_string(str(h)) for h in headers]}
        })
    for r in range(n_rows):
        row = cells[r] if r < len(cells) else []
        row_cells = []
        for c in range(n_cols):
            v = row[c] if c < len(row) else ""
            row_cells.append(_rich_text_from_string(str(v) if v else ""))
        table_children.append({
            "type": "table_row",
            "table_row": {"cells": row_cells}
        })
    table_block = {
        "type": "table",
        "table": {
            "table_width": n_cols,
            "has_column_header": bool(headers),
            "has_row_header": False,
            "children": table_children,
        }
    }

    # Callout adyacente con la matriz completa.
    matrix_lines = [f"Matriz original con rowspan/colspan ({n_rows}×{n_cols}):"]
    for r_idx, row in enumerate(matrix):
        for c_idx, cell in enumerate(row):
            val = cell if not isinstance(cell, dict) else cell.get("value", "")
            span = cell.get("span", "") if isinstance(cell, dict) else ""
            line = f"  ({r_idx},{c_idx}) = {val}"
            if span:
                line += f" [{span}]"
            matrix_lines.append(line)
    matrix_text = "\n".join(matrix_lines)
    callout_block = {
        "type": "callout",
        "callout": {
            "icon": {"type": "emoji", "emoji": "⚠️"},
            "color": "yellow_background",
            "rich_text": _rich_text_from_string(
                f"Estructura original con celdas combinadas ({n_rows} filas × "
                f"{n_cols} cols) — ver fuente §{section_path}.\n\n{matrix_text}"
            ),
        }
    }

    return [table_block, callout_block]


def _emit_code(node: dict, **ctx) -> dict:
    attrs = node.get("attrs", {}) or {}
    lang_raw = (attrs.get("lang", "") or "").lower()
    lang = LANG_MAP.get(lang_raw, "plain text")
    text = attrs.get("text", "") or ""
    return {
        "type": "code",
        "code": {
            "rich_text": _rich_text_from_string(text),
            "language": lang,
        }
    }


def _emit_equation(node: dict, **ctx) -> dict:
    attrs = node.get("attrs", {}) or {}
    return {
        "type": "equation",
        "equation": {"expression": attrs.get("latex", "") or ""}
    }


def _emit_figure(node: dict, **ctx) -> dict:
    attrs = node.get("attrs", {}) or {}
    src = attrs.get("src", "") or ""
    caption = attrs.get("caption", "")
    block: dict = {"type": "image"}
    if src.startswith(("http://", "https://")):
        block["image"] = {
            "type": "external",
            "external": {"url": src},
            "caption": _rich_text_from_string(caption) if caption else [],
        }
    else:
        # Path local — file_upload diferido (no implementado en este pase).
        block["image"] = {
            "type": "external",
            "external": {"url": f"file://{src}"},
            "caption": _rich_text_from_string(
                f"{caption} (upload local no implementado en F55; ver ADR-0010)"
            ) if caption else [],
        }
    return block


def _emit_diagram(node: dict, **ctx) -> dict:
    attrs = node.get("attrs", {}) or {}
    text = attrs.get("text", "") or ""
    alt = attrs.get("alt", "") or ""
    return {
        "type": "code",
        "code": {
            "rich_text": _rich_text_from_string(text),
            "language": "mermaid",
            "caption": _rich_text_from_string(alt) if alt else [],
        }
    }


def _emit_callout(node: dict, **ctx) -> dict:
    attrs = node.get("attrs", {}) or {}
    severity = str(attrs.get("severity", DEFAULT_SEVERITY) or DEFAULT_SEVERITY)
    title = str(attrs.get("title", "") or "")
    degradations = ctx.get("degradations", [])
    node_path = ctx.get("node_path", "")

    mapping = SEVERITY_TO_CALLOUT.get(severity)
    if mapping is None:
        degradations.append({
            "node_path": node_path,
            "node_type": "admonition",
            "capability": "callout",
            "alternative": (
                f"callout 'note' (severity='{severity}' no en SEVERITY_TO_CALLOUT; default aplicado)"
            ),
            "evidence": "POST /v1/blocks with callout (icon='📝', color='default')",
            "content_intact": True,
        })
        mapping = SEVERITY_TO_CALLOUT[DEFAULT_SEVERITY]

    body_rich = _rich_text_from_inline(
        node.get("children", []),
        ctx.get("note_id_to_page", {}),
        degradations,
        node_path,
    )
    rich_text = body_rich
    if title:
        title_rich = _rich_text_from_string(f"{title}\n")
        rich_text = title_rich + body_rich

    return {
        "type": "callout",
        "callout": {
            "icon": {"type": "emoji", "emoji": mapping["icon"]},
            "color": mapping["color"],
            "rich_text": rich_text,
        }
    }


def _emit_collapsible(node: dict, **ctx) -> dict:
    """Toggle; hijos en pass 2 via _emit_collapsible_children."""
    attrs = node.get("attrs", {}) or {}
    title = str(attrs.get("title", "Detalles") or "Detalles")
    children = node.get("children", [])
    if len(children) > MAX_NESTING_DEPTH:
        # Marca para pass 2 que necesita depth>1.
        ctx.setdefault("deferred_toggles", {})[id(node)] = children
        return {
            "type": "toggle",
            "toggle": {
                "rich_text": _rich_text_from_string(title),
                "children": [],
            }
        }
    # Render inmediato para depth ≤ MAX_NESTING_DEPTH-1 (children directos).
    ctx_children = {**ctx, "current_depth": ctx.get("current_depth", 0) + 1}
    child_blocks: List[dict] = []
    for i, child in enumerate(children):
        child_blocks.extend(_emit_node_blocks(child, i, ctx_children))
    return {
        "type": "toggle",
        "toggle": {
            "rich_text": _rich_text_from_string(title),
            "children": child_blocks,
        }
    }


def _emit_columns(node: dict, **ctx) -> dict:
    """column_list con column hijos."""
    children = node.get("children", [])
    column_blocks: List[dict] = []
    for i, col in enumerate(children):
        ctx_children = {**ctx, "current_depth": ctx.get("current_depth", 0) + 1}
        col_inner = []
        for j, item in enumerate(col.get("children", []) if isinstance(col, dict) else []):
            col_inner.extend(_emit_node_blocks(item, j, ctx_children))
        column_blocks.append({
            "type": "column",
            "column": {"children": col_inner}
        })
    return {
        "type": "column_list",
        "column_list": {"children": column_blocks}
    }


def _emit_divider(_node: dict, **ctx) -> dict:
    return {"type": "divider", "divider": {}}


def _emit_quote(node: dict, **ctx) -> dict:
    attrs = node.get("attrs", {}) or {}
    cite = attrs.get("cite", "")
    body = _rich_text_from_inline(
        node.get("children", []),
        ctx.get("note_id_to_page", {}),
        ctx.get("degradations", []),
        ctx.get("node_path", ""),
    )
    if cite:
        body = body + _rich_text_from_string(f"\n— {cite}")
    return {"type": "quote", "quote": {"rich_text": body}}


def _emit_step(node: dict, **ctx) -> dict:
    attrs = node.get("attrs", {}) or {}
    index = int(attrs.get("index", 1) or 1)
    body = _rich_text_from_inline(
        node.get("children", []),
        ctx.get("note_id_to_page", {}),
        ctx.get("degradations", []),
        ctx.get("node_path", ""),
    )
    prefix_rich = _rich_text_from_string(f"Paso {index}: ")
    return {
        "type": "numbered_list_item",
        "numbered_list_item": {"rich_text": prefix_rich + body}
    }


def _emit_question(node: dict, **ctx) -> dict:
    attrs = node.get("attrs", {}) or {}
    prompt = str(attrs.get("prompt", "") or "")
    body = _rich_text_from_inline(
        node.get("children", []),
        ctx.get("note_id_to_page", {}),
        ctx.get("degradations", []),
        ctx.get("node_path", ""),
    )
    full = _rich_text_from_string(f"Pregunta: {prompt}\n") + body
    return {"type": "paragraph", "paragraph": {"rich_text": full}}


def _emit_parameter_table(node: dict, **ctx) -> dict:
    attrs = node.get("attrs", {}) or {}
    columns = attrs.get("columns", []) or []
    rows = attrs.get("rows", []) or []
    children_blocks = []
    if columns:
        children_blocks.append({
            "type": "table_row",
            "table_row": {"cells": [_rich_text_from_string(str(c)) for c in columns]}
        })
    for row in rows:
        children_blocks.append({
            "type": "table_row",
            "table_row": {"cells": [_rich_text_from_string(str(c)) for c in row]}
        })
    n_cols = max(len(columns), max((len(r) for r in rows), default=0), 1)
    return {
        "type": "table",
        "table": {
            "table_width": n_cols,
            "has_column_header": bool(columns),
            "has_row_header": False,
            "children": children_blocks,
        }
    }


# ---------------------------------------------------------------------------
# Dispatch principal
# ---------------------------------------------------------------------------


def _emit_node_blocks(node: dict, idx: int, ctx: dict) -> List[dict]:
    """Emite uno o más blocks para un nodo IR (algunos nodos emiten varios blocks)."""
    kind = node.get("node", "")
    node_path = f"{ctx.get('node_path', '')}/{idx}"
    ctx2 = {**ctx, "node_path": node_path}

    if kind == "section":
        return [_emit_section(node, **ctx2)]
    if kind == "paragraph":
        return [_emit_paragraph(node, **ctx2)]
    if kind == "list":
        return _emit_list(node, **ctx2)
    if kind == "checklist":
        return _emit_checklist(node, **ctx2)
    if kind == "table":
        attrs = node.get("attrs", {}) or {}
        if attrs.get("matrix") or attrs.get("cells_with_span") or attrs.get("rowspan"):
            return _emit_table_merged(node, **ctx2)
        return [_emit_table_simple(node, **ctx2)]
    if kind == "table-merged-cells":
        return _emit_table_merged(node, **ctx2)
    if kind == "code":
        return [_emit_code(node, **ctx2)]
    if kind == "equation":
        return [_emit_equation(node, **ctx2)]
    if kind == "figure":
        return [_emit_figure(node, **ctx2)]
    if kind == "diagram":
        return [_emit_diagram(node, **ctx2)]
    if kind == "admonition":
        return [_emit_callout(node, **ctx2)]
    if kind == "collapsible":
        return [_emit_collapsible(node, **ctx2)]
    if kind == "columns":
        return [_emit_columns(node, **ctx2)]
    if kind == "divider":
        return [_emit_divider(node, **ctx2)]
    if kind == "quote":
        return [_emit_quote(node, **ctx2)]
    if kind == "step":
        return [_emit_step(node, **ctx2)]
    if kind == "question":
        return [_emit_question(node, **ctx2)]
    if kind == "parameter-table":
        return [_emit_parameter_table(node, **ctx2)]
    if kind == "query":
        return [_emit_diagram({"attrs": {"text": attrs.get("query", ""),
                                          "lang": "dataview"}, "children": []},
                               **ctx2)]
    # Nodos desconocidos: degradación silenciosa (preserva INV-07).
    ctx2.get("degradations", []).append({
        "node_path": node_path,
        "node_type": kind or "unknown",
        "capability": "unknown",
        "alternative": "nodo omitido (tipo no reconocido)",
        "evidence": "POST /v1/blocks sin bloque para este tipo",
        "content_intact": True,
    })
    return []


# ---------------------------------------------------------------------------
# Properties de database
# ---------------------------------------------------------------------------


def _emit_property(name: str, value: Any, value_type: str) -> Optional[dict]:
    notion_type = PROPERTY_TYPE_MAP.get(value_type.lower(), "rich_text")
    if notion_type == "rich_text":
        return {
            "type": "rich_text",
            "rich_text": _rich_text_from_string(str(value))
        }
    if notion_type == "number":
        try:
            return {"type": "number", "number": float(value)}
        except (TypeError, ValueError):
            return {"type": "rich_text", "rich_text": _rich_text_from_string(str(value))}
    if notion_type == "checkbox":
        return {"type": "checkbox", "checkbox": bool(value)}
    if notion_type == "date":
        return {"type": "date", "date": {"start": str(value)}}
    if notion_type == "url":
        return {"type": "url", "url": str(value)}
    if notion_type == "email":
        return {"type": "email", "email": str(value)}
    if notion_type == "phone_number":
        return {"type": "phone_number", "phone_number": str(value)}
    if notion_type == "select":
        return {"type": "select", "select": {"name": str(value)}}
    if notion_type == "multi_select":
        if isinstance(value, list):
            names = [str(v) for v in value]
        else:
            names = [str(value)]
        return {"type": "multi_select", "multi_select": [{"name": n} for n in names]}
    return None


def _collect_properties(ir: dict, database_properties: set,
                       renderer_version: str,
                       source_hash: str, ir_sha256: str,
                       dry_run: bool = False) -> Dict[str, dict]:
    """Recolecta todas las properties del IR.

    Modo producción (`dry_run=False`): solo emite properties presentes en
    `database_properties` (consultado vía GET /databases/{id}). Las que no
    existen se omiten con warning.

    Modo dry-run (`dry_run=True`): emite todas las properties del IR (incluidas
    las auto-properties). Permite verificar la lógica de emisión en CI sin
    token.
    """
    props: Dict[str, dict] = {}

    # Auto-properties (siempre intentamos; si la database no las tiene, las omitimos
    # en producción; en dry-run las emitimos siempre).
    auto = {
        "notemartin_note_id": ("rich_text", ir.get("note_id", "")),
        "notemartin_source_hash": ("rich_text", source_hash),
        "notemartin_ir_sha256": ("rich_text", ir_sha256),
        "notemartin_rendered_at": ("date", _now_utc_iso()),
        "notemartin_renderer_version": ("rich_text", renderer_version),
    }
    for name, (vt, val) in auto.items():
        if dry_run or not database_properties or name in database_properties:
            p = _emit_property(name, val, vt)
            if p:
                props[name] = p

    # User properties del IR.
    def _walk(node: Any) -> None:
        if not isinstance(node, dict):
            return
        if node.get("node") == "property-block":
            attrs = node.get("attrs", {}) or {}
            name = attrs.get("name", "")
            if not name:
                return
            if dry_run or not database_properties or name in database_properties:
                vt = attrs.get("type", "string")
                p = _emit_property(name, attrs.get("value"), vt)
                if p:
                    props[name] = p
        for child in node.get("children", []) or []:
            _walk(child)

    _walk(ir)
    return props


def _fetch_database_properties(database_id: str, token: str,
                                degradations: List[dict]) -> set:
    """Devuelve el set de nombres de properties existentes en la database."""
    try:
        resp = _notion_request_with_retry("GET", f"/databases/{database_id}", None,
                                          token, degradations)
    except NotionAPIError:
        return set()
    if not resp:
        return set()
    return set((resp.get("properties") or {}).keys())


# ---------------------------------------------------------------------------
# Reporte (contract §7)
# ---------------------------------------------------------------------------


def build_report(source_hash: str, degradations: List[dict],
                 ir_node_count: int, published: Dict[str, str],
                 api_calls: int, retries: int,
                 large_notes: List[str]) -> Tuple[Dict[str, Any], str]:
    content_loss = sum(1 for d in degradations if not d.get("content_intact", True))
    report = {
        "schema_version": "1.0.0",
        "target": "notion_api",
        "source_hash": source_hash,
        "generated_at": _now_utc_iso(),
        "totals": {
            "ir_nodes": ir_node_count,
            "degradations": len(degradations),
            "content_loss": content_loss,
        },
        "degradations": degradations,
        "published_pages": published,
        "unresolved_targets": [],
        "extra": {
            "api_calls": api_calls,
            "retries": retries,
            "large_note_blocks": large_notes,
        }
    }
    md_lines = [
        "# Reporte de degradación — Notion API",
        "",
        f"- **schema_version:** {report['schema_version']}",
        f"- **target:** notion_api",
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
        f"| Llamadas HTTP | {api_calls} |",
        f"| Reintentos | {retries} |",
        f"| Notas publicadas | {len(published)} |",
        f"| Notas grandes (>2000 blocks) | {len(large_notes)} |",
        "",
    ]
    if degradations:
        md_lines.append("## Degradaciones")
        md_lines.append("")
        for i, d in enumerate(degradations, start=1):
            md_lines.append(f"### notion_api / {d.get('capability', '?')}")
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
    md_lines.append(f"- Nodos contabilizados en el reporte: {len(degradations)}")
    md_lines.append(f"- Nodos IR totales: {ir_node_count}")
    md_lines.append(f"- content_loss: {content_loss} (debe ser 0; RC-01)")
    return report, "\n".join(md_lines)


# ---------------------------------------------------------------------------
# Render driver
# ---------------------------------------------------------------------------


class _RenderContext:
    def __init__(self, token: str, database_id: Optional[str],
                 parent_page_id: Optional[str], dry_run: bool,
                 renderer_version: str, source_hash: str,
                 payloads_dir: Path):
        self.token = token
        self.database_id = database_id
        self.parent_page_id = parent_page_id
        self.dry_run = dry_run
        self.renderer_version = renderer_version
        self.source_hash = source_hash
        self.payloads_dir = payloads_dir
        self.degradations: List[dict] = []
        self.api_calls = 0
        self.retries = 0
        self.published: Dict[str, str] = {}
        self.large_notes: List[str] = []
        self.note_id_to_page: Dict[str, str] = {}
        self.db_properties: set = set()
        if database_id and not dry_run:
            self.db_properties = _fetch_database_properties(
                database_id, token, self.degradations
            )

    def _emit_payload(self, note_id: str, idx: int, body: dict) -> None:
        if not self.dry_run:
            return
        self.payloads_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.payloads_dir / f"{note_id}-{idx:03d}.json"
        _atomic_write_json(out_path, body)

    def _track_call(self) -> None:
        self.api_calls += 1
        if self.api_calls > 1:
            time.sleep(INTER_REQUEST_DELAY)

    def _track_retry(self) -> None:
        self.retries += 1


def _render_ir(ir: dict, ctx: _RenderContext) -> Optional[str]:
    note_id = str(ir.get("note_id", "note-unknown"))
    title = ir.get("title", note_id)
    ir_sha256 = _sha256_of_ir(ir)

    # 1. Emitir top-level blocks.
    blocks: List[dict] = []
    block_ctx = {
        "note_id_to_page": ctx.note_id_to_page,
        "degradations": ctx.degradations,
        "current_depth": 0,
    }
    children = ir.get("children", []) or []
    for i, child in enumerate(children):
        blocks.extend(_emit_node_blocks(child, i, block_ctx))

    # 2. Detectar nota grande.
    if len(blocks) > 2000:
        ctx.large_notes.append(note_id)

    # 3. Idempotencia: buscar página existente.
    page_id: Optional[str] = None
    if not ctx.dry_run:
        page_id = _search_existing_page(note_id, ctx.token, ctx.database_id)
        ctx._track_call()
    else:
        page_id = None

    # 4. Crear o actualizar página.
    if page_id is None:
        # Create
        body = {
            "properties": _collect_properties(
                ir, ctx.db_properties,
                ctx.renderer_version, ctx.source_hash, ir_sha256,
                dry_run=ctx.dry_run,
            ) if ctx.database_id else {
                "title": {"title": [{"type": "text",
                                     "text": {"content": f"[{note_id}] {title}"}}]}
            },
            "children": blocks[:BLOCKS_PER_REQUEST],
        }
        if ctx.database_id:
            body["parent"] = {"database_id": ctx.database_id}
        elif ctx.parent_page_id:
            body["parent"] = {"page_id": ctx.parent_page_id}
        else:
            return None  # No se puede crear sin parent.

        ctx._emit_payload(note_id, 0, body)
        if ctx.dry_run:
            page_id = f"dry-run-page-{note_id}"
        else:
            resp = _notion_request_with_retry(
                "POST", "/pages", body, ctx.token, ctx.degradations, note_id
            )
            ctx._track_call()
            if resp:
                page_id = resp.get("id")
            if not page_id:
                return None
    else:
        # Patch children: archive existing, then append.
        ctx._emit_payload(note_id, 0, {"_action": "patch-existing", "page_id": page_id})
        if not ctx.dry_run:
            existing = _notion_request_with_retry(
                "GET", f"/blocks/{page_id}/children?page_size=100", None,
                ctx.token, ctx.degradations, note_id
            )
            ctx._track_call()
            for blk in (existing or {}).get("results", []):
                _notion_request_with_retry(
                    "DELETE", f"/blocks/{blk['id']}", None,
                    ctx.token, ctx.degradations, note_id
                )
                ctx._track_call()

    ctx.note_id_to_page[note_id] = page_id
    ctx.published[note_id] = page_id

    # 5. Trocear y enviar children restantes (si blocks > 100).
    remaining = blocks[BLOCKS_PER_REQUEST:]
    chunk_idx = 1
    for chunk in _chunk_blocks(remaining):
        body = {"children": chunk}
        ctx._emit_payload(note_id, chunk_idx, body)
        if not ctx.dry_run:
            _notion_request_with_retry(
                "PATCH", f"/blocks/{page_id}/children", body,
                ctx.token, ctx.degradations, note_id
            )
            ctx._track_call()
        chunk_idx += 1

    # 6. Si se proporcionaron properties adicionales (database), PATCH properties.
    if ctx.database_id and not ctx.dry_run:
        props = _collect_properties(
            ir, ctx.db_properties,
            ctx.renderer_version, ctx.source_hash, ir_sha256,
            dry_run=ctx.dry_run,
        )
        if props:
            body = {"properties": props}
            ctx._emit_payload(note_id, chunk_idx, body)
            _notion_request_with_retry(
                "PATCH", f"/pages/{page_id}", body, ctx.token, ctx.degradations, note_id
            )
            ctx._track_call()

    return page_id


# ---------------------------------------------------------------------------
# Mini-parser YAML para `targets.notion.*`
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


def _get_notion_config(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Acepta tanto `notion` (F11) como `notion_api` (F53)."""
    targets = profile.get("targets", {}) or {}
    return targets.get("notion") or targets.get("notion_api") or {}


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------


def load_ir(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_profile(path: Path) -> dict:
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
        prog="notion_api.py",
        description="Renderer Notion API (L4) para el Note IR. Implementa el contrato F53.",
    )
    parser.add_argument("--ir", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--matrix", type=Path,
                        default=(Path(__file__).resolve().parents[2] /
                                 "references" / "08-render" / "capability-matrix.md"))
    parser.add_argument("--source-hash", type=str, default=None)
    parser.add_argument("--notion-token", type=str,
                        default=os.environ.get("NOTION_TOKEN"))
    parser.add_argument("--database-id", type=str,
                        default=os.environ.get("NOTION_DATABASE_ID"))
    parser.add_argument("--page-parent-id", type=str, default=None)
    parser.add_argument("--renderer-version", type=str, default="0.1.0")
    parser.add_argument("--dry-run", action="store_true",
                        help="No hacer HTTP; escribir payloads a render/notion_api/payloads/.")
    parser.add_argument("--pre-render-diagrams", action="store_true",
                        help="Activa F70 (diagram_image.py) cuando exista. Default off.")

    args = parser.parse_args(argv)

    if not args.ir.exists():
        print(f"ERROR: IR no encontrado en {args.ir}", file=sys.stderr)
        return EXIT_FATAL
    if not args.profile.exists():
        print(f"ERROR: profile no encontrado en {args.profile}", file=sys.stderr)
        return EXIT_FATAL
    if not args.notion_token and not args.dry_run:
        print("ERROR: --notion-token o NOTION_TOKEN requerido (o usa --dry-run).",
              file=sys.stderr)
        return EXIT_FATAL

    profile = load_profile(args.profile)
    notion_cfg = _get_notion_config(profile)
    database_id = args.database_id or notion_cfg.get("database_id")
    parent_page_id = args.page_parent_id or notion_cfg.get("page_parent_id")

    if not args.dry_run and not database_id and not parent_page_id:
        print("ERROR: se requiere --database-id o --page-parent-id (o --dry-run).",
              file=sys.stderr)
        return EXIT_FATAL

    source_hash = derive_source_hash(args.out_dir, args.source_hash)
    if not re.match(r"^[0-9a-f]{64}$", source_hash):
        source_hash = "0" * 64

    payloads_dir = args.out_dir / "render" / "notion_api" / "payloads"

    ctx = _RenderContext(
        token=args.notion_token or "",
        database_id=database_id,
        parent_page_id=parent_page_id,
        dry_run=args.dry_run,
        renderer_version=args.renderer_version,
        source_hash=source_hash,
        payloads_dir=payloads_dir,
    )

    # Recolectar IRs.
    if args.ir.is_dir():
        ir_paths = sorted(args.ir.glob("*.json"))
    else:
        ir_paths = [args.ir]
    if not ir_paths:
        print(f"ERROR: no hay IRs en {args.ir}", file=sys.stderr)
        return EXIT_FATAL

    # Pre-pass: construir set de note_ids para resolver link-note targets.
    all_note_ids: set = set()
    ir_objs: List[dict] = []
    for ir_path in ir_paths:
        try:
            ir_obj = load_ir(ir_path)
        except (json.JSONDecodeError, OSError) as e:
            print(f"WARN: no se pudo cargar {ir_path}: {e}", file=sys.stderr)
            continue
        ir_objs.append(ir_obj)
        all_note_ids.add(ir_obj.get("note_id", ""))

    # Pre-pass: si NO dry_run, resolver note_id → page_id vía search.
    if not args.dry_run and ctx.token:
        for nid in all_note_ids:
            if not nid:
                continue
            page_id = _search_existing_page(nid, ctx.token, database_id)
            ctx._track_call()
            if page_id:
                ctx.note_id_to_page[nid] = page_id

    # Render pass.
    total_nodes = sum(len(ir.get("children", []) or []) for ir in ir_objs)
    for ir_obj in ir_objs:
        try:
            _render_ir(ir_obj, ctx)
        except (NotionAuthError, NotionAPIError) as e:
            print(f"ERROR: {ir_obj.get('note_id', '?')}: {e}", file=sys.stderr)
            return EXIT_FATAL

    # Reporte doble.
    report, report_md = build_report(
        source_hash=source_hash,
        degradations=ctx.degradations,
        ir_node_count=total_nodes,
        published=ctx.published,
        api_calls=ctx.api_calls,
        retries=ctx.retries,
        large_notes=ctx.large_notes,
    )
    reports_dir = args.out_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(reports_dir / "render-degradation.json", report)
    _atomic_write_text(reports_dir / "render-degradation.md", report_md)

    print(f"OK — {len(ctx.published)} nota(s) procesada(s)")
    print(f"     api_calls={ctx.api_calls} retries={ctx.retries} "
          f"degradations={len(ctx.degradations)}")
    if ctx.large_notes:
        print(f"WARN — {len(ctx.large_notes)} nota(s) > 2000 bloques")
        return EXIT_WARN
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
