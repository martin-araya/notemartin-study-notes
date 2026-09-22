# OCR eval — `evals/ocr-sample/`

Eval de F20. Verifica los 4 criterios del roadmap:

1. La salida incluye confianza y caja por palabra.
2. Un documento con ambos idiomas se procesa sin degradación notoria.
3. El reintento se dispara y se registra.
4. La instalación de cada motor está documentada por sistema operativo.

## Cómo se corre

```bash
python3 evals/ocr-sample/run_eval.py
```

Esperado: `4 PASS, 0 FAIL` (con Tesseract instalado) o `1 PASS + 3 SKIP` (sin Tesseract; criterion 4 sigue verificable offline).

## Estructura

```
evals/ocr-sample/
├── README.md
├── build_fixtures.py                  genera los 3 fixtures (Pillow + numpy)
├── run_eval.py                        corre ocr.py y valida los 4 criterios
├── fixtures/
│   ├── ocr-fixture.png                texto inglés simple, alto contraste
│   ├── bilingual-fixture.png          texto ES + EN mezclado
│   └── low-confidence-fixture.png     texto borroso / bajo contraste
└── expected/
    ├── ocr-fixture.json               expectations de criterion 1
    ├── bilingual-fixture.json         expectations de criterion 2
    ├── low-confidence-fixture.json    expectations de criterion 3
    └── installation-docs.json         expectations de criterion 4
```

## Cobertura

| Fixture | criterion 1 | criterion 2 | criterion 3 | criterion 4 |
|---|---|---|---|---|
| `ocr-fixture.png` | ✓ 59/59 words valid | n/a | n/a | n/a |
| `bilingual-fixture.png` | n/a | ✓ 99 words, mean_conf 95.4 | n/a | n/a |
| `low-confidence-fixture.png` | n/a | n/a | ✓ 2 retries (invert + sparse_psm) | n/a |
| `ocr-engines.md` spec | n/a | n/a | n/a | ✓ macOS + Ubuntu + Windows |

## Verificación de los 4 criterios del roadmap

| Criterio | Cómo se cumple |
|---|---|
| Confianza y caja por palabra | `run_eval.py` verifica que 100% de las palabras extraídas en `ocr-fixture.png` tienen `conf >= 0` y `bbox` válido `[x, y, w, h]` con `w > 0, h > 0`. |
| Multilingüe sin degradación | `bilingual-fixture.png` se ejecuta con `--languages "spa+eng"`; ≥ 80 palabras con `mean_conf >= 0.70` (esperado ≥ 70 en escala 0–100). |
| Reintento disparado | `low-confidence-fixture.png` produce `mean_conf < 0.70` en el primer intento → 2 retries registrados en `ocr_summary.json.retries[]` (`invert` + `sparse_psm` o `alternative_engine`). |
| Instalación por SO | `ocr-engines.md` §6 contiene instrucciones para macOS (`brew install tesseract tesseract-lang`), Ubuntu (`apt install tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng`), Fedora, Arch, Windows (instalador + chocolatey + scoop) con verificación post-instalación. |

## Regenerar los fixtures

```bash
python3 evals/ocr-sample/build_fixtures.py
```

Dependencias: `Pillow`, `numpy`. Ambas ya en uso desde F17/F18/F19.

## Lo que **no** cubre

- Validación con EasyOCR real. La eval asume Tesseract como motor primario; EasyOCR se prueba solo cuando Tesseract falla.
- Tests de regresión automatizados en CI. La suite completa se materializa en F118.
- PDF como input (F19 ya rasterizó a PNG; F20 falla explícitamente si llega PDF).
- Validación con muestras reales del corpus (e.g. `02-database-internals-chapter` escaneado). F118 lo incorporará.
