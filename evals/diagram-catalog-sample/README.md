# `evals/diagram-catalog-sample/` — Verificador de la Fase 65

Eval battery para `@/references/07-visual/diagram-catalog.md` (Fase 65). Verifica los **3 criterios de aceptación de la fase** más 3 criterios transversales:

| # | Criterio | Cubre |
|---|---|---|
| C1 | 10 tipos con plantilla y ejemplo técnico | Criterio 1 de F65 (§4) |
| C2 | Matriz resuelve todos los casos del corpus (14 fuentes) | Criterio 2 de F65 (§9) |
| C3 | Ningún ejemplo de visión por computador | Criterio 3 de F65 (§1/§2) |
| C4 | Regla de los 15 nodos (§6) | Detalle F65, regla dura R-D-02 |
| C5 | Obligatoriedad en arquitectura/índice/procedimiento ramificado (§7) | Detalle F65 |
| C6 | Wirings de cada tipo §4.x | Estilo de la skill |

## Cómo correr

```bash
python evals/diagram-catalog-sample/run_eval.py \
    --catalog skill/notemartin-study-notes/references/07-visual/diagram-catalog.md
```

Salida esperada:

```
============================================================
Fase 65 — Catálogo por intención
============================================================
  ✓ C1-10-tipos
  ✓ C2-corpus-coverage (14/14)
  ✓ C3-no-vision
  ✓ C4-15-nodes (8 casos)
  ✓ C5-obligatoriedad (5 casos)
  ✓ C6-wirings
============================================================
PASS 6/6
```

Exit 0 en PASS, exit 1 en cualquier FAIL.

## Cómo regenerar fixtures

```bash
python evals/diagram-catalog-sample/build_fixtures.py
```

Las fixtures son **datos verificables**, no se editan a mano: si necesitas cambiar la cobertura del corpus, edita el array `rows` en `build_fixtures.py:build_corpus_coverage` y regenera.

## Estructura

```
evals/diagram-catalog-sample/
├── README.md
├── build_fixtures.py          # regenera los YAMLs y la lista negra
├── run_eval.py                # verificador principal (6 criterios)
└── fixtures/
    ├── positive-intentions.yaml     # 10 tipos canónicos (§4)
    ├── corpus-coverage.yaml         # 14 fuentes (§9)
    ├── fifteen-nodes-decision.yaml  # 8 casos de tamaño (§6)
    ├── obligatoriedad.yaml          # 5 situaciones (§7)
    ├── matrix-resolution.yaml       # 20 intenciones no listadas (§3 fallback)
    └── no-vision-examples.txt       # lista negra de visión por computador
```
