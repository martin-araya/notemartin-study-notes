#!/usr/bin/env python3
"""run_eval.py — F29 eval: validates the 3 criteria of the roadmap.

Uso:
    python3 evals/web-docs-sample/run_eval.py

Criterios verificados:
  1. El orden reproduce el índice del sitio.
  2. El boilerplate no aparece en el SDM.
  3. Cada sección conserva su URL profunda.

Códigos de salida:
    0 — PASS los 3 criterios
    1 — Algún FAIL
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "evals" / "web-docs-sample" / "docs-site"
EXPECTED = ROOT / "evals" / "web-docs-sample" / "expected"
SCRIPT = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "web_docs.py"

PY = sys.executable


def _run_pipeline(out_dir: Path) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(
        [PY, str(SCRIPT), "--source", str(FIXTURES), "--base-url", "https://example.com/docs/",
         "--out-dir", str(out_dir), "--json-only"],
        capture_output=True, text=True, timeout=60,
    )
    if res.returncode not in (0, 2):
        raise RuntimeError(f"web_docs failed (exit {res.returncode}): {res.stderr}")
    sections_path = out_dir / "ingest" / "web_docs" / "sections.json"
    return json.loads(sections_path.read_text(encoding="utf-8"))


def _load_sections(out_dir: Path) -> List[Dict[str, Any]]:
    sections_path = out_dir / "ingest" / "web_docs" / "sections.json"
    return json.loads(sections_path.read_text(encoding="utf-8"))["sections"]


def _criterion_1_order_reproduces_index(out_dir: Path) -> Tuple[bool, str]:
    expected = json.loads((EXPECTED / "order.json").read_text(encoding="utf-8"))
    sections = _load_sections(out_dir)
    expected_order = expected["criterion_1_order_reproduces_index"]["expected_section_order"]
    actual_order = [s["url_path"] for s in sections if s["url_path"] != "index.html"]
    if actual_order != expected_order:
        return False, f"order mismatch: expected {expected_order}, got {actual_order}"
    msg = f"order matches: {' -> '.join(actual_order)}"
    return True, msg


def _criterion_2_no_boilerplate(out_dir: Path) -> Tuple[bool, str]:
    expected = json.loads((EXPECTED / "no-boilerplate.json").read_text(encoding="utf-8"))
    avoid = expected["criterion_2_no_boilerplate"]["boilerplate_strings_to_avoid"]
    sections = _load_sections(out_dir)
    found = {}
    for s in sections:
        text = s.get("text", "")
        for bp in avoid:
            if bp in text:
                found.setdefault(bp, []).append(s["url_path"])
    if found:
        return False, f"boilerplate found in SDM: {found}"
    msg = f"no boilerplate in {len(sections)} sections"
    return True, msg


def _criterion_3_canonical_url_deep(out_dir: Path) -> Tuple[bool, str]:
    expected = json.loads((EXPECTED / "canonical-urls.json").read_text(encoding="utf-8"))
    url_prefix = expected["criterion_3_canonical_url_deep"]["url_prefix"]
    sections = _load_sections(out_dir)
    bad = []
    for s in sections:
        cu = s.get("canonical_url", "")
        if not cu.startswith(url_prefix):
            bad.append(f"{s['url_path']}: {cu}")
        if cu == url_prefix.rstrip("/") or cu == url_prefix:
            bad.append(f"{s['url_path']}: canonical_url is just the root ({cu})")
    if bad:
        return False, f"canonical_url issues: {bad}"
    msg = f"all {len(sections)} sections have deep canonical_url"
    return True, msg


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="F29 eval runner")
    args = parser.parse_args(argv)

    total_passed = 0
    total_failed = 0
    failed_msgs: List[str] = []

    with tempfile.TemporaryDirectory(prefix="web-docs-eval-") as tmp:
        work = Path(tmp)
        try:
            _run_pipeline(work)
        except Exception as e:
            print(f"ERROR: failed to run pipeline: {e}")
            return 1

        for label, fn in (
            ("Criterion 1 (order reproduces index)", _criterion_1_order_reproduces_index),
            ("Criterion 2 (no boilerplate)", _criterion_2_no_boilerplate),
            ("Criterion 3 (canonical URL deep)", _criterion_3_canonical_url_deep),
        ):
            print(f"=== {label} ===")
            ok, msg = fn(work)
            tag = "PASS" if ok else "FAIL"
            print(f"  [{tag}] {msg}")
            if ok:
                total_passed += 1
            else:
                total_failed += 1
                failed_msgs.append(f"{label}: {msg}")

    print("")
    print(f"Resultado: {total_passed} PASS, {total_failed} FAIL")
    if failed_msgs:
        print("Fallos:")
        for f in failed_msgs:
            print(f"  - {f}")
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
