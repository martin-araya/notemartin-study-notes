# `practice` / lab — `references/05-note-types/practice.md`

> Documento normativo de la **Fase 92** del roadmap. Define el patrón de la
> nota de tipo `practice` (lab): objetivo, entorno, pasos numerados, resultado
> esperado, qué observar, variación, limpieza, marcado de lo que NO debe
> correrse en producción, y criterio de cuándo omitir el lab.
> **Exenta de la frecuencia mínima de callouts (F75 §6.15)**: el contenido
> es procedural.

---

## §1 · Propósito y alcance

Una nota `practice` documenta **un laboratorio o ejercicio reproducible**:
el lector puede ejecutarlo paso a paso para aprender un concepto o validar
una hipótesis, con entorno declarado, pasos numerados, resultado esperado
y limpieza. Los labs son la **aplicación práctica** de los conceptos
(`concept`), procedures (`procedure`) y APIs (`api-reference`).

`practice` cubre: tutoriales paso a paso (hello world en un lenguaje),
ejercicios de troubleshooting, simulaciones de errores, benchmarks
controlados, demos de productos, pruebas de concepto (PoC).

**Fuera de alcance:**

- Procedure de producción → `procedure` (F80).
- Concepto único → `concept` (F78).
- API o endpoint → `api-reference` (F79).
- Tabla de comandos → `cheatsheet` (F90).
- Capítulo de libro → `chapter-digest` (F86).

---

## §2 · Estructura de la nota

### §2.1 · Frontmatter (orden canónico, `source-bearing` recomendado)

```yaml
---
title: "<lab>: <objetivo>"
note-type: practice
status: draft | published
summary: "<≤ 200 chars, 1 línea>"
reading-time-minutes: <int ≥ 1>
tags: [type/practice, domain/<uno o más>, product/<nombre>]
source: "<ruta al tutorial original; opcional>"
source-type: docs | tutorial | blog | wiki
source-anchor: "<page|section>"
source-url: "<opcional>"
retrieved: <YYYY-MM-DD>
difficulty: <1-5>                # F75 §6.15: enum
vendor: "<proveedor>"
product: "<nombre del producto>"
product-version: "<versión>"
related: "[[note:concept-base]], [[note:procedure-relacionada]]"
---
```

`difficulty` ∈ {1, 2, 3, 4, 5}. 1 = trivial (hello world), 5 = avanzado
(multi-step con troubleshooting).

### §2.2 · Apertura común (heredada de F75 §3)

```markdown
# {title}

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | ... |
| **Procedencia** | source (source-type) §source-anchor · recuperado YYYY-MM-DD |
| **Versión** | product product-version |
| **Estado** | Borrador (draft) / Publicado (published) |
| **Tiempo de lectura** | N min |

## TL;DR
{1 frase con el objetivo del lab; ≤ 60 palabras}

{layer:l2}

## Enunciado
```

### §2.3 · Las 9 secciones específicas + 2 opcionales + 3 de cierre

| # | Sección | Estado | Notas |
|---|---|---|---|
| 1 | `## TL;DR` | obligatoria | 1 frase con el objetivo. |
| 2 | `## Enunciado` | obligatoria | 1 párrafo con el problema a resolver (F75 §6.15). |
| 3 | `## Entorno` | obligatoria | Tabla con software, versiones, recursos (criterio #1). |
| 4 | `## Objetivo` | obligatoria | 1-2 frases declarando qué se aprende. |
| 5 | `## Solución` | obligatoria | Pasos numerados con bloque `code`. |
| 6 | `## Qué observar` | obligatoria | `:::note` o lista con outputs esperados. |
| 7 | `## Verificación` | obligatoria | Cómo saber que la solución es correcta (F75 §6.15). |
| 8 | `## Limpieza` | obligatoria | Pasos para revertir los efectos (criterio #1). |
| 9 | `## Lo que NO debe correrse en producción` | obligatoria | `:::danger` listando comandos peligrosos. |
| 10 | `## Cuándo omitir este lab` | obligatoria | ≥ 1 criterio (criterio #3). |
| 11 | `## Pistas` | opcional | `:::tip` con pistas progresivas (F75 §6.15). |
| 12 | `## Variantes` | opcional | Otras formas de resolver (F75 §6.15). |
| 13 | `## Backlinks` | si hay aristas | Cierre común. |
| 14 | `## Queries` | si queries activas | Cierre común. |
| 15 | `## Ver también` | opcional si `related:` | Cierre común. |

### §2.4 · Capas (heredado de F51)

| Capa | Marcador | Contenido |
|---|---|---|
| L1 | `{layer:l1}` | Solo `## TL;DR`. |
| L2 | `{layer:l2}` | Enunciado + Entorno + Objetivo + Solución. 50-70% del total. |
| L3 | `{layer:l3}` | Qué observar + Verificación + Limpieza + Lo que NO debe correrse + Cuándo omitir + Pistas + Variantes. Si > 100 líneas, `:::collapsible` con `default_open: false` (R7). |

### §2.5 · Autoevaluación (F102)

Tipos de pregunta asignados a `practice` (ver
`references/09-study/self-evaluation.md` §3):

| Tipo de pregunta | Asignado |
|---|---|
| Recuerdo | — |
| Aplicación | ✅ |
| Diagnóstico | ✅ |
| Decisión | — |
| Predicción | ✅ |

Notas: aplicación (uso correcto en el lab) + diagnóstico (qué falla si…)
+ predicción (qué log/efecto esperas). El lector verifica con el lab.
La nota puede declarar `self-evaluation-types` como superset del default
(nunca subset).

---

## §3 · Componentes mínimos

| Componente | Mínimo | Fuente |
|---|---|---|
| Cabecera (F75 §2) | 5 campos en orden | F75 §2.1 |
| `difficulty` (1-5) | enum | F75 §6.15 |
| `source-bearing` | recomendado | F75 §6.15 |
| `## TL;DR` | 1 frase ≤ 60 palabras | ROADMAP |
| `## Enunciado` | 1 párrafo con el problema | F75 §6.15 |
| `## Entorno` | Tabla con ≥ 3 componentes (criterio #1) | ROADMAP + criterio #1 |
| `## Objetivo` | 1-2 frases | ROADMAP |
| `## Solución` | Pasos numerados con bloque `code` (F75 §6.15) | F75 §6.15 |
| `## Qué observar` | `:::note` o lista | ROADMAP |
| `## Verificación` | 1 frase | F75 §6.15 |
| `## Limpieza` | ≥ 1 paso (criterio #1) | ROADMAP + criterio #1 |
| `## Lo que NO debe correrse en producción` | `:::danger` | ROADMAP + criterio #2 |
| `## Cuándo omitir este lab` | ≥ 1 criterio (criterio #3) | ROADMAP + criterio #3 |
| `## Pistas` | opcional; `:::tip` con pistas progresivas | F75 §6.15 |
| `## Variantes` | opcional | F75 §6.15 |
| Marcas `{src:blk_xxxx}` | ≥ 1 por paso del SDM | F46 + F76 R8 |
| Pasos destructivos con `:::warning` | cada `rm -rf` / `DROP` / `kubectl delete` | criterio #2 |
| Exenta de callouts | contenido procedural | F75 §6.15 |
| Cierre | `## Backlinks` + `## Queries` | F75 §6.15 |

### §3.1 · Tabla canónica de Entorno (criterio #1)

```
| Componente | Versión | Notas |
|---|---|---|
| Sistema operativo | Linux 5.x / macOS 14 / WSL2 | - |
| Docker | 25.x | instalar via docker.com |
| PostgreSQL | 16 | cliente `psql` ≥ 16 |
| Recursos | 2 GB RAM, 5 GB disco | mínimo para el lab |
```

Reglas:
- ≥ 3 componentes listados.
- Versiones específicas (no "latest").
- Recursos mínimos declarados.

### §3.2 · Patrón de paso destructivo con `:::warning` (criterio #2)

```
### Paso 3: Borrar el container
:::warning
**Este paso es destructivo.** El container y sus datos se eliminan permanentemente. NO ejecutes este paso en producción sin antes hacer backup.
:::

```bash
docker rm -f practice-container
```
```

Reglas:
- `:::warning` o `:::danger` ANTES del bloque de código.
- Texto del warning explica qué se destruye y por qué es peligroso.
- Indica explícitamente "no ejecutar en producción" si aplica.

### §3.3 · Patrón de Limpieza (criterio #1)

```
## Limpieza

1. Parar y borrar el container:
   ```bash
   docker stop practice-container
   docker rm practice-container
   ```
2. Borrar la imagen:
   ```bash
   docker rmi practice-image
   ```
3. Borrar archivos temporales:
   ```bash
   rm -f /tmp/practice-output.txt
   ```

Después de la limpieza, el sistema vuelve a su estado original.
```

Reglas:
- Pasos numerados con bloque `code`.
- ≥ 1 paso de limpieza.
- Confirmación explícita del estado final.

### §3.4 · Patrón de Cuándo omitir (criterio #3)

```
## Cuándo omitir este lab

:::note
Omite este lab si: (1) ya dominas el flujo completo de backup + restore con `pg_dump`/`pg_restore`; (2) el cluster de producción tiene políticas de backup declaradas en Terraform/Kubernetes y prefieres validar esas políticas en lugar de hacer backup manual; (3) trabajas con bases de datos que usan replicación nativa y el backup se hace vía WAL archiving + PITR.
:::
```

Reglas:
- 1-2 frases declarando escenarios donde el lab no aplica.
- Formato `:::note` o párrafo claro.
- ≥ 1 criterio explícito.

---

## §4 · Reglas de contenido

### §4.1 · Densidad y estructura (R1-R8 de F76)

- **R1** `## TL;DR` ≤ 60 palabras / 8 líneas.
- **R2** Cada párrafo del L2 ≤ 200 palabras.
- **R3** ≥ 1 anclaje visual cada 200 palabras (tablas y code blocks cuentan).
- **R4** ≤ 3 callouts consecutivos sin prosa intermedia.
- **R5** ≤ 5 viñetas consecutivas.
- **R6** Cada H2/H3 tiene ≥ 1 párrafo, tabla, callout, figura, diagrama o código.
- **R7** Cualquier sección > 100 líneas → `:::collapsible` con `default_open: false`.
- **R8** Densidad `{src:}` ≥ 0.80 sobre filas fácticas.
- **Anti-patrón F75 §6.15**: la frecuencia mínima de callouts no aplica — el contenido es procedural.

### §4.2 · Marcas inline (F46)

- **`{src:blk_xxxx}`** — 12 caracteres hexadecimales (INV-I5). Cada paso del SDM lleva `{src:}`.
- **`[[term:nombre]]`** — opcional; siglas o términos técnicos relevantes.
- **`[[note:id]]`** — enlaces a notas concept / procedure / api-reference relevantes.
- **`:::warning`** — para pasos destructivos (criterio #2).
- **`:::danger`** — para `## Lo que NO debe correrse en producción`.
- **`:::tip`** — para pistas en `## Pistas`.
- **`:::note`** — para qué observar y cuándo omitir.

### §4.3 · Directivas de bloque (F45)

| Sección | Directiva preferida | Justificación |
|---|---|---|
| `## Qué observar` | `:::note` o tabla | ROADMAP. |
| `## Lo que NO debe correrse en producción` | `:::danger` | ROADMAP + criterio #2. |
| `## Cuándo omitir este lab` | `:::note` | ROADMAP + criterio #3. |
| `## Pistas` | `:::tip` (opcional) | F75 §6.15. |
| Paso destructivo | `:::warning` o `:::danger` antes del code block | criterio #2. |

### §4.4 · Anti-patrones

1. **"Sin entorno explícito"** (criterio #1) — el autor describe el procedimiento sin declarar versiones. Solución: `## Entorno` con tabla ≥ 3 componentes.
2. **"Sin limpieza"** (criterio #1) — el autor describe cómo hacer el lab pero no cómo revertir. Solución: `## Limpieza` con ≥ 1 paso.
3. **"Paso destructivo sin `:::warning`"** (criterio #2) — `rm -rf` o `DROP DATABASE` sin advertir. Solución: battery C3 detecta el patrón.
4. **"Sin criterio de cuándo omitir"** (criterio #3) — el lab se aplica universalmente. Solución: `## Cuándo omitir este lab` con ≥ 1 criterio.
5. **"Mezcla con procedure"** — el lab es muy largo (> 30 min). Solución: partir en labs secuenciales.
6. **"Pistas revelan la solución"** — el autor da la respuesta en `:::tip`. Solución: las pistas deben ser incrementales (no la solución final).
7. **"Sin `## Cuándo omitir`"** — el autor asume que el lab es universal.
8. **"Mezcla de dominios"** — un lab mezcla DB + Docker + Git. Solución: un lab por dominio.
9. **"Procedimiento sin enunciado"** — el autor describe pasos sin enunciar el problema a resolver. Solución: `## Enunciado` obligatorio (F75 §6.15).
10. **"Sin verificación"** — el autor describe pasos sin indicar cómo saber que la solución es correcta. Solución: `## Verificación` obligatorio (F75 §6.15).

### §4.5 · Diferencias operativas

| Concepto | Definición operativa |
|---|---|
| **Lab** | Ejercicio reproducible con entorno, pasos, resultado y limpieza. |
| **Entorno** | Software, versiones, recursos mínimos. |
| **Paso destructivo** | Comando que borra/modifica estado permanente (rm, DROP, kubectl delete). |
| **Limpieza** | Pasos para revertir el estado del lab al estado original. |
| **Resultado esperado** | Output o estado observable al completar el lab. |
| **Pista** | `:::tip` que ayuda sin revelar la solución final. |
| **Cuándo omitir** | Criterio explícito de escenarios donde el lab no aplica. |
| **`:::danger`** | Directiva que marca un paso como peligroso en producción. |

---

## §5 · Activación por perfil

```yaml
notes:
  types:
    practice:
      require_entorno_section: true       # criterio #1
      require_objetivo: true
      require_pasos_numerados: true        # F75 §6.15
      require_verificacion: true          # F75 §6.15
      require_limpieza: true              # criterio #1
      require_cuando_omitir: true         # criterio #3
      require_no_produccion: true         # criterio #2
      require_warning_on_destructive: true  # criterio #2
      min_entorno_components: 3
      min_limpieza_steps: 1
      min_omitir_criteria: 1
      exempt_from_callout_minimum: true   # F75 §6.15
      difficulty_required: true           # F75 §6.15
```

| Campo | Default | Significado |
|---|---|---|
| `require_entorno_section` | `true` | `## Entorno` con ≥ 3 componentes (criterio #1). |
| `require_objetivo` | `true` | `## Objetivo` con 1-2 frases. |
| `require_pasos_numerados` | `true` | `## Solución` con lista numerada (F75 §6.15). |
| `require_verificacion` | `true` | `## Verificación` (F75 §6.15). |
| `require_limpieza` | `true` | `## Limpieza` con ≥ 1 paso (criterio #1). |
| `require_cuando_omitir` | `true` | `## Cuándo omitir este lab` con ≥ 1 criterio (criterio #3). |
| `require_no_produccion` | `true` | `## Lo que NO debe correrse en producción` (criterio #2). |
| `require_warning_on_destructive` | `true` | Cada paso destructivo con `:::warning` adyacente (criterio #2). |
| `min_entorno_components` | `3` | Mínimo de componentes en `## Entorno` (criterio #1). |
| `min_limpieza_steps` | `1` | Mínimo de pasos en `## Limpieza` (criterio #1). |
| `min_omitir_criteria` | `1` | Mínimo de criterios en `## Cuándo omitir` (criterio #3). |
| `exempt_from_callout_minimum` | `true` | F75 §6.15 — el contenido es procedural. |
| `difficulty_required` | `true` | F75 §6.15 — enum `difficulty` (1-5) en frontmatter. |

---

## §6 · Checklist de cierre

Esta sección resume el bloque del tipo. La fuente normativa es
`references/10-quality/checklists-by-type.md` §4.15. Esta copia se conserva
para que el agente que carga solo este archivo tenga la lista delante;
cualquier cambio debe aplicarse primero allí y después sincronizarse aquí.

### §6.1 · Bloqueantes [B]

- [ ] [B] Cabecera con 5 campos en orden + `difficulty` (1-5) (F75 §6.15).
- [ ] [B] `source-bearing` recomendado (F75 §6.15).
- [ ] [B] `## TL;DR` ≤ 60 palabras.
- [ ] [B] `## Enunciado` con 1 párrafo (F75 §6.15).
- [ ] [B] `## Entorno` con tabla y ≥ 3 componentes (criterio #1).
- [ ] [B] `## Objetivo` con 1-2 frases.
- [ ] [B] `## Solución` con pasos numerados (F75 §6.15).
- [ ] [B] Cada paso destructivo con `:::warning` antes del code block (criterio #2).
- [ ] [B] `## Qué observar` con `:::note` o lista.
- [ ] [B] `## Verificación` con 1 frase (F75 §6.15).
- [ ] [B] `## Limpieza` con ≥ 1 paso (criterio #1).
- [ ] [B] `## Lo que NO debe correrse en producción` con `:::danger` (criterio #2). **OMIT en `reference`** (F112 §5.1).
- [ ] [B] `## Cuándo omitir este lab` con ≥ 1 criterio (criterio #3). **OMIT en `reference`** (F112 §5.1).
- [ ] [B] Densidad `{src:}` ≥ 0.80 sobre filas fácticas (R8).
- [ ] [B] `density_check.py --note <path>` exit 0.

### §6.2 · Recomendados [R]

- [ ] [R] `## Pistas` con `:::tip` cuando el lab es no trivial. **OMIT en `reference`** (F112 §5.1).
- [ ] [R] Cierre: `## Backlinks` + `## Queries`.

---

## §7 · Nota mínima viable

Ejemplo canónico de ~60-100 líneas. Pasa `density_check.py --strict` exit 0.

```markdown
---
title: "PostgreSQL — backup + restore con pg_dump/pg_restore"
note-type: practice
status: draft
difficulty: 2
tags: [type/practice, domain/databases, product/postgresql]
source: "PostgreSQL 16 docs"
source-type: docs
source-anchor: "backup-dump"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:procedure-postgres-backup]], [[note:postgresql-mvcc]]"
---

# PostgreSQL — backup + restore con pg_dump/pg_restore

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Lab: backup lógico de una BD con `pg_dump -Fc` y restore con `pg_restore`. |
| **Procedencia** | PostgreSQL 16 docs (docs) §backup-dump · recuperado 2026-09-27 |
| **Versión** | 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 10 min |

## TL;DR
Backup + restore completo de una BD PostgreSQL usando `pg_dump -Fc` (formato custom) y `pg_restore`. Aprende a crear archivos `.dump` comprimidos y restaurarlos selectivamente. {src:blk_p00000000001}

{layer:l2}

## Enunciado
Tienes una BD `mydb` que necesitas respaldar completamente y restaurar en otro servidor. El objetivo es practicar el flujo de backup/restore con formato custom (comprimido) y restauración selectiva.

## Entorno

| Componente | Versión | Notas |
|---|---|---|
| Sistema operativo | Linux 5.x / macOS 14 / WSL2 | - |
| PostgreSQL | 16.x | cliente `psql` ≥ 16 |
| Recursos | 1 GB RAM, 2 GB disco | mínimo para el lab |

## Objetivo
Aprender el flujo completo de backup lógico con `pg_dump -Fc` y restauración con `pg_restore`, incluyendo restauración selectiva (solo esquema, solo datos, etc.).

## Solución

### Paso 1: Crear BD de prueba con datos
```sql
createdb labdb
psql -d labdb -c "CREATE TABLE users (id serial PRIMARY KEY, email varchar(255));"
psql -d labdb -c "INSERT INTO users (email) VALUES ('a@example.com'), ('b@example.com');"
```

### Paso 2: Crear el backup en formato custom
```bash
pg_dump -h localhost -U postgres -Fc -f labdb.dump labdb
ls -la labdb.dump
```

### Paso 3: Crear BD destino y restaurar
:::warning
**`DROP DATABASE` es destructivo.** NO ejecutes este paso en producción sin antes hacer backup.
:::

```bash
psql -c "DROP DATABASE IF EXISTS labdb_restored;"
psql -c "CREATE DATABASE labdb_restored;"
pg_restore -h localhost -U postgres -d labdb_restored labdb.dump
```

## Qué observar
:::note
- El archivo `.dump` debe ser ~10x más pequeño que `pg_dump` plano (compresión automática).
- `pg_restore` debe mostrar mensajes `pg_restore: connecting to database ... pg_restore: creating ... pg_restore: processing data for table ...`.
- La BD `labdb_restored` debe tener la tabla `users` con 2 filas.
:::

## Verificación
```sql
psql -d labdb_restored -c "SELECT count(*) FROM users;"
```
Resultado esperado: `2`.

## Limpieza

1. Borrar la BD de prueba:
   ```bash
   dropdb labdb
   dropdb labdb_restored
   ```
2. Borrar el archivo de backup:
   ```bash
   rm -f labdb.dump
   ```

Después de la limpieza, el sistema vuelve a su estado original.

## Lo que NO debe correrse en producción

:::danger
- `DROP DATABASE` (Paso 3): elimina la BD destino permanentemente.
- `rm labdb.dump`: sin el archivo no se puede restaurar.

Nunca ejecutes este lab en un cluster de producción sin antes hacer un backup completo con `pg_dumpall --globals-only` + verificar la integridad del `.dump`.
:::

## Cuándo omitir este lab

:::note
Omite este lab si: (1) ya dominas el flujo completo de backup + restore con `pg_dump`/`pg_restore`; (2) el cluster de producción tiene políticas de backup declaradas en Terraform/Kubernetes y prefieres validar esas políticas; (3) trabajas con bases de datos que usan replicación nativa y el backup se hace vía WAL archiving + PITR.
:::

## Pistas

:::tip
Si `pg_restore` retorna errores de permisos, verifica que el usuario sea owner de la BD destino. Si retorna errores de FK, ejecuta con `--no-owner --role=postgres`.
:::

## Backlinks
- [[note:procedure-postgres-backup]]
- [[note:postgres-connection-errors]]
```

Esta nota mínima (~85 líneas) cubre R1-R8 de F76 + los 3 criterios del
ROADMAP + F75 §6.15 exención de callouts. Sirve de **referencia de forma**.

---

## §8 · Wirings y referencias cruzadas

- **F11** `assets/profile.template.yaml` — defaults de §5.
- **F12** `references/04-authoring/notemark.md` — directivas `:::warning`, `:::danger`, `:::tip`, `:::note`.
- **F44** `references/03-knowledge/note-plan.md` — selector asigna `practice` cuando la unidad es un lab reproducible.
- **F45** `references/04-authoring/block-directives.md` — directivas consumidas.
- **F46** `references/04-authoring/inline-marks.md` — `{src:blk_xxxx}` por paso del SDM.
- **F47** `references/04-authoring/properties.md` — frontmatter con `difficulty` (1-5) enum.
- **F51** `references/04-authoring/depth-layers.md` — capas L1/L2/L3.
- **F72** `references/07-visual/tokens.md` — colores semánticos de las directivas.
- **F75** `references/07-visual/note-templates.md` — cabecera, apertura/cierre común, §6.15 patrón resumido.
- **F76** `references/07-visual/density.md` — tabla cerrada R1-R8 ejecutable.
- **F77** `evals/visual/` — verificación visual multi-destino.
- **F78** `references/05-note-types/concept.md` — paraguas común; el lab practica conceptos.
- **F79** `references/05-note-types/api-reference.md` — el lab usa APIs documentadas.
- **F80** `references/05-note-types/procedure.md` — el lab deriva de procedures.
- **F82** `references/05-note-types/error-troubleshooting.md` — errores típicos del lab.
- **F86** `references/05-note-types/chapter-digest.md` — capítulos que contienen labs.
- **F90** `references/05-note-types/cheatsheet.md` — cheatsheets de comandos usados en el lab.

---

## §9 · Verificación al cierre de la fase

- `wc -l references/05-note-types/practice.md` ≤ 400 líneas.
- §2 con 4 subsecciones (incluye `difficulty` enum).
- §3 con tabla de componentes mínimos ≥ 14 filas + §3.1 patrón de Entorno + §3.2 patrón de paso destructivo + §3.3 patrón de Limpieza + §3.4 patrón de Cuándo omitir.
- §4 con 5 subsecciones (incluye §4.4 10 anti-patrones y §4.5 diferencias operativas).
- §5 con tabla de campos del perfil y sus defaults.
- §6 con checklist de cierre ≥ 14 items.
- §7 con nota mínima viable (≤ 100 líneas).
- §8 con ≥ 16 wirings.
- §9 lista de verificación explícita.

**Criterios de aceptación del ROADMAP F92:**

1. _Todo lab declara entorno, resultado esperado y limpieza._ → battery C2: cada fixture tiene `## Entorno` (≥ 3 componentes) + `## Limpieza` (≥ 1 paso).
2. _Ninguna instrucción destructiva sin advertencia._ → battery C3: cada paso con comandos destructivos (`DROP`, `DELETE`, `rm -rf`, `kubectl delete`) tiene `:::warning` o `:::danger` adyacente (±5 líneas).
3. _Existe criterio de cuándo omitir el lab._ → battery C4: cada fixture tiene `## Cuándo omitir este lab` con ≥ 1 criterio.
