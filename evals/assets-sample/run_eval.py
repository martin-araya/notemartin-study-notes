#!/usr/bin/env python3
"""run_eval.py — F33 eval runner.

Verifica los 3 criterios de Fase 33 sobre los fixtures sintéticos:
  1. Ninguna imagen se duplica (dedup por hash sha256).
  2. Cada imagen tiene clase y alt text.
  3. Las decorativas descartadas quedan registradas.

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
FIX = ROOT / "evals" / "assets-sample" / "fixtures"
EXPECTED = ROOT / "evals" / "assets-sample" / "expected"
ASSETS_PY = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "assets.py"

PY = sys.executable


def _build_fixtures() -> bool:
    r = subprocess.run(
        [PY, str(ROOT / "evals" / "assets-sample" / "build_fixtures.py")],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
    return r.returncode == 0


def _run_assets(src_dir: Path, out_dir: Path) -> Tuple[int, str]:
    """Run assets.py on a fixture dir containing source.pdf + sdm.json."""
    r = subprocess.run(
        [
            PY, str(ASSETS_PY),
            "--sdm", str(src_dir / "sdm.json"),
            "--source-file", str(src_dir / "source.pdf"),
            "--out-dir", str(out_dir),
        ],
        capture_output=True, text=True,
    )
    return r.returncode, (r.stdout + r.stderr).strip()


def _read_summary(p: Path) -> Dict[str, Any]:
    return json.loads((p / "assets" / "assets_summary.json").read_text(encoding="utf-8"))


def _read_catalog(p: Path) -> Dict[str, Any]:
    return json.loads((p / "assets" / "assets.json").read_text(encoding="utf-8"))


# ============================================================
# Criterion 1: no dup
# ============================================================

def _criterion_1_no_dup(work: Path) -> Tuple[bool, List[str]]:
    """pdf-dedup: 2 figures pointing at the SAME png bytes → 1 unique asset.
    pdf-mixed-classes: 3 figures, all visually distinct → 3 unique assets."""
    messages: List[str] = []
    all_ok = True

    for label, src in (
        ("dedup", "pdf-dedup"),
        ("mixed-classes", "pdf-mixed-classes"),
    ):
        out = work / src
        code, err = _run_assets(FIX / src, out)
        if code not in (0, 2):
            all_ok = False
            messages.append(f"[FAIL] {src}: exit={code}: {err}")
            continue
        s = _read_summary(out)
        msgs_ok = True
        if label == "dedup":
            if s["total_unique_assets"] != 1:
                msgs_ok = False
                messages.append(
                    f"[FAIL] {src}: unique_assets={s['total_unique_assets']} (expected 1)"
                )
            if s["total_figure_blocks"] - s["total_unique_assets"] != 1:
                msgs_ok = False
                messages.append(
                    f"[FAIL] {src}: dedup_count="
                    f"{s['total_figure_blocks'] - s['total_unique_assets']} (expected 1)"
                )
            cat = _read_catalog(out)
            refs = cat["assets"][0].get("referenced_by", [])
            if len(refs) != 2:
                msgs_ok = False
                messages.append(
                    f"[FAIL] {src}: catalog[0].referenced_by={refs} (expected 2 ids)"
                )
            if msgs_ok:
                messages.append(
                    f"[OK] {src}: 1 unique asset, referenced_by=2 (dedup works)"
                )
        else:
            if s["total_unique_assets"] != 3:
                msgs_ok = False
                messages.append(
                    f"[FAIL] {src}: unique_assets={s['total_unique_assets']} (expected 3)"
                )
            if msgs_ok:
                messages.append(
                    f"[OK] {src}: 3 unique assets, no false dedup"
                )
        if not msgs_ok:
            all_ok = False

    return all_ok, messages


# ============================================================
# Criterion 2: each image has class + alt text
# ============================================================

def _criterion_2_class_and_alt(work: Path) -> Tuple[bool, List[str]]:
    messages: List[str] = []
    all_ok = True

    src = "pdf-mixed-classes"
    out = work / src
    code, err = _run_assets(FIX / src, out)
    if code not in (0, 2):
        all_ok = False
        messages.append(f"[FAIL] {src}: exit={code}: {err}")
        return all_ok, messages

    cat = _read_catalog(out)
    s = _read_summary(out)
    expectations = json.loads(
        (EXPECTED / "mixed-classes-expectations.json").read_text(encoding="utf-8")
    )

    # (a) Every asset has a class
    no_class = [a.get("sha256")[:8] for a in cat["assets"] if not a.get("class")]
    if no_class:
        all_ok = False
        messages.append(f"[FAIL] assets missing class: {no_class}")
    else:
        messages.append(f"[OK] every asset has a class")

    # (b) classes_seen contains all 3 expected
    classes_seen = {a["class"] for a in cat["assets"]}
    expected_classes = set(expectations["criterion_2_class_and_alt"]["classes_seen"])
    missing = expected_classes - classes_seen
    if missing:
        all_ok = False
        messages.append(f"[FAIL] classes_seen={classes_seen}, missing={missing}")
    else:
        messages.append(f"[OK] classes observed include {sorted(expected_classes)}")

    # (c) Non-decorative assets must have alt
    nondesc_no_alt = [
        a.get("sha256")[:8]
        for a in cat["assets"]
        if a["class"] != "decorative" and not (a.get("alt") or "").strip()
    ]
    if nondesc_no_alt:
        all_ok = False
        messages.append(
            f"[FAIL] non-decorative assets without alt: {nondesc_no_alt}"
        )
    else:
        messages.append("[OK] every non-decorative asset has alt text")

    # (d) pdf-missing-alt: 1 figure triggers missing_alt
    src2 = "pdf-missing-alt"
    out2 = work / src2
    code2, err2 = _run_assets(FIX / src2, out2)
    if code2 not in (0, 2):
        all_ok = False
        messages.append(f"[FAIL] {src2}: exit={code2}: {err2}")
    else:
        s2 = _read_summary(out2)
        if "fig-no-alt" in s2.get("missing_alt", []):
            messages.append(
                f"[OK] {src2}: empty-alt non-decorative figure 'fig-no-alt' is flagged in missing_alt"
            )
        else:
            all_ok = False
            messages.append(
                f"[FAIL] {src2}: 'fig-no-alt' not in missing_alt={s2.get('missing_alt')}"
            )

    return all_ok, messages


# ============================================================
# Criterion 3: decorative recorded
# ============================================================

def _criterion_3_decorative_recorded(work: Path) -> Tuple[bool, List[str]]:
    messages: List[str] = []
    all_ok = True

    src = "pdf-mixed-classes"
    out = work / src
    code, err = _run_assets(FIX / src, out)
    if code not in (0, 2):
        all_ok = False
        messages.append(f"[FAIL] {src}: exit={code}: {err}")
        return all_ok, messages

    s = _read_summary(out)
    expectations = json.loads(
        (EXPECTED / "mixed-classes-expectations.json").read_text(encoding="utf-8")
    )

    discarded = s.get("discarded", [])
    min_discarded = expectations["criterion_3_decorative_recorded"]["discarded_min"]
    if len(discarded) < min_discarded:
        all_ok = False
        messages.append(
            f"[FAIL] discarded count={len(discarded)} (expected ≥ {min_discarded})"
        )
    else:
        messages.append(f"[OK] discarded={len(discarded)} (≥ {min_discarded})")

    # Each discarded entry must have block_id, sha256, reason=decorative
    bad = [
        d
        for d in discarded
        if not (d.get("block_id") and d.get("sha256") and d.get("reason"))
    ]
    if bad:
        all_ok = False
        messages.append(f"[FAIL] discarded entries malformed: {bad}")
    else:
        messages.append("[OK] every discarded entry has block_id, sha256, reason")

    # And the corresponding file lives in assets/<sid>/<hash>.ext (not deleted)
    for d in discarded:
        sha16 = d["sha256"][:16]
        sid = s["source_id"]
        path = out / "assets" / sid / f"{sha16}.png"
        if not path.exists():
            all_ok = False
            messages.append(f"[FAIL] decorative file missing on disk: {path}")

    if all_ok:
        messages.append("[OK] decorative files preserved on disk (logged, not deleted)")

    return all_ok, messages


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="F33 eval runner")
    parser.add_argument("--skip-build", action="store_true",
                        help="Skip rebuilding fixtures via build_fixtures.py")
    args = parser.parse_args(argv)

    if not args.skip_build and not _build_fixtures():
        sys.stderr.write("build_fixtures.py failed\n")
        return 2

    passed = 0
    failed = 0
    msgs: List[str] = []

    with tempfile.TemporaryDirectory(prefix="f33-eval-") as tmp:
        work = Path(tmp)
        for label, runner in [
            ("Criterion 1 (no duplicate images)", _criterion_1_no_dup),
            ("Criterion 2 (class + alt text)", _criterion_2_class_and_alt),
            ("Criterion 3 (decorative recorded)", _criterion_3_decorative_recorded),
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
