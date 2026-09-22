# Extracción de PDF nativo — `references/01-ingest/pdf-native.md`

> Documento normativo de la Fase 18 del roadmap. Define cómo el script `scripts/ingest/pdf_native.py` extrae runs de texto de un PDF (con sus coordenadas, fuente y tamaño), detecta encabezados por tipografía, marca boilerplate por repetición posicional entre páginas y reconstruye el índice desde los marcadores PDF cuando existen.
>
> Documentos complementarios: `references/01-ingest/triage.md` (F17, provee el plan opcional), `references/00-pipeline/architecture.md` §3.1 (capa L0 — Ingesta), §5 (frontera de capa), §8 (modo degradado).

## Índice

1. [Propósito](#1-propósito) · 2. [Cuándo se aplica](#2-cuándo-aplica) · 3. [Modelo de fragmento](#3-modelo-de-fragmento) · 4. [Detección de encabezados por tipografía](#4-detección-de-encabezados-por-tipografía) · 5. [Detección de boilerplate](#5-detección-de-boilerplate) · 6. [Reconstrucción del índice](#6-reconstrucción-del-índice-outline) · 7. [Forma de `fragments.json`](#7-forma-de-fragmentsjson) · 8. [Conexión con triage y SDM](#8-conexión-con-triage-y-sdm) · 9. [Advertencias y modo degradado](#9-advertencias-y-modo-degradado) · 10. [Anti-patrones](#10-anti-patrones) · 11. [Cómo verificar + cambios permitidos](#11-cómo-verificar--cambios-permitidos)

## 1. Propósito

Convertir un PDF con capa de texto en una lista de **fragmentos tipográficos** con coordenadas, fuente y tamaño por run. El script NO clasifica regiones (F22), NO OCR (F19+F20), NO monta el SDM (F31). Su salida es la entrada contractual para esos tres scripts posteriores.

`scripts/ingest/pdf_native.py` produce:

- `fragments.json` — lista de páginas con sus fragmentos tipográficos.
- `extraction.md` — resumen legible (tabla de páginas, roles, font sizes).

## 2. Cuándo se aplica

Después del triaje (F17) sobre un PDF clasificado como `native_reliable` o `native_degraded`. Si F17 emite `pure_scan` para una página, F18 la salta con warning (F19+F20 la cubren).

Invocación:

```
python3 scripts/ingest/pdf_native.py --source <pdf> --out-dir <workdir/ingest/> [--plan <triage.json>]
```

Sin `--plan`: extrae todas las páginas (modo standalone; F31 filtra luego). Con `--plan`: extrae solo los rangos `native_reliable` / `native_degraded`.

## 3. Modelo de fragmento

Un **fragmento** = run de texto del PDF: secuencia contigua de caracteres con misma `(font_name, font_size, posición)`. pypdf agrupa automáticamente caracteres consecutivos con misma transformación de texto (`tm`).

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string hex 12 | `sha1(f"{page}::{bbox_serialized}::{text_first_64}")[:12]` |
| `page` | int ≥ 1 | número de página (1-indexed) |
| `bbox` | array de 4 floats | `[x0, y0, x1, y1]` en puntos PDF, origen abajo-izquierda |
| `font_name` | string | nombre de la fuente (p.ej. `Helvetica-Bold`) |
| `font_size` | float | tamaño tipográfico en puntos |
| `text` | string | contenido del fragmento |
| `role` | enum | `heading` \| `body` \| `caption` \| `footnote` \| `header` \| `footer` \| `page_number` \| `unknown` |
| `heading_level` | int 1–6 \| null | nivel de heading si `role=heading` |
| `section_path` | string \| null | ruta jerárquica asignada tras reconstruir el índice |
| `is_boilerplate` | bool | marcado si es repetido posicionalmente |

## 4. Detección de encabezados por tipografía

Sin regex sobre el texto. Cuatro pasos:

### 4.1 body_size = tamaño modal

Recoger `(font_name, font_size, count)` de todos los fragmentos del documento. Calcular:

```
body_size = argmax_{size} (suma de count de fragmentos con font_size == size)
```

Robusto a encabezados largos (que pueden sumar pocos fragmentos pero con texto extenso): el modo es el tamaño con más **runs**, no más caracteres.

### 4.2 Ranking por tamaño

Candidatos a heading: `font_size > body_size`. Ordenar de mayor a menor y rankear en bloques:

```
candidatos_ordenados = sorted({size for size, count in distribution if size > body_size
                                 and count / total_fragments <= HEADING_FREQ_MAX}, reverse=True)
heading_levels = {size: idx + 1 for idx, size in enumerate(candidatos_ordenados)}
```

`HEADING_FREQ_MAX = 0.10` (constante): un tamaño que aparece en > 10 % de los fragmentos no es heading (es body o nota editorial repetida).

Si dos tamaños están a < `HEADING_SIZE_GAP_PT = 0.5` pt, se colapsan al mayor.

### 4.3 Refinamiento por peso

- `font_name` contiene `Bold`, `Black`, `Heavy`, `Demi` → promover el nivel un punto (heading más prominente).
- `font_name` contiene `Italic`, `Oblique` → no es heading; asignar `role = "caption"` o mantener como `body`.

### 4.4 Asignación final

- `heading_size` ∈ niveles → `role = "heading"`, `heading_level = nivel`.
- `body_size` → `role = "body"`.
- Tamaños < `body_size` → `role = "footnote"` si están en banda inferior; si no, `body`.

## 5. Detección de boilerplate

### 5.1 Bandas header/footer

Por cada página, calcular:

```
header_band = top HEADER_BAND_RATIO (8 %) de la altura de página
footer_band = bottom FOOTER_BAND_RATIO (8 %) de la altura de página
```

Constantes: `HEADER_BAND_RATIO = FOOTER_BAND_RATIO = 0.08`.

### 5.2 Frecuencia inter-página

Concatenar el texto de cada banda por página → `{(band, page): text}`. Para cada banda, contar frecuencia del texto en todo el documento. Un texto es boilerplate si aparece en ≥ `BOILERPLATE_PAGE_RATIO = 0.30` de las páginas Y coincide posicionalmente (centroide de bbox dentro de ± `BOILERPLATE_BBOX_TOLERANCE = 0.05` del área de banda).

### 5.3 Tolerancia posicional

Para cada candidato a boilerplate, calcular el centroide vertical de su bbox en cada página. Si los centroides están dentro del 5 % del área de banda en todas las apariciones, se acepta como boilerplate posicionalmente consistente. Textos que aparecen en ≥ 30 % de páginas pero en posiciones variables no se marcan (probablemente son "All rights reserved" u otro texto legal — ese caso lo cubre F41 como contradicción potencial, no como boilerplate).

### 5.4 Boilerplate inline (números de página)

Fragmentos < `INLINE_BOILERPLATE_MAX_CHARS = 30` en bandas header/footer con `font_size` < body_size y que consisten mayormente de dígitos / la cadena "Page" → `role = "page_number"`, `is_boilerplate = true`.

## 6. Reconstrucción del índice (outline)

### 6.1 Lectura de marcadores PDF

```python
outline = reader.outline if hasattr(reader, "outline") else []
```

`outline` puede ser una lista plana o un árbol de `dict`-like con `title` y `kids`. Algoritmo recursivo:

```python
def walk(items, level=1, parent_path=""):
    out = []
    for item in items:
        if isinstance(item, list):
            out.extend(walk(item, level + 1, parent_path))
        else:
            title = item.title if hasattr(item, "title") else str(item)
            page_num = reader.get_destination_page_number(item) + 1  # 0-indexed → 1-indexed
            section_path = f"{parent_path}/{slug(title)}"
            out.append({"level": level, "title": title, "page": page_num, "section_path": section_path})
            # Recurse into nested kids
            if hasattr(item, "kids") and item.kids:
                out.extend(walk(item.kids, level + 1, section_path))
    return out
```

### 6.2 Construcción de section_path

Para cada outline entry, generar `slug(title) = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")`. Concatenar con el path padre. Si dos outline entries comparten título, añadir sufijo numérico `-2`, `-3`, etc.

### 6.3 Coincidencia con fragmentos

Para cada outline entry, buscar en su página el primer fragmento cuyo `text` empieza con `title[:30]` (trim y tolerante a espacios). Si hay match:

- Asignar `fragment.section_path = outline.section_path` y `fragment.heading_level = outline.level`.

Si no hay match (p.ej. outline incompleto), mantener el outline como entrada "synthetic" sin fragmento asignado.

### 6.4 Fallback: jerarquía desde heading levels

Si `outline = []`, construir jerarquía desde los heading levels detectados (§4). Cada heading level N es hijo del último heading de nivel < N visto. Asignar `section_path` heurístico `"/hN-<slug>"`.

## 7. Forma de `fragments.json`

`schema_version: "1.0.0"` (const). Campos:

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `schema_version` | string const | sí | `"1.0.0"` |
| `source.path` | string | sí | ruta absoluta del PDF |
| `source.hash` | string hex 64 | sí | sha256 del PDF |
| `source.size_bytes` | int | sí | bytes del PDF |
| `source.format` | enum | sí | siempre `"pdf"` |
| `extraction_version` | string | sí | `"1.0.0"` |
| `page_count` | int | sí | total de páginas del PDF |
| `scope.type` | enum | sí | `"all"` o `"ranges"` |
| `scope.ranges` | array | sí | rangos extraídos (vacío si `type=all`) |
| `pages[]` | array | sí | una entrada por página extraída |
| `pages[].page` | int | sí | 1-indexed |
| `pages[].fragments[]` | array | sí | lista de fragmentos (§3) |
| `outline[]` | array | sí | jerarquía del índice (§6) |
| `boilerplate_summary.header_texts` | array<string> | sí | textos únicos detectados en banda header |
| `boilerplate_summary.footer_texts` | array<string> | sí | textos únicos detectados en banda footer |
| `boilerplate_summary.repeated_inline` | array<string> | sí | page numbers y textos cortos repetidos |
| `warnings[]` | array<string> | sí | advertencias detectadas |
| `generated_at` | string ISO 8601 | sí | timestamp UTC |

`extraction.md` derivado: tabla con `page`, `role`, `font_size`, `heading_level`, `is_boilerplate`, `text` truncado a 60 chars.

## 8. Conexión con triage y SDM

`pdf_native.py` consume opcionalmente `triage.json` de F17 vía `--plan`. Si se pasa, solo se extraen páginas dentro de los rangos `native_reliable` / `native_degraded`. Páginas `pure_scan` se omiten con warning.

El output `fragments.json` es la entrada para `scripts/ingest/build_sdm.py` (F31), que:

1. Agrupa fragmentos consecutivos por `role` y `section_path` → bloques del SDM.
2. Asigna `id` SDM estable por bloque (`sha1(source_hash + section_path + block_index)[:12]`).
3. Resuelve `anchor.page` desde el fragmento inicial del bloque.
4. Aplica la confianza (`confidence`): 1.0 para `native_reliable`, 0.8 para `native_degraded`, 0.6 si `is_boilerplate` (independiente del role).

F18 NO produce bloques SDM. NO produce `regions.json` (eso es F22 tras clasificar regiones). NO produce `notemark/` ni `ir/`. Esa es la frontera de capa (`architecture.md` §5).

## 9. Advertencias y modo degradado

El script emite código de salida 0 (ok), 1 (error fatal) o 2 (ok con advertencias). Warnings posibles:

- `outline not present; using heading-level fallback` — el PDF no tiene marcadores; la jerarquía se reconstruye desde headings.
- `page N is pure_scan (per triage plan); skipping` — F17 marcó esta página como scan; F19+F20 la cubren.
- `pypdf returned 0 fragments for page N; falling back to extract_text() per-page` — `visitor_text` no produjo runs; F18 cae a un único fragmento por página con bbox = mediabox completo y warning.
- `inline boilerplate detection skipped for page N: missing font_size` — fragmento sin font_size (PDF degenerado); se ignora ese fragmento para la detección inline.

`architecture.md` §8 (modo degradado de L0) sigue aplicando aguas abajo: F26 (`review_report.py`) confirma bloques `is_boilerplate = true` y baja confianza antes de L2.

## 10. Anti-patrones

- **No** detectar headings por regex sobre el texto (no detecta estilo).
- **No** borrar fragmentos marcados `is_boilerplate`. Mantenerlos en el output con `is_boilerplate = true`; el caller decide si emite bloque SDM. Borrar destruye evidencia de auditoría.
- **No** usar el bbox aproximado del mediabox como bbox de fragmento sin intentar `visitor_text`. La precisión importa para F22 y F31.
- **No** colapsar dos fragmentos consecutivos con misma fuente/tamaño/posición si están separados por un cambio de `tm`. pypdf ya lo hace; el script solo respeta.
- **No** inventar `outline` si el PDF no tiene. Devolver `outline = []` con warning; no fabricar jerarquía ficticia.
- **No** aceptar `font_size = 0` como válido. Filtrar y warning; un fragmento sin font_size no es heading ni body confiable.
- **No** ignorar la conexión con `triage.json` cuando `--plan` se pasa. Si se pasa y el rango no incluye la página, omitir. No extraer la página completa por defecto.

## 11. Cómo verificar + cambios permitidos

Cinco pasos (mismo patrón que `architecture.md` §10):

1. ¿Cada fragmento tiene `page` y `bbox`? (verificación estructural; criterio 3 del roadmap.)
2. ¿Los headings detectados coinciden con el outline del PDF en ≥ 95 %? (verificación funcional; criterio 1.)
3. ¿Los textos de header/footer repetidos se marcan como boilerplate sin afectar el cuerpo? (verificación funcional; criterio 2.)
4. ¿El `fragments.json` declara `schema_version` y pasa los checks de `run_eval.py`?
5. ¿El modo `--plan <triage.json>` filtra correctamente las páginas `pure_scan`?

```bash
python3 evals/pdf-native-sample/run_eval.py
# Esperado: "PASS criterios 1+2+3"
```

**Cambios permitidos sin reabrir Fase 18:**

- Añadir un campo opcional a `fragments.json` con default `null` (con ADR).
- Añadir un nuevo `role` enum cuando aparezca un caso real no modelado.
- Ajustar las constantes (`HEADER_BAND_RATIO`, `BOILERPLATE_PAGE_RATIO`, etc.) si la evidencia experimental contra el corpus (F6) muestra que son laxas o estrictas (con ADR).

**Reabren Fase 18:**

- Cambiar el algoritmo de detección de headings (afecta a F22, F31).
- Cambiar el algoritmo de boilerplate (afecta a F26, F31).
- Cambiar el modelo de fragmento (afecta a F31, F22).
- Cambiar la forma de `fragments.json` rompiendo backward compat.
- Mover `fragments.json` de `ingest/` a otra ubicación.

Materialización de la suite de evals automatizada contra el corpus completo: F118 (evals).

## 12. Siguiente extractor — `preprocess.py` (F19)

Tras F18 (extracción nativa), las páginas marcadas como `pure_scan` o `hybrid_page` por F17 necesitan un preprocesado de imagen antes de OCR. F19 cubre esa cadena:

1. F17 emite `triage.json` con `plan[].class ∈ {pure_scan, hybrid_page}` y rangos por páginas.
2. `preprocess.py --source <pdf> --out-dir <workdir/ingest/>` rasteriza cada página a 300 DPI y aplica el pipeline configurable de 6 etapas: rasterize → deskew → curvature (opt-in) → denoise → binarize → border.
3. La imagen original NUNCA se destruye: F19 escribe `<basename>-NNNN.png` (original rasterizado) y `<basename>-NNNN.processed.png` (procesada), más `<basename>-NNNN.meta.json` por página.
4. F20 (`ocr.py`) consume las imágenes `.processed.png` y aplica OCR con confianza esperada según las flags `is_blank`, `rotation_too_large`, etc.

Detalles y umbrales: [`preprocess.md`](preprocess.md).
