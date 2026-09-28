# `evals/version-delta-sample/` — Fase 88 `version-delta`

Eval de la Fase 88 — tipo de nota `version-delta`. Verifica que cada cambio
declara versión exacta (criterio #1), que los cambios de default están en
sección destacada aparte (criterio #2), y que las notas afectadas tienen
enlaces bidireccionales (criterio #3).

## Estructura

| Carpeta / archivo | Rol |
|---|---|
| `notes/postgresql-16-changelog-delta.md` | DB: delta de PostgreSQL 15 → 16 con 6 cambios (incluyendo `default alterado` para `password_encryption`), 2 breaking changes, 2 trampas de migración, 3 notas afectadas. |
| `notes/kubernetes-1-30-changelog-delta.md` | k8s: delta de Kubernetes 1.29 → 1.30 con 6 cambios (Pod Scheduling Readiness GA, sidecar containers GA), 1 breaking change (dockershim removed), 2 trampas, 3 notas afectadas. |
| `notes/docker-25-changelog-delta.md` | Docker: delta de Docker 24 → 25 con 5 cambios (cgroups v2 obligatorio, BuildKit default), 1 breaking change (legacy network plugins), 2 trampas, 3 notas afectadas. |
| `build_fixtures.py` | Regenera las 3 notas. `--check` ejecuta `density_check.py --strict`. |
| `run_eval.py` | Batería de 6 sub-criterios (ver abajo). |

## Modo de uso

```bash
# Regenera fixtures + evalúa.
python3 evals/version-delta-sample/run_eval.py --regen

# Solo evalúa (asume fixtures ya generadas).
python3 evals/version-delta-sample/run_eval.py

# Solo regenera.
python3 evals/version-delta-sample/build_fixtures.py
python3 evals/version-delta-sample/build_fixtures.py --check
```

## Batería (6 sub-criterios)

| # | Sub-criterio | Verifica |
|---|---|---|
| C1 | `version-delta.md` existe, ≤ 500 líneas, contiene las 9 secciones canónicas (§1-§9). | Estructura normativa del doc. |
| C2 | Cada fila de `## Cambios` tiene columna 1 "Versión exacta" con formato semver (`X.Y` o `X.Y.Z`). | **Criterio ROADMAP #1**. |
| C3 | `## Cambios de default` existe como sección separada con tabla que tiene ≥ 1 fila y columnas "anterior" + "nuevo". | **Criterio ROADMAP #2**. |
| C4 | `## Notas afectadas` lista ≥ 2 `[[note:id]]` apuntando a notas que cambiaron. | **Criterio ROADMAP #3**. |
| C5 | Los 3 fixtures pasan `density_check.py --strict` exit 0. | R1-R8 de F76. |
| C6 | `SKILL.md` §5.2 fila `version-delta` y `references/05-note-types/README.md` ya no marcan `[pendiente F88]`. | Wirings cerrados. |

## Salida esperada

```
PASS 6/6
  [PASS] C1-doc-structure
  [PASS] C2-exact-version-column
  [PASS] C3-default-changes-section
  [PASS] C4-affected-notes-with-links
  [PASS] C5-density-check
  [PASS] C6-wirings-closed
```

## Wirings (fases previas)

- **F45** `references/04-authoring/block-directives.md` — directivas `:::danger`, `:::warning`, `:::tip`, `:::note`.
- **F46** `references/04-authoring/inline-marks.md` — `{src:blk_xxxx}` por cambio; `[[note:id]]` para notas afectadas.
- **F47** `references/04-authoring/properties.md` — frontmatter; `source-bearing` obligatorio + `product-version` (NUEVA).
- **F72** `references/07-visual/tokens.md` — colores semánticos de las directivas.
- **F75** `references/07-visual/note-templates.md` — cabecera, apertura/cierre común, §6.11 patrón resumido.
- **F76** `references/07-visual/density.md` + `density_check.py` — reglas R1-R8.
- **F78** `references/05-note-types/concept.md` — paraguas común; notas concept referencian deltas.
- **F79** `references/05-note-types/api-reference.md` — deltas que documentan cambios en APIs.
- **F80** `references/05-note-types/procedure.md` — procedures de upgrade.
- **F81** `references/05-note-types/configuration.md` — deltas que documentan cambios en defaults.

## Sin dependencias externas

Python 3.9+ stdlib puro. Las 3 notas se generan inline en `build_fixtures.py`
para evitar divergencia entre fixtures y la regla que verifican.
