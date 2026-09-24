# Review report eval — `evals/review-sample/`

Eval de F26. Verifica los 3 criterios del roadmap:

1. El reporte muestra imagen y texto lado a lado.
2. Los umbrales difieren por tipo y están justificados.
3. Una fuente muy degradada no avanza sin confirmación.

## Cómo se corre

```bash
python3 evals/review-sample/run_eval.py
```

Esperado: `3 PASS, 0 FAIL`.

## Estructura

```
evals/review-sample/
├── README.md
├── build_fixtures.py             genera los 2 PDFs sintéticos (reportlab + Courier)
├── run_eval.py                   ejecuta review_report.py y valida los 3 criterios
├── fixtures/
│   ├── degraded-source-fixture.pdf      1 p, code + table + formula + text mixed
│   └── blocked-source-fixture.pdf       1 p, 4 critical regions low_confidence → BLOCK
└── expected/
    ├── degraded.json                    HTML contains <img> and <pre> side by side
    ├── blocked.json                     exit=1, summary.blocked=true
    └── thresholds.json                  per-class thresholds documented
```

## Cobertura

| Fixture | criterion 1 | criterion 2 | criterion 3 |
|---|---|---|---|
| `degraded-source-fixture.pdf` | ✓ <img> + <pre class="region-text"> in same row | ✓ per-type thresholds documented | n/a |
| `blocked-source-fixture.pdf` | n/a | n/a | ✓ exit=1 with summary.blocked=true |

## Verificación de los 3 criterios del roadmap

| Criterio | Cómo se cumple |
|---|---|
| Imagen y texto lado a lado | `_criterion_1_image_text_side_by_side` ejecuta review_report sobre `degraded-source-fixture.pdf`. Construye un ingest/ tree con 4 regiones (code low, table ok, formula ok, text ok) y crea una imagen sintética para recortes. Verifica que el HTML contiene `<img>`, `<pre class="region-text">`, y `<tr class="region-row">`. |
| Umbrales por tipo | `_criterion_2_thresholds_per_type` ejecuta review_report y verifica `summary.class_thresholds` contiene las 15 clases oficiales con umbrales distintos. Verifica además `code ≥ text` (code estricto, text relajado). |
| Bloqueo | `_criterion_3_blocking` ejecuta review_report sobre `blocked-source-fixture.pdf` con 4 regiones críticas (code, table, formula, syntax_diagram) todas low_confidence. Verifica `exit_code == 1` y `summary.blocked == true` y `blocked_reason == "too_many_low_confidence_critical_regions"`. |

## Regenerar los fixtures

```bash
python3 evals/review-sample/build_fixtures.py
```

Dependencias: `reportlab` (PDFs) + `Pillow` (imágenes sintéticas). Ya en uso desde F17/F19.

`run_eval.py` construye los `ingest/` trees sintéticos automáticamente; no requiere fixtures externas.

## Lo que **no** cubre

- Reporte interactivo con servidor HTTP. El HTML es self-contained; el reviewer lo abre localmente.
- Aplicación automática de correcciones. El reviewer edita y emite `corrections.json`; F26 propaga en re-invocación.
- Detección de imágenes faltantes en recortes (F26 emite warning; el HTML muestra `(crop unavailable)`).
- Validación contra corpus reales. F26 opera sobre los outputs sintéticos de F22/F23/F24/F25. F118 incorpora corpus completo.
