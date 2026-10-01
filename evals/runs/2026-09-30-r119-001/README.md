# Run `2026-09-30-r119-001` — primera corrida material de regresión

> Corrida generada por `evals/suite/runner/run_regression.py --dry-run` el 2026-09-30. Esta corrida es la **base** sobre la que se comparan releases futuros de la skill.

## Estado

- **Modo:** dry-run (sin agente en producción).
- **N ejecuciones por caso:** 3 (default 5 reducido para material rápido).
- **Casos:** 6 del set de regresión (4 referenciados a F118 + 2 nuevos).
- **Resultado del gate:** **FAIL** (esperado en dry-run; ver §Por qué falla abajo).
- **Evidencia archivada:** 4 archivos en `evidence/` (per `docs/release.md` §5).

## Estructura

```
runs/2026-09-30-r119-001/
├── README.md                        # este archivo
├── report.json                      # F118 — resumen del candidato (sintético)
├── variance.json                    # F119 — varianza sobre 3 ejecuciones
├── diff.json                        # F118 — diff vs F118 baseline
├── gate.json                        # F119 — decisión del gate
├── evidence/                        # copia inmutable per docs/release.md §5
│   ├── report.json
│   ├── variance.json
│   ├── diff.json
│   └── gate.json
└── cases/<case-id>/run-N/           # F118 — artefactos por ejecución (N=3)
```

## Por qué el gate falla

Sin agente en producción, las ejecuciones no producen workdir real, así que las métricas quedan en `null` y `approved=False`. Por diseño, esto dispara 3 de las 4 condiciones del gate:

- **Condición 1 (variance_within_threshold):** `coverage_must_keep_terminal` es `null` → stdev indefinido → dentro del umbral solo si mean es 0; el cálculo actual produce `within_threshold: true` para M1, pero otras métricas como `notes_planned` quedan en `null` y disparan el fail. Documentado en `variance.md` §5.
- **Condición 2 (no_blocking_failures):** `approved_rate = 0.0 < 1.0` para todos los casos → `blocking_failures` poblado.
- **Condición 4 (no_human_pending):** ningún `human.json` rellenado.

Esto es **deseado**: el dry-run verifica que el framework falla correctamente cuando no hay trabajo real, y pasa cuando hay.

## Cómo re-correr con agente real

```bash
python evals/suite/runner/run_regression.py \
  --case-dir evals/regression/cases/ \
  --release-tag 2026-09-30-r119-002 \
  --n-runs 5 \
  --agent-command "<comando del agente que carga la skill>" \
  --out-dir evals/runs/2026-09-30-r119-002/

# Rellenar human.json por caso (ver evals/suite/rubric-application.md).

python evals/suite/runner/drive_suite.py \
  --run-id 2026-09-30-r119-002 \
  --agent-command "<comando>"

python evals/suite/runner/release_gate.py \
  --candidate evals/runs/2026-09-30-r119-002/report.json \
  --baseline evals/runs/2026-09-30-r118-001/report.json \
  --variance evals/runs/2026-09-30-r119-002/variance.json \
  --regression-set evals/regression/SET.md \
  --out evals/runs/2026-09-30-r119-002/gate.json
```

## Comparabilidad

El `report.json` del candidato usa el mismo `skill_fingerprint.json` que F118 (sha256 de `SKILL.md` + `references/` + `schemas/` + `scripts/`). `compare_runs.py` detecta el fingerprint en el diff. Cualquier cambio evolutivo de la skill se reporta en `diff.json::skill_fingerprint_changed`.
