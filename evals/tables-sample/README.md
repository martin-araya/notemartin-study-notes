# Tables eval — `evals/tables-sample/`

Eval de F23. Verifica los 3 criterios del roadmap:

1. Una tabla escaneada de 30+ filas se extrae completa.
2. Las celdas combinadas conservan su valor.
3. Ninguna tabla se emite truncada ni resumida.

## Cómo se corre

```bash
python3 evals/tables-sample/run_eval.py
```

Esperado: `3 PASS, 0 FAIL`.

## Estructura

```
evals/tables-sample/
├── README.md
├── build_fixtures.py             genera los 3 PDFs sintéticos (reportlab)
├── run_eval.py                   corre tables.py y valida los 3 criterios
├── fixtures/
│   ├── large-table-fixture.pdf          1 p, 35 filas × 5 columnas
│   ├── merged-cells-fixture.pdf         1 p, 5×5 con celdas combinadas (colspan)
│   └── cross-page-table-fixture.pdf     2 pp, 24 filas con header repetido
└── expected/
    ├── large-table.json                 rows=36, cols=5
    ├── merged-cells.json                min 1 merged con value preservado
    └── cross-page-table.json            merged rows=24, cross_page_continued=true
```

## Cobertura

| Fixture | criterion 1 | criterion 2 | criterion 3 |
|---|---|---|---|
| `large-table-fixture.pdf` | ✓ rows=35, cols=5, all rows valid | n/a | n/a |
| `merged-cells-fixture.pdf` | n/a | ✓ "Combined Header (colspan 3)" preserved | n/a |
| `cross-page-table-fixture.pdf` | n/a | n/a | ✓ 24 rows merged, cross_page_continued |

## Verificación de los 3 criterios del roadmap

| Criterio | Cómo se cumple |
|---|---|
| 30+ filas se extraen completas | `_criterion_1_thirty_plus_rows` ejecuta el pipeline (F18→F21→F22→F23) sobre `large-table-fixture.pdf`. Verifica `rows ≥ 35`, `cols == 5`, total rows == 36 (1 header + 35 data), todas las filas tienen exactamente 5 celdas. |
| Celdas combinadas conservan su valor | `_criterion_2_merged_cells` ejecuta sobre `merged-cells-fixture.pdf`. Verifica que `merged_cells[]` tiene ≥ 1 entrada y que su `value` contiene "Combined Header (colspan 3)". |
| Ninguna tabla truncada | `_criterion_3_no_truncation` ejecuta sobre `cross-page-table-fixture.pdf`. Verifica `rows == 24` (12+12) y `cross_page_continued == true`. |

## Regenerar los fixtures

```bash
python3 evals/tables-sample/build_fixtures.py
```

Dependencias: `reportlab`. Ya en uso desde F17.

## Lo que **no** cubre

- Detección de celdas combinadas complejas (L-shape). Solo rectangulares en v1.
- Tablas escaneadas reales (e.g. del corpus `13-internet-archive-scan-hostil`). F118 las incorporará con F20 OCR + F19 preprocess.
- Tablas sin bordes (líneas no son necesarias en v1, pero las detecciones funcionan solo si hay texto en cada celda).
- Validación contra ground truth exhaustivo (corpus completo). F118 la ampliará.
- Tests de regresión automatizados en CI. La suite completa se materializa en F118.
