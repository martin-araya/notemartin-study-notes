#!/usr/bin/env python3
"""run_eval.py — F28 eval: validates the 3 criteria of the roadmap.

Uso:
    python3 evals/other-formats-sample/run_eval.py

Criterios verificados:
  1. Cada formato del corpus produce SDM válido.
  2. Las notas del orador quedan como bloques propios.
  3. Las anclas temporales son resolubles.

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
FIXTURES = ROOT / "evals" / "other-formats-sample" / "fixtures"
EXPECTED = ROOT / "evals" / "other-formats-sample" / "expected"
SCRIPT = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "other_formats.py"

PY = sys.executable


def _run_pipeline(out_dir: Path) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(
        [PY, str(SCRIPT), "--source", str(FIXTURES), "--out-dir", str(out_dir), "--json-only"],
        capture_output=True, text=True, timeout=120,
    )
    if res.returncode not in (0, 2):
        raise RuntimeError(f"other_formats failed (exit {res.returncode}): {res.stderr}")
    summary_path = out_dir / "ingest" / "other_formats" / "summary.json"
    return json.loads(summary_path.read_text(encoding="utf-8"))


def _load_regions(out_dir: Path) -> Dict[str, list]:
    """Returns {format: regions} from each <basename>.<format>.regions.json."""
    out = {}
    regions_dir = out_dir / "ingest" / "other_formats"
    if not regions_dir.exists():
        return out
    for p in regions_dir.glob("*.regions.json"):
        if p.name == "summary.json":
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        fmt = data.get("source_format", "unknown")
        if fmt not in out:
            out[fmt] = data.get("regions", [])
    return out


def _criterion_1_each_format_produces_valid_sdm(work: Path) -> Tuple[bool, str]:
    expected = json.loads((EXPECTED / "format-coverage.json").read_text(encoding="utf-8"))
    summary = _run_pipeline(work)
    regions_by_file = _load_regions(work)

    expected_fixtures = expected["fixtures"]
    for fmt in expected_fixtures:
        basename = f"corpus-sample.{fmt}"
        if basename not in regions_by_file:
            return False, f"format {fmt} missing: no regions.json for {basename}"
        regions = regions_by_file[basename]
        if not regions:
            return False, f"format {fmt} produced 0 regions"
        if len(regions) < expected["min_regions_per_format"]:
            return False, f"format {fmt} produced {len(regions)} regions (< {expected['min_regions_per_format']})"
        for r in regions:
            text = r.get("text")
            if not text and not r.get("alt"):
                return False, f"format {fmt} region {r.get('id')} has neither text nor alt"

    per_file = {f["file"]: f["region_count"] for f in summary.get("per_file", [])}
    msg = ", ".join(f"{k}={v}" for k, v in sorted(per_file.items()))
    return True, f"6 formats with valid regions: {msg}"


def _criterion_2_speaker_notes_own_blocks(work: Path) -> Tuple[bool, str]:
    expected = json.loads((EXPECTED / "speaker-notes.json").read_text(encoding="utf-8"))
    summary = _run_pipeline(work)
    regions_by_file = _load_regions(work)

    pptx_basename = "corpus-sample.pptx"
    if pptx_basename not in regions_by_file:
        return False, f"{pptx_basename} missing"
    regions = regions_by_file[pptx_basename]

    speaker_notes = [r for r in regions if r.get("semantic_class") == "speaker_note"]
    min_count = expected["criterion_2_speaker_notes_own_blocks"]["min_speaker_note_blocks"]
    if len(speaker_notes) < min_count:
        return False, f"only {len(speaker_notes)} speaker_note blocks (need ≥ {min_count})"
    for sn in speaker_notes:
        if not sn.get("text", "").strip():
            return False, f"speaker_note {sn.get('id')} has empty text"

    if summary["class_distribution"].get("speaker_note", 0) < min_count:
        return False, f"summary class_distribution missing speaker_note (got {summary['class_distribution']})"
    return True, f"{len(speaker_notes)} speaker_note blocks with text"


def _criterion_3_temporal_anchors_resolvable(work: Path) -> Tuple[bool, str]:
    expected = json.loads((EXPECTED / "temporal-anchors.json").read_text(encoding="utf-8"))
    regions_by_file = _load_regions(work)

    transcript_fixtures = expected["fixtures"]
    for fmt in transcript_fixtures:
        basename = f"corpus-sample.{fmt}"
        if basename not in regions_by_file:
            return False, f"transcript {fmt} missing"
        regions = regions_by_file[basename]
        for r in regions:
            if "anchor_id" not in r:
                return False, f"{basename} region {r.get('id')} missing anchor_id"
            if "start" not in r or "end" not in r:
                return False, f"{basename} region {r.get('id')} missing start/end"
            if not isinstance(r.get("start"), (int, float)):
                return False, f"{basename} region {r.get('id')} start not numeric"
            if not isinstance(r.get("end"), (int, float)):
                return False, f"{basename} region {r.get('id')} end not numeric"
            if r["start"] < 0 or r["end"] <= r["start"]:
                return False, f"{basename} region {r.get('id')} invalid timestamps"

    total_transcripts = sum(len(regions_by_file.get(f"corpus-sample.{fmt}", [])) for fmt in transcript_fixtures)
    return True, f"{total_transcripts} transcript regions with anchor_id + start + end"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="F28 eval runner")
    args = parser.parse_args(argv)

    total_passed = 0
    total_failed = 0
    failed_msgs: List[str] = []

    with tempfile.TemporaryDirectory(prefix="other-formats-eval-") as tmp:
        work = Path(tmp)
        # Run pipeline once and share the output across all criteria
        try:
            summary = _run_pipeline(work)
            regions_by_file = _load_regions(work)
        except Exception as e:
            print(f"ERROR: failed to run pipeline: {e}")
            return 1

        def _check_c1() -> Tuple[bool, str]:
            expected = json.loads((EXPECTED / "format-coverage.json").read_text(encoding="utf-8"))
            expected_fixtures = expected["fixtures"]
            min_regions = expected["criterion_1_each_format_produces_valid_sdm"]["min_regions_per_format"]
            for fmt in expected_fixtures:
                if fmt not in regions_by_file:
                    return False, f"format {fmt} missing: no regions.json for corpus-sample.{fmt}"
                regions = regions_by_file[fmt]
                if not regions:
                    return False, f"format {fmt} produced 0 regions"
                if len(regions) < min_regions:
                    return False, f"format {fmt} produced {len(regions)} regions (< {min_regions})"
                for r in regions:
                    text = r.get("text")
                    if not text and not r.get("alt"):
                        return False, f"format {fmt} region {r.get('id')} has neither text nor alt"
            per_file = {f["file"]: f["region_count"] for f in summary.get("per_file", [])}
            msg = ", ".join(f"{k}={v}" for k, v in sorted(per_file.items()))
            return True, f"6 formats with valid regions: {msg}"

        def _check_c2() -> Tuple[bool, str]:
            expected = json.loads((EXPECTED / "speaker-notes.json").read_text(encoding="utf-8"))
            if "pptx" not in regions_by_file:
                return False, "pptx missing"
            regions = regions_by_file["pptx"]
            speaker_notes = [r for r in regions if r.get("semantic_class") == "speaker_note"]
            min_count = expected["criterion_2_speaker_notes_own_blocks"]["min_speaker_note_blocks"]
            if len(speaker_notes) < min_count:
                return False, f"only {len(speaker_notes)} speaker_note blocks (need ≥ {min_count})"
            for sn in speaker_notes:
                if not sn.get("text", "").strip():
                    return False, f"speaker_note {sn.get('id')} has empty text"
            if summary["class_distribution"].get("speaker_note", 0) < min_count:
                return False, f"summary class_distribution missing speaker_note (got {summary['class_distribution']})"
            return True, f"{len(speaker_notes)} speaker_note blocks with text"

        def _check_c3() -> Tuple[bool, str]:
            expected = json.loads((EXPECTED / "temporal-anchors.json").read_text(encoding="utf-8"))
            transcript_fixtures = expected["fixtures"]
            for fmt in transcript_fixtures:
                if fmt not in regions_by_file:
                    return False, f"transcript {fmt} missing"
                regions = regions_by_file[fmt]
                for r in regions:
                    if "anchor_id" not in r:
                        return False, f"{fmt} region {r.get('id')} missing anchor_id"
                    if "start" not in r or "end" not in r:
                        return False, f"{fmt} region {r.get('id')} missing start/end"
                    if not isinstance(r.get("start"), (int, float)):
                        return False, f"{fmt} region {r.get('id')} start not numeric"
                    if not isinstance(r.get("end"), (int, float)):
                        return False, f"{fmt} region {r.get('id')} end not numeric"
                    if r["start"] < 0 or r["end"] <= r["start"]:
                        return False, f"{fmt} region {r.get('id')} invalid timestamps"
            total = sum(len(regions_by_file.get(fmt, [])) for fmt in transcript_fixtures)
            return True, f"{total} transcript regions with anchor_id + start + end"

        for label, fn in (
            ("Criterion 1 (each format produces valid SDM)", _check_c1),
            ("Criterion 2 (speaker notes own blocks)", _check_c2),
            ("Criterion 3 (temporal anchors resolvable)", _check_c3),
        ):
            print(f"=== {label} ===")
            ok, msg = fn()
            tag = "PASS" if ok else "FAIL"
            print(f"  [{tag}] {msg}")
            if ok:
                total_passed += 1
            else:
                total_failed += 1
                failed_msgs.append(f"{label}: {msg}")

    print("")
    print(f"Resultado: {total_passed} PASS, {total_failed} FAIL")
    if failed_msgs:
        print("Fallos:")
        for f in failed_msgs:
            print(f"  - {f}")
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
