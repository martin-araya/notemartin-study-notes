#!/usr/bin/env python3
"""build_fixtures.py — F31 eval fixtures.

Construye cuatro ingest-dir sintéticos que ejercitan todos los criterios de
Fase 31, más un quinto fixture round-trip que toma el SDM canónico de F13 y
construye un ingest-dir inverso para verificar que se puede volver a producir
un SDM válido.

Uso:
    python3 evals/build-sdm-sample/build_fixtures.py
    # Crea fixtures/ ya poblado
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("PyYAML required. Install with `pip install pyyaml`.\n")
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "evals" / "build-sdm-sample" / "fixtures"
SAMPLE = ROOT / "evals" / "sdm-sample"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload) -> None:
    write(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def write_yaml(path: Path, payload: dict) -> None:
    write(path, yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))


# =====================================================================
# Fixture 1: source-pdf — figure + caption association (criterion 3)
# =====================================================================

PDF_REGION_PAGE1 = {
    "page": 1,
    "regions": [
        {
            "id": "r-h1",
            "semantic_class": "heading",
            "level": 1,
            "text": "Chapter 1: Introduction",
            "bbox": [50.0, 700.0, 300.0, 20.0],
            "class_confidence": 0.92,
            "ambiguity": False,
            "origin": "native",
        },
        {
            "id": "r-p1",
            "semantic_class": "text",
            "text": "Distributed databases are a core building block of modern infrastructure.",
            "bbox": [50.0, 600.0, 500.0, 60.0],
            "class_confidence": 0.80,
            "ambiguity": False,
            "origin": "native",
        },
        {
            "id": "r-fig1",
            "semantic_class": "figure",
            "src": "assets/architecture.png",
            "alt": "High-level architecture",
            "bbox": [80.0, 300.0, 400.0, 250.0],
            "class_confidence": 0.90,
            "ambiguity": False,
            "origin": "native",
        },
    ],
}

PDF_REGION_PAGE2 = {
    "page": 2,
    "regions": [
        {
            "id": "r-cap1",
            "semantic_class": "capture",
            "text": "Figure 1.1: High-level architecture of a distributed database.",
            "bbox": [80.0, 240.0, 400.0, 18.0],
            "class_confidence": 0.85,
            "ambiguity": False,
            "origin": "native",
        },
        {
            "id": "r-cap-orphan",
            "semantic_class": "text",
            "text": "Table 2.1: Generic support summary.",
            "bbox": [60.0, 100.0, 400.0, 18.0],
            "class_confidence": 0.55,
            "ambiguity": True,
            "alternative_classes": [
                {"class": "capture", "score": 0.55},
                {"class": "text", "score": 0.50},
            ],
            "origin": "native",
        },
    ],
}

PDF_FRAGMENTS = {
    "schema_version": "1.0.0",
    "pages": [
        {
            "page": 1,
            "fragments": [
                {
                    "page": 1,
                    "bbox": [50.0, 700.0, 350.0, 720.0],
                    "font_name": "Helvetica-Bold",
                    "font_size": 18.0,
                    "text": "Chapter 1: Introduction",
                    "role": "heading",
                    "heading_level": 1,
                    "section_path": "/ch01/intro",
                    "is_boilerplate": False,
                },
                {
                    "page": 1,
                    "bbox": [50.0, 600.0, 550.0, 660.0],
                    "font_name": "Helvetica",
                    "font_size": 12.0,
                    "text": "Distributed databases are a core building block of modern infrastructure.",
                    "role": "body",
                    "heading_level": None,
                    "section_path": "/ch01/intro",
                    "is_boilerplate": False,
                },
                {
                    "page": 1,
                    "bbox": [80.0, 300.0, 480.0, 550.0],
                    "font_name": "Helvetica",
                    "font_size": 10.0,
                    "text": "[figure: assets/architecture.png alt='High-level architecture']",
                    "role": "body",
                    "heading_level": None,
                    "section_path": "/ch01/intro",
                    "is_boilerplate": False,
                },
            ],
        },
        {
            "page": 2,
            "fragments": [
                {
                    "page": 2,
                    "bbox": [80.0, 240.0, 480.0, 258.0],
                    "font_name": "Helvetica-Oblique",
                    "font_size": 10.0,
                    "text": "Figure 1.1: High-level architecture of a distributed database.",
                    "role": "caption",
                    "heading_level": None,
                    "section_path": "/ch01/intro",
                    "is_boilerplate": False,
                },
                {
                    "page": 2,
                    "bbox": [60.0, 100.0, 460.0, 118.0],
                    "font_name": "Helvetica",
                    "font_size": 10.0,
                    "text": "Table 2.1: Generic support summary.",
                    "role": "body",
                    "heading_level": None,
                    "section_path": "/ch01/intro",
                    "is_boilerplate": False,
                },
            ],
        },
    ],
    "outline": [
        {"level": 1, "title": "Chapter 1: Introduction", "page": 1, "section_path": "/ch01/intro"},
    ],
    "boilerplate_summary": {"header_band": [], "footer_band": []},
    "warnings": [],
}

PDF_META = {
    "id": "eval-01-pdf-figure",
    "hash": "f" * 64,
    "vendor": "Test corpus",
    "product": "Eval PDF",
    "version": "1.0",
    "url": "https://example.com/eval-pdf",
    "language": "en",
    "format": "pdf",
    "date": "2026-09-24",
    "authors": ["eval"],
}


# =====================================================================
# Fixture 2: source-html — web docs sections + footnote
# =====================================================================

HTML_SECTIONS = {
    "schema_version": "1.0.0",
    "source_url": "https://example.com/docs",
    "total_pages": 3,
    "sections": [
        {
            "url_path": "intro.html",
            "canonical_url": "https://example.com/docs/intro.html",
            "level": 1,
            "title": "Introduction",
            "text": "This document presents the core concepts of the system.\n\nFollow the setup steps in chapter two.",
            "headings": [
                {"level": 1, "text": "Introduction", "anchor": ""},
            ],
            "links_internal": [],
            "page_metadata": {"product": "EvalWeb", "version": "2.0", "domain": "https://example.com", "fetched_at": "2026-09-24T00:00:00Z"},
        },
        {
            "url_path": "install.html",
            "canonical_url": "https://example.com/docs/install.html",
            "level": 1,
            "title": "Installation",
            "text": "First, install the package. Then verify the installation as documented.",
            "headings": [
                {"level": 1, "text": "Installation", "anchor": ""},
            ],
            "links_internal": [],
            "page_metadata": {"product": "EvalWeb", "version": "2.0", "domain": "https://example.com", "fetched_at": "2026-09-24T00:00:00Z"},
        },
        {
            "url_path": "config.html",
            "canonical_url": "https://example.com/docs/config.html",
            "level": 1,
            "title": "Configuration",
            "text": "Configure the runtime with a YAML file.",
            "headings": [
                {"level": 1, "text": "Configuration", "anchor": ""},
            ],
            "links_internal": [],
            "page_metadata": {"product": "EvalWeb", "version": "2.0", "domain": "https://example.com", "fetched_at": "2026-09-24T00:00:00Z"},
        },
    ],
}

HTML_META = {
    "id": "eval-02-html-web-docs",
    "hash": "e" * 64,
    "vendor": "https://example.com",
    "product": "EvalWeb",
    "version": "2.0",
    "url": "https://example.com/docs/intro.html",
    "language": "en",
    "format": "html",
    "date": "2026-09-24",
    "authors": [],
}

# HTML fixture also carries a synthetic footnote region so the evaluator
# can verify footnote->ref preservation across formats. The region is
# section-pinned so it collapses into the first web section rather than
# producing an orphan /pNNNN section.
HTML_FOOTNOTE_REGION = {
    "page": 1,
    "regions": [
        {
            "id": "r-html-fn",
            "semantic_class": "footnote",
            "text": "See the RFC for the wire format.",
            "anchor": "footnote-1",
            "section_path": "/intro",
            "confidence": 0.95,
            "ambiguity": False,
            "origin": "native",
        },
    ],
}


# =====================================================================
# Fixture 3: source-ocr — low-confidence ocr blocks
# =====================================================================

OCR_REGIONS = {
    "page": 1,
    "regions": [
        {
            "id": "r-ocr-h1",
            "semantic_class": "heading",
            "level": 2,
            "text": "OCR Result",
            "bbox": [50.0, 700.0, 200.0, 20.0],
            "class_confidence": 0.62,
            "ambiguity": True,
            "alternative_classes": [{"class": "text", "score": 0.62}],
            "origin": "ocr",
            "confidence": 0.65,
        },
        {
            "id": "r-ocr-p",
            "semantic_class": "text",
            "text": "[OCR] Section heading detected with low confidence.",
            "bbox": [50.0, 600.0, 500.0, 40.0],
            "class_confidence": 0.58,
            "ambiguity": True,
            "origin": "ocr",
            "confidence": 0.6,
        },
    ],
}

OCR_FRAGMENTS = {
    "schema_version": "1.0.0",
    "pages": [
        {
            "page": 1,
            "fragments": [
                {
                    "page": 1,
                    "bbox": [50.0, 700.0, 250.0, 720.0],
                    "font_name": "Times-Italic",
                    "font_size": 16.0,
                    "text": "OCR Result",
                    "role": "heading",
                    "heading_level": 2,
                    "section_path": "/scan/intro",
                    "is_boilerplate": False,
                },
                {
                    "page": 1,
                    "bbox": [50.0, 600.0, 550.0, 640.0],
                    "font_name": "Times",
                    "font_size": 12.0,
                    "text": "[OCR] Section heading detected with low confidence.",
                    "role": "body",
                    "heading_level": None,
                    "section_path": "/scan/intro",
                    "is_boilerplate": False,
                },
            ],
        },
    ],
    "outline": [
        {"level": 1, "title": "OCR Result", "page": 1, "section_path": "/scan/intro"},
    ],
    "boilerplate_summary": {"header_band": [], "footer_band": []},
    "warnings": [],
}

OCR_META = {
    "id": "eval-03-ocr-low-conf",
    "hash": "d" * 64,
    "vendor": "Internet Archive",
    "product": "Eval Scan",
    "version": "1.0",
    "url": "https://archive.org/details/eval-scan",
    "language": "en",
    "format": "pdf",
    "date": "2026-09-24",
    "authors": [],
}


# =====================================================================
# Fixture 4: source-multi-format — exercises code/table/formula
# =====================================================================

MULTI_REGIONS = {
    "page": 1,
    "regions": [
        {
            "id": "r-multi-h1",
            "semantic_class": "heading",
            "level": 1,
            "text": "Multi-type page",
            "bbox": [50.0, 700.0, 300.0, 20.0],
            "class_confidence": 0.95,
            "ambiguity": False,
            "origin": "native",
        },
        {
            "id": "r-multi-prose",
            "semantic_class": "text",
            "text": "This page exercises every block type supported by the SDM schema.",
            "bbox": [50.0, 600.0, 500.0, 40.0],
            "class_confidence": 0.85,
            "ambiguity": False,
            "origin": "native",
        },
        {
            "id": "r-multi-list",
            "semantic_class": "text",
            "text": "1. Item one\n2. Item two\n3. Item three",
            "bbox": [50.0, 500.0, 400.0, 80.0],
            "class_confidence": 0.55,
            "ambiguity": True,
            "alternative_classes": [
                {"class": "list", "score": 0.55},
                {"class": "text", "score": 0.50},
            ],
            "origin": "native",
        },
        {
            "id": "r-multi-code",
            "semantic_class": "code",
            "language": "python",
            "text": "def hello():\n    print('hello, world')",
            "bbox": [50.0, 380.0, 400.0, 60.0],
            "class_confidence": 0.92,
            "ambiguity": False,
            "origin": "native",
        },
        {
            "id": "r-multi-formula",
            "semantic_class": "formula",
            "text": "f(x) = ax^2 + bx + c",
            "latex": "f(x) = ax^2 + bx + c",
            "display": True,
            "bbox": [50.0, 260.0, 200.0, 28.0],
            "class_confidence": 0.78,
            "ambiguity": False,
            "origin": "native",
        },
    ],
}

MULTI_FRAGMENTS = {
    "schema_version": "1.0.0",
    "pages": [
        {
            "page": 1,
            "fragments": [
                {
                    "page": 1,
                    "bbox": [50.0, 700.0, 350.0, 720.0],
                    "font_name": "Helvetica-Bold",
                    "font_size": 18.0,
                    "text": "Multi-type page",
                    "role": "heading",
                    "heading_level": 1,
                    "section_path": "/ch01/multi",
                    "is_boilerplate": False,
                },
                {
                    "page": 1,
                    "bbox": [50.0, 600.0, 550.0, 640.0],
                    "font_name": "Helvetica",
                    "font_size": 12.0,
                    "text": "This page exercises every block type supported by the SDM schema.",
                    "role": "body",
                    "heading_level": None,
                    "section_path": "/ch01/multi",
                    "is_boilerplate": False,
                },
                {
                    "page": 1,
                    "bbox": [50.0, 500.0, 450.0, 580.0],
                    "font_name": "Helvetica",
                    "font_size": 12.0,
                    "text": "1. Item one\n2. Item two\n3. Item three",
                    "role": "body",
                    "heading_level": None,
                    "section_path": "/ch01/multi",
                    "is_boilerplate": False,
                },
                {
                    "page": 1,
                    "bbox": [50.0, 380.0, 450.0, 440.0],
                    "font_name": "Courier",
                    "font_size": 10.0,
                    "text": "def hello():\n    print('hello, world')",
                    "role": "body",
                    "heading_level": None,
                    "section_path": "/ch01/multi",
                    "is_boilerplate": False,
                },
                {
                    "page": 1,
                    "bbox": [50.0, 260.0, 250.0, 288.0],
                    "font_name": "Helvetica-Oblique",
                    "font_size": 12.0,
                    "text": "f(x) = ax^2 + bx + c",
                    "role": "body",
                    "heading_level": None,
                    "section_path": "/ch01/multi",
                    "is_boilerplate": False,
                },
            ],
        },
    ],
    "outline": [
        {"level": 1, "title": "Multi-type page", "page": 1, "section_path": "/ch01/multi"},
    ],
    "boilerplate_summary": {"header_band": [], "footer_band": []},
    "warnings": [],
}

MULTI_TABLES_PAGE1 = {
    "page": 1,
    "tables": [
        {
            "region_id": "r-multi-table",
            "page_start": 1,
            "page_end": 1,
            "rows": 3,
            "cols": 2,
            "headers": ["Name", "Type"],
            "data": [
                ["foo", "string"],
                ["bar", "integer"],
                ["baz", "float"],
            ],
            "merged_cells": [],
            "cross_page_continued": False,
            "confidence": 0.95,
        }
    ],
}

MULTI_FORMULAS_PAGE1 = {
    "page": 1,
    "formulas": [
        {
            "id": "r-multi-formula",
            "latex": "f(x) = ax^2 + bx + c",
            "latex_compiled": True,
            "compile_errors": [],
            "display": True,
            "page": 1,
            "pending": False,
            "confidence": 0.9,
        }
    ],
}

MULTI_CODE_PAGE1 = {
    "page": 1,
    "blocks": [
        {
            "region_id": "r-multi-code",
            "language": "python",
            "sub_kind": "code",
            "text": "def hello():\n    print('hello, world')",
            "confidence": 0.92,
            "low_confidence": False,
            "corrections": [],
            "page": 1,
        }
    ],
}

MULTI_TABLE_REGION = {
    "page": 1,
    "regions": [
        {
            "id": "r-multi-table",
            "semantic_class": "table",
            "bbox": [50.0, 200.0, 400.0, 60.0],
            "class_confidence": 0.93,
            "ambiguity": False,
            "origin": "native",
        },
    ],
}

# Patch MULTI_REGIONS to include the table region too.
MULTI_REGIONS_FULL = {
    "page": 1,
    "regions": MULTI_REGIONS["regions"] + MULTI_TABLE_REGION["regions"],
}

MULTI_META = {
    "id": "eval-04-multi-format",
    "hash": "c" * 64,
    "vendor": "Test corpus",
    "product": "Eval Multi",
    "version": "1.0",
    "url": "https://example.com/eval-multi",
    "language": "en",
    "format": "pdf",
    "date": "2026-09-24",
    "authors": ["eval"],
}


def build_source_pdf():
    base = FIX / "source-pdf"
    write_json(base / "regions" / "page-0001.regions.json", PDF_REGION_PAGE1)
    write_json(base / "regions" / "page-0002.regions.json", PDF_REGION_PAGE2)
    write_json(base / "fragments.json", PDF_FRAGMENTS)
    write_yaml(base / "source_meta.yaml", PDF_META)


def build_source_html():
    base = FIX / "source-html"
    write_json(base / "web_docs" / "sections.json", HTML_SECTIONS)
    write_json(base / "web_docs" / "metadata.json", {
        "schema_version": "1.0.0",
        "source_url": "https://example.com/docs",
        "index_url": "https://example.com/docs/intro.html",
        "total_pages": 3,
        "product_version": "2.0",
        "domain": "https://example.com",
        "warnings": [],
        "source": {"dir": str(FIX / "source-html"), "base_url": "https://example.com/docs", "index": "intro.html", "hash": "e" * 64},
    })
    write_json(base / "regions" / "page-0001.regions.json", HTML_FOOTNOTE_REGION)
    write_yaml(base / "source_meta.yaml", HTML_META)


def build_source_ocr():
    base = FIX / "source-ocr"
    write_json(base / "regions" / "page-0001.regions.json", OCR_REGIONS)
    write_json(base / "fragments.json", OCR_FRAGMENTS)
    write_yaml(base / "source_meta.yaml", OCR_META)


def build_source_multi_format():
    base = FIX / "source-multi-format"
    write_json(base / "regions" / "page-0001.regions.json", MULTI_REGIONS_FULL)
    write_json(base / "tables" / "page-0001.tables.json", MULTI_TABLES_PAGE1)
    write_json(base / "formulas" / "page-0001.formulas.json", MULTI_FORMULAS_PAGE1)
    write_json(base / "code" / "page-0001.code.json", MULTI_CODE_PAGE1)
    write_json(base / "fragments.json", MULTI_FRAGMENTS)
    write_yaml(base / "source_meta.yaml", MULTI_META)


def build_expected():
    exp = FIX.parent / "expected"
    write_json(exp / "pdf-expectations.json", {
        "figures_count": 1,
        "captions_attached_count": 1,
        "figures_without_caption_count": 0,
        "captions_orphan_count": 0,
        "captions_total_count": 1,
        "sections_count": 1,
    })
    write_json(exp / "html-expectations.json", {
        "sections_count": 3,
        "footnotes_count": 1,
        "footnote_ref_non_empty": True,
    })
    write_json(exp / "ocr-expectations.json", {
        "blocks_low_confidence": 2,
        "all_origin_ocr": True,
    })
    write_json(exp / "multi-format-expectations.json", {
        "blocks_by_type": {
            "heading": 1,
            "prose": 2,
            "code": 1,
            "formula": 1,
            "table": 1,
        },
        "sections_count": 1,
    })


def main() -> None:
    build_source_pdf()
    build_source_html()
    build_source_ocr()
    build_source_multi_format()
    build_expected()
    print("OK — wrote fixtures/source-{pdf,html,ocr,multi-format}, expected/*.json")


if __name__ == "__main__":
    main()
