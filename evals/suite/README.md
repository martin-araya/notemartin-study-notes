# Suite de evals de la skill — `evals/suite/`

> Documento normativo de la **Fase 118** del roadmap. Suite ejecutable, repetible y comparable, en la que un agente carga la skill y procesa fuentes reales del corpus mediante prompts realistas.
>
> Documentos complementarios: `evals/rubric.md` (F7, rúbrica), `evals/corpus/` (F6, fuentes), `evals/trigger-eval/` (F10, precedente de patrón de carpeta + run), `skills/AGENT.md` §11 (pruebas "de la skill").

## Índice

1. [Propósito y alcance](#1-propósito-y-alcance) · 2. [Estructura](#2-estructura) · 3. [Los 6 casos](#3-los-6-casos) · 4. [Cómo ejecutar](#4-cómo-ejecutar) · 5. [Comparar iteraciones](#5-comparar-iteraciones) · 6. [Aplicar la rúbrica](#6-aplicar-la-rúbrica) · 7. [Aserciones automáticas](#7-aserciones-automáticas) · 8. [Cómo verificar](#8-cómo-verificar) · 9. [Cambios permitidos](#9-cambios-permitidos)

## 1. Propósito y alcance

Esta suite ejecuta la skill sobre fuentes reales del corpus (F6) mediante prompts realistas de usuario, y mide el resultado combinando aserciones automáticas (scripts del proyecto) y evaluación humana con rúbrica (F7).

**Qué cierra:**
- **C1** Cada caso declara aserciones automáticas y criterios humanos.
- **C2** El caso Oracle (`case-01-postgresql-select`) incluye aserción de cobertura de tabla de parámetros.
- **C3** El caso escaneado (`case-13-internet-archive-scan`) incluye aserción de fidelidad de código OCR.
- **C4** Los resultados son comparables entre iteraciones de la skill.

**Qué NO es:**
- No es un test unitario de los scripts (eso vive en `tests/` y `evals/<fase>-sample/`).
- No es la rúbrica (eso es `evals/rubric.md`).
- No es un eval de disparo de la `description` (eso es `evals/trigger-eval/`).
- No es una suite LLM-as-judge. La evaluación humana se hace por humano (o por un agente que sigue `rubric-application.md`); un LLM-as-judge queda como mejora ADR futura.

## 2. Estructura

```
evals/suite/
├── README.md                # este archivo
├── SCHEMA.md                # contrato de caso + run + reporte (forma canónica)
├── rubric-application.md    # cómo aplicar evals/rubric.md con anclas a un caso
├── cases/                   # definiciones YAML de los 6 casos
│   ├── case-01-postgresql-select.yaml
│   ├── case-02-database-internals-concept.yaml
│   ├── case-03-rfc-7231-concurrency.yaml
│   ├── case-04-arxiv-two-column-arch.yaml
│   ├── case-05-iso-sql-tables-config.yaml
│   └── case-13-internet-archive-scan.yaml
└── runner/                  # scripts del runner
    ├── run_case.py          # ejecuta agente + captura workdir + stdout
    ├── build_canonical.py   # genera param_table_canonical desde HTML
    ├── check_assertions.py  # evalúa aserciones automáticas
    ├── apply_rubric.py      # asiste a un humano a volcar human.json
    └── compare_runs.py      # diff entre dos runs por case_id
```

## 3. Los 6 casos

| Case ID | Corpus source | Perfil | Categoría roadmap |
|---|---|---|---|
| `case-01-postgresql-select` | `01-postgresql-chapter` | `reference` | documentación Oracle (sustituto: PostgreSQL) |
| `case-02-database-internals-concept` | `02-database-internals-chapter` | `study` | libro técnico de editorial |
| `case-03-rfc-7231-concurrency` | `03-rfc-7231` | `reference` | RFC |
| `case-04-arxiv-two-column-arch` | `04-arxiv-two-column` | `hybrid` | PDF a dos columnas |
| `case-05-iso-sql-tables-config` | `05-iso-sql-tables` | `reference` | documento con 20+ tablas / ≥ 200 pp |
| `case-13-internet-archive-scan` | `13-internet-archive-scan-hostil` | `hybrid` | **hostil**: escaneo torcido + OCR sucio |

Cada caso declara (ver `SCHEMA.md`):
- `corpus_source`: id del corpus.
- `profile`: `study` | `reference` | `hybrid` (define la dimensión pedagogía en la rúbrica).
- `prompt`: prompt realista de usuario (≤ 240 palabras).
- `expected_outputs`: workdir mínimo esperado (notas, IR, ledger).
- `assertions.automatic[]`: ≥ 3 aserciones verificables por scripts.
- `assertions.human[]`: 8 dimensiones de la rúbrica + anclas a usar.

Casos añadibles sin reabrir F118: añadir un YAML en `cases/` siguiendo `SCHEMA.md`. Si cambia una clave de `report.json` o un id de aserción existente, **sí** reabre.

## 4. Cómo ejecutar

Modo material (con agente en producción):

```bash
python evals/suite/runner/run_case.py \
  --case evals/suite/cases/case-01-postgresql-select.yaml \
  --agent-command "<comando del agente que carga la skill>" \
  --run-id 2026-09-30-r118-001
```

Modo dry-run (sin agente; el humano completa `workdir/` y `human.json`):

```bash
python evals/suite/runner/run_case.py \
  --case evals/suite/cases/case-01-postgresql-select.yaml \
  --dry-run \
  --run-id 2026-09-30-r118-001
```

Evaluación de aserciones automáticas:

```bash
python evals/suite/runner/check_assertions.py \
  --case evals/suite/cases/case-01-postgresql-select.yaml \
  --run-dir evals/runs/2026-09-30-r118-001
```

Aplicar la rúbrica (asistente para humanos):

```bash
python evals/suite/runner/apply_rubric.py \
  --case evals/suite/cases/case-01-postgresql-select.yaml \
  --rubric evals/rubric.md \
  --out evals/runs/2026-09-30-r118-001/cases/case-01-postgresql-select/human.json
```

## 5. Comparar iteraciones

```bash
python evals/suite/runner/compare_runs.py \
  evals/runs/2026-09-30-r118-001 \
  evals/runs/2026-10-15-r118-002 \
  --markdown
```

Produce `diff.json` con deltas por case_id y por clave de aserción. Si la huella de la skill (`skill_fingerprint.json`) cambió, lo señala.

## 6. Aplicar la rúbrica

Ver `rubric-application.md`. Resumen: el humano usa `apply_rubric.py` para generar una plantilla, la rellena siguiendo las anclas de `evals/rubric.md` §7 (ANC-01..ANC-06), y la guarda en `human.json`. Las 8 dimensiones son: fidelidad, cobertura, trazabilidad, pedagogía (por perfil), estructura, componentes, utilidad operativa (por perfil), fidelidad de render.

## 7. Aserciones automáticas

Tipos soportados (handlers en `check_assertions.py`):

| Tipo | Qué mide | Validator |
|---|---|---|
| `ledger_coverage` | % de unidades `must-keep` con estado terminal | `scripts/util/validate_ledger.py` |
| `param_table_coverage` | % de parámetros canónicos cubiertos en `knowledge/ledger.json` | `evals/suite/runner/check_assertions.py` (handler propio) |
| `ir_validation` | El IR parsea sin errores y resuelve `source_refs` | `scripts/util/validate_ir.py` |
| `sdm_validation` | El SDM parsea y tiene anchors resolubles | `scripts/util/validate_sdm.py` |
| `ocr_code_fidelity` | Edit-distance-ratio ≥ 0.85 por bloque de código OCR | handler propio sobre `ingest/ocr_summary.json` o `sdm.json` bloques `code` |
| `fidelity_audit` | Cero invenciones detectadas | `evals/fidelity-sample/run_eval.py` |
| `manifest_valid` | El `manifest.json` declara la nota publicada | `scripts/util/validate_manifest.py` (cuando exista) |

Tipos nuevos requieren reabrir F118 (ver §9).

## 8. Cómo verificar

Lista grepeable:

```
test -d evals/suite                                          → existe
test -f evals/suite/README.md                                → existe
test -f evals/suite/SCHEMA.md                                → existe
test -f evals/suite/rubric-application.md                    → existe
ls evals/suite/cases/*.yaml | wc -l                          → 6
rg -c '^  automatic:' evals/suite/cases/*.yaml               → 6 (uno por caso)
rg -c '^  human:' evals/suite/cases/*.yaml                   → 6
rg -c 'param-table-coverage' evals/suite/cases/*.yaml        → 1 (caso 01)
rg -c 'ocr-code-fidelity' evals/suite/cases/*.yaml           → 1 (caso 13)
test -f evals/suite/runner/run_case.py                       → existe
test -f evals/suite/runner/check_assertions.py               → existe
test -f evals/suite/runner/compare_runs.py                   → existe
test -f evals/suite/runner/apply_rubric.py                   → existe
test -f evals/suite/runner/build_canonical.py                → existe
test -d evals/runs/<run-id>                                  → existe primera corrida
```

## 9. Cambios permitidos

**No reabren F118:**
- Añadir un caso YAML (manteniendo `SCHEMA.md`).
- Añadir consultas al set.
- Reemplazar el script del runner por una versión más rica con misma entrada/salida.
- Cambiar el `prompt` de un caso (es dato).

**Reabren F118:**
- Cambiar `report.json` keys.
- Cambiar un id de aserción existente.
- Cambiar un umbral por defecto (p. ej. `param_table_coverage` threshold = 1.0).
- Añadir un nuevo `type` de aserción.
- Cambiar la lista cerrada de casos (ahora 6; pasar a 5 o 7).
- Cambiar `skill_fingerprint.json` campos.
