# Reporte final de verificación — F125

> Documento normativo de **F125**. Cierra el ciclo de las 125 fases del proyecto `notemartin-study-notes`. Materializa el veredicto PASS/PARTIAL/FAIL por cada criterio del ROADMAP y por cada defecto del diagnóstico inicial.

**Fecha:** 2026-10-01T01:54:48.165599+00:00
**Release tag:** `0.1.0`
**Modo:** live
**git_sha:** `aa033a4`

## Veredicto global

# **PARTIAL**

Todos los criterios del ROADMAP F125 cerrados con PASS o PARTIAL.

## Tabla de criterios del ROADMAP F125

| # | Criterio | Veredicto |
|---|---|---|
| **C1** | El capítulo de Oracle pasa la puerta de calidad en los tres destinos ricos | **PASS** |
| **C2** | El PDF escaneado produce notas con código fiel verificado manualmente | **PASS** |
| **C3** | La tasa de pérdida es cero en unidades `must-keep` | **PASS** |
| **C4** | `SKILL.md` sigue bajo 500 líneas tras las 125 fases | **PASS** |

## Tabla de defectos del diagnóstico inicial

Ver [`defects-table.md`](defects-table.md) para el detalle completo.

| # | Defecto | Métrica | Veredicto |
|---|---|---|---|
| **D-FID** | Fidelidad | 100% must-keep terminal + 100% source_refs | **PASS** |
| **D-COB** | Cobertura | respuesta única + loss_rate = 0 | **PARTIAL** |
| **D-TRZ** | Trazabilidad | ida y vuelta bloque↔nota | **PASS** |
| **D-PRT** | Portabilidad | F63 cross-target 0 ausencias | **PASS** |

## Artefactos generados

- [`oracle-quality-gate.json`](oracle-quality-gate.json) — output de quality gate sobre `case-01-postgresql-select`.
- [`oracle-renders/`](oracle-renders/) — los 3 destinos renderizados del caso Oracle (obsidian / notion_api / appflowy).
- [`pdf-scan-verification.md`](pdf-scan-verification.md) — verificación del caso PDF escaneado.
- [`loss-rate.csv`](loss-rate.csv) — 14 filas (1 por corpus source) + summary.
- [`skill-md-stats.txt`](skill-md-stats.txt) — stats de `SKILL.md` (líneas, secciones, refs).
- [`defects-table.md`](defects-table.md) — tabla detallada de defectos con veredictos.

## Decisión de release

Si el veredicto global es PASS o PARTIAL: bumpear `VERSION` de `0.1.0-dev` a `0.1.0` y añadir entrada `## [0.1.0]` a `CHANGELOG.md` per F123 §5.

Si el veredicto es FAIL: reabrir F125 tras corregir las causas; no bumpear.

## Out-of-scope (no se ejecuta en F125)

- Re-ejecución completa de F118 (suite de evals) — el set de regresión F119 ya lo hace.
- Comparación semántica de notas producidas (requiere LLM-as-judge).
- Performance benchmarks.
- Comparación con versiones externas.

## Cambios que reabren F125

- Cambiar los 4 criterios del ROADMAP F125.
- Cambiar las métricas de los defectos del diagnóstico inicial.
- Cambiar el límite de 500 líneas de `SKILL.md`.
- Cambiar el contrato de los artefactos generados (`evals/final-verification/`).
