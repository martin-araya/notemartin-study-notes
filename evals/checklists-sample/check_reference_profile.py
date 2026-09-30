#!/usr/bin/env python3
"""
check_reference_profile.py — Verifies criterion 3 of ROADMAP F112.

For each of the 15 note-type files in references/05-note-types/:
  1. Find §6.1 · Bloqueantes [B] subsection.
  2. Extract all [B] item texts.
  3. Verify NO [B] item references any of the 12 academic/pedagogical
     sections that must be OMIT in `reference` profile (per F112 §5.1):
       - Analogía
       - Intuición
       - Comparaciones (≥ 2)
       - Autoevaluación
       - Práctica
       - Decisiones de diseño
       - Objetivos oficiales
       - Lo que NO debe correrse en producción
       - Cuándo omitir este lab
       - Pistas
       - Ejercicios
       - Énfasis del autor
       - Conexiones
  4. Also verify at least 1 [B] item exists (covered elsewhere too).
  5. Exit 0 if all 15 types pass; exit 1 otherwise.

Note: [R] items that are tagged with OMIT en `reference` are acceptable;
they are simply not required. Only [B] items referencing those sections
violate criterion 3.

Usage:
  python3 check_reference_profile.py [--types-dir DIR] [--root ROOT]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

NOTE_TYPES = (
    "concept",
    "api-reference",
    "procedure",
    "configuration",
    "error-troubleshooting",
    "architecture",
    "syntax",
    "data-model",
    "chapter-digest",
    "comparison",
    "version-delta",
    "glossary-term",
    "cheatsheet",
    "index-moc",
    "practice",
)

# Academic / pedagogical sections that the `reference` profile must NOT
# require as [B]. The check normalises apostrophes and is case-insensitive.
OMIT_SECTIONS = (
    "Analogía",
    "Intuición",
    "Comparaciones",
    "Autoevaluación",
    "Práctica",
    "Decisiones de diseño",
    "Objetivos oficiales",
    "Lo que NO debe correrse en producción",
    "Cuándo omitir este lab",
    "Pistas",
    "Ejercicios",
    "Énfasis del autor",
    "Conexiones",
)

B_ITEM_RE = re.compile(r"^-\s+\[\s+\]\s+\[B\]\s+(.+)$")
S61_HEADER_RE = re.compile(r"^###\s+§6\.1\b.*Bloqueantes", re.IGNORECASE)


def normalise(s: str) -> str:
    """Lowercase + strip accents so 'Analogía' matches 'analogia'."""
    out = s.lower()
    repl = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "à": "a", "è": "e", "ì": "i", "ò": "o", "ù": "u",
        "ñ": "n", "ü": "u",
    }
    for src, dst in repl.items():
        out = out.replace(src, dst)
    return out


def find_s61_section(lines: list[str]) -> tuple[int, int] | None:
    start = None
    for i, ln in enumerate(lines):
        if S61_HEADER_RE.match(ln):
            start = i + 1
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start, len(lines)):
        if lines[j].startswith("### ") or (lines[j].startswith("## ") and j > start):
            end = j
            break
    return (start, end)


def check_file(path: Path) -> tuple[bool, list[str]]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    section = find_s61_section(lines)
    if section is None:
        return False, ["missing `### §6.1 · Bloqueantes [B]` subsection"]

    start, end = section
    body = lines[start:end]

    b_items: list[tuple[int, str]] = []
    for i, ln in enumerate(body):
        m = B_ITEM_RE.match(ln)
        if m:
            b_items.append((start + i, m.group(1)))

    if not b_items:
        return False, ["§6.1 has 0 [B] items"]

    # Normalise OMIT list once.
    omit_norm = {normalise(s) for s in OMIT_SECTIONS}

    for lineno, item_text in b_items:
        item_norm = normalise(item_text)

        # Skip items that are explicitly exempt from the reference profile.
        # Two forms of exemption are recognised:
        #   1. Explicit annotation: `OMIT en `reference`` (or `omit en reference`)
        #   2. Conditional form: the item only fires when a flag is true,
        #      e.g. "## Práctica ... solo si profile.include_practice: true".
        is_exempt = (
            "omit en `reference`" in item_norm
            or "omit en reference" in item_norm
            or "solo si " in item_norm
        )
        if is_exempt:
            continue

        for section_name in OMIT_SECTIONS:
            section_norm = normalise(section_name)
            # Match the H2/H3 form: "## <name>" or "### <name>".
            if (f"## {section_norm}" in item_norm
                    or f"### {section_norm}" in item_norm):
                issues.append(
                    f"line {lineno + 1}: [B] requires academic section "
                    f"`{section_name}` (must be OMIT in `reference`): "
                    f"{item_text[:80]}"
                )

    return (len(issues) == 0), issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--types-dir", default=None)
    parser.add_argument("--root", default=None)
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path.cwd()
    types_dir = Path(args.types_dir).resolve() if args.types_dir \
        else root / "skill" / "notemartin-study-notes" / "references" / "05-note-types"

    if not types_dir.is_dir():
        print(f"ERROR: types dir not found: {types_dir}", file=sys.stderr)
        return 2

    passes: list[str] = []
    failures: list[tuple[str, list[str]]] = []

    for nt in NOTE_TYPES:
        path = types_dir / f"{nt}.md"
        if not path.is_file():
            failures.append((nt, [f"file not found: {path}"]))
            continue
        ok, issues = check_file(path)
        if ok:
            passes.append(nt)
        else:
            failures.append((nt, issues))

    total = len(NOTE_TYPES)
    print(f"check_reference_profile: {len(passes)}/{total} types pass")
    for nt in passes:
        print(f"  PASS  {nt}")
    for nt, issues in failures:
        print(f"  FAIL  {nt}")
        for it in issues:
            print(f"        - {it}")

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())