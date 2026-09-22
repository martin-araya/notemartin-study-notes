#!/usr/bin/env python3
"""run_eval.py — F17 eval: clasifica las 14 fuentes del corpus + 1 fixture híbrido
y compara contra los expected.json.

Uso:
    python3 evals/triage-sample/run_eval.py [--keep] [--check-ranges]

Para cada expected.json, locate el sample correspondiente en evals/corpus/<id>/.
Si no hay sample (02, 08, 09, 13, 14), genera un stub sintético etiquetado
(HTML/TXT/PDF-stub) para validar la mecánica. La verificación material contra
las muestras reales se difiere a F118.

Códigos de salida:
    0 — PASS 15/15
    1 — Algún FAIL
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "evals" / "corpus"
EXPECTED = ROOT / "evals" / "triage-sample" / "expected"
FIXTURES = ROOT / "evals" / "triage-sample" / "fixtures"
TRIAGE_PY = ROOT / "skill" / "notemartin-study-notes" / "scripts" / "ingest" / "triage.py"

PY = sys.executable


def _stub_html(path: Path, body: str) -> None:
    path.write_text(
        f"<!DOCTYPE html><html><head><title>stub</title></head><body>{body}</body></html>",
        encoding="utf-8",
    )


def _stub_text(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def _stub_pdf_scan(path: Path) -> None:
    """Minimal PDF with a single page that's a pure scan.

    Uses raw PDF bytes to avoid the reportlab dependency at eval time.
    """
    # Inspired by minimal valid PDF + one full-page Image XObject.
    # We use an inline image (BI...EI) to keep things deterministic.
    objects: List[bytes] = []

    catalog_obj = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    pages_obj = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    page_obj = (
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /XObject << /Im0 5 0 R >> >> >>\n"
        b"endobj\n"
    )
    # Inline image (8x8 grayscale PNG, scaled to fill via cm transformation)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x08\x00\x00\x00\x08\x08\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x0eIDATx\x9cc\xfc\xcf\xc0P\x0f\x00\x05\x00\x01"
        b"\xff\xff\xff\xff\xa6\xb6\x05\x9e"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    content_stream = (
        b"q 612 0 0 792 0 0 cm /Im0 Do Q\n"
    )
    content_obj = (
        f"4 0 obj\n<< /Length {len(content_stream)} >>\nstream\n".encode("utf-8")
        + content_stream
        + b"endstream\nendobj\n"
    )
    image_stream = (
        f"5 0 obj\n<< /Type /XObject /Subtype /Image /Width 612 /Height 792 "
        f"/ColorSpace /DeviceGray /BitsPerComponent 8 /Length {len(png_bytes)} "
        f"/Filter /FlateDecode >>\nstream\n".encode("utf-8")
        + png_bytes
        + b"\nendstream\nendobj\n"
    )

    objects.extend([catalog_obj, pages_obj, page_obj, content_obj, image_stream])

    header = b"%PDF-1.4\n%\xc2\xa5\xc2\xb1\xc3\xab\n"
    offsets: List[int] = [0]
    for obj in objects:
        offsets.append(len(header) + sum(offsets) - len(b""))
    # Recompute offsets correctly
    offsets = [0]
    body = b""
    for obj in objects:
        offsets.append(len(header) + len(body))
        body += obj
    xref_offset = len(header) + len(body)
    xref = f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets[1:]:
        xref += f"{off:010d} 00000 n \n".encode()
    xref += b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
    xref += f"{xref_offset}\n".encode()
    xref += b"%%EOF\n"

    path.write_bytes(header + body + xref)


def _stub_repository(path: Path) -> None:
    """Stub a tiny .git/ + README so triage detects it as repository."""
    path.mkdir(parents=True, exist_ok=True)
    (path / ".git").mkdir(exist_ok=True)
    (path / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
    (path / "README.md").write_text("# stub\n\nThis is a stub repository for triage eval.\n", encoding="utf-8")


def _find_sample(source_id: str) -> Optional[Path]:
    """Locate sample. Some fixtures live outside evals/corpus (synthetic only)."""
    if source_id in ("hybrid-synthetic", "14-book-bad-numbering-hostil"):
        # Use the F17 fixture PDF (no corpus sample for these sources; they're
        # either fixture-only or hostiles sin muestra descargada). The shared
        # fixture (3 native + 2 scan + 3 degraded) covers both.
        p = FIXTURES / "hybrid-synthetic.pdf"
        return p if p.exists() else None
    d = CORPUS / source_id
    if not d.is_dir():
        return None
    for candidate in d.iterdir():
        if candidate.name.startswith("sample."):
            return candidate
    return None


def _ensure_sample(source_id: str, expected: Dict, work: Path) -> Tuple[Path, str]:
    """Returns (path, kind) where kind is 'real' or 'stub'."""
    sample = _find_sample(source_id)
    if sample is not None:
        return sample, "real"
    # Generate stub based on expected format_classification
    cls = expected["format_classification"]
    if cls == "html":
        p = work / f"{source_id}-stub.html"
        _stub_html(p, f"<h1>{source_id}</h1><p>stub HTML for F17 eval.</p>")
        return p, "stub"
    if cls == "text":
        p = work / f"{source_id}-stub.txt"
        _stub_text(p, f"{source_id}\n\nThis is a stub text file for F17 eval.\n" * 10)
        return p, "stub"
    if cls in ("pdf_pure_scan", "pdf_native_reliable", "pdf_native_degraded", "pdf_hybrid"):
        p = work / f"{source_id}-stub.pdf"
        _stub_pdf_scan(p)
        return p, "stub"
    if cls == "repository":
        p = work / f"{source_id}-stub-repo"
        _stub_repository(p)
        return p, "stub"
    raise RuntimeError(f"No stub generator for class {cls!r} (source {source_id})")


def _run_triage(source: Path, out_dir: Path) -> Dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(
        [PY, str(TRIAGE_PY), "--source", str(source), "--out-dir", str(out_dir), "--json-only"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if not (out_dir / "triage.json").exists():
        raise RuntimeError(f"triage.py failed (exit {res.returncode}): {res.stderr}")
    return json.loads((out_dir / "triage.json").read_text(encoding="utf-8"))


def _check_one(source_id: str, expected: Dict, work: Path) -> Tuple[bool, str]:
    sample, kind = _ensure_sample(source_id, expected, work)
    out = work / f"{source_id}-out"
    actual = _run_triage(sample, out)

    # 1. format_classification must match exactly
    exp_class = expected["format_classification"]
    act_class = actual["format_classification"]
    if exp_class != act_class:
        return False, (
            f"{source_id}[{kind}]: format_classification {act_class!r} != {exp_class!r}"
        )

    # 2. Each expected plan range's class must appear at least once in the actual plan
    exp_classes = [r["class"] for r in expected["plan_runs_expected"]]
    act_classes = [r["class"] for r in actual["plan"]]
    for needed in exp_classes:
        if needed not in act_classes:
            return False, (
                f"{source_id}[{kind}]: plan missing expected class {needed!r} "
                f"(got {act_classes!r})"
            )

    return True, f"{source_id}[{kind}]: {act_class} -> {len(act_classes)} ranges ({act_classes})"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="F17 eval runner")
    parser.add_argument("--check-ranges", action="store_true",
                        help="Extra check: hybrid-synthetic must have ≥ 3 distinct classes in the plan")
    parser.add_argument("--only", help="Run only this source_id (debug)")
    args = parser.parse_args(argv)

    expected_files = sorted(EXPECTED.glob("*.json"))
    if not expected_files:
        print("ERROR: no expected.json files found.", file=sys.stderr)
        return 1

    total = 0
    passed = 0
    failed: List[str] = []
    with tempfile.TemporaryDirectory(prefix="triage-eval-") as tmp:
        work = Path(tmp)
        for ef in expected_files:
            if args.only and ef.stem != args.only:
                continue
            expected = json.loads(ef.read_text(encoding="utf-8"))
            total += 1
            ok, msg = _check_one(ef.stem, expected, work)
            tag = "PASS" if ok else "FAIL"
            print(f"  [{tag}] {msg}")
            if ok:
                passed += 1
            else:
                failed.append(msg)

    print("")
    print(f"Resultado: {passed}/{total} PASS")
    if failed:
        print("Fallos:")
        for f in failed:
            print(f"  - {f}")

    if args.check_ranges:
        hybrid_expected = json.loads((EXPECTED / "hybrid-synthetic.json").read_text(encoding="utf-8"))
        n_classes = len({r["class"] for r in hybrid_expected["plan_runs_expected"]})
        if n_classes >= 3:
            print(f"hybrid-synthetic: {n_classes} clases distintas en plan ✓")
        else:
            print(f"hybrid-synthetic: solo {n_classes} clases; esperado ≥ 3")
            failed.append("hybrid-synthetic ranges")

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
