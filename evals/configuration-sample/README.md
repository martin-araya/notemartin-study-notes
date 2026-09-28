# `evals/configuration-sample/` — Fase 81 `configuration`

Eval de la Fase 81 — tipo de nota `configuration`. Verifica que la tabla
canónica de 8 columnas tiene `Default` y `Ámbito` en cada fila, que las
interacciones del SDM están documentadas, y que las recomendaciones llevan
respaldo `{src:}` o `:::external`.

## Estructura

| Carpeta / archivo | Rol |
|---|---|
| `notes/postgresql-conf.md` | DB: 11 GUC críticos de PostgreSQL 16 (memoria + conexión + WAL + logging). Cubre criterio #1 (8-col exhaustiva) y #2 (5 interacciones). |
| `notes/nginx-conf.md` | Web: 10 directivas core de nginx 1.27 (workers, timeouts, buffers, proxy). Cubre criterio #1 y #3 (recomendaciones con respaldo). |
| `notes/k8s-pod-resources.md` | k8s: requests + limits + QoS class. Cubre criterio #1 + diagrama de dependencias con `flowchart LR`. |
| `build_fixtures.py` | Regenera las 3 notas. `--check` ejecuta `density_check.py --strict`. |
| `run_eval.py` | Batería de 6 sub-criterios (ver abajo). |

## Modo de uso

```bash
# Regenera fixtures + evalúa.
python3 evals/configuration-sample/run_eval.py --regen

# Solo evalúa (asume fixtures ya generadas).
python3 evals/configuration-sample/run_eval.py

# Solo regenera (sin ejecutar eval).
python3 evals/configuration-sample/build_fixtures.py
python3 evals/configuration-sample/build_fixtures.py --check    # + density_check
```

## Batería (6 sub-criterios)

| # | Sub-criterio | Verifica |
|---|---|---|
| C1 | `configuration.md` existe, ≤ 500 líneas, contiene las 9 secciones canónicas (§1-§9). | Estructura normativa del doc. |
| C2 | Toda fila de tabla 8-col tiene `Default` y `Ámbito` no vacíos. | **Criterio ROADMAP #1**. |
| C3 | `## Interacciones` existe con ≥ 1 fila (tabla o bullet). | **Criterio ROADMAP #2**. |
| C4 | Ninguna recomendación (`recomendamos\|sugerido\|usar N\|...`) sin respaldo `{src:}` o `:::external` adyacente (±5 líneas), excluyendo filas de tabla. | **Criterio ROADMAP #3**. |
| C5 | Los 3 fixtures pasan `density_check.py --strict` exit 0. | R1-R8 de F76. |
| C6 | `SKILL.md` §5.2 fila `configuration` y `references/05-note-types/README.md` ya no marcan `[pendiente F81]`. | Wirings cerrados. |

## Salida esperada

```
PASS 6/6
  [PASS] C1-doc-structure
  [PASS] C2-table-completeness
  [PASS] C3-interactions-present
  [PASS] C4-no-unsupported-recommendations
  [PASS] C5-density-check
  [PASS] C6-wirings-closed
```

## Wirings (fases previas)

- **F46** `references/04-authoring/inline-marks.md` — marcas `{src:blk_xxxx}` y `[[note:id]]`.
- **F47** `references/04-authoring/properties.md` — frontmatter canónico (20 propiedades; `source-bearing` obligatorio).
- **F51** `references/04-authoring/depth-layers.md` — capas L1/L2/L3.
- **F66** `references/07-visual/mermaid-portable.md` — Mermaid portable en `## Diagrama de dependencias`.
- **F75** `references/07-visual/note-templates.md` — cabecera, apertura/cierre común, §6.4 patrón resumido.
- **F76** `references/07-visual/density.md` + `scripts/validate/density_check.py` — reglas R1-R8 ejecutables.
- **F78** `references/05-note-types/concept.md` — paraguas común.
- **F79** `references/05-note-types/api-reference.md` — APIs que modifican la config.
- **F80** `references/05-note-types/procedure.md` — procedure que aplica cambios de config.

## Sin dependencias externas

Python 3.9+ stdlib puro. Las 3 notas se generan inline en `build_fixtures.py`
para evitar divergencia entre fixtures y la regla que verifican.
