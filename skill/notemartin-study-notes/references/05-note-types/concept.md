# `concept` — `references/05-note-types/concept.md`

> Documento normativo de la **Fase 78** del roadmap. Define el patrón de la nota
> de tipo `concept`: 13 secciones (10 obligatorias + 3 de cierre heredado),
> componentes mínimos, reglas de contenido, checklist propio, nota mínima viable
> y contrato de activación por perfil (sección `## Práctica` opcional).
>
> **Cuándo cargar:** tras decidir el tipo de nota (selector F93) cuando el
> `note-type` resuelto es `concept`; antes de redactar la primera sección
> específica del tipo. Este archivo instancia el patrón común de
> `references/07-visual/note-templates.md` (F75) y delega las reglas comunes
> (cabecera, apertura, cierre, jerarquía visual) allí.
>
> **Wirings:**
> - `references/07-visual/note-templates.md` (F75) — cabecera canónica, apertura/cierre común.
> - `references/07-visual/density.md` (F76) — reglas R1-R8 ejecutables por `scripts/validate/density_check.py`.
> - `references/04-authoring/properties.md` (F47) — frontmatter canónico de 20 propiedades.
> - `references/04-authoring/inline-marks.md` (F46) — marcas `{src:blk_xxxx}`, `[[term:nombre]]`, `[[note:id]]`.
> - `references/04-authoring/block-directives.md` (F45) — directivas `:::warning`, `:::example`, `:::collapsible`, etc.
> - `references/04-authoring/depth-layers.md` (F51) — capas L1/L2/L3 y layer markers `{layer:l1|l2|l3}`.
> - `references/05-note-types/README.md` — los 15 tipos cerrados (F78-F92). `concept` ocupa el lugar §6.1 en el patrón resumido.

---

## §1 · Propósito y alcance

Una nota `concept` captura **un concepto** —una idea con nombre, definición y
mecanismo— y lo vuelve consultable, comparables y enlazable desde otras notas.
No es un tutorial, no es un procedimiento, no es un glosario: el `concept`
responde "¿qué es X, cómo funciona, en qué se diferencia de Y, cuándo NO
usarlo y qué conceptos vecinos lo complementan?".

El tipo `concept` es **el más versátil** del catálogo: cubre la mayor parte de
los conceptos extraídos en L2 (`{layer:l2}`) y sirve de pivote para el grafo
de prerrequisitos (`knowledge/concept-graph.json`, F39). Por eso su patrón es
el más exigente en reglas (las 8 reglas R1-R8 aplican, sin exención).

**Fuera de alcance:**

- Notas que solo definen un término corto sin mecanismo → `glossary-term` (F89).
- Comparaciones entre 3+ conceptos sin profundizar en uno → `comparison` (F87).
- Resumen de un capítulo entero → `chapter-digest` (F86).
- Componente de un sistema → `architecture` (F83).
- Referencia a una API o función → `api-reference` (F79).

El tipo `concept` es **el más versátil** del catálogo.

---

## §2 · Estructura de la nota

### §2.1 · Frontmatter (orden canónico)

```yaml
---
title: "<sustantivo canónico, sin artículo inicial salvo nombres propios>"
note-type: concept
status: draft | published
summary: "<≤ 200 chars, 1 línea, sin control chars>"
reading-time-minutes: <int ≥ 1>
tags: [type/concept, domain/<uno o más>, f<NN>/<sub>]
source: "<ruta al SDM original o vacío si nota auto-definida>"
source-type: book | docs | api | rfc | transcription | article | other
source-anchor: "<page|section_path>"
source-url: "<opcional>"
retrieved: <YYYY-MM-DD>
product: "<si aplica>"
product-version: "<si aplica>"
related: "[[note:...]], [[note:...]]"
---
```

Las 5 universales (`title`, `note-type`, `status`, `summary`, `reading-time-minutes`) son
obligatorias en `status: published` (INV-P5, F47 §5 + F75 §5.19-§5.20). En `status: draft`,
solo `title`, `note-type` y `status` son obligatorias; `summary` y `reading-time-minutes`
se difieren al cierre.

### §2.2 · Apertura común (heredada de F75 §3)

```markdown
# {title}

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | ... |
| **Procedencia** | source (source-type) §source-anchor · recuperado YYYY-MM-DD |
| **Versión** | product product-version |
| **Estado** | Publicado (published) / Borrador (draft) |
| **Tiempo de lectura** | N min |

## TL;DR
{primer párrafo del L1 — ≤ 8 líneas / ≤ 60 palabras, sin {src:}}

{layer:l2}

## Problema
```

### §2.3 · Las 10 secciones específicas + 3 de cierre

Orden obligatorio; cada sección es H2 salvo indicación.

| # | Sección | Estado | Capa | Notas |
|---|---|---|---|---|
| 1 | `## TL;DR` | obligatoria | L1 | Heredada de F75. ≤ 60 palabras / 8 líneas (R1, F76). |
| 2 | `## Problema` | obligatoria | L2 | Qué pregunta responde el concepto; por qué existe. |
| 3 | `## Intuición` | obligatoria | L2 | Imagen mental que lo vuelve obvio. Prosa pura, ≤ 200 palabras (R2). |
| 4 | `## Analogía` | obligatoria | L2 | Puente a un dominio conocido del lector; admite `:::example`. |
| 5 | `## Definición formal` | obligatoria | L2 | Versión precisa; admite ecuación, tabla de variables, fórmula. |
| 6 | `## Mecanismo` | obligatoria | L2 | Cómo opera paso a paso o qué estructuras internas lo componen. |
| 7 | `## Comparaciones` | obligatoria | L2 | Tabla o lista contra 2-4 conceptos vecinos. |
| 8 | `## Resumen` | obligatoria | L2 | 3-5 viñetas densas con anclas `{src:}`. |
| 9 | `## Trampas` | obligatoria | L2 | `:::warning` por trampa (causa + manifestación + evitación). |
| 10 | `## Cuándo NO usarlo` | obligatoria | L2 | Cada bullet nombra el caso + motivo + enlace `[[note:id]]`. |
| 11 | `## Límites y alternativas` | **obligatoria** | L2 | Qué cubre y qué queda fuera; ≥ 1 fila con `[[note:id]]` o `[[term:]]`. |
| 12 | `## Relacionados` | obligatoria | L2 | `[[note:id]]` a prerrequisitos (`requires:`) y derivados (`enables:`). |
| 13a | `## Backlinks` | obligatoria si hay aristas | cierre | Lista de notas que apuntan a esta. |
| 13b | `## Queries` | obligatoria si hay queries activas | cierre | Dataview / vistas Notion / etc. |
| 13c | `## Ver también` | opcional si `related:` presente | cierre | Repite los enlaces de `## Relacionados` en formato legible. |
| 14 | `## Práctica` | **opcional-condicional** (perfil) | L3 | Solo si `profile.notes.types.concept.include_practice: true`. Ver §5. |

Las secciones 13a-13c son el cierre común de F75 §4. La sección 14
(`## Práctica`) está documentada en §5.

### §2.4 · Capas (heredado de F51)

| Capa | Marcador | Contenido |
|---|---|---|
| L1 | `{layer:l1}` | Solo `## TL;DR`. ≤ 60 palabras / 8 líneas. |
| L2 | `{layer:l2}` | Secciones 2-12 (problema → relacionados). 30-70% del total. |
| L3 | `{layer:l3}` | `## Práctica` cuando esté activada. Si > 100 líneas, envolver en `:::collapsible` con `default_open: false` (R7). |

Si la nota tiene < 50 líneas de cuerpo, las 3 capas son **optativas** y basta L2.

### §2.5 · Autoevaluación (F102)

Tipos de pregunta asignados a `concept` (ver
`references/09-study/self-evaluation.md` §3):

| Tipo de pregunta | Asignado |
|---|---|
| Recuerdo | ✅ |
| Aplicación | ✅ |
| Diagnóstico | — |
| Decisión | ✅ |
| Predicción | — |

Notas: la nota puede declarar `self-evaluation-types` como superset del
default (nunca subset) — ver V2 en `self-evaluation.md` §6. La H3
`### Predicción` solo se incluye si la nota documenta comportamiento
dinámico explícito (no se añade por defecto).

---

## §3 · Componentes mínimos

Cada componente es **obligatorio** salvo indicación. Las reglas R1-R8 de F76
se aplican sin exención (concept no está en la lista de tipos exentos).

| Componente | Mínimo | Fuente |
|---|---|---|
| Cabecera (F75 §2) | 5 campos en este orden: Resumen, Procedencia, Versión, Estado, Tiempo de lectura | F75 §2.1 |
| `## TL;DR` | ≤ 60 palabras / 8 líneas (R1) | F76 §2 R1 |
| `## Problema` | 1-2 párrafos (≤ 200 palabras cada uno) | F94 §2/§5.1 |
| `## Intuición` | 1 párrafo, ≤ 200 palabras, con `[[term:nombre]]` | F94 §2/§5.2 |
| `## Analogía` | 1 analogía (dominio conocido distinto al del concepto) + declaración explícita de rotura | F94 §2/§5.3 |
| `## Definición formal` | 1 versión precisa (prosa, tabla o fórmula) | F94 §2/§5.4 |
| `## Mecanismo` | ≥ 3 frases o 1 diagrama con explicación | esta fase |
| `## Comparaciones` | ≥ 2 conceptos comparados (filas o columnas) | esta fase |
| `## Resumen` | 3-5 viñetas, ≥ 0.80 densidad `{src:}` (R8) | F46 §4 + F76 R8 |
| `## Trampas` | ≥ 1 `:::warning` con causa + manifestación + evitación | esta fase |
| `## Cuándo NO usarlo` | ≥ 1 bullet con motivo + enlace `[[note:id]]` | esta fase |
| `## Límites y alternativas` | ≥ 1 fila (tabla) o bullet con `[[note:id]]` o `[[term:]]` | **criterio ROADMAP F78** |
| `## Relacionados` | ≥ 2 enlaces `[[note:id]]` (1+ prerrequisito, 1+ derivado) | F39 |
| Marcas `{src:blk_xxxx}` | ≥ 1 cada 200 palabras de prosa continua (R3) | F46 §4 + F76 R3 |
| Anclaje visual | ≥ 1 callout/tabla/figura/diagrama por cada 200 palabras (R3) | F75 §5.2 + F76 R3 |
| Cierre | `## Backlinks` si hay aristas; `## Queries` si queries activas | F75 §4 |
| Activación por perfil | sección `### Activación por perfil` que documenta la lectura de `profile.notes.types.concept` | esta fase |

---

## §4 · Reglas de contenido

### §4.1 · Densidad y estructura (R1-R8 de F76)

- **R1** `## TL;DR` ≤ 60 palabras / 8 líneas. Si excede, partir en dos párrafos o mover prosa a `## Problema`.
- **R2** Cada párrafo del L2 ≤ 200 palabras. Excepción documentada: `## Mecanismo` y `## Definición formal` admiten bloques técnicos largos siempre que estén marcados con `{layer:l2}` o `{layer:l3}` y tengan un anclaje visual cada 200 palabras (R3).
- **R3** ≥ 1 anclaje visual (callout/tabla/figura/diagrama/código con caption/ecuación) cada 200 palabras de prosa continua. Reset al encontrar el siguiente anclaje.
- **R4** ≤ 3 callouts consecutivos sin prosa intermedia (un bloque `code` cuenta como prosa intermedia).
- **R5** ≤ 5 viñetas consecutivas sin prosa/estructura intermedia (checklists con `[ ]` cuentan como estructura si ≥ 3 items).
- **R6** Cada H2/H3 debe tener ≥ 1 párrafo, tabla, callout, figura, diagrama, ecuación o código. Si la sección es solo viñetas, se marca como error.
- **R7** Cualquier sección > 100 líneas debe envolverse en `:::collapsible` con `default_open: false`.
- **R8** Densidad de marcas `{src:}` ≥ 0.80 sobre bloques fácticos (de cada 5 bloques fácticos, ≥ 4 llevan al menos un ancla).

### §4.2 · Marcas inline (F46)

- **`{src:blk_xxxx}`** — exactamente 12 caracteres hexadecimales en minúsculas (INV-I5). Una instancia específica por bloque (INV-I1). Si la nota no tiene SDM detrás (caso auto-definido), se omite la marca o se sustituye por `:::external` o `:::derived` (F45 §10.11-§10.12).
- **`[[term:nombre]]`** — primera aparición del término en la nota (INV-I2). No repetir en cada mención.
- **`[[note:id]]`** — enlace a otra nota del catálogo. En `## Comparaciones`, `## Cuándo NO usarlo`, `## Límites y alternativas` y `## Relacionados`, **cada** mención de un concepto que tenga nota propia lleva esta marca.
- **`{derived}` / `{external}`** — excluyentes con `{src:}` simple (INV-I6). Se usan a nivel inline o como envoltorio de bloque (`:::derived`, `:::external`).

### §4.3 · Directivas de bloque (F45)

| Sección | Directiva preferida | Justificación |
|---|---|---|
| `## Trampas` | `:::warning` por trampa (causa + manifestación + evitación) | F45 §6 fila 1. |
| `## Analogía` | `:::example` si la analogía requiere visualización | F45 §6 fila 10. |
| `## Mecanismo` | `:::diagram` (Mermaid) si hay flujo o componentes | F45 §10.18 + F66 portabilidad. |
| `## Definición formal` | `:::equation` si hay fórmula; tabla si hay variables | F45 §10.20 / §10.13. |
| `## Comparaciones` | Tabla GFM (forma preferida por F75 §5.1) | F75 §5.1. |
| `## Práctica` | `:::question` por pregunta (F92 patrón) | F45 §6 fila 15. |
| `## Resumen` | Lista con viñetas + anclas `{src:}` | F75 §5.1 ("listas" → forma aceptable). |

Ninguna directiva lleva color literal (INV-14). Los tokens via
`assets/tokens.json` (F72) los decide el renderer.

### §4.4 · Anti-patrones

1. **"Definición formal con símbolos cuando la audiencia es operativa"** — nota heredada de `note-templates.md` §6.1. Si la nota va a un perfil `study` operativo, mover la matemática a `:::collapsible` con `default_open: false`.
2. **"Lista infinita de trampas"** — 8+ trampas consecutivas sin agrupar. Solución: agrupar por categoría con `### Categoría: <X>` y párrafo introductorio.
3. **"Comparación de uno"** — solo 1 fila en `## Comparaciones` (compara el concepto consigo mismo disfrazado). Solución: añadir ≥ 2 conceptos vecinos; si no los hay, el tipo de nota es `glossary-term`, no `concept`.
4. **"Cuándo NO usarlo ausente"** — sección vacía u omitida. Solución: si el concepto es universalmente aplicable (no se me ocurre un caso en contra), reconsiderar: probablemente la nota debería ser `glossary-term`, no `concept`.
5. **"Límites y alternativas fusionado con Cuándo NO usarlo"** — son secciones distintas. `## Cuándo NO usarlo` es por situación de uso; `## Límites y alternativas` es por cobertura del concepto mismo.
6. **"Práctica siempre presente"** — la sección `## Práctica` debe activarse por perfil, no incluirse por defecto en notas de referencia pura (perfil `reference`).
7. **"Muro de prosa en Definición formal"** — 200+ palabras sin anclaje. Solución: añadir tabla de variables o diagrama Mermaid.
8. **"Falta capa L3 cuando Práctica existe"** — `## Práctica` siempre va con `{layer:l3}` y, si > 100 líneas, `:::collapsible` (R7).
9. **"Nota sin `## Relacionados`"** — si la nota tiene dependencias en `concept-graph.json`, la sección es obligatoria.

---

## §5 · Activación por perfil

La sección `## Práctica` (L3) está **desactivada por default**. Se activa cuando
el perfil del usuario (`assets/profile.template.yaml`, F11) incluye:

```yaml
notes:
  types:
    concept:
      include_practice: true
      include_limits_alternatives: true   # default: true
      include_comparisons: true           # default: true
      min_comparisons: 2                  # default: 2; mínimo duro
      min_traps: 1                        # default: 1; mínimo duro
```

| Campo | Default | Significado |
|---|---|---|
| `include_practice` | `false` | Si `true`, la nota incluye `## Práctica` con preguntas derivadas del concepto. |
| `include_limits_alternatives` | `true` | La sección `## Límites y alternativas` es obligatoria por criterio ROADMAP F78; el default es `true`. |
| `include_comparisons` | `true` | La sección `## Comparaciones` es obligatoria (mínimo 2 conceptos). |
| `min_comparisons` | `2` | Mínimo de conceptos comparados (criterio F78). Por debajo, `density_check.py --strict` exit 1. |
| `min_traps` | `1` | Mínimo de trampas en `## Trampas` (defensa contra el anti-patrón "sección vacía"). |

Si el campo `profile.notes.types.concept` no existe, se aplican los defaults
de la tabla anterior. La precedencia es la del F11 §7.4: **prompt > perfil >
defaults**.

Las preguntas de `## Práctica` se redactan siguiendo el patrón de
`references/05-note-types/practice.md` (F92) pero **no** se enumeran como
preguntas completas en `concept.md`: se enlaza al usuario a la nota de práctica
correspondiente (referencia `[[practice:<concepto>]]` cuando exista, o la nota
`practice` por defecto si el corpus no la tiene).

---

## §6 · Checklist de cierre

Esta sección resume el bloque del tipo. La fuente normativa es
`references/10-quality/checklists-by-type.md` §4.1. Esta copia se conserva
para que el agente que carga solo este archivo tenga la lista delante;
cualquier cambio debe aplicarse primero allí y después sincronizarse aquí.

### §6.1 · Bloqueantes [B]

- [ ] [B] Cabecera con los 5 campos en el orden correcto (F75 §2.1).
- [ ] [B] `## TL;DR` ≤ 60 palabras / 8 líneas (R1).
- [ ] [B] Las 10 secciones obligatorias (Problema → Relacionados) están presentes y en el orden correcto.
- [ ] [B] `## Límites y alternativas` presente con ≥ 1 fila (criterio ROADMAP F78).
- [ ] [B] `## Trampas` con ≥ `min_traps` (default 1) bloque `:::warning`.
- [ ] [B] `## Cuándo NO usarlo` con ≥ 1 bullet + enlace `[[note:id]]`.
- [ ] [B] `## Resumen` con 3-5 viñetas, densidad `{src:}` ≥ 0.80 (R8).
- [ ] [B] `## Práctica` presente solo si `profile.notes.types.concept.include_practice: true`.
- [ ] [B] `density_check.py --note <path>` exit 0 (sin violaciones).
- [ ] [B] `validate_ir.py --ir <path>` exit 0 (parser acepta la nota).
- [ ] [B] `scripts/validate/mermaid.py --fail-on error` retorna exit 0 (F100 §3 S9).

### §6.2 · Recomendados [R]

- [ ] [R] `## Comparaciones` con ≥ `min_comparisons` conceptos comparados (default 2). **OMIT en `reference`** (F112 §5.1).
- [ ] [R] Si `## Práctica` está presente, lleva `{layer:l3}` y `:::collapsible` si > 100 líneas (R7).
- [ ] [R] Cierre: `## Backlinks` (si hay aristas) + `## Queries` (si hay queries).
- [ ] [R] Todas las menciones a términos canónicos en `[[term:nombre]]` en su primera aparición (INV-I2).
- [ ] [R] Ningún color literal; tokens via `assets/tokens.json` (INV-14).
- [ ] [R] **AP1** No hay transcripción disfrazada: el `## Resumen` no copia ≥ 50% de un párrafo del SDM verbatim sin reescritura (F100 §3 S5).
- [ ] [R] **AP2** No hay definiciones circulares: las definiciones no usan el término definido ("X es un X que…") (F100 §3 S1).
- [ ] [R] **AP3** No hay callouts decorativos: cada `:::note` / `:::tip` / `:::warning` informa, advierte o guía con ≥ 30 caracteres de cuerpo y un verbo de acción (F100 §3 S6).
- [ ] [R] **AP4** No hay tabla de una fila útil: las tablas tienen ≥ 2 filas de datos (F100 §3 S7).
- [ ] [R] **AP5** Las analogías tienen rotura explícita: cada analogía incluye una frase que matchea D5 (F95 §4 / F100 §3 S5).
- [ ] [R] **AP6** Los diagramas Mermaid añaden información no presente en el párrafo adyacente (F100 §3 inspección visual).
- [ ] [R] **AP7** Los enlaces entre notas llevan frase introductoria de ≥ 5 palabras antes del `[[note:id]]` (F100 §3 S4).
- [ ] [R] **AP8** No hay volcado de viñetas: las secciones con ≥ 5 viñetas consecutivas tienen prosa intermedia (F100 §3 S3 / F76 R5).
- [ ] [R] **AP9** No hay marketing copiado: ausencia de "solución innovadora", "transforma su negocio", "cambia las reglas", etc. (F100 §3 S2).
- [ ] [R] **AP10** Los bloques `:::example` tienen caption o salida esperada (F100 §3 S10).
- [ ] [R] **AP12** No hay secciones vacías: cada `##` tiene ≥ 1 párrafo sustantivo de ≥ 30 caracteres (F100 §3 S8).
- [ ] [R] **F101-AP1** Ningún nombre técnico aparece traducido: identificadores, parámetros, errores, comandos y código verbatim contra la lista cerrada de 45 no-traducibles de F101 §3.
- [ ] [R] **F101-AP2** Los términos se introducen bilingües en primera aparición: notas con `language == es-en` o `en-es` tienen ≥ 1 marca `[[en:term]]` o `[[es:term]]` en la primera mención y un bloque `## Glosario` al pie (F101 §4).
- [ ] [R] **F101-AP4** Bloque de procedencia al pie: la nota tiene `## Procedencia` con 4 campos cerrados (Fuente / Versión / Fecha de recuperación ISO YYYY-MM-DD / URL/anchor).
- [ ] [R] **F102-1** Sección `## Autoevaluación` presente con las H3 `### Recuerdo`, `### Aplicación` y `### Decisión` (F102 §3), cada una con 3-7 bloques `:::collapsible{default_open=false}` (V5). **OMIT en `reference`**.
- [ ] [R] **F102-2** Cada bloque plegable de `## Autoevaluación` cierra con la línea `> Fundamento: {src:blk_xxxx}` o `> Fundamento: [[note:id#§N]]` (V3), y la respuesta no es copia literal del bloque referenciado — Jaccard ≤ 0.8 sobre palabras no técnicas (V4).
- [ ] [R] **F105-1** Si `goal_profile == interview`: la nota incluye `## Decisiones de diseño` + `## Explicación oral` (F105 R-G4). **OMIT en `reference`**.
- [ ] [R] **F105-2** Si `goal_profile == certification`: la nota incluye `## Objetivos oficiales` + declara `certification-objective` en el frontmatter (F105 R-G5). **OMIT en `reference`**.

---

## §7 · Nota mínima viable

Ejemplo canónico de 25-30 líneas para un concepto sin SDM detrás (caso "nota
auto-definida"). El validador `density_check.py --strict` debe pasar con exit 0.

```markdown
---
title: "Pipeline L0–L4"
note-type: concept
status: draft
tags: [type/concept, domain/pipeline]
---

# Pipeline L0–L4

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Pipeline de 5 capas (L0 ingesta → L4 render) que transforma una fuente en notas publicadas. |
| **Estado** | Borrador (draft) |

## TL;DR
Pipeline L0–L4 es la cadena de 5 capas que transforma una fuente (PDF, libro, transcripción) en notas publicadas en los 7 destinos, con puertas de fidelidad, calidad y render.

{layer:l2}

## Problema
Producir notas consistentes a partir de fuentes heterogéneas sin reinventar el flujo por documento.

## Intuición
Una tubería con paradas explícitas: cada capa entrega un artefacto validable, y la siguiente solo lee lo que la anterior firmó.

## Analogía
Como una línea de ensamblaje automotriz: cada estación añade valor y firma su trabajo; el coche no avanza sin esa firma.

## Definición formal
| Capa | Entrada | Salida |
|---|---|---|
| L0 Ingesta | PDF, EPUB, DOCX | `ingest/` |
| L1 SDM | `ingest/` | `sdm.json` |
| L2 Conocimiento | `sdm.json` | `knowledge/` |
| L3 Autoría | `knowledge/` | `notemark/`, `ir/` |
| L4 Render | `ir/` | `render/` |

## Mecanismo
Cada capa lee solo su artefacto de entrada y el perfil. 3 puertas: fidelidad (100 % `must-keep`), calidad (IR válido + `{src:}` ≥ 0.80), render (sin degradación a plano).

## Comparaciones
| Aspecto | L0–L4 | ETL clásico |
|---|---|---|
| Granularidad | bloque SDM | tabla |
| Validación | 3 puertas | por fase |

## Resumen
- 5 capas con artefactos persistidos por capa.
- 3 puertas: fidelidad, calidad, render — ninguna se salta.
- Una capa lee solo su entrada y el perfil.

## Trampas
:::warning
**Salto de capa.** Procesar texto de L0 directamente en L3 sin pasar por L1/L2 rompe la trazabilidad: las anclas `{src:blk_xxxx}` no resuelven.
:::

## Cuándo NO usarlo
- Resúmenes de un solo párrafo → `glossary-term` (F89).
- Comparaciones exhaustivas ≥ 3 conceptos → `comparison` (F87).

## Límites y alternativas
| Alternativa | Cubre | Trade-off |
|---|---|---|
| ETL clásico | ingestas tabulares | sin puerta de fidelidad al SDM |
| Pipeline CI/CD | entrega continua | no modela conocimiento semántico |

## Relacionados
- `[[note:concept-graph]]` — grafo de prerrequisitos construido en L2.
- `[[note:coverage-ledger]]` — la puerta de fidelidad lo consulta.

## Backlinks
- [[note:arquitectura-de-capas]]
```

Esta nota mínima (~30 líneas de cuerpo) cumple R1-R8 de F76. Sirve de
referencia de **forma**; el contenido se sustituye por el del SDM en producción.

---

## §8 · Wirings y referencias cruzadas

- **F11** `assets/profile.template.yaml` — defaults de §5 (include_practice, min_comparisons, etc.).
- **F39** `references/03-knowledge/concept-graph.md` — `## Relacionados` se construye desde `related_concepts`.
- **F45** `references/04-authoring/block-directives.md` — directivas `:::warning`, `:::example`, `:::diagram`, `:::equation`, `:::question`, `:::collapsible`, `:::external`, `:::derived`.
- **F46** `references/04-authoring/inline-marks.md` — marcas `{src:blk_xxxx}`, `[[term:nombre]]`, `[[note:id]]`; regla de primera aparición (INV-I2).
- **F47** `references/04-authoring/properties.md` — frontmatter de 20 propiedades; `note-type: concept` (enum cerrado).
- **F51** `references/04-authoring/depth-layers.md` — capas L1/L2/L3; L1 ≤ 60 palabras; extracción a nota hermana si L3 desborda.
- **F66** `references/07-visual/mermaid-portable.md` — portabilidad de los Mermaid en `## Mecanismo`.
- **F72** `references/07-visual/tokens.md` — colores semánticos de las directivas.
- **F75** `references/07-visual/note-templates.md` — cabecera canónica, apertura/cierre común, jerarquía visual (§5.1 tabla para `## Comparaciones`).
- **F76** `references/07-visual/density.md` — tabla cerrada R1-R8 ejecutable por `scripts/validate/density_check.py`.
- **F77** `evals/visual/` — verificación visual multi-destino de una nota `concept` (visual_inspect.py exit 0).
- **F86** `references/05-note-types/chapter-digest.md` — `concept` extraído de un capítulo enlaza al `chapter-digest` padre.
- **F89** `references/05-note-types/glossary-term.md` — límite inferior: sin mecanismo ni comparaciones, es glosario.
- **F92** `references/05-note-types/practice.md` — patrón de la sección `## Práctica` cuando se activa.

---

## §9 · Verificación al cierre de la fase

- `wc -l references/05-note-types/concept.md` ≤ 400 líneas.
- §2 con 4 subsecciones (frontmatter, apertura, secciones, capas).
- §3 tabla de componentes mínimos con al menos 13 filas.
- §4 con 4 subsecciones (densidad, marcas, directivas, anti-patrones).
- §5 con la tabla de campos del perfil y sus defaults.
- §6 con el checklist de cierre de ≥ 13 items.
- §7 con la nota mínima viable (≥ 25 líneas, ≤ 40 líneas, pasa `density_check.py`).
- §8 con al menos 13 wirings documentados.
- §9 lista de verificación explícita.

**Criterios de aceptación del ROADMAP F78:**

1. _Funciona sin cambios para un concepto de base de datos y uno de redes._ → `evals/concept-sample/notes/db-*.md` y `net-*.md` pasan `density_check.py --strict` y la batería de 5 sub-criterios de `run_eval.py` (C1).
2. _Incluye sección de límites y alternativas._ → sección §2.3 fila 11 obligatoria; verificada por `run_eval.py` C2.
3. _Las preguntas de práctica son opcionales según perfil._ → sección §5 + dos fixtures de perfil + verificación por `run_eval.py` C3.
