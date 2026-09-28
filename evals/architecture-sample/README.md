# `evals/architecture-sample/` — Fase 83 `architecture`

Eval de la Fase 83 — tipo de nota `architecture`. Verifica que el diagrama
obligatorio está en Vista general, cada componente tiene una responsabilidad
en una frase (criterio #1), el flujo está descrito paso a paso (criterio #2),
y los puntos de fallo llevan respaldo `{src:}` (criterio #3).

## Estructura

| Carpeta / archivo | Rol |
|---|---|
| `notes/postgresql-architecture.md` | DB: PostgreSQL 16 con 5 componentes (postmaster, backend, bgwriter, walwriter, autovacuum). 5 puntos de fallo + 3 cuellos de botella con métrica. |
| `notes/kubernetes-architecture.md` | k8s: control plane + worker nodes con 6 componentes. 5 puntos de fallo + 3 cuellos de botella. |
| `notes/docker-architecture.md` | Docker: dockerd + containerd + runc + shim + kernel con 5 componentes. 4 puntos de fallo + 3 cuellos de botella. |
| `build_fixtures.py` | Regenera las 3 notas. `--check` ejecuta `density_check.py --strict`. |
| `run_eval.py` | Batería de 6 sub-criterios (ver abajo). |

## Modo de uso

```bash
# Regenera fixtures + evalúa.
python3 evals/architecture-sample/run_eval.py --regen

# Solo evalúa (asume fixtures ya generadas).
python3 evals/architecture-sample/run_eval.py

# Solo regenera.
python3 evals/architecture-sample/build_fixtures.py
python3 evals/architecture-sample/build_fixtures.py --check
```

## Batería (6 sub-criterios)

| # | Sub-criterio | Verifica |
|---|---|---|
| C1 | `architecture.md` existe, ≤ 500 líneas, contiene las 9 secciones canónicas (§1-§9). | Estructura normativa del doc. |
| C2 | Tabla de componentes: ≥ 3 filas Y primera frase de cada responsabilidad ≤ 30 palabras. | **Criterio ROADMAP #1**. |
| C3 | `## Flujo paso a paso` con ≥ 3 pasos numerados Y diagrama Mermaid `sequenceDiagram`. | **Criterio ROADMAP #2**. |
| C4 | Cada `:::warning`/`:::danger` en `## Puntos de fallo` lleva `{src:blk_xxxx}` adyacente (±2 líneas). | **Criterio ROADMAP #3**. |
| C5 | Los 3 fixtures pasan `density_check.py --strict` exit 0. | R1-R8 de F76. |
| C6 | `SKILL.md` §5.2 fila `architecture` y `references/05-note-types/README.md` ya no marcan `[pendiente F83]`. | Wirings cerrados. |

## Salida esperada

```
PASS 6/6
  [PASS] C1-doc-structure
  [PASS] C2-responsibility-one-sentence
  [PASS] C3-flow-step-by-step
  [PASS] C4-failure-points-with-source
  [PASS] C5-density-check
  [PASS] C6-wirings-closed
```

## Wirings (fases previas)

- **F45** `references/04-authoring/block-directives.md` — directivas `:::diagram`, `:::warning`, `:::danger`, `:::note`.
- **F46** `references/04-authoring/inline-marks.md` — `{src:blk_xxxx}` por componente / fallo; `[[note:id]]` para backlinks.
- **F47** `references/04-authoring/properties.md` — frontmatter canónico; `source-bearing` recomendado.
- **F51** `references/04-authoring/depth-layers.md` — architecture puede invocar L1/L2/L3 si la nota es extensa.
- **F66** `references/07-visual/mermaid-portable.md` — Mermaid portable en Vista general y Flujo.
- **F75** `references/07-visual/note-templates.md` — cabecera, apertura/cierre común, §6.6 patrón resumido.
- **F76** `references/07-visual/density.md` + `density_check.py` — reglas R1-R8.
- **F78** `references/05-note-types/concept.md` — paraguas común.
- **F80** `references/05-note-types/procedure.md` — flujos que aplican la arquitectura.
- **F82** `references/05-note-types/error-troubleshooting.md` — cada punto de fallo se enlaza a su nota de troubleshooting.

## Sin dependencias externas

Python 3.9+ stdlib puro. Las 3 notas se generan inline en `build_fixtures.py`
para evitar divergencia entre fixtures y la regla que verifican.
