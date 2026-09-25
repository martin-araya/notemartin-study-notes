# ADRs — Architecture Decision Records

Registro de decisiones arquitectónicas del proyecto. Cada ADR es un markdown corto con tres secciones: **Contexto**, **Decisión**, **Consecuencias**.

## Plantilla

```markdown
# ADR-NNNN — Título corto

**Fecha:** YYYY-MM-DD
**Estado:** propuesta | aceptada | sustituida

## Contexto

Qué problema se aborda, qué alternativas se consideraron.

## Decisión

Qué se decide.

## Consecuencias

Qué se gana, qué se pierde, qué queda atado a esta decisión.
```

## Reglas

- Numeración correlativa `ADR-NNNN`.
- Idioma español.
- Las decisiones cerradas (marcadas como `aceptada` en `skills/AGENT.md` §8) **no se reabren** salvo petición explícita del usuario; si se reabre, se crea un ADR nuevo que sustituya al anterior.
- Un ADR atado a un invariante (`INV-xx`) lo referencia en "Consecuencias".

## ADRs ya registradas

- `ADR-0001-units-closed-enum.md` — F37: enum cerrado, criticidad derivada, fusión prohibida en must-keep.
- `ADR-0002-ledger-split.md` — F38: `validate_ledger.py` (linter read-only) y `ledger.py` (operador read+write) conviven con responsabilidades distintas.
- `ADR-0003-concept-graph-edges.md` — F39: nodos desde `definition`, aristas desde `cross-reference` con `relation: prerequisite`, dominio = `vendor+product`.
- `ADR-0004-glossary-model.md` — F40: `knowledge/glossary.json` separado de `manifest.glossary`; sufijos `-<vendor>` para colisiones; definitions array para detectar redefiniciones.

Las decisiones cerradas hasta ahora viven en `skills/AGENT.md` §8. Cuando una de ellas se reabre formalmente, se promueve a ADR aquí.
- `ADR-0005-conflicts-model.md` — F41: storage dual JSON registry + directivas inline `:::contradiction`/`:::discrepancy`; taxonomía cross-cutting de obsolescencia; fuente gana sin excepciones.
