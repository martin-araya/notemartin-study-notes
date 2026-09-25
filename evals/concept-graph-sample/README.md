# Eval — Fase 39: grafo de prerrequisitos

Verifica los 3 criterios del roadmap + no-regresión F15/F37/F38:

1. **Sin ciclos**: `build` sobre grafo acíclico exit 0; nodos y aristas coinciden con `expected/pristine-{nodes,edges}.json`.
2. **Cycle policy**: `block` ante ciclo → exit 1; `allow` → exit 0 con `cycles[]` poblado.
3. **Rutas + export**: `routes --goal` emite shortest + broadest; `export` genera `<out>/<domain>/graph.mmd` con sintaxis Mermaid correcta.
4. **Aristas colgantes**: WARNING a stderr + `dangling_edges[]` poblado.
5. **No-regresión F15/F37/F38**: los eval battery previos siguen verdes.

## Estructura

```
evals/concept-graph-sample/
├── README.md
├── build_fixtures.py          # stdlib puro
├── fixtures/
│   ├── sdm-pristine.json
│   ├── sdm-cycle.json
│   ├── sdm-orphan.json
│   ├── ledger-pristine.json    # 6 definitions + 5 cross-refs prereq (DAG)
│   ├── ledger-cycle.json       # pristine + 2 cycle edges
│   ├── ledger-orphan.json      # pristine + 1 dangling edge
│   ├── profile-block.yaml      # cycle_policy: block
│   └── profile-allow.yaml      # cycle_policy: allow
├── expected/
│   ├── pristine-nodes.json
│   └── pristine-edges.json
├── tmp_workdir/               # se crea/borra en cada run
└── run_eval.py
```

## Uso

```bash
python3 evals/concept-graph-sample/build_fixtures.py   # genera fixtures
python3 evals/concept-graph-sample/run_eval.py         # verifica 7 sub-checks
```

Exit codes: `0` PASS los 7, `1` FAIL, `2` usage.

## Diseño

Cada sub-check crea un workdir sintético en `tmp_workdir/<name>` con la combinación sdm/ledger/profile necesaria. El script `concept_graph.py` se invoca vía subprocess y se compara su output (exit code, stdout, stderr, JSON en disco) contra los expected.

Para el sub-check 3 (rutas), se verifica que `routes --goal mvcc` emite tanto `strategy=shortest` (length 1) como `strategy=broadest` (length 2, ruta `acid → mvcc`).

Para el sub-check 3 (export), se verifica que el archivo `.mmd` generado contiene `flowchart LR`, `subgraph`, y aristas con `-->|prereq|`.

## Sin regresión

```bash
python3 scripts/util/validate_ledger.py --validate evals/ledger-sample/*.json   # F15 OK
python3 evals/information-units-sample/run_eval.py                              # F37 OK
python3 evals/ledger-operativo-sample/run_eval.py                               # F38 OK
python3 evals/concept-graph-sample/run_eval.py                                  # F39 OK
```
