# `schemas/`

JSON Schema versionados de los artefactos del workdir (`references/00-pipeline/architecture.md` §4).

## Qué vivirá aquí

| Schema | Artefacto | Fase |
|---|---|---|
| `profile.schema.json` | `.notes-work/<hash>/profile.yaml` | F11 |
| `sdm.schema.json` | `sdm.json` | F13 |
| `note-ir.schema.json` | `ir/<note-id>.json` | F14 |
| `ledger.schema.json` | `knowledge/ledger.json` | F15 |
| `manifest.schema.json` | `manifest.json` | F16 |

## Reglas (per `AGENT.md` §7.4)

- Cada schema con descripción por campo y `schema_version` obligatorio.
- Todo artefacto persistido lleva `schema_version`; el cargador rechaza versiones incompatibles con mensaje claro.
- Cambios incompatibles (tipo, semántica u obligatoriedad) → versión mayor.
- Cambios compatibles (campo opcional nuevo) → versión menor.

## Cuándo se crea

Esta carpeta se puebla desde F11 en adelante. Hoy está vacía por diseño: las fases productoras aún no han corrido.
