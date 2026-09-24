#!/usr/bin/env python3
"""run_eval.py — F34 eval runner.

Verifica los 3 criterios de Fase 34 sobre los 3 fixtures sintéticos:
  1. Procedencia presente (cada campo en source_provenance).
  2. Distinguibilidad (read vs inferred con confidence correcta).
  3. Version gating (--require-version bloquea SDMs sin version).

Códigos de salida:
    0 — PASS los 3 criterios
    1 — Algún FAIL
    2 — Setup error
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "evals" / "provenance-sample" / "fixtures"
EXPECTED = ROOT / "evals" / "provenance-sample" / "expected"
PROVENANCE_PY = ROOT / "scripts" / "validate" / "provenance.py"

PY = sys.executable

# (label, sdm_dir, require_version_flag)
CASES = [
    ("source-full", "source-full", False),
    ("source-web-docs-fallback", "source-web-docs-fallback", False),
    ("source-version-absent-without-flag", "source-version-absent", False),
    ("source-version-absent-with-flag", "source-version-absent", True),
]


def _build_fixtures() -> bool:
    r = subprocess.run(
        [PY, str(ROOT / "evals" / "provenance-sample" / "build_fixtures.py")],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
    return r.returncode == 0


def _run_provenance(sdm_path: Path, require_version: bool,
                    report_path: Path) -> Tuple[int, str]:
    args = [
        PY, str(PROVENANCE_PY),
        "--sdm", str(sdm_path),
        "--report", str(report_path),
        "--json-only",
    ]
    if require_version:
        args.append("--require-version")
    r = subprocess.run(args, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def _read_report(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


# ============================================================
# Criterion 1: source_provenance presente en cada SDM
# ============================================================

def _criterion_1_propagation(work: Path) -> Tuple[bool, List[str]]:
    """Each SDM has source_provenance with all required fields populated."""
    messages: List[str] = []
    all_ok = True

    for label, src, _ in CASES:
        if label.startswith("source-version-absent-with-flag"):
            continue  # covered in criterion 3
        sdm_path = FIX / src / "sdm.json"
        sdm = json.loads(sdm_path.read_text(encoding="utf-8"))
        prov = sdm.get("source_provenance") or {}
        if not prov:
            all_ok = False
            messages.append(f"[FAIL] {label}: source_provenance block is missing entirely")
            continue
        # Check required fields
        missing_required = [f for f in ("id", "hash", "vendor", "product", "version")
                            if f not in prov]
        if missing_required:
            all_ok = False
            messages.append(
                f"[FAIL] {label}: source_provenance missing entries for {missing_required}"
            )
            continue

        EXP_NAME_MAP = {
            "source-full": "full-expectations.json",
            "source-web-docs-fallback": "fallback-expectations.json",
            "source-version-absent": "absent-expectations.json",
        }
        exp_name = EXP_NAME_MAP.get(src, src + "-expectations.json")
        exp = json.loads(
            (EXPECTED / exp_name).read_text(encoding="utf-8")
        )
        # Count read vs inferred
        reads = sum(1 for v in prov.values() if v.get("method") == "read")
        inferred = sum(
            1 for v in prov.values()
            if v.get("method") in ("inferred", "url_regex", "cover_or_header", "web_docs_metadata")
        )
        if reads < exp.get("read_field_count_min", 0):
            all_ok = False
            messages.append(
                f"[FAIL] {label}: read fields={reads} < {exp.get('read_field_count_min')}"
            )
        if inferred > exp.get("inferred_field_count_max", 10**9):
            all_ok = False
            messages.append(
                f"[FAIL] {label}: inferred fields={inferred} > {exp.get('inferred_field_count_max')}"
            )
        if all_ok:
            messages.append(
                f"[OK] {label}: read={reads} inferred={inferred} required fields all present"
            )

    return all_ok, messages


# ============================================================
# Criterion 2: distinguibilidad read vs inferred
# ============================================================

def _criterion_2_distinguishability(work: Path) -> Tuple[bool, List[str]]:
    """Verify read⇔confidence=1.0 and inferred⇔confidence<1.0 invariants."""
    messages: List[str] = []
    all_ok = True

    for label, src, _ in CASES:
        if label.startswith("source-version-absent-with-flag"):
            continue
        sdm_path = FIX / src / "sdm.json"
        sdm = json.loads(sdm_path.read_text(encoding="utf-8"))
        prov = sdm.get("source_provenance") or {}
        bad: List[str] = []
        for field, entry in prov.items():
            method = entry.get("method", "")
            conf = entry.get("confidence")
            try:
                conf_val = float(conf)
            except (TypeError, ValueError):
                bad.append(f"{field}: confidence not numeric ({conf!r})")
                continue
            if method == "read" and conf_val != 1.0:
                bad.append(f"{field}: read + conf={conf_val} (must be 1.0)")
            inferred_methods = ("inferred", "url_regex", "cover_or_header",
                                "web_docs_metadata")
            if method in inferred_methods and conf_val >= 1.0:
                bad.append(f"{field}: {method} + conf={conf_val} (must be <1.0)")

        # Also: no field with method='read' AND inferred-style reasoning
        if not bad:
            messages.append(f"[OK] {label}: (read=1.0, inferred<1.0) invariants hold")
        else:
            all_ok = False
            messages.append(f"[FAIL] {label}: {len(bad)} invariants broken")
            for b in bad[:5]:
                messages.append(f"  - {b}")

    return all_ok, messages


# ============================================================
# Criterion 3: version gating
# ============================================================

def _criterion_3_version_gate(work: Path) -> Tuple[bool, List[str]]:
    """Without --require-version: warning. With: hard fail on documentation."""
    messages: List[str] = []
    all_ok = True

    # Case A: source-version-absent WITHOUT --require-version → exit 2 (warning)
    src = "source-version-absent"
    sdm_path = FIX / src / "sdm.json"
    out_a = work / "version-absent-soft"
    code_a, _ = _run_provenance(sdm_path, require_version=False, report_path=out_a / "report.json")
    if code_a not in (0, 2):
        all_ok = False
        messages.append(
            f"[FAIL] source-version-absent without flag: exit={code_a} (expected 0 or 2)"
        )
    elif code_a == 0:
        messages.append(
            "[NOTE] source-version-absent without flag: exit=0 (accepts version=null as OK)"
        )
    else:
        messages.append(
            "[OK] source-version-absent without flag: exit=2 (warning; version absent flagged)"
        )

    # Case B: same source WITH --require-version → exit 1 (hard fail, documentation)
    out_b = work / "version-absent-hard"
    code_b, _ = _run_provenance(sdm_path, require_version=True, report_path=out_b / "report.json")
    if code_b != 1:
        all_ok = False
        messages.append(
            f"[FAIL] source-version-absent WITH --require-version: exit={code_b} (expected 1)"
        )
    else:
        messages.append(
            "[OK] source-version-absent WITH --require-version: exit=1 (hard fail as expected)"
        )

    # Case C: source-full WITH --require-version → exit 0 (passes because version is present)
    src_c = "source-full"
    sdm_path_c = FIX / src_c / "sdm.json"
    out_c = work / "source-full-with-flag"
    code_c, _ = _run_provenance(sdm_path_c, require_version=True, report_path=out_c / "report.json")
    if code_c not in (0, 2):
        all_ok = False
        messages.append(
            f"[FAIL] source-full WITH --require-version: exit={code_c} (expected 0/2)"
        )
    else:
        messages.append(
            f"[OK] source-full WITH --require-version: exit={code_c} (version present, gate passes)"
        )

    return all_ok, messages


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="F34 eval runner")
    parser.add_argument("--skip-build", action="store_true",
                        help="Skip rebuilding fixtures via build_fixtures.py")
    args = parser.parse_args(argv)

    if not args.skip_build and not _build_fixtures():
        sys.stderr.write("build_fixtures.py failed\n")
        return 2

    passed = 0
    failed = 0
    msgs: List[str] = []

    with tempfile.TemporaryDirectory(prefix="f34-eval-") as tmp:
        work = Path(tmp)
        for label, runner in [
            ("Criterion 1 (procedencia presente)", _criterion_1_propagation),
            ("Criterion 2 (distinguibilidad)", _criterion_2_distinguishability),
            ("Criterion 3 (version gate)", _criterion_3_version_gate),
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
