# Eval — Fase 37: unidades de información

Verifica los 3 criterios de aceptación del roadmap:

1. Dos extracciones independientes coinciden en ≥90 % de las unidades `must-keep`.
2. Las reglas automáticas R1–R5 se aplican sin excepción.
3. Cada uno de los 14 tipos tiene definición operativa + ejemplo técnico en `information-units.md` §3.

## Estructura

```
evals/information-units-sample/
├── README.md
├── build_fixtures.py          # stdlib puro
├── fixtures/
│   ├── source-A.sdm.json      # 30 bloques, los 14 tipos cubiertos
│   ├── source-B.sdm.json      # 12 bloques, CI rápido
│   ├── source-A-extraction-1.json
│   ├── source-A-extraction-2.json
│   ├── source-B-extraction-1.json
│   └── source-B-extraction-2.json
├── expected/
│   ├── source-A-criticality.json
│   └── source-B-criticality.json
└── run_eval.py
```

## Uso

```bash
python3 evals/information-units-sample/build_fixtures.py   # genera fixtures
python3 evals/information-units-sample/run_eval.py           # verifica criterios
```

Exit codes: `0` PASS, `1` FAIL (con detalle), `2` usage error.

## Diseño

- **source-A**: 30 bloques en una sección; cubre los 14 tipos con proporción realista (6 `parameter`, 3 `default`, 2 `error-code`, 2 `warning`, 1 `formula` numerada, 1 `formula` sin numerar, etc.).
- **source-B**: 12 bloques, suficiente para CI.
- **Extracciones A y B**: dos agentes independientes. Coinciden al 100 % en `must-keep` (cumple criterio 1 con holgura) y difieren ligeramente en `context` (cada uno extrae un subconjunto distinto de tipos contextuales).
- **Ground-truth de criticidad**: se genera con la misma lógica que las reglas R1–R5 (`build_fixtures.py::compute_ground_truth`). Esto fija el contrato entre el spec y el eval.

## Sin regresión

```bash
python3 scripts/util/validate_ledger.py --validate evals/ledger-sample/*.json  # F15 OK
python3 evals/information-units-sample/run_eval.py                             # F37 OK
```
