#!/usr/bin/env python3
"""build_fixtures.py — F36 eval fixtures.

Emits synthetic SDM fixtures used by `run_eval.py`:

  - fixtures/source-A/sdm.json
      6 blocks of varied types + 1 block with confidence < 0.7 (criteria 3).
      Each block has `id` and `anchor.{page, section_path}` so the viewer's
      hierarchy can render.
  - fixtures/source-B/sdm.json
      Smaller source for cross-SDM variants in the cache run.

The cache eval uses these synthetic sdms only as fixtures for the viewer.
The cache itself is exercised with synthetic JSON values via the cache
library directly (no fixture needed beyond an empty cache_dir).

Uso:
    python3 evals/sdm-cache-sample/build_fixtures.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "evals" / "sdm-cache-sample" / "fixtures"


def write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sdm_template(sid: str, vendor: str, product: str, blocks: list, fmt: str = "pdf") -> dict:
    return {
        "schema_version": "1.0.0",
        "source": {
            "id": sid,
            "hash": "a" * 64,
            "algorithm": "sha256",
            "vendor": vendor,
            "product": product,
            "url": f"https://example.com/{sid}",
            "language": "en",
            "format": fmt,
        },
        "sections": [
            {
                "section_path": "/ch01/intro",
                "title": "Intro",
                "blocks": blocks,
            },
            {
                "section_path": "/ch01/concepts",
                "title": "Concepts",
                "blocks": [],
            },
        ],
    }


# Block fixtures with deterministic id-like shape (12 hex char per F13 spec).
def block(bid: str, btype: str, content, page: int, conf: float = 1.0,
          origin: str = "native", section_path: str = "/ch01/intro") -> dict:
    return {
        "id": bid,
        "type": btype,
        "content": content,
        "anchor": {"page": page, "section_path": section_path},
        "confidence": conf,
        "origin": origin,
    }


def build_source_A():
    blocks = [
        # 6 blocks of varied types including 2 low confidence (< 0.7)
        block("a000000001", "heading", {"level": 1, "text": "Chapter 1"}, page=1, conf=1.0),
        block("a000000002", "prose", "Distributed databases are the backbone of modern infrastructure.",
              page=1, conf=0.85),
        block("a000000003", "code", {"lang": "python", "text": "def hello():\n    return 42"},
              page=1, conf=0.92),
        block("a000000004", "table",
              {"headers": ["Name", "Type"], "rows": [["foo", "string"], ["bar", "int"]]},
              page=2, conf=0.78),
        # LOW confidence: tests criterion 3 filter visibility
        block("a000000005", "prose", "This section reads ambiguously in OCR.",
              page=2, conf=0.42, origin="ocr"),
        # Lower-confidence warning
        block("a000000006", "warning", {"text": "dangerous operation: review before proceeding.",
                                         "severity": "caution"},
              page=2, conf=0.55, origin="ocr"),
    ]
    sdm = sdm_template("eval-source-A", "Test corpus", "Eval Source A", blocks)
    write(FIX / "source-A" / "sdm.json", sdm)


def build_source_B():
    blocks = [
        block("b000000001", "prose", "Reference architecture diagram", page=1, conf=1.0),
        block("b000000002", "list",
              {"items": [{"text": "alpha"}, {"text": "beta"}, {"text": "gamma"}]},
              page=1, conf=1.0),
        block("b000000003", "code", {"lang": "sql", "text": "SELECT 1;"}, page=2, conf=0.95),
    ]
    sdm = sdm_template("eval-source-B", "Test corpus", "Eval Source B", blocks, fmt="html")
    write(FIX / "source-B" / "sdm.json", sdm)


def build_expected():
    E = FIX.parent / "expected"
    E.mkdir(parents=True, exist_ok=True)
    (E / "viewer-expected.json").write_text(json.dumps({
        "criteria_pass": ["c1_low_confidence_filter_present", "c2_low_confidence_blocks_visible"],
        "low_confidence_blocks_min": 2,        # at least 2 blocks with conf<0.7
        "types_in_dropdown_min": 5,             # dropdown has 5 distinct types min
        "filters_present": [
            "data-filter=type",
            "data-filter=confidence",
            "data-filter=boilerplate",
            "data-action=low-confidence",
        ],
    }, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    build_source_A()
    build_source_B()
    build_expected()
    print("OK — wrote 2 sdm fixtures + expected/")


if __name__ == "__main__":
    main()
