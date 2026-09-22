#!/usr/bin/env python3
"""run_eval.py — F20 eval: validates the 4 criteria of the roadmap.

Uso:
    python3 evals/ocr-sample/run_eval.py

Criterios verificados:
  1. La salida incluye confianza y caja por palabra.
  2. Un documento con ambos idiomas se procesa sin degradación notoria.
  3. El reintento se dispara y se registra.
  4. La instalación de cada motor está documentada por sistema operativo.

Códigos de salida:
    0 — PASS los 4 criterios (o skip graceful si Tesseract no instalado)
    1 — Algún FAIL

Si Tesseract no está instalado, los criterios 1-3 se saltan con nota; el
criterio 4 (documentación) sigue siendo verificable offline.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "evals" / "ocr-sample" / "fixtures"
EXPECTED = ROOT / "evals" / "ocr-sample" / "expected"
SPEC = ROOT / "skill" / "notemartin-study-notes" / "references" / "01-ingest" / "ocr-engines.md"
SCRIPT = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "ocr.py"

PY = sys.executable


def _tesseract_available() -> bool:
    return shutil.which("tesseract") is not None


def _run_ocr(source: Path, out_dir: Path, languages: str = "spa+eng") -> Dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(
        [PY, str(SCRIPT), "--source", str(source), "--out-dir", str(out_dir),
         "--languages", languages, "--json-only"],
        capture_output=True, text=True, timeout=600,
    )
    if not (out_dir / "ingest" / "ocr" / "ocr_summary.json").exists():
        raise RuntimeError(f"ocr.py failed (exit {res.returncode}): {res.stderr}")
    return json.loads((out_dir / "ingest" / "ocr" / "ocr_summary.json").read_text(encoding="utf-8"))


# ============================================================
# Criterion 1: word-level output
# ============================================================

def _criterion_1_word_level(work: Path) -> Tuple[bool, str]:
    if not _tesseract_available():
        return True, "SKIP (Tesseract not installed; criterion 4 still validates)"
    src = FIXTURES / "ocr-fixture.png"
    expected = json.loads((EXPECTED / "ocr-fixture.json").read_text(encoding="utf-8"))
    out = work / "ocr-fixture"
    data = _run_ocr(src, out, languages="eng")
    words = [w for p in data["pages"] for w in p["words"]]
    if not words:
        return False, "no words extracted"
    valid = sum(
        1 for w in words
        if w.get("conf", -1) >= 0
        and isinstance(w.get("bbox"), list)
        and len(w["bbox"]) == 4
        and w["bbox"][2] > 0
        and w["bbox"][3] > 0
    )
    pct = valid / len(words)
    min_pct = expected["criterion_1_word_level"]["min_pct_words_with_conf_ge_0_and_bbox_valid"]
    min_words = expected["criterion_1_word_level"]["min_words_with_valid_bbox_and_conf"]
    ok = pct >= min_pct and valid >= min_words
    msg = f"{valid}/{len(words)} words with conf >= 0 and valid bbox ({pct:.2%}, need >= {min_pct:.0%}); total >= {min_words}"
    return ok, msg


# ============================================================
# Criterion 2: multilingual
# ============================================================

def _criterion_2_multilingual(work: Path) -> Tuple[bool, str]:
    if not _tesseract_available():
        return True, "SKIP (Tesseract not installed)"
    src = FIXTURES / "bilingual-fixture.png"
    expected = json.loads((EXPECTED / "bilingual-fixture.json").read_text(encoding="utf-8"))
    out = work / "bilingual"
    data = _run_ocr(src, out, languages="spa+eng")
    words = [w for p in data["pages"] for w in p["words"]]
    mean_conf_pages = [p.get("mean_conf", 0) for p in data["pages"]]
    mean_conf = sum(mean_conf_pages) / max(len(mean_conf_pages), 1) if mean_conf_pages else 0
    min_words = expected["criterion_2_multilingual"]["min_words"]
    min_conf = expected["criterion_2_multilingual"]["min_mean_conf"] * 100
    ok = len(words) >= min_words and mean_conf >= min_conf
    msg = f"{len(words)} words (need >= {min_words}); mean_conf={mean_conf:.1f} (need >= {min_conf:.1f})"
    return ok, msg


# ============================================================
# Criterion 3: retry triggered
# ============================================================

def _criterion_3_retry(work: Path) -> Tuple[bool, str]:
    if not _tesseract_available():
        return True, "SKIP (Tesseract not installed)"
    src = FIXTURES / "low-confidence-fixture.png"
    expected = json.loads((EXPECTED / "low-confidence-fixture.json").read_text(encoding="utf-8"))
    out = work / "low-conf"
    data = _run_ocr(src, out, languages="eng")
    retries = data.get("retries", [])
    min_retries = expected["criterion_3_retry"]["min_retries"]
    if len(retries) < min_retries:
        return False, f"only {len(retries)} retries; expected >= {min_retries}. mean_conf was high enough not to trigger retry."
    has_reason = any("mean_conf" in r.get("reason", "") for r in retries)
    if not has_reason:
        return False, f"retries present but no reason mentions 'mean_conf': {retries}"
    actions = [r.get("action") for r in retries]
    msg = f"{len(retries)} retries: {actions}; reasons OK"
    return True, msg


# ============================================================
# Criterion 4: installation docs per SO
# ============================================================

def _criterion_4_install_docs() -> Tuple[bool, str]:
    if not SPEC.exists():
        return False, f"spec file missing: {SPEC}"
    md = SPEC.read_text(encoding="utf-8")
    missing = []
    if not re.search(r"macOS|mac ?os", md, re.IGNORECASE):
        missing.append("macOS")
    if not re.search(r"Ubuntu|Debian|apt", md, re.IGNORECASE):
        missing.append("Ubuntu/Debian (apt)")
    if not re.search(r"Windows", md, re.IGNORECASE):
        missing.append("Windows")
    if not re.search(r"brew install tesseract", md, re.IGNORECASE):
        missing.append("brew install command")
    if not re.search(r"apt install.*tesseract", md, re.IGNORECASE):
        missing.append("apt install command")
    if not re.search(r"tesseract --version", md):
        missing.append("tesseract --version verification")
    if missing:
        return False, f"missing: {missing}"
    return True, "macOS + Ubuntu/Debian + Windows sections present with commands and verification"


# ============================================================
# Main
# ============================================================

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="F20 eval runner")
    args = parser.parse_args(argv)

    total_passed = 0
    total_failed = 0
    failed_msgs: List[str] = []

    print(f"Tesseract available: {_tesseract_available()}")

    with tempfile.TemporaryDirectory(prefix="ocr-eval-") as tmp:
        work = Path(tmp)
        print("\n=== Criterion 1 (word-level output) ===")
        ok, msg = _criterion_1_word_level(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok and "SKIP" not in msg:
            total_passed += 1
        elif not ok:
            total_failed += 1
            failed_msgs.append(f"criterion 1: {msg}")

        print("\n=== Criterion 2 (multilingual) ===")
        ok, msg = _criterion_2_multilingual(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok and "SKIP" not in msg:
            total_passed += 1
        elif not ok:
            total_failed += 1
            failed_msgs.append(f"criterion 2: {msg}")

        print("\n=== Criterion 3 (retry triggered) ===")
        ok, msg = _criterion_3_retry(work)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if ok and "SKIP" not in msg:
            total_passed += 1
        elif not ok:
            total_failed += 1
            failed_msgs.append(f"criterion 3: {msg}")

    print("\n=== Criterion 4 (installation docs) ===")
    ok, msg = _criterion_4_install_docs()
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
