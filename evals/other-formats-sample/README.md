# Other formats eval — `evals/other-formats-sample/`

Eval de F28. Verifica los 3 criterios del roadmap:

1. Cada formato del corpus produce SDM válido.
2. Las notas del orador quedan como bloques propios.
3. Las anclas temporales son resolubles.

## Cómo se corre

```bash
python3 evals/other-formats-sample/run_eval.py
```

Esperado: `3 PASS, 0 FAIL`.

## Estructura

```
evals/other-formats-sample/
├── README.md
├── build_fixtures.py             genera los 6 fixtures (epub + docx + pptx + srt + vtt + json)
├── run_eval.py                   ejecuta other_formats.py y valida los 3 criterios
├── fixtures/
│   ├── corpus-sample.epub            2 capítulos + nota
│   ├── corpus-sample.docx           Heading 1, párrafo, tabla nativa 3×3
│   ├── corpus-sample.pptx           3 slides + notas del orador
│   ├── corpus-sample.srt            4 segmentos con timestamps + muletillas
│   ├── corpus-sample.vtt            2 segmentos VTT
│   └── corpus-sample.json           3 segmentos Whisper-style
└── expected/
    ├── format-coverage.json         ≥ 1 región por formato
    ├── speaker-notes.json           ≥ 1 speaker_note con texto
    └── temporal-anchors.json        anchor_id + start + end numéricos
```

## Cobertura

| Fixture | criterion 1 | criterion 2 | criterion 3 |
|---|---|---|---|
| `corpus-sample.epub` | ✓ 6 regiones | n/a | n/a |
| `corpus-sample.docx` | ✓ 6 regiones | n/a | n/a |
| `corpus-sample.pptx` | ✓ 8 regiones | ✓ 2 speaker_note blocks | n/a |
| `corpus-sample.srt` | ✓ 4 regiones | n/a | ✓ 4 anchor_id + start + end |
| `corpus-sample.vtt` | ✓ 2 regiones | n/a | ✓ 2 anchor_id + start + end |
| `corpus-sample.json` | ✓ 3 regiones | n/a | ✓ 3 anchor_id + start + end |

## Verificación de los 3 criterios del roadmap

| Criterio | Cómo se cumple |
|---|---|
| Cada formato produce SDM válido | `_check_c1` ejecuta other_formats sobre el directorio de fixtures. Verifica que cada formato tiene `regions.json` con ≥ 1 región y cada región con `text` o `alt` no vacío. |
| Notas del orador como bloques propios | `_check_c2` verifica `class_distribution['speaker_note'] >= 1` y cada `speaker_note` tiene `text` no vacío. |
| Anclas temporales resolubles | `_check_c3` verifica que cada región de transcript tiene `anchor_id`, `start` numérico, `end` numérico, y `start < end`. |

## Regenerar los fixtures

```bash
python3 evals/other-formats-sample/build_fixtures.py
```

Dependencias: `ebooklib`, `python-docx`, `python-pptx`. Ya instalados para F28.

## Lo que **no** cubre

- PDFs (cubierto por F18/F19/F21-F27).
- RTF, ODT, HTML (cubrirían F118 con corpus completo).
- Transcripciones con WhisperX o AWS Transcribe completas (se parsean los formatos standard SRT/VTT/Whisper-JSON; formatos propietarios quedan para F118).
- Validación contra corpus reales del proyecto (F118).
