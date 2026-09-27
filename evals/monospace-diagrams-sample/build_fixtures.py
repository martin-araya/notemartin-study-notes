#!/usr/bin/env python3
"""
Genera fixtures reproducibles para evals/monospace-diagrams-sample/.

Extrae los 12 patrones del archivo monospace-diagrams.md y los almacena
en fixtures/patterns.json junto con la tabla de decisión parseada de §3.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "evals" / "monospace-diagrams-sample" / "fixtures"
SOURCE_FILE = REPO_ROOT / "skill" / "notemartin-study-notes" / "references" / "07-visual" / "monospace-diagrams.md"


def extract_patterns(text: str) -> list[dict]:
    """Extrae los 12 patrones (§4-§15) con su plantilla principal."""
    patterns: list[dict] = []
    pattern_re = re.compile(
        r"## §(\d+) · Patrón: (.+?)\n"
        r"(.*?)(?=\n## §|\Z)",
        re.DOTALL,
    )
    for m in pattern_re.finditer(text):
        idx = int(m.group(1))
        name = m.group(2).strip()
        body = m.group(3)
        # Extraer la primera plantilla fenced code (sin lenguaje)
        code_match = re.search(r"```\n(.*?)```", body, re.DOTALL)
        if not code_match:
            continue
        code = code_match.group(1)
        # Ancho máximo de las líneas (excluyendo líneas vacías)
        widths = [len(line) for line in code.splitlines() if line.strip()]
        max_width = max(widths) if widths else 0
        patterns.append({
            "index": idx,
            "name": name,
            "code": code,
            "max_line_width": max_width,
        })
    return patterns


def extract_decision_table(text: str) -> list[list[str]]:
    """Extrae la tabla de decisión §3 como lista de filas."""
    lines = text.splitlines()
    # Buscar inicio de la tabla (línea con | Criterio | Mermaid | ...)
    start = None
    for i, line in enumerate(lines):
        if line.startswith("| Criterio") and "Mermaid" in line and "Monoespaciado" in line:
            start = i
            break
    if start is None:
        return []
    rows: list[list[str]] = []
    for line in lines[start + 2:]:  # +2 para saltar header y separator
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 3:
            rows.append(cells[:3])
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=FIXTURES_DIR)
    args = parser.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    if not SOURCE_FILE.exists():
        print(f"ERROR: archivo fuente no encontrado: {SOURCE_FILE}", file=sys.stderr)
        return 1

    text = SOURCE_FILE.read_text(encoding="utf-8")
    patterns = extract_patterns(text)
    decision_table = extract_decision_table(text)

    payload = {
        "source": str(SOURCE_FILE.relative_to(REPO_ROOT)),
        "patterns": patterns,
        "decision_table": decision_table,
    }
    (out / "patterns.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Fixtures generadas en {out}")
    print(f"  Patrones extraídos: {len(patterns)}")
    print(f"  Filas tabla decisión: {len(decision_table)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
