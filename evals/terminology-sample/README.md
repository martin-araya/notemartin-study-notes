# Eval — Fase 40: terminología y glosario acumulativo

Verifica los 3 criterios del roadmap + ortogonalidad de las señales + no-regresión F15/F37/F38/F39:

1. **Criterio 1**: ningún término tiene > 1 definition con `canonical: true`.
2. **Criterio 2**: ningún alias (string normalizado) apunta a dos términos distintos.
3. **Criterio 3**: ningún término tiene ≥ 2 definitions con `definition` distinta.

Más sub-checks: R1 (kebab-case), R4 (alias kind enum), schema validity (con `jsonschema` opcional), resolución de colisión `-<vendor>`.

## Estructura

```
evals/terminology-sample/
├── README.md
├── build_fixtures.py          # stdlib puro
├── fixtures/
│   ├── glossary-good.json             # 5 términos válidos (caso bueno)
│   ├── glossary-dual-def.json         # criterio 1 violado
│   ├── glossary-alias-collision.json  # criterio 2 violado
│   ├── glossary-redefinition.json     # criterio 3 violado
│   └── glossary-collision-suffix.json # 'wal' PostgreSQL + 'wal-oracle' Oracle (sufijo aplicado)
├── expected/
│   ├── good-canonicals.json
│   └── redefinition-chapters.json
└── run_eval.py
```

## Uso

```bash
python3 evals/terminology-sample/build_fixtures.py   # genera fixtures
python3 evals/terminology-sample/run_eval.py         # verifica los 3 criterios
```

Exit codes: `0` PASS, `1` FAIL, `2` usage.

## Diseño de los casos negativos

Cada fixture negativo aísla **un solo criterio** violado:

- `dual-def`: agrega una 2da entry `canonical=true` con **texto idéntico** al original (no dispara criterio 3). Solo viola criterio 1.
- `alias-collision`: añade el alias `"transaction"` al término `mvcc` con kind=`variant`. Solo viola criterio 2.
- `redefinition`: añade a `wal` una entry con `canonical=false, status=conflicting, definition` distinta a la canónica. Solo viola criterio 3.

Esto garantiza que las tres señales son ortogonales: un eval que reporta `dual-def FAIL en c3` es bug, no diseño.

## Sin regresión

```bash
python3 scripts/util/validate_ledger.py --validate evals/ledger-sample/*.json   # F15 OK
python3 evals/information-units-sample/run_eval.py                              # F37 OK
python3 evals/ledger-operativo-sample/run_eval.py                               # F38 OK
python3 evals/concept-graph-sample/run_eval.py                                  # F39 OK
python3 evals/terminology-sample/run_eval.py                                    # F40 OK
```
