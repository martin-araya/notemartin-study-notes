# `scripts/`

Ejecutables invocables por el agente. **No se leen en contexto**; se invocan por su comando con la entrada y salida declaradas. El catálogo legible está en `scripts/README.md` (producido por F117).

## Qué vivirá aquí

| Subcarpeta | Rol | Fases |
|---|---|---|
| `ingest/` | L0: triaje, OCR, layout, regiones, tablas, fórmulas, código, post-OCR, formatos no PDF | F17-F29, F33 |
| `validate/` | Validadores de SDM, IR, NoteMark, Mermaid, completitud, equivalencia cross-target, contraste de tokens, densidad de notas | F30, F43, F49, F63, F67, F72, F76 |
| `evals/visual/` (no es `scripts/` sino `evals/visual/`) | Verificación visual multi-destino (F77): 12 artefactos reales + checklist + defects.md + visual_inspect.py + run_eval.py | F77 |
| `authoring/` | Parser NoteMark → IR (F48, `parse_notemark.py`); transformaciones de IR (F50) | F48, F50 |
| `render/` | Renderers a cada destino + pre-render de diagramas y figuras + generador CSS de tokens + helper de cabecera F75 | F54-F60, F68, F68, F74, F75 |
| `util/` | Caché, visor, ledger, grafo de conceptos, trazabilidad, tokens, mapeo de estilo | F36, F38, F39, F52, F72, F73 |
| `pipeline/` | Meta-orquestadores sobre las 5 capas (modo obra completa, bucle por chunks, consolidación, índice de obra) | F106, F107, F109, F110 |
| `dedup/` | Detector de duplicados (canónico/alias/similarity) + orquestador de apply sobre F50 | F108 |
| (consolidation in `pipeline/`) | Orquestador de 5 pases de consolidación idempotentes | F109 |
| (book_index in `pipeline/`) | Generador del índice de obra (10 secciones canónicas) | F110 |
| `diff/` | Orquestador de actualización incremental (diff SDM + obsoletos + version-delta + republish selectiva) | F111 |
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
| Pre-render diagrams | `--pre-render-diagrams` (default off): activa F68 cuando exista |
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

L4 renderer: genera archivos Markdown optimizados para la importación a AppFlowy (File → Import → Markdown). Implementa el contrato `render(ir, profile, matrix) → (artifacts, degradation_report)` definido en `references/08-render/contract.md` (F53). Cubre las 14 capacidades con 13 ✅ nativas (encabezados, tablas simples, código con lenguaje, callouts `> [!type]` con color, plegables `<details>`, ecuaciones LaTeX, Mermaid nativo, enlaces, propiedades en frontmatter, imágenes, etc.) + 1 ❌ (fila 4 §6 contract: celdas combinadas → tabla vacía + `<details>` con matriz original). Pre-render de diagramas opt-in con `--pre-render-diagrams` que activa F68 (`scripts/render/diagram_image.py`) si está disponible; sin F68, fallback a bloque ` ```mermaid ` nativo (con warning en el reporte).

| Aspecto | Valor |
|---|---|
| Entrada | `--ir <path>`; `--profile <path>`; `--out-dir <dir>` |
| Salida | `<out-dir>/render/appflowy/<note-id>.md` por nota (cabecera YAML §8 + cuerpo); `<out-dir>/render/appflowy/diagrams/<note-id>-N.svg` si pre-render activo; `<out-dir>/reports/render-degradation.{json,md}` siempre |
| Pre-render diagrams | `--pre-render-diagrams` (default off): invoca F68; sin F68, fallback a mermaid nativo + warning |
| Instrucciones de importación | `--include-import-instructions` (default off): escribe `render/appflowy/IMPORT_INSTRUCTIONS.md` |
| Renderer version | `--renderer-version <semver>` (default `0.1.0`) |
| Invocación | `python3 scripts/render/appflowy.py --ir evals/appflowy-render-sample/fixtures --profile <yaml> --out-dir /tmp/workdir [--pre-render-diagrams] [--include-import-instructions]` |
| Dependencias | Python 3.9+ stdlib puro (parser YAML mínimo propio para `targets.appflowy.*`; subprocess opcional para F68) |
| Códigos de salida | 0 OK · 1 error fatal · 2 OK con advertencias (wikilinks sin resolver, F68 ausente) |
| Escritura | Atómica: `tempfile` + `Path.replace` (compartido vía `util/_io.py`) |
| Constantes inline | `SEVERITY_TO_CALLOUT` (19 severidades → 6 tipos AppFlowy nativos: note/info/warning/danger/success/question), `LANG_MAP` (compatible AppFlowy importer) |
| Tabla de degradación | `references/08-render/contract.md §6` fila 4 (AppFlowy / Celdas combinadas) |
| Documentación | `references/08-render/contract.md` (F53) + docstring del script |
| Schema del reporte | `evals/render-contract-sample/schema/report.schema.json` |

### `render/markdown.py` — F58 · Renderer Markdown estándar (GFM)

L4 renderer: genera archivos GitHub-Flavored Markdown optimizados para visualización en GitHub. Implementa el contrato `render(ir, profile, matrix) → (artifacts, degradation_report)` definido en `references/08-render/contract.md` (F53). Cubre las 14 capacidades con 9 ✅ nativas (encabezados `#`/`##`/`###`, listas, checklists, tablas simples, code blocks, plegables `<details>`, ecuaciones LaTeX inline/bloque, imágenes con rutas relativas, Mermaid nativo) + 5 ❌ (filas 5/7/12/16/20 de contract §6: Celdas combinadas → `<details>` con matriz; Callouts → blockquote con emoji + CSS class `callout-<severity>`; Backlinks → sección `## Referenciado por` generada en build; Consultas dinámicas → tabla estática `## Consultas habituales`; Colores semánticos → emoji + CSS class `semantic-<token>`). Diagramas: bloque ` ```mermaid ` (GitHub nativo) + imagen SVG pre-renderizada como fallback cuando F68 está disponible. Rutas relativas (`[text](<note-id>.md)`) resuelven en la estructura generada (criterio 3).

| Aspecto | Valor |
|---|---|
| Entrada | `--ir <path>`; `--profile <path>`; `--out-dir <dir>` |
| Salida | `<out-dir>/render/markdown/<note-id>.md` por nota (cabecera YAML §8 + cuerpo + sección backlinks si hay); `<out-dir>/render/markdown/diagrams/<note-id>-N.svg` si pre-render activo; `<out-dir>/reports/render-degradation.{json,md}` siempre |
| Base URL | `--base-url <url>` (vacío por defecto): prefijo absoluto para wikilinks resueltos (e.g. `https://github.com/user/repo/blob/main/`); sin él, paths relativos `<note-id>.md` (criterio 3) |
| Backlinks | `--generate-backlinks` (default ON): inserta `## Referenciado por` al final (fila 7 §6) |
| Queries table | `--generate-queries-table` (default ON): inserta tabla estática `## Consultas habituales` para queries (fila 16 §6) |
| Pre-render diagrams | `--pre-render-diagrams` (default off): invoca F68 si existe; fallback a ` ```mermaid ` nativo |
| Renderer version | `--renderer-version <semver>` (default `0.1.0`) |
| Invocación | `python3 scripts/render/markdown.py --ir evals/markdown-render-sample/fixtures --profile <yaml> --out-dir /tmp/workdir [--base-url <url>] [--pre-render-diagrams]` |
| Dependencias | Python 3.9+ stdlib puro (parser YAML mínimo propio para `targets.markdown.*`; subprocess opcional para F68) |
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

### `render/linking.py` — F61 · Enlaces por destino

CLI de orquestación de enlaces: invoca los renderers (F54-F60) y produce
los outputs derivados del grafo de links (`reports/link_debt.json`,
`reports/linking-report.{json,md}`). Módulo compartido `_linking.py` con
API centralizada (`LinkTarget`, `LinkReport`, `LinkGraph`, `resolve_links`,
`build_backlinks_section_md`, `build_backlinks_aside_html`,
`aggregate_link_debt`). El spec normativo está en
`references/08-render/linking.md`.

| Aspecto | Valor |
|---|---|
| Entrada | `--ir <path>`; `--out-dir <dir>`; `--profile <yaml>`; `--renderers <csv>` (default todos) |
| Salida | `reports/link_debt.json` (deuda por destino); `reports/linking-report.{json,md}`; invoca renderers y recolecta paths |
| Pasadas | `--pass1-only` (invoca renderers); `--pass2-only` (análisis); default ambas |
| Dependencias | Python 3.9+ stdlib puro (subprocess para invocar renderers) |
| Códigos de salida | 0 OK · 1 error fatal · 2 OK con deuda residual |
| Documentación | `references/08-render/linking.md` (F61) + docstring |

### `publish/publishing.py` — F62 · Publicación idempotente

CLI de publicación que orquesta los renderers con un manifest de IDs remotos.
Implementa los 3 criterios: republicar N notas actualiza N, no crea N (post-primer-publish);
páginas editadas a mano bloqueadas sin `--confirm-overwrite`; publicación parcial solo toca lo
cambiado. 4 sub-comandos: `plan`, `publish`, `status`, `mark-edited`. Módulo compartido
`_manifest.py` con dataclasses `PublishEntry` y `Manifest`.

| Aspecto | Valor |
|---|---|
| Entrada | `--ir <path>`; `--out-dir <dir>`; `--destinations <csv>`; `--confirm-overwrite`; `--force-manual-keep-comments`; `--notion-token <token>` |
| Salida | `reports/publish-report.{json,md}` con summary {created, updated, skipped, blocked, errors} |
| Manifest | `<out-dir>/.publish/manifest.json` con `{note_id × destination → remote_id, remote_hash, ir_sha256, last_published_at, edited_by_hand, user_content}`; backup automático `manifest.json.bak` |
| Detección manual | `sha256(remote_file) != manifest_entry.remote_hash` → `edited_by_hand=true` |
| Códigos de salida | 0 OK · 1 fatal · 2 OK con bloqueos |
| Dependencias | Python 3.9+ stdlib puro |

### `validate/cross_target.py` — F63 · Equivalencia entre destinos

Script de validación que compara el contenido textual de cada IR contra el
artifact renderizado por cada destino y verifica que toda unidad del IR
aparezca en el artifact (criterio 1) o esté cubierta por una degradación
declarada (criterio 1), con cero pérdidas reales (criterio 2). Implementa
los 3 criterios del roadmap. Stdlib puro.

| Aspecto | Valor |
|---|---|
| Entrada | `--ir <path>`; `--out-dir <dir>`; `--destinations <csv>` (default: todos) |
| Salida | `<out-dir>/reports/cross-target-report.{json,md}` con summary {total_units, units_present, units_justified, units_lost, notes, destinations} |
| Matching | Canonical text extraction del IR + normalized substring match contra artifact + degradation lookup |
| Códigos de salida | 0 OK (sin pérdidas reales) · 1 FAIL (al menos 1 pérdida real) · 2 uso incorrecto |
| Dependencias | Python 3.9+ stdlib puro |

### `render/migrate.py` — F64 · Re-render y migración

CLI para migrar entre destinos sin volver a la fuente y reconstruir IR
desde artifacts existentes. 3 sub-comandos:
  - `re-render`: lee IRs persistidos e invoca el renderer del destino nuevo.
  - `reverse-import`: parsea un artifact (md/html) y reconstruye un IR
    estructural (jerarquía de headings, listas, admonitions, code, wikilinks).
  - `diff-capabilities`: muestra gains/losses entre dos destinos sin migrar.

| Aspecto | Valor |
|---|---|
| Entrada | `--ir-source <path>`; `--out-dir <dir>`; `--from <dest>`; `--to <dest>` |
| Salida | `reports/migration-report.json` con summary {notes_total, notes_created, notes_updated, notes_errors, capabilities_gained, capabilities_lost} + capability_diff {gains, losses}; `migration-report.md` legible |
| Reverse input | `--input <file>`; `--output-ir <path>`; `--format md\|html`; confidence high\|medium\|low |
| Capacidad diff | Basado en CAPABILITY_SUPPORT (subset F8): 7 destinos × 7 capabilities |
| Códigos de salida | 0 OK · 1 fatal · 2 warnings (migration con degradaciones) |
| Dependencias | Python 3.9+ stdlib puro |


### `validate/mermaid.py` — F67 · Validador de diagramas Mermaid

CLI que extrae bloques `:::diagram` de archivos NoteMark (`.nm`/`.md`) y los
valida contra el catálogo portable de F66 (`mermaid-portable.md`) y las
reglas de legibilidad de F65 (`diagram-catalog.md` §6). Parser ad-hoc para
los 9 tipos portables (WP-1..WP-9) sin dependencias externas. Cubre los 3
criterios de la Fase 67: detecta el 100 % de los 20 diagramas rotos a
propósito, cero falsos positivos sobre los diagramas válidos del repo,
y reporta violaciones de portabilidad además de errores de sintaxis.

| Aspecto | Valor |
|---|---|
| Entrada | `--source <path>` (archivo único) o `--glob <pattern>` (múltiples) |
| Salida | `--out-dir <dir>` escribe `validate-report.{json,md}`; sin `--out-dir` imprime a stdout (Markdown por defecto o JSON con `--json`) |
| Reglas sintaxis | S-01..S-08: tipo desconocido, dirección inválida, corchetes desbalanceados, participante inválido, mensaje sin `:`, `[*]` ausente, cardinalidad er inválida, gantt sin dateFormat |
| Reglas portabilidad | P-01..P-06: etiqueta sin comillas (R-MP-01), ID Unicode (R-MP-02), `style X fill:#hex` (R-MP-04), `click`/`linkStyle` (R-MP-06), `init` con theme (R-MP-06), HTML inline complejo |
| Reglas legibilidad | L-01..L-06: >15 nodos, gantt >25 hitos, jerarquía >25 profundidad ≤4, etiqueta >40/60 chars, subgraphs anidados >2 niveles, `:::diagram` sin `alt=` |
| Severidades | `error` (criterios duros) · `warning` (recomendaciones) · `info` (informativo: ej. gantt con 16-25 hitos) |
| Thresholds | `--max-nodes` (default 15) · `--max-label-len` (default 40) · `--severity` mínimo (default info) · `--fail-on` (default error) |
| Filtro por tipo | `--include-types WP-1,WP-2,...` (default: todos) |
| Reporte | JSON con `schema_version: 1.0.0`, `file`, `block_index`, `directive_src`, `directive_alt`, `diagram_type`, `violations[]` (rule_id, severity, node_id, line, column, message, fix_hint) |
| Códigos de salida | 0 OK · 1 FAIL (≥1 violación ≥ `--fail-on`) · 2 uso incorrecto |
| Escritura | Atómica vía `util/_io.py:atomic_write_json` |
| Constantes inline | `PORTABLE_TYPES` (11), `SEVERITY_ORDER`, `EXIT_*`, `RULES` (20 reglas) |
| Tabla de degradación | `references/07-visual/mermaid-portable.md §6` (reglas R-MP-01..R-MP-06) y `diagram-catalog.md §6` (regla R-D-02 sobre 15 nodos) |
| Documentación | `references/07-visual/diagram-catalog.md` (F65) + `references/07-visual/mermaid-portable.md` (F66) + docstring del script |
| Dependencias | Python 3.9+ stdlib puro |

### `render/diagram_image.py` — F68 · Pre-renderizado de diagramas

CLI que extrae bloques `:::diagram` de archivos NoteMark (`.nm`/`.md`) y los
pre-renderiza a SVG (y opcionalmente PNG) en tema claro y oscuro usando el
binario `mmdc` (`@mermaid-js/mermaid-cli`). Cuando `mmdc` no está disponible,
degrada a `native_mermaid` (criterio D-01): el bloque ```mermaid ``` queda
tal cual y el código fuente plegable se incluye en el manifest.

Cubre los 3 criterios de F68: todo diagrama tiene versión imagen disponible
(criterio 1); el mismo código produce el mismo archivo (criterio 2, hash
determinista + caché por hash); el código fuente plegable (`source_code`)
acompaña siempre a la imagen en el `manifest.json` (criterio 3). Stdlib puro.

| Aspecto | Valor |
|---|---|
| Entrada | `--source <path>` (archivo único) o `--glob <pattern>` (múltiples) |
| Salida | `<out-dir>/manifest-<stem>.{json,md}` (uno por archivo × tema) + `<out-dir>/render-degradation.{json,md}`; `<out-dir>/diagrams/<note-id>-<block_idx>-<theme>.{svg,png}` |
| Caché | `<cache-dir>/<hash>-<theme>.json` (index) + archivos `<hash>.{svg,png}`; `--force` ignora caché, `--cache-clear` la vacía |
| Hash determinista | `sha256(diagram_code \|\| theme \|\| format \|\| ir_sha256)` — incluye `ir_sha256` para invalidar caché cuando cambia el IR aunque el código del diagrama sea idéntico |
| Tema | `light` (default), `dark`, `both` (genera `*-light.svg` + `*-dark.svg`) |
| Formato | `svg` (default), `png`, `both` |
| mmdc invocation | `mmdc --input X.mmd --output Y.svg --configFile config.json --puppeteerConfig '{...}' --quiet`; Puppeteer config: `{"args": ["--no-sandbox", "--disable-setuid-sandbox"]}` |
| Fallback D-01 | Cuando `mmdc` no está disponible: `fallback_used: "native_mermaid"`; manifest incluye `source_code` (criterio 3) y `errors: []`; renderer L4 embebe ```mermaid ``` nativo |
| API importable | `render_block(block, out_dir, cache, mmdc_path, mmdc_version, theme, format_, ir_sha256, force, no_fallback, max_width, max_height, timeout)` — usada por appflowy/markdown/html_pdf vía `--pre-render-diagrams` |
| Códigos de salida | 0 OK · 1 degradación parcial · 2 fatal (mmdc no disponible + `--no-fallback` o paths faltantes) |
| Escritura | Atómica vía `util/_io.py:atomic_write_json` |
| Tabla de degradación | `references/08-render/capability-matrix.md` fila 8 (Mermaid) — Notion API / AppFlowy / HTML-PDF / Flashcards pre-renderizan via F68; Obsidian / Notion import / Markdown estándar usan nativo |
| Documentación | `references/08-render/capability-matrix.md` (F8) + `references/07-visual/diagram-catalog.md` (F65) + docstring del script |
| Dependencias | Python 3.9+ stdlib puro + `mmdc` opcional (subprocess); Puppeteer + Chrome implícitos cuando `mmdc` está disponible |

### `render/make_figure.py` — F70 · Figuras de datos

CLI que renderiza figuras de datos en SVG vectorial a partir de un JSON
spec. Cubre los 3 criterios de F70: las 6 figuras (bar, line, heatmap,
confusion_matrix, distribution, before_after) se leen bien en tema claro
y oscuro (ejes grises neutros, paleta Okabe-Ito, fondo configurable); la
paleta pasa verificación de daltonismo con ΔE CIEL76 ≥ 20; toda serie
tiene `source_refs` no vacío (regla F70-SR-01, exit 1 si falta).

Stdlib puro. Genera alt text automáticamente; exige reading_phrase no vacío.

| Aspecto | Valor |
|---|---|
| Entrada | `--input <spec.json>` (archivo único) o `--input-dir <dir>` (varios specs) |
| Salida | `<out-dir>/<slug>.svg` + `<out-dir>/<slug>.manifest.json` + `<out-dir>/render-degradation.{json,md}` |
| Tipos | `bar`, `line`, `heatmap`, `confusion_matrix`, `distribution`, `before_after` |
| Paleta | Okabe-Ito (8 colores) desde `assets/tokens.json` → `series.okabe-ito-*` (F72 ratifica el seed F70); inversión `okabe-ito-black` light↔dark modelada en el JSON; verificada con ΔE CIEL76 ≥ 20 |
| Ejes neutros | Resueltos desde `assets/tokens.json` → `series.axisLight` / `series.axisDark` (F72) |
| Source refs | Validación obligatoria por serie; `--allow-missing-refs` para modo draft |
| Alt text | Auto-generado por tipo; sobrescribible vía spec |
| Reading phrase | Obligatorio no vacío (≤ 280 chars recomendado) |
| Manifest | `schema_version: 1.0.0`; `ir_sha256`; `palette_colorblind_safe`; `palette_min_delta_e`; `source_refs_total` |
| Códigos de salida | 0 OK · 1 con violaciones ≥ `--fail-on` · 2 fatal |
| Escritura | Atómica vía `util/_io.py:atomic_write_json/text` |
| Tabla de degradación | `references/08-render/contract.md` §6 — figuras como capacidad; obsidian/no, notion_api/svg-inline, notion_md/svg-embed, appflowy/svg-inline, html_pdf/svg-inline, markdown/svg-embed, flashcards/png-raster |
| Documentación | `references/07-visual/tokens.md` (F72 — tokens.json + loader + verificador WCAG) + docstring del script |
| Dependencias | Python 3.9+ stdlib puro (Pillow opcional para `--format png\|both`) |

### `util/tokens.py` — F72

Loader de design tokens. Lee `assets/tokens.json` (la fuente única de color, tipografía, espaciado, radios y pesos per `INV-14`), valida `$version` semver y expone helpers de resolución por modo (`light` | `dark`). Consumido por `scripts/render/make_figure.py` (paleta Okabe-Ito + ejes neutros) y por `scripts/validate/contrast_check.py` (verificación WCAG). Migración retroactiva de `references/08-render/html_pdf.template.css` queda para F74 (wiring explícito en `references/07-visual/tokens.md` §3).

| Aspecto | Detalle |
|---|---|
| Propósito | Resolver cualquier token semántico, neutral o de serie a su hex concreto, eliminando literales de color del código (INV-14) |
| API | `load_tokens(path=None)` → dict · `resolve_token(t, category, name, mode="light", field=None)` → hex · `resolve_series(t, name, mode="light")` → hex (maneja inversión de `okabe-ito-black` light↔dark) · `warn_if_unsupported_major(version, supported_major=1)` |
| CLI | `python -m scripts.util.tokens --dump` (imprime JSON completo) · `--resolve CATEGORY NAME [MODE] [FIELD]` (imprime hex; p.ej. `semantic info light fgOnBg` → `#0D47A1`) |
| Source-of-truth | `skill/notemartin-study-notes/assets/tokens.json` (`$version: 1.0.0`) |
| Búsqueda del archivo | Explícita (`--tokens <path>`) → `<cwd>/skill/notemartin-study-notes/assets/tokens.json` → `<repo>/skill/notemartin-study-notes/assets/tokens.json` (vía `parents[2]`) |
| Validación | `$version` debe ser semver `X.Y.Z` con `major ≤ 1`; claves top-level obligatorias: `typography`, `spacing`, `radii`, `_neutral`, `semantic`, `series` |
| Hex regex | `^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$` (3, 6 u 8 dígitos) |
| Semver | major bump = rename/remove; minor = add; patch = hex adjustment (re-auditar con `contrast_check.py`) |
| Errores | `FileNotFoundError` si no hay tokens.json en ninguna ruta · `ValueError` si JSON inválido o `$version` no semver · `KeyError` si ruta no existe |
| Códigos CLI | 0 OK · 1 ruta no resuelta |
| Dependencias | Python 3.9+ stdlib puro (json, re, pathlib, argparse) |
| Wirings | F70 `make_figure.py` (consume Okabe-Ito + ejes), F72 `contrast_check.py` (verifica), F73/F74 (consumidores futuros) |

### `validate/contrast_check.py` — F72

Verificador de contraste WCAG 2.1 sobre `assets/tokens.json`. Calcula el ratio entre `fgOnBg` y `bg` para los 9 tokens semánticos en cada modo (light + dark = 18 pares) usando la fórmula WCAG SC 1.4.3 (linealización sRGB + luminancia relativa). Pensado para ejecutarse en CI y bloquear el commit si algún par cae por debajo del mínimo AA.

| Aspecto | Detalle |
|---|---|
| Propósito | Garantizar `INV-14` no solo estructural (sin literales) sino funcional (contraste suficiente en ambos temas) |
| Fórmula | `L = 0.2126 R + 0.7152 G + 0.0722 B` (canal linealizado con `c/12.92` si `c ≤ 0.03928`, si no `((c+0.055)/1.055)**2.4`); `ratio = (L_lighter+0.05)/(L_darker+0.05)` |
| Ratios | AA = 4.5:1 (mínimo, default `--min-ratio`); AAA = 7:0 (referencia en la tabla) |
| CLI | `python scripts/validate/contrast_check.py --tokens <path> --min-ratio 4.5 --mode both` |
| Salida | Markdown (default) con tabla 18 filas + veredicto PASS/FAIL; o JSON (`--json`) con `tokens_path`, `min_ratio`, `aa_ratio`, `aaa_ratio`, `pairs[]`, `fails[]` |
| Exit codes | 0 todos ≥ min · 1 algún par falla · 2 archivo no encontrado / JSON inválido / sin `semantic` |
| Resultado esperado | 18/18 PASS en `assets/tokens.json` actual; tabla de referencia en `references/07-visual/tokens.md` §5 |
| Dependencias | Python 3.9+ stdlib puro (json, argparse, pathlib) |
| Wirings | Cierra criterio 3 de F72; documentado en `references/07-visual/tokens.md` §4 y §10 |

### `util/style_mapping.py` — F73

Tabla canónica `severidad → estilo por destino`. Cierra el drift entre los 6 renderers L4 (cada uno tenía su propio `SEVERITY_TO_*` local con 19 keys divergentes); F73 los consolida en una única tupla inmutable de 20 `StyleMapping` (dataclass frozen). El módulo valida al import (20 entradas, Notion color ∈ lista cerrada de 10, sin campos vacíos) y expone 6 helpers (`icon_for`, `obsidian_callout_for`, `notion_callout_for`, `appflowy_callout_for`, `html_css_class_for`, `semantic_token_for`) que devuelven `KeyError` con sugerencia Levenshtein si llega una severidad desconocida.

| Aspecto | Detalle |
|---|---|
| Propósito | Single source of truth para los 6 renderers L4; cualquier cambio de mapeo severidad→destino se aplica una vez aquí |
| Tabla | 20 `StyleMapping`: severities `note, tip, info, warning, caution, danger, example, question, success, failure, bug, quote, abstract, security, performance, version, deprecated, conflict, external, derived` |
| 7 campos por fila | `semantic_token` (F72) · `icon` (emoji canónico) · `obsidian_callout` (tipo nativo Obsidian 1.5+) · `notion_icon` · `notion_color` (uno de los 10 válidos) · `appflowy_callout` (tipo nativo AppFlowy) · `html_css_class` (prefijo `callout-<severity>`) |
| Validador | `validate_table()` al import; verifica 20 entradas, severidades únicas ∈ `CANONICAL_SEVERITIES`, Notion color ∈ `NOTION_VALID_COLORS`, sin campos vacíos |
| Constantes exportadas | `CANONICAL_SEVERITIES` (frozenset de 20) · `NOTION_VALID_COLORS` (frozenset de 10) |
| Sugerencia | `KeyError` con Levenshtein(limit=2) si la severidad no existe (p.ej. `warnign` → `¿quizás 'warning'?`) |
| CLI | `python -m scripts.util.style_mapping --dump` (JSON con los 20 mappings) · `--resolve SEVERITY` (1 mapping detallado) |
| Consumidores | `scripts/render/obsidian.py` (obsidian_callout_for) · `scripts/render/notion_api.py` (notion_callout_for) · `scripts/render/notion_md.py` (icon_for) · `scripts/render/appflowy.py` (appflowy_callout_for) · `scripts/render/markdown.py` (icon_for + html_css_class_for) · `scripts/render/html_pdf.py` (icon_for + html_css_class_for) |
| Inconsistencias cerradas | 12 divergencias entre los dicts legacy (caution, security, performance, external, failure, bug, etc.); tabla D3 en `references/07-visual/style-mapping.md` §6 justifica cada una |
| Migración | Los 6 dicts `SEVERITY_TO_*` locales eliminados; verificado por `rg -n 'SEVERITY_TO_' scripts/render/` exit 1 |
| Códigos | 0 OK · 1 severidad desconocida (con sugerencia) |
| Dependencias | Python 3.9+ stdlib puro (dataclasses, json, argparse) |
| Wirings | Cierra los 3 criterios del ROADMAP §1437-1440 para F73; documentado en `references/07-visual/style-mapping.md` §8-§9; eval en `evals/style-mapping-sample/` (5/5 PASS) |

### `render/css_from_tokens.py` — F74

Generador de CSS variables desde `assets/tokens.json` (F72). Produce `assets/css-tokens.generated.css`: un bloque `:root { --token: hex; }` con los 9 tokens semánticos × 5 valores (45 vars) + 9 neutrals + tipografía + spacing + radii en modo light, y los mismos redefinidos en `@media (prefers-color-scheme: dark) { :root { ... } }` para el tema oscuro. Carga tokens vía `scripts/util/tokens.py` (reusa validación semver + estructura); advertencia (no error) si `$version.major > 1`. Naming convention estricto (ver tabla abajo).

| Aspecto | Detalle |
|---|---|
| Propósito | Single source of truth para que el snippet CSS (F74) y, en el futuro, la plantilla HTML/PDF (F74-FUERA) consuman `var(--semantic-*)` y `var(--_neutral-*)` sin literales hex propios (INV-14) |
| Naming | `semantic.<name>.<field>` → `--semantic-<name>-<field>` (p.ej. `semantic.info.bg` → `--semantic-info-bg`); `_neutral.<name>` → `--_neutral-<name>`; `typography.{families,scale,weights,lineHeights}.*` → `--typography-...`; `spacing.{scale,density}.*` → `--spacing-...`; `radii.<name>` → `--radii-<name>` |
| Modo | Light por defecto; dark override vía `@media (prefers-color-scheme: dark) :root { ... }` (no usa la clase `.theme-dark` de Obsidian; respeta el modo del sistema) |
| Estático (mode-agnostic) | Tipografía + spacing + radii: un solo bloque `:root` arriba; no se redefinen en dark |
| Validación | `load_tokens()` centralizado en `scripts/util/tokens.py` (verifica $version semver + 6 top-level keys + regex `#RRGGBB`) |
| Atomic write | Vía `scripts/util/_io.py:atomic_write_text` (fallback a `Path.write_text`); chmod 0644 post-write |
| CLI | `python3 -m scripts.render.css_from_tokens --out <path>` (escribe; default `assets/css-tokens.generated.css`) · `--check` (exit 0 si al día, 1 si drift o falta) · `--print` (stdout; útil para diff) |
| Consumidores | `assets/notemartin.css` (F74, `@import "css-tokens.generated.css"`) — futuro: `references/08-render/html_pdf.template.css` (F74-FUERA) |
| Códigos | 0 OK / archivo al día · 1 archivo desactualizado (con `--check`) o ruta no encontrada |
| Dependencias | Python 3.9+ stdlib puro (importlib, json, hashlib, argparse, pathlib) |
| Wirings | Cierra los 3 criterios de F74 ROADMAP §1453-1455 (snippet ≤ 400 líneas, tema dual, tablas 10+ cols legibles); eval en `evals/css-snippet-sample/` (6/6 PASS) |

### `render/_header.py` — F75

Helper `## Cabecera` que emite el bloque con los 5 campos canónicos (Resumen, Procedencia, Versión, Estado, Tiempo de lectura) en 7 formatos distintos según `dest`. Cierra la dispersión de los renderers L4 (cada uno construía su propia cabecera; F75 los unifica en una sola tabla cerrada). El módulo valida al import que `SUPPORTED_DESTS` cubra los 7 destinos canónicos. Cero literales de color (INV-14).

| Aspecto | Detalle |
|---|---|
| Propósito | Single source of truth para la cabecera visual de las 7 destinos; cualquier cambio de composición o campos se aplica una vez aquí. |
| Tabla | 5 campos en orden fijo: `summary`, `source` (compuesto), `product_version` (compuesto), `status`, `reading_time_minutes`. Filas vacías se omiten. |
| 7 destinos | `obsidian` / `appflowy` → callout nativo con bullets; `notion_api` → callout block con rich_text; `notion_md` / `markdown` → tabla GFM 2-col; `html_pdf` → `<table class="cabecera">` integrable con la tabla `## Metadata` de F59; `flashcards` → tupla `(anverso, reverso)` con `""` en anverso y `summary` como hint en reverso. |
| Composición | Procedencia = `source (source-type) §source-anchor source-url · recuperado YYYY-MM-DD`. Versión = `product product-version`. Estado = `"Publicado (published)"` con etiqueta humana + valor canónico. Reading time = `"N min"`. |
| Validación | `validate_dest_coverage()` al import; verifica que `SUPPORTED_DESTS` cubra exactamente los 7 destinos canónicos. |
| API | `emit_cabecera(frontmatter, *, dest, profile=None)` retorna `str` o `dict` (notion_api) o `tuple` (flashcards); `compute_cabecera_rows(frontmatter)` retorna `[(etiqueta, valor), ...]`; `get_summary_hint(frontmatter)` retorna `str` (summary para flashcards hint). |
| Consumidores | Los 7 renderers L4 importan este helper en lugar de construir la cabecera localmente. |
| Códigos | 0 OK / 1 destino no soportado (`ValueError`) / bug en `_header.py` (`AssertionError`). |
| Dependencias | Python 3.9+ stdlib puro. |
| Wirings | Cierra los 3 criterios de F75 ROADMAP §1467-1470; 2 propiedades universales nuevas (`summary`, `reading-time-minutes` per properties.md §5.19-§5.20) consumidas en cada destino; eval en `evals/note-templates-sample/` (5/5 PASS). |

### `validate/density_check.py` — F76

Verificador de densidad y jerarquía. Lee una nota NoteMark (`.md`), parsea
bloques por sección H2/H3, y mide las 8 reglas canónicas R1-R8 de
`references/07-visual/density.md`. Cierra el drift entre las reglas
dispersas que existían en F51 (longitudes L1/L2), F75 §5.2 (frecuencia
de anclaje y máximo de callouts consecutivos) y F46 §4 (densidad `{src:}`).
Sin dependencias externas.

| Aspecto | Detalle |
|---|---|
| Propósito | Hacer ejecutable la tabla cerrada de densidad R1-R8; cualquier cambio de umbral se aplica una vez aquí. |
| Tabla R1-R8 | R1 max L1 ≤ 60 palabras / 8 líneas; R2 max L2 ≤ 200 palabras; R3 ≥ 1 anclaje cada 200 palabras; R4 ≤ 3 callouts consecutivos; R5 ≤ 5 viñetas consecutivas; R6 sección ≥ 1 estructura; R7 L3 > 100 líneas plegable; R8 densidad `{src:}` ≥ 0.80. |
| Exenciones | `glossary-term` (R3+R6); `cheatsheet` (R3+R5+R6); `index-moc` (R3+R5+R6). 12 tipos restantes aplican todas las reglas. |
| Algoritmo | Pseudocódigo en `density.md` §5; implementación 1:1. Parser Markdown ligero (regex sobre líneas) reconoce callouts, tablas, directivas `:::type`, code fences, listas con/sin checklist. |
| Severidad | R2/R4/R5/R6 = error (bloquea cierre); R1/R3/R7/R8 = warning. `--strict` hace que warnings también exit 1. |
| CLI | `--note <path>` (un archivo), `--notes <dir>` (batch), `--json` (estructurado), `--strict`, `--allow-violations R2,R5` (override). |
| Códigos | 0 sin violaciones; 1 con violaciones; 2 error de uso. |
| Dependencias | Python 3.9+ stdlib puro (`re`, `dataclasses`, `pathlib`, `argparse`). |
| Wirings | Cierra los 3 criterios de F76 ROADMAP §1483-1485; wirings desde F46 (R8), F51 (R1+R2+R7), F75 (R3+R4); eval en `evals/density-sample/` (5/5 PASS). |

### `evals/visual/visual_inspect.py` — F77

Inspector de los 12 artefactos generados por los renderers en F77. Detecta
defectos visuales: líneas > 200 chars, tablas 10+ cols sin wrapper de
overflow, links con formato no estándar, marcas `{src:}` no canónicas, bloques
HTML sin cerrar, `<th>` sin `scope` (a11y WCAG 1.3.1), SVG sin `<title>` o
`viewBox`, CSV con > 5 clauses por front/back. Sin dependencias externas.

| Aspecto | Detalle |
|---|---|
| Propósito | Validar que los 12 artefactos reales (4 destinos × 2 notas) no tienen contenido cortado/ilegible. Cierra criterio 2 del ROADMAP §1499. |
| Formatos | Markdown (`.md`), HTML (`.html` / `.htm`), SVG (`.svg`), CSV (`.csv`). |
| Severidades | error (bloquea cierre) vs warning (no bloquea). `--strict` hace que warnings también exit 1. |
| Códigos | `MD_LINE_TOO_LONG`, `MD_TABLE_WIDE`, `MD_SRC_NONCANONICAL`, `MD_LINK_FORMAT`, `HTML_*_UNBALANCED`, `HTML_TH_NO_SCOPE`, `HTML_INLINE_STYLES`, `HTML_SRC_NONCANONICAL`, `SVG_NO_VIEWBOX`, `SVG_VIEWBOX_MALFORMED`, `SVG_NO_TITLE`, `SVG_NO_ROLE`, `CSV_RFC4180`, `CSV_MISSING_COLUMNS`, `CSV_FRONT_TOO_MANY_CLAUSES`, `CSV_BACK_TOO_MANY_CLAUSES`, `FILE_MISSING`. |
| CLI | `--artifacts-dir <path>` (default requerido), `--json`, `--strict`. |
| Códigos | 0 sin issues; 1 con issues; 2 error de uso. |
| Dependencias | Python 3.9+ stdlib puro (re, csv, json, argparse, pathlib). |
| Wirings | Cierra criterio 2 de F77 ROADMAP §1499; eval en `evals/visual/run_eval.py` (5/5 PASS); 1 fix trivial aplicado en `_header.py:204` (defect #1 en `evals/visual/defects.md`). |

### `evals/visual/run_eval.py` — F77

Eval visual de la Fase 77. 5 sub-criterios: C1 notas fuente + sha256,
C2 12 artefactos válidos, C3 45 vars semánticas en light+dark, C4
visual_inspect.py exit 0 o issues documentados, C5 checklist 12 entradas.
Cierra los 3 criterios del ROADMAP §1498-1500.

| Aspecto | Detalle |
|---|---|
| Propósito | Test ejecutable del cierre de F77. |
| Criterios | C1 (notas), C2 (artefactos), C3 (theme), C4 (inspect), C5 (checklist). |
| Salida | `PASS 5/5` o `FAIL n/5 (passed k/5)` con detalle por criterio. |
| Códigos | 0 todos PASS; 1 alguno FAIL. |
| Dependencias | Python 3.9+ stdlib puro. |
| Wirings | Cierra los 3 criterios de F77 ROADMAP §1498-1500.

### `pipeline/book_mode.py` — F106 · Orquestador del modo obra completa

Meta-orquestador sobre las 5 capas L0-L4 para fuentes multi-capítulo
(libros). Reconoce la obra entera antes del primer capítulo (índice,
prefacio, mapa de dependencias Mermaid), procesa por capítulos con estado
compartido (`book-state.json`), consolida parcialmente cada N capítulos
(default 5), y permite detenerse / reanudar en cualquier capítulo con
escritura atómica + `.bak`.

| Aspecto | Valor |
|---|---|
| Entrada | `--sdm <sdm.json> --workdir <DIR>` (init); `--workdir <DIR> --chapter chNN` (process); etc. |
| Salida | `<workdir>/book-state.json`, `<workdir>/book_map.json`, `<workdir>/book_map.mmd` (init) + mutaciones in-place (process/resume/consolidate) |
| Subcomandos | `init`, `process`, `consolidate`, `status`, `resume`, `map`, `check`, `detect-ap-bm1`, `register-concept` (9 en total) |
| Invocación | `python3 scripts/pipeline/book_mode.py init --sdm <sdm.json> --workdir <DIR> --book-id my-book --consolidation-every 5` |
| API Python | `from book_mode import BookState, register_concept, mark_done` |
| Códigos | 0 OK · 1 validación (BM-R1, BM-R4, AP-BM1..AP-BM4) · 2 uso (paths faltantes, BOOK_MODE_NO_INDEX) |
| Escritura | Atómica: tempfile + `Path.replace` + backup `.bak` antes de cada save (BM-R2) |
| Signals | SIGTERM → flush atómico + exit 0 (BM-R5b) |
| Dependencias | Python 3.9+ stdlib puro (sin `jsonschema`); usa `difflib.SequenceMatcher` para AP-BM1 |
| Documentación | `references/00-pipeline/book-mode.md` (normativa, 387 líneas) + `schemas/book-state.schema.json` + `schemas/book-map.schema.json` |
| Eval | `evals/book-mode-sample/run_eval.py` 6/6 PASS (C1 BM-R1, C2 AP-BM1, C3 stop/resume, C4 consolidación N=5 idempotente, C5 .bak atómico, C6 AP-BM2..AP-BM4) |

### `pipeline/chunk_loop.py` — F107 · Bucle por chunks y presupuesto de contexto

Meta-orquestador sobre L1-L4 para fuentes cuyo SDM supera el presupuesto
de contexto (≥ 30 bloques / ≥ 50 páginas). Fragmenta el SDM en chunks
(by_blocks / by_chapter / by_section_path) y procesa cada chunk siguiendo
el ciclo de 6 etapas (leer → inventariar → ledger → NoteMark → validar →
manifiesto) con un **presupuesto acotado** de archivos cargados por etapa.
Las unidades que cruzan la frontera entre dos chunks se documentan **una
vez** (first-seen wins; AP-CHK1 detecta duplicación). El texto crudo de la
fuente NUNCA se abre fuera de L0 (verificable con `--audit-loads`; AP-CHK2).

| Aspecto | Valor |
|---|---|
| Entrada | `--sdm <sdm.json> --workdir <DIR>` (init); `--workdir <DIR> --chunk chkNN` (walk); etc. |
| Salida | `<workdir>/chunk-state.json` (init + walk); `<audit-loads>.jsonl` (walk con flag) |
| Subcomandos | `init`, `walk`, `status`, `resume`, `check` (5 en total) |
| Invocación | `python3 scripts/pipeline/chunk_loop.py init --sdm <sdm.json> --workdir <DIR> --strategy by_blocks --chunk-size 30 --strict` |
| API Python | `from chunk_loop import ChunkState, register_cross_chunk_unit` |
| Códigos | 0 OK · 1 validación (AP-CHK1..AP-CHK4) · 2 uso (paths faltantes, CHUNK_NO_SDM, CHUNK_INVALID_ID) |
| Presupuesto | `BUDGET_PER_STAGE = {leer:4, inventariar:3, ledger:4, notemark:4, validar:3, manifiesto:3}` (tabla §3) |
| Escritura | Atómica: tempfile + `Path.replace` + backup `.bak` antes de cada save (CHK-R2) |
| Signals | SIGTERM → flush atómico + exit 0 |
| Dependencias | Python 3.9+ stdlib puro (sin `jsonschema`) |
| Documentación | `references/00-pipeline/chunk-loop.md` (normativa, 314 líneas) + `schemas/chunk-state.schema.json` |
| Eval | `evals/chunk-loop-sample/run_eval.py` 6/6 PASS (C1 chunk_size=30, C2 by_chapter, C3 cross-chunk unit, C4 AP-CHK2 audit-loads, C5 idempotente + previous_processed_at, C6 resume + .bak + timestamps inmutables) |

### `dedup/detect.py` — F108 · Detector de duplicados entre notas

Escanea todos los NoteMark (`.md`/`.nm`) del workdir y produce una lista
de pares candidatos a `merge` / `specialize` / `split` por matching de
término canónico (F40), alias (F47 §5.17 + F40), y similitud textual
(`difflib.SequenceMatcher`). Algoritmo de 4 pasos (canonical → alias →
similarity → combined). Invocable standalone o desde F106 consolidate /
F107 consolidate.

| Aspecto | Valor |
|---|---|
| Entrada | `--workdir DIR [--strategy {default,consolidate,single-chunk}] [--threshold 0.6] [--glossary PATH] [--json-out PATH]` |
| Salida | JSON `candidates.json` con `[{pair, scores, suggested_action, confidence, rationale}]` |
| Subcomandos | `scan`, `inspect --pair A B`, `explain --candidate-id N`, `verify` (recall contra fixtures) |
| Invocación | `python3 scripts/dedup/detect.py scan --workdir .notes-work/abc --glossary knowledge/glossary.json --json-out candidates.json` |
| API Python | `from detect import Detector, Candidate; det = Detector(workdir=Path('.'), glossary=Path('g.json')); cands = det.scan()` |
| Códigos | 0 OK · 1 validación (recall < 80%) · 2 uso |
| Default | `DEFAULT_SIMILARITY_THRESHOLD = 0.6`, `MIN_NOTES_TO_RUN = 5` |
| Dependencias | Python 3.9+ stdlib puro |
| Documentación | `references/03-knowledge/dedup.md` (normativa) + `schemas/profile.schema.json::def::dedup` |
| Eval | `evals/dedup-sample/run_eval.py` 3/3 PASS (C1 DEDUP-R1+R3, C2 DEDUP-R2+R4, C3 recall=4/4) |

### `dedup/apply.py` — F108 · Orquestador de apply sobre F50

Envuelve `scripts/authoring/transform.py merge|split` por subproceso;
aporta `_rewrite_links_glob` propio (workaround al bug de F50 v1 con
`*.json` globs) y actualiza `manifest.json::link_debt[]` con entradas
`redirected` por cada ID viejo redirigido.

| Aspecto | Valor |
|---|---|
| Entrada | `merge --a A.json --b B.json --output C.json --workdir DIR --irs-glob 'ir/*.json' [--note-id ID] [--dry-run] [--yes]` |
| Salida | IR merged en `<output>`; `manifest.json::link_debt[]` con entradas `redirected` |
| Subcomandos | `merge`, `split`, `specialize` (wrapper parcial) |
| Invocación | `python3 scripts/dedup/apply.py merge --a A.json --b B.json --output C.json --workdir . --irs-glob 'ir/*.json' --yes` |
| Códigos | 0 OK · 1 validación (DEDUP-R1..R5) · 2 uso (falta --yes, --irs-glob, ≥2 --at-heading) |
| Garantías | DEDUP-R1 (source_refs union), DEDUP-R2 (link redirection), DEDUP-R3 (aliases), DEDUP-R4 (manifest link_debt), DEDUP-R5 (≥2 headings) |
| Dependencias | Python 3.9+ stdlib puro (invoca `scripts/authoring/transform.py` por subproceso) |

### `pipeline/consolidate.py` — F109 · Orquestador de pases de consolidación
