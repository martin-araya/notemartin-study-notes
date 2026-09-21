# `references/04-authoring/`

Reglas de L3 (autoría): gramática NoteMark, catálogo del IR, marcas inline, propiedades, capas de profundidad.

## Orden de lectura

Cargar al redactar cualquier nota. `notemark.md` siempre; el resto según el tipo de marca o nodo en uso.

## Estado actual

- `notemark.md` `[pendiente F12]`
- `ir-spec.md` `[pendiente F14]`
- `block-directives.md` `[pendiente F45]`
- `inline-marks.md` `[pendiente F46]`
- `properties.md` `[pendiente F47]`
- `depth-layers.md` `[pendiente F51]`

## Quién lee / quién produce

| Archivo | Lee | Produce |
|---|---|---|
| `notemark.md` | Agente al redactar | F12 |
| `ir-spec.md` | F48 (parser), F49 (validador) | F14 |
| `block-directives.md` | Agente al elegir directiva | F45 |
| `inline-marks.md` | Agente al insertar marcas | F46 |
| `properties.md` | Agente al definir YAML | F47 |
| `depth-layers.md` | Agente al estructurar nota extensa | F51 |

## Restricción especial

Ni una mención de plataforma en esta carpeta (`INV-06`).
