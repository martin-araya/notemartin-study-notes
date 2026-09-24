#!/usr/bin/env python3
"""run_eval.py — F26 eval: validates the 3 criteria of the roadmap.

Uso:
    python3 evals/review-sample/run_eval.py

Criterios verificados:
  1. El reporte muestra imagen y texto lado a lado.
  2. Los umbrales difieren por tipo y están justificados.
  3. Una fuente muy degradada no avanza sin confirmación.

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
FIXTURES = ROOT / "evals" / "review-sample" / "fixtures"
EXPECTED = ROOT / "evals" / "review-sample" / "expected"
REVIEW_PY = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "review_report.py"

PY = sys.executable


def _build_ingest_degraded(work: Path) -> Path:
    """Build an ingest/ tree for the degraded-source-fixture."""
    source_dir = work / "degraded" / "ingest"
    if source_dir.parent.exists():
        shutil.rmtree(source_dir.parent)
    source_dir.mkdir(parents=True)

    regions_payload = {
        "page": 1,
        "regions": [
            {"id": "r001", "class": "column", "semantic_class": "code",
             "bbox": [54, 700, 200, 30], "in_main_flow": True, "column_index": 0,
             "word_count": 2, "first_word": "def hello():", "last_word": "pass",
             "class_confidence": 0.42, "ambiguity": True,
             "alternative_classes": [{"class": "formula", "score": 0.30}],
             "signals": [{"signal": "S_MONOSPACE", "value": 1.0}],
             "word_indices": [0, 1], "sub_kind": None},
            {"id": "r002", "class": "column", "semantic_class": "table",
             "bbox": [54, 620, 280, 60], "in_main_flow": True, "column_index": 0,
             "word_count": 15, "first_word": "id", "last_word": "20.00",
             "class_confidence": 0.85, "ambiguity": False,
             "alternative_classes": [], "signals": [{"signal": "S_TABLE_GRID", "value": 1.0}],
             "word_indices": list(range(15)), "sub_kind": None},
            {"id": "r003", "class": "column", "semantic_class": "formula",
             "bbox": [54, 540, 300, 25], "in_main_flow": True, "column_index": 0,
             "word_count": 6, "first_word": "f(x)", "last_word": "\\beta",
             "class_confidence": 0.75, "ambiguity": False,
             "alternative_classes": [{"class": "code", "score": 0.50}],
             "signals": [{"signal": "S_SYMBOL_DENSITY", "value": 0.85}],
             "word_indices": list(range(6)), "sub_kind": None},
            {"id": "r004", "class": "column", "semantic_class": "text",
             "bbox": [54, 480, 300, 60], "in_main_flow": True, "column_index": 0,
             "word_count": 30, "first_word": "Some", "last_word": "noise.",
             "class_confidence": 0.85, "ambiguity": False,
             "alternative_classes": [], "signals": [],
             "word_indices": list(range(30)), "sub_kind": None},
        ],
    }
    (source_dir / "regions").mkdir()
    (source_dir / "regions" / "page-0001.regions.json").write_text(
        json.dumps(regions_payload, indent=2, ensure_ascii=False)
    )

    tables_payload = {
        "page": 1,
        "tables": [
            {"id": "t001", "region_id": "r002", "page_start": 1, "page_end": 1,
             "rows": 3, "cols": 3, "headers": [["id", "name", "price"]],
             "data": [["1", "Widget", "10.00"], ["2", "Gadget", "20.00"], ["3", "Gizmo", "15.00"]],
             "merged_cells": [], "cross_page_continued": False,
             "confidence": 0.85, "low_confidence": False, "warnings": [], "dwell_ms": 5,
             "bbox": [54, 620, 280, 60]}
        ],
    }
    (source_dir / "tables").mkdir()
    (source_dir / "tables" / "page-0001.tables.json").write_text(
        json.dumps(tables_payload, indent=2, ensure_ascii=False)
    )

    formulas_payload = {
        "page": 1,
        "formulas": [
            {"id": "f001", "latex": "f(x) = \\alpha x + \\beta",
             "latex_compiled": True, "compile_errors": [], "number": None,
             "inline": True, "pending": False, "image_path": None,
             "bbox": [54, 540, 300, 25], "page": 1, "dwell_ms": 5}
        ],
    }
    (source_dir / "formulas").mkdir()
    (source_dir / "formulas" / "page-0001.formulas.json").write_text(
        json.dumps(formulas_payload, indent=2, ensure_ascii=False)
    )

    code_payload = {
        "page": 1,
        "blocks": [
            {"id": "c001", "language": "python", "text": "def hello():\n    pass",
             "confidence": 0.42, "low_confidence": True,
             "low_confidence_reason": "ambiguous_monospace_chars",
             "corrections": [], "commands": [], "output": [],
             "bbox": [54, 700, 200, 30], "page": 1, "dwell_ms": 5}
        ],
    }
    (source_dir / "code").mkdir()
    (source_dir / "code" / "page-0001.code.json").write_text(
        json.dumps(code_payload, indent=2, ensure_ascii=False)
    )

    return work / "degraded"


def _build_ingest_blocked(work: Path) -> Path:
    """Build an ingest/ tree with 4 critical regions low_confidence."""
    source_dir = work / "blocked" / "ingest"
    if source_dir.parent.exists():
        shutil.rmtree(source_dir.parent)
    source_dir.mkdir(parents=True)

    regions_payload = {
        "page": 1,
        "regions": [
            {"id": "r001", "class": "column", "semantic_class": "code",
             "bbox": [54, 700, 200, 30], "in_main_flow": True, "column_index": 0,
             "word_count": 2, "first_word": "def foo():", "last_word": "pass",
             "class_confidence": 0.30, "ambiguity": True,
             "alternative_classes": [], "signals": [],
             "word_indices": [0, 1], "sub_kind": None},
            {"id": "r002", "class": "column", "semantic_class": "table",
             "bbox": [54, 620, 280, 60], "in_main_flow": True, "column_index": 0,
             "word_count": 15, "first_word": "id", "last_word": "20",
             "class_confidence": 0.40, "ambiguity": True,
             "alternative_classes": [], "signals": [],
             "word_indices": list(range(15)), "sub_kind": None},
            {"id": "r003", "class": "column", "semantic_class": "formula",
             "bbox": [54, 540, 300, 25], "in_main_flow": True, "column_index": 0,
             "word_count": 6, "first_word": "f(x)", "last_word": "\\fract",
             "class_confidence": 0.20, "ambiguity": True,
             "alternative_classes": [], "signals": [],
             "word_indices": list(range(6)), "sub_kind": None},
            {"id": "r004", "class": "column", "semantic_class": "syntax_diagram",
             "bbox": [54, 460, 200, 25], "in_main_flow": True, "column_index": 0,
             "word_count": 3, "first_word": "if", "last_word": "1",
             "class_confidence": 0.25, "ambiguity": True,
             "alternative_classes": [], "signals": [],
             "word_indices": list(range(3)), "sub_kind": None},
        ],
    }
    (source_dir / "regions").mkdir()
    (source_dir / "regions" / "page-0001.regions.json").write_text(
        json.dumps(regions_payload, indent=2, ensure_ascii=False)
    )
    for sub in ("tables", "formulas", "code"):
        (source_dir / sub).mkdir()
        (source_dir / sub / f"page-0001.{sub.replace('tables','tables').replace('formulas','formulas').replace('code','code')}.json").write_text(
            json.dumps({"page": 1, sub.rstrip('s') if sub != 'code' else 'blocks': []}, indent=2)
        )

    return work / "blocked"


def _create_fake_image(work: Path) -> Path:
    """Create a fake page-0001.processed.png for the degraded fixture."""
    try:
        from PIL import Image
    except ImportError:
        return None
    images_dir = work / "images"
    images_dir.mkdir(exist_ok=True)
    img = Image.new("RGB", (612, 792), color=(255, 255, 255))
    img.save(images_dir / "page-0001.processed.png")
    return images_dir


def _run_review(source: Path, out_dir: Path, images_dir: Optional[Path]) -> Tuple[int, Dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [PY, str(REVIEW_PY), "--source", str(source), "--out-dir", str(out_dir)]
    if images_dir is not None:
        cmd += ["--images-dir", str(images_dir)]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    summary_path = out_dir / "ingest" / "review" / "summary.json"
    if not summary_path.exists():
        raise RuntimeError(f"review_report failed (exit {res.returncode}): {res.stderr}")
    return res.returncode, json.loads(summary_path.read_text(encoding="utf-8"))


def _criterion_1_image_text_side_by_side(work: Path) -> Tuple[bool, str]:
    src = _build_ingest_degraded(work)
    out = work / "review-degraded"
    images_dir = _create_fake_image(work)
    rc, summary = _run_review(src, out, images_dir)
    if rc not in (0, 2):
        return False, f"unexpected exit code {rc}; summary={summary}"
    report_path = out / "ingest" / "review" / "report.html"
    if not report_path.exists():
        return False, "report.html not generated"
    html = report_path.read_text(encoding="utf-8")
    if "<img" not in html:
        return False, "no <img> tag in HTML"
    if '<pre class="region-text">' not in html:
        return False, 'no <pre class="region-text"> tag in HTML'
    if "<tr class=\"region-row\"" not in html:
        return False, "no <tr class=\"region-row\"> in HTML"
    return True, "HTML contains <img>, <pre class=\"region-text\">, <tr class=\"region-row\"> side by side"


def _criterion_2_thresholds_per_type(work: Path) -> Tuple[bool, str]:
    src = _build_ingest_degraded(work)
    out = work / "review-degraded-thresholds"
    rc, summary = _run_review(src, out, None)
    thresholds = summary.get("class_thresholds", {})
    expected_classes = json.loads((EXPECTED / "thresholds.json").read_text())["criterion_2_thresholds_per_type"]["required_classes"]
    missing = [c for c in expected_classes if c not in thresholds]
    if missing:
        return False, f"missing threshold for classes: {missing}"
    code_t = thresholds.get("code", 0)
    text_t = thresholds.get("text", 0)
    if code_t <= text_t:
        return False, f"code threshold ({code_t}) should be stricter than text ({text_t})"
    return True, f"thresholds per class: code={code_t} text={text_t}, all {len(thresholds)} classes present"


def _criterion_3_blocking(work: Path) -> Tuple[bool, str]:
    src = _build_ingest_blocked(work)
    out = work / "review-blocked"
    rc, summary = _run_review(src, out, None)
    expected_exit = json.loads((EXPECTED / "blocked.json").read_text())["criterion_3_blocking"]["must_have_exit_code"]
    if rc != expected_exit:
        return False, f"exit code {rc} (expected {expected_exit})"
    if not summary.get("blocked"):
        return False, f"summary.blocked={summary.get('blocked')} (expected True)"
    if summary.get("blocked_reason") != "too_many_low_confidence_critical_regions":
        return False, f"blocked_reason={summary.get('blocked_reason')!r}"
    critical_low = summary.get("critical_low_confidence_count", 0)
    return True, f"BLOCKED with exit={rc}, critical_low={critical_low}"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="F26 eval runner")
    args = parser.parse_args(argv)

    total_passed = 0
    total_failed = 0
    failed_msgs: List[str] = []

    with tempfile.TemporaryDirectory(prefix="review-eval-") as tmp:
        work = Path(tmp)
        print("=== Criterion 1 (image + text side by side) ===")
        ok, msg = _criterion_1_image_text_side_by_side(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok:
            total_passed += 1
        else:
            total_failed += 1
            failed_msgs.append(f"criterion 1: {msg}")

        print("\n=== Criterion 2 (thresholds per type) ===")
        ok, msg = _criterion_2_thresholds_per_type(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok:
            total_passed += 1
        else:
            total_failed += 1
            failed_msgs.append(f"criterion 2: {msg}")

        print("\n=== Criterion 3 (blocking) ===")
        ok, msg = _criterion_3_blocking(work)
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
