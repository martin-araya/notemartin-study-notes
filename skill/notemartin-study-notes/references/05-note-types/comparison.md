# `comparison` — `references/05-note-types/comparison.md`

> Documento normativo de la **Fase 87** del roadmap. Define el patrón de la
> nota de tipo `comparison`: tabla principal con fila decisiva al final,
> párrafo obligatorio de síntesis tras cada tabla, matriz de decisión por
> escenario, tabla de trade-offs y veredicto final.
>
> **Cuándo cargar:** tras decidir el tipo de nota (selector F93) cuando el
> `note-type` resuelto es `comparison`; antes de redactar la primera sección.
> Instancia el patrón común de `references/07-visual/note-templates.md`
> (F75) §6.10.
>
> **Wirings:**
> - `references/07-visual/note-templates.md` (F75) §6.10 — patrón resumido.
> - `references/07-visual/density.md` (F76) — reglas R1-R8.
> - `references/04-authoring/properties.md` (F47) — frontmatter; `source-bearing` recomendado.
> - `references/04-authoring/inline-marks.md` (F46) — `{src:blk_xxxx}` por dato; `[[note:id]]` para referencias.
> - `references/04-authoring/block-directives.md` (F45) — directivas `:::derived`, `:::external`, `:::tip`, `:::example`, `:::warning`.
> - `references/04-authoring/depth-layers.md` (F51) — capas L1/L2/L3.
> - `references/05-note-types/concept.md` (F78) — paraguas común.
> - `references/05-note-types/api-reference.md` (F79) — comparisons que incluyen APIs.
> - `references/05-note-types/architecture.md` (F83) — comparisons entre arquitecturas.

---

## §1 · Propósito y alcance

Una nota `comparison` documenta **una comparación entre 2-5 alternativas** que
comparten un dominio y casos de uso, ayudando al lector a elegir entre
ellas basándose en criterios explícitos y veredictos derivados de la
documentación oficial (no de opinión del autor).

`comparison` cubre: productos (PostgreSQL vs MySQL), herramientas (kubectl vs
docker CLI), protocolos (REST vs gRPC), frameworks (React vs Vue), formatos
(JSON vs YAML), y opciones arquitectónicas (monolito vs microservicios).

**Fuera de alcance:**

- Tutorial de cómo usar una sola opción → `procedure` (F80).
- Documentar la sintaxis de cada opción → `syntax` (F84).
- Documentar un error específico → `error-troubleshooting` (F82).
- Concepto único aislado → `concept` (F78).
- Cambios entre versiones de un producto → `version-delta` (F88).

---

## §2 · Estructura de la nota

### §2.1 · Frontmatter (orden canónico, `source-bearing` recomendado)

```yaml
---
title: "<Opción A> vs <Opción B> (vs <Opción C> opcional)"
note-type: comparison
status: draft | published
summary: "<≤ 200 chars, 1 línea>"
reading-time-minutes: <int ≥ 1>
tags: [type/comparison, domain/<uno o más>]
source: "<ruta al doc o estudio>"
source-type: docs | rfc | paper | article
source-anchor: "<page|chapter|section_path>"
source-url: "<opcional>"
retrieved: <YYYY-MM-DD>
vendor: "<proveedor(es)>"
product: "<nombre(s)>"
product-version: "<versión(es)>"
related: "[[note:concept-del-dominio]], [[note:api-reference-de-opciones]]"
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
{primer párrafo del L1 — ≤ 8 líneas / ≤ 60 palabras}

{layer:l2}

## Comparativa
```

### §2.3 · Las 9 secciones específicas + 2 opcionales + 3 de cierre

| # | Sección | Estado | Notas |
|---|---|---|---|
| 1 | `## TL;DR` | obligatoria | ≤ 60 palabras (R1). |
| 2 | `## Comparativa` | obligatoria | Tabla principal con `:::tip` en la fila decisiva. |
| 3 | `## Síntesis` | obligatoria | Párrafo obligatorio después de la tabla. Criterio #1. |
| 4 | `## Criterios` | obligatoria | Lista con bullets explicando cada criterio. |
| 5 | `## Matriz de decisión por escenario` | obligatoria | Tabla `Escenario / Mejor opción / Justificación`. ≥ 3 escenarios. |
| 6 | `## Trade-offs` | obligatoria | Tabla `Trade-off / Opción A / Opción B`. ≥ 3 filas. |
| 7 | `## Casos de uso` | opcional | Sub-secciones por opción. |
| 8 | `## Veredicto` | obligatoria | 1-2 párrafos con la recomendación final. |
| 9 | `## Backlinks` | si hay aristas | Cierre común. |
| 10 | `## Queries` | si queries activas | Cierre común. |
| 11 | `## Ver también` | opcional si `related:` | Cierre común. |

### §2.4 · Capas (heredado de F51)

| Capa | Marcador | Contenido |
|---|---|---|
| L1 | `{layer:l1}` | Solo `## TL;DR`. ≤ 60 palabras. |
| L2 | `{layer:l2}` | Comparativa, Síntesis, Criterios, Matriz, Trade-offs, Veredicto. 70-90% del total. |
| L3 | `{layer:l3}` | Casos de uso (opcional). Si > 100 líneas, `:::collapsible` con `default_open: false` (R7). |

---

## §3 · Componentes mínimos

| Componente | Mínimo | Fuente |
|---|---|---|
| Cabecera (F75 §2) | 5 campos en orden | F75 §2.1 |
| `## TL;DR` | ≤ 60 palabras / 8 líneas | F76 R1 |
| `## Comparativa` | Tabla con criterios en filas, opciones en columnas; ≥ 4 criterios | F75 §6.10 |
| Fila decisiva | Última fila con `:::tip` | ROADMAP |
| `## Síntesis` | ≥ 2 similitudes + 1 diferencia clave | criterio #1 |
| `## Criterios` | Lista con bullets explicando cada criterio | F75 §6.10 |
| `## Matriz de decisión por escenario` | Tabla con ≥ 3 escenarios | ROADMAP |
| `## Trade-offs` | Tabla con ≥ 3 filas | ROADMAP |
| `## Veredicto` | 1-2 párrafos | F75 §6.10 |
| Marcas `{src:blk_xxxx}` | ≥ 1 por dato fáctico del SDM | F46 + F76 R8 |
| Anclaje visual | ≥ 1 cada 200 palabras | F76 R3 |
| Cierre | `## Backlinks` + `## Queries` | F75 §4 |

### §3.1 · Tabla principal con "fila decisiva al final"

```
| Criterio | Opción A | Opción B |
|---|---|---|
| Rendimiento (writes/s) | 50k | 200k |
| Consistencia | ACID | eventual |
| Madurez (años) | 25 | 10 |
| Ecosistema | amplio | amplio |

:::tip
**Fila decisiva — Madurez.** En producción, A es preferida por madurez y soporte a largo plazo; B requiere experiencia interna.
:::
```

Reglas:
- **La última fila DEBE ser la decisiva** (criterio más determinante).
- La fila decisiva va envuelta en `:::tip` para resaltarla visualmente.
- Cero criterios no paralelos (criterio #3): cada opción DEBE tener valor en cada criterio, o `n/a` explícito si genuinamente no aplica.

### §3.2 · Regla del "párrafo de síntesis" (criterio #1)

```
## Síntesis

Ambas opciones [A y B] comparten [similitud 1: ej. consistencia eventual vs ACID configurable] y [similitud 2: ej. soporte JSON]. La diferencia clave es que [A se enfoca en X mientras B optimiza Y]. {src:blk_xxxx}
```

Reglas:
- ≥ 2 similitudes explícitas.
- 1 diferencia clave en una frase.
- 1 frase resumen final.
- Sin este párrafo, la tabla queda "suelta" y viola criterio #1.

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
- **R8** Densidad `{src:}` ≥ 0.80 sobre filas fácticas.

### §4.2 · Marcas inline (F46)

- **`{src:blk_xxxx}`** — 12 caracteres hexadecimales (INV-I5). Cada dato fáctico del SDM lleva `{src:}`.
- **`[[term:nombre]]`** — primera aparición del término (INV-I2).
- **`[[note:id]]`** — enlaces a notas `concept` del dominio, `api-reference` de cada opción.
- **`:::derived`** — afirmaciones NO explícitas en el SDM pero deducibles por el autor del digest.
- **`:::external`** — opiniones de expertos externos al SDM (blog posts reconocidos, benchmarks independientes).

### §4.3 · Directivas de bloque (F45)

| Sección | Directiva preferida | Justificación |
|---|---|---|
| `## Comparativa` | Tabla GFM con `:::tip` en la fila decisiva | F45 §6 fila 11 + ROADMAP. |
| `## Síntesis` | Párrafo con ≥ 30 palabras | criterio #1. |
| `## Criterios` | Lista con bullets | F75 §6.10. |
| `## Matriz de decisión` | Tabla GFM | ROADMAP. |
| `## Trade-offs` | Tabla GFM | ROADMAP. |
| `## Casos de uso` | Sub-secciones H3 con `:::tip` / `:::warning` | F45 §6. |
| `## Veredicto` | 1-2 párrafos | F75 §6.10. |

### §4.4 · Anti-patrones

1. **"Tabla suelta sin síntesis"** (criterio #1) — la tabla va seguida de otra sección sin párrafo de síntesis. Solución: cada tabla debe ir seguida de ≥ 1 párrafo narrativo de ≥ 30 palabras.
2. **"Criterios no paralelos"** (criterio #3) — la tabla tiene celdas vacías o `—`. Solución: usar `n/a` explícito solo si genuinamente no aplica; rechazar celdas vacías.
3. **"Fila decisiva ausente"** (ROADMAP) — la tabla no tiene fila decisiva marcada. Solución: la última fila con `:::tip`.
4. **"Comparación inventada"** (criterio #2) — el autor pone un dato que NO está en el SDM. Solución: cada dato lleva `{src:}` o `:::external`/`:::derived`.
5. **"Veredicto contradictorio"** — el párrafo de veredicto dice "elegir A" pero la tabla muestra B mejor en todos los criterios. Solución: revisión humana (no automatizable).
6. **"Matriz de decisión con < 3 escenarios"** — el ROADMAP exige ≥ 3.
7. **"Trade-offs con < 3 filas"** — el ROADMAP exige ≥ 3.
8. **"Tabla > 5 columnas de opciones"** — ilegible. Solución: máximo 5 opciones (típicamente 2-3).
9. **"Síntesis sin diferencia clave"** — el párrafo solo describe similitudes sin nombrar la diferencia. Solución: la frase "diferencia clave" debe aparecer.
10. **"Sección solo de viñetas"** (R6) — `## Criterios` con bullets sin contexto. Solución: 1 párrafo introductorio + bullets.

### §4.5 · Diferencias operativas

| Concepto | Definición operativa |
|---|---|
| **Opción** | Una alternativa comparable (e.g., PostgreSQL, MySQL). |
| **Criterio** | Eje de comparación que se aplica a TODAS las opciones por igual (paralelo). |
| **Fila decisiva** | El criterio que más influye en la decisión final; típicamente madurez, soporte, o dominio. |
| **Trade-off** | Renuncia entre 2 propiedades (e.g., consistencia vs rendimiento). |
| **Escenario** | Caso de uso típico (web app, data warehouse, embedded) que orienta la decisión. |
| **Comparación derivada** | Afirmación no explícita en el SDM; marcada con `:::derived`. |
| **Síntesis** | Párrafo que sigue a una tabla; resume similitudes + diferencia clave. |

---

## §5 · Activación por perfil

```yaml
notes:
  types:
    comparison:
      require_synthesis_after_table: true  # default: true (criterio #1)
      require_decisive_row: true           # default: true (ROADMAP)
      require_scenario_matrix: true        # default: true (ROADMAP)
      require_tradeoffs_table: true        # default: true (ROADMAP)
      require_verdict: true                # default: true
      min_criteria: 4                       # default: 4
      min_scenarios: 3                      # default: 3 (matriz)
      min_tradeoffs: 3                      # default: 3
      max_options: 5                        # default: 5 (más = ilegible)
      parallel_criteria_only: true          # default: true (criterio #3)
      mark_derived_with_directive: true      # default: true (criterio #2)
```

| Campo | Default | Significado |
|---|---|---|
| `require_synthesis_after_table` | `true` | Cada tabla va seguida de `## Síntesis` (criterio #1). |
| `require_decisive_row` | `true` | Última fila con `:::tip` (ROADMAP). |
| `require_scenario_matrix` | `true` | `## Matriz de decisión por escenario` obligatorio (ROADMAP). |
| `require_tradeoffs_table` | `true` | `## Trade-offs` obligatorio (ROADMAP). |
| `require_verdict` | `true` | `## Veredicto` obligatorio (F75 §6.10). |
| `min_criteria` | `4` | Mínimo de criterios en la tabla principal. |
| `min_scenarios` | `3` | Mínimo de escenarios en la matriz. |
| `min_tradeoffs` | `3` | Mínimo de filas en trade-offs. |
| `max_options` | `5` | Máximo de opciones a comparar (más = ilegible). |
| `parallel_criteria_only` | `true` | Criterios no paralelos prohibidos (criterio #3). |
| `mark_derived_with_directive` | `true` | Afirmaciones derivadas usan `:::derived` (criterio #2). |

---

## §6 · Checklist de cierre

Antes de publicar:

- [ ] Cabecera con 5 campos en orden (F75 §2.1).
- [ ] `source-bearing` recomendado.
- [ ] `## TL;DR` ≤ 60 palabras / 8 líneas (R1).
- [ ] `## Comparativa` con tabla; ≥ 4 criterios; última fila con `:::tip` (fila decisiva).
- [ ] `## Síntesis` con ≥ 2 similitudes + 1 diferencia clave (criterio #1).
- [ ] Criterios paralelos: cada opción tiene valor en cada criterio (criterio #3).
- [ ] `## Criterios` con bullets explicando cada criterio (F75 §6.10).
- [ ] `## Matriz de decisión por escenario` con ≥ 3 escenarios (ROADMAP).
- [ ] `## Trade-offs` con ≥ 3 filas (ROADMAP).
- [ ] `## Veredicto` con 1-2 párrafos (F75 §6.10).
- [ ] Afirmaciones derivadas marcadas con `:::derived` o `:::external` (criterio #2).
- [ ] Cierre: `## Backlinks` + `## Queries`.
- [ ] Densidad `{src:}` ≥ 0.80 sobre filas fácticas (R8).
- [ ] `density_check.py --note <path>` exit 0.

---

## §7 · Nota mínima viable

Ejemplo canónico de ~80-100 líneas para una comparación entre 2 opciones.
Pasa `density_check.py --strict` exit 0.

```markdown
---
title: "PostgreSQL vs MySQL (comparativa)"
note-type: comparison
status: draft
tags: [type/comparison, domain/databases]
source: "PostgreSQL 16 docs vs MySQL 8 docs"
source-type: docs
source-anchor: "comparativa"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group / Oracle
product: PostgreSQL 16 / MySQL 8
product-version: "16 / 8"
---

# PostgreSQL vs MySQL (comparativa)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Comparativa de PostgreSQL 16 y MySQL 8: madurez, replicación, JSON, ecosistema, y decisión por escenario. |
| **Procedencia** | PostgreSQL 16 docs vs MySQL 8 docs (docs) §comparativa · recuperado 2026-09-27 |
| **Versión** | 16 / 8 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
PostgreSQL y MySQL son las dos RDBMS open source más maduras. PostgreSQL sobresale en conformidad SQL, extensibilidad y JSONB; MySQL sobresale en simplicidad operativa y replicación madura. La elección depende del caso de uso. {src:blk_m00000000001}

{layer:l2}

## Comparativa
| Criterio | PostgreSQL 16 | MySQL 8 |
|---|---|---|
| Madurez (años) | 28 | 28 |
| Conformidad SQL | alta (la más cercana al estándar) | media |
| Tipos de datos | rico (arrays, JSONB, ranges, hstore) | estándar |
| Replicación | streaming + logical | group replication + binlog |
| JSON | JSONB (binario, indexable) | JSON (texto) |
| Ecosystem | amplio | amplio |
:::tip
**Fila decisiva — Madurez.** Ambas tienen > 25 años de producción; el resto de criterios tiene diferencias superables con configuración. {src:blk_m00000000002}
:::

## Síntesis
Ambas RDBMS son open source y comparten [similitud 1: > 25 años de madurez y soporte amplio] y [similitud 2: replicación nativa robusta]. La diferencia clave es que PostgreSQL prioriza conformidad SQL y extensibilidad (JSONB, arrays, tipos custom) mientras MySQL prioriza simplicidad operativa y rendimiento en read-heavy workloads. {src:blk_m00000000003}

## Criterios
- **Madurez:** años en producción; ambas están entre las más estables.
- **Conformidad SQL:** cercanía al estándar; PostgreSQL lidera.
- **Tipos de datos:** PostgreSQL tiene JSONB, arrays, ranges; MySQL solo JSON texto.
- **Replicación:** ambas soportan streaming y group replication.
- **JSON:** PostgreSQL JSONB indexable; MySQL JSON texto.

## Matriz de decisión por escenario
| Escenario | Mejor opción | Justificación |
|---|---|---|
| OLTP con consultas complejas | PostgreSQL | Mejor planner, conformidad SQL |
| Web app simple | MySQL | Más simple de operar |
| Data warehouse (OLAP) | PostgreSQL | JSONB + extensiones |
| Embedded / móvil | MySQL | Footprint menor |

## Trade-offs
| Trade-off | PostgreSQL 16 | MySQL 8 |
|---|---|---|
| Conformidad SQL vs simplicidad | alta | media |
| Tipos ricos vs footprint | rico | estándar |
| JSON binario vs texto | JSONB indexable | JSON texto |
| Read-heavy vs write-heavy | write-heavy optimizado | read-heavy optimizado |

## Veredicto
Para la mayoría de proyectos nuevos, **PostgreSQL es la opción por defecto** por su conformidad SQL, extensibilidad y ecosistema JSONB. Para web apps simples o cuando la operación del equipo es prioridad, **MySQL sigue siendo válido**. La diferencia real es de ecosistema y cultura del equipo, no de capacidad técnica pura. {src:blk_m00000000004}

## Backlinks
- [[note:postgresql-architecture]] — arquitectura interna.
- [[note:mysql-architecture]] — arquitectura interna.
```

Esta nota mínima (~80 líneas) cubre R1-R8 de F76 y los 3 criterios del
ROADMAP. Sirve de **referencia de forma**.

---

## §8 · Wirings y referencias cruzadas

- **F11** `assets/profile.template.yaml` — defaults de §5.
- **F12** `references/04-authoring/notemark.md` — directivas `:::derived`, `:::external`, `:::tip`, `:::example`, `:::warning`.
- **F44** `references/03-knowledge/note-plan.md` — selector asigna `comparison` cuando la unidad son 2+ alternativas.
- **F45** `references/04-authoring/block-directives.md` — directivas consumidas.
- **F46** `references/04-authoring/inline-marks.md` — `{src:blk_xxxx}` por dato; `[[note:id]]` para referencias.
- **F47** `references/04-authoring/properties.md` — frontmatter; `source-bearing` recomendado.
- **F51** `references/04-authoring/depth-layers.md` — capas L1/L2/L3.
- **F72** `references/07-visual/tokens.md` — colores semánticos de las directivas.
- **F75** `references/07-visual/note-templates.md` — cabecera, apertura/cierre común, §6.10 patrón resumido.
- **F76** `references/07-visual/density.md` — tabla cerrada R1-R8 ejecutable.
- **F77** `evals/visual/` — verificación visual multi-destino.
- **F78** `references/05-note-types/concept.md` — paraguas común.
- **F79** `references/05-note-types/api-reference.md` — comparisons que incluyen APIs.
- **F80** `references/05-note-types/procedure.md` — procedures que aplican la elección.
- **F83** `references/05-note-types/architecture.md` — comparisons entre arquitecturas.
- **F87** `references/05-note-types/comparison.md` — (esta fase).

---

## §9 · Verificación al cierre de la fase

- `wc -l references/05-note-types/comparison.md` ≤ 400 líneas.
- §2 con 4 subsecciones.
- §3 con tabla de componentes mínimos ≥ 11 filas + §3.1 tabla principal + §3.2 patrón de síntesis.
- §4 con 5 subsecciones.
- §5 con tabla de campos del perfil y sus defaults.
- §6 con checklist de cierre ≥ 14 items.
- §7 con nota mínima viable (≥ 80 líneas).
- §8 con ≥ 15 wirings.
- §9 lista de verificación explícita.

**Criterios de aceptación del ROADMAP F87:**

1. _Toda tabla va seguida del párrafo de síntesis._ → battery C2: cada tabla GFM tiene ≥ 1 párrafo narrativo de ≥ 30 palabras en las siguientes ≤ 3 párrafos.
2. _Las comparaciones derivadas están marcadas._ → battery C3: las afirmaciones NO respaldadas por el SDM usan `:::derived` o `:::external`.
3. _Ninguna usa criterios no paralelos._ → battery C4: cada tabla tiene todas las columnas con valor (o `n/a` explícito) en cada fila.
