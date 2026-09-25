"""Parser de marcas inline — Fase 48.

Tokeniza una línea (o fragmento) de párrafo en nodos inline IR. Reconoce las 9
marcas de F46 más el resto de inline IR (CommonMark: text, strong, em, code-inline,
link-external, math-inline, etc.).

Sin dependencias externas. Python 3.9+ stdlib.
"""

import re
from typing import List

try:
    from ._lexer import extract_inline_marks  # type: ignore
except ImportError:
    from _lexer import extract_inline_marks  # type: ignore  # noqa: F401

# Inline IR nodes (F14 §4) — capacidad según capability-matrix de F8.
INLINE_CAPS = {
    "text": "text",
    "strong": "strong",
    "em": "em",
    "code-inline": "code-inline",
    "link-external": "link-external",
    "link-note": "link-note",
    "term-ref": "link-term",
    "source-ref": "source-ref",
    "math-inline": "math-inline",
    "footnote-ref": "footnote-ref",
    "keyboard": "keyboard",
    "placeholder": "placeholder",
    "deleted": "deleted",
    "derived": "derived",
    "external": "external",
    "layer-mark": "layer-mark",
}


def parse_inline(line: str, default_capability: str = "text") -> List[dict]:
    """Convierte una línea de párrafo en una lista de nodos inline IR.

    Implementación: tokeniza las marcas inline por orden de aparición y rellena
    los huecos con nodos `text`. Las marcas dentro de code fences NO se procesan
    (el caller es responsable).
    """
    if not line:
        return []

    marks = extract_inline_marks(line)
    nodes: List[dict] = []
    cursor = 0

    for mk in marks:
        if mk["start"] > cursor:
            text_seg = line[cursor:mk["start"]]
            nodes.extend(_parse_text_segment(text_seg, default_capability))
        node = _build_inline_node(mk, default_capability)
        if node is not None:
            nodes.append(node)
        cursor = mk["end"]

    if cursor < len(line):
        tail = line[cursor:]
        nodes.extend(_parse_text_segment(tail, default_capability))

    return nodes


def _parse_text_segment(text: str, capability: str) -> List[dict]:
    """Parsea un segmento de texto: extrae code-inline, em, strong, link-external."""
    if not text:
        return []

    nodes: List[dict] = []
    # Buscar patrones en orden: code-inline, link-external, em, strong.
    patterns = [
        ("code-inline", re.compile(r"`([^`]+)`")),
        ("link-external", re.compile(r"\[([^\]]+)\]\(([^)]+)\)")),
        ("strong", re.compile(r"\*\*([^*]+)\*\*")),
        ("em", re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")),
    ]

    cursor = 0
    while cursor < len(text):
        best_match = None
        best_kind = None
        for kind, pat in patterns:
            m = pat.search(text, cursor)
            if m and (best_match is None or m.start() < best_match.start()):
                best_match = m
                best_kind = kind
        if best_match is None:
            if cursor < len(text):
                nodes.append(_node("text", {"text": text[cursor:], "capability": "text"}))
            break
        if best_match.start() > cursor:
            nodes.append(_node("text", {"text": text[cursor:best_match.start()], "capability": "text"}))
        if best_kind == "code-inline":
            nodes.append(_node("code-inline", {"text": best_match.group(1), "capability": "code-inline"}))
        elif best_kind == "link-external":
            nodes.append(_node("link-external", {
                "text": best_match.group(1),
                "url": best_match.group(2),
                "capability": "link-external",
            }))
        elif best_kind == "strong":
            nodes.append(_node("strong", {"capability": "strong"}))
        elif best_kind == "em":
            nodes.append(_node("em", {"capability": "em"}))
        cursor = best_match.end()

    return nodes


def _build_inline_node(mk: dict, capability: str):
    """Construye un nodo inline IR a partir de una marca extraída."""
    kind = mk["kind"]
    groups = mk["groups"]

    if kind == "source-ref":
        # Schema exige 12 lowercase hex chars. groups[0] es "blk_xxxxxxxxxxxx".
        # Extraemos solo los 12 hex.
        raw = groups[0]
        hex_id = raw[4:] if raw.startswith("blk_") else raw
        return _node("source-ref", {
            "block_id": hex_id,
            "source_hash": "0" * 64,
            "capability": "source-ref",
        })
    if kind == "term-ref":
        return _node("term-ref", {
            "text": groups[0],
            "term_id": groups[0],
            "capability": "link-term",
        })
    if kind == "link-note":
        return _node("link-note", {
            "text": groups[0],
            "target": groups[0],
            "capability": "link-note",
        })
    if kind == "placeholder":
        return _node("placeholder", {
            "text": groups[0],
            "capability": "placeholder",
        })
    if kind == "derived":
        # El schema no tiene nodo 'derived' — se representa como text + flag.
        return {
            "node": "text",
            "attrs": {"text": "", "capability": "text"},
            "source_refs": [],
            "derived": True,
        }
    if kind == "external":
        return {
            "node": "text",
            "attrs": {"text": "", "capability": "text"},
            "source_refs": [],
            "external": True,
        }
    if kind == "footnote-ref":
        return _node("footnote-ref", {
            "ref_id": groups[0],
            "capability": "footnote-ref",
        })
    if kind == "keyboard":
        return _node("keyboard", {
            "text": groups[0],
            "capability": "keyboard",
        })
    if kind == "deleted":
        return _node("deleted", {"capability": "deleted"})
    if kind == "layer-mark":
        # El schema no tiene nodo 'layer-mark' — el layer es un atributo
        # sibling del nodo. Devolvemos un text vacío con `layer` como
        # atributo del nodo (no dentro de attrs).
        n = _node("text", {"text": "", "capability": "text"})
        n["layer"] = groups[0]
        return n
    if kind == "math-inline":
        return _node("math-inline", {
            "latex": groups[0],
            "capability": "math-inline",
        })
    return None


def _node(kind: str, attrs: dict):
    """Crea un nodo IR con estructura válida para el schema."""
    return {
        "node": kind,
        "attrs": attrs,
        "source_refs": [],
    }
