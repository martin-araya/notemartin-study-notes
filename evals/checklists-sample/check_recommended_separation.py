#!/usr/bin/env python3
"""
check_recommended_separation.py — Verifies criterion 2 of ROADMAP F112.

For each of the 15 note-type files in references/05-note-types/:
  1. Find §6.1 · Bloqueantes [B] and §6.2 · Recomendados [R] subsections.
  2. Verify §6.1 contains only [B] items (no [R] leakage).
  3. Verify §6.2 contains only [R] items (no [B] leakage).
  4. Verify §6.1 is non-empty (covered by check_blockers.py too; double check).
  5. Exit 0 if all 15 types pass; exit 1 otherwise.

Usage:
  python3 check_recommended_separation.py [--types-dir DIR] [--root ROOT]
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

B_ITEM_RE = re.compile(r"^-\s+\[\s+\]\s+\[B\]\s+\S")
R_ITEM_RE = re.compile(r"^-\s+\[\s+\]\s+\[R\]\s+\S")
S61_HEADER_RE = re.compile(r"^###\s+§6\.1\b.*Bloqueantes", re.IGNORECASE)
S62_HEADER_RE = re.compile(r"^###\s+§6\.2\b.*Recomendados", re.IGNORECASE)


def find_subsection(lines: list[str], header_re: re.Pattern) -> tuple[int, int] | None:
    start = None
    for i, ln in enumerate(lines):
        if header_re.match(ln):
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

    s61 = find_subsection(lines, S61_HEADER_RE)
    s62 = find_subsection(lines, S62_HEADER_RE)

    if s61 is None:
        issues.append("missing `### §6.1 · Bloqueantes [B]` subsection")
    if s62 is None:
        issues.append("missing `### §6.2 · Recomendados [R]` subsection")

    if issues:
        return False, issues

    b1, e1 = s61
    b2, e2 = s62

    body_61 = lines[b1:e1]
    body_62 = lines[b2:e2]

    # §6.1 must not contain [R] items.
    for ln in body_61:
        if R_ITEM_RE.match(ln):
            issues.append(f"[R] leaked into §6.1: {ln.strip()[:80]}")
    # §6.2 must not contain [B] items.
    for ln in body_62:
        if B_ITEM_RE.match(ln):
            issues.append(f"[B] leaked into §6.2: {ln.strip()[:80]}")

    # §6.1 must have ≥ 1 [B] item.
    if not any(B_ITEM_RE.match(ln) for ln in body_61):
        issues.append("§6.1 has 0 [B] items")

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
    print(f"check_recommended_separation: {len(passes)}/{total} types pass")
    for nt in passes:
        print(f"  PASS  {nt}")
    for nt, issues in failures:
        print(f"  FAIL  {nt}")
        for it in issues:
            print(f"        - {it}")

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())