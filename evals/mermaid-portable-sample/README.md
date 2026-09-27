# `evals/mermaid-portable-sample/` — Verificador de la Fase 66

Eval battery para `@/references/07-visual/mermaid-portable.md` (Fase 66). Verifica los **3 criterios de aceptación de la fase** más 2 criterios transversales:

| # | Criterio | Cubre |
|---|---|---|
| C1 | Lista blanca con 9 tipos (WP-1 … WP-9) y lista negra ≥10 entradas | Detalle F66, §3 y §5 |
| C2 | Cada entrada de la lista negra tiene alternativa explícita | Criterio 2 de F66 |
| C3 | Las 6 reglas R-MP-01 a R-MP-06 están enunciadas y verificables | Detalle F66, §4 |
| C4 | La tabla §8 cubre los 3 destinos de la intersección | Criterio 3 de F66 |
| C5 | Acentos y `ñ` documentados en §6 con procedimiento y reemplazos ASCII | Criterio 3 de F66 |

## Cómo correr

```bash
python evals/mermaid-portable-sample/run_eval.py \
    --catalog skill/notemartin-study-notes/references/07-visual/mermaid-portable.md
```

Salida esperada:

```
============================================================
Fase 66 — Subconjunto Mermaid portable
============================================================
  ✓ C1-whitelist+blacklist (9 WP, 16 LN)
  ✓ C2-blacklist-alternative (16 entradas con alternativa)
  ✓ C3-writing-rules (6 reglas)
  ✓ C4-three-dest (21 filas, NI: 8✅ 2⚠ 6❌)
  ✓ C5-acentos (11 etiquetas)
============================================================
PASS 5/5
```

Exit 0 en PASS, exit 1 en cualquier FAIL.

## Cómo regenerar fixtures

```bash
python evals/mermaid-portable-sample/build_fixtures.py
```

Las fixtures son **datos verificables**, no se editan a mano: si necesitas cambiar la cobertura, edita las funciones en `build_fixtures.py` y regenera.

## Estructura

```
evals/mermaid-portable-sample/
├── README.md
├── build_fixtures.py           # regenera los YAMLs
├── run_eval.py                 # verificador principal (5 criterios)
└── fixtures/
    ├── whitelist.yaml           # 9 tipos portables (WP-1 … WP-9)
    ├── blacklist.yaml           # 16 entradas (LN-1 … LN-16) con alternativa
    ├── writing-rules.yaml       # 6 reglas R-MP-01 … R-MP-06 con PASS/FAIL
    ├── three-dest-render.yaml   # 18 filas × 3 destinos
    └── acentos-ñ.yaml           # 11 etiquetas con acentos/ñ + veredicto
```
