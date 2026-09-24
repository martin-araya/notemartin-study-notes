#!/usr/bin/env python3
"""build_fixtures.py — F33 eval fixtures.

Generates 3 PDF fixtures exercising the 3 criteria:
- pdf-mixed-classes: 3 figures (1 diagram, 1 screenshot-like, 1 decorative)
- pdf-dedup:          2 figure blocks pointing to the SAME embedded image
- pdf-missing-alt:    1 figure with empty alt

Also produces 1 sdm.json per fixture (compatible with assets.py).
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import zlib
from pathlib import Path

try:
    import reportlab
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
except ImportError:
    sys.stderr.write("reportlab required for fixtures. Install with `pip install reportlab`.\n")
    sys.exit(1)

from PIL import Image, ImageDraw
import io

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "evals" / "assets-sample" / "fixtures"


def write(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def make_diagram_png() -> bytes:
    """A diagram-style image: white bg + black thin lines + colored boxes."""
    img = Image.new("RGB", (640, 480), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Three colored boxes connected by lines (architecture diagram look)
    for x, y, c in [(60, 80, (220, 80, 80)), (320, 80, (80, 180, 80)), (190, 280, (80, 80, 220))]:
        draw.rectangle([x, y, x + 160, y + 90], fill=c, outline=(0, 0, 0), width=3)
    for (a, b) in [((220, 125), (320, 125)), ((140, 170), (270, 325)), ((400, 170), (270, 325))]:
        draw.line([a, b], fill=(0, 0, 0), width=3)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_screenshot_png() -> bytes:
    """A screenshot-style image: 16:9 + colorful UI-like rectangles."""
    img = Image.new("RGB", (1280, 720), (240, 240, 245))
    draw = ImageDraw.Draw(img)
    # Header bar
    draw.rectangle([0, 0, 1280, 60], fill=(50, 60, 70))
    # Sidebar
    draw.rectangle([0, 60, 200, 720], fill=(230, 230, 235))
    # Content panels
    for i in range(3):
        draw.rectangle([220, 100 + i * 200, 1240, 270 + i * 200],
                       fill=(255, 255, 255), outline=(180, 180, 200), width=2)
        # Color bands
        for j in range(5):
            draw.rectangle([240 + j * 200, 140 + i * 200, 420 + j * 200, 200 + i * 200],
                           fill=((j * 50) % 255, (j * 90) % 255, (j * 120) % 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_decorative_png() -> bytes:
    """A logo-style decorative: small, mostly uniform color."""
    img = Image.new("RGB", (80, 80), (200, 200, 200))
    draw = ImageDraw.Draw(img)
    draw.ellipse([20, 20, 60, 60], fill=(180, 30, 30))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_placeholder_png() -> bytes:
    """Tiny uniform PNG used as fallback when bytes are 'missing'."""
    img = Image.new("RGB", (16, 16), (255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_pdf(figure_specs: list[dict], out_path: Path) -> None:
    """Build a 1-page PDF with multiple figure regions embedded.
    `figure_specs`: list of {"name", "png_bytes", "bbox_pdf_units"}.
    PDF user space is 612x792 (letter); we map bbox directly."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmpdir = Path(tempfile.mkdtemp(prefix="assets-fixtures-"))
    try:
        c = canvas.Canvas(str(out_path), pagesize=letter)
        width, height = letter

        for spec in figure_specs:
            name = spec["name"]
            data = spec["png_bytes"]
            x0, y0, x1, y1 = spec["bbox_pdf_units"]
            tmp = tmpdir / f"{name}.png"
            tmp.write_bytes(data)
            c.drawImage(str(tmp), x0, height - y1,
                        width=x1 - x0, height=y1 - y0)

        c.showPage()
        c.save()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def sdm_template(
    sid: str, hash_val: str, vendor: str, product: str,
    figures: list[dict], page_width: float = 612.0, page_height: float = 792.0,
) -> dict:
    """Build an SDM template compatible with assets.py:
    - source.{id, hash, vendor, product, ...}
    - sections[].blocks[] with figures pointing to bbox in PDF user space."""
    return {
        "schema_version": "1.0.0",
        "source": {
            "id": sid,
            "hash": hash_val,
            "vendor": vendor,
            "product": product,
            "url": "https://example.com/eval",
            "language": "en",
            "format": "pdf",
        },
        "sections": [
            {
                "section_path": "/ch01/figures",
                "title": "Figures",
                "blocks": figures,
            }
        ],
    }


def build_mixed_classes():
    base = FIX / "pdf-mixed-classes"
    diagram_png = make_diagram_png()
    screenshot_png = make_screenshot_png()
    decorative_png = make_decorative_png()

    # Place figures on a single PDF page.
    pdf_path = base / "source.pdf"
    make_pdf([
        {"name": "diagram", "png_bytes": diagram_png,
         "bbox_pdf_units": [50, 380, 580, 700]},
        {"name": "screenshot", "png_bytes": screenshot_png,
         "bbox_pdf_units": [50, 50, 580, 370]},
        {"name": "logo", "png_bytes": decorative_png,
         "bbox_pdf_units": [700, 380, 750, 430]},
    ], pdf_path)

    # Source hash is deterministic from PDF bytes
    import hashlib
    pdf_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()

    figures = [
        {"id": "fig-diag", "type": "figure",
         "content": {"src": "diagram.png",
                     "alt": "Architecture diagram showing three connected services"},
         "anchor": {"page": 1, "section_path": "/ch01/figures",
                    "bbox": [50.0, 380.0, 530.0, 320.0]},
         "confidence": 1.0, "origin": "native"},
        {"id": "fig-screen", "type": "figure",
         "content": {"src": "screenshot.png",
                     "alt": "Screenshot of the configuration page"},
         "anchor": {"page": 1, "section_path": "/ch01/figures",
                    "bbox": [50.0, 50.0, 530.0, 320.0]},
         "confidence": 1.0, "origin": "native"},
        {"id": "fig-logo", "type": "figure",
         "content": {"src": "logo.png", "alt": ""},
         "anchor": {"page": 1, "section_path": "/ch01/figures",
                    "bbox": [700.0, 380.0, 50.0, 50.0]},
         "confidence": 1.0, "origin": "native"},
    ]
    sdm = sdm_template(
        "eval-mixed-classes", pdf_hash, "Test corpus", "Eval Mixed",
        figures=figures,
    )
    write(base / "sdm.json", json.dumps(sdm, indent=2, ensure_ascii=False) + "\n")


def build_dedup():
    base = FIX / "pdf-dedup"
    # Two figures pointing at the SAME image bytes (same png data)
    shared = make_diagram_png()
    pdf_path = base / "source.pdf"
    make_pdf([
        {"name": "diagram_a", "png_bytes": shared,
         "bbox_pdf_units": [50, 380, 580, 700]},
        {"name": "diagram_b_dup", "png_bytes": shared,
         "bbox_pdf_units": [50, 50, 580, 370]},
    ], pdf_path)

    import hashlib
    pdf_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()

    figures = [
        {"id": "fig-dup-a", "type": "figure",
         "content": {"src": "diagram_a.png", "alt": "Diagram A"},
         "anchor": {"page": 1, "section_path": "/ch01/figures",
                    "bbox": [50.0, 380.0, 530.0, 320.0]},
         "confidence": 1.0, "origin": "native"},
        {"id": "fig-dup-b", "type": "figure",
         "content": {"src": "diagram_b_dup.png", "alt": "Same diagram reused"},
         "anchor": {"page": 1, "section_path": "/ch01/figures",
                    "bbox": [50.0, 50.0, 530.0, 320.0]},
         "confidence": 1.0, "origin": "native"},
    ]
    sdm = sdm_template(
        "eval-dedup", pdf_hash, "Test corpus", "Eval Dedup",
        figures=figures,
    )
    write(base / "sdm.json", json.dumps(sdm, indent=2, ensure_ascii=False) + "\n")


def build_missing_alt():
    base = FIX / "pdf-missing-alt"
    diagram_png = make_diagram_png()
    pdf_path = base / "source.pdf"
    make_pdf([
        {"name": "diag_no_alt", "png_bytes": diagram_png,
         "bbox_pdf_units": [50, 380, 580, 700]},
        {"name": "diag_with_alt", "png_bytes": diagram_png,
         "bbox_pdf_units": [50, 50, 580, 370]},
    ], pdf_path)

    import hashlib
    pdf_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()

    figures = [
        # empty alt + non-decorative (diagram) → triggers warning missing_alt
        {"id": "fig-no-alt", "type": "figure",
         "content": {"src": "diag_no_alt.png", "alt": ""},
         "anchor": {"page": 1, "section_path": "/ch01/figures",
                    "bbox": [50.0, 380.0, 530.0, 320.0]},
         "confidence": 1.0, "origin": "native"},
        # non-empty alt for control
        {"id": "fig-with-alt", "type": "figure",
         "content": {"src": "diag_with_alt.png",
                     "alt": "Reference architecture diagram"},
         "anchor": {"page": 1, "section_path": "/ch01/figures",
                    "bbox": [50.0, 50.0, 530.0, 320.0]},
         "confidence": 1.0, "origin": "native"},
    ]
    sdm = sdm_template(
        "eval-missing-alt", pdf_hash, "Test corpus", "Eval Missing Alt",
        figures=figures,
    )
    write(base / "sdm.json", json.dumps(sdm, indent=2, ensure_ascii=False) + "\n")


def build_expected():
    """Expected values used by run_eval.py."""
    exp = FIX.parent / "expected"
    write(exp / "mixed-classes-expectations.json", """{
  "criterion_1_no_dup": {"unique_assets_min": 3, "by_class_min_count": {"decorative": 1}},
  "criterion_2_class_and_alt": {
    "figures_count": 3,
    "every_class_assigned": true,
    "classes_seen": ["diagram_conceptual", "screenshot", "decorative"]
  },
  "criterion_3_decorative_recorded": {
    "discarded_min": 1,
    "discarded_reason": "decorative"
  }
}
""")
    write(exp / "dedup-expectations.json", """{
  "criterion_1_no_dup": {
    "unique_assets": 1,
    "referenced_by_len": 2,
    "dedup_count": 1
  }
}
""")
    write(exp / "missing-alt-expectations.json", """{
  "criterion_2_class_and_alt": {
    "missing_alt_min": 1,
    "decorative_with_alt_min": 0
  }
}
""")


def main() -> None:
    build_mixed_classes()
    build_dedup()
    build_missing_alt()
    build_expected()
    print("OK — wrote fixtures (3 PDFs + sdms) + expected/")


if __name__ == "__main__":
    main()
