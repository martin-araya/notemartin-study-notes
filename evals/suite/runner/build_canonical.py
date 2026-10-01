#!/usr/bin/env python3
"""build_canonical.py — Genera param_table_canonical desde sample.html

Forma de uso:
  python build_canonical.py --card <card.md> --sample <sample.html> --out <out.yaml>

Extrae los <dt><span class="term"><code>NAME</code>...</span></dt> de cada
<dl class="variablelist"> y emite un YAML con la forma canónica definida en
evals/suite/SCHEMA.md §1 (clave param_table_canonical).

Si el HTML declara menos de threshold_min_count parámetros, aborta con código 2.

Dependencias: PyYAML (rec); sin PyYAML emite JSON.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path


TERM_CLASS = "term"
VARIABLELIST_CLASS = "variablelist"
DEFAULT_THRESHOLD = 10


class HeadingExtractor(HTMLParser):
    """Detecta el texto de cada <h3> con su offset de carácter en el documento."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.headings: list[tuple[int, str]] = []
        self._in_h3 = False
        self._buf: list[str] = []
        self._start_offset = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "h3":
            self._in_h3 = True
            self._buf = []
            line, col = self.getpos()
            self._start_offset = _approx_offset_from_linecol(self.rawdata, line, col)

    def handle_endtag(self, tag: str) -> None:
        if tag == "h3" and self._in_h3:
            text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            if text:
                self.headings.append((self._start_offset, text))
            self._in_h3 = False

    def handle_data(self, data: str) -> None:
        if self._in_h3:
            self._buf.append(data)


def _approx_offset_from_linecol(raw: str, line: int, col: int) -> int:
    """Aproxima offset de carácter a partir de (línea 1-index, columna 0-index)."""
    if line <= 1:
        return max(0, col)
    # Contar saltos de línea hasta `line-1` y añadir col.
    nl = 0
    pos = 0
    while pos < len(raw) and nl < line - 1:
        if raw[pos] == "\n":
            nl += 1
        pos += 1
    return pos + max(0, col)


def _normalise_term(raw: str) -> str:
    return re.sub(r"\s+", " ", raw).strip().strip(",; ")


def _infer_kind(name: str) -> str:
    n = name.upper()
    if n in {"ON", "USING", "NATURAL", "CROSS JOIN", "LATERAL", "TABLESAMPLE"}:
        return "clause_keyword"
    if "join_type" in n.lower():
        return "clause_keyword"
    return "identifier"


def _extract_params_from_block(block: str) -> list[str]:
    out: list[str] = []
    for m in re.finditer(
        r'<dt>\s*<span class="term">(.*?)</span>\s*</dt>',
        block,
        re.DOTALL,
    ):
        inner = m.group(1)
        # Capturar TODO el contenido del primer <code>...</code>.
        cm = re.search(r"<code[^>]*>(.*?)</code>", inner, re.DOTALL)
        if not cm:
            continue
        raw_html = cm.group(1)
        raw = re.sub(r"<[^>]+>", "", raw_html)
        raw = _normalise_term(raw)
        # Para cláusulas con sintaxis mixta (palabra clave + placeholder), conservar
        # solo la palabra clave inicial cuando esté claramente identificable.
        # Ej.: "TABLESAMPLE sampling_method (...)" → "TABLESAMPLE".
        leading = raw.split(" ", 1)[0]
        if leading.upper() in {"TABLESAMPLE", "ON", "USING", "NATURAL", "CROSS", "LATERAL"}:
            if leading.upper() == "CROSS":
                # Conservar "CROSS JOIN" si aparece.
                if "CROSS JOIN" in raw.upper():
                    raw = "CROSS JOIN"
                else:
                    raw = leading
            else:
                raw = leading
        # Quitar paréntesis/coletillas residuales.
        raw = raw.split("(")[0].strip()
        if raw:
            out.append(raw)
    return out


def extract(html_text: str) -> list[dict]:
    """Extrae cada <dl class="variablelist"> con su h3 previo como sección."""
    he = HeadingExtractor()
    he.feed(html_text)
    headings = he.headings

    dl_matches = list(re.finditer(r'<dl class="variablelist">', html_text))
    out: list[dict] = []
    for dl in dl_matches:
        section: str | None = None
        for o, t in headings:
            if o <= dl.start():
                section = t
            else:
                break
        start = dl.end()
        end_m = re.search(r"</dl>", html_text[start:])
        end = start + end_m.start() if end_m else len(html_text)
        block = html_text[start:end]
        for name in _extract_params_from_block(block):
            out.append(
                {
                    "name": name,
                    "kind": _infer_kind(name),
                    "section": section or "UNKNOWN",
                }
            )
    return out


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def emit(params: list[dict], sample_sha256: str, card_path: str, today: str) -> str:
    obj = {
        "schema_version": "1.0.0",
        "source_card": card_path,
        "source_sample_sha256": sample_sha256,
        "extraction_date": today,
        "threshold_min_count": DEFAULT_THRESHOLD,
        "params": params,
    }
    try:
        import yaml  # type: ignore

        return yaml.safe_dump(obj, sort_keys=False, allow_unicode=True)
    except ImportError:
        return json.dumps(obj, indent=2, ensure_ascii=False)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Genera param_table_canonical desde sample.html")
    p.add_argument("--card", required=True)
    p.add_argument("--sample", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    args = p.parse_args(argv)

    sample = Path(args.sample)
    if not sample.exists():
        print(f"ERROR: sample no encontrado: {sample}", file=sys.stderr)
        return 2
    html_text = sample.read_text(encoding="utf-8", errors="replace")
    sample_sha256 = sha256_file(sample)

    params = extract(html_text)
    n = len(params)
    if n < args.threshold:
        print(
            f"ERROR: extraídos {n} parámetros; umbral mínimo {args.threshold}.",
            file=sys.stderr,
        )
        return 2

    out = emit(params, sample_sha256, args.card, date.today().isoformat())
    Path(args.out).write_text(out, encoding="utf-8")
    print(f"OK: {n} parámetros extraídos → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
