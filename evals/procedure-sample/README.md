# `evals/procedure-sample/` — Fase 80 `procedure`

Eval de la Fase 80 — tipo de nota `procedure`. Verifica que cada paso tiene
criterio de verificación, que existe rollback o declaración de irreversibilidad,
y que los pasos destructivos están envueltos en `:::danger`.

## Estructura

| Carpeta / archivo | Rol |
|---|---|
| `notes/postgresql-backup-restore.md` | DB: backup lógico con `pg_dump` + restore con `pg_restore`. Cubre criterio #2 (rollback explícito) y #3 (`DROP DATABASE` con `:::danger`). 4 pasos. |
| `notes/nginx-logrotate.md` | OS: rotación de logs con `mv` + `kill -USR1`. Cubre criterio #1 (verificación por paso) y reversibilidad sin estado externo. 2 pasos. |
| `notes/k8s-rolling-restart.md` | k8s: rolling restart de Deployment con `kubectl rollout restart`. Cubre criterio #1 y #3 (`kubectl delete pod` con `:::danger`). 4 pasos. |
| `build_fixtures.py` | Regenera las 3 notas. `--check` ejecuta `density_check.py --strict`. |
| `run_eval.py` | Batería de 6 sub-criterios (ver abajo). |

## Modo de uso

```bash
# Regenera fixtures + evalúa.
python3 evals/procedure-sample/run_eval.py --regen

# Solo evalúa (asume fixtures ya generadas).
python3 evals/procedure-sample/run_eval.py

# Solo regenera (sin ejecutar eval).
python3 evals/procedure-sample/build_fixtures.py
python3 evals/procedure-sample/build_fixtures.py --check    # + density_check
```

## Batería (6 sub-criterios)

| # | Sub-criterio | Verifica |
|---|---|---|
| C1 | `procedure.md` existe, ≤ 500 líneas, contiene las 9 secciones canónicas (§1-§9). | Estructura normativa del doc. |
| C2 | Cada paso (`### Paso N:`) lleva `**Verificación:**` explícita. | **Criterio ROADMAP #1**. |
| C3 | `## Impacto y reversibilidad` contiene columna Rollback **o** declaración de irreversibilidad. | **Criterio ROADMAP #2**. |
| C4 | Cada paso destructivo en código (palabras clave: `DROP`, `DELETE`, `rm -rf`, `kubectl delete`, etc.) está envuelto en `:::danger` (±5 líneas). | **Criterio ROADMAP #3**. |
| C5 | Los 3 fixtures pasan `density_check.py --strict` exit 0. | R1-R8 de F76. |
| C6 | `SKILL.md` §5.2 fila `procedure` y `references/05-note-types/README.md` ya no marcan `[pendiente F80]`. | Wirings cerrados. |

## Salida esperada

```
PASS 6/6
  [PASS] C1-doc-structure
  [PASS] C2-step-verifications
  [PASS] C3-rollback-present
  [PASS] C4-danger-for-destructive
  [PASS] C5-density-check
  [PASS] C6-wirings-closed
```

## Wirings (fases previas)

- **F46** `references/04-authoring/inline-marks.md` — marcas `{src:blk_xxxx}` y `[[note:id]]`.
- **F47** `references/04-authoring/properties.md` — frontmatter canónico (20 propiedades; `source-bearing` recomendado).
- **F51** `references/04-authoring/depth-layers.md` — capas L1/L2/L3.
- **F75** `references/07-visual/note-templates.md` — cabecera canónica, apertura/cierre común, §6.3 patrón resumido + anti-patrón > 10 pasos.
- **F76** `references/07-visual/density.md` + `scripts/validate/density_check.py` — reglas R1-R8 ejecutables.
- **F78** `references/05-note-types/concept.md` — paraguas común.
- **F79** `references/05-note-types/api-reference.md` — `procedure` orquesta APIs documentadas en `api-reference`.
- **F82** `references/05-note-types/error-troubleshooting.md` — errores en `## Errores frecuentes` enlazan aquí.

## Sin dependencias externas

Python 3.9+ stdlib puro. Las 3 notas se generan inline en `build_fixtures.py`
para evitar divergencia entre fixtures y la regla que verifican.
