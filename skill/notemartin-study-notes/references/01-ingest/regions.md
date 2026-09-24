# Clasificación de regiones — `references/01-ingest/regions.md`

> Documento normativo de la Fase 22 del roadmap. Define cómo el script `scripts/ingest/regions.py` reclasifica las regiones geométricas de F21 (`page-NNNN.regions.json`) en clases semánticas (texto, encabezado, tabla, figura, código, fórmula, etc.) mediante 11 señales tipográficas / geométricas con scoring numérico.
>
> Documentos complementarios: `references/01-ingest/layout.md` (F21, provee regiones geométricas), `references/01-ingest/pdf-native.md` (F18), `references/01-ingest/ocr-engines.md` (F20), `references/00-pipeline/architecture.md` §3.1 (L0 Ingesta), §5 (frontera de capa).

## Índice

1. [Propósito](#1-propósito) · 2. [Cuándo se aplica](#2-cuándo-aplica) · 3. [Las 13 clases semánticas](#3-las-13-clases-semánticas) · 4. [Catálogo de señales (11)](#4-catálogo-de-señales-11) · 5. [Perfiles de clase](#5-perfiles-de-clase) · 6. [Scoring y umbrales numéricos](#6-scoring-y-umbrales-numéricos) · 7. [Manejo de ambigüedad](#7-manejo-de-ambigüedad) · 8. [Detección de cajas editoriales](#8-detección-de-cajas-editoriales) · 9. [Forma de `regions.json` y `regions_summary.json`](#9-forma-de-regionsjson-y-regions_summaryjson) · 10. [Anti-patrones](#10-anti-patrones) · 11. [Cómo verificar + cambios permitidos](#11-cómo-verificar--cambios-permitidos)

## 1. Propósito

Asignar a cada región detectada por F21 una **clase semántica** del conjunto de 13 fijas. El script NO produce bloques SDM (F31), NO genera notas NoteMark (F12), NO renderiza (F4). Su salida es la entrada contractual para F31.

`scripts/ingest/regions.py` produce, en `<out-dir>/ingest/regions/`:

- `page-NNNN.regions.json` — copia del output de F21 enriquecido con `semantic_class`, `class_confidence`, `ambiguity`, `alternative_classes[]`, `signals[]`.
- `regions_summary.json` — global con `class_distribution`, `ambiguous_count`, `ambiguous_regions[]`, `class_metrics{}`.

## 2. Cuándo se aplica

Tras F21 (`layout.py`). Las regiones geométricas (`column`, `sidebar_left`, `sidebar_right`, `margin_note`, `figure_caption`) se reclasifican en clases semánticas:

```
python3 scripts/ingest/regions.py \
    --source <regions_dir|page-NNNN.regions.json> \
    --out-dir <dir> \
    [--fragments <fragments.json>] [--ocr <ocr_summary.json>] \
    [--class-profile <yaml>] [--json-only]
```

Si `--source` es un directorio, lee todas las `page-NNNN.regions.json` (típicamente `<out-dir>/ingest/layout/`). Si no se pasa `--fragments` ni `--ocr`, el script los busca en `<out-dir>/ingest/` (F18/F20 outputs).

## 3. Las 13 clases semánticas

| Clase | Descripción | Señales primarias |
|---|---|---|
| `text` | Texto corrido (párrafos de prosa). | ninguna fuerte; ausencia de todas las demás |
| `heading` | Encabezados y títulos de sección. | `S_LARGE` + `S_BOLD` |
| `table` | Tabla con estructura columnar repetida. | `S_TABLE_GRID` + `S_HAS_GAPS` |
| `figure` | Imagen o diagrama a página completa / parcial. | `S_HAS_GAPS` + `S_TOP_BOTTOM` |
| `capture` | Captura de pantalla o fotografía incrustada (no figure con caption). | `S_HAS_GAPS` alta |
| `diagram` | Diagrama genérico (no railroad, no captura). | `S_SYMBOL_DENSITY` moderado + `S_HAS_GAPS` |
| `code` | Bloque de código fuente. | `S_MONOSPACE` + `S_INDENT` + `S_SYMBOL_DENSITY` |
| `console` | Salida de terminal (prompt + líneas). | `S_MONOSPACE` + `S_PATTERN` (`$`, `>`, `PS1=`) |
| `formula` | Fórmula matemática (LaTeX/MathJax). | `S_SYMBOL_DENSITY` + `S_ITALIC` + `S_HAS_GAPS` |
| `editorial_note` | Nota editorial (Note/Tip/Warning/Caution/Important). | `S_PATTERN` + `S_HAS_GAPS` (caja) |
| `syntax_diagram` | Diagrama de sintaxis (railroad). | `S_MONOSPACE` + `S_SYMBOL_DENSITY` (flechas) + `S_ALIGN_CENTER` |
| `footer` | Pie de página, número de página, copyright. | `S_TOP_BOTTOM` + `S_BOLD` opcional |
| `index` | Entrada de índice (TOC, glosario). | `S_TOP_BOTTOM` + `S_PATTERN` (números+puntos) |

Cualquier clase fuera de la lista se emite como `unknown` con `ambiguity: true`.

## 4. Catálogo de señales (11)

Cada señal es una función pura `(Region, [Word]) → float ∈ [0, 1]`.

### S_MONOSPACE
`font_name` contiene (case-insensitive) alguno de: `courier`, `consolas`, `monaco`, `menlo`, `monospace`, `liberation mono`, `source code`, `inconsolata`, `fira mono`, `ibm plex mono`. Retorna 1.0 si match; 0.0 si no. Match ≥ 80 % de los words de la región.

### S_BOLD
`font_name` contiene `Bold`, `Black`, `Heavy`, `Demi`. Retorna 1.0 si match ≥ 80 % de words.

### S_ITALIC
`font_name` contiene `Italic`, `Oblique`. Retorna 1.0 si match ≥ 80 % de words.

### S_LARGE
`font_size` ≥ `LARGE_FACTOR × body_size` (1.3 ×). `body_size` se infiere como el tamaño modal de la página. Retorna 1.0 si cumple; 0.0 si no.

### S_SYMBOL_DENSITY
Ratio de tokens no-alfanuméricos sobre tokens alfanuméricos en el texto de la región. Retorna `min(ratio / SYMBOL_DENSITY_HIGH, 1.0)` con `SYMBOL_DENSITY_HIGH = 0.30`.

### S_INDENT
Todos los fragments de la región tienen `x ∈ [region.x_min + INDENT_MIN_PX, region.x_min + INDENT_MAX_PX]`. Retorna 1.0 si cumple ≥ 80 % de los lines; 0.0 si no.

### S_ALIGN_CENTER
Centroide x de la región está dentro de ±`CENTER_TOL_PCT` (5 %) del centro de la columna padre. Retorna 1.0 si cumple; 0.0 si no.

### S_TABLE_GRID
F21 marcó la región con `S_TABLE_GRID` (≥ 3 columnas a la misma Y). Retorna 1.0 si cumple; 0.0 si no.

### S_HAS_GAPS
`1 − (palabras_density × bbox_area_ratio)`. Si la región tiene ≥ `EMPTY_AREA_RATIO = 0.30` del bbox sin palabras, retorna 1.0; 0.0 si no.

### S_PATTERN
Match contra regex predefinidos:
- `^(Figure|Fig\.|Tab\.|Tabla|Listing|Snippet|Code)\s*\d` → `S_PATTERN` × 0.7
- `^(Note|Tip|Warning|Caution|Important|See also|Example|NB|Remark):?` → × 1.0 (editorial_note)
- `^(\d+\.)+\s+[A-Z]` → × 0.6 (index)
- `^(\$\s|>\s|PS1=|>>>)` → × 0.7 (console)
- `^(→|⇐|⇒|⟶)` → × 0.8 (syntax_diagram)

### S_TOP_BOTTOM
Centroide y de la región ≤ `TOP_REGION_PCT × page_height` O ≥ `(1 − BOTTOM_REGION_PCT) × page_height`. Retorna 1.0 si cumple; 0.0 si no.

## 5. Perfiles de clase

Cada clase tiene un perfil con 11 pesos numéricos `[0, 1]` (0 desactiva, 1 peso fuerte). El perfil `text` está cerca de cero en todas las señales (es el "ruido de fondo"). Perfiles default inline en `regions.py`:

```python
DEFAULT_PROFILES = {
    "text":             {"S_MONOSPACE": 0.0, "S_BOLD": 0.0, "S_ITALIC": 0.0, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.0, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.0, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.0, "S_PATTERN": 0.0, "S_TOP_BOTTOM": 0.0},
    "heading":          {"S_MONOSPACE": 0.0, "S_BOLD": 0.85, "S_ITALIC": 0.0, "S_LARGE": 0.95, "S_SYMBOL_DENSITY": 0.0, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.5, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.0, "S_PATTERN": 0.4, "S_TOP_BOTTOM": 0.4},
    "table":            {"S_MONOSPACE": 0.0, "S_BOLD": 0.0, "S_ITALIC": 0.0, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.0, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.0, "S_TABLE_GRID": 0.95, "S_HAS_GAPS": 0.6, "S_PATTERN": 0.0, "S_TOP_BOTTOM": 0.0},
    "figure":           {"S_MONOSPACE": 0.0, "S_BOLD": 0.0, "S_ITALIC": 0.0, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.0, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.4, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.7, "S_PATTERN": 0.5, "S_TOP_BOTTOM": 0.3},
    "capture":          {"S_MONOSPACE": 0.0, "S_BOLD": 0.0, "S_ITALIC": 0.0, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.0, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.0, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.85, "S_PATTERN": 0.0, "S_TOP_BOTTOM": 0.0},
    "diagram":          {"S_MONOSPACE": 0.0, "S_BOLD": 0.0, "S_ITALIC": 0.0, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.4, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.3, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.5, "S_PATTERN": 0.3, "S_TOP_BOTTOM": 0.0},
    "code":             {"S_MONOSPACE": 0.95, "S_BOLD": 0.0, "S_ITALIC": 0.0, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.7, "S_INDENT": 0.6, "S_ALIGN_CENTER": 0.0, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.1, "S_PATTERN": 0.6, "S_TOP_BOTTOM": 0.0},
    "console":          {"S_MONOSPACE": 0.85, "S_BOLD": 0.0, "S_ITALIC": 0.0, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.4, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.0, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.1, "S_PATTERN": 0.7, "S_TOP_BOTTOM": 0.0},
    "formula":          {"S_MONOSPACE": 0.0, "S_BOLD": 0.0, "S_ITALIC": 0.6, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.85, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.4, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.3, "S_PATTERN": 0.5, "S_TOP_BOTTOM": 0.0},
    "editorial_note":   {"S_MONOSPACE": 0.0, "S_BOLD": 0.4, "S_ITALIC": 0.85, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.0, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.3, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.85, "S_PATTERN": 1.0, "S_TOP_BOTTOM": 0.0},
    "syntax_diagram":   {"S_MONOSPACE": 0.4, "S_BOLD": 0.0, "S_ITALIC": 0.0, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.85, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.5, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.4, "S_PATTERN": 0.8, "S_TOP_BOTTOM": 0.0},
    "footer":           {"S_MONOSPACE": 0.0, "S_BOLD": 0.0, "S_ITALIC": 0.0, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.0, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.0, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.0, "S_PATTERN": 0.5, "S_TOP_BOTTOM": 0.95},
    "index":            {"S_MONOSPACE": 0.0, "S_BOLD": 0.0, "S_ITALIC": 0.0, "S_LARGE": 0.0, "S_SYMBOL_DENSITY": 0.4, "S_INDENT": 0.0, "S_ALIGN_CENTER": 0.0, "S_TABLE_GRID": 0.0, "S_HAS_GAPS": 0.0, "S_PATTERN": 0.7, "S_TOP_BOTTOM": 0.6},
}
```

El usuario puede sobreescribir perfiles vía `--class-profile <yaml>` con la misma estructura.

## 6. Scoring y umbrales numéricos

Para cada región:

```
score(class) = Σ_k (signal_k(region) × profile[class][signal_k])
```

Luego:

```
max_score = max(score(class) for class in 13)
second_score = second_max(score)
ambiguity = (max_score < CLASS_MIN_THRESHOLD) or (max_score - second_score < AMBIGUITY_MARGIN)
semantic_class = argmax if not ambiguity else None
class_confidence = round(max_score, 3)
```

Umbrales constantes (`regions.py`):

| Constante | Valor | Significado |
|---|---|---|
| `CLASS_MIN_THRESHOLD` | `0.45` | Mínimo para asignar clase con confianza |
| `AMBIGUITY_MARGIN` | `0.10` | Mínimo margen entre top1 y top2 |

## 7. Manejo de ambigüedad (regla dura)

Cuando `ambiguity = true`:

```jsonc
{
  "id": "r007",
  "semantic_class": null,            // ← explícitamente null, no string vacío
  "class_confidence": 0.42,
  "ambiguity": true,
  "alternative_classes": [
    {"class": "figure", "score": 0.42},
    {"class": "table", "score": 0.38},
    {"class": "diagram", "score": 0.30}
  ]
}
```

Regla dura: **ninguna región se fuerza a una clase cuando las señales son insuficientes.** El script NUNCA emite `semantic_class` distinto de las 13 oficiales si `max_score < CLASS_MIN_THRESHOLD`.

## 8. Detección de cajas editoriales

Las "cajas editoriales" en libros técnicos (Note/Tip/Warning/Caution) tienen señales combinadas:

- Bloque corto (≤ `EDITORIAL_BOX_MAX_WORDS = 80`).
- Rodeado por gaps ≥ `EDITORIAL_BOX_GAP_PX = 30` arriba y abajo.
- Empieza con `Note:`, `Tip:`, `Warning:`, `Caution:`, `Important:`, `See also:`, `Example:`, `NB:`, `Remark:` (regex en `S_PATTERN`).
- A veces `S_ITALIC` activo.

Cuando se detecta este patrón, la clase primaria es `editorial_note` y se añade sub-info:

```jsonc
{
  "id": "r012",
  "semantic_class": "editorial_note",
  "class_confidence": 0.88,
  "ambiguity": false,
  "signals": [
    {"signal": "S_PATTERN", "value": 1.0, "matched_regex": "^(Note|Tip|Warning):?"},
    {"signal": "S_HAS_GAPS", "value": 0.85}
  ],
  "sub_kind": "box"   // sub-tipo: "box" o "inline"
}
```

`sub_kind: "box"` (rodeado de gaps) vs `"inline"` (entre texto corrido). Documentado en `signals[].matched_regex` para auditoría.

## 9. Forma de `regions.json` y `regions_summary.json`

`regions.json` por página — copia enriquecida de F21:

```jsonc
{
  "page": 1,
  "regions": [
    {
      "id": "r001",
      "layout_class": "column",
      "semantic_class": "code",
      "class_confidence": 0.92,
      "ambiguity": false,
      "alternative_classes": [],
      "signals": [{"signal": "S_MONOSPACE", "value": 1.0}, ...],
      "bbox": [54, 100, 280, 700],
      "in_main_flow": true,
      "word_count": 32,
      "first_word": "def",
      "last_word": "return",
      "sub_kind": null
    }
  ]
}
```

`regions_summary.json` global:

```jsonc
{
  "schema_version": "1.0.0",
  "source": { "layout_dir": "...", "fragments_path": "...", "ocr_summary_path": "...", "hash": "..." },
  "class_profile_version": "1.0.0",
  "page_count": 8,
  "class_distribution": { "text": 24, "heading": 8, "table": 3, ... },
  "ambiguous_count": 2,
  "ambiguous_regions": [{"page": 5, "region_id": "r007", "alternative_classes": [...]}],
  "warnings": [],
  "generated_at": "2026-09-24T..."
}
```

## 10. Anti-patrones

- **No** forzar `semantic_class` cuando las señales son insuficientes. La regla dura de ambigüedad es innegociable.
- **No** introducir clases fuera de las 13 oficiales. Cualquier nueva es `unknown`.
- **No** usar OCR adicional ni embeddings. Solo heurísticas sobre font/text/bbox.
- **No** re-clasificar regiones sin haber leído F21 primero. Si `--source` falta o el directorio no existe, error claro.
- **No** emitir `signals` con más de 11 entradas. El catálogo es fijo.
- **No** aceptar fuentes no-PDF / no-OCR. Si faltan tanto `--fragments` como `--ocr`, warning pero no abortar.

## 11. Cómo verificar + cambios permitidos

Cinco pasos:

1. ¿La entrada son `regions.json` de F21 (≥ 1 página)?
2. ¿Cada región tiene `semantic_class` ∈ 13 + `null`?
3. ¿Las regiones ambiguas tienen `semantic_class: null` + `ambiguity: true` + `alternative_classes.length ≥ 2`?
4. ¿La clase `code` se asigna con precision/recall ≥ 0.85?
5. ¿Las cajas editoriales se detectan como `editorial_note`?

```bash
python3 evals/regions-sample/run_eval.py
# Esperado: "PASS los 3 criterios"
```

**Cambios permitidos sin reabrir Fase 22:**

- Ajustar pesos numéricos de los perfiles (`class_profile.yaml`) con ADR.
- Añadir una sub-clase `sub_kind` nueva para una clase existente (p.ej. `code: "snippet"`) con ADR.
- Añadir una señal nueva al catálogo (manteniendo las 11 originales) con ADR.

**Reabren Fase 22:**

- Añadir una clase semántica nueva.
- Cambiar el algoritmo de scoring (multiplicativo vs aditivo).
- Cambiar la regla de ambigüedad (umbral o criterio).
- Cambiar el orden de aplicación de señales.
