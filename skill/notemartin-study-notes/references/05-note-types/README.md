# `references/05-note-types/`

Plantillas de los 15 tipos de nota. Cada archivo define secciones obligatorias y opcionales en NoteMark, componentes mínimos, reglas de contenido, checklist propio y nota mínima viable.

## Orden de lectura

Cargar cuando el agente ya ha decidido el tipo de nota (F93 selector).

## Estado actual

Los 15 archivos están pendientes:

- `concept.md` `[pendiente F78]`
- `api-reference.md` `[pendiente F79]`
- `procedure.md` `[pendiente F80]`
- `configuration.md` `[pendiente F81]`
- `error-troubleshooting.md` `[pendiente F82]`
- `architecture.md` `[pendiente F83]`
- `syntax.md` `[pendiente F84]`
- `data-model.md` `[pendiente F85]`
- `chapter-digest.md` `[pendiente F86]`
- `comparison.md` `[pendiente F87]`
- `version-delta.md` `[pendiente F88]`
- `glossary-term.md` `[pendiente F89]`
- `cheatsheet.md` `[pendiente F90]`
- `index-moc.md` `[pendiente F91]`
- `practice.md` `[pendiente F92]`

## Quién lee / quién produce

El agente lee el archivo del tipo elegido. Cada fase `F78`-`F92` produce su archivo.

## Referencia cruzada

Estos 15 tipos son los valores cerrados del campo `notes[].type` en `knowledge/note-plan.json` (F44, `references/03-knowledge/note-plan.md` §3). El plan asigna unidades del ledger a uno de estos tipos siguiendo las reglas de división semántica (F44 §4) y la resolución de colisiones (F44 §5).
