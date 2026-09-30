#!/usr/bin/env python3
"""
run_eval.py — Orchestrator for the ROADMAP F112 checklist battery.

Runs the 3 verification scripts in order:
  1. check_blockers              (criterion 1: each type has [B] block)
  2. check_recommended_separation (criterion 2: [B] / [R] strict separation)
  3. check_reference_profile      (criterion 3: no academic [B] in reference)

Reports a unified PASS / FAIL summary. Exit 0 iff all 3 scripts exit 0.

Usage:
  python3 run_eval.py [--root ROOT]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPTS = (
    "check_blockers.py",
    "check_recommended_separation.py",
    "check_reference_profile.py",
)


def run(script_path: Path, root: Path) -> tuple[int, str]:
    """Run a check script; return (exit_code, captured_stdout)."""
    proc = subprocess.run(
        [sys.executable, str(script_path), "--root", str(root)],
        capture_output=True,
        text=True,
        cwd=root,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--root", default=None,
                        help="Repo root (defaults to parent of script dir)")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent.parent

    here = Path(__file__).resolve().parent

    print(f"run_eval: root = {root}")
    print(f"run_eval: scripts in {here}")
    print()

    results: list[tuple[str, int]] = []
    for name in SCRIPTS:
        script = here / name
        if not script.is_file():
            print(f"MISSING: {name}")
            results.append((name, 2))
            continue
        rc, out = run(script, root)
        # Print the script's stdout (compact per-script summary).
        for line in out.splitlines():
            print(f"  [{name}] {line}")
        print()
        results.append((name, rc))

    print("=== Summary ===")
    overall = 0
    for name, rc in results:
        label = "PASS" if rc == 0 else f"FAIL (exit {rc})"
        print(f"  {name:42s} {label}")
        if rc != 0:
            overall = 1

    print()
    if overall == 0:
        print("run_eval: 3/3 PASS — F112 cierre verificado")
    else:
        print(f"run_eval: FAIL — {sum(1 for _, rc in results if rc != 0)}/3 scripts failed")
    return overall


if __name__ == "__main__":
    sys.exit(main())