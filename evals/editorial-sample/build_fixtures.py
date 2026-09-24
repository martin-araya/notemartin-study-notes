#!/usr/bin/env python3
"""build_fixtures.py — F35 eval fixtures.

Genera fixtures que separan los 2 artefactos del eval:
  - `sdm.json`: el SDM canónico con los bloques ya clasificados por F35
    (es lo que validaría validate_sdm.py).
  - `region.json`: la región cruda `editorial_note.box` que el eval aplica al
    helper `_classify_editorial_box` directamente para verificar la mecánica
    sin desplegar F31/F22.

4 fixtures ejercitando los 3 criterios:
  - postgresql-warning:    vendor matched + WARNING: prefix -> type=warning, severity=caution
  - python-warning:        vendor matched + [WARN] prefix   -> type=warning, severity=caution
  - kubernetes-admonition: vendor matched + admonition-warning -> type=warning
  - unknown-vendor:        vendor no catalogado + "Important:" -> type=note/info,
                            decision.unknown_convention=true

Uso:
    python3 evals/editorial-sample/build_fixtures.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "evals" / "editorial-sample" / "fixtures"


def write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _stable_block_id(source_hash: str, section_path: str, index: int) -> str:
    h = hashlib.sha1()
    h.update(source_hash.encode())
    h.update(section_path.encode())
    h.update(str(index).encode())
    return h.hexdigest()[:12]


def _vendor_sdm(sid: str, vendor: str, product: str, version: str | None,
                blocks: list) -> dict:
    source_hash = hashlib.sha256(f"{sid}-{vendor}".encode()).hexdigest()
    return {
        "schema_version": "1.0.0",
        "source": {
            "id": sid,
            "hash": source_hash,
            "algorithm": "sha256",
            "vendor": vendor,
            "product": product,
            "version": version,
            "url": "https://example.com/eval",
            "language": "en",
            "format": "html",
        },
        "source_provenance": {
            "id":         {"method": "read", "value": sid,                          "confidence": 1.0},
            "hash":       {"method": "read", "value": source_hash,                  "confidence": 1.0},
            "vendor":     {"method": "read", "value": vendor,                        "confidence": 1.0},
            "product":    {"method": "read", "value": product,                       "confidence": 1.0},
            "version":    {"method": "read", "value": version,                       "confidence": 1.0} if version else {"method": "absent", "value": None, "confidence": 0.0},
            "url":        {"method": "read", "value": "https://example.com/eval",    "confidence": 1.0},
            "language":   {"method": "default", "value": "en",                        "confidence": 0.0},
            "date":       {"method": "default", "value": "2026-09-24",                "confidence": 0.0},
            "format":     {"method": "read", "value": "html",                         "confidence": 1.0},
            "edition":    {"method": "default", "value": None,                        "confidence": 0.0},
            "isbn":       {"method": "default", "value": None,                        "confidence": 0.0},
            "authors":    {"method": "default", "value": [],                          "confidence": 0.0},
            "algorithm":  {"method": "read", "value": "sha256",                       "confidence": 1.0},
        },
        "sections": [
            {
                "section_path": "/ch01/intro",
                "title": "Intro",
                "blocks": blocks,
            }
        ],
    }


def _make_block(source_hash: str, section_path: str, index: int,
                block_type: str, content: dict, raw_region: dict) -> dict:
    bid = _stable_block_id(source_hash, section_path, index)
    return {
        "id": bid,
        "type": block_type,
        "content": content,
        "anchor": {
            "page": 1,
            "section_path": section_path,
            "bbox": raw_region.get("bbox", [10.0, 100.0, 200.0, 60.0]),
        },
        "confidence": 1.0,
        "origin": "native",
    }


def build_postgresql_warning():
    sid = "eval-pg-warning"
    vendor = "PostgreSQL Global Development Group"
    product = "PostgreSQL 16"
    version = "16"
    raw_region = {
        "id": "r-pg-warn",
        "semantic_class": "editorial_note",
        "sub_kind": "box",
        "text": "WARNING: this query may lock the table for hours.",
        "bbox": [10.0, 100.0, 200.0, 60.0],
        "class_confidence": 0.92,
        "ambiguity": False,
        "origin": "native",
        "vendor": vendor,
        "product": product,
    }
    sdm = _vendor_sdm(sid, vendor, product, version, blocks=[])
    sh = sdm["source"]["hash"]
    block = _make_block(sh, "/ch01/intro", 0,
                         block_type="warning",
                         content={"text": raw_region["text"], "severity": "caution"},
                         raw_region=raw_region)
    sdm["sections"][0]["blocks"] = [block]
    write(FIX / "postgresql-warning" / "sdm.json", sdm)
    write(FIX / "postgresql-warning" / "region.json", {"raw_region": raw_region})


def build_python_warning():
    sid = "eval-py-warning"
    vendor = "Python Software Foundation"
    product = "Python docs"
    version = "3.12"
    raw_region = {
        "id": "r-py-warn",
        "semantic_class": "editorial_note",
        "sub_kind": "box",
        "text": "[WARN] This is deprecated since 3.10.",
        "bbox": [10.0, 100.0, 200.0, 60.0],
        "class_confidence": 0.92,
        "ambiguity": False,
        "origin": "native",
        "vendor": "Python Software Foundation (docs.python.org)",
        "product": "Python docs",
    }
    sdm = _vendor_sdm(sid, vendor, product, version, blocks=[])
    sh = sdm["source"]["hash"]
    block = _make_block(sh, "/ch01/intro", 0,
                         block_type="warning",
                         content={"text": raw_region["text"], "severity": "caution"},
                         raw_region=raw_region)
    sdm["sections"][0]["blocks"] = [block]
    write(FIX / "python-warning" / "sdm.json", sdm)
    write(FIX / "python-warning" / "region.json", {"raw_region": raw_region})


def build_kubernetes_admonition():
    sid = "eval-k8s-admonition"
    vendor = "Kubernetes"
    product = "Kubernetes docs"
    version = "1.30"
    raw_region = {
        "id": "r-k8s-warn",
        "semantic_class": "editorial_note",
        "sub_kind": "box",
        "text": "admonition-warning: this configuration is unsafe.",
        "bbox": [10.0, 100.0, 200.0, 60.0],
        "class_confidence": 0.92,
        "ambiguity": False,
        "origin": "native",
        "vendor": vendor,
        "product": product,
    }
    sdm = _vendor_sdm(sid, vendor, product, version, blocks=[])
    sh = sdm["source"]["hash"]
    block = _make_block(sh, "/ch01/intro", 0,
                         block_type="warning",
                         content={"text": raw_region["text"], "severity": "caution"},
                         raw_region=raw_region)
    sdm["sections"][0]["blocks"] = [block]
    write(FIX / "kubernetes-admonition" / "sdm.json", sdm)
    write(FIX / "kubernetes-admonition" / "region.json", {"raw_region": raw_region})


def build_unknown_vendor():
    sid = "eval-unknown-vendor"
    vendor = "AcmeCustomVendor"
    product = "Internal Wiki"
    version = None
    raw_region = {
        "id": "r-unknown",
        "semantic_class": "editorial_note",
        "sub_kind": "box",
        "text": "Important: review the migration guide before continuing.",
        "bbox": [10.0, 100.0, 200.0, 60.0],
        "class_confidence": 0.92,
        "ambiguity": False,
        "origin": "native",
        "vendor": vendor,
        "product": product,
    }
    sdm = _vendor_sdm(sid, vendor, product, version, blocks=[])
    sh = sdm["source"]["hash"]
    # Per F35 spec: unknown vendor + no text-regex match → type=note, severity=info.
    block = _make_block(sh, "/ch01/intro", 0,
                         block_type="note",
                         content={"text": raw_region["text"], "severity": "info"},
                         raw_region=raw_region)
    sdm["sections"][0]["blocks"] = [block]
    write(FIX / "unknown-vendor" / "sdm.json", sdm)
    write(FIX / "unknown-vendor" / "region.json", {"raw_region": raw_region})


def build_expected():
    E = FIX.parent / "expected"
    E.mkdir(parents=True, exist_ok=True)
    (E / "postgresql-expected.json").write_text(json.dumps({
        "criterion_1_vendor_recognized": True,
        "block_type": "warning",
        "block_severity": "caution",
    }, indent=2) + "\n", encoding="utf-8")
    (E / "python-expected.json").write_text(json.dumps({
        "criterion_1_vendor_recognized": True,
        "block_type": "warning",
        "block_severity": "caution",
    }, indent=2) + "\n", encoding="utf-8")
    (E / "kubernetes-expected.json").write_text(json.dumps({
        "criterion_1_vendor_recognized": True,
        "block_type": "warning",
        "block_severity": "caution",
    }, indent=2) + "\n", encoding="utf-8")
    (E / "unknown-expected.json").write_text(json.dumps({
        "criterion_2_not_prose": True,
        "criterion_3_unknown_recorded": True,
        "block_type": "note",
        "block_severity": "info",
        "unknown_convention_min": 1,
    }, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    build_postgresql_warning()
    build_python_warning()
    build_kubernetes_admonition()
    build_unknown_vendor()
    build_expected()
    print("OK — wrote 4 fixtures (sdm.json + region.json) + expected/")


if __name__ == "__main__":
    main()
