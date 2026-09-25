# Eval — Fase 38: ledger operativo

Verifica los 3 criterios del roadmap + no-regresión de F15/F37:

1. El reporte se genera en cualquier punto del proceso.
2. Detecta huérfanos y contenido sin respaldo.
3. El estado persiste en el manifiesto.
4. No-regresión F15: `validate_ledger.py` valida los fixtures regenerados bajo `schema 2.0.0`.
5. No-regresión F37: `evals/information-units-sample/run_eval.py` sigue verde con el shim de `unit_rules.py`.

## Estructura

```
evals/ledger-operativo-sample/
├── README.md
├── build_fixtures.py          # stdlib puro
├── fixtures/
│   ├── sdm-A.json             # 10 bloques, mix de 10 tipos
│   ├── sdm-B.json             # 6 bloques
│   ├── ledger-A-ok.json       # cubre 8/10 bloques
│   ├── ledger-A-orphan.json   # + 1 entry con block_id inexistente
│   ├── ledger-A-gap.json      # cubre 7/10 → 2 gaps (prose excluido)
│   ├── ledger-B-empty.json    # 0 entradas → 6 gaps
│   └── manifest-A.json        # baseline con units_processed=0
├── expected/
│   ├── orphans.json
│   ├── gaps.json
│   ├── gaps-include-prose.json
│   └── manifest-patch.json
├── tmp_workdir/               # se crea/borra en cada run
└── run_eval.py
```

## Uso

```bash
python3 evals/ledger-operativo-sample/build_fixtures.py   # genera fixtures
python3 evals/ledger-operativo-sample/run_eval.py         # verifica los 3 criterios
```

Exit codes: `0` PASS los 5 sub-checks, `1` FAIL, `2` usage.

## Diseño

- **Sub-check 1 (reporte)**: corre `ledger.py --workdir <wd> report` sobre `ledger-A-ok.json`; verifica que imprime las 4 vistas del reporte.
- **Sub-check 2a (huérfanos)**: corre `check` sobre `ledger-A-orphan.json` + `sdm-A.json`; verifica que lista el `block_id` inexistente.
- **Sub-check 2b (gaps, default)**: corre `check` sobre `ledger-A-gap.json` + `sdm-A.json`; verifica los 2 `block_id` sin entry (excluye `prose`).
- **Sub-check 2c (gaps, --include-prose)**: corre `check --include-prose` sobre el mismo ledger; verifica los 3 `block_id` (incluye `prose`).
- **Sub-check 2d (--strict)**: corre `check --strict` con desviaciones; verifica exit 1.
- **Sub-check 3 (manifest sync)**: corre `manifest --dry-run` (verifica que NO escribe) + `manifest` (verifica el patch + que no se tocan otros campos).
- **No-regresión F15**: corre `validate_ledger.py` contra los fixtures regenerados con `schema 2.0.0`.
- **No-regresión F37**: corre `evals/information-units-sample/run_eval.py` con el shim de `unit_rules.py`.

## Sin regresión

```bash
python3 scripts/util/validate_ledger.py --validate evals/ledger-sample/*.json   # F15 OK
python3 evals/information-units-sample/run_eval.py                              # F37 OK
python3 evals/ledger-operativo-sample/run_eval.py                               # F38 OK
```
