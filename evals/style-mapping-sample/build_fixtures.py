#!/usr/bin/env python3
"""Genera fixtures para `evals/style-mapping-sample/`.

Produce `fixtures/style-mapping.golden.json` con el dump de la tabla
canónica (los 20 StyleMapping serializados) y `expected/style-mapping.md`
con la tabla markdown que `references/07-visual/style-mapping.md` debe
contener (a nivel de severidades, no de hex).

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skill" / "notemartin-study-notes"
FIXTURES_DIR = REPO_ROOT / "evals" / "style-mapping-sample" / "fixtures"
EXPECTED_DIR = REPO_ROOT / "evals" / "style-mapping-sample" / "expected"


def _load_module():
    """Carga `scripts.util.style_mapping` y devuelve el módulo."""
    spec = importlib.util.spec_from_file_location(
        "scripts.util.style_mapping",
        SKILL_DIR / "scripts" / "util" / "style_mapping.py",
    )
    mod = importlib.util.module_from_spec(spec)
    import sys
    sys.modules.setdefault("scripts.util.style_mapping", mod)
    spec.loader.exec_module(mod)
    return mod


def _build_golden() -> dict:
    mod = _load_module()
    return {
        "validate_table_ok": True,
        "mapping_size": len(mod._MAPPING),
        "mappings": [asdict(m) for m in mod._MAPPING],
    }


def _build_markdown_golden() -> str:
    """Markdown con las 20 filas canónicas (formato usado en el doc)."""
    mod = _load_module()
    lines = [
        "# Tabla canónica severidad → estilo por destino (F73 — golden esperado)",
        "",
        "| Severidad | Token (F72) | Icono | Obsidian callout | Notion color | AppFlowy | HTML class |",
        "|---|---|---|---|---|---|---|",
    ]
    for m in mod._MAPPING:
        lines.append(
            f"| `{m.severity}` | `{m.semantic_token}` | {m.icon} | `{m.obsidian_callout}` "
            f"| `{m.notion_color}` | `{m.appflowy_callout}` | `{m.html_css_class}` |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regen", action="store_true", help="Fuerza regeneración.")
    args = parser.parse_args()

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)

    golden_path = FIXTURES_DIR / "style-mapping.golden.json"
    md_path = EXPECTED_DIR / "style-mapping.md"

    if args.regen or not golden_path.exists():
        golden = _build_golden()
        with golden_path.open("w", encoding="utf-8") as f:
            json.dump(golden, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Golden escrito: {golden_path}")

    if args.regen or not md_path.exists():
        md = _build_markdown_golden()
        with md_path.open("w", encoding="utf-8") as f:
            f.write(md)
        print(f"Markdown golden escrito: {md_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
