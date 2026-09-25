"""Eval — Fase 44: Note Plan.

Verifica los 3 criterios del roadmap + no-regresión F15/F37/F38/F39/F40/F41/F42/F43.

Exit codes: 0 PASS los 7, 1 FAIL, 2 usage.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
FIX = HERE / "fixtures"
EXP = HERE / "expected"

SCHEMA = REPO / "skill" / "notemartin-study-notes" / "schemas" / "note-plan.schema.json"
VALIDATE_LEDGER = REPO / "scripts" / "util" / "validate_ledger.py"
F37_EVAL = REPO / "evals" / "information-units-sample" / "run_eval.py"
F38_EVAL = REPO / "evals" / "ledger-operativo-sample" / "run_eval.py"
F39_EVAL = REPO / "evals" / "concept-graph-sample" / "run_eval.py"
F40_EVAL = REPO / "evals" / "terminology-sample" / "run_eval.py"
F41_EVAL = REPO / "evals" / "conflicts-sample" / "run_eval.py"
F42_EVAL = REPO / "evals" / "fidelity-sample" / "run_eval.py"
F43_EVAL = REPO / "evals" / "completeness-sample" / "run_eval.py"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# -------------------------------------------------------------------
# Criterio 1: toda unidad must-keep asignada.
# -------------------------------------------------------------------

def check_coverage(plan: dict) -> tuple[bool, str]:
    """`assigned_must_keep == total_must_keep` y `unassigned_unit_ids` vacío."""
    md = plan.get("metadata", {})
    total = md.get("total_must_keep", 0)
    assigned = md.get("assigned_must_keep", 0)
    unassigned = md.get("unassigned_unit_ids", [])
    expected_assigned = sum(len(n["unit_ids"]) for n in plan["notes"])
    # assigned_must_keep debe reflejar el conteo real de unidades asignadas.
    count_ok = assigned == expected_assigned
    coverage_ok = (total == assigned) and not unassigned
    ok = count_ok and coverage_ok
    return ok, (f"  total={total}, assigned={assigned} (esperado {expected_assigned}), "
                f"unassigned={unassigned}, "
                f"{'PASS' if ok else 'FAIL'}")


# -------------------------------------------------------------------
# Criterio 2: división nunca parte procedimiento / tabla / ejemplo.
# -------------------------------------------------------------------

def check_atomic_units(plan: dict) -> tuple[bool, str]:
    """Detecta procedimientos / tablas / ejemplos partidos entre notas.

    Heurísticas:
    - Procedure split: ≥ 2 notas con type=procedure (un procedimiento no debe
      partirse entre múltiples notas).
    - Configuration table split: ≥ 2 notas con type=configuration.
    - Example split: una nota con un block_id `example_*` debe tener al menos
      un unit de tipo concept/definition/parameter en la misma nota (si no,
      el ejemplo está "flotando" fuera de su concepto).

    Heurística simplificada por la naturaleza del spec: los splits atómicos
    son siempre "demasiadas notas del mismo tipo" o "examples aislados".
    """
    notes = plan["notes"]
    violations: list[str] = []

    # Procedure split: ≥ 2 notas type=procedure.
    proc_notes = [n for n in notes if n["type"] == "procedure"]
    if len(proc_notes) >= 2:
        violations.append(f"procedure partido en {len(proc_notes)} notas")

    # Configuration table split: ≥ 2 notas type=configuration.
    cfg_notes = [n for n in notes if n["type"] == "configuration"]
    if len(cfg_notes) >= 2:
        violations.append(f"configuration (parameter-table) partido en {len(cfg_notes)} notas")

    # Example split: si una nota tiene unit_id de tipo 'u_example_*' pero no
    # tiene unit de tipo 'u_definition_*' o 'u_concept_*' en la misma nota,
    # el ejemplo está flotando — el spec §4 dice que el ejemplo va con el
    # concepto que ilustra.
    for n in notes:
        has_example = any(uid.startswith("u_example_") for uid in n["unit_ids"])
        has_concept = any(
            uid.startswith(("u_definition_", "u_concept_"))
            for uid in n["unit_ids"]
        )
        if has_example and not has_concept:
            violations.append(
                f"example en nota {n['note_id']!r} sin definition/concept asociado "
                f"(posible split del ejemplo)"
            )

    ok = len(violations) == 0
    return ok, f"  violations={violations or 'ninguno'}, {'PASS' if ok else 'FAIL'}"


# -------------------------------------------------------------------
# Criterio 3: umbral.
# -------------------------------------------------------------------

def check_threshold(plan: dict) -> tuple[bool, str]:
    """`threshold_exceeded = (notes_planned > 5) OR (total_must_keep > 30)`.
    `user_approval_required = threshold_exceeded`."""
    md = plan["metadata"]
    notes_planned = md.get("notes_planned", 0)
    total_must_keep = md.get("total_must_keep", 0)
    expected_threshold = (notes_planned > 5) or (total_must_keep > 30)
    expected_approval = expected_threshold

    threshold_ok = md.get("threshold_exceeded") == expected_threshold
    approval_ok = md.get("user_approval_required") == expected_approval

    ok = threshold_ok and approval_ok
    return ok, (f"  notes_planned={notes_planned}, total_must_keep={total_must_keep}, "
                f"threshold={md.get('threshold_exceeded')}/{expected_threshold}, "
                f"approval={md.get('user_approval_required')}/{expected_approval}, "
                f"{'PASS' if ok else 'FAIL'}")


# -------------------------------------------------------------------
# Colisiones (R5).
# -------------------------------------------------------------------

def check_collision(plan: dict, expected_decision: str) -> tuple[bool, str]:
    """Verifica que cada nota con collision_decision coincida con expected."""
    notes_with_collision = [n for n in plan["notes"]
                            if n.get("collision_decision") is not None]
    if not notes_with_collision:
        return False, "FAIL (ninguna nota con collision_decision)"
    ok = all(n.get("collision_decision") == expected_decision
             and n.get("collision_with")
             for n in notes_with_collision)
    decisions = [n.get("collision_decision") for n in notes_with_collision]
    return ok, f"  decisions={decisions} (esperado {expected_decision}), {'PASS' if ok else 'FAIL'}"


# -------------------------------------------------------------------
# Schema validity (R10).
# -------------------------------------------------------------------

def check_schema(plan: dict) -> tuple[bool, str]:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return True, "SKIP (jsonschema ausente)"
    schema = _load(SCHEMA)
    try:
        jsonschema.Draft202012Validator(schema).validate(plan)
        return True, "PASS"
    except jsonschema.ValidationError as e:
        return False, f"FAIL ({e.message})"


# -------------------------------------------------------------------
# Tipos cerrados (R1).
# -------------------------------------------------------------------

ALLOWED_TYPES = {
    "concept", "api-reference", "procedure", "configuration",
    "error-troubleshooting", "architecture", "syntax", "data-model",
    "chapter-digest", "comparison", "version-delta", "glossary-term",
    "cheatsheet", "index-moc", "practice",
}


def check_types_closed(plan: dict) -> tuple[bool, str]:
    """Verifica que todos los tipos estén en el enum cerrado.

    Para `plan-good`: ok=True (todos válidos).
    Para `plan-wrong-type`: ok=True significa que el eval DETECTÓ tipos fuera
    del enum (lo cual es lo deseado para el caso negativo).
    """
    bad = [n["type"] for n in plan["notes"] if n["type"] not in ALLOWED_TYPES]
    # Para el caso negativo (esperamos bad_types no vacío), el test es positivo.
    return bad, f"  bad_types={bad or 'ninguno'}"


# -------------------------------------------------------------------
# Main.
# -------------------------------------------------------------------

def main() -> int:
    print("Fase 44 — eval: Note Plan")
    print()

    # Criterio 1 — coverage.
    print("Criterio 1 — Toda unidad must-keep está asignada a una nota del plan:")
    p_good = _load(FIX / "plan-good.json")
    p_unassigned = _load(FIX / "plan-unassigned.json")

    c1_good, m1_good = check_coverage(p_good)
    print(f"  [good] {m1_good}")
    c1_bad, m1_bad = check_coverage(p_unassigned)
    print(f"  [unassigned] {m1_bad}")
    c1_overall = c1_good and not c1_bad
    print(f"  criterio 1 overall: {'PASS' if c1_overall else 'FAIL'}")
    print()

    # Criterio 2 — atomicidad.
    print("Criterio 2 — La división nunca parte procedimiento/tabla/ejemplo:")
    p_split_proc = _load(FIX / "plan-split-procedure.json")
    p_split_table = _load(FIX / "plan-split-table.json")
    p_split_ex = _load(FIX / "plan-split-example.json")
    p_good_again = _load(FIX / "plan-good.json")

    ok2_proc_bad, m2_proc_bad = check_atomic_units(p_split_proc)
    ok2_table_bad, m2_table_bad = check_atomic_units(p_split_table)
    ok2_ex_bad, m2_ex_bad = check_atomic_units(p_split_ex)
    ok2_good, m2_good = check_atomic_units(p_good_again)
    print(f"  [good] {m2_good}")
    print(f"  [split-procedure] {m2_proc_bad}")
    print(f"  [split-table] {m2_table_bad}")
    print(f"  [split-example] {m2_ex_bad}")
    c2_overall = ok2_good and not ok2_proc_bad and not ok2_table_bad and not ok2_ex_bad
    print(f"  criterio 2 overall: {'PASS' if c2_overall else 'FAIL'}")
    print()

    # Criterio 3 — threshold.
    print("Criterio 3 — El plan se muestra antes de redactar cuando supera el umbral:")
    p_large = _load(FIX / "plan-large.json")
    p_small = _load(FIX / "plan-small.json")
    ok3_large, m3_large = check_threshold(p_large)
    ok3_small, m3_small = check_threshold(p_small)
    print(f"  [large] {m3_large}")
    print(f"  [small] {m3_small}")
    c3_overall = ok3_large and ok3_small
    print(f"  criterio 3 overall: {'PASS' if c3_overall else 'FAIL'}")
    print()

    # Colisiones.
    print("Colisiones (R5):")
    p_reuse = _load(FIX / "plan-reuse.json")
    p_new = _load(FIX / "plan-new.json")
    ok_reuse, m_reuse = check_collision(p_reuse, "reuse")
    ok_new, m_new = check_collision(p_new, "new")
    print(f"  [reuse] {m_reuse}")
    print(f"  [new] {m_new}")
    collisions_ok = ok_reuse and ok_new
    print(f"  colisiones overall: {'PASS' if collisions_ok else 'FAIL'}")
    print()

    # Schema validity.
    print("Schema validity:")
    p_wrong = _load(FIX / "plan-wrong-type.json")
    bad_types, m_types = check_types_closed(p_wrong)
    # Caso negativo: el eval DETECTÓ tipos fuera del enum → eval correcto.
    types_detected = len(bad_types) > 0
    print(f"  [types-cerrados] eval detecta bad_types={types_detected} (esperado True): {m_types}")
    ok_schema_good, m_schema_good = check_schema(p_good)
    print(f"  [schema-good] {m_schema_good}")
    schema_ok = types_detected and ok_schema_good
    print(f"  schema overall: {'PASS' if schema_ok else 'FAIL'}")
    print()

    # No-regresión.
    print("No-regresión:")
    nr = []
    r = subprocess.run(
        [sys.executable, str(VALIDATE_LEDGER), "--validate",
         str(REPO / "evals" / "ledger-sample" / "full-coverage.json"),
         str(REPO / "evals" / "ledger-sample" / "mixed-states.json")],
        capture_output=True, text=True,
    )
    ok = r.returncode == 0
    print(f"  [F15] {'PASS' if ok else 'FAIL'}")
    nr.append(ok)
    for label, script in [("F37", F37_EVAL), ("F38", F38_EVAL),
                          ("F39", F39_EVAL), ("F40", F40_EVAL),
                          ("F41", F41_EVAL), ("F42", F42_EVAL),
                          ("F43", F43_EVAL)]:
        r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
        ok = r.returncode == 0 and "RESULTADO: PASS" in r.stdout
        print(f"  [{label}] {'PASS' if ok else 'FAIL'}")
        nr.append(ok)

    all_ok = (c1_overall and c2_overall and c3_overall
              and collisions_ok and schema_ok
              and all(nr))
    print()
    print(f"RESULTADO: {'PASS' if all_ok else 'FAIL'} "
          f"(c1={c1_overall} c2={c2_overall} c3={c3_overall} "
          f"collisions={collisions_ok} schema={schema_ok} "
          f"nr={sum(nr)}/{len(nr)})")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
