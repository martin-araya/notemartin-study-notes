# `evals/monospace-diagrams-sample/` — Verificador de la Fase 69

Eval battery para `skill/notemartin-study-notes/references/07-visual/monospace-diagrams.md` (Fase 69). Verifica los **3 criterios de aceptación de la fase**:

| # | Criterio | Cubre |
|---|---|---|
| C1 | Al menos 10 patrones listos para copiar | Criterio 1 de F69 |
| C2 | Todos respetan el ancho máximo (≤60 estándar / ≤70 absoluto) | Criterio 2 de F69 |
| C3 | Tabla de decisión con 12 filas × 3 columnas = 36 celdas no vacías | Criterio 3 de F69 |

## Cómo correr

```bash
python evals/monospace-diagrams-sample/run_eval.py
```

Salida esperada:

```
============================================================
Fase 69 — Diagramas monoespaciados
============================================================
  ✓ C1-patterns-count (12 patrones)
  ✓ C2-width-compliance (12/12 ≤60 chars; 0 entre 61-70)
  ✓ C3-decision-table (12 filas, 36 celdas)
============================================================
PASS 3/3
```

Exit 0 en PASS, exit 1 en cualquier FAIL.

## Estructura

```
evals/monospace-diagrams-sample/
├── README.md
├── build_fixtures.py        # extrae patrones del archivo source
├── run_eval.py              # verificador principal (3 criterios)
└── fixtures/
    └── patterns.json        # {patterns: [...], decision_table: [...]}
```

## Detalles

- **`build_fixtures.py`** parsea `monospace-diagrams.md` extrayendo los 12 patrones (§4-§15) con sus plantillas principales, y la tabla de decisión §3. Genera `patterns.json`.
- **`run_eval.py`** carga `patterns.json` y verifica los 3 criterios:
  - **C1**: cuenta de patrones ≥10.
  - **C2**: ancho máximo de línea por patrón ≤70 chars (política §2.1).
  - **C3**: tabla de decisión con 12 filas × 3 columnas y todas las celdas no vacías.
