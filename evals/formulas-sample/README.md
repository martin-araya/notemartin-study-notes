# Formulas eval — `evals/formulas-sample/`

Eval de F24. Verifica los 3 criterios del roadmap:

1. Todo LaTeX emitido compila.
2. Una fórmula no reconocida se conserva como imagen marcada.
3. Las referencias a ecuaciones numeradas siguen resolviendo.

## Cómo se corre

```bash
python3 evals/formulas-sample/run_eval.py
```

Esperado: `3 PASS, 0 FAIL`.

## Estructura

```
evals/formulas-sample/
├── README.md
├── build_fixtures.py                  genera los 3 PDFs sintéticos (reportlab + Courier)
├── run_eval.py                        corre formulas.py y valida los 3 criterios
├── fixtures/
│   ├── latex-fixture.pdf                    1 p, 4 fórmulas bloque + 2 inline válidas
│   ├── pending-fixture.pdf                  1 p, 1 fórmula inválida (\fract{1}{2})
│   └── numbered-equations-fixture.pdf       2 pp, 2 fórmulas numeradas (1.1)(1.2)(1.3)
└── expected/
    ├── latex.json                           min 4 compiladas
    ├── pending.json                         1 pending con image_path o bbox
    └── numbered.json                        equation_index con (1.1)(1.2)(1.3)
```

## Cobertura

| Fixture | criterion 1 | criterion 2 | criterion 3 |
|---|---|---|---|
| `latex-fixture.pdf` | ✓ 5 formulas compiladas | n/a | n/a |
| `pending-fixture.pdf` | n/a | ✓ 1 formula pending con image_path | n/a |
| `numbered-equations-fixture.pdf` | n/a | n/a | ✓ equation_index con (1.1)(1.2)(1.3) |

## Verificación de los 3 criterios del roadmap

| Criterio | Cómo se cumple |
|---|---|
| LaTeX compila | `_criterion_1_latex_compiles` ejecuta el pipeline (F18→F21→F22→F24) sobre `latex-fixture.pdf`. Verifica `compiled_count ≥ 4`, `pending_count = 0`, y que ninguna fórmula tenga `compile_errors` no vacío. |
| Pending fallback | `_criterion_2_pending` ejecuta sobre `pending-fixture.pdf` con `--images-dir` (imágenes sintéticas blancas). Verifica `pending_count ≥ 1` y que cada pending tenga `image_path` o `bbox` referencial. |
| Numeración preservada | `_criterion_3_numbered` ejecuta sobre `numbered-equations-fixture.pdf`. Verifica `equation_index ≥ 3` entradas y que `(1.1)`, `(1.2)`, `(1.3)` aparezcan. |

## Regenerar los fixtures

```bash
python3 evals/formulas-sample/build_fixtures.py
```

Dependencias: `reportlab`. Ya en uso desde F17.

## Lo que **no** cubre

- Reconocimiento de fórmulas LaTeX desde imágenes escaneadas (sin pix2tex / Nougat). F26/F118 podrían incorporarlo.
- Compilación con `pdflatex` real. F24 usa un verificador regex puro Python.
- Tablas con fórmulas en celdas. Queda para F23 (que se ocupa de tablas) + F24.
- Tests de regresión automatizados en CI. La suite completa se materializa en F118.
