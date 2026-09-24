# Regions eval — `evals/regions-sample/`

Eval de F22. Verifica los 3 criterios del roadmap:

1. Distingue código de texto corrido con precisión alta en el corpus.
2. Las cajas editoriales de los libros se detectan como tales.
3. Toda región ambigua queda marcada.

## Cómo se corre

```bash
python3 evals/regions-sample/run_eval.py
```

Esperado: `3 PASS, 0 FAIL`.

## Estructura

```
evals/regions-sample/
├── README.md
├── build_fixtures.py             genera los 3 PDFs sintéticos (reportlab + Menlo.ttc)
├── run_eval.py                   corre regions.py y valida los 3 criterios
├── fixtures/
│   ├── code-vs-text-fixture.pdf       2 pp, izquierda texto normal, derecha código monoespaciado
│   ├── editorial-boxes-fixture.pdf    2 pp, 3 cajas Note/Tip/Warning por página
│   └── ambiguous-region-fixture.pdf   1 p, región con señales conflictivas
└── expected/
    ├── code-vs-text.json             precision ≥ 0.85, recall ≥ 0.85, F1 ≥ 0.85
    ├── editorial-boxes.json           min editorial_note count ≥ 10
    └── ambiguous-region.json         semantic_class=null, ambiguity=true, alternatives ≥ 2
```

## Cobertura

| Fixture | criterion 1 | criterion 2 | criterion 3 |
|---|---|---|---|
| `code-vs-text-fixture.pdf` | ✓ precision=1.00, recall=1.00, F1=1.00 | n/a | n/a |
| `editorial-boxes-fixture.pdf` | n/a | ✓ 13 editorial_note regions | n/a |
| `ambiguous-region-fixture.pdf` | n/a | n/a | ✓ semantic_class=null, 4 distinct alternatives |

## Verificación de los 3 criterios del roadmap

| Criterio | Cómo se cumple |
|---|---|
| Distingue código de texto corrido con precisión alta | `_criterion_1_code_vs_text` usa ground truth posicional: columna derecha (x_center ≥ 300) → code; columna izquierda arriba (y > 600) → heading; columna izquierda abajo → text. Mide TP/FP/FN/TN sobre las 9 regiones de la fixture. |
| Cajas editoriales detectadas como tales | `_criterion_2_editorial_boxes` ejecuta el pipeline sobre `editorial-boxes-fixture.pdf` y cuenta regiones con `semantic_class = "editorial_note"`. Umbral: ≥ 10. |
| Toda región ambigua marcada | `_criterion_3_ambiguity` ejecuta el pipeline sobre `ambiguous-region-fixture.pdf` y verifica que la región con señales conflictivas tenga `semantic_class = null`, `ambiguity = true` y `alternative_classes` con ≥ 2 clases distintas. |

## Regenerar los fixtures

```bash
python3 evals/regions-sample/build_fixtures.py
```

Dependencias: `reportlab` (Menlo.ttc viene con macOS; en otras plataformas ajustar `MONO_PATH`).

## Lo que **no** cubre

- Validación con PDFs académicos reales del corpus. La eval opera sobre fixtures sintéticos con ground truth posicional. F118 la ampliará al corpus completo.
- Detección de fórmulas tipografiadas como `formula` con confianza alta. El fixture `ambiguous-region` cubre el caso conflictivo.
- Sub-clases de `editorial_note` (box vs inline). El script detecta pero el eval no las verifica explícitamente.
- Tests de regresión automatizados en CI. La suite completa se materializa en F118.
