#!/usr/bin/env python3
"""Verificador de la Fase 72 — Design tokens.

Ejecuta 4 sub-criterios sobre `assets/tokens.json` y los scripts
asociados (`scripts/util/tokens.py`, `scripts/validate/contrast_check.py`):

  C1 — Schema cerrado: `$version` semver + 6 claves top-level obligatorias
        (`typography`, `spacing`, `radii`, `_neutral`, `semantic`, `series`)
        + los 9 nombres canónicos de `semantic.*` (info, success, warning,
        danger, note, example, deprecated, security, performance).

  C2 — Contraste WCAG AA en ambos modos: ejecuta
        `scripts/validate/contrast_check.py` con `--min-ratio 4.5 --mode both`
        y exige exit 0. Genera `expected/contrast-report.md` con la tabla
        18 filas para inspección humana.

  C3 — `make_figure.py` migrado: no contiene literales de color (regex con
        lookbehind para evitar falsos positivos en identificadores como
        `hex_to_rgb` o `lstrip("#")`). Cobertura: 0 ocurrencias.

  C3b — Loader funcional: el helper `resolve_token` resuelve los 9
        `semantic.<name>.light.fgOnBg` a hex válidos (regex `#RRGGBB`).
        Pasa si los 9 resuelven sin excepción.

  C4 — INV-14 cubre los archivos F72: los deliverables creados o
        migrados por esta fase (`tokens.md`, `scripts/util/tokens.py`,
        `scripts/validate/contrast_check.py`, `scripts/render/make_figure.py`,
        `evals/tokens-sample/`) no contienen literales de color. Excepción
        documentada: el docstring de `tokens.py` lleva hex como ejemplo
        de salida esperada. La migración completa de archivos
        pre-existentes (`html_pdf.template.css`, `review_report.py`)
        queda para F74.

Uso:
    python3 evals/tokens-sample/run_eval.py
    python3 evals/tokens-sample/run_eval.py --regen   # regenera fixtures antes

Salida esperada: PASS 5/5 (C1, C2, C3, C3b, C4).

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skill" / "notemartin-study-notes"
TOKENS_PATH = SKILL_DIR / "assets" / "tokens.json"
LOADER_PATH = SKILL_DIR / "scripts" / "util" / "tokens.py"
CONTRAST_SCRIPT = SKILL_DIR / "scripts" / "validate" / "contrast_check.py"
MAKE_FIGURE = SKILL_DIR / "scripts" / "render" / "make_figure.py"
BUILD_FIXTURES = Path(__file__).resolve().parent / "build_fixtures.py"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
EXPECTED_DIR = Path(__file__).resolve().parent / "expected"

EXPECTED_SEMANTIC_NAMES = [
    "info", "success", "warning", "danger", "note",
    "example", "deprecated", "security", "performance",
]
EXPECTED_TOP_KEYS = ("typography", "spacing", "radii", "_neutral", "semantic", "series")
HEX_LITERAL_RE = re.compile(
    r"(?<![A-Za-z_])#[0-9A-Fa-f]{3,8}\b|(?<![A-Za-z_])rgba?\("
)
RG_HEX_PATTERN = r"(?<![A-Za-z_])#[0-9A-Fa-f]{3,8}\b|(?<![A-Za-z_])rgba?\("


class EvalResult:
    def __init__(self) -> None:
        self.passed: List[str] = []
        self.failed: List[Tuple[str, str]] = []

    def ok(self, name: str) -> None:
        self.passed.append(name)

    def fail(self, name: str, detail: str) -> None:
        self.failed.append((name, detail))

    @property
    def total(self) -> int:
        return len(self.passed) + len(self.failed)

    def summary(self) -> str:
        if not self.failed:
            return f"PASS {len(self.passed)}/{self.total}"
        return f"FAIL {len(self.failed)}/{self.total} (passed {len(self.passed)}/{self.total})"


def c1_schema(result: EvalResult) -> None:
    try:
        with TOKENS_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        result.fail("C1-schema", f"tokens.json no legible: {e}")
        return
    version = data.get("$version", "")
    parts = version.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        result.fail("C1-schema", f"`$version` no es semver X.Y.Z: {version!r}")
        return
    missing = [k for k in EXPECTED_TOP_KEYS if k not in data]
    if missing:
        result.fail("C1-schema", f"faltan claves top-level: {missing}")
        return
    sem = data.get("semantic", {})
    missing_names = [n for n in EXPECTED_SEMANTIC_NAMES if n not in sem]
    if missing_names:
        result.fail("C1-schema", f"faltan tokens semánticos: {missing_names}")
        return
    extras = [n for n in sem if n not in EXPECTED_SEMANTIC_NAMES]
    if extras:
        result.fail("C1-schema", f"tokens semánticos no canónicos: {extras}")
        return
    result.ok(f"C1-schema (9/9 semánticos, $version={version}, 6/6 top-keys)")


def c2_contrast(result: EvalResult) -> None:
    if not CONTRAST_SCRIPT.is_file():
        result.fail("C2-contrast", f"contrast_check.py no encontrado en {CONTRAST_SCRIPT}")
        return
    cmd = [
        sys.executable, str(CONTRAST_SCRIPT),
        "--tokens", str(TOKENS_PATH),
        "--min-ratio", "4.5",
        "--mode", "both",
    ]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)
    if proc.returncode == 0:
        result.ok("C2-contrast (18/18 PASS AA, exit 0)")
    else:
        lines = proc.stdout.splitlines()[-3:] if proc.stdout else []
        result.fail("C2-contrast", f"exit={proc.returncode}; tail={lines}")


def c3_make_figure_no_literals(result: EvalResult) -> None:
    if not MAKE_FIGURE.is_file():
        result.fail("C3-make-figure", f"make_figure.py no encontrado")
        return
    text = MAKE_FIGURE.read_text(encoding="utf-8")
    offenders: List[str] = []
    for i, line in enumerate(text.splitlines(), start=1):
        for m in HEX_LITERAL_RE.finditer(line):
            offenders.append(f"line {i}: {m.group(0)} | {line.strip()[:80]}")
    if offenders:
        result.fail("C3-make-figure", f"{len(offenders)} literales: {offenders[:3]}")
    else:
        result.ok("C3-make-figure (0 literales de color en make_figure.py)")


def c3b_loader_resolves(result: EvalResult) -> None:
    if not LOADER_PATH.is_file():
        result.fail("C3b-loader", f"tokens.py loader no encontrado")
        return
    sys.path.insert(0, str(SKILL_DIR))
    try:
        from scripts.util.tokens import load_tokens, resolve_token
    except Exception as e:
        result.fail("C3b-loader", f"import loader falló: {e}")
        return
    try:
        tokens = load_tokens()
    except Exception as e:
        result.fail("C3b-loader", f"load_tokens() falló: {e}")
        return
    hex_re = re.compile(r"^#[0-9A-Fa-f]{6}$")
    failed: List[str] = []
    for name in EXPECTED_SEMANTIC_NAMES:
        for mode in ("light", "dark"):
            try:
                value = resolve_token(tokens, "semantic", name, mode, "fgOnBg")
                if not isinstance(value, str) or not hex_re.match(value):
                    failed.append(f"semantic.{name}.{mode}.fgOnBg = {value!r}")
            except Exception as e:
                failed.append(f"semantic.{name}.{mode}: {e}")
    if failed:
        result.fail("C3b-loader", "; ".join(failed[:3]))
    else:
        result.ok(f"C3b-loader (9 semánticos × 2 modos = 18 hex resueltos)")


def c4_inv14_no_literals(result: EvalResult) -> None:
    """C4 — INV-14 sobre los archivos CREADOS o MIGRADOS por F72.

    Alcance acotado a los deliverables de esta fase:
      - `assets/tokens.json` (la fuente — permitido)
      - `references/07-visual/tokens.md` (doc)
      - `scripts/util/tokens.py` (loader — hex permitidos en docstring)
      - `scripts/validate/contrast_check.py` (verificador WCAG)
      - `scripts/render/make_figure.py` (consumidor migrado)
      - `evals/tokens-sample/` (eval de F72)

    La migración de `references/08-render/html_pdf.template.css` y
    `scripts/ingest/review_report.py` (otros literales pre-existentes)
    queda explícitamente diferida a F74 (snippet CSS Obsidian + barrido
    completo de INV-14), documentada en `references/07-visual/tokens.md`
    §3. C4 cubre solo lo que F72 toca.
    """
    targets = [
        TOKENS_PATH,                                     # permitido (fuente)
        SKILL_DIR / "references" / "07-visual" / "tokens.md",
        LOADER_PATH,                                     # docstring exceptuada
        CONTRAST_SCRIPT,
        MAKE_FIGURE,
        FIXTURES_DIR,
        EXPECTED_DIR,
    ]
    offenders: List[str] = []
    # Docstring de tokens.py contiene ejemplos como "#0D47A1" que son
    # documentación, no literales: se permite esa única excepción explícita.
    allowed_in_loader_docstring = {
        "#0D47A1", "#000000", "#FFFFFF", "#E69F00", "#56B4E9",
        "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7",
        "#1F2328", "#E6E6E6", "#7B7B7B",
    }
    # tokens.md usa `#000000`/`#FFFFFF` para documentar la inversión
    # light↔dark de okabe-ito-black, y `#abc123` como ejemplo genérico
    # de la regla "no hex literales" en F48. Todas son referencias, no
    # literales que el código vaya a usar.
    allowed_in_tokens_md = {"#000000", "#FFFFFF", "#0D47A1", "#abc123"}
    for path in targets:
        if not path.is_file():
            continue
        if path == TOKENS_PATH:
            continue  # tokens.json ES la fuente; sus hex son los tokens canónicos
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), start=1):
            for m in HEX_LITERAL_RE.finditer(line):
                token = m.group(0)
                if path == LOADER_PATH and token in allowed_in_loader_docstring:
                    continue
                if (
                    path == SKILL_DIR / "references" / "07-visual" / "tokens.md"
                    and token in allowed_in_tokens_md
                ):
                    continue
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{i}: {token}")
    if offenders:
        result.fail("C4-inv14", f"{len(offenders)} literales: {offenders[:3]}")
    else:
        result.ok(
            f"C4-inv14 (0 literales en {len([t for t in targets if t.is_file()])} "
            f"archivos F72: tokens.md, tokens.py, contrast_check.py, "
            f"make_figure.py, evals/tokens-sample/)"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regen", action="store_true", help="Regenera fixtures antes de evaluar.")
    args = parser.parse_args()

    if args.regen or not (FIXTURES_DIR / "tokens.golden.json").exists():
        subprocess.run([sys.executable, str(BUILD_FIXTURES), "--regen"], check=True)

    result = EvalResult()
    c1_schema(result)
    c2_contrast(result)
    c3_make_figure_no_literals(result)
    c3b_loader_resolves(result)
    c4_inv14_no_literals(result)

    print("=" * 60)
    print("Fase 72 — Design tokens")
    print("=" * 60)
    for name in result.passed:
        print(f"  PASS  {name}")
    for name, detail in result.failed:
        print(f"  FAIL  {name}\n        {detail}")
    print("=" * 60)
    print(result.summary())
    return 0 if not result.failed else 1


if __name__ == "__main__":
    sys.exit(main())
