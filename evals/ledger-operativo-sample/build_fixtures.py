"""Eval battery — Fase 38: ledger operativo.

Sintetiza workdirs reproducibles (SDM + ledger + manifest) para verificar
los 3 criterios del roadmap:
1. El reporte se genera en cualquier punto del proceso.
2. Detecta huérfanos y contenido sin respaldo.
3. El estado persiste en el manifiesto.

Sin dependencias externas (Python 3.9+ stdlib puro).

Uso:
    python3 evals/ledger-operativo-sample/build_fixtures.py
    python3 evals/ledger-operativo-sample/run_eval.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
FIX = HERE / "fixtures"
EXP = HERE / "expected"
TMP = HERE / "tmp_workdir"

LEDGER_SCRIPT = REPO / "skill" / "notemartin-study-notes" / "scripts" / "util" / "ledger.py"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


# -------------------------------------------------------------------
# SDM sintético A: 10 bloques.
# -------------------------------------------------------------------

def sdm_a() -> dict:
    blocks: list[dict] = []
    section = "/ch02/configuration"
    for idx, (btype, content) in enumerate([
        ("definition", {"text": "Una vista materializada."}),
        ("parameter", {"name": "shared_buffers", "description": "Tamaño del caché."}),
        ("default", {"name": "shared_buffers", "value": "128 MB"}),
        ("warning", {"text": "WARNING: este comando borra datos.", "severity": "caution"}),
        ("error-code", {"code": "EADDRINUSE", "message": "Puerto en uso."}),
        ("example", {"text": "Ejemplo: SELECT pg_reload_conf();"}),
        ("step", {"ordinal": 1, "text": "Verificar hash."}),
        ("formula", {"latex": "t = O(n log n)", "numbered": True}),
        ("prose", {"text": "Texto introductorio sin info nueva."}),
        ("tradeoff", {"text": "Índice acelera lecturas pero ralentiza escrituras."}),
    ]):
        h = __import__("hashlib").sha1()
        h.update(f"sdm-A/{section}/{idx}".encode())
        bid = h.hexdigest()[:12]
        blocks.append({
            "id": bid,
            "type": btype,
            "content": content,
            "anchor": {"page": 1 + idx // 4, "section_path": section, "bbox": None},
            "confidence": 1.0,
            "origin": "native",
        })
    return {
        "schema_version": "1.0.0",
        "source": {"id": "fixture-A", "hash": "a" * 64, "format": "pdf"},
        "sections": [{"section_path": section, "title": "Configuration", "blocks": blocks}],
    }


def sdm_b() -> dict:
    blocks: list[dict] = []
    section = "/ch01/intro"
    for idx, (btype, content) in enumerate([
        ("definition", {"text": "Una transacción es una unidad atómica."}),
        ("parameter", {"name": "default_transaction_isolation", "description": "Nivel de aislamiento."}),
        ("default", {"name": "default_transaction_isolation", "value": "read committed"}),
        ("warning", {"text": "WARNING: transacciones largas.", "severity": "caution"}),
        ("error-code", {"code": "EIO", "message": "Error de E/S."}),
        ("formula", {"latex": "n = r * w", "numbered": True}),
    ]):
        h = __import__("hashlib").sha1()
        h.update(f"sdm-B/{section}/{idx}".encode())
        bid = h.hexdigest()[:12]
        blocks.append({
            "id": bid,
            "type": btype,
            "content": content,
            "anchor": {"page": 1 + idx // 4, "section_path": section, "bbox": None},
            "confidence": 1.0,
            "origin": "native",
        })
    return {
        "schema_version": "1.0.0",
        "source": {"id": "fixture-B", "hash": "b" * 64, "format": "pdf"},
        "sections": [{"section_path": section, "title": "Introduction", "blocks": blocks}],
    }


# -------------------------------------------------------------------
# Ledgers sintéticos.
# -------------------------------------------------------------------

def _bid(sdm: dict, idx: int) -> str:
    return sdm["sections"][0]["blocks"][idx]["id"]


def _entry(unit_id: str, block_ids: list[str], type_: str, criticality: str,
           target_note: str | None = None, state: str = "written",
           discard_reason: str | None = None) -> dict:
    e: dict = {
        "unit_id": unit_id,
        "source_block_ids": block_ids,
        "source_section_path": "/ch02/configuration",
        "type": type_,
        "criticality": criticality,
        "target_note": target_note,
        "target_section": None,
        "state": state,
    }
    if discard_reason is not None:
        e["discard_reason"] = discard_reason
    return e


def ledger_a_ok(sdm: dict) -> dict:
    """Cubre 8 de 10 bloques (definition, parameter, default, warning, error-code,
    example, step, formula) — gaps en prose y tradeoff."""
    return {
        "schema_version": "2.0.0",
        "source": {"id": "fixture-A", "hash": "a" * 64},
        "entries": [
            _entry("u_001", [_bid(sdm, 0)], "definition", "must-keep", "postgres-config"),
            _entry("u_002", [_bid(sdm, 1)], "parameter", "must-keep", "postgres-config"),
            _entry("u_003", [_bid(sdm, 2)], "default", "must-keep", "postgres-config"),
            _entry("u_004", [_bid(sdm, 3)], "warning", "must-keep", "postgres-config"),
            _entry("u_005", [_bid(sdm, 4)], "error-code", "must-keep", "postgres-config"),
            _entry("u_006", [_bid(sdm, 5)], "example", "must-keep", "postgres-config"),
            _entry("u_007", [_bid(sdm, 6)], "step", "must-keep", "postgres-config"),
            _entry("u_008", [_bid(sdm, 7)], "formula", "must-keep", "postgres-config"),
        ],
    }


def ledger_a_orphan(sdm: dict) -> dict:
    """ledger-A-ok + 1 entry con block_id inexistente."""
    base = ledger_a_ok(sdm)
    base["entries"].append(
        _entry("u_orphan", ["deadbeef0000"], "definition", "must-keep", "postgres-config")
    )
    return base


def ledger_a_gap(sdm: dict) -> dict:
    """Cubre solo 7 de 10 → 3 gaps (sin incluir prose, ejemplo y tradeoff)."""
    return {
        "schema_version": "2.0.0",
        "source": {"id": "fixture-A", "hash": "a" * 64},
        "entries": [
            _entry("u_001", [_bid(sdm, 0)], "definition", "must-keep", "postgres-config"),
            _entry("u_002", [_bid(sdm, 1)], "parameter", "must-keep", "postgres-config"),
            _entry("u_003", [_bid(sdm, 2)], "default", "must-keep", "postgres-config"),
            _entry("u_004", [_bid(sdm, 3)], "warning", "must-keep", "postgres-config"),
            _entry("u_005", [_bid(sdm, 4)], "error-code", "must-keep", "postgres-config"),
            _entry("u_007", [_bid(sdm, 6)], "step", "must-keep", "postgres-config"),
            _entry("u_008", [_bid(sdm, 7)], "formula", "must-keep", "postgres-config"),
        ],
    }


def ledger_b_empty(sdm: dict) -> dict:
    return {
        "schema_version": "2.0.0",
        "source": {"id": "fixture-B", "hash": "b" * 64},
        "entries": [],
    }


def manifest_a() -> dict:
    return {
        "schema_version": "1.0.0",
        "source": {"id": "fixture-A", "path": "/tmp/fixture-A.pdf", "hash": "a" * 64, "algorithm": "sha256"},
        "current_stage": "l2",
        "stage_progress": {"l0": "done", "l1": "done", "l2": "in_progress", "l3": "pending", "l4": "pending"},
        "units_processed": 0,
        "published_notes": [],
        "glossary": {"view": "Vista materializada"},
        "naming_decisions": [{"entity": "note-id", "decision": "kebab-case"}],
        "link_debt": [],
        "hash_mismatch": False,
        "last_modified": "2026-09-24T00:00:00+00:00",
    }


def manifest_patch_expected(ledger: dict) -> dict:
    units_processed = sum(1 for e in ledger["entries"] if e["state"] in {"written", "merged", "discarded"})
    return {
        "units_processed": units_processed,
        "last_modified": "<set by ledger.py at runtime>",
    }


def main() -> int:
    FIX.mkdir(exist_ok=True)
    EXP.mkdir(exist_ok=True)

    sdm_a_data = sdm_a()
    sdm_b_data = sdm_b()

    _write_json(FIX / "sdm-A.json", sdm_a_data)
    _write_json(FIX / "sdm-B.json", sdm_b_data)

    ledger_ok = ledger_a_ok(sdm_a_data)
    _write_json(FIX / "ledger-A-ok.json", ledger_ok)
    _write_json(FIX / "ledger-A-orphan.json", ledger_a_orphan(sdm_a_data))
    _write_json(FIX / "ledger-A-gap.json", ledger_a_gap(sdm_a_data))
    _write_json(FIX / "ledger-B-empty.json", ledger_b_empty(sdm_b_data))

    _write_json(FIX / "manifest-A.json", manifest_a())

    # Expected patch: units_processed debe ser el número de entries en estado terminal.
    _write_json(EXP / "manifest-patch.json", manifest_patch_expected(ledger_ok))

    # Expected orphan list (block_ids deadbeef0000).
    _write_json(EXP / "orphans.json", [{"unit_id": "u_orphan", "block_id": "deadbeef0000"}])

    # Expected gap list: bloques de sdm-A no cubiertos por ledger-A-gap
    # (índices 5=example, 8=prose, 9=tradeoff; prose se excluye por default).
    gap_block_ids = sorted([_bid(sdm_a_data, 5), _bid(sdm_a_data, 9)])
    _write_json(EXP / "gaps.json", gap_block_ids)

    # Gap con --include-prose incluye también el bloque prose (idx 8).
    gap_with_prose = sorted(gap_block_ids + [_bid(sdm_a_data, 8)])
    _write_json(EXP / "gaps-include-prose.json", gap_with_prose)

    print(f"sdm-A: {len(sdm_a_data['sections'][0]['blocks'])} bloques")
    print(f"sdm-B: {len(sdm_b_data['sections'][0]['blocks'])} bloques")
    print(f"ledger-A-ok: {len(ledger_ok['entries'])} entradas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
