# `evals/consolidation-sample/` — F109 Pases de consolidación

Eval battery para la Fase 109. Verifica los **3 criterios del ROADMAP**:

| Criterio ROADMAP | Sub-eval | Qué verifica |
|---|---|---|
| Tras consolidar no quedan enlaces rotos ni huérfanos | C1 | `run-all` emite `report-link-debt.json` con 1 `broken-wikilink` + 6 `orphan-note`; `manifest.json::link_debt[]` tiene 7 entradas (CON-R4 verificado) |
| Ningún término tiene 2 definiciones canónicas | C2 | `pass-glossary` reporta 1 violación R3 (alias "mv" en `["mvcc", "wal"]`); `consistency-report.json` sin violations adicionales (AP-CON-3 verificado) |
| Es re-ejecutable sin efectos secundarios | C3 | 2 ejecuciones consecutivas de `run-all` producen el mismo `after_sha256` (CON-R1 verificado; idempotencia) |

## Estructura

```
evals/consolidation-sample/
├── build_fixtures.py        # stdlib puro; --regen idempotente
├── run_eval.py              # 3 sub-criterios PASS/FAIL
├── fixtures/
│   └── workdir/
│       ├── ir/              # 7 IRs (a, b, c, d, f, g, x) con 1 broken-wikilink
│       └── knowledge/glossary.json  # 1 colisión R3 (alias "mv")
├── expected/
│   └── expected.json        # invariantes agregadas para auditoría
└── README.md                # este archivo
```

## Uso

```bash
python3 evals/consolidation-sample/build_fixtures.py --regen
python3 evals/consolidation-sample/run_eval.py
```

Salida esperada: `PASS 3/3`.

## Dependencias

Python 3.9+ stdlib puro. Sin `jsonschema`, sin red.