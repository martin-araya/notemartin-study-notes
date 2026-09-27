#!/usr/bin/env python3
"""Genera fixtures para `evals/css-snippet-sample/`.

Produce:
- `fixtures/css-tokens.generated.golden.css` (snapshot determinista del output del generador).
- `fixtures/notemartin.snapshot.txt` (resumen del snippet: líneas, secciones, número de clases).
- `expected/contrast-report.md` (no aplica contraste aquí; placeholder).

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skill" / "notemartin-study-notes"
GENERATOR_PATH = SKILL_DIR / "scripts" / "render" / "css_from_tokens.py"
NOTEMARTIN_CSS = SKILL_DIR / "assets" / "notemartin.css"
GENERATED_CSS = SKILL_DIR / "assets" / "css-tokens.generated.css"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
EXPECTED_DIR = Path(__file__).resolve().parent / "expected"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "scripts.render.css_from_tokens",
        GENERATOR_PATH,
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("scripts.render.css_from_tokens", mod)
    spec.loader.exec_module(mod)
    return mod


def _build_generated_snapshot() -> dict:
    mod = _load_generator()
    tokens = mod.load_tokens()
    content = mod.render(tokens)
    return {
        "tokens_version": tokens["$version"],
        "byte_count": len(content.encode("utf-8")),
        "line_count": content.count("\n") + 1,
        "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "content": content,
    }


def _build_notemartin_snapshot() -> dict:
    text = NOTEMARTIN_CSS.read_text(encoding="utf-8")
    # Cuenta clases CSS usadas (selector class)
    classes = sorted(set(re.findall(r"\.([a-zA-Z][a-zA-Z0-9_-]*)", text)))
    return {
        "byte_count": len(text.encode("utf-8")),
        "line_count": text.count("\n") + 1,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "class_count": len(classes),
        "classes": classes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regen", action="store_true", help="Fuerza regeneración.")
    args = parser.parse_args()

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)

    gen_path = FIXTURES_DIR / "css-tokens.generated.golden.json"
    note_path = FIXTURES_DIR / "notemartin.snapshot.json"

    if args.regen or not gen_path.exists():
        snap = _build_generated_snapshot()
        with gen_path.open("w", encoding="utf-8") as f:
            json.dump(
                {"tokens_version": snap["tokens_version"],
                 "byte_count": snap["byte_count"],
                 "line_count": snap["line_count"],
                 "sha256": snap["sha256"]},
                f, indent=2, ensure_ascii=False,
            )
        # Also write the actual CSS for diffing
        (FIXTURES_DIR / "css-tokens.generated.golden.css").write_text(
            snap["content"], encoding="utf-8",
        )
        print(f"Golden generado: {gen_path}")

    if args.regen or not note_path.exists():
        snap = _build_notemartin_snapshot()
        with note_path.open("w", encoding="utf-8") as f:
            json.dump(snap, f, indent=2, ensure_ascii=False)
        print(f"Snapshot snippet: {note_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
