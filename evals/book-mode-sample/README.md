# `evals/book-mode-sample/` — F106 Modo obra completa

Eval battery para la Fase 106. Verifica los **3 criterios del ROADMAP**:

| Criterio ROADMAP | Sub-eval | Qué verifica |
|---|---|---|
| El mapa se genera antes del primer capítulo | C1 | BM-R1: `init` exige `book_map.json` antes de permitir `process` |
| Un concepto del capítulo 2 no se redefine en el 9 | C2 | AP-BM1 detecta redefinición textual en ch09 (sin `[[note:mvcc]]`); NO detecta ch03 (con link) |
| Se detiene y reanuda en cualquier capítulo | C3 | `resume` continúa desde `next_chapter` sin re-procesar done; `started_at`/`processed_at` inmutables |

Sub-evals derivados:

- C4: consolidación N=5 se dispara tras ch05; re-ejecutar `consolidate` es idempotente.
- C5: escritura atómica — `.bak` se crea tras cada `save()` (BM-R2 + AP-BM3).
- C6: AP-BM2 (mapa regenerado con `generated_at > ch1.started_at`), AP-BM3 (`.bak` ausente), AP-BM4 (`--force` preserva `previous_processed_at`).

## Estructura

```
evals/book-mode-sample/
├── build_fixtures.py        # stdlib puro; --regen idempotente
├── run_eval.py              # 6 sub-criterios PASS/FAIL
├── fixtures/
│   ├── sdm-book.json        # SDM sintético (11 capítulos: 1 prefacio + 10)
│   └── notes/               # ch02/mvcc.md (canónico), ch03 (linkea), ch09 (redefine)
├── expected/
│   └── expected.json        # invariantes agregadas para auditoría
└── README.md                # este archivo
```

## Uso

```bash
python3 evals/book-mode-sample/build_fixtures.py --regen
python3 evals/book-mode-sample/run_eval.py
```

Salida esperada: `PASS 6/6`.

## Dependencias

Python 3.9+ stdlib puro. Sin `jsonschema`, sin red.