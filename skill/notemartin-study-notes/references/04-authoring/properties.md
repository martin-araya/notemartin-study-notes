# Properties — `references/04-authoring/properties.md`

> Documento normativo de la Fase 47 del roadmap. Contrato del **frontmatter canónico**
> de toda nota en NoteMark: las 18 propiedades cerradas, su tipo, su mapeo a los 7
> destinos, su obligatoriedad por tipo de nota (15 cerrados), y la estrategia de
> render legible cuando el destino no soporta properties nativas.
>
> Documentos relacionados:
> - [`notemark.md`](notemark.md): gramática legible; §8 Frontmatter reescrita como
>   puntero a este doc.
> - [`notemark.ebnf`](notemark.ebnf): gramática formal; reglas `frontmatter` /
>   `yaml-body` / `yaml-line` / `key` (no se duplican aquí).
> - [`block-directives.md`](block-directives.md): `:::property` (§10.22) es metadata
>   **local a un bloque**; el frontmatter de este doc es metadata **global** del
>   archivo. La distinción local-vs-global está documentada en F45 §10.22.
> - [`../../assets/profile.template.yaml`](../../assets/profile.template.yaml) (F11):
>   defaults del **perfil del usuario** (distinto del frontmatter de cada nota).
> - [`../05-note-types/README.md`](../05-note-types/README.md): los 15 tipos cerrados
>   de nota (F78-F92). §6 de este doc es la fuente de verdad de obligatoriedad.
> - [`../08-render/capability-matrix.md`](../08-render/capability-matrix.md): los 7
>   destinos y sus capacidades (F8). §5 mapea cada propiedad al destino.

## §1 · Propósito y alcance

Este documento es la **fuente normativa** del frontmatter de cualquier nota NoteMark.
Responde cuatro preguntas por propiedad:

1. ¿Cuál es su tipo y su validación sintáctica?
2. ¿Es obligatoria u opcional, y para qué tipos de nota?
3. ¿Cómo se renderiza en cada uno de los 7 destinos?
4. ¿Qué notas o convenciones especiales la afectan?

`notemark.md` §8 Frontmatter listaba 11 propiedades (3 obligatorias + 8 recomendadas)
con tabla parcial de tipos. La Fase 47 las completa a las **18 propiedades cerradas**
del detalle F47, añade el **mapeo por destino** (criterio #1), la **obligatoriedad
por tipo** (criterio #2) y la **estrategia de render legible** para destinos sin
soporte nativo (criterio #3).

**Frontera con otros documentos:**

- El **perfil del usuario** (`profile.yaml`, F11) configura el comportamiento global
  de la skill (idioma de salida, OCR, destinos activos, profundidad). Es metadata de
  **configuración**, no del archivo.
- El **frontmatter de la nota** (este doc) declara metadata del **archivo concreto**
  (título, tipo, fuente, estado). Es lo que el lector ve al abrir la nota.
- `:::property` (F45 §10.22) es metadata **local a un bloque** dentro del cuerpo.
- Los **layer markers** (`{layer:l1|l2|l3}`, F51) son metadata de **profundidad**, no
  aparecen en el frontmatter.

## §2 · Cuándo se aplica

- Cualquier redacción de una nota nueva en L3 (el frontmatter es obligatorio antes
  del cuerpo).
- Cualquier revisión de una nota existente que requiera actualizar metadata
  (cambio de versión del producto, paso a `published`, etc.).
- Validación en F49: el parser (F48) acepta el frontmatter, el validador (F49)
  verifica obligatoriedad por tipo, formato de fechas y enums cerrados.
- Render en F54-F60: cada destino mapea las propiedades según §5.

**No se aplica a:** ingesta (F17-F29), validación del IR (F49 post-parse), publicación
(F62). El parser (F48) consume este doc como contrato sintáctico; los renderers
(F54-F60) lo consultan para capacidades por destino.

## §3 · Reglas duras (invariantes)

| ID | Invariante | Si se omite… |
|---|---|---|
| **INV-P1** *(F47, +F102, +F104, +F105)* | El conjunto de propiedades canónicas es exactamente las 24 documentadas en §5. Añadir una nueva requiere reabrir F47. | El parser rechaza claves no listadas o el renderer las descarta silenciosamente. |
| **INV-P2** *(F47)* | Las claves se escriben en **kebab-case** sin espacios, sin underscores, sin CamelCase. Las claves de namespace `x-*` o `user-*` también en kebab-case. | El parser (F48) rechaza claves que no coincidan con `^[a-z][a-z0-9-]*$`. |
| **INV-P3** *(F47)* | Cero colores literales en valores de propiedades. Tokens via `assets/tokens.json` (F72). | INV-14 violación. |
| **INV-P4** *(F47)* | Ninguna clave duplicada dentro del mismo frontmatter. | El parser rechaza el YAML. |
| **INV-P5** *(F47, F75)* | Las 5 propiedades universales (`title`, `note-type`, `status`, `summary`, `reading-time-minutes`) son obligatorias en `status: published`. En `status: draft`, `summary` y `reading-time-minutes` son opcionales. | El validador (F49) bloquea el cierre de la nota publicada. |
| **INV-P10** *(F75)* | `summary` ≤ 200 chars, 1 línea, sin caracteres de control. `reading-time-minutes` es int ≥ 1. | El validador rechaza el cierre con tipo no entero o valor ≤ 0. |
| **INV-P6** *(F47)* | `retrieved` y `review-next` usan exclusivamente formato `YYYY-MM-DD` (ISO 8601 sin hora). | El parser rechaza formatos con hora, zona, o separadores distintos. |
| **INV-P7** *(F47)* | `source-url` debe ser URL válida (`http://` o `https://`). | El validador (F49) lo reporta como warning; el parser no rechaza (algunos corpus sintéticos no la tienen). |
| **INV-P8** *(F47)* | Los valores de los enums cerrados (`note-type`, `status`, `source-type`, `language`, `coverage`, `difficulty`) deben pertenecer exactamente a la lista de §5. | El parser rechaza valores fuera del enum. |
| **INV-P12** *(F115)* | `status: verified` requiere haber pasado la puerta de calidad completa (`scripts/quality_gate.py promote` exit 0). El campo `verified_at` (ISO 8601) y `quality_gate_run_id` (UUID) se añaden en la promoción. | `quality_gate.py promote` modifica el frontmatter. |
| **INV-P9** *(F47)* | El orden en el archivo es: frontmatter (`---` … `---`), luego cuerpo. Ningún bloque antes del frontmatter. | El parser (F48) espera frontmatter al inicio; si hay otro bloque, falla. |

## §4 · Conjunto canónico (resumen)

Las 24 propiedades cerradas. Las 5 primeras (universales) son obligatorias en notas con `status: published`; el resto tiene obligatoriedad variable según §6. Las universales son obligatorias en `status: draft` solo las 3 primeras (title, note-type, status) — `summary` y `reading-time-minutes` se difieren hasta el cierre (F75).

| # | Propiedad | Tipo | Universal |
|---|---|---|---|
| 1 | `title` | string | ✅ |
| 2 | `note-type` | enum (15) | ✅ |
| 3 | `status` | enum (4) | ✅ |
| 4 | `summary` | string (≤ 200 chars) | ✅ (en published) |
| 5 | `reading-time-minutes` | int ≥ 1 | ✅ (en published) |
| 6 | `tags` | array of string | |
| 7 | `source` | string | |
| 8 | `source-type` | enum (6) | |
| 9 | `vendor` | string | |
| 10 | `product` | string | |
| 11 | `product-version` | string | |
| 12 | `source-anchor` | string | |
| 13 | `source-url` | URL | |
| 14 | `retrieved` | date ISO 8601 | |
| 15 | `language` | enum (4) | |
| 16 | `coverage` | enum (3) | |
| 17 | `difficulty` | enum (1-5) | |
| 18 | `review-next` | date ISO 8601 | |
| 19 | `aliases` | array of string | |
| 20 | `related` | array of string (note_id o term_id) | |
| 21 | `self-evaluation-types` | array of enum (5) | |
| 22 | `study-path-goals` | array of enum (3) | |
| 23 | `goal-profile-override` | enum (4) | |
| 24 | `certification-objective` | array of string | |

Detalle de cada una en **§5**. Para propiedades personalizadas fuera de esta lista,
ver **§8**.

---

## §5 · Catálogo por propiedad

Una subsección por propiedad con la plantilla: tipo → obligatoriedad → descripción →
validación → mapeo por destino (7) → notas.

### 5.1 `title`  {#prop-title}

- **Tipo:** string (1 línea, sin saltos de línea, sin caracteres de control).
- **Obligatoriedad:** siempre obligatoria (INV-P5). Universal.
- **Descripción:** título legible de la nota; es lo primero que el lector ve.
- **Validación:** no vacío; ≤ 120 caracteres; no comienza con `#` ni `>`; sin
  secuencias de escape (`\n`, `\t`).
- **Mapeo por destino:**
  - Obsidian → `Properties.title` (visible en el panel).
  - Notion API → `page.properties.title` (columna `Name` por defecto).
  - Notion import → literal YAML al inicio.
  - AppFlowy → `Properties.title`.
  - MD → literal YAML.
  - HTML/PDF → celda `title` de la tabla `## Metadata` (§7).
  - Flashcards → campo `title` del deck; aparece en el reverso como referencia.
- **Notas:** si el SDM da un título largo, el agente lo acorta respetando la
  semántica; nunca trunca a media frase.

### 5.2 `note-type`  {#prop-note-type}

- **Tipo:** enum (15 valores cerrados).
- **Obligatoriedad:** siempre obligatoria (INV-P5). Universal.
- **Descripción:** tipo de la nota; controla qué plantilla se usa (F78-F92).
- **Valores:** `concept`, `api-reference`, `procedure`, `configuration`,
  `error-troubleshooting`, `architecture`, `syntax`, `data-model`,
  `chapter-digest`, `comparison`, `version-delta`, `glossary-term`,
  `cheatsheet`, `index-moc`, `practice`.
- **Mapeo por destino:**
  - Obsidian → `Properties.note-type`; el agente puede usarlo para filtrar con
    Dataview.
  - Notion API → `page.properties.note-type` (columna `select`).
  - Notion import → literal YAML (Notion no lo interpreta como tipo).
  - AppFlowy → `Properties.note-type`.
  - MD → literal YAML; el renderer de MOC (§5.18) lo usa para indexar.
  - HTML/PDF → celda `note-type` de la tabla `## Metadata`.
  - Flashcards → descartado; el deck no clasifica por tipo.
- **Notas:** si el SDM no encaja en ninguno de los 15, abrir F44 (no improvisar
  valores nuevos).

### 5.3 `status`  {#prop-status}

- **Tipo:** enum (4 valores; F115 añadió `verified`).
- **Obligatoriedad:** siempre obligatoria (INV-P5). Universal.
- **Descripción:** estado de publicación de la nota; controla visibilidad en
  destinos con indexación.
- **Valores:** `draft` (en redacción), `published` (lista para consumir),
  `archived` (obsoleta, conservada por trazabilidad),
  `verified` (promovida por `scripts/quality_gate.py promote` exit 0; INV-P12).
- **Mapeo por destino:**
  - Obsidian → `Properties.status`; filtro Dataview por `status != archived`.
  - Notion API → `page.properties.status` (columna `select`).
  - Notion import → literal YAML.
  - AppFlowy → `Properties.status`.
  - MD → literal YAML.
  - HTML/PDF → celda `status` de la tabla `## Metadata`.
  - Flashcards → descartado.
- **Notas:** el cambio de `draft` → `published` es irreversible hasta una
  nueva edición; `archived` requiere un comentario en `aliases` o `related`
  apuntando al sucesor.

### 5.4 `tags`  {#prop-tags}

- **Tipo:** array of string (kebab-case).
- **Obligatoriedad:** recomendada en todos los tipos; obligatoria solo si el
  perfil activa prefijos de namespace (`type/`, `domain/`, `fXXX/`, ver
  `profile.template.yaml`).
- **Descripción:** clasificación temática de la nota; se usa para filtrar,
  agrupar y generar MOCs.
- **Validación:** cada tag en kebab-case (`^[a-z][a-z0-9-]*$`); sin duplicados;
  sin strings vacíos.
- **Mapeo por destino:**
  - Obsidian → `Properties.tags` + tags inline al final de la nota (visible
    en el grafo).
  - Notion API → `page.properties.tags` (columna `multi_select`).
  - Notion import → literal YAML; tags adicionales se pierden.
  - AppFlowy → `Properties.tags`.
  - MD → literal YAML.
  - HTML/PDF → celda `tags` (lista separada por comas) de `## Metadata`.
  - Flashcards → campo `tags` del deck (categoría de la card).
- **Notas:** los prefijos `type/<note-type>` y `domain/<área>` se recomiendan
  para indexar MOCs automáticamente.

### 5.5 `source`  {#prop-source}

- **Tipo:** string (identificador estable).
- **Obligatoriedad:** obligatoria en tipos source-bearing (§6); opcional en
  `glossary-term`, `index-moc`.
- **Descripción:** nombre canónico de la fuente (título del libro, id del RFC,
  nombre del repo). Complementa a `source-type` y `source-url`.
- **Validación:** no vacío cuando obligatoria; sin caracteres de control.
- **Mapeo por destino:**
  - Obsidian → `Properties.source`; link a la nota-raíz si existe.
  - Notion API → `page.properties.source` (columna `rich_text`).
  - Notion import → literal YAML.
  - AppFlowy → `Properties.source`.
  - MD → literal YAML.
  - HTML/PDF → celda `source` de `## Metadata`.
  - Flashcards → descartado.
- **Notas:** consistente con el `manifest.json` (F16); un cambio de `source`
  dispara `hash_mismatch` si el hash también cambia.

### 5.6 `source-type`  {#prop-source-type}

- **Tipo:** enum (6 valores).
- **Obligatoriedad:** obligatoria si `source` está presente; opcional en tipos
  no source-bearing.
- **Descripción:** tipo de la fuente.
- **Valores:** `book`, `rfc`, `manual`, `repo`, `transcript`, `synthetic`.
- **Mapeo por destino:**
  - Obsidian → `Properties.source-type`.
  - Notion API → `page.properties.source-type` (columna `select`).
  - Notion import → literal YAML.
  - AppFlowy → `Properties.source-type`.
  - MD → literal YAML.
  - HTML/PDF → celda `source-type` de `## Metadata`.
  - Flashcards → descartado.
- **Notas:** `synthetic` se usa para corpus construido por el agente (novela,
  ficción, material sin atribución real).

### 5.7 `vendor`  {#prop-vendor}

- **Tipo:** string.
- **Obligatoriedad:** recomendada en tipos source-bearing con producto
  comercial (`api-reference`, `procedure`, `configuration`, etc.).
- **Descripción:** proveedor del producto documentado.
- **Validación:** no vacío cuando presente.
- **Mapeo por destino:**
  - Obsidian → `Properties.vendor`.
  - Notion API → `page.properties.vendor` (`rich_text`).
  - Notion import → literal YAML.
  - AppFlowy → `Properties.vendor`.
  - MD → literal YAML.
  - HTML/PDF → celda `vendor` de `## Metadata`.
  - Flashcards → descartado.
- **Notas:** útil para agrupar productos del mismo proveedor (ej. todas las
  notas de PostgreSQL → `PostgreSQL Global Development Group`).

### 5.8 `product`  {#prop-product}

- **Tipo:** string.
- **Obligatoriedad:** obligatoria en tipos source-bearing con producto
  comercial.
- **Descripción:** nombre del producto.
- **Validación:** no vacío cuando presente; sin versiones (eso va en
  `product-version`).
- **Mapeo por destino:**
  - Obsidian → `Properties.product`.
  - Notion API → `page.properties.product` (`rich_text`).
  - Notion import → literal YAML.
  - AppFlowy → `Properties.product`.
  - MD → literal YAML.
  - HTML/PDF → celda `product` de `## Metadata` (§7).
  - Flashcards → descartado.
- **Notas:** si el SDM cubre múltiples productos del mismo vendor (ej. PG +
  pgAdmin), cada nota lleva su propio `product`.

### 5.9 `product-version`  {#prop-product-version}

- **Tipo:** string (versión exacta, rango, o `unknown`).
- **Obligatoriedad:** recomendada en tipos source-bearing; **`unknown`** si
  no se puede determinar (INV-17 del notemark).
- **Descripción:** versión del producto al que aplica la nota.
- **Validación:** formato libre (`16.1`, `15-16`, `unknown`, `>=14`).
- **Mapeo por destino:**
  - Obsidian → `Properties.product-version`.
  - Notion API → `page.properties.product-version` (`rich_text`).
  - Notion import → literal YAML.
  - AppFlowy → `Properties.product-version`.
  - MD → literal YAML.
  - HTML/PDF → celda `product-version` de `## Metadata` (§7).
  - Flashcards → descartado.
- **Notas:** rango `15-16` indica que la nota aplica a ambas; `unknown` se
  usa cuando el SDM no especifica versión y no se puede inferir.

### 5.10 `source-anchor`  {#prop-source-anchor}

- **Tipo:** string (path de sección, página, commit, o id de bloque).
- **Obligatoriedad:** recomendada en todos los tipos con `source`.
- **Descripción:** ancla principal dentro de la fuente (no a nivel de bloque
  individual, eso lo cubre `{src:blk_xxxx}` de F46).
- **Validación:** no vacío cuando presente.
- **Mapeo por destino:**
  - Obsidian → `Properties.source-anchor`.
  - Notion API → `page.properties.source-anchor` (`rich_text`).
  - Notion import → literal YAML.
  - AppFlowy → `Properties.source-anchor`.
  - MD → literal YAML.
  - HTML/PDF → celda `source-anchor` de `## Metadata` (§7).
  - Flashcards → descartado.
- **Notas:** complementario a `source-url`. Ej. `source-url: https://.../postgresql-16.pdf`
  + `source-anchor: chapter-14`.

### 5.11 `source-url`  {#prop-source-url}

- **Tipo:** URL (`http://` o `https://`).
- **Obligatoriedad:** recomendada en tipos source-bearing con fuente en línea;
  opcional para libros físicos y escaneos locales.
- **Descripción:** URL pública o local de la fuente.
- **Validación:** debe comenzar con `http://` o `https://` (INV-P7); warning
  si la URL no responde (F49).
- **Mapeo por destino:**
  - Obsidian → `Properties.source-url` (clickeable).
  - Notion API → `page.properties.source-url` (columna `url`).
  - Notion import → literal YAML.
  - AppFlowy → `Properties.source-url`.
  - MD → literal YAML.
  - HTML/PDF → celda `source-url` de `## Metadata` (con link).
  - Flashcards → descartado.
- **Notas:** si la URL no es estable (CDN, ephemeral), usar `source-anchor`
  como anclaje lógico y omitir `source-url`.

### 5.12 `retrieved`  {#prop-retrieved}

- **Tipo:** date ISO 8601 (`YYYY-MM-DD`).
- **Obligatoriedad:** obligatoria en `chapter-digest`, `version-delta`,
  `practice` (cuando hay fuente externa); recomendada en todos los tipos con
  fuente.
- **Descripción:** fecha en que se obtuvo la fuente.
- **Validación:** INV-P6 (formato estricto `YYYY-MM-DD`).
- **Mapeo por destino:**
  - Obsidian → `Properties.retrieved`.
  - Notion API → `page.properties.retrieved` (columna `date`).
  - Notion import → literal YAML.
  - AppFlowy → `Properties.retrieved`.
  - MD → literal YAML.
  - HTML/PDF → celda `retrieved` de `## Metadata`.
  - Flashcards → descartado.
- **Notas:** usado por el ledger (F15) para detectar obsolescencia si la
  fuente caduca o cambia de URL.

### 5.13 `language`  {#prop-language}

- **Tipo:** enum (4 valores).
- **Obligatoriedad:** recomendada en todos los tipos.
- **Descripción:** idioma del contenido de la nota.
- **Valores:** `es` (español), `en` (inglés), `es-en` (bilingüe, español primario),
  `en-es` (bilingüe, inglés primario).
- **Mapeo por destino:**
  - Obsidian → `Properties.language`; el agente puede usar el valor para
    configurar spellcheck.
  - Notion API → `page.properties.language` (`select`).
  - Notion import → literal YAML.
  - AppFlowy → `Properties.language`.
  - MD → literal YAML.
  - HTML/PDF → atributo `lang="..."` en `<html>` + celda en `## Metadata`.
  - Flashcards → descartado; el deck no cambia por idioma.
- **Notas:** `es-en` significa que la nota tiene secciones en ambos idiomas
  (típicamente cuando el SDM es EN y la salida esperada es bilingüe).
  El idioma de la prosa, las marcas bilingües `[[en:term]]` / `[[es:term]]`
  y el bloque `## Procedencia` al pie se normativizan en F101
  (`references/06-writing/i18n-and-citation.md`).

### 5.14 `coverage`  {#prop-coverage}

- **Tipo:** enum (3 valores).
- **Obligatoriedad:** recomendada en todos los tipos.
- **Descripción:** nivel de cobertura del SDM en la nota.
- **Valores:**
  - `full` — la nota cubre el 100% de las unidades must-keep del SDM.
  - `partial` — la nota cubre una parte (ej. solo los capítulos 1-3 de un libro
    de 20).
  - `summary` — la nota es un resumen ejecutivo (no apta para estudio
    exhaustivo).
- **Mapeo por destino:**
  - Obsidian → `Properties.coverage`.
  - Notion API → `page.properties.coverage` (`rich_text`).
  - Notion import → literal YAML.
  - AppFlowy → `Properties.coverage`.
  - MD → literal YAML.
  - HTML/PDF → celda `coverage` de `## Metadata` (§7).
  - Flashcards → descartado.
  visual (token semántico) cuando es `partial` o `summary`.
- **Notas:** el ledger (F15) cierra solo cuando `coverage = full` para todas
  las unidades must-keep.

### 5.15 `difficulty`  {#prop-difficulty}

- **Tipo:** enum (5 valores numéricos).
- **Obligatoriedad:** recomendada en tipos con contenido técnico
  (`concept`, `api-reference`, `procedure`, `configuration`,
  `error-troubleshooting`, `syntax`, `data-model`, `cheatsheet`,
  `practice`).
- **Descripción:** nivel de dificultad del contenido (escala 1-5).
- **Valores:** `1` (introductorio, sin prerrequisitos), `2` (básico,
  requiere familiaridad), `3` (intermedio, requiere práctica), `4` (avanzado,
  requiere experiencia), `5` (experto, requiere dominio profundo).
- **Mapeo por destino:**
  - Obsidian → `Properties.difficulty`.
  - Notion API → `page.properties.difficulty` (`rich_text`).
  - Notion import → literal YAML.
  - AppFlowy → `Properties.difficulty`.
  - MD → literal YAML.
  - HTML/PDF → celda `difficulty` de `## Metadata` (§7).
  - Flashcards → descartado.
  barra de progreso visual con el número.
- **Notas:** escala relativa al corpus, no absoluta. Una nota `1` para
  PostgreSQL puede ser `3` para SQL general.

### 5.16 `review-next`  {#prop-review-next}

- **Tipo:** date ISO 8601 (`YYYY-MM-DD`).
- **Obligatoriedad:** recomendada en tipos con复习 (`concept`, `procedure`,
  `cheatsheet`, `practice`); opcional en tipos referenciales (`api-reference`,
  `index-moc`, `glossary-term`).
- **Descripción:** próxima fecha de repaso de la nota (controlada por F62
  flashcards).
- **Validación:** INV-P6; debe ser fecha futura al momento de redactar.
- **Mapeo por destino:**
  - Obsidian → `Properties.review-next`; el renderer de MOC puede marcar
    notas vencidas.
  - Notion API → `page.properties.review-next` (columna `date`).
  - Notion import → literal YAML.
  - AppFlowy → `Properties.review-next`.
  - MD → literal YAML.
  - HTML/PDF → celda `review-next` de `## Metadata`.
  - Flashcards → campo de scheduling de la card (controla cuándo aparece
    en el deck).
- **Notas:** si la nota cambia de versión del producto, actualizar
  `review-next` para forzar un repaso. F103 (`references/09-study/error-log.md`)
  reutiliza `review-next` también por entrada del living-doc de errores
  propios (`study/errors/<dominio>.md`), controlando el scheduling de
  las tarjetas prioritarias (tag `priority-error`).

### 5.17 `aliases`  {#prop-aliases}

- **Tipo:** array of string.
- **Obligatoriedad:** recomendada en `concept`, `glossary-term`; opcional en
  resto.
- **Descripción:** nombres alternativos de la nota (sinónimos, abreviaturas).
- **Validación:** cada alias en kebab-case; sin duplicados; sin colisiones con
  otros `title` del corpus.
- **Mapeo por destino:**
  - Obsidian → `Properties.aliases`; Obsidian los trata como wikilinks
    equivalentes al `title`.
  - Notion API → `page.properties.aliases` (`multi_select`).
  - Notion import → literal YAML (Noción no resuelve aliases).
  - AppFlowy → `Properties.aliases`.
  - MD → literal YAML.
  - HTML/PDF → celda `aliases` (lista separada por comas) de `## Metadata`.
  - Flashcards → descartado.
- **Notas:** el renderer de MOC usa `aliases` para resolver búsquedas; el
  agente debe evitar duplicar `title` en `aliases`.

### 5.18 `related`  {#prop-related}

- **Tipo:** array of string (cada elemento es `note_id` o `term_id`).
- **Obligatoriedad:** recomendada en `concept`, `comparison`, `index-moc`;
  opcional en resto.
- **Descripción:** enlaces a otras notas o términos del corpus.
- **Validación:** cada id existe en el corpus (F49 lo verifica); formato
  kebab-case o snake_case consistente.
- **Mapeo por destino:**
  - Obsidian → `Properties.related`; cada id se renderiza como wikilink.
  - Notion API → `page.properties.related` (`relation` a otras páginas o
    términos).
  - Notion import → literal YAML.
  - AppFlowy → `Properties.related`.
  - MD → literal YAML.
  - HTML/PDF → celda `related` (lista de links) de `## Metadata`.
  - Flashcards → descartado.
- **Notas:** un `id` que no existe genera warning (F49 §11.5) pero no
  bloquea; el renderer marca el enlace como roto.

### 5.19 `summary`  {#prop-summary}

- **Tipo:** string (1 línea, ≤ 200 chars, sin saltos de línea, sin caracteres de control).
- **Universalidad:** obligatoria en `status: published`; opcional en `status: draft` (F75).
- **Descripción:** el TL;DR de la nota en una línea. Aparece en la primera fila de la
  cabecera `## Cabecera` (definida en `references/07-visual/note-templates.md` §2).
  Es el campo más visible tras `title`; el agente debe generarlo como destilación
  semántica del `## TL;DR` (L1) o reescribirlo manualmente si la nota es muy densa.
- **Validación:** ≤ 200 chars; sin `\n`, `\r`, `\t`; sin caracteres de control
  (rangos U+0000-U+001F y U+007F-U+009F). El parser rechaza silenciosamente
  caracteres de control pero NO los imprime (INV-P10).
- **Mapeo por destino:**
  - Obsidian → `Properties.summary` (visible en el panel); también se renderiza
    en la `## Cabecera` (F75) como bloque visible.
  - Notion API → `page.properties.summary` (columna `rich_text`).
  - Notion import → literal YAML al inicio.
  - AppFlowy → `Properties.summary`.
  - MD → literal YAML; el renderer también emite `## Cabecera` con tabla 2-col.
  - HTML/PDF → celda `summary` de `## Cabecera` (fusionada con la tabla
    `## Metadata` existente per F75 D6).
  - Flashcards → descartado en el anverso; aparece como hint opcional
    en el reverso de la card (debajo de la respuesta, en letra pequeña).
- **Notas:** si la nota es muy corta (un solo bloque párrafo), el `summary`
  puede coincidir con el `## TL;DR` literal. El agente nunca debe truncar
  a media frase; prefiere indicar el corte con `…` o reescribir.

### 5.20 `reading-time-minutes`  {#prop-reading-time}

- **Tipo:** int ≥ 1.
- **Universalidad:** obligatoria en `status: published`; opcional en
  `status: draft` (F75).
- **Descripción:** tiempo estimado de lectura en minutos. Aparece en la
  última fila de la cabecera `## Cabecera` como "Tiempo de lectura: N min".
  Se calcula al cierre de la nota a 200 palabras/minuto (F75 §8.1) y se
  almacena como propiedad; el agente puede sobreescribirlo manualmente
  si la nota requiere más tiempo (lectura densa con muchos ejemplos o
  cuadros).
- **Validación:** int ≥ 1; sin valores fraccionarios. El parser rechaza
  con error si llega un string, float, o int ≤ 0 (INV-P10). El warning
  R3 del plan F75 (drift > 50% vs cálculo actual) se difiere a F77.
- **Mapeo por destino:**
  - Obsidian → `Properties.reading-time-minutes`; también se renderiza
    en la `## Cabecera` (F75) como bloque visible.
  - Notion API → `page.properties.reading-time-minutes` (columna `number`).
  - Notion import → literal YAML al inicio.
  - AppFlowy → `Properties.reading-time-minutes`.
  - MD → literal YAML; el renderer también emite `## Cabecera` con tabla 2-col.
  - HTML/PDF → celda `reading-time-minutes` de `## Cabecera`.
  - Flashcards → descartado (no aporta a la memorización).
- **Notas:** la fórmula canónica es `ceil(palabras_cuerpo / 200)` con
  mínimo 1. El script `scripts/util/reading_time.py` (F75-FUERA) la
  implementa; hasta entonces, el validador acepta cualquier int ≥ 1
  escrito por el agente. El override manual se usa cuando la nota tiene
  tablas densas que el ojo lee más lento que la prosa (factor 1.5x típico).

### 5.21 `self-evaluation-types`  {#prop-self-evaluation-types}

- **Tipo:** array of enum (5 valores).
- **Obligatoriedad:** opcional. Recomendada en notas con `note-type` distinto
  de `index-moc` que tengan sección `## Autoevaluación`.
- **Descripción:** tipos de pregunta que la nota declara en su sección
  `## Autoevaluación`. El validador `scripts/validate/self_eval_check.py`
  lo cruza con la tabla cerrada de `references/09-study/self-evaluation.md`
  §3 (mapeo `note-type` × tipos-de-pregunta).
- **Valores:** `recuerdo`, `aplicación`, `diagnóstico`, `decisión`, `predicción`
  (5 valores cerrados, en kebab-case con tildes — literal como aparecen en
  la H3 canónica `### Recuerdo` / `### Aplicación` / etc.; el validador
  normaliza a minúsculas y sin tildes para comparar).
- **Default:** si está ausente, se usa la fila de §3 de `self-evaluation.md`
  correspondiente al `note-type` de la nota.
- **Validación:**
  - Cada valor debe pertenecer a los 5 cerrados.
  - El array debe ser un **superset** del default §3 (nunca subset).
  - `index-moc` debe tener `self-evaluation-types: []` o ausente.
- **Mapeo por destino:**
  - Obsidian → `Properties.self-evaluation-types` (array CSV).
  - Notion API → `page.properties.self-evaluation-types` (`multi_select`).
  - Notion import → literal YAML.
  - AppFlowy → `Properties.self-evaluation-types`.
  - MD → literal YAML.
  - HTML/PDF → celda en `## Metadata` como array CSV.
  - Flashcards → descartado.
- **Notas:** F102 (`references/09-study/self-evaluation.md`) define los
  5 tipos, la tabla cerrada de mapeo y las reglas V1-V7 del validador.
  Esta propiedad existe para que el validador V2 pueda detectar
  notas que añaden tipos no permitidos por su `note-type` o que
  omiten tipos esperados.

### 5.22 `study-path-goals`  {#prop-study-path-goals}

- **Tipo:** array of enum (3 valores).
- **Obligatoriedad:** opcional. Default: `["operate-hoy", "entender-a-fondo"]`
  (la ruta `repasar` solo se incluye si la nota tiene errores propios
  en `study/errors/<domain>.md`).
- **Descripción:** objetivos para los que la nota canónica es relevante.
  F104 (`references/09-study/study-paths.md`) usa esto para filtrar qué
  notas aparecen en cada ruta (`operate-hoy` / `entender-a-fondo` /
  `repasar`).
- **Valores:** `operate-hoy`, `entender-a-fondo`, `repasar` (3 valores
  cerrados, en kebab-case inglés).
- **Default:** si está ausente, F104 incluye la nota en todas las rutas
  aplicables (decidido por la estrategia `shortest`/`broadest` del
  grafo).
- **Validación:**
  - Cada valor debe pertenecer a los 3 cerrados.
  - El array debe ser un **sub-set** del default + `repasar`
    (nunca inventar valores).
- **Mapeo por destino:**
  - Obsidian → `Properties.study-path-goals` (array CSV).
  - Notion API → `page.properties.study-path-goals` (`multi_select`).
  - Notion import → literal YAML.
  - AppFlowy → `Properties.study-path-goals`.
  - MD → literal YAML.
  - HTML/PDF → celda en `## Metadata` como array CSV.
  - Flashcards → descartado.
- **Notas:** F104 (`references/09-study/study-paths.md`) define los
  3 objetivos cerrados, las 7 reglas R-P1 a R-P7, y los scripts
  `study_paths.py` (Q1-Q6) + `study_paths_check.py` (V1-V4).
  Esta propiedad permite al autor sobrescribir la inferencia
  automática del grafo (ej. una nota `practice` que NO es relevante
  para `operate-hoy` puede declararse solo en `entender-a-fondo`).

### 5.23 `goal-profile-override`  {#prop-goal-profile-override}

- **Tipo:** enum (4 valores).
- **Obligatoriedad:** opcional. Default: ausente (usa el `goal_profile`
  global del `profile.yaml`).
- **Descripción:** sobrescribe el `goal_profile` activo del
  `profile.yaml` para esta nota específica. Útil cuando una nota
  pertenece a un perfil por defecto (ej. `work`) pero el estudiante
  la necesita bajo otro perfil (ej. `interview`).
- **Valores:** `hybrid`, `interview`, `certification`, `work` (4
  valores cerrados).
- **Default:** si está ausente, la nota hereda `goal_profile` del
  `profile.yaml`.
- **Validación:**
  - El valor debe pertenecer a los 4 cerrados.
- **Mapeo por destino:**
  - Obsidian → `Properties.goal-profile-override` (enum).
  - Notion API → `page.properties.goal-profile-override` (`select`).
  - Notion import → literal YAML.
  - AppFlowy → `Properties.goal-profile-override`.
  - MD → literal YAML.
  - HTML/PDF → celda en `## Metadata`.
  - Flashcards → descartado.
- **Notas:** F105 (`references/09-study/goal-profiles.md`) define los
  4 perfiles canónicos, las 7 reglas R-G1 a R-G7, y los scripts
  `goal_profiles.py` (P1-P4) + `goal_profile_check.py` (V1-V5).
  Esta propiedad permite al autor sobrescribir el perfil activo nota
  por nota, sin modificar el `profile.yaml` global.

### 5.24 `certification-objective`  {#prop-certification-objective}

- **Tipo:** array of string.
- **Obligatoriedad:** opcional. Default: ausente (la nota no cubre
  ningún `objetivo_id` externo).
- **Descripción:** lista de `objetivo_id` externos que esta nota cubre.
  El validador V2 de `goal_profile_check.py --by-objective <id>`
  consulta esta propiedad para emitir el reporte de cobertura por
  objetivo (F105 §4).
- **Valores:** array de strings (slugs kebab-case). Cada `objetivo_id`
  debe estar declarado en `profile.yaml::certification.objectives[]`.
- **Default:** si está ausente, la nota no contribuye al reporte de
  cobertura por objetivo.
- **Validación:**
  - Cada valor debe ser un slug kebab-case válido (regex `^[a-z0-9][a-z0-9-]{0,63}$`).
  - Si `goal_profile == certification`, se recomienda (no obligatorio)
    declarar ≥ 1 `objetivo_id` para que la nota aporte al reporte.
- **Mapeo por destino:**
  - Obsidian → `Properties.certification-objective` (array CSV).
  - Notion API → `page.properties.certification-objective` (`multi_select`).
  - Notion import → literal YAML.
  - AppFlowy → `Properties.certification-objective`.
  - MD → literal YAML.
  - HTML/PDF → celda en `## Metadata` como array CSV.
  - Flashcards → descartado.
- **Notas:** F105 (`references/09-study/goal-profiles.md`) §4 define el
  reporte JSON canónico por objetivo. Esta propiedad es la fuente
  primaria del reporte (`goal_profile_check.py --profile certification
  --by-objective <id>`).

---

## §6 · Obligatoriedad por tipo de nota

Una entrada por cada uno de los 15 tipos cerrados (F78-F92). Las 5 propiedades
universales (`title`, `note-type`, `status`, `summary`, `reading-time-minutes`)
son obligatorias en `status: published` (INV-P5) y no se repiten aquí; en
`status: draft` solo las 3 primeras son obligatorias (F75).

### 6.1 `concept`  {#type-concept}

- **Descripción:** nota que explica un solo concepto (qué es X, cómo funciona).
- **Obligatorias:** `title`, `note-type`, `status` + (ninguna específica).
- **Recomendadas:** `tags`, `aliases`, `language`, `difficulty`, `review-next`,
  `related`.
- **Opcionales:** el resto.
- **Plantilla:** [`../05-note-types/concept.md`](../05-note-types/concept.md)
  (F78).

### 6.2 `api-reference`  {#type-api-reference}

- **Descripción:** nota de referencia de una API (funciones, métodos, endpoints).
- **Obligatorias:** `title`, `note-type`, `status` + `source`, `source-type`, `product`.
- **Recomendadas:** `source-anchor`, `source-url`, `product-version`,
  `vendor`, `tags`, `language`, `difficulty`, `related`.
- **Opcionales:** `aliases`, `coverage`, `review-next`, `retrieved`.
- **Plantilla:** F79.

### 6.3 `procedure`  {#type-procedure}

- **Descripción:** nota que describe un procedimiento paso a paso.
- **Obligatorias:** `title`, `note-type`, `status` + `source`, `source-type`.
- **Recomendadas:** `source-url`, `product`, `product-version`, `vendor`,
  `review-next`, `difficulty`, `tags`, `related`.
- **Opcionales:** `source-anchor`, `aliases`, `language`, `coverage`,
  `retrieved`.
- **Plantilla:** F80.

### 6.4 `configuration`  {#type-configuration}

- **Descripción:** nota sobre opciones de configuración de un producto.
- **Obligatorias:** `title`, `note-type`, `status` + `source`, `source-type`.
- **Recomendadas:** `product`, `product-version`, `source-url`, `vendor`,
  `tags`, `language`, `difficulty`, `related`.
- **Opcionales:** el resto.
- **Plantilla:** F81.

### 6.5 `error-troubleshooting`  {#type-error-troubleshooting}

- **Descripción:** nota sobre un error específico y su diagnóstico.
- **Obligatorias:** `title`, `note-type`, `status` + `source`, `source-type`.
- **Recomendadas:** `product`, `product-version`, `source-url`, `vendor`,
  `tags`, `language`, `difficulty`, `review-next`, `related`.
- **Opcionales:** el resto.
- **Plantilla:** F82.

### 6.6 `architecture`  {#type-architecture}

- **Descripción:** nota sobre la arquitectura de un sistema.
- **Obligatorias:** `title`, `note-type`, `status` + `source`, `source-type`.
- **Recomendadas:** `product`, `product-version`, `source-url`, `vendor`,
  `tags`, `language`, `difficulty`, `related`.
- **Opcionales:** el resto.
- **Plantilla:** F83.

### 6.7 `syntax`  {#type-syntax}

- **Descripción:** nota sobre sintaxis de un lenguaje o DSL.
- **Obligatorias:** `title`, `note-type`, `status` + `source`, `source-type`.
- **Recomendadas:** `product`, `product-version`, `source-url`, `vendor`,
  `tags`, `language`, `difficulty`, `related`.
- **Opcionales:** el resto.
- **Plantilla:** F84.

### 6.8 `data-model`  {#type-data-model}

- **Descripción:** nota sobre un modelo de datos (entidades, relaciones).
- **Obligatorias:** `title`, `note-type`, `status` + `source`, `source-type`.
- **Recomendadas:** `product`, `product-version`, `source-url`, `vendor`,
  `tags`, `language`, `difficulty`, `related`.
- **Opcionales:** el resto.
- **Plantilla:** F85.

### 6.9 `chapter-digest`  {#type-chapter-digest}

- **Descripción:** resumen estructurado de un capítulo entero.
- **Obligatorias:** `title`, `note-type`, `status` + `source`, `source-type`, `retrieved`.
- **Recomendadas:** `source-url`, `vendor`, `product`, `product-version`,
  `tags`, `language`, `coverage`, `related`.
- **Opcionales:** `difficulty`, `review-next`, `aliases`.
- **Plantilla:** F86.

### 6.10 `comparison`  {#type-comparison}

- **Descripción:** nota que compara dos o más alternativas (productos, versiones,
  enfoques).
- **Obligatorias:** `title`, `note-type`, `status` + `source`, `source-type` (uno o varios).
- **Recomendadas:** `source-url`, `tags`, `language`, `difficulty`,
  `related`.
- **Opcionales:** `product`, `product-version`, `vendor`, `aliases`,
  `coverage`, `review-next`, `retrieved`.
- **Plantilla:** F87.

### 6.11 `version-delta`  {#type-version-delta}

- **Descripción:** nota sobre cambios entre versiones de un producto.
- **Obligatorias:** `title`, `note-type`, `status` + `source`, `source-type`, `product`,
  `product-version`.
- **Recomendadas:** `vendor`, `source-url`, `retrieved`, `tags`, `language`,
  `related`.
- **Opcionales:** `difficulty`, `aliases`, `coverage`, `review-next`.
- **Plantilla:** F88.

### 6.12 `glossary-term`  {#type-glossary-term}

- **Descripción:** entrada de glosario para un término.
- **Obligatorias:** `title`, `note-type`, `status` + (ninguna específica; puede o no tener
  fuente).
- **Recomendadas:** `tags`, `aliases`, `related`, `language`.
- **Opcionales:** `source`, `source-type`, `source-anchor`, `coverage`,
  `difficulty`.
- **Plantilla:** F89.

### 6.13 `cheatsheet`  {#type-cheatsheet}

- **Descripción:** hoja de referencia rápida (sin prosa).
- **Obligatorias:** `title`, `note-type`, `status` + (ninguna específica; recomendada pero no
  obligatoria la triada `source`, `source-type`).
- **Recomendadas:** `product`, `product-version`, `source-url`, `tags`,
  `language`, `difficulty`.
- **Opcionales:** el resto.
- **Plantilla:** F90.

### 6.14 `index-moc`  {#type-index-moc}

- **Descripción:** índice de mapa de contenido (lista de enlaces a otras notas).
- **Obligatorias:** `title`, `note-type`, `status` + (ninguna específica).
- **Recomendadas:** `related`, `tags`, `language`, `review-next`.
- **Opcionales:** `source`, `source-type`, `aliases`, `coverage`.
- **Plantilla:** F91.

### 6.15 `practice`  {#type-practice}

- **Descripción:** práctica / laboratorio con entorno y limpieza.
- **Obligatorias:** `title`, `note-type`, `status` + `source`, `source-type`, `product`,
  `product-version`.
- **Recomendadas:** `vendor`, `source-url`, `retrieved`, `difficulty`, `tags`,
  `review-next`, `related`.
- **Opcionales:** `source-anchor`, `aliases`, `language`, `coverage`.
- **Plantilla:** F92.

---

## §7 · Render legible en destinos sin soporte

Cuando el destino no soporta properties nativas (o las soporta parcialmente), el
renderer aplica una estrategia de fallback uniforme: **sección `## Metadata`** al
inicio del documento con una tabla de 2 columnas (`propiedad` | `valor`).

### 7.1 Estrategia de fallback

- **Posición:** la sección se inserta **después** del frontmatter literal (si lo
  hay) y **antes** del primer heading del cuerpo.
- **Contenido:** tabla con 2 columnas; cada fila es una propiedad y su valor.
- **Orden:** primero las obligatorias, luego las recomendadas, luego las
  opcionales, luego las personalizadas (`x-*`, `user-*`) en sub-sección aparte.
- **Visibilidad:** las propiedades marcadas como `internal-only: true`
  (personalizadas) se renderizan en un comentario HTML `<!-- ... -->` o
  equivalente que el lector no ve pero el parser sí recupera.

### 7.2 Comportamiento por destino

| Destino | Soporte nativo | Fallback aplicado |
|---|---|---|
| **Obsidian** | ✅ panel `Properties` | nunca |
| **Notion API** | ✅ `page.properties` | solo si una property no existe como columna en la database destino (config del perfil decide) |
| **Notion import** | ⚠ parcial (YAML literal al inicio) | sección `## Metadata` completa para properties no reconocidas |
| **AppFlowy** | ✅ panel `Properties` | nunca |
| **MD** | ✅ YAML literal | nunca |
| **HTML/PDF** | ❌ no nativo | sección `## Metadata` siempre |
| **Flashcards** | ⚠ solo `title` y `tags` | `title` → campo del deck; resto → `## Metadata` opcional en el anverso |

### 7.3 Ejemplo generado

Para una nota `api-reference` con frontmatter:

```yaml
---
title: "PostgreSQL — Función array_append"
note-type: api-reference
status: published
tags: [type/api-reference, domain/databases, f047]
source: postgresql-16-manual
source-type: manual
product: PostgreSQL
product-version: "16"
vendor: PostgreSQL Global Development Group
source-anchor: chapter-9-functions-array
source-url: https://www.postgresql.org/docs/16/functions-array.html
retrieved: 2026-09-20
language: en
coverage: full
difficulty: 2
aliases: [array-append, array_concat-equivalent]
related: [term:array, note:array-functions-overview]
---
```

El renderer de HTML/PDF genera automáticamente:

```markdown
## Metadata

| propiedad | valor |
| --- | --- |
| title | PostgreSQL — Función array_append |
| note-type | api-reference |
| status | published |
| tags | type/api-reference, domain/databases, f047 |
| source | postgresql-16-manual |
| source-type | manual |
| product | PostgreSQL |
| product-version | 16 |
| vendor | PostgreSQL Global Development Group |
| source-anchor | chapter-9-functions-array |
| source-url | https://www.postgresql.org/docs/16/functions-array.html |
| retrieved | 2026-09-20 |
| language | en |
| coverage | full |
| difficulty | 2 |
| aliases | array-append, array_concat-equivalent |
| related | [[term:array]], [[note:array-functions-overview]] |

---

# cuerpo de la nota...
```

El renderer de Obsidian no genera esta sección (el panel `Properties` la cubre).
El renderer de Notion API tampoco (la database tiene columnas para cada
propiedad).

---

## §8 · Propiedades personalizadas

Las 18 propiedades de §5 son el **conjunto canónico cerrado**. Para metadata
adicional que el usuario o el agente necesitan pero no encaja en las 18, se
admite un sistema de **namespace**:

### 8.1 Prefijos permitidos

- **`x-*`** — extensiones del agente (ej. `x-internal-reviewer: alice`,
  `x-llm-temperature: 0.7`, `x-pipeline-version: 3`).
- **`user-*`** — metadata del usuario final (ej. `user-priority: high`,
  `user-project: data-platform-2026`).

Cualquier clave con un prefijo distinto se rechaza (INV-P2 + parser).

### 8.2 Validación

- Las claves completas (incluido el prefijo) deben cumplir
  `^[a-z][a-z0-9-]*$`.
- Los valores son libres (string, número, array, objeto).
- Si una misma clave `x-*` aparece en ≥ 3 notas distintas, el validador (F49)
  emite warning sugiriendo su promoción al conjunto canónico.

### 8.3 Comportamiento por destino

| Destino | Soporte de personalizadas |
|---|---|
| **Obsidian** | ✅ en `Properties` con prefijo visible |
| **Notion API** | ✅ como columnas `select` o `rich_text` adicionales (config del perfil) |
| **Notion import** | ❌ se pierden |
| **AppFlowy** | ✅ en `Properties` con prefijo visible |
| **MD** | ✅ literal YAML (visible si el lector abre el archivo) |
| **HTML/PDF** | ⚠ en sub-sección `## Metadata extendida` (debajo de la tabla principal) |
| **Flashcards** | ❌ se descartan |

### 8.4 Ejemplo

```yaml
---
title: "..."
note-type: concept
status: draft
x-internal-reviewer: alice
x-pipeline-version: 3
user-priority: high
---
```

El validador (F49) acepta; el renderer las incluye en `## Metadata extendida`
para destinos que no las soportan nativamente (HTML/PDF).

---

## §9 · Anti-patrones transversales

Patrones que el parser (F48) o el validador (F49) marcan como warning o error.

| # | Anti-patrón | Consecuencia | Reemplazo correcto |
|---|---|---|---|
| 1 | `note-type` con valor fuera de los 15 cerrados (`tutorial`, `guide`, `lesson`, etc.) | Parser rechaza (INV-P8). | Usar uno de los 15 cerrados; si no encaja, abrir F44. |
| 2 | `status` con valor fuera de `draft`/`published`/`archived` (`wip`, `todo`, `done`) | Parser rechaza (INV-P8). | Mapeo: `wip` → `draft`; `done` → `published`; `obsolete` → `archived`. |
| 3 | `tags` con strings vacíos (`tags: [type/concept, ""]`) | Parser rechaza (validación §5.4). | Quitar los strings vacíos. |
| 4 | `source-url` que no es URL válida (`source-url: postgresql.org/...` sin esquema) | Validador warning (INV-P7). | Añadir `https://`. |
| 5 | `retrieved` o `review-next` en formato distinto a ISO 8601 (`retrieved: 20/09/2026`) | Parser rechaza (INV-P6). | Usar `YYYY-MM-DD`. |
| 6 | Mezclar namespace canónico con `x-*` (`xtitle`, `xnote-type`) | Parser rechaza (INV-P2). | Las 18 propiedades canónicas van sin prefijo. |
| 7 | Propiedades personalizadas sin namespace (`reviewer: alice`) | Parser rechaza. | Usar `x-internal-reviewer: alice` o `user-reviewer: alice`. |
| 8 | `related` con id que no existe en el corpus (`related: [term:nonexistent]`) | Validador warning (no bloquea). | Verificar el id contra `manifest.json` antes de insertar. |

---

## §10 · Cambios permitidos sin reabrir F47

Cambios que se pueden hacer en `properties.md` sin reabrir la fase:

1. Añadir entrada a §6 (obligatoriedad por tipo) cuando F78-F92 modifiquen las
   reglas de un tipo existente.
2. Refinar §7 (render legible) cuando un destino actualice su capacidad (F8).
3. Añadir entradas a §8 cuando se identifiquen namespaces adicionales
   (ej. `org-*` para organización).
4. Añadir anti-patrones a §9 cuando F49 detecte un patrón nuevo.
5. Añadir entradas a §5 cuando una propiedad canónica refine su validación
   (ej. nuevo formato para `product-version`).

**Reabren F47:**

- Añadir o quitar una propiedad del conjunto canónico cerrado de 18.
- Cambiar el tipo de una propiedad (ej. `tags` de array a string).
- Añadir o quitar un valor de los enums cerrados.
- Cambiar el formato de `retrieved` o `review-next` (INV-P6).
- Cambiar los prefijos de namespace de personalizadas (§8.1).
- Cambiar la estrategia de render legible (§7) cuando el destino no soporta
  properties.

---

## §11 · Cómo verificar

Verificaciones automatizables. Cada una debe pasar antes de cerrar F47.

```bash
# Estructura
wc -l skill/notemartin-study-notes/references/04-authoring/properties.md   # 600-900
rg -c '^### 5\.' skill/notemartin-study-notes/references/04-authoring/properties.md   # 18 (propiedades)
rg -c '^### 6\.' skill/notemartin-study-notes/references/04-authoring/properties.md   # 15 (tipos)

# INV-06 (cero sintaxis de plataforma)
rg '^\s*>\s*\[!' skill/notemartin-study-notes/references/04-authoring/properties.md   # 0

# INV-14 (cero colores literales)
rg '#[0-9-a-fA-F]{3,6}\b' skill/notemartin-study-notes/references/04-authoring/properties.md   # 0

# Coherencia con notemark.md
wc -l skill/notemartin-study-notes/references/04-authoring/notemark.md   # ≤ 159 (no creció)
rg '## §8 · Frontmatter' skill/notemartin-study-notes/references/04-authoring/notemark.md   # §8 ahora es puntero

# Router SKILL.md
rg -c '\[pendiente F47\]' skill/notemartin-study-notes/SKILL.md   # 0

# README 04-authoring
rg '\[pendiente F47\]' skill/notemartin-study-notes/references/04-authoring/README.md   # 0

# Cobertura §5 (mapeo por destino — 7 destinos en cada propiedad)
rg -c '\| Obsidian \|' skill/notemartin-study-notes/references/04-authoring/properties.md   # ≥ 18
rg -c '\| Notion API \|' skill/notemartin-study-notes/references/04-authoring/properties.md   # ≥ 18
rg -c '\| Flashcards \|' skill/notemartin-study-notes/references/04-authoring/properties.md   # ≥ 18

# Fixture
python3 evals/properties-sample/run_eval.py --check-all   # exit 0
```

Tres criterios de la Fase 47 (ROADMAP):

1. **Cada propiedad tiene tipo y mapeo en los siete destinos.** §5 tiene 18 entradas;
   cada una declara tipo + 7-columnas de destino. El fixture verifica.
2. **Los campos obligatorios por tipo están declarados.** §6 tiene 15 entradas; cada
   una lista explícitamente las propiedades obligatorias (universales + específicas).
   El fixture verifica que las 3 universales aparecen en los 15 tipos.
3. **Un destino sin propiedades las renderiza de forma legible.** §7 define la
   estrategia de fallback (`## Metadata` con tabla key/value) + ejemplo generado.
   El fixture verifica que la sección existe en el doc.
