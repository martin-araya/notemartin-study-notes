# `evals/make-figure-sample/` — Verificador de la Fase 70

Eval battery para `skill/notemartin-study-notes/scripts/render/make_figure.py` (Fase 70). Verifica los **3 criterios de aceptación de la fase** más 2 criterios transversales:

| # | Criterio | Cubre |
|---|---|---|
| C1 | Las 6 figuras (bar, line, heatmap, confusion_matrix, distribution, before_after) se generan en light y dark | Criterio 1 de F70 |
| C2 | La paleta Okabe-Ito pasa daltonismo con ΔE CIEL76 ≥ 20 | Criterio 2 de F70 |
| C3 | Toda serie tiene `source_refs` no vacío; spec inválido dispara error | Criterio 3 de F70 |
| C4 | Alt text + reading phrase no vacíos en cada manifest | Detalle F70 |
| C5 | Ejes neutros (grises) no usan colores Okabe-Ito | Detalle F70 (accesibilidad) |

## Cómo correr

```bash
python evals/make-figure-sample/run_eval.py --regen
```

Salida esperada:

```
============================================================
Fase 70 — Figuras de datos
============================================================
  ✓ C1-renders (6/6 light + 6/6 dark)
  ✓ C2-colorblind-safe (ΔE_min=... ≥ 20)
  ✓ C3-source-refs (6 specs, todas con source_refs)
  ✓ C3b-invalid-rejected (exit=1)
  ✓ C4-alt-text (6 figuras con alt + reading)
  ✓ C5-neutral-axes (ejes con grises neutros)
============================================================
PASS 5/5
```

## Estructura

```
evals/make-figure-sample/
├── README.md
├── build_fixtures.py        # genera 6 specs + 1 inválida
├── run_eval.py              # verificador principal (5 criterios)
└── fixtures/
    ├── bar.json
    ├── line.json
    ├── heatmap.json
    ├── confusion_matrix.json
    ├── distribution.json
    ├── before_after.json
    └── missing-refs.json    # spec inválida (sin source_refs)
```
