# `chapter-digest` — `references/05-note-types/chapter-digest.md`

> Documento normativo de la **Fase 86** del roadmap (tipo `[núcleo]`). Define
> el patrón de la nota de tipo `chapter-digest`: 9 secciones obligatorias
> + 2 opcionales + cierre con `## Ver también` siempre, cobertura completa
> de los argumentos del capítulo, continuidad explícita en ambos sentidos,
> conceptos nuevos enlazados a notas propias, erratas, ejercicios y citas
> textuales.
>
> **Cuándo cargar:** tras decidir el tipo de nota (selector F93) cuando el
> `note-type` resuelto es `chapter-digest`; antes de redactar la primera
> sección. Instancia el patrón común de `references/07-visual/note-templates.md`
> (F75) §6.9.
>
> **Wirings:**
> - `references/07-visual/note-templates.md` (F75) §6.9 — patrón resumido.
> - `references/07-visual/density.md` (F76) — reglas R1-R8 (L1 puede ser extendida).
> - `references/04-authoring/properties.md` (F47) — frontmatter; `coverage: summary` (enum).
> - `references/04-authoring/inline-marks.md` (F46) — `{src:blk_xxxx}` por cita; `[[note:id]]` para conceptos.
> - `references/04-authoring/block-directives.md` (F45) — directivas `:::example`, `:::warning`, `:::note`, `:::external`, `:::derived`, `:::tip`.
> - `references/04-authoring/depth-layers.md` (F51) — L1 extendida, L2 medio, L3 detalle.
> - `references/05-note-types/concept.md` (F78) — paraguas común; conceptos nuevos referencian notas concept.
> - `references/05-note-types/api-reference.md` (F79) — capítulos que documentan APIs.
> - `references/05-note-types/architecture.md` (F83) — capítulos que documentan arquitecturas.
> - `references/05-note-types/procedure.md` (F80) — capítulos que documentan procedimientos.

---

## §1 · Propósito y alcance

Una nota `chapter-digest` documenta **un capítulo entero de un libro técnico,
RFC, spec o manual**, reducido a sus argumentos principales. El lector que
solo lee los digests de un libro debe poder reconstruir el argumento del
libro sin volver al original.

Esta es la única nota `[núcleo]` (junto con `concept`, `api-reference`,
`procedure`) que documenta una unidad **secuencial** (capítulos dependen
de capítulos anteriores y alimentan capítulos siguientes). Por eso la
continuidad es **obligatoria en ambos sentidos** (criterio #1) y los
**conceptos reutilizables deben tener nota propia** (criterio #2), no pueden
quedarse en un párrafo del digest.

Cubre libros técnicos (PostgreSQL docs, Kubernetes docs, Redis docs,
DDIA), RFCs (HTTP, TLS, DNS), papers, manuales, y guías extensas.

**Fuera de alcance:**

- Un único concepto aislado → `concept` (F78).
- Una API o endpoint → `api-reference` (F79).
- Una arquitectura de sistema → `architecture` (F83).
- Un procedimiento paso a paso → `procedure` (F80).
- Comparar 2+ capítulos/libros → `comparison` (F87).
- Cambios entre versiones de un capítulo → `version-delta` (F88).

---

## §2 · Estructura de la nota

### §2.1 · Frontmatter (orden canónico, `source-bearing` obligatorio)

```yaml
---
title: "<libro/spec> — Ch N: <título del capítulo>"
note-type: chapter-digest
status: draft | published
summary: "<≤ 200 chars, 1 línea>"
reading-time-minutes: <int ≥ 1>
tags: [type/chapter-digest, domain/<uno o más>, source/<libro>]
source: "<ruta al libro/spec>"
source-type: book | rfc | spec | docs | paper
source-anchor: "<chapter|section_path>"
source-url: "<opcional>"
retrieved: <YYYY-MM-DD>
vendor: "<autor o fundación>"
product: "<nombre del libro/spec>"
product-version: "<versión>"
coverage: summary                # F47 enum; "summary" indica que esta nota es digest
related: "[[note:chapter-N-1-digest]], [[note:chapter-N+1-digest]]"
---
```

`source-bearing` es **obligatorio** (F75 §6.9). `coverage: summary` es el
único valor del enum que aplica; los digests son siempre `summary`.

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
{L1 extendida — ≤ 120 palabras para capítulos densos; F75 §6.9 permite > 60 palabras}

{layer:l2}

## Resumen ejecutivo
```

### §2.3 · Las 9 secciones obligatorias + 2 opcionales + 3 de cierre

| # | Sección | Estado | Notas |
|---|---|---|---|
| 1 | `## TL;DR` | obligatoria | L1 extendida (≤ 120 palabras). |
| 2 | `## Resumen ejecutivo` | obligatoria | 1-2 párrafos; el más importante del digest. |
| 3 | `## Continuidad` | obligatoria | 2 sub-secciones: `### Hacia atrás`, `### Hacia adelante`. Criterio #1. |
| 4 | `## Puntos clave` | obligatoria | 3-7 bullets; los takeaways principales. |
| 5 | `## Conceptos nuevos` | obligatoria | Sub-sección por concepto con `[[note:id]]` o `[[term:nombre]]`. Criterio #2. |
| 6 | `## Citas textuales` | obligatoria | `:::external` con citas literales del SDM. |
| 7 | `## Énfasis del autor` | obligatoria | `:::note` con las observaciones que el autor explícitamente destaca. |
| 8 | `## Detalles` | obligatoria | Sub-secciones H3: `### Mecanismos`, `### Código`, `### Diagramas`. |
| 9 | `## Conexiones` | obligatoria | `:::derived` con conexiones inferidas a otras notas. |
| 10 | `## Erratas` | obligatoria | `:::warning` por error conocido en la edición. |
| 11 | `## Ejercicios` | obligatoria | ≥ 1 ejercicio en `:::example`. |
| 12 | `## Backlinks` | si hay aristas | Cierre común. |
| 13 | `## Queries` | si queries activas | Cierre común. |
| 14 | `## Ver también` | **siempre** (F75 §6.9) | Cierre común; enlaza a `## Continuidad` y a otras notas relacionadas. |

### §2.4 · Capas (heredado de F51, F75 §6.9 marca L1 extendida)

| Capa | Marcador | Contenido |
|---|---|---|
| L1 | `{layer:l1}` | Solo `## TL;DR`. **Extendida**: ≤ 120 palabras (F75 §6.9 permite > 60). |
| L2 | `{layer:l2}` | Resumen ejecutivo, Continuidad, Puntos clave, Conceptos nuevos, Citas, Énfasis, Conexiones. 50-70% del total. |
| L3 | `{layer:l3}` | Detalles, Erratas, Ejercicios. Si > 100 líneas, `:::collapsible` con `default_open: false` (R7). |

### §2.5 · Autoevaluación (F102)

Tipos de pregunta asignados a `chapter-digest` (ver
`references/09-study/self-evaluation.md` §3):

| Tipo de pregunta | Asignado |
|---|---|
| Recuerdo | ✅ |
| Aplicación | — |
| Diagnóstico | — |
| Decisión | ✅ |
| Predicción | — |

Notas: recuerdo (puntos clave del capítulo) + decisión (cuál idea
justifica más la atención). Aplicación + diagnóstico se añaden solo si
la nota conserva ejemplos ejecutables del capítulo. La nota puede
declarar `self-evaluation-types` como superset del default.

---

## §3 · Componentes mínimos

| Componente | Mínimo | Fuente |
|---|---|---|
| Cabecera (F75 §2) | 5 campos en orden | F75 §2.1 |
| `## TL;DR` | L1 extendida, ≤ 120 palabras | F76 R1 + F75 §6.9 |
| `## Resumen ejecutivo` | 1-2 párrafos | F75 §6.9 |
| `## Continuidad` | 2 sub-secciones (`### Hacia atrás`, `### Hacia adelante`) con enlaces | criterio #1 + ROADMAP |
| `## Puntos clave` | 3-7 bullets | F75 §6.9 |
| `## Conceptos nuevos` | ≥ 3 conceptos con `[[note:id]]` o `[[term:nombre]]` | criterio #2 + ROADMAP |
| `## Citas textuales` | ≥ 1 `:::external` con cita literal del SDM | F75 §6.9 + ROADMAP |
| `## Énfasis del autor` | ≥ 1 `:::note` con observación del autor | ROADMAP |
| `## Detalles` | Sub-secciones H3 con mecanismos / código / diagramas | F75 §6.9 + ROADMAP |
| `## Conexiones` | ≥ 1 `:::derived` con conexión inferida | F75 §6.9 + ROADMAP |
| `## Erratas` | ≥ 1 `:::warning` por error conocido en la edición | ROADMAP |
| `## Ejercicios` | ≥ 1 ejercicio en `:::example` con enunciado + pista | ROADMAP |
| Marcas `{src:blk_xxxx}` | ≥ 1 por cita, concepto y errata del SDM | F46 + F76 R8 |
| Anclaje visual | ≥ 1 cada 200 palabras (tablas y diagramas cuentan) | F76 R3 |
| Cierre | `## Backlinks` + `## Queries` + `## Ver también` | F75 §6.9 |

### §3.1 · Tabla canónica de Conceptos nuevos

```
| Concepto | Nota propia | Definición breve |
|---|---|---|
| `MVCC` | [[note:postgresql-mvcc]] | Control de concurrencia multiversión |
| `xmin` | [[note:postgresql-xmin]] | ID de transacción que insertó la fila |
| `xmax` | [[note:postgresql-xmax]] | ID de transacción que eliminó la fila |
| `clog` | [[note:postgresql-clog]] | Commit log: estado de cada transacción |
```

Reglas duras:
- **≥ 3 conceptos** por digest.
- Cada concepto enlaza con `[[note:id]]` (criterio #2: "nota propia enlazada") o `[[term:nombre]]` si el concepto aún no tiene nota dedicada.
- Si un concepto reutilizable no tiene nota propia, el digest lo declara como `:::warning` "concepto sin nota propia — crear nota concept o glossary-term".
- La columna `Definición breve` permite entender el concepto sin abrir la nota; 1 frase ≤ 20 palabras.

### §3.2 · Patrón de Continuidad

```markdown
## Continuidad

### Hacia atrás
El capítulo anterior ([[note:chapter-12-digest]]) introdujo el modelo de almacenamiento físico. Aquí extendemos con el modelo de concurrencia sobre disco.

### Hacia adelante
El siguiente capítulo ([[note:chapter-14-digest]]) cubre tips de performance basados en la comprensión de MVCC. {src:blk_c00000000001}
```

Reglas:
- 2 sub-secciones explícitas: `### Hacia atrás` y `### Hacia adelante` (criterio #1).
- Cada sub-sección tiene ≥ 1 enlace `[[note:chapter-X-digest]]` o `[[note:concepto]]`.
- El texto describe **qué se conecta** (1-2 frases), no solo que existe conexión.

---

## §4 · Reglas de contenido

### §4.1 · Densidad y estructura (R1-R8 de F76)

- **R1** `## TL;DR` ≤ 120 palabras (F75 §6.9: L1 extendida permitida).
- **R2** Cada párrafo del L2 ≤ 200 palabras.
- **R3** ≥ 1 anclaje visual cada 200 palabras. Tablas, diagramas y callouts cuentan.
- **R4** ≤ 3 callouts consecutivos sin prosa intermedia.
- **R5** ≤ 5 viñetas consecutivas.
- **R6** Cada H2/H3 tiene ≥ 1 párrafo, tabla, callout, figura, diagrama o código.
- **R7** Cualquier sección > 100 líneas → `:::collapsible` con `default_open: false`.
- **R8** Densidad `{src:}` ≥ 0.80 sobre filas fácticas (citas, erratas, conceptos).

### §4.2 · Marcas inline (F46)

- **`{src:blk_xxxx}`** — 12 caracteres hexadecimales (INV-I5). Cada cita textual, errata y concepto del SDM lleva `{src:blk_xxxx}`.
- **`[[term:nombre]]`** — primera aparición del término (INV-I2).
- **`[[note:id]]`** — enlaces a notas propias: `[[note:postgresql-mvcc]]` para conceptos, `[[note:chapter-12-digest]]` para continuidad, `[[note:procedure-de-instalacion]]` para procedures referenciados.
- **`:::external`** — citas textuales del SDM, distinguibles de la prosa del digest.
- **`:::derived`** — conexiones inferidas que el SDM NO dice explícitamente; el autor del digest las propone.

### §4.3 · Directivas de bloque (F45)

| Sección | Directiva preferida | Justificación |
|---|---|---|
| `## Resumen ejecutivo` | 1-2 párrafos | F75 §6.9. |
| `## Continuidad` | Sub-secciones H3 con enlaces | criterio #1. |
| `## Puntos clave` | Lista con bullets | F75 §6.9 (3-7 bullets). |
| `## Conceptos nuevos` | Tabla con `[[note:id]]` | criterio #2. |
| `## Citas textuales` | `:::external` con bloque `quote` | F45 §6. |
| `## Énfasis del autor` | `:::note` por observación | F45 §6 fila 12. |
| `## Detalles` | Sub-secciones H3 + bloques `code` | F75 §6.9. |
| `## Conexiones` | `:::derived` por conexión inferida | F45 §6. |
| `## Erratas` | `:::warning` por error | F45 §6 fila 1. |
| `## Ejercicios` | `:::example` con `**Enunciado:**` + `code` | F45 §6 fila 10. |

### §4.4 · Anti-patrones fundamentales

1. **"Continuidad solo hacia adelante"** (criterio #1) — el digest menciona el siguiente capítulo pero no el anterior. Solución: battery C2 rechaza digest sin `### Hacia atrás`.
2. **"Concepto sin `[[note:id]]`"** (criterio #2) — el digest menciona "MVCC" sin enlazar a la nota `postgresql-mvcc`. Solución: cada concepto en `## Conceptos nuevos` debe tener `[[note:id]]` o `[[term:nombre]]`.
3. **"Resumen demasiado vago"** (criterio #3) — el `## Resumen ejecutivo` no captura los argumentos principales del SDM. Solución: battery C4 verifica cobertura de keywords.
4. **"Puntos clave > 7 bullets"** — anti-patrón de F75 §6.9. Solución: máximo 7; agrupar si excede.
5. **"Concepto inventado"** — el digest menciona un concepto que NO está en el SDM. Solución: cada concepto lleva `{src:blk_xxxx}` apuntando al SDM.
6. **"Errata especulativa"** — el autor asume erratas sin fuente. Solución: cada errata lleva `{src:blk_xxxx}` y referencia la página.
7. **"Ejercicio sin enunciado"** — `:::example` con solo código. Solución: el enunciado va antes del código.
8. **"Sección solo de viñetas"** (R6) — `## Puntos clave` con bullets sin contexto. Solución: 1 párrafo introductorio antes de los bullets.
9. **"Notas referenciadas que no existen"** — `[[note:concepto-inexistente]]` produce backlinks rotos. Solución: el battery verifica que el target existe o se declara en `[[term:]]`.
10. **"Sin `## Ver también`"** — F75 §6.9 declara que `## Ver también` es **siempre** obligatorio en chapter-digest. Solución: batería rechaza digest sin esta sección.

### §4.5 · Diferencias operativas

| Concepto | Definición operativa |
|---|---|
| **Capítulo** | Unidad secuencial de un libro; depende de capítulos anteriores y alimenta capítulos siguientes. |
| **Continuidad** | Relación explícita entre este capítulo y el anterior/siguiente. |
| **Concepto reutilizable** | Concepto que aparece en ≥ 2 capítulos o que tiene nota propia en el corpus. |
| **Cita textual** | Frase literal del SDM entre comillas, atribuible a página/sección. |
| **Énfasis del autor** | Observación que el autor explícitamente destaca (warning, design rationale, "this is critical"). |
| **Errata** | Error conocido en una edición específica del libro; puede ser tipográfico o técnico. |
| **Ejercicio** | Pregunta o tarea al final del capítulo; típicamente con respuesta. |
| **Conexión inferida** | Relación no explícita en el SDM pero deducible por el lector; se marca como `:::derived`. |

---

## §5 · Activación por perfil

```yaml
notes:
  types:
    chapter-digest:
      coverage_default: summary        # valor único del enum; siempre 'summary'
      require_continuity_both_directions: true  # criterio #1
      require_concepts_with_notes: true  # criterio #2
      require_exec_summary: true        # criterio #3
      min_concepts: 3
      max_key_points: 7
      min_citations: 1
      min_errata: 1
      min_exercises: 1
      max_tldr_words: 120              # F75 §6.9: L1 extendida
      enforce_ver_tambien: true        # F75 §6.9: Ver también siempre
```

| Campo | Default | Significado |
|---|---|---|
| `coverage_default` | `summary` | Único valor para chapter-digest. |
| `require_continuity_both_directions` | `true` | `## Continuidad` tiene `### Hacia atrás` Y `### Hacia adelante` (criterio #1). |
| `require_concepts_with_notes` | `true` | Cada concepto reutilizable tiene `[[note:id]]` (criterio #2). |
| `require_exec_summary` | `true` | `## Resumen ejecutivo` obligatorio (criterio #3). |
| `min_concepts` | `3` | Mínimo de conceptos nuevos. |
| `max_key_points` | `7` | Máximo de bullets en `## Puntos clave` (anti-patrón). |
| `min_citations` | `1` | Mínimo de citas textuales en `:::external`. |
| `min_errata` | `1` | Mínimo de erratas documentadas. |
| `min_exercises` | `1` | Mínimo de ejercicios. |
| `max_tldr_words` | `120` | F75 §6.9: L1 extendida permitida. |
| `enforce_ver_tambien` | `true` | F75 §6.9: `## Ver también` siempre obligatorio. |

---

## §6 · Checklist de cierre

Esta sección resume el bloque del tipo. La fuente normativa es
`references/10-quality/checklists-by-type.md` §4.9. Esta copia se conserva
para que el agente que carga solo este archivo tenga la lista delante;
cualquier cambio debe aplicarse primero allí y después sincronizarse aquí.

### §6.1 · Bloqueantes [B]

- [ ] [B] Cabecera con 5 campos en orden + `coverage: summary` (F75 §6.9).
- [ ] [B] `source-bearing` obligatorio (F75 §6.9).
- [ ] [B] `## TL;DR` ≤ 120 palabras (F75 §6.9: L1 extendida).
- [ ] [B] `## Resumen ejecutivo` con 1-2 párrafos (criterio #3).
- [ ] [B] `## Continuidad` con `### Hacia atrás` Y `### Hacia adelante` (criterio #1).
- [ ] [B] `## Puntos clave` con 3-7 bullets.
- [ ] [B] `## Conceptos nuevos` con ≥ 3 conceptos con `[[note:id]]` o `[[term:nombre]]` (criterio #2).
- [ ] [B] `## Citas textuales` con ≥ 1 `:::external` con cita literal.
- [ ] [B] `## Detalles` con sub-secciones H3 (mecanismos / código / diagramas).
- [ ] [B] `## Ver también` siempre presente (F75 §6.9).
- [ ] [B] Densidad `{src:}` ≥ 0.80 sobre filas fácticas (R8).
- [ ] [B] `density_check.py --note <path>` exit 0.

### §6.2 · Recomendados [R]

- [ ] [R] `## Énfasis del autor` con ≥ 1 `:::note`. **OMIT en `reference`** (F112 §5.1).
- [ ] [R] `## Conexiones` con ≥ 1 `:::derived`. **OMIT en `reference`** (F112 §5.1).
- [ ] [R] `## Erratas` con ≥ 1 `:::warning`. **OMIT en `reference`** (F112 §5.1).
- [ ] [R] `## Ejercicios` con ≥ 1 ejercicio en `:::example`. **OMIT en `reference`** (F112 §5.1).
- [ ] [R] Cierre: `## Backlinks` + `## Queries`.

---

## §7 · Nota mínima viable

Ejemplo canónico de ~80-100 líneas para un capítulo de libro técnico.
Pasa `density_check.py --strict` exit 0.

```markdown
---
title: "PostgreSQL 16 — Ch 13: Concurrency Control (digest)"
note-type: chapter-digest
status: draft
tags: [type/chapter-digest, domain/databases, source/postgresql-docs]
source: "PostgreSQL 16 — Server Administration"
source-type: docs
source-anchor: "concurrency-control"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
coverage: summary
related: "[[note:chapter-12-physical-storage-digest]], [[note:chapter-14-performance-tips-digest]]"
---

# PostgreSQL 16 — Ch 13: Concurrency Control (digest)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Digest del Chapter 13 de la doc oficial de PostgreSQL 16 sobre control de concurrencia: MVCC, isolation levels, explicit locking. |
| **Procedencia** | PostgreSQL 16 — Server Administration (docs) §concurrency-control · recuperado 2026-09-27 |
| **Versión** | PostgreSQL 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 5 min |

## TL;DR
El capítulo introduce MVCC como mecanismo por defecto para la concurrencia: cada transacción ve un snapshot consistente basado en `xmin`/`xmax`. Cubre los 4 niveles de aislamiento (Read Uncommitted emula a Read Committed; Read Committed es el default; Repeatable Read y Serializable usan snapshot-based) y los bloqueos explícitos (`FOR UPDATE`, `FOR SHARE`). {src:blk_c00000000010}

{layer:l2}

## Resumen ejecutivo
PostgreSQL usa MVCC (Multi-Version Concurrency Control) por defecto: en lugar de bloquear filas para mantener aislamiento, cada fila lleva marcas de transacción (`xmin`, `xmax`) que permiten a cada sesión ver su propio snapshot consistente sin interferir con otras. Esto maximiza concurrencia pero requiere `VACUUM` periódico para reclamar espacio de filas muertas. El capítulo documenta los 4 niveles de aislamiento SQL estándar (Read Uncommitted, Read Committed, Repeatable Read, Serializable), cómo PostgreSQL implementa cada uno (con snapshot, sin bloqueos por defecto), y los bloqueos explícitos (`SELECT ... FOR UPDATE/SHARE`) cuando se necesita sincronización estricta. {src:blk_c00000000011}

## Continuidad

### Hacia atrás
El [[note:chapter-12-physical-storage-digest]] introdujo el modelo de almacenamiento físico (heap files, TOAST, FSM, VM). Aquí extendemos con el modelo de concurrencia sobre disco: cómo múltiples transacciones leen y escriben sin corromperse.

### Hacia adelante
El [[note:chapter-14-performance-tips-digest]] cubre tips de performance basados en la comprensión de MVCC — por qué `VACUUM` regular importa, cómo `work_mem` interactúa con MVCC. {src:blk_c00000000012}

## Puntos clave
- MVCC es el mecanismo por defecto; cada transacción ve un snapshot consistente.
- Los 4 niveles de aislamiento se implementan con snapshots, no con bloqueos por defecto.
- `SELECT ... FOR UPDATE/SHARE` permite sincronización explícita cuando se necesita.
- `VACUUM` es esencial para reclamar espacio de tuplas muertas generadas por MVCC.
- El catálogo del sistema (`pg_locks`, `pg_stat_activity`) expone el estado de locks.

## Conceptos nuevos

| Concepto | Nota propia | Definición breve |
|---|---|---|
| `MVCC` | [[note:postgresql-mvcc]] | Control de concurrencia multiversión |
| `xmin` | [[note:postgresql-xmin]] | ID de transacción que insertó la fila |
| `xmax` | [[note:postgresql-xmax]] | ID de transacción que eliminó la fila |
| `clog` | [[note:postgresql-clog]] | Commit log: estado de cada transacción |

## Citas textuales

> "The main advantage of using the MVCC model is that locks acquired for querying never conflict with locks acquired for writing data, so reading never blocks writing and writing never blocks reading."
> — *PostgreSQL 16 §13.1 Introduction*, retrieved 2026-09-27 {src:blk_c00000000020}

## Énfasis del autor

:::note
"Read Uncommitted has the same behavior as Read Committed in PostgreSQL" — el autor enfatiza que PostgreSQL no permite lecturas sucias incluso en Read Uncommitted. {src:blk_c00000000030}
:::

## Detalles

### Mecanismos
- `xmin`/`xmax` se almacenan en cada tupla (heap y TOAST).
- El commit log (`clog`) es un archivo en `pg_xact/` con el estado de cada transacción.
- Cada backend mantiene su propio `ActiveSnapshot` actualizado al inicio de cada query.

### Código
```sql
-- Bloqueo explícito: SELECT FOR UPDATE
SELECT * FROM accounts WHERE id = 42 FOR UPDATE;

-- Nivel de aislamiento explícito
BEGIN ISOLATION LEVEL SERIALIZABLE;
SELECT ...;
COMMIT;
```

## Conexiones

:::derived
El capítulo conecta MVCC con [[note:postgresql-architecture]] (los backends procesan tuplas siguiendo el snapshot) y con [[note:postgres-connection-errors]] (los errores `FATAL: too many connections` se relacionan con MVCC porque cada backend mantiene su propio snapshot).
:::

## Erratas

:::warning
**Edición PG 9.6, sección 13.2:** la frase "snapshot is taken at statement start" es imprecisa — en Repeatable Read el snapshot es al inicio de la transacción, no de la sentencia. Corregido en ediciones posteriores. {src:blk_c00000000040}
:::

## Ejercicios

:::example
**Ejercicio 13.1:** ¿Qué retorna `SELECT * FROM accounts WHERE id = 42` en una transacción con `READ COMMITTED` si otra transacción concurrente hace `UPDATE accounts SET balance = 0 WHERE id = 42` y luego hace `COMMIT`?

**Pista:** considera que el snapshot se renueva en cada sentencia bajo Read Committed. {src:blk_c00000000050}
:::

## Backlinks
- [[note:chapter-12-physical-storage-digest]] — capítulo previo.
- [[note:chapter-14-performance-tips-digest]] — capítulo siguiente.
- [[note:postgresql-mvcc]] — concepto principal del capítulo.

## Ver también
- [[note:postgres-connection-errors]] — errores típicos de conexión.
- [[note:procedure-postgres-failover]] — procedure de failover usando streaming replication.
```

Esta nota mínima (~95 líneas) cubre R1-R8 de F76 y los 3 criterios del
ROADMAP. Sirve de **referencia de forma**.

---

## §8 · Wirings y referencias cruzadas

- **F11** `assets/profile.template.yaml` — defaults de §5 (`min_concepts`, `enforce_ver_tambien`).
- **F12** `references/04-authoring/notemark.md` — directivas `:::example`, `:::warning`, `:::note`, `:::external`, `:::derived`, `:::tip`.
- **F44** `references/03-knowledge/note-plan.md` — selector asigna `chapter-digest` cuando la unidad es un capítulo entero.
- **F45** `references/04-authoring/block-directives.md` — directivas consumidas.
- **F46** `references/04-authoring/inline-marks.md` — `{src:blk_xxxx}` por cita; `[[note:id]]` para conceptos.
- **F47** `references/04-authoring/properties.md` — frontmatter; `coverage: summary` enum.
- **F51** `references/04-authoring/depth-layers.md` — capas L1/L2/L3; L1 extendida.
- **F66** `references/07-visual/mermaid-portable.md` — portabilidad de Mermaid en `## Detalles`.
- **F72** `references/07-visual/tokens.md` — colores semánticos de las directivas.
- **F75** `references/07-visual/note-templates.md` — cabecera, apertura/cierre común, §6.9 patrón resumido.
- **F76** `references/07-visual/density.md` — tabla cerrada R1-R8 ejecutable; L1 extendida permitida para chapter-digest.
- **F77** `evals/visual/` — verificación visual multi-destino.
- **F78** `references/05-note-types/concept.md` — paraguas común; conceptos nuevos referencian notas concept.
- **F79** `references/05-note-types/api-reference.md` — capítulos que documentan APIs.
- **F80** `references/05-note-types/procedure.md` — capítulos que documentan procedimientos.
- **F81** `references/05-note-types/configuration.md` — capítulos que documentan configuración.
- **F83** `references/05-note-types/architecture.md` — capítulos que documentan arquitecturas.
- **F87** `references/05-note-types/comparison.md` — comparar 2 capítulos.
- **F88** `references/05-note-types/version-delta.md` — cambios entre versiones de un capítulo.

---

## §9 · Verificación al cierre de la fase

- `wc -l references/05-note-types/chapter-digest.md` ≤ 500 líneas.
- §2 con 4 subsecciones.
- §3 con tabla de componentes mínimos ≥ 14 filas + §3.1 tabla de Conceptos nuevos + §3.2 patrón de Continuidad.
- §4 con 5 subsecciones.
- §5 con tabla de campos del perfil y sus defaults.
- §6 con checklist de cierre ≥ 17 items.
- §7 con nota mínima viable (≥ 90 líneas).
- §8 con ≥ 19 wirings.
- §9 lista de verificación explícita.

**Criterios de aceptación del ROADMAP F86:**

1. _Declara continuidad en ambos sentidos._ → battery C2: `## Continuidad` tiene `### Hacia atrás` Y `### Hacia adelante` con enlaces.
2. _Todo concepto reutilizable tiene nota propia enlazada._ → battery C3: cada concepto en `## Conceptos nuevos` (o equivalente) tiene `[[note:id]]` o `[[term:nombre]]`.
3. _Leyendo solo los digests se reconstruye el argumento del libro._ → battery C4: cobertura de keywords del SDM en `## Resumen ejecutivo` + `## Puntos clave` ≥ 60%.
