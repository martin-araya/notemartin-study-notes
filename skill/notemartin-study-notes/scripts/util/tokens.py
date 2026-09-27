"""Loader de design tokens (F72).

Carga `assets/tokens.json` (la fuente única de color, tipografía,
espaciado, radios y pesos) y expone helpers de resolución por modo
(light | dark). Aplica INV-14: ningún archivo del proyecto debe
contener literales de color; los consumidores (figuras, CSS, etc.)
leen de aquí.

Sin dependencias externas. Python 3.9+ stdlib puro.

CLI mínimo:
    python3 -m scripts.util.tokens --dump
    python3 -m scripts.util.tokens --resolve semantic info.fg light
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

TOKENS_FILENAME = "tokens.json"
SUPPORTED_MAJOR = 1
_VALID_MODE = ("light", "dark")
_HEX_RE = re.compile(r"^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$")


def _candidate_paths(explicit: Optional[Path]) -> list[Path]:
    """Devuelve rutas candidatas para `tokens.json` en orden de prioridad.

    1. Ruta explícita si se pasó.
    2. `<cwd>/skill/notemartin-study-notes/assets/tokens.json`.
    3. `<repo>/skill/notemartin-study-notes/assets/tokens.json`
       (relativo a este archivo: .../scripts/util/tokens.py →
       .../skill/notemartin-study-notes/assets/tokens.json, subiendo 2 niveles).
    """
    out: list[Path] = []
    if explicit is not None:
        out.append(Path(explicit))
    cwd = Path.cwd()
    out.append(cwd / "skill" / "notemartin-study-notes" / "assets" / TOKENS_FILENAME)
    here = Path(__file__).resolve()
    repo_from_script = here.parents[2] / "assets" / TOKENS_FILENAME
    out.append(repo_from_script)
    return out


def load_tokens(path: Optional[Path] = None) -> Dict[str, Any]:
    """Carga y valida `tokens.json`.

    Raises:
        FileNotFoundError: si el archivo no existe en ninguna ruta candidata.
        ValueError: si el JSON es inválido, no tiene `$version`, o
                    `$version.major` > `SUPPORTED_MAJOR`.
    """
    last_err: Optional[Exception] = None
    for candidate in _candidate_paths(path):
        if candidate.is_file():
            try:
                with candidate.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"tokens.json inválido en {candidate}: {e}") from e
            _validate(data, candidate)
            return data
            last_err = None  # not reachable, kept for type-checker clarity
    raise FileNotFoundError(
        "tokens.json no encontrado. Probé: "
        + ", ".join(str(p) for p in _candidate_paths(path))
    )


def _validate(data: Dict[str, Any], path: Path) -> None:
    if not isinstance(data, dict):
        raise ValueError(f"{path}: el root debe ser un objeto JSON")
    version = data.get("$version")
    if not isinstance(version, str):
        raise ValueError(f"{path}: falta `$version` (string)")
    parts = version.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError(f"{path}: `$version` debe ser semver (X.Y.Z), recibido {version!r}")
    major = int(parts[0])
    if major > SUPPORTED_MAJOR:
        raise ValueError(
            f"{path}: `$version.major={major}` > soportado ({SUPPORTED_MAJOR})"
        )
    for key in ("typography", "spacing", "radii", "_neutral", "semantic", "series"):
        if key not in data:
            raise ValueError(f"{path}: falta clave top-level `{key}`")


def warn_if_unsupported_major(
    version: str, supported_major: int = SUPPORTED_MAJOR
) -> None:
    """Imprime warning (no error) si `version.major` > `supported_major`.

    No aborta: el caller decide si elevar a error. Pensado para
    consumidores tolerantes (figuras, CSS) que pueden seguir renderizando
    con tokens nuevos no conocidos.
    """
    parts = version.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return
    major = int(parts[0])
    if major > supported_major:
        print(
            f"[tokens] AVISO: `$version` major={major} > soportado "
            f"({supported_major}). Algunos tokens pueden no reconocerse.",
            file=sys.stderr,
        )


def resolve_token(
    tokens: Dict[str, Any],
    category: str,
    name: str,
    mode: str = "light",
    field: Optional[str] = None,
) -> str:
    """Resuelve un token a un hex string.

    La navegación usa dot-path sobre `name` y opcionalmente `field` para
    llegar al nodo hoja, y luego selecciona `mode` si la hoja es un dict
    `{light, dark}`. Si la hoja es un string directo, se ignora `mode`.

    Args:
        tokens: dict cargado por `load_tokens()`.
        category: categoría top-level (`semantic`, `_neutral`, `series`).
        name: nombre dentro de la categoría; soporta dot-path
              (p.ej. `"info"` para `semantic.info`).
        mode: `light` o `dark`. Aplicado solo si la hoja tiene subdict por modo.
        field: clave final dentro del nodo seleccionado (p.ej. `"fg"`,
               `"bg"`, `"fgOnBg"`). Si se omite, se devuelve el nodo completo
               o el subdict por modo.

    Returns:
        Hex string con `#` (p.ej. `"#0D47A1"`). Si `field=None` y la hoja
        tiene `{light, dark}`, devuelve el subdict del modo.

    Raises:
        KeyError: si la ruta no existe o `mode` no es válido.
    """
    if mode not in _VALID_MODE:
        raise KeyError(f"mode debe ser uno de {_VALID_MODE}, recibido {mode!r}")
    if category not in tokens:
        raise KeyError(f"categoría {category!r} no existe en tokens.json")
    if not isinstance(tokens[category], dict) or name not in tokens[category]:
        raise KeyError(f"ruta `{category}.{name}` no existe en tokens.json")
    node: Any = tokens[category][name]
    has_mode_branch = (
        isinstance(node, dict) and "light" in node and "dark" in node
    )
    if has_mode_branch:
        node = node[mode]
    if field is not None:
        if not isinstance(node, dict) or field not in node:
            path = f"{category}.{name}.{mode}.{field}" if has_mode_branch else f"{category}.{name}.{field}"
            raise KeyError(f"campo `{field}` no existe en `{path}`")
        node = node[field]
    if isinstance(node, str):
        if not _HEX_RE.match(node):
            raise ValueError(
                f"token resuelto no es hex válido: {node!r}"
            )
        return node
    if isinstance(node, dict) and field is None:
        return node
    raise KeyError(
        f"no se pudo resolver `{category}.{name}"
        + (f".{field}" if field else "")
        + f"` para mode={mode!r}"
    )


def resolve_series(
    tokens: Dict[str, Any],
    name: str,
    mode: str = "light",
) -> str:
    """Resuelve un color de la paleta de series (F70 Okabe-Ito).

    Maneja la inversión light↔dark de `okabe-ito-black` (negro en
    light, blanco en dark) automáticamente: el token se modela como
    `{light: "#000000", dark: "#FFFFFF"}`.

    Args:
        tokens: dict cargado por `load_tokens()`.
        name: nombre del token (p.ej. `okabe-ito-blue` o `blue` con
              prefijo automático). Si el nombre no lleva prefijo
              `okabe-ito-`, se añade.
        mode: `light` o `dark`.

    Returns:
        Hex string.
    """
    full = name if name.startswith("okabe-ito-") else f"okabe-ito-{name}"
    if mode not in _VALID_MODE:
        raise KeyError(f"mode debe ser uno de {_VALID_MODE}, recibido {mode!r}")
    if "series" not in tokens:
        raise KeyError("categoría `series` no existe en tokens.json")
    node = tokens["series"].get(full)
    if node is None:
        raise KeyError(f"token de serie `{full}` no existe en tokens.json")
    if isinstance(node, str):
        return node
    if isinstance(node, dict) and mode in node:
        value = node[mode]
        if isinstance(value, str) and _HEX_RE.match(value):
            return value
    raise ValueError(f"token de serie `{full}` malformado para mode={mode!r}")


def _dump(tokens: Dict[str, Any]) -> str:
    return json.dumps(tokens, indent=2, ensure_ascii=False)


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="scripts.util.tokens",
        description="Loader de design tokens (F72).",
    )
    parser.add_argument(
        "--dump",
        action="store_true",
        help="Imprime el contenido completo de tokens.json en stdout.",
    )
    parser.add_argument(
        "--resolve",
        nargs="+",
        metavar="ARG",
        help=(
            "Resuelve un token. Formatos: "
            "`CATEGORY NAME [MODE] [FIELD]` (p.ej. `semantic info light fgOnBg` "
            "o `series okabe-ito-blue`)."
        ),
    )
    parser.add_argument(
        "--tokens",
        type=Path,
        default=None,
        help="Ruta explícita a tokens.json (opcional).",
    )
    args = parser.parse_args(argv)

    tokens = load_tokens(args.tokens)
    warn_if_unsupported_major(tokens["$version"])

    if args.dump:
        print(_dump(tokens))
        return 0
    if args.resolve:
        category = args.resolve[0] if len(args.resolve) >= 1 else None
        name = args.resolve[1] if len(args.resolve) >= 2 else None
        mode = args.resolve[2] if len(args.resolve) >= 3 else "light"
        field = args.resolve[3] if len(args.resolve) >= 4 else None
        try:
            print(
                resolve_token(tokens, category, name, mode=mode, field=field)
            )
        except (KeyError, ValueError) as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
