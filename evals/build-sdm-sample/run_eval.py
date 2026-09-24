#!/usr/bin/env python3
"""run_eval.py — F31 eval runner.

Verifica los 3 criterios de la Fase 31 contra los 4 fixtures sintéticos más
los 15 SDMs canónicos de F13 (round-trip via validate_sdm.py).

Uso:
    python3 evals/build-sdm-sample/run_eval.py
    # o:
    python3 evals/build-sdm-sample/run_eval.py --skip-golden

Criterios verificados:
  1. Valida contra el esquema para todas las fuentes del corpus.
  2. Los ids son idénticos entre ejecuciones.
  3. Toda figura tiene su pie asociado cuando existe.

Códigos de salida:
    0 — PASS los 3 criterios
    1 — Algún FAIL
    2 — Setup error (fixture build failed, etc.)
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
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "evals" / "build-sdm-sample" / "fixtures"
EXPECTED = ROOT / "evals" / "build-sdm-sample" / "expected"
GOLDEN_SDM_DIR = ROOT / "evals" / "sdm-sample"
BUILD_SDM = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "build_sdm.py"
VALIDATE_SDM = ROOT / "scripts" / "util" / "validate_sdm.py"

PY = sys.executable

# Fixture sources exercised by the eval (in order of execution).
SOURCES = ["source-pdf", "source-html", "source-ocr", "source-multi-format"]


def _build_fixtures() -> bool:
    """Re-build fixtures via build_fixtures.py to be sure they are fresh."""
    build_py = ROOT / "evals" / "build-sdm-sample" / "build_fixtures.py"
    r = subprocess.run([PY, str(build_py)], capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        return False
    return True


def _run_build_sdm(
    ingest_dir: Path, source_meta: Path, out_dir: Path, deterministic: bool = True
) -> Tuple[int, str]:
    args = [
        PY, str(BUILD_SDM),
        "--ingest-dir", str(ingest_dir),
        "--source-meta", str(source_meta),
        "--out-dir", str(out_dir),
    ]
    if deterministic:
        args.append("--check-determinism")
    r = subprocess.run(args, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def _read_summary(out_dir: Path) -> Dict[str, Any]:
    p = out_dir / "build_sdm_summary.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _read_sdm(out_dir: Path) -> Dict[str, Any]:
    p = out_dir / "sdm.json"
    return json.loads(p.read_text(encoding="utf-8"))


# ============================================================
# Criterion 1: validates against the schema for all sources in the corpus.
# ============================================================

def _criterion_1_schema_validation(work: Path) -> Tuple[bool, List[str]]:
    """Build SDMs from the 4 fixtures and validate against sdm.schema.json.
    Additionally round-trip-validate the 15 golden SDMs from F13."""
    messages: List[str] = []
    all_ok = True

    # 4 fresh fixtures
    for src in SOURCES:
        out = work / src
        exit_code, stderr = _run_build_sdm(
            FIX / src,
            FIX / src / "source_meta.yaml",
            out,
            deterministic=True,
        )
        if exit_code not in (0, 2):
            all_ok = False
            messages.append(f"[FAIL] build_sdm {src} exit={exit_code}: {stderr}")
            continue
        # Validate via the dedicated script.
        proc = subprocess.run(
            [PY, str(VALIDATE_SDM), "--validate", str(out / "sdm.json")],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            all_ok = False
            messages.append(f"[FAIL] validate {src}: {proc.stderr.strip()}")
        else:
            messages.append(f"[OK] {src} schema validates")

    # 15 golden SDMs from F13
    for golden in sorted(GOLDEN_SDM_DIR.glob("*.json")):
        proc = subprocess.run(
            [PY, str(VALIDATE_SDM), "--validate", str(golden)],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            all_ok = False
            messages.append(f"[FAIL] golden {golden.name}: {proc.stderr.strip()}")
        else:
            messages.append(f"[OK] golden {golden.name}")

    return all_ok, messages


# ============================================================
# Criterion 2: ids are identical between runs.
# ============================================================

def _criterion_2_determinism(work: Path) -> Tuple[bool, List[str]]:
    """For each fixture source, run build_sdm twice and diff the outputs."""
    messages: List[str] = []
    all_ok = True

    for src in SOURCES:
        out = work / f"det-{src}"
        exit_code, stderr = _run_build_sdm(
            FIX / src,
            FIX / src / "source_meta.yaml",
            out,
            deterministic=True,
        )
        if exit_code not in (0, 2):
            all_ok = False
            messages.append(f"[FAIL] det {src}: build exit={exit_code}: {stderr}")
            continue
        # build_sdm already runs twice under --check-determinism; consult summary.
        s = _read_summary(out)
        ident = s.get("determinism", {}).get("identical")
        if ident is True:
            messages.append(f"[OK] {src} deterministic across 2 runs")
        else:
            all_ok = False
            messages.append(
                f"[FAIL] {src} not deterministic: determinism={s.get('determinism')}"
            )

    # Also verify the build_sdm.compute_block_id matches validate_sdm.compute_block_id.
    import importlib.util
    sys.path.insert(0, str(BUILD_SDM.parent))
    import build_sdm as bs_mod  # type: ignore
    sys.path.insert(0, str(VALIDATE_SDM.parent))
    spec = importlib.util.spec_from_file_location("validate_sdm", VALIDATE_SDM)
    vs_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vs_mod)
    match = True
    for i in range(1000):
        h = hashlib.sha1(f"seed-{i}".encode()).hexdigest()
        a = bs_mod.compute_block_id(h, f"/s/{i}", i)
        b = vs_mod.compute_block_id(h, f"/s/{i}", i)
        if a != b:
            match = False
            messages.append(f"[FAIL] parity mismatch at i={i}: bs={a} vs={b}")
            break
    if match:
        messages.append("[OK] compute_block_id parity verified (1000 samples)")
    else:
        all_ok = False

    return all_ok, messages


# ============================================================
# Criterion 3: every figure has its caption attached when one exists.
# ============================================================

def _criterion_3_captions(work: Path) -> Tuple[bool, List[str]]:
    messages: List[str] = []
    all_ok = True

    # Source-pdf: 1 figure with caption, 0 orphan
    src = "source-pdf"
    out = work / f"cap-{src}"
    exit_code, stderr = _run_build_sdm(
        FIX / src,
        FIX / src / "source_meta.yaml",
        out,
        deterministic=True,
    )
    if exit_code not in (0, 2):
        all_ok = False
        messages.append(f"[FAIL] cap {src}: exit={exit_code}: {stderr}")
        return all_ok, messages
    s = _read_summary(out)
    expectations = json.loads((EXPECTED / "pdf-expectations.json").read_text(encoding="utf-8"))
    if s["figures"] != expectations["figures_count"]:
        all_ok = False
        messages.append(f"[FAIL] figures={s['figures']} != {expectations['figures_count']}")
    if s["captions_attached"] != expectations["captions_attached_count"]:
        all_ok = False
        messages.append(
            f"[FAIL] captions_attached={s['captions_attached']} != {expectations['captions_attached_count']}"
        )
    if s["figures_without_caption"] != expectations["figures_without_caption_count"]:
        all_ok = False
        messages.append(
            f"[FAIL] figures_without_caption={s['figures_without_caption']} != {expectations['figures_without_caption_count']}"
        )
    if s["captions_orphan"] != expectations["captions_orphan_count"]:
        all_ok = False
        messages.append(
            f"[FAIL] captions_orphan={s['captions_orphan']} != {expectations['captions_orphan_count']}"
        )
    if s["sections_count"] != expectations["sections_count"]:
        all_ok = False
        messages.append(
            f"[FAIL] sections={s['sections_count']} != {expectations['sections_count']}"
        )
    if all_ok:
        messages.append(
            f"[OK] {src}: figures=1 captions_attached=1 captions_orphan=0 sections=1"
        )

    # Source-html: 3 sections, 1 footnote with non-empty ref
    src = "source-html"
    out = work / f"cap-{src}"
    exit_code, stderr = _run_build_sdm(
        FIX / src,
        FIX / src / "source_meta.yaml",
        out,
        deterministic=True,
    )
    if exit_code not in (0, 2):
        all_ok = False
        messages.append(f"[FAIL] cap {src}: exit={exit_code}: {stderr}")
    else:
        sdm = _read_sdm(out)
        expectations = json.loads((EXPECTED / "html-expectations.json").read_text(encoding="utf-8"))
        sections_count = len(sdm.get("sections", []))
        if sections_count != expectations["sections_count"]:
            all_ok = False
            messages.append(f"[FAIL] {src} sections={sections_count} != {expectations['sections_count']}")
        # collect footnotes
        footnotes = []
        for sec in sdm.get("sections", []):
            for b in sec.get("blocks", []):
                if b.get("type") == "footnote":
                    footnotes.append(b)
        if len(footnotes) != expectations["footnotes_count"]:
            all_ok = False
            messages.append(f"[FAIL] {src} footnotes={len(footnotes)} != {expectations['footnotes_count']}")
        elif expectations["footnote_ref_non_empty"]:
            non_empty = all(bool((b.get("content") or {}).get("ref")) for b in footnotes)
            if not non_empty:
                all_ok = False
                messages.append(f"[FAIL] {src} has footnote with empty ref")
        if all_ok:
            messages.append(
                f"[OK] {src}: sections={sections_count} footnotes={len(footnotes)} (all refs non-empty)"
            )

    # Source-multi-format: 1 of each block type {heading, prose, code, formula, table}
    src = "source-multi-format"
    out = work / f"cap-{src}"
    exit_code, stderr = _run_build_sdm(
        FIX / src,
        FIX / src / "source_meta.yaml",
        out,
        deterministic=True,
    )
    if exit_code not in (0, 2):
        all_ok = False
        messages.append(f"[FAIL] cap {src}: exit={exit_code}: {stderr}")
    else:
        s = _read_summary(out)
        expectations = json.loads((EXPECTED / "multi-format-expectations.json").read_text(encoding="utf-8"))
        if s["blocks_by_type"] != expectations["blocks_by_type"]:
            all_ok = False
            messages.append(
                f"[FAIL] {src} blocks_by_type={s['blocks_by_type']} != {expectations['blocks_by_type']}"
            )
        if s["sections_count"] != expectations["sections_count"]:
            all_ok = False
            messages.append(f"[FAIL] {src} sections={s['sections_count']} != {expectations['sections_count']}")
        if all_ok:
            messages.append(f"[OK] {src}: all 5 expected block types present")

    # Source-ocr: 2 low-confidence blocks, all origin ocr
    src = "source-ocr"
    out = work / f"cap-{src}"
    exit_code, stderr = _run_build_sdm(
        FIX / src,
        FIX / src / "source_meta.yaml",
        out,
        deterministic=True,
    )
    if exit_code not in (0, 2):
        all_ok = False
        messages.append(f"[FAIL] cap {src}: exit={exit_code}: {stderr}")
    else:
        sdm = _read_sdm(out)
        expectations = json.loads((EXPECTED / "ocr-expectations.json").read_text(encoding="utf-8"))
        low_conf_count = sum(
            1
            for sec in sdm.get("sections", [])
            for b in sec.get("blocks", [])
            if b.get("confidence", 1.0) < 1.0
        )
        if low_conf_count < expectations["blocks_low_confidence"]:
            all_ok = False
            messages.append(
                f"[FAIL] {src} low_confidence blocks={low_conf_count} < {expectations['blocks_low_confidence']}"
            )
        if expectations["all_origin_ocr"]:
            all_ocr = all(
                b.get("origin") in ("ocr", "reconstructed")
                for sec in sdm.get("sections", [])
                for b in sec.get("blocks", [])
            )
            if not all_ocr:
                all_ok = False
                messages.append(f"[FAIL] {src} some block has origin=native with confidence<1")
        if all_ok:
            messages.append(
                f"[OK] {src}: {low_conf_count} low_confidence blocks, origin consistent"
            )

    return all_ok, messages


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="F31 eval runner")
    parser.add_argument("--skip-golden", action="store_true",
                        help="Skip validating the 15 golden SDMs from F13")
    parser.add_argument("--skip-build", action="store_true",
                        help="Skip rebuilding fixtures via build_fixtures.py")
    args = parser.parse_args(argv)

    if not args.skip_build and not _build_fixtures():
        sys.stderr.write("build_fixtures.py failed\n")
        return 2

    passed = 0
    failed = 0
    total_messages: List[str] = []

    with tempfile.TemporaryDirectory(prefix="f31-eval-") as tmp:
        work = Path(tmp)
        for label, runner in [
            ("Criterion 1 (schema validation)", _criterion_1_schema_validation if not args.skip_golden else None),
            ("Criterion 2 (deterministic ids)", _criterion_2_determinism),
            ("Criterion 3 (figure↔caption)", _criterion_3_captions),
        ]:
            if runner is None:
                continue
            ok, messages = runner(work)
            total_messages.append("")
            total_messages.append(f"=== {label} ===")
            for m in messages:
                total_messages.append("  " + m)
            if ok:
                passed += 1
                total_messages.append("  RESULT: PASS")
            else:
                failed += 1
                total_messages.append("  RESULT: FAIL")

    print("\n".join(total_messages))
    print("")
    print(f"Criterios: {passed} PASS, {failed} FAIL")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
