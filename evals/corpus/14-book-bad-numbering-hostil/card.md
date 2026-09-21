# 14 — Book with inconsistent section numbering (HOSTIL)

## Identificador
`14-book-bad-numbering-hostil`

## Título y autor / fuente
Libro técnico en PDF donde la numeración de las secciones impresas no coincide con el índice declarado. Sustituto concreto: cualquier PDF técnico abierto con esta característica (p. ej. captura de libro escaneado donde el TOC dice "Chapter 4" pero el cuerpo dice "Chapter 5", o donde faltan números intermedios).

## URL canónica
No fijada. Se busca en Internet Archive o en repositorios abiertos.

## Licencia
Variable; se elige dominio público o CC-BY.

## Formato
PDF (nativo o escaneado según disponibilidad; se prefiere nativo para que la hostil sea **solo** la numeración inconsistente, no la calidad del escaneo).

## Páginas
~10 (muestra representativa).

## Densidad
- Tablas: media.
- Código: media.
- Figuras: media.

## Idioma
inglés.

## Versión del producto
no aplica.

## Presencia
- `tablas`: sí
- `codigo`: sí
- `formulas`: sí (posible)
- `figuras`: sí
- `diagramas_sintaxis`: no
- `cajas_editoriales`: sí

## Hostilidad
**`numeracion_inconsistente`** — el PDF tiene:
- Capítulos numerados con saltos (e.g. 1, 2, 4, 5 — falta el 3).
- Capítulos duplicados en numeración (e.g. dos "Chapter 7").
- TOC declarando secciones que no existen en el cuerpo.
- Cuerpo con secciones que no aparecen en el TOC.

## OCR requerido
`no` (se elige PDF nativo para aislar la hostil).

## Destinos esperados
Todos.

## Tipos de nota esperados
- `concept` (conceptos del libro).
- `architecture` (si el libro describe un sistema).
- `chapter-digest` (resumen del libro).

## Plan de ingesta
L0 nativo; L1 SDM con **anclas sintéticas estables** (F32) — la numeración impresa no se usa para anclar; L2 unidades con `source_block_ids` resueltos por anclas sintéticas; L3 como `concept` o `chapter-digest`; L4 a todos los destinos. El validador de ingest (F30) detecta los saltos.

## Categoría cubierta
**Numeración de secciones inconsistente** (categoría hostile específica).

## Categoría adicional cubierta
**Capítulo de libro técnico de editorial** (categoría cubierta por #02 friendly + #14 hostile).

## Riesgo si falta
Sin esta fuente no se练习a F32 (anclas sintéticas); el validador de ingesta (F30) no练习a con numeración rota.

## Muestra
- Archivo: `sample.pdf` (3-5 páginas con numeración inconsistente) — **no descargado en esta fase**.
- Motivo: la condición "numeración inconsistente" puede aparecer en muchos PDFs; se requiere selección manual que documente el caso específico (qué capítulo falta, dónde aparece el salto). Esta selección se difiere a un eval real.
- Procedimiento documentado: dado cualquier PDF técnico abierto, verificar el TOC vs el cuerpo; si hay saltos o duplicaciones, el PDF sirve como muestra y se documenta el caso en la ficha.
- Hash sha256: pendiente.
