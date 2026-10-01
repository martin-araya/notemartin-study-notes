# Run `2026-09-30-r118-001` — primera corrida material de la suite

> Corrida generada por `evals/suite/runner/drive_suite.py --dry-run` el 2026-09-30. Esta corrida es la **base** sobre la que se comparan iteraciones futuras de la skill.

## Estado

- **Modo:** dry-run (sin agente en producción).
- **Casos:** 6 declarados, 6 procesados.
- **Aserciones automáticas:** 18 declaradas (3 por caso), 18 pending por falta de workdir.
- **Evaluación humana:** 6 plantillas `human.json` generadas, pendientes de rellenar por un humano.

## Cómo completar esta corrida

1. Ejecutar la skill con un agente real sobre cada caso (recomendado: usar `run_case.py --agent-command <cmd>`).
2. Re-correr `check_assertions.py` para evaluar aserciones con workdir real.
3. Rellenar `human.json` por caso siguiendo `evals/suite/rubric-application.md`.

```bash
# Paso 1: ejecutar con agente real
python3 evals/suite/runner/drive_suite.py \
  --run-id 2026-09-30-r118-001 \
  --agent-command "<comando que carga la skill y ejecuta el prompt>"

# Paso 2: rellenar human.json por caso
for c in evals/runs/2026-09-30-r118-001/cases/*/; do
  python3 evals/suite/runner/apply_rubric.py \
    --case "${c%/}.yaml".yaml \
    --out "$c/human.json"
done
```

## Caso 13 — particularidad

`case-13-internet-archive-scan` tiene la aserción `ocr-code-fidelity` en estado `pending_due_to_missing_sample` porque el corpus `13-internet-archive-scan-hostil` no tiene muestra descargada (F6). Esto es esperado y queda documentado en `cases/case-13-internet-archive-scan.yaml::expected_code_snippets.status`. La aserción se activará automáticamente cuando F6 descargue la muestra.

## Comparabilidad

Esta corrida incluye `skill_fingerprint.json` con el sha256 de `SKILL.md`, `references/`, `schemas/` y `scripts/`. Cualquier cambio en estos archivos entre esta corrida y la siguiente se reporta en el diff como `skill_fingerprint_changed`.
