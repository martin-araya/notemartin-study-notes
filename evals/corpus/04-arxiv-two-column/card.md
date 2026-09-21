# 04 — arXiv paper (two-column LaTeX)

## Identificador
`04-arxiv-two-column`

## Título y autor / fuente
arXiv preprint técnico, formato LaTeX estándar de dos columnas. Sustituto concreto: cualquier preprint de cs.DB o cs.DC, e.g. "FoundationDB: A Distributed Key-Value Store" o equivalente.

## URL canónica
https://arxiv.org/

## Licencia
Variable por autor; arXiv estándar permite redistribución con fines no comerciales. Se elige un preprint con licencia explícitamente libre (CC-BY 4.0 o CC0).

## Formato
PDF nativo (LaTeX compilado, dos columnas).

## Páginas
~15.

## Densidad
- Tablas: media.
- Código: baja (pseudocódigo).
- Figuras: media.
- Fórmulas: sí (matemáticas).

## Idioma
inglés.

## Versión del producto
no aplica.

## Presencia
- `tablas`: sí
- `codigo`: sí
- `formulas`: sí
- `figuras`: sí
- `diagramas_sintaxis`: no
- `cajas_editoriales`: no

## Hostilidad
`none`.

## OCR requerido
`no`.

## Destinos esperados
Todos (la estructura de dos columnas se renderiza correctamente en cada destino).

## Tipos de nota esperados
- `concept` (conceptos del paper).
- `comparison` (frente a alternativas mencionadas).
- `architecture` (si el paper describe un sistema).

## Plan de ingesta
L0 nativo (PDF dos columnas); L1 SDM con layout multi-columna (F21); L2 unidades `definition`, `mechanism`; L3 como `concept`; L4 a todos los destinos.

## Categoría cubierta
PDF a dos columnas.

## Riesgo si falta
Sin esta fuente no hay cobertura para "PDF a dos columnas"; el validador de layout (F21) no se练a sobre casos reales.

## Muestra
- Archivo: `sample.pdf` (preprint arXiv descargado; 4 MB, dos columnas).
- Comando de descarga: `curl -sSL --max-time 20 -o sample.pdf https://arxiv.org/pdf/2201.00001`
- Hash sha256: `9c0ec88674d888e77aa774fe22e12904b7f3ec77bd0aa55cc3676d3d02a4502e` (4 018 868 bytes).
- Sustituto concreto: el documento original puede cambiar de URL; mientras el sha256 siga siendo verificable, la muestra es válida.
