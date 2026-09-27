#!/usr/bin/env python3
"""Genera fixtures para `evals/tokens-sample/`.

Produce `fixtures/tokens.golden.json` con un snapshot esperado de los
9 tokens semánticos (campos `fgOnBg` y `bg` por modo), que sirve para
verificar que `assets/tokens.json` mantiene la cobertura completa y
los hex que el equipo de diseño aprobó al cierre de F72.

También deja un `expected/contrast-report.md` con la tabla WCAG que
`scripts/validate/contrast_check.py` debe reproducir al pasar el
test C2.

Uso:
    python3 evals/tokens-sample/build_fixtures.py
    python3 evals/tokens-sample/build_fixtures.py --regen  # fuerza regeneración

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOKENS_PATH = REPO_ROOT / "skill" / "notemartin-study-notes" / "assets" / "tokens.json"
FIXTURES_DIR = REPO_ROOT / "evals" / "tokens-sample" / "fixtures"
EXPECTED_DIR = REPO_ROOT / "evals" / "tokens-sample" / "expected"
EXPECTED_SEMANTIC_NAMES = [
    "info", "success", "warning", "danger", "note",
    "example", "deprecated", "security", "performance",
]


def _build_golden() -> dict:
    """Extrae los hex `fgOnBg` y `bg` de los 9 tokens semánticos en ambos modos."""
    with TOKENS_PATH.open("r", encoding="utf-8") as f:
        tokens = json.load(f)
    golden = {"$version": tokens["$version"], "semantic": {}}
    for name in EXPECTED_SEMANTIC_NAMES:
        sem = tokens["semantic"][name]
        golden["semantic"][name] = {
            "light": {
                "fgOnBg": sem["light"]["fgOnBg"],
                "bg":     sem["light"]["bg"],
            },
            "dark": {
                "fgOnBg": sem["dark"]["fgOnBg"],
                "bg":     sem["dark"]["bg"],
            },
        }
    return golden


def _build_contrast_report() -> str:
    """Genera un report Markdown mínimo para golden-comparación."""
    with TOKENS_PATH.open("r", encoding="utf-8") as f:
        tokens = json.load(f)
    lines = [
        "# Contrast report — F72 (golden esperado)",
        "",
        "Calculado en build; `run_eval.py` regenera al vuelo y compara.",
        "",
    ]
    for name in EXPECTED_SEMANTIC_NAMES:
        sem = tokens["semantic"][name]
        for mode in ("light", "dark"):
            fg = sem[mode]["fgOnBg"]
            bg = sem[mode]["bg"]
            lines.append(f"- semantic.{name}.{mode}: fgOnBg={fg} bg={bg}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regen", action="store_true", help="Fuerza regeneración aunque existan fixtures.")
    args = parser.parse_args()

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)

    golden_path = FIXTURES_DIR / "tokens.golden.json"
    report_path = EXPECTED_DIR / "contrast-report.md"

    if args.regen or not golden_path.exists():
        golden = _build_golden()
        with golden_path.open("w", encoding="utf-8") as f:
            json.dump(golden, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Golden escrito: {golden_path}")

    if args.regen or not report_path.exists():
        report = _build_contrast_report()
        with report_path.open("w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report escrito: {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
