"""Constructor del IR — Fase 48.

Convierte el árbol de bloques + nodos inline en un árbol IR JSON-ready conforme
a `schemas/note-ir.schema.json` (F14, Draft 2020-12). El schema es estricto:
- Top-level required: `schema_version`, `note_id`, `title`, `blocks`.
- Cada nodo tiene `node`, `attrs` (con `capability` obligatoria + campos específicos),
  `source_refs`, opcional `children`.
- `attrs` tiene `additionalProperties: false`.

Sin dependencias externas. Python 3.9+ stdlib.
"""

import sys
from pathlib import Path
from typing import List

# Asegurar que el módulo `_block_parser` se carga con el mismo nombre que en
# parse_notemark.py (donde `_skill_block_parser` es un alias). Esto evita
# que `isinstance(c, Block)` falle por clases distintas.
_pkg_dir = Path(__file__).resolve().parent
if "_block_parser" not in sys.modules:
    import importlib.util
    spec = importlib.util.spec_from_file_location("_block_parser", str(_pkg_dir / "_block_parser.py"))
    _mod = importlib.util.module_from_spec(spec)
    sys.modules["_block_parser"] = _mod
    spec.loader.exec_module(_mod)
Block = sys.modules["_block_parser"].Block

if "_inline_parser" not in sys.modules:
    import importlib.util
    spec = importlib.util.spec_from_file_location("_inline_parser", str(_pkg_dir / "_inline_parser.py"))
    _mod = importlib.util.module_from_spec(spec)
    sys.modules["_inline_parser"] = _mod
    spec.loader.exec_module(_mod)
parse_inline = sys.modules["_inline_parser"].parse_inline
_parse_text_segment = sys.modules["_inline_parser"]._parse_text_segment


# Capacidades por tipo de bloque IR (F14 §7 + capability-matrix de F8).
BLOCK_CAPABILITIES = {
    "section": "section",
    "paragraph": "paragraph",
    "list": "list",
    "table": "table",
    "code": "code",
    "console": "console",
    "equation": "equation-block",
    "figure": "figure",
    "diagram": "diagram",
    "admonition": "callout",
    "collapsible": "collapsible",
    "quote": "quote",
    "columns": "columns",
    "divider": "divider",
    "property-block": "property-block",
    "question": "question",
    "step": "step",
    "parameter-table": "parameter-table",
    "heading": "section",
}

# Severidades válidas para admonition (F14 schema + F45 §3.1).
ADMONITION_SEVERITIES = {
    "warning", "note", "tip", "example", "danger", "security",
    "performance", "version", "deprecated", "conflict", "external", "derived",
}


class IRBuilder:
    """Construye el árbol IR desde el árbol de bloques."""

    def __init__(self, frontmatter=None, source_hash: str = ""):
        self.frontmatter = frontmatter or {}
        self.source_hash = source_hash

    def build(self, blocks: List[Block]) -> dict:
        """Punto de entrada; devuelve el árbol IR como dict."""
        # Filtrar bloques de tipo frontmatter (no van en `blocks`).
        body_blocks = [b for b in blocks if b.kind != "frontmatter"]
        tree = self._build_blocks(body_blocks)
        title = self.frontmatter.get("title", "")
        if not title:
            # Si no hay title en frontmatter, derivarlo del primer heading.
            title = self._first_h1_title(body_blocks) or ""
        note_id = title.lower().replace(" ", "-") if title else ""
        return {
            "schema_version": "1.0.0",
            "note_id": note_id,
            "title": title,
            "layer": "l2",
            "blocks": tree,
        }

    def _first_h1_title(self, blocks: List[Block]) -> str:
        for b in blocks:
            if b.kind == "heading" and b.attrs.get("level", 1) == 1:
                return b.attrs.get("text", "")
        return ""

    def _build_blocks(self, blocks: List[Block]) -> List[dict]:
        result: List[dict] = []
        for b in blocks:
            node = self._build_block(b)
            if node is not None:
                result.append(node)
        return result

    def _build_block(self, b: Block):
        kind = b.kind
        capability = BLOCK_CAPABILITIES.get(kind, "text")

        if kind == "heading":
            level = int(b.attrs.get("level", 1))
            # El schema no incluye title en section.attrs, pero lo añadimos
            # como campo auxiliar para que el round-trip pueda re-emitir el
            # heading. La validación contra schema marcará este campo como
            # "additionalProperties not allowed"; el caller lo acepta o lo
            # filtra antes de validar.
            return self._node("section", {
                "level": level,
                "capability": capability,
                "_title": b.attrs.get("text", ""),  # auxiliar, fuera del schema
            })
        if kind == "paragraph":
            lines = b.children if b.children and isinstance(b.children[0], str) else []
            text = " ".join(lines).strip()
            return self._node("paragraph", {"capability": capability}, children=_build_paragraph_children(text))
        if kind == "list":
            ordered = bool(b.attrs.get("ordered", False))
            items = []
            for item in b.children:
                if isinstance(item, dict) and "text" in item:
                    inline = parse_inline(item["text"])
                    items.extend(inline)
            return self._node("list", {"ordered": ordered, "capability": capability}, children=items)
        if kind == "table":
            rows_text = [r["text"] if isinstance(r, dict) else r for r in b.children]
            # Parsear headers (primera fila).
            headers = _split_table_row(rows_text[0]) if rows_text else []
            return self._node("table", {
                "headers": headers,
                "capability": capability,
            })
        if kind == "code":
            text = "\n".join(b.children) if b.children and isinstance(b.children[0], str) else ""
            return self._node("code", {
                "lang": b.attrs.get("lang", "text"),
                "text": text,
                "capability": capability,
            })
        if kind == "console":
            # El contenido de :::console se almacena como paragraph con líneas-string.
            lines_text: List[str] = []
            for c in b.children:
                if isinstance(c, Block) and c.kind == "paragraph":
                    for ln in c.children:
                        if isinstance(ln, str):
                            lines_text.append(ln)
            return self._node("console", {
                "lines": lines_text,
                "capability": capability,
            })
        if kind == "equation":
            latex = "\n".join(b.children) if b.children and isinstance(b.children[0], str) else ""
            return self._node("equation", {
                "latex": latex,
                "display": True,
                "capability": capability,
            })
        if kind == "figure":
            image_text = ""
            for c in b.children:
                if isinstance(c, str) and c.startswith("!"):
                    image_text = c
                    break
            return self._node("figure", {
                "src": image_text,
                "alt": image_text,
                "capability": capability,
            })
        if kind == "diagram":
            code_text = ""
            for c in b.children:
                if isinstance(c, Block) and c.kind == "code":
                    code_text = "\n".join(c.children)
                    break
            return self._node("diagram", {
                "kind": "mermaid",
                "text": code_text,
                "capability": capability,
            })
        if kind == "admonition":
            raw = b.attrs.get("raw_name", "note")
            # Mapear example → tip (F45 §10.4); el resto se mantiene.
            severity = raw if raw in ADMONITION_SEVERITIES else "note"
            if raw == "example":
                severity = "tip"
            children_ir = self._build_blocks([c for c in b.children if isinstance(c, Block)])
            return self._node("admonition", {
                "severity": severity,
                "capability": capability,
            }, children=children_ir)
        if kind == "collapsible":
            title = b.attrs.get("title", "")
            for c in b.children:
                if isinstance(c, Block) and c.kind == "heading":
                    title = c.attrs.get("text", "")
                    break
            children_ir = self._build_blocks([c for c in b.children if isinstance(c, Block)])
            return self._node("collapsible", {
                "title": title,
                "default_open": False,
                "capability": capability,
            }, children=children_ir)
        if kind == "columns":
            children_ir = self._build_blocks([c for c in b.children if isinstance(c, Block)])
            return self._node("columns", {"count": 2, "capability": capability}, children=children_ir)
        if kind == "parameter-table":
            children_ir = self._build_blocks([c for c in b.children if isinstance(c, Block)])
            return self._node("parameter-table", {
                "columns": ["name", "type", "default", "range"],
                "capability": capability,
            }, children=children_ir)
        if kind == "step":
            index = int(b.attrs.get("n", "1") or 1)
            children_ir = self._build_blocks([c for c in b.children if isinstance(c, Block)])
            return self._node("step", {
                "index": index,
                "capability": capability,
            }, children=children_ir)
        if kind == "question":
            prompt = ""
            for c in b.children:
                if isinstance(c, Block) and c.kind == "heading":
                    prompt = c.attrs.get("text", "")
                    break
            children_ir = self._build_blocks([c for c in b.children if isinstance(c, Block) and c.kind != "heading"])
            return self._node("question", {
                "prompt": prompt,
                "capability": capability,
            }, children=children_ir)
        if kind == "quote":
            lines_text = b.children if b.children and isinstance(b.children[0], str) else []
            text = " ".join(lines_text)
            return self._node("quote", {"capability": capability}, children=_build_paragraph_children(text))
        if kind == "divider":
            return self._node("divider", {"capability": capability})
        if kind == "property-block":
            yaml_text = "\n".join(b.children) if b.children and isinstance(b.children[0], str) else ""
            return self._node("property-block", {
                "name": "block-local",
                "value": yaml_text,
                "capability": capability,
            })
        return None

    def _node(self, kind, attrs, children=None):
        """Construye un nodo IR con la estructura exigida por el schema."""
        node = {
            "node": kind,
            "attrs": attrs,
            "source_refs": [],
        }
        if children is not None:
            node["children"] = children
        return node


def _build_paragraph_children(text: str) -> List[dict]:
    """Parsea texto de párrafo en inline nodes."""
    return parse_inline(text)


def _split_table_row(row: str) -> List[str]:
    """Divide una fila de tabla por `|`, limpiando espacios."""
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    return [c for c in cells if c != ""]
