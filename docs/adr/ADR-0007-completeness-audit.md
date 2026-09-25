# ADR-0007 — Auditoría de no-pérdida (Fase 43)

**Fecha:** 2026-09-25
**Estado:** aceptada
**Atada a:** F43, F15 (ledger), F13 (sdm), F37 (information-units), F35 (editorial-semantics), F38 (ledger operativo), F42 (fidelity-rules), INV-08

## Contexto

Fase 43 implementa el gate mecánico que enforza `architecture.md` §3.3: "100 % de `must-keep` con estado terminal antes de cerrar". Las alternativas consideradas:

1. **Auditoría solo en L4 / al publicar** — descartada: el daño se detecta tarde. El spec pide gate en L2.
2. **Forward pass sin inverse sample** — descartada: omite omisiones inversas (block sin entry). La spec menciona "muestreo inverso desde el SDM".
3. **Forward + inverse (estratificado) + threshold gate** (elegida) — los 3 ejes del audit.

## Decisión

1. **Tres ejes** (R1):
   - **Forward pass**: ledger → SDM. Verifica localización, no-mutilación, tipo coherente por entry.
   - **Inverse sample**: SDM → ledger. Muestreo estratificado del SDM para detectar omisiones inversas.
   - **Threshold gate**: 100 % de `must-keep` con `state ∈ {written, merged, discarded}`. Cero excepciones.

2. **Muestreo estratificado** (R2, decisión confirmada): 100 % de bloques must-keep (tipos R1–R5 de F37 + severidades F35) + 10 % aleatorio del resto (seed configurable, default `0`). Reproducible: misma entrada + mismo seed = misma muestra.

3. **Umbrales de mutilación** (R3):
   - Exact match para campos clave: `parameter.name`, `error-code.code`, `version-note.version_introduced/_removed`, `syntax-rule.rule`.
   - Normalized match (lowercase + whitespace collapsed) para texto libre: `definition.text`, `example.text/code`, `step.text`, `warning.text`, `cross-reference.target`, `mechanism.text`, `tradeoff.text`.
   - Cualquier diferencia normalizada = `critical` para must-keep, `warning` para context.

4. **Threshold 100 % must-keep** (R4): sin excepciones. Coherente con `INV-08` (architecture.md §3.3).

5. **Lista accionable con anclas** (R5): cada finding es `{anchor: {type, id}, severity, category, expected, actual, fix}`. Categorías cerradas: `orphan-block`, `mutilated`, `type-mismatch`, `missing-backward`, `pending-must-keep`.

6. **CLI sin flag `--allow-critical`** (R6): a diferencia de `ingest_check.py` F30, NO se permite cerrar con rojo. Criterio 3 del roadmap: "No se puede cerrar el trabajo con la auditoría en rojo".

7. **Sin JSON nuevo**: el reporte es efímero (output del script). Si el agente quiere archivar, lo guarda en `reports/coverage.md` (architecture.md §4).

8. **Schema validation opcional**: con `jsonschema` valida ledger y SDM antes del audit; sin él, salta con WARNING. El audit nunca aborta por schema inválido (deja pasar y reporta el hallazgo).

## Consecuencias

**Gana**:
- El gate mecánico es ejecutable por CI o por el agente al cerrar un workdir.
- La lista accionable con anclas permite al agente o a un script resolver cada hallazgo sin ambigüedad.
- El inverse sample detecta omisiones que el forward pass no ve (block sin entry).
- La regla "fuente gana" de F41 + las 3 prohibiciones de F42 + el gate de F43 cierran la promesa de fidelidad del proyecto (architecture.md §3.3).

**Pierde**:
- El 10 % de muestreo context puede perder omisiones contextuales; el 100 % must-keep cubre el riesgo crítico.
- Mutilación normalizada puede dar falsos negativos si el reformateo es legítimo (mitigado por `:::derived` F42).

**Queda atado**:
- F15 (ledger): el audit lee su JSON; valida contra su schema.
- F38 (ledger operativo): el audit orquesta `check` de F38 + agrega nuevos checks (mutilación + inverse sample).
- F37 (information-units): los tipos R1–R5 son el universo de must-keep.
- F35 (editorial-semantics): las severidades `deprecated`/`removed`/`novelty` son must-keep.
- F42 (fidelity-rules): los valores técnicos sin respaldo en ledger son hallazgos `mutilated`.
- F114 (quality gate): ejecuta el audit continuamente.
- INV-08: 100 % must-keep con estado terminal es el threshold.
