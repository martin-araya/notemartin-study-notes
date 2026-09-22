# `references/01-ingest/`

Reglas de ingesta: triaje, OCR, layout, formatos no PDF.

## Orden de lectura

Cargar antes de la primera ingesta de una fuente (L0). Cargar también durante la revisión humana de regiones dudosas.

## Estado actual

Estado de los archivos:

- `triage.md` ✅ F17
- `ocr-engines.md` `[pendiente F20]`
- `code-ocr.md` `[pendiente F25]`
- `confidence.md` `[pendiente F26]`

## Quién lee / quién produce

| Archivo | Lee | Produce |
|---|---|---|
| `triage.md` | agente al inicio de cada ingesta; `scripts/ingest/triage.py` | F17 |
| `ocr-engines.md` | F20, agente al elegir motor | F20 |
| `code-ocr.md` | F25, agente en validación sintáctica | F25 |
| `confidence.md` | F26, humano en revisión | F26 |
