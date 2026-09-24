# OCR de tablas — `references/01-ingest/tables.md`

> Documento normativo de la Fase 23 del roadmap. Define cómo el script `scripts/ingest/tables.py` detecta y extrae tablas a partir de las regiones marcadas como `table` por F22, con clusterización geométrica por filas y columnas, detección de celdas combinadas (rowspan/colspan), encabezados multinivel y reunión cross-page.
>
> Documentos complementarios: `references/01-ingest/regions.md` (F22, provee anclas `semantic_class = "table"`), `references/01-ingest/layout.md` (F21), `references/01-ingest/pdf-native.md` (F18), `references/01-ingest/ocr-engines.md` (F20), `references/00-pipeline/architecture.md` §3.1 (L0 Ingesta), §5 (frontera de capa).

## Índice

1. [Propósito](#1-propósito) · 2. [Cuándo se aplica](#2-cuándo-aplica) · 3. [Detección de tablas](#3-detección-de-tablas) · 4. [Clusterización por filas y columnas](#4-clusterización-por-filas-y-columnas) · 5. [Celdas combinadas (rowspan / colspan)](#5-celdas-combinadas-rowspan--colspan) · 6. [Encabezados multinivel](#6-encabezados-multinivel) · 7. [Tablas cross-page (reunificación)](#7-tablas-cross-page-reunificación) · 8. [Verificación y baja confianza](#8-verificación-y-baja-confianza) · 9. [Forma de `tables.json` y `tables_summary.json`](#9-forma-de-tablesjson-y-tables_summaryjson) · 10. [Anti-patrones](#10-anti-patrones) · 11. [Cómo verificar + cambios permitidos](#11-cómo-verificar--cambios-permitidos)

## 1. Propósito

Producir la estructura completa de cada tabla detectada en la fuente (filas × columnas, headers multinivel, celdas combinadas, reunión cross-page) con verificación material de integridad.

`scripts/ingest/tables.py` produce, en `<out-dir>/ingest/tables/`:

- `page-NNNN.tables.json` — tablas detectadas en la página con `headers[][]`, `data[][]`, `merged_cells[]`, metadata.
- `tables_summary.json` — global con todas las tablas (incluyendo cross-page merged), `class_distribution`, `warnings[]`.

## 2. Cuándo se aplica

Tras F22 (`regions.py`). Las regiones con `semantic_class = "table"` son anclas para F23. Si F22 no se ejecutó, F23 detecta tablas geométricamente desde fragments/words.

```
python3 scripts/ingest/tables.py \
    --source <regions_dir> --out-dir <dir> \
    [--fragments <fragments.json>] [--ocr <ocr_summary.json>] \
    [--json-only]
```

Si `--source` no se pasa, busca `<out-dir>/ingest/regions/`. Si tampoco, autodetecta tablas desde `--fragments` o `--ocr`.

## 3. Detección de tablas

**Modo 1 (con F22)**: lee `page-NNNN.regions.json` y selecciona regiones con `semantic_class = "table"`. Cada una es una tabla candidato.

**Modo 2 (sin F22)**: lee fragments/words y aplica detección geométrica:
- Construye histograma de alineaciones X (palabras con mismo `x` ± 4 px, conteo ≥ 3).
- Construye histograma de alineaciones Y (palabras con mismo `y_centroid` ± 4 px, conteo ≥ 3).
- Si hay ≥ 3 alineaciones X y ≥ 3 alineaciones Y, hay tabla candidato.

**Salidas**: lista de `TableRegion {page, bbox, words_in_region}`.

## 4. Clusterización por filas y columnas

Para cada región:

1. Filtrar palabras cuyo bbox intersecta con `region_bbox` (tolerancia 5 px).
2. **Cluster por Y (filas)**: agrupar palabras con `y_centroid` dentro de ±`ROW_BAND_TOL_PX = 4.0`. Cada cluster es una fila.
3. **Cluster por X (columnas)**: dentro de cada fila, agrupar palabras con `x` dentro de ±`COL_BAND_TOL_PX = 6.0`. Cada cluster es una celda.
4. Construir grid `rows × cols`. Las celdas vacías se rellenan con string vacío `""`.
5. Concatenar palabras de cada celda (orden de lectura izquierda-a-derecha).

Salida: matriz `data[r][c]` (lista de strings) + `headers[r][c]` (primeras filas si detectadas como header).

## 5. Celdas combinadas (rowspan / colspan)

### Rowspan
- Para cada celda, calcular `height = y_max − y_min`.
- Si `height > MERGED_CELL_FACTOR × average_row_height (= 1.5 × h_avg)`, la celda es rowspan.
- `rowspan = round(height / h_avg)`.
- Marcar con `merged_cells: [{r, c, rowspan: M, colspan: 1, value: <texto>}]`.
- Las celdas cubiertas por el rowspan se llenan con `""` en el grid, excepto la primera (la que tiene el value).

### Colspan
- Para cada celda, calcular `width = x_max − x_min`.
- Si `width > MERGED_CELL_FACTOR × average_col_width (= 1.5 × w_avg)` Y no hay otras palabras dentro de su rango X, la celda es colspan.
- `colspan = round(width / w_avg)`.

### Intersección (rowspan + colspan)
- Si `height > 1.5×h_avg` Y `width > 1.5×w_avg`, marcar con ambos.

L-shape no soportado en v1: se aproxima al rectángulo máximo; warning explícito.

## 6. Encabezados multinivel

Hasta `HEADER_MAX_ROWS = 3` filas consecutivas en la parte superior con `font_size ≥ HEADER_FONT_SIZE_FACTOR × body_size (= 1.10)` O `font_name contains "Bold"` se tratan como header compuesto.

`headers[r][c]` para cada nivel `r` (0, 1, 2) y columna `c`. Celdas vacías en una fila de header se rellenan con `""` (puede haber celdas vacías entre headers multinivel).

## 7. Tablas cross-page (reunificación)

Para cada par de tablas consecutivas en páginas N y N+1:

1. Si ambas tablas tienen la misma cantidad de columnas, continuar; si no, no mergea.
2. Calcular similitud de strings entre la primera fila de la tabla N+1 y la última fila de la tabla N:
   - `match_ratio = (caracteres iguales en la misma posición) / max(len(A), len(B))`.
3. Si `match_ratio ≥ CROSS_PAGE_HEADER_MATCH_THRESHOLD (= 0.80)`:
   - Marcar tabla N: `cross_page_continued: true`, `page_end: N+1`, `page_jumps: [...]`.
   - Concatenar `data` (excluyendo la fila repetida en N+1).
   - Actualizar `rows = rows_N + rows_{N+1} − 1` (header repetido descontado).
4. Si `0.60 ≤ match_ratio < 0.80`: marcar `cross_page_continued: false` pero warning "header similitud ambigua".
5. Si `match_ratio < 0.60`: NO mergea.

## 8. Verificación y baja confianza

### Regla dura (criterio 3)

Para cada tabla:

```python
assert len(data) == rows           # no truncado de filas
assert all(len(row) == cols for row in data)  # todas las filas tienen cols celdas
assert merged_cells' references are within bounds
```

Si alguna verificación falla, warning + `low_confidence: true` + `confidence: 0.0`.

### Marcado de baja confianza

`low_confidence: true` si:

- `len(data) < LOW_CONFIDENCE_MIN_ROWS = 3` Y no se detectó header.
- Alguna celda está vacía rodeada de celdas con texto (posible error de segmentación).
- Cross-page reunión ambigua (`0.60 ≤ match_ratio < 0.80`).

## 9. Forma de `tables.json` y `tables_summary.json`

`tables.json` por página:

```jsonc
{
  "page": 3,
  "tables": [
    {
      "id": "t001",
      "region_id": "r005",
      "page_start": 3,
      "page_end": 3,
      "rows": 35,
      "cols": 5,
      "headers": [["id", "name", "category", "price", "stock"]],
      "data": [
        ["1", "Widget", "A", "10.00", "100"],
        ["2", "Gadget", "B", "20.00", "50"],
        ...
      ],
      "merged_cells": [
        {"r": 0, "c": 1, "rowspan": 1, "colspan": 3, "value": "Combined Header"}
      ],
      "cross_page_continued": false,
      "confidence": 0.92,
      "low_confidence": false,
      "warnings": [],
      "dwell_ms": 145
    }
  ]
}
```

`tables_summary.json` global:

```jsonc
{
  "schema_version": "1.0.0",
  "source": { "regions_dir": "...", "fragments_path": "...", "hash": "..." },
  "table_count": 3,
  "tables": [
    {
      "id": "t001",
      "page_start": 3,
      "page_end": 5,
      "rows": 24,
      "cols": 4,
      "cross_page_continued": true,
      "page_jumps": [{"from_page": 3, "to_page": 4, "kind": "repeated_header", "match_ratio": 0.95}],
      "confidence": 0.92,
      "low_confidence": false,
      "warnings": []
    }
  ],
  "warnings": [],
  "generated_at": "2026-09-24T..."
}
```

## 10. Anti-patrones

- **No** truncar `data` cuando la tabla es muy larga. Emitir todas las filas.
- **No** fusionar dos tablas en una cuando tienen diferentes cantidades de columnas.
- **No** inventar headers cuando no se detectan — dejar `headers: []`.
- **No** marcar `low_confidence = false` cuando hay celdas faltantes.
- **No** usar OCR adicional ni ML. Solo heurísticas geométricas sobre fragments/words.
- **No** emitir tablas vacías (`rows = 0`). Si no hay palabras, omitir la región.
- **No** aceptar input que no sea PDF/JSON/OCR. Si `--source` y `--fragments`/`--ocr` faltan, error claro.

## 11. Cómo verificar + cambios permitidos

Cinco pasos:

1. ¿El input es un directorio de regiones de F22 o un fragments/ocr de F18/F20?
2. ¿Cada tabla tiene `len(data) == rows` y `len(row) == cols`?
3. ¿Las celdas combinadas aparecen en `merged_cells[]` con su `value` preservado?
4. ¿Las tablas cross-page con header repetido se mergean con `match_ratio ≥ 0.80`?
5. ¿Ninguna tabla se trunca?

```bash
python3 evals/tables-sample/run_eval.py
# Esperado: "PASS los 3 criterios"
```

**Cambios permitidos sin reabrir Fase 23:**

- Ajustar las constantes numéricas con ADR.
- Añadir sub-clase de celda combinada (`L-shape`) cuando aparezca un caso real.
- Añadir un campo opcional a `tables.json` con default sensato.

**Reabren Fase 23:**

- Cambiar el algoritmo de clusterización (Y / X con tolerancia).
- Cambiar la fórmula de rowspan/colspan detection.
- Cambiar el threshold `CROSS_PAGE_HEADER_MATCH_THRESHOLD`.
- Cambiar el orden de aplicación de headers multinivel.

## 12. Siguiente extractor — `formulas.py` (F24)

Tras F23 (tables), las regiones con `semantic_class = "formula"` (o autodetectadas por alta densidad de símbolos desde fragments) se consumen para extracción LaTeX:

1. F24 lee `ingest/regions/page-NNNN.regions.json` + `fragments.json` (F18). Si F22 no marcó nada, autodetecta clusters de palabras con symbol_density ≥ 0.20.
2. Por cada fórmula candidata, concatena el texto en orden de lectura.
3. `LaTeXValidator` (regex puro Python, sin pdflatex) verifica:
   - Llaves balanceadas.
   - Anidamiento ≤ 5 (`LATEX_MAX_NESTED_BRACES`).
   - Entornos `\begin{}/\end{}` balanceados con whitelist (equation, align, matrix, cases, etc.).
   - Sin especiales huérfanos (`_`, `^`).
   - Comandos conocidos (whitelist ~80 macros: `\frac`, `\sum`, `\int`, `\alpha`, `\beta`, `\lim`, etc.).
4. Detección bloque vs inline (height ≤ 30 px y width < 50% page_width → inline).
5. Numeración preservada vía regex `(N.M)` o `(N)`; `equation_index[]` global en `formulas_summary.json`.
6. Fallback: si LaTeX no compila → `pending: true` con `image_path` (recorte desde imágenes F19) o `bbox` referencial (PDF-only). Nunca se aproxima la expresión.

Detalles y umbrales: [`formulas.md`](formulas.md).
