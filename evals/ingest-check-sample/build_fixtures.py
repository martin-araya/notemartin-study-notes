#!/usr/bin/env python3
"""build_fixtures.py — Generate synthetic fixtures for F30 eval.

Builds 3 scenarios in evals/ingest-check-sample/scenarios/:
  - sdm-with-missing-page/ — page-0001.json + page-0003.json (page 2 omitted)
  - sdm-with-missing-section/ — page-0001.json + page-0002.json with headings
    1.1, 1.2 but NOT 1.3; declared-index contains 1.1, 1.2, 1.3
  - sdm-critical/ — multiple critical anomalies (missing page + missing section)
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

SCENARIOS = Path(__file__).resolve().parent / "scenarios"


def _build_sdm_with_missing_page() -> Path:
    """pages 1 and 3, missing page 2."""
    out = SCENARIOS / "sdm-with-missing-page"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    page1 = {
        "page": 1,
        "regions": [
            {"id": "r001", "page": 1, "semantic_class": "heading", "level": 1, "number": "1", "text": "Introduction", "word_count": 1},
            {"id": "r002", "page": 1, "semantic_class": "text", "text": "Lorem ipsum dolor sit amet.", "word_count": 5},
        ],
    }
    page3 = {
        "page": 3,
        "regions": [
            {"id": "r003", "page": 3, "semantic_class": "heading", "level": 1, "number": "2", "text": "Methods", "word_count": 1},
            {"id": "r004", "page": 3, "semantic_class": "text", "text": "Methods section content.", "word_count": 3},
        ],
    }
    (out / "page-0001.regions.json").write_text(json.dumps(page1, indent=2), encoding="utf-8")
    (out / "page-0003.regions.json").write_text(json.dumps(page3, indent=2), encoding="utf-8")
    declared_index = {
        "pages": [1, 2, 3],
        "sections": [
            {"number": "1", "title": "Introduction", "expected_pages": [1]},
            {"number": "2", "title": "Methods", "expected_pages": [3]},
        ],
    }
    (out / "declared-index.json").write_text(json.dumps(declared_index, indent=2), encoding="utf-8")
    return out


def _build_sdm_with_missing_section() -> Path:
    """Pages 1, 2 with headings 1.1, 1.2 but NOT 1.3; declared-index contains 1.1, 1.2, 1.3."""
    out = SCENARIOS / "sdm-with-missing-section"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    page1 = {
        "page": 1,
        "regions": [
            {"id": "r001", "page": 1, "semantic_class": "heading", "level": 1, "number": "1.1", "text": "Background", "word_count": 1},
            {"id": "r002", "page": 1, "semantic_class": "text", "text": "Background content here.", "word_count": 3},
        ],
    }
    page2 = {
        "page": 2,
        "regions": [
            {"id": "r003", "page": 2, "semantic_class": "heading", "level": 1, "number": "1.2", "text": "Prior Work", "word_count": 2},
            {"id": "r004", "page": 2, "semantic_class": "text", "text": "Prior work discussion.", "word_count": 3},
        ],
    }
    (out / "page-0001.regions.json").write_text(json.dumps(page1, indent=2), encoding="utf-8")
    (out / "page-0002.regions.json").write_text(json.dumps(page2, indent=2), encoding="utf-8")
    declared_index = {
        "pages": [1, 2],
        "sections": [
            {"number": "1.1", "title": "Background", "expected_pages": [1]},
            {"number": "1.2", "title": "Prior Work", "expected_pages": [2]},
            {"number": "1.3", "title": "Methods", "expected_pages": [2]},
        ],
    }
    (out / "declared-index.json").write_text(json.dumps(declared_index, indent=2), encoding="utf-8")
    return out


def _build_sdm_critical() -> Path:
    """Multiple critical anomalies: missing page + missing section + empty heading."""
    out = SCENARIOS / "sdm-critical"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    page1 = {
        "page": 1,
        "regions": [
            {"id": "r001", "page": 1, "semantic_class": "heading", "level": 1, "number": "1", "text": "Title", "word_count": 1},
            {"id": "r002", "page": 1, "semantic_class": "text", "text": "Body content.", "word_count": 2},
        ],
    }
    page3 = {
        "page": 3,
        "regions": [
            {"id": "r003", "page": 3, "semantic_class": "heading", "level": 1, "number": "2", "text": "", "word_count": 0},
            {"id": "r004", "page": 3, "semantic_class": "text", "text": "Content for section 2.", "word_count": 4},
        ],
    }
    (out / "page-0001.regions.json").write_text(json.dumps(page1, indent=2), encoding="utf-8")
    (out / "page-0003.regions.json").write_text(json.dumps(page3, indent=2), encoding="utf-8")
    declared_index = {
        "pages": [1, 2, 3],
        "sections": [
            {"number": "1", "title": "Title", "expected_pages": [1]},
            {"number": "2", "title": "Section Two", "expected_pages": [3]},
        ],
    }
    (out / "declared-index.json").write_text(json.dumps(declared_index, indent=2), encoding="utf-8")
    return out


def main() -> int:
    SCENARIOS.mkdir(parents=True, exist_ok=True)
    for fn in (
        _build_sdm_with_missing_page,
        _build_sdm_with_missing_section,
        _build_sdm_critical,
    ):
        out = fn()
        files = sorted(p.name for p in out.iterdir())
        print(f"Wrote {out} ({', '.join(files)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
