# `references/09-study/study-paths.md` — Rutas de estudio

> Documento normativo de la **Fase 104** `[ref]`. Define los **3
> objetivos cerrados** (`operar-hoy`, `entender-a-fondo`, `repasar`)
> mapeados a tipos de rutas generados desde el grafo de prerrequisitos
> (F39), la **forma canónica JSON de una ruta** con 5 campos
> (`domain`, `goal`, `note_path[]`, `estimated_minutes`, `checkpoints[]`),
> las **7 reglas duras R-P1 a R-P7**, y los algoritmos de los 2 scripts
> (`study_paths.py` con Q1-Q6; `study_paths_check.py` con V1-V4).
>
> F104 cierra los 3 criterios del ROADMAP §1727-1729:
> cada dominio tiene al menos dos rutas (§5 R-P1);
> respetan el orden de prerrequisitos (§5 R-P3 vía topological sort);
> cada ruta tiene puntos de verificación explícitos (§5 R-P4).
>
> **Cuándo cargar:** al planificar una ruta de estudio (operar hoy /
> entender a fondo / repasar); al revisar si una nota tiene propósito
> claro dentro de las rutas del corpus; al filtrar rutas por perfil
> de objetivo (F105).
>
> **Wirings:**
> - `references/03-knowledge/concept-graph.md` (F39) — `concept-graph.json`
>   provee las rutas `shortest` + `broadest` por dominio y `goal_concept_id`.
> - `references/03-knowledge/note-plan.md` (F44) — `note-plan.json` provee
>   el mapping `concept_id → note_id` + `depends_on[]`.
> - `references/04-authoring/properties.md` (F47) §5.20 — `reading-time-minutes`
>   alimenta el tiempo estimado. F104 añade §5.22 `study-path-goals` (opcional).
> - `references/05-note-types/practice.md` (F92) — los labs son la fuente
>   natural de puntos de verificación.
> - `references/09-study/self-evaluation.md` (F102) — `## Autoevaluación`
>   es checkpoint alternativo cuando no hay `practice` en el dominio.
> - `references/09-study/error-log.md` (F103) — el living-doc alimenta
>   la ruta `repasar` cuando existe.
> - `SKILL.md` §5.3 — wiring.

---

## §1 · Propósito y alcance

Tres problemas resueltos por F104:

1. **El estudiante no sabe por dónde empezar.** El grafo de prerrequisitos
   (F39) tiene ≥ 2 rutas por dominio y `goal_concept_id`, pero son rutas
   "frías": solo nodos y aristas. El estudiante necesita saber **qué
   objetivo persigue cada ruta** (operar vs entender vs repasar), **qué
   tiempo le costará** y **dónde verificar que avanza bien**. F104
   añade las 3 capas (objetivo + tiempo + checkpoint) sobre las rutas
   existentes.
2. **Las rutas no distinguen el "para ya" del "para después".** Un
   profesional que necesita usar PostgreSQL hoy no puede hacer el camino
   completo de comprensión. F104 introduce **3 objetivos cerrados** con
   estrategias diferenciadas: `operar-hoy` usa el camino más corto
   (Dijkstra); `entender-a-fondo` usa el camino más amplio (DFS); `repasar`
   consume el camino más corto + las entradas del living-doc de errores
   (F103) ordenadas por `review-next`.
3. **No hay forma de saber si la ruta "funciona".** El estudiante puede
   terminar una ruta y no saber si aprendió. F104 introduce **puntos de
   verificación explícitos** por ruta: tras visitar cierto paso, debe
   ejecutar un lab (`practice`, F92) o responder la sección
   `## Autoevaluación` (F102). La ruta es **auto-verificable**.

**Fuera de alcance:**

- Perfiles de objetivo (`interview`, `certification`, `work`) — F105.
  F104 entrega las 3 rutas genéricas; F105 las filtra por perfil.
- Algoritmo de rutas — F39 ya calcula `shortest` + `broadest`. F104
  las consume y las decora; **no** reimplementa Dijkstra/DFS.
- Generación de tarjetas — F103 + F62. F104 podría en una fase futura
  emitir un `study-deck.apkg` a partir de las 3 rutas, pero queda fuera.
- Modificación del note-plan — F104 lo consume tal cual.

---

## §2 · Los 3 objetivos cerrados

Tabla cerrada con los **3 objetivos** autoasignables. Cada uno tiene:
definición operativa, estrategia de ruta, perfil de uso, ejemplo.

| # | Objetivo | Definición operativa | Estrategia | Perfil de uso | Ejemplo |
|---|---|---|---|---|---|
| 1 | `operar-hoy` | Mínimo viable para usar la tecnología en producción: comandos, parámetros por defecto, errores típicos. | `shortest` (camino más corto por aristas). | Profesional con plazo. | "Necesito configurar PostgreSQL mañana; dame el camino mínimo para no romper nada." |
| 2 | `entender-a-fondo` | Comprensión completa del dominio: mecanismos, decisiones de diseño, comparativas, trade-offs. | `broadest` (DFS que prefiere visitar más nodos). | Estudiante con tiempo. | "Estoy aprendiendo Docker desde cero; quiero entender todos los componentes antes de usarlo." |
| 3 | `repasar` | Recordatorio enfocado en errores propios del estudiante + repetición espaciada de tarjetas prioritarias (F103). | `shortest` + entradas del living-doc ordenadas por `review-next` ascendente. | Cualquiera que tenga un living-doc. | "Tengo el living-doc `study/errors/postgresql.md` con 3 errores vencidos; quiero repasarlos antes de seguir." |

**Reglas algorítmicas S1-S3:**

- **S1** _Detección de objetivo_ — el CLI acepta `--goal operate-hoy | entender-a-fondo | repasar | all`. Default `all`. Si el valor no está en el enum cerrado, fail con `unknown-goal`.
- **S2** _Estrategia implícita_ — `operar-hoy` → `shortest`; `entender-a-fondo` → `broadest`; `repasar` → combinación de `shortest` con living-doc.
- **S3** _Cobertura_ — `operar-hoy` y `entender-a-fondo` siempre se emiten (si el dominio tiene ≥ 1 nodo). `repasar` solo si existe `study/errors/<domain>.md` (R-P7).

---

## §3 · Estructura de una ruta

### §3.1 · Plantilla JSON canónica

```json
{
  "domain": "postgresql",
  "goal": "operar-hoy",
  "note_path": [
    {
      "note_id": "postgres-basics",
      "step": 1,
      "depends_on": []
    },
    {
      "note_id": "postgres-mvcc",
      "step": 2,
      "depends_on": ["postgres-basics"]
    }
  ],
  "estimated_minutes": 90,
  "checkpoints": [
    {
      "after_step": 2,
      "type": "practice",
      "note_id": "postgres-lab-backup",
      "description": "Ejecutar el lab de pg_dump antes de continuar."
    },
    {
      "after_step": 5,
      "type": "auto-eval",
      "note_id": "postgres-mvcc",
      "section": "## Autoevaluación",
      "description": "Responder la pregunta de decisión sobre nivel de aislamiento."
    }
  ]
}
```

### §3.2 · Campos obligatorios

| Campo | Tipo | Descripción |
|---|---|---|
| `domain` | string | Slug del dominio (kebab-case). |
| `goal` | enum (3 valores) | `operar-hoy` \| `entender-a-fondo` \| `repasar`. |
| `note_path` | array | Notas en orden topológico. Cada item: `note_id`, `step` (int ≥ 1), `depends_on[]` (array de note_ids). |
| `estimated_minutes` | int ≥ 1 | Suma de `reading-time-minutes` de las notas en `note_path` (las que lo tengan; las sin se omiten con warning R-P6). |
| `checkpoints` | array | ≥ 1 item. Cada item: `after_step` (int ≥ 1), `type` (`practice` \| `auto-eval`), `note_id`, `description`. |

**Ejemplo positivo completo:**

```json
{
  "domain": "docker",
  "goal": "entender-a-fondo",
  "note_path": [
    {"note_id": "docker-basics", "step": 1, "depends_on": []},
    {"note_id": "docker-images", "step": 2, "depends_on": ["docker-basics"]},
    {"note_id": "docker-compose", "step": 3, "depends_on": ["docker-images"]},
    {"note_id": "docker-volumes", "step": 4, "depends_on": ["docker-compose"]},
    {"note_id": "docker-networking", "step": 5, "depends_on": ["docker-compose"]}
  ],
  "estimated_minutes": 145,
  "checkpoints": [
    {
      "after_step": 3,
      "type": "practice",
      "note_id": "docker-lab-compose",
      "description": "Levantar el stack web+db y verificar conectividad."
    }
  ]
}
```

**Ejemplo negativo (NO usar):**

```json
{
  "domain": "docker",
  "goal": "operar-hoy",
  "note_path": [
    {"note_id": "docker-compose", "step": 1, "depends_on": ["docker-basics"]}
  ]
}
```

Este ejemplo viola R-P3 (`docker-compose` aparece antes de `docker-basics` en el
orden pero la dependencia es la inversa — el orden topológico no la respeta)
y R-P4 (sin checkpoints).

---

## §4 · Lista cerrada de los 3 objetivos

Enumeración compacta de los 3 objetivos cerrados:

```
1.  operar-hoy        (mínimo viable, camino más corto)
2.  entender-a-fondo  (camino completo, camino más amplio)
3.  repasar           (recordatorio + errores propios)
```

**Reglas duras:**

- **R-O1** _Enum cerrado_ — los 3 objetivos son los únicos valores válidos
  para `goal`. Cualquier otro valor abre F104-bis.
- **R-O2** _Mapeo a estrategia_ — `operar-hoy` → `shortest`;
  `entender-a-fondo` → `broadest`; `repasar` → combinación.
- **R-O3** _Mínimo 2 por dominio_ — cada dominio emite `operar-hoy` +
  `entender-a-fondo` siempre (≥ 2 rutas, R-P1). `repasar` es opcional
  condicional a F103 (R-P7).

---

## §5 · Reglas duras (R-P1 a R-P7)

| ID | Regla | Si se omite… |
|---|---|---|
| **R-P1** | Cada dominio tiene ≥ 2 rutas (ROADMAP #1). | El validador `study_paths_check.py` falla con `insufficient-routes`. |
| **R-P2** | ≥ 1 ruta `operar-hoy` por dominio (mínimo viable para no quedar sin ruta usable). | El validador falla con `no-operate-hoy-route`. |
| **R-P3** | Cada ruta respeta el orden de prerrequisitos del note-plan: para cada paso `i`, todos los `note_id` en `depends_on[]` aparecen en pasos anteriores (topological sort estricto). | El validador falla con `prerequisite-violation`. |
| **R-P4** | Cada ruta tiene ≥ 1 punto de verificación explícito (`checkpoints[]` con `type: practice | auto-eval`). | El validador falla con `no-checkpoint`. |
| **R-P5** | Cada `note_id` en `note_path` existe en `knowledge/note-plan.json::notes[]`. | El validador falla con `note-not-in-plan`. |
| **R-P6** | `estimated_minutes` se calcula como `sum(reading-time-minutes)` de las notas en `note_path` que lo tengan; las notas sin `reading-time-minutes` se omiten con warning (no error). | El validador warning `missing-reading-time`. |
| **R-P7** | La ruta `repasar` solo se emite si existe `study/errors/<domain>.md`. Sin living-doc, solo `operar-hoy` + `entender-a-fondo` (≥ 2 rutas, cumple R-P1). | El script omite `repasar` silenciosamente. |

---

## §6 · Algoritmo del script `scripts/study/study_paths.py`

**Ubicación:** `skill/notemartin-study-notes/scripts/study/study_paths.py`.
**CLI:** `--domain <slug>` / `--goal operate-hoy|entender-a-fondo|repasar|all` (default `all`)
/ `--workdir <dir>` (default `.`) / `--format md|json` (default `md`) /
`--errors-dir <dir>` (default `study/errors/`).
**Salida:** Markdown (default) o JSON (`--json`).
**Exit codes:** 0 = OK, 1 = alguna ruta falta criterios (≥ 2, prerrequisitos,
checkpoints) — solo si `--strict` está activo, 2 = error de uso.

**Seis reglas Q1-Q6:**

### Q1 — Lectura del grafo

- Cargar `knowledge/concept-graph.json`. Si no existe, fail con
  `concept-graph-not-found`.
- Extraer las rutas existentes (`routes[]`) por dominio y
  `goal_concept_id` + `strategy`. Filtrar por `--domain` si se pasa.

### Q2 — Lectura del note-plan

- Cargar `knowledge/note-plan.json`. Si no existe, fail con
  `note-plan-not-found`.
- Construir mapa `concept_id → note_id` desde `notes[].concept_ids[]`
  (F44 declara este campo).
- Construir mapa `note_id → depends_on[]` desde `notes[].depends_on[]`.

### Q3 — Tiempo estimado

- Para cada `note_id` en el `note_path`, buscar `reading-time-minutes`
  en `ir/<note_id>.json` (campo `frontmatter.reading-time-minutes`) o
  en `notemark/<note-id>.nm` (frontmatter YAML).
- Si no se encuentra, omitir la nota de la suma (warning R-P6).
- `estimated_minutes = sum(reading-time-minutes)`.

### Q4 — Emisión de las 3 rutas

- Para cada dominio:
  - `operar-hoy`: tomar la ruta `shortest` con `goal_concept_id` que
    tenga el mayor `out_degree` del dominio (el nodo que "abre" más
    caminos). Si el dominio tiene 1 solo nodo, usar ese nodo como
    path completo (1 paso). Resolver `concept_id → note_id` desde Q2.
    Aplicar topological sort: para cada paso `i`, sus `depends_on[]`
    deben aparecer en pasos anteriores (R-P3).
  - `entender-a-fondo`: tomar la ruta `broadest` para el mismo
    `goal_concept_id`. Si `broadest` coincide con `shortest` (dominio
    con 1 nodo), usar el mismo `shortest` y marcar la ruta como
    `coincides_with_shortest: true`.
  - `repasar`: solo si existe `study/errors/<domain>.md` (R-P7). Tomar
    la ruta `shortest` y añadir, tras cada paso, las entradas del
    living-doc con `review-next < today`, ordenadas por `review-next`
    ascendente. El `step` se incrementa por entrada del living-doc;
    el `note_id` es el `[[note:id]]` canónico referenciado en
    `### Corrección` de la entrada.

### Q5 — Puntos de verificación

- Para cada ruta, generar `checkpoints[]`:
  - Si el dominio tiene ≥ 1 nota `practice` (F92) en el `note_path`,
    usar `type: practice` para el primer nodo con `practice` disponible;
    el `after_step` es el step de ese nodo.
  - Si no hay `practice`, usar `type: auto-eval` (F102): el primer nodo
    con sección `## Autoevaluación` en el `note_path`. `note_id` es el
    de ese nodo; `section: "## Autoevaluación"`.
  - R-P4 exige ≥ 1 checkpoint; si no hay ninguno disponible, emitir
    warning R-P4 (no error en `--strict` por defecto).

### Q6 — Emisión

- Markdown:
  ```
  # Rutas de estudio — <domain>
  
  ## operar-hoy
  
  **Tiempo estimado:** N min
  
  1. [[note:postgres-basics]]
  2. [[note:postgres-mvcc]] (depends on: postgres-basics)
  ...
  
  **Checkpoints:**
  - Tras paso 2: ejecutar lab `postgres-lab-backup`.
  
  ## entender-a-fondo
  ...
  
  ## repasar (3 entradas del living-doc)
  ...
  ```
- JSON: lista de rutas con el shape de §3.1.

---

## §7 · Algoritmo del validador `scripts/validate/study_paths_check.py`

**Ubicación:** `skill/notemartin-study-notes/scripts/validate/study_paths_check.py`.
**CLI:** `--routes <path>` (ruta al archivo JSON de rutas generadas) /
`--json` / `--strict`.
**Salida:** Markdown (default) o JSON (`--json`).
**Exit codes:** 0 = OK, 1 = violación, 2 = error de uso.

**Cuatro reglas V1-V4:**

### V1 — ≥ 2 rutas por dominio (ROADMAP #1)

- Contar rutas por `domain` en el archivo JSON. Si algún dominio tiene
  < 2, falla con `insufficient-routes`.

### V2 — Orden topológico (ROADMAP #2)

- Para cada ruta, verificar que para cada paso `i`, todos los
  `note_id` en `depends_on[]` aparecen en pasos con `step < i`. Si
  algún paso viola, falla con `prerequisite-violation` indicando el
  paso concreto.

### V3 — Checkpoints explícitos (ROADMAP #3)

- Para cada ruta, contar items en `checkpoints[]`. Si es 0, falla con
  `no-checkpoint`.

### V4 — Notas en el note-plan

- Para cada `note_id` en `note_path`, verificar que existe en el
  note-plan (si se pasa `--note-plan`). Si falta, falla con
  `note-not-in-plan`.

---

## §8 · Wirings y referencias cruzadas

| Fase | Archivo | Relación |
|---|---|---|
| F39 | `references/03-knowledge/concept-graph.md` | `concept-graph.json` provee las rutas `shortest` + `broadest` por dominio. F104 añade los 3 objetivos como capa decorativa. |
| F44 | `references/03-knowledge/note-plan.md` | `note-plan.json` provee el mapping `concept_id → note_id` + `depends_on[]`. F104 lo consume tal cual. |
| F45 | `references/04-authoring/block-directives.md` §10 | Las notas del `note_path` usan bloques `:::collapsible`, `:::question`, etc. |
| F47 | `references/04-authoring/properties.md` §5.20 | `reading-time-minutes` alimenta el tiempo estimado (R-P6). |
| F47 | `references/04-authoring/properties.md` §5.22 | Nueva propiedad opcional `study-path-goals`. |
| F51 | `references/04-authoring/depth-layers.md` | Las notas del `note_path` mantienen su layer markers (L1/L2/L3). |
| F78-F92 | `references/05-note-types/*.md` | Los 15 tipos son las unidades del `note_path`. |
| F92 | `references/05-note-types/practice.md` | Los labs `practice` son la fuente natural de checkpoints (V3). |
| F102 | `references/09-study/self-evaluation.md` | `## Autoevaluación` es checkpoint alternativo cuando no hay `practice` (V3). |
| F103 | `references/09-study/error-log.md` | El living-doc alimenta la ruta `repasar` (R-P7). |
| F105 | (futuro) `references/09-study/goal-profiles.md` | Filtrar las 3 rutas por perfil (`interview` / `certification` / `work`). |
| F112 | (futuro) suite consolidada | `study_paths_check.py` se invocará desde la suite. |
| F115 | (futuro) reporte de calidad | El reporte cita las rutas por dominio y su cobertura. |

**Invocación desde SKILL.md:** la fila de `references/09-study/study-paths.md`
aparece en §5.3 con la entrada _"Al planificar una ruta de estudio
(operar hoy / entender a fondo / repasar)"_, entre la fila de
`error-log.md` (F103) y la fila de F105.

---

## §9 · Verificación al cierre de la fase

Los **3 criterios del ROADMAP** se verifican algorítmicamente:

| Criterio | Cómo se verifica |
|---|---|
| **C1** Cada dominio tiene al menos dos rutas | `evals/study-paths-sample/run_eval.py` C8 verifica que cada dominio del fixture emite ≥ 2 rutas; el validador `study_paths_check.py` aplica V1 (falla con `insufficient-routes`). |
| **C2** Respetan el orden de prerrequisitos | C6 verifica el orden topológico del fixture; el validador aplica V2 (falla con `prerequisite-violation`). |
| **C3** Cada ruta tiene puntos de verificación explícitos | C7 verifica que cada ruta del fixture tiene ≥ 1 checkpoint; el validador aplica V3 (falla con `no-checkpoint`). |

Criterios derivados cubiertos por el eval:

- **D1.** `wc -l study-paths.md` ≤ 600 (INV-02).
- **D2.** 9 secciones canónicas §1-§9 presentes.
- **D3.** §4 enum cerrado con exactamente 3 objetivos.
- **D4.** Wirings cerrados (alias C10).
