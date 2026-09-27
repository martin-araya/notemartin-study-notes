# `scripts/`

Ejecutables invocables por el agente. **No se leen en contexto**; se invocan por su comando con la entrada y salida declaradas. El catálogo legible está en `scripts/README.md` (producido por F117).

## Qué vivirá aquí

| Subcarpeta | Rol | Fases |
|---|---|---|
| `ingest/` | L0: triaje, OCR, layout, regiones, tablas, fórmulas, código, post-OCR, formatos no PDF | F17-F29, F33 |
| `validate/` | Validadores de SDM, IR, NoteMark, Mermaid, completitud, equivalencia cross-target | F30, F43, F49, F63, F67 |
| `authoring/` | Parser NoteMark → IR (F48, `parse_notemark.py`); transformaciones de IR (F50) | F48, F50 |
| `render/` | Renderers a cada destino + pre-render de diagramas y figuras | F54-F60, F68, F70 |
| `util/` | Caché, visor, ledger, grafo de conceptos, trazabilidad | F36, F38, F39, F52 |
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

### `ingest/tables.py` — F23 · OCR de tablas

L0 table extractor: detecta tablas (con o sin bordes) a partir de las regiones `table` de F22 (con fallback geométrico desde fragments si F22 no marcó ninguna). Clusterización por filas y columnas, celdas combinadas (rowspan/colspan), headers multinivel y reunión cross-page. Verificación dura de integridad (rows × cols = data × cells, no truncado).

| Aspecto | Valor |
|---|---|
| Entrada | `--source <regions_dir>` (F22); opcional `--fragments <fragments.json>` (F18) o `--ocr <ocr_summary.json>` (F20) |
| Salida | `<out-dir>/ingest/tables/page-NNNN.tables.json` (tablas por página con headers/data/merged_cells) + `tables_summary.json` global con cross-page merged |
| Solo JSON | `--json-only` |
| Invocación | `python3 scripts/ingest/tables.py --source <regions_dir> --out-dir <dir> [--fragments <fragments.json>]` |
| Dependencias | Python 3.9+ stdlib (sin numpy ni ML) |
| Comportamiento si falta input | Error fatal con código 1 |
| Códigos de salida | 0 OK · 1 error fatal · 2 OK con advertencias (low_confidence, cross-page ambiguo) |
| Escritura | Atómica: tempfile + `Path.replace` |
| Constantes | `references/01-ingest/tables.md` §4-§8 (`ROW_BAND_TOL_PX=4.0`, `COL_BAND_TOL_PX=6.0`, `HEADER_MAX_ROWS=3`, `MERGED_CELL_FACTOR=4.0`, `CROSS_PAGE_HEADER_MATCH_THRESHOLD=0.80`) |
| Documentación | `references/01-ingest/tables.md` (normativa) |

### `ingest/formulas.py` — F24 · OCR de fórmulas

L0 formula OCR: extrae fórmulas matemáticas como LaTeX, valida con un verificador regex puro Python (sin pdflatex), preserva numeración y marca pendientes las fórmulas inválidas con recorte de imagen o bbox referencial.

| Aspecto | Valor |
|---|---|
| Entrada | `--source <regions_dir>` (F22); opcional `--fragments <fragments.json>` (F18) o `--ocr <ocr_summary.json>` (F20); opcional `--images-dir <images_dir>` (F19) para recortes |
| Salida | `<out-dir>/ingest/formulas/page-NNNN.formulas.json` (fórmulas por página) + `formulas_summary.json` global con `equation_index[]` + recortes PNG de pendientes |
| Solo JSON | `--json-only` |
| Invocación | `python3 scripts/ingest/formulas.py --source <regions_dir> --out-dir <dir> [--fragments <fragments.json>] [--images-dir <dir>]` |
| Dependencias | Python 3.9+ stdlib; Pillow opcional (solo si se recortan imágenes) |
| Comportamiento si falta input | Error fatal con código 1 |
| Códigos de salida | 0 OK · 1 error fatal · 2 OK con advertencias (pending, numeración faltante) |
| Escritura | Atómica: tempfile + `Path.replace` |
| Constantes | `references/01-ingest/formulas.md` §5-§6 (`LATEX_MAX_NESTED_BRACES=5`, `INLINE_MAX_HEIGHT_PX=30`, `INLINE_MAX_WIDTH_RATIO=0.5`, ~80 macros en whitelist) |
| Documentación | `references/01-ingest/formulas.md` (normativa) |

### `ingest/code_ocr.py` — F25 · OCR de código y consolas

L0 code/console OCR: reconstruye texto byte-exact preservando indentación, aplica solo correcciones sintácticas forzadas (cada una registrada con char_pos, original, corrected, reason), separa prompt y salida en consolas, y marca como `low_confidence: true` cualquier bloque dudoso con `reason` documentado.

| Aspecto | Valor |
|---|---|
| Entrada | `--source <regions_dir>` (F22); opcional `--fragments <fragments.json>` (F18) |
| Salida | `<out-dir>/ingest/code/page-NNNN.code.json` (bloques por página con text/language/confidence/low_confidence/corrections/commands/output) + `code_summary.json` global con correcciones y low_confidence_blocks |
| Solo JSON | `--json-only` |
| Invocación | `python3 scripts/ingest/code_ocr.py --source <regions_dir> --out-dir <dir> [--fragments <fragments.json>]` |
| Dependencias | Python 3.9+ stdlib (sin numpy ni ML) |
| Comportamiento si falta input | Error fatal con código 1 |
| Códigos de salida | 0 OK · 1 error fatal · 2 OK con advertencias (correcciones, low_confidence) |
| Escritura | Atómica: tempfile + `Path.replace` |
| Constantes | `references/01-ingest/code-ocr.md` §3-§8 (`LINE_HEIGHT_TOL_PX=4.0`, `SMALL_GAP=2.0`, `LOW_CONFIDENCE_THRESHOLD=0.7`, `MAX_CORRECTIONS_PER_BLOCK=20`) |
| Documentación | `references/01-ingest/code-ocr.md` (normativa) |

### `ingest/review_report.py` — F26 · Confianza y revisión humana

Fase mixta (script + spec): agrega confianza por tipo de región, genera reporte HTML con recortes de imagen y texto lado a lado, bloquea si hay demasiadas regiones críticas dudosas, propaga correcciones humanas a repeticiones del mismo error.

| Aspecto | Valor |
|---|---|
| Entrada | `--source <ingest_dir>` (contiene ingest/regions, tables, formulas, code); opcional `--images-dir <images_dir>` (F19) para recortes; opcional `--corrections <corrections.json>` para propagación |
| Salida | `<out-dir>/ingest/review/report.html` (reporte interactivo con filter bar JS) + `summary.json` (machine-readable con umbrales, blocked, applied_corrections, propagated_corrections) + `crops/page-NNNN/<id>.png` (recortes Pillow) |
| Solo JSON | `--json-only` |
| Invocación | `python3 scripts/ingest/review_report.py --source <ingest_dir> --out-dir <dir> [--images-dir <dir>] [--corrections <corrections.json>]` |
| Dependencias | Python 3.9+ stdlib; Pillow opcional (solo para recortes de imagen) |
| Comportamiento si falta input | Error fatal con código 1 |
| Códigos de salida | 0 OK · **1 BLOQUEADO** (≥ 3 regiones críticas dudosas) · 2 OK con advertencias |
| Escritura | Atómica: tempfile + `Path.replace` |
| Constantes | `references/01-ingest/confidence.md` §2-§5 (15 umbrales por clase, `MAX_LOW_CONF_CRITICAL=3`, `CROP_PADDING_PX=5`, `PROPAGATION_MIN_LENGTH=5`) |
| Documentación | `references/01-ingest/confidence.md` (normativa) |

### `ingest/post_ocr.py` — F27 · Corrección post-OCR determinista

Aplica correcciones deterministas (R001-R010) y diccionario técnico auditable. NUNCA usa ML; NUNCA modifica código ni tablas. Cada corrección tiene `correction_id` único y es individualmente revertible.

| Aspecto | Valor |
|---|---|
| Entrada | `--source <ingest_dir>` (contiene ingest/regions); opcional `--dictionary <dictionary.yaml>` (default: 5 entradas comunes) |
| Salida | `<out-dir>/ingest/post_ocr/page-NNNN.post_ocr.json` (regiones con original/corrected/corrections) + `post_ocr_summary.json` (global) + `audit_log.json` (applies + reverts) |
| Modos | apply (default) · `--revert <correction_id>` · `--revert-all` |
| Invocación | `python3 scripts/ingest/post_ocr.py --source <ingest_dir> --out-dir <dir> [--dictionary <dict.yaml>]` |
| Dependencias | Python 3.9+ stdlib (sin numpy ni ML) |
| Comportamiento si falta input | Error fatal con código 1 |
| Códigos de salida | 0 OK · 1 error fatal · 2 OK con advertencias (regiones saltadas, parcial) |
| Escritura | Atómica: tempfile + `Path.replace` |
| Constantes | `references/01-ingest/post-ocr.md` §3-§7 (10 reglas R001-R010, `INDENT_PRESERVE_MIN=4`, `MAX_CORRECTIONS_PER_REGION=50`, `MAX_DICTIONARY_ENTRIES=1000`, `MAX_AUDIT_LOG_ENTRIES=1000`) |
| Documentación | `references/01-ingest/post-ocr.md` (normativa) |

### `ingest/other_formats.py` — F28 · EPUB, DOCX, PPTX, transcripciones

Procesa formatos que no son PDF y los normaliza al contrato de F22. Detecta formato por extensión + magic bytes. EPUB (`ebooklib`), DOCX (`python-docx`), PPTX (`python-pptx`), SRT/VTT/JSON (stdlib). Notas del orador → `speaker_note` (bloques propios). Muletillas fuera en transcripciones (whitelist cerrada). Marcas temporales como `anchor_id` resolubles.

| Aspecto | Valor |
|---|---|
| Entrada | `--source <file_or_dir>` (EPUB/DOCX/PPTX/SRT/VTT/JSON); `--format auto\|epub\|docx\|pptx\|srt\|vtt\|json` (opcional) |
| Salida | `<out-dir>/ingest/other_formats/<basename>.<fmt>.regions.json` (por formato) + `summary.json` (global con class_distribution, fillers_removed_count) |
| Invocación | `python3 scripts/ingest/other_formats.py --source <dir> --out-dir <dir> [--format auto]` |
| Dependencias | Python 3.9+ stdlib; `ebooklib` + `python-docx` + `python-pptx` opcionales (cada uno emite error claro si falta) |
| Comportamiento si falta input | Error fatal con código 1 |
| Códigos de salida | 0 OK · 1 error fatal · 2 OK con advertencias |
| Escritura | Atómica: tempfile + `Path.replace` |
| Constantes | `references/01-ingest/other-formats.md` §2-§7 (`TRANSCRIPT_FILLER_WORDS` = {um, uh, er, ah, eh, mm, hmm, mm-hmm, uh-huh}, `MIN_PAUSE_FOR_FILLER_REMOVAL_S = 2.0`, ITEM_NOTE=10) |
| Documentación | `references/01-ingest/other-formats.md` (normativa) |

### `ingest/web_docs.py` — F29 · Documentación web multipágina

Procesa un mirror de documentación HTML multipágina y produce `sections.json` con el orden del índice preservado, texto limpio (sin boilerplate: nav/menus/banners/footers), URL canónica por sección y versión del producto detectada. BFS desde `--index` con `--max-depth` y `--max-pages`. Sin ML, sin OCR, sin descarga de URLs remotas (wget se hace fuera de F29).

| Aspecto | Valor |
|---|---|
| Entrada | `--source <dir>` (mirror HTML local); `--base-url <url>`; opcional `--index <path>` (default `index.html`); opcional `--respect-robots-txt`, `--allow-domain`, `--max-depth`, `--max-pages` |
| Salida | `<out-dir>/ingest/web_docs/sections.json` (array de secciones en orden del índice) + `metadata.json` (global con total_pages, product_version, domain, warnings) |
| Invocación | `python3 scripts/ingest/web_docs.py --source <dir> --base-url <url> --out-dir <dir> [--index <path>]` |
| Dependencias | Python 3.9+ stdlib (html.parser) |
| Comportamiento si falta input | Error fatal con código 1 |
| Códigos de salida | 0 OK · 1 error fatal · 2 OK con advertencias |
| Escritura | Atómica: tempfile + `Path.replace` |
| Constantes | `references/01-ingest/web-docs.md` §2-§7 (`MAX_PAGES_DEFAULT=500`, `MAX_DEPTH_DEFAULT=5`, `MIN_TEXT_LENGTH=50`, lista `BOILERPLATE_SELECTORS` con 14 selectores, `BOILERPLATE_ROLES` con 3 valores ARIA, `VERSION_PATTERNS` con 2 regex) |
| Documentación | `references/01-ingest/web-docs.md` (normativa) |

### `validate/ingest_check.py` — F30 · Verificación de ingesta (gate a L2)

Detecta anomalías en la ingesta (páginas omitidas, secciones del índice ausentes, saltos de numeración, bloques vacíos, densidad anómala). Actúa como **puerta de verificación** entre L0 y L1/L2: exit 1 bloquea el avance si hay anomalías críticas sin override humano explícito.

| Aspecto | Valor |
|---|---|
| Entrada | `--sdm <path>` (file o directorio `page-*.regions.json`); opcional `--declared-index <path>` (TOC JSON); opcional `--allow-critical --human-decision "..."` (override explícito) |
| Salida | `<out-dir>/validation_report.json` (anomalías critical + warnings) + opcional `<out-dir>/decision_log.json` (registro de overrides) |
| Invocación | `python3 scripts/validate/ingest_check.py --sdm <path> --out-dir <dir> [--declared-index <path>]` |
| Dependencias | Python 3.9+ stdlib (sin numpy ni ML) |
| Comportamiento si falta input | Error fatal con código 1 |
| Códigos de salida | 0 OK · 1 BLOQUEADO (críticas sin override) · 2 OK con warnings |
| Escritura | Atómica: tempfile + `Path.replace` |
| Constantes | `references/01-ingest/ingest-check.md` §2-§7 (`MIN_WORDS_PER_BLOCK=3`, `MAX_WORDS_PER_BLOCK=5000`, `MAX_NUMBERING_JUMP_FOR_WARNING=1`, `MAX_NUMBERING_JUMP_FOR_CRITICAL=100`) |
| Documentación | `references/01-ingest/ingest-check.md` (normativa) |

### `validate/provenance.py` — F34 · Procedencia y versión

Valida que cada SDM lleva `source_provenance` con los campos requeridos (id, hash, vendor, product, version), aplica las reglas duras de distinguibilidad (`read ⇒ confidence==1.0`; métodos inferidos ⇒ `confidence<1.0`), y opcionalmente aplica `--require-version` como gate de release (documentación sin versión ⇒ exit 1).

| Aspecto | Valor |
|---|---|
| Entrada | `--sdm <path>` (file o dir con `*.json`) |
| Salida | `--report <path>` JSON (`validation_report.json` por defecto) |
| Modos | `--require-version` (gate; exit 1 cuando documentación sin versión); `--min-confidence <float>` (warning por debajo del umbral, default 0.7); `--json-only` |
| Invocación | `python3 scripts/validate/provenance.py --sdm <path> [--require-version] [--min-confidence 0.7]` |
| Dependencias | Python 3.9+ stdlib |
| Comportamiento si falta | Error fatal (input ausente o ilegible) con exit 1 |
| Códigos de salida | 0 OK · 1 hard fail (`--require-version` + doc sin version) · 2 OK con warnings (inferred bajo umbral o version ausente sin `--require-version`) |
| Escritura | Atómica: `tempfile` + `Path.replace` para texto y JSON |
| Constantes | inline en el docstring (taxonomía de 8 métodos; `INFERRED_METHODS = {inferred, url_regex, cover_or_header, web_docs_metadata}`; `triage_metadata` excluido porque su `confidence == 1.0` por spec §4) |
| Documentación | `references/02-source-model/provenance.md` (normativa) |

### `ingest/assets.py` — F33 · Catálogo de assets

L0→L1 catálogo: lee el SDM (F31), auto-extrae las imágenes desde `--source-file` (PDF vía pypdfium2, EPUB vía ZIP), dedup por hash sha256 con nombre determinista (`assets/<source_id>/<sha256[:16]>.<ext>`), clasifica cada asset en `diagram_conceptual | screenshot | data_figure | decorative` mediante heurística Pillow + override YAML por vendor/product, valida alt text (decorativas pueden llevar `alt=""`, no-decorativas requieren `alt` ≥ 3 chars), actualiza `figure.content.src` en el SDM y emite `assets.json` + `assets_summary.json` (counts + discarded + warnings).

| Aspecto | Valor |
|---|---|
| Entrada | `--sdm <sdm.json>` (F31 output); `--source-file <pdf\|epub>`; opcional `--out-sdm <path>` (default: sobreescribe `--sdm`); opcional `--classify <yaml>` (overrides vendor/product → class) |
| Salida | `<out-dir>/assets/<source_id>/<sha256[:16]>.<ext>` (1 archivo por hash único) + `<out-dir>/assets/assets.json` + `<out-dir>/assets/assets_summary.json` + opcional `<out-dir>/assets/assets.md` |
| Solo JSON | `--json-only` |
| Invocación | `python3 scripts/ingest/assets.py --sdm <sdm.json> --source-file <pdf\|epub> --out-dir <dir> [--out-sdm <path>] [--classify <yaml>]` |
| Dependencias | Python 3.9+ stdlib; Pillow ≥ 10 (obligatorio); pypdfium2 ≥ 4 (PDF); `zipfile` stdlib para EPUB (sin ebooklib obligatorio) |
| Comportamiento si falta Pillow | Decorativos con fallback, warning + `needs_review=true` |
| Comportamiento si falta pypdfium2 (PDF) | Exit 1 con instrucción de instalación |
| Códigos de salida | 0 OK sin advertencias · 1 error fatal / source ilegible · 2 OK con advertencias (`missing_alt`, `low_resolution`, `format_not_supported` para figuras HTML) |
| Escritura | Atómica: `tempfile` + `Path.replace` para texto, JSON y bytes |
| Constantes | inline (`MIN_DIMMENSION_PX=32`, `MIN_WIDTH_PX=256`, `MIN_HEIGHT_PX=256`, `DECORATIVE_AREA_RATIO=0.05`, `SCREENSHOT_ASPECTS=[(16,9),(16,10),(4,3),(3,2)]`, `EDGE_DENSITY_MIN=0.04`, `COLOR_BUCKETS_MIN=4`, `MAX_LARGE_BYTES=50 MB`) — registradas en `--help` epilog |

### `ingest/build_sdm.py` — F31 · Construcción del SDM

L0→L1 ensamble: consume la salida de F17-F30 (regions, tables, formulas, code, review, web_docs, other_formats, fragments) en un único `sdm.json` conforme a `schemas/sdm.schema.json` (F13). Genera ids deterministas, asocia pies a figuras dentro de `CAPTION_MAX_PAGES_AHEAD=1` página y preserva referencias de footnotes. Valida el resultado contra el schema vía `scripts/util/validate_sdm.py`.

| Aspecto | Valor |
|---|---|
| Entrada | `--ingest-dir <dir>` (con `regions/`, `tables/`, `formulas/`, `code/`, `web_docs/`, `other_formats/`, `fragments.json`); `--source-meta <yaml>` (id, hash sha256 hex64, vendor, product, url, language, format); opcional `--source-file <path>` para calcular hash; opcional `--format {auto,pdf,html,epub,docx,pptx,transcript,repo}` |
| Salida | `<out-dir>/sdm.json` + `<out-dir>/build_sdm_summary.json` + `<out-dir>/build_sdm.md` |
| Determinismo | `--check-determinism` (re-construye dos veces y compara byte a byte) |
| Solo JSON | `--json-only` |
| Invocación | `python3 scripts/ingest/build_sdm.py --ingest-dir <dir> --source-meta <yaml> --out-dir <dir> [--format auto] [--check-determinism]` |
| Dependencias | Python 3.9+ stdlib; PyYAML (obligatorio para `--source-meta`); `scripts/util/validate_sdm.py` (subproceso) para validación de schema |
| Comportamiento si falta PyYAML | Exit 1 con instrucción de instalación |
| Códigos de salida | 0 OK sin advertencias · 1 error fatal / schema invalid / determinismo roto · 2 OK con advertencias (asociaciones faltantes, regiones ambiguas, etc.) |
| Escritura | Atómica: tempfile + `Path.replace` |
| Constantes | `references/02-source-model/build-sdm.md` §6-§9 (`CAPTION_PATTERN`, `CAPTION_MAX_PAGES_AHEAD=1`, `AMBIG_CLASS_MIN=0.45`, fórmula de id `sha1(hash + path + idx)[:12]`)

### `util/sdm_cache.py` — F36 · Caché por hash con invalidación selectiva

API Python (`cache_get_or_compute(source_hash, step, engine_version, script_version, params, compute_fn, cache_dir)`) que evita recomputes cuando la misma fuente + step + motor + script_version + params se repiten (criterio 1). Cambios en `engine_version` invalidan solo esa rama (criterio 2); coexisten directorios por motor. Para uso futuro por F19/F25/F31/F23/F24 — esta fase entrega la librería y la cierra sin reabrir otros contratos.

| Aspecto | Valor |
|---|---|
| CLI subcomandos | `put` (almacena desde `--value-file`), `get` (imprime stdout; exit 2 si no existe), `list`, `invalidate` (`--step s [--engine-version v]`), `info` (resumen por step / engine_version) |
| Layout | `<cache-dir>/<step>/<key>.json` con `key = sha256(source_hash + step + engine_version + script_version + params_canon)[:16]`; `index.json` en la raíz |
| Override | `--cache-dir <dir>` (default `.sdm_cache`) |
| Invocación | `python3 scripts/util/sdm_cache.py put --step ocr --source-hash <h> --engine-version <ev> --value-file <f>` |
| API | `from sdm_cache import cache_get_or_compute; cache_get_or_compute(...)` |
| Dependencias | Python 3.9+ stdlib |
| Comportamiento si `cache_dir` no existe | Creado transparente; sin cache previo → `compute_fn()` se invoca y se persiste |
| Códigos de salida | 0 OK · 1 error fatal (input ilegible) · 2 OK con warning (`get` con cache miss) |
| Escritura | Atómica: `tempfile` + `Path.replace` |
| Constantes inline | función `cache_clear_engine_version` (selective), `cache_clear_step` (wipe), `cache_info` (resumen) |

### `util/sdm_view.py` — F36 · Visor HTML self-contained del SDM

Genera un archivo HTML único con CSS + JS inline (sin assets externos). Jerarquía (aside izquierdo), resumen con histogramas y conteos por tipo, lista de bloques con `data-confidence`, badge de origen, anchor.page, y enlace al source. Filtros reactivos client-side: dropdown por tipo (16 clases + "all"), input numérico de umbral de confianza, botón "Show only low-confidence (< 0.7)" (criterio 3), checkbox Hide boilerplate. Bloques con `figure.content.src` muestran `<img>` o placeholder. Si `source.url` está presente, muestra `→ go to source` por bloque.

| Aspecto | Valor |
|---|---|
| Entrada | `--sdm <path>` (F31 output) |
| Salida | `--out <html>` (HTML self-contained) |
| Skip imágenes | `--no-include-images` (omite el resolver a `file://`) |
| Invocación | `python3 scripts/util/sdm_view.py --sdm <sdm.json> --out <out.html> [--no-include-images]` |
| Dependencias | Python 3.9+ stdlib (`html`, `json`, `base64`, `pathlib`) — sin Pillow, sin CDN |
| Comportamiento | Cero assets externos (CSS/JS inline); funciona offline; los filtros son client-side sin backend |
| Códigos de salida | 0 OK · 1 sdm no encontrado o inválido · 2 OK con warnings (assets no resueltos) |
| Constantes inline | 16 BLOCK_TYPES, lista cerrada de clases para dropdown |
| Límites | Sin paginación; para SDMs > 100k bloques el visor puede ralentizar (DOM completo); fuera del scope F36 | |
| Documentación | `references/02-source-model/build-sdm.md` (normativa) |

### `util/ledger.py` — F38 · CLI operativo del Coverage Ledger

CLI con 6 subcomandos para mantener `knowledge/ledger.json` desde L2: `init`, `add` (aplica R1–R5 mecánicamente), `mark` (transiciona estados), `report` (4 vistas de cobertura, funciona en cualquier punto), `check` (detecta huérfanos y gaps; `--strict` rompe con desviaciones; `--include-prose` cuenta bloques `prose` como gap), `manifest` (parchea `manifest.json::units_processed + last_modified` sin tocar otros campos; `--dry-run` muestra el patch). Convierte cada `add`/`mark` en escritura atómica `tempfile + Path.replace` (L-04). Aplica las reglas automáticas R1–R5 importadas de `util/unit_rules.py` (F37). Endurece el `entries[].type` al enum cerrado de 14 tipos (F37/ADR-0001).

| Aspecto | Valor |
|---|---|
| CLI subcomandos | `init [--force]`, `add --unit-id ... --source-block-ids ... --type ... [--content ...] [--section-path ...] [--criticality ...] [--rationale ...]`, `mark <id> --state {written,merged,discarded} [--target-note ...] [--target-section ...] [--discard-reason ...]`, `report`, `check [--strict] [--include-prose]`, `manifest [--dry-run]` |
| Paths por defecto | `--workdir <PATH>`; `<workdir>/sdm.json` + `<workdir>/knowledge/ledger.json` + `<workdir>/manifest.json` |
| Override de paths | `--sdm`, `--ledger`, `--manifest` |
| Invocación | `python3 scripts/util/ledger.py --workdir .notes-work/<hash> add --unit-id u_001 --source-block-ids a8f4ce140580 --type parameter --section-path /ch02 --content '{"name":"shared_buffers"}'` |
| Validación | Schema (`schemas/ledger.schema.json` v2.0.0) vía `jsonschema` opcional; invariantes L-04/L-05 del spec `references/03-knowledge/ledger.md`; reglas R1–R5 vía `util/unit_rules.py` |
| Dependencias | Python 3.9+ stdlib; `jsonschema` opcional (validación contra el schema) |
| Comportamiento si falta `jsonschema` | Validación opcional desactivada; las invariantes L-04/L-05 siguen activas; exit codes iguales |
| Códigos de salida | 0 OK · 1 validación (schema/invariantes/--strict) · 2 uso (paths faltantes) |
| Escritura | Atómica: `tempfile` + `Path.replace` (L-04) |
| Constantes inline | `TERMINAL_STATES`, `ALLOWED_DISCARD_REASONS`, `ALLOWED_TYPES` (los 14 tipos de F37 §3) |
| Documentación | `references/03-knowledge/ledger-operativo.md` (normativa) |

### `util/unit_rules.py` — F37/F38 · Reglas automáticas R1–R5 (fuente única)

Módulo compartido que codifica `AUTO_RULES` (R1–R4 por tipo) y la condición adicional de R5 (`formula` con `content.numbered == true`). Exporta `is_must_keep(block) -> Optional[str]` que devuelve el id de regla o `None`. Importado por `evals/information-units-sample/{build_fixtures,run_eval}.py` (vía shim) y por `util/ledger.py` (F38). Cero dependencias.

| Aspecto | Valor |
|---|---|
| API | `is_must_keep(block)`, `AUTO_RULES: dict[str, str]` |
| Bloque/unidad aceptado | dict con `type: string` y `content: dict` |
| Invocación | `from unit_rules import is_must_keep` |
| Documentación | `references/03-knowledge/information-units.md` §5 (normativa) |

### `util/concept_graph.py` — F39 · CLI del grafo de prerrequisitos

CLI con 4 subcomandos que deriva `knowledge/concept-graph.json` desde el ledger (F38) + SDM (F13) como proyección. Nodos desde unidades `definition`; aristas desde unidades `cross-reference` con `content.relation: "prerequisite"`. Respeta `profile.yaml::graph.cycle_policy` (`block` default exit 1; `allow` registra ciclos en `cycles[]` y continúa). Detecta ciclos con DFS iterativo + marcas white/gray/black; calcula rutas (Dijkstra para `shortest`, DFS con poda para `broadest`); exporta un `.mmd` por dominio (`flowchart LR` con aristas `-->|prereq|`). Comparte `atomic_write_json` con `ledger.py` vía `util/_io.py`.

| Aspecto | Valor |
|---|---|
| CLI subcomandos | `build`, `routes [--goal <id>] [--domain <d>] [--strategy {shortest,broadest,all}]`, `export [--out-dir <dir>]` (genera `<dir>/<domain>/graph.mmd`), `check [--strict]` |
| Paths por defecto | `--workdir <PATH>`; `<workdir>/knowledge/ledger.json` + `<workdir>/sdm.json` + `<workdir>/profile.yaml` (opcional) |
| Override | `--profile` |
| Invocación | `python3 scripts/util/concept_graph.py --workdir .notes-work/<hash> build` |
| Dependencias | Python 3.9+ stdlib; PyYAML opcional (lectura de `profile.graph.cycle_policy`); `jsonschema` opcional (validación contra schema) |
| Comportamiento si falta PyYAML | `cycle_policy=block` por default + WARNING a stderr |
| Comportamiento si falta jsonschema | Validación opcional desactivada; exit codes iguales |
| Códigos de salida | 0 OK · 1 validación (ciclos con `cycle_policy=block`) · 2 uso (paths faltantes) |
| Escritura | Atómica: `tempfile` + `Path.replace` (compartido con `ledger.py` vía `_io.py`) |
| Constantes inline | `ALLOWED_RELATIONS = {"prerequisite"}`, `MAX_LABEL_LEN = 80`, `CYCLE_POLICIES = {"block", "allow"}` |
| Documentación | `references/03-knowledge/concept-graph.md` (normativa) |
| Schema | `schemas/concept-graph.schema.json` |

### `util/_io.py` — F38/F39/F54 · Utilidad I/O compartida (escritura atómica)

Helper interno que codifica el patrón `tempfile` + `Path.replace` (L-04 de F15). Importado por `ledger.py`, `concept_graph.py` y `render/obsidian.py`. Sin dependencias externas.

| Aspecto | Valor |
|---|---|
| API | `atomic_write_json(path: Path, payload: Any) -> None` · `atomic_write_text(path: Path, payload: str\|bytes) -> None` (añadida en F54) |
| Garantía | El path destino siempre queda con un JSON válido o un texto UTF-8 (o no se toca) |
| Documentación | (helper interno; sin spec normativa) |

### `validate/completeness.py` — F43 · Auditoría de no-pérdida

CLI con 4 subcomandos que audita ledger (F38) contra SDM (F13): forward pass (localización + no-mutilación), inverse sample (estratificado: 100% must-keep + 10% context con seed configurable), threshold gate (100% must-keep con estado terminal). Emite reporte JSON con lista accionable de hallazgos (anchor + severity + category + expected/actual + fix). Exit 1 con cualquier finding critical (criterio 3 del roadmap: no se puede cerrar con rojo). Comparte `atomic_write_json` con `ledger.py`/`concept_graph.py` vía `util/_io.py`. Validación opcional contra `schemas/ledger.schema.json` y `schemas/sdm.schema.json` con `jsonschema`.

| Aspecto | Valor |
|---|---|
| CLI subcomandos | `audit` (default; emite JSON o `--out <path>`), `report` (humano), `check [--strict]` (aborta al primer critical), `fix` (solo lista accionable) |
| Paths por defecto | `--workdir <PATH>`; `<workdir>/sdm.json` + `<workdir>/knowledge/ledger.json` |
| Override | `--sdm`, `--ledger` |
| Muestreo | `--sample-rate 0.10` (10% context), `--seed 0` (reproducible); 100% must-keep siempre |
| Invocación | `python3 scripts/validate/completeness.py --workdir .notes-work/<hash> audit` |
| Dependencias | Python 3.9+ stdlib; `jsonschema` opcional (validación contra schema) |
| Comportamiento si falta `jsonschema` | Validación opcional desactivada con WARNING; las invariantes R1/R2/R4 siguen activas |
| Códigos de salida | 0 PASS (sin critical) · 1 FAIL (≥1 critical; gate rojo) · 2 uso (paths faltantes) |
| Escritura | Atómica con `--out <path>`: `tempfile` + `Path.replace` |
| Constantes inline | `MUST_KEEP_TYPES_PLAIN`, `MUST_KEEP_TYPES_FORMULA_NUMBERED`, `EDITORIAL_SEVERITIES_MUST_KEEP`, `EXACT_MATCH_FIELDS`, `NORMALIZED_MATCH_FIELDS`, `DEFAULT_SAMPLE_RATE=0.10`, `DEFAULT_SEED=0` |
| Documentación | `references/10-quality/completeness-audit.md` (normativa) |

### `render/obsidian.py` — F54 · Renderer Obsidian

L4 renderer: traduce el Note IR validado a Markdown nativo de Obsidian 1.5+. Implementa el contrato `render(ir, profile, matrix) → (artifacts, degradation_report)` definido en `references/08-render/contract.md` (F53). Para Obsidian: 13 capacidades ✅ (admonition → callout nativo, collapsible → callout plegable, link-note → wikilink, propiedades → YAML frontmatter, diagram → bloque Mermaid, equation, code, table simple, list, checklist, figure, step, divider) + 1 ❌ (celdas combinadas → degradación elegante con `<details>`). Dataview es opt-in (`--enable-dataview`); por defecto las consultas se degradan a admonition estática para cumplir el criterio 1 ("sin ningún plugin").

| Aspecto | Valor |
|---|---|
| Entrada | `--ir <path>` (archivo `.json` o directorio de IRs); `--profile <path>` (YAML); `--out-dir <dir>` (raíz del workdir) |
| Salida | `<out-dir>/render/obsidian/<folder>/<note-id>.md` por nota (cabecera YAML §8); `<out-dir>/reports/render-degradation.json` + `.md` siempre (RC-03) |
| Matriz | `--matrix <path>` (default: `references/08-render/capability-matrix.md`) |
| Source hash | `--source-hash <hex64>` (override; si no, se lee de `<out-dir>/manifest.json`) |
| Dataview opt-in | `--enable-dataview` (default off: admonition estática; on: bloque ```dataview dentro de admonition) |
| Renderer version | `--renderer-version <semver>` (default `0.1.0`); bumpear implica regenerar |
| Folder | `profile.targets.obsidian.folder` (default `notes/`) |
| Invocación | `python3 scripts/render/obsidian.py --ir evals/obsidian-render-sample/fixtures --profile <profile> --out-dir /tmp/workdir` |
| Dependencias | Python 3.9+ stdlib puro (sin paquetes externos); parser YAML mínimo propio para `targets.obsidian.*` |
| Comportamiento si falta input | Error fatal con código 1 |
| Códigos de salida | 0 OK · 1 error fatal · 2 OK con advertencias (severidad desconocida, wikilinks sin resolver) |
| Escritura | Atómica: `tempfile` + `Path.replace` (compartido con F38/F39 vía `util/_io.py`) |
| Constantes inline | `SEVERITY_TO_CALLOUT` (20 severidades → 13 callout types), `NATIVE_CALLOUTS` (13), `OPEN_SUFFIX="+"`, `CLOSED_SUFFIX="-"`, `DEFAULT_SEVERITY="note"` |
| Tabla de degradación | `references/08-render/contract.md §6` fila 1 (Obsidian/Celdas combinadas) |
| Documentación | `references/08-render/contract.md` (F53, contrato) + docstring del script |
| Schema del reporte | `evals/render-contract-sample/schema/report.schema.json` (Draft 2020-12) |

### `render/notion_api.py` — F55 · Renderer Notion API

L4 renderer: traduce el Note IR validado a páginas de Notion vía la API REST (`https://api.notion.com/v1`, version `2022-06-28`). Implementa el contrato `render(ir, profile, matrix) → (artifacts, degradation_report)` definido en `references/08-render/contract.md` (F53). Cubre las 14 capacidades de Notion API: 13 nativas ✅ (admonition → callout con icon+color, collapsible → toggle, link-note → mention, propiedades → database properties con tipo correcto, diagram Mermaid → code lang=mermaid, equation, code, table simple, list, checklist, figure, step, divider, quote, columns) + 1 ❌ (celdas combinadas → fila 2 §6 contract). Troceo en chunks de 100 bloques/petición (capability-matrix §4). Anidamiento en 2 pasadas con `_nested` placeholder para > 2 niveles. Reintentos con backoff exponencial 5s/30s/2m/10m ante 429 o 5xx (architecture.md §8). Idempotencia por búsqueda de `notemartin_note_id` property (D4 ADR-0010). Cliente HTTP con `urllib.request` stdlib puro.

| Aspecto | Valor |
|---|---|
| Entrada | `--ir <path>`; `--profile <path>`; `--out-dir <dir>`; `--notion-token <token>` (o env `NOTION_TOKEN`) |
| Salida | `<out-dir>/render/notion_api/payloads/<note-id>-NNN.json` por chunk (dry-run); `<out-dir>/reports/render-degradation.{json,md}` siempre |
| Database | `--database-id <hex>` (o env `NOTION_DATABASE_ID` o `profile.targets.notion.database_id`); si no, `--page-parent-id` |
| Matriz | `--matrix <path>` (default: `08-render/capability-matrix.md`) |
| Dry-run | `--dry-run` (default off): no HTTP; escribe payloads a disco para inspección/testing |
| Pre-render diagrams | `--pre-render-diagrams` (default off): activa F70 cuando exista |
| API base override | `--api-base <url>` o env `NOTION_API_BASE` (testing con mock) |
| Renderer version | `--renderer-version <semver>` (default `0.1.0`) |
| Invocación | `python3 scripts/render/notion_api.py --ir <path> --profile <yaml> --out-dir <dir> --notion-token <token> [--database-id <hex>] [--dry-run]` |
| Dependencias | Python 3.9+ stdlib puro (`urllib.request`, `urllib.error`); parser YAML mínimo propio |
| Códigos de salida | 0 OK · 1 error fatal · 2 OK con advertencias (nota > 2000 bloques, retries) |
| Escritura | Atómica: `tempfile` + `Path.replace` (compartido con F38/F39/F54 vía `util/_io.py`) |
| Constantes inline | `BLOCKS_PER_REQUEST=100`, `RICH_TEXT_MAX_CHARS=2000`, `MAX_NESTING_DEPTH=2`, `INTER_REQUEST_DELAY=0.333s`, `RETRY_DELAYS=[5,30,120,600]`, `SEVERITY_TO_CALLOUT` (19), `PROPERTY_TYPE_MAP` (14) |
| Tabla de degradación | `references/08-render/contract.md §6` fila 2 (Notion API / Celdas combinadas) |
| Documentación | `references/08-render/contract.md` (F53) + `docs/adr/ADR-0010-notion-renderer.md` |
| Schema del reporte | `evals/render-contract-sample/schema/report.schema.json` |

### `render/appflowy.py` — F57 · Renderer AppFlowy

L4 renderer: genera archivos Markdown optimizados para la importación a AppFlowy (File → Import → Markdown). Implementa el contrato `render(ir, profile, matrix) → (artifacts, degradation_report)` definido en `references/08-render/contract.md` (F53). Cubre las 14 capacidades con 13 ✅ nativas (encabezados, tablas simples, código con lenguaje, callouts `> [!type]` con color, plegables `<details>`, ecuaciones LaTeX, Mermaid nativo, enlaces, propiedades en frontmatter, imágenes, etc.) + 1 ❌ (fila 4 §6 contract: celdas combinadas → tabla vacía + `<details>` con matriz original). Pre-render de diagramas opt-in con `--pre-render-diagrams` que activa F70 (`scripts/render/diagram_image.py`) si está disponible; sin F70, fallback a bloque ` ```mermaid ` nativo (con warning en el reporte).

| Aspecto | Valor |
|---|---|
| Entrada | `--ir <path>`; `--profile <path>`; `--out-dir <dir>` |
| Salida | `<out-dir>/render/appflowy/<note-id>.md` por nota (cabecera YAML §8 + cuerpo); `<out-dir>/render/appflowy/diagrams/<note-id>-N.svg` si pre-render activo; `<out-dir>/reports/render-degradation.{json,md}` siempre |
| Pre-render diagrams | `--pre-render-diagrams` (default off): invoca F70; sin F70, fallback a mermaid nativo + warning |
| Instrucciones de importación | `--include-import-instructions` (default off): escribe `render/appflowy/IMPORT_INSTRUCTIONS.md` |
| Renderer version | `--renderer-version <semver>` (default `0.1.0`) |
| Invocación | `python3 scripts/render/appflowy.py --ir evals/appflowy-render-sample/fixtures --profile <yaml> --out-dir /tmp/workdir [--pre-render-diagrams] [--include-import-instructions]` |
| Dependencias | Python 3.9+ stdlib puro (parser YAML mínimo propio para `targets.appflowy.*`; subprocess opcional para F70) |
| Códigos de salida | 0 OK · 1 error fatal · 2 OK con advertencias (wikilinks sin resolver, F70 ausente) |
| Escritura | Atómica: `tempfile` + `Path.replace` (compartido vía `util/_io.py`) |
| Constantes inline | `SEVERITY_TO_CALLOUT` (19 severidades → 6 tipos AppFlowy nativos: note/info/warning/danger/success/question), `LANG_MAP` (compatible AppFlowy importer) |
| Tabla de degradación | `references/08-render/contract.md §6` fila 4 (AppFlowy / Celdas combinadas) |
| Documentación | `references/08-render/contract.md` (F53) + docstring del script |
| Schema del reporte | `evals/render-contract-sample/schema/report.schema.json` |

### `render/markdown.py` — F58 · Renderer Markdown estándar (GFM)

L4 renderer: genera archivos GitHub-Flavored Markdown optimizados para visualización en GitHub. Implementa el contrato `render(ir, profile, matrix) → (artifacts, degradation_report)` definido en `references/08-render/contract.md` (F53). Cubre las 14 capacidades con 9 ✅ nativas (encabezados `#`/`##`/`###`, listas, checklists, tablas simples, code blocks, plegables `<details>`, ecuaciones LaTeX inline/bloque, imágenes con rutas relativas, Mermaid nativo) + 5 ❌ (filas 5/7/12/16/20 de contract §6: Celdas combinadas → `<details>` con matriz; Callouts → blockquote con emoji + CSS class `callout-<severity>`; Backlinks → sección `## Referenciado por` generada en build; Consultas dinámicas → tabla estática `## Consultas habituales`; Colores semánticos → emoji + CSS class `semantic-<token>`). Diagramas: bloque ` ```mermaid ` (GitHub nativo) + imagen SVG pre-renderizada como fallback cuando F70 está disponible. Rutas relativas (`[text](<note-id>.md)`) resuelven en la estructura generada (criterio 3).

| Aspecto | Valor |
|---|---|
| Entrada | `--ir <path>`; `--profile <path>`; `--out-dir <dir>` |
| Salida | `<out-dir>/render/markdown/<note-id>.md` por nota (cabecera YAML §8 + cuerpo + sección backlinks si hay); `<out-dir>/render/markdown/diagrams/<note-id>-N.svg` si pre-render activo; `<out-dir>/reports/render-degradation.{json,md}` siempre |
| Base URL | `--base-url <url>` (vacío por defecto): prefijo absoluto para wikilinks resueltos (e.g. `https://github.com/user/repo/blob/main/`); sin él, paths relativos `<note-id>.md` (criterio 3) |
| Backlinks | `--generate-backlinks` (default ON): inserta `## Referenciado por` al final (fila 7 §6) |
| Queries table | `--generate-queries-table` (default ON): inserta tabla estática `## Consultas habituales` para queries (fila 16 §6) |
| Pre-render diagrams | `--pre-render-diagrams` (default off): invoca F70 si existe; fallback a ` ```mermaid ` nativo |
| Renderer version | `--renderer-version <semver>` (default `0.1.0`) |
| Invocación | `python3 scripts/render/markdown.py --ir evals/markdown-render-sample/fixtures --profile <yaml> --out-dir /tmp/workdir [--base-url <url>] [--pre-render-diagrams]` |
| Dependencias | Python 3.9+ stdlib puro (parser YAML mínimo propio para `targets.markdown.*`; subprocess opcional para F70) |
| Códigos de salida | 0 OK · 1 error fatal · 2 OK con advertencias (wikilinks sin resolver) |
| Escritura | Atómica: `tempfile` + `Path.replace` (compartido vía `util/_io.py`) |
| Constantes inline | `SEVERITY_TO_EMOJI` (19 → 5 emoji principales), `SEMANTIC_TOKENS` (5), `LANG_MAP` (subset GFM), `BACKLINK_HEADING`, `QUERIES_HEADING` |
| Tabla de degradación | `references/08-render/contract.md §6` filas 5/7/12/16/20 (Markdown) |
| Documentación | `references/08-render/contract.md` (F53) + docstring del script |
| Schema del reporte | `evals/render-contract-sample/schema/report.schema.json` |

### `render/notion_md.py` — F56 · Renderer Notion por importación

L4 renderer: genera archivos Markdown optimizados para la importación a Notion vía UI (Settings → Import → Markdown). Implementa el contrato `render(ir, profile, matrix) → (artifacts, degradation_report)` definido en `references/08-render/contract.md` (F53). Cubre las 14 capacidades con 10 ✅ nativas (encabezados, tablas simples, código con lenguaje, listas, checklists, ecuaciones LaTeX, imágenes, Mermaid, links externos, dividers, quotes, steps, parameters) + 4 ❌ (filas 3, 11, 15, 19 de contract §6: Celdas combinadas → `<details>` con matriz; Callouts semánticos → blockquote con emoji prefijo; Propiedades → YAML frontmatter; Colores semánticos → emoji semántico). El reporte incluye campo `vs_notion_api` por entrada + sección `cross_target_diff` que documenta qué se degradó respecto a la ruta API (F55). Sin HTTP.

| Aspecto | Valor |
|---|---|---|
| Entrada | `--ir <path>`; `--profile <path>`; `--out-dir <dir>` |
| Salida | `<out-dir>/render/notion_md/<note-id>.md` por nota (cabecera YAML §8 + cuerpo); `<out-dir>/reports/render-degradation.{json,md}` |
| Instrucciones de importación | `--include-import-instructions` (default off): escribe `render/notion_md/IMPORT_INSTRUCTIONS.md` con el procedimiento UI |
| Renderer version | `--renderer-version <semver>` (default `0.1.0`) |
| Invocación | `python3 scripts/render/notion_md.py --ir evals/notion-md-render-sample/fixtures --profile <yaml> --out-dir /tmp/workdir [--include-import-instructions]` |
| Dependencias | Python 3.9+ stdlib puro (parser YAML mínimo propio para `targets.notion_md.*`) |
| Códigos de salida | 0 OK · 1 error fatal · 2 OK con advertencias (wikilinks sin resolver) |
| Escritura | Atómica: `tempfile` + `Path.replace` (compartido con F38/F39/F54/F55 vía `util/_io.py`) |
| Constantes inline | `SEVERITY_TO_EMOJI` (19 entradas), `LANG_MAP` (compatible Notion importer), `CROSS_TARGET_DIFF` (resumen vs notion_api) |
| Tabla de degradación | `references/08-render/contract.md §6` filas 3, 11, 15, 19 |
| Documentación | `references/08-render/contract.md` (F53) + docstring del script |
| Schema del reporte | `evals/render-contract-sample/schema/report.schema.json` (con extensión `cross_target_diff` propia) |

### `authoring/parse_notemark.py` — F48 · Parser NoteMark → IR

L3 autoría: parsea un archivo `.nm` (NoteMark) a un archivo `.note-ir.json` validado contra `schemas/note-ir.schema.json`. Implementa los 4 criterios de F48: gramática completa, errores con archivo:línea:causa, IR válido, round-trip estructural.

| Aspecto | Valor |
|---|---|
| Entrada | `--source <ruta>` (archivo `.nm`) |
| Salida | `<out>.note-ir.json` (IR con `schema_version`, `note_id`, `title`, `blocks`) |
| Schema | `--schema <ruta>` (default: `schemas/note-ir.schema.json`) |
| Modo | `--mode {parse,lint}` (parse = abortar al primer error; lint = recopilar todos) |
| Validación | Activa por defecto; `--no-validate` la salta |
| Round-trip | `--round-trip` (parsea → emite → re-parsea → compara estructuralmente) |
| Invocación | `python3 scripts/authoring/parse_notemark.py --source notes/foo.nm --out notes/foo.note-ir.json` |
| Dependencias | Python 3.9+ stdlib; jsonschema (recomendado); PyYAML (recomendado para frontmatter completo) |
| Comportamiento si falta jsonschema | Warning prominente; `--no-validate` permite continuar |
| Comportamiento si falta PyYAML | Parser YAML mínimo limitado a las 18 propiedades de F47; warning por clave no reconocida |
| Códigos de salida | 0 OK · 1 error de sintaxis / validación / round-trip · 2 uso (paths faltantes) |
| Escritura | Atómica: `_io.atomic_write_json` compartido con `util/` |
| Documentación | `references/04-authoring/notemark.ebnf` (F12) + `references/04-authoring/ir-spec.md` (F14) |
| Limitaciones del round-trip | Lossy: footnote definitions al final se omiten; filas de tabla se pierden (schema no las almacena); paragraphs consecutivos se colapsan; layer marks como nodos text se pierden. Cobertura estructural ≥ 70% se considera OK. |

### `validate/validate_ir.py` — F49 · Validador de IR

L3 validación: valida archivos `.note-ir.json` contra el schema JSON + reglas semánticas (allowed_children, capability, source_ref resoluble) + avisos de calidad estructural (W1..W11).

| Aspecto | Valor |
|---|---|
| Entrada | `--ir <ruta>` (repetible; valida múltiples IRs) |
| SDM | `--sdm <ruta>` (obligatorio; archivo sdm.json con block_ids válidos) |
| Saltar SDM | `--skip-sdm` (omite verificación de source_ref.block_id contra SDM) |
| Modo | `--strict` (warnings también exit 1) |
| Inspect | `--inspect` (resumen estructural sin validar errores) |
| Salida | Texto (default) o `--json` |
| Invocación | `python3 scripts/validate/validate_ir.py --ir notes/foo.note-ir.json --sdm .notes-work/<hash>/sdm.json` |
| Dependencias | Python 3.9+ stdlib; jsonschema (recomendado para validación contra `note-ir.schema.json`) |
| Comportamiento sin jsonschema | Solo valida reglas embebidas (catálogo de nodos, capabilities, allowed_children, source_refs); warning "schema no validado" |
| Severidades | `error` (nodo desconocido, hijo no permitido, source_ref colgante, capability ausente, source_ref malformado) → exit 1; `warning` (calidad estructural: tabla 1 fila, lista 1 ítem, sección vacía, paragraph sin texto, code sin texto, admonition sin contenido, text vacío, source_refs duplicados, capability fuera del catálogo) → exit 0 por defecto |
| Códigos de salida | 0 OK · 1 errores · 2 uso (paths faltantes) |
| Documentación | `references/04-authoring/ir-spec.md` (F14) + `schemas/note-ir.schema.json` |

### `authoring/transform.py` — F50 · Transformaciones sobre IR

L3 autoría: aplica 4 transformaciones sobre archivos `.note-ir.json`:
- `split`: divide una nota en 2+ (heading explícito o threshold automático).
- `merge`: fusiona 2+ IRs en uno (consolidación).
- `layer`: cambia el layer (`l1`/`l2`/`l3`) de un nodo o top-level.
- `dedup`: elimina bloques duplicados (hash del subárbol).

| Aspecto | Valor |
|---|---|
| Split — modo A | `--ir X --at-heading "## Y" --at-heading "## Z"` (cortes explícitos) |
| Split — modo B | `--ir X --max-blocks N` (corte automático en heading más cercano) |
| Merge | `--irs A B --output AB` (≥ 2 archivos) |
| Layer | `--ir X --node-path "blocks[2]" --layer l1` (vacío = top-level) |
| Dedup | `--ir X` (hash estable del subárbol; preserva source_refs) |
| Reescritura | `--irs-glob "*.note-ir.json"` (re-escribe `[[note:X]]` y `related` en otras IRs) |
| Conservación | Unión de `source_refs` siempre preservada (criterio #1) |
| Bidireccional | `split`/`merge` añaden back-link en cada hija al padre (criterio #2) |
| Ledger | `--workdir` actualiza `knowledge/ledger.json` con unidades `merged` (criterio #3) |
| Dry run | `--dry-run` simula sin escribir |
| Sin ledger | `--no-update-ledger` salta la actualización |
| Invocación | `python3 scripts/authoring/transform.py split --ir X --at-heading "## Y" --workdir <dir>` |
| Dependencias | Python 3.9+ stdlib; `util/ledger.py` (F38) para integración con ledger |
| Códigos de salida | 0 OK · 1 error · 2 uso |
| Documentación | `references/04-authoring/ir-spec.md` (F14) + `references/03-knowledge/ledger.md` (F15) |
| Garantía INV-08 | 100% de `must-keep` con estado terminal preservado (split/merge → `merged`; dedup/layer → contenido intacto) |

### `util/trace.py` — F52 · Trazabilidad bidireccional IR ↔ SDM

L1/L2/L3 autoría: provee trazabilidad bidireccional entre nodos IR y bloques
SDM, detecta huérfanos (fácticos sin `source_refs` y derivados sin marca) y
ejecuta auditorías de un workdir completo.

| Aspecto | Valor |
|---|---|
| Forward | `node --ir X --node-path "blocks[3]" --sdm Y` → muestra el bloque SDM del nodo |
| Backward | `block --sdm Y --block-id abc... --workdir DIR` → muestra en qué notas IR aparece |
| Huérfanos tipo A | `orphans --ir X` (o `--workdir DIR`) → nodos fácticos sin `source_refs` |
| Huérfanos tipo B | `orphans --ir X` → párrafos con marcadores de derivación sin `attrs.derived` |
| Auditoría | `audit --workdir DIR [--sdm SDM]` → ejecuta node + block + orphans + reporta blocks indexados y huérfanos |
| Output | Texto (default) o `--json` |
| Índice | Bidireccional en memoria: O(N) construcción, O(1) por lookup (criterio #1) |
| Marcadores de derivación | Lista cerrada: "podría", "tal vez", "es probable", "presumiblemente", "quizás", "posiblemente", "analogía", "análogo" |
| Invocación | `python3 scripts/util/trace.py audit --workdir .notes-work/abc/` |
| Dependencias | Python 3.9+ stdlib |
| Códigos de salida | 0 OK (sin huérfanos tipo A) · 1 huérfanos tipo A o errores · 2 uso |
| Documentación | `references/03-knowledge/ledger.md` (F15) + `schemas/sdm.schema.json` (F13) + `schemas/note-ir.schema.json` (F14) |
### `render/html_pdf.py` — F59 · Renderer HTML y PDF

L4 renderer: genera HTML5 autocontenido (CSS inline, sin recursos externos) con TOC lateral, SVG embebido para diagramas, y opcionalmente PDF via `weasyprint`. Implementa el contrato `render(ir, profile, matrix) → (artifacts, degradation_report)` definido en `references/08-render/contract.md` (F53). Cubre las 14 capacidades con 12 ✅ nativas (encabezados con id+anchor, listas, checklists, tablas con rowspan/colspan nativos, code blocks, plegables `<details>`, ecuaciones `<span class="math">`, imágenes con rutas relativas, Mermaid pre-renderizado a SVG o `<pre class="mermaid">` fallback, callouts `<aside class="callout-*">` con 8 colores semánticos, quotes `<blockquote><cite>` con cita preservada) + 2 ❌ (filas 8/17 de contract §6: Backlinks → `<aside class="backlinks">`; Consultas dinámicas → `<section class="queries">`). Self-contained: sin `<link rel="stylesheet" href="http">`, sin `<script src="http">`, sin `@import url(http)`, sin `<img src="http">` (criterio 1).

| Aspecto | Valor |
|---|---|
| Entrada | `--ir <path>`; `--profile <path>`; `--out-dir <dir>` |
| Salida | `<out-dir>/render/html_pdf/<note-id>.html` por nota (HTML5 completo con `<style>` inline); `<out-dir>/render/html_pdf/diagrams/<note-id>-N.svg` si pre-render; `<out-dir>/render/html_pdf/<note-id>.pdf` si weasyprint disponible; `<out-dir>/reports/render-degradation.{json,md}` siempre |
| Plantilla CSS | `references/08-render/html_pdf.template.css` (362 líneas, self-contained) |
| PDF | weasyprint opcional (soft-dep). Sin weasyprint: HTML + warning en reporte + exit WARN. `--no-pdf` salta el intento. `--print-instructions` escribe `PRINT_INSTRUCTIONS.md` |
| Print CSS | `@media print` con `page-break-inside: avoid` para `table, pre, code, figure, aside, blockquote, dl, details` (criterio 2). `@page { @top-left { source; } @bottom-right { counter(page); } }` para weasyprint |
| Renderer version | `--renderer-version <semver>` (default `0.1.0`) |
| Invocación | `python3 scripts/render/html_pdf.py --ir <path> --profile <yaml> --out-dir <dir> [--no-pdf] [--print-instructions]` |
| Dependencias | Python 3.9+ stdlib puro; `weasyprint` soft-dep opcional |
| Códigos de salida | 0 OK · 1 error fatal · 2 OK con advertencias (PDF skipped, etc.) |
| Escritura | Atómica: `tempfile` + `Path.replace` (compartido vía `util/_io.py`) |
| Constantes inline | `SEVERITY_TO_CSS_CLASS` (19 → 8 clases CSS), `SEVERITY_TO_EMOJI` (19), `LANG_MAP` (compatible con highlight.js) |
| Tabla de degradación | `references/08-render/contract.md §6` filas 8/17 (HTML/PDF) |
| Documentación | `references/08-render/contract.md` (F53) + `references/08-render/html_pdf.template.css` (comentarios inline) |
| Schema del reporte | `evals/render-contract-sample/schema/report.schema.json` |

### `render/flashcards.py` — F60 · Renderer de repaso espaciado

L4 renderer: genera tarjetas de repaso desde nodos IR atómicos. Implementa el contrato `render(ir, profile, matrix) → (artifacts, degradation_report)` definido en `references/08-render/contract.md` (F53). Salida en dos formatos: Obsidian (Spaced Repetition plugin) con líneas `Pregunta:: Respuesta` y CSV para Anki. Cubre 7 ✅ nativas + 6 ❌ (filas 6/9/10/13/14/18 de contract §6). Reglas duras: **D1** solo `question` o nodos con `is_atomic_card=true`; **D2** una tarjeta = un hecho (heurística de cláusulas; descarta si >2); **D3** trazabilidad con `note_id` en frontmatter/tags; **D4** prohibido generar desde prosa narrativa (paragraph narrativo se descarta).

| Aspecto | Valor |
|---|---|
| Entrada | `--ir <path>`; `--profile <path>`; `--out-dir <dir>` |
| Salida | `<out-dir>/render/flashcards/<note-id>.md` por nota con tarjetas (formato Spaced Repetition plugin); `<out-dir>/render/flashcards/anki.csv` agregando todas las notas; `<out-dir>/reports/render-degradation.{json,md}` |
| Max clauses | `--max-clauses N` (default 2; descarta si >) — criterio 2 enforcement |
| Max words | `--max-words N` (default 25; warning si >) |
| Renderer version | `--renderer-version <semver>` (default `0.1.0`) |
| Invocación | `python3 scripts/render/flashcards.py --ir evals/flashcards-render-sample/fixtures --profile <yaml> --out-dir <dir>` |
| Dependencias | Python 3.9+ stdlib puro (csv stdlib para RFC 4180 escape) |
| Códigos de salida | 0 OK · 1 error fatal · 2 OK con advertencias (compound-fact descartados) |
| Escritura | Atómica: `tempfile` + `Path.replace` (compartido vía `util/_io.py`) |
| Constantes inline | `ATOMIC_NODE_KINDS` (5), `NO_OP_CAPABILITIES` (5 filas), `CLAUSE_SEPARATORS` (regex), `REASON_PROSE`, `REASON_COMPOUND` |
| Tabla de degradación | `references/08-render/contract.md §6` filas 6/9/10/13/14/18 (Flashcards) |
| Documentación | `references/08-render/contract.md` (F53) + docstring del script |
| Schema del reporte | `evals/render-contract-sample/schema/report.schema.json` |

