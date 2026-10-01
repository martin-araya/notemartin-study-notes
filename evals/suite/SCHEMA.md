# SCHEMA — `evals/suite/SCHEMA.md`

> Contrato canónico de la Fase 118: forma de un caso, de un run y de un reporte. Cambiar una clave aquí reabre F118.

## Índice

1. [Caso (`cases/<case-id>.yaml`)](#1-caso-casescase-idyaml) · 2. [Run (`runs/<run-id>/`)](#2-run-runsrun-id) · 3. [Reporte (`runs/<run-id>/report.json`)](#3-reporte-runsrun-idreportjson) · 4. [Huella de la skill (`skill_fingerprint.json`)](#4-huella-de-la-skill-skill_fingerprintjson) · 5. [Aserciones](#5-aserciones)

## 1. Caso (`cases/<case-id>.yaml`)

```yaml
id: case-<NN>-<slug>             # snake_case kebab; único en la suite
version: 1.0.0                   # del caso, no de la skill
corpus_source: <corpus-id>       # id existente en evals/corpus/
profile: study | reference | hybrid
prompt: |                        # prompt realista de usuario (≤ 240 palabras)
  ...
expected_outputs:                # lo mínimo que el agente debe producir
  notes_min: 1
  ir_files_min: 1
  ledger_required: true

# Claves hermandas (opcionales, según el caso)
param_table_canonical:           # solo caso 01; usado por param-table-coverage
  schema_version: "1.0.0"
  source_card: evals/corpus/01-postgresql-chapter/card.md
  source_sample_sha256: <hex64>
  extraction_date: <YYYY-MM-DD>
  threshold_min_count: 10
  params:
    - name: table_name
      kind: identifier
      section: FROM
    - name: alias
      kind: identifier
      section: FROM
    ...

expected_code_snippets:          # solo caso 13; usado por ocr-code-fidelity
  schema_version: "1.0.0"
  source_card: evals/corpus/13-internet-archive-scan-hostil/card.md
  status: pending_due_to_missing_sample | ready
  snippets:                      # vacío si status=pending_due_to_missing_sample
    - id: <slug>
      expected_text: <snippet canónico>
      location: <página o sección>
      confidence_floor: 0.85

assertions:
  automatic:
    - id: <unique-within-case>
      type: ledger_coverage | param_table_coverage | ir_validation | sdm_validation | ocr_code_fidelity | fidelity_audit | manifest_valid
      spec:
        # parámetros específicos del tipo (ver §5)
        ...
      threshold: <número, semántica por tipo>
      validator: <ruta relativa al validador>
  human:
    - id: rubric-application
      spec:
        rubric: evals/rubric.md
        dimensions: [fidelity, coverage, traceability, pedagogy, structure, components, operational, render-fidelity]
        # pedagogy y operational se redefinen por perfil en el YAML efectivo
        anchors_used: [ANC-01, ANC-02, ...]
```

### 1.1 Reglas de validación

`check_assertions.py` rechaza el caso si:

- Falta `id`, `corpus_source`, `profile`, `prompt`, `assertions.automatic` o `assertions.human`.
- `profile` no está en `{study, reference, hybrid}`.
- `assertions.automatic` está vacío.
- Una aserción `automatic` no tiene `id`, `type`, `spec`, `threshold` o `validator`.
- Una aserción `automatic.type` no tiene handler registrado.
- Caso 01 sin `param_table_canonical` con `threshold_min_count ≥ 10`.
- Caso 13 sin `expected_code_snippets` con `status ∈ {pending_due_to_missing_sample, ready}`.

## 2. Run (`runs/<run-id>/`)

```
runs/<run-id>/
├── meta.json                   # run_id, timestamp, skill_version, model_id, agent_command, dry_run
├── skill_fingerprint.json      # sha256 de SKILL.md, references/, schemas/, scripts/
├── cases/<case-id>/
│   ├── prompt.txt              # copia del prompt enviado
│   ├── stdout.txt              # salida cruda del agente (puede ser vacía en --dry-run)
│   ├── workdir/                # copia del .notes-work/<hash>/ del agente
│   ├── assertions.json         # resultado de check_assertions.py
│   └── human.json              # volcado de evaluación humana (una entrada por dimensión)
└── report.json                 # resumen global
```

### 2.1 `meta.json`

```json
{
  "run_id": "2026-09-30-r118-001",
  "timestamp": "<ISO-8601>",
  "skill_version": "<git sha o tag>",
  "model_id": "<modelo del agente>",
  "agent_command": "<comando invocado>",
  "dry_run": false
}
```

### 2.2 `assertions.json` (por caso)

```json
{
  "case_id": "case-01-postgresql-select",
  "automatic": [
    {
      "id": "param-table-coverage",
      "type": "param_table_coverage",
      "validator": "evals/suite/runner/check_assertions.py",
      "passed": true,
      "observed": 1.0,
      "threshold": 1.0,
      "evidence": "12/12 parámetros cubiertos; 0 pendientes; 0 descartes",
      "errors": []
    }
  ],
  "human": null
}
```

`human` se rellena por `apply_rubric.py`. Mientras esté `null`, el reporte global marca el caso como `human_pending: true` y lo excluye del `human_global_avg`.

### 2.3 `human.json` (por caso)

```json
{
  "case_id": "case-01-postgresql-select",
  "evaluator": "<humano o agente>",
  "timestamp": "<ISO-8601>",
  "anchors_used": ["ANC-03", "ANC-04"],
  "scores": {
    "fidelity": 4,
    "coverage": 4,
    "traceability": 4,
    "pedagogy": 4,
    "structure": 4,
    "components": 4,
    "operational": 4,
    "render-fidelity": 2
  },
  "profile": "reference",
  "approved": true,
  "notes": "<observaciones libres>"
}
```

Validación: `scores` ∈ 0..4; `approved` = `global ≥ 2.5 AND todas las dimensiones ≥ su mínimo por dimensión del perfil`.

## 3. Reporte (`runs/<run-id>/report.json`)

```json
{
  "schema_version": "1.0.0",
  "run_id": "2026-09-30-r118-001",
  "skill_version": "<git sha o tag>",
  "model_id": "<modelo del agente>",
  "agent_command": "<comando>",
  "skill_fingerprint": "<sha256>",
  "cases": [
    {
      "case_id": "case-01-postgresql-select",
      "corpus_source": "01-postgresql-chapter",
      "profile": "reference",
      "automatic_pass": 3,
      "automatic_total": 3,
      "human_scores": {"fidelity": 4, ...},
      "human_global": 3.85,
      "human_min_dimension_floor": 3,
      "human_pending": false,
      "approved": true
    }
  ],
  "summary": {
    "cases_total": 6,
    "cases_approved": 5,
    "cases_human_pending": 1,
    "automatic_pass_rate": 0.92,
    "human_global_avg": 3.4
  }
}
```

## 4. Huella de la skill (`skill_fingerprint.json`)

```json
{
  "computed_at": "<ISO-8601>",
  "skill_md_sha256": "<hex64>",
  "references_sha256": "<hex64 del tar>",
  "schemas_sha256": "<hex64 del tar>",
  "scripts_sha256": "<hex64 del tar>",
  "composite_sha256": "<hex64>"
}
```

Cambia entre iteraciones de la skill. `compare_runs.py` lo incluye en el diff.

## 5. Aserciones

### 5.1 `param_table_coverage`

`spec`:

```yaml
canonical_ref: <ruta absoluta al caso o clave param_table_canonical>
ledger_path: <workdir>/knowledge/ledger.json
```

Cálculo: contar unidades `must-keep` del ledger con `state` terminal y `target_note` no nulo **cuyo `unit_id` o `source_block_ids` referencia (por nombre de parámetro en `section_path` o en cualquier campo de texto de `notes`/`unit_id`)** los parámetros de `param_table_canonical.params[].name`. Un parámetro se considera cubierto si aparece en la nota destino del ledger.

`threshold`: 1.0 (100 % de cobertura).

`passed`: `(covered / total) ≥ threshold`.

### 5.2 `ocr_code_fidelity`

`spec`:

```yaml
snippets_ref: <ruta a expected_code_snippets>
sdm_or_ocr_path: <workdir>/sdm.json | <workdir>/ingest/ocr_summary.json
edit_distance_threshold: 0.85
```

Cálculo: por cada `snippet.id`, buscar el bloque OCR (`origin=ocr` y `type=code`) que mejor coincida por `section_path` o posición; calcular `1 - edit_distance / max(len_a, len_b)`; promedio de ratios.

`threshold`: 0.85 (declarado en plan §D5).

Si `expected_code_snippets.status == pending_due_to_missing_sample`, la aserción queda `status: pending` (no cuenta como pass ni fail; warning en `assertions.json`).

### 5.3 `ledger_coverage`, `ir_validation`, `sdm_validation`, `fidelity_audit`, `manifest_valid`

Disparan el validator declarado con `--coverage` / `--validate` / `--inspect` y comparan contra `threshold`. El handler específico está en `check_assertions.py`.

### 5.4 Tipos de aserción — formas canónicas del threshold

| type | threshold | semántica |
|---|---|---|
| `param_table_coverage` | ratio 0..1 | proporción de params canónicos cubiertos |
| `ocr_code_fidelity` | ratio 0..1 | fidelidad media del código OCR |
| `ledger_coverage` | ratio 0..1 | cobertura de unidades must-keep |
| `ir_validation` | 1.0 | validación pasa |
| `sdm_validation` | 1.0 | validación pasa |
| `fidelity_audit` | 1.0 | cero invenciones |
| `manifest_valid` | 1.0 | esquema válido |
