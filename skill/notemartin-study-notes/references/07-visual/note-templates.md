# `references/07-visual/note-templates.md` — Plantillas visuales por tipo

> Documento normativo de la **Fase 75**. Define la cabecera canónica
> (5 campos: Resumen, Procedencia, Versión, Estado, Tiempo de lectura),
> el patrón de apertura/cierre común a los 15 tipos de nota, y la
> jerarquía visual (qué va en tabla, qué en callout, qué en prosa).
>
> **Cuándo cargar:** tras decidir el tipo de nota (selector F93); antes
> de redactar la primera sección. Los archivos individuales de cada
> tipo (`references/05-note-types/*.md`, F78-F92) instancian este patrón
> y delegan las reglas comunes aquí.
>
> **Wiring:** tokens canónicos en `references/07-visual/tokens.md` (F72);
> estilo por destino en `references/07-visual/style-mapping.md` (F73);
> snippet CSS en `assets/notemartin.css` (F74); renderizado de la
> cabecera por `scripts/render/_header.py` (F75). Las 2 propiedades
> nuevas universales (`summary`, `reading-time-minutes`) viven en
> `references/04-authoring/properties.md` §5.19-§5.20.

---

## §1 · Propósito y alcance

F75 unifica la estructura visual de las notas. Define:

- Una **cabecera canónica** con 5 campos, visible en los 7 destinos
  (decisión de duplicación intencional: el panel de propiedades nativo
  en Obsidian/Notion API/AppFlowy y la sección `## Cabecera` se ven
  ambos; el panel es la fuente de verdad de la base de datos, la
  sección es la fuente de verdad humana).
- Un **patrón de apertura y cierre común** a los 15 tipos: frontmatter →
  `## Cabecera` → `## TL;DR` → contenido → `## Backlinks` → `## Queries`
  (→ opcional `## Ver también`).
- Una **jerarquía visual** que indica qué bloque de información va en
  tabla, qué en callout, qué en prosa, según el tipo de nota.

**Fuera de alcance:**

- Los 15 archivos individuales de `references/05-note-types/*.md` (F78-F92).
- El cálculo automático de `reading-time-minutes` (script de cierre
  en `scripts/util/reading_time.py`, F75-FUERA; el validador acepta
  cualquier int ≥ 1).
- La densidad visual (longitud de párrafo, frecuencia de callouts) — F76.

---

## §2 · Cabecera canónica

### §2.1 · Formato único (todos los destinos)

La cabecera contiene exactamente **5 campos** en este orden, omitiendo los
vacíos:

| # | Etiqueta | Campo en frontmatter | Tipo |
|---|---|---|---|
| 1 | **Resumen** | `summary` | string (≤ 200 chars) |
| 2 | **Procedencia** | `source` + `source-type` + `source-anchor` + `source-url` + `retrieved` | compuesto |
| 3 | **Versión** | `product` + `product-version` | compuesto |
| 4 | **Estado** | `status` | enum (3: `draft` / `published` / `archived`) |
| 5 | **Tiempo de lectura** | `reading-time-minutes` | int ≥ 1 |

La composición de los campos compuestos (Procedencia, Versión) sigue las reglas
de `scripts/render/_header.py:compute_cabecera_rows`:

- **Procedencia:** `source (source-type) §source-anchor source-url · recuperado YYYY-MM-DD` (con ` · ` como separador; campos vacíos se omiten).
- **Versión:** `product product-version` (o solo uno de los dos si el otro está vacío).

### §2.2 · Mapeo a propiedades

| Campo cabecera | Propiedades frontmatter | Notas |
|---|---|---|
| Resumen | `summary` | F75 §5.19; obligatorio en `status: published` |
| Procedencia | `source` (F47 §5.5), `source-type` (5.6), `source-anchor` (5.10), `source-url` (5.11), `retrieved` (5.12) | source-bearing según §6 de properties.md |
| Versión | `product` (5.8), `product-version` (5.9) | recomendado en tipos con producto comercial |
| Estado | `status` (5.3) | F47 universal estricta (siempre obligatoria) |
| Tiempo de lectura | `reading-time-minutes` (F75 §5.20) | F75 universal; obligatorio en `status: published` |

### §2.3 · Reglas de "Resumen en 1 línea"

- Máximo **200 caracteres** (validador INV-P10 rechaza con error).
- Una sola línea: sin `\n`, `\r`, `\t`; sin caracteres de control.
- El agente puede generarlo como destilación semántica del `## TL;DR` (L1)
  o reescribirlo manualmente si la nota es muy densa.
- Si coincide con el `## TL;DR` literal (notas muy cortas), no es problema
  — se permite la duplicación.
- Nunca truncar a media frase: preferir `…` o reescritura.

---

## §3 · Apertura común (los 15 tipos)

Toda nota se abre con esta secuencia idéntica:

```markdown
---
title: "..."
note-type: <uno de los 15>
status: draft | published
summary: "..."                      # F75 (universal en published)
reading-time-minutes: N              # F75 (universal en published)
tags: [...]                         # opcional
source: "..."                       # si source-bearing
# ... resto de propiedades source-bearing (5-15) ...
---

# {title}

## Cabecera                          # F75: 5 campos visibles

| Campo | Valor |
| --- | --- |
| **Resumen** | ... |
| **Procedencia** | ... |
| **Versión** | ... |
| **Estado** | ... (Publicado (published)) |
| **Tiempo de lectura** | N min |

## TL;DR                              # F51 L1 layer marker (capa 1)

{primer párrafo del L1, ≤ 8 líneas / ≤ 60 palabras, sin {src:}}

{layer:l2}

## {primer H2 específico del tipo}   # Definición | Sintaxis | Procedimiento | ...

{contenido del L2}
```

**Lo que varía entre tipos** es el primer H2 después de `## TL;DR` (§6).
El resto de la apertura es **idéntico** en estructura.

---

## §4 · Cierre común (los 15 tipos)

Toda nota cierra con esta secuencia idéntica:

```markdown
... (cuerpo del L2) ...

{layer:l3}                            # opcional, si la nota es extensa

## Detalle exhaustivo                  # opcional, F51 L3 layer
...

## Backlinks                          # siempre, si edges existen
...

## Queries                            # siempre, si queries están activas
...

## Ver también                        # opcional, si related: está presente
...
```

- `## Backlinks` y `## Queries` son obligatorios si el destino activo
  los soporta (per `references/08-render/contract.md`); si no hay
  backlinks/queries, se omiten sin warning.
- `## Ver también` solo aparece cuando la propiedad `related:` está
  presente en el frontmatter con al menos un id válido.
- El cierre puede tener un párrafo final de "TL;DR reverso" para notas
  muy largas (≥ 50 líneas), pero no es obligatorio.

---

## §5 · Jerarquía visual por tipo

### §5.1 · Reglas generales

| Bloque de información | Forma preferida | Forma aceptable |
|---|---|---|
| Comparativas (X vs Y) | **Tabla GFM** | Lista con bullets |
| Parámetros / configuración | **Tabla GFM** (3-col: nombre, tipo, default) | Lista con bullets |
| Propiedades de un objeto | **Tabla GFM** (2-col: clave, valor) | Definition list |
| Procedimiento secuencial | Lista numerada con `## Procedimiento` | Diagrama de flujo |
| Advertencias operativas | **Callout `warning`** o `danger` (F73) | Prosa en negrita |
| Ejemplos de uso | **Callout `example`** o bloque ```code``` | Prosa con sangría |
| Notas de procedencia | **Callout `external`** o `derived` (F73) | Cita en bloque `>` |
| Definiciones | **Definition list** o `## Definición` con tabla | Prosa |
| Justificaciones / debates | **Prosa** con `{layer:l2}` o `:::collapsible` | Lista con bullets |
| Admonitiones semánticas | **Callout con `severity` F73** | Texto plano |

### §5.2 · Frecuencia mínima de anclaje visual

- Mínimo 1 callout o tabla cada 200 palabras (F76 lo formaliza como R3 en `references/07-visual/density.md`).
- Máximo 3 callouts consecutivos sin prosa intermedia (anti-fatiga; F76 lo formaliza como R4).
- Una nota sin ningún callout ni tabla se considera "lista plana" y se
  reporta como warning en `density.md` (F76).
- Las notas `glossary-term` y `cheatsheet` están exentas (su contenido
  es por definición denso en entradas cortas).

### §5.3 · Cuándo NO usar callouts

- Para enfatizar texto individual → usar `**bold**` o `==highlight==`.
- Para notas inline → usar `[[term:x]]` (F46) o `{{ph}}` (F46).
- Para diferenciar el `## TL;DR` → usar el heading H2 con su capa L1, no callout.
- Para el reverso de flashcards → no hay bloque visible (la respuesta es texto).

---

## §6 · Plantillas de los 15 tipos

Cada tipo se instancia con: frontmatter concreto, apertura específica (primer H2
después de TL;DR), secciones obligatorias, secciones opcionales, cierre, anti-patrones.

### §6.1 · `concept`

- **Frontmatter:** `tags: [type/concept, domain/...]`. `source-bearing` recomendado.
- **Apertura:** `## Definición` (1-2 párrafos; la primera frase es la L1 de TL;DR).
- **Secciones obligatorias:** `## Características` (lista con bullets o tabla si hay > 5), `## Ejemplos` (≥ 1 callout `example`).
- **Secciones opcionales:** `## Historia`, `## Comparativa` (con al menos otro concepto), `## Errores comunes` (callout `warning`).
- **Cierre:** `## Backlinks` + `## Queries` + (si `related:`) `## Ver también`.
- **Anti-patrones:** evitar el bloque "Definición formal con símbolos matemáticos" si la audiencia es operativa; preferir prosa con analogía (F51 §3 anti-ejemplo de L1).
- **Ejemplo mínimo viable:** 25 líneas.

### §6.2 · `api-reference`

- **Frontmatter:** `source-bearing` obligatorio. `product`, `product-version`.
- **Apertura:** `## Sintaxis` (firma completa de la función / endpoint).
- **Secciones obligatorias:** `## Parámetros` (tabla 3-col), `## Respuesta` (tipo + ejemplo), `## Errores` (códigos con tabla o callout `danger`).
- **Secciones opcionales:** `## Ejemplos` (callout `example` con bloque `code`), `## Notas` (callout `note`).
- **Cierre:** `## Backlinks` + `## Queries` + (si `related:`) `## Ver también`.
- **Anti-patrones:** no enumerar errores en prosa; siempre tabla; no documentar
  parámetros op-args con "puede ser X o Y" — enumerar las 2-3 firmas.

### §6.3 · `procedure`

- **Frontmatter:** `source-bearing` recomendado. `tags: [type/procedure]`.
- **Apertura:** `## Procedimiento` (lista numerada, 1-N; cada paso < 5 líneas).
- **Secciones obligatorias:** `## Prerrequisitos` (lista con bullets o tabla), `## Verificación` (cómo saber que funcionó).
- **Secciones opcionales:** `## Troubleshooting` (callout `warning` con casos), `## Notas` (callout `note`).
- **Cierre:** `## Backlinks` + `## Queries`.
- **Anti-patrones:** no usar más de 10 pasos en `## Procedimiento`; partir en sub-procedimientos con `## Procedimiento: <sub>`.

### §6.4 · `configuration`

- **Frontmatter:** `source-bearing` obligatorio. `product` + `product-version` + `vendor`.
- **Apertura:** `## Configuración` (bloque `code` con la config completa comentada).
- **Secciones obligatorias:** `## Parámetros` (tabla 3-col con `default`), `## Ejemplo completo` (callout `example`).
- **Secciones opcionales:** `## Troubleshooting`, `## Valores comunes` (tabla).
- **Cierre:** `## Backlinks` + `## Queries`.

### §6.5 · `error-troubleshooting`

- **Frontmatter:** `source-bearing` obligatorio.
- **Apertura:** `## Síntomas` (lista de mensajes de error exactos que el usuario ve).
- **Secciones obligatorias:** `## Causa raíz` (1-3 párrafos), `## Solución` (pasos numerados), `## Prevención` (cómo evitarlo en el futuro).
- **Secciones opcionales:** `## Diagnóstico adicional` (comandos para confirmar la causa raíz).
- **Cierre:** `## Backlinks` + `## Queries`.
- **Anti-patrones:** no dar "Solución" sin antes establecer "Causa raíz"; es
  un anti-patrón clásico de docs técnicos.

### §6.6 · `architecture`

- **Frontmatter:** `source-bearing` recomendado. `tags: [type/architecture, domain/...]`.
- **Apertura:** `## Vista general` (1 párrafo + opcional diagrama Mermaid `:::diagram`).
- **Secciones obligatorias:** `## Componentes` (tabla o diagrama), `## Interacciones`
  (diagrama de secuencia o tabla), `## Decisiones de diseño` (lista numerada con
  trade-offs).
- **Secciones opcionales:** `## Trade-offs`, `## Alternativas consideradas`.
- **Cierre:** `## Backlinks` + `## Queries` + `## Ver también`.
- **Especial:** puede invocar F51 (capas L1/L2/L3) si la nota es extensa.

### §6.7 · `syntax`

- **Frontmatter:** `source-bearing` obligatorio.
- **Apertura:** `## Sintaxis` (definición formal o gramática BNF/EBNF).
- **Secciones obligatorias:** `## Elementos` (tabla 3-col: token, descripción, ejemplo), `## Semántica` (qué significa cada regla).
- **Secciones opcionales:** `## Ejemplos` (callout `example`), `## Errores` (callout `warning`).
- **Cierre:** `## Backlinks` + `## Queries`.

### §6.8 · `data-model`

- **Frontmatter:** `source-bearing` recomendado.
- **Apertura:** `## Modelo` (diagrama ER o tabla de la entidad principal).
- **Secciones obligatorias:** `## Campos` (tabla 3-col: nombre, tipo, descripción),
  `## Relaciones` (tabla o diagrama).
- **Secciones opcionales:** `## Índices`, `## Restricciones` (callout `warning` con CHECK constraints).
- **Cierre:** `## Backlinks` + `## Queries`.

### §6.9 · `chapter-digest`

- **Frontmatter:** `source-bearing` obligatorio. `coverage: summary` (enum F47).
- **Apertura:** `## Resumen ejecutivo` (1-2 párrafos; el más importante de la nota).
- **Secciones obligatorias:** `## Puntos clave` (lista con 3-7 bullets), `## Detalles` (puede tener varias sub-secciones).
- **Secciones opcionales:** `## Citas textuales` (callout `external`), `## Conexiones` (callout `derived`).
- **Cierre:** `## Backlinks` + `## Queries` + (siempre) `## Ver también`.
- **Especial:** L1 obligatoria y extendida (puede ser > 60 palabras si el capítulo
  es denso); L3 opcional con detalle exhaustivo.

### §6.10 · `comparison`

- **Frontmatter:** `source-bearing` recomendado. `tags: [type/comparison]`.
- **Apertura:** `## Comparativa` (tabla principal con las opciones en filas, criterios en columnas).
- **Secciones obligatorias:** `## Criterios` (lista con bullets explicando cada criterio), `## Veredicto` (1-2 párrafos).
- **Secciones opcionales:** `## Casos de uso` (cuándo elegir cada opción).
- **Cierre:** `## Backlinks` + `## Queries`.

### §6.11 · `version-delta`

- **Frontmatter:** `source-bearing` obligatorio. `product-version` (la versión NUEVA).
- **Apertura:** `## Cambios` (tabla 3-col: tipo, área, descripción; tipo ∈ {added, changed, deprecated, removed, fixed, security}).
- **Secciones obligatorias:** `## Migración` (pasos numerados), `## Breaking changes` (callout `danger` con la lista).
- **Secciones opcionales:** `## Compatibilidad` (tabla con versiones soportadas).
- **Cierre:** `## Backlinks` + `## Queries`.

### §6.12 · `glossary-term`

- **Frontmatter:** `tags: [type/glossary-term]`. Sin `source-bearing` obligatorio
  (puede ser un término auto-definido por el SDM).
- **Apertura:** `## Definición` (1-2 frases; el L1 es esta misma frase).
- **Secciones obligatorias:** `## Ejemplos` (≥ 1 ejemplo de uso real, callout `example`).
- **Secciones opcionales:** `## Términos relacionados` (lista con `[[term:x]]`).
- **Cierre:** `## Backlinks` (obligatorio; cada term es apuntado desde muchas
  notas) + `## Queries`.
- **Anti-patrones:** no hacer la nota más larga de 30 líneas; es un término,
  no un artículo.

### §6.13 · `cheatsheet`

- **Frontmatter:** `source-bearing` recomendado. `tags: [type/cheatsheet]`.
- **Apertura:** `## Comandos` (tabla 3-col: comando, descripción, ejemplo; 10-30 filas).
- **Secciones obligatorias:** `## Atajos` (tabla 2-col) si aplica al dominio.
- **Secciones opcionales:** `## Errores comunes` (callout `warning` con códigos de error).
- **Cierre:** `## Backlinks` + `## Queries`.
- **Exenta** de la frecuencia mínima de callouts (§5.2) — la tabla es el
  contenido principal.

### §6.14 · `index-moc`

- **Frontmatter:** `tags: [type/index-moc]`. Sin `source-bearing` (es un índice,
  no una nota source-bearing).
- **Apertura:** `## Índice` (lista de links a las notas del MOC, agrupadas por
  sección H2).
- **Secciones obligatorias:** `## Pendientes` (lista de notas en `status: draft` que pertenecen al MOC).
- **Secciones opcionales:** `## Próximas incorporaciones` (notas planeadas en el Note Plan).
- **Cierre:** sin `## Backlinks` (la nota ES el destino de los backlinks).
- **Anti-patrones:** no incluir contenido fáctico en el MOC; solo links a otras notas.

### §6.15 · `practice`

- **Frontmatter:** `source-bearing` recomendado. `difficulty` (1-5).
- **Apertura:** `## Enunciado` (1 párrafo con el problema a resolver; el L1 es este mismo párrafo).
- **Secciones obligatorias:** `## Solución` (pasos numerados o bloque `code`), `## Verificación` (cómo saber que la solución es correcta).
- **Secciones opcionales:** `## Pistas` (callout `tip` con pistas progresivas), `## Variantes` (otras formas de resolver).
- **Cierre:** `## Backlinks` + `## Queries`.
- **Exenta** de la frecuencia mínima de callouts; el contenido es procedural.

---

## §7 · Renderizado de la cabecera en los 7 destinos

| Destino | Cabecera rendering | Panel de propiedades | Notas |
|---|---|---|---|
| **Obsidian** | Callout nativo `> [!info] **Cabecera**` con 5 bullets | Sí (Properties panel) | Duplicación intencional (D6); el panel es la fuente de verdad de DB, la sección es la humana. |
| **Notion API** | Bloque `callout` con `icon=📋, color=default` y `rich_text` con los 5 campos | Sí (`page.properties`) | Mismo principio de duplicación que Obsidian. |
| **Notion import** | Tabla GFM 2-col (`## Cabecera` con `| Campo | Valor |`) | No (Notion importer no lee YAML como panel) | Sección visible es la única representación. |
| **AppFlowy** | Callout nativo `> [!info] **Cabecera**` con 5 bullets | Sí (Properties panel) | Mismo patrón que Obsidian. |
| **Markdown plano (GFM)** | Tabla GFM 2-col | No (literal YAML solo) | Sección visible es la única representación. |
| **HTML/PDF** | `<table class="cabecera">` con los 5 campos en `<thead>` + `<tbody>` | Sí (`## Metadata` separado, F59) | El F75 NO fusiona con `## Metadata` — son 2 bloques distintos: la cabecera es la humana; la metadata es técnica. |
| **Flashcards** | No se emite bloque visible (anverso) | No (cards no tienen propiedades) | El `summary` se usa como **hint** en el reverso de la card (debajo de la respuesta, en letra pequeña). |

**Implementación:** `scripts/render/_header.py:emit_cabecera(frontmatter, *, dest)`.
Los 7 renderers importan este helper. La duplicación entre panel y
sección visible es por diseño (decisión F75 D6); se documenta en
`references/07-visual/README.md` y en `capability-matrix.md` fila 13.

---

## §8 · Cálculo de `reading-time-minutes`

### §8.1 · Fórmula canónica

```
reading_time_minutes = ceil(palabras_cuerpo / 200)
```

con mínimo 1 minuto y redondeo al entero superior. El cuerpo excluye
frontmatter, headings vacíos, y bloques `code` (la lectura de código
es ~2x más lenta pero se documenta por separado en F76 density).

### §8.2 · Procedimiento de cierre (F75-FUERA)

`scripts/util/reading_time.py --note <path>` (a crear en F75-FUERA):

1. Lee el archivo NoteMark.
2. Cuenta palabras del cuerpo (excluyendo frontmatter, headings, code).
3. Aplica la fórmula §8.1.
4. Si el frontmatter ya tiene `reading-time-minutes`:
   - Si difiere > 50% del cálculo → **warning** (R3 del plan F75).
   - Si difiere ≤ 50% → respeta el valor manual.
5. Si no tiene → escribe el calculado.

### §8.3 · Override manual

El agente puede sobreescribir `reading-time-minutes` directamente en el
frontmatter cuando:
- La nota tiene tablas densas que el ojo lee más lento (factor 1.5x típico).
- La nota tiene diagramas Mermaid (factor 1.3x).
- La nota tiene muchos ejemplos (factor 1.2x por cada 5 ejemplos).

El validador (F75 INV-P10) acepta cualquier `int ≥ 1`; el agente tiene
autoridad sobre el cálculo automático.

---

## §9 · Wirings

- **F11** `assets/profile.template.yaml` — `visual.density` (compact|normal|spacious) por defecto `normal`; la cabecera no se ve afectada por density (siempre los 5 campos).
- **F47** `references/04-authoring/properties.md` — 2 propiedades nuevas (`summary` §5.19, `reading-time-minutes` §5.20) amplían el conjunto canónico de 18 a 20; FRONTMATTER_ORDER de `_emitter.py` reordenado; INV-P5 ahora exige 5 universales en `status: published`.
- **F51** `references/04-authoring/depth-layers.md` — el patrón de apertura fija el H2 `## TL;DR` como capa L1; el resto de capas L2/L3 siguen el patrón F51 sin cambios.
- **F53** `references/08-render/contract.md` — la cabecera es una nueva fila de capacidad transversal (afecta a las 7 destinos).
- **F66** `references/07-visual/mermaid-portable.md` §5 — los diagramas Mermaid siguen siendo `:::diagram`; su presencia afecta el factor de reading-time (1.3x) pero no cambia la cabecera.
- **F70** `scripts/render/make_figure.py` — las figuras no afectan la cabecera (se renderizan dentro del cuerpo, no en la sección `## Cabecera`).
- **F72** `references/07-visual/tokens.md` — los colores de la cabecera son los del `_neutral.*` y `semantic.info.*` (F73 mapea `> [!info]` para la cabecera).
- **F73** `references/07-visual/style-mapping.md` + `scripts/util/style_mapping.py` — el callout `> [!info]` que usa la cabecera en Obsidian/AppFlowy/HTML-PDF consume `obsidian_callout_for('info')` y `notion_callout_for('info')`.
- **F74** `assets/notemartin.css` §1 — la cabecera usa `.callout-info` con `var(--semantic-info-bg)`; en HTML/PDF usa `<table class="cabecera">` (definida en F59 `html_pdf.template.css` con estilos pre-F75; la F74 añade la clase sin hex literales).
- **F77** `evals/visual/` — verificación visual multi-destino de la cabecera en los 7 destinos (cerrado; 12 capturas reales; `## Cabecera` con 5 campos visible en los 4 destinos renderizables + checklist para 3 externos).
- **F78-F92** `references/05-note-types/*.md` — cada archivo individual instancia este patrón para su tipo; este doc define las reglas comunes.

---

**Verificación al cierre de la fase:**

- `wc -l references/07-visual/note-templates.md` ≤ 500 líneas.
- §2 con 3 subsecciones (formato, mapeo, reglas de resumen).
- §3 con la apertura común (frontmatter → `## Cabecera` → `## TL;DR`).
- §4 con el cierre común.
- §5 con 3 subsecciones (reglas generales, frecuencia, anti-patrones).
- §6 con **15 subsecciones numeradas §6.1 a §6.15**, cada una con frontmatter concreto, apertura específica, secciones obligatorias, secciones opcionales, cierre, anti-patrones.
- §7 con tabla 7 destinos.
- §8 con 3 subsecciones (fórmula, procedimiento, override).
- §9 con 11 wirings documentados.
