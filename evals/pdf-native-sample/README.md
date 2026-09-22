# PDF native eval — `evals/pdf-native-sample/`

Eval de F18. Verifica los 3 criterios del roadmap:

1. Headings detectados (tipografía) coinciden con el índice del PDF en ≥ 95% de los casos del corpus.
2. Boilerplate se elimina sin borrar contenido real.
3. Cada fragmento conserva página y coordenadas.

## Cómo se corre

```bash
python3 evals/pdf-native-sample/run_eval.py
```

Esperado: `7 PASS, 0 FAIL`.

## Estructura

```
evals/pdf-native-sample/
├── README.md
├── build_fixtures.py                  genera los 2 PDFs sintéticos (reportlab + pypdf)
├── run_eval.py                        corre pdf_native.py y valida los 3 criterios
├── fixtures/
│   ├── boilerplate-test.pdf           10 pp con header/footer repetidos + cuerpo único
│   └── outline-test.pdf               5 pp con PDF outline inyectado (5 entries)
└── expected/
    ├── boilerplate-test.json          expectativas de criterion 2
    ├── outline-test.json              expectativas de criterion 1 (5 entries)
    └── corpus.json                    expectativas para 04, 12
```

## Cobertura

| Fuente | criterion 1 | criterion 2 | criterion 3 |
|---|---|---|---|
| `fixtures/outline-test.pdf` | ✓ 5/5 entries | n/a | ✓ |
| `evals/corpus/04-arxiv-two-column/sample.pdf` | ✓ 11/11 | n/a | ✓ |
| `evals/corpus/12-arxiv-formulas/sample.pdf` | ✓ 19/20 (95.0%) | n/a | ✓ |
| `fixtures/boilerplate-test.pdf` | n/a | ✓ | ✓ |

Los PDFs nativos `pure_scan` (02, 09, 13) no se evalúan en F18: la extracción nativa no aplica, F19+F20 los cubren.

## Verificación de los 3 criterios del roadmap

| Criterio | Cómo se cumple en este eval |
|---|---|
| Headings coinciden con el índice en ≥ 95% | `run_eval.py` mide el ratio `covered / total outline entries` para `outline-test`, `04`, `12`. 7/7 PASS. |
| Boilerplate se elimina sin borrar contenido real | `boilerplate-test.pdf` (10 pp) verifica que header "Confidential Draft v1" + footer "Internal Distribution Only" quedan en `boilerplate_summary.*_texts` y que los ≥ 7 fragmentos de cuerpo por página están sin flag boilerplate. |
| Cada fragmento conserva página y coordenadas | `run_eval.py` itera todos los fragments de todos los PDFs y verifica `page` (int ≥ 1) + `bbox` (`[x0,y0,x1,y1]` con `x1 > x0` y `y1 > y0`). 100% PASS en 2122 fragments. |

## Regenerar los fixtures

```bash
python3 evals/pdf-native-sample/build_fixtures.py
```

Dependencias: `reportlab` (construcción de PDFs con texto), `pypdf` (inyección del outline en `outline-test.pdf`). Ambos ya en uso desde F17.

## Lo que **no** cubre

- Validación material contra PDFs escaneados (F19+F20 los cubre; F18 los salta con warning si vienen vía `--plan`).
- Extracción con coordenadas sub-pixel (p.ej. precisión 0.001 pt). F18 aproxima el ancho del texto con `len(text) * font_size * 0.5`.
- Round-trip IR → fragments (no aplica; fragments es output, no IR).
- Tests de regresión automatizados en CI. La suite completa se materializa en F118.
