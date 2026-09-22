#!/usr/bin/env python3
"""run_eval.py — F18 eval: validates the 3 criteria of the roadmap.

Uso:
    python3 evals/pdf-native-sample/run_eval.py

Criterios verificados:
  1. Headings coinciden con el índice del PDF en ≥ 95% de los casos del corpus.
  2. Boilerplate se elimina sin borrar contenido real.
  3. Cada fragmento conserva página y coordenadas.

Códigos de salida:
    0 — PASS los 3 criterios
    1 — Algún FAIL
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "evals" / "pdf-native-sample" / "fixtures"
EXPECTED = ROOT / "evals" / "pdf-native-sample" / "expected"
CORPUS = ROOT / "evals" / "corpus"
SCRIPT = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "pdf_native.py"

PY = sys.executable


def _run_pdf_native(pdf: Path, out_dir: Path) -> Dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(
        [PY, str(SCRIPT), "--source", str(pdf), "--out-dir", str(out_dir), "--json-only"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if not (out_dir / "fragments.json").exists():
        raise RuntimeError(f"pdf_native.py failed (exit {res.returncode}): {res.stderr}")
    return json.loads((out_dir / "fragments.json").read_text(encoding="utf-8"))


def _slug_outline_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def _criterion_1_heading_match_rate(data: Dict) -> Tuple[bool, float, str]:
    """Check that detected headings (and outline-derived section_path coverage) reach ≥ 95%.

    An outline entry is considered "covered" if either:
      (a) a fragment with role=heading and matching slug exists on its page, OR
      (b) any fragment on its page has text starting with the outline title prefix.

    This dual criterion reflects the spec: typography-based detection takes
    precedence (case a), but the script's `assign_section_paths` falls back
    to text-prefix matching for outline entries whose typography is
    indistinguishable from body text (case b). Both cases produce a
    section_path assignment, which is what F31 needs.
    """
    outline = data.get("outline", [])
    if not outline:
        return False, 0.0, "no outline entries detected"

    pages_by_num: Dict[int, List[Dict]] = {}
    for p in data.get("pages", []):
        pages_by_num[p["page"]] = p["fragments"]

    heading_slugs_by_page: Dict[int, set] = {}
    for p_num, frags in pages_by_num.items():
        s = set()
        for f in frags:
            if f.get("role") == "heading":
                s.add(_slug_outline_title(f["text"][:50]))
        heading_slugs_by_page[p_num] = s

    covered = 0
    for o in outline:
        page = o["page"]
        slug = _slug_outline_title(o["title"])
        prefix = o["title"][:30].strip()
        prefix_lower = prefix.lower()
        page_frags = pages_by_num.get(page, [])
        heading_slugs = heading_slugs_by_page.get(page, set())
        if slug in heading_slugs or any(slug in h or h in slug for h in heading_slugs):
            covered += 1
            continue
        if prefix:
            for f in page_frags:
                ftext = f.get("text", "").strip()
                if ftext.startswith(prefix) or ftext.lower().startswith(prefix_lower):
                    covered += 1
                    break

    rate = covered / len(outline) if outline else 0.0
    msg = f"covered {covered}/{len(outline)} outline entries (rate={rate:.3f})"
    return rate >= 0.95, rate, msg


def _criterion_2_boilerplate(pdf: Path, data: Dict, expected: Dict) -> Tuple[bool, str]:
    c2 = expected["criterion_2"]
    bp = data["boilerplate_summary"]
    for h in c2["header_text_expected"]:
        if h not in bp["header_texts"]:
            return False, f"missing header boilerplate: {h!r}"
    for f in c2["footer_text_expected"]:
        if f not in bp["footer_texts"]:
            return False, f"missing footer boilerplate: {f!r}"

    pages = data["pages"]
    for p in pages:
        body_fragments = [
            f for f in p["fragments"]
            if f["role"] not in ("header", "footer", "page_number")
        ]
        if len(body_fragments) < c2["min_body_fragments_per_page"]:
            return False, f"page {p['page']}: only {len(body_fragments)} body fragments (expected ≥ {c2['min_body_fragments_per_page']})"
        for f in body_fragments:
            if f.get("is_boilerplate", False):
                return False, f"page {p['page']}: body fragment marked as boilerplate: {f['text'][:40]!r}"
    for p in pages:
        for f in p["fragments"]:
            if f.get("is_boilerplate", False):
                if f["role"] not in ("header", "footer", "page_number"):
                    return False, f"page {p['page']}: boilerplate fragment with role={f['role']!r}"
    return True, f"boilerplate OK: headers {bp['header_texts']}, footers {bp['footer_texts']}, body preserved"


def _criterion_3_page_bbox(pdf: Path, data: Dict) -> Tuple[bool, str]:
    total_fragments = 0
    for p in data["pages"]:
        for f in p["fragments"]:
            total_fragments += 1
            if not isinstance(f.get("page"), int) or f["page"] < 1:
                return False, f"page {p['page']}: invalid page value {f.get('page')!r}"
            bbox = f.get("bbox")
            if not isinstance(bbox, list) or len(bbox) != 4:
                return False, f"page {p['page']}: invalid bbox {bbox!r}"
            try:
                x0, y0, x1, y1 = [float(v) for v in bbox]
            except (TypeError, ValueError):
                return False, f"page {p['page']}: bbox not numeric {bbox!r}"
            if not (x1 > x0 and y1 > y0):
                return False, f"page {p['page']}: bbox non-monotonic {bbox}"
    return True, f"all {total_fragments} fragments have valid page + bbox"


def _eval_outline_test(work: Path) -> Tuple[int, int, List[str]]:
    """Run criterion 1 on outline-test fixture."""
    pdf = FIXTURES / "outline-test.pdf"
    expected = json.loads((EXPECTED / "outline-test.json").read_text())
    data = _run_pdf_native(pdf, work / "outline-test")
    passed = 0
    failed = []
    c1, rate, msg = _criterion_1_heading_match_rate(data)
    if c1:
        passed += 1
        print(f"  [PASS] outline-test criterion 1: {msg}")
    else:
        failed.append(f"outline-test criterion 1: {msg}")
        print(f"  [FAIL] outline-test criterion 1: {msg}")
    return passed, 1 if not c1 else 0, failed


def _eval_boilerplate_test(work: Path) -> Tuple[int, int, List[str]]:
    pdf = FIXTURES / "boilerplate-test.pdf"
    expected = json.loads((EXPECTED / "boilerplate-test.json").read_text())
    data = _run_pdf_native(pdf, work / "boilerplate-test")
    passed = 0
    failed = []
    c2, msg = _criterion_2_boilerplate(pdf, data, expected)
    if c2:
        passed += 1
        print(f"  [PASS] boilerplate-test criterion 2: {msg}")
    else:
        failed.append(f"boilerplate-test criterion 2: {msg}")
        print(f"  [FAIL] boilerplate-test criterion 2: {msg}")
    c3, msg = _criterion_3_page_bbox(pdf, data)
    if c3:
        passed += 1
        print(f"  [PASS] boilerplate-test criterion 3: {msg}")
    else:
        failed.append(f"boilerplate-test criterion 3: {msg}")
        print(f"  [FAIL] boilerplate-test criterion 3: {msg}")
    return passed, 2 if not (c2 and c3) else 0, failed


def _eval_corpus_pdf(corpus_id: str, work: Path) -> Tuple[int, int, List[str]]:
    pdf = CORPUS / corpus_id / "sample.pdf"
    if not pdf.exists():
        return 0, 0, [f"{corpus_id}: sample.pdf not found"]
    data = _run_pdf_native(pdf, work / f"corpus-{corpus_id}")
    passed = 0
    failed = []
    c1, rate, msg = _criterion_1_heading_match_rate(data)
    if c1:
        passed += 1
        print(f"  [PASS] {corpus_id} criterion 1: {msg}")
    else:
        failed.append(f"{corpus_id} criterion 1: {msg}")
        print(f"  [FAIL] {corpus_id} criterion 1: {msg}")
    c3, msg = _criterion_3_page_bbox(pdf, data)
    if c3:
        passed += 1
        print(f"  [PASS] {corpus_id} criterion 3: {msg}")
    else:
        failed.append(f"{corpus_id} criterion 3: {msg}")
        print(f"  [FAIL] {corpus_id} criterion 3: {msg}")
    return passed, 2 if not (c1 and c3) else 0, failed


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="F18 eval runner")
    args = parser.parse_args(argv)

    total_passed = 0
    total_failed = 0
    failed_msgs: List[str] = []

    with tempfile.TemporaryDirectory(prefix="pdf-native-eval-") as tmp:
        work = Path(tmp)
        print("=== Criterion 1 (heading) ===")
        p, _, failed = _eval_outline_test(work)
        total_passed += p
        total_failed += len(failed)
        failed_msgs.extend(failed)

        print("\n=== Criterion 1 (corpus: 04, 12) ===")
        for cid in ("04-arxiv-two-column", "12-arxiv-formulas"):
            p, _, failed = _eval_corpus_pdf(cid, work)
            total_passed += p
            total_failed += len(failed)
            failed_msgs.extend(failed)

        print("\n=== Criterion 2 (boilerplate) ===")
        p, _, failed = _eval_boilerplate_test(work)
        total_passed += p
        total_failed += len(failed)
        failed_msgs.extend(failed)

    print("")
    print(f"Resultado: {total_passed} PASS, {total_failed} FAIL")
    if failed_msgs:
        print("Fallos:")
        for f in failed_msgs:
            print(f"  - {f}")
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
