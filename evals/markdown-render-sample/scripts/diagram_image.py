#!/usr/bin/env python3
"""diagram_image.py — Stub mínimo de F70 para testing del flag --pre-render-diagrams."""

from __future__ import annotations

import argparse
import pathlib
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Stub de F70 diagram_image.py")
    parser.add_argument("--input", required=True, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    parser.add_argument("--format", default="svg")
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg"><!-- mock F70 for {args.input.name} --></svg>\n',
        encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
