# Eval — Fase 41: contradicciones y obsolescencia

Verifica los 3 criterios del roadmap + reglas R1–R8 del spec + no-regresión F15/F37/F38/F39/F40.

## Criterios del roadmap

1. **Una contradicción inyectada se detecta y documenta con ambas anclas.**
   - Caso bueno: registry con 3 contradicciones válidas (anchors distintos, ambos válidos).
   - Casos negativos: anchor apuntando a bloque inexistente, 2 anchors idénticos (R3), contradicción en SDM no documentada.
2. **Todo contenido deprecado llega marcado.**
   - Caso bueno: cada bloque `deprecated` en SDM tiene entry en ledger con `deprecation_status`.
   - Caso negativo: bloque deprecated sin marker — eval detecta el issue.
3. **El cuerpo nunca contradice la fuente sin señalarlo.**
   - Caso bueno: directivas `:::contradiction` en NoteMark tienen id válido en el registry.
   - Caso negativo: id inexistente en el registry.

## Estructura

```
evals/conflicts-sample/
├── README.md
├── build_fixtures.py          # stdlib puro
├── fixtures/
│   ├── conflicts-good.json              # 3 contradicciones válidas
│   ├── conflicts-orphan-anchor.json     # R2 violada: anchor apunta a bloque inexistente
│   ├── conflicts-same-anchor.json       # R3 violada: 2 anchors idénticos
│   ├── conflicts-undocumented.json      # registry vacío (criterio 1 — eval detecta)
│   ├── sdm-with-contradiction.json      # SDM con 2 bloques parameter contradictorios
│   ├── sdm-deprecated-unmarked.json     # SDM con bloques que mencionan deprecated
│   ├── sdm-deprecated-marked.json       # (mismo SDM; el marker está en el ledger)
│   ├── ledger-with-deprecation.json     # entries con deprecation_status poblado
│   ├── ledger-no-deprecation.json       # entries SIN deprecation_status (negativo)
│   ├── notemark-good.md                 # directivas :::contradiction con id válido
│   └── notemark-undocumented.md         # directivas con id que no existe en registry
├── expected/
└── run_eval.py
```

## Uso

```bash
python3 evals/conflicts-sample/build_fixtures.py   # genera fixtures
python3 evals/conflicts-sample/run_eval.py         # verifica los 3 criterios
```

Exit codes: `0` PASS, `1` FAIL, `2` usage.

## Diseño

- **Criterio 1 — sub-check `[undocumented]`**: el eval detecta duplicados de `parameter.name` en el SDM y compara con el registry. Si el registry NO contiene un conflict con anchor block que matchee uno de los ids del par duplicado, el eval reporta `FAIL`. Esto verifica la *detección*, no la cobertura total.
- **Criterio 2 — negativo `[no-marker-in-ledger]`**: el mismo `check_deprecation_marked` corre con un ledger SIN `deprecation_status`. Esperamos que retorne `FAIL` (issue detectado), lo que demuestra que el eval identifica el caso no marcado.
- **Criterio 3 — directo**: parsea NoteMark con regex `:::contradiction\s+id="([^"]+)"` y compara contra `registry.conflicts[*].id`.

## Sin regresión

```bash
python3 scripts/util/validate_ledger.py --validate evals/ledger-sample/*.json   # F15 OK
python3 evals/information-units-sample/run_eval.py                              # F37 OK
python3 evals/ledger-operativo-sample/run_eval.py                               # F38 OK
python3 evals/concept-graph-sample/run_eval.py                                  # F39 OK
python3 evals/terminology-sample/run_eval.py                                    # F40 OK
python3 evals/conflicts-sample/run_eval.py                                      # F41 OK
```
