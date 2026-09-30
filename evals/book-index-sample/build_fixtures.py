#!/usr/bin/env python3
"""build_fixtures.py — F110 eval fixtures para book_index.

Genera un workdir sintético con:
  - 5 IRs (1 concept, 1 cheatsheet, 1 practice, 1 glossary-term, 1 procedure)
  - glossary.json con 3 términos canónicos
  - concept-graph.json (F39) con 4 nodos + 3 aristas
  - book-state.json (F106) con 3 capítulos (2 done, 1 pending)
  - book_map.mmd (F106) con graph LR
  - reports/{cheatsheets-index,study-paths,report-link-debt}.json (F109)
  - manifest.json (F16)

Stdlib puro.

Uso:
    python3 evals/book-index-sample/build_fixtures.py [--regen]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
WORKDIR = FIXTURES_DIR / "workdir"
IR_DIR = WORKDIR / "ir"
KNOWLEDGE_DIR = WORKDIR / "knowledge"
REPORTS_DIR = WORKDIR / "reports"
EXPECTED_DIR = Path(__file__).resolve().parent / "expected"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_irs() -> None:
    if IR_DIR.exists():
        shutil.rmtree(IR_DIR)
    IR_DIR.mkdir(parents=True)
    # IRs: 1 concept, 1 cheatsheet, 1 practice, 1 glossary-term, 1 procedure.
    _write_json(IR_DIR / "mvcc.note-ir.json", {
        "schema_version": "1.0.0", "note_id": "mvcc", "title": "MVCC",
        "layer": "l2", "note_type": "concept",
        "frontmatter": {"title": "MVCC", "note-type": "concept"},
        "blocks": [{"node": "text",
                    "attrs": {"text": "Multi-Version Concurrency Control.",
                                "capability": "text"}, "source_refs": []}],
    })
    _write_json(IR_DIR / "wal-cheatsheet.note-ir.json", {
        "schema_version": "1.0.0", "note_id": "wal-cheatsheet",
        "title": "WAL Cheatsheet", "layer": "l1", "note_type": "cheatsheet",
        "frontmatter": {"title": "WAL Cheatsheet",
                          "note-type": "cheatsheet",
                          "source-anchor": "Chapter 9.1"},
        "blocks": [{"node": "text",
                    "attrs": {"text": "Quick reference for WAL.",
                                "capability": "text"}, "source_refs": []}],
    })
    _write_json(IR_DIR / "backup-practice.note-ir.json", {
        "schema_version": "1.0.0", "note_id": "backup-practice",
        "title": "Backup Practice", "layer": "l1", "note_type": "practice",
        "frontmatter": {"title": "Backup Practice", "note-type": "practice"},
        "blocks": [{"node": "text",
                    "attrs": {"text": "Practice exercises.",
                                "capability": "text"}, "source_refs": []}],
    })
    _write_json(IR_DIR / "mvcc-glossary.note-ir.json", {
        "schema_version": "1.0.0", "note_id": "mvcc-glossary",
        "title": "MVCC Glossary", "layer": "l1", "note_type": "glossary-term",
        "frontmatter": {"title": "MVCC Glossary", "note-type": "glossary-term"},
        "blocks": [{"node": "text",
                    "attrs": {"text": "Glossary entry for MVCC.",
                                "capability": "text"}, "source_refs": []}],
    })
    _write_json(IR_DIR / "postgres-config.note-ir.json", {
        "schema_version": "1.0.0", "note_id": "postgres-config",
        "title": "Postgres Config", "layer": "l2", "note_type": "procedure",
        "frontmatter": {"title": "Postgres Config", "note-type": "procedure"},
        "blocks": [{"node": "text",
                    "attrs": {"text": "Procedure for config.",
                                "capability": "text"}, "source_refs": []}],
    })


def build_glossary() -> None:
    if KNOWLEDGE_DIR.exists():
        shutil.rmtree(KNOWLEDGE_DIR)
    KNOWLEDGE_DIR.mkdir(parents=True)
    _write_json(KNOWLEDGE_DIR / "glossary.json", {
        "schema_version": "1.0.0",
        "source": {"id": "postgres", "vendor": "pg"},
        "terms": [
            {"canonical": "mvcc",
             "definition": "Multi-Version Concurrency Control.",
             "domain": "postgres",
             "aliases": [{"alias": "mv", "kind": "acronym"}],
             "definitions": []},
            {"canonical": "wal",
             "definition": "Write-Ahead Logging.",
             "domain": "postgres",
             "aliases": [],
             "definitions": []},
            {"canonical": "vacuum",
             "definition": "Process that reclaims space.",
             "domain": "postgres",
             "aliases": [],
             "definitions": []},
        ],
        "build_metadata": {"built_at": "2026-01-01T00:00:00Z", "term_count": 3},
    })


def build_concept_graph() -> None:
    _write_json(WORKDIR / "concept-graph.json", {
        "schema_version": "1.0.0",
        "nodes": [
            {"id": "mvcc", "label": "MVCC"},
            {"id": "wal", "label": "Write-Ahead Logging"},
            {"id": "vacuum", "label": "VACUUM"},
            {"id": "tx", "label": "Transaction"},
        ],
        "edges": [
            {"from": "mvcc", "to": "wal", "label": "uses"},
            {"from": "vacuum", "to": "mvcc", "label": "depends on"},
            {"from": "tx", "to": "mvcc", "label": "controlled by"},
        ],
    })


def build_book_state() -> None:
    """Genera book-state.json con F106 schema (chapters[])."""
    _write_json(WORKDIR / "book-state.json", {
        "schema_version": "1.0.0",
        "source_hash": "a" * 64,
        "chunk_strategy": "by_chapter",
        "chapters": [
            {"id": "ch01", "title": "Intro", "status": "done",
             "started_at": "2026-09-30T00:00:00Z",
             "processed_at": "2026-09-30T01:00:00Z",
             "previous_processed_at": None,
             "notes_written": ["mvcc", "mvcc-glossary"], "error": None},
            {"id": "ch02", "title": "Concurrency", "status": "done",
             "started_at": "2026-09-30T01:00:00Z",
             "processed_at": "2026-09-30T02:00:00Z",
             "previous_processed_at": None,
             "notes_written": ["wal-cheatsheet", "postgres-config"], "error": None},
            {"id": "ch03", "title": "Operations", "status": "pending",
             "started_at": None, "processed_at": None,
             "previous_processed_at": None,
             "notes_written": ["backup-practice"], "error": None},
        ],
        "config": {"chunk_strategy": "by_chapter", "chunk_size": 3,
                    "neighbor_window": 1, "strict_no_full_load": True},
        "created_at": "2026-09-30T00:00:00Z",
        "updated_at": "2026-09-30T00:00:00Z",
    })


def build_book_map() -> None:
    _write_text(WORKDIR / "book_map.mmd",
        "```mermaid\n"
        "graph LR\n"
        "  CH01[\"Chapter 1 (Intro)\"]\n"
        "  CH02[\"Chapter 2 (Concurrency)\"]\n"
        "  CH03[\"Chapter 3 (Operations)\"]\n"
        "  CH01 --> CH02\n"
        "  CH02 --> CH03\n"
        "```\n"
    )


def build_reports() -> None:
    if REPORTS_DIR.exists():
        shutil.rmtree(REPORTS_DIR)
    REPORTS_DIR.mkdir(parents=True)
    _write_json(REPORTS_DIR / "cheatsheets-index.json", {
        "schema_version": "1.0.0",
        "generated_at": "2026-09-30T00:00:00Z",
        "cheatsheets": [
            {"note_id": "wal-cheatsheet", "title": "WAL Cheatsheet",
             "source_anchor": "Chapter 9.1"},
        ],
        "count": 1,
    })
    _write_json(REPORTS_DIR / "study-paths.json", {
        "schema_version": "1.0.0",
        "generated_at": "2026-09-30T00:00:00Z",
        "paths": [
            {"id": "MVP", "steps": ["mvcc", "wal-cheatsheet"]},
            {"id": "Advanced", "steps": ["mvcc", "postgres-config", "backup-practice"]},
        ],
    })
    _write_json(REPORTS_DIR / "report-link-debt.json", {
        "schema_version": "1.0.0",
        "generated_at": "2026-09-30T00:00:00Z",
        "total_link_debt": 2,
        "count_by_kind": {
            "broken-wikilink": 1, "missing-target": 0,
            "orphan-note": 1, "redirected": 0, "external-dead": 0,
        },
    })


def build_manifest() -> None:
    _write_json(WORKDIR / "manifest.json", {
        "schema_version": "1.0.0",
        "source": {"id": "postgres-doc", "path": ".", "hash": "a" * 64,
                    "algorithm": "sha256"},
        "current_stage": "l3",
        "stage_progress": {"l0": "done", "l1": "done", "l2": "done",
                            "l3": "in_progress"},
        "published_notes": [],
        "link_debt": [],
        "consolidation_runs": [],
        "last_modified": "2026-09-30T00:00:00Z",
    })


def write_expected() -> None:
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)
    expected = {
        "section_count": 10,
        "sections_order": [
            "Ficha", "Mapa de capítulos", "Grafo de dependencias",
            "Rutas de lectura", "Cobertura por capítulo", "Glosario",
            "Cheatsheets", "Prácticas", "Erratas", "Progreso",
        ],
        "coverage_chapters_total": 3,
        "coverage_done_count": 2,
        "glossary_terms_total": 3,
        "concept_graph_nodes": 4,
        "concept_graph_edges": 3,
        "cheatsheet_count": 1,
        "practice_count": 1,
    }
    (EXPECTED_DIR / "expected.json").write_text(
        json.dumps(expected, indent=2), encoding="utf-8"
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--regen", action="store_true")
    args = p.parse_args()
    build_irs()
    build_glossary()
    build_concept_graph()
    build_book_state()
    build_book_map()
    build_reports()
    build_manifest()
    write_expected()
    sys.stdout.write(
        "OK — 5 IRs; glossary; concept-graph; book-state; book_map; "
        "3 F109 reports; manifest\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())