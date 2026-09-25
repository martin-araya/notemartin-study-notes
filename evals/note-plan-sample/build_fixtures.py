"""Eval battery — Fase 44: Note Plan.

Sintetiza planes reproducibles (note-plan.json + ledger de respaldo) para
verificar los 3 criterios del roadmap:

1. Toda unidad `must-keep` está asignada a una nota del plan.
2. La división nunca parte un procedimiento, una tabla de parámetros ni
   un ejemplo desarrollado.
3. El plan se muestra antes de redactar cuando supera el umbral.

Sin dependencias externas (Python 3.9+ stdlib puro).

Uso:
    python3 evals/note-plan-sample/build_fixtures.py
    python3 evals/note-plan-sample/run_eval.py
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures"
EXP = HERE / "expected"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _make_plan(notes: list[dict], source: dict | None = None,
               ledger_total_must_keep: int = 0,
               ledger_total_units: int = 0,
               ledger_total_blocks: int = 0) -> dict:
    notes_planned = len(notes)
    assigned = sum(1 for _n in notes for _u in _n["unit_ids"]) if False else 0  # placeholder
    # assigned_must_keep computed externally
    plan = {
        "schema_version": "1.0.0",
        "source": source or {"id": "fixture-pg", "hash": "a" * 64,
                             "vendor": "PGDG", "product": "PostgreSQL"},
        "notes": notes,
        "metadata": {
            "total_must_keep": ledger_total_must_keep,
            "assigned_must_keep": 0,  # filled below
            "unassigned_unit_ids": [],
            "total_units": ledger_total_units,
            "total_blocks": ledger_total_blocks,
            "notes_planned": notes_planned,
            "threshold_exceeded": False,
            "user_approval_required": False,
        },
    }
    return plan


def _bid(section: str, idx: int) -> str:
    """sha1 hex 12 determinista para block_id."""
    import hashlib
    h = hashlib.sha1()
    h.update(f"plan-{section}-{idx}".encode())
    return h.hexdigest()[:12]


def _note(note_id: str, type_: str, unit_ids: list[str], block_ids: list[str],
          section_path: str = "/ch02", estimated_size: str = "small",
          destination: list[str] | None = None,
          depends_on: list[str] | None = None,
          rationale: str = "test rationale") -> dict:
    return {
        "note_id": note_id,
        "type": type_,
        "title": note_id.replace("-", " ").title(),
        "unit_ids": unit_ids,
        "block_ids": block_ids,
        "depends_on": depends_on or [],
        "destination": destination or ["obsidian"],
        "estimated_size": estimated_size,
        "rationale": rationale,
        "collision_with": None,
        "collision_decision": None,
    }


def plan_good() -> dict:
    """5 notas; todas las unidades must-keep asignadas; sin violaciones."""
    notes = [
        _note("postgres-config", "configuration",
              ["u_001", "u_002"], [_bid("a", 1), _bid("a", 2)]),
        _note("postgres-warnings", "error-troubleshooting",
              ["u_003"], [_bid("a", 3)]),
        _note("postgres-formulas", "syntax",
              ["u_004"], [_bid("a", 4)]),
        _note("postgres-intro", "concept",
              ["u_005"], [_bid("b", 1)]),
        _note("postgres-glossary", "glossary-term",
              ["u_006"], [_bid("b", 2)]),
    ]
    plan = _make_plan(notes, ledger_total_must_keep=6, ledger_total_units=6,
                      ledger_total_blocks=6)
    plan["metadata"]["assigned_must_keep"] = 6
    plan["metadata"]["user_approval_required"] = False  # 5 notes, 6 must-keep
    plan["metadata"]["threshold_exceeded"] = False
    return plan


def plan_unassigned() -> dict:
    """1 nota con 5 unidades; 1 must-keep sin asignar."""
    notes = [
        _note("postgres-config", "configuration",
              ["u_001", "u_002", "u_003", "u_004", "u_005"], [_bid("a", 1)]),
    ]
    plan = _make_plan(notes, ledger_total_must_keep=6, ledger_total_units=6,
                      ledger_total_blocks=6)
    plan["metadata"]["assigned_must_keep"] = 5
    plan["metadata"]["unassigned_unit_ids"] = ["u_006"]
    plan["metadata"]["notes_planned"] = 1
    plan["metadata"]["user_approval_required"] = False
    plan["metadata"]["threshold_exceeded"] = False
    return plan


def plan_split_procedure() -> dict:
    """Procedimiento partido entre 2 notas (R3 violada)."""
    notes = [
        _note("postgres-step1", "procedure",
              ["u_001"], [_bid("a", 1)]),
        _note("postgres-step2", "procedure",
              ["u_002"], [_bid("a", 2)]),
        _note("postgres-other", "concept",
              ["u_003"], [_bid("b", 1)]),
    ]
    plan = _make_plan(notes, ledger_total_must_keep=3, ledger_total_units=3,
                      ledger_total_blocks=3)
    plan["metadata"]["assigned_must_keep"] = 3
    plan["metadata"]["notes_planned"] = 3
    return plan


def plan_split_table() -> dict:
    """Tabla de parámetros partida entre 2 notas (R3 violada)."""
    notes = [
        _note("postgres-table1", "configuration",
              ["u_001"], [_bid("a", 1)], rationale="param1"),
        _note("postgres-table2", "configuration",
              ["u_002"], [_bid("a", 2)], rationale="param2"),
        _note("postgres-table3", "configuration",
              ["u_003"], [_bid("a", 3)], rationale="param3"),
    ]
    plan = _make_plan(notes, ledger_total_must_keep=3, ledger_total_units=3,
                      ledger_total_blocks=3)
    plan["metadata"]["assigned_must_keep"] = 3
    return plan


def plan_split_example() -> dict:
    """Ejemplo desarrollado partido entre 2 notas (R3 violada).

    La heurística detecta: una nota con un unit de tipo `example_*` y sin
    unit de tipo `concept_*` o `definition_*` en la misma nota — el ejemplo
    está "flotando".
    """
    notes = [
        _note("postgres-concept1", "concept",
              ["u_definition_001"], [_bid("a", 1)], rationale="definición"),
        _note("postgres-other", "procedure",
              ["u_example_002"], [_bid("a", 2)], rationale="ejemplo (debería ir con u_definition_001)"),
    ]
    plan = _make_plan(notes, ledger_total_must_keep=2, ledger_total_units=2,
                      ledger_total_blocks=2)
    plan["metadata"]["assigned_must_keep"] = 2
    return plan


def plan_large() -> dict:
    """6 notas, 31 must-keep → user_approval_required=true."""
    notes = []
    for i in range(6):
        units = [f"u_{i:03d}_{j:02d}" for j in range(5)] + [f"u_mk_{i:02d}"]
        notes.append(_note(f"postgres-note-{i}", "configuration",
                           units, [_bid("a", i)]))
    plan = _make_plan(notes, ledger_total_must_keep=36, ledger_total_units=36,
                      ledger_total_blocks=6)
    plan["metadata"]["assigned_must_keep"] = 36
    plan["metadata"]["notes_planned"] = 6
    plan["metadata"]["threshold_exceeded"] = True  # 6 > 5
    plan["metadata"]["user_approval_required"] = True
    return plan


def plan_small() -> dict:
    """3 notas, 10 must-keep → user_approval_required=false."""
    notes = [
        _note("postgres-config", "configuration",
              ["u_001", "u_002", "u_003", "u_004"], [_bid("a", 1)]),
        _note("postgres-concept", "concept",
              ["u_005", "u_006", "u_007"], [_bid("b", 1)]),
        _note("postgres-procedure", "procedure",
              ["u_008", "u_009", "u_010"], [_bid("c", 1)]),
    ]
    plan = _make_plan(notes, ledger_total_must_keep=10, ledger_total_units=10,
                      ledger_total_blocks=3)
    plan["metadata"]["assigned_must_keep"] = 10
    plan["metadata"]["notes_planned"] = 3
    plan["metadata"]["threshold_exceeded"] = False
    plan["metadata"]["user_approval_required"] = False
    return plan


def plan_reuse() -> dict:
    """Colisión resuelta con reuse."""
    notes = [
        _note("postgres-config", "configuration",
              ["u_001", "u_002"], [_bid("a", 1)]),
    ]
    notes[0]["collision_with"] = "postgres-config-existing"
    notes[0]["collision_decision"] = "reuse"
    plan = _make_plan(notes, ledger_total_must_keep=2, ledger_total_units=2,
                      ledger_total_blocks=2)
    plan["metadata"]["assigned_must_keep"] = 2
    return plan


def plan_new() -> dict:
    """Colisión resuelta con new."""
    notes = [
        _note("postgres-config-v2", "configuration",
              ["u_001", "u_002"], [_bid("a", 1)]),
    ]
    notes[0]["collision_with"] = "postgres-config-existing"
    notes[0]["collision_decision"] = "new"
    notes[0]["rationale"] = "scope distinto: parámetros de cluster vs instancia"
    plan = _make_plan(notes, ledger_total_must_keep=2, ledger_total_units=2,
                      ledger_total_blocks=2)
    plan["metadata"]["assigned_must_keep"] = 2
    return plan


def plan_wrong_type() -> dict:
    """Tipo fuera del enum cerrado (15 tipos válidos)."""
    notes = [
        _note("postgres-config", "wrong-type-not-in-enum",
              ["u_001"], [_bid("a", 1)]),
    ]
    plan = _make_plan(notes, ledger_total_must_keep=1, ledger_total_units=1,
                      ledger_total_blocks=1)
    plan["metadata"]["assigned_must_keep"] = 1
    return plan


def main() -> int:
    FIX.mkdir(exist_ok=True)
    EXP.mkdir(exist_ok=True)

    _write_json(FIX / "plan-good.json", plan_good())
    _write_json(FIX / "plan-unassigned.json", plan_unassigned())
    _write_json(FIX / "plan-split-procedure.json", plan_split_procedure())
    _write_json(FIX / "plan-split-table.json", plan_split_table())
    _write_json(FIX / "plan-split-example.json", plan_split_example())
    _write_json(FIX / "plan-large.json", plan_large())
    _write_json(FIX / "plan-small.json", plan_small())
    _write_json(FIX / "plan-reuse.json", plan_reuse())
    _write_json(FIX / "plan-new.json", plan_new())
    _write_json(FIX / "plan-wrong-type.json", plan_wrong_type())

    print("fixtures: 10 planes")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
