# `evals/comparison-sample/` — Fase 87 `comparison`

Eval de la Fase 87 — tipo de nota `comparison`. Verifica que la tabla
principal va seguida de un párrafo de síntesis (criterio #1), que las
afirmaciones derivadas están marcadas (criterio #2), y que las tablas usan
criterios paralelos (criterio #3).

## Estructura

| Carpeta / archivo | Rol |
|---|---|
| `notes/postgresql-vs-mysql.md` | DB: PostgreSQL 16 vs MySQL 8 con 6 criterios + fila decisiva (Madurez) + matriz de 4 escenarios + trade-offs. |
| `notes/kubectl-vs-docker.md` | CLI: kubectl vs docker CLI con 5 criterios + fila decisiva (Target) + matriz de 4 escenarios + trade-offs. |
| `notes/rest-vs-grpc.md` | RPC: REST vs gRPC con 5 criterios + fila decisiva (Schema) + matriz de 6 escenarios + trade-offs. |
| `build_fixtures.py` | Regenera las 3 notas. `--check` ejecuta `density_check.py --strict`. |
| `run_eval.py` | Batería de 6 sub-criterios (ver abajo). |

## Modo de uso

```bash
# Regenera fixtures + evalúa.
python3 evals/comparison-sample/run_eval.py --regen

# Solo evalúa (asume fixtures ya generadas).
python3 evals/comparison-sample/run_eval.py

# Solo regenera.
python3 evals/comparison-sample/build_fixtures.py
python3 evals/comparison-sample/build_fixtures.py --check
```

## Batería (6 sub-criterios)

| # | Sub-criterio | Verifica |
|---|---|---|
| C1 | `comparison.md` existe, ≤ 600 líneas, contiene las 9 secciones canónicas (§1-§9). | Estructura normativa del doc. |
| C2 | `## Comparativa` es seguida de `## Síntesis` con ≥ 1 párrafo ≥ 30 palabras. | **Criterio ROADMAP #1**. |
| C3 | La nota usa `:::derived` o `:::external` para afirmaciones derivadas. | **Criterio ROADMAP #2**. |
| C4 | La tabla principal en `## Comparativa` tiene criterios paralelos (cada columna tiene valor por fila). | **Criterio ROADMAP #3**. |
| C5 | Los 3 fixtures pasan `density_check.py --strict` exit 0. | R1-R8 de F76. |
| C6 | `SKILL.md` §5.2 fila `comparison` y `references/05-note-types/README.md` ya no marcan `[pendiente F87]`. | Wirings cerrados. |

## Salida esperada

```
PASS 6/6
  [PASS] C1-doc-structure
  [PASS] C2-table-followed-by-synthesis
  [PASS] C3-derived-marked
  [PASS] C4-parallel-criteria
  [PASS] C5-density-check
  [PASS] C6-wirings-closed
```

## Wirings (fases previas)

- **F45** `references/04-authoring/block-directives.md` — directivas `:::derived`, `:::external`, `:::tip`, `:::example`, `:::warning`.
- **F46** `references/04-authoring/inline-marks.md` — `{src:blk_xxxx}` por dato; `[[note:id]]` para referencias.
- **F47** `references/04-authoring/properties.md` — frontmatter canónico; `source-bearing` recomendado.
- **F75** `references/07-visual/note-templates.md` — cabecera, apertura/cierre común, §6.10 patrón resumido.
- **F76** `references/07-visual/density.md` + `density_check.py` — reglas R1-R8.
- **F78** `references/05-note-types/concept.md` — paraguas común.
- **F79** `references/05-note-types/api-reference.md` — comparisons que incluyen APIs.
- **F83** `references/05-note-types/architecture.md` — comparisons entre arquitecturas.
- **F86** `references/05-note-types/chapter-digest.md` — capítulos que comparan alternativas.

## Sin dependencias externas

Python 3.9+ stdlib puro. Las 3 notas se generan inline en `build_fixtures.py`
para evitar divergencia entre fixtures y la regla que verifican.
