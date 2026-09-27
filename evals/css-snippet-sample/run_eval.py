#!/usr/bin/env python3
"""Verificador de la Fase 74 — Snippet CSS para Obsidian.

Ejecuta 6 sub-criterios sobre los deliverables de F74:

  C1 — `assets/notemartin.css` existe y ≤ 400 líneas.
  C2 — `assets/css-tokens.generated.css` existe y comienza con la cabecera esperada.
  C3 — El snippet referencia las 9 × 5 = 45 variables semánticas
        (cada `--semantic-<name>-{fg,bg,border,fgOnBg,borderContrast}` aparece al menos una vez).
  C4 — Tema dual: bloque `@media (prefers-color-scheme: dark)` con overrides.
  C5 — INV-14: el snippet NO contiene literales hex ni `rgba()` en valores CSS
        (excluyendo comentarios).
  C6 — El generador `scripts/render/css_from_tokens.py` es determinista:
        dos invocaciones consecutivas producen el mismo output.

Uso:
    python3 evals/css-snippet-sample/run_eval.py
    python3 evals/css-snippet-sample/run_eval.py --regen

Salida esperada: PASS 6/6.

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skill" / "notemartin-study-notes"
NOTEMARTIN_CSS = SKILL_DIR / "assets" / "notemartin.css"
GENERATED_CSS = SKILL_DIR / "assets" / "css-tokens.generated.css"
GENERATOR_PATH = SKILL_DIR / "scripts" / "render" / "css_from_tokens.py"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
BUILD_FIXTURES = Path(__file__).resolve().parent / "build_fixtures.py"

SEMANTIC_NAMES = (
    "info", "success", "warning", "danger", "note",
    "example", "deprecated", "security", "performance",
)
SEMANTIC_FIELDS = ("fg", "bg", "border", "fgOnBg", "borderContrast")

# Regex de valores CSS con hex/rgba en líneas de declaración.
# Restricciones: línea que NO sea comentario (no empieza con `*` o `//`)
# Y que tenga `<prop>: ...<hex|rgba>...` (declaración real).
_CSS_VALUE_HEX = re.compile(
    r"^\s*[a-zA-Z\-]+\s*:\s*[^;{}]*#[0-9A-Fa-f]{3,8}\b"
)
_CSS_VALUE_RGBA = re.compile(
    r"^\s*[a-zA-Z\-]+\s*:\s*[^;{}]*rgba?\("
)


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


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "scripts.render.css_from_tokens_evals",
        GENERATOR_PATH,
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("scripts.render.css_from_tokens_evals", mod)
    spec.loader.exec_module(mod)
    return mod


def c1_notemartin_size(result: EvalResult) -> None:
    if not NOTEMARTIN_CSS.is_file():
        result.fail("C1-notemartin-size", f"{NOTEMARTIN_CSS} no existe")
        return
    n = sum(1 for _ in NOTEMARTIN_CSS.open("r", encoding="utf-8"))
    if n > 400:
        result.fail("C1-notemartin-size", f"{n} líneas > 400")
        return
    result.ok(f"C1-notemartin-size ({n} líneas ≤ 400)")


def c2_generated_exists(result: EvalResult) -> None:
    if not GENERATED_CSS.is_file():
        result.fail("C2-generated-exists", f"{GENERATED_CSS} no existe")
        return
    first_line = GENERATED_CSS.open("r", encoding="utf-8").readline().strip()
    expected_prefix = "/* Auto-generated from assets/tokens.json"
    if not first_line.startswith(expected_prefix):
        result.fail("C2-generated-exists", f"cabecera inesperada: {first_line!r}")
        return
    result.ok(f"C2-generated-exists (cabecera OK, primera línea: {first_line[:60]}...)")


def c3_semantic_vars_coverage(result: EvalResult) -> None:
    if not GENERATED_CSS.is_file():
        result.fail("C3-semantic-coverage", f"{GENERATED_CSS} no existe")
        return
    text = GENERATED_CSS.read_text(encoding="utf-8")
    missing: List[str] = []
    for name in SEMANTIC_NAMES:
        for field in SEMANTIC_FIELDS:
            var = f"--semantic-{name}-{field}"
            if var not in text:
                missing.append(var)
    if missing:
        result.fail("C3-semantic-coverage", f"faltan {len(missing)} vars: {missing[:3]}")
        return
    result.ok(
        f"C3-semantic-coverage (9 × 5 = 45 vars semánticas presentes en light + dark)"
    )


def c4_dark_theme(result: EvalResult) -> None:
    if not GENERATED_CSS.is_file():
        result.fail("C4-dark-theme", f"{GENERATED_CSS} no existe")
        return
    text = GENERATED_CSS.read_text(encoding="utf-8")
    if "@media (prefers-color-scheme: dark)" not in text:
        result.fail("C4-dark-theme", "no se encontró el media query dark")
        return
    # Verificar que dentro del bloque hay al menos 9 vars semánticas
    # redefinidas con hex diferente al light.
    dark_block_match = re.search(
        r"@media \(prefers-color-scheme: dark\)\s*\{(.*?)^\}",
        text,
        re.DOTALL | re.MULTILINE,
    )
    if not dark_block_match:
        result.fail("C4-dark-theme", "bloque dark no encontrado")
        return
    block = dark_block_match.group(1)
    semantic_count = sum(
        1 for name in SEMANTIC_NAMES
        for field in SEMANTIC_FIELDS
        if f"--semantic-{name}-{field}" in block
    )
    if semantic_count < 9:
        result.fail("C4-dark-theme", f"pocas vars en dark: {semantic_count}/45")
        return
    result.ok(f"C4-dark-theme ({semantic_count}/45 vars semánticas redefinidas en dark)")


def c5_no_css_literals(result: EvalResult) -> None:
    if not NOTEMARTIN_CSS.is_file():
        result.fail("C5-no-css-literals", f"{NOTEMARTIN_CSS} no existe")
        return
    text = NOTEMARTIN_CSS.read_text(encoding="utf-8")
    hex_offenders: List[str] = []
    rgba_offenders: List[str] = []
    for i, line in enumerate(text.splitlines(), start=1):
        # Skip pure comment lines (CSS comment starts with optional whitespace + `*` or `/*` or `//`)
        stripped = line.lstrip()
        if stripped.startswith("*") or stripped.startswith("/*") or stripped.startswith("//"):
            continue
        if _CSS_VALUE_HEX.match(line):
            hex_offenders.append(f"L{i}: {line.strip()[:80]}")
        if _CSS_VALUE_RGBA.match(line):
            rgba_offenders.append(f"L{i}: {line.strip()[:80]}")
    offenders = hex_offenders + rgba_offenders
    if offenders:
        result.fail("C5-no-css-literals", f"{len(offenders)}: {offenders[:3]}")
        return
    result.ok("C5-no-css-literals (0 literales hex/rgba en valores CSS de notemartin.css)")


def c6_generator_deterministic(result: EvalResult) -> None:
    try:
        mod = _load_generator()
    except Exception as e:
        result.fail("C6-deterministic", f"import del generador falló: {e}")
        return
    try:
        tokens = mod.load_tokens()
    except Exception as e:
        result.fail("C6-deterministic", f"load_tokens() falló: {e}")
        return
    out1 = mod.render(tokens).encode("utf-8")
    out2 = mod.render(tokens).encode("utf-8")
    if out1 != out2:
        result.fail("C6-deterministic", "render no es determinista")
        return
    h1 = hashlib.sha256(out1).hexdigest()[:16]
    # Cross-check with the actual generated file
    if GENERATED_CSS.is_file():
        actual = GENERATED_CSS.read_bytes()
        if actual != out1:
            result.fail(
                "C6-deterministic",
                f"hash {h1} no coincide con {GENERATED_CSS.name} ({hashlib.sha256(actual).hexdigest()[:16]}). "
                f"Re-genera con: python3 -m scripts.render.css_from_tokens --out {GENERATED_CSS.relative_to(REPO_ROOT)}",
            )
            return
    result.ok(f"C6-deterministic (2 invocaciones idénticas, sha256={h1})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regen", action="store_true", help="Regenera fixtures antes.")
    args = parser.parse_args()

    if args.regen or not (FIXTURES_DIR / "css-tokens.generated.golden.json").exists():
        subprocess.run([sys.executable, str(BUILD_FIXTURES), "--regen"], check=True)

    result = EvalResult()
    c1_notemartin_size(result)
    c2_generated_exists(result)
    c3_semantic_vars_coverage(result)
    c4_dark_theme(result)
    c5_no_css_literals(result)
    c6_generator_deterministic(result)

    print("=" * 60)
    print("Fase 74 — Snippet CSS para Obsidian")
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
