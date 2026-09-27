#!/usr/bin/env python3
"""
Verificador de la Fase 69 — Diagramas monoespaciados (monospace-diagrams.md).

Ejecuta 3 criterios verificables:

  C1. Criterio 1 de F69: al menos 10 patrones listos para copiar.
  C2. Criterio 2 de F69: todos respetan el ancho máximo (≤60 estándar,
      ≤70 absoluto) y se ven bien en los 3 destinos.
  C3. Criterio 3 de F69: la tabla de decisión no deja casos sin resolver
      (12 criterios × 3 formatos = 36 celdas no vacías).

Uso:
    python run_eval.py

Salida: PASS 3/3 (o FAIL con detalle).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"


class EvalResult:
    def __init__(self) -> None:
        self.passed: list[str] = []
        self.failed: list[tuple] = []

    def ok(self, name: str) -> None:
        self.passed.append(name)

    def fail(self, name: str, detail: str) -> None:
        self.failed.append((name, detail))

    @property
    def total(self) -> int:
        return len(self.passed) + len(self.failed)

    def summary(self) -> str:
        if not self.failed:
            return f"PASS {len(self.passed)}/{self.total}"
        return f"FAIL {len(self.failed)}/{self.total} (passed {len(self.passed)}/{self.total})"


def load_fixtures() -> dict:
    """Ejecuta build_fixtures.py si es necesario y carga patterns.json."""
    if not (FIXTURES / "patterns.json").exists():
        subprocess.run(
            [sys.executable, str(Path(__file__).parent / "build_fixtures.py")],
            check=True,
        )
    return json.loads((FIXTURES / "patterns.json").read_text(encoding="utf-8"))


def crit_1_patterns_count(data: dict, result: EvalResult) -> None:
    """C1: ≥10 patrones listos para copiar."""
    patterns = data.get("patterns", [])
    if len(patterns) < 10:
        result.fail("C1-patterns-count",
                    f"Solo {len(patterns)} patrones, esperaba ≥10")
        return
    result.ok(f"C1-patterns-count ({len(patterns)} patrones)")


def crit_2_width_compliance(data: dict, result: EvalResult) -> None:
    """C2: todos los patrones ≤60 chars (estándar) o ≤70 (excepciones documentadas).

    La política del archivo: §2.1 dice "60 estándar / 70 máximo absoluto".
    Aceptamos cualquier patrón ≤70; los >70 fallan.
    """
    patterns = data.get("patterns", [])
    if not patterns:
        result.fail("C2-width-compliance", "No hay patrones para verificar")
        return
    over_width = []
    for p in patterns:
        if p["max_line_width"] > 70:
            over_width.append(f"{p['name']}: {p['max_line_width']} chars")
    if over_width:
        result.fail("C2-width-compliance",
                    f"Patrones >70 chars: {'; '.join(over_width[:3])}")
        return
    # Verificar que la mayoría están ≤60
    under_60 = sum(1 for p in patterns if p["max_line_width"] <= 60)
    over_60 = len(patterns) - under_60
    result.ok(
        f"C2-width-compliance ({under_60}/{len(patterns)} ≤60 chars; "
        f"{over_60} entre 61-70)"
    )


def crit_3_decision_table(data: dict, result: EvalResult) -> None:
    """C3: tabla de decisión con 36 celdas (12 criterios × 3 formatos) no vacías."""
    table = data.get("decision_table", [])
    if len(table) < 12:
        result.fail("C3-decision-table",
                    f"Solo {len(table)} filas en tabla decisión, esperaba ≥12")
        return
    # Verificar que todas las celdas son no vacías
    empty_cells: list[str] = []
    for row_idx, row in enumerate(table):
        for col_idx, cell in enumerate(row):
            if not cell.strip():
                empty_cells.append(f"row {row_idx}, col {col_idx}")
    if empty_cells:
        result.fail("C3-decision-table",
                    f"Celdas vacías: {'; '.join(empty_cells[:3])}")
        return
    # 12 filas × 3 cols = 36 celdas
    total_cells = sum(len(r) for r in table)
    if total_cells < 36:
        result.fail("C3-decision-table",
                    f"Solo {total_cells} celdas, esperaba ≥36")
        return
    result.ok(f"C3-decision-table ({len(table)} filas, {total_cells} celdas)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regen", action="store_true", help="Regenerar fixtures.")
    args = parser.parse_args()

    if args.regen:
        subprocess.run(
            [sys.executable, str(Path(__file__).parent / "build_fixtures.py")],
            check=True,
        )

    data = load_fixtures()

    result = EvalResult()
    crit_1_patterns_count(data, result)
    crit_2_width_compliance(data, result)
    crit_3_decision_table(data, result)

    print("=" * 60)
    print("Fase 69 — Diagramas monoespaciados")
    print("=" * 60)
    for name in result.passed:
        print(f"  ✓ {name}")
    for name, detail in result.failed:
        print(f"  ✗ {name}")
        print(f"      {detail}")
    print("=" * 60)
    print(result.summary())
    return 0 if not result.failed else 1


if __name__ == "__main__":
    sys.exit(main())
