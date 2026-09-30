# `evals/dedup-sample/` — F108 Deduplicación y fusión

Eval battery para la Fase 108. Verifica los **3 criterios del ROADMAP**:

| Criterio ROADMAP | Sub-eval | Qué verifica |
|---|---|---|
| Una fusión no pierde ninguna unidad de las notas originales | C1 | `apply merge` sobre par A+B; DEDUP-R1 (`merged_refs ⊇ a.source_refs ∪ b.source_refs`) + DEDUP-R3 (`frontmatter.aliases` de C contiene note-a y note-b) |
| Los enlaces entrantes siguen funcionando | C2 | Tras merge A+B→C: 0 old links en IRs externos + `manifest.json::link_debt[]` tiene 2 entradas `redirected` (DEDUP-R2 + DEDUP-R4) |
| El detector encuentra duplicados inyectados a propósito | C3 | `detect scan` sobre fixture de 4 pares ground-truth: **recall = 4/4** (≥ 80%) |

**Sub-eval derivado**: par 5 (`concurrency ↔ mvcc-only`) es `specialize` candidate (similarity 0.48, sin match canónico/alias); el detector lo emite con `suggested_action: "specialize"`.

## Estructura

```
evals/dedup-sample/
├── build_fixtures.py        # stdlib puro; --regen idempotente
├── run_eval.py              # 3 sub-criterios PASS/FAIL
├── fixtures/
│   ├── notes/               # 12 notas (4 pares inyectados + 2 extra + 4 notas base)
│   └── glossary.json        # término canónico `mvcc` con 2 aliases
├── expected/
│   └── candidates.json      # 4 pares ground-truth para `verify`
└── README.md                # este archivo
```

## Uso

```bash
python3 evals/dedup-sample/build_fixtures.py --regen
python3 evals/dedup-sample/run_eval.py
```

Salida esperada: `PASS 3/3`.

## Dependencias

Python 3.9+ stdlib puro. Sin `jsonschema`, sin red.