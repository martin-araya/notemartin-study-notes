# `references/05-note-types/`

Plantillas de los 15 tipos de nota. Cada archivo define secciones obligatorias y opcionales en NoteMark, componentes mínimos, reglas de contenido, checklist propio y nota mínima viable.

## Orden de lectura

Cargar cuando el agente ya ha decidido el tipo de nota (F93 selector).

## Estado actual

Los 15 archivos están pendientes (F78-F92). Cada uno instancia el patrón canónico de
`references/07-visual/note-templates.md` (F75), que define la cabecera común, el
patrón de apertura/cierre y la jerarquía visual por tipo. La densidad por tipo
se mide contra la tabla cerrada R1-R8 de `references/07-visual/density.md` (F76),
con exenciones explícitas para glossary-term, cheatsheet e index-moc.

- `concept.md`
- `api-reference.md`
- `procedure.md`
- `configuration.md`
- `error-troubleshooting.md`
- `architecture.md`
- `syntax.md`
- `data-model.md`
- `chapter-digest.md`
- `comparison.md`
- `version-delta.md`
- `glossary-term.md`
- `cheatsheet.md`
- `index-moc.md`
- `practice.md`
- `selector.md`

## Quién lee / quién produce

El agente lee el archivo del tipo elegido. Cada fase `F78`-`F93` produce su archivo.

## Referencia cruzada

Estos 15 tipos son los valores cerrados del campo `notes[].type` en `knowledge/note-plan.json` (F44, `references/03-knowledge/note-plan.md` §3). El plan asigna unidades del ledger a uno de estos tipos siguiendo las reglas de división semántica (F44 §4) y la resolución de colisiones (F44 §5).
