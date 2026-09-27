# `evals/style-mapping-sample/` — Fase 73

Verificador de la Fase 73 (mapeo de estilo por destino). Cubre los 3 criterios del ROADMAP §1437-1440 con 5 sub-criterios:

| Criterio | Qué verifica | Método |
|---|---|---|
| **C1** | Cobertura 20 severidades × 7 campos = 140 celdas no vacías; severidades = `CANONICAL_SEVERITIES` (20) | in-process: `len(_MAPPING) == 20` + bucle de validación |
| **C2** | Iconos canónicos: 17 únicos + 3 compartidos (warning/caution/conflict → ⚠️) | in-process: agrupa severidades por icono; compara con `SHARED_ICON_GROUPS` |
| **C3** | Notion color ∈ `NOTION_VALID_COLORS` (10 colores válidos) | in-process: bucle de validación por mapping |
| **C4** | Los 6 renderers L4 NO tienen `SEVERITY_TO_*` local (consolidación) | `rg -n 'SEVERITY_TO_' scripts/render/` exit 1 |
| **C5** | `style-mapping.md` ≤ 400 líneas | `wc -l` |

## Uso

```bash
# Generar fixtures y ejecutar
python3 evals/style-mapping-sample/run_eval.py

# Forzar regeneración de golden
python3 evals/style-mapping-sample/run_eval.py --regen
```

## Salida esperada

```
============================================================
Fase 73 — Mapeo de estilo por destino
============================================================
  PASS  C1-coverage (20 mappings, 7×20=140 fields non-empty, severities match CANONICAL)
  PASS  C2-icons (17 unique + 3 shared en 1 grupo(s): [['caution', 'conflict', 'warning']])
  PASS  C3-notion-colors (8 colores usados de 10 válidos; resto fuera de la lista)
  PASS  C4-no-local-dicts (0 literales SEVERITY_TO_* en 6 renderers)
  PASS  C5-doc-size (221 líneas ≤ 400)
============================================================
PASS 5/5
```

Exit code `0` si todos pasan; `1` si alguno falla.

## Archivos

- `build_fixtures.py` — genera `fixtures/style-mapping.golden.json` (dump de los 20 StyleMapping) y `expected/style-mapping.md` (tabla markdown canónica).
- `run_eval.py` — los 5 sub-criterios documentados arriba.
- `fixtures/style-mapping.golden.json` — snapshot del módulo canónico.
- `expected/style-mapping.md` — tabla markdown generada desde el módulo, para inspección humana.

## Dependencias

Python 3.9+ stdlib puro. `rg` (ripgrep) necesario para C4.

## Wirings

- Cierra los 3 criterios de `ROADMAP.md` §1437-1440 para Fase 73.
- El criterio C4 (consolidación) es el más estricto: garantiza que los 6 renderers no tienen dicts `SEVERITY_TO_*` locales que puedan divergir del módulo canónico. Esto cierra la causa principal de drift futuro.
