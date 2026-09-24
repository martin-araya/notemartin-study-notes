#!/usr/bin/env python3
"""run_eval.py — F22 eval: validates the 3 criteria of the roadmap.

Uso:
    python3 evals/regions-sample/run_eval.py

Criterios verificados:
  1. Distingue código de texto corrido con precisión alta en el corpus.
  2. Las cajas editoriales de los libros se detectan como tales.
  3. Toda región ambigua queda marcada.

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
FIXTURES = ROOT / "evals" / "regions-sample" / "fixtures"
EXPECTED = ROOT / "evals" / "regions-sample" / "expected"
PDF_NATIVE_PY = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "pdf_native.py"
LAYOUT_PY = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "layout.py"
REGIONS_PY = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "regions.py"

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
    return json.loads((out_dir / "ingest" / "regions" / "regions_summary.json").read_text(encoding="utf-8"))


def _all_regions(summary: Dict[str, Any], out_dir: Path) -> List[Dict[str, Any]]:
    """Collect all region records across pages."""
    flat: List[Dict[str, Any]] = []
    for p in summary.get("pages", []):
        flat.append(p)
    return flat


def _load_regions_from_disk(out_dir: Path) -> List[Dict[str, Any]]:
    flat: List[Dict[str, Any]] = []
    for p_path in sorted((out_dir / "ingest" / "regions").glob("page-*.regions.json")):
        data = json.loads(p_path.read_text(encoding="utf-8"))
        for r in data.get("regions", []):
            flat.append(r)
    return flat


def _criterion_1_code_vs_text(work: Path) -> Tuple[bool, str]:
    """Position-based ground truth:
      - right column (x_center >= 300): expected = code
      - left column heading area (y_center > 600): expected = heading
      - left column body (y_center <= 600): expected = text
    """
    src = FIXTURES / "code-vs-text-fixture.pdf"
    expected = json.loads((EXPECTED / "code-vs-text.json").read_text(encoding="utf-8"))
    out = work / "code-vs-text"
    summary = _run_pipeline(src, out)
    regions = _load_regions_from_disk(out)

    def expected_class(r: Dict[str, Any]) -> str:
        bbox = r.get("bbox", [0, 0, 0, 0])
        x_center = bbox[0] + bbox[2] / 2
        y_center = bbox[1] + bbox[3] / 2
        if x_center >= 300:
            return "code"
        if y_center > 600:
            return "heading"
        return "text"

    tp = fp = fn = tn = 0
    for r in regions:
        exp = expected_class(r)
        actual = r.get("semantic_class")
        is_amb = r.get("ambiguity", False)
        if exp == "code":
            if actual == "code" and not is_amb:
                tp += 1
            elif actual == "code" and is_amb:
                tp += 1  # ambiguous between code and other is partial match
            else:
                fn += 1
        else:
            if actual == "code":
                fp += 1
            else:
                tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    min_p = expected["criterion_1_code_vs_text"]["min_precision"]
    min_r = expected["criterion_1_code_vs_text"]["min_recall"]
    min_f1 = expected["criterion_1_code_vs_text"]["min_f1"]
    ok = precision >= min_p and recall >= min_r and f1 >= min_f1
    msg = (
        f"TP={tp} FP={fp} FN={fn} TN={tn}; "
        f"precision={precision:.2f} (≥ {min_p}) recall={recall:.2f} (≥ {min_r}) f1={f1:.2f} (≥ {min_f1})"
    )
    return ok, msg


def _criterion_2_editorial_boxes(work: Path) -> Tuple[bool, str]:
    src = FIXTURES / "editorial-boxes-fixture.pdf"
    expected = json.loads((EXPECTED / "editorial-boxes.json").read_text(encoding="utf-8"))
    out = work / "editorial-boxes"
    summary = _run_pipeline(src, out)
    regions = _load_regions_from_disk(out)
    notes = [r for r in regions if r.get("semantic_class") == "editorial_note"]
    min_count = expected["criterion_2_editorial_boxes"]["min_editorial_note_count"]
    ok = len(notes) >= min_count
    msg = f"editorial_note regions: {len(notes)} (need ≥ {min_count})"
    return ok, msg


def _criterion_3_ambiguity(work: Path) -> Tuple[bool, str]:
    src = FIXTURES / "ambiguous-region-fixture.pdf"
    expected = json.loads((EXPECTED / "ambiguous-region.json").read_text(encoding="utf-8"))
    out = work / "ambiguous-region"
    summary = _run_pipeline(src, out)
    regions = _load_regions_from_disk(out)
    ambiguous = [r for r in regions if r.get("ambiguity", False)]
    min_amb = expected["criterion_3_ambiguity_marked"]["min_ambiguous_regions"]
    if len(ambiguous) < min_amb:
        return False, f"only {len(ambiguous)} ambiguous regions; need ≥ {min_amb}"
    r = ambiguous[0]
    if expected["criterion_3_ambiguity_marked"]["require_semantic_class_null"]:
        if r.get("semantic_class") is not None:
            return False, f"semantic_class={r.get('semantic_class')!r}; expected null"
    alts = r.get("alternative_classes", [])
    min_alts = expected["criterion_3_ambiguity_marked"]["min_alternative_classes_length"]
    if len(alts) < min_alts:
        return False, f"only {len(alts)} alternative_classes; need ≥ {min_alts}"
    if expected["criterion_3_ambiguity_marked"]["alternative_classes_unique"]:
        classes = [a.get("class") for a in alts]
        if len(set(classes)) != len(classes):
            return False, f"alternative_classes not unique: {classes}"
    msg = (
        f"ambiguity OK: semantic_class=null, alternative_classes={[a['class'] for a in alts]} "
        f"({len(alts)} distinct classes)"
    )
    return True, msg


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="F22 eval runner")
    args = parser.parse_args(argv)

    total_passed = 0
    total_failed = 0
    failed_msgs: List[str] = []

    with tempfile.TemporaryDirectory(prefix="regions-eval-") as tmp:
        work = Path(tmp)
        print("=== Criterion 1 (code vs text) ===")
        ok, msg = _criterion_1_code_vs_text(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok:
            total_passed += 1
        else:
            total_failed += 1
            failed_msgs.append(f"criterion 1: {msg}")

        print("\n=== Criterion 2 (editorial boxes) ===")
        ok, msg = _criterion_2_editorial_boxes(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok:
            total_passed += 1
        else:
            total_failed += 1
            failed_msgs.append(f"criterion 2: {msg}")

        print("\n=== Criterion 3 (ambiguity) ===")
        ok, msg = _criterion_3_ambiguity(work)
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
