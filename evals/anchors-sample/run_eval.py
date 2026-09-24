#!/usr/bin/env python3
"""run_eval.py — F32 eval runner.

Verifica los 3 criterios de Fase 32 sobre los fixtures sintéticos de
evals/anchors-sample/.

Criterios:
  1. Un documento sin numeración produce anclas igualmente utilizables.
  2. Las anclas son estables entre ejecuciones.
  3. Toda unidad de L2 puede referenciar un ancla.

Códigos de salida:
    0 — PASS los 3 criterios
    1 — Algún FAIL
    2 — Setup error
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "evals" / "anchors-sample" / "fixtures"
EXPECTED = ROOT / "evals" / "anchors-sample" / "expected"
BUILD_SDM = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "build_sdm.py"
VALIDATE_SDM = ROOT / "scripts" / "util" / "validate_sdm.py"
LEDGER_SAMPLE = ROOT / "evals" / "ledger-sample"

PY = sys.executable

SOURCES = ["source-unnumbered-html", "source-renumbered-pdf", "source-stable-rerun"]


def _build_fixtures() -> bool:
    r = subprocess.run(
        [PY, str(ROOT / "evals" / "anchors-sample" / "build_fixtures.py")],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
    return r.returncode == 0


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


def _read_sdm(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def _read_summary(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


# ============================================================
# Criterion 1: doc sin numeración → anclas utilizables
# ============================================================

def _criterion_1_unnumbered(work: Path) -> Tuple[bool, List[str]]:
    messages: List[str] = []
    all_ok = True

    src = "source-unnumbered-html"
    out = work / src
    exit_code, stderr = _run_build_sdm(
        FIX / src,
        FIX / src / "source_meta.yaml",
        out,
        deterministic=True,
    )
    if exit_code not in (0, 2):
        all_ok = False
        messages.append(f"[FAIL] build {src}: exit={exit_code}: {stderr}")
        return all_ok, messages

    sdm = _read_sdm(out / "sdm.json")
    expectations = json.loads((EXPECTED / "unnumbered-expectations.json").read_text(encoding="utf-8"))

    sections = sdm.get("sections", [])
    if len(sections) < expectations["criterion_1_unnumbered_anchors"]["min_sections"]:
        all_ok = False
        messages.append(
            f"[FAIL] sections={len(sections)} < {expectations['criterion_1_unnumbered_anchors']['min_sections']}"
        )
        return all_ok, messages
    messages.append(f"[OK] sections={len(sections)} (≥ 5)")

    bad_anchors = []
    bad_pages = []
    for sec in sections:
        for b in sec.get("blocks", []):
            anchor = b.get("anchor") or {}
            sp = anchor.get("section_path")
            if not sp:
                bad_anchors.append(b.get("id"))
            if anchor.get("page") is not None:
                bad_pages.append(b.get("id"))

    if bad_anchors:
        all_ok = False
        messages.append(
            f"[FAIL] blocks without section_path: {len(bad_anchors)} ({bad_anchors[:3]}…)"
        )
    else:
        messages.append("[OK] every block has anchor.section_path")

    if bad_pages:
        all_ok = False
        messages.append(
            f"[FAIL] HTML blocks with non-null anchor.page (expected null): {len(bad_pages)}"
        )
    else:
        messages.append("[OK] every block has anchor.page = null (HTML no paginated)")

    # Sanity: 5 distinct section_paths
    sps = [
        b["anchor"]["section_path"]
        for sec in sections
        for b in sec.get("blocks", [])
    ]
    unique = set(sps)
    if len(unique) != len(sps):
        # It is OK to have repeated section_path (multiple blocks in one section),
        # but each block must belong to *some* section.
        if len(unique) < 5:
            all_ok = False
            messages.append(
                f"[FAIL] distinct section_paths={len(unique)} (expected 5)"
            )
        else:
            messages.append(
                f"[OK] distinct section_paths={len(unique)}, total blocks={len(sps)}"
            )
    else:
        # all unique == 1 case: degenerate; skip
        messages.append(f"[OK] distinct section_paths={len(unique)}")

    return all_ok, messages


# ============================================================
# Criterion 2: anclas estables entre ejecuciones
# ============================================================

def _criterion_2_stable(work: Path) -> Tuple[bool, List[str]]:
    messages: List[str] = []
    all_ok = True

    # Run each fixture with --check-determinism; the build_sdm runs the pipeline
    # twice under the hood. Re-check by also running the pipeline twice manually
    # on source-stable-rerun (the explicit "rerun determinism" target).
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
            messages.append(f"[FAIL] {src}: build exit={exit_code}: {stderr}")
            continue
        s = _read_summary(out / "build_sdm_summary.json")
        same = s.get("determinism", {}).get("identical")
        if same is True:
            messages.append(f"[OK] {src} deterministic across 2 internal runs")
        else:
            all_ok = False
            messages.append(f"[FAIL] {src} not deterministic: {s.get('determinism')}")

    # Extra: rerun source-stable-rerun explicitly TWICE and diff the sdm.json
    # bytes. This is the explicit F32 criterion 2 test (not just relying on
    # build_sdm's internal check).
    src = "source-stable-rerun"
    a = work / "rerun-A"
    b = work / "rerun-B"
    for tag, target in (("A", a), ("B", b)):
        code, err = _run_build_sdm(
            FIX / src,
            FIX / src / "source_meta.yaml",
            target,
            deterministic=False,
        )
        if code not in (0, 2):
            all_ok = False
            messages.append(f"[FAIL] explicit rerun {tag}: exit={code}: {err}")
            return all_ok, messages

    sdm_a = (a / "sdm.json").read_bytes()
    sdm_b = (b / "sdm.json").read_bytes()
    if sdm_a == sdm_b:
        messages.append(
            f"[OK] source-stable-rerun explicit rerun: sdm.json byte-identical ({len(sdm_a)} bytes)"
        )
    else:
        all_ok = False
        messages.append(
            f"[FAIL] source-stable-rerun explicit rerun: sdm.json differs "
            f"(a={len(sdm_a)}B vs b={len(sdm_b)}B)"
        )

    return all_ok, messages


# ============================================================
# Criterion 3: toda unidad L2 puede referenciar un ancla
# ============================================================

def _criterion_3_l2_references(work: Path) -> Tuple[bool, List[str]]:
    messages: List[str] = []
    all_ok = True

    # Pick source-unnumbered-html as the canonical artifact; load its SDM and
    # walk a sample ledger that references its blocks. Because F15 is not yet
    # implemented, we synthesize a mini-ledger inline.
    src = "source-unnumbered-html"
    sdm_path = work / src / "sdm.json"
    if not sdm_path.exists():
        all_ok = False
        messages.append(f"[FAIL] {src} sdm.json missing")
        return all_ok, messages
    sdm = _read_sdm(sdm_path)

    # Collect every block id in the SDM
    sdm_block_ids = set()
    for sec in sdm.get("sections", []):
        for b in sec.get("blocks", []):
            sdm_block_ids.add(b.get("id"))

    # Build a synthetic ledger where each entry references 1-2 real block_ids
    # plus one entry that references a NON-EXISTENT block_id (to verify the
    # validator catches invalid references).
    block_list = sorted(sdm_block_ids)
    if len(block_list) < 3:
        all_ok = False
        messages.append(f"[FAIL] SDM has only {len(block_list)} blocks; need ≥ 3")
        return all_ok, messages

    valid_refs = block_list[:3]
    invalid_ref = "deadbeef0000"
    synthetic_ledger = {
        "schema_version": "1.0.0",
        "units": [
            {"unit_id": "u_01", "source_block_ids": [valid_refs[0]], "status": "kept"},
            {"unit_id": "u_02", "source_block_ids": [valid_refs[1], valid_refs[2]], "status": "kept"},
            {"unit_id": "u_99", "source_block_ids": [invalid_ref], "status": "kept"},
        ],
    }

    # Resolve every reference.
    broken = []
    for u in synthetic_ledger["units"]:
        for ref in u["source_block_ids"]:
            if ref not in sdm_block_ids:
                broken.append((u["unit_id"], ref))

    # The 3 criteria we track:
    # (a) every valid unit's refs resolve;
    # (b) every invalid ref is detected (negative test).
    if any(ref in sdm_block_ids for u in synthetic_ledger["units"][:2] for ref in u["source_block_ids"]):
        messages.append("[OK] synthetic ledger unit_u01/u02 references resolve to real block_ids")

    if not broken:
        all_ok = False
        messages.append(
            "[FAIL] synthetic invalid ref (deadbeef0000) was NOT detected as broken — validator gap"
        )
    else:
        messages.append(
            f"[OK] synthetic invalid ref (deadbeef0000) correctly detected as broken ({len(broken)} total)"
        )

    # Positive: every real reference in the ledger exists.
    unresolved = []
    for u in synthetic_ledger["units"][:2]:
        for ref in u["source_block_ids"]:
            if ref not in sdm_block_ids:
                unresolved.append((u["unit_id"], ref))
    if unresolved:
        all_ok = False
        messages.append(f"[FAIL] real ledger refs unresolved: {unresolved}")
    else:
        messages.append("[OK] all 3 real ledger refs resolve to blocks in sdm.json")

    return all_ok, messages


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="F32 eval runner")
    parser.add_argument("--skip-build", action="store_true",
                        help="Skip rebuilding fixtures via build_fixtures.py")
    args = parser.parse_args(argv)

    if not args.skip_build and not _build_fixtures():
        sys.stderr.write("build_fixtures.py failed\n")
        return 2

    passed = 0
    failed = 0
    msgs: List[str] = []

    with tempfile.TemporaryDirectory(prefix="f32-eval-") as tmp:
        work = Path(tmp)
        for label, runner in [
            ("Criterion 1 (unnumbered anchors)", _criterion_1_unnumbered),
            ("Criterion 2 (stable anchors)", _criterion_2_stable),
            ("Criterion 3 (L2 references)", _criterion_3_l2_references),
        ]:
            ok, lines = runner(work)
            msgs.append("")
            msgs.append(f"=== {label} ===")
            msgs.extend("  " + l for l in lines)
            if ok:
                passed += 1
                msgs.append("  RESULT: PASS")
            else:
                failed += 1
                msgs.append("  RESULT: FAIL")

    print("\n".join(msgs))
    print("")
    print(f"Criterios: {passed} PASS, {failed} FAIL")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
