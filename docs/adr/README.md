# ADRs — Architecture Decision Records

Registro de decisiones arquitectónicas del proyecto. Cada ADR es un markdown corto con tres secciones: **Contexto**, **Decisión**, **Consecuencias**.

> Documentos complementarios: [`CONTRIBUTING.md`](../../CONTRIBUTING.md) §2 (triada regla→motivación→prueba), [`references/00-pipeline/contributing.md`](../../skill/notemartin-study-notes/references/00-pipeline/contributing.md) (estilo de referencias), [`VERSIONING.md`](../../VERSIONING.md) (cuándo bumpear major — los ADRs pueden motivar un bump).

## Plantilla

```markdown
# ADR-NNNN — Título corto

**Fecha:** YYYY-MM-DD
**Estado:** propuesta | aceptada | sustituida
**Atada a:** F<phase>, INV-<id>, ADR-<id>

## Contexto

Qué problema se aborda, qué alternativas se consideraron.
Caso de fallo real que motiva la decisión (per CONTRIBUTING.md §2 triada).

## Decisión

Qué se decide.

## Consecuencias

Qué se gana, qué se pierde, qué queda atado a esta decisión.
Si la decisión afecta al contrato de artefactos, indicar el schema_version afectado.
```

## Reglas

- Numeración correlativa `ADR-NNNN`.
- Idioma español.
- Las decisiones cerradas (marcadas como `aceptada` en `skills/AGENT.md` §8) **no se reabren** salvo petición explícita del usuario; si se reabre, se crea un ADR nuevo que sustituya al anterior.
- Un ADR atado a un invariante (`INV-xx`) lo referencia en "Consecuencias".
- Todo ADR nuevo sigue la **triada** de CONTRIBUTING.md §2 (motivación + definición + caso de prueba).
- Para registrar un conversor externo (per `docs/external-ingest-contract.md` §6), abrir un ADR con nombre `ADR-NNNN-external-converter-<nombre>.md`.

## ADRs ya registradas

- `ADR-0001-units-closed-enum.md` — F37: enum cerrado, criticidad derivada, fusión prohibida en must-keep.
- `ADR-0002-ledger-split.md` — F38: `validate_ledger.py` (linter read-only) y `ledger.py` (operador read+write) conviven con responsabilidades distintas.
- `ADR-0003-concept-graph-edges.md` — F39: nodos desde `definition`, aristas desde `cross-reference` con `relation: prerequisite`, dominio = `vendor+product`.
- `ADR-0004-glossary-model.md` — F40: `knowledge/glossary.json` separado de `manifest.glossary`; sufijos `-<vendor>` para colisiones; definitions array para detectar redefiniciones.
- `ADR-0005-conflicts-model.md` — F41: storage dual JSON registry + directivas inline `:::contradiction`/`:::discrepancy`; taxonomía cross-cutting de obsolescencia; fuente gana sin excepciones.
- `ADR-0006-fidelity-levels.md` — F42: tres niveles source/derived/external; tagging dual `:::external`+`:::derived`; prohibiciones absolutas sobre 7 categorías de valores técnicos; regla de la duda.
- `ADR-0007-completeness-audit.md` — F43: forward pass + inverse sample estratificado (100% must-keep + 10% context) + threshold gate 100%; sin flag `--allow-critical`.
- `ADR-0008-note-plan-model.md` — F44: enum cerrada de 15 tipos (F78-F92); división semántica (no por conteo); umbral combinado (notes_planned > 5 OR total_must_keep > 30); resolución de colisiones con `reuse`/`new`.
- `ADR-0009-render-contract.md` — F53: contrato del renderer (interfaz pura + tabla cerrada de degradación 20 filas); cinco invariantes RC-01…RC-05; reporte doble JSON+Markdown generado siempre.
- `ADR-0010-notion-renderer.md` — F55: renderer Notion API; dialecto canónico `notion_api` (D1, cierra discrepancia F53↔F11); cliente HTTP `urllib.request` stdlib puro (D2); anidamiento en 2 pasadas con placeholders (D3); idempotencia por `notemartin_note_id` property (D4).

Las decisiones cerradas hasta ahora viven en `skills/AGENT.md` §8. Cuando una de ellas se reabre formalmente, se promueve a ADR aquí.

## Cómo abrir un ADR nuevo

```bash
# 1. Copia la plantilla.
cp docs/adr/ADR-NNNN-template.md docs/adr/ADR-0011-<slug>.md

# 2. Edita el nuevo ADR siguiendo la plantilla y la triada de CONTRIBUTING.md §2.

# 3. Lista el ADR nuevo en la sección "ADRs ya registradas" de este README.

# 4. (Opcional) Adjúntalo a un PR; scripts/check_pr.py item 10 lo detecta como warning si no.
```
