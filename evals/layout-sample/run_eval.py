#!/usr/bin/env python3
"""run_eval.py — F21 eval: validates the 3 criteria of the roadmap.

Uso:
    python3 evals/layout-sample/run_eval.py

Criterios verificados:
  1. Un documento a dos columnas se reconstruye en orden correcto.
  2. Una tabla que cruza páginas se reunifica.
  3. La verificación detecta un orden roto inyectado a propósito.

Códigos de salida:
    0 — PASS los 3 criterios
    1 — Algún FAIL
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "evals" / "layout-sample" / "fixtures"
EXPECTED = ROOT / "evals" / "layout-sample" / "expected"
LAYOUT_PY = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "layout.py"
PDF_NATIVE_PY = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "pdf_native.py"

PY = sys.executable


def _run_layout(pdf: Path, out_dir: Path) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    src_dir = out_dir / "_src"
    src_dir.mkdir(parents=True, exist_ok=True)
    r1 = subprocess.run(
        [PY, str(PDF_NATIVE_PY), "--source", str(pdf), "--out-dir", str(src_dir), "--json-only"],
        capture_output=True, text=True, timeout=300,
    )
    if not (src_dir / "fragments.json").exists():
        raise RuntimeError(f"pdf_native failed (exit {r1.returncode}): {r1.stderr}")
    r2 = subprocess.run(
        [PY, str(LAYOUT_PY), "--source", str(src_dir / "fragments.json"), "--out-dir", str(out_dir), "--json-only"],
        capture_output=True, text=True, timeout=300,
    )
    if not (out_dir / "ingest" / "layout" / "layout_summary.json").exists():
        raise RuntimeError(f"layout failed (exit {r2.returncode}): {r2.stderr}")
    return json.loads((out_dir / "ingest" / "layout" / "layout_summary.json").read_text(encoding="utf-8"))


def _criterion_1_column_order(work: Path) -> Tuple[bool, str]:
    src = FIXTURES / "two-column-fixture.pdf"
    expected = json.loads((EXPECTED / "two-column.json").read_text(encoding="utf-8"))
    data = _run_layout(src, work / "two-column")
    cols_p1 = data["pages"][0]["column_count"]
    cols_p2 = data["pages"][1]["column_count"]
    valid_p1 = data["pages"][0]["reading_order_valid"]
    valid_p2 = data["pages"][1]["reading_order_valid"]
    min_cols = expected["criterion_1_column_order"]["min_pages_with_cols_ge_2"]
    cols_ok = (cols_p1 >= 2) and (cols_p2 >= 2)
    valid_ok = valid_p1 and valid_p2
    ok = cols_ok and valid_ok
    msg = f"p1 cols={cols_p1} valid={valid_p1}; p2 cols={cols_p2} valid={valid_p2} (need ≥ {min_cols} pages with cols≥2)"
    return ok, msg


def _criterion_2_cross_page_table(work: Path) -> Tuple[bool, str]:
    src = FIXTURES / "cross-page-table.pdf"
    expected = json.loads((EXPECTED / "cross-page-table.json").read_text(encoding="utf-8"))
    data = _run_layout(src, work / "cross-page")
    table_links = [l for l in data.get("cross_page_links", []) if l.get("type") == "table"]
    min_links = expected["criterion_2_cross_page_table"]["min_table_links"]
    ok = len(table_links) >= min_links
    msg = f"cross_page_links type=table: {len(table_links)} (need ≥ {min_links})"
    return ok, msg


def _criterion_3_broken_order(work: Path) -> Tuple[bool, str]:
    """Inject a synthetic broken order and verify the verifier detects it."""
    import sys as _sys
    layout_dir = str(LAYOUT_PY.parent)
    if layout_dir not in _sys.path:
        _sys.path.insert(0, layout_dir)
    import importlib
    if "layout" in _sys.modules:
        layout_mod = _sys.modules["layout"]
    else:
        layout_mod = importlib.import_module("layout")
    regions = [
        layout_mod.Region(
            id="r001", cls="column", bbox=(0, 0, 100, 100),
            in_main_flow=True, column_index=0, word_indices=[0],
            first_word="A", last_word="A.", y_centroid=200,
        ),
        layout_mod.Region(
            id="r002", cls="column", bbox=(0, 0, 100, 100),
            in_main_flow=True, column_index=1, word_indices=[1],
            first_word="B", last_word="B.", y_centroid=200,
        ),
    ]
    columns = [(0, 100), (100, 200)]
    valid, inconsistencies = layout_mod.verify_reading_order(regions, ["r002", "r001"], columns)
    if valid:
        return False, "verify_reading_order did NOT detect reversed order (expected valid=False)"
    if len(inconsistencies) < 1:
        return False, "no inconsistencies reported"
    if inconsistencies[0].get("kind") != "column_order_inverted":
        return False, f"wrong inconsistency kind: {inconsistencies[0].get('kind')}"
    valid_ok, _ = layout_mod.verify_reading_order(regions, ["r001", "r002"], columns)
    if not valid_ok:
        return False, "verify_reading_order falsely flagged correct order as broken"
    msg = (
        f"verify_reading_order: reversed → valid=False, inconsistencies={len(inconsistencies)} "
        f"(kind=column_order_inverted); in-order → valid=True"
    )
    return True, msg


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="F21 eval runner")
    args = parser.parse_args(argv)

    total_passed = 0
    total_failed = 0
    failed_msgs: List[str] = []

    with tempfile.TemporaryDirectory(prefix="layout-eval-") as tmp:
        work = Path(tmp)
        print("=== Criterion 1 (two-column order) ===")
        ok, msg = _criterion_1_column_order(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok:
            total_passed += 1
        else:
            total_failed += 1
            failed_msgs.append(f"criterion 1: {msg}")

        print("\n=== Criterion 2 (cross-page table) ===")
        ok, msg = _criterion_2_cross_page_table(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok:
            total_passed += 1
        else:
            total_failed += 1
            failed_msgs.append(f"criterion 2: {msg}")

        print("\n=== Criterion 3 (broken-order detection) ===")
        ok, msg = _criterion_3_broken_order(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok:
            total_passed += 1
        else:
            total_failed += 1
            failed_msgs.append(f"criterion 3: {msg}")

    print("")
    print(f"Resultado: {total_passed} PASS, {total_failed} FAIL")
    if failed_msgs:
        print("Fallos:")
        for f in failed_msgs:
            print(f"  - {f}")
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
