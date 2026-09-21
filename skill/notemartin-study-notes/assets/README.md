# `assets/`

Material copiable que el agente y los renderers cargan como dato, no como instrucción: design tokens, CSS, plantillas, paletas.

## Qué vivirá aquí

| Archivo | Rol | Fase |
|---|---|---|
| `tokens.json` | Design tokens (color, tipografía, espaciado) con valor claro y oscuro | F72 |
| `notemartin.css` | Snippet CSS para Obsidian | F74 |
| `profile.template.yaml` | Plantilla del perfil del usuario | F11 |
| `palettes/` | Paletas daltonismo-seguras para figuras | F70 |

## Regla de colores

Ningún archivo del proyecto contiene un color literal fuera de `tokens.json` (`INV-14`). Todo uso de color se referencia a un token semántico.

## Cuándo se crea

Esta carpeta se puebla desde F11 (plantilla de perfil) y F70-F76 (visual). Hoy está vacía.
