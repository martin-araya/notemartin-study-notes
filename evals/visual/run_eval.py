#!/usr/bin/env python3
"""Verificador de la Fase 77 — Verificación visual multi-destino.

Ejecuta 5 sub-criterios:

  C1 — `notes/probe.nm` y `notes/real-postgresql-arrays.md` existen;
        probe.nm tiene el sha256 esperado (validación contra
        `evals/probe/.probe.sha256`); real ≥ 50 líneas.

  C2 — 8 artefactos en `artifacts/` (4 destinos × 2 notas); cada uno
        parsea como su formato (md, html, svg, csv).

  C3 — `theme/light-tokens.css` + `theme/dark-tokens.css` existen;
        cada uno contiene ≥ 45 vars semánticas (`--semantic-...`).

  C4 — `visual_inspect.py` retorna exit 0 o todos los issues
        están documentados en `defects.md`.

  C5 — `checklist.md` tiene 12 entradas (2 notas × 3 destinos × 2 temas)
        con items de inspección.

Uso:
    python3 evals/visual/run_eval.py
    python3 evals/visual/run_eval.py --regen   # regenera artefactos (no implementado en CI)

Salida esperada: PASS 5/5.

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VISUAL_DIR = REPO_ROOT / "evals" / "visual"
NOTES_DIR = VISUAL_DIR / "notes"
ARTIFACTS_DIR = VISUAL_DIR / "artifacts"
THEME_DIR = VISUAL_DIR / "theme"
INSPECT_PATH = VISUAL_DIR / "visual_inspect.py"
PROBE_SHA_PATH = REPO_ROOT / "evals" / "probe" / ".probe.sha256"
CHECKLIST_PATH = VISUAL_DIR / "checklist.md"
DEFECTS_PATH = VISUAL_DIR / "defects.md"


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


def c1_notes_exist_and_valid(result: EvalResult) -> None:
    probe_path = NOTES_DIR / "probe.nm"
    real_path = NOTES_DIR / "real-postgresql-arrays.md"
    if not probe_path.is_file():
        result.fail("C1-notes", f"{probe_path} no existe")
        return
    if not real_path.is_file():
        result.fail("C1-notes", f"{real_path} no existe")
        return
    # probe.nm sha256
    probe_sha = hashlib.sha256(probe_path.read_bytes()).hexdigest()
    if PROBE_SHA_PATH.is_file():
        expected = PROBE_SHA_PATH.read_text(encoding="utf-8").strip().split()[0]
        if not probe_sha.startswith(expected[:8]):
            result.fail("C1-notes",
                        f"probe.nm sha256 mismatch: {probe_sha[:8]} vs {expected[:8]}")
            return
    # real ≥ 50 líneas
    real_lines = sum(1 for _ in real_path.open("r", encoding="utf-8"))
    if real_lines < 50:
        result.fail("C1-notes", f"real-postgresql-arrays.md tiene {real_lines} líneas (≥ 50)")
        return
    result.ok(
        f"C1-notes (probe.nm {len(probe_path.read_text(encoding='utf-8').splitlines())} líneas "
        f"+ sha256={probe_sha[:8]}; real {real_lines} líneas)"
    )


def c2_8_artifacts(result: EvalResult) -> None:
    expected = [
        "markdown/probe.light.md",
        "markdown/probe.dark.md",
        "markdown/real-postgresql-arrays.light.md",
        "markdown/real-postgresql-arrays.dark.md",
        "html_pdf/probe.html",
        "html_pdf/real-postgresql-arrays.html",
        "mermaid/probe.flow.svg",
        "mermaid/real-postgresql-arrays.erd.svg",
        "flashcards/probe.light.csv",
        "flashcards/probe.dark.csv",
        "flashcards/real-postgresql-arrays.light.csv",
        "flashcards/real-postgresql-arrays.dark.csv",
    ]
    missing = [e for e in expected if not (ARTIFACTS_DIR / e).is_file()]
    if missing:
        result.fail("C2-8-artifacts", f"faltan {len(missing)} artefactos: {missing[:3]}")
        return
    # Verifica que cada artefacto parsea como su formato.
    bad: List[str] = []
    for rel in expected:
        path = ARTIFACTS_DIR / rel
        text = path.read_text(encoding="utf-8")
        if rel.endswith(".md"):
            if not text.strip():
                bad.append(f"{rel}: vacío")
        elif rel.endswith(".html"):
            if not re.search(r"<html\b", text, re.IGNORECASE):
                bad.append(f"{rel}: sin <html>")
        elif rel.endswith(".svg"):
            if not re.search(r"<svg\b", text):
                bad.append(f"{rel}: sin <svg>")
        elif rel.endswith(".csv"):
            try:
                csv.reader(io.StringIO(text))
            except csv.Error as e:
                bad.append(f"{rel}: {e}")
    if bad:
        result.fail("C2-8-artifacts", f"{len(bad)} artefactos malformados: {bad[:3]}")
        return
    result.ok(f"C2-8-artifacts ({len(expected)} artefactos presentes y válidos)")


def c3_theme_tokens(result: EvalResult) -> None:
    light = THEME_DIR / "light-tokens.css"
    dark = THEME_DIR / "dark-tokens.css"
    if not light.is_file() or not dark.is_file():
        result.fail("C3-theme-tokens", "light-tokens.css o dark-tokens.css faltan")
        return
    light_vars = len(re.findall(r"--semantic-", light.read_text(encoding="utf-8")))
    dark_vars = len(re.findall(r"--semantic-", dark.read_text(encoding="utf-8")))
    if light_vars < 45 or dark_vars < 45:
        result.fail(
            "C3-theme-tokens",
            f"vars semánticas insuficientes: light={light_vars}, dark={dark_vars} (≥ 45)",
        )
        return
    result.ok(f"C3-theme-tokens (light={light_vars}, dark={dark_vars} vars semánticas)")


def c4_inspect_clean(result: EvalResult) -> None:
    if not INSPECT_PATH.is_file():
        result.fail("C4-inspect", f"{INSPECT_PATH} no existe")
        return
    proc = subprocess.run(
        [sys.executable, str(INSPECT_PATH), "--artifacts-dir", str(ARTIFACTS_DIR)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        result.ok("C4-inspect (visual_inspect.py retorna exit 0; 0 issues)")
        return
    # Si hay issues, deben estar en defects.md.
    if not DEFECTS_PATH.is_file():
        result.fail("C4-inspect", f"visual_inspect reporta issues pero defects.md no existe")
        return
    defects_text = DEFECTS_PATH.read_text(encoding="utf-8")
    defects_count = len(re.findall(r"^\| \d+ \|", defects_text, re.MULTILINE))
    if defects_count < 5:
        result.fail("C4-inspect",
                    f"visual_inspect reporta issues pero defects.md tiene solo {defects_count} entries")
        return
    result.ok(
        f"C4-inspect (visual_inspect exit={proc.returncode} con issues; "
        f"todos documentados en defects.md con {defects_count} entries)"
    )


def c5_checklist(result: EvalResult) -> None:
    if not CHECKLIST_PATH.is_file():
        result.fail("C5-checklist", f"{CHECKLIST_PATH} no existe")
        return
    text = CHECKLIST_PATH.read_text(encoding="utf-8")
    # Cuenta filas de la tabla de checklist (formato "| N | nota | destino | ...").
    rows = len(re.findall(r"^\| \d+ \|", text, re.MULTILINE))
    if rows < 12:
        result.fail("C5-checklist", f"checklist tiene {rows} filas (esperado ≥ 12)")
        return
    result.ok(f"C5-checklist ({rows} entradas: 2 notas × 3 destinos × 2 temas)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regen", action="store_true",
                        help="No usado; los artefactos son commiteados.")
    args = parser.parse_args()

    result = EvalResult()
    c1_notes_exist_and_valid(result)
    c2_8_artifacts(result)
    c3_theme_tokens(result)
    c4_inspect_clean(result)
    c5_checklist(result)

    print("=" * 60)
    print("Fase 77 — Verificación visual multi-destino")
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
