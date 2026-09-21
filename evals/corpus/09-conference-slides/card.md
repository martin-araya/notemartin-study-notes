# 09 — Conference slides (PPTX)

## Identificador
`09-conference-slides`

## Título y autor / fuente
Diapositivas de una charla técnica reciente. Sustituto concreto: cualquier presentación de PGConf / KubeCon / DockerCon publicada como PDF o PPTX.

## URL canónica
https://speakerdeck.com/ o https://www.slideshare.net/ (sustitutos genéricos).

## Licencia
Variable; se elige presentación con CC-BY o equivalente.

## Formato
**PDF escaneado** (imágenes de slides; OCR requerido). PDF generado al imprimir las slides como imágenes; sin capa de texto.

## Páginas
~30 (30 slides).

## Densidad
- Tablas: baja.
- Código: bajo (snippets en slides).
- Figuras: alta (diagramas en cada slide).

## Idioma
inglés.

## Versión del producto
Variable.

## Presencia
- `tablas`: sí (pocas)
- `codigo`: sí (poco)
- `formulas`: no
- `figuras`: sí
- `diagramas_sintaxis`: no
- `cajas_editoriales`: no

## Hostilidad
`none`.

## OCR requerido
**`sí`** — confianza media esperada entre 0.70 y 0.90 (texto grande de slides es más fácil de OCR que prosa). Reintento ≤ 2; umbral de bloqueo si < 0.70.

## Destinos esperados
Obsidian, Notion API, Markdown.

## Tipos de nota esperados
- `chapter-digest` (orden de slides = orden de temas).
- `concept` (un concepto por slide típico).

## Plan de ingesta
L0 con PPTX (`scripts/ingest/other_formats.py`); L1 SDM con notas del orador como bloques propios; L2 unidades `definition`; L3 como `chapter-digest`; L4 a destinos declarados.

## Categoría cubierta
Diapositivas **+ PDF escaneado con OCR sucio** (segunda fuente friendly con OCR; complementa #02 y #13).

## Riesgo si falta
Sin esta fuente no se练习a la cadena sobre PPTX; la nota `chapter-digest` no tiene caso de prueba con notas del orador.

## Muestra
- Archivo: `sample.pdf` (5-10 slides) — **no descargado en esta fase**.
- Motivo: las presentaciones en SlideShare/SpeakerDeck tienen URLs por charla individual; selección requiere decisión editorial que se difiere a un eval real.
- Sustituto propuesto: `https://www.postgresql.org/events/pgconf.nyc/2024/schedule/` (presentaciones listadas por año).
- Hash sha256: pendiente.
