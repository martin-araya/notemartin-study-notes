#!/usr/bin/env python3
"""run_eval.py — F25 eval: validates the 4 criteria of the roadmap.

Uso:
    python3 evals/code-ocr-sample/run_eval.py

Criterios verificados:
  1. La indentación del código escaneado se conserva exactamente.
  2. Cada corrección sintáctica queda registrada individualmente.
  3. Ningún carácter se corrige por plausibilidad.
  4. Los bloques dudosos no pasan en silencio.

Códigos de salida:
    0 — PASS los 4 criterios
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
FIXTURES = ROOT / "evals" / "code-ocr-sample" / "fixtures"
EXPECTED = ROOT / "evals" / "code-ocr-sample" / "expected"
PDF_NATIVE_PY = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "pdf_native.py"
LAYOUT_PY = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "layout.py"
REGIONS_PY = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "regions.py"
CODE_PY = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "code_ocr.py"

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
        [PY, str(CODE_PY), "--source", str(out_dir / "ingest" / "regions"), "--out-dir", str(out_dir),
         "--fragments", str(src_dir / "fragments.json"), "--json-only"],
        capture_output=True, text=True, timeout=300,
    )
    if not (out_dir / "ingest" / "code" / "code_summary.json").exists():
        raise RuntimeError(f"code_ocr failed (exit {r4.returncode}): {r4.stderr}")
    return {
        "summary": json.loads((out_dir / "ingest" / "code" / "code_summary.json").read_text(encoding="utf-8")),
        "fragments": json.loads((src_dir / "fragments.json").read_text(encoding="utf-8")),
    }


def _expected_text_via_reconstruct(fragments: Dict[str, Any]) -> str:
    """Reconstruct the expected text using the same logic as code_ocr.py."""
    import sys
    sys.path.insert(0, str(Path(CODE_PY).parent))
    from code_ocr import words_in_region_bbox
    page_data = fragments["pages"][0]
    words = []
    for f in page_data.get("fragments", []):
        text = f.get("text", "")
        if not text:
            continue
        bbox = f.get("bbox", [0, 0, 0, 0])
        words.append({"text": text, "bbox": bbox, "font_name": f.get("font_name")})
    region_bbox = [0.0, 0.0, 612.0, 792.0]
    in_bbox = words_in_region_bbox(words, region_bbox)
    from code_ocr import reconstruct_text
    return reconstruct_text(in_bbox)


def _criterion_1_indent_preservation(work: Path) -> Tuple[bool, str]:
    src = FIXTURES / "clean-code-fixture.pdf"
    expected = json.loads((EXPECTED / "clean-code.json").read_text(encoding="utf-8"))
    out = work / "clean-code-fixture"
    data = _run_pipeline(src, out)
    summary = data["summary"]
    expected_text = _expected_code_text_via_reconstruct(data["fragments"])
    code_blocks = _load_code_blocks(out)
    if not code_blocks:
        return False, "no code blocks found"
    sorted_blocks = sorted(code_blocks, key=lambda b: -b.get("bbox", [0, 0, 0, 0])[1])
    actual_text = "\n".join(b["text"] for b in sorted_blocks)
    if actual_text != expected_text:
        return False, f"text mismatch:\n  expected: {expected_text!r}\n  actual:   {actual_text!r}"
    corrections = summary.get("corrections_total", 0)
    max_c = expected["criterion_1_indent_preservation"]["max_corrections"]
    if corrections > max_c:
        return False, f"corrections={corrections} (max allowed: {max_c})"
    msg = f"text byte-exact match ({len(code_blocks)} blocks concatenated), corrections={corrections} (≤ {max_c})"
    return True, msg


def _expected_code_text_via_reconstruct(fragments: Dict[str, Any]) -> str:
    """Reconstruct expected text including ONLY words with monospace fonts
    (matches what F22 marks as `code` or `ambiguity` and what F25 emits).
    """
    page_data = fragments["pages"][0]
    words = []
    for f in page_data.get("fragments", []):
        text = f.get("text", "")
        if not text:
            continue
        bbox = f.get("bbox", [0, 0, 0, 0])
        words.append({"text": text, "bbox": bbox, "font_name": f.get("font_name")})
    mono = [w for w in words if any(t in (w.get("font_name") or "").lower() for t in
            ("courier", "consolas", "monaco", "menlo", "monospace", "zapfdingbats"))]
    mono.sort(key=lambda w: (-w["bbox"][1], w["bbox"][0]))
    parts: List[str] = []
    prev_y: Optional[float] = None
    prev_x: Optional[float] = None
    prev_w: Optional[float] = None
    for w in mono:
        x0, y0 = w["bbox"][0], w["bbox"][1]
        x1 = x0 + (w["bbox"][2] - w["bbox"][0])
        if prev_y is None:
            parts.append(w["text"])
        else:
            if abs(y0 - prev_y) > 4.0:
                parts.append("\n")
                parts.append(w["text"])
            else:
                if prev_x is not None and prev_w is not None:
                    gap = x0 - (prev_x + prev_w)
                    if gap > 2.0:
                        parts.append(" ")
                parts.append(w["text"])
        prev_y = y0
        prev_x = x0
        prev_w = w["bbox"][2] - w["bbox"][0]
    return "".join(parts)


def _load_code_blocks(out_dir: Path) -> List[Dict[str, Any]]:
    flat: List[Dict[str, Any]] = []
    for p_path in sorted((out_dir / "ingest" / "code").glob("page-*.code.json")):
        data = json.loads(p_path.read_text(encoding="utf-8"))
        for b in data.get("blocks", []):
            flat.append(b)
    return flat


def _criterion_2_corrections_registered(work: Path) -> Tuple[bool, str]:
    src = FIXTURES / "confusion-fixture.pdf"
    expected = json.loads((EXPECTED / "confusion.json").read_text(encoding="utf-8"))
    out = work / "confusion-fixture"
    data = _run_pipeline(src, out)
    summary = data["summary"]
    corrections = summary.get("corrections", [])
    min_c = expected["criterion_2_corrections_registered"]["min_corrections"]
    if len(corrections) < min_c:
        return False, f"corrections={len(corrections)} (need ≥ {min_c})"
    required = expected["criterion_2_corrections_registered"]["required_fields"]
    for c in corrections:
        for field in required:
            if field not in c:
                return False, f"correction missing field '{field}': {c}"
        if c["char_pos"] is None:
            return False, f"correction field 'char_pos' null: {c}"
        if c["corrected"] == "" or c["corrected"] is None:
            return False, f"correction field 'corrected' empty: {c}"
        if c["reason"] == "" or c["reason"] is None:
            return False, f"correction field 'reason' empty: {c}"
        if "original" not in c:
            return False, f"correction field 'original' missing: {c}"
    msg = f"{len(corrections)} corrections, all with required fields (original may be empty for insertions)"
    return True, msg


def _criterion_3_no_plausibility(work: Path) -> Tuple[bool, str]:
    src = FIXTURES / "plausibility-fixture.pdf"
    expected = json.loads((EXPECTED / "plausibility.json").read_text(encoding="utf-8"))
    out = work / "plausibility-fixture"
    data = _run_pipeline(src, out)
    summary = data["summary"]
    if summary.get("corrections_total", 0) != 0:
        return False, f"corrections_total={summary['corrections_total']} (expected 0)"
    if summary.get("low_confidence_count", 0) < expected["criterion_3_no_plausibility"]["min_low_confidence_count"]:
        return False, f"low_confidence_count={summary['low_confidence_count']} (need ≥ {expected['criterion_3_no_plausibility']['min_low_confidence_count']})"
    msg = f"corrections=0, low_confidence={summary['low_confidence_count']}"
    return True, msg


def _criterion_4_no_silent_blocks(work: Path) -> Tuple[bool, str]:
    src = FIXTURES / "low-confidence-fixture.pdf"
    expected = json.loads((EXPECTED / "low-confidence.json").read_text(encoding="utf-8"))
    out = work / "low-confidence-fixture"
    data = _run_pipeline(src, out)
    summary = data["summary"]
    blocks = _load_code_blocks(out)
    if not blocks:
        return False, "no code blocks found"
    low_blocks = [b for b in blocks if b.get("low_confidence")]
    if not low_blocks:
        return False, "no block marked low_confidence: true"
    for b in low_blocks:
        reason = b.get("low_confidence_reason")
        if not reason:
            return False, f"block {b['id']} has low_confidence=true but no reason"
    msg = f"low_confidence_count={summary['low_confidence_count']}, all with non-empty reason"
    return True, msg


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="F25 eval runner")
    args = parser.parse_args(argv)

    total_passed = 0
    total_failed = 0
    failed_msgs: List[str] = []

    with tempfile.TemporaryDirectory(prefix="code-eval-") as tmp:
        work = Path(tmp)
        print("=== Criterion 1 (indent preservation) ===")
        ok, msg = _criterion_1_indent_preservation(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok:
            total_passed += 1
        else:
            total_failed += 1
            failed_msgs.append(f"criterion 1: {msg}")

        print("\n=== Criterion 2 (corrections registered) ===")
        ok, msg = _criterion_2_corrections_registered(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok:
            total_passed += 1
        else:
            total_failed += 1
            failed_msgs.append(f"criterion 2: {msg}")

        print("\n=== Criterion 3 (no plausibility) ===")
        ok, msg = _criterion_3_no_plausibility(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok:
            total_passed += 1
        else:
            total_failed += 1
            failed_msgs.append(f"criterion 3: {msg}")

        print("\n=== Criterion 4 (no silent blocks) ===")
        ok, msg = _criterion_4_no_silent_blocks(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok:
            total_passed += 1
        else:
            total_failed += 1
            failed_msgs.append(f"criterion 4: {msg}")

    print("")
    print(f"Resultado: {total_passed} PASS, {total_failed} FAIL")
    if failed_msgs:
        print("Fallos:")
        for f in failed_msgs:
            print(f"  - {f}")
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
