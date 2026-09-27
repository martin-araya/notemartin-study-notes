#!/usr/bin/env python3
"""make_figure.py — F70 · Generador de figuras de datos.

Renderiza figuras (bar, line, heatmap, confusion_matrix, distribution,
before_after) en SVG vectorial a partir de un JSON spec. La paleta Okabe-Ito
es colorblind-safe (verificada con ΔE CIEL76 ≥ 20 entre pares). Ejes
neutros (grises) que no compiten con las series. Soporta tema claro y
oscuro. Genera alt text automáticamente. Valida source_refs no vacío por
serie (INV-04).

Cubre los 3 criterios de la Fase 70:
- C1: toda figura se lee bien en tema claro y oscuro (ejes neutros,
  paleta Okabe-Ito, fondo transparente o sólido según destino).
- C2: la paleta pasa verificación de daltonismo (ΔE ≥ 20 entre colores
  adyacentes en orden de luminosidad).
- C3: toda serie tiene `source_refs` no vacío (regla F70-SR-01; exit 1 si falta).

Uso:
    python3 scripts/render/make_figure.py --input <spec.json>
                                         [--out-dir <dir>]
                                         [--theme {light,dark}]
                                         [--format {svg,png,both}]
                                         [--width N] [--height N]
                                         [--allow-missing-refs]
                                         [--json]
                                         [--fail-on {error,warning,info}]

Dependencias: Python 3.9+ stdlib puro (Pillow opcional para PNG).
Códigos de salida:
    0 — OK (todas las figuras generadas).
    1 — Alguna figura con violaciones ≥ `--fail-on`.
    2 — Error fatal (paths faltantes, JSON inválido).
"""

from __future__ import annotations

import argparse
import colorsys
import datetime as _dt
import hashlib
import importlib.util as _importlib_util
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Comparte atomic_write_json con F38+.
_IO_PATH = Path(__file__).resolve().parent.parent / "util" / "_io.py"
_spec = _importlib_util.spec_from_file_location("_skill_io", _IO_PATH)
_io_mod = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_io_mod)
_atomic_write_json = _io_mod.atomic_write_json
_atomic_write_text = _io_mod.atomic_write_text

# Design tokens (F72): consume desde assets/tokens.json. INV-14: este archivo
# no contiene literales de color.
_TOKENS_PATH = Path(__file__).resolve().parents[2] / "assets" / "tokens.json"
_tokens_spec = _importlib_util.spec_from_file_location(
    "_skill_tokens", Path(__file__).resolve().parent.parent / "util" / "tokens.py"
)
_tokens_mod = _importlib_util.module_from_spec(_tokens_spec)
_tokens_spec.loader.exec_module(_tokens_mod)
load_tokens = _tokens_mod.load_tokens
resolve_token = _tokens_mod.resolve_token
resolve_series = _tokens_mod.resolve_series
warn_if_unsupported_major = _tokens_mod.warn_if_unsupported_major

_TOKENS = load_tokens(_TOKENS_PATH)
warn_if_unsupported_major(_TOKENS["$version"])


EXIT_OK = 0
EXIT_PARTIAL = 1
EXIT_FATAL = 2

SCHEMA_VERSION = "1.0.0"
DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 500
DEFAULT_MARGIN_LEFT = 60
DEFAULT_MARGIN_BOTTOM = 60
DEFAULT_MARGIN_TOP = 50
DEFAULT_MARGIN_RIGHT = 30


# ---------------------------------------------------------------------------
# Paleta Okabe-Ito (F70 seed ratificado por F72; vive en tokens.json)
# ---------------------------------------------------------------------------


_OKABE_ITO_NAMES = (
    "okabe-ito-orange",
    "okabe-ito-sky-blue",
    "okabe-ito-bluish-green",
    "okabe-ito-yellow",
    "okabe-ito-blue",
    "okabe-ito-vermillion",
    "okabe-ito-reddish-purple",
    "okabe-ito-black",
)


def _okabe_ito_palette(theme: str) -> Dict[str, str]:
    """Devuelve la paleta Okabe-Ito resuelta desde tokens.json para `theme`.

    La inversión light↔dark de `okabe-ito-black` (negro en light, blanco en
    dark) está modelada en tokens.json `series.okabe-ito-black.{light,dark}`
    y la aplica automáticamente `resolve_series`.
    """
    return {name: resolve_series(_TOKENS, name, theme) for name in _OKABE_ITO_NAMES}


def palette_for_theme(palette: Dict[str, str], theme: str) -> Dict[str, str]:
    """Devuelve la paleta adaptada al tema (light/dark).

    Mantiene la firma histórica (recibe `palette`) para no romper consumidores
    externos, pero ignora el argumento y reconstruye desde tokens. Conservar el
    parámetro es deliberado: documenta que el adaptador es por-tema, no
    por-paleta.
    """
    return _okabe_ito_palette(theme)


def get_neutral(theme: str) -> Dict[str, str]:
    """Devuelve el dict de ejes neutros (axisLine, gridline, textAxis, etc.) para `theme`.

    Lee desde `tokens.json["series"]["axisLight"|"axisDark"]`. Los nombres
    históricos (snake_case) se preservan en la salida para no tocar los
    consumidores (`neutral["axis_line"]`, etc.).
    """
    bucket = "axisDark" if theme == "dark" else "axisLight"
    src = resolve_token(_TOKENS, "series", bucket)
    return {
        "axis_line":  src["axisLine"],
        "gridline":   src["gridline"],
        "text_axis":  src["textAxis"],
        "title":      src["title"],
        "subtitle":   src["subtitle"],
        "background": src["background"],
    }


# ---------------------------------------------------------------------------
# Verificación de daltonismo (ΔE CIEL76)
# ---------------------------------------------------------------------------


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    h = hex_str.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def rgb_to_xyz(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """RGB (0-255) → XYZ (D65)."""
    def linearize(c: int) -> float:
        cs = c / 255.0
        return cs / 12.92 if cs <= 0.04045 else ((cs + 0.055) / 1.055) ** 2.4

    rl, gl, bl = linearize(r), linearize(g), linearize(b)
    # sRGB D65 matrix
    x = rl * 0.4124564 + gl * 0.3575761 + bl * 0.1804375
    y = rl * 0.2126729 + gl * 0.7151522 + bl * 0.0721750
    z = rl * 0.0193339 + gl * 0.1191920 + bl * 0.9503041
    return (x, y, z)


def xyz_to_lab(x: float, y: float, z: float) -> Tuple[float, float, float]:
    """XYZ → CIE L*a*b* (D65 white point)."""
    # D65 reference white
    xn, yn, zn = 0.95047, 1.0, 1.08883

    def f(t: float) -> float:
        return t / (3 * (6 / 29) ** 3) if t <= (6 / 29) ** 3 else t ** (1 / 3)

    fx, fy, fz = f(x / xn), f(y / yn), f(z / zn)
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)
    return (L, a, b)


def hex_to_lab(hex_str: str) -> Tuple[float, float, float]:
    r, g, b = hex_to_rgb(hex_str)
    return xyz_to_lab(*rgb_to_xyz(r, g, b))


def delta_e_cie76(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float]) -> float:
    """ΔE CIE76 (distancia euclídea en L*a*b*)."""
    return ((lab1[0] - lab2[0]) ** 2 + (lab1[1] - lab2[1]) ** 2 + (lab1[2] - lab2[2]) ** 2) ** 0.5


def verify_palette_colorblind_safe(
    palette: Dict[str, str],
    min_delta_e: float = 20.0,
) -> Dict[str, Any]:
    """Verifica que la paleta es colorblind-safe con ΔE ≥ min_delta_e entre pares.

    Ordena los colores por luminancia (L*) y verifica que pares adyacentes
    tengan ΔE ≥ min_delta_e.
    """
    items = [(name, hex_to_lab(hex_str)) for name, hex_str in palette.items()]
    items.sort(key=lambda x: x[1][0])  # por L*

    pairs = []
    for i in range(len(items) - 1):
        name1, lab1 = items[i]
        name2, lab2 = items[i + 1]
        de = delta_e_cie76(lab1, lab2)
        pairs.append({
            "pair": (name1, name2),
            "delta_e": round(de, 2),
        })

    min_de = min((p["delta_e"] for p in pairs), default=0.0)
    safe = min_de >= min_delta_e
    closest = min(pairs, key=lambda p: p["delta_e"]) if pairs else None

    return {
        "safe": safe,
        "min_delta_e": round(min_de, 2),
        "min_delta_e_threshold": min_delta_e,
        "closest_pair": closest,
        "all_pairs": pairs,
    }


# ---------------------------------------------------------------------------
# Modelo
# ---------------------------------------------------------------------------


@dataclass
class DataPoint:
    category: str
    value: float
    source_ref: str = ""


@dataclass
class Series:
    name: str
    color_token: str
    source_refs: List[str]
    data: List[DataPoint]
    color_hex: str = ""


@dataclass
class FigureSpec:
    schema_version: str
    figure_type: str  # bar, line, heatmap, confusion_matrix, distribution, before_after
    title: str
    theme: str  # light, dark
    x_axis_label: str = ""
    y_axis_label: str = ""
    series: List[Series] = field(default_factory=list)
    alt_text: str = ""
    reading_phrase: str = ""


@dataclass
class Degradation:
    rule_id: str
    severity: str
    message: str
    fix_hint: str = ""
    series_name: str = ""


@dataclass
class FigureManifest:
    schema_version: str = SCHEMA_VERSION
    generated_at: str = ""
    input_path: str = ""
    ir_sha256: str = ""
    figure_type: str = ""
    title: str = ""
    theme: str = "light"
    format: str = "svg"
    output_svg_path: Optional[str] = None
    output_png_path: Optional[str] = None
    alt_text: str = ""
    reading_phrase: str = ""
    series: List[Dict[str, Any]] = field(default_factory=list)
    dimensions: Dict[str, int] = field(default_factory=dict)
    palette_used: str = "okabe-ito"
    palette_colorblind_safe: bool = False
    palette_min_delta_e: float = 0.0
    source_refs_total: int = 0
    errors: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# JSON spec parsing
# ---------------------------------------------------------------------------


def parse_figure_spec(data: Dict[str, Any]) -> Tuple[Optional[FigureSpec], List[Degradation]]:
    """Parsea un JSON spec y devuelve (FigureSpec, degradations)."""
    degradations: List[Degradation] = []

    schema_version = data.get("schema_version", "")
    if schema_version and schema_version != SCHEMA_VERSION:
        degradations.append(Degradation(
            rule_id="F70-SPEC-01",
            severity="warning",
            message=f"schema_version '{schema_version}' != '{SCHEMA_VERSION}' (asumida compatibilidad)",
            fix_hint="Actualizar a la última versión",
        ))

    figure_type = data.get("figure_type", "")
    if figure_type not in ("bar", "line", "heatmap", "confusion_matrix", "distribution", "before_after"):
        degradations.append(Degradation(
            rule_id="F70-SPEC-02",
            severity="error",
            message=f"figure_type '{figure_type}' no soportado",
            fix_hint="Usar uno de: bar, line, heatmap, confusion_matrix, distribution, before_after",
        ))
        return (None, degradations)

    title = data.get("title", "")
    if not title:
        degradations.append(Degradation(
            rule_id="F70-SPEC-03",
            severity="warning",
            message="title vacío",
            fix_hint="Añadir un título descriptivo",
        ))

    theme = data.get("theme", "light")
    if theme not in ("light", "dark"):
        degradations.append(Degradation(
            rule_id="F70-SPEC-04",
            severity="warning",
            message=f"theme '{theme}' no soportado, usando 'light'",
            fix_hint="Usar 'light' o 'dark'",
        ))
        theme = "light"

    alt_text = data.get("alt_text", "")
    if not alt_text:
        alt_text = generate_alt_text(figure_type, title, data.get("series", []))

    reading_phrase = data.get("reading_phrase", "")
    if not reading_phrase:
        degradations.append(Degradation(
            rule_id="F70-SPEC-05",
            severity="error",
            message="reading_phrase vacío",
            fix_hint="Añadir una frase de lectura guiada al spec",
        ))

    series_list: List[Series] = []
    for s_idx, s in enumerate(data.get("series", [])):
        color_token = s.get("color_token", "")
        source_refs = s.get("source_refs", [])

        if not source_refs:
            degradations.append(Degradation(
                rule_id="F70-SR-01",
                severity="error",
                message=f"Serie {s_idx} '{s.get('name', '?')}' sin source_refs",
                series_name=s.get("name", "?"),
                fix_hint="Añadir source_refs con los IDs de bloque del SDM",
            ))

        color_hex = _okabe_ito_palette(theme).get(color_token) or resolve_series(_TOKENS, "okabe-ito-blue", theme)

        data_points = [
            DataPoint(
                category=dp.get("category", ""),
                value=float(dp.get("value", 0.0)),
                source_ref=dp.get("source_ref", ""),
            )
            for dp in s.get("data", [])
        ]
        series_list.append(Series(
            name=s.get("name", ""),
            color_token=color_token,
            source_refs=source_refs,
            data=data_points,
            color_hex=color_hex,
        ))

    spec = FigureSpec(
        schema_version=schema_version or SCHEMA_VERSION,
        figure_type=figure_type,
        title=title,
        theme=theme,
        x_axis_label=data.get("x_axis_label", ""),
        y_axis_label=data.get("y_axis_label", ""),
        series=series_list,
        alt_text=alt_text,
        reading_phrase=reading_phrase,
    )
    return (spec, degradations)


def generate_alt_text(figure_type: str, title: str, series: List[Dict[str, Any]]) -> str:
    """Genera alt text automáticamente según el tipo de figura."""
    n_series = len(series)
    series_names = [s.get("name", "?") for s in series]
    if figure_type == "bar":
        names = ", ".join(series_names[:3])
        if n_series > 3:
            names += f" y {n_series - 3} más"
        return f"Gráfico de barras titulado '{title}' con {n_series} series: {names}."
    elif figure_type == "line":
        return f"Gráfico de líneas titulado '{title}' con {n_series} series."
    elif figure_type == "heatmap":
        return f"Heatmap titulado '{title}'."
    elif figure_type == "confusion_matrix":
        return f"Matriz de confusión titulada '{title}'."
    elif figure_type == "distribution":
        return f"Distribución titulada '{title}'."
    elif figure_type == "before_after":
        return f"Comparación antes/después titulada '{title}' con {n_series} categorías."
    return f"Figura '{title}'."


# ---------------------------------------------------------------------------
# SVG builders
# ---------------------------------------------------------------------------


def _svg_header(width: int, height: int, theme: str) -> str:
    bg = get_neutral(theme)["background"]
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" style="background:{bg};font-family:system-ui,-apple-system,sans-serif">\n'
    )


def _svg_footer() -> str:
    return "</svg>\n"


def _draw_axes(width: int, height: int, theme: str,
               ml: int = DEFAULT_MARGIN_LEFT, mb: int = DEFAULT_MARGIN_BOTTOM,
               mt: int = DEFAULT_MARGIN_TOP, mr: int = DEFAULT_MARGIN_RIGHT) -> str:
    neutral = get_neutral(theme)
    x0, y0 = ml, height - mb
    x1, y1 = width - mr, mt
    return (
        f'  <line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="{neutral["axis_line"]}" stroke-width="1"/>\n'
        f'  <line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="{neutral["axis_line"]}" stroke-width="1"/>\n'
    )


def _draw_title(title: str, width: int, theme: str) -> str:
    if not title:
        return ""
    neutral = get_neutral(theme)
    x = width / 2
    return f'  <text x="{x}" y="20" text-anchor="middle" fill="{neutral["title"]}" font-size="16" font-weight="bold">{_xml_escape(title)}</text>\n'


def _draw_axis_labels(spec: FigureSpec, width: int, height: int) -> str:
    neutral = get_neutral(spec.theme)
    out = []
    if spec.x_axis_label:
        x = (width + DEFAULT_MARGIN_LEFT - DEFAULT_MARGIN_RIGHT) / 2
        y = height - 15
        out.append(f'  <text x="{x}" y="{y}" text-anchor="middle" fill="{neutral["text_axis"]}" font-size="12">{_xml_escape(spec.x_axis_label)}</text>\n')
    if spec.y_axis_label:
        x = 15
        y = (height + DEFAULT_MARGIN_TOP - DEFAULT_MARGIN_BOTTOM) / 2
        out.append(f'  <text x="{x}" y="{y}" text-anchor="middle" fill="{neutral["text_axis"]}" font-size="12" transform="rotate(-90 {x} {y})">{_xml_escape(spec.y_axis_label)}</text>\n')
    return "".join(out)


def _draw_legend(spec: FigureSpec, palette: Dict[str, str], width: int) -> str:
    if not spec.series:
        return ""
    neutral = get_neutral(spec.theme)
    out = ['  <g transform="translate(60, 35)">\n']
    x = 0
    for i, s in enumerate(spec.series):
        if i > 0:
            x += 110
        color = palette.get(s.color_token, s.color_hex)
        out.append(f'    <rect x="{x}" y="0" width="12" height="12" fill="{color}"/>\n')
        out.append(f'    <text x="{x + 18}" y="11" fill="{neutral["text_axis"]}" font-size="11">{_xml_escape(s.name)}</text>\n')
    out.append("  </g>\n")
    return "".join(out)


def _xml_escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&apos;"))


def _categories(spec: FigureSpec) -> List[str]:
    """Devuelve las categorías únicas en orden de aparición."""
    seen: List[str] = []
    for s in spec.series:
        for dp in s.data:
            if dp.category and dp.category not in seen:
                seen.append(dp.category)
    return seen


def _max_value(spec: FigureSpec) -> float:
    """Valor máximo entre todas las series (para escalar ejes)."""
    m = 0.0
    for s in spec.series:
        for dp in s.data:
            m = max(m, dp.value)
    return m if m > 0 else 1.0


def build_bar_chart(spec: FigureSpec, width: int, height: int, palette: Dict[str, str]) -> str:
    """Barras verticales agrupadas."""
    out = [_svg_header(width, height, spec.theme)]
    out.append(_draw_title(spec.title, width, spec.theme))
    out.append(_draw_legend(spec, palette, width))
    out.append(_draw_axes(width, height, spec.theme))
    out.append(_draw_axis_labels(spec, width, height))

    cats = _categories(spec)
    n_series = len(spec.series)
    n_cats = len(cats)
    if n_cats == 0 or n_series == 0:
        return "".join(out) + _svg_footer()

    plot_w = width - DEFAULT_MARGIN_LEFT - DEFAULT_MARGIN_RIGHT
    plot_h = height - DEFAULT_MARGIN_TOP - DEFAULT_MARGIN_BOTTOM
    group_w = plot_w / n_cats
    bar_w = group_w / (n_series + 1)

    max_v = _max_value(spec)
    neutral = get_neutral(spec.theme)

    for ci, cat in enumerate(cats):
        for si, s in enumerate(spec.series):
            dp = next((d for d in s.data if d.category == cat), None)
            if dp is None:
                continue
            color = palette.get(s.color_token, s.color_hex)
            x = DEFAULT_MARGIN_LEFT + ci * group_w + si * bar_w + bar_w * 0.1
            h = (dp.value / max_v) * plot_h
            y = height - DEFAULT_MARGIN_BOTTOM - h
            out.append(f'  <rect x="{x:.1f}" y="{y:.1f}" width="{bar_w * 0.8:.1f}" height="{h:.1f}" fill="{color}">\n')
            out.append(f'    <title>{_xml_escape(s.name)} en {_xml_escape(cat)}: {dp.value}</title>\n')
            out.append('  </rect>\n')

    # Etiquetas X
    for ci, cat in enumerate(cats):
        x = DEFAULT_MARGIN_LEFT + ci * group_w + group_w / 2
        y = height - DEFAULT_MARGIN_BOTTOM + 15
        out.append(f'  <text x="{x:.1f}" y="{y}" text-anchor="middle" fill="{neutral["text_axis"]}" font-size="10">{_xml_escape(cat)}</text>\n')

    return "".join(out) + _svg_footer()


def build_line_chart(spec: FigureSpec, width: int, height: int, palette: Dict[str, str]) -> str:
    out = [_svg_header(width, height, spec.theme)]
    out.append(_draw_title(spec.title, width, spec.theme))
    out.append(_draw_legend(spec, palette, width))
    out.append(_draw_axes(width, height, spec.theme))
    out.append(_draw_axis_labels(spec, width, height))

    cats = _categories(spec)
    if len(cats) < 2 or not spec.series:
        return "".join(out) + _svg_footer()

    plot_w = width - DEFAULT_MARGIN_LEFT - DEFAULT_MARGIN_RIGHT
    plot_h = height - DEFAULT_MARGIN_TOP - DEFAULT_MARGIN_BOTTOM
    max_v = _max_value(spec)
    neutral = get_neutral(spec.theme)

    for s in spec.series:
        if not s.data:
            continue
        color = palette.get(s.color_token, s.color_hex)
        points = []
        for ci, cat in enumerate(cats):
            dp = next((d for d in s.data if d.category == cat), None)
            if dp is None:
                continue
            x = DEFAULT_MARGIN_LEFT + (ci / max(1, len(cats) - 1)) * plot_w
            y = height - DEFAULT_MARGIN_BOTTOM - (dp.value / max_v) * plot_h
            points.append((x, y, cat, dp.value))
        if points:
            path_d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y, _, _ in points)
            out.append(f'  <path d="{path_d}" stroke="{color}" stroke-width="2" fill="none"/>\n')
            for x, y, cat, val in points:
                out.append(f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}">\n')
                out.append(f'    <title>{_xml_escape(s.name)} en {_xml_escape(cat)}: {val}</title>\n')
                out.append('  </circle>\n')

    for ci, cat in enumerate(cats):
        x = DEFAULT_MARGIN_LEFT + (ci / max(1, len(cats) - 1)) * plot_w
        y = height - DEFAULT_MARGIN_BOTTOM + 15
        out.append(f'  <text x="{x:.1f}" y="{y}" text-anchor="middle" fill="{neutral["text_axis"]}" font-size="10">{_xml_escape(cat)}</text>\n')

    return "".join(out) + _svg_footer()


def build_heatmap(spec: FigureSpec, width: int, height: int, palette: Dict[str, str]) -> str:
    """Heatmap: una sola serie con rows/cols."""
    out = [_svg_header(width, height, spec.theme)]
    out.append(_draw_title(spec.title, width, spec.theme))
    out.append(_draw_legend(spec, palette, width))

    if not spec.series or not spec.series[0].data:
        return "".join(out) + _svg_footer()

    series = spec.series[0]
    cats = _categories(spec)
    n_cats = len(cats)
    if n_cats == 0:
        return "".join(out) + _svg_footer()

    plot_w = width - DEFAULT_MARGIN_LEFT - DEFAULT_MARGIN_RIGHT - 80
    plot_h = height - DEFAULT_MARGIN_TOP - DEFAULT_MARGIN_BOTTOM - 20
    cell_w = plot_w / n_cats
    cell_h = plot_h / n_cats

    max_v = max((dp.value for dp in series.data), default=1.0)
    if max_v == 0:
        max_v = 1.0

    color_token = series.color_token or "okabe-ito-blue"
    base_color = palette.get(color_token) or resolve_series(_TOKENS, "okabe-ito-blue", spec.theme)
    neutral = get_neutral(spec.theme)

    for ci, cat in enumerate(cats):
        dp = next((d for d in series.data if d.category == cat), None)
        if dp is None:
            continue
        # Mezclar con blanco/negro según luminosidad del base
        intensity = dp.value / max_v
        fill = _interpolate_color(base_color, neutral["background"], intensity)
        x = DEFAULT_MARGIN_LEFT + 60 + ci * cell_w
        y = DEFAULT_MARGIN_TOP + 20 + ci * cell_h
        out.append(f'  <rect x="{x:.1f}" y="{y:.1f}" width="{cell_w:.1f}" height="{cell_h:.1f}" fill="{fill}" stroke="{neutral["gridline"]}">\n')
        out.append(f'    <title>{_xml_escape(cat)}: {dp.value}</title>\n')
        out.append('  </rect>\n')
        # Etiquetas de fila/columna
        out.append(f'  <text x="{x + cell_w / 2:.1f}" y="{y - 4:.1f}" text-anchor="middle" fill="{neutral["text_axis"]}" font-size="9">{_xml_escape(cat)}</text>\n')
        out.append(f'  <text x="{x - 4:.1f}" y="{y + cell_h / 2:.1f}" text-anchor="end" fill="{neutral["text_axis"]}" font-size="9">{_xml_escape(cat)}</text>\n')

    return "".join(out) + _svg_footer()


def build_confusion_matrix(spec: FigureSpec, width: int, height: int, palette: Dict[str, str]) -> str:
    """Matriz de confusión: una serie con categorías TP/FP/FN/TN."""
    out = [_svg_header(width, height, spec.theme)]
    out.append(_draw_title(spec.title, width, spec.theme))

    if not spec.series or not spec.series[0].data:
        return "".join(out) + _svg_footer()

    series = spec.series[0]
    cats = _categories(spec)
    n = len(cats)
    if n == 0:
        return "".join(out) + _svg_footer()

    plot_w = width - DEFAULT_MARGIN_LEFT - DEFAULT_MARGIN_RIGHT
    plot_h = height - DEFAULT_MARGIN_TOP - DEFAULT_MARGIN_BOTTOM - 20
    cell_w = plot_w / n
    cell_h = plot_h / n

    max_v = max((dp.value for dp in series.data), default=1.0)
    if max_v == 0:
        max_v = 1.0
    color_token = series.color_token or "okabe-ito-blue"
    base_color = palette.get(color_token) or resolve_series(_TOKENS, "okabe-ito-blue", spec.theme)
    neutral = get_neutral(spec.theme)

    for ri, row_cat in enumerate(cats):
        for ci, col_cat in enumerate(cats):
            dp = next((d for d in series.data if d.category == f"{row_cat},{col_cat}" or d.category == f"{row_cat}|{col_cat}"), None)
            if dp is None:
                # Buscar por combinación
                for d in series.data:
                    if d.category.startswith(f"{row_cat},") or d.category.startswith(f"{row_cat}|"):
                        parts = re.split(r"[,|]", d.category, maxsplit=1)
                        if len(parts) == 2 and parts[1] == col_cat:
                            dp = d
                            break
            if dp is None:
                continue
            intensity = dp.value / max_v
            fill = _interpolate_color(base_color, neutral["background"], intensity)
            x = DEFAULT_MARGIN_LEFT + ci * cell_w
            y = DEFAULT_MARGIN_TOP + 20 + ri * cell_h
            out.append(f'  <rect x="{x:.1f}" y="{y:.1f}" width="{cell_w:.1f}" height="{cell_h:.1f}" fill="{fill}" stroke="{neutral["gridline"]}">\n')
            out.append(f'    <title>{_xml_escape(row_cat)}/{_xml_escape(col_cat)}: {dp.value}</title>\n')
            out.append('  </rect>\n')
            # Etiqueta central
            cx = x + cell_w / 2
            cy = y + cell_h / 2
            text_color = resolve_token(_TOKENS, "_neutral", "background", "light") if intensity > 0.5 else neutral["text_axis"]
            out.append(f'  <text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" fill="{text_color}" font-size="11" dominant-baseline="middle">{dp.value}</text>\n')
            # Etiquetas de fila/columna
            if ri == 0:
                out.append(f'  <text x="{cx:.1f}" y="{y - 4:.1f}" text-anchor="middle" fill="{neutral["text_axis"]}" font-size="9">{_xml_escape(col_cat)}</text>\n')
            if ci == 0:
                out.append(f'  <text x="{x - 4:.1f}" y="{cy:.1f}" text-anchor="end" fill="{neutral["text_axis"]}" font-size="9">{_xml_escape(row_cat)}</text>\n')

    return "".join(out) + _svg_footer()


def build_distribution(spec: FigureSpec, width: int, height: int, palette: Dict[str, str]) -> str:
    """Histograma: una sola serie, bins en X, frecuencia en Y."""
    out = [_svg_header(width, height, spec.theme)]
    out.append(_draw_title(spec.title, width, spec.theme))
    out.append(_draw_legend(spec, palette, width))
    out.append(_draw_axes(width, height, spec.theme))
    out.append(_draw_axis_labels(spec, width, height))

    if not spec.series or not spec.series[0].data:
        return "".join(out) + _svg_footer()

    series = spec.series[0]
    color = palette.get(series.color_token, series.color_hex)
    neutral = get_neutral(spec.theme)
    cats = _categories(spec)
    n_bins = len(cats)
    if n_bins == 0:
        return "".join(out) + _svg_footer()

    plot_w = width - DEFAULT_MARGIN_LEFT - DEFAULT_MARGIN_RIGHT
    plot_h = height - DEFAULT_MARGIN_TOP - DEFAULT_MARGIN_BOTTOM
    bin_w = plot_w / n_bins
    max_v = _max_value(spec)

    for ci, cat in enumerate(cats):
        dp = next((d for d in series.data if d.category == cat), None)
        if dp is None:
            continue
        h = (dp.value / max_v) * plot_h
        x = DEFAULT_MARGIN_LEFT + ci * bin_w
        y = height - DEFAULT_MARGIN_BOTTOM - h
        out.append(f'  <rect x="{x:.1f}" y="{y:.1f}" width="{bin_w:.1f}" height="{h:.1f}" fill="{color}">\n')
        out.append(f'    <title>{_xml_escape(cat)}: {dp.value}</title>\n')
        out.append('  </rect>\n')
        out.append(f'  <text x="{x + bin_w / 2:.1f}" y="{height - DEFAULT_MARGIN_BOTTOM + 15}" text-anchor="middle" fill="{neutral["text_axis"]}" font-size="9">{_xml_escape(cat)}</text>\n')

    return "".join(out) + _svg_footer()


def build_before_after(spec: FigureSpec, width: int, height: int, palette: Dict[str, str]) -> str:
    """Dumbbell: dos puntos conectados por línea, una serie 'before' y otra 'after'."""
    out = [_svg_header(width, height, spec.theme)]
    out.append(_draw_title(spec.title, width, spec.theme))
    out.append(_draw_legend(spec, palette, width))
    out.append(_draw_axes(width, height, spec.theme))
    out.append(_draw_axis_labels(spec, width, height))

    if len(spec.series) < 2:
        return "".join(out) + _svg_footer()

    cats = _categories(spec)
    if len(cats) == 0:
        return "".join(out) + _svg_footer()

    series_a, series_b = spec.series[0], spec.series[1]
    color_a = palette.get(series_a.color_token, series_a.color_hex)
    color_b = palette.get(series_b.color_token, series_b.color_hex)
    neutral = get_neutral(spec.theme)

    plot_w = width - DEFAULT_MARGIN_LEFT - DEFAULT_MARGIN_RIGHT
    plot_h = height - DEFAULT_MARGIN_TOP - DEFAULT_MARGIN_BOTTOM
    max_v = _max_value(spec)

    for ci, cat in enumerate(cats):
        dp_a = next((d for d in series_a.data if d.category == cat), None)
        dp_b = next((d for d in series_b.data if d.category == cat), None)
        if dp_a is None or dp_b is None:
            continue
        # Posiciones X ligeramente desplazadas
        x_a = DEFAULT_MARGIN_LEFT + (ci + 0.4) / len(cats) * plot_w
        x_b = DEFAULT_MARGIN_LEFT + (ci + 0.6) / len(cats) * plot_w
        y_a = height - DEFAULT_MARGIN_BOTTOM - (dp_a.value / max_v) * plot_h
        y_b = height - DEFAULT_MARGIN_BOTTOM - (dp_b.value / max_v) * plot_h
        # Línea conectando
        out.append(f'  <line x1="{x_a:.1f}" y1="{y_a:.1f}" x2="{x_b:.1f}" y2="{y_b:.1f}" stroke="{neutral["axis_line"]}" stroke-width="1"/>\n')
        # Puntos
        out.append(f'  <circle cx="{x_a:.1f}" cy="{y_a:.1f}" r="5" fill="{color_a}">\n')
        out.append(f'    <title>{_xml_escape(series_a.name)}: {dp_a.value}</title>\n')
        out.append('  </circle>\n')
        out.append(f'  <circle cx="{x_b:.1f}" cy="{y_b:.1f}" r="5" fill="{color_b}">\n')
        out.append(f'    <title>{_xml_escape(series_b.name)}: {dp_b.value}</title>\n')
        out.append('  </circle>\n')
        # Etiqueta de categoría
        x_label = DEFAULT_MARGIN_LEFT + (ci + 0.5) / len(cats) * plot_w
        out.append(f'  <text x="{x_label:.1f}" y="{height - DEFAULT_MARGIN_BOTTOM + 15}" text-anchor="middle" fill="{neutral["text_axis"]}" font-size="10">{_xml_escape(cat)}</text>\n')

    return "".join(out) + _svg_footer()


def _interpolate_color(hex1: str, hex2: str, t: float) -> str:
    """Interpola entre dos colores hex en espacio RGB."""
    r1, g1, b1 = hex_to_rgb(hex1)
    r2, g2, b2 = hex_to_rgb(hex2)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


BUILDERS = {
    "bar": build_bar_chart,
    "line": build_line_chart,
    "heatmap": build_heatmap,
    "confusion_matrix": build_confusion_matrix,
    "distribution": build_distribution,
    "before_after": build_before_after,
}


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------


def render_figure(
    spec: FigureSpec,
    width: int,
    height: int,
    palette_name: str,
) -> Tuple[str, Dict[str, Any]]:
    """Renderiza la figura a SVG y devuelve (svg_string, palette_check)."""
    palette = palette_for_theme({}, spec.theme)
    builder = BUILDERS[spec.figure_type]
    svg = builder(spec, width, height, palette)

    palette_check = verify_palette_colorblind_safe(palette)
    return svg, palette_check


def build_manifest(
    spec: FigureSpec,
    input_path: Path,
    palette_check: Dict[str, Any],
    svg_path: Optional[Path],
    png_path: Optional[Path],
    width: int,
    height: int,
    ir_sha256: str,
) -> FigureManifest:
    palette_name = "okabe-ito"
    series_meta = []
    source_refs_total = 0
    for s in spec.series:
        series_meta.append({
            "name": s.name,
            "color_token": s.color_token,
            "color_hex": s.color_hex,
            "source_refs": s.source_refs,
            "data_points": len(s.data),
        })
        source_refs_total += len(s.source_refs)
    return FigureManifest(
        schema_version=SCHEMA_VERSION,
        generated_at=_dt.datetime.now(_dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        input_path=str(input_path),
        ir_sha256=ir_sha256,
        figure_type=spec.figure_type,
        title=spec.title,
        theme=spec.theme,
        format="svg",
        output_svg_path=str(svg_path.relative_to(svg_path.parent.parent)) if svg_path else None,
        output_png_path=str(png_path.relative_to(png_path.parent.parent)) if png_path else None,
        alt_text=spec.alt_text,
        reading_phrase=spec.reading_phrase,
        series=series_meta,
        dimensions={"width": width, "height": height},
        palette_used=palette_name,
        palette_colorblind_safe=palette_check["safe"],
        palette_min_delta_e=palette_check["min_delta_e"],
        source_refs_total=source_refs_total,
    )


def process_file(
    input_path: Path,
    out_dir: Path,
    width: int,
    height: int,
    allow_missing_refs: bool,
) -> Tuple[FigureManifest, List[Degradation]]:
    text = input_path.read_text(encoding="utf-8")
    data = json.loads(text)
    ir_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()

    spec, degradations = parse_figure_spec(data)

    if spec is None:
        return (None, degradations)  # type: ignore[arg-type]

    if any(d.severity == "error" and d.rule_id == "F70-SR-01" for d in degradations) and not allow_missing_refs:
        return (None, degradations)  # type: ignore[arg-type]

    svg, palette_check = render_figure(spec, width, height, "okabe-ito")

    if not palette_check["safe"]:
        degradations.append(Degradation(
            rule_id="F70-CB-01",
            severity="warning",
            message=f"Paleta no pasa daltonismo: ΔE mínimo {palette_check['min_delta_e']:.1f} < 20",
            fix_hint="Revisar la paleta: pares más cercanos podrían confundirse",
        ))

    out_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^A-Za-z0-9._-]", "_", input_path.stem)
    svg_path = out_dir / f"{slug}.svg"
    _atomic_write_text(svg_path, svg)

    manifest = build_manifest(
        spec=spec,
        input_path=input_path,
        palette_check=palette_check,
        svg_path=svg_path,
        png_path=None,
        width=width,
        height=height,
        ir_sha256=ir_sha256,
    )

    manifest_path = out_dir / f"{slug}.manifest.json"
    _atomic_write_json(manifest_path, asdict(manifest))

    return (manifest, degradations)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}


def severity_at_least(sev: str, threshold: str) -> bool:
    return SEVERITY_ORDER[sev] <= SEVERITY_ORDER[threshold]


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="make_figure.py",
        description="F70 — Generador de figuras de datos.",
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--input", type=Path, help="Spec JSON único.")
    src.add_argument("--input-dir", type=Path, help="Directorio con varios specs JSON.")
    p.add_argument("--out-dir", type=Path, default=Path("render/figures"), help="Directorio de salida.")
    p.add_argument("--theme", choices=["light", "dark"], default="light", help="Tema (default: light).")
    p.add_argument("--format", choices=["svg", "png", "both"], dest="format_", default="svg", help="Formato (default: svg).")
    p.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    p.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    p.add_argument("--allow-missing-refs", action="store_true", help="No abortar si source_refs falta (modo draft).")
    p.add_argument("--fail-on", choices=["error", "warning", "info"], default="error")
    p.add_argument("--json", action="store_true", help="Salida solo JSON.")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    files: List[Path] = []
    if args.input:
        if not args.input.exists():
            print(f"ERROR: --input no encontrado: {args.input}", file=sys.stderr)
            return EXIT_FATAL
        files = [args.input]
    else:
        if not args.input_dir or not args.input_dir.exists():
            print(f"ERROR: --input-dir no encontrado: {args.input_dir}", file=sys.stderr)
            return EXIT_FATAL
        files = sorted(args.input_dir.glob("*.json"))
        if not files:
            print(f"ERROR: --input-dir sin JSONs: {args.input_dir}", file=sys.stderr)
            return EXIT_FATAL

    args.out_dir.mkdir(parents=True, exist_ok=True)

    all_manifests: List[FigureManifest] = []
    all_degradations: List[Degradation] = []
    last_manifest_dict: Optional[Dict[str, Any]] = None

    for f in files:
        manifest, degradations = process_file(
            input_path=f,
            out_dir=args.out_dir,
            width=args.width,
            height=args.height,
            allow_missing_refs=args.allow_missing_refs,
        )
        if manifest is not None:
            all_manifests.append(manifest)
            last_manifest_dict = asdict(manifest)
        all_degradations.extend(degradations)

    # Reporte de degradación
    _atomic_write_json(args.out_dir / "render-degradation.json", {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "files": [str(f) for f in files],
        "degradations": [asdict(d) for d in all_degradations],
    })

    if args.json and last_manifest_dict is not None:
        print(json.dumps(last_manifest_dict, indent=2, ensure_ascii=False))
    elif last_manifest_dict is not None:
        # Markdown mínimo
        out = [f"# Figure Manifest ({last_manifest_dict['figure_type']})"]
        out.append("")
        out.append(f"- Title: {last_manifest_dict['title']}")
        out.append(f"- Theme: {last_manifest_dict['theme']}")
        out.append(f"- Palette: {last_manifest_dict['palette_used']} (colorblind safe: {last_manifest_dict['palette_colorblind_safe']})")
        out.append(f"- Series: {len(last_manifest_dict['series'])}")
        out.append(f"- Source refs total: {last_manifest_dict['source_refs_total']}")
        out.append("")
        out.append(f"**Alt text**: {last_manifest_dict['alt_text']}")
        out.append("")
        out.append(f"**Reading phrase**: {last_manifest_dict['reading_phrase']}")
        print("\n".join(out))

    any_fail = any(severity_at_least(d.severity, args.fail_on) for d in all_degradations)
    return EXIT_PARTIAL if any_fail else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
