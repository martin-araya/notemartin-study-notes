# `evals/book-index-sample/` — F110 Índice de obra

Eval battery para la Fase 110. Verifica los **3 criterios del ROADMAP**:

| Criterio ROADMAP | Sub-eval | Qué verifica |
|---|---|---|
| Refleja el estado real de cobertura por capítulo | C1 | `book-index.md` tiene sección `## Cobertura por capítulo` con tabla; 3 capítulos (2 done + 1 pending); % done correcto |
| Incluye grafo renderizado | C2 | Sección `## Grafo de dependencias` con bloque ` ```mermaid ` válido (4 nodos + 3 aristas de `concept-graph.json`); IDX-R5 verificado |
| Enlaza glosario, cheatsheets y prácticas | C3 | Secciones 6/7/8 tienen `[[note:id]]` con descripción; los IDs existen en IRs (IDX-R4); `book_index.py check` pasa |

## Estructura

```
evals/book-index-sample/
├── build_fixtures.py        # stdlib puro; --regen idempotente
├── run_eval.py              # 3 sub-criterios PASS/FAIL
├── fixtures/
│   └── workdir/
│       ├── ir/              # 5 IRs (1 concept + 1 cheatsheet + 1 practice + 1 glossary-term + 1 procedure)
│       ├── knowledge/glossary.json   # 3 términos canónicos
│       ├── concept-graph.json        # 4 nodos + 3 aristas
│       ├── book-state.json           # F106: 3 capítulos (2 done + 1 pending)
│       ├── book_map.mmd              # F106: Mermaid graph LR
│       └── reports/                  # 3 F109 reports (cheatsheets / study-paths / link-debt)
├── expected/
│   └── expected.json        # invariantes agregadas para auditoría
└── README.md                # este archivo
```

## Uso

```bash
python3 evals/book-index-sample/build_fixtures.py --regen
python3 evals/book-index-sample/run_eval.py
```

Salida esperada: `PASS 3/3`.

## Dependencias

Python 3.9+ stdlib puro. Sin `jsonschema`, sin red.