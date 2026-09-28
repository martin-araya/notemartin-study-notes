# `cheatsheet` — `references/05-note-types/cheatsheet.md`

> Documento normativo de la **Fase 90** del roadmap. Define el patrón de la
> nota de tipo `cheatsheet`: denso, sin prosa, derivado exclusivamente de
> notas completas, cada entrada enlaza a su nota, una o dos pantallas.
> **Exenta de la frecuencia mínima de callouts (F75 §6.13)**: la tabla es
> el contenido principal.
>
> **Cuándo cargar:** tras decidir el tipo de nota (selector F93) cuando el
> `note-type` resuelto es `cheatsheet`; antes de redactar la primera
> sección. Instancia el patrón común de `references/07-visual/note-templates.md`
> (F75) §6.13.
>
> **Wirings:**
> - `references/07-visual/note-templates.md` (F75) §6.13 — patrón resumido.
> - `references/07-visual/density.md` (F76) — reglas R1-R8.
> - `references/04-authoring/properties.md` (F47) — frontmatter; `source-bearing` recomendado.
> - `references/04-authoring/inline-marks.md` (F46) — `[[note:id]]` por entrada; `[[term:X]]` por sigla.
> - `references/04-authoring/block-directives.md` (F45) — directivas `:::warning` para errores; `:::tip` para atajos.
> - `references/04-authoring/depth-layers.md` (F51) — capas L1/L2/L3.
> - `references/05-note-types/concept.md` (F78) — paraguas común; cheatsheet deriva de notas concept.
> - `references/05-note-types/api-reference.md` (F79) — cheatsheet deriva de API references.
> - `references/05-note-types/procedure.md` (F80) — cheatsheet deriva de procedures.
> - `references/05-note-types/glossary-term.md` (F89) — cheatsheet usa `[[term:X]]` para términos.

---

## §1 · Propósito y alcance

Una nota `cheatsheet` documenta **una referencia rápida de comandos, atajos
y errores comunes** de un sistema o dominio, optimizada para consulta
frecuente (1-2 pantallas). Cada entrada es **un puntero a una nota completa**
que la desarrolla — el cheatsheet nunca contiene afirmaciones espontáneas.

`cheatsheet` cubre: comandos CLI (psql, docker, git, kubectl, redis-cli),
atajos (psql `\dt`, vim, bash), errores frecuentes con códigos y soluciones,
flags y opciones de uso común.

**Fuera de alcance:**

- API o endpoint → `api-reference` (F79).
- Procedure paso a paso → `procedure` (F80).
- Concepto único aislado → `concept` (F78).
- Tabla completa de términos → `glossary-term` (F89).
- Mapa de notas → `index-moc` (F91).

---

## §2 · Estructura de la nota

### §2.1 · Frontmatter (orden canónico, `source-bearing` recomendado)

```yaml
---
title: "<sistema> cheatsheet"
note-type: cheatsheet
status: draft | published
summary: "<≤ 200 chars, 1 línea>"
reading-time-minutes: <int ≥ 1>
tags: [type/cheatsheet, domain/<uno o más>, product/<nombre>]
source: "<ruta al manual; opcional>"
source-type: docs | man | wiki | spec
source-anchor: "<page|chapter|section_path>"
source-url: "<opcional>"
retrieved: <YYYY-MM-DD>
vendor: "<proveedor>"
product: "<nombre del producto>"
product-version: "<versión>"
related: "[[note:procedure-de-instalacion]], [[note:concept-del-dominio]]"
---
```

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
{1 frase declarando el dominio del cheatsheet; ≤ 30 palabras}

{layer:l1}

## Comandos
```

### §2.3 · Las 5 secciones específicas + 2 de cierre

| # | Sección | Estado | Notas |
|---|---|---|---|
| 1 | `## TL;DR` | obligatoria | 1 frase declarando el dominio (≤ 30 palabras). |
| 2 | `## Comandos` | obligatoria | Tabla 3-col con 10-30 filas. Cada fila con `[[note:id]]` o `[[term:X]]` (criterio #2). |
| 3 | `## Atajos` | obligatoria si aplica | Tabla 2-col con ≥ 5 filas (F75 §6.13). |
| 4 | `## Errores comunes` | opcional | `:::warning` por código típico. |
| 5 | `## Backlinks` | si hay aristas | Cierre común. |
| 6 | `## Queries` | si queries activas | Cierre común. |

### §2.4 · Capas (F75 §6.13: la nota es típicamente L1)

| Capa | Marcador | Contenido |
|---|---|---|
| L1 | `{layer:l1}` | Toda la nota. El cheatsheet es denso y no requiere separación L1/L2/L3. |

---

## §3 · Componentes mínimos

| Componente | Mínimo | Fuente |
|---|---|---|
| Cabecera (F75 §2) | 5 campos en orden | F75 §2.1 |
| `source-bearing` | recomendado | F75 §6.13 |
| `## TL;DR` | 1 frase ≤ 30 palabras | ROADMAP (denso, sin prosa) |
| `## Comandos` | Tabla 3-col con 10-30 filas | F75 §6.13 |
| `[[note:id]]` o `[[term:X]]` | cada fila con ≥ 1 enlace | criterio #2 |
| `## Atajos` | si aplica: tabla 2-col con ≥ 5 filas | F75 §6.13 |
| `## Errores comunes` | opcional: `:::warning` por código | F75 §6.13 |
| **Sin párrafos de prosa** | la nota es 100% tablas + callouts | criterio #3 |
| Densidad `{src:}` | no requerida (cheatsheet derivado) | F75 §6.13 |

### §3.1 · Tabla canónica de Comandos (3 columnas)

```
| Comando | Descripción | Ejemplo |
|---|---|---|
| `psql -h localhost -U postgres db` | Conectar a una BD con usuario específico | ver [[note:postgres-connection-errors]] |
| `pg_dump -Fc -f backup.dump db` | Backup lógico en formato custom | ver [[note:procedure-postgres-backup]] |
| `VACUUM ANALYZE;` | Liberar tuplas muertas y actualizar estadísticas | ver [[note:postgresql-mvcc]] |
| `\dt+` | Listar todas las tablas con tamaño | ver [[note:glossary-term-table]] |
| `\di+` | Listar índices con tamaño | ver [[note:glossary-term-index]] |
```

Reglas:
- **10-30 filas** por tabla principal (F75 §6.13).
- Cada fila con `[[note:id]]` o `[[term:X]]` apuntando a la nota que la desarrolla (criterio #2).
- Sin párrafos de prosa (criterio #3): la tabla es el contenido.
- 1 fila = 1 comando o atajo; nada se mezcla.

### §3.2 · Tabla canónica de Atajos (2 columnas)

```
| Atajo | Significado |
|---|---|
| `\dt` | Listar tablas |
| `\dn` | Listar schemas |
| `\du` | Listar usuarios |
| `\dv` | Listar vistas |
| `\dx` | Listar extensiones |
```

Reglas:
- ≥ 5 filas si la sección está presente (F75 §6.13).
- Formato corto: atajo a la izquierda, significado a la derecha.
- Sin explicaciones largas.

### §3.3 · Patrón de Errores comunes

```
## Errores comunes

:::warning
**`FATAL: too many connections for role "app"`** — excede `max_connections`. Solución: desplegar pgbouncer o reducir pool. Ver [[note:postgres-connection-errors]].
:::

:::warning
**`ERROR: duplicate key value violates unique constraint`** — INSERT conflict. Solución: usar `ON CONFLICT DO NOTHING` o `UPSERT`. Ver [[note:error-troubleshooting-constraints]].
:::
```

Reglas:
- ≥ 1 `:::warning` por código de error típico.
- Cada `:::warning` con `[[note:id]]` apuntando a la nota de troubleshooting.
- Sin prosa entre callouts.

---

## §4 · Reglas de contenido

### §4.1 · Densidad y estructura (R1-R8 de F76)

- **R1** `## TL;DR` ≤ 30 palabras.
- **R2-R5** aplican con brevedad (cheatsheet es denso).
- **R6** Cada H2/H3 tiene ≥ 1 tabla o callout.
- **R7** Si la nota es > 2 pantallas (~80 líneas), partir en 2 cheatsheets.
- **R8** Densidad `{src:}` no requerida (F75 §6.13 exenta).
- **Anti-patrón F75 §6.13**: la frecuencia mínima de callouts no aplica — la tabla es el contenido principal.

### §4.2 · Marcas inline (F46)

- **`{src:blk_xxxx}`** — 12 caracteres hexadecimales (INV-I5). Opcional en cheatsheet (puede derivarse de notas que sí lo tienen).
- **`[[note:id]]`** — cada entrada enlaza a la nota que la desarrolla (criterio #2).
- **`[[term:X]]`** — para términos que tienen nota glossary-term (e.g., `[[term:MVCC]]`).
- **`:::warning`** — para errores comunes.
- **`:::tip`** — para atajos destacados.

### §4.3 · Directivas de bloque (F45)

| Sección | Directiva preferida | Justificación |
|---|---|---|
| `## Comandos` | Tabla GFM 3-col | F75 §6.13 (contenido principal). |
| `## Atajos` | Tabla GFM 2-col | F75 §6.13. |
| `## Errores comunes` | `:::warning` por error | F75 §6.13 (opcional). |

### §4.4 · Anti-patrones

1. **"Párrafos de prosa"** (criterio #3) — el autor escribe prosa narrativa entre tablas. Solución: la nota es 100% tablas + callouts; 0 párrafos > 50 palabras.
2. **"Filas sin respaldo"** (criterio #1) — una fila tiene información que no está en ninguna nota del corpus. Solución: cada fila tiene `[[note:id]]` o `[[term:X]]`.
3. **"Filas sin enlace"** (criterio #2) — una fila no tiene `[[note:id]]` o `[[term:X]]`. Solución: battery C2 cuenta enlaces por fila.
4. **"Tabla con < 10 filas"** — F75 §6.13 dice 10-30 filas. Solución: battery C3 exige ≥ 10.
5. **"Tabla con > 30 filas"** — ilegible; debe partirse en 2 cheatsheets.
6. **"Mezcla de dominios"** — un cheatsheet mezcla PostgreSQL + Docker. Solución: un cheatsheet por dominio.
7. **"Sin secciones obligatorias"** — el cheatsheet no tiene `## Comandos`. Solución: battery C1 lo rechaza.
8. **"Sección solo de viñetas"** (R6) — bullets sin contexto. Solución: usar tabla 2-col o 3-col.
9. **"Backlinks genéricos"** — apuntar a `[[note:postgres-cheatsheet-backref]]` en vez de la nota específica que desarrolla el comando. Solución: cada fila apunta a la nota que la desarrolla.

### §4.5 · Diferencias operativas

| Concepto | Definición operativa |
|---|---|
| **Comando** | Llamada CLI que ejecuta una acción; una fila = un comando. |
| **Atajo** | Forma corta que invoca el mismo comando (ej: `\dt` en psql = `SELECT * FROM pg_tables`). |
| **Error común** | Código de error típico con solución documentada en otra nota. |
| **Backlink nota-específica** | Cada entrada apunta a la nota que desarrolla el comando, no a una nota genérica. |
| **Densidad** | Tablas con muchas filas + poco espacio entre ellas (1-2 pantallas). |

---

## §5 · Activación por perfil

```yaml
notes:
  types:
    cheatsheet:
      require_source_anchor: false       # default: false (puede ser derivado)
      require_comandos_table: true        # default: true
      require_atajos_section: true        # default: true (F75 §6.13 si aplica)
      require_backlinks_per_row: true     # default: true (criterio #2)
      require_no_prose: true              # default: true (criterio #3)
      min_comandos_rows: 10               # default: 10 (F75 §6.13)
      max_comandos_rows: 30               # default: 30 (F75 §6.13)
      min_atajos_rows: 5                  # default: 5
      max_total_lines: 80                 # default: 80 (≤ 2 pantallas)
      enforce_all_entries_have_note: true  # default: true (criterio #1)
      exempt_from_callout_minimum: true   # F75 §6.13
```

| Campo | Default | Significado |
|---|---|---|
| `require_source_anchor` | `false` | `source-bearing` recomendado pero opcional. |
| `require_comandos_table` | `true` | `## Comandos` obligatorio (F75 §6.13). |
| `require_atajos_section` | `true` | `## Atajos` obligatorio si aplica al dominio (F75 §6.13). |
| `require_backlinks_per_row` | `true` | Cada fila tiene `[[note:id]]` o `[[term:X]]` (criterio #2). |
| `require_no_prose` | `true` | Sin párrafos narrativos > 50 palabras (criterio #3). |
| `min_comandos_rows` | `10` | Mínimo de filas en `## Comandos` (F75 §6.13). |
| `max_comandos_rows` | `30` | Máximo de filas (F75 §6.13). |
| `min_atajos_rows` | `5` | Mínimo de filas en `## Atajos`. |
| `max_total_lines` | `80` | Máximo total (≤ 2 pantallas). |
| `enforce_all_entries_have_note` | `true` | Cada fila tiene nota de respaldo (criterio #1). |
| `exempt_from_callout_minimum` | `true` | F75 §6.13 — la tabla es el contenido principal. |

---

## §6 · Checklist de cierre

Antes de publicar:

- [ ] Cabecera con 5 campos en orden (F75 §2.1).
- [ ] `source-bearing` recomendado (F75 §6.13).
- [ ] `## TL;DR` con 1 frase ≤ 30 palabras (criterio #3).
- [ ] `## Comandos` con tabla 3-col; ≥ 10 filas; ≤ 30 filas (F75 §6.13).
- [ ] Cada fila de `## Comandos` tiene `[[note:id]]` o `[[term:X]]` (criterio #2).
- [ ] `## Atajos` con tabla 2-col ≥ 5 filas si aplica al dominio (F75 §6.13).
- [ ] `## Errores comunes` con `:::warning` por código (opcional).
- [ ] **Sin párrafos de prosa > 50 palabras** (criterio #3).
- [ ] **≤ 80 líneas totales** (≤ 2 pantallas).
- [ ] Cierre: `## Backlinks` + `## Queries`.
- [ ] `density_check.py --note <path>` exit 0.

---

## §7 · Nota mínima viable

Ejemplo canónico de ~50-80 líneas. Pasa `density_check.py --strict` exit 0.

```markdown
---
title: "PostgreSQL 16 cheatsheet"
note-type: cheatsheet
status: draft
tags: [type/cheatsheet, domain/databases, product/postgresql]
source: "PostgreSQL 16 docs"
source-type: docs
source-anchor: "cheatsheet"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:postgresql-mvcc]], [[note:postgres-connection-errors]]"
---

# PostgreSQL 16 cheatsheet

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Cheatsheet de PostgreSQL 16: comandos CLI, atajos psql, errores frecuentes. |
| **Procedencia** | PostgreSQL 16 docs (docs) §cheatsheet · recuperado 2026-09-27 |
| **Versión** | 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 5 min |

## TL;DR
Comandos CLI de PostgreSQL 16, atajos psql (`\dt`, `\dn`, `\du`), y errores frecuentes con enlaces a notas detalladas.

{layer:l1}

## Comandos
| Comando | Descripción | Ver |
|---|---|---|
| `psql -h localhost -U postgres db` | Conectar a una BD | [[note:postgres-connection-errors]] |
| `pg_dump -Fc -f backup.dump db` | Backup lógico | [[note:procedure-postgres-backup]] |
| `pg_restore -d db backup.dump` | Restore lógico | [[note:procedure-postgres-backup]] |
| `VACUUM ANALYZE;` | Liberar tuplas y actualizar stats | [[note:postgresql-mvcc]] |
| `EXPLAIN ANALYZE SELECT ...;` | Ver plan de query | [[note:postgresql-configuration]] |
| `createdb dbname` | Crear BD | [[note:data-model]] |
| `dropdb dbname` | Eliminar BD | [[note:data-model]] |
| `\dt+` | Listar tablas con tamaño | [[note:glossary-term-table]] |
| `\di+` | Listar índices con tamaño | [[note:glossary-term-index]] |
| `\du` | Listar usuarios | [[note:glossary-term-role]] |
| `SELECT pg_size_pretty(pg_database_size('db'));` | Tamaño de una BD | [[note:postgresql-configuration]] |

## Atajos
| Atajo | Significado |
|---|---|
| `\dt` | Listar tablas |
| `\dn` | Listar schemas |
| `\dv` | Listar vistas |
| `\dx` | Listar extensiones |
| `\d+ tabla` | Describir tabla con detalles |
| `\df` | Listar funciones |

## Errores comunes

:::warning
**`FATAL: too many connections for role "app"`** — excede `max_connections`. Solución: pgbouncer o reducir pool. Ver [[note:postgres-connection-errors]].
:::

:::warning
**`ERROR: duplicate key value violates unique constraint`** — INSERT conflict. Solución: usar `ON CONFLICT DO NOTHING`. Ver [[note:error-troubleshooting-constraints]].
:::

## Backlinks
- [[note:postgresql-mvcc]]
- [[note:postgres-connection-errors]]

## Queries
```dataview
LIST
FROM "notes"
WHERE contains(tags, "type/cheatsheet")
```
```

Esta nota mínima (~70 líneas) cubre R1-R8 de F76 + F75 §6.13 exención de callouts + los 3 criterios del ROADMAP. Sirve de **referencia de forma**.

---

## §8 · Wirings y referencias cruzadas

- **F11** `assets/profile.template.yaml` — defaults de §5.
- **F12** `references/04-authoring/notemark.md` — directivas `:::warning`, `:::tip`.
- **F44** `references/03-knowledge/note-plan.md` — selector asigna `cheatsheet` cuando la unidad es una referencia rápida de comandos.
- **F45** `references/04-authoring/block-directives.md` — directivas consumidas.
- **F46** `references/04-authoring/inline-marks.md` — `[[note:id]]` por entrada (criterio #2); `[[term:X]]` por sigla.
- **F47** `references/04-authoring/properties.md` — frontmatter; `source-bearing` recomendado.
- **F51** `references/04-authoring/depth-layers.md` — capas L1/L2/L3; cheatsheet típicamente L1.
- **F72** `references/07-visual/tokens.md` — colores semánticos de las directivas.
- **F75** `references/07-visual/note-templates.md` — cabecera, apertura/cierre común, §6.13 patrón resumido.
- **F76** `references/07-visual/density.md` — tabla cerrada R1-R8 ejecutable.
- **F77** `evals/visual/` — verificación visual multi-destino.
- **F78** `references/05-note-types/concept.md` — paraguas común; cheatsheet deriva de notas concept.
- **F79** `references/05-note-types/api-reference.md` — cheatsheet deriva de API references.
- **F80** `references/05-note-types/procedure.md` — cheatsheet deriva de procedures.
- **F82** `references/05-note-types/error-troubleshooting.md` — `[[note:]]` apunta a notas de troubleshooting.
- **F89** `references/05-note-types/glossary-term.md` — `[[term:X]]` apunta a notas de términos.

---

## §9 · Verificación al cierre de la fase

- `wc -l references/05-note-types/cheatsheet.md` ≤ 400 líneas.
- §2 con 4 subsecciones.
- §3 con tabla de componentes mínimos ≥ 9 filas + §3.1 tabla 3-col + §3.2 tabla 2-col + §3.3 patrón de Errores comunes.
- §4 con 5 subsecciones.
- §5 con tabla de campos del perfil y sus defaults.
- §6 con checklist de cierre ≥ 11 items.
- §7 con nota mínima viable (≤ 80 líneas).
- §8 con ≥ 16 wirings.
- §9 lista de verificación explícita.

**Criterios de aceptación del ROADMAP F90:**

1. _Ninguna afirmación está ausente de las notas completas._ → battery C2: cada fila tiene `[[note:id]]` o `[[term:X]]` apuntando a una nota del corpus.
2. _Cada entrada enlaza a la nota que la desarrolla._ → battery C3: cada fila tiene ≥ 1 enlace a una nota (cuenta los `[[note:]]`/`[[term:]]` por fila).
3. _No contiene párrafos de prosa._ → battery C4: el cuerpo de la nota no tiene secciones con párrafos narrativos > 50 palabras; predominan tablas y callouts.
