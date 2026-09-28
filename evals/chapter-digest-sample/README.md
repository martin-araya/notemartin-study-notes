# `evals/chapter-digest-sample/` — Fase 86 `chapter-digest` [núcleo]

Eval de la Fase 86 — tipo de nota `chapter-digest`. Verifica continuidad en
ambos sentidos (criterio #1), conceptos nuevos con `[[note:id]]` (criterio #2),
y cobertura de keywords del SDM (criterio #3).

## Estructura

| Carpeta / archivo | Rol |
|---|---|
| `notes/postgresql-chapter-13-digest.md` | DB: digest del PostgreSQL 16 Chapter 13 (Concurrency Control) con MVCC, xmin/xmax, isolation levels, VACUUM. Continuidad Ch 12 → 13 → 14. |
| `notes/kubernetes-pod-spec-digest.md` | k8s: digest del Pod v1 API reference con containers, resources, scheduling, lifecycle. Continuidad Overview → Pod → Deployment. |
| `notes/rfc-7231-chapter-4-digest.md` | RFC: digest del RFC 7231 §4 (HTTP/1.1 Request Methods) con safe/idempotent. Continuidad §3 → §4 → §5. |
| `build_fixtures.py` | Regenera las 3 notas. `--check` ejecuta `density_check.py --strict`. |
| `run_eval.py` | Batería de 6 sub-criterios (ver abajo). |

## Modo de uso

```bash
# Regenera fixtures + evalúa.
python3 evals/chapter-digest-sample/run_eval.py --regen

# Solo evalúa (asume fixtures ya generadas).
python3 evals/chapter-digest-sample/run_eval.py

# Solo regenera.
python3 evals/chapter-digest-sample/build_fixtures.py
python3 evals/chapter-digest-sample/build_fixtures.py --check
```

## Batería (6 sub-criterios)

| # | Sub-criterio | Verifica |
|---|---|---|
| C1 | `chapter-digest.md` existe, ≤ 600 líneas, contiene las 9 secciones canónicas (§1-§9). | Estructura normativa del doc. |
| C2 | `## Continuidad` tiene sub-secciones `### Hacia atrás` Y `### Hacia adelante` con ≥ 1 enlace `[[note:]]` o `[[term:]]` cada una. | **Criterio ROADMAP #1**. |
| C3 | Cada concepto en `## Conceptos nuevos` (tabla) tiene `[[note:id]]` o `[[term:nombre]]` en la columna 2. | **Criterio ROADMAP #2**. |
| C4 | Cobertura ≥ 60% de keywords esperadas del SDM en `## Resumen ejecutivo` + `## Puntos clave`. | **Criterio ROADMAP #3**. |
| C5 | Los 3 fixtures pasan `density_check.py --strict` exit 0. | R1-R8 de F76. |
| C6 | `SKILL.md` §5.2 fila `chapter-digest` y `references/05-note-types/README.md` ya no marcan `[pendiente F86]`. | Wirings cerrados. |

## Salida esperada

```
PASS 6/6
  [PASS] C1-doc-structure
  [PASS] C2-continuity-both-directions
  [PASS] C3-concepts-with-notes
  [PASS] C4-keyword-coverage
  [PASS] C5-density-check
  [PASS] C6-wirings-closed
```

## Wirings (fases previas)

- **F45** `references/04-authoring/block-directives.md` — directivas `:::example`, `:::warning`, `:::note`, `:::external`, `:::derived`, `:::tip`.
- **F46** `references/04-authoring/inline-marks.md` — `{src:blk_xxxx}` por cita; `[[note:id]]` para conceptos.
- **F47** `references/04-authoring/properties.md` — frontmatter con `coverage: summary` enum.
- **F66** `references/07-visual/mermaid-portable.md` — Mermaid portable en `## Detalles`.
- **F75** `references/07-visual/note-templates.md` — cabecera, apertura/cierre común, §6.9 patrón resumido.
- **F76** `references/07-visual/density.md` + `density_check.py` — reglas R1-R8; L1 extendida permitida.
- **F78** `references/05-note-types/concept.md` — paraguas común; conceptos nuevos referencian notas concept.
- **F79** `references/05-note-types/api-reference.md` — capítulos que documentan APIs.
- **F80** `references/05-note-types/procedure.md` — capítulos que documentan procedimientos.
- **F81** `references/05-note-types/configuration.md` — capítulos que documentan configuración.
- **F83** `references/05-note-types/architecture.md` — capítulos que documentan arquitecturas.

## Sin dependencias externas

Python 3.9+ stdlib puro. Las 3 notas se generan inline en `build_fixtures.py`
para evitar divergencia entre fixtures y la regla que verifican.
