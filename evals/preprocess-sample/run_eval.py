#!/usr/bin/env python3
"""run_eval.py — F19 eval: validates the 3 criteria of the roadmap.

Uso:
    python3 evals/preprocess-sample/run_eval.py

Criterios verificados:
  1. La fuente hostil mejora su tasa de acierto de OCR de forma medible.
  2. Las páginas rotadas se corrigen automáticamente.
  3. La imagen original nunca se destruye.

Códigos de salida:
    0 — PASS los 3 criterios
    1 — Algún FAIL
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "evals" / "preprocess-sample" / "fixtures"
EXPECTED = ROOT / "evals" / "preprocess-sample" / "expected"
SCRIPT = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "preprocess.py"

PY = sys.executable


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def _run_preprocess(source: Path, out_dir: Path, pipeline: Optional[List[str]] = None) -> Dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [PY, str(SCRIPT), "--source", str(source), "--out-dir", str(out_dir), "--json-only"]
    if pipeline is not None:
        cmd += ["--pipeline", ",".join(pipeline)]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if not (out_dir / "ingest" / "preprocess_summary.json").exists():
        raise RuntimeError(f"preprocess.py failed (exit {res.returncode}): {res.stderr}")
    return json.loads((out_dir / "ingest" / "preprocess_summary.json").read_text(encoding="utf-8"))


def _useful_rows(p: Path) -> int:
    """Count image rows with std dev > 30 (proxy for OCR-readability)."""
    import cv2
    import numpy as np
    img = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return 0
    return int(np.sum(np.std(img.astype(float), axis=1) > 30))


# ============================================================
# Criterion 1: hostile improves measurably
# ============================================================

def _criterion_1_hostile(work: Path) -> Tuple[bool, str]:
    src = FIXTURES / "hostile-scan.png"
    expected = json.loads((EXPECTED / "hostile-scan.json").read_text(encoding="utf-8"))
    out = work / "hostile"
    _run_preprocess(src, out)
    original_useful = _useful_rows(src)
    processed_path = out / "ingest" / "pages" / (src.stem + "-0001.processed.png")
    processed_useful = _useful_rows(processed_path)
    min_ratio = expected["criterion_1_improvement"]["min_improvement_ratio"]
    if original_useful == 0:
        return False, f"original has 0 useful rows (fixture broken)"
    ratio = processed_useful / original_useful
    ok = ratio >= min_ratio
    msg = f"original useful_rows={original_useful}, processed useful_rows={processed_useful}, ratio={ratio:.2f} (≥ {min_ratio})"
    return ok, msg


# ============================================================
# Criterion 2: rotated pages auto-corrected
# ============================================================

def _criterion_2_rotation(work: Path) -> Tuple[bool, str]:
    src = FIXTURES / "rotated-test.pdf"
    expected = json.loads((EXPECTED / "rotated-test.json").read_text(encoding="utf-8"))
    out = work / "rotated"
    data = _run_preprocess(src, out)
    rotations_expected = expected["criterion_2_rotation"]["page_rotations_deg"]
    applied_expected = expected["criterion_2_rotation"]["rotation_applied_expected"]
    tol = expected["criterion_2_rotation"]["tolerance_deg"]
    if len(data["pages"]) != len(rotations_expected):
        return False, f"page count mismatch: got {len(data['pages'])}, expected {len(rotations_expected)}"
    details = []
    for i, p in enumerate(data["pages"]):
        expected_abs = abs(rotations_expected[i])
        detected_abs = abs(p["rotation_detected_deg"])
        delta = abs(detected_abs - expected_abs)
        applied = p["rotation_applied"]
        if delta > tol:
            return False, f"page {p['page']}: |detected|={detected_abs:.2f}° vs |expected|={expected_abs:.2f}° (delta={delta:.2f}, tol={tol})"
        if applied != applied_expected[i]:
            return False, f"page {p['page']}: rotation_applied={applied} vs expected={applied_expected[i]}"
        details.append(f"p{p['page']}: |det|={detected_abs:.2f}° applied={applied}")
    return True, "rotation OK: " + "; ".join(details)


# ============================================================
# Criterion 3: original never destroyed
# ============================================================

def _criterion_3_preservation(work: Path) -> Tuple[bool, str]:
    files = ["rotated-test.pdf", "blank-test.pdf", "hostile-scan.png"]
    failures = []
    for name in files:
        p = FIXTURES / name
        before = _sha256(p)
        out = work / f"pres-{p.stem}"
        _run_preprocess(p, out)
        after = _sha256(p)
        if before != after:
            failures.append(f"{name}: hash changed {before[:8]}→{after[:8]}")
    if failures:
        return False, "original modified: " + "; ".join(failures)
    return True, f"original sha256 unchanged for all {len(files)} files"


# ============================================================
# Blank detection (auxiliary)
# ============================================================

def _blank_detection(work: Path) -> Tuple[bool, str]:
    src = FIXTURES / "blank-test.pdf"
    expected = json.loads((EXPECTED / "blank-test.json").read_text(encoding="utf-8"))
    out = work / "blank"
    data = _run_preprocess(src, out)
    is_blank_expected = expected["criterion_blank_detection"]["is_blank_expected"]
    failures = []
    for p in data["pages"]:
        exp = is_blank_expected.get(p["page"])
        if exp is None:
            continue
        if p["is_blank"] != exp:
            failures.append(f"page {p['page']}: is_blank={p['is_blank']} vs expected={exp}")
    if failures:
        return False, "; ".join(failures)
    return True, f"blank detection OK for {len(is_blank_expected)} pages"


# ============================================================
# Main
# ============================================================

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="F19 eval runner")
    args = parser.parse_args(argv)

    total_passed = 0
    total_failed = 0
    failed_msgs: List[str] = []

    with tempfile.TemporaryDirectory(prefix="preprocess-eval-") as tmp:
        work = Path(tmp)
        print("=== Criterion 1 (hostile improvement) ===")
        ok, msg = _criterion_1_hostile(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok:
            total_passed += 1
        else:
            total_failed += 1
            failed_msgs.append(f"criterion 1: {msg}")

        print("\n=== Criterion 2 (rotation auto-correction) ===")
        ok, msg = _criterion_2_rotation(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok:
            total_passed += 1
        else:
            total_failed += 1
            failed_msgs.append(f"criterion 2: {msg}")

        print("\n=== Criterion 3 (original preservation) ===")
        ok, msg = _criterion_3_preservation(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok:
            total_passed += 1
        else:
            total_failed += 1
            failed_msgs.append(f"criterion 3: {msg}")

        print("\n=== Auxiliary (blank detection) ===")
        ok, msg = _blank_detection(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok:
            total_passed += 1
        else:
            total_failed += 1
            failed_msgs.append(f"blank detection: {msg}")

    print("")
    print(f"Resultado: {total_passed} PASS, {total_failed} FAIL")
    if failed_msgs:
        print("Fallos:")
        for f in failed_msgs:
            print(f"  - {f}")
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
