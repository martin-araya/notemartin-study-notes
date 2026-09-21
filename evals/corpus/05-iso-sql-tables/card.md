# 05 — PostgreSQL Reference (dense in tables)

## Identificador
`05-iso-sql-tables`

## Título y autor / fuente
PostgreSQL 16 Reference Documentation — SQL Commands / System Catalogs / Data Types. Sustituto de la ISO/IEC 9075 (SQL Foundation) por accesibilidad.

## URL canónica
https://www.postgresql.org/docs/16/reference.html

## Licencia
PostgreSQL License (libre).

## Formato
HTML estructurado, equivalente al imprimir como PDF de ~200+ páginas.

## Páginas
~250 (sumando todas las páginas de referencia: SQL command reference, system catalogs, data types, functions).

## Densidad
- Tablas: muy alta (cada página de comando tiene 3–5 tablas de parámetros y sintaxis).
- Código: media.
- Figuras: no.
- Fórmulas: no.

## Idioma
inglés.

## Versión del producto
PostgreSQL 16.

## Presencia
- `tablas`: sí (más de 20 tablas en total)
- `codigo`: sí
- `formulas`: no
- `figuras`: no
- `diagramas_sintaxis`: no
- `cajas_editoriales`: sí

## Hostilidad
`none`.

## OCR requerido
`no`.

## Destinos esperados
Todos.

## Tipos de nota esperados
- `api-reference` (firma de cada comando).
- `configuration` (parámetros).
- `cheatsheet` (resumen tabular).

## Plan de ingesta
L0 nativo (HTML); L1 SDM con jerarquía profunda; L2 unidades `parameter` masivas; L3 como `api-reference`; L4 a todos los destinos.

## Categoría cubierta
Documento con 20+ tablas.

## Categoría adicional cubierta
Documentación de producto extensa (>= 200 páginas).

## Riesgo si falta
Sin esta fuente no se estresa la cadena sobre documentos densos en tablas; la auditoría de cobertura (F43) no练习a con >100 unidades `must-keep`.

## Muestra
- Archivo: `sample.html` (página de `CREATE TABLE`, densa en tablas).
- Comando de descarga: `curl -sSL -o sample.html https://www.postgresql.org/docs/16/sql-createtable.html`
- Hash sha256: `d21a9121420bb8d732d08c473164b9cd7ed039b2a44ea2fdde43f478662b03cc` (124 108 bytes).
- Nota: la página completa del manual de referencia de PostgreSQL 16 supera las 200 páginas si se concatena; la muestra es una página representativa con alta densidad tabular.
