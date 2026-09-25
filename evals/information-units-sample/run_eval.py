"""Eval — Fase 37: unidades de información.

Verifica los 3 criterios del roadmap:
1. Dos extracciones independientes coinciden en ≥90 % de must-keep (Jaccard).
2. Las reglas automáticas R1–R5 se aplican sin excepción (carga el ground-truth
   desde `expected/source-*-criticality.json` y verifica que cada unidad
   must-keep aparezca en TODAS las extracciones).
3. Cada uno de los 14 tipos tiene definición operativa + ejemplo técnico en
   `information-units.md` §3.

Exit codes:
  0 = PASS los 3 criterios.
  1 = FAIL algún criterio (con detalle).
  2 = usage error (fixtures faltantes, spec ausente).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SPEC = REPO / "skill/notemartin-study-notes/references/03-knowledge/information-units.md"

sys.path.insert(0, str(HERE))
from rules import is_must_keep  # noqa: E402

TYPES_14 = [
    "definition",
    "mechanism",
    "parameter",
    "default",
    "constraint",
    "step",
    "example",
    "warning",
    "error-code",
    "tradeoff",
    "version-note",
    "syntax-rule",
    "cross-reference",
    "formula",
]

TYPES_14_SET = set(TYPES_14)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def must_keep_units(extraction: dict) -> set[str]:
    """Devuelve el conjunto de unit_ids con criticality=must-keep."""
    return {u["unit_id"] for u in extraction["units"] if u["criticality"] == "must-keep"}


def must_keep_units_full(extraction: dict) -> list[dict]:
    return [u for u in extraction["units"] if u["criticality"] == "must-keep"]


def check_criterion_1(ext1: dict, ext2: dict, label: str) -> tuple[bool, str]:
    mk1 = must_keep_units(ext1)
    mk2 = must_keep_units(ext2)
    j = jaccard(mk1, mk2)
    ok = j >= 0.90
    return ok, f"  [{label}] must-keep |E1|={len(mk1)} |E2|={len(mk2)} |E1∩E2|={len(mk1 & mk2)} Jaccard={j:.3f} (umbral 0.90) → {'PASS' if ok else 'FAIL'}"


def check_criterion_2(ext1: dict, ext2: dict, gt_path: Path, label: str) -> tuple[bool, str]:
    """Carga ground-truth desde JSON; verifica que cada must-keep aparezca en AMBAS extracciones.

    El ground-truth es la lista canónica de unidades must-keep generada por
    `build_fixtures.compute_ground_truth` (que aplica R1–R5 vía `rules.is_must_keep`).
    Esto desacopla la verificación del generador de extracciones: si R1–R5 cambian
    en `rules.py` y el generador de extracciones se queda atrás, el eval falla.
    """
    if not gt_path.exists():
        return False, f"  [{label}] ground-truth ausente: {gt_path}"
    gt = load_json(gt_path)
    gt_block_ids = {entry["block_id"] for entry in gt}

    must_blocks_1 = {u["source_block_ids"][0] for u in must_keep_units_full(ext1)}
    must_blocks_2 = {u["source_block_ids"][0] for u in must_keep_units_full(ext2)}

    missing_1 = gt_block_ids - must_blocks_1
    missing_2 = gt_block_ids - must_blocks_2
    violations = []
    if missing_1:
        violations.append(f"E1 missing {sorted(missing_1)}")
    if missing_2:
        violations.append(f"E2 missing {sorted(missing_2)}")

    # Verificación adicional: toda unidad que active R1–R5 (calculada fresh
    # desde el SDM-equivalente vía rules.is_must_keep) debe ser must-keep en
    # AMBAS extracciones. Esto detecta el caso donde una unidad no está en
    # ground-truth por desincronización pero la regla sí la activaría.
    auto_units_in_ext1: set[str] = set()
    auto_units_in_ext2: set[str] = set()
    for u in ext1["units"]:
        if is_must_keep(u):
            auto_units_in_ext1.add(u["source_block_ids"][0])
    for u in ext2["units"]:
        if is_must_keep(u):
            auto_units_in_ext2.add(u["source_block_ids"][0])
    auto_not_mk_1 = auto_units_in_ext1 - must_blocks_1
    auto_not_mk_2 = auto_units_in_ext2 - must_blocks_2
    if auto_not_mk_1:
        violations.append(f"E1 rule-trigger no must-keep: {sorted(auto_not_mk_1)}")
    if auto_not_mk_2:
        violations.append(f"E2 rule-trigger no must-keep: {sorted(auto_not_mk_2)}")

    ok = len(violations) == 0
    detail = f"  [{label}] |gt|={len(gt_block_ids)} |E1.must|={len(must_blocks_1)} |E2.must|={len(must_blocks_2)}"
    if violations:
        detail += "\n    " + "\n    ".join(violations)
    return ok, detail + f" → {'PASS' if ok else 'FAIL'}"


def check_criterion_3(sdm_a: dict, sdm_b: dict) -> tuple[bool, str]:
    """Los 14 tipos aparecen en source-A∪source-B, y §3 del spec tiene ejemplos."""
    types_seen: set[str] = set()
    for sdm in (sdm_a, sdm_b):
        for section in sdm["sections"]:
            for block in section["blocks"]:
                t = block["type"]
                if t in TYPES_14_SET:
                    types_seen.add(t)
    missing_in_fixtures = TYPES_14_SET - types_seen

    if not SPEC.exists():
        return False, f"  spec ausente: {SPEC}"

    spec_text = SPEC.read_text()
    section_3_match = re.search(r"## §3.*?(?=^## §4)", spec_text, re.MULTILINE | re.DOTALL)
    if not section_3_match:
        return False, "  §3 del spec no encontrada"
    section_3 = section_3_match.group(0)
    missing_examples = [t for t in TYPES_14 if f"| `{t}`" not in section_3]

    coverage_ok = len(missing_in_fixtures) == 0
    examples_ok = len(missing_examples) == 0
    ok = coverage_ok and examples_ok
    detail = (
        f"  cobertura fixtures: {len(types_seen)}/14 tipos vistos; "
        f"faltan en fixtures: {sorted(missing_in_fixtures) or 'ninguno'}; "
        f"ejemplos en §3: faltan {missing_examples or 'ninguno'} → "
        f"{'PASS' if ok else 'FAIL'}"
    )
    return ok, detail


def main() -> int:
    required = [
        HERE / "fixtures/source-A.sdm.json",
        HERE / "fixtures/source-B.sdm.json",
        HERE / "fixtures/source-A-extraction-1.json",
        HERE / "fixtures/source-A-extraction-2.json",
        HERE / "fixtures/source-B-extraction-1.json",
        HERE / "fixtures/source-B-extraction-2.json",
        HERE / "expected/source-A-criticality.json",
        HERE / "expected/source-B-criticality.json",
    ]
    for p in required:
        if not p.exists():
            print(f"FAIL: artefacto faltante {p}. Ejecuta build_fixtures.py primero.", file=sys.stderr)
            return 2

    sdm_a = load_json(HERE / "fixtures/source-A.sdm.json")
    sdm_b = load_json(HERE / "fixtures/source-B.sdm.json")
    a1 = load_json(HERE / "fixtures/source-A-extraction-1.json")
    a2 = load_json(HERE / "fixtures/source-A-extraction-2.json")
    b1 = load_json(HERE / "fixtures/source-B-extraction-1.json")
    b2 = load_json(HERE / "fixtures/source-B-extraction-2.json")

    print("Fase 37 — eval: unidades de información")
    print()
    print("Criterio 1 — Dos extracciones coinciden en ≥90 % de must-keep:")
    ok1a, msg1a = check_criterion_1(a1, a2, "source-A")
    ok1b, msg1b = check_criterion_1(b1, b2, "source-B")
    print(msg1a)
    print(msg1b)
    print()

    print("Criterio 2 — Reglas automáticas R1–R5 sin excepción (ground-truth desde JSON):")
    ok2a, msg2a = check_criterion_2(a1, a2, HERE / "expected/source-A-criticality.json", "source-A")
    ok2b, msg2b = check_criterion_2(b1, b2, HERE / "expected/source-B-criticality.json", "source-B")
    print(msg2a)
    print(msg2b)
    print()

    print("Criterio 3 — Cada tipo tiene definición operativa + ejemplo técnico:")
    ok3, msg3 = check_criterion_3(sdm_a, sdm_b)
    print(msg3)
    print()

    all_ok = ok1a and ok1b and ok2a and ok2b and ok3
    print(f"RESULTADO: {'PASS' if all_ok else 'FAIL'} (criterios: 1A={ok1a} 1B={ok1b} 2A={ok2a} 2B={ok2b} 3={ok3})")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
