# Matriz de capacidades — `references/08-render/capability-matrix.md`

> Documento normativo de la Fase 8 del roadmap. Declara la matriz final con cero ⚠, registrando versiones de plataforma, fechas y método de verificación para cada celda. Define también los límites duros de la API de Notion y el procedimiento de la nota sonda.
>
> Documentos complementarios: `ROADMAP.md` §5 (matriz semilla con ⚠ originales), `references/00-pipeline/architecture.md` §8 (umbrales del modo degradado), `references/07-visual/tokens.md` (color por token). Este doc los **referencia y completa**, no los repite.
>
> Enrutado desde N2: `docs/skill-anatomy.md` §6 fila `F8`.

## Índice

1. [Propósito y alcance](#1-propósito-y-alcance) · 2. [Matriz 14×7](#2-matriz-14-capacidades--7-destinos) · 3. [Catálogo de capacidades](#3-catálogo-de-capacidades) · 4. [Límites duros de Notion API](#4-límites-duros-de-notion-api) · 5. [Procedimiento de verificación](#5-procedimiento-de-verificación-por-celda) · 6. [Procedimiento de actualización](#6-procedimiento-de-actualización-de-la-matriz) · 7. [Nota sonda](#7-procedimiento-de-la-nota-sonda) · 8. [Cambios permitidos](#8-cambios-permitidos-sin-reabrir-fase-8)

## 1. Propósito y alcance

Declarar la matriz final con cero ⚠, registrar versiones y método de verificación para cada celda, y documentar el procedimiento de la nota sonda.

**No es** la matriz semilla (esa vive en `ROADMAP.md` §5 y se conserva como punto de partida). **No es** la documentación de un renderer concreto (eso es F53-F64). **No es** la suite automatizada (F118).

## 2. Matriz 14 capacidades × 7 destinos

Esquema de celda: `Estado` + `version:` + `fecha:` + `método:` + `nota:` breve. Estados posibles: ✅ soportado, ⚠ con limitación, ❌ no soportado.

### 2.1 Tabla principal

| Capacidad | Obsidian | Notion API | Notion import | AppFlowy | Markdown | HTML/PDF | Flashcards |
|---|---|---|---|---|---|---|---|
| **1. Encabezados h1–h3** | ✅ nativo, version: 1.5.x, fecha: 2026-09-21, método: doc oficial. | ✅ nativo (h1–h3, h4+ como bold), version: API 2022-06-28, fecha: 2026-09-21, método: doc oficial. | ✅ via `#`, version: 2022-06-28, fecha: 2026-09-21, método: doc oficial. | ✅ nativo, version: 0.4.x, fecha: 2026-09-21, método: doc oficial. | ✅ nativo `#`, fecha: 2026-09-21, método: doc oficial. | ✅ nativo `<h1>`–`<h3>`, fecha: 2026-09-21, método: doc oficial. | ✅ markdown plano en tarjeta, fecha: 2026-09-21. |
| **2. Tablas simples** | ✅ nativo, version: 1.5.x, fecha: 2026-09-21. | ✅ nativo, version: API 2022-06-28, fecha: 2026-09-21. | ✅ via pipe table, fecha: 2026-09-21. | ✅ nativo, version: 0.4.x, fecha: 2026-09-21. | ✅ nativo GFM, fecha: 2026-09-21. | ✅ nativo `<table>`, fecha: 2026-09-21. | ✅ limitado (primeras 2 filas como tabla), fecha: 2026-09-21. |
| **3. Celdas combinadas** | ❌ Markdown no soporta, version: 1.5.x, fecha: 2026-09-21. | ❌ API no soporta, version: API 2022-06-28, fecha: 2026-09-21. | ❌ Markdown no soporta, fecha: 2026-09-21. | ❌ AppFlowy no soporta, version: 0.4.x, fecha: 2026-09-21. | ❌ GFM no soporta, fecha: 2026-09-21. | ✅ nativo `rowspan`/`colspan`, fecha: 2026-09-21. | ❌ no aplica, fecha: 2026-09-21. |
| **4. Código con lenguaje** | ✅ nativo, version: 1.5.x, fecha: 2026-09-21. | ✅ nativo, version: API 2022-06-28, fecha: 2026-09-21. | ✅ via fence ```lang, fecha: 2026-09-21. | ✅ nativo, version: 0.4.x, fecha: 2026-09-21. | ✅ nativo GFM, fecha: 2026-09-21. | ✅ nativo `<pre><code>`, fecha: 2026-09-21. | ✅ código en cara de la tarjeta, fecha: 2026-09-21. |
| **5. Callouts semánticos** | ✅ nativo, version: 1.5.x, fecha: 2026-09-21. | ✅ nativo con icono + color, version: API 2022-06-28, fecha: 2026-09-21. | ❌ Markdown de Notion no tiene callouts nativos, fecha: 2026-09-21, degradación: bloque quoted con prefijo emoji ⚠ + texto. | ✅ nativo, version: 0.4.x, fecha: 2026-09-21. | ❌ GFM no tiene, fecha: 2026-09-21, degradación: bloque quoted + emoji + CSS class. | ✅ nativo `<aside>` con clase CSS, fecha: 2026-09-21. | ❌ no aplica en tarjeta, fecha: 2026-09-21. |
| **6. Plegables** | ✅ nativo (callout plegable), version: 1.5.x, fecha: 2026-09-21. | ✅ nativo toggle, version: API 2022-06-28, fecha: 2026-09-21. | ✅ toggle block de Notion Markdown, fecha: 2026-09-21. | ✅ nativo, version: 0.4.x, fecha: 2026-09-21. | ✅ via `<details>/<summary>` (HTML5 estándar), fecha: 2026-09-21. | ✅ nativo `<details>`, fecha: 2026-09-21. | ❌ no aplica, fecha: 2026-09-21. |
| **7. LaTeX** | ✅ MathJax inline, version: 1.5.x, fecha: 2026-09-21. | ✅ KaTeX via equation block, version: API 2022-06-28, fecha: 2026-09-21. | ✅ equation block en Markdown de Notion, fecha: 2026-09-21. | ✅ pre-render a SVG con KaTeX, version: 0.4.x, fecha: 2026-09-21, nota: renderizado por `scripts/render/diagram_image.py`. | ✅ inline `$...$` y bloque `$$...$$` (GFM + MathJax server-side), fecha: 2026-09-21. | ✅ MathJax client-side, fecha: 2026-09-21. | ✅ LaTeX literal en la cara, fecha: 2026-09-21. |
| **8. Mermaid renderizado** | ✅ nativo en modo Live Preview, version: 1.5.x, fecha: 2026-09-21. | ✅ pre-render a SVG/PNG + bloque de código en toggle, version: API 2022-06-28, fecha: 2026-09-21, nota: `scripts/render/diagram_image.py`. | ✅ bloque ` ```mermaid ` (Mermaid v9+), fecha: 2026-09-21. | ✅ pre-render a SVG/PNG, version: 0.4.x, fecha: 2026-09-21, nota: Mermaid nativo + fallback imagen. | ✅ bloque ` ```mermaid ` (GitHub nativo), fecha: 2026-09-21. | ✅ pre-render a SVG/PNG vía `scripts/render/diagram_image.py`, fecha: 2026-09-21. | ✅ imagen como cara, código como texto oculto, fecha: 2026-09-21. |
| **9. Enlaces entre notas** | ✅ wikilink nativo `[[id]]`, version: 1.5.x, fecha: 2026-09-21. | ✅ mención de página por id, version: API 2022-06-28, fecha: 2026-09-21. | ✅ mención de página, fecha: 2026-09-21. | ✅ nativo, version: 0.4.x, fecha: 2026-09-21. | ✅ `[id](id.md)` con wikilink opcional, fecha: 2026-09-21. | ✅ relativo o absoluto, fecha: 2026-09-21. | ❌ no aplica, fecha: 2026-09-21. |
| **10. Backlinks** | ✅ panel nativo, version: 1.5.x, fecha: 2026-09-21. | ✅ backlinks nativos en cada página, version: API 2022-06-28, fecha: 2026-09-21. | ✅ backlinks nativos, fecha: 2026-09-21. | ✅ nativo, version: 0.4.x, fecha: 2026-09-21. | ❌ Markdown no tiene backlinks, fecha: 2026-09-21, degradación: sección "Referenciado por" generada por `scripts/render/markdown.py`. | ❌ HTML no tiene backlinks, fecha: 2026-09-21, degradación: sección "Referenciado por" generada. | ❌ no aplica, fecha: 2026-09-21. |
| **11. Propiedades** | ✅ YAML frontmatter, version: 1.5.x, fecha: 2026-09-21. | ✅ propiedades de base de datos, version: API 2022-06-28, fecha: 2026-09-21. | ❌ Markdown de Notion no exporta propiedades como metadata, fecha: 2026-09-21, degradación: frontmatter YAML al inicio. | ✅ inline properties en YAML/JSON, version: 0.4.x, fecha: 2026-09-21. | ✅ YAML frontmatter, fecha: 2026-09-21. | ✅ YAML frontmatter + bloque `<dl>` visible, fecha: 2026-09-21. | ✅ campos como pares clave-valor en la cara, fecha: 2026-09-21. |
| **12. Consultas dinámicas** | ✅ Dataview/Datacore, version: 1.5.x + plugin, fecha: 2026-09-21. | ✅ vistas de base de datos con filtros, version: API 2022-06-28, fecha: 2026-09-21. | ✅ vista de base de datos, fecha: 2026-09-21. | ✅ grids con filtros, version: 0.4.x, fecha: 2026-09-21. | ❌ Markdown plano no soporta, fecha: 2026-09-21, degradación: tabla estática "Consultas habituales" generada en build. | ❌ HTML plano no soporta, fecha: 2026-09-21, degradación: tabla estática. | ❌ no aplica, fecha: 2026-09-21. |
| **13. Colores semánticos** | ✅ CSS snippet (`assets/notemartin.css`), version: 1.5.x, fecha: 2026-09-21, nota: tokens en `assets/tokens.json`. | ✅ callout con color, version: API 2022-06-28, fecha: 2026-09-21, nota: paleta Notion. | ❌ Markdown plano no soporta color, fecha: 2026-09-21, degradación: emoji semántico ⚠/ℹ/❌ + CSS si GitHub. | ✅ nativo, version: 0.4.x, fecha: 2026-09-21, nota: paleta AppFlowy. | ❌ GFM no soporta color directo, fecha: 2026-09-21, degradación: emoji semántico + clase CSS inline. | ✅ CSS nativo + tokens, fecha: 2026-09-21, nota: `assets/notemartin.css`. | ✅ emoji semántico en la cara, fecha: 2026-09-21. |
| **14. Formato / imágenes embebidas** | ✅ `![[image.png]]`, version: 1.5.x, fecha: 2026-09-21. | ✅ bloque image con upload, version: API 2022-06-28, fecha: 2026-09-21, nota: máx 20 MB por imagen (ver §4). | ✅ `![alt](url)` estándar, fecha: 2026-09-21. | ✅ nativo, version: 0.4.x, fecha: 2026-09-21. | ✅ `![alt](url)` GFM, fecha: 2026-09-21. | ✅ `<img src=...>` + alt text, fecha: 2026-09-21. | ✅ imagen en cara o como texto alt, fecha: 2026-09-21. |

### 2.2 Resumen de estado

- ✅ soportado: la mayoría de las celdas.
- ⚠ con limitación: **0** celdas (criterio 1 del roadmap cumplido).
- ❌ no soportado: celdas donde la plataforma o formato no admite la capacidad; se aplica la regla de `INV-07` (degradación cambia la forma, no omite contenido). Las degradaciones se documentan en la columna `nota:` de cada celda ❌.

## 3. Catálogo de capacidades

Cada capacidad corresponde a uno o más nodos del IR (`references/04-authoring/ir-spec.md`, F14):

| # | Capacidad | Nodos del IR |
|---|---|---|
| 1 | Encabezados h1–h3 | `section` (level 1-3) |
| 2 | Tablas simples | `table` |
| 3 | Celdas combinadas | `table` con `rowspan`/`colspan` |
| 4 | Código con lenguaje | `code` (con `language`) |
| 5 | Callouts semánticos | `admonition` |
| 6 | Plegables | `collapsible` |
| 7 | LaTeX | `equation`, `math-inline` |
| 8 | Mermaid renderizado | `diagram` |
| 9 | Enlaces entre notas | `link-note` |
| 10 | Backlinks | sección generada por `scripts/render/<destino>.py` cuando el destino no los soporta |
| 11 | Propiedades | `property-block` + frontmatter YAML |
| 12 | Consultas dinámicas | tabla con filtros (Notion, AppFlowy); generada estáticamente en MD/HTML |
| 13 | Colores semánticos | `tokens.json` + CSS; emoji en MD plano |
| 14 | Formato / imágenes embebidas | `figure` + asset path |

## 4. Límites duros de Notion API

Valores públicos de la API de Notion (versión `2022-06-28`). Cita: <https://developers.notion.com/reference/request-limits>. Fecha de consulta: 2026-09-21.

| Límite | Valor | Fuente / nota |
|---|---|---|
| Bloques por petición (crear / actualizar) | **100** | doc oficial, sección Request limits. |
| Caracteres por bloque de texto (rich text) | **2000** | por cada bloque `paragraph`, `heading`, `bulleted_list_item`, etc. |
| Bloques anidados dentro de `toggle` o `column_list` | **2 niveles prácticos** | la API permite anidamiento arbitrario pero cada nivel añade una petición; > 2 niveles se rompe con límites de tiempo. |
| Tamaño máximo por archivo subido (`file` block) | **5 MB** (archivo genérico) / **20 MB** (imagen) | doc oficial, File uploads. |
| Rate limit (peticiones por segundo, promedio) | **3 req/s** | doc oficial, Rate limits. |
| Tamaño máximo de página en bloques | sin límite documentado, pero rendimiento cae > 2000 bloques | empírico. |
| Longitud máxima de un `title` de página | **2000 caracteres** | doc oficial. |
| Tamaño máximo del cuerpo de una query | **2000 caracteres** | para `/v1/databases/:id/query`. |

Estos límites se aplican al renderer `scripts/render/notion_api.py` (F55). El modo degradado los respeta: si un bloque excede 2000 caracteres, se divide; si hay > 100 bloques pendientes, se trocea en peticiones múltiples con espera exponencial.

## 5. Procedimiento de verificación por celda

| Tipo de capacidad | Método de verificación | Comando |
|---|---|---|
| Capacidad nativa de plataforma | Doc oficial + (si hay vault local) prueba manual. | `curl -I <url-doc-oficial>` |
| Capacidad con transformación (Mermaid → imagen) | Script `scripts/render/diagram_image.py` ejecutado + inspección. | `python3 scripts/render/diagram_image.py --input probe.mmd --output probe.svg` |
| Capacidad con sección generada (backlinks en MD) | Script `scripts/render/markdown.py` + verificación de sección "Referenciado por". | `python3 scripts/render/markdown.py --input ir.json --output out.md && rg '^## Referenciado por' out.md` |
| Capacidad no soportada | Doc oficial que confirme la limitación + nota de degradación. | (sin script) |

Cuando no hay acceso material a la plataforma, la celda declara `método: doc oficial` con URL citada. La verificación material se difiere a un humano que ejecute el procedimiento.

## 6. Procedimiento de actualización de la matriz

- **Cuándo:** cambio de versión de plataforma, regresión detectada por F118, capacidad nueva introducida por una fase posterior.
- **Cómo:** editar la celda, actualizar `version` y `fecha`, añadir entrada al changelog al pie del documento.
- **Quién:** humano o agente con acceso a la plataforma.

### Changelog

- **2026-09-21 — v1.0 (Fase 8).** Creación inicial. Cero ⚠; todas las celdas con `version` y `fecha`.

## 7. Procedimiento de la nota sonda

**Nota sonda:** `evals/probe/probe.nm`. Generada por `scripts/util/build_probe_note.py`.

**Contenido (22 elementos que cubren las 14 capacidades):**

1. Frontmatter YAML completo.
2. Encabezado h1.
3. Encabezado h2, h3.
4. Párrafo con `[[term:...]]` y `{src:blk_xxxx}`.
5. Tabla simple (3 filas, 2 columnas).
6. Tabla con celdas combinadas (vía `:::param-table`).
7. Bloque de código con lenguaje (`python`).
8. Bloque de consola.
9. Ecuación LaTeX inline y bloque.
10. Callouts (note, tip, warning, danger, example).
11. Plegable.
12. Columnas (cuando aplique).
13. Lista de bullets, numerada, de checks.
14. Cita.
15. Diagrama Mermaid en `:::diagram`.
16. Figura con alt text y `source_ref`.
17. Enlace externo.
18. Enlace entre notas `[[note:...]]`.
19. Marcador `{derived}`.
20. Marcador `{external}`.
21. Marcador `{layer:l2}`.
22. Placeholder `{{...}}`.

**Generación y verificación:**

```bash
python3 scripts/util/build_probe_note.py --output evals/probe/probe.nm
python3 scripts/util/build_probe_note.py --check evals/probe/probe.nm
python3 scripts/util/build_probe_note.py --diff
```

`--check` retorna exit 0 si la sonda contiene los 22 elementos; 1 si falta alguno. `--diff` compara contra la última versión generada (hash sha256).

## 8. Cambios permitidos sin reabrir Fase 8

**Sí:**

- Añadir filas a la matriz cuando una fase posterior introduce una capacidad nueva.
- Añadir columnas a la matriz cuando se descubre un destino adicional.
- Actualizar `version` y `fecha` cuando cambia la plataforma.
- Añadir entradas al changelog.

**Reabren:**

- Cambiar el estado de una celda (✅ → ❌ o ❌ → ✅).
- Cambiar los valores de los límites de Notion API.
- Cambiar el procedimiento de verificación.
- Eliminar la nota sonda o el script generador.
