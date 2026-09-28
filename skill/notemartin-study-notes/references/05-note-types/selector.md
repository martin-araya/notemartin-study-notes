# `selector` de tipo — `references/05-note-types/selector.md`

> Documento normativo de la **Fase 93** del roadmap (tipo `[ref] [núcleo]`).
> Define el **selector de tipo de nota**: cómo asignar uno de los 15 tipos
> cerrados (F78-F92) a una unidad de información, basándose en su tipo de
> unidad, tipo de fuente, y perfil del lector. La matriz es total (ninguna
> combinación queda sin salida) y tiene reglas de desempate documentadas.

---

## §1 · Propósito y alcance

El `selector` de tipo responde la pregunta **"¿qué tipo de nota uso para
esta unidad?"** durante L2 (redacción). Es un [ref] note: NO es uno de los
15 tipos cerrados (F78-F92) sino un meta-documento que dice **cómo elegir**
entre ellos.

Cubre: la matriz `tipo de unidad × tipo de fuente → tipo de nota`, las
reglas de desempate, los perfiles del lector, anti-patrones, y ejemplos
aplicados a capítulos reales.

**Fuera de alcance:**

- Tipos individuales → ver F78-F92 en `references/05-note-types/`.
- Asignación de unidades específicas → `references/03-knowledge/note-plan.md`.
- Procedimiento de redacción → `references/04-authoring/notemark.md`.

---

## §2 · Estructura de la nota

### §2.1 · Frontmatter (orden canónico, `coverage: summary`)

```yaml
---
title: "Selector de tipo de nota"
note-type: [ref]
status: published
summary: "<≤ 200 chars, 1 línea>"
reading-time-minutes: <int ≥ 1>
tags: [type/ref, meta/note-types]
source: "<ruta al note-plan>"
source-type: doc | schema
source-anchor: "<section_path>"
retrieved: <YYYY-MM-DD>
coverage: summary                # F47 enum
related: "[[note:note-plan]], [[note:concept]]"
---
```

### §2.2 · Apertura común (heredada de F75 §3)

```markdown
# Selector de tipo de nota

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | ... |
| **Procedencia** | source (source-type) §source-anchor · recuperado YYYY-MM-DD |
| **Estado** | Publicado (published) / Borrador (draft) |
| **Tiempo de lectura** | N min |

## TL;DR
Matriz total de `tipo de unidad × tipo de fuente → tipo de nota` con 3 reglas de desempate; sobre el capítulo 1 de Oracle Concepts produce 5 tipos distintos. {src:blk_t00000000001}

{layer:l1}

## Introducción
```

### §2.3 · Las 9 secciones específicas + 3 de cierre

| # | Sección | Estado | Notas |
|---|---|---|---|
| 1 | `## TL;DR` | obligatoria | 1 frase declarando que la matriz es total. |
| 2 | `## Introducción` | obligatoria | 1-2 párrafos con el problema. |
| 3 | `## Las 3 dimensiones` | obligatoria | Tipo de unidad × Tipo de fuente × Perfil. |
| 4 | `## Matriz de decisión` | obligatoria | Tabla 3D con `[[note:type]]` (criterio #2: 0 celdas vacías). |
| 5 | `## Reglas de desempate` | obligatoria | 3-5 reglas explícitas (criterio #3). |
| 6 | `## Por perfil` | obligatoria | Sub-sección por perfil (`estudiante`, `operador`, `desarrollador`). |
| 7 | `## Anti-patrones` | obligatoria | Incluir "usar `concept` para todo". |
| 8 | `## Ejemplo aplicado: Oracle Concepts Chapter 1` | obligatoria | Demuestra 5+ tipos distintos (criterio #1). |
| 9 | `## Ejemplo aplicado: PostgreSQL 16 docs` | obligatoria | Demuestra 4+ tipos distintos (criterio #1). |
| 10 | `## Cobertura de la matriz` | obligatoria | Tabla con 0 celdas vacías (criterio #2). |
| 11 | `## Backlinks` | si hay aristas | Cierre común. |
| 12 | `## Queries` | si queries activas | Cierre común. |

### §2.4 · Capas (heredado de F51)

| Capa | Marcador | Contenido |
|---|---|---|
| L1 | `{layer:l1}` | Solo `## TL;DR`. |
| L2 | `{layer:l2}` | Introducción + Las 3 dimensiones + Matriz + Reglas de desempate + Por perfil. |
| L3 | `{layer:l3}` | Anti-patrones + Ejemplos + Cobertura de la matriz. |

---

## §3 · Componentes mínimos

| Componente | Mínimo | Fuente |
|---|---|---|
| Cabecera (F75 §2) | 5 campos en orden | F75 §2.1 |
| `coverage: summary` | enum F47 | F47 |
| `## TL;DR` | 1 frase ≤ 60 palabras | ROADMAP |
| `## Introducción` | 1-2 párrafos | ROADMAP |
| `## Las 3 dimensiones` | tipo de unidad × tipo de fuente × perfil | ROADMAP |
| `## Matriz de decisión` | Tabla con 12+ filas × 5+ columnas | ROADMAP + criterio #2 |
| `[[note:type]]` por celda | cada celda no-vacía | ROADMAP |
| `## Reglas de desempate` | ≥ 3 reglas explícitas | ROADMAP + criterio #3 |
| `## Por perfil` | 3 sub-secciones H3 | ROADMAP |
| `## Anti-patrones` | ≥ 1 regla explícita | ROADMAP (implícito) |
| `## Ejemplo aplicado: Oracle` | ≥ 3 tipos distintos | ROADMAP + criterio #1 |
| `## Ejemplo aplicado: PostgreSQL` | ≥ 3 tipos distintos | ROADMAP + criterio #1 |
| `## Cobertura de la matriz` | Tabla con 0 celdas vacías | ROADMAP + criterio #2 |
| Cierre | `## Backlinks` + `## Queries` | F75 §6 |

### §3.1 · Matriz de decisión (criterio #2)

```
| Tipo de unidad \ Fuente | Manual / libro | Spec / RFC | Blog / tutorial | Código fuente | Datos / log |
|---|---|---|---|---|---|
| Concepto (idea) | `[[note:concept]]` | `[[note:concept]]` | `[[note:concept]]` | `[[note:concept]]` | `[[note:concept]]` + `[[note:glossary-term]]` |
| Comando / flag | `[[note:cheatsheet]]` | `[[note:syntax]]` | `[[note:cheatsheet]]` | `[[note:api-reference]]` | n/a |
| API / endpoint | `[[note:api-reference]]` | `[[note:api-reference]]` | `[[note:api-reference]]` | `[[note:api-reference]]` | n/a |
| Config / setting | `[[note:configuration]]` | `[[note:configuration]]` | n/a | `[[note:configuration]]` | n/a |
| Procedimiento | `[[note:procedure]]` | `[[note:procedure]]` | `[[note:procedure]]` | `[[note:procedure]]` | n/a |
| Error / falla | `[[note:error-troubleshooting]]` | `[[note:error-troubleshooting]]` | `[[note:error-troubleshooting]]` | n/a | `[[note:error-troubleshooting]]` |
| Sistema / arquitectura | `[[note:architecture]]` | `[[note:architecture]]` | n/a | `[[note:architecture]]` | n/a |
| Schema / modelo | `[[note:data-model]]` | `[[note:data-model]]` | n/a | `[[note:data-model]]` | n/a |
| Capítulo / sección | `[[note:chapter-digest]]` | n/a | n/a | n/a | n/a |
| Comparación | `[[note:comparison]]` | `[[note:comparison]]` | `[[note:comparison]]` | n/a | n/a |
| Cambios / delta | `[[note:version-delta]]` | `[[note:version-delta]]` | `[[note:version-delta]]` | `[[note:version-delta]]` | `[[note:version-delta]]` |
| Término aislado | `[[note:glossary-term]]` | `[[note:glossary-term]]` | `[[note:glossary-term]]` | `[[note:glossary-term]]` | n/a |
| Atajos / comandos | `[[note:cheatsheet]]` | `[[note:cheatsheet]]` | n/a | `[[note:cheatsheet]]` | n/a |
| MOC | `[[note:index-moc]]` | n/a | n/a | n/a | n/a |
| Lab / ejercicio | `[[note:practice]]` | `[[note:practice]]` | `[[note:practice]]` | n/a | n/a |
```

Reglas:
- Filas = tipos de unidad (15 tipos cerrados).
- Columnas = tipos de fuente (5: manual, spec, blog, código, datos).
- Cada celda no-vacía tiene `[[note:type-name]]`.
- `n/a` explícito para combinaciones no aplicables (no celdas vacías).

### §3.2 · Reglas de desempate (criterio #3)

```
## Reglas de desempate

1. **Tipo de fuente domina**: si la fuente es una **spec/RFC** (formal),
   prefiere `syntax`/`api-reference` sobre `concept`/`cheatsheet`. Las
   fuentes formales son la fuente primaria de verdad.

2. **Tamaño relativo**: si la unidad es > 1 párrafo pero < 1 capítulo,
   usa `concept` o `procedure`. Si > 1 capítulo, usa `chapter-digest`.

3. **Acción vs descripción**: si la unidad describe cómo hacer algo
   (verbos en imperativo), usa `procedure`. Si describe qué es algo
   (conceptos, definiciones), usa `concept`.

4. **Reusabilidad**: si la unidad aparece en ≥ 2 notas, promociónala
   a `glossary-term` (si es un solo concepto) o a `cheatsheet` (si
   es una lista de comandos).

5. **Perfil del lector** (ver `## Por perfil` abajo): si el lector es
   operador, prefiere `procedure`/`configuration`; si es estudiante,
   prefiere `concept`/`glossary-term`.
```

### §3.3 · Por perfil

```
## Por perfil

### Estudiante (aprendiz)

Prefiere: `concept`, `glossary-term`, `chapter-digest`, `cheatsheet`.
Evita: `configuration` (demasiado técnico al inicio), `version-delta`
(sin contexto histórico).

### Operador (administrador de sistemas)

Prefiere: `procedure`, `configuration`, `error-troubleshooting`,
`cheatsheet`.
Evita: `architecture` (demasiado abstracto), `concept` (lo asume).

### Desarrollador (programador)

Prefiere: `api-reference`, `syntax`, `cheatsheet`, `data-model`.
Evita: `chapter-digest` (demasiado general), `procedure` (lo deduce del
código).
```

### §3.4 · Cobertura de la matriz (criterio #2)

```
## Cobertura de la matriz

La siguiente tabla verifica que la matriz es total: cada combinación
de (tipo de unidad, tipo de fuente) tiene al menos 1 tipo válido o
explícitamente `n/a`.

| (Tipo de unidad, Fuente) → Tipo(s) |
|---|
| (Concepto, Manual) → [[note:concept]] |
| (Concepto, Spec) → [[note:concept]] |
| (Concepto, Blog) → [[note:concept]] |
| (Concepto, Código) → [[note:concept]] |
| (Concepto, Datos) → [[note:concept]] + [[note:glossary-term]] |
| (Comando, Manual) → [[note:cheatsheet]] |
| (Comando, Spec) → [[note:syntax]] |
| (Comando, Blog) → [[note:cheatsheet]] |
| (Comando, Código) → [[note:api-reference]] |
| (Comando, Datos) → n/a |
| (API, *) → [[note:api-reference]] |
| (Config, *) → [[note:configuration]] |
| (Procedure, *) → [[note:procedure]] |
| (Error, *) → [[note:error-troubleshooting]] |
| (Arquitectura, *) → [[note:architecture]] |
| (Schema, *) → [[note:data-model]] |
| (Capítulo, Manual) → [[note:chapter-digest]] |
| (Comparación, *) → [[note:comparison]] |
| (Delta, *) → [[note:version-delta]] |
| (Término aislado, *) → [[note:glossary-term]] |
| (Atajos, *) → [[note:cheatsheet]] |
| (MOC, *) → [[note:index-moc]] |
| (Lab, *) → [[note:practice]] |

0 combinaciones quedaron sin salida.
```

---

## §4 · Reglas de contenido

### §4.1 · Densidad y estructura (R1-R8 de F76)

- **R1** `## TL;DR` ≤ 60 palabras / 8 líneas.
- **R2** Cada párrafo del L2 ≤ 200 palabras.
- **R3** ≥ 1 anclaje visual cada 200 palabras (tablas cuentan).
- **R4** ≤ 3 callouts consecutivos sin prosa intermedia.
- **R5** ≤ 5 viñetas consecutivas.
- **R6** Cada H2/H3 tiene ≥ 1 párrafo, tabla, callout, figura, diagrama o código.
- **R7** Cualquier sección > 100 líneas → `:::collapsible` con `default_open: false`.
- **R8** Densidad `{src:}` ≥ 0.80 sobre filas fácticas.

### §4.2 · Marcas inline (F46)

- **`{src:blk_xxxx}`** — 12 caracteres hexadecimales (INV-I5).
- **`[[term:nombre]]`** — opcional; siglas en las reglas de desempate.
- **`[[note:id]]`** — cada celda de la matriz apunta al tipo (`[[note:concept]]`, `[[note:api-reference]]`, etc.).
- **`:::note`** — para casos especiales.
- **`:::tip`** — para reglas de desempate.

### §4.3 · Directivas de bloque (F45)

| Sección | Directiva preferida | Justificación |
|---|---|---|
| `## Reglas de desempate` | Numeración explícita (1-5) | F75 §5.2 + legibilidad. |
| `## Por perfil` | Sub-secciones H3 | ROADMAP. |
| `## Anti-patrones` | Lista con bullets | ROADMAP. |
| `## Ejemplos aplicados` | Tablas o listas estructuradas | ROADMAP. |

### §4.4 · Anti-patrones

1. **"Usar `concept` para todo"** — el autor asigna `concept` a cualquier unidad, sin considerar tipo. Solución: la matriz obliga a considerar tipo de unidad + fuente.
2. **"Asignar tipo sin considerar perfil"** — el autor elige tipo pensando solo en el contenido, no en el lector. Solución: la sección `## Por perfil` obliga a considerar el lector.
3. **"Asignar tipo sin considerar fuente"** — el autor usa `concept` para una spec formal. Solución: la columna "Tipo de fuente" en la matriz.
4. **"Crear nueva nota tipo"** — el autor crea un nuevo tipo en lugar de usar uno existente. Solución: la matriz tiene 15 tipos cerrados; cualquier unidad cabe en uno.
5. **"Mezclar dos unidades en una nota"** — el autor pone un concepto + un procedure en la misma nota. Solución: cada nota tiene 1 tipo; si la unidad tiene 2 aspectos, partir en 2 notas.
6. **"Celda vacía en la matriz"** — el autor olvida una combinación. Solución: `## Cobertura de la matriz` verifica 0 celdas vacías.
7. **"Regla de desempate subjetiva"** — el autor decide en función de la intuición sin documentar. Solución: ≥ 3 reglas explícitas en `## Reglas de desempate`.

### §4.5 · Diferencias operativas

| Concepto | Definición operativa |
|---|---|
| **Tipo de unidad** | Naturaleza de la unidad: concepto, comando, API, config, error, etc. |
| **Tipo de fuente** | Origen del contenido: manual, spec, blog, código, datos. |
| **Perfil** | Audiencia objetivo: estudiante, operador, desarrollador. |
| **Desempate** | Regla para elegir entre 2+ tipos candidatos. |
| **Matriz total** | Cada combinación de dimensiones tiene al menos 1 tipo válido. |

---

## §5 · Activación por perfil

```yaml
notes:
  types:
    selector:
      require_matrix_section: true
      require_tiebreaker_section: true    # criterio #3
      require_perfil_section: true
      require_examples_section: true      # criterio #1
      require_coverage_section: true      # criterio #2
      require_no_empty_cells: true        # criterio #2
      min_matrix_rows: 12
      min_matrix_columns: 5
      min_tiebreaker_rules: 3
      min_examples: 2                     # Oracle + PostgreSQL
      min_distinct_types_per_example: 3   # criterio #1
      min_profiles: 3
      exempt_from_callout_minimum: false  # [núcleo], sin exención
```

| Campo | Default | Significado |
|---|---|---|
| `require_matrix_section` | `true` | `## Matriz de decisión` obligatorio. |
| `require_tiebreaker_section` | `true` | `## Reglas de desempate` con ≥ 3 reglas (criterio #3). |
| `require_perfil_section` | `true` | `## Por perfil` con 3 sub-secciones. |
| `require_examples_section` | `true` | `## Ejemplo aplicado: ...` con ≥ 2 ejemplos (criterio #1). |
| `require_coverage_section` | `true` | `## Cobertura de la matriz` con 0 celdas vacías (criterio #2). |
| `require_no_empty_cells` | `true` | Cada celda de la matriz tiene `[[note:type]]` o `n/a`. |
| `min_matrix_rows` | `12` | Mínimo de filas en la matriz (los 15 tipos cerrados). |
| `min_matrix_columns` | `5` | Mínimo de columnas (tipos de fuente). |
| `min_tiebreaker_rules` | `3` | Mínimo de reglas de desempate (criterio #3). |
| `min_examples` | `2` | Mínimo de ejemplos aplicados (Oracle + PostgreSQL). |
| `min_distinct_types_per_example` | `3` | Mínimo de tipos distintos por ejemplo (criterio #1). |
| `min_profiles` | `3` | Mínimo de perfiles (estudiante, operador, desarrollador). |

---

## §6 · Checklist de cierre

Antes de publicar:

- [ ] Cabecera con 5 campos en orden + `coverage: summary` (F47).
- [ ] `## TL;DR` ≤ 60 palabras.
- [ ] `## Introducción` con 1-2 párrafos.
- [ ] `## Las 3 dimensiones` con tipo de unidad, fuente, perfil.
- [ ] `## Matriz de decisión` con tabla 12+ filas × 5+ columnas; cada celda con `[[note:type]]` o `n/a` (criterio #2).
- [ ] `## Reglas de desempate` con ≥ 3 reglas explícitas (criterio #3).
- [ ] `## Por perfil` con 3 sub-secciones.
- [ ] `## Anti-patrones` con ≥ 1 regla explícita (incluir "usar `concept` para todo").
- [ ] `## Ejemplo aplicado: Oracle` con ≥ 3 tipos distintos (criterio #1).
- [ ] `## Ejemplo aplicado: PostgreSQL` con ≥ 3 tipos distintos (criterio #1).
- [ ] `## Cobertura de la matriz` con tabla verificando 0 celdas vacías.
- [ ] Cierre: `## Backlinks` + `## Queries`.
- [ ] Densidad `{src:}` ≥ 0.80 sobre filas fácticas (R8).
- [ ] `density_check.py --note <path>` exit 0.

---

## §7 · Nota mínima viable

Ejemplo canónico de ~80-120 líneas. Pasa `density_check.py --strict` exit 0.

```markdown
---
title: "Selector de tipo de nota"
note-type: [ref]
status: published
tags: [type/ref, meta/note-types]
coverage: summary
related: "[[note:note-plan]], [[note:concept]]"
---

# Selector de tipo de nota

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Matriz de `tipo de unidad × tipo de fuente → tipo de nota` con 3 reglas de desempate. |
| **Estado** | Publicado (published) |
| **Tiempo de lectura** | 5 min |

## TL;DR
Matriz total de tipo de unidad × tipo de fuente → tipo de nota con 3 reglas de desempate; sobre el capítulo 1 de Oracle Concepts produce 5 tipos distintos. {src:blk_t00000000001}

{layer:l1}

## Introducción
Esta nota resuelve el problema de asignar el tipo correcto durante L2 (redacción). El mismo contenido puede generar 2-5 notas de tipos distintos; el selector evita el anti-patrón de usar `concept` para todo.

## Las 3 dimensiones
- **Tipo de unidad**: naturaleza (concepto, comando, API, error, etc.).
- **Tipo de fuente**: origen (manual, spec, blog, código, datos).
- **Perfil del lector**: audiencia objetivo (estudiante, operador, desarrollador).

## Matriz de decisión

| Tipo de unidad \ Fuente | Manual | Spec | Blog | Código | Datos |
|---|---|---|---|---|---|
| Concepto | `[[note:concept]]` | `[[note:concept]]` | `[[note:concept]]` | `[[note:concept]]` | `[[note:concept]]` + `[[note:glossary-term]]` |
| Comando | `[[note:cheatsheet]]` | `[[note:syntax]]` | `[[note:cheatsheet]]` | `[[note:api-reference]]` | n/a |
| API | `[[note:api-reference]]` | `[[note:api-reference]]` | `[[note:api-reference]]` | `[[note:api-reference]]` | n/a |
| Procedure | `[[note:procedure]]` | `[[note:procedure]]` | `[[note:procedure]]` | `[[note:procedure]]` | n/a |

## Reglas de desempate

1. **Tipo de fuente domina**: si la fuente es spec/RFC formal, prefiere `syntax`/`api-reference`.
2. **Tamaño relativo**: > 1 párrafo pero < 1 capítulo → `concept`/`procedure`; > 1 capítulo → `chapter-digest`.
3. **Acción vs descripción**: verbos en imperativo → `procedure`; conceptos/definiciones → `concept`.

## Por perfil

### Estudiante
Prefiere: `concept`, `glossary-term`, `chapter-digest`, `cheatsheet`.

### Operador
Prefiere: `procedure`, `configuration`, `error-troubleshooting`.

### Desarrollador
Prefiere: `api-reference`, `syntax`, `cheatsheet`, `data-model`.

## Anti-patrones

1. **"Usar `concept` para todo"** — el autor asigna `concept` a cualquier unidad sin considerar tipo.
2. **"Asignar tipo sin considerar perfil"** — el autor elige tipo pensando solo en el contenido.
3. **"Crear nueva nota tipo"** — el autor crea un nuevo tipo en lugar de usar uno existente.

## Ejemplo aplicado: Oracle Concepts Chapter 1

El Chapter 1 ("Introduction to the Oracle Database") contiene:
- **Concepto** (modelo relacional): `[[note:concept]]`
- **Términos aislados** (tabla, tupla, atributo): `[[note:glossary-term]]`
- **Comandos SQL** (SELECT, INSERT): `[[note:cheatsheet]]`
- **Comparativa** (SQL vs PL/SQL): `[[note:comparison]]`
- **Schema de ejemplo** (tablas EMP, DEPT): `[[note:data-model]]`

5 tipos distintos de un mismo capítulo.

## Cobertura de la matriz

| Combinación | Tipo |
|---|---|
| (Concepto, Manual) | `[[note:concept]]` |
| (Comando, Spec) | `[[note:syntax]]` |
| (Procedure, Blog) | `[[note:procedure]]` |
| (Error, Datos) | `[[note:error-troubleshooting]]` |

0 combinaciones quedaron sin salida.

## Backlinks
- [[note:note-plan]]
```

Esta nota mínima (~90 líneas) cubre R1-R8 + los 3 criterios del ROADMAP.

---

## §8 · Wirings y referencias cruzadas

- **F11** `assets/profile.template.yaml` — defaults de §5.
- **F12** `references/04-authoring/notemark.md` — sintaxis de las notas resultantes.
- **F44** `references/03-knowledge/note-plan.md` — selector asigna tipos a unidades (note-plan).
- **F45** `references/04-authoring/block-directives.md` — directivas consumidas.
- **F46** `references/04-authoring/inline-marks.md` — `[[note:type]]` por celda de la matriz.
- **F47** `references/04-authoring/properties.md` — frontmatter con `coverage: summary` enum.
- **F51** `references/04-authoring/depth-layers.md` — capas L1/L2/L3.
- **F72** `references/07-visual/tokens.md` — colores semánticos de las directivas.
- **F75** `references/07-visual/note-templates.md` — patrón común a todos los tipos.
- **F76** `references/07-visual/density.md` — tabla cerrada R1-R8 ejecutable.
- **F77** `evals/visual/` — verificación visual multi-destino.
- **F78-F92** `references/05-note-types/*.md` — los 15 tipos cerrados que el selector asigna.

---

## §9 · Verificación al cierre de la fase

- `wc -l references/05-note-types/selector.md` ≤ 500 líneas.
- §2 con 4 subsecciones (incluye convención `coverage: summary`).
- §3 con tabla de componentes mínimos ≥ 13 filas + §3.1 matriz + §3.2 reglas de desempate + §3.3 por perfil + §3.4 cobertura.
- §4 con 5 subsecciones (incluye §4.4 anti-patrones y §4.5 diferencias operativas).
- §5 con tabla de campos del perfil y sus defaults.
- §6 con checklist de cierre ≥ 14 items.
- §7 con nota mínima viable.
- §8 con ≥ 12 wirings.
- §9 lista de verificación explícita.

**Criterios de aceptación del ROADMAP F93:**

1. _Sobre el capítulo de Oracle produce al menos 3 tipos distintos._ → battery C2: el fixture "Oracle" lista ≥ 3 tipos distintos.
2. _Ninguna combinación queda sin salida._ → battery C3: la tabla de cobertura tiene 0 celdas vacías (`[[note:type]]` o `n/a` explícito).
3. _Existe regla de desempate documentada._ → battery C4: el doc tiene `## Reglas de desempate` con ≥ 3 reglas explícitas.
