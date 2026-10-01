# Aplicación de la rúbrica — `evals/suite/rubric-application.md`

> Cómo aplicar `evals/rubric.md` (F7) a un caso concreto de la suite de evals (F118). Este documento es el puente entre las dos fases: define el procedimiento que sigue un humano (o un agente que simula evaluación humana) para producir `human.json` por caso.

## Índice

1. [Propósito](#1-propósito) · 2. [Cuándo se aplica](#2-cuándo-se-aplica) · 3. [Procedimiento](#3-procedimiento) · 4. [Anclas por caso](#4-anclas-por-caso) · 5. [Pesos y mínimos](#5-pesos-y-mínimos) · 6. [Aprobación](#6-aprobación) · 7. [Comparabilidad](#7-comparabilidad) · 8. [Cambios permitidos](#8-cambios-permitidos)

## 1. Propósito

La rúbrica `evals/rubric.md` define 8 dimensiones con niveles 0–4. La suite de evals ejecuta prompts realistas y produce artefactos por caso en `runs/<run-id>/cases/<case-id>/`. Este documento explica cómo un humano puntúa esos artefactos siguiendo la rúbrica, con anclas calibradoras y sin reinventar criterios.

## 2. Cuándo se aplica

Después de que `check_assertions.py` ha volcado `assertions.json` (con las aserciones automáticas ya evaluadas) y el humano ha revisado el `workdir/` del caso. La evaluación humana es complementaria a las automáticas, no las sustituye.

Si una dimensión es **automáticamente verificable** (marcada "Detección automática: sí" en `rubric.md`), el humano **confirma** el resultado automático, no lo recalcula.

## 3. Procedimiento

```
1. Generar plantilla:
   python3 evals/suite/runner/apply_rubric.py \
     --case evals/suite/cases/<case-id>.yaml \
     --rubric evals/rubric.md \
     --out runs/<run-id>/cases/<case-id>/human.json

2. El evaluador rellena `human.json`:
   - evaluator: nombre o identificador
   - scores.<dim>: 0..4 siguiendo §3 de rubric.md
   - anchors_used: añadir/quitar anclas que efectivamente se usaron
   - notes: observaciones libres

3. Validación manual:
   - global = Σ(weight × score) por dimensión según perfil
   - approved = (global ≥ 2.5) AND (cada dimensión ≥ su mínimo por dimensión)
   - Si falla: registrar motivo en notes; reabrir si la dimensión no estaba clara.

4. Volcado:
   python3 -c "
   import json, sys
   from evals.suite.runner.apply_rubric import compute_global
   h = json.load(open('runs/<run-id>/cases/<case-id>/human.json'))
   g, ok, viol = compute_global(h['scores'], h['profile'])
   h['global_score'] = g
   h['approved'] = ok
   h['min_violations'] = viol
   json.dump(h, open('runs/<run-id>/cases/<case-id>/human.json','w'), indent=2)
   "
```

## 4. Anclas por caso

Las anclas de `evals/rubric.md` §7 son los puntos de calibración. Cada caso declara `anchors_used` en su YAML; el evaluador las lee antes de puntuar.

| Caso | Anclas sugeridas |
|---|---|
| `case-01-postgresql-select` | ANC-03, ANC-04 (referencia pura: tabla exhaustiva, terminología uniforme) |
| `case-02-database-internals-concept` | ANC-01, ANC-06 (study: intuición + analogía + trampas; cobertura parcial justificada) |
| `case-03-rfc-7231-concurrency` | ANC-03, ANC-04 (referencia: prosa precisa, terminología uniforme) |
| `case-04-arxiv-two-column-arch` | ANC-05 (hybrid: arquitectura con diagrama) |
| `case-05-iso-sql-tables-config` | ANC-03, ANC-04 (referencia densa en tablas) |
| `case-13-internet-archive-scan` | ANC-05 (hybrid); consideración: bloques OCR dudosos bajan fidelidad de contenido y render |

## 5. Pesos y mínimos

El script `apply_rubric.py` conoce los pesos y mínimos por dimensión y perfil (de `rubric.md` §5). El evaluador no necesita memorizarlos: están en `weights_and_mins` dentro de la plantilla `human.json`.

**Regla práctica:**
- Si la dimensión tiene `weight: 0`, sigue contando para el mínimo pero no para la media. (Esto cierra la puerta: si render vale 0, no se aprueba la nota — `rubric.md` §5.2.)
- El mínimo siempre se aplica. Aunque la media supere 2.5, si una dimensión cae bajo su mínimo, no aprobada.

## 6. Aprobación

Una nota está aprobada si y solo si:

```
approved = (global ≥ 2.5) AND (todas las dimensiones ≥ su mínimo por dimensión del perfil)
```

Si no aprobada: registrar el motivo en `human.json::min_violations` (lo emite el cálculo del paso 3.4 del procedimiento). Si la dimensión no estaba clara, reabrir F7.

## 7. Comparabilidad

`human.json` tiene claves estables: `scores`, `profile`, `approved`, `global_score`, `min_violations`. Cualquier cambio en estas claves reabre F118.

`compare_runs.py` compara `human_scores` por dimensión y reporta deltas; un cambio de más de 1 nivel en una dimensión entre dos runs dispara una revisión del cambio de skill.

## 8. Cambios permitidos

**No reabren F118:**
- Añadir un nuevo caso (no toca este doc).
- Cambiar las anclas usadas en un caso concreto (es un dato del caso, no del procedimiento).
- Cambiar las notas (`notes`) en `human.json`.

**Reabren F118:**
- Cambiar el procedimiento de §3.
- Cambiar las anclas sugeridas por defecto en §4 (afecta la calibración).
- Cambiar las reglas de aprobación en §6 (criterio normativo).
- Cambiar las claves estables de `human.json` en §7.

**Reabren F7 (no F118):**
- Cambiar una dimensión (nombre, definición, niveles).
- Cambiar pesos o mínimos por perfil.
- Modificar las anclas (más allá de añadir; modificar cambia el contrato de calibración).
