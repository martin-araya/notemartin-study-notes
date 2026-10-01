# Set de regresión y varianza — `evals/regression/`

> Documento normativo de la **Fase 119** del roadmap. Cierra la varianza intra-run, el set de regresión con casos problemáticos conocidos, y el gate que bloquea un release cuando una métrica cae fuera de umbral o un caso del set cambia su aprobación.
>
> Documentos complementarios: `evals/suite/README.md` y `SCHEMA.md` (F118, runner + comparador), `evals/rubric.md` (F7, rúbrica humana), `evals/corpus/` (F6, fuentes), `docs/release.md` (F119, proceso de release).

## Índice

1. [Propósito y alcance](#1-propósito-y-alcance) · 2. [Estructura](#2-estructura) · 3. [Set de regresión](#3-set-de-regresión) · 4. [Cómo se ejecuta](#4-cómo-se-ejecuta) · 5. [Cómo se cierra un release](#5-cómo-se-cierra-un-release) · 6. [Variabilidad y umbrales](#6-variabilidad-y-umbrales) · 7. [Cambios permitidos](#7-cambios-permitidos)

## 1. Propósito y alcance

Esta carpeta convierte la suite de F118 en un sistema que mide **varianza intra-caso**, mantiene un **set de regresión curado**, y bloquea un **release** cuando una métrica cae fuera de umbral o un caso del set cambia su aprobación entre candidato y baseline.

**Qué cierra (criterios del ROADMAP):**
- **C1.** La varianza de cobertura está bajo el umbral definido.
- **C2.** La suite corre antes de cada release.
- **C3.** Todo cambio aceptado tiene evidencia de no-regresión.

**Qué NO es:**
- No es un test unitario de los scripts (eso vive en `tests/` y `evals/<fase>-sample/`).
- No es la rúbrica humana (eso es `evals/rubric.md`).
- No es la suite de evals de la skill (eso es `evals/suite/`, F118).
- No es la política de versionado semántico (eso es F123).
- No es la integración con un CI concreto; F119 entrega un comando portable.

## 2. Estructura

```
evals/regression/
├── README.md                     # este archivo
├── SET.md                        # qué casos y por qué
├── variance.md                   # spec normativa de varianza y umbrales
├── variance_thresholds.yaml      # umbrales numéricos versionados
├── cases/                        # definiciones YAML del set de regresión
│   ├── case-01-postgresql-select.ref.yaml       # referencia al caso F118
│   ├── case-04-arxiv-two-column-arch.ref.yaml  # referencia al caso F118
│   ├── case-05-iso-sql-tables-config.ref.yaml  # referencia al caso F118
│   ├── case-13-internet-archive-scan.ref.yaml  # referencia al caso F118
│   ├── case-09-conference-slides-diag.yaml     # caso nuevo (F119)
│   └── case-06-kubernetes-api-ref-params.yaml  # caso nuevo (F119)
└── fixtures/                     # artefactos de referencia (golden) por caso
    └── <case-id>/                # sdm.json + ledger.json + notemark/ + ir/ + report.json
```

## 3. Set de regresión

Ver `SET.md` para la composición y justificación. Resumen:

| Case ID | Origen | Categoría | Métrica de regresión primaria |
|---|---|---|---|
| `case-01-postgresql-select` | F118 (referenciado) | documentación Oracle | cobertura de parámetros canónicos |
| `case-04-arxiv-two-column-arch` | F118 (referenciado) | PDF dos columnas | lectura columnar / IR ordenado |
| `case-05-iso-sql-tables-config` | F118 (referenciado) | tabla exhaustiva ≥ 200 pp | truncado (INV-10) |
| `case-13-internet-archive-scan` | F118 (referenciado, sample pendiente F6) | hostil: escaneo torcido | fidelidad de código OCR |
| `case-09-conference-slides-diag` | F119 nuevo | diapositivas (PPT) | ingesta PPT + decisión diagram/slide |
| `case-06-kubernetes-api-ref-params` | F119 nuevo | API reference | tabla de parámetros exhaustiva |

**Política de extensión:** añadir un caso solo cuando ha aparecido una regresión real en el corpus o cuando el caso ya es estable y queremos blindarlo. Máximo soft-cap de 12 casos (registrado en `SET.md`).

## 4. Cómo se ejecuta

```bash
# N ejecuciones de cada caso del set de regresión.
python evals/suite/runner/run_regression.py \
  --case-dir evals/regression/cases/ \
  --n-runs 5 \
  --agent-command "<comando del agente que carga la skill>" \
  --thresholds evals/regression/variance_thresholds.yaml \
  --release-tag v0.1.0 \
  --out-dir evals/runs/v0.1.0/
```

El runner:
1. Para cada caso YAML en `cases/`, ejecuta `run_case.py` N veces.
2. Cada ejecución produce un workdir aislado bajo `runs/<release-tag>/cases/<case-id>/run-N/` con `assertions.json` + `human.json`.
3. Tras las N ejecuciones, calcula media, stdev, min, max, rango, coeficiente de variación por métrica (`coverage_must_keep_terminal`, `notes_planned`, `ir_node_count`, `human_global`, `approved`) por caso.
4. Compara cada métrica contra `variance_thresholds.yaml`.
5. Emite `runs/<release-tag>/variance.json` con la forma descrita en `variance.md` §5.

## 5. Cómo se cierra un release

Ver `docs/release.md` (entregable de F119). Resumen:

1. Generar `baseline` corriendo `run_regression.py` sobre el último release tag.
2. Generar `candidate` corriendo `run_regression.py` sobre el commit candidato.
3. Correr `release_gate.py --candidate X --baseline Y --variance Z`.
4. Si pass: archivar 4 archivos en `runs/<release-tag>/evidence/`.
5. Taggear el commit.

## 6. Variabilidad y umbrales

Ver `variance.md` para la spec completa y `variance_thresholds.yaml` para los valores numéricos. Las 5 métricas medidas son:

- **M1.** `coverage_must_keep_terminal` — stdev ≤ 0.05 entre N ejecuciones.
- **M2.** `notes_planned` — stdev ≤ 1 nota.
- **M3.** `ir_node_count` — stdev ≤ 10 % del valor medio.
- **M4.** `human_global_avg` — stdev ≤ 0.5 puntos.
- **M5.** `approved_rate` — siempre 1.0 (cualquier flip en el set de regresión bloquea).

## 7. Cambios permitidos

**No reabren F119:**
- Añadir un caso al set de regresión (es dato).
- Cambiar los umbrales en `variance_thresholds.yaml` (con commit + nota en CHANGELOG; ADR si el cambio es > 20 %).
- Cambiar `n_runs` (con commit + nota).
- Cambiar `release-tag` (es dato de cada corrida).

**Reabren F119:**
- Cambiar una métrica de varianza (M1..M5).
- Cambiar la política de release (qué condiciones bloquean).
- Cambiar los 4 archivos de evidencia de no-regresión.
- Cambiar la composición cerrada del set de regresión más allá de los 12 casos.
- Cambiar el contrato de `variance.json` (claves estables).
