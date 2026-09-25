"""Parser de bloques — Fase 48.

Convierte la lista de tokens del lexer en un árbol de bloques estructurales
reconocidos. Cada bloque se emite como un dict Python con:
  { "kind": str, "line": int, "children": [...], "attrs": {...}, "meta": {...} }

Sin dependencias externas. Python 3.9+ stdlib.
"""

from dataclasses import dataclass
from typing import List

try:
    from ._lexer import Token  # type: ignore
except ImportError:
    # Carga plana (no como paquete) — usada por parse_notemark.py vía importlib.
    from _lexer import Token  # type: ignore  # noqa: F401


@dataclass
class Block:
    kind: str           # "section", "paragraph", "list", "table", "code", "admonition",
                        # "collapsible", "columns", "param-table", "step", "question",
                        # "diagram", "figure", "equation", "console", "divider",
                        # "property-block", "frontmatter"
    line: int
    attrs: dict
    children: list      # otros Block o strings (paragraph line, etc.)
    meta: dict


class BlockParser:
    """Parser recursivo-descendente de bloques NoteMark."""

    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset: int = 0) -> Token:
        i = min(self.pos + offset, len(self.tokens) - 1)
        return self.tokens[i]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def parse(self) -> List[Block]:
        """Punto de entrada; devuelve la lista de bloques raíz."""
        blocks: List[Block] = []
        while self.peek().kind != "EOF":
            tok = self.peek()
            if tok.kind == "FRONTMATTER_DELIM":
                blocks.append(self._parse_frontmatter())
            elif tok.kind == "BLANK":
                self.advance()
            elif tok.kind == "HR":
                blocks.append(Block("divider", tok.line, {}, [], {}))
                self.advance()
            elif tok.kind == "HEADING":
                blocks.append(self._parse_heading())
            elif tok.kind == "LIST_ITEM":
                blocks.append(self._parse_list())
            elif tok.kind == "TABLE_ROW":
                blocks.append(self._parse_table())
            elif tok.kind == "BLOCKQUOTE":
                blocks.append(self._parse_blockquote())
            elif tok.kind == "CODE_FENCE_OPEN":
                blocks.append(self._parse_code_fence())
            elif tok.kind == "DIRECTIVE_OPEN":
                blocks.append(self._parse_directive())
            elif tok.kind == "PARAGRAPH_LINE":
                blocks.append(self._parse_paragraph())
            else:
                self.advance()
        return blocks

    def _parse_frontmatter(self) -> Block:
        open_tok = self.advance()  # ---
        # Next token: FRONTMATTER_BODY.
        body_tok = self.advance()
        close_tok = self.advance()  # ---
        return Block(
            "frontmatter",
            open_tok.line,
            {"body": body_tok.value, "close_line": close_tok.line},
            [],
            {},
        )

    def _parse_heading(self) -> Block:
        tok = self.advance()
        return Block(
            "heading",
            tok.line,
            {"level": tok.meta.get("level", 1), "text": tok.value, "raw": tok.meta.get("raw", "")},
            [],
            {},
        )

    def _parse_list(self) -> Block:
        first = self.advance()
        ordered = first.meta.get("ordered", False)
        items = [{"text": first.value, "line": first.line}]
        # Continuar mientras veamos LIST_ITEM.
        while self.peek().kind == "LIST_ITEM":
            nxt = self.advance()
            items.append({"text": nxt.value, "line": nxt.line})
        return Block(
            "list",
            first.line,
            {"ordered": ordered},
            items,
            {},
        )

    def _parse_table(self) -> Block:
        first = self.advance()
        rows = [{"text": first.value, "line": first.line}]
        while self.peek().kind == "TABLE_ROW":
            nxt = self.advance()
            rows.append({"text": nxt.value, "line": nxt.line})
        # Detectar separator row.
        has_separator = any("---" in r["text"] for r in rows[1:2]) if len(rows) >= 2 else False
        return Block(
            "table",
            first.line,
            {"headers": rows[0]["text"] if rows else "", "has_separator": has_separator},
            rows,
            {},
        )

    def _parse_blockquote(self) -> Block:
        first = self.advance()
        lines = [first.value]
        while self.peek().kind == "BLOCKQUOTE":
            nxt = self.advance()
            lines.append(nxt.value)
        return Block(
            "quote",
            first.line,
            {},
            lines,
            {},
        )

    def _parse_code_fence(self) -> Block:
        open_tok = self.advance()
        lines: List[str] = []
        while self.peek().kind == "CODE_LINE":
            ln = self.advance()
            lines.append(ln.value)
        close_tok = self.advance() if self.peek().kind == "CODE_FENCE_CLOSE" else None
        return Block(
            "code",
            open_tok.line,
            {"lang": open_tok.meta.get("lang", "text")},
            lines,
            {"close_line": close_tok.line if close_tok else None},
        )

    def _parse_directive(self) -> Block:
        open_tok = self.advance()
        name = open_tok.meta.get("name", "")
        attrs = open_tok.meta.get("attrs", {})
        directive_kind = self._directive_to_kind(name)
        children: List[Block] = []
        # Consumir hasta DIRECTIVE_CLOSE (o EOF si se cerró antes).
        while self.peek().kind not in ("DIRECTIVE_CLOSE", "EOF"):
            tok = self.peek()
            if tok.kind == "BLANK":
                self.advance()
            elif tok.kind == "HEADING":
                children.append(self._parse_heading())
            elif tok.kind == "PARAGRAPH_LINE":
                children.append(self._parse_paragraph())
            elif tok.kind == "LIST_ITEM":
                children.append(self._parse_list())
            elif tok.kind == "TABLE_ROW":
                children.append(self._parse_table())
            elif tok.kind == "BLOCKQUOTE":
                children.append(self._parse_blockquote())
            elif tok.kind == "CODE_FENCE_OPEN":
                children.append(self._parse_code_fence())
            elif tok.kind == "DIRECTIVE_OPEN":
                children.append(self._parse_directive())
            else:
                self.advance()
        close_tok = self.advance() if self.peek().kind == "DIRECTIVE_CLOSE" else None
        return Block(
            directive_kind,
            open_tok.line,
            {**attrs, "raw_name": name},
            children,
            {"close_line": close_tok.line if close_tok else None},
        )

    @staticmethod
    def _directive_to_kind(name: str) -> str:
        """Mapea nombre de directiva al nodo IR equivalente."""
        if name in {"warning", "note", "tip", "example", "danger", "security",
                    "performance", "version", "deprecated", "conflict",
                    "external", "derived"}:
            return "admonition"
        mapping = {
            "collapsible": "collapsible",
            "columns": "columns",
            "param-table": "parameter-table",
            "step": "step",
            "question": "question",
            "diagram": "diagram",
            "figure": "figure",
            "equation": "equation",
            "console": "console",
            "property": "property-block",
        }
        return mapping.get(name, "admonition")

    def _parse_paragraph(self) -> Block:
        first = self.advance()
        lines = [first.value]
        while self.peek().kind == "PARAGRAPH_LINE":
            nxt = self.advance()
            lines.append(nxt.value)
        return Block(
            "paragraph",
            first.line,
            {},
            lines,
            {},
        )
