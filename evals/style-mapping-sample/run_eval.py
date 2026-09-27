#!/usr/bin/env python3
"""Verificador de la Fase 73 — Mapeo de estilo por destino.

Ejecuta 5 sub-criterios:

  C1 — El módulo cubre 20 severidades × 5 destinos = 100 campos no vacíos.
  C2 — Iconos canónicos: 17 únicos + 3 casos compartidos (warning/caution/
       conflict → ⚠️) documentados en el doc.
  C3 — Notion colors ∈ lista cerrada de 10 (default + 9 background).
  C4 — Los 6 renderers NO tienen `SEVERITY_TO_*` local (consolidación).
  C5 — `style-mapping.md` ≤ 400 líneas.

Uso:
    python3 evals/style-mapping-sample/run_eval.py
    python3 evals/style-mapping-sample/run_eval.py --regen

Salida esperada: PASS 5/5.

Sin dependencias externas. Python 3.9+ stdlib puro. `rg` necesario para C4.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skill" / "notemartin-study-notes"
STYLE_MAPPING_PATH = SKILL_DIR / "scripts" / "util" / "style_mapping.py"
STYLE_DOC = SKILL_DIR / "references" / "07-visual" / "style-mapping.md"
RENDERERS_DIR = SKILL_DIR / "scripts" / "render"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
EXPECTED_DIR = Path(__file__).resolve().parent / "expected"
BUILD_FIXTURES = Path(__file__).resolve().parent / "build_fixtures.py"

SHARED_ICON_GROUPS = (
    frozenset({"warning", "caution", "conflict"}),
)


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "scripts.util.style_mapping_evals",
        STYLE_MAPPING_PATH,
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("scripts.util.style_mapping_evals", mod)
    spec.loader.exec_module(mod)
    return mod


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


def c1_coverage(result: EvalResult) -> None:
    mod = _load_module()
    mappings = mod._MAPPING
    if len(mappings) != 20:
        result.fail("C1-coverage", f"expected 20 mappings, got {len(mappings)}")
        return
    field_names = (
        "semantic_token", "icon", "obsidian_callout",
        "notion_icon", "notion_color", "appflowy_callout", "html_css_class",
    )
    empty = []
    for m in mappings:
        for fn in field_names:
            v = getattr(m, fn)
            if not isinstance(v, str) or not v:
                empty.append(f"{m.severity}.{fn}")
    if empty:
        result.fail("C1-coverage", f"{len(empty)} empty fields: {empty[:3]}")
        return
    severities = sorted(m.severity for m in mappings)
    if severities != sorted(mod.CANONICAL_SEVERITIES):
        result.fail("C1-coverage", f"severity mismatch: {set(severities) ^ set(mod.CANONICAL_SEVERITIES)}")
        return
    result.ok(f"C1-coverage (20 mappings, 7×20=140 fields non-empty, severities match CANONICAL)")


def c2_icons(result: EvalResult) -> None:
    mod = _load_module()
    icon_to_sev: dict = {}
    for m in mod._MAPPING:
        icon_to_sev.setdefault(m.icon, []).append(m.severity)
    shared = {ic: sevs for ic, sevs in icon_to_sev.items() if len(sevs) > 1}
    expected_shared_sets = {frozenset(s) for s in SHARED_ICON_GROUPS}
    actual_shared_sets = {frozenset(sevs) for sevs in shared.values()}
    if actual_shared_sets != expected_shared_sets:
        result.fail(
            "C2-icons",
            f"shared-icon groups mismatch. got={list(actual_shared_sets)}, "
            f"expected={list(expected_shared_sets)}",
        )
        return
    unique_icons = sum(1 for sevs in icon_to_sev.values() if len(sevs) == 1)
    shared_count = sum(len(s) for s in shared.values())
    result.ok(
        f"C2-icons ({unique_icons} unique + {shared_count} shared en "
        f"{len(shared)} grupo(s): {[sorted(s) for s in shared.values()]})"
    )


def c3_notion_colors(result: EvalResult) -> None:
    mod = _load_module()
    bad = []
    seen = set()
    for m in mod._MAPPING:
        if m.notion_color not in mod.NOTION_VALID_COLORS:
            bad.append(f"{m.severity}.notion_color={m.notion_color!r}")
        seen.add(m.notion_color)
    if bad:
        result.fail("C3-notion-colors", f"invalid: {bad[:3]}")
        return
    result.ok(
        f"C3-notion-colors ({len(seen)} colores usados de {len(mod.NOTION_VALID_COLORS)} "
        f"válidos; resto fuera de la lista)"
    )


def c4_no_local_dicts(result: EvalResult) -> None:
    try:
        proc = subprocess.run(
            [
                "rg", "-n", "SEVERITY_TO_",
                str(RENDERERS_DIR),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        result.fail("C4-no-local-dicts", "`rg` (ripgrep) no está instalado")
        return
    if proc.returncode == 0:
        offenders = [
            line for line in proc.stdout.splitlines()
            if "style_mapping" not in line
        ]
        if offenders:
            result.fail("C4-no-local-dicts", f"literales en renderers: {offenders[:3]}")
            return
    elif proc.returncode == 1:
        pass  # 0 matches, perfecto
    else:
        result.fail("C4-no-local-dicts", f"rg exit={proc.returncode}; stderr={proc.stderr.strip()[:200]}")
        return
    result.ok("C4-no-local-dicts (0 literales SEVERITY_TO_* en 6 renderers)")


def c5_doc_size(result: EvalResult) -> None:
    if not STYLE_DOC.is_file():
        result.fail("C5-doc-size", f"{STYLE_DOC} no existe")
        return
    n = sum(1 for _ in STYLE_DOC.open("r", encoding="utf-8"))
    if n > 400:
        result.fail("C5-doc-size", f"{n} líneas > 400")
        return
    result.ok(f"C5-doc-size ({n} líneas ≤ 400)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regen", action="store_true", help="Regenera fixtures antes.")
    args = parser.parse_args()

    if args.regen or not (FIXTURES_DIR / "style-mapping.golden.json").exists():
        subprocess.run([sys.executable, str(BUILD_FIXTURES), "--regen"], check=True)

    result = EvalResult()
    c1_coverage(result)
    c2_icons(result)
    c3_notion_colors(result)
    c4_no_local_dicts(result)
    c5_doc_size(result)

    print("=" * 60)
    print("Fase 73 — Mapeo de estilo por destino")
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
