# Preprocesado de imagen — `references/01-ingest/preprocess.md`

> Documento normativo de la Fase 19 del roadmap. Define cómo el script `scripts/ingest/preprocess.py` rasteriza un PDF o un directorio de imágenes, detecta y corrige rotación, curvatura, ruido, contraste, binarización y bordes, conservando el original en todo momento.
>
> Documentos complementarios: `references/01-ingest/triage.md` (F17, provee la lista de páginas `pure_scan` que F19 procesa), `references/01-ingest/pdf-native.md` (F18, precede a F19 en el pipeline para nativos), `references/00-pipeline/architecture.md` §3.1 (L0 Ingesta), §4 (workdir `ingest/pages/`), §5 (frontera de capa), §8 (modo degradado).

## Índice

1. [Propósito](#1-propósito) · 2. [Cuándo se aplica](#2-cuándo-aplica) · 3. [Pipeline de 6 etapas](#3-pipeline-de-6-etapas) · 4. [Heurísticas y umbrales numéricos](#4-heurísticas-y-umbrales-numéricos) · 5. [Detección de rotación y páginas en blanco](#5-detección-de-rotación-y-páginas-en-blanco) · 6. [Manejo de bordes y sombra de encuadernación](#6-manejo-de-bordes-y-sombra-de-encuadernación) · 7. [Forma de `preprocess_summary.json`](#7-forma-de-preprocess_summaryjson) · 8. [Preservación del original](#8-preservación-del-original) · 9. [Advertencias y modo degradado](#9-advertencias-y-modo-degradado) · 10. [Anti-patrones](#10-anti-patrones) · 11. [Cómo verificar + cambios permitidos](#11-cómo-verificar--cambios-permitidos)

## 1. Propósito

Producir una versión limpia de cada página escaneada para que F20 (OCR) alcance su mejor tasa de acierto. El script aplica un pipeline configurable de 6 etapas y emite dos artefactos por página: la imagen **original** (nunca modificada) y la imagen **procesada**. Más una bitácora global y un resumen estructurado.

`scripts/ingest/preprocess.py` produce, en `<out-dir>`:

- `ingest/pages/<basename>-NNNN.png` — rasterización original (input PDF o copia de la imagen de entrada).
- `ingest/pages/<basename>-NNNN.processed.png` — versión preprocesada lista para OCR.
- `ingest/pages/<basename>-NNNN.meta.json` — métricas de la página (rotación, curvatura, blank, etc.).
- `ingest/preprocess.log` — bitácora plana, una línea por página.
- `ingest/preprocess_summary.json` — resumen global con todas las páginas.

## 2. Cuándo se aplica

Tras el triaje (F17) y la extracción nativa (F18). F19 cubre:

- Páginas marcadas como `pure_scan` por F17 (PDFs escaneados sin capa de texto fiable).
- Páginas `hybrid_page` (parte escaneada dentro de un PDF nativo).
- Imágenes sueltas (PNG/JPEG) que el usuario entrega como fuente.

Para PDFs nativos confiables (`native_reliable`), F19 sigue siendo útil si el usuario quiere rasterizar a DPI uniforme; pero F18 ya extrae texto por coordenadas sin rasterizar, así que la invocación conjunta suele ser opt-in.

```
python3 scripts/ingest/preprocess.py --source <pdf|img|dir> --out-dir <workdir/ingest/> \
    [--dpi 300] [--pipeline rasterize,deskew,denoise,binarize,border,curvature] \
    [--format auto|pdf|images] [--json-only]
```

## 3. Pipeline de 6 etapas

Cada etapa es independiente. El orden es fijo, pero pueden activarse o desactivarse vía `--pipeline`. Etapas omitidas se saltan sin warning.

### 3.1 rasterize (obligatoria)

Entrada PDF → imagen PNG por página a DPI configurable (default 300). Usa `pypdfium2` por defecto; `pdf2image` opcional si está disponible. Para imágenes de entrada (PNG/JPEG), simplemente copia al directorio de salida y la marca como ya rasterizada.

Salida: `ingest/pages/<basename>-NNNN.png` con tamaño aproximado `8.5" × 11" × 300 DPI = 2550 × 3300`.

### 3.2 deskew

Detecta el ángulo de inclinación mediante projection profile y rota la imagen para corregirlo. Rango de búsqueda: `[-MAX_ROTATION_DEG, +MAX_ROTATION_DEG]` con paso `ROTATION_STEP_DEG`. Solo aplica si la mejora en varianza del histograma proyectado supera `ROTATION_IMPROVEMENT_RATIO`.

### 3.3 curvature (opt-in)

Detecta curvatura en el lomo de un libro escaneado midiendo el ángulo de las líneas base de texto mediante Hough Lines. Si `curvature_score ≥ CURVATURE_SCORE_THRESHOLD`, aplica warping polinomial de grado 2. Etapa costosa y propensa a fallar; opt-in por defecto.

### 3.4 denoise

Aplica `cv2.fastNlMeansDenoising` (o bilateral filter como fallback más rápido) sobre la imagen en escala de grises. Reduce ruido de fondo (manchas, sombras de escaneo) preservando bordes de texto.

### 3.5 binarize

Convierte a blanco/negro mediante `cv2.adaptiveThreshold` con `ADAPTIVE_BLOCK_SIZE = 31` y `ADAPTIVE_C = 10`. Resiste iluminaciones desiguales típicas de escaneos antiguos. CLAHE opcional previo para mejorar contraste antes de binarizar.

### 3.6 border

Detecta bandas oscuras en los márgenes (`MARGIN_PIXELS` filas/columnas) y las reemplaza por el fondo interior mediante `cv2.inpaint` con `INPAINT_RADIUS = 5`. Si la sombra cubre > 50 % del ancho, se marca `spine_shadow: true` y se aplica inpainting más agresivo.

## 4. Heurísticas y umbrales numéricos

Todas las constantes viven en `scripts/ingest/preprocess.py` (no YAML; mismo patrón que F18). Cambiar un umbral es **modificar el código**, con ADR.

| Constante | Valor | Descripción |
|---|---|---|
| `DEFAULT_DPI` | `300` | DPI por defecto del rasterizado |
| `MAX_ROTATION_DEG` | `10.0` | Máximo ángulo corregible; más allá se marca `rotation_too_large` |
| `ROTATION_STEP_DEG` | `0.5` | Paso del barrido en projection profile |
| `ROTATION_IMPROVEMENT_RATIO` | `1.10` | Mejora mínima de varianza para aplicar deskew |
| `ADAPTIVE_BLOCK_SIZE` | `31` | Vecindad de `cv2.adaptiveThreshold` |
| `ADAPTIVE_C` | `10` | Constante sustraída de la media local |
| `BLANK_THRESHOLD` | `0.005` | `non_white_ratio` por debajo del cual la página se considera en blanco |
| `BORDER_DARKNESS_THRESHOLD` | `180` | Intensidad media del margen por debajo de la cual se detecta sombra |
| `MARGIN_PIXELS` | `30` | Grosor de las bandas de margen evaluadas (en píxeles) |
| `INPAINT_RADIUS` | `5` | Radio de `cv2.inpaint` para sustitución de píxeles |
| `CURVATURE_SCORE_THRESHOLD` | `0.6` | Score mínimo para aplicar corrección de curvatura |
| `CURVATURE_BASELINE_THRESHOLD` | `2.0` | Variación de ángulo (°) top vs. bottom para marcar como curvada |
| `WHITE_INTENSITY` | `240` | Intensidad por encima de la cual un píxel cuenta como blanco |

## 5. Detección de rotación y páginas en blanco

### 5.1 Rotación (deskew)

Algoritmo projection profile:

1. Convertir a grayscale + binarizar (Otsu).
2. Proyectar la suma de píxeles negros por fila → histograma vertical; el ancho del histograma varía con el ángulo.
3. Para cada ángulo `θ` en `[-MAX_ROTATION_DEG, +MAX_ROTATION_DEG]` con paso `ROTATION_STEP_DEG`, rotar la imagen `θ` grados, recalcular el histograma y guardar su varianza.
4. El ángulo con varianza máxima es la inclinación detectada.
5. Solo aplicar la rotación si `variance(θ_opt) ≥ variance(0) × ROTATION_IMPROVEMENT_RATIO`. Si no, asumir sin rotación.
6. Si `|θ_opt| > MAX_ROTATION_DEG`, marcar `rotation_too_large: true` y devolver sin corrección.

Páginas cuya rotación detectada supera `MAX_ROTATION_DEG` se devuelven tal cual, con warning.

### 5.2 Páginas en blanco

Cálculo:

```
non_white_ratio = (píxeles con intensidad < WHITE_INTENSITY) / total_píxeles
is_blank = (non_white_ratio < BLANK_THRESHOLD)
```

`BLANK_THRESHOLD = 0.005` (0.5 % de la página tiene contenido) cubre páginas totalmente blancas o con un sello mínimo. La imagen procesada se emite igualmente, con `is_blank: true` en `meta.json`. F20 puede usarla para saltarse la página sin OCR.

## 6. Manejo de bordes y sombra de encuadernación

Algoritmo de detección:

1. Calcular la intensidad media de las `MARGIN_PIXELS` filas superiores, inferiores, izquierda y derecha.
2. Si la intensidad media del margen cae por debajo de `BORDER_DARKNESS_THRESHOLD` (180 vs. fondo blanco ≈ 250), marcar como sombra.
3. Si la sombra detectada cubre > 50 % del ancho de la página, marcar `spine_shadow: true`.

Algoritmo de corrección (cuando se detecta sombra):

1. Construir una máscara que abarque las filas/columnas oscuras periféricas.
2. Aplicar `cv2.inpaint(img, mask, INPAINT_RADIUS, cv2.INPAINT_TELEA)`.
3. La imagen corregida se devuelve en color o escala de grises según las etapas previas.

Si la corrección no es concluyente (p.ej. la sombra afecta contenido real), se aplica y se marca warning.

## 7. Forma de `preprocess_summary.json`

`schema_version: "1.0.0"` (const). Campos:

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `schema_version` | string const | sí | `"1.0.0"` |
| `source.path` | string | sí | ruta absoluta del input |
| `source.hash` | string hex 64 | sí | sha256 del input (architecture.md §6) |
| `source.size_bytes` | int | sí | bytes del input |
| `source.format` | enum | sí | `pdf / png / jpeg / images-dir` |
| `pipeline` | array | sí | etapas ejecutadas (en orden) |
| `dpi` | int | sí | DPI usado en rasterizado |
| `page_count` | int | sí | total de páginas/imágenes procesadas |
| `pages[]` | array | sí | una entrada por página |
| `pages[].page` | int | sí | 1-indexed |
| `pages[].original_path` | string | sí | ruta relativa a `<out-dir>/ingest/pages/<basename>-NNNN.png` |
| `pages[].processed_path` | string | sí | ruta relativa a `<basename>-NNNN.processed.png` |
| `pages[].rotation_detected_deg` | float | sí | ángulo detectado (0 si no se detectó) |
| `pages[].rotation_applied` | bool | sí | si se aplicó la corrección |
| `pages[].rotation_too_large` | bool | sí | si la rotación supera `MAX_ROTATION_DEG` |
| `pages[].curvature_score` | float | sí | score [0, 1] |
| `pages[].curvature_applied` | bool | sí | si se aplicó warping |
| `pages[].denoise_applied` | bool | sí | si se aplicó denoise |
| `pages[].binarize_applied` | bool | sí | si se aplicó binarización |
| `pages[].border_shadow_removed` | bool | sí | si se quitaron bordes |
| `pages[].spine_shadow` | bool | sí | si se detectó sombra de encuadernación |
| `pages[].is_blank` | bool | sí | página en blanco |
| `pages[].non_white_ratio` | float | sí | ratio [0, 1] |
| `pages[].size_before` | int | sí | bytes de la imagen original |
| `pages[].size_after` | int | sí | bytes de la imagen procesada |
| `pages[].dwell_ms` | int | sí | tiempo de procesamiento |
| `warnings[]` | array<string> | sí | advertencias detectadas |
| `generated_at` | string ISO 8601 | sí | timestamp UTC |

`preprocess.log` es texto plano, una línea por página, con campos clave-valor tab-separados.

## 8. Preservación del original

**Regla dura:** la imagen original nunca se destruye. Estructura de salida:

```
<out-dir>/ingest/pages/<basename>-NNNN.png            # original (rasterizado o copiado)
<out-dir>/ingest/pages/<basename>-NNNN.processed.png  # versión preprocesada
<out-dir>/ingest/pages/<basename>-NNNN.meta.json      # métricas
<out-dir>/ingest/preprocess.log                       # bitácora
<out-dir>/ingest/preprocess_summary.json              # resumen global
```

`<basename>` = nombre del archivo input sin extensión (PDF o imagen). Si el input es un directorio de imágenes, `<basename>` = nombre de cada archivo.

Si el archivo original ya existe en `ingest/pages/`, **no se sobrescribe**: se añade sufijo de timestamp (`<basename>-NNNN.ts<unix>.png`). Escritura atómica por archivo (`tempfile` + `Path.replace`).

El input del usuario (PDF o imagen original fuera del workdir) nunca se modifica. El script solo escribe dentro de `--out-dir`.

## 9. Advertencias y modo degradado

El script emite código 0 (ok), 1 (error fatal) o 2 (ok con advertencias). Warnings posibles:

- `page N: rotation detected is X° (> MAX_ROTATION_DEG); not correcting`
- `page N: curvature score is X (< threshold); not correcting`
- `page N: is_blank; processed image emitted anyway`
- `pypdfium2 failed to render page N; falling back to error skip`
- `border inpainting applied despite overlapping content`

`architecture.md` §8 (modo degradado de L0) sigue aplicando aguas abajo: si una página sale con `is_blank: true` o `non_white_ratio` muy bajo, F20 puede saltarla; si la confianza OCR es baja, F26 confirma.

## 10. Anti-patrones

- **No** sobrescribir el archivo original bajo ninguna circunstancia. Si `--out-dir` coincide con la ruta del input, abortar.
- **No** inventar curvatura cuando `curvature_score < threshold`. Mejor skip que dañar la imagen.
- **No** aplicar deskew con varianza menor al threshold; deja la imagen rotada y warning.
- **No** binarizar imágenes en color (que aún no han pasado por grayscale). Si el pipeline omite `denoise`, la binarización toma la imagen a color → resultado pobre.
- **No** usar `cv2.adaptiveThreshold` con `ADAPTIVE_BLOCK_SIZE` menor al ancho de la línea más fina del texto; pierde información.
- **No** introducir dependencias no declaradas. OpenCV (`opencv-python-headless`), `pypdfium2`, `Pillow`, `numpy` son las únicas permitidas.
- **No** escribir imágenes procesadas con extensión distinta de `.processed.png`. Conservar `.png` para original y `.processed.png` para procesado.
- **No** omitir `preprocess.log`. Aunque se escriba `preprocess_summary.json`, el log plano es el formato canónico para auditoría humana.

## 11. Cómo verificar + cambios permitidos

Cinco pasos (mismo patrón que `architecture.md` §10):

1. ¿El input tiene su hash sha256 intacto tras la invocación? (criterio 3 del roadmap.)
2. ¿Las páginas con rotación > 1° se corrigen automáticamente? (criterio 2.)
3. ¿La fuente hostil mejora su tasa de acierto? (criterio 1.)
4. ¿El `preprocess_summary.json` declara `schema_version` y pasa los checks de `run_eval.py`?
5. ¿El pipeline configurado se ejecuta en orden y omite etapas no pedidas sin error?

```bash
python3 evals/preprocess-sample/run_eval.py
# Esperado: "PASS criterios 1+2+3"
```

**Cambios permitidos sin reabrir Fase 19:**

- Añadir una nueva etapa al pipeline (con ADR; actualizar §3 y `--pipeline`).
- Ajustar las constantes de §4 con evidencia experimental (con ADR).
- Añadir un campo opcional a `preprocess_summary.json` con default sensato.
- Cambiar el renderer por defecto (`pypdfium2` → `pdf2image`) vía flag `--renderer`.

**Reabren Fase 19:**

- Cambiar el algoritmo de deskew (afecta a F22 layout, F31 SDM).
- Cambiar el modelo de preserv del original (afecta a F26 review_report).
- Cambiar el orden fijo del pipeline.
- Dividir `preprocess_summary.json` en dos archivos.

## 12. Siguiente extractor — `ocr.py` (F20)

Tras F19 (preprocesado), las imágenes `<basename>-NNNN.processed.png` necesitan OCR. F20 cubre esa cadena:

1. F20 lee las imágenes `*.processed.png` del directorio `<out-dir>/ingest/pages/` (excluye las originales).
2. Para cada imagen no blank (F19 marca `is_blank: true`), invoca Tesseract 5.x como motor principal con `--languages "spa+eng"` y `--psm 6`.
3. Si `mean_conf < 0.70` y `len(words) > 5`, dispara reintentos en cascada: invert → alternative_engine (EasyOCR) → sparse_psm. Cada reintento se registra en `ocr_summary.json.retries[]`.
4. F20 produce `ocr_summary.json` global + `ocr_pages/<basename>-NNNN.json` por página con `words[]` (text + bbox + conf + position).
5. F22 (clasificación de regiones) y F31 (build_sdm) consumen `ocr_summary.json`.

Detalles e instalación por SO: [`ocr-engines.md`](ocr-engines.md).
