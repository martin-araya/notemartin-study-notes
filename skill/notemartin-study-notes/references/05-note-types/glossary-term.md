# `glossary-term` — `references/05-note-types/glossary-term.md`

> Documento normativo de la **Fase 89** del roadmap. Define el patrón de la
> nota de tipo `glossary-term`: definición de 1 frase, formas en inglés y
> español, aliases/siglas, confundibles con enlaces bidireccionales, y notas
> donde aparece. **Anti-patrón duro (F75 §6.12): la nota no debe exceder 30 líneas.**
>
> **Cuándo cargar:** tras decidir el tipo de nota (selector F93) cuando el
> `note-type` resuelto es `glossary-term`; antes de redactar la primera
> sección. Instancia el patrón común de `references/07-visual/note-templates.md`
> (F75) §6.12.
>
> **Wirings:**
> - `references/07-visual/note-templates.md` (F75) §6.12 — patrón resumido + anti-patrón.
> - `references/07-visual/density.md` (F76) — reglas R1-R8.
> - `references/04-authoring/properties.md` (F47) — frontmatter sin `source-bearing` obligatorio.
> - `references/04-authoring/inline-marks.md` (F46) — `[[term:nombre]]` y `[[note:id]]`.
> - `references/04-authoring/block-directives.md` (F45) — directivas `:::example`, `:::tip`, `:::warning`.
> - `references/04-authoring/depth-layers.md` (F51) — capas L1/L2/L3; glossary-term es típicamente L1.
> - `references/05-note-types/concept.md` (F78) — paraguas común; confundibles con notas concept.
> - `references/05-note-types/error-troubleshooting.md` (F82) — mensajes de error referencian términos.

---

## §1 · Propósito y alcance

Una nota `glossary-term` documenta **un término técnico aislado** con su
definición, formas, aliases, confundibles y notas donde aparece. Es la
"entrada de diccionario" del corpus: corta, buscable por texto exacto,
con backlinks bidireccionales.

`glossary-term` cubre: jerga técnica (`MVCC`, `xmin`, `fork`), siglas
(`DDL`, `DML`, `ACID`), nombres de features (`Span<T>`, `Result<T>` en Rust),
términos operativos (`sharding`, `replication`), y conceptos breves que no
ameritan una nota `concept` completa.

**Fuera de alcance:**

- Concepto complejo con mecanismo → `concept` (F78).
- API o endpoint → `api-reference` (F79).
- Comparación entre términos → `comparison` (F87).
- Procedure → `procedure` (F80).
- Tabla completa de términos → `cheatsheet` (F90).

---

## §2 · Estructura de la nota

### §2.1 · Frontmatter (orden canónico)

```yaml
---
title: "<término canónico>"
note-type: glossary-term
status: draft | published
summary: "<≤ 200 chars, 1 línea — la definición corta>"
reading-time-minutes: <int ≥ 1>
tags: [type/glossary-term, domain/<uno o más>]
source: "<ruta al doc; opcional si auto-definido>"
source-type: docs | spec | wiki | article
source-anchor: "<page|chapter|section_path>"
source-url: "<opcional>"
retrieved: <YYYY-MM-DD>
vendor: "<opcional>"
product: "<opcional>"
product-version: "<opcional>"
related: "[[note:donde-aparece-1]], [[note:donde-aparece-2]]"
---
```

`source-bearing` es **opcional** (F75 §6.12): el término puede ser
auto-definido por el SDM (e.g., un acrónimo creado en una nota técnica
sin proveniencia formal).

### §2.2 · Apertura común (heredada de F75 §3)

```markdown
# {title}

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | ... |
| **Procedencia** | source (source-type) §source-anchor · recuperado YYYY-MM-DD |
| **Estado** | Publicado (published) / Borrador (draft) |
| **Tiempo de lectura** | N min |

## TL;DR
{1-2 frases; el L1 es la definición del término}

{layer:l1}

## Definición
```

### §2.3 · Las 8 secciones específicas + 1 opcional + 3 de cierre

| # | Sección | Estado | Notas |
|---|---|---|---|
| 1 | `## TL;DR` | obligatoria | 1-2 frases = definición del término. |
| 2 | `## Definición` | obligatoria | 1 frase (criterio #1). |
| 3 | `## Formas` | obligatoria | Tabla inglés/español/siglas. Criterio #3. |
| 4 | `## Aliases` | obligatoria | Lista con ≥ 1 alias (criterio #1). |
| 5 | `## Contexto` | obligatoria | `:::tip` con dominio / sistema donde se usa. |
| 6 | `## Ejemplos` | obligatoria | ≥ 1 `:::example` con uso real. |
| 7 | `## Confundibles` | obligatoria | Tabla con `[[note:]]` o `[[term:]]` (criterio #2). |
| 8 | `## Notas donde aparece` | obligatoria | Lista con `[[note:id]]` (criterio #3). |
| 9 | `## Términos relacionados` | opcional | Lista con `[[term:x]]` (F75 §6.12). |
| 10 | `## Backlinks` | **obligatorio** (F75 §6.12) | Cierre común. |
| 11 | `## Queries` | si queries activas | Cierre común. |

### §2.4 · Anti-patrón duro (F75 §6.12)

> "No hacer la nota más larga de 30 líneas; es un término, no un artículo."

Reglas:
- **≤ 30 líneas totales** por nota (sin contar el frontmatter).
- Si excede, partir en `concept` (F78) o `procedure` (F80).
- La brevedad es parte del contrato.

### §2.5 · Autoevaluación (F102)

Tipos de pregunta asignados a `glossary-term` (ver
`references/09-study/self-evaluation.md` §3):

| Tipo de pregunta | Asignado |
|---|---|
| Recuerdo | ✅ |
| Aplicación | — |
| Diagnóstico | — |
| Decisión | — |
| Predicción | — |

Notas: **único tipo donde solo recuerdo aplica** — terminología pura.
La `glossary-term` se considera referencia pura (ver
`self-evaluation.md` §4); el término + la definición breve son la
unidad de recuerdo. La nota puede declarar `self-evaluation-types` como
superset del default (nunca subset).

---

## §3 · Componentes mínimos

| Componente | Mínimo | Fuente |
|---|---|---|
| Cabecera (F75 §2) | 5 campos en orden | F75 §2.1 |
| `## TL;DR` | 1-2 frases = definición | F75 §6.12 |
| `## Definición` | 1 frase ≤ 30 palabras | criterio #1 |
| `## Formas` | Tabla con ≥ 2 formas (inglés + español o forma + sigla) | criterio #3 |
| `## Aliases` | Lista con ≥ 1 alias | criterio #1 |
| `## Contexto` | `:::tip` con dominio | ROADMAP |
| `## Ejemplos` | ≥ 1 `:::example` con uso real | F75 §6.12 |
| `## Confundibles` | Tabla con ≥ 1 confundible con `[[note:]]` o `[[term:]]` | criterio #2 |
| `## Notas donde aparece` | ≥ 1 `[[note:id]]` | ROADMAP |
| `## Backlinks` | obligatorio | F75 §6.12 |
| Marcas `{src:blk_xxxx}` | Opcional (puede no tener SDM) | F75 §6.12 |

### §3.1 · Tabla canónica de Formas (inglés/español/siglas)

```
| Idioma | Forma | Notas |
|---|---|---|
| Inglés | MVCC (Multi-Version Concurrency Control) | forma canónica |
| Español | CCMV (Control de Concurrencia Multiversión) | traducción literal |
| Sigla | MVCC | universal; no varía por idioma |
```

Reglas:
- **≥ 2 formas** (inglés + español) o (forma completa + sigla).
- La forma canónica va marcada.
- Las siglas son universales (no traducir, p.ej., `MVCC` es igual en ambos idiomas).

### §3.2 · Patrón de Confundibles (criterio #2 — bidireccionalidad)

```
## Confundibles

| Término confundible | Diferencia clave | Nota |
|---|---|---|
| `2PL` (Two-Phase Locking) | 2PL bloquea filas; MVCC usa snapshots | [[note:two-phase-locking]] |
| `SERIALIZABLE` (PostgreSQL) | SERIALIZABLE en PostgreSQL usa SSI; en otros motores usa 2PL | [[note:postgres-isolation-levels]] |
| `Snapshot isolation` | Sinónimo aproximado pero no idéntico | (sin nota propia) |
```

Reglas:
- ≥ 1 confundible con `[[note:id]]` o `[[term:x]]`.
- Cada confundible tiene **enlace bidireccional**: la nota target también enlaza de vuelta aquí (mediante `[[term:nombre-de-esta-nota]]`).
- Las notas confundibles usan `[[term:nombre-de-esta-nota]]` para apuntar de vuelta.

---

## §4 · Reglas de contenido

### §4.1 · Densidad y estructura (R1-R8 de F76)

- **R1** `## TL;DR` ≤ 30 líneas totales de la nota (F75 §6.12 anti-patrón duro).
- **R2-R5** aplican con brevedad; la nota raramente excede L1.
- **R6** Cada H2/H3 tiene ≥ 1 párrafo, tabla o callout (lista con bullets cuenta como contenido si tiene contexto).
- **R7** Si la nota es > 30 líneas, partir en `concept`.
- **R8** Densidad `{src:}` ≥ 0.80 sobre filas fácticas (opcional en glossary-term auto-definido).

### §4.2 · Marcas inline (F46)

- **`{src:blk_xxxx}`** — 12 caracteres hexadecimales (INV-I5). Opcional; se usa cuando el término viene del SDM (ej: docs oficiales).
- **`[[term:nombre]]`** — enlaces a otros términos; cada uso crea un backlink bidireccional (criterio #3).
- **`[[note:id]]`** — enlaces a notas donde el término aparece (criterio #3).
- **`:::external`** — definiciones tomadas de fuentes externas (Wikipedia, blogs).

### §4.3 · Directivas de bloque (F45)

| Sección | Directiva preferida | Justificación |
|---|---|---|
| `## Definición` | 1 frase | criterio #1. |
| `## Contexto` | `:::tip` por dominio | ROADMAP. |
| `## Ejemplos` | `:::example` por uso real | F75 §6.12. |
| `## Confundibles` | Tabla con `[[note:]]` o `[[term:]]` | criterio #2. |

### §4.4 · Anti-patrones

1. **"Nota demasiado larga"** (F75 §6.12) — > 30 líneas. Solución: partir en `concept`.
2. **"Sin definición de 1 frase"** (criterio #1) — la nota empieza con prosa extendida. Solución: 1 frase ≤ 30 palabras en `## Definición`.
3. **"Sin aliases"** (criterio #1) — `## Aliases` vacío. Solución: ≥ 1 alias obligatorio.
4. **"Confundibles sin enlace bidireccional"** (criterio #2) — la nota lista confundibles pero las notas target no enlazan de vuelta. Solución: documentar la convención; verificación opcional.
5. **"Sin formas en ambos idiomas"** (criterio #3) — `## Formas` solo contiene inglés. Solución: ≥ 1 forma en español o sigla universal.
6. **"Sin `[[term:]]` en otras notas"** (criterio #3) — los términos no se usan como `[[term:X]]` en otras notas. Solución: documentar la convención de backlinks.
7. **"Mezcla de términos"** — una nota con 2+ términos. Solución: una nota por término.
8. **"Sección solo de viñetas"** (R6) — `## Aliases` con bullets sin contexto. Solución: lista con descripción o tabla.

### §4.5 · Diferencias operativas

| Concepto | Definición operativa |
|---|---|
| **Término canónico** | La forma principal del término (usualmente inglés). |
| **Alias** | Variante ortográfica, sigla, o forma relacionada (e.g., "MVCC" para "Multi-Version Concurrency Control"). |
| **Forma bilingüe** | Traducción al español (o viceversa). |
| **Confundible** | Término similar que se confunde con este; enlaza bidireccionalmente. |
| **Bidireccionalidad** | Confundibles se enlazan mutuamente; notas-que-apuntan-aquí usan `[[term:nombre]]` apuntando aquí. |
| **Sigla universal** | Sigla que no se traduce (e.g., `API`, `SQL`, `TCP`); vale en todos los idiomas. |

---

## §5 · Activación por perfil

```yaml
notes:
  types:
    glossary-term:
      max_lines: 30                       # default: 30 (F75 §6.12 anti-patrón duro)
      require_phrase_definition: true     # default: true (criterio #1)
      require_aliases: true               # default: true (criterio #1)
      require_bilingual_forms: true       # default: true (criterio #3)
      require_confundibles_with_links: true  # default: true (criterio #2)
      min_aliases: 1
      min_forms: 2                        # inglés + español o forma + sigla
      min_confundibles: 1
      enforce_bidirectional_confundibles: true  # default: true (criterio #2)
```

| Campo | Default | Significado |
|---|---|---|
| `max_lines` | `30` | Máximo de líneas por nota (F75 §6.12 anti-patrón duro). |
| `require_phrase_definition` | `true` | `## Definición` con 1 frase ≤ 30 palabras (criterio #1). |
| `require_aliases` | `true` | `## Aliases` con ≥ 1 alias (criterio #1). |
| `require_bilingual_forms` | `true` | `## Formas` con ≥ 2 formas (inglés + español o forma + sigla) (criterio #3). |
| `require_confundibles_with_links` | `true` | `## Confundibles` con `[[note:]]` o `[[term:]]` (criterio #2). |
| `min_aliases` | `1` | Mínimo de aliases. |
| `min_forms` | `2` | Mínimo de formas (inglés + español o forma + sigla). |
| `min_confundibles` | `1` | Mínimo de confundibles. |
| `enforce_bidirectional_confundibles` | `true` | Cada confundible con backlink (criterio #2). |

---

## §6 · Checklist de cierre

Antes de publicar:

- [ ] Cabecera con 5 campos en orden (F75 §2.1).
- [ ] `## TL;DR` = 1-2 frases = definición del término (criterio #1).
- [ ] `## Definición` con 1 frase ≤ 30 palabras (criterio #1).
- [ ] `## Formas` con ≥ 2 formas (inglés + español o forma + sigla) (criterio #3).
- [ ] `## Aliases` con ≥ 1 alias (criterio #1).
- [ ] `## Contexto` con `:::tip` por dominio (ROADMAP).
- [ ] `## Ejemplos` con ≥ 1 `:::example` (F75 §6.12).
- [ ] `## Confundibles` con ≥ 1 confundible con `[[note:]]` o `[[term:]]` (criterio #2).
- [ ] `## Notas donde aparece` con ≥ 1 `[[note:id]]` (criterio #3).
- [ ] `## Backlinks` obligatorio (F75 §6.12).
- [ ] **≤ 30 líneas totales** (F75 §6.12 anti-patrón duro).
- [ ] `density_check.py --note <path>` exit 0.

---

## §7 · Nota mínima viable

Ejemplo canónico de ≤ 30 líneas. Pasa `density_check.py --strict` exit 0.

```markdown
---
title: "MVCC"
note-type: glossary-term
status: draft
tags: [type/glossary-term, domain/databases]
source: "PostgreSQL 16 docs"
source-type: docs
source-anchor: "mvcc-intro"
retrieved: 2026-09-27
related: "[[note:postgresql-mvcc]]"
---

# MVCC

## TL;DR
MVCC (Multi-Version Concurrency Control) permite a múltiples transacciones leer y escribir sin bloqueos manteniendo un snapshot por sesión. {src:blk_g00000000001}

{layer:l1}

## Definición
Técnica de control de concurrencia donde cada transacción ve un snapshot consistente del estado de la base de datos sin necesidad de bloqueos de lectura.

## Formas
| Idioma | Forma |
|---|---|
| Inglés | Multi-Version Concurrency Control |
| Español | Control de Concurrencia Multiversión |
| Sigla | MVCC |

## Aliases
- Concurrency control via snapshots
- Multi-versioning

## Contexto
:::tip
Usado en PostgreSQL, MySQL InnoDB, Oracle, y la mayoría de RDBMS modernas.
:::

## Ejemplos
:::example
`SELECT * FROM users WHERE id = 1;` retorna el snapshot del último COMMIT antes de la transacción, incluso si otras transacciones modifican la fila.
:::

## Confundibles
| Término | Diferencia |
|---|---|
| `2PL` | Bloquea filas; MVCC usa snapshots |
| `Snapshot isolation` | Sinónimo aproximado pero no idéntico |

## Notas donde aparece
- [[note:postgresql-mvcc]]
- [[note:postgresql-configuration]]

## Backlinks
- [[note:postgresql-mvcc]]
```

Esta nota mínima (~25 líneas) cubre R1-R8 de F76 y los 3 criterios del
ROADMAP. Sirve de **referencia de forma**.

---

## §8 · Wirings y referencias cruzadas

- **F11** `assets/profile.template.yaml` — defaults de §5.
- **F12** `references/04-authoring/notemark.md` — directivas `:::example`, `:::tip`, `:::warning`.
- **F44** `references/03-knowledge/note-plan.md` — selector asigna `glossary-term` cuando la unidad es un término aislado.
- **F45** `references/04-authoring/block-directives.md` — directivas consumidas.
- **F46** `references/04-authoring/inline-marks.md` — `[[term:nombre]]` para enlaces entre términos; `[[note:id]]` para notas donde aparece.
- **F47** `references/04-authoring/properties.md` — frontmatter sin `source-bearing` obligatorio.
- **F51** `references/04-authoring/depth-layers.md` — capas L1/L2/L3; glossary-term típicamente L1.
- **F72** `references/07-visual/tokens.md` — colores semánticos de las directivas.
- **F75** `references/07-visual/note-templates.md` — cabecera, apertura/cierre común, §6.12 patrón resumido + anti-patrón.
- **F76** `references/07-visual/density.md` — tabla cerrada R1-R8 ejecutable.
- **F77** `evals/visual/` — verificación visual multi-destino.
- **F78** `references/05-note-types/concept.md` — paraguas común; confundibles con notas concept.
- **F79** `references/05-note-types/api-reference.md` — APIs que usan el término.
- **F82** `references/05-note-types/error-troubleshooting.md` — errores referencian términos.

---

## §9 · Verificación al cierre de la fase

- `wc -l references/05-note-types/glossary-term.md` ≤ 400 líneas.
- §2 con 4 subsecciones (incluye anti-patrón de 30 líneas).
- §3 con tabla de componentes mínimos ≥ 9 filas + §3.1 tabla de Formas + §3.2 patrón de Confundibles.
- §4 con 5 subsecciones.
- §5 con tabla de campos del perfil y sus defaults.
- §6 con checklist de cierre ≥ 12 items.
- §7 con nota mínima viable (≤ 30 líneas).
- §8 con ≥ 14 wirings.
- §9 lista de verificación explícita.

**Criterios de aceptación del ROADMAP F89:**

1. _Cada término tiene definición de una frase y alias completos._ → battery C2: `## Definición` con 1 frase ≤ 30 palabras Y `## Aliases` con ≥ 1 alias.
2. _Los confundibles se enlazan mutuamente._ → battery C3: `## Confundibles` con `[[note:]]` o `[[term:]]`; la bidireccionalidad se documenta en el doc.
3. _Buscar en inglés o español lleva a la misma nota en los 3 destinos._ → battery C4: `## Formas` contiene inglés Y español (o forma + sigla).
