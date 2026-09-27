"""Verificador de contraste WCAG 2.1 sobre design tokens (F72).

Calcula el ratio de contraste WCAG entre `fgOnBg` y `bg` de cada token
semántico en cada modo (light | dark) e imprime una tabla Markdown
(o JSON con `--json`). Pensado para ejecutarse en CI sobre
`assets/tokens.json` y bloquear el commit si algún par cae por debajo
del mínimo AA (4.5:1) o AAA (7:1, opcional).

Fórmula (WCAG 2.1 SC 1.4.3):
    L = 0.2126 R + 0.7152 G + 0.0722 B
    con cada canal linealizado:
        c <= 0.03928 → c / 12.92
        c >  0.03928 → ((c + 0.055) / 1.055) ** 2.4
    ratio = (L_lighter + 0.05) / (L_darker + 0.05)

CLI:
    python3 scripts/validate/contrast_check.py \
        --tokens skill/notemartin-study-notes/assets/tokens.json \
        --min-ratio 4.5 --mode both

Exit codes:
    0  todos los pares cumplen el ratio mínimo
    1  algún par cae por debajo (se imprime cuáles)
    2  archivo no encontrado / JSON inválido / uso incorrecto

Sin dependencias externas. Python 3.9+ stdlib puro.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_TOKENS_PATH = (
    Path(__file__).resolve().parents[2] / "assets" / "tokens.json"
)
MODES = ("light", "dark")
AAA_RATIO = 7.0
AA_RATIO = 4.5
AA_LARGE_RATIO = 3.0


def _channel_linear(c: float) -> float:
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_str: str) -> float:
    """Luminancia relativa WCAG de un color hex (`#RGB`, `#RRGGBB`, `#RRGGBBAA`)."""
    s = hex_str.lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) == 8:
        s = s[:6]
    if len(s) != 6:
        raise ValueError(f"hex inválido: {hex_str!r}")
    r = int(s[0:2], 16) / 255.0
    g = int(s[2:4], 16) / 255.0
    b = int(s[4:6], 16) / 255.0
    return 0.2126 * _channel_linear(r) + 0.7152 * _channel_linear(g) + 0.0722 * _channel_linear(b)


def ratio(c1: str, c2: str) -> float:
    """Ratio WCAG entre dos colores hex (orden indiferente)."""
    l1, l2 = luminance(c1), luminance(c2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _format_ratio(r: float) -> str:
    return f"{r:.2f}:1"


def _check_pair(fg_on_bg: str, bg: str) -> Tuple[float, bool, bool]:
    r = ratio(fg_on_bg, bg)
    return r, r >= AA_RATIO, r >= AAA_RATIO


def _load_tokens(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        print(f"ERROR: tokens.json no encontrado en {path}", file=sys.stderr)
        sys.exit(2)
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: tokens.json inválido en {path}: {e}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, dict) or "semantic" not in data:
        print(
            f"ERROR: tokens.json en {path} no tiene clave top-level `semantic`",
            file=sys.stderr,
        )
        sys.exit(2)
    return data


def _collect_pairs(
    tokens: Dict[str, Any], mode: str
) -> List[Dict[str, Any]]:
    """Recolecta los pares (token, fgOnBg, bg, ratio, AA, AAA) para un modo."""
    pairs: List[Dict[str, Any]] = []
    for name, payload in sorted(tokens["semantic"].items()):
        if not isinstance(payload, dict):
            continue
        per_mode = payload.get(mode)
        if not isinstance(per_mode, dict):
            continue
        fg_on_bg = per_mode.get("fgOnBg")
        bg = per_mode.get("bg")
        if not isinstance(fg_on_bg, str) or not isinstance(bg, str):
            continue
        r, aa, aaa = _check_pair(fg_on_bg, bg)
        pairs.append(
            {
                "token": f"semantic.{name}",
                "mode": mode,
                "fg_on_bg": fg_on_bg,
                "bg": bg,
                "ratio": round(r, 3),
                "aa": aa,
                "aaa": aaa,
            }
        )
    return pairs


def _render_markdown(
    pairs: List[Dict[str, Any]], min_ratio: float
) -> str:
    if not pairs:
        return "(sin pares para mostrar)\n"
    headers = ["Token", "Modo", "fgOnBg", "bg", "Ratio", f"AA ≥ {AA_RATIO}", f"AAA ≥ {AAA_RATIO}"]
    lines: List[str] = []
    lines.append("# Verificación de contraste WCAG 2.1 — design tokens (F72)")
    lines.append("")
    lines.append(
        f"Calculado sobre `semantic.*` (9 tokens × 2 modos = 18 pares). "
        f"Mínimo exigido por CLI: {min_ratio}:1."
    )
    lines.append("")
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    for p in pairs:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{p['token']}`",
                    p["mode"],
                    f"`{p['fg_on_bg']}`",
                    f"`{p['bg']}`",
                    _format_ratio(p["ratio"]),
                    "✅" if p["aa"] else "❌",
                    "✅" if p["aaa"] else "❌",
                ]
            )
            + " |"
        )
    fails = [p for p in pairs if p["ratio"] < min_ratio]
    lines.append("")
    if fails:
        lines.append(f"## ❌ {len(fails)} par(es) por debajo de {min_ratio}:1")
        for p in fails:
            lines.append(
                f"- `{p['token']}` ({p['mode']}): "
                f"{_format_ratio(p['ratio'])} < {min_ratio}:1"
            )
    else:
        lines.append(f"## ✅ Todos los {len(pairs)} pares cumplen ≥ {min_ratio}:1")
    lines.append("")
    return "\n".join(lines)


def _main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="scripts.validate.contrast_check",
        description="Verifica el contraste WCAG de los design tokens semánticos.",
    )
    parser.add_argument(
        "--tokens",
        type=Path,
        default=DEFAULT_TOKENS_PATH,
        help=f"Ruta a tokens.json (default: {DEFAULT_TOKENS_PATH}).",
    )
    parser.add_argument(
        "--mode",
        choices=("light", "dark", "both"),
        default="both",
        help="Modo a verificar (default: both).",
    )
    parser.add_argument(
        "--min-ratio",
        type=float,
        default=AA_RATIO,
        help=f"Ratio mínimo a exigir (default: {AA_RATIO} = AA WCAG).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Salida en JSON en lugar de Markdown.",
    )
    args = parser.parse_args(argv)

    tokens = _load_tokens(args.tokens)

    if args.mode == "both":
        modes: Tuple[str, ...] = MODES
    else:
        modes = (args.mode,)

    pairs: List[Dict[str, Any]] = []
    for m in modes:
        pairs.extend(_collect_pairs(tokens, m))

    if args.json:
        print(
            json.dumps(
                {
                    "tokens_path": str(args.tokens),
                    "min_ratio": args.min_ratio,
                    "aa_ratio": AA_RATIO,
                    "aaa_ratio": AAA_RATIO,
                    "pairs": pairs,
                    "fails": [p for p in pairs if p["ratio"] < args.min_ratio],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        print(_render_markdown(pairs, args.min_ratio))

    return 0 if all(p["ratio"] >= args.min_ratio for p in pairs) else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
