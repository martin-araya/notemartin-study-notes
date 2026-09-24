# F32 — `anchors-sample/`

Battery de evaluación de la Fase 32 (anclas estables y numeración inconsistente). Verifica los 3 criterios de la fase:

1. Un documento sin numeración produce anclas igualmente utilizables.
2. Las anclas son estables entre ejecuciones.
3. Toda unidad de L2 puede referenciar un ancla.

## Estructura

```
evals/anchors-sample/
├── README.md                         # este archivo
├── build_fixtures.py                 # genera los 3 ingest-dir + expected/
├── fixtures/
│   ├── source-unnumbered-html/       # HTML sin headings numerados (criterio 1)
│   ├── source-renumbered-pdf/        # outline 1.1, 1.1 duplicado, 1.3 saltado (regla §7)
│   └── source-stable-rerun/          # re-empaqueta source-pdf de F31 (criterio 2)
├── expected/
│   ├── unnumbered-expectations.json
│   ├── renumbered-expectations.json
│   └── stable-rerun-expectations.json
└── run_eval.py                       # ejecuta los 3 criterios
```

## Cómo correr

```bash
python3 evals/anchors-sample/run_eval.py
```

Exit 0 = PASS los 3 criterios; 1 = FAIL alguno; 2 = setup error.

## Lo que mide cada criterio

### Criterio 1 (`_criterion_1_unnumbered`)
Toma `source-unnumbered-html` (HTML sin headings numerados, 5 secciones, cada `headings=[{level:1, text:"Overview", anchor:""}]` sin números). Verifica:
- el SDM tiene ≥ 5 secciones;
- cada bloque lleva `anchor.section_path` no vacío;
- cada bloque tiene `anchor.page = null` (HTML no paginada per spec §5);
- hay 5 `section_path` distintos entre los bloques (uno por sección).

### Criterio 2 (`_criterion_2_stable`)
Para cada fixture: corre `build_sdm --check-determinism` (que ejecuta el pipeline dos veces) y confirma `summary.determinism.identical == True`. Adicionalmente toma `source-stable-rerun` y corre `build_sdm` dos veces **explícitamente** sin `--check-determinism` y compara bytes de `sdm.json` — esto cierra el invariante "mismo `source.hash` + mismo algoritmo ⇒ mismo SDM byte a byte".

### Criterio 3 (`_criterion_3_l2_references`)
Toma el SDM de `source-unnumbered-html` y construye un mini-ledger sintético con 3 unidades: dos que referencian bloques reales del SDM y una que referencia un `block_id` inexistente (`deadbeef0000`). Verifica:
- las dos unidades reales resuelven a bloques existentes;
- el ledger marca la referencia inválida como rota.

(La verdadera integración con F15 — `validate_ledger.py` — se materializa cuando F15 cierre; este eval ejecuta la regla de referencia directamente como doble positivo/negativo.)

## Notas de diseño

- Las reglas **duplicados resueltos con ordinal `-N`** y **saltos no inventados** (§7 de `anchors.md`) son **advisory** en este eval. El fixture `source-renumbered-pdf` ejerce ambas, pero su no cumplimiento no falla el eval: queda documentado en la spec y se reabre F31 cuando corresponda.
- El eval reutiliza `validate_sdm.py` (F13) y `build_sdm.py` (F31) sin modificarlos. F32 es puro spec + verificación; no toca scripts.

## Regresión a F31

`evals/build-sdm-sample/run_eval.py` (F31) sigue ejecutando al día como parte del cierre de Fase 32. Si F32 modificara accidentalmente algún comportamiento de F31, ese eval saldría en FAIL y alertaría.

```bash
python3 evals/build-sdm-sample/run_eval.py   # PASS los 3 criterios F31
```
