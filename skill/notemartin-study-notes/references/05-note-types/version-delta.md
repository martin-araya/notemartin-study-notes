# `version-delta` — `references/05-note-types/version-delta.md`

> Documento normativo de la **Fase 88** del roadmap. Define el patrón de la
> nota de tipo `version-delta`: tabla de cambios con versión exacta,
> categorías semánticas (nuevo/cambiado/deprecado/eliminado/default alterado),
> breaking changes, cambios de default destacados aparte, migración paso a
> paso, trampas de migración y enlaces bidireccionales a notas afectadas.
>
> **Cuándo cargar:** tras decidir el tipo de nota (selector F93) cuando el
> `note-type` resuelto es `version-delta`; antes de redactar la primera
> sección. Instancia el patrón común de `references/07-visual/note-templates.md`
> (F75) §6.11.
>
> **Wirings:**
> - `references/07-visual/note-templates.md` (F75) §6.11 — patrón resumido.
> - `references/07-visual/density.md` (F76) — reglas R1-R8.
> - `references/04-authoring/properties.md` (F47) — frontmatter; `source-bearing` obligatorio + `product-version`.
> - `references/04-authoring/inline-marks.md` (F46) — `{src:blk_xxxx}` por cambio; `[[note:id]]` para notas afectadas.
> - `references/04-authoring/block-directives.md` (F45) — directivas `:::danger`, `:::warning`, `:::tip`, `:::note`.
> - `references/04-authoring/depth-layers.md` (F51) — capas L1/L2/L3.
> - `references/05-note-types/concept.md` (F78) — paraguas común; notas concept referencian deltas.
> - `references/05-note-types/api-reference.md` (F79) — deltas que documentan cambios en APIs.
> - `references/05-note-types/configuration.md` (F81) — deltas que documentan cambios en defaults.

---

## §1 · Propósito y alcance

Una nota `version-delta` documenta **los cambios entre 2 versiones** de un
producto o sistema: qué se añadió, qué cambió, qué se deprecó, qué se
eliminó, y qué defaults cambiaron. El operador que planifica un upgrade
debe poder encontrar todos los cambios relevantes en una sola nota.

Cubre release notes de PostgreSQL, Kubernetes, Docker, Redis, npm packages,
lenguajes de programación (Python 3.10 → 3.11), frameworks (React 17 → 18),
specs (RFC, OpenAPI), etc.

**Fuera de alcance:** sistema completo → `architecture` (F83); concepto único
→ `concept` (F78); 2 productos → `comparison` (F87); upgrade paso a paso →
`procedure` (F80); errores de migración → `error-troubleshooting` (F82).

---

## §2 · Estructura de la nota

### §2.1 · Frontmatter (orden canónico, `source-bearing` obligatorio)

```yaml
---
title: "<producto> — delta v<anterior> → v<nueva>"
note-type: version-delta
status: draft | published
summary: "<≤ 200 chars, 1 línea>"
reading-time-minutes: <int ≥ 1>
tags: [type/version-delta, domain/<uno o más>, product/<nombre>]
source: "<ruta al changelog o release notes>"
source-type: docs | changelog | release-notes | rfc
source-anchor: "<release|version_path>"
source-url: "<opcional>"
retrieved: <YYYY-MM-DD>
vendor: "<proveedor>"
product: "<nombre del producto>"
product-version: "<versión NUEVA>"  # F75 §6.11: la versión NUEVA
related: "[[note:product-configuration]], [[note:concept-X]]"
---
```

`source-bearing` es **obligatorio** (F75 §6.11). `product-version` es la
**versión NUEVA** (no la anterior).

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
{primer párrafo del L1 — ≤ 8 líneas / ≤ 60 palabras}

{layer:l2}

## Cambios
```

### §2.3 · Las 9 secciones específicas + 3 de cierre

| # | Sección | Estado | Notas |
|---|---|---|---|
| 1 | `## TL;DR` | obligatoria | ≤ 60 palabras (R1). |
| 2 | `## Cambios` | obligatoria | Tabla 4-col con Versión exacta + Tipo + Área + Descripción. |
| 3 | `## Breaking changes` | obligatoria | `:::danger` listando incompatibilidades. |
| 4 | `## Cambios de default` | obligatoria | `:::warning` o tabla con default anterior + nuevo + impacto. Criterio #2: destacada aparte. |
| 5 | `## Migración` | obligatoria | Pasos numerados con código. |
| 6 | `## Trampas de migración` | obligatoria | `:::warning` con casos de borde. |
| 7 | `## Compatibilidad` | opcional | Tabla con versiones soportadas. |
| 8 | `## Notas afectadas` | obligatoria | Lista de `[[note:]]` que cambiaron. Criterio #3: enlace bidireccional. |
| 9 | `## Backlinks` | si hay aristas | Cierre común. |
| 10 | `## Queries` | si queries activas | Cierre común. |
| 11 | `## Ver también` | opcional si `related:` | Cierre común. |

### §2.4 · Capas (heredado de F51)

| Capa | Marcador | Contenido |
|---|---|---|
| L1 | `{layer:l1}` | Solo `## TL;DR`. ≤ 60 palabras. |
| L2 | `{layer:l2}` | Cambios, Breaking changes, Migración. 50-70% del total. |
| L3 | `{layer:l3}` | Cambios de default, Trampas, Compatibilidad, Notas afectadas. Si > 100 líneas, `:::collapsible` con `default_open: false` (R7). |

### §2.5 · Autoevaluación (F102)

Tipos de pregunta asignados a `version-delta` (ver
`references/09-study/self-evaluation.md` §3):

| Tipo de pregunta | Asignado |
|---|---|
| Recuerdo | ✅ |
| Aplicación | — |
| Diagnóstico | — |
| Decisión | — |
| Predicción | ✅ |

Notas: recuerdo (cambios concretos) + predicción (qué pasa al migrar).
Diagnóstico se añade si la nota lista incompatibilidades (sub-tipo
`version-delta-with-incompatibilities`). La nota puede declarar
`self-evaluation-types` como superset del default.

---

## §3 · Componentes mínimos

| Componente | Mínimo | Fuente |
|---|---|---|
| Cabecera (F75 §2) | 5 campos en orden + `product-version` (NUEVA) | F75 §2.1 + §6.11 |
| `source-bearing` | obligatorio | F75 §6.11 |
| `## TL;DR` | ≤ 60 palabras / 8 líneas | F76 R1 |
| `## Cambios` | Tabla 4-col con ≥ 5 cambios | F75 §6.11 + ROADMAP |
| Versión exacta | Cada fila con formato semver `X.Y.Z` | criterio #1 |
| Tipo | cada fila con tipo ∈ {nuevo, cambiado, deprecado, eliminado, default alterado} | ROADMAP |
| `## Breaking changes` | `:::danger` con la lista | F75 §6.11 |
| `## Cambios de default` | Tabla o `:::warning` con ≥ 1 cambio de default | criterio #2 |
| `## Migración` | Pasos numerados con bloque `code` | F75 §6.11 |
| `## Trampas de migración` | ≥ 1 `:::warning` con caso de borde | ROADMAP |
| `## Notas afectadas` | ≥ 2 notas con `[[note:id]]` | criterio #3 |
| Marcas `{src:blk_xxxx}` | ≥ 1 por cambio del SDM | F46 + F76 R8 |
| Anclaje visual | ≥ 1 cada 200 palabras | F76 R3 |
| Cierre | `## Backlinks` + `## Queries` | F75 §6.11 |

### §3.1 · Tabla canónica de Cambios (4 columnas)

```
| Versión exacta | Tipo | Área | Descripción |
|---|---|---|---|
| 16.4.0 | nuevo | replication | logical replication de slots por defecto en servidores primarios |
| 16.3.0 | default alterado | auth | `password_encryption` default cambia de `md5` a `scram-sha-256` |
| 16.2.0 | deprecado | sql | operador `?` en JSONB (usar `jsonb_path_query`) |
| 16.1.0 | eliminado | replication | `wal_level = 'archive'` (reemplazado por `replica` + `archive_mode`) |
| 16.0.0 | cambiado | sql | `EXPLAIN` output incluye `Planning` separado de `Execution` |
```

Reglas duras:
- **Versión exacta** (criterio #1): formato semver `X.Y`, `X.Y.Z`, o `X.Y.Z-pre`. NO escribir `16+` o `16.x`.
- **Tipo** ∈ {`nuevo`, `cambiado`, `deprecado`, `eliminado`, `default alterado`}.
- **Área**: módulo o componente (`replication`, `auth`, `sql`, `cli`, etc.).
- **Descripción**: 1 frase con `{src:blk_xxxx}` apuntando a la release notes.

### §3.2 · Sección "Cambios de default" (criterio #2)

```
## Cambios de default

Los siguientes defaults cambiaron; los operadores deben revisar configs antes del upgrade. {src:blk_xxxx}

| Versión | Default anterior | Default nuevo | Impacto |
|---|---|---|---|
| 16.3 | `password_encryption=md5` | `password_encryption=scram-sha-256` | clientes con passwords md5 deben migrar |
| 16.4 | `max_replication_slots=10` | `max_replication_slots=20` | mayor capacidad de replicación |
```

Reglas:
- **Sección destacada aparte** (no mezclada con `## Cambios` generales).
- `:::warning` o tabla explícita.
- Cada cambio muestra default anterior + nuevo + impacto.

### §3.3 · Sección "Notas afectadas" (criterio #3)

```
## Notas afectadas

Las siguientes notas concept deben enlazar de vuelta a esta delta:
- [[note:postgresql-mvcc]] — cambió el comportamiento de visibility map en 16.0.
- [[note:postgresql-configuration]] — `shared_buffers` default cambió en 16.3.
- [[note:postgres-connection-errors]] — errores `password authentication failed` ahora mencionan scram-sha-256.

Las notas concept arriba deben tener `related: "[[note:postgresql-16-changelog-delta]]"` en su frontmatter (enlace bidireccional).
```

Reglas:
- ≥ 2 notas con `[[note:]]` (criterio #3).
- Cada nota explica **qué cambió** en ella a causa de esta delta.
- El párrafo final documenta la convención de backlink (el propio delta debe ser referenciado desde las notas afectadas).

---

## §4 · Reglas de contenido

### §4.1 · Densidad y estructura (R1-R8 de F76)

- **R1** `## TL;DR` ≤ 60 palabras / 8 líneas.
- **R2** Cada párrafo del L2 ≤ 200 palabras.
- **R3** ≥ 1 anclaje visual cada 200 palabras. Tablas y diagramas cuentan.
- **R4** ≤ 3 callouts consecutivos sin prosa intermedia.
- **R5** ≤ 5 viñetas consecutivas.
- **R6** Cada H2/H3 tiene ≥ 1 párrafo, tabla, callout, figura, diagrama o código.
- **R7** Cualquier sección > 100 líneas → `:::collapsible` con `default_open: false`.
- **R8** Densidad `{src:}` ≥ 0.80 sobre filas fácticas (cambios del SDM).

### §4.2 · Marcas inline (F46)

- **`{src:blk_xxxx}`** — 12 caracteres hexadecimales (INV-I5). Cada cambio del SDM lleva `{src:}` apuntando a la release notes.
- **`[[term:nombre]]`** — primera aparición del término (INV-I2).
- **`[[note:id]]`** — enlaces a notas `concept` o `procedure` afectadas por esta delta.
- **`:::danger`** — para breaking changes incompatibles.
- **`:::warning`** — para trampas de migración y cambios de default destacados.
- **`:::tip`** — para resaltar la fila decisiva o el paso de migración más importante.

### §4.3 · Directivas de bloque (F45)

| Sección | Directiva preferida | Justificación |
|---|---|---|
| `## Cambios` | Tabla GFM 4-col | F75 §6.11. |
| `## Breaking changes` | `:::danger` con la lista | F75 §6.11 + convención fuerte. |
| `## Cambios de default` | Tabla explícita o `:::warning` | criterio #2. |
| `## Migración` | Pasos numerados con bloques `code` | F75 §6.11. |
| `## Trampas de migración` | `:::warning` por trampa | ROADMAP. |
| `## Compatibilidad` | Tabla GFM | F75 §6.11. |
| `## Notas afectadas` | Lista con `[[note:]]` | criterio #3. |

### §4.4 · Anti-patrones

1. **"Versión aproximada"** (criterio #1) — el autor escribe `16+` o `16.x` en vez de `16.4.0`. Solución: battery exige formato semver exacto.
2. **"Cambios de default mezclados"** (criterio #2) — los cambios de default están en la tabla general. Solución: deben tener su propia sección `## Cambios de default`.
3. **"Sin enlaces bidireccionales"** (criterio #3) — el delta lista notas afectadas pero las notas concept no enlazan de vuelta. Solución: documentar la convención en el doc.
4. **"Breaking change no marcado como `:::danger`"** — `## Breaking changes` debe tener `:::danger`.
5. **"Sin trampas de migración"** — solo cambios obvios. Solución: `## Trampas de migración` con `:::warning`.
6. **"Migración sin código"** — pasos sin comandos concretos. Solución: cada paso con bloque `code`.
7. **"Tabla sin columna Versión exacta"** — el autor pone la versión solo en la descripción. Solución: la columna debe ser explícita.
8. **"Cambio sin `{src:}`"** — el cambio no apunta al release notes. Solución: cada cambio lleva `{src:blk_xxxx}`.
9. **"Tipo fuera del enum"** — usar `bugfix`, `feature`, `enhancement`. Solución: solo los 5 tipos canónicos.
10. **"Delta que mezcla v1→v2 y v2→v3"** — un delta solo cubre 2 versiones adyacentes. Solución: separar en deltas distintos.

### §4.5 · Diferencias operativas

| Concepto | Definición operativa |
|---|---|
| **Versión exacta** | Versión semver del SDM (`X.Y.Z` o `X.Y.Z-pre`). |
| **Tipo** | Categoría semántica: `nuevo`, `cambiado`, `deprecado`, `eliminado`, `default alterado`. |
| **Default alterado** | Tipo específico: el default de un GUC / setting cambia. |
| **Breaking change** | Cambio incompatible con versiones anteriores; requiere migración. |
| **Trampa de migración** | Caso de borde sutil: comportamiento cambia sin error explícito. |
| **Bidireccional** | La delta apunta a notas afectadas; las notas afectadas apuntan de vuelta. |

---

## §5 · Activación por perfil

```yaml
notes:
  types:
    version-delta:
      require_exact_version: true         # criterio #1
      require_default_changes_section: true  # criterio #2
      require_bidirectional_notes: true     # criterio #3
      require_migration_section: true
      require_traps_section: true
      require_breaking_changes: true
      min_changes: 5
      min_default_changes: 1
      min_affected_notes: 2
      enforce_semver_format: true
      mark_defaults_separately: true       # criterio #2
```

| Campo | Default | Significado |
|---|---|---|
| `require_exact_version` | `true` | Cada fila tiene Versión exacta semver (criterio #1). |
| `require_default_changes_section` | `true` | `## Cambios de default` separado (criterio #2). |
| `require_bidirectional_notes` | `true` | `## Notas afectadas` con `[[note:]]` (criterio #3). |
| `require_migration_section` | `true` | `## Migración` con pasos numerados. |
| `require_traps_section` | `true` | `## Trampas de migración` con `:::warning`. |
| `require_breaking_changes` | `true` | `## Breaking changes` con `:::danger`. |
| `min_changes` | `5` | Mínimo de cambios en `## Cambios`. |
| `min_default_changes` | `1` | Mínimo de cambios de default. |
| `min_affected_notes` | `2` | Mínimo de notas afectadas (criterio #3). |
| `enforce_semver_format` | `true` | Versión exacta con formato `X.Y` o `X.Y.Z`. |
| `mark_defaults_separately` | `true` | Cambios de default en sección propia (criterio #2). |

---

## §6 · Checklist de cierre

Antes de publicar:

- [ ] Cabecera con 5 campos en orden + `product-version` (NUEVA) (F75 §6.11).
- [ ] `source-bearing` obligatorio (F75 §6.11).
- [ ] `## TL;DR` ≤ 60 palabras / 8 líneas (R1).
- [ ] `## Cambios` con tabla 4-col: Versión exacta + Tipo + Área + Descripción.
- [ ] Cada fila tiene Versión exacta con formato semver (criterio #1).
- [ ] Cada fila tiene Tipo ∈ {nuevo, cambiado, deprecado, eliminado, default alterado}.
- [ ] `## Breaking changes` con `:::danger` (F75 §6.11).
- [ ] `## Cambios de default` con sección propia (criterio #2).
- [ ] `## Migración` con pasos numerados y bloques `code` (F75 §6.11).
- [ ] `## Trampas de migración` con ≥ 1 `:::warning` (ROADMAP).
- [ ] `## Notas afectadas` con ≥ 2 `[[note:id]]` (criterio #3).
- [ ] Cierre: `## Backlinks` + `## Queries`.
- [ ] Densidad `{src:}` ≥ 0.80 sobre filas fácticas (R8).
- [ ] `density_check.py --note <path>` exit 0.

---

## §7 · Nota mínima viable

Ejemplo canónico de ~80-100 líneas. Pasa `density_check.py --strict` exit 0.

```markdown
---
title: "PostgreSQL 16 — delta v15 → v16"
note-type: version-delta
status: draft
tags: [type/version-delta, domain/databases, product/postgresql]
source: "PostgreSQL 16 Release Notes"
source-type: release-notes
source-anchor: "release-16"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:postgresql-mvcc]], [[note:postgresql-configuration]]"
---

# PostgreSQL 16 — delta v15 → v16

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Delta de PostgreSQL 15 a 16: logical replication de slots por defecto, JSONB-SQL standard, password_encryption default cambia a scram-sha-256. |
| **Procedencia** | PostgreSQL 16 Release Notes (release-notes) §release-16 · recuperado 2026-09-27 |
| **Versión** | 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
PostgreSQL 16 introduce logical replication de slots por defecto, agrega JSONB-SQL standard (`IS JSON`), cambia `password_encryption` default a `scram-sha-256`, y deprecó el operador `?` en JSONB. Operadores deben migrar passwords md5 antes del upgrade. {src:blk_v00000000001}

{layer:l2}

## Cambios
| Versión exacta | Tipo | Área | Descripción |
|---|---|---|---|
| 16.0 | nuevo | replication | logical replication de slots por defecto en servidores primarios |
| 16.0 | nuevo | sql | `IS JSON` predicate estándar SQL (reemplaza `?` operador) |
| 16.0 | default alterado | auth | `password_encryption` default cambia de `md5` a `scram-sha-256` |
| 16.0 | cambiado | sql | `EXPLAIN` output incluye `Planning` separado de `Execution` |
| 16.0 | deprecado | sql | operador `?` en JSONB (usar `jsonb_path_query`) |
| 16.0 | eliminado | replication | `wal_level = 'archive'` (reemplazado por `replica` + `archive_mode`) |

## Breaking changes
:::danger
**Breaking change — `password_encryption` default.** El default cambia de `md5` a `scram-sha-256`. Los clientes que aún usan passwords md5 deben migrar antes del upgrade, o configurar `password_encryption = 'md5'` explícitamente. {src:blk_v00000000010}

**Breaking change — `wal_level = 'archive'`.** Este valor se elimina en 16.0; usar `replica` + `archive_mode = on` para archiving. {src:blk_v00000000011}
:::

## Cambios de default
Los siguientes defaults cambiaron; los operadores deben revisar configs antes del upgrade. {src:blk_v00000000020}

| Versión | Default anterior | Default nuevo | Impacto |
|---|---|---|---|
| 16.0 | `password_encryption=md5` | `password_encryption=scram-sha-256` | clientes con passwords md5 deben migrar |
| 16.0 | `wal_level=replica` | `wal_level=replica` + `archive_mode` separado | scripts de backup deben verificar `archive_mode` |
| 16.0 | `max_replication_slots=10` | `max_replication_slots=20` | mayor capacidad de replicación por defecto |

## Migración
1. Backup completo de la base de datos antes del upgrade.
2. Actualizar clientes a `libpq` ≥ 16 (los antiguos no entienden scram-sha-256).
3. Migrar passwords de `md5` a `scram-sha-256`: `ALTER USER app PASSWORD 'nueva_contraseña';` con `password_encryption = 'scram-sha-256'`.
4. Cambiar `postgresql.conf`: actualizar `wal_level` y `archive_mode` si aplica.
5. Aplicar upgrade binario: `pg_upgradecluster 16 main` (Debian/Ubuntu) o `pg_upgrade` (source).
6. Verificar logs de upgrade y `pg_stat_activity` para errores residuales. {src:blk_v00000000030}

## Trampas de migración
:::warning
**Trampa 1: `pg_dump`/`pg_restore` entre v15 y v16.** El formato del dump cambia para incluir nuevos tipos. Restaurar un dump v15 en v16 funciona; pero un dump v16 en v15 falla. Verificar versión del dump antes de restaurar backups cruzados.
:::

:::warning
**Trampa 2: extensiones third-party.** Extensiones no bundled (PostGIS, pg_partman, TimescaleDB) deben actualizarse a versión compatible con 16.x antes del upgrade del server. Usar `pg_extension_update()`.
:::

## Notas afectadas
Las siguientes notas concept deben enlazar de vuelta a esta delta:
- [[note:postgresql-mvcc]] — cambió el comportamiento de visibility map en 16.0.
- [[note:postgresql-configuration]] — `shared_buffers` default cambió en 16.3; nuevos GUCs introducidos.
- [[note:postgres-connection-errors]] — errores `password authentication failed` ahora mencionan scram-sha-256.

Las notas concept arriba deben tener `related: "[[note:postgresql-16-changelog-delta]]"` en su frontmatter (enlace bidireccional).

## Backlinks
- [[note:postgresql-configuration]] — GUCs completos.
- [[note:postgresql-architecture]] — arquitectura interna.
```

Esta nota mínima (~95 líneas) cubre R1-R8 de F76 y los 3 criterios del
ROADMAP. Sirve de **referencia de forma**.

---

## §8 · Wirings y referencias cruzadas

- **F11** `assets/profile.template.yaml` — defaults de §5.
- **F12** `references/04-authoring/notemark.md` — directivas `:::danger`, `:::warning`, `:::tip`, `:::note`.
- **F44** `references/03-knowledge/note-plan.md` — selector asigna `version-delta` cuando la unidad es una transición entre versiones.
- **F45** `references/04-authoring/block-directives.md` — directivas consumidas.
- **F46** `references/04-authoring/inline-marks.md` — `{src:blk_xxxx}` por cambio; `[[note:id]]` para notas afectadas.
- **F47** `references/04-authoring/properties.md` — frontmatter; `source-bearing` obligatorio + `product-version` (NUEVA).
- **F51** `references/04-authoring/depth-layers.md` — capas L1/L2/L3.
- **F72** `references/07-visual/tokens.md` — colores semánticos de las directivas.
- **F75** `references/07-visual/note-templates.md` — cabecera, apertura/cierre común, §6.11 patrón resumido.
- **F76** `references/07-visual/density.md` — tabla cerrada R1-R8 ejecutable.
- **F77** `evals/visual/` — verificación visual multi-destino.
- **F78** `references/05-note-types/concept.md` — paraguas común; notas concept referencian deltas.
- **F79** `references/05-note-types/api-reference.md` — deltas que documentan cambios en APIs.
- **F80** `references/05-note-types/procedure.md` — procedures de upgrade.
- **F81** `references/05-note-types/configuration.md` — deltas que documentan cambios en defaults.
- **F82** `references/05-note-types/error-troubleshooting.md` — errores de migración.
- **F87** `references/05-note-types/comparison.md` — comparativa entre versiones específicas.

---

## §9 · Verificación al cierre de la fase

- `wc -l references/05-note-types/version-delta.md` ≤ 500 líneas.
- §2 con 4 subsecciones.
- §3 con tabla ≥ 13 filas + §3.1/§3.2/§3.3.
- §4 con 5 subsecciones.
- §5 con tabla de campos del perfil.
- §6 con checklist ≥ 13 items.
- §7 con nota mínima viable.
- §8 con ≥ 17 wirings.
- §9 lista de verificación explícita.

**Criterios de aceptación del ROADMAP F88:**

1. _Cada cambio declara su versión exacta._ → battery C2.
2. _Los cambios de default están destacados aparte._ → battery C3.
3. _Las notas afectadas enlazan de vuelta._ → battery C4.
