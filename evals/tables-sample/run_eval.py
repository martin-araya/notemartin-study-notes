#!/usr/bin/env python3
"""run_eval.py — F23 eval: validates the 3 criteria of the roadmap.

Uso:
    python3 evals/tables-sample/run_eval.py

Criterios verificados:
  1. Una tabla escaneada de 30+ filas se extrae completa.
  2. Las celdas combinadas conservan su valor.
  3. Ninguna tabla se emite truncada ni resumida.

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
FIXTURES = ROOT / "evals" / "tables-sample" / "fixtures"
EXPECTED = ROOT / "evals" / "tables-sample" / "expected"
PDF_NATIVE_PY = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "pdf_native.py"
LAYOUT_PY = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "layout.py"
REGIONS_PY = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "regions.py"
TABLES_PY = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "tables.py"

PY = sys.executable


def _run_pipeline(pdf: Path, out_dir: Path) -> Dict[str, Any]:
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
    r3 = subprocess.run(
        [PY, str(REGIONS_PY), "--source", str(out_dir / "ingest" / "layout"), "--out-dir", str(out_dir),
         "--fragments", str(src_dir / "fragments.json"), "--json-only"],
        capture_output=True, text=True, timeout=300,
    )
    if not (out_dir / "ingest" / "regions" / "regions_summary.json").exists():
        raise RuntimeError(f"regions failed (exit {r3.returncode}): {r3.stderr}")
    r4 = subprocess.run(
        [PY, str(TABLES_PY), "--source", str(out_dir / "ingest" / "regions"), "--out-dir", str(out_dir),
         "--fragments", str(src_dir / "fragments.json"), "--json-only"],
        capture_output=True, text=True, timeout=300,
    )
    if not (out_dir / "ingest" / "tables" / "tables_summary.json").exists():
        raise RuntimeError(f"tables failed (exit {r4.returncode}): {r4.stderr}")
    return json.loads((out_dir / "ingest" / "tables" / "tables_summary.json").read_text(encoding="utf-8"))


def _load_tables_from_disk(out_dir: Path) -> List[Dict[str, Any]]:
    flat: List[Dict[str, Any]] = []
    for p_path in sorted((out_dir / "ingest" / "tables").glob("page-*.tables.json")):
        data = json.loads(p_path.read_text(encoding="utf-8"))
        for t in data.get("tables", []):
            flat.append(t)
    return flat


def _criterion_1_thirty_plus_rows(work: Path) -> Tuple[bool, str]:
    src = FIXTURES / "large-table-fixture.pdf"
    expected = json.loads((EXPECTED / "large-table.json").read_text(encoding="utf-8"))
    out = work / "large-table"
    summary = _run_pipeline(src, out)
    tables = summary.get("tables", [])
    if not tables:
        return False, "no tables detected"
    t = tables[0]
    rows = t.get("rows", 0)
    cols = t.get("cols", 0)
    page_tables = _load_tables_from_disk(out)
    page_t = page_tables[0] if page_tables else {}
    data = page_t.get("data", [])
    headers = page_t.get("headers", [])
    actual_data_rows = len(data) + len(headers) if headers else len(data)
    if rows < expected["criterion_1_thirty_plus_rows"]["expected_data_rows"]:
        return False, f"rows={rows} (need ≥ {expected['criterion_1_thirty_plus_rows']['expected_data_rows']})"
    if cols != expected["criterion_1_thirty_plus_rows"]["expected_cols"]:
        return False, f"cols={cols} (need {expected['criterion_1_thirty_plus_rows']['expected_cols']})"
    if actual_data_rows != expected["criterion_1_thirty_plus_rows"]["expected_rows"]:
        return False, f"total rows={actual_data_rows} (need {expected['criterion_1_thirty_plus_rows']['expected_rows']})"
    if any(len(row) != cols for row in data + (headers if headers else [])):
        return False, "inconsistent row widths"
    msg = f"rows={rows} (≥ 35), cols={cols}, total={actual_data_rows} (36), all rows have {cols} cells"
    return True, msg


def _criterion_2_merged_cells(work: Path) -> Tuple[bool, str]:
    src = FIXTURES / "merged-cells-fixture.pdf"
    expected = json.loads((EXPECTED / "merged-cells.json").read_text(encoding="utf-8"))
    out = work / "merged-cells"
    _run_pipeline(src, out)
    page_tables = _load_tables_from_disk(out)
    if not page_tables:
        return False, "no tables detected"
    t = page_tables[0]
    merged = t.get("merged_cells", [])
    min_count = expected["criterion_2_merged_cells_preserve_value"]["expected_merged_cells_min"]
    if len(merged) < min_count:
        return False, f"only {len(merged)} merged_cells (need ≥ {min_count})"
    values = {mc.get("value", "") for mc in merged}
    missing = [v for v in expected["criterion_2_merged_cells_preserve_value"]["must_contain_values"] if v not in values]
    if missing:
        return False, f"missing values in merged_cells: {missing}"
    msg = f"merged_cells={len(merged)}; preserved values: {sorted(values)}"
    return True, msg


def _criterion_3_no_truncation(work: Path) -> Tuple[bool, str]:
    src = FIXTURES / "cross-page-table-fixture.pdf"
    expected = json.loads((EXPECTED / "cross-page-table.json").read_text(encoding="utf-8"))
    out = work / "cross-page-table"
    summary = _run_pipeline(src, out)
    tables = summary.get("tables", [])
    if not tables:
        return False, "no tables detected"
    t = tables[0]
    rows = t.get("rows", 0)
    cross = t.get("cross_page_continued", False)
    expected_rows = expected["criterion_3_no_truncation"]["expected_total_rows"]
    if rows != expected_rows:
        return False, f"rows={rows} (need {expected_rows})"
    if not cross:
        return False, "cross_page_continued=false; expected true"
    msg = f"merged rows={rows}, cross_page_continued=true (no truncation)"
    return True, msg


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="F23 eval runner")
    args = parser.parse_args(argv)

    total_passed = 0
    total_failed = 0
    failed_msgs: List[str] = []

    with tempfile.TemporaryDirectory(prefix="tables-eval-") as tmp:
        work = Path(tmp)
        print("=== Criterion 1 (30+ rows, complete) ===")
        ok, msg = _criterion_1_thirty_plus_rows(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok:
            total_passed += 1
        else:
            total_failed += 1
            failed_msgs.append(f"criterion 1: {msg}")

        print("\n=== Criterion 2 (merged cells preserve value) ===")
        ok, msg = _criterion_2_merged_cells(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok:
            total_passed += 1
        else:
            total_failed += 1
            failed_msgs.append(f"criterion 2: {msg}")

        print("\n=== Criterion 3 (no truncation, cross-page merged) ===")
        ok, msg = _criterion_3_no_truncation(work)
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
