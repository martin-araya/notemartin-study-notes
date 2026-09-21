# 01 — PostgreSQL 16 Documentation, "The SQL Language"

## Identificador
`01-postgresql-chapter`

## Título y autor / fuente
PostgreSQL 16 Documentation — Chapter 2 "The SQL Language" (SQL Syntax, Data Definition, Data Manipulation, Queries, Concurrency, Performance).

## URL canónica
https://www.postgresql.org/docs/16/sql.html

## Licencia
PostgreSQL License (libre; equivalente a BSD/MIT). Redistribución permitida con aviso de copyright.

## Formato
HTML estructurado (multi-página); convertible a PDF nativo si se necesita. Tablas y código embebidos.

## Páginas
~80 (estimado por densidad del sitio).

## Densidad
- Tablas: alta (tablas de parámetros, de tipos, de operadores).
- Código: alta (bloques SQL en cada página de referencia).
- Figuras: baja.
- Fórmulas: ninguna.

## Idioma
inglés.

## Versión del producto
PostgreSQL 16.

## Presencia
- `tablas`: sí
- `codigo`: sí
- `formulas`: no
- `figuras`: no
- `diagramas_sintaxis`: parcial (diagramas de árbol sintáctico en algunos apartados)
- `cajas_editoriales`: sí (Note, Tip, Warning, Caution)

## Hostilidad
`none`.

## OCR requerido
`no` (HTML nativo, texto extraíble).

## Destinos esperados
Todos (Obsidian, Notion API, Notion import, AppFlowy, Markdown, HTML/PDF, Flashcards).

## Tipos de nota esperados
- `api-reference` (firma de comandos SQL).
- `concept` (definiciones operativas).
- `procedure` (procedimientos transaccionales).

## Plan de ingesta
L0 nativo (HTML); L1 SDM; L2 con unidades `parameter`, `step`, `example`; L3 redactar como `api-reference`; L4 a todos los destinos.

## Categoría cubierta
Capítulo de documentación Oracle (sustituto: PostgreSQL — equivalente estructural).

## Categoría adicional cubierta
Documento en inglés con salida esperada en español (perfil de salida alternativo).

## Riesgo si falta
Sin esta fuente no hay cobertura para la categoría "documentación de producto"; el agente no练习ía la cadena de ingesta sobre tablas de parámetros reales.

## Muestra
- Archivo: `sample.html` (página de `SELECT`, PostgreSQL 16 docs).
- Comando de descarga: `curl -sSL -o sample.html https://www.postgresql.org/docs/16/sql-select.html`
- Hash sha256: `a8f4ce1405802cacbb35e6fb88f5e3cf138a4e872910cdfd276f378f13371657` (117 667 bytes).
