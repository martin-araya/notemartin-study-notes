# `scripts/`

Ejecutables invocables por el agente. **No se leen en contexto**; se invocan por su comando con la entrada y salida declaradas. El catálogo legible está en `scripts/README.md` (producido por F117).

## Qué vivirá aquí

| Subcarpeta | Rol | Fases |
|---|---|---|
| `ingest/` | L0: triaje, OCR, layout, regiones, tablas, fórmulas, código, post-OCR, formatos no PDF | F17-F29, F33 |
| `validate/` | Validadores de SDM, IR, NoteMark, Mermaid, completitud, equivalencia cross-target | F30, F43, F49, F63, F67 |
| `authoring/` | Parser NoteMark, transformaciones de IR | F48, F50 |
| `render/` | Renderers a cada destino + pre-render de diagramas y figuras | F54-F60, F68, F70 |
| `util/` | Caché, visor, ledger, trazabilidad | F36, F38, F52 |
| `README.md` | Catálogo con qué hace cada script, entrada, salida, dependencias, invocación | F117 |

## Reglas (per `AGENT.md` §6)

- Cada script independiente, invocable solo, sin importar un paquete común pesado.
- Entrada y salida por archivo con rutas explícitas por argumento.
- `--help` útil y entrada en `scripts/README.md` con dependencias y comportamiento si faltan.
- Dependencias mínimas y declaradas en `requirements.txt` plano.
- Salida en dos formatos: legible por humano y estructurada para el agente.
- Códigos de salida: 0 correcto, 1 error, 2 advertencias.
- Escritura atómica: temporal + `rename`.

## Cuándo se crea

Esta carpeta se puebla desde F17 en adelante. Hoy tiene **F17 materializado** (`triage.py`).

## Scripts disponibles

### `ingest/triage.py` — F17 · Triaje de archivo

L0 preflight: clasifica una fuente (PDF / EPUB / DOCX / PPTX / HTML / Markdown / TXT / repositorio) y emite un plan de ingesta por rangos de páginas.

| Aspecto | Valor |
|---|---|
| Entrada | `--source <ruta>` (archivo o directorio) |
| Salida | `<out-dir>/triage.json` + `<out-dir>/triage.md` |
| Umbrales | `ingest/thresholds.yaml` (default; override con `--thresholds`) |
| Forzar formato | `--format {auto,pdf,epub,docx,pptx,html,markdown,text,repository}` |
| Solo JSON | `--json-only` |
| Invocación | `python3 scripts/ingest/triage.py --source <ruta> --out-dir <dir>` |
| Dependencias | Python 3.9+ stdlib; PyYAML (recomendado, para umbrales); pypdf (opcional, mejora precisión de PDF) |
| Comportamiento si falta PyYAML | Usa defaults internos; warning en `warnings[]` del JSON |
| Comportamiento si falta pypdf | Análisis PDF a nivel de bytes (aproximado); warning; exit code 2 |
| Códigos de salida | 0 OK · 1 error fatal · 2 OK con advertencias |
| Escritura | Atómica: tempfile + `Path.replace` |
| Documentación | `references/01-ingest/triage.md` (normativa) |

### `ingest/pdf_native.py` — F18 · Extracción de PDF nativo

L0 extracción: extrae runs de texto de un PDF con coordenadas, fuente y tamaño. Detecta encabezados por tipografía, marca boilerplate por repetición posicional y reconstruye el índice desde los marcadores PDF.

| Aspecto | Valor |
|---|---|
| Entrada | `--source <pdf>`; opcionalmente `--plan <triage.json>` para limitar a rangos nativos |
| Salida | `<out-dir>/fragments.json` + `<out-dir>/extraction.md` |
| Solo JSON | `--json-only` |
| Invocación | `python3 scripts/ingest/pdf_native.py --source <pdf> --out-dir <dir> [--plan <triage.json>]` |
| Dependencias | Python 3.9+ stdlib; pypdf >= 4 (obligatorio) |
| Comportamiento si falta pypdf | Error fatal, exit code 1 |
| Códigos de salida | 0 OK · 1 error fatal · 2 OK con advertencias (outline ausente, pure_scan saltadas, etc.) |
| Escritura | Atómica: tempfile + `Path.replace` |
| Constantes | `references/01-ingest/pdf-native.md` §4-§5 (`HEADER_BAND_RATIO=0.08`, `BOILERPLATE_PAGE_RATIO=0.30`, `HEADING_FREQ_MAX=0.20`, etc.) |
| Documentación | `references/01-ingest/pdf-native.md` (normativa) |

### `ingest/preprocess.py` — F19 · Preprocesado de imagen

L0 preprocesado: rasteriza PDFs y aplica un pipeline configurable de 6 etapas (rasterize, deskew, curvature opt-in, denoise, binarize, border) para producir imágenes limpias para OCR. La imagen original nunca se destruye.

| Aspecto | Valor |
|---|---|
| Entrada | `--source <pdf|img|dir>`; `--dpi 300`; `--pipeline csv` |
| Salida | `<out-dir>/ingest/pages/<basename>-NNNN.png` (original) + `<basename>-NNNN.processed.png` + `<basename>-NNNN.meta.json`; `<out-dir>/ingest/preprocess.log` + `preprocess_summary.json` |
| Solo JSON | `--json-only` |
| Invocación | `python3 scripts/ingest/preprocess.py --source <pdf> --out-dir <dir> [--dpi 300] [--pipeline rasterize,deskew,denoise,binarize,border]` |
| Dependencias | Python 3.9+ stdlib; pypdfium2 ≥ 4 (renderizado PDF); opencv-python-headless ≥ 4 (pipeline de imagen); Pillow ≥ 10; numpy ≥ 1.24 |
| Comportamiento si falta alguna dependencia | Error fatal, exit code 1 |
| Códigos de salida | 0 OK · 1 error fatal · 2 OK con advertencias (rotación fuera de rango, blank, curvatura no corregida) |
| Escritura | Atómica: tempfile + `Path.replace` |
| Constantes | `references/01-ingest/preprocess.md` §4 (`DEFAULT_DPI=300`, `MAX_ROTATION_DEG=10.0`, `BLANK_THRESHOLD=0.005`, etc.) |
| Documentación | `references/01-ingest/preprocess.md` (normativa) |

### `ingest/ocr.py` — F20 · Motor OCR multilingüe

L0 OCR: ejecuta Tesseract (motor principal) o EasyOCR (alternativo) sobre las imágenes preprocesadas por F19. Reintentos automáticos en cascada (invert → alternative_engine → sparse_psm) cuando la confianza media cae bajo el umbral. Idiomas combinados (es/en) y wordlists opcionales.

| Aspecto | Valor |
|---|---|
| Entrada | `--source <dir|img>`; `--languages "spa+eng"`; `--engine auto|tesseract|easyocr`; `--user-words <path>`; `--user-patterns <path>` |
| Salida | `<out-dir>/ingest/ocr/ocr_summary.json` (global con retries) + `ocr_pages/<basename>-NNNN.json` (palabras por página con text+bbox+conf) |
| Solo JSON | `--json-only` |
| Invocación | `python3 scripts/ingest/ocr.py --source <dir|img> --out-dir <dir> [--languages "spa+eng"] [--engine tesseract]` |
| Dependencias | Python 3.9+ stdlib; pytesseract ≥ 0.3.10 (Tesseract wrapper); Pillow ≥ 10; opencv-python-headless + numpy (para retry con invert); Tesseract 5.x binario externo; easyocr opcional (lazy import) |
| Comportamiento si falta el motor | Error fatal, exit code 1, con instrucciones de instalación por SO |
| Códigos de salida | 0 OK · 1 error fatal · 2 OK con advertencias (reintentos, motor alternativo, blank) |
| Escritura | Atómica: tempfile + `Path.replace` |
| Constantes | `references/01-ingest/ocr-engines.md` §3 (`OCR_RETRY_THRESHOLD=0.70`, `OCR_MIN_WORDS=5`, `OCR_MAX_RETRIES=3`, `OCR_DEFAULT_PSM=6`, `OCR_SPARSE_PSM=11`) |
| Documentación | `references/01-ingest/ocr-engines.md` (normativa con instalación por SO) |

### `ingest/layout.py` — F21 · Layout y orden de lectura

L0 layout: detecta columnas, sidebars, margin notes, figure captions y floats; calcula el orden de lectura con `continuity_score`; verifica el orden; reunifica párrafos/tablas/código cross-page.

| Aspecto | Valor |
|---|---|
| Entrada | `--source <fragments.json\|ocr_summary.json>` o `--pdf <pdf>` (invoca F18 internamente); `--input-type auto\|pdf-native\|ocr` |
| Salida | `<out-dir>/ingest/layout/page-NNNN.regions.json` + `page-NNNN.reading_order.json` por página + `layout_summary.json` global con `cross_page_links[]` e `inconsistencies[]` |
| Solo JSON | `--json-only` |
| Invocación | `python3 scripts/ingest/layout.py --source <fragments.json> --out-dir <dir> [--json-only]` |
| Dependencias | Python 3.9+ stdlib; numpy (recomendado, opcional) |
| Comportamiento si falta input | Error fatal con código 1 |
| Códigos de salida | 0 OK · 1 error fatal · 2 OK con advertencias (orden roto, cross-page ambiguo) |
| Escritura | Atómica: tempfile + `Path.replace` |
| Constantes | `references/01-ingest/layout.md` §4-§9 (`X_HISTOGRAM_BUCKET_PX=8`, `MIN_COLUMN_DENSITY=0.05`, `SIDEBAR_MAX_WIDTH_RATIO=0.20`, `MARGIN_THRESHOLD_PX=50`, `MIN_CONTINUITY_SCORE=0.30`) |
| Documentación | `references/01-ingest/layout.md` (normativa) |

### `ingest/regions.py` — F22 · Clasificación de regiones

L0 classifier: reclasifica regiones geométricas de F21 en 13 clases semánticas mediante 11 señales tipográficas / geométricas con scoring numérico. Regla dura de ambigüedad: ninguna región se fuerza a una clase cuando las señales son insuficientes.

| Aspecto | Valor |
|---|---|
| Entrada | `--source <layout_dir>` (páginas de F21); opcional `--fragments <fragments.json>` (F18) o `--ocr <ocr_summary.json>` (F20); opcional `--class-profile <yaml>` |
| Salida | `<out-dir>/ingest/regions/page-NNNN.regions.json` (F21 enriquecido) + `regions_summary.json` global con `class_distribution` y `ambiguous_regions[]` |
| Solo JSON | `--json-only` |
| Invocación | `python3 scripts/ingest/regions.py --source <layout_dir> --out-dir <dir> [--fragments <fragments.json>]` |
| Dependencias | Python 3.9+ stdlib (sin numpy ni ML) |
| Comportamiento si falta input | Error fatal con código 1 |
| Códigos de salida | 0 OK · 1 error fatal · 2 OK con advertencias (regiones ambiguas, falta fragments/ocr) |
| Escritura | Atómica: tempfile + `Path.replace` |
| Constantes | `references/01-ingest/regions.md` §6 (`CLASS_MIN_THRESHOLD=0.45`, `AMBIGUITY_MARGIN=0.10`, `LARGE_FACTOR=1.3`, `EMPTY_AREA_RATIO=0.60`) |
| Documentación | `references/01-ingest/regions.md` (normativa) |
