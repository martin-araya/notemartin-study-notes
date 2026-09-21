# `scripts/`

Ejecutables invocables por el agente. **No se leen en contexto**; se invocan por su comando con la entrada y salida declaradas. El catálogo legible está en `scripts/README.md` (producido por F117).

## Qué vivirá aquí

| Subcarpeta | Rol | Fases |
|---|---|---|
| `ingest/` | L0: triaje, OCR, layout, regiones, tablas, fórmulas, código, post-OCR, formatos no PDF | F17-F29, F33 |
| `validate/` | Validadores de SDM, IR, NoteMark, Mermaid, completitud, equivalencia cross-target | F30, F43, F49, F63, F67 |
| `authoring/` | Parser NoteMark, transformaciones de IR | F48, F50 |
| `render/` | Renderers a cada destino + pre-render de diagramas y figuras | F54-F60, F68, F70 |
| `util/` | Caché, visor, ledger, trazabilidad | F36, F38, F52 |
| `README.md` | Catálogo con qué hace cada script, entrada, salida, dependencias, invocación | F117 |

## Reglas (per `AGENT.md` §6)

- Cada script independiente, invocable solo, sin importar un paquete común pesado.
- Entrada y salida por archivo con rutas explícitas por argumento.
- `--help` útil y entrada en `scripts/README.md` con dependencias y comportamiento si faltan.
- Dependencias mínimas y declaradas en `requirements.txt` plano.
- Salida en dos formatos: legible por humano y estructurada para el agente.
- Códigos de salida: 0 correcto, 1 error, 2 advertencias.
- Escritura atómica: temporal + `rename`.

## Cuándo se crea

Esta carpeta se puebla desde F17 en adelante. Hoy está vacía.
