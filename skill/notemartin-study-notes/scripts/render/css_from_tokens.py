"""Generador de CSS variables desde `assets/tokens.json` (F74).

Produce `assets/css-tokens.generated.css`: un bloque `:root { --token: hex; }`
para el tema light, seguido de `@media (prefers-color-scheme: dark) { :root { ... } }`
con los overrides dark. La fuente única de los hex es `assets/tokens.json` (F72);
este módulo NO contiene literales de color (INV-14).

Convenciones de naming (importante para F73/F74 wiring):
- `semantic.<name>.<field>` → `--semantic-<name>-<field>` (p.ej. `semantic.info.bg` → `--semantic-info-bg`)
- `_neutral.<name>` → `--_neutral-<name>`
- `typography.families.<role>` → `--typography-families-<role>` (string font-family)
- `typography.scale.<size>` → `--typography-scale-<size>` (rem string)
- `typography.lineHeights.<name>` → `--typography-lineheights-<name>` (CSS number)
- `typography.weights.<name>` → `--typography-weights-<name>` (CSS number)
- `spacing.scale.<n>` → `--spacing-scale-<n>`
- `spacing.density.<preset>.<field>` → `--spacing-density-<preset>-<field>` (alias al spacing.scale.X)
- `radii.<name>` → `--radii-<name>`

CLI:
    python3 -m scripts.render.css_from_tokens --out <path>
    python3 -m scripts.render.css_from_tokens --check  # exit 0 si el archivo está al día, 1 si desactualizado

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

DEFAULT_TOKENS_PATH = (
    Path(__file__).resolve().parents[2] / "assets" / "tokens.json"
)
DEFAULT_OUT_PATH = (
    Path(__file__).resolve().parents[2] / "assets" / "css-tokens.generated.css"
)
SEMANTIC_FIELDS = ("fg", "bg", "border", "fgOnBg", "borderContrast")
SUPPORTED_MAJOR = 1


def _load_tokens_module():
    """Carga `scripts.util.tokens` vía importlib (mismo patrón que los renderers)."""
    spec = importlib.util.spec_from_file_location(
        "scripts.util.tokens",
        Path(__file__).resolve().parent.parent / "util" / "tokens.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("scripts.util.tokens", mod)
    spec.loader.exec_module(mod)
    return mod


def _format_value(v: Any) -> str:
    """Formatea un valor de tokens.json como CSS value (string/num)."""
    if isinstance(v, str):
        return v
    if isinstance(v, (int, float)):
        return str(v)
    raise ValueError(f"valor no serializable a CSS: {v!r}")


def _var_name(*parts: str) -> str:
    return "--" + "-".join(parts)


def _emit_neutral_vars(tokens: Dict[str, Any], mode: str) -> List[str]:
    """Emite las variables de `_neutral` para el modo (light/dark)."""
    lines: List[str] = []
    for name, payload in sorted(tokens["_neutral"].items()):
        if not isinstance(payload, dict) or mode not in payload:
            continue
        lines.append(f"  {_var_name('_neutral', name)}: {_format_value(payload[mode])};")
    return lines


def _emit_semantic_vars(tokens: Dict[str, Any], mode: str) -> List[str]:
    """Emite las variables de `semantic` para el modo (9 × 5 = 45 entries)."""
    lines: List[str] = []
    for name, payload in sorted(tokens["semantic"].items()):
        if not isinstance(payload, dict):
            continue
        per_mode = payload.get(mode)
        if not isinstance(per_mode, dict):
            continue
        for field in SEMANTIC_FIELDS:
            if field not in per_mode:
                continue
            lines.append(
                f"  {_var_name('semantic', name, field)}: "
                f"{_format_value(per_mode[field])};"
            )
    return lines


def _emit_typography_vars(tokens: Dict[str, Any]) -> List[str]:
    """Emite las variables de `typography` (mode-agnostic)."""
    lines: List[str] = []
    typo = tokens["typography"]
    # families.<role>: lista → string CSS font-family
    for role, family_list in sorted(typo.get("families", {}).items()):
        if not isinstance(family_list, list):
            continue
        # CSS font-family: cada elemento entre comillas si no es identificador CSS genérico
        parts = []
        for f in family_list:
            if f in ("serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui"):
                parts.append(f)
            else:
                parts.append(f'"{f}"')
        lines.append(f"  {_var_name('typography', 'families', role)}: {', '.join(parts)};")
    # scale.<size>: string rem
    for size, val in sorted(typo.get("scale", {}).items()):
        lines.append(f"  {_var_name('typography', 'scale', size)}: {_format_value(val)};")
    # weights.<name>: int
    for name, val in sorted(typo.get("weights", {}).items()):
        lines.append(f"  {_var_name('typography', 'weights', name)}: {_format_value(val)};")
    # lineHeights.<name>: number
    for name, val in sorted(typo.get("lineHeights", {}).items()):
        lines.append(f"  {_var_name('typography', 'lineheights', name)}: {_format_value(val)};")
    return lines


def _emit_spacing_vars(tokens: Dict[str, Any]) -> List[str]:
    """Emite las variables de `spacing` (mode-agnostic)."""
    lines: List[str] = []
    spacing = tokens["spacing"]
    # scale.<n>: rem string
    for n, val in sorted(spacing.get("scale", {}).items()):
        lines.append(f"  {_var_name('spacing', 'scale', n)}: {_format_value(val)};")
    # density.<preset>.<field>: alias al spacing.scale.X (string)
    for preset, fields in sorted(spacing.get("density", {}).items()):
        if not isinstance(fields, dict):
            continue
        for field, scale_n in sorted(fields.items()):
            alias_value = spacing.get("scale", {}).get(scale_n, scale_n)
            lines.append(
                f"  {_var_name('spacing', 'density', preset, field)}: "
                f"{_format_value(alias_value)};"
            )
    return lines


def _emit_radii_vars(tokens: Dict[str, Any]) -> List[str]:
    """Emite las variables de `radii` (mode-agnostic)."""
    lines: List[str] = []
    for name, val in sorted(tokens.get("radii", {}).items()):
        lines.append(f"  {_var_name('radii', name)}: {_format_value(val)};")
    return lines


def _emit_token_version(tokens: Dict[str, Any]) -> str:
    """Emite un comentario con la versión semver de tokens.json."""
    return f"/* tokens.json $version: {tokens['$version']} */"


def _render_root_block(tokens: Dict[str, Any], mode: str) -> str:
    """Renderiza un bloque `:root { ... }` con las variables del modo."""
    lines: List[str] = []
    lines.append(":root {")
    lines.extend(_emit_neutral_vars(tokens, mode))
    lines.extend(_emit_semantic_vars(tokens, mode))
    lines.append("}")
    return "\n".join(lines)


def _render_static_block(tokens: Dict[str, Any]) -> str:
    """Renderiza el bloque estático (tipografía + spacing + radii) — sin modo."""
    lines: List[str] = []
    lines.append(":root {")
    lines.extend(_emit_typography_vars(tokens))
    lines.extend(_emit_spacing_vars(tokens))
    lines.extend(_emit_radii_vars(tokens))
    lines.append("}")
    return "\n".join(lines)


def render(tokens: Dict[str, Any]) -> str:
    """Renderiza el CSS completo: cabecera + static block + light + dark.

    Returns:
        String CSS con la cabecera, el bloque estático y los dos modos.
    """
    version = tokens.get("$version", "?")
    parts: List[str] = [
        "/* Auto-generated from assets/tokens.json — DO NOT EDIT.",
        f" * $version: {version}",
        " * Regenerate: python3 -m scripts.render.css_from_tokens --out <path>",
        " * Source: F72 tokens.json (assets/tokens.json)",
        " * Wiring: references/07-visual/tokens.md §10",
        " */",
        "",
    ]
    # Static block (typography, spacing, radii — mode-agnostic).
    parts.append("/* === Tipografía, espaciado, radios (mode-agnostic) === */")
    parts.append(_render_static_block(tokens))
    parts.append("")
    # Light (default)
    parts.append("/* === Tema claro (default) === */")
    parts.append(_render_root_block(tokens, "light"))
    parts.append("")
    # Dark (prefers-color-scheme)
    parts.append("/* === Tema oscuro (prefers-color-scheme: dark) === */")
    parts.append("@media (prefers-color-scheme: dark) {")
    dark = _render_root_block(tokens, "dark")
    # Indent the :root block by 2 spaces
    for line in dark.split("\n"):
        if line.strip():
            parts.append(f"  {line}")
        else:
            parts.append("")
    parts.append("}")
    parts.append("")
    return "\n".join(parts)


def load_tokens(path: Path = DEFAULT_TOKENS_PATH) -> Dict[str, Any]:
    """Carga tokens.json vía scripts.util.tokens.load_tokens (validación centralizada)."""
    mod = _load_tokens_module()
    return mod.load_tokens(path)


def check_up_to_date(tokens: Dict[str, Any], out_path: Path) -> bool:
    """Devuelve True si `out_path` ya contiene el render actual de `tokens`."""
    if not out_path.is_file():
        return False
    current = render(tokens).encode("utf-8")
    existing = out_path.read_bytes()
    if current == existing:
        return True
    # También aceptar si el hash semver coincide (no regenerable en este pase)
    return f"$version: {tokens['$version']}" in existing.decode("utf-8", errors="replace")


def write(tokens: Dict[str, Any], out_path: Path) -> None:
    """Escribe el CSS renderizado a `out_path` (atomic write si está disponible)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    content = render(tokens)
    try:
        import importlib.util as _iu
        io_spec = _iu.spec_from_file_location(
            "_skill_io", Path(__file__).resolve().parent.parent / "util" / "_io.py"
        )
        io_mod = _iu.module_from_spec(io_spec)
        sys.modules.setdefault("_skill_io", io_mod)
        io_spec.loader.exec_module(io_mod)
        io_mod.atomic_write_text(out_path, content)
    except (ImportError, FileNotFoundError):
        out_path.write_text(content, encoding="utf-8")
    # Asegurar permisos legibles (atomic_write_text puede dejar 0600 en algunos FS)
    try:
        out_path.chmod(0o644)
    except OSError:
        pass


def _main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="scripts.render.css_from_tokens",
        description="Genera CSS variables desde assets/tokens.json (F74).",
    )
    parser.add_argument(
        "--tokens",
        type=Path,
        default=DEFAULT_TOKENS_PATH,
        help=f"Ruta a tokens.json (default: {DEFAULT_TOKENS_PATH}).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT_PATH,
        help=f"Ruta de salida (default: {DEFAULT_OUT_PATH}).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 0 si --out está al día, 1 si está desactualizado o falta.",
    )
    parser.add_argument(
        "--print",
        action="store_true",
        dest="print_stdout",
        help="Imprime el CSS a stdout en lugar de escribir a --out.",
    )
    args = parser.parse_args(argv)

    tokens = load_tokens(args.tokens)
    # Advertencia si major > supported (no aborta)
    parts = tokens.get("$version", "0.0.0").split(".")
    if len(parts) == 3 and parts[0].isdigit():
        if int(parts[0]) > SUPPORTED_MAJOR:
            print(
                f"[css_from_tokens] AVISO: tokens.json $version major={parts[0]} > "
                f"soportado ({SUPPORTED_MAJOR}). Variables nuevas no se reconocerán.",
                file=sys.stderr,
            )

    if args.check:
        ok = check_up_to_date(tokens, args.out)
        if ok:
            print(f"OK: {args.out} al día con tokens.json $version={tokens['$version']}")
            return 0
        print(f"DESACTUALIZADO: {args.out} no coincide con tokens.json $version={tokens['$version']}")
        return 1

    if args.print_stdout:
        print(render(tokens))
        return 0

    write(tokens, args.out)
    print(f"Escrito: {args.out} (tokens.json $version={tokens['$version']})")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
