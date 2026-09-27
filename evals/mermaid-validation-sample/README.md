# `evals/mermaid-validation-sample/` — Verificador de la Fase 67

Eval battery para `skill/notemartin-study-notes/scripts/validate/mermaid.py` (Fase 67). Verifica los **3 criterios de aceptación de la fase** más 2 criterios transversales:

| # | Criterio | Cubre |
|---|---|---|
| C1 | Detecta 100% de la batería de 20 diagramas rotos a propósito | Criterio 1 de F67 |
| C2 | Cero falsos positivos sobre los diagramas válidos del repo | Criterio 2 de F67 |
| C3 | Las 6 reglas de portabilidad P-01..P-06 están activas | Criterio 3 de F67 |
| C4 | Las 3 clases (sintaxis, portabilidad, legibilidad) tienen reglas | Detalle F67 |
| C5 | Formato del reporte (file, node_id, rule_id) | Detalle F67 |

## Cómo correr

```bash
python evals/mermaid-validation-sample/run_eval.py --regen
```

Salida esperada:

```
============================================================
Fase 67 — Validador de diagramas
============================================================
  ✓ C1-detect-broken (20/20 detectados)
  ✓ C2-zero-false-positives (≥20 bloques válidos, 0 FP)
  ✓ C3-portability-rules (6/6 activas)
  ✓ C4-three-classes (sintaxis+portabilidad+legibilidad)
  ✓ C5-report-format (N bloques con violaciones, formato OK)
============================================================
PASS 5/5
```

Exit 0 en PASS, exit 1 en cualquier FAIL.

## Estructura

```
evals/mermaid-validation-sample/
├── README.md
├── build_fixtures.py               # regenera broken.nm + valid-checks.yaml
├── run_eval.py                     # verificador principal (5 criterios)
└── fixtures/
    ├── broken.nm                   # archivo con 20 diagramas rotos envueltos en :::diagram
    ├── broken-diagrams.yaml        # spec de cada broken-diagram (id, clase, regla esperada)
    ├── valid-checks.yaml           # paths a los 20 diagramas válidos del repo
    └── valid-checks.yaml           # (generado)
```

## Cómo añadir un nuevo caso roto

Editar `build_fixtures.py` → `build_broken_nm()` → añadir entrada a `rows`. El verificador lo recoge automáticamente.
