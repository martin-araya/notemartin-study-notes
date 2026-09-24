# Code OCR eval — `evals/code-ocr-sample/`

Eval de F25. Verifica los 4 criterios del roadmap:

1. La indentación del código escaneado se conserva exactamente.
2. Cada corrección sintáctica queda registrada individualmente.
3. Ningún carácter se corrige por plausibilidad.
4. Los bloques dudosos no pasan en silencio.

## Cómo se corre

```bash
python3 evals/code-ocr-sample/run_eval.py
```

Esperado: `4 PASS, 0 FAIL`.

## Estructura

```
evals/code-ocr-sample/
├── README.md
├── build_fixtures.py             genera los 4 PDFs sintéticos (reportlab + Courier)
├── run_eval.py                   corre code_ocr.py y valida los 4 criterios
├── fixtures/
│   ├── clean-code-fixture.pdf         Python con indentación por tabs (criterio 1)
│   ├── confusion-fixture.pdf          Python con paréntesis faltante (criterio 2)
│   ├── plausibility-fixture.pdf       Python con l/1/I, 0/O en identificadores (criterio 3)
│   └── low-confidence-fixture.pdf     Python con identificadores ambiguos (criterio 4)
└── expected/
    ├── clean-code.json                 byte-exact, 0 correcciones
    ├── confusion.json                  ≥ 1 corrección con 4 campos
    ├── plausibility.json               0 correcciones, ≥ 1 low_confidence
    └── low-confidence.json             low_confidence: true con reason no vacío
```

## Cobertura

| Fixture | criterion 1 | criterion 2 | criterion 3 | criterion 4 |
|---|---|---|---|---|
| `clean-code-fixture.pdf` | ✓ text byte-exact, 0 corrections | n/a | n/a | n/a |
| `confusion-fixture.pdf` | n/a | ✓ 1 correction registrada | n/a | n/a |
| `plausibility-fixture.pdf` | n/a | n/a | ✓ 0 corrections, low_confidence=true | n/a |
| `low-confidence-fixture.pdf` | n/a | n/a | n/a | ✓ low_confidence con reason |

## Verificación de los 4 criterios del roadmap

| Criterio | Cómo se cumple |
|---|---|
| Indentación preservada | `_criterion_1_indent_preservation` ejecuta el pipeline (F18→F21→F22→F25) sobre `clean-code-fixture.pdf`. Construye el texto esperado usando solo palabras monoespaciadas del fragments.json (mismo algoritmo que `reconstruct_text`). Compara carácter por carácter con los bloques de código emitidos por F25 (ordenados por y descendente). Verifica que `corrections_total == 0` (F25 no modificó nada). |
| Correcciones registradas | `_criterion_2_corrections_registered` ejecuta sobre `confusion-fixture.pdf`. Verifica `corrections[]` tiene ≥ 1 entrada. Cada corrección debe tener `char_pos` (no null), `corrected` (no vacío), `reason` (no vacío), `original` (puede estar vacío para inserciones). |
| Sin plausibilidad | `_criterion_3_no_plausibility` ejecuta sobre `plausibility-fixture.pdf`. Verifica `corrections_total == 0` (ningún carácter corregido por plausibilidad) y `low_confidence_count ≥ 1` (el bloque ambiguo se marca como low_confidence). |
| Sin bloques silenciosos | `_criterion_4_no_silent_blocks` ejecuta sobre `low-confidence-fixture.pdf`. Verifica que `low_confidence_count ≥ 1` y que cada bloque low_confidence tenga `low_confidence_reason` no vacío. |

## Regenerar los fixtures

```bash
python3 evals/code-ocr-sample/build_fixtures.py
```

Dependencias: `reportlab`. Ya en uso desde F17.

## Lo que **no** cubre

- Reconocimiento de código desde imágenes escaneadas (sin pix2tex). F26/F118 podrían incorporarlo.
- Validación de sintaxis JS/Bash/SQL con parsers reales. F25 usa bracket matching para esos lenguajes.
- Conversión de tabs a espacios o re-formateo. F25 NUNCA re-formatea.
- Tests de regresión automatizados en CI. La suite completa se materializa en F118.
