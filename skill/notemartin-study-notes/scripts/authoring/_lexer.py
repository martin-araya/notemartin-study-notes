"""Lexer para NoteMark — Fase 48.

Tokeniza un archivo fuente a nivel de línea + columna. Emite tokens con metadatos
de posición para reportar errores con `archivo:línea:columna`.

Cobertura (47 reglas del EBNF):
- Frontmatter delimiters (`---`).
- Directivas de bloque (`:::nombre … :::`).
- Code fences (` ``` `).
- Headings (`#`, `##`, …).
- Lists, tables, blockquotes.
- Layer markers (`{layer:l1|l2|l3}`).
- Inline marks: `{src:blk_xxxx}`, `[[term:x]]`, `[[note:id]]`, `{{nombre}}`,
  `{derived}`, `{external}`, `[[fn:id]]`, `[[kbd:…]]`, `~~x~~`.

Sin dependencias externas. Python 3.9+ stdlib.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Token:
    kind: str
    value: str
    line: int       # 1-based
    col: int        # 1-based
    meta: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"Token({self.kind}, {self.value!r}, L{self.line}:C{self.col})"


@dataclass
class LexError(Exception):
    file: str
    line: int
    col: int
    token: str
    cause: str
    source_line: str = ""

    def __str__(self) -> str:
        ctx = f"\n  Contexto: {self.source_line}" if self.source_line else ""
        return (
            f"ERROR: {self.file}:{self.line}:{self.col}\n"
            f"  Token: {self.token!r}\n"
            f"  Causa: {self.cause}{ctx}"
        )


# Patrones de marcas inline (orden importa: de más específicos a más generales).
RE_SOURCE_REF = re.compile(r"\{src:(blk_[0-9a-f]{12})\}")
RE_TERM_REF = re.compile(r"\[\[term:([a-z][a-z0-9-]*)\]\]")
RE_LINK_NOTE = re.compile(r"\[\[note:([a-zA-Z0-9_-]+)\]\]")
RE_PLACEHOLDER = re.compile(r"\{\{([a-zA-Z][a-zA-Z0-9_-]*)\}\}")
RE_DERIVED = re.compile(r"\{derived\}")
RE_EXTERNAL = re.compile(r"\{external\}")
RE_FOOTNOTE = re.compile(r"\[\[fn:([a-zA-Z0-9_-]+)\]\]")
RE_KEYBOARD = re.compile(r"\[\[kbd:([^\]]+)\]\]")
RE_DELETED = re.compile(r"~~([^~]+)~~")
RE_LAYER = re.compile(r"\{layer:(l1|l2|l3)\}")
RE_MATH_INLINE = re.compile(r"\$([^$]+)\$")

# Compilado para detectar cualquier marca inline.
ALL_INLINE_PATTERNS = [
    ("source-ref", RE_SOURCE_REF),
    ("term-ref", RE_TERM_REF),
    ("link-note", RE_LINK_NOTE),
    ("placeholder", RE_PLACEHOLDER),
    ("derived", RE_DERIVED),
    ("external", RE_EXTERNAL),
    ("footnote-ref", RE_FOOTNOTE),
    ("keyboard", RE_KEYBOARD),
    ("deleted", RE_DELETED),
    ("layer-mark", RE_LAYER),
    ("math-inline", RE_MATH_INLINE),
]

# 22 directivas cerradas (F45 §3.1).
DIRECTIVE_NAMES = {
    "warning", "note", "tip", "example", "danger", "security",
    "performance", "version", "deprecated", "conflict", "external",
    "derived", "collapsible", "columns", "param-table", "step",
    "question", "diagram", "figure", "equation", "console", "property",
}

RE_DIRECTIVE_OPEN = re.compile(r"^:::([a-z][a-z0-9-]*)(?:\s+(.+))?$")
RE_DIRECTIVE_CLOSE = re.compile(r"^:::$")
RE_HEADING = re.compile(r"^(#{1,6})\s+(.+)$")
RE_FRONTMATTER_DELIM = re.compile(r"^---$")
RE_CODE_FENCE = re.compile(r"^```(\w*)$")
RE_LIST_ITEM = re.compile(r"^(\s*)([-*+]|\d+\.)\s+(.+)$")
RE_TABLE_SEP = re.compile(r"^\|?(\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?$")
RE_HR = re.compile(r"^---+$")
RE_BLOCKQUOTE = re.compile(r"^>\s?(.*)$")


class Lexer:
    """Tokeniza una fuente NoteMark en una lista de tokens."""

    def __init__(self, source, file: str = "<source>") -> None:
        # Normaliza CRLF y BOM.
        if source.startswith("\ufeff"):
            source = source[1:]
        source = source.replace("\r\n", "\n").replace("\r", "\n")
        self.source = source
        self.file = file
        self.lines = source.split("\n")
        self.tokens: List[Token] = []
        self.errors: List[LexError] = []

    def tokenize(self, collect_all: bool = False) -> List[Token]:
        """Tokeniza; si collect_all=True, no aborta al primer error."""
        self.tokens = []
        self.errors = []
        in_frontmatter = False
        frontmatter_lines: List[str] = []
        in_code_fence = False
        code_fence_lang = ""
        code_fence_start = 0
        in_directive = None  # nombre de la directiva abierta
        directive_start_line = 0
        directive_open_token: Optional[Token] = None

        for i, line in enumerate(self.lines):
            lineno = i + 1
            stripped = line.strip()

            # Code fence dentro o fuera de directiva.
            if not in_frontmatter:
                fence_match = RE_CODE_FENCE.match(stripped)
                if fence_match:
                    if not in_code_fence:
                        in_code_fence = True
                        code_fence_lang = fence_match.group(1) or "text"
                        code_fence_start = lineno
                        self.tokens.append(Token(
                            "CODE_FENCE_OPEN", stripped, lineno, 1,
                            {"lang": code_fence_lang},
                        ))
                        continue
                    else:
                        # Cierre.
                        in_code_fence = False
                        self.tokens.append(Token(
                            "CODE_FENCE_CLOSE", stripped, lineno, 1,
                            {"start_line": code_fence_start},
                        ))
                        continue

            # Dentro de code fence: línea literal.
            if in_code_fence:
                self.tokens.append(Token("CODE_LINE", line, lineno, 1))
                continue

            # Frontmatter.
            if not in_frontmatter and not in_directive:
                if RE_FRONTMATTER_DELIM.match(stripped) and lineno == 1:
                    in_frontmatter = True
                    self.tokens.append(Token("FRONTMATTER_DELIM", stripped, lineno, 1))
                    continue
                if RE_FRONTMATTER_DELIM.match(stripped) and i > 0 and not frontmatter_lines:
                    # `---` dentro del cuerpo = thematic break (HR).
                    self.tokens.append(Token("HR", stripped, lineno, 1))
                    continue

            if in_frontmatter:
                if RE_FRONTMATTER_DELIM.match(stripped):
                    # Cierre del frontmatter.
                    in_frontmatter = False
                    self.tokens.append(Token("FRONTMATTER_DELIM", stripped, lineno, 1))
                    # Emitir el cuerpo del frontmatter como una sola entidad.
                    self.tokens.append(Token(
                        "FRONTMATTER_BODY", "\n".join(frontmatter_lines), lineno, 1,
                        {"line_count": len(frontmatter_lines)},
                    ))
                    frontmatter_lines = []
                    continue
                else:
                    frontmatter_lines.append(line)
                    continue

            # Directive open/close.
            if in_directive is None:
                dopen = RE_DIRECTIVE_OPEN.match(stripped)
                if dopen:
                    name = dopen.group(1)
                    attrs_raw = dopen.group(2) or ""
                    if name not in DIRECTIVE_NAMES:
                        err = LexError(
                            self.file, lineno, 1, f":::{name}",
                            f"directiva desconocida '{name}'. "
                            f"Directivas válidas: {', '.join(sorted(DIRECTIVE_NAMES))}.",
                            line,
                        )
                        self.errors.append(err)
                        if not collect_all:
                            raise err
                    attrs = _parse_attrs(attrs_raw)
                    tok = Token(
                        "DIRECTIVE_OPEN", stripped, lineno, 1,
                        {"name": name, "attrs": attrs},
                    )
                    self.tokens.append(tok)
                    directive_open_token = tok
                    in_directive = name
                    directive_start_line = lineno
                    continue
            else:
                # Cierre: `:::` (sin nombre) o `:::{name}` (mismo nombre que abrió).
                if RE_DIRECTIVE_CLOSE.match(stripped):
                    self.tokens.append(Token(
                        "DIRECTIVE_CLOSE", stripped, lineno, 1,
                        {"name": in_directive, "start_line": directive_start_line},
                    ))
                    in_directive = None
                    continue
                # Cierre con nombre idéntico al abierto.
                dclose = RE_DIRECTIVE_OPEN.match(stripped)
                if dclose and dclose.group(1) == in_directive and not dclose.group(2):
                    self.tokens.append(Token(
                        "DIRECTIVE_CLOSE", stripped, lineno, 1,
                        {"name": in_directive, "start_line": directive_start_line},
                    ))
                    in_directive = None
                    continue

            # Heading.
            heading_match = RE_HEADING.match(stripped)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2).strip()
                self.tokens.append(Token(
                    "HEADING", text, lineno, 1,
                    {"level": level, "raw": stripped},
                ))
                continue

            # Línea en blanco.
            if not stripped:
                self.tokens.append(Token("BLANK", "", lineno, 1))
                continue

            # Lista.
            list_match = RE_LIST_ITEM.match(line)
            if list_match:
                indent = len(list_match.group(1))
                marker = list_match.group(2)
                text = list_match.group(3)
                is_ordered = bool(re.match(r"\d+\.", marker))
                self.tokens.append(Token(
                    "LIST_ITEM", text, lineno, 1 + indent,
                    {"ordered": is_ordered, "indent": indent // 2, "marker": marker},
                ))
                continue

            # Tabla.
            if "|" in line and lineno > 1:
                # Línea de tabla simple; la verificación del separador la hace el parser.
                self.tokens.append(Token("TABLE_ROW", line, lineno, 1))
                continue

            # Blockquote.
            bq_match = RE_BLOCKQUOTE.match(line)
            if bq_match:
                self.tokens.append(Token(
                    "BLOCKQUOTE", bq_match.group(1), lineno, 1,
                ))
                continue

            # Línea suelta → párrafo (cerrado por línea en blanco o cambio de bloque).
            self.tokens.append(Token("PARAGRAPH_LINE", line, lineno, 1))

        # Validar cierres pendientes.
        if in_code_fence:
            err = LexError(
                self.file, code_fence_start, 1, "```",
                f"code fence no cerrado (abierto en L{code_fence_start}).",
                self.lines[code_fence_start - 1] if code_fence_start <= len(self.lines) else "",
            )
            self.errors.append(err)
            if not collect_all:
                raise err
        if in_directive:
            err = LexError(
                self.file, directive_start_line, 1, f":::{in_directive}",
                f"directiva '{in_directive}' no cerrada (abierta en L{directive_start_line}).",
                self.lines[directive_start_line - 1] if directive_start_line <= len(self.lines) else "",
            )
            self.errors.append(err)
            if not collect_all:
                raise err
        if in_frontmatter:
            err = LexError(
                self.file, 1, 1, "---",
                "frontmatter no cerrado (falta línea '---' de cierre).",
                self.lines[0] if self.lines else "",
            )
            self.errors.append(err)
            if not collect_all:
                raise err

        self.tokens.append(Token("EOF", "", len(self.lines) + 1, 1))
        return self.tokens


def _parse_attrs(s: str) -> dict:
    """Parsea atributos `key="value"` o `key=value`."""
    attrs: dict = {}
    if not s.strip():
        return attrs
    # Permite pares key="value" o key=value (con comillas o sin).
    pattern = re.compile(r'(\w[\w-]*)=(?:"([^"]*)"|(\S+))')
    for m in pattern.finditer(s):
        key = m.group(1)
        value = m.group(2) if m.group(2) is not None else m.group(3)
        attrs[key] = value
    return attrs


def extract_inline_marks(line: str) -> List[dict]:
    """Extrae las marcas inline de una línea en orden de aparición."""
    marks = []
    for name, pattern in ALL_INLINE_PATTERNS:
        for m in pattern.finditer(line):
            marks.append({
                "kind": name,
                "match": m.group(0),
                "groups": m.groups(),
                "start": m.start(),
                "end": m.end(),
            })
    marks.sort(key=lambda x: x["start"])
    return marks
