# `references/14-operation/`

Catálogo operativo de modos de fallo y contratos cross-fase para que la
ejecución no quede a medias ni duplique contenido.

## Orden de lectura

Cargar antes de implementar cualquier orquestador de larga duración
(modo libro, modo chunk, dedup, consolidación, incremental). En F118
evals para verificar las reglas duras R-INT-* y R-REP-*.

## Estado actual

- [`failure-modes.md`](failure-modes.md) `[existente]` — F116: catálogo
  cerrado de 7 modos de fallo (OCR fallido / fuente ilegible / contexto
  agotado / API caída / validador en rojo repetido / conflicto
  irresoluble / interrupción), contratos de interrupción y reproceso
  (R-INT-1..3 / R-REP-1..3), regla de extensión cerrada.