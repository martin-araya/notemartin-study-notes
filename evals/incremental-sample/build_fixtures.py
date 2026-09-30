#!/usr/bin/env python3
"""build_fixtures.py — F111 eval fixtures para update.

Genera:
  - fixtures/old_sdm.json   — SDM v15 con 4 bloques (b1..b4) en 3 capítulos.
  - fixtures/new_sdm.json   — SDM v16 con b1 (unchanged), b2 (modified),
                              b3 REMOVED, b5 ADDED.
  - fixtures/workdir/ir/{a,b,c,d}.note-ir.json
    - a: refs b1 (unchanged) → unaffected.
    - b: refs b2 (modified) → re-processable, no obsoleto.
    - c: refs b3 (removed) → obsoleted con superseded_by=d.
    - d: refs b5 (added) → nueva IR sister.
  - fixtures/workdir/manifest.json con published_notes en obsidian.

Stdlib puro.

Uso:
    python3 evals/incremental-sample/build_fixtures.py [--regen]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
OLD_DIR = FIXTURES_DIR / "old"
WORKDIR = FIXTURES_DIR / "workdir"
IR_DIR = WORKDIR / "ir"
EXPECTED_DIR = Path(__file__).resolve().parent / "expected"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_sdm_files() -> None:
    OLD_DIR.mkdir(parents=True, exist_ok=True)
    # OLD SDM: 4 blocks.
    old = {
        "schema_version": "1.0.0",
        "source": {"id": "postgres-doc", "vendor": "postgres",
                    "hash": "a" * 64, "version": "15.0"},
        "blocks": [
            {"block_id": "b1", "type": "text", "text": "MVCC intro unchanged",
             "anchor": {"section_path": "/ch01/intro", "page": 1}},
            {"block_id": "b2", "type": "text", "text": "WAL old text",
             "anchor": {"section_path": "/ch02/main", "page": 5}},
            {"block_id": "b3", "type": "text", "text": "Deprecated section",
             "anchor": {"section_path": "/ch03/deprecated", "page": 10}},
            {"block_id": "b4", "type": "text", "text": "Misc",
             "anchor": {"section_path": "/ch04/misc", "page": 15}},
        ],
    }
    _write_json(OLD_DIR / "old_sdm.json", old)
    # NEW SDM: b1 unchanged, b2 modified, b3 removed, b5 added.
    new = {
        "schema_version": "1.0.0",
        "source": {"id": "postgres-doc", "vendor": "postgres",
                    "hash": "b" * 64, "version": "16.0"},
        "blocks": [
            {"block_id": "b1", "type": "text", "text": "MVCC intro unchanged",
             "anchor": {"section_path": "/ch01/intro", "page": 1}},
            {"block_id": "b2", "type": "text", "text": "WAL NEW text",
             "anchor": {"section_path": "/ch02/main", "page": 5}},
            {"block_id": "b4", "type": "text", "text": "Misc",
             "anchor": {"section_path": "/ch04/misc", "page": 15}},
            {"block_id": "b5", "type": "text", "text": "New section",
             "anchor": {"section_path": "/ch05/new", "page": 20}},
        ],
    }
    _write_json(OLD_DIR / "new_sdm.json", new)


def build_irs() -> None:
    if IR_DIR.exists():
        shutil.rmtree(IR_DIR)
    IR_DIR.mkdir(parents=True)
    # IR `a`: refs b1 (unchanged) — no afectada.
    _write_json(IR_DIR / "a.note-ir.json", {
        "schema_version": "1.0.0", "note_id": "a", "title": "A",
        "layer": "l2", "note_type": "concept",
        "frontmatter": {"title": "A", "note-type": "concept",
                          "status": "done"},
        "blocks": [{"node": "paragraph", "attrs": {"capability": "paragraph"},
                     "source_refs": [{"block_id": "b1", "source_hash": "a" * 64,
                                       "section_path": "/ch01/intro"}],
                     "children": [{"node": "text",
                                     "attrs": {"text": "A body",
                                                 "capability": "text"},
                                     "source_refs": []}]}],
    })
    # IR `b`: refs b2 (modified) — re-processable, no obsoleto.
    _write_json(IR_DIR / "b.note-ir.json", {
        "schema_version": "1.0.0", "note_id": "b", "title": "B",
        "layer": "l2", "note_type": "concept",
        "frontmatter": {"title": "B", "note-type": "concept",
                          "status": "done"},
        "blocks": [{"node": "paragraph", "attrs": {"capability": "paragraph"},
                     "source_refs": [{"block_id": "b2", "source_hash": "a" * 64,
                                       "section_path": "/ch02/main"}],
                     "children": [{"node": "text",
                                     "attrs": {"text": "B body",
                                                 "capability": "text"},
                                     "source_refs": []}]}],
    })
    # IR `c`: refs b3 (removed) — obsoleted con superseded_by=d.
    _write_json(IR_DIR / "c.note-ir.json", {
        "schema_version": "1.0.0", "note_id": "c", "title": "C",
        "layer": "l2", "note_type": "concept",
        "frontmatter": {"title": "C", "note-type": "concept",
                          "status": "done"},
        "blocks": [{"node": "paragraph", "attrs": {"capability": "paragraph"},
                     "source_refs": [{"block_id": "b3", "source_hash": "a" * 64,
                                       "section_path": "/ch03/deprecated"}],
                     "children": [{"node": "text",
                                     "attrs": {"text": "C body",
                                                 "capability": "text"},
                                     "source_refs": []}]}],
    })
    # IR `d`: refs b5 (added) — nueva sister IR.
    _write_json(IR_DIR / "d.note-ir.json", {
        "schema_version": "1.0.0", "note_id": "d", "title": "D",
        "layer": "l2", "note_type": "concept",
        "frontmatter": {"title": "D", "note-type": "concept",
                          "status": "done"},
        "blocks": [{"node": "paragraph", "attrs": {"capability": "paragraph"},
                     "source_refs": [{"block_id": "b5", "source_hash": "b" * 64,
                                       "section_path": "/ch05/new"}],
                     "children": [{"node": "text",
                                     "attrs": {"text": "D body",
                                                 "capability": "text"},
                                     "source_refs": []}]}],
    })


def build_manifest() -> None:
    _write_json(WORKDIR / "manifest.json", {
        "schema_version": "1.0.0",
        "source": {"id": "postgres-doc", "path": ".", "hash": "a" * 64,
                    "algorithm": "sha256"},
        "current_stage": "l3",
        "stage_progress": {"l0": "done", "l1": "done", "l2": "done",
                            "l3": "done"},
        "published_notes": [
            {"note_id": "a", "destination": "obsidian",
             "remote_id": "obs-a-uuid",
             "published_at": "2026-01-01T00:00:00Z",
             "last_updated": "2026-01-01T00:00:00Z"},
            {"note_id": "b", "destination": "obsidian",
             "remote_id": "obs-b-uuid",
             "published_at": "2026-01-01T00:00:00Z",
             "last_updated": "2026-01-01T00:00:00Z"},
        ],
        "link_debt": [],
        "consolidation_runs": [],
        "last_modified": "2026-01-01T00:00:00Z",
    })


def write_expected() -> None:
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)
    expected = {
        "obsoleted_ir_ids": ["c"],
        "affected_ir_ids_count_min": 2,
        "delta_id_pattern": r"^vd\d{4,}$",
        "obsoleted_count": 1,
        "added_count": 1,
        "modified_count": 1,
        "removed_count": 1,
        "unchanged_count_min": 1,
    }
    (EXPECTED_DIR / "expected.json").write_text(
        json.dumps(expected, indent=2), encoding="utf-8"
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--regen", action="store_true")
    args = p.parse_args()
    build_sdm_files()
    build_irs()
    build_manifest()
    write_expected()
    sys.stdout.write(
        "OK — 2 SDMs (old + new); 4 IRs (a/b/c/d); manifest.json\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())