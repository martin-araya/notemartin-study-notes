"""Mapeo canónico severidad → estilo por destino (F73).

Tabla cerrada de 20 severidades × 5 destinos (Obsidian callout, Notion API
icon, Notion API color, AppFlowy callout, HTML/PDF CSS class). Consumida por
los 6 renderers L4 (`obsidian.py`, `notion_api.py`, `notion_md.py`,
`appflowy.py`, `markdown.py`, `html_pdf.py`) en lugar de sus dicts
`SEVERITY_TO_*` locales (drift-free).

Cierra el criterio 1 del ROADMAP §1438 ("cada intención tiene mapeo en los
cuatro destinos con estilo"), el criterio 2 ("un mismo tipo de advertencia
usa el mismo icono en todos" — cada `StyleMapping.icon` es canónico) y el
criterio 3 ("ninguna intención queda sin mapeo" — `KeyError` con sugerencia
si llega una severidad desconocida).

Carga implícita: `validate_table()` se ejecuta al import y verifica
20 entradas, Notion color ∈ lista cerrada, ningún campo vacío. Si la
verificación falla, `RuntimeError`.

Sin dependencias externas. Python 3.9+ stdlib puro.

CLI:
    python3 -m scripts.util.style_mapping --dump
    python3 -m scripts.util.style_mapping --resolve note
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from typing import Dict, FrozenSet, List, Optional, Tuple

NOTION_VALID_COLORS: FrozenSet[str] = frozenset({
    "default",
    "gray_background",
    "brown_background",
    "orange_background",
    "yellow_background",
    "green_background",
    "blue_background",
    "purple_background",
    "pink_background",
    "red_background",
})

CANONICAL_SEVERITIES: FrozenSet[str] = frozenset({
    "note", "tip", "info", "warning", "caution", "danger", "example",
    "question", "success", "failure", "bug", "quote", "abstract",
    "security", "performance", "version", "deprecated", "conflict",
    "external", "derived",
})


@dataclass(frozen=True)
class StyleMapping:
    severity: str
    semantic_token: str
    icon: str
    obsidian_callout: str
    notion_icon: str
    notion_color: str
    appflowy_callout: str
    html_css_class: str


_MAPPING: Tuple[StyleMapping, ...] = (
    StyleMapping("note",        "_neutral.quote",      "📝", "note",     "📝", "default",          "note",     "callout-note"),
    StyleMapping("tip",         "semantic.info",       "💡", "tip",      "💡", "green_background",  "info",     "callout-tip"),
    StyleMapping("info",        "semantic.info",       "ℹ️",  "info",     "ℹ️",  "blue_background",   "info",     "callout-info"),
    StyleMapping("warning",     "semantic.warning",    "⚠️", "warning",  "⚠️", "yellow_background", "warning",  "callout-warning"),
    StyleMapping("caution",     "semantic.warning",    "⚠️", "warning",  "⚠️", "orange_background", "warning",  "callout-warning"),
    StyleMapping("danger",      "semantic.danger",     "🚫", "danger",   "🚫", "red_background",    "danger",   "callout-danger"),
    StyleMapping("example",     "semantic.example",    "📋", "example",  "📋", "gray_background",   "info",     "callout-example"),
    StyleMapping("question",    "semantic.info",       "❓", "question", "❓", "purple_background", "question", "callout-question"),
    StyleMapping("success",     "semantic.success",    "✅", "success",  "✅", "green_background",  "success",  "callout-success"),
    StyleMapping("failure",     "semantic.danger",     "❌", "danger",   "❌", "red_background",    "danger",   "callout-danger"),
    StyleMapping("bug",         "semantic.danger",     "🐛", "danger",   "🐛", "red_background",    "danger",   "callout-danger"),
    StyleMapping("quote",       "_neutral.quote",      "💬", "quote",    "💬", "gray_background",   "info",     "callout-note"),
    StyleMapping("abstract",    "_neutral.quote",      "📑", "abstract", "📑", "gray_background",   "info",     "callout-note"),
    StyleMapping("security",    "semantic.security",   "🔒", "danger",   "🔒", "red_background",    "danger",   "callout-danger"),
    StyleMapping("performance", "semantic.performance","⚡", "warning",  "⚡", "orange_background", "warning",  "callout-warning"),
    StyleMapping("version",     "semantic.info",       "🏷️",  "info",    "🏷️",  "blue_background",   "info",     "callout-info"),
    StyleMapping("deprecated",  "semantic.deprecated", "⛔", "warning",  "⛔", "gray_background",   "warning",  "callout-warning"),
    StyleMapping("conflict",    "semantic.warning",    "⚠️", "warning",  "⚠️", "orange_background", "warning",  "callout-warning"),
    StyleMapping("external",    "_neutral.quote",      "🔗", "quote",    "🔗", "gray_background",   "info",     "callout-info"),
    StyleMapping("derived",     "_neutral.quote",      "✨", "quote",    "✨", "gray_background",   "info",     "callout-info"),
)

_BY_SEVERITY: Dict[str, StyleMapping] = {m.severity: m for m in _MAPPING}


def validate_table() -> None:
    """Valida la tabla al import. Lanza `RuntimeError` si la tabla está rota.

    Verificaciones:
      - 20 entradas.
      - Severidades únicas y todas ∈ `CANONICAL_SEVERITIES`.
      - Notion color ∈ `NOTION_VALID_COLORS` (10 valores aceptados).
      - Ningún campo de string vacío.
    """
    if len(_MAPPING) != 20:
        raise RuntimeError(
            f"style_mapping: se esperaban 20 entradas, hay {len(_MAPPING)}"
        )
    seen: set = set()
    for m in _MAPPING:
        if m.severity in seen:
            raise RuntimeError(f"style_mapping: severidad duplicada {m.severity!r}")
        seen.add(m.severity)
        if m.severity not in CANONICAL_SEVERITIES:
            raise RuntimeError(
                f"style_mapping: severidad {m.severity!r} no ∈ CANONICAL_SEVERITIES"
            )
        for field_name in (
            "semantic_token", "icon", "obsidian_callout",
            "notion_icon", "notion_color", "appflowy_callout", "html_css_class",
        ):
            value = getattr(m, field_name)
            if not isinstance(value, str) or not value:
                raise RuntimeError(
                    f"style_mapping: {m.severity}.{field_name} vacío o no-string"
                )
        if m.notion_color not in NOTION_VALID_COLORS:
            raise RuntimeError(
                f"style_mapping: {m.severity}.notion_color={m.notion_color!r} "
                f"no ∈ NOTION_VALID_COLORS"
            )


validate_table()


def _suggest(unknown: str) -> Optional[str]:
    """Sugiere la severidad canónica más cercana a `unknown` (distancia Levenshtein ≤ 2)."""
    if not isinstance(unknown, str):
        return None
    target = unknown.lower()
    best: Tuple[int, Optional[str]] = (3, None)
    for sev in CANONICAL_SEVERITIES:
        d = _levenshtein(target, sev, limit=2)
        if d is not None and d < best[0]:
            best = (d, sev)
            if d == 0:
                break
    return best[1]


def _levenshtein(a: str, b: str, limit: int) -> Optional[int]:
    """Levenshtein con early-exit si supera `limit`."""
    if a == b:
        return 0
    if abs(len(a) - len(b)) > limit:
        return None
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i] + [0] * len(b)
        row_min = i
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            row_min = min(row_min, cur[j])
        if row_min > limit:
            return None
        prev = cur
    return prev[-1]


def _resolve(severity: str) -> StyleMapping:
    if severity not in _BY_SEVERITY:
        suggestion = _suggest(severity)
        msg = f"style_mapping: severidad desconocida {severity!r}"
        if suggestion is not None:
            msg += f" (¿quizás {suggestion!r}?)"
        raise KeyError(msg)
    return _BY_SEVERITY[severity]


def icon_for(severity: str) -> str:
    """Devuelve el emoji canónico único para `severity` (criterio 2 ROADMAP)."""
    return _resolve(severity).icon


def obsidian_callout_for(severity: str) -> str:
    """Devuelve el tipo de callout nativo Obsidian 1.5+ para `severity`."""
    return _resolve(severity).obsidian_callout


def notion_callout_for(severity: str) -> Tuple[str, str]:
    """Devuelve `(icon, color)` para el callout de Notion API (2022-06-28)."""
    m = _resolve(severity)
    return (m.notion_icon, m.notion_color)


def appflowy_callout_for(severity: str) -> str:
    """Devuelve el tipo de callout nativo AppFlowy para `severity`."""
    return _resolve(severity).appflowy_callout


def html_css_class_for(severity: str) -> str:
    """Devuelve la clase CSS prefijo `callout-<severity>` para HTML/PDF."""
    return _resolve(severity).html_css_class


def semantic_token_for(severity: str) -> str:
    """Devuelve el nombre del token semántico o neutro en `tokens.json` para `severity`."""
    return _resolve(severity).semantic_token


def all_mappings() -> List[StyleMapping]:
    """Devuelve la tabla completa como lista de dataclasses (snapshot inmutable)."""
    return list(_MAPPING)


def _dump() -> str:
    return json.dumps(
        [asdict(m) for m in _MAPPING],
        indent=2,
        ensure_ascii=False,
    )


def _main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="scripts.util.style_mapping",
        description="Tabla canónica severidad → estilo por destino (F73).",
    )
    parser.add_argument(
        "--dump",
        action="store_true",
        help="Imprime la tabla canónica completa en JSON.",
    )
    parser.add_argument(
        "--resolve",
        metavar="SEVERITY",
        help="Resuelve una severidad a su StyleMapping (todos los campos).",
    )
    args = parser.parse_args(argv)

    if args.dump:
        print(_dump())
        return 0
    if args.resolve:
        try:
            m = _resolve(args.resolve)
        except KeyError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        print(json.dumps(asdict(m), indent=2, ensure_ascii=False))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
