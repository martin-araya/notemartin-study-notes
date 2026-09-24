#!/usr/bin/env python3
"""run_eval.py — F27 eval: validates the 3 criteria of the roadmap.

Uso:
    python3 evals/post-ocr-sample/run_eval.py

Criterios verificados:
  1. Toda corrección es rastreable a una regla o entrada de diccionario.
  2. Código y tablas quedan intactos.
  3. Cualquier corrección individual se puede revertir.

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
FIXTURES = ROOT / "evals" / "post-ocr-sample" / "fixtures"
DICT_PATH = ROOT / "evals" / "post-ocr-sample" / "dictionary.yaml"
EXPECTED = ROOT / "evals" / "post-ocr-sample" / "expected"
POST_OCR_PY = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "post_ocr.py"

PY = sys.executable


def _build_ingest_degraded(work: Path) -> Path:
    """Build a minimal ingest/ tree for prose-fixture: 1 region, semantic_class=text."""
    source_dir = work / "prose" / "ingest"
    if source_dir.parent.exists():
        shutil.rmtree(source_dir.parent)
    source_dir.mkdir(parents=True)

    regions_payload = {
        "page": 1,
        "regions": [
            {
                "id": "r001", "class": "column", "semantic_class": "text",
                "bbox": [54, 540, 504, 200], "in_main_flow": True, "column_index": 0,
                "word_count": 16,
                "first_word": "PostgresQL is a database that handles JSON. It has",
                "last_word": "transactions.",
                "class_confidence": 0.92, "ambiguity": False,
                "alternative_classes": [], "signals": [],
                "word_indices": list(range(16)), "sub_kind": None,
            },
        ],
    }
    (source_dir / "regions").mkdir()
    (source_dir / "regions" / "page-0001.regions.json").write_text(
        json.dumps(regions_payload, indent=2, ensure_ascii=False)
    )
    for sub in ("tables", "formulas", "code"):
        (source_dir / sub).mkdir()
        (source_dir / sub / f"page-0001.{sub}.json").write_text(
            json.dumps({"page": 1, "blocks" if sub == "code" else ("formulas" if sub == "formulas" else "tables"): []}, indent=2)
        )
    return work / "prose"


def _build_ingest_code(work: Path) -> Path:
    """Build a minimal ingest/ tree for code-fixture: 1 region, semantic_class=code."""
    source_dir = work / "code" / "ingest"
    if source_dir.parent.exists():
        shutil.rmtree(source_dir.parent)
    source_dir.mkdir(parents=True)

    regions_payload = {
        "page": 1,
        "regions": [
            {
                "id": "r001", "class": "column", "semantic_class": "code",
                "bbox": [54, 540, 504, 100], "in_main_flow": True, "column_index": 0,
                "word_count": 6,
                "first_word": "def hello():",
                "last_word": "0",
                "class_confidence": 0.95, "ambiguity": False,
                "alternative_classes": [], "signals": [],
                "word_indices": list(range(6)), "sub_kind": None,
            },
        ],
    }
    (source_dir / "regions").mkdir()
    (source_dir / "regions" / "page-0001.regions.json").write_text(
        json.dumps(regions_payload, indent=2, ensure_ascii=False)
    )
    for sub in ("tables", "formulas", "code"):
        (source_dir / sub).mkdir()
        (source_dir / sub / f"page-0001.{sub}.json").write_text(
            json.dumps({"page": 1, "blocks" if sub == "code" else ("formulas" if sub == "formulas" else "tables"): []}, indent=2)
        )
    return work / "code"


def _build_ingest_table(work: Path) -> Path:
    """Build a minimal ingest/ tree for table-fixture: 1 region, semantic_class=table."""
    source_dir = work / "table" / "ingest"
    if source_dir.parent.exists():
        shutil.rmtree(source_dir.parent)
    source_dir.mkdir(parents=True)

    regions_payload = {
        "page": 1,
        "regions": [
            {
                "id": "r001", "class": "column", "semantic_class": "table",
                "bbox": [54, 540, 504, 100], "in_main_flow": True, "column_index": 0,
                "word_count": 16,
                "first_word": "id name qty price",
                "last_word": "15.00",
                "class_confidence": 0.90, "ambiguity": False,
                "alternative_classes": [], "signals": [],
                "word_indices": list(range(16)), "sub_kind": None,
            },
        ],
    }
    (source_dir / "regions").mkdir()
    (source_dir / "regions" / "page-0001.regions.json").write_text(
        json.dumps(regions_payload, indent=2, ensure_ascii=False)
    )
    for sub in ("tables", "formulas", "code"):
        (source_dir / sub).mkdir()
        (source_dir / sub / f"page-0001.{sub}.json").write_text(
            json.dumps({"page": 1, "blocks" if sub == "code" else ("formulas" if sub == "formulas" else "tables"): []}, indent=2)
        )
    return work / "table"


def _build_ingest_revert(work: Path) -> Path:
    """Build a minimal ingest/ tree for revert-fixture."""
    source_dir = work / "revert" / "ingest"
    if source_dir.parent.exists():
        shutil.rmtree(source_dir.parent)
    source_dir.mkdir(parents=True)

    regions_payload = {
        "page": 1,
        "regions": [
            {
                "id": "r001", "class": "column", "semantic_class": "text",
                "bbox": [54, 540, 504, 100], "in_main_flow": True, "column_index": 0,
                "word_count": 5,
                "first_word": "Para uno.",
                "last_word": "Para dos.",
                "text": "Para uno.\n\n\n\nPara dos.",
                "class_confidence": 0.90, "ambiguity": False,
                "alternative_classes": [], "signals": [],
                "word_indices": list(range(5)), "sub_kind": None,
            },
        ],
    }
    (source_dir / "regions").mkdir()
    (source_dir / "regions" / "page-0001.regions.json").write_text(
        json.dumps(regions_payload, indent=2, ensure_ascii=False)
    )
    for sub in ("tables", "formulas", "code"):
        (source_dir / sub).mkdir()
        (source_dir / sub / f"page-0001.{sub}.json").write_text(
            json.dumps({"page": 1, "blocks" if sub == "code" else ("formulas" if sub == "formulas" else "tables"): []}, indent=2)
        )
    return work / "revert"


def _run_post_ocr(source: Path, out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(
        [PY, str(POST_OCR_PY), "--source", str(source), "--out-dir", str(out_dir),
         "--dictionary", str(DICT_PATH)],
        capture_output=True, text=True, timeout=60,
    )
    return res.returncode


def _criterion_1_corrections_traceable(work: Path) -> Tuple[bool, str]:
    src = _build_ingest_degraded(work)
    out = work / "review-prose"
    rc = _run_post_ocr(src, out)
    p = out / "ingest" / "post_ocr" / "page-0001.post_ocr.json"
    if not p.exists():
        return False, "post_ocr.json not generated"
    data = json.loads(p.read_text(encoding="utf-8"))
    regions = data.get("regions", [])
    if not regions:
        return False, "no regions in post_ocr.json"
    region = regions[0]
    corrections = region.get("corrections", [])
    if not corrections:
        return False, "no corrections applied"
    required_fields = ["correction_id", "char_pos", "char_end", "original", "corrected", "applied_at"]
    for c in corrections:
        for field in required_fields:
            if field not in c:
                return False, f"correction missing field '{field}'"
        if not c.get("rule_id") and not c.get("dict_id"):
            return False, f"correction missing source (rule_id or dict_id)"
    return True, f"{len(corrections)} corrections, all with required fields and source"


def _criterion_2_code_table_intact(work: Path) -> Tuple[bool, str]:
    src_code = _build_ingest_code(work)
    src_table = _build_ingest_table(work)
    out_code = work / "review-code"
    out_table = work / "review-table"
    _run_post_ocr(src_code, out_code)
    _run_post_ocr(src_table, out_table)
    for label, out in [("code", out_code), ("table", out_table)]:
        p = out / "ingest" / "post_ocr" / "page-0001.post_ocr.json"
        if not p.exists():
            return False, f"{label}: post_ocr.json not generated"
        data = json.loads(p.read_text(encoding="utf-8"))
        for region in data.get("regions", []):
            if region["semantic_class"] not in ("code", "console", "table", "syntax_diagram"):
                continue
            if region["corrected_text"] != region["original_text"]:
                return False, f"{label} region {region['id']} was modified! corrected != original"
            if region.get("corrections"):
                return False, f"{label} region {region['id']} has corrections"
            if not region.get("skipped"):
                return False, f"{label} region {region['id']} not marked skipped"
    return True, "code and table regions intact (skipped=True, corrected==original)"


def _criterion_3_revertible(work: Path) -> Tuple[bool, str]:
    src = _build_ingest_revert(work)
    out = work / "review-revert"
    rc = _run_post_ocr(src, out)
    p = out / "ingest" / "post_ocr" / "page-0001.post_ocr.json"
    if not p.exists():
        return False, "post_ocr.json not generated"
    data_before = json.loads(p.read_text(encoding="utf-8"))
    region_before = data_before["regions"][0]
    corrections = region_before.get("corrections", [])
    if not corrections:
        return False, "no corrections applied to revert"
    target_id = corrections[0]["correction_id"]
    text_before = region_before["corrected_text"]

    res = subprocess.run(
        [PY, str(POST_OCR_PY), "--source", str(src), "--out-dir", str(out),
         "--revert", target_id],
        capture_output=True, text=True, timeout=60,
    )
    if res.returncode != 0:
        return False, f"revert failed: exit={res.returncode}, stderr={res.stderr}"
    data_after = json.loads(p.read_text(encoding="utf-8"))
    region_after = data_after["regions"][0]
    text_after = region_after["corrected_text"]
    if text_after != region_before["original_text"]:
        return False, f"text not reverted: after={text_after!r}, expected={region_before['original_text']!r}"
    return True, f"reverted {target_id}: text restored to original"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="F27 eval runner")
    args = parser.parse_args(argv)

    total_passed = 0
    total_failed = 0
    failed_msgs: List[str] = []

    with tempfile.TemporaryDirectory(prefix="post-ocr-eval-") as tmp:
        work = Path(tmp)
        print("=== Criterion 1 (corrections traceable) ===")
        ok, msg = _criterion_1_corrections_traceable(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok:
            total_passed += 1
        else:
            total_failed += 1
            failed_msgs.append(f"criterion 1: {msg}")

        print("\n=== Criterion 2 (code and table intact) ===")
        ok, msg = _criterion_2_code_table_intact(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok:
            total_passed += 1
        else:
            total_failed += 1
            failed_msgs.append(f"criterion 2: {msg}")

        print("\n=== Criterion 3 (revertible) ===")
        ok, msg = _criterion_3_revertible(work)
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
