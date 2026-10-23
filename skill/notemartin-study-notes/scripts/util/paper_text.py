#!/usr/bin/env python3
"""paper_text.py — normalización de texto específica de papers (P2 del plan arXiv).

Funciones puras (sin I/O) que consume `scripts/ingest/pdf_native.py`:

    normalize_ligatures(text)        ﬁ ﬂ ﬃ ﬄ ﬀ ﬅ ﬆ → fi fl ffi ffl ff ft st
    classify_script(frag, neighbors) → "sub" | "sup" | None  (índices matemáticos)
    dehyphenate(fragments)           une palabras cortadas a fin de línea (reversible)
    detect_arxiv_stamp(text)         → dict | None  (estampa lateral arXiv:ID [cat] fecha)

Reglas:
  - Nada se borra: cada cambio queda registrado en `fragment["normalizations"]`.
  - `dehyphenate` conserva el guion en compuestos conocidos (`non-`, `self-`, ...)
    y cuando la continuación ya contiene un guion (`state-of-the-art`).

Documentación normativa: references/01-ingest/pdf-native.md §9 (paper mode).
Dependencias: Python 3.9+ stdlib.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence

LIGATURES: Dict[str, str] = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
    "\ufb05": "ft",
    "\ufb06": "st",
}

# Fuentes matemáticas de LaTeX/AMS: sus fragmentos pequeños son índices, no notas al pie.
MATH_FONT_RE = re.compile(r"(CMMI|CMSY|CMEX|CMR|CMBX|CMTI|MSBM|MSAM|MnSymbol|Math)", re.I)

# Prefijos de compuestos que conservan el guion aunque la línea se corte ahí.
COMPOUND_PREFIXES = frozenset({
    "non", "pre", "post", "anti", "semi", "multi", "self", "cross", "well", "ill",
    "high", "low", "long", "short", "state", "real", "end", "least", "mean", "inter",
    "intra", "sub", "co", "re", "half", "full", "single", "double", "high-dimensional",
})

# Colas típicas de compuestos (`physics-based`, `scale-free`, `real-world`).
COMPOUND_TAILS = frozenset({
    "based", "free", "like", "wise", "world", "time", "scale", "order", "level",
    "specific", "aware", "dependent", "independent", "driven", "informed", "valued",
    "agnostic", "oriented", "bound", "tuned", "art", "off", "line",
})

_TOKEN_RE = re.compile(r"[a-z]+(?:-[a-z]+)*")

ARXIV_STAMP_RE = re.compile(
    r"^arXiv:(?P<id>(?:\d{4}\.\d{4,5}|[a-z\-]+(?:\.[A-Z]{2})?/\d{7}))"
    r"(?P<version>v\d+)?\s*\[(?P<category>[A-Za-z\-]+(?:\.[A-Za-z\-]+)?)\]\s*"
    r"(?P<date>\d{1,2}\s+[A-Z][a-z]{2}\s+\d{4})\s*$"
)

# Un índice se acopla a un fragmento "padre" a menos de este múltiplo de su tamaño.
SCRIPT_MAX_GAP_FACTOR = 1.5
SCRIPT_MAX_TEXT_LEN = 12
SCRIPT_SIZE_RATIO_MAX = 0.85


def normalize_ligatures(text: str) -> str:
    """Sustituye ligaduras tipográficas Unicode por sus letras."""
    if not any(c in text for c in LIGATURES):
        return text
    return "".join(LIGATURES.get(c, c) for c in text)


def _note(frag: Dict[str, Any], kind: str, **extra: Any) -> None:
    entry = {"type": kind}
    entry.update(extra)
    frag.setdefault("normalizations", []).append(entry)


def apply_ligature_normalization(fragments: Sequence[Dict[str, Any]]) -> int:
    """Normaliza ligaduras in situ y registra el cambio. Devuelve nº de fragmentos tocados."""
    touched = 0
    for f in fragments:
        new = normalize_ligatures(f["text"])
        if new != f["text"]:
            _note(f, "ligature", original=f["text"])
            f["text"] = new
            touched += 1
    return touched


def classify_script(
    frag: Dict[str, Any],
    neighbors: Sequence[Dict[str, Any]],
    body_size: float,
) -> Optional[str]:
    """Devuelve "sub"/"sup" si `frag` es un índice de un fragmento vecino de tamaño de cuerpo.

    Un índice es un fragmento más pequeño que el cuerpo, corto (o en fuente matemática),
    adyacente en X a un vecino de tamaño >= cuerpo, y desplazado en la línea base:
    más abajo (y menor) = subíndice, más arriba = superíndice.
    """
    fs = float(frag.get("font_size", 0) or 0)
    if fs <= 0 or body_size <= 0 or fs >= body_size * SCRIPT_SIZE_RATIO_MAX:
        return None
    is_math_font = bool(MATH_FONT_RE.search(frag.get("font_name", "")))
    if len(frag["text"].strip()) > SCRIPT_MAX_TEXT_LEN and not is_math_font:
        return None
    fx0, fy0 = frag["bbox"][0], frag["bbox"][1]
    max_gap = SCRIPT_MAX_GAP_FACTOR * fs
    best: Optional[Dict[str, Any]] = None
    best_gap = None
    for n in neighbors:
        if n is frag or float(n.get("font_size", 0) or 0) < body_size * SCRIPT_SIZE_RATIO_MAX:
            continue
        nx1 = n["bbox"][2]
        nx0 = n["bbox"][0]
        gap = fx0 - nx1  # índice a la derecha del padre
        gap_left = nx0 - frag["bbox"][2]  # índice a la izquierda (poco común)
        if -fs <= gap <= max_gap:
            d = abs(gap)
        elif 0 <= gap_left <= max_gap:
            d = gap_left
        else:
            continue
        if abs(n["bbox"][1] - fy0) > 0.9 * float(n["font_size"]):
            continue
        if best_gap is None or d < best_gap:
            best, best_gap = n, d
    if best is None:
        return None
    dy = fy0 - best["bbox"][1]
    if abs(dy) < 0.12 * float(best["font_size"]) and not is_math_font:
        return None  # misma línea base: texto pequeño normal, no índice
    return "sup" if dy > 0 else "sub"


def mark_scripts(fragments: List[Dict[str, Any]], body_size: float) -> int:
    """Reclasifica índices matemáticos: rol `body` + campo `script`, no `footnote`.

    - Índice (sub/sup) adyacente a un padre de tamaño de cuerpo → `body` + `script`.
    - Glifo en fuente matemática que no es índice (p. ej. fórmula en tamaño reducido)
      → `body` (un glifo matemático nunca es una nota al pie).
    Las notas al pie reales (texto, tamaño menor) conservan el rol `footnote`.
    """
    changed = 0
    for f in fragments:
        if f.get("role") != "footnote":
            continue
        kind = classify_script(f, fragments, body_size)
        if kind:
            f["role"] = "body"
            f["script"] = kind
            changed += 1
        elif MATH_FONT_RE.search(f.get("font_name", "")):
            f["role"] = "body"
            changed += 1
    return changed


def build_vocab(all_fragments: Sequence[Sequence[Dict[str, Any]]]) -> Dict[str, int]:
    """Frecuencia de tokens en minúscula del documento (incluye compuestos con guion).

    Se construye ANTES de unir guiones, para decidir si `physics-` + `based` era un
    compuesto (aparece `physics-based` en otro lugar) o una palabra cortada.
    """
    vocab: Dict[str, int] = {}
    for frags in all_fragments:
        for f in frags:
            for tok in _TOKEN_RE.findall(f["text"].lower()):
                vocab[tok] = vocab.get(tok, 0) + 1
    return vocab


def _keep_hyphen(prefix: str, word: str, vocab: Optional[Dict[str, int]]) -> bool:
    base = re.sub(r"[^a-z\-]", "", word.lower())
    if vocab:
        if vocab.get(f"{prefix}-{base}", 0) > 0:
            return True
        if vocab.get(f"{prefix}{base}", 0) > 0:
            return False
    return prefix in COMPOUND_PREFIXES or base in COMPOUND_TAILS or "-" in base


def _is_continuation_candidate(frag: Dict[str, Any]) -> bool:
    return frag.get("role") in ("body", "caption") and bool(re.match(r"^[a-z]", frag["text"]))


def dehyphenate(fragments: List[Dict[str, Any]], vocab: Optional[Dict[str, int]] = None) -> int:
    """Une palabras cortadas a fin de línea entre fragmentos consecutivos del mismo cuerpo.

    Para `... trans-` + `port the ...` produce `... transport` + `the ...`. Mueve la
    primera palabra del fragmento siguiente al final del actual (el contenido total
    no cambia) y registra la operación en `normalizations` de ambos fragmentos.
    Devuelve el nº de uniones realizadas.
    """
    joined = 0
    for i in range(len(fragments) - 1):
        cur, nxt = fragments[i], fragments[i + 1]
        if cur.get("role") not in ("body", "caption") or cur.get("is_boilerplate"):
            continue
        text = cur["text"].rstrip()
        if not re.search(r"[A-Za-z]{2}-$", text):
            continue
        if not _is_continuation_candidate(nxt) or nxt.get("is_boilerplate"):
            continue
        if abs(float(cur.get("font_size", 0)) - float(nxt.get("font_size", 0))) > 0.5:
            continue
        m = re.match(r"^([a-z][a-z\-]*[a-z]|[a-z])([.,;:)\]]*)(\s+|$)", nxt["text"])
        if not m:
            continue
        word, punct = m.group(1), m.group(2)
        prefix = re.search(r"([A-Za-z]+)-$", text).group(1).lower()
        keep_hyphen = _keep_hyphen(prefix, word, vocab)
        merged = (text + word) if keep_hyphen else (text[:-1] + word)
        merged += punct
        rest = nxt["text"][m.end():]
        if not rest.strip():
            continue  # no vaciar el fragmento siguiente
        _note(cur, "dehyphenate", original=cur["text"], moved_word=word + punct, kept_hyphen=keep_hyphen)
        _note(nxt, "dehyphenate_source", original=nxt["text"], moved_word=word + punct)
        cur["text"] = merged
        nxt["text"] = rest
        joined += 1
    return joined


def detect_arxiv_stamp(text: str) -> Optional[Dict[str, str]]:
    """Reconoce la estampa lateral de arXiv: `arXiv:2201.00001v3 [math.NA] 17 Feb 2022`."""
    m = ARXIV_STAMP_RE.match(" ".join(text.split()))
    if not m:
        return None
    return {
        "id": m.group("id"),
        "version": m.group("version") or "",
        "category": m.group("category"),
        "date": m.group("date"),
    }
