"""Helper `## Cabecera` para los 7 destinos (F75).

Single source of truth: los 6 renderers L4 (`obsidian.py`, `notion_api.py`,
`notion_md.py`, `appflowy.py`, `markdown.py`, `html_pdf.py`) más el de
flashcards importan `emit_cabecera(frontmatter, *, dest, profile)` para
emitir el bloque que precede a `## TL;DR` en cada nota. La cabecera
contiene los 5 campos canónicos:

    1. Resumen            ← `summary`
    2. Procedencia        ← `source` + `source-type` + `source-anchor` + `source-url` + `retrieved`
    3. Versión            ← `product` + `product-version`
    4. Estado             ← `status`
    5. Tiempo de lectura  ← `reading-time-minutes`

Por destino:
  - obsidian / appflowy: callout nativo con los 5 campos como bullets
    (panel de propiedades nativo también visible — duplicación intencional).
  - notion_api: bloque `callout` Notion (icon=📋, color=default) con
    rich_text para los 5 campos.
  - notion_md / markdown: tabla GFM 2-col.
  - html_pdf: `<table class="cabecera">` integrable con la tabla
    `## Metadata` existente del F59.
  - flashcards: `""` (no se emite el bloque en anverso; el `summary` se
    devuelve por separado para hint en el reverso).

INV-14: este módulo no contiene literales de color. Los renderers
consumen tokens via `scripts/util/style_mapping.py` (F73) o via clases
CSS de `assets/notemartin.css` (F74).

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

# Orden canónico de los 5 campos de la cabecera (F75 §2.2).
CABECERA_FIELDS: Tuple[str, ...] = (
    "summary", "source", "product_version", "status", "reading_time_minutes",
)

# Etiquetas legibles por campo (i18n-pendiente; F11).
CABECERA_LABELS: Dict[str, str] = {
    "summary":              "Resumen",
    "source":               "Procedencia",
    "product_version":      "Versión",
    "status":               "Estado",
    "reading_time_minutes": "Tiempo de lectura",
}

# Destinos soportados.
SUPPORTED_DESTS: Tuple[str, ...] = (
    "obsidian", "notion_api", "notion_md", "appflowy", "markdown", "html_pdf", "flashcards",
)

STATUS_LABELS: Dict[str, str] = {
    "draft":     "Borrador",
    "published": "Publicado",
    "archived":  "Archivado",
}


def _procedencia_value(fm: Dict[str, Any]) -> str:
    """Compone el campo `Procedencia` desde `source` + `source-type` + `source-anchor` + `source-url` + `retrieved`."""
    parts: list = []
    src = fm.get("source", "")
    if src:
        parts.append(src)
    st = fm.get("source-type", "")
    if st:
        parts.append(f"({st})")
    sa = fm.get("source-anchor", "")
    if sa:
        parts.append(f"§{sa}")
    su = fm.get("source-url", "")
    if su:
        parts.append(su)
    rt = fm.get("retrieved", "")
    if rt:
        parts.append(f"recuperado {rt}")
    return " · ".join(parts) if parts else ""


def _version_value(fm: Dict[str, Any]) -> str:
    """Compone el campo `Versión` desde `product` + `product-version`."""
    product = fm.get("product", "")
    version = fm.get("product-version", "")
    if product and version:
        return f"{product} {version}"
    if product:
        return product
    if version:
        return version
    return ""


def _status_value(fm: Dict[str, Any]) -> str:
    """Compone el campo `Estado` con etiqueta humana + valor canónico."""
    status = fm.get("status", "")
    if not status:
        return ""
    label = STATUS_LABELS.get(status, status)
    return f"{label} ({status})"


def _reading_time_value(fm: Dict[str, Any]) -> str:
    """Compone el campo `Tiempo de lectura` con sufijo `min`."""
    rtm = fm.get("reading-time-minutes", "")
    if rtm == "" or rtm is None:
        return ""
    try:
        n = int(rtm)
    except (TypeError, ValueError):
        return str(rtm)
    return f"{n} min"


def _compute_field(field: str, fm: Dict[str, Any]) -> str:
    """Devuelve el valor computado del campo, listo para renderizar."""
    if field == "summary":
        return str(fm.get("summary", "") or "")
    if field == "source":
        return _procedencia_value(fm)
    if field == "product_version":
        return _version_value(fm)
    if field == "status":
        return _status_value(fm)
    if field == "reading_time_minutes":
        return _reading_time_value(fm)
    return ""


def compute_cabecera_rows(frontmatter: Dict[str, Any]) -> list:
    """Devuelve la lista `[(etiqueta, valor), ...]` con los 5 campos, omitiendo vacíos.

    Si todos los campos están vacíos, devuelve `[]` (los renderers deciden
    no emitir el bloque en ese caso).
    """
    fm = frontmatter or {}
    rows: list = []
    for field in CABECERA_FIELDS:
        value = _compute_field(field, fm)
        if value:
            rows.append((CABECERA_LABELS[field], value))
    return rows


def _emit_markdown_table(rows: list) -> str:
    """Emite la cabecera como tabla GFM 2-col (notion_md, markdown, html_pdf variante)."""
    if not rows:
        return ""
    lines: list = ["## Cabecera", "", "| Campo | Valor |", "| --- | --- |"]
    for label, value in rows:
        # Escapar pipes en value para no romper la tabla GFM.
        safe_value = str(value).replace("|", "\\|")
        lines.append(f"| **{label}** | {safe_value} |")
    lines.append("")
    return "\n".join(lines)


def _emit_obsidian_callout(rows: list) -> str:
    """Emite la cabecera como callout nativo de Obsidian con bullets."""
    if not rows:
        return ""
    lines: list = ['> [!info] **Cabecera**', ">"]
    for label, value in rows:
        lines.append(f"> **{label}**: {value}")
    lines.append(">")
    lines.append("")
    return "\n".join(lines)


def _emit_notion_api_callout(rows: list) -> Dict[str, Any]:
    """Emite la cabecera como bloque callout de la Notion API (2022-06-28).

    Devuelve un dict con la forma:
        {"type": "callout", "callout": {"icon": ..., "color": ..., "rich_text": [...]}}
    """
    if not rows:
        return {"type": "callout", "callout": {"icon": {"type": "emoji", "emoji": "📋"},
                                                  "color": "default", "rich_text": []}}
    rich_text: list = []
    for i, (label, value) in enumerate(rows):
        if i > 0:
            rich_text.append({"type": "text", "text": {"content": "\n"}})
        rich_text.append({"type": "text", "text": {"content": f"{label}: "},
                          "annotations": {"bold": True}})
        rich_text.append({"type": "text", "text": {"content": str(value)}})
    return {
        "type": "callout",
        "callout": {
            "icon": {"type": "emoji", "emoji": "📋"},
            "color": "default",
            "rich_text": rich_text,
        },
    }


def _emit_html_table(rows: list) -> str:
    """Emite la cabecera como tabla HTML integrable con la tabla `## Metadata` de F59."""
    if not rows:
        return ""
    lines: list = [
        '<table class="cabecera">',
        "  <thead><tr><th scope=\"col\">Campo</th><th scope=\"col\">Valor</th></tr></thead>",
        "  <tbody>",
    ]
    for label, value in rows:
        safe_value = (
            str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        lines.append(f"    <tr><th scope=\"row\">{label}</th><td>{safe_value}</td></tr>")
    lines.append("  </tbody>")
    lines.append("</table>")
    return "\n".join(lines)


def emit_cabecera(
    frontmatter: Dict[str, Any],
    *,
    dest: str,
    profile: Optional[Dict[str, Any]] = None,
) -> Any:
    """Emite el bloque `## Cabecera` para el destino dado.

    Args:
        frontmatter: dict de las 20 propiedades del frontmatter de la nota.
        dest: uno de `obsidian`, `notion_api`, `notion_md`, `appflowy`,
              `markdown`, `html_pdf`, `flashcards`.
        profile: opcional, dict del perfil del usuario (F11) para
                 densidad visual. Por ahora no se usa (F76 define las reglas
                 canónicas en `references/07-visual/density.md`; F76-FUERA
                 ajustará la cabecera al perfil de densidad).

    Returns:
        String Markdown/HTML (la mayoría de destinos), o dict con la
        forma de bloque Notion API (notion_api), o tupla `(anverso,
        reverso)` con strings vacíos para flashcards.
    """
    if dest not in SUPPORTED_DESTS:
        raise ValueError(
            f"_header.emit_cabecera: destino no soportado {dest!r}; "
            f"soportados: {sorted(SUPPORTED_DESTS)}"
        )
    rows = compute_cabecera_rows(frontmatter or {})
    if not rows:
        # Sin campos: el destino decide si emite algo (la mayoría no).
        if dest == "flashcards":
            return ("", "")
        if dest == "notion_api":
            return _emit_notion_api_callout([])
        return ""

    if dest in ("obsidian", "appflowy"):
        return _emit_obsidian_callout(rows)
    if dest == "notion_api":
        return _emit_notion_api_callout(rows)
    if dest in ("notion_md", "markdown"):
        return _emit_markdown_table(rows)
    if dest == "html_pdf":
        return _emit_html_table(rows)
    if dest == "flashcards":
        # Anverso: sin cabecera visible. Reverso: summary como hint.
        summary_hint = (frontmatter or {}).get("summary", "")
        return ("", str(summary_hint) if summary_hint else "")
    raise AssertionError(f"destino {dest!r} no manejado (bug en _header)")


def get_summary_hint(frontmatter: Dict[str, Any]) -> str:
    """Devuelve el `summary` como hint para el reverso de flashcards u otros consumidores."""
    return str((frontmatter or {}).get("summary", "") or "")


def validate_dest_coverage() -> None:
    """Valida que SUPPORTED_DESTS cubra exactamente los 7 destinos canónicos.

    Pensado para ejecutarse al import en tests / CI; raise si cambia la lista
    de destinos sin actualizar el helper.
    """
    expected = ("obsidian", "notion_api", "notion_md", "appflowy",
                "markdown", "html_pdf", "flashcards")
    if SUPPORTED_DESTS != expected:
        raise RuntimeError(
            f"_header: SUPPORTED_DESTS desactualizado: {sorted(SUPPORTED_DESTS)} vs {sorted(expected)}"
        )
