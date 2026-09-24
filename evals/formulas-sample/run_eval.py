#!/usr/bin/env python3
"""run_eval.py — F24 eval: validates the 3 criteria of the roadmap.

Uso:
    python3 evals/formulas-sample/run_eval.py

Criterios verificados:
  1. Todo LaTeX emitido compila.
  2. Una fórmula no reconocida se conserva como imagen marcada.
  3. Las referencias a ecuaciones numeradas siguen resolviendo.

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
FIXTURES = ROOT / "evals" / "formulas-sample" / "fixtures"
EXPECTED = ROOT / "evals" / "formulas-sample" / "expected"
PDF_NATIVE_PY = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "pdf_native.py"
LAYOUT_PY = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "layout.py"
REGIONS_PY = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "regions.py"
FORMULAS_PY = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "formulas.py"

PY = sys.executable


def _run_pipeline(pdf: Path, out_dir: Path, images_dir: Optional[Path] = None) -> Dict[str, Any]:
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
    cmd = [PY, str(FORMULAS_PY), "--source", str(out_dir / "ingest" / "regions"), "--out-dir", str(out_dir),
           "--fragments", str(src_dir / "fragments.json"), "--json-only"]
    if images_dir is not None:
        cmd += ["--images-dir", str(images_dir)]
    r4 = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if not (out_dir / "ingest" / "formulas" / "formulas_summary.json").exists():
        raise RuntimeError(f"formulas failed (exit {r4.returncode}): {r4.stderr}")
    return json.loads((out_dir / "ingest" / "formulas" / "formulas_summary.json").read_text(encoding="utf-8"))


def _load_page_formulas(out_dir: Path) -> List[Dict[str, Any]]:
    flat: List[Dict[str, Any]] = []
    for p_path in sorted((out_dir / "ingest" / "formulas").glob("page-*.formulas.json")):
        data = json.loads(p_path.read_text(encoding="utf-8"))
        for f in data.get("formulas", []):
            flat.append(f)
    return flat


def _criterion_1_latex_compiles(work: Path) -> Tuple[bool, str]:
    src = FIXTURES / "latex-fixture.pdf"
    expected = json.loads((EXPECTED / "latex.json").read_text(encoding="utf-8"))
    out = work / "latex-fixture"
    summary = _run_pipeline(src, out)
    compiled = summary.get("compiled_count", 0)
    pending = summary.get("pending_count", 0)
    min_compiled = expected["criterion_1_latex_compiles"]["min_compiled"]
    max_pending = expected["criterion_1_latex_compiles"]["max_pending"]
    if compiled < min_compiled:
        return False, f"compiled_count={compiled} (need ≥ {min_compiled})"
    if pending > max_pending:
        return False, f"pending_count={pending} (need ≤ {max_pending})"
    page_formulas = _load_page_formulas(out)
    bad = [f for f in page_formulas if not f.get("latex_compiled", False) or f.get("compile_errors")]
    if bad:
        return False, f"{len(bad)} formulas have compile errors"
    msg = f"compiled={compiled}, pending={pending}, all formulas compile"
    return True, msg


def _criterion_2_pending(work: Path) -> Tuple[bool, str]:
    src = FIXTURES / "pending-fixture.pdf"
    expected = json.loads((EXPECTED / "pending.json").read_text(encoding="utf-8"))
    out = work / "pending-fixture"
    images_dir = out / "_images"
    images_dir.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image
        for p in (1, 2):
            img = Image.new("RGB", (612, 792), color=(255, 255, 255))
            img.save(images_dir / f"page-{p:04d}.processed.png")
    except ImportError:
        pass

    summary = _run_pipeline(src, out, images_dir=images_dir)
    pending = summary.get("pending_formulas", [])
    min_pending = expected["criterion_2_pending_fallback"]["min_pending"]
    if len(pending) < min_pending:
        return False, f"pending_count={len(pending)} (need ≥ {min_pending})"
    for p in pending:
        if not p.get("image_path"):
            page_formulas = _load_page_formulas(out)
            match = next((f for f in page_formulas if f["id"] == p["region_id"]), None)
            if not match or not match.get("bbox"):
                return False, f"pending {p['region_id']} has neither image_path nor bbox"
    msg = f"pending_count={len(pending)}, all have image_path or bbox"
    return True, msg


def _criterion_3_numbered(work: Path) -> Tuple[bool, str]:
    src = FIXTURES / "numbered-equations-fixture.pdf"
    expected = json.loads((EXPECTED / "numbered.json").read_text(encoding="utf-8"))
    out = work / "numbered-equations-fixture"
    summary = _run_pipeline(src, out)
    idx = summary.get("equation_index", [])
    min_idx = expected["criterion_3_numbered_preservation"]["min_equation_index"]
    expected_numbers = set(expected["criterion_3_numbered_preservation"]["expected_numbers"])
    found_numbers = {e["number"] for e in idx if e.get("number")}
    if len(idx) < min_idx:
        return False, f"equation_index={len(idx)} (need ≥ {min_idx})"
    missing = expected_numbers - found_numbers
    if missing:
        return False, f"missing numbers in equation_index: {sorted(missing)}"
    msg = f"equation_index={len(idx)} entries, numbers: {sorted(found_numbers)}"
    return True, msg


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="F24 eval runner")
    args = parser.parse_args(argv)

    total_passed = 0
    total_failed = 0
    failed_msgs: List[str] = []

    with tempfile.TemporaryDirectory(prefix="formulas-eval-") as tmp:
        work = Path(tmp)
        print("=== Criterion 1 (LaTeX compiles) ===")
        ok, msg = _criterion_1_latex_compiles(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok:
            total_passed += 1
        else:
            total_failed += 1
            failed_msgs.append(f"criterion 1: {msg}")

        print("\n=== Criterion 2 (pending fallback) ===")
        ok, msg = _criterion_2_pending(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok:
            total_passed += 1
        else:
            total_failed += 1
            failed_msgs.append(f"criterion 2: {msg}")

        print("\n=== Criterion 3 (numbered preservation) ===")
        ok, msg = _criterion_3_numbered(work)
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
