# 10 — PostgreSQL GitHub repo (README + tree)

## Identificador
`10-postgres-readme-repo`

## Título y autor / fuente
Repositorio `postgres/postgres` en GitHub. README + árbol de carpetas + muestras de código fuente (e.g. `src/backend/executor/`).

## URL canónica
https://github.com/postgres/postgres

## Licencia
PostgreSQL License (libre).

## Formato
Markdown (README) + árbol de carpetas + código fuente plano.

## Páginas
~5 (README) + árbol expandido como muestra (no se almacena el repo completo).

## Densidad
- Tablas: no.
- Código: alta (el árbol tiene miles de archivos `.c` y `.h`; la muestra son 5-10 archivos seleccionados).
- Figuras: no.

## Idioma
inglés (código en C con comentarios en inglés).

## Versión del producto
PostgreSQL 16 (HEAD del repo al cierre de F6).

## Presencia
- `tablas`: no
- `codigo`: sí
- `formulas`: no
- `figuras`: no
- `diagramas_sintaxis`: no
- `cajas_editoriales`: no

## Hostilidad
`none`.

## OCR requerido
`no`.

## Destinos esperados
Todos.

## Tipos de nota esperados
- `procedure` (procedimientos de compilación, build).
- `concept` (estructura del código fuente).

## Plan de ingesta
L0 texto plano (no PDF); L1 SDM con detección de secciones en Markdown + bloques de código preservados; L2 unidades `step` (procedimiento build) y `definition` (estructura); L3 como `procedure`; L4 a todos los destinos.

## Categoría cubierta
README + repositorio.

## Riesgo si falta
Sin esta fuente no se cubre el caso "fuente no PDF, gran cantidad de código"; la nota `procedure` no练习a con código fuente real.

## Muestra
- Archivo: `sample.md` (README del repo postgres/postgres, 989 bytes).
- Comando de descarga: `curl -sSL -o sample.md https://raw.githubusercontent.com/postgres/postgres/master/README.md`
- Hash sha256: `f8f3f3b5e7f522c8b4d8e49679ccab090b26fd0a0b4bcf6fd54e22fec6a88b2a`.
- Nota: muestra mínima. La estructura del árbol (sample-tree.txt) y archivos de código seleccionados (sample-code.c) se descargarán cuando un eval real los necesite, no se versionan aquí para no inflar el repo.
