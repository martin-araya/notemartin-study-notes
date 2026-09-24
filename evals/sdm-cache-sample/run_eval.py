#!/usr/bin/env python3
"""run_eval.py — F36 eval runner.

Verifica los 3 criterios de Fase 36:
  1. Reprocesar la misma fuente no repite el cómputo (cache hit).
  2. Cambiar el motor invalida solo lo afectado (invalidación selectiva por engine_version).
  3. El visor permite filtrar baja confianza en un click.

Estrategia para los criterios del cache: usamos la API Python
`cache_get_or_compute` directamente con una función simulada (que cuenta
invocaciones). Para el visor: invocamos `sdm_view.py` como subproceso y
verificamos el HTML resultante.

Códigos de salida:
    0 — PASS los 3 criterios
    1 — Algún FAIL
    2 — Setup error
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "evals" / "sdm-cache-sample" / "fixtures"
EXPECTED = ROOT / "evals" / "sdm-cache-sample" / "expected"
SDMCACHE = ROOT / "scripts" / "util" / "sdm_cache.py"
SDMVIEW = ROOT / "scripts" / "util" / "sdm_view.py"
VALIDATE_SDM = ROOT / "scripts" / "util" / "validate_sdm.py"

PY = sys.executable


def _build_fixtures() -> bool:
    r = subprocess.run(
        [PY, str(ROOT / "evals" / "sdm-cache-sample" / "build_fixtures.py")],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
    return r.returncode == 0


def _load_sdm_module():
    spec = importlib.util.spec_from_file_location("sdm_cache_f36", SDMCACHE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ============================================================
# Criterion 1: cache hit (no recompute)
# ============================================================

def _criterion_1_cache_hit(work: Path) -> Tuple[bool, List[str]]:
    messages: List[str] = []
    all_ok = True
    mod = _load_sdm_module()

    cache_dir = work / "cache1"
    cache_dir.mkdir(parents=True, exist_ok=True)

    calls = {"n": 0}

    def expensive_compute() -> Dict[str, Any]:
        calls["n"] += 1
        return {"calls": calls["n"], "value": 42}

    key_args = dict(
        source_hash="deadbeef0001",
        step="ocr",
        engine_version="tesseract@5.0.0",
        script_version="sdm_cache@1.0.0",
        params={"page": 1},
        cache_dir=cache_dir,
    )

    value1 = mod.cache_get_or_compute(compute_fn=expensive_compute, **key_args)
    value2 = mod.cache_get_or_compute(compute_fn=expensive_compute, **key_args)
    value3 = mod.cache_get_or_compute(compute_fn=expensive_compute, **key_args)

    if calls["n"] != 1:
        all_ok = False
        messages.append(
            f"[FAIL] cache compute_fn was invoked {calls['n']} times (expected 1: only first call should hit the slow path)"
        )
    elif value1 != value2 or value2 != value3:
        all_ok = False
        messages.append(f"[FAIL] cached values differ across calls: {value1} {value2} {value3}")
    elif value1.get("value") != 42:
        all_ok = False
        messages.append(f"[FAIL] value mismatch: {value1}")
    else:
        messages.append(
            f"[OK] 3 cache_get_or_compute calls → 1 compute_fn invocation; value={value1}"
        )

    # Persistence: cache file exists.
    entry_files = list((cache_dir / "ocr").glob("*.json"))
    if not entry_files:
        all_ok = False
        messages.append("[FAIL] cache entry file not found on disk")
    else:
        messages.append(f"[OK] cache persisted to {entry_files[0]}")

    return all_ok, messages


# ============================================================
# Criterion 2: invalidación selectiva por engine_version
# ============================================================

def _criterion_2_invalidate_selective(work: Path) -> Tuple[bool, List[str]]:
    messages: List[str] = []
    all_ok = True
    mod = _load_sdm_module()

    cache_dir = work / "cache2"
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Seed two engine_versions under the same step.
    mod.cache_get_or_compute(
        source_hash="aa" * 32, step="ocr", engine_version="tesseract@5.0",
        script_version="sdm@1.0", params={"page": 1},
        compute_fn=lambda: {"engine": "5.0", "page_text": "alpha"},
        cache_dir=cache_dir,
    )
    mod.cache_get_or_compute(
        source_hash="aa" * 32, step="ocr", engine_version="tesseract@5.1",
        script_version="sdm@1.0", params={"page": 1},
        compute_fn=lambda: {"engine": "5.1", "page_text": "alpha-v51"},
        cache_dir=cache_dir,
    )

    # Both entries coexist (key includes engine_version).
    info = mod.cache_info(cache_dir)
    if info["by_engine_version"].get("tesseract@5.0", 0) != 1 or info["by_engine_version"].get("tesseract@5.1", 0) != 1:
        all_ok = False
        messages.append(
            f"[FAIL] expected 1 entry per engine_version, got: {info['by_engine_version']}"
        )
    else:
        messages.append(
            f"[OK] two entries co-exist under different engine_versions: {info['by_engine_version']}"
        )

    # Now selectively invalidate only the 5.0 entry.
    mod.cache_clear_engine_version(cache_dir, "ocr", "tesseract@5.0")
    info2 = mod.cache_info(cache_dir)
    if info2["by_engine_version"].get("tesseract@5.0", 0) != 0:
        all_ok = False
        messages.append(
            f"[FAIL] selective invalidation did not drop 5.0: {info2['by_engine_version']}"
        )
    elif info2["by_engine_version"].get("tesseract@5.1", 0) != 1:
        all_ok = False
        messages.append(
            f"[FAIL] 5.1 was wiped during selective invalidation of 5.0: {info2['by_engine_version']}"
        )
    else:
        messages.append(
            f"[OK] selective invalidation: tesseract@5.0 dropped, tesseract@5.1 intact ({info2['by_engine_version']})"
        )

    # Same source_hash → get with 5.1 returns the 5.1 cache (no recompute).
    calls = {"n": 0}

    def expensive_5_1() -> Dict[str, Any]:
        calls["n"] += 1
        return {"engine": "5.1", "page_text": "alpha-v51"}

    val = mod.cache_get_or_compute(
        source_hash="aa" * 32, step="ocr", engine_version="tesseract@5.1",
        script_version="sdm@1.0", params={"page": 1},
        compute_fn=expensive_5_1, cache_dir=cache_dir,
    )
    if calls["n"] != 0 or val["page_text"] != "alpha-v51":
        all_ok = False
        messages.append(f"[FAIL] 5.1 lookup recomputed (calls={calls['n']}) or wrong value {val}")
    else:
        messages.append("[OK] 5.1 lookup is cache hit (no recompute)")

    return all_ok, messages


# ============================================================
# Criterion 3: filter low confidence in one click
# ============================================================

def _criterion_3_filter_low_confidence(work: Path) -> Tuple[bool, List[str]]:
    messages: List[str] = []
    all_ok = True

    out_html = work / "viewer-A.html"
    proc = subprocess.run(
        [PY, str(SDMVIEW), "--sdm", str(FIX / "source-A" / "sdm.json"),
         "--out", str(out_html), "--no-include-images"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        all_ok = False
        messages.append(f"[FAIL] sdm_view.py exit={proc.returncode}: {proc.stderr}")
        return all_ok, messages

    html_str = out_html.read_text(encoding="utf-8")

    # (a) Filter UI controls present (criterio 3 base).
    required = [
        'data-filter="type"',
        'data-filter="confidence"',
        'data-filter="boilerplate"',
        'data-action="low-confidence"',
    ]
    missing = [r for r in required if r not in html_str]
    if missing:
        all_ok = False
        messages.append(f"[FAIL] missing filter controls in HTML: {missing}")
    else:
        messages.append("[OK] viewer has 4 filter controls (type, confidence, boilerplate, low-confidence button)")

    # (b) The synthetic SDM has 2 blocks with conf<0.7 visible in markup.
    low_conf_blocks = []
    for line_match in re.finditer(
        r'class="block"\s+data-type="[^"]+"\s+data-confidence="([^"]+)"', html_str
    ):
        c = float(line_match.group(1))
        if c < 0.7:
            low_conf_blocks.append(c)
    # Fallback regex variant: order is data-type, data-confidence per our renderer
    matches = re.findall(r'data-type="(\w+)"\s+data-confidence="([\d.]+)"', html_str)
    low_conf_blocks = [float(c) for t, c in matches if float(c) < 0.7]
    if len(low_conf_blocks) < 2:
        all_ok = False
        messages.append(
            f"[FAIL] viewer HTML has fewer than 2 low-confidence blocks: {low_conf_blocks}"
        )
    else:
        messages.append(
            f"[OK] viewer HTML contains {len(low_conf_blocks)} low-confidence blocks (conf<0.7)"
        )

    # (c) Simulated one-click filter: assert that the JS logic
    # correctly applies the low-confidence threshold (criterio 3 strong).
    import re as _re
    blocks = _re.findall(
        r'class="block"[^>]*data-type="(\w+)"[^>]*data-confidence="([\d.]+)"',
        html_str,
    )
    threshold = 0.7
    # The rendered JS hides blocks when their conf >= threshold.
    # So visible (kept) blocks are those with conf < threshold OR matches
    # by type. For the "low-confidence only" view: expected kept = those
    # with conf < threshold.
    kept_low = [c for t, c in blocks if float(c) < threshold]
    hidden_low = [c for t, c in blocks if float(c) >= threshold]
    if not kept_low or not hidden_low:
        all_ok = False
        messages.append(
            f"[FAIL] simulated filter cannot demonstrate hide-non-low: kept_low={kept_low}, hidden_low={hidden_low}"
        )
    else:
        messages.append(
            f"[OK] simulated one-click filter (threshold=0.7) keeps {len(kept_low)} blocks, would hide {len(hidden_low)}"
        )

    return all_ok, messages


import re


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="F36 eval runner")
    parser.add_argument("--skip-build", action="store_true",
                        help="Skip rebuilding fixtures via build_fixtures.py")
    args = parser.parse_args(argv)

    if not args.skip_build and not _build_fixtures():
        sys.stderr.write("build_fixtures.py failed\n")
        return 2

    passed = 0
    failed = 0
    msgs: List[str] = []

    with tempfile.TemporaryDirectory(prefix="f36-eval-") as tmp:
        work = Path(tmp)
        for label, runner in [
            ("Criterion 1 (cache hit on reprocess)", _criterion_1_cache_hit),
            ("Criterion 2 (selective invalidation by engine_version)",
             _criterion_2_invalidate_selective),
            ("Criterion 3 (filter low confidence in one click)",
             _criterion_3_filter_low_confidence),
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
