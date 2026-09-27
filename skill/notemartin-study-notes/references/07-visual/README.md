# `references/07-visual/`

Reglas visuales: catálogo de diagramas, Mermaid portable, diagramas monoespaciados, reconstrucción, accesibilidad, tokens, mapeo de estilo, plantillas, densidad.

## Orden de lectura

Cargar al elegir tipo de diagrama o estilo visual; cargar `tokens.md` antes de cualquier CSS.

## Estado actual

- `diagram-catalog.md` `[existente]` — F65 ✅
- `mermaid-portable.md` `[existente]` — F66 ✅
- `monospace-diagrams.md` `[existente]` — F69 ✅
- `reconstruction.md` `[existente]` — F71 ✅
- `accessibility.md` `[existente]` — F71 ✅
- `tokens.md` `[existente]` — F72 ✅
- `style-mapping.md` `[existente]` — F73 ✅
- `note-templates.md` `[existente]` — F75 ✅
- `density.md` `[existente]` — F76 ✅

## Quién lee / quién produce

| Archivo | Lee | Produce |
|---|---|---|
| `diagram-catalog.md` | Agente al elegir diagrama; F67 (validador) | F65 |
| `mermaid-portable.md` | Agente y F67 (validador) | F66 |
| `monospace-diagrams.md` | Agente al decidir entre tipos | F69 |
| `reconstruction.md` | Agente y F67 (validador) ante diagrama impreso | F71 |
| `accessibility.md` | Agente, revisor visual, F67 (L-06 alt), F70 (paleta) | F71 |
| `tokens.md` | Cualquier archivo que cite color; F70 (consume Okabe-Ito + ejes), F73 (severidad→token), F74 (genera CSS `var(--token)`) | F72 |
| `style-mapping.md` | 6 renderers L4 vía `scripts/util/style_mapping.py` (consolidación) | F73 |
| `notemartin.css` (en `assets/`) | Obsidian renderer (snippet canónico) | F74 |
| `note-templates.md` | 7 renderers L4 + `scripts/render/_header.py` (cabecera F75) + 15 archivos F78-F92 | F75 |
| `density.md` | agente al redactar + `scripts/validate/density_check.py` (validador de 8 reglas R1-R8) | F76 |
| `note-templates.md` | Agente al redactar cabecera | F75 |
| `density.md` | Agente y validador | F76 |
