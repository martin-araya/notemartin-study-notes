"""Reglas automáticas R1–R5 — fuente única compartida por F37 y F38.

Implementa `is_must_keep(block)` y `AUTO_RULES` que el spec
`information-units.md` §5 declara. Lo importan:

- `evals/information-units-sample/build_fixtures.py` y `run_eval.py` (vía shim)
  para generar y verificar extracciones.
- `scripts/util/ledger.py` (F38) para aplicar las reglas mecánicamente al añadir
  entradas al ledger.

Sin dependencias externas (Python 3.9+ stdlib puro).
"""

from __future__ import annotations

from typing import Optional


AUTO_RULES: dict[str, str] = {
    "parameter": "R1",
    "default": "R2",
    "error-code": "R3",
    "warning": "R4",
}


def is_must_keep(block: dict) -> Optional[str]:
    """Devuelve el id de regla (`"R1"`..`"R5"`) si el bloque activa una regla
    automática de criticidad, o `None` en caso contrario.

    Acepta tanto bloques del SDM (con `block["type"]` y `block["content"]`)
    como unidades del ledger (con `unit["type"]` y `unit["content"]`).
    """
    t = block["type"]
    rationale = AUTO_RULES.get(t)
    if rationale:
        return rationale
    if t == "formula" and block["content"].get("numbered") is True:
        return "R5"
    return None
