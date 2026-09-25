# ADR-0005 — Modelo de contradicciones y obsolescencia (Fase 41)

**Fecha:** 2026-09-25
**Estado:** aceptada
**Atada a:** F41, F12 (notemark), F15 (ledger), F35 (editorial-semantics), F37 (information-units), F39 (concept-graph), F40 (terminology), F42 (fidelity-rules)

## Contexto

Fase 41 documenta contradicciones internas y formaliza la taxonomía de obsolescencia. La detección es semántica (no automatizable); la documentación es estructural. Las alternativas consideradas:

1. **Solo inline en NoteMark** — directivas `:::contradiction` dispersas; el eval tendría que parsear cada nota. Descartada: no hay punto único de verdad.
2. **Solo JSON registry** sin directivas inline — el renderer tiene que resolver anclas a entries del JSON por id. Descartada: el cuerpo no señala visualmente la contradicción.
3. **JSON registry + directivas inline** (elegida) — el JSON es la fuente de verdad; las directivas inline señalan al lector en el punto del cuerpo donde aplica.

## Decisión

1. **Storage dual**: `knowledge/conflicts.json` (registry canónico) + directivas `:::contradiction` y `:::discrepancy` en NoteMark (F12). Decisión confirmada por el usuario en planning.

2. **Tipos cerrados** (enum):
   - `source-vs-source`: dos partes de la fuente se contradicen.
   - `source-vs-derived`: la fuente dice X pero el modelo deriva Y.
   - `source-vs-external`: la fuente es silenciosa; el agente usa conocimiento externo.
   - `deprecation-mismatch`: marcado inconsistente (current vs deprecated).
   - `version-mismatch`: información de versión inconsistente entre capítulos.
   - Extensible solo vía reabrir F41. Enum cerrada porque permite validación mecánica por `jsonschema`.

3. **Anchors** de 3 tipos: `block` (F13, sha1 hex 12), `note` (F38, `target_note`), `concept` (F39, `concept_id`). Cada contradicción tiene ≥ 2 anchors de tipos o instancias distintas.

4. **Estados cerrados**: `open` / `resolved` / `unresolved`. Sin transiciones implícitas; el agente actualiza explícitamente.

5. **Resolución fuente-wins (R6)**: cuando `type=source-vs-derived`, el cuerpo refleja la fuente y `model_says` se popula con la derivación del modelo. Sin excepciones. Coherente con F42 (reglas de fidelidad) y AGENT.md INV-09 ("Los literales de la fuente se conservan textualmente").

6. **Taxonomía cross-cutting de obsolescencia**: enum cerrada `current` / `preview` / `deprecated` / `legacy` / `removed`. Aplica a:
   - `glossary.json` (F40): `term.deprecation_status`.
   - `concept-graph.json` (F39): `node.deprecation_status`.
   - `ledger.json` (F15/F38): `entry.deprecation_status`.
   - Notas (F12): directivas inline `:::deprecated`.
   - Cajas editoriales (F35): reusa `severity: deprecated`/`removed`.
   - `version-note` (F37): reusa `version_removed`.

   **Sin redefinir** el enum en cada lugar. Si un mecanismo nuevo quiere un valor adicional, se reabre F41.

7. **Directivas NoteMark** añadidas a F12 §4:
   - `:::contradiction id="c_001"` — apunta al registry.
   - `:::discrepancy source-says="X" model-says="Y"` — inline diff fuente vs modelo.

8. **Sin script de mantenimiento**: la detección es semántica. El eval verifica que las contradicciones documentadas cumplan las reglas, no que el agente detecte todas.

## Consecuencias

**Gana**:
- Las contradicciones tienen un punto de verdad único (registry JSON).
- El cuerpo de las notas señala visualmente las contradicciones (insignia "⚠").
- La regla "fuente gana" se enforza por diseño: el cuerpo refleja la fuente, el modelo se documenta en `model_says`.
- La taxonomía de obsolescencia se comparte cross-cutting; los mecanismos existentes (F35 `severity`, F37 `version_removed`, F40 `definitions[].status`) se referencian sin redefinirse.

**Pierde**:
- Las directivas inline pueden quedar desincronizadas con el registry. Mitigado por el eval (sub-check 3): toda directiva `:::contradiction` debe tener un id válido en el registry.
- Añadir un valor a la enum de tipos requiere reabrir F41. Razón: las enums cerradas son la base de la validación mecánica.

**Queda atado**:
- F12 (notemark): las directivas `:::contradiction` y `:::discrepancy` se añaden a §4.
- F15/F38 (ledger): `entry.deprecation_status` es opcional (`null` permitido).
- F37 (information-units): `version-note.version_removed` se mapea a `deprecation_status=removed`.
- F40 (terminology): `term.deprecation_status` es opcional.
- F42 (fidelity-rules): la regla "fuente gana" se invoca desde aquí.
- F43 (auditoría): ejecuta `check` sobre `conflicts.json`.
