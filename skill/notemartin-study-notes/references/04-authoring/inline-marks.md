# Inline marks — `references/04-authoring/inline-marks.md`

> Documento normativo de la Fase 46 del roadmap. Catálogo operativo de las 6 marcas
> inline obligatorias y 3 de apoyo del formato NoteMark: sintaxis, cuándo se insertan,
> densidad de citación, primera aparición de términos, comportamiento por destino,
> reglas de legibilidad y la regla "no más de una vez por bloque".
>
> Documentos relacionados:
> - [`notemark.md`](notemark.md): gramática legible, directivas de bloque (F45),
>   frontmatter y layer markers.
> - [`notemark.ebnf`](notemark.ebnf): gramática formal (reglas 49-68 son la fuente
>   normativa de las marcas inline; **no se duplica aquí**).
> - [`ir-spec.md`](ir-spec.md): 13 nodos inline del Note IR (F14) a los que cada
>   marca mapea.
> - [`block-directives.md`](block-directives.md): INV-D1 (F45) obliga a que toda
>   admonition fáctica lleve `{src:}`; este doc la generaliza a todos los tipos
>   de bloque y la amplía.
> - [`../08-render/capability-matrix.md`](../08-render/capability-matrix.md): los
>   7 destinos y sus capacidades.

## §1 · Propósito y alcance

Este documento es la **referencia operativa** que el agente consulta en L3 cuando
redacta una frase que contiene un hecho fáctico del SDM, un término canónico, un
enlace a otra nota, un placeholder para el usuario, o una marca de origen (derivado
o externo). Responde cinco preguntas por marca:

1. ¿Cuál es su sintaxis exacta y qué errores mecánicos la invalidan?
2. ¿Cuándo se inserta y cuándo **no**?
3. ¿Cómo se ve en cada uno de los 7 destinos?
4. ¿Cuál es la densidad de citación esperada en cada tipo de bloque?
5. ¿Cómo se escribe sin ensuciar la lectura?

`notemark.md` §7 listaba las 6 marcas en una tabla mínima y daba un ejemplo compuesto
de una línea. La Fase 46 las extrae a este documento y añade cinco piezas que faltaban:
**densidad de citación** (§4), **regla de primera aparición** (§5), **tabla SÍ/NO**
para `{src:}` (§6), **comportamiento por destino** (§7), **reglas de legibilidad**
(§8) y la **regla "no más de una vez por bloque"** (§9).

**Frontera con otros documentos:**
- Las directivas de bloque (`:::warning`, `:::example`, etc.) se documentan en
  `block-directives.md` (F45). Las marcas inline pueden aparecer **dentro** de las
  directivas; este doc explica cuáles admite cada una (§10 de F45).
- `{layer:l1|l2|l3}` NO es marca inline de bloque; se documenta en
  [`depth-layers.md`](depth-layers.md) (F51).
- El frontmatter canónico (`title`, `note-type`, etc.) se documenta en
  `properties.md` (F47).
- `[[fn:id]]`, `[[kbd:]]`, `~~x~~` se listan aquí como marcas de apoyo pero su
  desarrollo completo está en `notemark.ebnf` y en F47/F51.

## §2 · Cuándo se aplica

- Cualquier redacción de una nota nueva en L3 que contenga un hecho del SDM, un
  término, un enlace entre notas, un placeholder, o conocimiento no respaldado.
- Cualquier revisión de una nota que necesite ajustar la densidad de citación.
- Cualquier regeneración desde el IR (vuelta atrás por error de render) que requiera
  re-anclar marcas.

**No se aplica a:** ingesta (F17-F29), render (F54-F60), validación del IR (F49),
publicación (F62). El parser (F48) consume este documento como especificación de las
marcas que debe reconocer.

## §3 · Reglas duras (invariantes)

| ID | Invariante | Si se omite… |
|---|---|---|
| **INV-D1** *(F45)* | Toda admonition fáctica lleva `{src:blk_xxxx}` cuando el hecho viene del SDM. Excepciones: `:::danger`, `:::tip` y `:::external` pueden no llevarlo (advice operativo, knowledge externo). | La nota "explica" lo que la fuente no dice. |
| **INV-I1** *(F46)* | Una instancia específica de marca (mismo `blk_xxxx`, mismo `term:x`, mismo `id`, mismo `{{ph}}`) aparece **una sola vez por bloque**. | Ruido visual y cobertura inflada en el ledger. |
| **INV-I2** *(F46)* | `[[term:nombre]]` se inserta **una sola vez por nota**, en la primera aparición del término. | Sobrecarga visual; el glosario no necesita re-marcaje. |
| **INV-I3** *(F46)* | Cero colores literales en marcas. Tokens via `assets/tokens.json` (F72). | INV-14 violación. |
| **INV-I4** *(F46)* | Ninguna marca menciona una plataforma (`{{ph}}` se renderiza con tokens, no con sintaxis de Obsidian o Notion). | INV-06 violación; el parser colapsa marcas. |
| **INV-I5** *(F46)* | `{src:}` lleva exactamente 12 caracteres hexadecimales en minúsculas. | El parser rechaza el anclaje; la nota pierde trazabilidad. |
| **INV-I6** *(F46)* | `{derived}` y `{external}` son **excluyentes** con `{src:}`. Un párrafo con `{derived}` no lleva `{src:}` simple (puede llevar el atributo `from=` de `:::derived` con la lista de anclajes). | Marca doble: el bloque "es derivado Y está en el SDM", lo cual es contradictorio. |

## §4 · Densidad de citación

Reglas precisas y verificables de cuántas `{src:}` (u otras marcas) debe llevar cada
tipo de bloque. La unidad de citación depende del tipo de bloque.

| Tipo de bloque | Densidad `{src:}` | Razón |
|---|---|---|
| Admonition fáctica (`warning`/`note`/`example`/`security`/`performance`/`version`/`deprecated`/`conflict`) | 1 por admonition | INV-D1 (F45). |
| Tabla de parámetros (`:::param-table`) | 1 por celda con valor fáctico (no en nombres de columna); mínimo 1 por tabla | Criterio #1 ROADMAP. |
| Bloque de código con mensaje de error literal del SDM | 1 por bloque de error | Criterio #1 ROADMAP. |
| Lista de hechos (GFM `1.` / `-`) | 1 por ítem fáctico; máximo 1 cada 80 caracteres | Una línea = un hecho = una ancla. |
| Tabla GFM (no `:::param-table`) | 1 por fila con datos del SDM | Mapeo fila ↔ bloque SDM. |
| Párrafo de prosa fáctica | 1 por bloque `paragraph` | Cada `paragraph` = 1 unidad atómica. |
| Párrafo `{derived}` | 0 marcas `{src:}` simples; opcionalmente `:::derived from="blk_a,blk_b"` con la lista de anclajes | `{derived}` excluye `{src:}` simple (INV-I6). |
| Párrafo `{external}` | 0; nunca `{src:}` | Excluyente (INV-I6). |
| `:::diagram` (Mermaid reconstruido) | 1 al final del bloque (atributo `src=` o `{src:}` tras el caption) | El diagrama resume el SDM. |
| `:::figure` (imagen raster del SDM) | 1 en la línea `![alt](src){src:blk_figXX}` | La imagen viene del SDM. |
| `:::equation` (fórmula del SDM) | 1 al final o en caption (atributo `src=`) | La fórmula viene del SDM. |
| `:::question` | 1 en la respuesta (no en el heading = pregunta) | Pregunta = redacción propia; respuesta = anclada. |
| `:::step` | 1 por step (en el heading o al final del cuerpo) | Cada step = unidad fáctica. |
| `:::console` | 0 por línea; 1 al final si la sesión tiene anclaje principal | Prompt + output no se citan línea a línea. |
| Frontmatter | 0 (el `source-anchor` del frontmatter ya es anclaje global) | Distinto nivel. |
| Heading | 0 (los headings no llevan anclaje; va en el bloque siguiente si aplica) | El heading es estructura, no contenido fáctico. |
| Caption de figura (`*Figura 1: ...*`) | 0 (el anclaje va en la línea `![alt](src)`) | Caption es metadato. |
| Enlace externo `[texto](url)` | 0 (el link es a un URL, no a un bloque SDM) | Marca equivocada. |

**Densidad objetivo global por nota:** ≥ 0.80 `{src:}` por bloque fáctico (de cada
5 bloques fácticos, ≥ 4 llevan al menos una ancla). El validador (F49) mide esta
densidad; no la exige para cierre en F46 pero la usa para detectar notas con baja
cobertura.

## §5 · Regla de primera aparición de términos

**Regla principal:** `[[term:nombre]]` se inserta **una sola vez por nota**, en la
primera aparición del término canónico.

**Disparadores de "primera aparición":**

1. La primera vez que el término aparece en la nota, en cualquier bloque (heading,
   paragraph, admonition, código, etc.).
2. Si el término ya está en el título de la nota (`frontmatter.title`), se cuenta
   como primera aparición y la marca va en el primer bloque del cuerpo.
3. Si la nota tiene un `:::question` cuyo heading es "¿Qué es X?", el heading cuenta
   como primera aparición de X; la marca puede ir en el heading.

**Cuándo re-marcar (excepciones opt-in):**

- Tras un heading `#` o `##` que re-introduce el término (útil en notas largas con
  ≥ 5 secciones principales). Opt-in vía `frontmatter.re-mark-terms: true`. Default: `false`.
- En un `:::collapsible` que resume otra sección.
- En una `[[note:id]]` cuyo target ya tiene el término marcado.

**Cuándo NO marcar:**

- En una enumeración donde el término aparece como ítem (ej. "Conceptos relacionados:
  MVCC, WAL, [[term:vacuum]], …"). Aquí solo se marca el primer término nuevo.
- En un bloque `code` como nombre de variable o string literal (no se interpreta).
- En un bloque `:::external` (el bloque no es del SDM; los términos no se enlazan).

**Forma del nombre:** kebab-case, coincide con el `term_id` del glosario (F40).
Ej. `[[term:shared-buffers]]`, `[[term:hash-join]]`, `[[term:multiversion-concurrency-control]]`.

**Errores mecánicos:**

| Mal | Bien | Razón |
|---|---|---|
| `[[term: Shared Buffers]]` | `[[term:shared-buffers]]` | Espacios no permitidos. |
| `[[term:shared_buffers]]` | `[[term:shared-buffers]]` | Snake_case no coincide con kebab-case del glosario. |
| `[[shared-buffers]]` | `[[term:shared-buffers]]` | Sin prefijo `term:` colisiona con wikilink Obsidian (INV-06). |
| `[[term:SharedBuffers]]` | `[[term:shared-buffers]]` | CamelCase no permitido. |
| `[[Term:shared-buffers]]` | `[[term:shared-buffers]]` | `term` literal en minúscula (case-sensitive). |

## §6 · Tabla SÍ/NO de `{src:}`

15 situaciones concretas. El agente debe responder SÍ/NO antes de decidir si inserta
la marca. Las excepciones se resuelven por tipo de bloque (§4) o por invariante (§3).

| # | Situación | ¿Lleva `{src:}`? | Razón |
|---|---|---|---|
| 1 | Tabla `:::param-table` con valores del SDM | **Sí** | Criterio #1 ROADMAP. |
| 2 | Bloque de código con mensaje de error literal del SDM | **Sí** | Criterio #1 ROADMAP. |
| 3 | Bloque de código con comando CLI del SDM | **Sí** | Cita textual. |
| 4 | Admonition fáctica (`warning`/`note`/`example`/etc.) | **Sí** | INV-D1 (F45). |
| 5 | Lista de hechos puntuales del SDM | **Sí** (uno por ítem) | §4. |
| 6 | Diagrama Mermaid reconstruido del SDM | **Sí** (al final del bloque) | Resume el SDM. |
| 7 | Figura raster escaneada del SDM | **Sí** (en la línea `![alt](src){src:...}`) | Imagen viene del SDM. |
| 8 | Ecuación del SDM | **Sí** (al final o en caption) | Fórmula viene del SDM. |
| 9 | Console session del SDM | **Opcional** (1 al final si hay anclaje principal) | No línea a línea. |
| 10 | Analogía del agente basada en el SDM | **No** (`{derived}` o `:::derived` en su lugar) | Excluyente (INV-I6). |
| 11 | Conocimiento general fuera del SDM | **No** (`{external}` en su lugar) | Excluyente (INV-I6). |
| 12 | Placeholder `{{nombre}}` | **No** | El placeholder es del usuario. |
| 13 | Frontmatter (`source-anchor`) | **No** | Distinto nivel de anclaje. |
| 14 | Heading `#`/`##`/`###` | **No** (el anclaje va en el bloque siguiente) | Heading es estructura. |
| 15 | Caption de figura (`*Figura 1: ...*`) | **No** (el anclaje va en la línea `![alt](src)`) | Caption es metadato. |

## §7 · Comportamiento por destino (7 destinos)

Las 6 marcas obligatorias se rinden de forma distinta en cada uno de los 7 destinos
(según `capability-matrix.md` §2). Las marcas que el destino no soporte caen al modo
degradado documentado en F8 §4 (no se eliminan del NoteMark; el renderer decide).

| Marca | Obsidian | Notion API | Notion import | AppFlowy | MD | HTML/PDF | Flashcards |
|---|---|---|---|---|---|---|---|
| `{src:blk_xxxx}` | callout inline gris al final + tooltip con anchor | `mention` de página vacía o `code` con fondo gris (`annotations.code`) | se pierde (limitación) | highlight gris via token | literal `{src:blk_xxxx}` | `<span class="source-ref">blk_xxxx</span>` con CSS gris | se descarta |
| `[[term:x]]` | wikilink `[[x]]` (con prefijo `term:` se mantiene como texto) | `link_to_page` o texto con tooltip | se convierte en texto o se pierde | wikilink o tooltip | literal `[[term:x]]` | `<a class="term-ref" href="#glossary-x">x</a>` | literal en anverso; tooltip en reverso |
| `[[note:id]]` | wikilink `[[id]]` | `link_to_page` (si la página existe) | se convierte en texto o se pierde | wikilink | literal `[[note:id]]` | `<a class="note-ref" href="notes/id.html">id</a>` | descartado |
| `{{nombre}}` | `<span style="background:highlight-token">nombre</span>` via CSS | `code` con fondo amarillo (`annotations.code`) | se pierde | highlight amarillo via token | literal `{{nombre}}` | `<span class="placeholder">{{nombre}}</span>` con CSS highlight | se sustituye por `_____` en anverso |
| `{derived}` | `<span class="derived">…</span>` via CSS | `callout` con color semántico derivado (token) | se pierde | highlight via token | literal `{derived}` | `<span class="derived">{derived}</span>` | descartado |
| `{external}` | `<span class="external">…</span>` via CSS | `callout` con color externo (token) | se pierde | highlight via token | literal `{external}` | `<span class="external">{external}</span>` | descartado |

**Colores:** todos via `assets/tokens.json` (INV-I3 / INV-14). Cero literales. Los
nombres `highlight-token`, `derived`, `external` referencian tokens concretos definidos
en F72.

**Marcas "se pierden":** significa que el destino degrada el bloque a texto plano o
lo descarta según F8 §4. La marca sigue presente en el NoteMark y en el IR; no se
elimina. La trazabilidad se conserva porque el `blk_xxxx` sigue en el SDM y en el IR.

**Marcas "descartadas" en flashcards:** el anverso lleva el contenido sin anclajes;
el reverso puede llevar la lista de `blk_xxxx` como referencia. El renderer decide
(F62 flashcards).

## §8 · Reglas de legibilidad

8 reglas operativas para que el cuerpo de la nota no parezca una lista de anclajes.
Cada regla cierra con ejemplo correcto + anti-ejemplo.

| # | Regla | Ejemplo correcto | Anti-ejemplo |
|---|---|---|---|
| 1 | `{src:}` va al final de la proposición, antes del punto. | `MVCC permite lecturas sin bloqueos. {src:blk_a123}` | `MVCC {src:blk_a123} permite lecturas sin bloqueos.` |
| 2 | Máximo 1 `{src:}` por frase. Excepción: `:::conflict` admite 2 (uno por cada lado de la contradicción). | `PostgreSQL usa MVCC. {src:blk_a}` | `PostgreSQL {src:blk_a} usa MVCC {src:blk_b}.` |
| 3 | No apilar 3+ marcas de tipos distintos en la misma frase. | `El optimizador elige Hash Join. [[term:hash-join]] {src:blk_a}` | `El optimizador elige [[term:hash-join]] {src:blk_a} {{ph}} Hash Join.` |
| 4 | `[[term:x]]` solo en la primera aparición (§5); nunca inline en medio de una fórmula o comando. | `[[term:shared-buffers]] es un parámetro.` | `` postgres.conf: shared_buffers [[term:shared-buffers]] = 128MB `` |
| 5 | En listas, la marca va al final del ítem. | `- ``VACUUM`` no bloquea lecturas. {src:blk_c}` | `- ``VACUUM`` {src:blk_c} no bloquea.` |
| 6 | En tablas, la marca va en la última celda de la fila o en una celda dedicada `fuente`. | `\| max_connections \| 100 \| {src:blk_p} \|` | `\| max_connections \| {src:blk_p} \| 100 \|` |
| 7 | `{{placeholder}}` se rodea de contexto que indique al usuario dónde sustituir. | `Conectarse a \`{{host}}:{{port}}\` con usuario \`{{user}}\`.` | `{{host}}` suelto sin contexto. |
| 8 | `{derived}` y `{external}` van al final del párrafo, no al inicio (no rompen el flujo). | `Esta analogía con Git es nuestra. {external}` | `{external} Esta analogía con Git es nuestra.` |

**Regla global:** si una nota con ≥ 50 bloques fácticos acumula > 30 caracteres
de marcas por bloque de promedio, está sobre-anclada. Releer la nota y consolidar:
varias proposiciones en un párrafo con un solo `{src:}` por paragraph (§4).

## §9 · Regla "no más de una vez por bloque"

**Interpretación (confirmada en planificación):** cada **instancia específica** de
una marca aparece una sola vez por bloque. **No** significa "una sola marca de
cualquier tipo por bloque". Un bloque puede llevar simultáneamente `{src:blk_a}` +
`[[term:x]]` + `{{ph}}` si las tres son distintas.

| Marca | Límite por bloque | Verificación mecánica |
|---|---|---|
| Un `blk_xxxx` específico | 1 | `rg -c '\{src:blk_xxxx\}' block.nm` = 1 |
| Un `term:x` específico | 1 | `rg -c '\[\[term:x\]\]' block.nm` = 1 |
| Un `id` de nota específico | ≤ 2 (excepción `:::conflict` lleva 2) | `rg -c '\[\[note:id\]\]' block.nm` ≤ 2 |
| Un `{{ph}}` específico | 1 | `rg -c '\{\{ph\}\}' block.nm` = 1 |
| `{derived}` (literal) | ≤ 1 | `rg -c '\{derived\}' block.nm` ≤ 1 |
| `{external}` (literal) | ≤ 1 | `rg -c '\{external\}' block.nm` ≤ 1 |

**Excepciones documentadas:**

- `:::conflict` admite hasta 2 `{src:}` (uno por cada lado de la contradicción).
  Ver `block-directives.md` §10.10.
- `:::derived` admite hasta 5 anclajes en el atributo `from="blk_a,blk_b,..."`
  (síntesis de varios bloques) — esos anclajes **no** se repiten como `{src:}` inline.

**Consecuencia de violar la regla:** el parser (F48) acepta la nota pero el ledger
(F15) marca el bloque como "anclaje duplicado" y el validador (F49) lo reporta. La
nota no se rechaza; el ruido visual es el coste.

---

## §10 · Catálogo de marcas

Una subsección por marca con la plantilla: nodo IR → sintaxis → cuándo se inserta →
cuándo NO → ejemplo canónico → anti-ejemplo → errores mecánicos comunes.

### 10.1 `{src:blk_xxxxxxxxxxxx}`  {#mark-src}

- **Categoría:** source-ref.
- **Nodo IR:** `source-ref` con `block_id` (hex 12) + `source_hash` (hex 64).
- **Sintaxis:** `{src:` + 12 caracteres hexadecimales en minúsculas + `}`. Sin espacios.
- **Cuándo se inserta:** cada hecho fáctico del SDM que se traduce a prosa (criterio #1
  cubre tablas de parámetros y códigos de error explícitamente; §4 cubre los demás
  tipos de bloque).
- **Cuándo NO se inserta:** en bloques `{derived}` o `{external}` (excluyente INV-I6);
  en headings (estructura, no contenido); en frontmatter (`source-anchor` ya ancla).

````notemark
PostgreSQL usa MVCC para permitir lecturas concurrentes sin bloqueos. {src:blk_a123}
````

````notemark
PostgreSQL usa MVCC para permitir lecturas concurrentes sin bloqueos.
````

> Por qué el anti-ejemplo está mal: el hecho viene del SDM (atribución "PostgreSQL usa
> MVCC") pero no lleva `{src:}`. Sin ancla, la nota pierde trazabilidad y el ledger
> reporta cobertura incompleta.

**Errores mecánicos comunes:**

- `{src:blk_a123}` (10 hex) — longitud incorrecta; el parser rechaza.
- `{src:BLK_A1234567}` (mayúsculas) — el parser exige minúsculas (INV-I5).
- `{src:blk-a123}` (con guión) — el parser solo acepta hex puro.
- `{ src:blk_a123 }` (con espacios) — sintaxis inválida.
- `{{src:blk_a123}}` (con doble llave) — confunde con `{{placeholder}}`.

### 10.2 `[[term:nombre]]`  {#mark-term}

- **Categoría:** term-ref.
- **Nodo IR:** `term-ref` con `text`, `term_id` (kebab-case), `capability: link-term`.
- **Sintaxis:** `[[term:` + nombre en kebab-case + `]]`. Sin espacios en el nombre.
- **Cuándo se inserta:** primera aparición del término en la nota (§5); puede ir en
  heading, paragraph o bloque donde aparece por primera vez.
- **Cuándo NO se inserta:** en bloques `{external}`; en nombres de variable dentro
  de `code`; en cada nueva aparición del término (solo la primera; ver INV-I2).

````notemark
[[term:shared-buffers]] es el parámetro de PostgreSQL que controla la memoria dedicada al caché de páginas.
````

````notemark
shared_buffers es el parámetro de PostgreSQL que controla la memoria dedicada al caché de páginas.
````

> Por qué el anti-ejemplo está mal: la primera aparición del término no lleva la marca
> `[[term:shared-buffers]]`. El glosario no se enlaza automáticamente y la nota pierde
> la conexión con F40.

**Errores mecánicos comunes:**

- `[[term: Shared Buffers]]` (espacios) — sintaxis inválida.
- `[[term:shared_buffers]]` (snake_case) — no coincide con `term_id` del glosario.
- `[[shared-buffers]]` (sin prefijo) — colisiona con wikilink Obsidian (INV-I4).
- `[[term:SharedBuffers]]` (CamelCase) — kebab-case es la norma.
- `[[Term:shared-buffers]]` (mayúscula en prefijo) — `term` es case-sensitive.

### 10.3 `[[note:id]]`  {#mark-note}

- **Categoría:** link-note.
- **Nodo IR:** `link-note` con `text`, `target: note_id`, `capability: link-note`.
- **Sintaxis:** `[[note:` + identificador estable + `]]`. Sin espacios en el id.
- **Cuándo se inserta:** cuando la nota referencia explícitamente a otra nota del
  corpus (no a un bloque, no a un término).
- **Cuándo NO se inserta:** si la referencia es a un bloque del SDM → `{src:}`; si
  es a un término → `[[term:]]`; si es a una URL externa → `[texto](url)`.

````notemark
Ver la nota de referencia sobre índices hash para más detalle. [[note:hash-indexes]]
````

````notemark
Ver la nota sobre índices hash para más detalle.
````

> Por qué el anti-ejemplo está mal: la referencia a otra nota no lleva `[[note:id]]`.
> El renderer no puede enlazar; la nota queda huérfana y el grafo de notas pierde un
> arco.

**Errores mecánicos comunes:**

- `[[note:hash indexes]]` (espacios en el id) — el id debe ser kebab-case o
  snake_case, sin espacios.
- `[[note:]]` (id vacío) — sin target, el renderer no sabe a dónde enlazar.
- `[[note:hash-indexes]]` con id que no existe en el corpus — el renderer reporta
  enlace roto (F49).
- `[[hash-indexes]]` (sin prefijo `note:`) — colisiona con wikilink Obsidian
  (INV-I4); no se distingue de `[[term:]]`.

### 10.4 `{{nombre}}`  {#mark-placeholder}

- **Categoría:** placeholder.
- **Nodo IR:** `placeholder` con `text` (kebab-case), `default_value?` opcional.
- **Sintaxis:** `{{` + nombre en kebab-case o snake_case + `}}`. Sin espacios.
- **Cuándo se inserta:** cuando el SDM tiene un valor configurable por el usuario
  (host, puerto, nombre de tabla, ruta de archivo, etc.) y la nota debe distinguir
  el literal del valor sustituible.
- **Cuándo NO se inserta:** si el valor es fijo y conocido (no se sustituye); si el
  SDM ya da el valor concreto; si la marca confundiría al lector sobre qué sustituir.

````notemark
Conectarse a `{{host}}:{{port}}` con el usuario `{{db-user}}` y la base `{{db-name}}`.
````

````notemark
Conectarse a localhost:5432 con el usuario postgres y la base mydb.
````

> Por qué el anti-ejemplo está mal: los valores están hardcoded; el lector no puede
> adaptar el comando a su entorno. Si el SDM da ejemplos concretos, deben ir en una
> admonition o collapsibles; en el flujo principal van placeholders.

**Errores mecánicos comunes:**

- `{{host name}}` (espacios) — el parser rechaza; el nombre debe ser kebab-case.
- `{{host}}` sin contexto — el lector no sabe qué sustituir (regla §8 #7).
- `{{HOST}}` (mayúsculas) — kebab-case es la norma.
- `{host}` (una sola llave) — sintaxis inválida; el parser no lo reconoce como
  placeholder.
- Mezclar placeholder con `{src:}` en la misma palabra: `{{ {src:blk_a} }}` —
  anti-patrón; los placeholders son para el usuario, no para el SDM.

### 10.5 `{derived}`  {#mark-derived}

- **Categoría:** derived-mark.
- **Nodo IR:** `derived` (inline).
- **Sintaxis:** literal `{derived}` (sin parámetros, sin atributos).
- **Cuándo se inserta:** al final de un párrafo que es síntesis del agente basada en
  varios bloques del SDM (analogía propia, diagrama resumen, tabla comparativa
  construida).
- **Cuándo NO se inserta:** si el contenido es literal del SDM → `{src:}` en su
  lugar; si es conocimiento de fuera del SDM → `{external}`; si es una analogía
  menor en medio de un párrafo fáctico → no usar marca, escribir la analogía dentro
  del flujo y usar `{derived}` solo si es un párrafo entero.

````notemark
El optimizador de PostgreSQL funciona como un planificador de proyectos: cada
consulta es un proyecto y el optimizador elige el orden de ejecución más barato
según las estadísticas disponibles. {derived}
````

````notemark
El optimizador de PostgreSQL funciona como un planificador de proyectos. {derived} {src:blk_a123}
````

> Por qué el anti-ejemplo está mal: combina `{derived}` con `{src:}` simple. Son
> excluyentes (INV-I6): si el bloque es derivado (síntesis), no lleva anclaje
> simple; debe llevar `:::derived from="blk_a,blk_b"` o el atributo `from` en
> `:::derived` con la lista de anclajes.

**Errores mecánicos comunes:**

- `{ derived }` (con espacios) — sintaxis inválida.
- `{DERIVED}` (mayúsculas) — case-sensitive; solo minúsculas.
- `{derived}` al inicio del párrafo — rompe el flujo (regla §8 #8).
- Apilar `{derived}` con `{external}` en el mismo párrafo — son excluyentes entre
  sí también.

### 10.6 `{external}`  {#mark-external}

- **Categoría:** external-mark.
- **Nodo IR:** `external` (inline).
- **Sintaxis:** literal `{external}` (sin parámetros, sin atributos).
- **Cuándo se inserta:** al final de un párrafo que contiene conocimiento del agente
  no basado en el SDM (analogía traída de otro dominio, ejemplo inventado,
  comparación con un producto externo).
- **Cuándo NO se inserta:** si el contenido es literal del SDM → `{src:}`; si es
  síntesis basada en el SDM → `{derived}`.

````notemark
Esta analogía con Git es nuestra, no del libro. {external}
````

````notemark
El control de versiones funciona como Git. {external} {src:blk_s789}
````

> Por qué el anti-ejemplo está mal: combina `{external}` con `{src:}`. Si lleva
> `{src:blk_s789}`, el contenido sí viene del SDM y debe usar otra marca (típicamente
> `:::note` o `:::tip` con su ancla), no `{external}`.

**Errores mecánicos comunes:**

- `{ external }` (con espacios) — sintaxis inválida.
- `{EXTERNAL}` (mayúsculas) — case-sensitive.
- `{external}` al inicio del párrafo — rompe el flujo (regla §8 #8).
- `{external}` para "este párrafo es externo" cuando realmente se basa en el SDM —
  confunde la trazabilidad.

### 10.7 `[[fn:id]]` (footnote-ref, marca de apoyo)

- **Categoría:** footnote-ref.
- **Nodo IR:** `footnote-ref` con `id` + `text`.
- **Sintaxis:** `[[fn:` + id estable + `]]`.
- **Cuándo se inserta:** para notas al pie con referencias bibliográficas o
  aclaraciones que no rompen el flujo principal.
- **Cuándo NO se inserta:** para aclaraciones que sí son contenido principal →
  `:::note`; para referencias externas → `[texto](url)`.

> El desarrollo completo (formato del footnote, numeración) se difiere a F47
> properties o a un F46-bis si surge fricción. Esta entrada existe para que
> `notemark.ebnf` y este doc estén alineados.

### 10.8 `[[kbd:Ctrl+S]]` (keyboard, marca de apoyo)

- **Categoría:** keyboard.
- **Nodo IR:** `keyboard` con `combo`.
- **Sintaxis:** `[[kbd:` + combinación de teclas + `]]`. Separador estándar `+` o `-`.
- **Cuándo se inserta:** al describir un atajo de teclado del SDM (ej. "guardar con
  Ctrl+S").
- **Cuándo NO se inserta:** para atajos del lector (que el SDM no menciona) → no
  usar la marca.

> El desarrollo (estilos por SO: Mac vs Windows, separador normalizado) se difiere
> a F51 o F62 (renderers). Esta entrada existe para coherencia con `notemark.ebnf`.

### 10.9 `~~texto~~` (deleted, marca de apoyo)

- **Categoría:** deleted.
- **Nodo IR:** `deleted` con `text`.
- **Sintaxis:** `~~` + texto + `~~` (CommonMark GFM).
- **Cuándo se inserta:** para marcar texto obsoleto, removido o desaconsejado que
  sigue presente en una versión anterior del SDM (típicamente en `:::version` o
  `:::deprecated`).
- **Cuándo NO se inserta:** para tachar texto del agente como "esto no aplica" —
  eso es opinión, usar `:::note` o quitar el texto.

> El desarrollo (relación con `:::deprecated`, `:::version`) se documenta en F45
> `block-directives.md` §10.8 y §10.9. Esta entrada existe por completitud.

---

## §11 · Anti-patrones transversales

Patrones que cruzan varias marcas y que el parser (F48) o el validador (F49)
marcan como warning.

| # | Anti-patrón | Consecuencia | Reemplazo correcto |
|---|---|---|---|
| 1 | `{src:}` sin `blk_xxxx` válido (no es hex de 12) | El parser rechaza el anclaje; la nota pierde trazabilidad. | Verificar longitud (12) y caracteres (`[0-9a-f]{12}`) antes de insertar. |
| 2 | `[[note:id]]` con un id que no existe en el corpus | El renderer reporta enlace roto (F49); el grafo de notas tiene arcos huérfanos. | Verificar el id contra el `manifest.json` antes de insertar. |
| 3 | `{{placeholder}}` que parece texto normal (sin nombre distintivo) | El lector no sabe qué sustituir; la nota no es portable. | Usar nombre kebab-case que indique el rol (`{{host}}`, `{{db-name}}`). |
| 4 | Apilar 3+ marcas en la misma frase (`{src:} [[term:]] {{ph}}`) | Rompe el flujo de lectura; el lector pierde la idea principal. | Mover una marca al final; consolidar las demás en el bloque siguiente. |
| 5 | Marcar `[[term:x]]` en lugar del título cuando el término ya está en el `title` del frontmatter | Marca redundante; el glosario ya sabe que el término existe. | Quitar la marca del título; si la primera aparición del cuerpo es diferente, marcar ahí. |
| 6 | Usar `{external}` para parafrasear algo que sí está en el SDM | Atribución incorrecta; el bloque debería llevar `{src:}`. | Reemplazar por `:::note` o `:::tip` con `{src:blk_xxxx}`. |
| 7 | Marcar `[[term:x]]` dentro de un bloque `{external}` | El término no es del SDM; el glosario no debe enlazarlo desde aquí. | Quitar la marca; los términos en bloques externos no se enlazan. |
| 8 | Repetir `{src:blk_xxxx}` dentro del mismo bloque | Ruido; viola INV-I1. | Consolidar las proposiciones en un párrafo con un solo `{src:}`. |

---

## §12 · Cambios permitidos sin reabrir F46

Cambios que se pueden hacer en `inline-marks.md` sin reabrir la fase:

1. Añadir fila a §6 (tabla SÍ/NO) cuando se detecte un nuevo patrón recurrente en
   F49.
2. Refinar §7 cuando un destino actualice su capacidad (F8).
3. Refinar §4 (densidad) cuando F15 (ledger) refine las métricas y la densidad
   objetivo cambie.
4. Añadir anti-patrones a §11 cuando F49 detecte un patrón nuevo.
5. Actualizar §10 con sub-entradas cuando F47/F51 desarrollen las marcas de apoyo
   (`[[fn:id]]`, `[[kbd:]]`, `~~x~~`).
6. Añadir marcas de apoyo adicionales (sin contar como obligatorias) si surgen de
   F12 o F14 sin romper la gramática.

**Reabren F46:**

- Cambiar la lista cerrada de 6 marcas obligatorias.
- Redefinir la regla de primera aparición (§5, INV-I2).
- Cambiar la regla "1 instancia por bloque" (§9, INV-I1).
- Levantar la prohibición INV-I4 (sintaxis de plataforma) dentro de este doc.
- Introducir marca que rompa compat con el IR (F14) o la gramática EBNF (F12).

---

## §13 · Cómo verificar

Verificaciones automatizables. Cada una debe pasar antes de cerrar F46.

```bash
# Estructura
wc -l skill/notemartin-study-notes/references/04-authoring/inline-marks.md   # 400-500
rg -c '^### 10\.' skill/notemartin-study-notes/references/04-authoring/inline-marks.md   # 9 (6 obligatorias + 3 apoyo)

# INV-06 / INV-I4 (cero sintaxis de plataforma en marcas fuera de bloques de código)
rg '^\s*>\s*\[!' skill/notemartin-study-notes/references/04-authoring/inline-marks.md   # 0
rg -c '^### 10\.7|^### 10\.8|^### 10\.9' skill/notemartin-study-notes/references/04-authoring/inline-marks.md   # 3 (marcas de apoyo documentadas)

# INV-14 / INV-I3 (cero colores literales)
rg '#[0-9-a-fA-F]{3,6}\b' skill/notemartin-study-notes/references/04-authoring/inline-marks.md   # 0

# Coherencia con notemark.md
wc -l skill/notemartin-study-notes/references/04-authoring/notemark.md   # ≤ 158 (no creció)
rg -c '^### Marcas inline|## §7 ·' skill/notemartin-study-notes/references/04-authoring/notemark.md   # §7 ahora es puntero

# Router SKILL.md
rg -c '\[pendiente F46\]' skill/notemartin-study-notes/SKILL.md   # 0

# README 04-authoring
rg '\[pendiente F46\]' skill/notemartin-study-notes/references/04-authoring/README.md   # 0

# Cobertura §7 (7 destinos)
rg -c '\| Obsidian \|' skill/notemartin-study-notes/references/04-authoring/inline-marks.md   # ≥ 6 (filas de la tabla 7×6)
rg -c '\| Notion API \|' skill/notemartin-study-notes/references/04-authoring/inline-marks.md   # ≥ 6
rg -c '\| AppFlowy \|' skill/notemartin-study-notes/references/04-authoring/inline-marks.md   # ≥ 6
rg -c '\| Flashcards \|' skill/notemartin-study-notes/references/04-authoring/inline-marks.md   # ≥ 6

# Cobertura §6 (tabla SÍ/NO)
rg -c '^\| .* \| \*\*Sí\*\* \|' skill/notemartin-study-notes/references/04-authoring/inline-marks.md   # ≥ 5

# Fixture
python3 evals/inline-marks-sample/run_eval.py --check-all   # exit 0
```

Tres criterios de la Fase 46 (ROADMAP):

1. **Toda tabla de parámetros y todo código de error lleva `{src:}`.** §4 + §6 + §10.1
   lo cubren. El fixture verifica que el corpus tenga ejemplos de `:::param-table` y
   `:::example` con códigos de error, ambos con `{src:}`.
2. **Los placeholders se distinguen en los siete destinos.** §7 tiene 6 filas × 7
   columnas (42 celdas), cada celda con su representación o fallback. El fixture
   verifica que las 7 columnas estén presentes.
3. **Las marcas no aparecen más de una vez por bloque.** §9 tiene 6 reglas con
   verificación mecánica. El fixture verifica que la nota-probe no tenga instancias
   duplicadas dentro de ningún bloque.
