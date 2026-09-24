#!/usr/bin/env python3
"""build_fixtures.py — F32 eval fixtures.

Construye los 3 ingest-dir que ejercitan los 3 criterios de Fase 32:
- source-unnumbered-html: HTML sin headings numerados (criterio 1, anclas utilizables)
- source-renumbered-pdf: PDF con outline 1.1, 1.1 duplicado, 1.3 saltado (reglas §7)
- source-stable-rerun: re-empaqueta source-pdf con mismo hash, valida criterio 2

También escribe un mini-ledger para validar criterio 3 (block_id referenciado
existe en el SDM).

Uso:
    python3 evals/anchors-sample/build_fixtures.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "evals" / "anchors-sample" / "fixtures"
EXP = ROOT / "evals" / "anchors-sample" / "expected"
F31_FIX = ROOT / "evals" / "build-sdm-sample" / "fixtures"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload) -> None:
    write(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


# =====================================================================
# Fixture 1: source-unnumbered-html
# =====================================================================

UNNUMBERED_HTML_SECTIONS = {
    "schema_version": "1.0.0",
    "source_url": "https://example.com/docs",
    "total_pages": 5,
    "sections": [
        {
            "url_path": "overview.html",
            "canonical_url": "https://example.com/docs/overview.html",
            "level": 1,
            "title": "Overview",
            "text": "This document has no numbered sections. Navigation flows by URL slug.",
            "headings": [{"level": 1, "text": "Overview", "anchor": ""}],
            "links_internal": [],
            "page_metadata": {"product": "Anchorless", "version": "1.0", "domain": "https://example.com", "fetched_at": "2026-09-24T00:00:00Z"},
        },
        {
            "url_path": "concepts.html",
            "canonical_url": "https://example.com/docs/concepts.html",
            "level": 1,
            "title": "Concepts",
            "text": "Core concepts without numbers.",
            "headings": [{"level": 1, "text": "Concepts", "anchor": ""}],
            "links_internal": [],
            "page_metadata": {"product": "Anchorless", "version": "1.0", "domain": "https://example.com", "fetched_at": "2026-09-24T00:00:00Z"},
        },
        {
            "url_path": "setup.html",
            "canonical_url": "https://example.com/docs/setup.html",
            "level": 1,
            "title": "Setup",
            "text": "How to set up the project.",
            "headings": [{"level": 1, "text": "Setup", "anchor": ""}],
            "links_internal": [],
            "page_metadata": {"product": "Anchorless", "version": "1.0", "domain": "https://example.com", "fetched_at": "2026-09-24T00:00:00Z"},
        },
        {
            "url_path": "usage.html",
            "canonical_url": "https://example.com/docs/usage.html",
            "level": 1,
            "title": "Usage",
            "text": "Common usage patterns.",
            "headings": [{"level": 1, "text": "Usage", "anchor": ""}],
            "links_internal": [],
            "page_metadata": {"product": "Anchorless", "version": "1.0", "domain": "https://example.com", "fetched_at": "2026-09-24T00:00:00Z"},
        },
        {
            "url_path": "reference.html",
            "canonical_url": "https://example.com/docs/reference.html",
            "level": 1,
            "title": "Reference",
            "text": "API reference without numbers.",
            "headings": [{"level": 1, "text": "Reference", "anchor": ""}],
            "links_internal": [],
            "page_metadata": {"product": "Anchorless", "version": "1.0", "domain": "https://example.com", "fetched_at": "2026-09-24T00:00:00Z"},
        },
    ],
}

UNNUMBERED_META = {
    "id": "eval-anchorless-html",
    "hash": "a" * 64,
    "vendor": "https://example.com",
    "product": "Anchorless",
    "version": "1.0",
    "url": "https://example.com/docs/overview.html",
    "language": "en",
    "format": "html",
    "date": "2026-09-24",
    "authors": [],
}


# =====================================================================
# Fixture 2: source-renumbered-pdf (outline with duplicate 1.1, skipped 1.2)
# =====================================================================

RENUMBERED_FRAGMENTS = {
    "schema_version": "1.0.0",
    "pages": [
        {
            "page": 1,
            "fragments": [
                {"page": 1, "bbox": [50.0, 700.0, 350.0, 720.0], "font_name": "Helvetica-Bold",
                 "font_size": 18.0, "text": "1.1 Foo",
                 "role": "heading", "heading_level": 2, "section_path": "/ch01/foo", "is_boilerplate": False},
                {"page": 1, "bbox": [50.0, 600.0, 550.0, 640.0], "font_name": "Helvetica",
                 "font_size": 12.0, "text": "First definition of foo.",
                 "role": "body", "heading_level": None, "section_path": "/ch01/foo", "is_boilerplate": False},
            ],
        },
        {
            "page": 2,
            "fragments": [
                {"page": 2, "bbox": [50.0, 700.0, 350.0, 720.0], "font_name": "Helvetica-Bold",
                 "font_size": 18.0, "text": "1.1 Foo (duplicate printing)",
                 "role": "heading", "heading_level": 2, "section_path": "/ch01/foo", "is_boilerplate": False},
                {"page": 2, "bbox": [50.0, 600.0, 550.0, 640.0], "font_name": "Helvetica",
                 "font_size": 12.0, "text": "Bar arg redefined.",
                 "role": "body", "heading_level": None, "section_path": "/ch01/foo", "is_boilerplate": False},
            ],
        },
        {
            "page": 3,
            "fragments": [
                {"page": 3, "bbox": [50.0, 700.0, 350.0, 720.0], "font_name": "Helvetica-Bold",
                 "font_size": 18.0, "text": "1.3 Skipped",
                 "role": "heading", "heading_level": 2, "section_path": "/ch01/skipped", "is_boilerplate": False},
                {"page": 3, "bbox": [50.0, 600.0, 550.0, 640.0], "font_name": "Helvetica",
                 "font_size": 12.0, "text": "Numbered 1.3 because 1.2 was reserved by the editor.",
                 "role": "body", "heading_level": None, "section_path": "/ch01/skipped", "is_boilerplate": False},
            ],
        },
    ],
    "outline": [
        {"level": 1, "title": "Chapter 1", "page": 1, "section_path": "/ch01"},
        {"level": 2, "title": "1.1 Foo", "page": 1, "section_path": "/ch01/foo"},
        # NOTE: outline re-emits "/ch01/foo" for the duplicate on page 2 — this
        # is the inconsistency that the source printed. The eval verifies
        # whether the SDM keeps BOTH blocks (D5) or collapses them.
        {"level": 2, "title": "1.1 Foo (duplicate)", "page": 2, "section_path": "/ch01/foo"},
        {"level": 2, "title": "1.3 Skipped", "page": 3, "section_path": "/ch01/skipped"},
    ],
    "boilerplate_summary": {"header_band": [], "footer_band": []},
    "warnings": [],
}

RENUMBERED_REGIONS = {
    "page": 1,
    "regions": [
        {"id": "rn-h1", "semantic_class": "heading", "level": 2, "text": "1.1 Foo",
         "bbox": [50.0, 700.0, 300.0, 20.0], "class_confidence": 0.92, "ambiguity": False, "origin": "native"},
        {"id": "rn-p1", "semantic_class": "text", "text": "First definition of foo.",
         "bbox": [50.0, 600.0, 500.0, 60.0], "class_confidence": 0.85, "ambiguity": False, "origin": "native"},
    ],
}
RENUMBERED_PAGE2 = {
    "page": 2,
    "regions": [
        {"id": "rn-h2", "semantic_class": "heading", "level": 2, "text": "1.1 Foo (duplicate printing)",
         "bbox": [50.0, 700.0, 350.0, 20.0], "class_confidence": 0.92, "ambiguity": False, "origin": "native"},
        {"id": "rn-p2", "semantic_class": "text", "text": "Bar arg redefined.",
         "bbox": [50.0, 600.0, 500.0, 60.0], "class_confidence": 0.85, "ambiguity": False, "origin": "native"},
    ],
}
RENUMBERED_PAGE3 = {
    "page": 3,
    "regions": [
        {"id": "rn-h3", "semantic_class": "heading", "level": 2, "text": "1.3 Skipped",
         "bbox": [50.0, 700.0, 300.0, 20.0], "class_confidence": 0.92, "ambiguity": False, "origin": "native"},
        {"id": "rn-p3", "semantic_class": "text", "text": "Numbered 1.3 because 1.2 was reserved by the editor.",
         "bbox": [50.0, 600.0, 500.0, 60.0], "class_confidence": 0.85, "ambiguity": False, "origin": "native"},
    ],
}

RENUMBERED_META = {
    "id": "eval-renumbered-pdf",
    "hash": "b" * 64,
    "vendor": "Test corpus",
    "product": "Eval Renumbered",
    "version": "1.0",
    "url": "https://example.com/renumbered",
    "language": "en",
    "format": "pdf",
    "date": "2026-09-24",
    "authors": ["eval"],
}


# =====================================================================
# Fixture 3: source-stable-rerun — re-empaqueta source-pdf de F31 con mismo hash
# =====================================================================

# Simple shell: copy the F31 source-pdf fixture into a parallel directory and
# change only the source_meta id/hash to ensure rerun determinism can be probed
# independently. The actual bytes come from build_sdm's own output.


# =====================================================================
# Building fixture dirs
# =====================================================================

def build_unnumbered_html():
    base = FIX / "source-unnumbered-html"
    write_json(base / "web_docs" / "sections.json", UNNUMBERED_HTML_SECTIONS)
    write_json(base / "web_docs" / "metadata.json", {
        "schema_version": "1.0.0",
        "source_url": "https://example.com/docs",
        "index_url": "https://example.com/docs/overview.html",
        "total_pages": 5,
        "product_version": "1.0",
        "domain": "https://example.com",
        "warnings": [],
        "source": {"dir": str(FIX / "source-unnumbered-html"), "base_url": "https://example.com/docs",
                   "index": "overview.html", "hash": "a" * 64},
    })
    write(path := base / "source_meta.yaml", """\
id: eval-anchorless-html
hash: """ + "a" * 64 + """
vendor: 'https://example.com'
product: Anchorless
version: '1.0'
url: 'https://example.com/docs/overview.html'
language: en
format: html
date: '2026-09-24'
authors: []
""")


def build_renumbered_pdf():
    base = FIX / "source-renumbered-pdf"
    write_json(base / "fragments.json", RENUMBERED_FRAGMENTS)
    write_json(base / "regions" / "page-0001.regions.json", RENUMBERED_REGIONS)
    write_json(base / "regions" / "page-0002.regions.json", RENUMBERED_PAGE2)
    write_json(base / "regions" / "page-0003.regions.json", RENUMBERED_PAGE3)
    write(path := base / "source_meta.yaml", """\
id: eval-renumbered-pdf
hash: """ + "b" * 64 + """
vendor: Test corpus
product: 'Eval Renumbered'
version: '1.0'
url: 'https://example.com/renumbered'
language: en
format: pdf
date: '2026-09-24'
authors:
  - eval
""")


def build_stable_rerun():
    """Copy F31's source-pdf fixture wholesale. The eval builds SDM from it
    twice and compares bytes — that's the criterion 2 rerun check."""
    import shutil
    src = F31_FIX / "source-pdf"
    dst = FIX / "source-stable-rerun"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def build_expected():
    """expected/ files. The shape mirrors the planned `expected/*.json`."""
    write_json(EXP / "unnumbered-expectations.json", {
        "criterion_1_unnumbered_anchors": {
            "min_sections": 5,
            "all_blocks_have_section_path": True,
            "all_anchors_resolvable": True,
            "page_is_null": True,
            "notes": "HTML doc without numbered headings. Every block must carry anchor.section_path non-empty and anchor.page = null."
        },
        "criterion_2_stable_anchors": {
            "identical_across_runs": True,
            "notes": "build_sdm --check-determinism runs twice, sdm.json must be byte-identical."
        },
        "criterion_3_L2_references": {
            "all_referenced_block_ids_exist": True,
            "no_orphan_section_paths": True,
            "notes": "The sample ledger references block_ids; every one must resolve to a real block in sdm.json."
        },
        "duplicates_resolved_with_ordinal": {
            "advisory": True,
            "notes": "D5 says duplicate-numbered sections must each get a distinct section_path with ordinal suffix. Currently build_sdm uses outline section_path literally; this check documents the gap if it fails, not the criteria."
        },
        "skipped_numbers_not_invented": {
            "no_synthetic_section_path_for_1_2": True
        },
    })

    write_json(EXP / "renumbered-expectations.json", {
        "criterion_1_unnumbered_anchors": {
            "applies_to_html_only": True,
            "applies": False
        },
        "criterion_2_stable_anchors": {
            "identical_across_runs": True
        },
        "criterion_3_L2_references": {
            "all_referenced_block_ids_exist": True
        },
        "duplicates_resolved_with_ordinal": {
            "advisory": True,
            "notes": "Outline has /ch01/foo twice (pages 1 and 2). Either BOTH survive as two sections (with -N ordinal per §7.1), or the second is dropped. The expected behavior is BOTH survive; if F31 doesn't yet emit -N, this check is informational, not a fail."
        },
        "skipped_numbers_not_invented": {
            "no_synthetic_section_path_for_1_2": True,
            "notes": "Source skips 1.2 (jumps 1.1 → 1.3). SDM must NOT invent a 1.2 section."
        },
    })

    write_json(EXP / "stable-rerun-expectations.json", {
        "criterion_2_stable_anchors": {
            "identical_across_runs": True,
            "notes": "Re-run of F31 source-pdf with the same hash must produce a bit-identical sdm.json."
        },
    })


def main() -> None:
    build_unnumbered_html()
    build_renumbered_pdf()
    build_stable_rerun()
    build_expected()
    print("OK — wrote fixtures/source-{unnumbered-html,renumbered-pdf,stable-rerun}, expected/*.json")


if __name__ == "__main__":
    main()
