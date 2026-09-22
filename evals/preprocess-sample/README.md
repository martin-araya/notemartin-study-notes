# Preprocess eval — `evals/preprocess-sample/`

Eval de F19. Verifica los 3 criterios del roadmap:

1. La fuente hostil mejora su tasa de acierto de OCR de forma medible.
2. Las páginas rotadas se corrigen automáticamente.
3. La imagen original nunca se destruye.

## Cómo se corre

```bash
python3 evals/preprocess-sample/run_eval.py
```

Esperado: `4 PASS, 0 FAIL` (3 criterios + auxiliar de blank detection).

## Estructura

```
evals/preprocess-sample/
├── README.md
├── build_fixtures.py                  genera los 3 fixtures (reportlab + Pillow + numpy)
├── run_eval.py                        corre preprocess.py y valida los 3 criterios
├── fixtures/
│   ├── rotated-test.pdf               3 pp con rotaciones 0°, +3°, -5° (c.rotate)
│   ├── blank-test.pdf                 5 pp: 2 con contenido, 3 en blanco
│   └── hostile-scan.png               PNG con rotación 3° + ruido + sombra
└── expected/
    ├── rotated-test.json              rotaciones esperadas: 0.0, 3.0, 5.0 (|.|)
    ├── blank-test.json                is_blank esperado por página
    ├── hostile-scan.json              mejora esperada: ≥ 15% (1.15x)
    └── preservation.json              lista de archivos cuyo sha256 no debe cambiar
```

## Cobertura

| Fixture | criterion 1 | criterion 2 | criterion 3 |
|---|---|---|---|
| `hostile-scan.png` | ✓ 2.86x mejora (≥ 1.15x) | n/a | ✓ |
| `rotated-test.pdf` | n/a | ✓ \|det\|=0°, 3°, 5° tol ±0.5° | ✓ |
| `blank-test.pdf` | n/a | n/a | ✓ + blank detection auxiliar |
| `hostile-scan.png`, `rotated-test.pdf`, `blank-test.pdf` | n/a | n/a | ✓ sha256 unchanged |

## Verificación de los 3 criterios del roadmap

| Criterio | Cómo se cumple |
|---|---|
| La fuente hostil mejora su tasa de acierto de OCR | `run_eval.py` mide `useful_rows` (filas con std dev > 30) en el original y el procesado. El threshold es 1.15x; el fixture da 2.86x. Sin Tesseract instalado, usa este proxy. |
| Las páginas rotadas se corrigen automáticamente | `run_eval.py` ejecuta preprocess.py sobre `rotated-test.pdf` y verifica `|rotation_detected_deg|` contra los valores esperados (0°, 3°, 5°), con tolerancia ± 0.5° y `rotation_applied: true` para las 2 páginas no triviales. |
| La imagen original nunca se destruye | `run_eval.py` compara el hash sha256 del input antes y después. Verifica los 3 fixtures. |

## Regenerar los fixtures

```bash
python3 evals/preprocess-sample/build_fixtures.py
```

Dependencias: `reportlab` (PDFs), `Pillow` (PNG + rotación), `numpy` (ruido). Todas ya en uso desde F17/F18.

## Lo que **no** cubre

- Validación con Tesseract real. La eval usa un proxy (`useful_rows`) cuando Tesseract no está instalado. Si Tesseract está disponible, se puede extender `run_eval.py` para medir caracteres OCR extraídos.
- Páginas con curvatura > 6° (fixture solo cubre rotación y blank; curvatura queda para casos reales del corpus).
- PDF > 200 páginas. F30 (`ingest_check.py`) cierra ese extremo.
- Tests de regresión automatizados en CI. La suite completa se materializa en F118.
