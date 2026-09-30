# `evals/chunk-loop-sample/` — F107 Bucle por chunks

Eval battery para la Fase 107. Verifica los **3 criterios del ROADMAP**:

| Criterio ROADMAP | Sub-eval | Qué verifica |
|---|---|---|
| Ninguna etapa requiere más de un número acotado de referencias | C1 + C6 | Default `chunk_size=30` produce 9 chunks sobre 250; presupuesto por etapa en spec §3 (`max_files_loaded` por etapa ≤ 4) |
| Una unidad que cruza dos chunks se documenta una vez y completa | C3 | Cross-chunk unit `mvcc` aparece en chk01+chk02; registrada con `primary_chunk=chk01`, `secondary_chunks=[chk02]`, `note_id` único (AP-CHK1 PASS) |
| Una fuente de 200+ páginas se procesa sin tenerla entera en contexto | C4 | `chunk_loop.py check --audit-loads` detecta carga del texto crudo (`.pdf`/`.epub`/`.html`) en log → AP-CHK2 FAIL |

Sub-evals derivados:

- C2: estrategia `by_chapter` con `chapter_size=3` produce `ceil(25/3)=9` chunks.
- C5: re-walk sobre chunk done sin `--force` → exit 1; con `--force` preserva `previous_processed_at`.
- C6: resume continúa; `.bak` presente tras `save()`; timestamps de chunks previos inmutables.

## Estructura

```
evals/chunk-loop-sample/
├── build_fixtures.py        # stdlib puro; --regen idempotente
├── run_eval.py              # 6 sub-criterios PASS/FAIL
├── fixtures/
│   ├── sdm-large.json       # 250 bloques (~250 páginas)
│   ├── sdm-cross-chunk.json # 60 bloques con 1 unidad cruzando 2 chunks
│   └── audit-loads-with-full.jsonl  # log sucio (contiene .pdf) → AP-CHK2 FAIL
├── expected/
│   ├── expected.json        # invariantes agregadas para auditoría
│   └── audit-loads-no-full.jsonl   # log limpio (sin .pdf) → AP-CHK2 PASS
└── README.md                # este archivo
```

## Uso

```bash
python3 evals/chunk-loop-sample/build_fixtures.py --regen
python3 evals/chunk-loop-sample/run_eval.py
```

Salida esperada: `PASS 6/6`.

## Dependencias

Python 3.9+ stdlib puro. Sin `jsonschema`, sin red.