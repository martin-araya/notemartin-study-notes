# Eval — Fase 43: auditoría de no-pérdida

Verifica los 3 criterios del roadmap + no-regresión F15/F37/F38/F39/F40/F41/F42.

## Criterios del roadmap

1. **Detecta una omisión inyectada deliberadamente.**
   - Caso `missing-backward`: ledger omite un must-keep block.
   - Caso `mutilated`: `parameter.name` alterado.
   - Caso `pending-must-keep`: must-keep en `state=pending`.
2. **El muestreo inverso tiene tamaño y método definidos.**
   - Verifica campos: `total_blocks`, `must_keep_count`, `editorial_severity_count`, `context_pool_count`, `sampled_must_keep`, `sampled_context`, `sampled_context_pct`, `sample_rate`, `seed`, `must_keep_coverage_pct`.
   - Verifica determinismo: dos corridas con mismo seed producen el mismo `sampled_context`.
3. **No se puede cerrar el trabajo con la auditoría en rojo.**
   - `audit` exit 1 con cualquier critical.
   - `check` exit 1 con cualquier critical.
   - `check --strict` exit 1.
   - `audit` sobre ledger limpio exit 0.

## Estructura

```
evals/completeness-sample/
├── README.md
├── build_fixtures.py          # stdlib puro
├── fixtures/
│   ├── sdm-clean.json                 # 7 blocks: 5 must-keep + 1 context + 1 prose
│   ├── ledger-clean.json              # 6 entries, todos terminales, 100% must-keep cobertura
│   ├── ledger-with-omission.json      # omite el entry error-code (criterio 1)
│   ├── ledger-mutilated.json          # parameter.name mutilado
│   ├── ledger-pending.json            # must-keep con state=pending
│   ├── sdm-context-rich.json          # 50 prose + 2 must-keep (test del muestreo 10%)
│   └── ledger-context-rich-partial.json  # cubre must-keep pero omite context
├── expected/
├── tmp_workdir/                      # se crea/borra en cada run
└── run_eval.py
```

## Uso

```bash
python3 evals/completeness-sample/build_fixtures.py   # genera fixtures
python3 evals/completeness-sample/run_eval.py         # verifica los 3 criterios
```

Exit codes: `0` PASS los 8 sub-checks, `1` FAIL, `2` usage.

## Diseño

Cada sub-check crea un workdir sintético en `tmp_workdir/<name>` con la combinación SDM/ledger necesaria, invoca el script vía subprocess y compara el exit code + JSON output contra los expected.

- **criterio 1**: 3 sub-checks ortogonales (omisión / mutilación / pending). Cada uno activa una `category` distinta del audit.
- **criterio 2**: 2 sub-checks. El primero verifica que el reporte declara los tamaños. El segundo verifica determinismo del sampling con seed.
- **criterio 3**: 3 sub-checks (audit-exit-1, clean-exit-0, actionable-list-shape).

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
```
