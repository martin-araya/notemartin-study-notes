# Varianza y umbrales — `evals/regression/variance.md`

> Spec normativa de la Fase 119: qué se entiende por varianza, cómo se mide, cuáles son los umbrales, qué hacer cuando un caso los excede.

## Índice

1. [Propósito y alcance](#1-propósito-y-alcance) · 2. [Cuándo se aplica](#2-cuándo-se-aplica) · 3. [Definiciones operativas](#3-definiciones-operativas) · 4. [Métricas y umbrales](#4-métricas-y-umbrales) · 5. [Protocolo de medición](#5-protocolo-de-medición) · 6. [Política de release](#6-política-de-release) · 7. [Evidencia de no-regresión](#7-evidencia-de-no-regresión) · 8. [Aceptación de un cambio](#8-aceptación-de-un-cambio) · 9. [Comparabilidad con F118](#9-comparabilidad-con-f118) · 10. [Cambios permitidos sin reabrir F119](#10-cambios-permitidos-sin-reabrir-f119) · 11. [Cambios que reabren F119](#11-cambios-que-reabren-f119)

## 1. Propósito y alcance

Define cómo se mide la **estabilidad** del comportamiento de la skill sobre el mismo caso: misma skill, mismo agente, misma configuración, N ejecuciones. La varianza **es** la del sistema completo (skill + instrucciones + agente + temperatura). Una varianza alta indica instrucciones no deterministas o un agente poco estable sobre esa tarea.

## 2. Cuándo se aplica

- Antes de cada release (manual o automatizado por CI): N ejecuciones del set de regresión.
- Antes de aceptar un cambio que toque `references/`, `SKILL.md`, `schemas/`, `scripts/` del paquete, o los scripts del runner: N ejecuciones del set de regresión como evidencia del PR.
- Opcional: en commits nocturnos como vigilancia continua (coste: N × 6 casos × minutos por caso).

## 3. Definiciones operativas

- **Ejecución:** una invocación completa de `run_case.py` sobre un caso, con su `workdir`, `assertions.json` y `human.json`.
- **N:** número de ejecuciones por caso. Default 5 (en `variance_thresholds.yaml`).
- **Métrica:** valor escalar derivado de los artefactos de una ejecución (`coverage_must_keep_terminal`, `notes_planned`, `ir_node_count`, `human_global`, `approved`).
- **Varianza:** `stdev(values)` sobre las N ejecuciones de un caso. Para `ir_node_count`, también se calcula `stdev / mean` (coeficiente de variación) y se compara contra un ratio.
- **Regresión:** cambio de comportamiento entre dos runs (`baseline` vs `candidate`) que viola una regla de §6.
- **Release:** tag semántico (string) que identifica un commit como entregable. La política de versionado semántico vive en F123; F119 no la impone.
- **Baseline:** ejecución sobre el último release tag.
- **Candidate:** ejecución sobre el commit candidato a release.
- **Approved:** un caso está aprobado si `human.json.approved == true` (computado por `compute_global()` de F118).

## 4. Métricas y umbrales

Las 5 métricas se miden sobre N ejecuciones de cada caso. Los umbrales viven en `variance_thresholds.yaml` (versionados, no hardcoded).

| Métrica | Definición | Fuente | Umbral default | Cómo se calcula |
|---|---|---|---|---|
| **M1** `coverage_must_keep_terminal` | ratio de unidades `must-keep` con `state ∈ {written, merged, discarded}` | `ledger.json` por ejecución | `stdev ≤ 0.05` | `1 − (must_keep_pending / must_keep_total)` por ejecución, stdev sobre N |
| **M2** `notes_planned` | número de notas en `note-plan.json` | `note-plan.json` por ejecución | `stdev ≤ 1` | entero por ejecución, stdev sobre N |
| **M3** `ir_node_count` | número de nodos en el IR | `ir/*.json` por ejecución | `stdev / mean ≤ 0.10` | suma de `len(blocks)` por ejecución, ratio sobre N |
| **M4** `human_global_avg` | media ponderada de la rúbrica | `human.json` por ejecución | `stdev ≤ 0.5` | `compute_global(scores, profile)` por ejecución, stdev sobre N |
| **M5** `approved_rate` | fracción de ejecuciones con `approved == true` | `human.json` por ejecución | `= 1.0` | booleano por ejecución, ratio sobre N |

**Regla dura:** M5 siempre exige 1.0. Cualquier flip (de approved a not-approved) bloquea el release automáticamente, sin importar las otras métricas. Esta es la métrica "binaria" del set de regresión.

## 5. Protocolo de medición

`run_regression.py` ejecuta el siguiente flujo:

```
1. Cargar thresholds desde variance_thresholds.yaml.
2. Por cada caso en --case-dir:
   2.1. Resolver referencia si el caso es .ref.yaml.
   2.2. Para i en 1..N:
        - Invocar run_case.py con --run-suffix -i.
        - Invocar check_assertions.py.
        - Invocar apply_rubric.py (genera plantilla human.json si no existe).
   2.3. Acumular métricas por ejecución.
   2.4. Calcular mean, stdev, min, max, range por métrica.
   2.5. Comparar contra thresholds.
3. Emitir variance.json con la forma canónica:
   {
     "schema_version": "1.0.0",
     "release_tag": "<tag>",
     "n_runs": N,
     "thresholds_applied": "<sha256 del YAML>",
     "cases": [
       {
         "case_id": "<case-id>",
         "metrics": {
           "coverage_must_keep_terminal": {
             "values": [...],
             "mean": ...,
             "stdev": ...,
             "min": ...,
             "max": ...,
             "range": ...,
             "within_threshold": true|false,
             "threshold": 0.05
           },
           ...
         },
         "approved": [true, true, ...],
         "approved_rate": 1.0,
         "passes_regression": true|false
       }
     ],
     "summary": {
       "cases_total": M,
       "cases_pass": M',
       "cases_fail": M - M',
       "blocking_failures": [<case_id>, ...]
     }
   }
```

## 6. Política de release

Un release es aprobado por `release_gate.py` cuando **se cumplen las cuatro condiciones**:

1. `variance.json.summary.cases_fail == 0` (todas las métricas dentro de umbral).
2. `variance.json.summary.blocking_failures == []` (ningún caso del set tiene M5 < 1.0).
3. `compare_runs.py candidate vs baseline` no muestra ningún caso del set de regresión cambiando `approved: true → false`.
4. `candidate.report.json.cases_human_pending == 0` (todas las evaluaciones humanas rellenas, sin `null`).

Si alguna falla, el gate emite `gate.json` con `{status: "fail", reasons: [...]}` y exit 1. Las 4 condiciones se enumeran en `reasons[]` para que el revisor sepa qué regla violar.

**Override humano:** un humano puede aceptar un release con overrides explícitos, documentados como ADR y archivados en `evidence/overrides.json` con la firma del responsable y el motivo. El gate se respeta: el override es post-gate, no bypass.

## 7. Evidencia de no-regresión

Por cada release aceptado se archiva en `runs/<release-tag>/evidence/` exactamente 4 archivos:

| Archivo | Fuente | Para qué sirve |
|---|---|---|
| `report.json` | `run_case.py` + `drive_suite.py` (F118) | Resumen de la suite del candidato. |
| `variance.json` | `run_regression.py` (F119) | Estabilidad de N ejecuciones por caso. |
| `diff.json` | `compare_runs.py` (F118) | Cambios candidato vs baseline. |
| `gate.json` | `release_gate.py` (F119) | Decisión del gate con sus razones. |

Estos 4 archivos son el contrato. Cambiar la lista reabre F119.

## 8. Aceptación de un cambio

Un PR que toca la skill cumple los criterios del ROADMAP F119 si y solo si:

1. El cambio pasa el suite de F118 (`assertions.json` con todas las aserciones `passed: true` o `status: pending`).
2. El cambio pasa el set de regresión de F119 (`variance.json.summary.cases_fail == 0`).
3. La evidencia de no-regresión (§7) está adjunta al PR.

Si el cambio toca `references/` o `SKILL.md`, el revisor debe **adjuntar** los 4 archivos de evidencia (no basta con que el CI los genere y los borre). Esto convierte la evidencia en artefacto auditable.

## 9. Comparabilidad con F118

F119 reutiliza la base de F118 sin modificarla:

- `evals/suite/runner/run_case.py` — invocado por `run_regression.py` con `--run-suffix`.
- `evals/suite/runner/check_assertions.py` — invocado por `run_regression.py` para cada ejecución.
- `evals/suite/runner/apply_rubric.py` — invocado para generar plantilla `human.json`.
- `evals/suite/runner/compare_runs.py` — invocado por `release_gate.py` para el diff.
- `evals/suite/SCHEMA.md` §2 — la forma de `runs/<run-id>/cases/<case-id>/run-N/` extiende §2 sin romperla.

**Invariante:** F119 **no** modifica ningún archivo de F118. Si una nueva necesidad lo requiere, se reabre F118.

## 10. Cambios permitidos sin reabrir F119

- Editar `variance_thresholds.yaml` (umbrales o `n_runs`) con commit + nota en CHANGELOG; ADR si el cambio es > 20 % en un valor.
- Añadir un caso al set de regresión (cumple política de `SET.md` §3).
- Cambiar el `release-tag` de una corrida (es dato).
- Añadir documentación o ejemplos a `variance.md` sin cambiar las reglas de §6.

## 11. Cambios que reabren F119

- Cambiar una métrica de §4 (M1..M5): nombre, definición, fuente, umbral por defecto, regla de cálculo.
- Cambiar las 4 condiciones de §6 (política de release).
- Cambiar los 4 archivos de evidencia de §7.
- Cambiar la composición cerrada del set más allá de los 12 casos (sin ADR).
- Cambiar el contrato de `variance.json` (claves estables).
- Bump de `variance.json::schema_version` por cambio incompatible.
- Cambiar las reglas de §8 (aceptación de un cambio).
