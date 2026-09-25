#!/usr/bin/env python3
"""Genera los 5 ledgers sintéticos para Fase 15 (regenerado en Fase 38).

Salida:
    evals/ledger-sample/full-coverage.json
    evals/ledger-sample/mixed-states.json
    evals/ledger-sample/section-query.json
    evals/ledger-sample/negative-pending.json
    evals/ledger-sample/negative-discard-reason.json

Cambios respecto a la versión pre-F38:
- schema_version: "1.0.0" → "2.0.0" (enum cerrado de 14 tipos).
- Tipos re-mapeados al enum cerrado:
    "note"      → "definition"
    "tip"       → "version-note"
    "navigation"→ "cross-reference"
- Los `content` ahora se rellenan con el shape de F37 §3 (no exigidos por el
  schema 2.0.0 pero útiles para los renderers).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "evals" / "ledger-sample"
OUT.mkdir(parents=True, exist_ok=True)

PG_HASH = "a8f4ce1405802cacbb35e6fb88f5e3cf138a4e872910cdfd276f378f13371657"


def block_id(label: str) -> str:
    return hashlib.sha1(label.encode("utf-8")).hexdigest()[:12]


def write(name: str, ledger: dict) -> None:
    path = OUT / name
    path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  wrote {path.relative_to(REPO)}")


def mk(unit_id: str, blocks: list[str], section: str, type_: str,
       criticality: str, target_note: str | None, target_section: str | None,
       state: str, discard_reason: str | None = None,
       content: dict | None = None) -> dict:
    e: dict = {
        "unit_id": unit_id,
        "source_block_ids": blocks,
        "source_section_path": section,
        "type": type_,
        "criticality": criticality,
        "target_note": target_note,
        "target_section": target_section,
        "state": state,
    }
    if content is not None:
        e["content"] = content
    if discard_reason is not None:
        e["discard_reason"] = discard_reason
    return e


def full_coverage() -> dict:
    return {
        "schema_version": "2.0.0",
        "source": {"id": "01-postgresql-chapter", "hash": PG_HASH},
        "entries": [
            mk("u_001", [block_id("pg/intro-p1")], "/ch02/intro", "definition", "must-keep",
               "postgres-shared-buffers", "Configuration", "written",
               content={"text": "Una vista materializada es una relación almacenada."}),
            mk("u_002", [block_id("pg/intro-p2")], "/ch02/intro", "parameter", "must-keep",
               "postgres-shared-buffers", "Configuration", "written",
               content={"name": "shared_buffers", "description": "Tamaño del caché compartido."}),
            mk("u_003", [block_id("pg/section-2-3-2")], "/ch02/section-2.3.2", "warning", "must-keep",
               "postgres-shared-buffers", "Warnings", "merged",
               content={"text": "WARNING: este comando borra datos.", "severity": "caution"}),
            mk("u_004", [block_id("pg/wal-p1")], "/ch03/wal", "step", "must-keep",
               "postgres-wal", "Procedure", "written",
               content={"ordinal": 1, "text": "Activar WAL."}),
            mk("u_005", [block_id("pg/wal-p2")], "/ch03/wal", "warning", "must-keep",
               "postgres-wal", "Warnings", "discarded", "out-of-scope-by-user"),
            mk("u_006", [block_id("pg/note-1")], "/ch02/intro", "definition", "context",
               None, None, "written",
               content={"text": "Nota auxiliar de contexto."}),
            mk("u_007", [block_id("pg/tip-1")], "/ch02/intro", "version-note", "context",
               None, None, "discarded", "boilerplate"),
        ],
    }


def mixed_states() -> dict:
    """6 must-keep: 2 written, 2 merged, 2 discarded (1 cada motivo)."""
    return {
        "schema_version": "2.0.0",
        "source": {"id": "06-kubernetes-api-ref", "hash": "b" * 64},
        "entries": [
            mk("u_010", [block_id("k/pod-1")], "/workload/pod-v1", "definition", "must-keep",
               "kubernetes-pod-v1", "Overview", "written",
               content={"text": "Un Pod es la unidad mínima de despliegue."}),
            mk("u_011", [block_id("k/pod-2")], "/workload/pod-v1", "parameter", "must-keep",
               "kubernetes-pod-v1", "Spec", "written",
               content={"name": "restartPolicy", "description": "Política de reinicio."}),
            mk("u_012", [block_id("k/pod-3")], "/workload/pod-v1", "example", "must-keep",
               "kubernetes-pod-v1", "Examples", "merged",
               content={"text": "Ejemplo de Pod con initContainer."}),
            mk("u_013", [block_id("k/intro-1")], "/intro", "step", "must-keep",
               "kubernetes-pod-v1", "Setup", "merged",
               content={"ordinal": 1, "text": "kubectl apply -f pod.yaml."}),
            mk("u_014", [block_id("k/toc-1")], "/toc", "cross-reference", "must-keep",
               "kubernetes-pod-v1", None, "discarded", "navigation",
               content={"target": "/workload/pod-v1", "label": "Ver Pod v1."}),
            mk("u_015", [block_id("k/dup-1")], "/workload/pod-v1", "definition", "must-keep",
               "kubernetes-pod-v1", None, "discarded", "redundant-with:u_010",
               content={"text": "Duplicado de u_010."}),
        ],
    }


def section_query() -> dict:
    """5 must-keep con source_section_path declarado, incluyendo /ch02/section-2.3.2."""
    return {
        "schema_version": "2.0.0",
        "source": {"id": "03-rfc-7231", "hash": "c" * 64},
        "entries": [
            mk("u_020", [block_id("rfc/intro-1")], "/ch01/intro", "definition", "must-keep",
               "rfc7231-overview", "Intro", "written",
               content={"text": "RFC 7231 define la semántica de HTTP/1.1."}),
            mk("u_021", [block_id("rfc/ch02-1")], "/ch02/request-methods", "parameter", "must-keep",
               "rfc7231-overview", "Methods", "written",
               content={"name": "method", "description": "Verbo HTTP."}),
            mk("u_022", [block_id("rfc/2-3-2-1")], "/ch02/section-2.3.2", "step", "must-keep",
               "rfc7231-overview", "Semantics", "written",
               content={"ordinal": 1, "text": "GET recupera una representación."}),
            mk("u_023", [block_id("rfc/2-3-2-2")], "/ch02/section-2.3.2", "warning", "must-keep",
               "rfc7231-overview", "Semantics", "merged",
               content={"text": "GET no debe tener efectos colaterales."}),
            mk("u_024", [block_id("rfc/app-1")], "/appendix", "definition", "must-keep",
               "rfc7231-overview", "Appendix", "written",
               content={"text": "Cambios respecto a RFC 2616."}),
        ],
    }


def negative_pending() -> dict:
    """1 must-keep con state=pending → viola criterio 1."""
    return {
        "schema_version": "2.0.0",
        "source": {"id": "13-internet-archive-scan-hostil", "hash": "d" * 64},
        "entries": [
            mk("u_030", [block_id("ocr/p1")], "/page-3", "definition", "must-keep",
               None, None, "pending",
               content={"text": "Fragmento OCR pendiente."}),
        ],
    }


def negative_discard_reason() -> dict:
    """1 discarded con discard_reason fuera de la lista cerrada → viola criterio 2."""
    return {
        "schema_version": "2.0.0",
        "source": {"id": "14-book-bad-numbering-hostil", "hash": "e" * 64},
        "entries": [
            mk("u_040", [block_id("book/p1")], "/ch01", "definition", "context",
               None, None, "discarded", "outdated",
               content={"text": "Pasaje descartado por obsoleto (motivo fuera de lista)."}),
        ],
    }


if __name__ == "__main__":
    print("Generando ledgers (schema 2.0.0, enum cerrado de 14 tipos)...")
    write("full-coverage.json", full_coverage())
    write("mixed-states.json", mixed_states())
    write("section-query.json", section_query())
    write("negative-pending.json", negative_pending())
    write("negative-discard-reason.json", negative_discard_reason())
    print("OK.")
