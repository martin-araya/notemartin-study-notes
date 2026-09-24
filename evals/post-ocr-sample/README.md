# Post-OCR eval — `evals/post-ocr-sample/`

Eval de F27. Verifica los 3 criterios del roadmap:

1. Toda corrección es rastreable a una regla o entrada de diccionario.
2. Código y tablas quedan intactos.
3. Cualquier corrección individual se puede revertir.

## Cómo se corre

```bash
python3 evals/post-ocr-sample/run_eval.py
```

Esperado: `3 PASS, 0 FAIL`.

## Estructura

```
evals/post-ocr-sample/
├── README.md
├── build_fixtures.py             genera los 4 PDFs sintéticos (reportlab + Courier)
├── run_eval.py                   ejecuta post_ocr.py y valida los 3 criterios
├── fixtures/
│   ├── prose-fixture.pdf                prosa con R001/R002/R005 + D001
│   ├── code-fixture.pdf                 Python code (NO debe modificarse)
│   ├── table-fixture.pdf                tabla 4×4 (NO debe modificarse)
│   └── revert-fixture.pdf               prosa activable para revertir
├── dictionary.yaml                    5 entradas (PostgreSQL, JavaScript, etc.)
└── expected/
    ├── prose.json                       ≥ 1 corrección con source
    ├── code-table.json                  code y table intactos
    └── revert.json                      revert restaura text original
```

## Cobertura

| Fixture | criterion 1 | criterion 2 | criterion 3 |
|---|---|---|---|
| `prose-fixture.pdf` | ✓ corrección rastreable | n/a | n/a |
| `code-fixture.pdf` + `table-fixture.pdf` | n/a | ✓ skipped=True, corrected==original | n/a |
| `revert-fixture.pdf` | n/a | n/a | ✓ `--revert c-NNNN` restaura text |

## Verificación de los 3 criterios del roadmap

| Criterio | Cómo se cumple |
|---|---|
| Correcciones rastreables | `_criterion_1_corrections_traceable` ejecuta post_ocr sobre `prose-fixture.pdf`. Verifica que cada corrección tiene `correction_id`, `char_pos`, `char_end`, `original`, `corrected`, `applied_at`, y `source` ∈ {`rule_id`, `dict_id`}. |
| Código y tablas intactos | `_criterion_2_code_table_intact` ejecuta post_ocr sobre `code-fixture.pdf` y `table-fixture.pdf`. Verifica `corrected_text == original_text` y `skipped: true` para cada región code/table. |
| Revertibilidad | `_criterion_3_revertible` ejecuta post_ocr, captura el primer `correction_id`, re-invoca con `--revert <correction_id>`, y verifica que `corrected_text == original_text`. |

## Regenerar los fixtures

```bash
python3 evals/post-ocr-sample/build_fixtures.py
```

Dependencias: `reportlab`. Ya en uso desde F17.

`run_eval.py` construye los `ingest/` trees sintéticos automáticamente; no requiere fixtures externas.

## Lo que **no** cubre

- Correcciones con modelos de lenguaje (criterio 1 prohíbe explícitamente ML).
- Modificación de código o tablas (criterio 2 es regla dura).
- Validación contra corpus reales del proyecto (F118 incorpora corpus completo).
- Re-invocación con `--revert-all` (el eval verifica revert individual; --revert-all sigue la misma lógica).
