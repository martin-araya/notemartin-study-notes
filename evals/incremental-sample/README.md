# `evals/incremental-sample/` — F111 Actualización incremental

Eval battery para la Fase 111. Verifica los **3 criterios del ROADMAP**:

| Criterio ROADMAP | Sub-eval | Qué verifica |
|---|---|---|
| Un cambio en una sección reprocesa solo lo afectado | C1 | `c.note-ir.json` se marca `status: archived` + `superseded_by` poblado; `a` y `b` mantienen sus `source_refs` originales byte-a-byte |
| Se genera el delta automáticamente | C2 | Existe `ir/vd0001.note-ir.json` con `note_type: "version-delta"` + tabla `changes` con ≥ 3 entradas (una por sección afectada: `/ch02/main` modified + `/ch03/deprecated` removed + `/ch05/new` added) |
| Ninguna nota pierde contenido válido | C3 | `a` y `b` mantienen `source_refs` originales; `c` NO se borra (INC-R2) y tiene `superseded_by` poblado; source_refs originales preservados |

## Estructura

```
evals/incremental-sample/
├── build_fixtures.py        # stdlib puro; --regen idempotente
├── run_eval.py              # 3 sub-criterios PASS/FAIL
├── fixtures/
│   ├── old/old_sdm.json     # SDM v15: 4 bloques b1..b4
│   ├── old/new_sdm.json     # SDM v16: b1 unchanged + b2 modified + b3 REMOVED + b5 ADDED
│   └── workdir/
│       ├── ir/{a,b,c,d}.note-ir.json
│       └── manifest.json
├── expected/
│   └── expected.json        # invariantes agregadas
└── README.md
```

## Uso

```bash
python3 evals/incremental-sample/build_fixtures.py --regen
python3 evals/incremental-sample/run_eval.py
```

Salida esperada: `PASS 3/3`.

## Dependencias

Python 3.9+ stdlib puro. Sin `jsonschema`, sin red.