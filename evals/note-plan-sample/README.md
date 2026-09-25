# Eval — Fase 44: Note Plan

Verifica los 3 criterios del roadmap + reglas R1–R10 del spec + no-regresión F15/F37/F38/F39/F40/F41/F42/F43.

## Criterios del roadmap

1. **Toda unidad `must-keep` está asignada a una nota del plan.**
   - Caso bueno: `assigned_must_keep == total_must_keep`, `unassigned_unit_ids` vacío.
   - Caso negativo: `unassigned_unit_ids` poblado → eval FAIL.
2. **La división nunca parte un procedimiento, una tabla de parámetros ni un ejemplo desarrollado.**
   - Caso bueno: 0 violaciones.
   - Casos negativos: ≥ 2 notas de tipo `procedure` (procedimiento partido), ≥ 2 notas de tipo `configuration` (tabla partida), example sin definition/concept asociado (ejemplo flotando).
3. **El plan se muestra antes de redactar cuando supera el umbral.**
   - Caso grande (6 notas / 36 must-keep): `threshold_exceeded=true`, `user_approval_required=true`.
   - Caso pequeño (3 notas / 10 must-keep): `threshold_exceeded=false`, `user_approval_required=false`.

Más sub-checks: tipos cerrados (15 valores); colisiones (reuse/new); schema validity.

## Estructura

```
evals/note-plan-sample/
├── README.md
├── build_fixtures.py          # stdlib puro
├── fixtures/
│   ├── plan-good.json                # 5 notas, cobertura 100%
│   ├── plan-unassigned.json          # 1 must-keep sin asignar (criterio 1 negativo)
│   ├── plan-split-procedure.json     # 2 notas procedure (criterio 2 negativo)
│   ├── plan-split-table.json         # 3 notas configuration (criterio 2 negativo)
│   ├── plan-split-example.json       # example sin definition/concept (criterio 2 negativo)
│   ├── plan-large.json               # 6 notas / 36 must-keep → approval required (criterio 3 positivo)
│   ├── plan-small.json               # 3 notas / 10 must-keep → approval not required (criterio 3 negativo)
│   ├── plan-reuse.json               # colisión resuelta con reuse
│   ├── plan-new.json                 # colisión resuelta con new
│   └── plan-wrong-type.json          # tipo fuera del enum cerrado (15 tipos)
├── expected/
└── run_eval.py
```

## Uso

```bash
python3 evals/note-plan-sample/build_fixtures.py   # genera fixtures
python3 evals/note-plan-sample/run_eval.py         # verifica los 3 criterios
```

Exit codes: `0` PASS los 7 sub-checks, `1` FAIL, `2` usage.

## Sin regresión

```bash
python3 scripts/util/validate_ledger.py --validate evals/ledger-sample/*.json
python3 evals/information-units-sample/run_eval.py
python3 evals/ledger-operativo-sample/run_eval.py
python3 evals/concept-graph-sample/run_eval.py
python3 evals/terminology-sample/run_eval.py
python3 evals/conflicts-sample/run_eval.py
python3 evals/fidelity-sample/run_eval.py
python3 evals/completeness-sample/run_eval.py
python3 evals/note-plan-sample/run_eval.py
```
