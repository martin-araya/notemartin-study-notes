# `references/09-study/goal-profiles.md` — Perfiles de objetivo

> Documento normativo de la **Fase 105** `[ref]`. Define los **3 perfiles
> de objetivo cerrados** (`interview`, `certification`, `work`),
> ortogonales a `use_case_profile` (F11), que **añaden** secciones y/o
> **relajan** reglas R-* sobre el corpus base; el **principio INV-GP1**
> de no-reducción garantiza que ningún perfil quita cobertura; el
> reporte de cobertura por `objetivo_id` para `certification`; y los
> algoritmos de los 2 scripts (`goal_profiles.py` con P1-P4;
> `goal_profile_check.py` con V1-V5).
>
> F105 cierra los 3 criterios del ROADMAP §1737-1739:
> cada perfil declara qué añade y qué relaja (§2);
> ninguno reduce la cobertura (INV-GP1 en §3);
> `certification` permite consultar cobertura por objetivo (§4 + V2).
>
> **Cuándo cargar:** al configurar el perfil de objetivo (`interview` /
> `certification` / `work`) en `profile.yaml`; al sobrescribir el perfil
> por nota (`goal-profile-override`); al consultar cobertura por
> `objetivo_id` (`goal_profile_check.py --by-objective`).
>
> **Wirings:**
> - `assets/profile.template.yaml` (F11) — propiedad nueva `goal_profile`
>   + bloque `certification.objectives[]`.
> - `references/04-authoring/properties.md` (F47) §5.23 + §5.24 — añade
>   `goal-profile-override` + `certification-objective` (INV-P1 ahora 24).
> - `references/03-knowledge/concept-graph.md` (F39) — consume las rutas.
> - `references/03-knowledge/note-plan.md` (F44) — consume `notes[]`.
> - `references/05-note-types/concept.md` (F78) — checklist extendido con
>   F105-1 + F105-2.
> - `references/06-writing/anti-patterns.md` (F100) — AP17, AP18, AP19.
> - `references/09-study/self-evaluation.md` (F102) — F105 no modifica
>   F102; los checkpoints de F104 (R-P4) siguen aplicando.
> - `references/09-study/error-log.md` (F103) — F105 no modifica F103;
>   `interview` puede pedir "errores comunes" como `adds` opcional.
> - `references/09-study/study-paths.md` (F104) — F105 filtra las 3 rutas
>   por perfil; las secciones `adds[]` se inyectan tras la ruta.
> - `SKILL.md` §5.3 — wiring.

---

## §1 · Propósito y alcance

Tres problemas resueltos por F105:

1. **Las notas son universales pero el objetivo del estudiante no.** El
   corpus base (F78-F92 + F100 + F102 + F103 + F104) está pensado para
   cubrir las necesidades de cualquier estudiante. Pero un profesional
   preparando una entrevista técnica necesita trade-offs explícitos;
   un estudiante de certificación oficial necesita cobertura por
   `objetivo_id`; un operador que necesita usar la tecnología el lunes
   necesita prosa con contexto operacional. F105 introduce **3 perfiles
   de objetivo** que adaptan la salida del agente sin modificar el
   corpus base.
2. **No hay forma de declarar "qué añade un perfil".** Cada perfil debe
   ser explícito: añade tales secciones, relaja tales reglas R-*,
   respeta la cobertura base. F105 cierra esto con la regla R-G2: cada
   perfil declara `adds[]` y `relaxes[]` en una tabla cerrada.
3. **Para certificación no hay forma de mapear notas a objetivos
   oficiales.** Los exámenes externos (CKAD, AWS Solutions Architect,
   etc.) declaran objetivos en su documentación. Sin mapeo, no se sabe
   qué nota cubre qué objetivo. F105 introduce la propiedad opcional
   `certification-objective` (enum array) en el frontmatter + la
   consulta `--by-objective <id>` del validador.

**Distinción fundamental: `use_case_profile` vs `goal_profile`.**

| Campo | Pregunta que responde | Fase | Valores |
|---|---|---|---|
| `use_case_profile` | ¿Cómo se escriben las notas? (estilo de prosa) | F11 | `study` / `reference` / `hybrid` |
| `goal_profile` | ¿Para qué usas las notas? (objetivo del estudiante) | F105 | `hybrid` / `interview` / `certification` / `work` |

Ambos perfiles conviven en `profile.yaml`. Un `profile.yaml` válido puede
tener `use_case_profile: study` + `goal_profile: interview` simultáneamente.

**Fuera de alcance:**

- Nuevos `note-types` (los 15 cerrados siguen siendo los únicos valores
  canónicos del enum; F105 no añade).
- Cambios a `use_case_profile` (F11 sigue siendo el dueño).
- Modificar las 9 invariantes (INV-01..INV-09) ni INV-* de las fases
  previas. F105 añade **INV-GP1** (no-reducción) en §3 de este doc; la
  integración en la tabla global de invariantes queda para F115.
- Generación de tarjetas desde el reporte por objetivo (eso es F62).

---

## §2 · Los 3 perfiles cerrados

Tabla cerrada con los **3 perfiles de objetivo** autoasignables. Cada
uno tiene: `goal_profile` (string), `definition` (qué prioriza),
`adds[]` (secciones adicionales), `relaxes[]` (reglas R-* que se
relajan opcionalmente con justificación), `audience` (quién lo usa),
ejemplo.

| # | `goal_profile` | Definición | `adds[]` | `relaxes[]` | Audience | Ejemplo |
|---|---|---|---|---|---|---|
| 1 | `interview` | Preparación de entrevista técnica: trade-offs explícitos + explicación oral. | `## Decisiones de diseño` (en concept + architecture; ya obligatoria en architecture F83); `## Explicación oral` (1 párrafo con respuesta a "¿Cómo lo explicarías en una entrevista?"). | R3 densidad `{src:}` ≥ 0.80 → ≥ 0.70 — la prosa argumentativa gana a la prosa anclada. | Profesional que prepara entrevista. | "Tengo una entrevista para Senior Backend sobre PostgreSQL; dame las decisiones de diseño y cómo explicarlas en voz alta." |
| 2 | `certification` | Preparación de certificación oficial: cobertura verificable por `objetivo_id`. | `## Objetivos oficiales` (tabla con `objetivo_id` + `cobertura: covered\|partial\|missing`); `## Cobertura por objetivo` (link al reporte generado por `goal_profile_check.py --by-objective`). | R5 estructura libre: la tabla de objetivos puede ser una sola columna. | Estudiante de certificación. | "Estoy preparando el CKAD; dame las notas que cubren el objetivo `ckad-core-1` (Core Concepts 13 %)." |
| 3 | `work` | Operatividad inmediata: prosa con contexto operacional + comandos verbatim. | (ninguna; el perfil no añade secciones). | R1 TL;DR ≤ 60 palabras → ≤ 100 palabras — el operador necesita contexto amplio. | Operador que necesita usar la tecnología ya. | "Voy a configurar un cluster de Kubernetes el lunes; dame los pasos con contexto operacional y sin floritura." |

**Reglas algorítmicas S1-S4:**

- **S1** _Detección del perfil activo_ — el script acepta `--profile <hybrid|interview|certification|work>`. Default: `hybrid`. Si el valor no está en el enum cerrado, fail con `unknown-profile` (R-G1 + V5).
- **S2** _Aplicación de `adds[]`_ — al emitir Markdown, el script añade las secciones de `adds[]` **al final** de la nota (no reemplaza las existentes).
- **S3** _Aplicación de `relaxes[]`_ — el script documenta las reglas relajadas en una cabecera del output. El validador sigue aplicando las reglas no relajadas (V1 + R-G3).
- **S4** _Perfil `hybrid`_ — aplica los `adds[]` de los 3 perfiles canónicos, pero solo los `relaxes[]` que aplican al `study-path-goals` declarado (F104 §5.22). Sin `study-path-goals`, default `operate-hoy` + `entender-a-fondo`.

---

## §3 · Principio de no-reducción (INV-GP1)

**Definición operativa:** la cobertura base de una nota (las secciones
obligatorias de su `note-type` según F78-F92 + las reglas R1-R8 de F76)
se mantiene **íntegra** bajo los 3 perfiles. Los perfiles pueden:

- ✅ Añadir secciones (`## Decisiones de diseño`, `## Explicación oral`,
  `## Objetivos oficiales`, `## Cobertura por objetivo`).
- ✅ Relajar reglas R-* opcionales (R1 TL;DR, R3 densidad, R5 estructura).
- ❌ **Nunca** quitar secciones obligatorias del `note-type`.
- ❌ **Nunca** relajar reglas R-* que afecten la fidelidad (INV-08
  cobertura `must-keep`, INV-09 literales verbatim, INV-P6 ISO 8601).
- ❌ **Nunca** modificar la forma canónica del frontmatter (los 24
  campos cerrados de F47).

**Detector algorítmico (V1):**

Para cada nota en el corpus:
1. Contar las secciones obligatorias del `note-type` declarado (de
   F78-F92). Ej. `concept` requiere `## TL;DR`, `## Mecanismo`.
2. Contar las secciones presentes en la nota (regex `^## ` ).
3. Si una sección obligatoria falta → **violación** (`missing-mandatory-section`).
4. Si una sección obligatoria falta **solo bajo perfil activo** → el
   validador verifica que el perfil activo no la excluye. Si la
   excluye, **violación** (`profile-reduces-coverage`, R-G3).

**Relajaciones permitidas (R-G* + INV-GP1):**

| Regla base | Relajación permitida | Razón |
|---|---|---|
| R1 (TL;DR ≤ 60 palabras) | `work` permite ≤ 100 palabras (R-G6) | Operador necesita contexto amplio. |
| R3 (`{src:}` ≥ 0.80) | `interview` permite ≥ 0.70 (R-G4) | Prosa argumentativa prima sobre anclada. |
| R5 (estructura libre) | `certification` permite tabla de objetivos en una sola columna (R-G5) | Cobertura verificable > estructura estética. |

Todas las demás reglas R-* se mantienen estrictas (R2, R4, R6, R7, R8,
INV-08, INV-09, INV-P6).

---

## §4 · Estructura del reporte de cobertura por objetivo (solo `certification`)

### §4.1 · Plantilla JSON canónica

```json
{
  "objetivo_id": "ckad-core-1",
  "description": "Core Concepts (13 %)",
  "notas": [
    {
      "note_id": "k8s-pods",
      "concept_ids": ["k8s-pod-basics"],
      "depends_on": [],
      "contribution": "covers",
      "evidence": ["## Mecanismo › §1", "## Procedimiento › §2"]
    },
    {
      "note_id": "k8s-services",
      "concept_ids": ["k8s-svc-basics"],
      "depends_on": ["k8s-pods"],
      "contribution": "partial",
      "evidence": ["## Mecanismo › §1"]
    }
  ],
  "coverage_ratio": 0.85,
  "status": "covered"
}
```

### §4.2 · Campos obligatorios

| Campo | Tipo | Descripción |
|---|---|---|
| `objetivo_id` | string | Slug kebab-case del objetivo externo (declarado en `profile.yaml::certification.objectives[]`). |
| `description` | string | Descripción del objetivo (de `profile.yaml`). |
| `notas` | array | Notas que cubren el objetivo. Cada item: `note_id`, `concept_ids[]`, `depends_on[]`, `contribution` (`covers` \| `partial`), `evidence[]` (anchor en el IR). |
| `coverage_ratio` | decimal 0..1 | `notas_con_contribution=covers / total_objetivo`. |
| `status` | enum (3) | `covered` (ratio ≥ 0.80), `partial` (ratio 0.40-0.79), `missing` (ratio < 0.40). |

### §4.3 · Lista cerrada de `objetivo_id`

Los `objetivo_id` válidos se declaran en `profile.yaml`:

```yaml
goal_profile: certification
certification:
  objectives:
    - id: "ckad-core-1"
      description: "Core Concepts (13 %)"
    - id: "ckad-core-2"
      description: "Configuration (18 %)"
    - id: "psql-admin-1"
      description: "Architecture and Design (15 %)"
```

Si `goal_profile == certification` y `profile.yaml::certification.objectives[]`
no está declarado, el script `goal_profile_check.py --by-objective`
falla con `no-objectives-declared`.

---

## §5 · Reglas duras (R-G1 a R-G7)

| ID | Regla | Si se omite… |
|---|---|---|
| **R-G1** | Los 3 perfiles canónicos son los únicos valores válidos de `goal_profile`: `hybrid`, `interview`, `certification`, `work`. Cualquier otro valor abre F105-bis. | El validador V5 falla con `unknown-profile`. |
| **R-G2** | Cada perfil declara explícitamente `adds[]` (array de secciones, máx 2 entradas) y `relaxes[]` (array de reglas R-*, máx 2 entradas, todas justificadas). | El validador V4 falla con `adds-too-many` o `relaxes-too-many`. |
| **R-G3** | Ningún perfil reduce cobertura (INV-GP1). | El validador V1 falla con `profile-reduces-coverage`. |
| **R-G4** | `interview` añade `## Decisiones de diseño` + `## Explicación oral` a notas `concept` + `architecture`. | El validador V1 falla con `missing-section-for-interview`. |
| **R-G5** | `certification` añade `## Objetivos oficiales` + `## Cobertura por objetivo` a cualquier nota del corpus. | El validador V1 falla con `missing-section-for-certification`. |
| **R-G6** | `work` no añade secciones; relaja R1 a ≤ 100 palabras (TL;DR con contexto operacional). | El validador V1 falla con `missing-section-for-work` (no aplica; `work` no añade secciones). |
| **R-G7** | `certification` permite consultar cobertura por objetivo vía `goal_profile_check.py --by-objective <objetivo_id>`. | El validador V2 falla con `no-objectives-declared` o `unknown-objective`. |

---

## §6 · Algoritmo del script `scripts/study/goal_profiles.py`

**Ubicación:** `skill/notemartin-study-notes/scripts/study/goal_profiles.py`.
**CLI:** `--profile <hybrid|interview|certification|work>` (default `hybrid`)
/ `--input <path>` (default `study-paths/<domain>.json`) /
`--output <path>` (default stdout) / `--format md|json` /
`--by-objective <objetivo_id>` (solo con `--profile certification`).
**Salida:** Markdown (default) o JSON (`--json`).
**Exit codes:** 0 = OK, 1 = perfil desconocido o violación R-G2/R-G3, 2 = error de uso.

**Cuatro reglas P1-P4:**

### P1 — Lectura del perfil activo

- Lee el perfil activo desde `--profile` (default `hybrid`).
- Si `--profile certification`, carga adicionalmente `profile.yaml` para
  obtener `certification.objectives[]`. Si `--profile certification` y
  no hay objetivos declarados, fail con `no-objectives-declared`.

### P2 — Lectura del input

- Lee el input JSON desde `--input` (producido por F104 `study_paths.py
  --format json`). El input tiene la forma:
  ```json
  [{"domain": "...", "goal": "...", "note_path": [...], "estimated_minutes": ..., "checkpoints": [...]}, ...]
  ```
- Si el archivo no existe, fail con `input-not-found`.

### P3 — Filtro por perfil + secciones adicionales

- Para cada ruta del input, aplica el perfil activo:
  - `interview`: añade al final de cada nota (en el output Markdown) las
    secciones declaradas en `adds[]` (si la nota no las tiene).
  - `certification`: añade `## Objetivos oficiales` con la tabla de
    objetivos declarados; si `--by-objective <id>` está activo, filtra
    solo las notas con `certification-objective` que incluya `<id>`.
  - `work`: no añade secciones; solo marca la cabecera "R1 relajada:
    TL;DR ≤ 100 palabras".
  - `hybrid`: aplica los 3 perfiles en modo light (solo secciones
    `adds[]` de los 3, sin relajaciones).

### P4 — Emisión

- Markdown: rutas filtradas + secciones `adds[]` inyectadas al final de
  cada nota (formato `## ...`) + cabecera con perfil activo.
- JSON: lista de rutas + `applied_profile` + lista de `added_sections`.

---

## §7 · Algoritmo del validador `scripts/validate/goal_profile_check.py`

**Ubicación:** `skill/notemartin-study-notes/scripts/validate/goal_profile_check.py`.
**CLI:** `--profile <hybrid|interview|certification|work>` /
`--workdir <dir>` (default `.`) / `--json` / `--strict` /
`--by-objective <objetivo_id>` (solo con `--profile certification`).
**Salida:** Markdown (default) o JSON (`--json`).
**Exit codes:** 0 = OK, 1 = violación, 2 = error de uso.

**Cinco reglas V1-V5:**

### V1 — No-reducción de cobertura (R-G3 + INV-GP1)

- Para cada nota en el corpus (`<workdir>/notemark/`):
  - Determinar `note-type` (de frontmatter).
  - Cargar las secciones obligatorias del note-type (de F78-F92).
  - Cargar las secciones presentes (regex `^## `).
  - Si una sección obligatoria falta → violación `missing-mandatory-section`.
  - Si el perfil activo añade secciones declaradas en `adds[]` y la nota
    NO las tiene → violación `missing-profile-section`.

### V2 — Coherencia del reporte por objetivo (R-G7)

- Si `--profile certification --by-objective <id>`:
  - Cargar `profile.yaml::certification.objectives[]`.
  - Si la lista está vacía → violación `no-objectives-declared`.
  - Si el `id` no está en la lista → violación `unknown-objective`.
  - Si el `id` está, recorrer las notas del corpus:
    - Si la nota tiene `certification-objective` que incluya `<id>` →
      sumar a `covers` (contribution=`covers`) o `partial` (contribution=`partial`).
    - Calcular `coverage_ratio = covers / total_objetivo`.
    - Determinar `status` (`covered` ≥ 0.80, `partial` 0.40-0.79, `missing` < 0.40).

### V3 — Notas en el note-plan

- Si `--workdir` tiene `knowledge/note-plan.json`, verificar que cada
  nota del corpus está en `notes[]`. Si falta → violación `note-not-in-plan`.

### V4 — Validación de `adds[]` y `relaxes[]`

- Cargar el catálogo de perfiles (de §2).
- Verificar que cada `adds[]` tiene ≤ 2 entradas (R-G2).
- Verificar que cada `relaxes[]` tiene ≤ 2 entradas y todas están
  justificadas (R-G2).

### V5 — `goal_profile` ∈ enum cerrado (R-G1)

- Si `--profile` no está en `{hybrid, interview, certification, work}`
  → violación `unknown-profile` (R-G1).

---

## §8 · Wirings y referencias cruzadas

| Fase | Archivo | Relación |
|---|---|---|
| F11 | `assets/profile.template.yaml` | Añade bloque `goal_profile` + `certification.objectives[]`. |
| F39 | `references/03-knowledge/concept-graph.md` | `concept-graph.json` provee rutas (consumidas por F104 → F105). |
| F44 | `references/03-knowledge/note-plan.md` | `note-plan.json` consumido por V3. |
| F47 | `references/04-authoring/properties.md` §5.23 + §5.24 | Nuevas propiedades `goal-profile-override` + `certification-objective`. INV-P1 ahora 24 propiedades. |
| F78 | `references/05-note-types/concept.md` §6 | Checklist extendido con F105-1 + F105-2. |
| F82 | `references/05-note-types/error-troubleshooting.md` | Puede heredar F105-2 si `goal_profile == certification`. |
| F83 | `references/05-note-types/architecture.md` | `## Decisiones de diseño` ya es obligatoria (F83 §2); F105 la reitera para `interview` (R-G4). |
| F92 | `references/05-note-types/practice.md` | `practice` no se afecta por F105 (es meta-documental). |
| F100 | `references/06-writing/anti-patterns.md` §2 | AP17, AP18, AP19 específicos de F105 (lista cerrada de 19 AP). |
| F102 | `references/09-study/self-evaluation.md` | Sin cambios. F105 no toca F102. |
| F103 | `references/09-study/error-log.md` | Sin cambios. `interview` puede pedir "errores comunes" como `adds[]` opcional por nota. |
| F104 | `references/09-study/study-paths.md` | F105 filtra las 3 rutas por perfil + inyecta `adds[]`. |
| F112 | (futuro) suite consolidada | `goal_profile_check.py` se invocará desde la suite. |
| F115 | (futuro) reporte de calidad | El reporte cita la cobertura por objetivo del corpus. |
| F118 | (futuro) evals | Criterios del ROADMAP §1737-1739 cubiertos por F105. |

**Invocación desde SKILL.md:** la fila de `references/09-study/goal-profiles.md`
aparece en §5.3 con la entrada _"Al configurar el perfil de objetivo
(interview / certification / work) o consultar cobertura por objetivo"_,
entre la fila de `study-paths.md` (F104) y la fila de F106.

---

## §9 · Verificación al cierre de la fase

Los **3 criterios del ROADMAP** se verifican algorítmicamente:

| Criterio | Cómo se verifica |
|---|---|
| **C1** Cada perfil declara qué añade y qué relaja | `evals/goal-profiles-sample/run_eval.py` C2 verifica que §2 tabla cerrada tiene los 3 perfiles con `adds[]` y `relaxes[]` declarados; `goal_profile_check.py --profile <p>` aplica V4 (R-G2). |
| **C2** Ninguno reduce la cobertura | C3 verifica INV-GP1; `goal_profile_check.py` aplica V1 (R-G3) sobre el corpus fixture. |
| **C3** `certification` permite consultar cobertura por objetivo | C4 verifica §4 plantilla JSON; `goal_profile_check.py --profile certification --by-objective <id>` aplica V2 (R-G7). |

Criterios derivados cubiertos por el eval:

- **D1.** `wc -l goal-profiles.md` ≤ 600 (INV-02).
- **D2.** 9 secciones canónicas §1-§9 presentes.
- **D3.** §2 enum cerrado con exactamente 3 perfiles.
- **D4.** Wirings cerrados (alias C14).
