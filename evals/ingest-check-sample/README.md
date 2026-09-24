# Ingest check eval — `evals/ingest-check-sample/`

Eval de F30. Verifica los 3 criterios del roadmap:

1. Detecta una página omitida deliberadamente.
2. Lista secciones del índice ausentes en el SDM.
3. La puerta bloquea con anomalías críticas.

## Cómo se corre

```bash
python3 evals/ingest-check-sample/run_eval.py
```

Esperado: `3 PASS, 0 FAIL`.

## Estructura

```
evals/ingest-check-sample/
├── README.md
├── build_fixtures.py             genera 3 escenarios con SDM y declared-index
├── run_eval.py                   ejecuta ingest_check.py y valida los 3 criterios
├── scenarios/
│   ├── sdm-with-missing-page/    page 2 omitida (1, 3 presentes; declared: 1, 2, 3)
│   ├── sdm-with-missing-section/  headings 1.1, 1.2 presentes; declared: 1.1, 1.2, 1.3
│   └── sdm-critical/              page 2 omitida + sección 1.3 omitida + heading vacío
└── expected/
    ├── missing-page.json          missing_pages contains [2]
    ├── missing-section.json       missing_sections contains ["1.3"]
    └── blocking.json               exit_code == 1, critical_count >= 1
```

## Cobertura

| Scenario | criterion 1 | criterion 2 | criterion 3 |
|---|---|---|---|
| `sdm-with-missing-page/` | ✓ missing_pages=[2] | n/a | n/a |
| `sdm-with-missing-section/` | n/a | ✓ missing_sections=["1.3"] | n/a |
| `sdm-critical/` | n/a | n/a | ✓ exit=1, critical=1 |

## Verificación de los 3 criterios del roadmap

| Criterio | Cómo se cumple |
|---|---|
| Detecta página omitida | `_criterion_1_missing_page` ejecuta ingest_check sobre `sdm-with-missing-page/`. Verifica que `totals.missing_pages == [2]`. |
| Lista secciones ausentes | `_criterion_2_missing_section` ejecuta sobre `sdm-with-missing-section/`. Verifica que `"1.3"` ∈ `totals.missing_sections`. |
| Puerta bloquea críticas | `_criterion_3_blocking_gate` ejecuta sobre `sdm-critical/`. Verifica `exit_code == 1` y `len(anomalies.critical) >= 1`. |

## Regenerar los fixtures

```bash
python3 evals/ingest-check-sample/build_fixtures.py
```

Dependencias: ninguna (solo Python stdlib).

## Lo que **no** cubre

- Validación de más de 5 anomalías por escenario (cubrimos las principales).
- Override humano con `--allow-critical --human-decision` (verificado en `sdm-critical` retorna exit 1 sin override; F31 NO debe consumir).
- Comparación con declared-index muy grandes (> 1000 secciones).
- Tests de regresión automatizados en CI. La suite completa se materializa en F118.
