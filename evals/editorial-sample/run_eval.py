#!/usr/bin/env python3
"""run_eval.py — F35 eval runner.

Verifica los 3 criterios de Fase 35 sobre los 4 fixtures sintéticos:
  1. Las cajas de advertencia de tres fuentes distintas se reconocen.
  2. Toda advertencia editorial llega al IR como advertencia, no como párrafo.
  3. Las convenciones desconocidas se registran.

Estrategia:
  - El helper `_classify_editorial_box(text, sub_kind, vendor, product)` se
    invoca directamente sobre el `__input_region_for_eval__` de cada SDM
    fixture (no requerimos un PDF fuente). Esto reduce el eval a la mecánica
    F35 sin depender de F31/F22.
  - Complementariamente se valida la `sdm.json` canónica embebida en cada
    fixture contra la schema JSON (sin regresión F13).

Códigos de salida:
    0 — PASS los 3 criterios
    1 — Algún FAIL
    2 — Setup error
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "evals" / "editorial-sample" / "fixtures"
EXPECTED = ROOT / "evals" / "editorial-sample" / "expected"
BUILD_SDM = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "build_sdm.py"
VALIDATE_SDM = ROOT / "scripts" / "util" / "validate_sdm.py"

PY = sys.executable

# Map of fixture-dir-name → expected-file-name
EXPECTED_MAP = {
    "postgresql-warning":     "postgresql-expected.json",
    "python-warning":         "python-expected.json",
    "kubernetes-admonition":  "kubernetes-expected.json",
    "unknown-vendor":         "unknown-expected.json",
}


def _build_fixtures() -> bool:
    r = subprocess.run(
        [PY, str(ROOT / "evals" / "editorial-sample" / "build_fixtures.py")],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
    return r.returncode == 0


def _load_build_sdm_module():
    spec = importlib.util.spec_from_file_location("build_sdm", BUILD_SDM)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_sdm(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _classify(mod, region: Dict[str, Any]) -> Dict[str, Any]:
    """Apply _classify_editorial_box to a synthetic region. Mirrors how
    build_sdm.py invokes it during F35 production."""
    return mod._classify_editorial_box(
        text=region.get("text", ""),
        sub_kind=region.get("sub_kind"),
        vendor=region.get("vendor", ""),
        product=region.get("product", ""),
    )


# ============================================================
# Criterion 1: 3 vendors recognize warning boxes
# ============================================================

def _criterion_1_vendor_recognition() -> Tuple[bool, List[str]]:
    messages: List[str] = []
    all_ok = True
    mod = _load_build_sdm_module()

    fixtures_for_c1 = ["postgresql-warning", "python-warning", "kubernetes-admonition"]
    for label in fixtures_for_c1:
        region_path = FIX / label / "region.json"
        if not region_path.exists():
            all_ok = False
            messages.append(f"[FAIL] {label}: region.json missing")
            continue
        region = json.loads(region_path.read_text(encoding="utf-8")).get("raw_region") or {}
        decision = _classify(mod, region)

        exp = json.loads((EXPECTED / EXPECTED_MAP[label]).read_text(encoding="utf-8"))
        ok = True
        if decision.get("type") != exp["block_type"]:
            ok = False
            all_ok = False
            messages.append(
                f"[FAIL] {label}: type={decision.get('type')!r} (expected {exp['block_type']!r})"
            )
        if exp.get("block_severity") and decision.get("severity") != exp["block_severity"]:
            ok = False
            all_ok = False
            messages.append(
                f"[FAIL] {label}: severity={decision.get('severity')!r} (expected {exp['block_severity']!r})"
            )
        if decision.get("type") == "prose":
            ok = False
            all_ok = False
            messages.append(
                f"[FAIL] {label}: type=prose is FORBIDDEN per spec §5 (invariante crítica)"
            )
        if ok:
            messages.append(
                f"[OK] {label}: vendor '{region.get('vendor', '')}' recognized as type={decision['type']!r}, severity={decision.get('severity')!r}"
            )

    return all_ok, messages


# ============================================================
# Criterion 2: ninguna editorial_note.box cae a prose
# ============================================================

def _criterion_2_no_prose_drop() -> Tuple[bool, List[str]]:
    """Strong invariant: across all 4 fixtures (incl. unknown), no
    editorial_note.box becomes prose."""
    messages: List[str] = []
    all_ok = True
    mod = _load_build_sdm_module()

    for label in EXPECTED_MAP:
        region_path = FIX / label / "region.json"
        if not region_path.exists():
            all_ok = False
            messages.append(f"[FAIL] {label}: region.json missing")
            continue
        region = json.loads(region_path.read_text(encoding="utf-8")).get("raw_region") or {}
        decision = _classify(mod, region)
        if decision.get("type") == "prose":
            all_ok = False
            messages.append(
                f"[FAIL] {label}: editorial_note.box dropped to prose (FORBIDDEN by spec §5 invariante)"
            )
        else:
            messages.append(
                f"[OK] {label}: editorial_note.box -> type={decision.get('type')!r} (NOT prose)"
            )

    return all_ok, messages


# ============================================================
# Criterion 3: unknown convention registered in summary
# ============================================================

def _criterion_3_unknown_recorded() -> Tuple[bool, List[str]]:
    """Validate that the unknown-vendor fixture's _classify_editorial_box
    falls into the F35 unknown_convention path (decision['unknown_convention']
    is true). Also confirm the canonical sdm.json shape (the embedded block)
    remains as note/info."""
    messages: List[str] = []
    all_ok = True
    mod = _load_build_sdm_module()

    label = "unknown-vendor"
    sdm = _load_sdm(FIX / label / "sdm.json")
    region_path = FIX / label / "region.json"
    region = json.loads(region_path.read_text(encoding="utf-8")).get("raw_region") or {}
    decision = _classify(mod, region)

    exp = json.loads((EXPECTED / EXPECTED_MAP[label]).read_text(encoding="utf-8"))

    if not decision.get("unknown_convention"):
        all_ok = False
        messages.append(
            f"[FAIL] {label}: decision.unknown_convention is False (should be True per spec §5)"
        )
    else:
        messages.append(
            f"[OK] {label}: unknown_convention=true (decision={decision.get('type')!r}/{decision.get('severity')!r})"
        )

    # The canonical sdm block must be type=note, severity=info
    blocks = sdm.get("sections", [{}])[0].get("blocks", [])
    if blocks:
        b = blocks[0]
        if b.get("type") != exp["block_type"] or (b.get("content", {}).get("severity") not in (exp.get("block_severity"), None)):
            all_ok = False
            messages.append(
                f"[FAIL] {label}: canonical block type/severity mismatch — got type={b.get('type')!r} severity={b.get('content', {}).get('severity')!r}"
            )
        else:
            messages.append(
                f"[OK] {label}: canonical block intact: type={b['type']!r}, severity={b['content'].get('severity')!r}"
            )

    # Also validate that the canonical sdm validates against sdm.schema.json
    proc = subprocess.run(
        [PY, str(VALIDATE_SDM), "--validate", str(FIX / label / "sdm.json")],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        all_ok = False
        messages.append(
            f"[FAIL] {label}: canonical sdm does NOT validate against schema: {proc.stderr.strip()}"
        )
    else:
        messages.append(
            f"[OK] {label}: canonical sdm validates against sdm.schema.json (no schema regression)"
        )

    return all_ok, messages


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="F35 eval runner")
    parser.add_argument("--skip-build", action="store_true",
                        help="Skip rebuilding fixtures via build_fixtures.py")
    args = parser.parse_args(argv)

    if not args.skip_build and not _build_fixtures():
        sys.stderr.write("build_fixtures.py failed\n")
        return 2

    passed = 0
    failed = 0
    msgs: List[str] = []

    for label, runner in [
        ("Criterion 1 (vendor recognition for warnings)", _criterion_1_vendor_recognition),
        ("Criterion 2 (no editorial-note.box drops to prose)", _criterion_2_no_prose_drop),
        ("Criterion 3 (unknown convention recorded)", _criterion_3_unknown_recorded),
    ]:
        ok, lines = runner()
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
