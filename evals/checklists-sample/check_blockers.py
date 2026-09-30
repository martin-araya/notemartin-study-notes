#!/usr/bin/env python3
"""
check_blockers.py — Verifies criterion 1 of ROADMAP F112.

For each of the 15 note-type files in references/05-note-types/:
  1. Find §6.1 · Bloqueantes [B] subsection.
  2. Parse all `- [ ] [B] ...` items under it.
  3. Verify ≥ 1 [B] item is present (no trivial type).
  4. Verify every item starts with literal `[B]` prefix.
  5. Exit 0 if all 15 types pass; exit 1 otherwise.

Usage:
  python3 check_blockers.py [--types-dir DIR] [--root ROOT]

Defaults: --types-dir = skill/notemartin-study-notes/references/05-note-types
relative to repo root. The script auto-detects the repo root from CWD.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Closed list of 15 effective note types (selector.md is meta, not a note type).
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

# Regex for a [B] item line: - [ ] [B] ...
B_ITEM_RE = re.compile(r"^-\s+\[\s+\]\s+\[B\]\s+\S")

# Regex for the §6.1 subsection header.
S61_HEADER_RE = re.compile(r"^###\s+§6\.1\b.*Bloqueantes", re.IGNORECASE)


def find_s61_section(lines: list[str]) -> tuple[int, int] | None:
    """Return (start, end) line indices of the §6.1 subsection body, or None."""
    start = None
    for i, ln in enumerate(lines):
        if S61_HEADER_RE.match(ln):
            start = i + 1
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start, len(lines)):
        # Stop at next H3 (`### §`) or H2 (`## §7`) heading.
        if lines[j].startswith("### ") or (lines[j].startswith("## ") and j > start):
            end = j
            break
    return (start, end)


def check_file(path: Path) -> tuple[bool, list[str]]:
    """Return (pass, list_of_issues) for one note-type file."""
    issues: list[str] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    section = find_s61_section(lines)
    if section is None:
        return False, [f"missing `### §6.1 · Bloqueantes [B]` subsection"]

    start, end = section
    body = lines[start:end]

    b_items = [ln for ln in body if B_ITEM_RE.match(ln)]

    if not b_items:
        issues.append("§6.1 has 0 [B] items (must be ≥ 1; the type would be trivial)")
        return False, issues

    for ln in body:
        # Every `- [ ]` line in §6.1 must be tagged.
        if re.match(r"^-\s+\[\s+\]", ln) and not B_ITEM_RE.match(ln):
            issues.append(f"un-tagged item in §6.1: {ln.strip()[:80]}")

    return (len(issues) == 0), issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--types-dir", default=None,
                        help="Path to 05-note-types/ directory")
    parser.add_argument("--root", default=None,
                        help="Repo root (defaults to CWD)")
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
    print(f"check_blockers: {len(passes)}/{total} types pass")
    for nt in passes:
        print(f"  PASS  {nt}")
    for nt, issues in failures:
        print(f"  FAIL  {nt}")
        for it in issues:
            print(f"        - {it}")

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())