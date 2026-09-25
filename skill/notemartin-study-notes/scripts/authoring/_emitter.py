"""Emisor canónico — Fase 48.

Toma un IR y lo emite como NoteMark en forma canónica (frontmatter ordenado,
una línea en blanco entre bloques, indentación de 2 espacios, marcas inline en
orden de aparición). Usado por el round-trip test (F48 criterio #4).

Sin dependencias externas. Python 3.9+ stdlib.
"""

from typing import List

# Orden canónico de las 18 propiedades del frontmatter (F47 §5).
FRONTMATTER_ORDER = [
    "title", "note-type", "status", "tags",
    "source", "source-type", "vendor", "product", "product-version",
    "source-anchor", "source-url", "retrieved",
    "language", "coverage", "difficulty", "review-next",
    "aliases", "related",
]


class CanonicalEmitter:
    """Emite NoteMark canónico desde un IR."""

    def __init__(self, ir: dict) -> None:
        self.ir = ir

    def emit(self) -> str:
        parts: List[str] = []
        # Emitir frontmatter solo si está presente como campo separado (no en
        # el schema actual; se preserva si el caller lo añade).
        frontmatter = self.ir.get("frontmatter")
        if frontmatter:
            parts.append(self._emit_frontmatter(frontmatter))
            parts.append("")
        # Usar 'blocks' (schema F14) o 'tree' (legado).
        blocks = self.ir.get("blocks", self.ir.get("tree", []))
        for node in blocks:
            parts.append(self._emit_node(node))
        return "\n".join(parts).rstrip() + "\n"

    def _emit_frontmatter(self, fm: dict) -> str:
        lines = ["---"]
        for key in FRONTMATTER_ORDER:
            if key in fm:
                lines.append(self._emit_yaml_value(key, fm[key]))
        for key in sorted(fm.keys()):
            if key in FRONTMATTER_ORDER:
                continue
            if key.startswith(("x-", "user-")):
                lines.append(self._emit_yaml_value(key, fm[key]))
        lines.append("---")
        return "\n".join(lines)

    def _emit_yaml_value(self, key: str, value) -> str:
        if isinstance(value, list):
            items = ", ".join(self._yaml_scalar(v) for v in value)
            return f"{key}: [{items}]"
        if isinstance(value, bool):
            return f"{key}: {'true' if value else 'false'}"
        return f"{key}: {self._yaml_scalar(value)}"

    @staticmethod
    def _yaml_scalar(value) -> str:
        s = str(value)
        if any(c in s for c in [":", "#", "&", "*", "?", "|", ">", "%", "@", "`"]) or s.startswith(("-", "[", "{", "&", "*", "!", "|", ">", "'", "\"", "%", "@", "`")):
            return f'"{s}"'
        return s

    def _emit_node(self, node: dict, indent: int = 0) -> str:
        kind = node.get("node", "")
        attrs = node.get("attrs", {})
        children = node.get("children", [])

        if kind == "section":
            level = attrs.get("level", 1)
            # El schema no incluye title en section.attrs; usamos _title como
            # auxiliar (añadido por el IR builder).
            title = attrs.get("title") or attrs.get("_title", "")
            header = ("#" * level) + " " + title
            body_parts = [header]
            for c in children:
                body_parts.append(self._emit_node(c, indent))
            return "\n\n".join(body_parts)

        if kind == "paragraph":
            return self._emit_inline_paragraph(children, indent)

        if kind == "list":
            ordered = attrs.get("ordered", False)
            items_out = []
            for i, item in enumerate(children):
                marker = f"{i + 1}." if ordered else "-"
                text = self._emit_inline_text(item.get("children", []))
                items_out.append(f"{'  ' * indent}{marker} {text}")
            return "\n".join(items_out)

        if kind == "table":
            # El schema no almacena las filas; emitimos solo los headers como
            # tabla GFM de 1 fila. Las filas se pierden en el round-trip
            # (limitación documentada).
            headers = attrs.get("headers", [])
            if not headers:
                return ""
            line = "| " + " | ".join(headers) + " |"
            sep = "|" + "|".join(["---"] * len(headers)) + "|"
            return f"{line}\n{sep}"

        if kind == "code":
            lang = attrs.get("lang", "text")
            text = attrs.get("text", "")
            return f"```{lang}\n{text}\n```"

        if kind == "console":
            lines = attrs.get("lines", [])
            text = "\n".join(lines)
            return f":::console\n{text}\n:::console"

        if kind == "equation":
            latex = attrs.get("latex", "")
            return f":::equation\n$$\n{latex}\n$$\n:::equation"

        if kind == "figure":
            image = attrs.get("image", "")
            caption = attrs.get("caption", "")
            return f":::figure\n{image}\n{caption}\n:::figure"

        if kind == "diagram":
            mermaid = attrs.get("mermaid", "")
            return f":::diagram\n```mermaid\n{mermaid}\n```\n:::diagram"

        if kind == "admonition":
            sub_kind = attrs.get("severity") or attrs.get("sub_kind", "note")
            title = attrs.get("title", "")
            attrs_str = f' title="{title}"' if title else ""
            children_out = "\n\n".join(self._emit_node(c, indent) for c in children)
            return f":::{sub_kind}{attrs_str}\n{children_out}\n:::{sub_kind}"

        if kind == "collapsible":
            title = attrs.get("title", "")
            attrs_str = f' title="{title}"' if title else ""
            children_out = "\n\n".join(self._emit_node(c, indent) for c in children)
            return f":::collapsible{attrs_str}\n{children_out}\n:::collapsible"

        if kind == "columns":
            children_out = "\n\n".join(self._emit_node(c, indent) for c in children)
            return f":::columns\n{children_out}\n:::columns"

        if kind == "parameter-table":
            children_out = "\n\n".join(self._emit_node(c, indent) for c in children)
            return f":::param-table\n{children_out}\n:::param-table"

        if kind == "step":
            index = attrs.get("index", 1)
            title = attrs.get("title", "")
            attrs_str = f' n="{index}"' if index > 1 else ""
            children_out = "\n\n".join(self._emit_node(c, indent) for c in children)
            head = f"### {title}" if title else ""
            body = head + ("\n\n" if head and children_out else "") + children_out
            return f":::step{attrs_str}\n{body}\n:::step"

        if kind == "question":
            prompt = attrs.get("prompt", "")
            attrs_str = ""
            children_out = "\n\n".join(self._emit_node(c, indent) for c in children)
            head = f"### {prompt}" if prompt else ""
            body = head + ("\n\n" if head and children_out else "") + children_out
            return f":::question{attrs_str}\n{body}\n:::question"

        if kind == "quote":
            text = self._emit_inline_text(children)
            return "\n".join(f"> {line}" for line in text.split("\n"))

        if kind == "divider":
            return "---"

        if kind == "property-block":
            yaml_text = attrs.get("yaml", "")
            return f":::property\n{yaml_text}\n:::property"

        if kind == "metadata":
            return ""

        return ""

    def _emit_inline_paragraph(self, children: list, indent: int) -> str:
        return self._emit_inline_text(children)

    def _emit_inline_text(self, children: list) -> str:
        parts: List[str] = []
        for n in children:
            kind = n.get("node", "")
            attrs = n.get("attrs", {})
            if kind == "text":
                parts.append(attrs.get("text", ""))
            elif kind == "strong":
                parts.append(f"**{attrs.get('text', '')}**")
            elif kind == "em":
                parts.append(f"*{attrs.get('text', '')}*")
            elif kind == "code-inline":
                parts.append(f"`{attrs.get('text', '')}`")
            elif kind == "link-external":
                parts.append(f"[{attrs.get('text', '')}]({attrs.get('url', '')})")
            elif kind == "source-ref":
                parts.append(f"{{src:{attrs.get('block_id', '')}}}")
            elif kind == "term-ref":
                parts.append(f"[[term:{attrs.get('term_id', attrs.get('text', ''))}]]")
            elif kind == "link-note":
                parts.append(f"[[note:{attrs.get('target', attrs.get('text', ''))}]]")
            elif kind == "placeholder":
                parts.append(f"{{{{{attrs.get('text', '')}}}}}")
            elif kind == "derived":
                parts.append("{derived}")
            elif kind == "external":
                parts.append("{external}")
            elif kind == "footnote-ref":
                parts.append(f"[[fn:{attrs.get('id', '')}]]")
            elif kind == "keyboard":
                parts.append(f"[[kbd:{attrs.get('combo', '')}]]")
            elif kind == "deleted":
                parts.append(f"~~{attrs.get('text', '')}~~")
            elif kind == "math-inline":
                parts.append(f"${attrs.get('latex', '')}$")
            elif kind == "layer-mark":
                parts.append(f"{{{{layer:{attrs.get('layer', '')}}}}}")
        return "".join(parts)
