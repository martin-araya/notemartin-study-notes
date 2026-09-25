# NoteMark — `references/04-authoring/notemark.md`

> Documento normativo de la Fase 12 del roadmap. Define el formato intermedio que el agente escribe en L3 y que el parser (F48) traduce al Note IR (F14). Gramática formal en [`notemark.ebnf`](notemark.ebnf).
>
> Documentos complementarios: `skills/AGENT.md` §2 INV-05/INV-06 (reglas duras), §13 (forma canónica — este doc la formaliza), `references/00-pipeline/architecture.md` §3.4 (contrato L3), `references/04-authoring/README.md` (restricción INV-06). Fases hermanas: F14 IR, F45-F47 y F51 separan este contenido si crece.

## §1 · Propósito y alcance

NoteMark es el **único formato** que el agente escribe a mano en L3. Vive entre el SDM (F13) y el IR (F14): el agente redacta prosa + directivas, el parser las convierte al IR, los renderers (F54-F60) traducen el IR al dialecto de cada destino. Esto es lo que mantiene la skill como skill y no como aplicación (ver ADR-0001 y ADR-0002).

**No es:** Markdown de Obsidian, Markdown de Notion, Markdown de AppFlowy, ni ningún dialecto de plataforma. Es un superconjunto de CommonMark con directivas de bloque (`:::tipo`) y marcas inline (`{src:}`, `[[term:]]`, etc.).

## §2 · Cuándo se aplica

- Cualquier redacción de una nota nueva.
- Cualquier revisión de una nota existente.
- Cualquier regeneración desde el IR (vuelta atrás por error de render).

**No se aplica a:** validación del IR (eso es F49), render (F54-F60), publicación (F62), ni ingesta (F17-F29).

## §3 · Reglas duras (invariantes)

| ID | Invariante | Si se omite… |
|---|---|---|
| **INV-05** | El agente escribe NoteMark, nunca Markdown de destino ni JSON de IR a mano. | Los destinos no-Obsidian quedan rotos en silencio. |
| **INV-06** | NoteMark no contiene sintaxis de ninguna plataforma (callouts, toggles, wikilinks). | El parser produce nodos ambiguos y un destino se vuelve oráculo. |
| **INV-09** | Literales de la fuente (mensajes de error, defaults, sintaxis, comandos) textuales. | La nota "explica" lo que la fuente no dice. |
| **INV-10** | Enumeraciones cerradas nunca truncadas; prohibido `etc.`, `entre otros`, `los más relevantes`. | La fuente dice 7 cosas; la nota dice "varias". |
| **INV-14** | Cero colores literales. Tokens via `assets/tokens.json` (F72). | INV-14 violación; ver §10. |
| **INV-17** | Incertidumbre declarada. Versión indeterminable → `unknown`; nunca inferir. | El agente rellena huecos con conocimiento propio. |

## §4 · Gramática — visión general

Cuatro ejes:

1. **Directivas de bloque** con valla `:::tipo` (líneas que empiezan por `:::identificador` y terminan con otra línea `:::`). Ver §6.
2. **Marcas inline** dentro del texto: `{src:blk_xxxx}`, `[[term:nombre]]`, `[[note:id]]`, `{{placeholder}}`, `{derived}`, `{external}`, `{layer:l1|l2|l3}`. Ver §7.
3. **Frontmatter YAML canónico** al inicio del archivo entre `---` y `---`. Ver §8.
4. **Marcadores de capa** a nivel de bloque (`{layer:l1}`, `{layer:l2}`, `{layer:l3}`). Ver §9.

Sintaxis base: Markdown estándar de CommonMark (paragraph, heading, list, table, fenced code, image, link, math-inline `$...$`). La gramática formal completa está en `notemark.ebnf` (47 reglas, 75 líneas).

## §5 · Cobertura IR ↔ NoteMark

Cada nodo del Note IR (Fase 14) tiene exactamente una sintaxis NoteMark. 20 nodos de bloque + 13 inline = 33 filas.

### 5.1 Bloques (20)

| Nodo IR | Sintaxis NoteMark |
|---|---|
| `section`, `paragraph`, `list`, `checklist`, `table`, `code`, `quote`, `divider` | CommonMark / GFM. |
| `definition-list`, `property-block` | `:::property` con YAML interno. |
| `console` | `:::console` … `:::console`. |
| `equation` | `:::equation` … `:::equation` (con `$$…$$`). |
| `figure` | `:::figure` … `:::figure` (con `![alt](src)`). |
| `diagram` | `:::diagram` … `:::diagram` (con ` ```mermaid `). |
| `admonition` (10 tipos) | `:::warning` / `note` / `tip` / `example` / `danger` / `security` / `performance` / `version` / `deprecated` / `conflict` / `external` … `:::`. |
| `collapsible` | `:::collapsible` … `:::collapsible`. |
| `columns` | `:::columns` con dos columnas separadas por línea en blanco. |
| `question` | `:::question` … `:::question`. |
| `step` | `:::step` … `:::step`. |
| `parameter-table` | `:::param-table` con tabla GFM dentro. |
| `contradiction` | `:::contradiction id="c_001"` (apunta al registry `knowledge/conflicts.json`; Fase 41). |
| `discrepancy` | `:::discrepancy source-says="X" model-says="Y"` (inline diff fuente vs modelo; Fase 41). |
| `derived` | `:::derived` … `:::derived` (síntesis, analogías o diagramas propios del agente basados en la fuente; Fase 42). |

### 5.2 Inline (13)

| Nodo IR | Sintaxis NoteMark |
|---|---|
| `text`, `strong`, `em`, `code`, `link-external` | CommonMark (`**x**`, `*x*`, `` `x` ``, `[t](u)`). |
| `link-note` | `[[note:id]]`. |
| `term-ref` | `[[term:nombre]]`. |
| `source-ref` | `{src:blk_xxxxxxxxxxxx}` (12 hex). |
| `math-inline` | `$E=mc^2$`. |
| `footnote-ref`, `keyboard`, `placeholder`, `deleted`, `derived`, `external` | `[[fn:id]]`, `[[kbd:Ctrl+S]]`, `{{nombre}}`, `~~x~~`, `{derived}`, `{external}`. |

## §6 · Directivas de bloque

Las 22 directivas (`warning`, `note`, `tip`, `example`, `danger`, `security`,
`performance`, `version`, `deprecated`, `conflict`, `external`, `derived`,
`collapsible`, `columns`, `param-table`, `step`, `question`, `diagram`,
`figure`, `equation`, `console`, `property`) se documentan en detalle en
[`block-directives.md`](block-directives.md). Este documento mantiene la
**gramática formal** ([`notemark.ebnf`](notemark.ebnf)), la **cobertura IR ↔
NoteMark** (§5 de este doc) y las **marcas inline** (§7 de este doc).

Para elegir qué directiva usar ante un hecho del SDM, consultar la tabla de
decisión rápida en `block-directives.md` §6. Para resolver confusiones entre
directivas vecinas, §7 (fronteras). Para reglas de anidamiento y longitud,
§8 y §9. El catálogo completo está en §10.

> **Directivas que aún no tienen ficha en §10** (reservadas para F41):
> `:::contradiction` y `:::discrepancy`. Se añadirán a `block-directives.md`
> sin reabrir F45 cuando F41 cierre.

## §7 · Marcas inline

Las 6 marcas obligatorias (`{src:blk_xxxx}`, `[[term:nombre]]`, `[[note:id]]`,
`{{nombre}}`, `{derived}`, `{external}`) y las 3 de apoyo (`[[fn:id]]`,
`[[kbd:]]`, `~~x~~`) se documentan en detalle en
[`inline-marks.md`](inline-marks.md). Este documento mantiene la
**gramática formal** ([`notemark.ebnf`](notemark.ebnf)) y el **mapeo IR**
([`ir-spec.md`](ir-spec.md)).

Para decidir cuántas `{src:}` lleva cada bloque, ver `inline-marks.md` §4
(densidad de citación). Para la regla de primera aparición de términos, §5.
Para la tabla de comportamiento por destino (7 destinos), §7. Para las reglas
de legibilidad y la regla "no más de una vez por bloque", §8 y §9.

## §8 · Frontmatter

Forma: `---` al inicio, propiedades YAML canónicas, `---` de cierre.

El frontmatter canónico (18 propiedades cerradas, 3 obligatorias universales)
se documenta en [`properties.md`](properties.md). Este documento mantiene la
**gramática formal** ([`notemark.ebnf`](notemark.ebnf), reglas `frontmatter` /
`yaml-body` / `yaml-line` / `key`) y la regla de orden (frontmatter al inicio
del archivo, ningún bloque antes).

Para declarar propiedades personalizadas (`x-*` o `user-*`), ver
`properties.md` §8. Para la obligatoriedad por tipo de nota, §6. Para el
render legible en destinos sin soporte de properties, §7.

## §9 · Marcadores de capa

La marca `{layer:l1|l2|l3}` se documenta en
[`depth-layers.md`](depth-layers.md) (F51). Resumen:

- `{layer:l1}` = TL;DR autónomo (≤ 8 líneas / ≤ 60 palabras).
- `{layer:l2}` = operativo (30-70% del cuerpo).
- `{layer:l3}` = referencia exhaustiva (30-70% del cuerpo; en `:::collapsible` con `default_open: false`).

Regla dura (INV-08): **l3 nunca se omite** (puerta de fidelidad, F42). Si el
agente decide no redactar l2, sigue redactando l3.

Aplicación: la marca va inmediatamente después de un heading `##` o `###`,
antes del contenido de esa sección. Herencia: si se omite, el layer se hereda
del anterior o del top-level `layer:` del frontmatter.

Para umbrales de "nota extensa", override por tipo (F78-F92), extracción a
nota hermana cuando L3 desborda, e integración con el ledger, ver
`depth-layers.md` §2, §5 y §6.

## §10 · Anti-patrones generales

- ~~`> [!warning]` (Obsidian callout)~~ → usar `:::warning`.
- ~~`> [!note]`, `> [!tip]`, `> [!example]`, `> [!danger]`~~ → directivas equivalentes.
- ~~Toggles de Notion (`<details>` con markdown propio)~~ → `:::collapsible`.
- ~~Wikilinks Obsidian `[[doble]]` sin prefijo `note:`/`term:`~~ → `[[note:id]]` o `[[term:nombre]]`.
- ~~Bloques JSON de IR embebidos~~ → no; el parser (F48) los genera.
- ~~Colores hex `#abc123` o `rgb(...)` literales~~ → tokens via `assets/tokens.json`.
- ~~`etc.`, `entre otros`, `los más relevantes` en enumeraciones cerradas~~ → listar todas (INV-10).

## §11 · Cómo verificar

1. `wc -l notemark.md` ≤ 300; `wc -l notemark.ebnf` ≤ 80.
2. Verificaciones de directivas redirigidas a `block-directives.md` §13.
3. `rg -c '\[\!warning\]|\[\!note\]' notemark.md evals/notemark-sample/full-note.nm` → 0.
4. `wc -l evals/notemark-sample/full-note.nm` entre 380 y 420; contiene las 20 directivas, las 6 marcas inline y los 3 layer markers.

## §12 · Cambios permitidos sin reabrir F12

Refinar §5 (cobertura IR ↔ NoteMark) cuando F14 extienda el IR; ajustar §10 (anti-patrones generales) sin tocar §6 (que es puntero a `block-directives.md` F45) ni §7 (que es puntero a `inline-marks.md` F46). **Reabren F12:** cambiar INV-05/06/09, redefinir sintaxis de `:::directiva` o de marca inline, introducir inline/bloque que rompa compat con notas existentes, eliminar la prohibición de platform-specific, mover contenido de F45/F46 de vuelta a este documento.
