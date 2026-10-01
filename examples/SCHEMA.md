# SCHEMA — `examples/SCHEMA.md`

> Contrato canónico de los ejemplos end-to-end de F120. Cambiar una clave aquí reabre F120.

## Índice

1. [Ejemplo (directorio)](#1-ejemplo-directorio) · 2. [Artefactos](#2-artefactos) · 3. [Render](#3-render) · 4. [Reportes](#4-reportes)

## 1. Ejemplo (directorio)

Cada ejemplo es un subdirectorio de `examples/` con nombre igual al `case_id` de F118 (sin prefijo numérico opcional). Estructura fija per `README.md` §3.

**Identidad:**

| Campo | Forma | Ejemplo |
|---|---|---|
| `case_id` | snake_case kebab | `01-postgresql-chapter` |
| `corpus_source` | id de `evals/corpus/` | `01-postgresql-chapter` |
| `note_types` | enum cerrada de F44 | `[api-reference]` |
| `profile` | `study` \| `reference` \| `hybrid` | `reference` |

## 2. Artefactos

`artifacts/` contiene los 5 subdirectorios del pipeline:

| Subdir | Archivo(s) | Origen | Validador |
|---|---|---|---|
| raíz | `triage.json` | `scripts/ingest/triage.py` | (sin esquema formal; verificación humana) |
| raíz | `sdm.json` | `scripts/ingest/build_sdm.py` | `scripts/util/validate_sdm.py` (F13) |
| `knowledge/` | `ledger.json` | `scripts/util/ledger.py init/add/mark` | `scripts/util/validate_ledger.py` (F15) |
| `knowledge/` | `note-plan.json` | (synthetic por build_examples) | (sin esquema formal; cross-check con SDM) |
| `knowledge/` | `glossary.json` | (synthetic mínimo) | `glossary.schema.json` (F40) |
| `notemark/` | `<note-id>.nm` | `examples/synthetic-notes/<id>.nm` (curado) | `scripts/validate/validate_notemark.py` (F12) |
| `ir/` | `<note-id>.json` | `parse_notemark.py` (F48) | `scripts/util/validate_ir.py` (F14) |

Forma canónica de cada uno ya está definida en los esquemas F13/F14/F15/F40/F47/F48. No redefinimos aquí.

## 3. Render

`render/` contiene los 5 destinos (3 obligatorios + 2 bonus):

| Destino | Obligatorio | Salida principal | Capturas |
|---|---|---|---|
| `obsidian/` | sí | `<note-id>.md` (F54) | `<note-id>.svg` (sintética) + `<note-id>.png` (si `--real-captures`) |
| `notion_api/` | sí | `payloads/<note-id>-NNN.json` (F55 dry-run) | `<note-id>.svg` |
| `notion_md/` | bonus | `<note-id>.md` (F56) | `<note-id>.svg` |
| `appflowy/` | sí | `<note-id>.md` (F57) | `<note-id>.svg` |
| `html_pdf/` | bonus | `<note-id>.html` (F59) | `<note-id>.svg` |

**Capturas SVG — forma canónica:**

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 1000">
  <rect class="bg" />
  <g class="header">  <!-- título + propiedades --> </g>
  <g class="content"> <!-- cuerpo con admonitions, plegables, etc. --> </g>
  <g class="footer">  <!-- metadatos: source_hash, schema_version, etc. --> </g>
</svg>
```

Cada destino tiene su plantilla en `examples/assets/captures/<destino>.svg.j2` (o `<destino>.svg.tmpl` si no hay Jinja2). El renderer (`examples/capture.py`) instancia la plantilla con los datos del render.

## 4. Reportes

`reports/` contiene 4 archivos canónicos:

| Archivo | Forma | Origen | Lectura |
|---|---|---|---|
| `quality-gate.json` | `schemas/quality-gate.schema.json` (F115) | `scripts/quality_gate.py report` | 1 línea: `summary.errors` debe ser 0 |
| `validator-suite.json` | shape de `evals/validator-suite-sample/` (F113) | `scripts/validate/run_all.py` | por validador: pass / fail / warning |
| `fidelity-audit.json` | shape de `evals/fidelity-audit-sample/` (F114) | `scripts/audit/fidelity_audit.py` | issues por nodo |
| `rubric-application.json` | `evals/suite/rubric-application.md` | build_examples (synthetic) | 8 dimensiones + `approved` |

Para que un ejemplo **cuente como PASS** del criterio C1 de F120, los 4 reportes deben coincidir con:

- `quality-gate.json::summary.errors == 0`
- `validator-suite.json` sin `fail`
- `fidelity-audit.json` sin `severity: critical`
- `rubric-application.json::approved == true`

`build_examples.py` exit 0 cuando los 4 ejemplos cumplen; exit 1 en cualquier fallo.
