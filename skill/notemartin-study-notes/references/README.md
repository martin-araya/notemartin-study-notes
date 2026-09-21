# `references/`

Prosa normativa para el agente (N3). Cada subcarpeta agrupa archivos por dominio técnico. Las 12 subcarpetas prefijadas fijan el orden de lectura; dentro de cada una, los archivos se citan por nombre y se cargan bajo demanda desde `SKILL.md`.

## Convención

- Nombre de archivo: `kebab-case.md`, nombre por concepto, no por descripción.
- Estructura por archivo (per `AGENT.md` §7.2): Propósito → Cuándo se aplica → Reglas → Ejemplos → Anti-ejemplos → Cómo verificar.
- Toda regla con criterio verificable y, cuando aplique, umbral numérico.
- Máximo 300 líneas por archivo; índice al inicio si se acerca.
- Ejemplos de al menos 2 dominios (INV-15).
- Cero duplicación: si la regla existe en otro archivo, se enlaza.

## Subcarpetas

| Prefijo | Carpeta | Dominio |
|---|---|---|
| 00 | `00-pipeline/` | División de responsabilidades, arquitectura, manifiesto reanudable |
| 01 | `01-ingest/` | OCR, layout, formatos |
| 02 | `02-source-model/` | SDM, anclas, procedencia, semántica editorial |
| 03 | `03-knowledge/` | Unidades, ledger, grafo, plan, terminología, conflictos |
| 04 | `04-authoring/` | NoteMark, IR, marcas, propiedades, capas |
| 05 | `05-note-types/` | Plantillas por tipo de nota |
| 06 | `06-writing/` | Redacción, analogías, ejemplos, comparaciones |
| 07 | `07-visual/` | Diagramas, figuras, tokens, densidad |
| 08 | `08-render/` | Capacidades por destino, contrato, enlaces, publicación |
| 09 | `09-study/` | Estudio activo, autoevaluación, errores, rutas |
| 10 | `10-quality/` | Fidelidad, auditoría de no-pérdida |
| 11 | `11-i18n/` | Idioma bilingüe, citación |

Mapeo completo ruta → entrada N2 (futura `SKILL.md`): [`docs/skill-anatomy.md` §6](../../docs/skill-anatomy.md).
