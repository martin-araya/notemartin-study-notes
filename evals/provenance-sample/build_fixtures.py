#!/usr/bin/env python3
"""build_fixtures.py — F34 eval fixtures.

Emits 3 SDMs (pure JSON, no real source needed) that exercise each of the
3 criteria:
  - source-full:                 all fields read, version present.
  - source-web-docs-fallback:    vendor/product/version inferred via web_docs
                                 (lower confidence).
  - source-version-absent:       vendor+product present, version absent.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "evals" / "provenance-sample" / "fixtures"


def write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def doc_id(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:64]


def make_source(*, sid: str, vendor: str, product: str, version: str | None,
                url: str, language: str, fmt: str, source_provenance: dict,
                date: str = "2026-09-24", extra_source: dict | None = None,
                sections: list | None = None) -> dict:
    src: dict = {
        "id": sid,
        "hash": doc_id(f"{sid}-{vendor}-{product}-{version or ''}"),
        "algorithm": "sha256",
        "vendor": vendor,
        "product": product,
        "url": url,
        "language": language,
        "format": fmt,
        "date": date,
    }
    if version is not None:
        src["version"] = version
    if extra_source:
        src.update(extra_source)
    sdm: dict = {
        "schema_version": "1.0.0",
        "source": src,
        "source_provenance": source_provenance,
        "sections": sections or [
            {
                "section_path": "/ch01/intro",
                "title": "Intro",
                "blocks": [
                    {
                        "id": "bbea33d7135a", "type": "heading", "level": 1,
                        "content": {"level": 1, "text": "Hello"},
                        "anchor": {"page": 1, "section_path": "/ch01/intro"},
                        "confidence": 1.0, "origin": "native",
                    }
                ],
            }
        ],
    }
    return sdm


def full_prov(field: str, value, conf: float = 1.0) -> dict:
    return {"method": "read", "value": value, "confidence": conf}


def inferred_prov(field: str, value, method: str, reason: str, conf: float) -> dict:
    return {"method": method, "value": value, "confidence": conf, "reason": reason}


def build_source_full():
    """All fields are read (--source-meta). Vendor+product non-trivial.
    Criterion 1: every field has provenance. Criterion 2: method=read all.
    Criterion 3: version present, so no gate trip."""
    sid = "01-postgresql-chapter"
    sdm = make_source(
        sid=sid,
        vendor="PostgreSQL Global Development Group",
        product="PostgreSQL 16",
        version="16",
        url="https://www.postgresql.org/docs/16/sql.html",
        language="en",
        fmt="html",
        source_provenance={
            "id": full_prov("id", sid),
            "hash": full_prov("hash", doc_id(f"{sid}-...-16")),
            "algorithm": full_prov("algorithm", "sha256"),
            "vendor": full_prov("vendor", "PostgreSQL Global Development Group"),
            "product": full_prov("product", "PostgreSQL 16"),
            "version": full_prov("version", "16"),
            "edition": full_prov("edition", None),
            "isbn": full_prov("isbn", None),
            "authors": full_prov("authors", ["PGDG"]),
            "url": full_prov("url", "https://www.postgresql.org/docs/16/sql.html"),
            "language": full_prov("language", "en"),
            "date": full_prov("date", "2026-09-24"),
            "format": full_prov("format", "html"),
        },
        extra_source={"edition": None, "isbn": None, "authors": ["PGDG"]},
    )
    write(FIX / "source-full" / "sdm.json", sdm)


def build_source_web_docs_fallback():
    """Vendor/product/version inferred via web_docs.metadata (heuristic).
    Criterion 2: method='web_docs_metadata' with confidence<1.0 distinguishes them
    from read."""
    sid = "eval-web-docs-fallback"
    sdm = make_source(
        sid=sid,
        vendor="PostgreSQL Global Development Group",  # filled from web_docs
        product="PostgreSQL 17",
        version="17",
        url="https://www.postgresql.org/docs/17/sql.html",
        language="en",
        fmt="html",
        source_provenance={
            "id": full_prov("id", sid),
            "hash": inferred_prov("hash", doc_id(f"{sid}-...-17"),
                                  method="triage_metadata", reason="triage.sha256_of_pdf", conf=1.0),
            "algorithm": full_prov("algorithm", "sha256"),
            "vendor": inferred_prov(
                "vendor", "PostgreSQL Global Development Group",
                method="web_docs_metadata", reason="web_docs.metadata.domain", conf=0.9,
            ),
            "product": inferred_prov(
                "product", "PostgreSQL 17",
                method="web_docs_metadata", reason="web_docs.metadata.product", conf=0.9,
            ),
            "version": inferred_prov(
                "version", "17",
                method="url_regex", reason="url:docs/17/(\\d+)", conf=0.8,
            ),
            "edition": full_prov("edition", None),
            "isbn": full_prov("isbn", None),
            "authors": full_prov("authors", []),
            "url": full_prov("url", "https://www.postgresql.org/docs/17/sql.html"),
            "language": full_prov("language", "en"),
            "date": full_prov("date", "2026-09-24"),
            "format": full_prov("format", "html"),
        },
        extra_source={"authors": []},
    )
    write(FIX / "source-web-docs-fallback" / "sdm.json", sdm)


def build_source_version_absent():
    """Vendor+product present, version field present with method='absent'.
    Criterion 1: version entry exists (passes C1).
    Criterion 3 (no --require-version): warning (version absent flagged).
    Criterion 3 (--require-version): hard fail (documentation source)."""
    sid = "03-rfc-7231"
    sdm = make_source(
        sid=sid,
        vendor="IETF",
        product="RFC 7231",
        version=None,                    # absent
        url="https://datatracker.ietf.org/doc/html/rfc7231",
        language="en",
        fmt="html",
        source_provenance={
            "id": full_prov("id", sid),
            "hash": full_prov("hash", doc_id(f"{sid}-IETF-RFC7231")),
            "algorithm": full_prov("algorithm", "sha256"),
            "vendor": full_prov("vendor", "IETF"),
            "product": full_prov("product", "RFC 7231"),
            # version entry IS present per spec §5 contract — method='absent',
            # value=null. Validator's C1 sees the entry; C3 detects method=absent
            # + value=null and emits the gate.
            "version": {"method": "absent", "value": None, "confidence": 0.0,
                        "reason": "no_version_in_source"},
            "edition": full_prov("edition", None),
            "isbn": full_prov("isbn", None),
            "authors": full_prov("authors", []),
            "url": full_prov("url", "https://datatracker.ietf.org/doc/html/rfc7231"),
            "language": full_prov("language", "en"),
            "date": full_prov("date", "2026-09-24"),
            "format": full_prov("format", "html"),
        },
        extra_source={"authors": []},
    )
    write(FIX / "source-version-absent" / "sdm.json", sdm)


def build_expected():
    """Expected values used by run_eval.py."""
    E = FIX.parent / "expected"
    (E / "full-expectations.json").write_text(json.dumps({
        "criteria_pass": ["C1", "C2", "C3"],
        "read_field_count_min": 12,
        "inferred_field_count_max": 0,
        "missing_version": False,
    }, indent=2) + "\n", encoding="utf-8")

    (E / "fallback-expectations.json").write_text(json.dumps({
        "criteria_pass": ["C1", "C2"],
        "criteria_warn": ["C3"],  # if had --require-version would hard fail
        "inferred_field_count_min": 3,
        "inferred_fields": ["vendor", "product", "version"],
        "read_field_count_min": 7,
        "missing_version": False,
    }, indent=2) + "\n", encoding="utf-8")

    (E / "absent-expectations.json").write_text(json.dumps({
        "criteria_pass_without_require_version": ["C1", "C2"],
        "criteria_hard_fail_with_require_version": True,
        "missing_version": True,
        "is_documentation": True,
    }, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    build_source_full()
    build_source_web_docs_fallback()
    build_source_version_absent()
    build_expected()
    print("OK — wrote 3 fixtures + expected/")


if __name__ == "__main__":
    main()
