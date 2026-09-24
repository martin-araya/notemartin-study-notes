# `references/02-source-model/`

Reglas del SDM: contrato del bloque, anclas, procedencia, semántica editorial.

## Orden de lectura

Cargar en L1 (construcción del SDM) y cada vez que el agente consulta anclas.

## Estado actual

- `spec.md` (F13) — contrato del SDM y fórmula del id.
- `build-sdm.md` (F31) — mecánica de ensamblado.
- `anchors.md` (F32) — anclas sintéticas estables; numeración duplicada/saltada; persistencia.
- `provenance.md` `[pendiente F34]` — metadatos editoriales.
- `editorial-semantics.md` `[pendiente F35]` — cajas Nota/Precaución/Ejemplo.

## Quién lee / quién produce

| Archivo | Lee | Produce |
|---|---|---|
| `spec.md` | L1 (construir SDM), L2 (en anclas), L4 (en assets) | F13 |
| `build-sdm.md` | L1 (consumir L0 → emitir sdm.json) | F31 |
| `anchors.md` | L1 (al derivar `section_path`), L2 (al construir `source_block_ids`), L3 (al redactar `{src:blk_xxxx}`), L4 (al resolver deep-links) | F32 |
| `provenance.md` | L1 al clasificar, L3 al redactar propiedades | F34 |
| `editorial-semantics.md` | L1 al clasificar regiones editoriales | F35 |
