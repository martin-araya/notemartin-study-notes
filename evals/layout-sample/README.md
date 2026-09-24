# Layout eval — `evals/layout-sample/`

Eval de F21. Verifica los 3 criterios del roadmap:

1. Un documento a dos columnas se reconstruye en orden correcto.
2. Una tabla que cruza páginas se reunifica.
3. La verificación detecta un orden roto inyectado a propósito.

## Cómo se corre

```bash
python3 evals/layout-sample/run_eval.py
```

Esperado: `3 PASS, 0 FAIL`.

## Estructura

```
evals/layout-sample/
├── README.md
├── build_fixtures.py                  genera los 3 PDFs sintéticos (reportlab)
├── run_eval.py                        corre layout.py y valida los 3 criterios
├── fixtures/
│   ├── two-column-fixture.pdf         2 pp, 2 columnas con 3 párrafos cada una
│   ├── cross-page-table.pdf           2 pp, tabla de 4 cols × 12 filas (6+6)
│   └── broken-order-fixture.pdf       2 pp, 2 columnas (inyección sintética de orden roto)
└── expected/
    ├── two-column.json                expectations de criterion 1
    ├── cross-page-table.json          expectations de criterion 2
    └── broken-order.json              expectations de criterion 3 (synthetic)
```

## Cobertura

| Fixture | criterion 1 | criterion 2 | criterion 3 |
|---|---|---|---|
| `two-column-fixture.pdf` | ✓ cols=2, valid | n/a | n/a |
| `cross-page-table.pdf` | n/a | ✓ 1 cross_page_link type=table | n/a |
| Synthetic broken order | n/a | n/a | ✓ verify_reading_order detecta inversion |

## Verificación de los 3 criterios del roadmap

| Criterio | Cómo se cumple |
|---|---|
| Dos columnas en orden correcto | `_run_layout` sobre `two-column-fixture.pdf` produce `pages[0].column_count=2` y `pages[1].column_count=2` con `reading_order_valid=True` en ambas. |
| Tabla cross-page reunificada | `_run_layout` sobre `cross-page-table.pdf` produce `cross_page_links[]` con ≥ 1 entrada `type=table` (heurística: cualquier ventana de 6 palabras consecutivas con `|y_max - y_min| < 3 line heights` y ≥ 3 X distintos). |
| Verificación detecta orden roto | `_criterion_3_broken_order` llama directamente a `layout.verify_reading_order` con un input sintético de 2 regiones (`column_index=0`, `column_index=1`) emitidas en orden invertido (`["r002", "r001"]`). Verifica que retorna `valid=False, inconsistencies[0].kind=column_order_inverted`. Verifica también que el orden correcto (`["r001", "r002"]`) produce `valid=True` (no falsos positivos). |

## Regenerar los fixtures

```bash
python3 evals/layout-sample/build_fixtures.py
```

Dependencias: `reportlab`. Ya en uso desde F17/F19.

## Lo que **no** cubre

- Validación con PDFs académicos reales del corpus. La eval opera sobre fixtures sintéticos con estructura controlada. F118 lo amplía al corpus completo.
- Detección de curvas en línea base de texto (no aplica a los criterios).
- Detección de figuras a página completa con captions. Cubierto parcialmente.
- Tests de regresión automatizados en CI. La suite completa se materializa en F118.
