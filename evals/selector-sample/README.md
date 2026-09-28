# `evals/selector-sample/` — Fase 93 `Selector de tipo` [núcleo]

Eval de la Fase 93 — tipo de nota `selector` [ref] [núcleo]. Verifica que el
doc tiene las 9 secciones canónicas, que sobre el capítulo de Oracle produce
≥ 3 tipos distintos (criterio #1), que la tabla de cobertura no tiene
celdas vacías (criterio #2), y que las reglas de desempate tienen ≥ 3 reglas
explícitas (criterio #3).

## Estructura

| Carpeta / archivo | Rol |
|---|---|
| `notes/oracle-concepts-ch1-selector.md` | DB: aplicación del selector al Chapter 1 de Oracle Concepts 19c; identifica 5 tipos distintos (`concept`, `glossary-term`, `cheatsheet`, `comparison`, `data-model`). |
| `notes/postgresql-ch13-selector.md` | DB: aplicación del selector al Chapter 13 de PostgreSQL 16; identifica 4 tipos distintos (`concept`, `glossary-term`, `configuration`, `data-model`). |
| `build_fixtures.py` | Regenera las 2 notas. `--check` ejecuta `density_check.py --strict`. |
| `run_eval.py` | Batería de 6 sub-criterios (ver abajo). |

## Modo de uso

```bash
# Regenera fixtures + evalúa.
python3 evals/selector-sample/run_eval.py --regen

# Solo evalúa (asume fixtures ya generadas).
python3 evals/selector-sample/run_eval.py

# Solo regenera.
python3 evals/selector-sample/build_fixtures.py
python3 evals/selector-sample/build_fixtures.py --check
```

## Batería (6 sub-criterios)

| # | Sub-criterio | Verifica |
|---|---|---|
| C1 | `selector.md` existe, ≤ 500 líneas, contiene las 9 secciones canónicas (§1-§9). | Estructura normativa del doc. |
| C2 | El fixture "Oracle" lista ≥ 3 tipos distintos en `## Tipos asignados`. | **Criterio ROADMAP #1**. |
| C3 | La tabla de cobertura en `## Cobertura de la matriz` no tiene celdas vacías (`[[note:type]]` o `n/a` explícito). | **Criterio ROADMAP #2**. |
| C4 | El doc tiene `## Reglas de desempate` con ≥ 3 reglas explícitas (items numerados). | **Criterio ROADMAP #3**. |
| C5 | Los 2 fixtures pasan `density_check.py --strict` exit 0. | R1-R8 de F76. |
| C6 | `SKILL.md` §5.2 fila `selector` y `references/05-note-types/README.md` ya no marcan `[pendiente F93]`. | Wirings cerrados. |

## Salida esperada

```
PASS 6/6
  [PASS] C1-doc-structure
  [PASS] C2-oracle-distinct-types
  [PASS] C3-no-empty-cells
  [PASS] C4-tiebreaker-rules
  [PASS] C5-density-check
  [PASS] C6-wirings-closed
```

## Wirings (fases previas)

- **F44** `references/03-knowledge/note-plan.md` — el selector asigna tipos a unidades.
- **F45** `references/04-authoring/block-directives.md` — directivas consumidas.
- **F46** `references/04-authoring/inline-marks.md` — `[[note:type]]` por celda de la matriz.
- **F47** `references/04-authoring/properties.md` — frontmatter con `coverage: summary`.
- **F75** `references/07-visual/note-templates.md` — patrón común.
- **F76** `references/07-visual/density.md` + `density_check.py` — reglas R1-R8.
- **F78-F92** `references/05-note-types/*.md` — los 15 tipos que el selector asigna.

## Sin dependencias externas

Python 3.9+ stdlib puro. Las 2 notas se generan inline en `build_fixtures.py`
para evitar divergencia entre fixtures y la regla que verifican.
