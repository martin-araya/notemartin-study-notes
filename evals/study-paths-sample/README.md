# `evals/study-paths-sample/` — Fase 104 `Rutas de estudio`

Eval de la Fase 104 — generación de rutas de estudio desde el grafo de
prerrequisitos (F39) con **3 objetivos cerrados** (`operate-hoy`,
`entender-a-fondo`, `repasar`), **≥ 2 rutas por dominio**, **orden
topológico** que respeta los prerrequisitos del note-plan (F44),
**tiempo estimado** desde `reading-time-minutes` (F47 §5.20), y
**puntos de verificación** (`practice` o `auto-eval`).

## Estructura

| Archivo / carpeta | Rol |
|---|---|
| `build_fixtures.py` | Genera `fixtures/` con un mini-corpus: 2 dominios (`postgresql`, `docker`), 8 conceptos en el grafo, 10 notas NoteMark (concept + procedure + practice + configuration), `concept-graph.json` con ≥ 6 rutas, `note-plan.json` con 10 notas + `depends_on`, y `study/errors/error-log-postgresql.md` (F103) para alimentar la ruta `repasar`. |
| `run_eval.py` | Batería de 17 sub-criterios (3 ROADMAP + 3 estructura + 5 scripts + 1 wirings + 3 density + 3 derivados + 1 alias). |
| `fixtures/` | Corpus generado por `build_fixtures.py`. |
| `fixtures/knowledge/concept-graph.json` | Grafo con 8 nodos, 6 aristas, 6 rutas (2 dominios × 2 estrategias + 1 goal extra). |
| `fixtures/knowledge/note-plan.json` | 10 notas con `concept_ids`, `depends_on`, `study-path-goals`. |
| `fixtures/notemark/*.nm` | 10 notas (5 PostgreSQL + 5 Docker) con `reading-time-minutes` y `## Autoevaluación` en las concept. |
| `fixtures/study/errors/error-log-postgresql.md` | Living-doc con 2 errores (F103). |

## Modo de uso

```bash
# Regenera fixtures y ejecuta el eval.
python3 evals/study-paths-sample/build_fixtures.py --force
python3 evals/study-paths-sample/run_eval.py

# Solo evalúa (asume fixtures ya generadas).
python3 evals/study-paths-sample/run_eval.py
```

## Batería (17 sub-criterios)

### Criterios ROADMAP (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C1** | Cada dominio tiene al menos dos rutas | `study_paths.py --domain all --goal all` emite ≥ 2 rutas por dominio (alias de C10). |
| **C2** | Respetan el orden de prerrequisitos | `study_paths_check.py` aplica V2; pasa sin violaciones (alias de C8). |
| **C3** | Cada ruta tiene puntos de verificación explícitos | Cada ruta emitida tiene ≥ 1 checkpoint (alias de C9). |

### Estructura del doc (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C4** | `study-paths.md` existe, ≤ 600 líneas, 9 secciones canónicas §1-§9 | Estructura del doc |
| **C5** | §2 tabla con los 3 objetivos cerrados (`operate-hoy`, `entender-a-fondo`, `repasar`) | Catálogo cerrado |
| **C6** | §5 reglas R-P1 a R-P7 presentes (7 reglas) | Reglas duras |

### Scripts (5)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C7** | `study_paths.py --domain all --goal all` ejecuta exit 0 | CLI funcional |
| **C8** | Las rutas emitidas respetan el orden topológico (V2) | Criterio #2 ROADMAP |
| **C9** | Las rutas emitidas tienen ≥ 1 checkpoint (V3) | Criterio #3 ROADMAP |
| **C10** | Cada dominio del fixture tiene ≥ 2 rutas | Criterio #1 ROADMAP |
| **C11** | `study_paths.py --format json` emite JSON válido | Emisión JSON |
| **C12** | `study_paths_check.py --routes <out> --note-plan <plan>` pasa sin violaciones | Validador funcional |

### Density + wirings (2)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C13** | Las 10 notas fixture + living-doc pasan `density_check.py --strict` exit 0 | R1-R8 F76 |
| **C14** | Wirings cerrados: `SKILL.md §5.3` menciona `study-paths.md`; `references/09-study/README.md` marca `study-paths.md` como `publicado`; `references/04-authoring/properties.md` §5.22 cita F104 + `study-path-goals`; `references/03-knowledge/concept-graph.md` R5 cita F104; `schemas/concept-graph.schema.json` tiene `goal` + `estimated_minutes` | Wirings |

### Derivados (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **D1** | `wc -l study-paths.md` ≤ 600 | INV-02 |
| **D2** | 9 secciones canónicas §1-§9 presentes | Estructura |
| **D3** | §4 enum cerrado con exactamente 3 objetivos | Lista cerrada |

## Salida esperada

```
PASS 17/17
  [PASS] C4
  [PASS] C5
  [PASS] C6
  [PASS] C7
  [PASS] C11
  [PASS] C10
  [PASS] C8
  [PASS] C9
  [PASS] C12
  [PASS] C13
  [PASS] C14
  [PASS] D1
  [PASS] D2
  [PASS] D3
  [PASS] C1-roadmap-dominios-2-rutas
  [PASS] C2-roadmap-prerrequisitos
  [PASS] C3-roadmap-checkpoints
```

## Wirings (fases relacionadas)

- **F39** `references/03-knowledge/concept-graph.md` — `concept-graph.json`
  provee las rutas `shortest` + `broadest` por dominio y `goal_concept_id`.
  F104 añade los 3 objetivos como capa decorativa.
- **F44** `references/03-knowledge/note-plan.md` — `note-plan.json` provee
  el mapping `concept_id → note_id` + `depends_on[]`.
- **F47** `references/04-authoring/properties.md` §5.20 — `reading-time-minutes`
  alimenta el tiempo estimado (R-P6).
- **F47** `references/04-authoring/properties.md` §5.22 — nueva propiedad
  opcional `study-path-goals` (3 valores cerrados).
- **F92** `references/05-note-types/practice.md` — los labs son la fuente
  natural de checkpoints (V3).
- **F102** `references/09-study/self-evaluation.md` — `## Autoevaluación`
  es checkpoint alternativo cuando no hay `practice` (V3).
- **F103** `references/09-study/error-log.md` — el living-doc alimenta
  la ruta `repasar` (R-P7).

## Sin dependencias externas

Python 3.9+ stdlib puro + invocación de `density_check.py` (F76) y
`study_paths_check.py` (F104). El corpus se genera inline en
`build_fixtures.py` para evitar divergencia entre fixtures y la regla
que verifican.
