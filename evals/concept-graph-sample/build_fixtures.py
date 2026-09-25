"""Eval battery — Fase 39: grafo de prerrequisitos.

Sintetiza workdirs reproducibles (ledger + SDM + profile) para verificar
los 3 criterios del roadmap + no-regresión F15/F37/F38:
1. El grafo no tiene ciclos sin resolver.
2. Todo concepto usado está definido o declarado como prerrequisito.
3. Se generan al menos dos rutas por dominio.

Sin dependencias externas (Python 3.9+ stdlib puro).

Uso:
    python3 evals/concept-graph-sample/build_fixtures.py
    python3 evals/concept-graph-sample/run_eval.py
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures"
EXP = HERE / "expected"


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# -------------------------------------------------------------------
# SDM sintético (PostgreSQL como vendor/product).
# -------------------------------------------------------------------

def sdm_pristine() -> dict:
    return {
        "schema_version": "1.0.0",
        "source": {
            "id": "fixture-pg",
            "hash": "a" * 64,
            "format": "pdf",
            "vendor": "PostgreSQL Global Development Group",
            "product": "PostgreSQL",
            "language": "en",
        },
        "sections": [
            {"section_path": "/ch01/intro", "title": "Introduction", "blocks": []},
            {"section_path": "/ch02/transactions", "title": "Transactions", "blocks": []},
        ],
    }


# -------------------------------------------------------------------
# Ledger sintético: 6 definitions + 5 cross-references prerequisite (DAG).
# -------------------------------------------------------------------

def ledger_pristine() -> dict:
    return {
        "schema_version": "2.0.0",
        "source": {"id": "fixture-pg", "hash": "a" * 64},
        "entries": [
            {"unit_id": "u_d_01", "source_block_ids": ["a" * 12], "source_section_path": "/ch01/intro",
             "type": "definition", "criticality": "must-keep", "target_note": "pg",
             "state": "written",
             "content": {"term": "transaccion", "text": "Una transacción es una unidad atómica de trabajo."}},
            {"unit_id": "u_d_02", "source_block_ids": ["b" * 12], "source_section_path": "/ch01/intro",
             "type": "definition", "criticality": "must-keep", "target_note": "pg",
             "state": "written",
             "content": {"term": "mvcc", "text": "MVCC es control de concurrencia multiversión."}},
            {"unit_id": "u_d_03", "source_block_ids": ["c" * 12], "source_section_path": "/ch01/intro",
             "type": "definition", "criticality": "must-keep", "target_note": "pg",
             "state": "written",
             "content": {"term": "wal", "text": "WAL es el registro de escritura anticipada."}},
            {"unit_id": "u_d_04", "source_block_ids": ["d" * 12], "source_section_path": "/ch01/intro",
             "type": "definition", "criticality": "must-keep", "target_note": "pg",
             "state": "written",
             "content": {"term": "vista-materializada", "text": "Una vista materializada almacena el resultado de una consulta."}},
            {"unit_id": "u_d_05", "source_block_ids": ["e" * 12], "source_section_path": "/ch02/transactions",
             "type": "definition", "criticality": "must-keep", "target_note": "pg",
             "state": "written",
             "content": {"term": "acid", "text": "ACID son las propiedades de una transacción."}},
            {"unit_id": "u_d_06", "source_block_ids": ["f" * 12], "source_section_path": "/ch02/transactions",
             "type": "definition", "criticality": "must-keep", "target_note": "pg",
             "state": "written",
             "content": {"term": "aislamiento", "text": "El aislamiento es el grado de interferencia entre transacciones."}},
            # Cross-references: acid necesita mvcc; mvcc necesita wal; view necesita transacción; etc.
            # ADR-0003: from_concept se declara explícitamente.
            {"unit_id": "u_x_01", "source_block_ids": ["1" * 12], "source_section_path": "/ch02/transactions",
             "type": "cross-reference", "criticality": "context", "target_note": None,
             "state": "written",
             "content": {"relation": "prerequisite", "from_concept": "acid", "target_concept": "mvcc", "target": "/ch01/intro"}},
            {"unit_id": "u_x_02", "source_block_ids": ["2" * 12], "source_section_path": "/ch02/transactions",
             "type": "cross-reference", "criticality": "context", "target_note": None,
             "state": "written",
             "content": {"relation": "prerequisite", "from_concept": "acid", "target_concept": "wal", "target": "/ch01/intro"}},
            {"unit_id": "u_x_03", "source_block_ids": ["3" * 12], "source_section_path": "/ch01/intro",
             "type": "cross-reference", "criticality": "context", "target_note": None,
             "state": "written",
             "content": {"relation": "prerequisite", "from_concept": "vista-materializada", "target_concept": "wal", "target": "/ch01/intro"}},
            {"unit_id": "u_x_04", "source_block_ids": ["4" * 12], "source_section_path": "/ch01/intro",
             "type": "cross-reference", "criticality": "context", "target_note": None,
             "state": "written",
             "content": {"relation": "prerequisite", "from_concept": "vista-materializada", "target_concept": "transaccion", "target": "/ch01/intro"}},
            {"unit_id": "u_x_05", "source_block_ids": ["5" * 12], "source_section_path": "/ch02/transactions",
             "type": "cross-reference", "criticality": "context", "target_note": None,
             "state": "written",
             "content": {"relation": "prerequisite", "from_concept": "aislamiento", "target_concept": "transaccion", "target": "/ch01/intro"}},
            # Un cross-reference "lateral" (no prereq) — debe ignorarse.
            {"unit_id": "u_x_lateral", "source_block_ids": ["6" * 12], "source_section_path": "/ch01/intro",
             "type": "cross-reference", "criticality": "context", "target_note": None,
             "state": "written",
             "content": {"target": "/bibliography", "label": "Ver refs."}},
        ],
    }


def ledger_cycle() -> dict:
    """Mismo ledger pristine + aristas que cierran ciclo: mvcc → wal → mvcc."""
    base = json.loads(json.dumps(ledger_pristine()))  # deep copy
    base["entries"].append({
        "unit_id": "u_x_cycle_a", "source_block_ids": ["7" * 12],
        "source_section_path": "/ch01/intro",
        "type": "cross-reference", "criticality": "context", "target_note": None,
        "state": "written",
        "content": {"relation": "prerequisite", "from_concept": "mvcc", "target_concept": "wal"},
    })
    base["entries"].append({
        "unit_id": "u_x_cycle_b", "source_block_ids": ["8" * 12],
        "source_section_path": "/ch01/intro",
        "type": "cross-reference", "criticality": "context", "target_note": None,
        "state": "written",
        "content": {"relation": "prerequisite", "from_concept": "wal", "target_concept": "mvcc"},
    })
    return base


def ledger_orphan() -> dict:
    """Mismo ledger pristine + 1 cross-reference a un concepto inexistente."""
    base = json.loads(json.dumps(ledger_pristine()))
    base["entries"].append({
        "unit_id": "u_x_orphan", "source_block_ids": ["9" * 12],
        "source_section_path": "/ch01/intro",
        "type": "cross-reference", "criticality": "context", "target_note": None,
        "state": "written",
        "content": {"relation": "prerequisite", "from_concept": "transaccion",
                    "target_concept": "concepto_inexistente",
                    "target": "/ch99"},
    })
    return base


def profile_block() -> str:
    return "graph:\n  cycle_policy: block\n"


def profile_allow() -> str:
    return "graph:\n  cycle_policy: allow\n"


def main() -> int:
    FIX.mkdir(exist_ok=True)
    EXP.mkdir(exist_ok=True)

    sdm_p = sdm_pristine()
    led_p = ledger_pristine()
    led_c = ledger_cycle()
    led_o = ledger_orphan()

    _write_json(FIX / "sdm-pristine.json", sdm_p)
    _write_json(FIX / "sdm-cycle.json", sdm_p)
    _write_json(FIX / "sdm-orphan.json", sdm_p)
    _write_json(FIX / "ledger-pristine.json", led_p)
    _write_json(FIX / "ledger-cycle.json", led_c)
    _write_json(FIX / "ledger-orphan.json", led_o)
    _write_text(FIX / "profile-block.yaml", profile_block())
    _write_text(FIX / "profile-allow.yaml", profile_allow())

    # Expected: 6 definitions → 6 concepts:
    #   transaccion, mvcc, wal, vista-materializada, acid, aislamiento
    # Edges pristine (5 con relation=prerequisite):
    #   acid → mvcc (u_x_01)
    #   acid → wal (u_x_02)
    #   vista-materializada → wal (u_x_03)
    #   vista-materializada → transaccion (u_x_04)
    #   aislamiento → transaccion (u_x_05)
    # (u_x_lateral se ignora por no tener relation=prerequisite)
    expected_nodes = {
        "transaccion", "mvcc", "wal", "vista-materializada", "acid", "aislamiento"
    }
    expected_edges = {
        ("acid", "mvcc"), ("acid", "wal"),
        ("vista-materializada", "wal"), ("vista-materializada", "transaccion"),
        ("aislamiento", "transaccion"),
    }
    _write_json(EXP / "pristine-nodes.json", sorted(expected_nodes))
    _write_json(EXP / "pristine-edges.json", [list(e) for e in sorted(expected_edges)])

    print(f"ledger-pristine: {len(led_p['entries'])} entries, "
          f"{sum(1 for e in led_p['entries'] if e['type']=='definition')} definitions, "
          f"{sum(1 for e in led_p['entries'] if e['type']=='cross-reference' and (e.get('content') or {}).get('relation')=='prerequisite')} prerequisite edges")
    print(f"ledger-cycle: +2 cycle edges")
    print(f"ledger-orphan: +1 dangling edge")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
