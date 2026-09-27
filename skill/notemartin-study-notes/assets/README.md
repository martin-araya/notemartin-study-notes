# `assets/`

Material copiable que el agente y los renderers cargan como dato, no como instrucción: design tokens, CSS, plantillas, paletas.

## Qué vivirá aquí

| Archivo | Rol | Fase |
|---|---|---|
| `tokens.json` | Design tokens (color, tipografía, espaciado) con valor claro y oscuro (18/18 AA WCAG verificados) | F72 ✅ |
| `notemartin.css` | Snippet CSS canónico para Obsidian (363 líneas, 9 secciones, 0 literales hex) | F74 ✅ |
| `css-tokens.generated.css` | Variables CSS auto-generadas desde `tokens.json` (light + dark) | F74 |
| `profile.template.yaml` | Plantilla del perfil del usuario | F11 |
| `palettes/` | Paletas daltonismo-seguras para figuras | F70 |

## Regla de colores

Ningún archivo del proyecto contiene un color literal fuera de `tokens.json` (`INV-14`). Todo uso de color se referencia a un token semántico.

## Cuándo se crea

Esta carpeta se puebla desde F11 (plantilla de perfil) y F70-F76 (visual). `tokens.json` (F72), `notemartin.css` (F74) y `profile.template.yaml` (F11) ya están publicados; `palettes/` (F70+) está pendiente.
