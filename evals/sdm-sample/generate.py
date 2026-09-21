#!/usr/bin/env python3
"""Genera los 14 SDMs mínimos del corpus + 1 canónico para Fase 13.

Uso:
    python3 evals/sdm-sample/generate.py
    # Escribe evals/sdm-sample/<NN>-<id>.json (14 archivos)
    #       y evals/sdm-sample/01-postgresql-chapter-full.json (canónico).

No dependencias externas.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CORPUS = REPO / "evals" / "corpus"
OUT = REPO / "evals" / "sdm-sample"
OUT.mkdir(parents=True, exist_ok=True)


def block_id(source_hash: str, section_path: str, idx: int) -> str:
    h = hashlib.sha1()
    h.update(source_hash.encode("utf-8"))
    h.update(section_path.encode("utf-8"))
    h.update(str(idx).encode("utf-8"))
    return h.hexdigest()[:12]


def sha256_hex(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# (id, vendor, product, url, language, format, sample_file, blocks_spec, section_path)
# blocks_spec: list of (type, content_factory(idx))
SOURCES = [
    {
        "id": "01-postgresql-chapter",
        "vendor": "PostgreSQL Global Development Group",
        "product": "PostgreSQL 16",
        "version": "16",
        "url": "https://www.postgresql.org/docs/16/sql.html",
        "language": "en",
        "format": "html",
        "sample": "sample.html",
        "section_path": "/ch02/intro",
        "blocks": [
            ("heading", lambda i: {"level": 2, "text": "The SQL Language"}),
            ("prose",   lambda i: "This chapter describes the SQL language as implemented in PostgreSQL 16."),
            ("table",   lambda i: {"headers": ["name", "type"], "rows": [["foo", "string"], ["bar", "integer"]]}),
            ("code",    lambda i: {"lang": "sql", "text": "SELECT * FROM pg_class WHERE relkind = 'r';"}),
        ],
    },
    {
        "id": "02-database-internals-chapter",
        "vendor": "O'Reilly Media",
        "product": "Database Internals",
        "version": "1st Edition",
        "isbn": "978-1492040347",
        "url": "https://www.databass.dev/",
        "language": "en",
        "format": "pdf",
        "sample": None,
        "section_path": "/ch01/introduction",
        "blocks": [
            ("heading", lambda i: {"level": 1, "text": "Introduction"}),
            ("prose",   lambda i: "Distributed databases are a core building block of modern infrastructure."),
            ("figure",  lambda i: {"src": "assets/architecture.png", "alt": "Database architecture"}),
            ("caption", lambda i: "Figure 1.1: High-level architecture of a distributed database."),
        ],
    },
    {
        "id": "03-rfc-7231",
        "vendor": "IETF",
        "product": "RFC 7231",
        "version": "7231",
        "url": "https://datatracker.ietf.org/doc/html/rfc7231",
        "language": "en",
        "format": "html",
        "sample": "sample.txt",
        "section_path": "/section-4-request-methods",
        "blocks": [
            ("heading", lambda i: {"level": 2, "text": "Request Methods"}),
            ("prose",   lambda i: "The Request-Line begins with a method token."),
            ("code",    lambda i: {"lang": "http", "text": "GET /index.html HTTP/1.1"}),
            ("footnote",lambda i: {"text": "See RFC 7230 for connection management.", "ref": "1"}),
        ],
    },
    {
        "id": "04-arxiv-two-column",
        "vendor": "arXiv",
        "product": "arXiv preprint",
        "url": "https://arxiv.org/abs/cs.DC/0001001",
        "language": "en",
        "format": "pdf",
        "sample": "sample.pdf",
        "section_path": "/abstract",
        "blocks": [
            ("heading", lambda i: {"level": 2, "text": "Abstract"}),
            ("prose",   lambda i: "We present a new approach to distributed consensus."),
            ("formula", lambda i: {"latex": "P = \\lim_{n \\to \\infty} \\frac{1}{n} \\sum_{i=1}^n X_i", "display": True}),
        ],
    },
    {
        "id": "05-iso-sql-tables",
        "vendor": "ISO/IEC",
        "product": "ISO/IEC 9075:2023 SQL",
        "version": "2023",
        "url": "https://www.iso.org/standard/76583.html",
        "language": "en",
        "format": "pdf",
        "sample": "sample.html",
        "section_path": "/annex-a",
        "blocks": [
            ("heading", lambda i: {"level": 2, "text": "Annex A (informative)"}),
            ("prose",   lambda i: "This annex provides additional context for the SQL standard."),
            ("table",   lambda i: {"headers": ["Feature", "Status"], "rows": [["Feature 1", "mandatory"], ["Feature 2", "optional"]]}),
        ],
    },
    {
        "id": "06-kubernetes-api-ref",
        "vendor": "Cloud Native Computing Foundation",
        "product": "Kubernetes API Reference",
        "url": "https://kubernetes.io/docs/reference/kubernetes-api/",
        "language": "en",
        "format": "html",
        "sample": "sample.html",
        "section_path": "/workload-resources/pod-v1",
        "blocks": [
            ("heading", lambda i: {"level": 2, "text": "Pod v1"}),
            ("prose",   lambda i: "Pod is a collection of containers that can run on a host."),
            ("list",    lambda i: {"ordered": False, "items": ["spec.containers", "spec.restartPolicy", "spec.nodeSelector"]}),
            ("code",    lambda i: {"lang": "yaml", "text": "apiVersion: v1\nkind: Pod"}),
        ],
    },
    {
        "id": "07-docker-cli-ref",
        "vendor": "Docker Inc.",
        "product": "Docker Engine CLI",
        "url": "https://docs.docker.com/engine/reference/commandline/cli/",
        "language": "en",
        "format": "html",
        "sample": "sample.html",
        "section_path": "/run",
        "blocks": [
            ("heading", lambda i: {"level": 2, "text": "docker run"}),
            ("prose",   lambda i: "Run a command in a new container."),
            ("code",    lambda i: {"lang": "bash", "text": "docker run -d --name web nginx:alpine"}),
            ("console", lambda i: {"lines": ["$ docker ps --filter name=web", "CONTAINER ID   IMAGE          PORTS     NAMES", "abc123         nginx:alpine   80/tcp    web"]}),
        ],
    },
    {
        "id": "08-conference-transcript",
        "vendor": "PostgreSQL Conference",
        "product": "Conference Transcript",
        "url": "https://www.postgresqlconference.org/",
        "language": "en",
        "format": "transcript",
        "sample": None,
        "section_path": "/talk/intro",
        "blocks": [
            ("heading", lambda i: {"level": 2, "text": "Talk Introduction"}),
            ("prose",   lambda i: "Speaker: Today I want to talk about MVCC implementation in PostgreSQL."),
            ("list",    lambda i: {"ordered": True, "items": ["Why MVCC matters", "Implementation details", "Operational tips"]}),
        ],
    },
    {
        "id": "09-conference-slides",
        "vendor": "PostgreSQL Conference",
        "product": "Conference Slides",
        "url": "https://www.postgresqlconference.org/",
        "language": "en",
        "format": "pdf",
        "sample": None,
        "section_path": "/slide-3",
        "blocks": [
            ("heading", lambda i: {"level": 2, "text": "Slide 3: Architecture"}),
            ("prose",   lambda i: "Two-layer storage: shared buffers + WAL."),
            ("figure",  lambda i: {"src": "assets/slide-3.png", "alt": "Architecture diagram"}),
            ("caption", lambda i: "Two-layer storage with WAL."),
        ],
    },
    {
        "id": "10-postgres-readme-repo",
        "vendor": "PostgreSQL Global Development Group",
        "product": "PostgreSQL GitHub README",
        "url": "https://github.com/postgres/postgres",
        "language": "en",
        "format": "repo",
        "sample": "sample.md",
        "section_path": "/readme",
        "blocks": [
            ("heading", lambda i: {"level": 2, "text": "PostgreSQL"}),
            ("prose",   lambda i: "PostgreSQL is an advanced object-relational database management system."),
            ("code",    lambda i: {"lang": "sh", "text": "./configure && make && make install"}),
            ("list",    lambda i: {"ordered": False, "items": ["Multi-version concurrency control", "Point-in-time recovery", "SQL/MED"]}),
        ],
    },
    {
        "id": "11-iso-cpp-syntax",
        "vendor": "ISO/IEC",
        "product": "ISO C++ Standard Draft",
        "version": "n4910",
        "url": "https://www.iso.org/standard/83626.html",
        "language": "en",
        "format": "html",
        "sample": "sample.html",
        "section_path": "/syntax/declaration",
        "blocks": [
            ("heading", lambda i: {"level": 2, "text": "Declaration syntax"}),
            ("prose",   lambda i: "A declaration introduces one or more names into a scope."),
            ("syntax-diagram", lambda i: {"notation": "ebnf", "text": "declaration := block-declaration | function-definition | template-declaration"}),
            ("code",    lambda i: {"lang": "cpp", "text": "int x = 42;"}),
        ],
    },
    {
        "id": "12-arxiv-formulas",
        "vendor": "arXiv",
        "product": "arXiv preprint",
        "url": "https://arxiv.org/abs/math.AC/0001002",
        "language": "en",
        "format": "pdf",
        "sample": "sample.pdf",
        "section_path": "/section-2",
        "blocks": [
            ("prose",   lambda i: "We derive the following bound:"),
            ("formula", lambda i: {"latex": "\\sum_{i=1}^{n} \\frac{1}{i^2} = \\frac{\\pi^2}{6}", "display": True}),
        ],
    },
    {
        "id": "13-internet-archive-scan-hostil",
        "vendor": "Internet Archive",
        "product": "Scanned document",
        "url": "https://archive.org/details/example-scan",
        "language": "en",
        "format": "pdf",
        "sample": None,
        "section_path": "/page-3",
        "origin": "ocr",
        "blocks": [
            ("prose",   lambda i: "[OCR result with rotation; partially garbled]"),
            ("code",    lambda i: {"lang": "python", "text": "def hello(): print('hello, world')"}),
            ("formula", lambda i: {"latex": "f(x) = ax^2 + bx + c", "display": False}),
        ],
    },
    {
        "id": "14-book-bad-numbering-hostil",
        "vendor": "Editorial Hostil (test fixture)",
        "product": "Book with inconsistent numbering",
        "url": "https://example.com/hostil-book",
        "language": "en",
        "format": "pdf",
        "sample": None,
        "section_path": "/chapter-2",
        "blocks": [
            ("heading", lambda i: {"level": 1, "text": "Chapter 2 (numbered as 1 in the original)"}),
            ("prose",   lambda i: "This chapter has inconsistent numbering across printings."),
            ("list",    lambda i: {"ordered": False, "items": ["Item 1", "Item 2", "Item 3"]}),
            ("toc",     lambda i: {"entries": [{"label": "Chapter 2", "page": 17, "anchor": "/chapter-2"}, {"label": "Appendix A", "page": 245, "anchor": "/appendix-a"}]}),
        ],
    },
]


def make_block(idx: int, block_type: str, content_factory, section_path: str, anchor, origin: str, source_hash: str):
    bid = block_id(source_hash, section_path, idx)
    return {
        "id": bid,
        "type": block_type,
        "content": content_factory(idx),
        "anchor": anchor,
        "confidence": 0.85 if origin == "ocr" else 1.0,
        "origin": origin,
    }


def make_anchor(page: int, section_path: str, char_range: list[int] | None = None, bbox: list[float] | None = None):
    a = {"page": page, "section_path": section_path}
    if bbox is not None:
        a["bbox"] = bbox
    if char_range is not None:
        a["char_range"] = char_range
    return a


def build_source(src: dict, source_hash: str) -> dict:
    section_path = src["section_path"]
    origin = src.get("origin", "native")
    sdm = {
        "schema_version": "1.0.0",
        "source": {
            "id": src["id"],
            "hash": source_hash,
            "algorithm": "sha256",
            "vendor": src["vendor"],
            "product": src["product"],
            "url": src["url"],
            "language": src["language"],
            "format": src["format"],
        },
        "sections": [
            {
                "section_path": section_path,
                "blocks": [
                    make_block(
                        idx=i,
                        block_type=bt,
                        content_factory=cf,
                        section_path=section_path,
                        anchor=make_anchor(page=i + 1, section_path=section_path, char_range=[i * 100, (i + 1) * 100]),
                        origin=origin,
                        source_hash=source_hash,
                    )
                    for i, (bt, cf) in enumerate(src["blocks"])
                ],
            }
        ],
    }
    # Optional fields
    if src.get("version"):
        sdm["source"]["version"] = src["version"]
    if src.get("isbn"):
        sdm["source"]["isbn"] = src["isbn"]
    sdm["source"]["authors"] = []
    sdm["source"]["date"] = "2026-09-21"
    return sdm


def hash_for_source(src: dict, corpus_dir: Path) -> str:
    sample_path = corpus_dir / src["sample"] if src.get("sample") else None
    if sample_path and sample_path.exists():
        return sha256_hex(sample_path)
    # Stable synthetic hash from the source id
    h = hashlib.sha256()
    h.update(src["id"].encode("utf-8"))
    h.update(b"-synthetic-no-sample")
    return h.hexdigest()


def generate_minimal():
    for src in SOURCES:
        corpus_dir = CORPUS / src["id"]
        source_hash = hash_for_source(src, corpus_dir)
        sdm = build_source(src, source_hash)
        out_path = OUT / f"{src['id']}.json"
        out_path.write_text(json.dumps(sdm, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"  wrote {out_path.relative_to(REPO)} ({sum(len(s['blocks']) for s in sdm['sections'])} blocks)")


def generate_canonical():
    """Canonical SDM: 01-postgresql-chapter with all 16 block types covered."""
    src = next(s for s in SOURCES if s["id"] == "01-postgresql-chapter")
    corpus_dir = CORPUS / src["id"]
    source_hash = hash_for_source(src, corpus_dir)

    section_path = "/ch02/intro"
    # All 16 types, in order
    blocks_spec = [
        ("heading",       {"level": 1, "text": "Chapter 2: The SQL Language"}, "native"),
        ("prose",         "SQL is a declarative language for querying and modifying relational data.", "native"),
        ("heading",       {"level": 2, "text": "2.1 Lexical Structure"}, "native"),
        ("list",          {"ordered": True, "items": ["identifier", "keyword", "literal", "operator"]}, "native"),
        ("code",          {"lang": "sql", "text": "SELECT * FROM pg_class;"}, "native"),
        ("console",       {"lines": ["$ psql -U postgres", "postgres=# SELECT version();", "PostgreSQL 16.1"]}, "native"),
        ("formula",       {"latex": "\\sum_{i=1}^{n} w_i x_i = b", "display": True}, "native"),
        ("figure",        {"src": "assets/architecture.png", "alt": "Architecture", "caption": "System overview"}, "native"),
        ("caption",       "Figure 2.1: System architecture overview.", "native"),
        ("note",          {"text": "This is an editorial note.", "severity": "tip"}, "native"),
        ("warning",       {"text": "Backups must be verified before relying on them."}, "native"),
        ("example",       {"text": "Example: SELECT count(*) FROM pg_class WHERE relkind='r';"}, "native"),
        ("syntax-diagram",{"notation": "ebnf", "text": "select := 'SELECT' select_list"}, "native"),
        ("footnote",      {"text": "See the SQL standard ISO/IEC 9075.", "ref": "1"}, "native"),
        ("toc",           {"entries": [{"label": "Chapter 2", "page": 47, "anchor": "/ch02"}, {"label": "Chapter 3", "page": 89, "anchor": "/ch03"}]}, "native"),
        ("boilerplate",   "Copyright © The PostgreSQL Global Development Group.", "native"),
    ]

    blocks = []
    for idx, (bt, content, origin) in enumerate(blocks_spec):
        blocks.append({
            "id": block_id(source_hash, section_path, idx),
            "type": bt,
            "content": content,
            "anchor": {"page": idx + 1, "section_path": section_path, "char_range": [idx * 50, (idx + 1) * 50]},
            "confidence": 0.85 if origin == "ocr" else 1.0,
            "origin": origin,
        })

    sdm = {
        "schema_version": "1.0.0",
        "source": {
            "id": src["id"],
            "hash": source_hash,
            "algorithm": "sha256",
            "vendor": src["vendor"],
            "product": src["product"],
            "version": src["version"],
            "authors": ["The PostgreSQL Global Development Group"],
            "url": src["url"],
            "language": src["language"],
            "date": "2026-09-21",
            "format": src["format"],
        },
        "sections": [
            {"section_path": section_path, "title": "The SQL Language", "blocks": blocks}
        ],
    }
    out_path = OUT / "01-postgresql-chapter-full.json"
    out_path.write_text(json.dumps(sdm, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  wrote {out_path.relative_to(REPO)} ({len(blocks)} blocks)")


if __name__ == "__main__":
    print("Generando SDMs mínimos...")
    generate_minimal()
    print("Generando SDM canónico...")
    generate_canonical()
    print("OK.")
