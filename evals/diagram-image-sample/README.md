# `evals/diagram-image-sample/` — Verificador de la Fase 68

Eval battery para `skill/notemartin-study-notes/scripts/render/diagram_image.py` (Fase 68). Verifica los **3 criterios de aceptación de la fase** más 2 criterios transversales:

| # | Criterio | Cubre |
|---|---|---|
| C1 | Todo diagrama tiene versión imagen disponible (o fallback con source_code) | Criterio 1 de F68 |
| C2 | El mismo código produce el mismo archivo (determinismo) | Criterio 2 de F68 |
| C3 | El código fuente plegable acompaña siempre a la imagen | Criterio 3 de F68 |
| C4 | La caché funciona (cache_hit en 2ª corrida) | Detalle F68 |
| C5 | El manifest es válido (schema 1.0.0, 5 bloques) | Detalle F68 |

## Cómo correr

```bash
python evals/diagram-image-sample/run_eval.py --regen
```

Salida esperada:

```
============================================================
Fase 68 — Pre-renderizado a imagen
============================================================
  ✓ C1-image-per-diagram (5 bloques)
  ✓ C3-source-code-folded (5 bloques con código fuente)
  ✓ C5-manifest-valid (schema 1.0.0, 5 bloques)
  ✓ C4-cache-works (degraded: mmdc no disponible; 0 cache hits esperado)
  ✓ C2-determinism (5 hashes reproducibles)
============================================================
PASS 5/5
```

Exit 0 en PASS, exit 1 en cualquier FAIL.

## Modos de operación

- **Con `mmdc` instalado:** el script genera SVG/PNG reales; C4 valida cache hits.
- **Sin `mmdc`:** el script degrada a `native_mermaid`; C4 se acepta como "degraded" porque el manifest incluye el código fuente.

## Estructura

```
evals/diagram-image-sample/
├── README.md
├── build_fixtures.py           # regenera diagrams.nm + profile.yaml
├── run_eval.py                 # verificador principal (5 criterios)
└── fixtures/
    ├── diagrams.nm             # archivo con 5 diagramas (WP-1/2/3/4/6)
    └── profile.yaml            # profile mínimo
```
