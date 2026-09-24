# Layout y orden de lectura — `references/01-ingest/layout.md`

> Documento normativo de la Fase 21 del roadmap. Define cómo el script `scripts/ingest/layout.py` consume las salidas word-level de F18 (PDF nativo) o F20 (OCR), detecta columnas, sidebars, notas al margen, pies de figura y flotantes, calcula el orden de lectura verificado por continuidad sintáctica y reunifica contenido que cruza páginas.
>
> Documentos complementarios: `references/01-ingest/pdf-native.md` (F18, fuente `fragments.json`), `references/01-ingest/ocr-engines.md` (F20, fuente `ocr_summary.json`), `references/01-ingest/triage.md` (F17), `references/00-pipeline/architecture.md` §3.1 (L0 Ingesta), §5 (frontera de capa).

## Índice

1. [Propósito](#1-propósito) · 2. [Cuándo se aplica](#2-cuándo-aplica) · 3. [Normalización de entrada](#3-normalización-de-entrada) · 4. [Detección de columnas](#4-detección-de-columnas) · 5. [Sidebars y notas al margen](#5-sidebars-y-notas-al-margen) · 6. [Pies de figura y flotantes](#6-pies-de-figura-y-flotantes) · 7. [Orden de lectura y continuidad](#7-orden-de-lectura-y-continuidad) · 8. [Verificación del orden](#8-verificación-del-orden) · 9. [Reunificación cross-page](#9-reunificación-cross-page) · 10. [Forma de `layout_summary.json`](#10-forma-de-layout_summaryjson) · 11. [Cómo verificar + cambios permitidos](#11-cómo-verificar--cambios-permitidos)

## 1. Propósito

Reconstruir el flujo de lectura de una página a partir de sus palabras con coordenadas. El script NO clasifica semánticamente las regiones (F22); NO construye el SDM (F31). Su salida es la entrada contractual para ambos.

`scripts/ingest/layout.py` produce, en `<out-dir>`:

- `ingest/layout/page-NNNN.regions.json` — regiones detectadas por página con `bbox` y `class`.
- `ingest/layout/page-NNNN.reading_order.json` — orden de lectura con `continuity_score`.
- `ingest/layout/layout_summary.json` — global con `cross_page_links[]` e `inconsistencies[]`.

## 2. Cuándo se aplica

Tras F18 (extracción nativa) o F20 (OCR). Para cada página:

1. Cargar palabras con coordenadas (`x, y, w, h`) y, si está disponible, `font_name`/`font_size`.
2. Detectar columnas, sidebars, margin notes, captions, floats.
3. Calcular orden de lectura y verificar continuidad.
4. Reunificar párrafos/tablas/código que cruzan páginas.

```
python3 scripts/ingest/layout.py --source <fragments.json|ocr_summary.json> --out-dir <dir> \
    [--input-type auto|pdf-native|ocr] [--json-only]
```

Si se pasa `--pdf <pdf>`, el script invoca F18 internamente para producir `fragments.json` antes de ejecutar el análisis de layout.

## 3. Normalización de entrada

### 3.1 fragments.json (F18)

Cada fragmento tiene `bbox` `[x0, y0, x1, y1]`. Para análisis de layout, cada fragmento se descompone en pseudo-palabras por espacios (manteniendo el bbox como bbox del fragmento entero si no se puede subdividir). El campo `font_name` se usa para heurísticas; `role` se preserva pero no influye en layout geométrico.

### 3.2 ocr_summary.json (F20)

Cada palabra tiene `bbox` `[x, y, w, h]`. Más granular; cada palabra es atómica. `conf` se ignora para layout (F20 ya filtró las inválidas).

### 3.3 Modelo unificado

Internamente, F21 trabaja con `list[Word]` donde:

```python
@dataclass
class Word:
    text: str
    bbox: tuple[float, float, float, float]  # x, y, w, h
    font_name: Optional[str]
    font_size: Optional[float]
    page: int
```

El normalizador selecciona el `Word` apropiado según `input_type` o auto-detecta por la presencia de campos (`fragments` vs `words`).

## 4. Detección de columnas

Algoritmo de proyección horizontal:

1. Recoger `bbox.x` (centroide horizontal de cada palabra).
2. Construir histograma en X con buckets de `X_HISTOGRAM_BUCKET_PX = 8` píxeles.
3. Calcular `max_density = max(histogram)`.
4. Encontrar gaps: posiciones donde `histogram[x] = 0` Y `histogram[x-1] > 0` Y `histogram[x+1] > 0`, ambas con altura ≥ `MIN_COLUMN_DENSITY = 0.05 * max_density`.
5. Si hay ≥ 1 gap, hay ≥ 2 columnas. Cada columna tiene `x_range = [gap_left, gap_right]` continuo entre gaps consecutivos.
6. Si no hay gaps pero la densidad tiene un único pico claro: 1 columna que ocupa toda la página.
7. Asignar cada palabra a la columna cuyo `x_range` contiene `bbox.x_centroid`.

Columnas se numeran de izquierda a derecha (`column_index` 0, 1, 2, ...).

## 5. Sidebars y notas al margen

### 5.1 Sidebars

Cluster de palabras en una franja vertical estrecha:

- `x_range_width < SIDEBAR_MAX_WIDTH_RATIO * page_width (= 0.20)`.
- No coincide con el rango X de ninguna columna principal.

Si el cluster tiene ≥ 3 palabras y cumple el ancho, se marca como `class: "sidebar"` (left/right según posición) con `in_main_flow: false`.

### 5.2 Notas al margen

Palabra individual en el margen izquierdo o derecho:

- `bbox.x < MARGIN_THRESHOLD_PX (= 50)` O `bbox.x + bbox.w > page_width - MARGIN_THRESHOLD_PX (= 50)`.
- `font_size <= MARGIN_NOTE_MAX_SIZE (= 11.0)` (heurística: las notas al margen suelen ser más pequeñas).

Se marca como `class: "margin_note"`, `in_main_flow: false`.

## 6. Pies de figura y flotantes

### 6.1 Pies de figura

1. Detectar "huecos verticales": gaps en la distribución Y de palabras donde la densidad cae a 0 durante ≥ 1.5 × `line_height`.
2. Para cada hueco, buscar texto inmediatamente debajo (gap ≤ 1.5 × line_height).
3. Si el texto comienza con patrón "caption-like": `Figure N`, `Fig. N`, `Tab. N`, `Tabla N`, o es texto corto (< 30 palabras), marcar como `class: "figure_caption"`, `in_main_flow: false`.

### 6.2 Flotantes

Una región se marca `class: "float", in_main_flow: false` si:

- Su bbox cubre ≥ `FLOAT_WIDTH_RATIO (= 0.60)` del ancho de página.
- A la misma Y, hay palabras a la izquierda Y a la derecha del bbox (el texto fluye alrededor).
- En word-level, esto se infiere por presencia de "huecos rectangulares" (zonas sin palabras) flanqueados por palabras.

Para v1, marcamos `float: candidate` cuando una región rectangular tiene ≥ 50% de su bbox sin palabras y flanqueada.

## 7. Orden de lectura y continuidad

### 7.1 Orden base

Para cada página:

```
sort regiones by (column_index asc, y_centroid asc)
```

Las regiones con `in_main_flow: false` se ordenan al final (footer/header/margin notes) o se excluyen del flujo principal según heurística (sidebars: orden por Y al final del documento).

### 7.2 Continuity score

Para cada par de regiones consecutivas del flujo principal, calcular `continuity_score ∈ [0, 1]`:

| Regla | Puntos |
|---|---|
| Última palabra de región A termina con `.`, `;`, `:`, `?`, `!` Y primera palabra de B empieza con mayúscula | `+0.3` |
| Última palabra de A termina con `-` (silabeo) Y primera palabra de B empieza con minúscula | `+0.3` |
| `|y_centroid_A - y_centroid_B| < 1.5 × line_height` (continuación del mismo párrafo) | `+0.2` |
| A y B están en la misma columna Y A no es la última región de esa columna | `+0.2` |

`continuity_score ≥ MIN_CONTINUITY_SCORE (= 0.30)` indica buena continuidad. Si es menor, se registra un "jump" en `reading_order.json`.

### 7.3 Reading order por página

```jsonc
{
  "page": 1,
  "ordered_region_ids": ["r001", "r002", "r003"],
  "jumps": [
    {"from_region": "r002", "to_region": "r003", "score": 0.2, "kind": "low_continuity"}
  ],
  "excluded_region_ids": ["r004"]  // sidebars, margin notes
}
```

## 8. Verificación del orden

### 8.1 Ground truth por reglas estrictas

El script calcula un orden "ground truth" alternativo con reglas más estrictas:

1. Mismo algoritmo base (column_index, y_centroid).
2. Para sidebars: si la sidebar está a la izquierda de la primera columna principal y al inicio vertical, va primero; si está al final vertical, va al final.

Si el orden emitido por §7 difiere del ground truth en ≥ 2 regiones consecutivas para una página con `column_count >= 2` y `region_count >= 4`, se marca `reading_order_valid: false`.

### 8.2 Inconsistencies

`layout_summary.json.inconsistencies[]` es un array de:

```jsonc
{
  "page": 2,
  "expected_order": ["r001", "r002"],
  "emitted_order": ["r002", "r001"],
  "kind": "column_order_inverted"
}
```

`kind` puede ser: `column_order_inverted`, `sidebar_position_wrong`, `caption_in_main_flow`, etc.

## 9. Reunificación cross-page

### 9.1 Párrafos

`type: "paragraph"` cuando:

- La última palabra de la última región de la página N NO termina con `.`, `;`, `:`, `?`, `!`, `,` (cierre ausente).
- La primera palabra de la primera región de la página N+1 empieza con minúscula O continúa la palabra (silabeo: `A_last_word.endswith("-")`).

### 9.2 Tablas

`type: "table"` cuando:

- La primera región de la página N+1 tiene estructura columnar sospechosa: ≥ 3 palabras a la misma Y, separadas por gaps X consistentes con la última tabla de la página N.
- Heurística: las palabras están alineadas verticalmente con la última tabla detectada en N.

### 9.3 Código

`type: "code"` cuando:

- La última línea de N termina con uno de `CROSS_PAGE_BREAK_MARKERS = (',', ';', ':', '(', '[', '{', '\\')` (indicadores de continuación de código).
- La primera línea de N+1 está indentada (mismo `x_centroid` que líneas internas de un bloque de código en N) o comienza con operador/llave.

`cross_page_links[]` en `layout_summary.json`:

```jsonc
{
  "type": "paragraph",
  "page_a": 1,
  "region_id_a": "r005",
  "page_b": 2,
  "region_id_b": "r001",
  "confidence": 0.85
}
```

## 10. Forma de `layout_summary.json`

`schema_version: "1.0.0"` (const). Campos:

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `schema_version` | string const | sí | `"1.0.0"` |
| `source.path` | string | sí | ruta del input |
| `source.hash` | string hex 64 | sí | sha256 del input |
| `source.size_bytes` | int | sí | bytes del input |
| `source.format` | enum | sí | `pdf-native / ocr / pdf` (si se usó `--pdf`) |
| `input_type` | enum | sí | `pdf-native / ocr / auto` |
| `page_count` | int | sí | total de páginas analizadas |
| `pages[]` | array | sí | una entrada por página |
| `pages[].page` | int | sí | 1-indexed |
| `pages[].column_count` | int | sí | columnas detectadas (1, 2, 3+) |
| `pages[].region_count` | int | sí | total de regiones |
| `pages[].reading_order_valid` | bool | sí | si el orden pasa la verificación |
| `pages[].continuity_score` | float | sí | media de los `continuity_score` (0–1) |
| `pages[].out_of_flow_count` | int | sí | regiones `in_main_flow: false` |
| `cross_page_links[]` | array | sí | reuniones detectadas (puede ser vacío) |
| `cross_page_links[].type` | enum | sí | `paragraph / table / code` |
| `cross_page_links[].page_a/b` | int | sí | páginas involucradas |
| `cross_page_links[].region_id_a/b` | string | sí | IDs de las regiones |
| `cross_page_links[].confidence` | float | sí | [0, 1] |
| `inconsistencies[]` | array | sí | órdenes rotos detectados (puede ser vacío) |
| `warnings[]` | array | sí | advertencias |
| `generated_at` | string ISO 8601 | sí | timestamp UTC |

## 11. Cómo verificar + cambios permitidos

Cinco pasos:

1. ¿La entrada es un `fragments.json` o `ocr_summary.json` válido?
2. ¿Cada página produce al menos 1 región con `in_main_flow: true`?
3. ¿Para páginas con 2+ columnas, el orden es `(col_0 → col_1 → ...)` con `reading_order_valid: true`?
4. ¿Las reuniones cross-page se detectan y registran?
5. ¿Una inyección deliberada de orden roto se detecta?

```bash
python3 evals/layout-sample/run_eval.py
# Esperado: "PASS los 3 criterios"
```

**Cambios permitidos sin reabrir Fase 21:**

- Añadir un nuevo detector (e.g., `footnote_block`) con ADR.
- Ajustar las constantes numéricas con evidencia experimental.
- Añadir un campo opcional a `layout_summary.json`.

**Reabren Fase 21:**

- Cambiar el algoritmo de detección de columnas.
- Cambiar el orden base (column_index, y_centroid).
- Cambiar la fórmula de `continuity_score`.
- Cambiar la convención de bbox.
- Dividir `layout_summary.json`.

## 12. Siguiente extractor — `regions.py` (F22)

Tras F21 (layout), cada región geométrica (`column`, `sidebar_*`, `margin_note`, `figure_caption`) se reclasifica en una de las **13 clases semánticas oficiales** (`text`, `heading`, `table`, `figure`, `capture`, `diagram`, `code`, `console`, `formula`, `editorial_note`, `syntax_diagram`, `footer`, `index`) mediante 11 señales tipográficas / geométricas con scoring numérico:

1. F22 lee `ingest/layout/page-NNNN.regions.json` + `fragments.json` (F18) o `ocr_summary.json` (F20) para tener font_name/text/bbox.
2. Las palabras se asocian a regiones por bbox overlap (F21 no emite `word_indices`).
3. Para cada región, 11 señales se computan: `S_MONOSPACE`, `S_BOLD`, `S_ITALIC`, `S_LARGE`, `S_SYMBOL_DENSITY`, `S_INDENT`, `S_ALIGN_CENTER`, `S_TABLE_GRID`, `S_HAS_GAPS`, `S_PATTERN`, `S_TOP_BOTTOM`.
4. Cada clase tiene un perfil con 11 pesos. `score(class) = BASE_BIAS[class] + Σ signal × weight`.
5. Regla dura de ambigüedad: si `max_score < 0.45` O `max − second < 0.10`, `semantic_class = null`, `ambiguity = true`, `alternative_classes` con ≥ 2 clases distintas.
6. Cajas editoriales: gap ≥ 30 pt + patrón `^(Note|Tip|Warning):?` + `S_ITALIC` → `editorial_note` con `sub_kind = "box"`.

Detalles y umbrales: [`regions.md`](regions.md).
