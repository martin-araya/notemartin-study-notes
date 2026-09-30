# `evals/goal-profiles-sample/` — Fase 105 `Perfiles de objetivo`

Eval de la Fase 105 — **3 perfiles de objetivo cerrados**
(`interview`, `certification`, `work`) ortogonales a `use_case_profile`
(F11), que **añaden** secciones o **relajan** reglas R-* sobre el corpus
base; el **principio INV-GP1** de no-reducción garantiza que ningún
perfil quita cobertura; el **reporte por `objetivo_id`** para
`certification`; y los algoritmos de los 2 scripts
(`goal_profiles.py` con P1-P4; `goal_profile_check.py` con V1-V5).

## Estructura

| Archivo / carpeta | Rol |
|---|---|
| `build_fixtures.py` | Genera `fixtures/` con un mini-corpus: `profile.yaml` con `goal_profile: hybrid` + 3 objetivos en `certification.objectives`; `study-paths/postgresql.json` (output simulado de F104); 3 notas NoteMark (1 concept con `## Decisiones de diseño` + `## Explicación oral` para `interview`, 1 concept con `## Objetivos oficiales` + `## Cobertura por objetivo` para `certification`, 1 configuration sin secciones adicionales); `knowledge/note-plan.json`. |
| `run_eval.py` | Batería de 16 sub-criterios (3 ROADMAP + 3 estructura + 4 scripts + 1 density + 1 wirings + 3 derivados + 1 alias). |
| `fixtures/profile.yaml` | Profile con `goal_profile: hybrid` + 3 objetivos CKAD/PSQL. |
| `fixtures/notemark/pg-mvcc-concept.nm` | Nota concept con secciones `## Decisiones de diseño` + `## Explicación oral` (perfil `interview`). |
| `fixtures/notemark/k8s-pods.nm` | Nota concept con `## Objetivos oficiales` + `## Cobertura por objetivo` + `certification-objective: [ckad-core-1, ckad-core-2]` (perfil `certification`). |
| `fixtures/notemark/nginx-quick.nm` | Nota configuration sin secciones adicionales (perfil `work`). |
| `fixtures/study-paths/postgresql.json` | Output simulado de F104 con 2 rutas (`operate-hoy`, `entender-a-fondo`). |

## Modo de uso

```bash
# Regenera fixtures y ejecuta el eval.
python3 evals/goal-profiles-sample/build_fixtures.py --force
python3 evals/goal-profiles-sample/run_eval.py

# Solo evalúa (asume fixtures ya generadas).
python3 evals/goal-profiles-sample/run_eval.py
```

## Batería (16 sub-criterios)

### Criterios ROADMAP (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C1** | Cada perfil declara qué añade y qué relaja | `goal_profiles.py --profile <p>` emite las secciones `adds[]` correctamente (alias de C5). |
| **C2** | Ninguno reduce la cobertura | `goal_profile_check.py --profile <p>` aplica V1 sin violaciones críticas (alias de C11). |
| **C3** | `certification` permite consultar cobertura por objetivo | `goal_profiles.py --profile certification --by-objective <id>` emite el reporte (alias de C8). |

### Estructura del doc (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C4** | `goal-profiles.md` existe, ≤ 600 líneas, 9 secciones canónicas §1-§9 | Estructura del doc |
| **C5** | §2 tabla con los 3 perfiles + cada uno con `adds[]` y `relaxes[]` | Catálogo cerrado |
| **C6** | §5 reglas R-G1 a R-G7 presentes (7 reglas) | Reglas duras |

### Scripts (5)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C7** | `goal_profiles.py --profile interview --input <out>` añade las secciones declaradas en `adds[]` al output Markdown | Perfil `interview` |
| **C8** | `goal_profiles.py --profile certification --by-objective <id>` emite el reporte por objetivo | Perfil `certification` |
| **C9** | `goal_profiles.py --profile work` no añade secciones (relaja solo R1) | Perfil `work` |
| **C10** | `goal_profiles.py --profile hybrid` pasa sin errores (modo passthrough) | Perfil `hybrid` |
| **C11** | `goal_profile_check.py --profile <p>` funciona para los 3 perfiles canónicos | Validador funcional |

### Density + wirings (2)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C12** | Las 3 notas fixture pasan `density_check.py --strict` exit 0 | R1-R8 F76 |
| **C13** | Wirings cerrados: `SKILL.md §5.3` menciona `goal-profiles.md`; `references/09-study/README.md` marca `goal-profiles.md` como `publicado`; `references/04-authoring/properties.md` §5.23-§5.24 cita F105 + `goal-profile-override` + `certification-objective`; `references/06-writing/anti-patterns.md` §2 lista `AP17` + `AP18` + `AP19`; `references/05-note-types/concept.md` §6 lista `**F105-1**` + `**F105-2**`; `assets/profile.template.yaml` tiene bloque `goal_profile` + `certification.objectives` | Wirings |

### Derivados (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **D1** | `wc -l goal-profiles.md` ≤ 600 | INV-02 |
| **D2** | 9 secciones canónicas §1-§9 presentes | Estructura |
| **D3** | §2 enum cerrado con exactamente 3 perfiles | Lista cerrada |

## Salida esperada

```
PASS 16/16
  [PASS] C4
  [PASS] C5
  [PASS] C6
  [PASS] C7
  [PASS] C8
  [PASS] C9
  [PASS] C10
  [PASS] C11
  [PASS] C12
  [PASS] C13
  [PASS] D1
  [PASS] D2
  [PASS] D3
  [PASS] C1-roadmap-declara-adds-relaxes
  [PASS] C2-roadmap-no-reduce-cobertura
  [PASS] C3-roadmap-certification-cobertura
```

## Wirings (fases relacionadas)

- **F11** `assets/profile.template.yaml` — añade bloque `goal_profile` +
  `certification.objectives[]`.
- **F39** `references/03-knowledge/concept-graph.md` — `concept-graph.json`
  provee rutas (consumidas por F104 → F105).
- **F44** `references/03-knowledge/note-plan.md` — `note-plan.json`
  consumido por V3.
- **F47** `references/04-authoring/properties.md` §5.23 + §5.24 — añade
  `goal-profile-override` + `certification-objective` (INV-P1 ahora 24
  propiedades).
- **F78** `references/05-note-types/concept.md` §6 — checklist extendido
  con F105-1 + F105-2.
- **F83** `references/05-note-types/architecture.md` — `## Decisiones de diseño`
  ya es obligatoria (F83 §2); F105 la reitera para `interview`.
- **F100** `references/06-writing/anti-patterns.md` §2 — AP17, AP18, AP19
  específicos de F105 (lista cerrada de 19 AP).
- **F104** `references/09-study/study-paths.md` — F105 filtra las 3
  rutas por perfil + inyecta `adds[]`.

## Sin dependencias externas

Python 3.9+ stdlib puro + invocación de `density_check.py` (F76) y
`goal_profile_check.py` (F105). El corpus se genera inline en
`build_fixtures.py` para evitar divergencia entre fixtures y la regla
que verifican.
