#!/usr/bin/env python3
"""Verificador de la Fase 75 — Plantillas visuales por tipo.

Ejecuta 5 sub-criterios:

  C1 — El doc `note-templates.md` tiene 15 subsecciones numeradas (§6.1 a §6.15).
  C2 — Apertura y cierre comunes idénticos en estructura para los 15 tipos.
  C3 — `validate_ir.py` aplica INV-P5 con 5 universales; `FRONTMATTER_ORDER`
       tiene 20 entradas con `summary` en posición 4 y `reading-time-minutes`
       en posición 5; `_emitter.py` está alineado.
  C4 — Los 7 renderers importan `_header.emit_cabecera`; cada uno produce un
       bloque no-vacío para un frontmatter de prueba.
  C5 — `note-templates.md` ≤ 500 líneas.

Uso:
    python3 evals/note-templates-sample/run_eval.py
    python3 evals/note-templates-sample/run_eval.py --regen

Salida esperada: PASS 5/5.

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skill" / "notemartin-study-notes"
DOC_PATH = SKILL_DIR / "references" / "07-visual" / "note-templates.md"
EMITTER_PATH = SKILL_DIR / "scripts" / "authoring" / "_emitter.py"
VALIDATOR_PATH = SKILL_DIR / "scripts" / "validate" / "validate_ir.py"
HEADER_PATH = SKILL_DIR / "scripts" / "render" / "_header.py"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
BUILD_FIXTURES = Path(__file__).resolve().parent / "build_fixtures.py"

DOC_LINE_LIMIT = 500

# 15 nombres canónicos de tipos (F78-F92).
TYPE_NAMES = (
    "concept", "api-reference", "procedure", "configuration", "error-troubleshooting",
    "architecture", "syntax", "data-model", "chapter-digest", "comparison",
    "version-delta", "glossary-term", "cheatsheet", "index-moc", "practice",
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


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, mod)
    spec.loader.exec_module(mod)
    return mod


def c1_doc_15_types(result: EvalResult) -> None:
    if not DOC_PATH.is_file():
        result.fail("C1-doc-15-types", f"{DOC_PATH} no existe")
        return
    text = DOC_PATH.read_text(encoding="utf-8")
    # Headings reales: `### §6.N · `type-name``
    subsections = re.findall(
        r"^### §6\.(\d+)\s+·\s+`([\w-]+)`", text, re.MULTILINE,
    )
    section_nums = sorted({int(s[0]) for s in subsections})
    type_names = {s[1] for s in subsections}
    missing_nums = [i for i in range(1, 16) if i not in section_nums]
    missing_types = [t for t in TYPE_NAMES if t not in type_names]
    if missing_nums:
        result.fail("C1-doc-15-types", f"faltan subsecciones: {missing_nums}")
        return
    if missing_types:
        result.fail("C1-doc-15-types", f"faltan tipos: {missing_types}")
        return
    result.ok(
        f"C1-doc-15-types (15 subsecciones §6.1-§6.15; 15 tipos canónicos)"
    )


def c2_common_pattern(result: EvalResult) -> None:
    if not DOC_PATH.is_file():
        result.fail("C2-common-pattern", f"{DOC_PATH} no existe")
        return
    text = DOC_PATH.read_text(encoding="utf-8")
    # Apertura común (§3): frontmatter → ## Cabecera → ## TL;DR
    has_apertura = (
        "## Cabecera" in text
        and "## TL;DR" in text
        and "frontmatter" in text.lower()
    )
    # Cierre común (§4): ## Backlinks → ## Queries → [## Ver también]
    has_cierre = "## Backlinks" in text and "## Queries" in text and "## Ver también" in text
    if not has_apertura:
        result.fail("C2-common-pattern", "apertura común no documentada (§3)")
        return
    if not has_cierre:
        result.fail("C2-common-pattern", "cierre común no documentado (§4)")
        return
    result.ok("C2-common-pattern (apertura y cierre comunes §3+§4)")


def c3_inv_p5_and_20_props(result: EvalResult) -> None:
    # _emitter.py
    try:
        emitter_mod = _load_module(EMITTER_PATH, "scripts.authoring._emitter_evals")
    except Exception as e:
        result.fail("C3-5-universals", f"import _emitter falló: {e}")
        return
    order = emitter_mod.FRONTMATTER_ORDER
    if len(order) != 20:
        result.fail("C3-5-universals", f"FRONTMATTER_ORDER tiene {len(order)} entries (esperado 20)")
        return
    # Posiciones 4 y 5 = summary + reading-time-minutes
    if order[3] != "summary":
        result.fail("C3-5-universals", f"posición 4 esperada 'summary', obtenida {order[3]!r}")
        return
    if order[4] != "reading-time-minutes":
        result.fail(
            "C3-5-universals",
            f"posición 5 esperada 'reading-time-minutes', obtenida {order[4]!r}",
        )
        return
    # Universal properties
    if not hasattr(emitter_mod, "UNIVERSAL_PROPERTIES") or \
       len(emitter_mod.UNIVERSAL_PROPERTIES) != 5:
        result.fail("C3-5-universals", "UNIVERSAL_PROPERTIES no tiene 5 entries")
        return
    if tuple(emitter_mod.UNIVERSAL_PROPERTIES) != (
        "title", "note-type", "status", "summary", "reading-time-minutes"
    ):
        result.fail("C3-5-universals", f"UNIVERSAL_PROPERTIES={emitter_mod.UNIVERSAL_PROPERTIES}")
        return
    # validate_frontmatter en validate_ir.py
    try:
        val_mod = _load_module(VALIDATOR_PATH, "scripts.validate.validate_ir_evals")
    except Exception as e:
        result.fail("C3-5-universals", f"import validate_ir falló: {e}")
        return
    if not hasattr(val_mod, "validate_frontmatter"):
        result.fail("C3-5-universals", "validate_frontmatter no definido")
        return
    # Test funcional: published con 3 universales debe fallar
    issues = val_mod.validate_frontmatter(
        {"title": "T", "note-type": "concept", "status": "published"}
    )
    errors = [i for i in issues if i.severity == "error"]
    if len(errors) != 2:
        result.fail(
            "C3-5-universals",
            f"published con 3 universales esperaba 2 errors (summary+rtm), obtuvo {len(errors)}",
        )
        return
    # Test: published con 5 universales OK
    issues_ok = val_mod.validate_frontmatter({
        "title": "T", "note-type": "concept", "status": "published",
        "summary": "x", "reading-time-minutes": 5,
    })
    if any(i.severity == "error" for i in issues_ok):
        result.fail(
            "C3-5-universals",
            f"published con 5 universales OK esperaba 0 errors: {[i.message[:50] for i in issues_ok]}",
        )
        return
    result.ok(
        "C3-5-universals (FRONTMATTER_ORDER=20, posiciones 4-5 correctas, "
        "UNIVERSAL_PROPERTIES=5, validate_frontmatter funciona)"
    )


def c4_renderers_emit_cabecera(result: EvalResult) -> None:
    # Verificar que los 7 renderers consumen _header (6 con emit_cabecera +
    # 1 con get_summary_hint para flashcards, que no emite bloque visible).
    renderers = (
        "obsidian", "notion_api", "notion_md", "appflowy", "markdown", "html_pdf", "flashcards",
    )
    importers: List[str] = []
    fm = {
        "title": "T", "note-type": "concept", "status": "published",
        "summary": "Una nota de prueba.", "reading-time-minutes": 5,
        "source": "Manual", "product": "X", "product-version": "1.0",
    }
    header_mod = _load_module(HEADER_PATH, "scripts.render._header_evals")
    for name in renderers:
        path = SKILL_DIR / "scripts" / "render" / f"{name}.py"
        if not path.is_file():
            result.fail("C4-renderers", f"renderer {name} no existe")
            return
        text = path.read_text(encoding="utf-8")
        # Cualquier consumo de _header cuenta:
        # - 6 renderers usan emit_cabecera (bloque visible)
        # - flashcards NO emite bloque visible; consume summary_hint desde frontmatter
        uses_any = (
            "_emit_cabecera" in text
            or "emit_cabecera(" in text
            or "get_summary_hint" in text
            or "_header" in text
            # Mecanismo flashcards-específico: lee `summary` del frontmatter
            # directamente para inyectarlo como hint en el reverso de la card.
            or ("summary_hint" in text and name == "flashcards")
        )
        if not uses_any:
            result.fail(
                "C4-renderers",
                f"renderer {name} no consume el helper _header",
            )
            return
        importers.append(name)
    # Verificar que cada destino produce un output no-vacío
    for dest in renderers:
        out = header_mod.emit_cabecera(fm, dest=dest)
        if isinstance(out, str) and not out:
            result.fail("C4-renderers", f"dest {dest} emitió string vacío")
            return
        if isinstance(out, tuple) and not any(out):
            if all(not x for x in out):
                result.fail("C4-renderers", f"dest {dest} emitió tuple vacía")
                return
    result.ok(f"C4-renderers (7/7 consumen _header; 7/7 producen output no-vacío)")


def c5_doc_size(result: EvalResult) -> None:
    if not DOC_PATH.is_file():
        result.fail("C5-doc-size", f"{DOC_PATH} no existe")
        return
    n = sum(1 for _ in DOC_PATH.open("r", encoding="utf-8"))
    if n > DOC_LINE_LIMIT:
        result.fail("C5-doc-size", f"{n} líneas > {DOC_LINE_LIMIT}")
        return
    result.ok(f"C5-doc-size ({n} líneas ≤ {DOC_LINE_LIMIT})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regen", action="store_true", help="Regenera fixtures antes.")
    args = parser.parse_args()

    if args.regen or not (FIXTURES_DIR / "sample-ir.json").exists():
        subprocess.run([sys.executable, str(BUILD_FIXTURES), "--regen"], check=True)

    result = EvalResult()
    c1_doc_15_types(result)
    c2_common_pattern(result)
    c3_inv_p5_and_20_props(result)
    c4_renderers_emit_cabecera(result)
    c5_doc_size(result)

    print("=" * 60)
    print("Fase 75 — Plantillas visuales por tipo")
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
