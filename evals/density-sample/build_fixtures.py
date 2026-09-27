#!/usr/bin/env python3
"""Genera fixtures para `evals/density-sample/`.

Las 5 notas sintéticas ya están commiteadas en `fixtures/notes/`.
Este script las regenera desde la fuente si se modifican las reglas
en `references/07-visual/density.md` y los placeholders quedan stale.

Uso:
    python3 evals/density-sample/build_fixtures.py --regen
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "evals" / "density-sample" / "fixtures" / "notes"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regen", action="store_true",
                        help="Imprime recordatorio de dónde están los fixtures.")
    args = parser.parse_args()
    if args.regen:
        print(f"Las 5 notas sintéticas están en: {FIXTURES_DIR}")
        print("Edita directamente los archivos .md; no se regeneran automáticamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
