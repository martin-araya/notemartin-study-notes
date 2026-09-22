# Triaje de archivo — `references/01-ingest/triage.md`

> Documento normativo de la Fase 17 del roadmap. Define cómo el script `scripts/ingest/triage.py` clasifica una fuente (PDF/EPUB/DOCX/PPTX/HTML/Markdown/TXT/repositorio) y emite un plan de ingesta por rangos de páginas. Las heurísticas tienen umbrales numéricos declarados en `scripts/ingest/thresholds.yaml`.
>
> Documentos complementarios: `SKILL.md` §3 (triaje por página, no por documento), `references/00-pipeline/architecture.md` §3.1 (capa L0 — Ingesta), §8 (modo degradado).
>
> Enrutado desde N2: `docs/skill-anatomy.md` §6 fila `F17`. Docs hermanos: `references/01-ingest/ocr-engines.md` (F20), `references/01-ingest/code-ocr.md` (F25).

## Índice

1. [Propósito](#1-propósito) · 2. [Cuándo se aplica](#2-cuándo-aplica) · 3. [Clases de clasificación](#3-clases-de-clasificación) · 4. [Heurísticas y umbrales numéricos](#4-heurísticas-y-umbrales-numéricos) · 5. [Pipeline de análisis](#5-pipeline-de-análisis) · 6. [Forma del plan de ingesta](#6-forma-del-plan-de-ingesta) · 7. [Forma del `triage.json`](#7-forma-del-triagejson) · 8. [Mapeo del corpus dorado](#8-mapeo-del-corpus-dorado) · 9. [Advertencias y modo degradado](#9-advertencias-y-modo-degradado) · 10. [Anti-patrones](#10-anti-patrones) · 11. [Cómo verificar + cambios permitidos](#11-cómo-verificar--cambios-permitidos)

## 1. Propósito

Decidir **cómo** se ingiere cada fuente antes de ejecutar extractores. Sin un triaje previo, el agente gastaría OCR sobre un PDF con capa de texto fiable o trataría como HTML un markdown ya estructurado.

El script `scripts/ingest/triage.py`:

- Detecta el formato top-level (PDF, EPUB, DOCX, PPTX, HTML, Markdown, TXT, repositorio).
- Para PDF: clasifica **cada página** en una de cuatro clases (`native_reliable`, `native_degraded`, `pure_scan`, `hybrid_page`); de ahí deriva la clase global.
- Para el resto: la clase coincide con el formato.
- Emite un **plan de ingesta** con rangos de páginas consecutivos colapsados cuando comparten `(clase, extractor)`.
- Registra hash sha256, tamaño, advertencias y versión de umbrales.

## 2. Cuándo se aplica

Antes de la primera ingesta de una fuente. Un solo comando al inicio del pipeline:

```
python3 scripts/ingest/triage.py --source <ruta> --out-dir <workdir/ingest/>
```

El plan escrito en `<out-dir>/triage.{json,md}` es la entrada contractual de los extractores F18–F29. Re-triaje solo se ejecuta si cambia `thresholds_version` o el formato detectado.

## 3. Clases de clasificación

### 3.1 PDF (clasificación por página)

| Clase | Definición operativa | Origen típico |
|---|---|---|
| `native_reliable` | Capa de texto presente, fonts embebidas, sin imagen dominante | PDF/A, manuales técnicos renderizados, papers con figuras pequeñas |
| `native_degraded` | Capa de texto presente pero ruidosa: chars cortos, sin fonts, o ratio no-imprimible alto | PDFs escaneados con OCR previo deficiente, copias de baja calidad |
| `pure_scan` | Imagen a página completa; sin texto extraíble | Escaneos puros (sin OCR previo), libros antiguos digitalizados |
| `hybrid_page` | Texto nativo coexiste con imagen grande (≥ 50 % del área) | Apéndices escaneados dentro de manuales nativos, figuras a página completa con pie de foto |

### 3.2 Clasificación global del PDF

| Condición | Resultado |
|---|---|
| ≥ 80 % de páginas son `pure_scan` | `pdf_pure_scan` |
| ≥ 80 % de páginas son `native_reliable` | `pdf_native_reliable` |
| Hay ≥ 1 página con texto y ≥ 1 página scan, y ≥ 2 clases distintas | `pdf_hybrid` |
| Cualquier otro caso con texto presente | `pdf_native_degraded` |

Si no hay páginas (PDF vacío): `unknown`.

### 3.3 Formatos no PDF

| Formato | Clasificación global | Plan típico |
|---|---|---|
| `html` | `html` | 1 rango, extractor `web_docs` |
| `markdown` | `markdown` | 1 rango, extractor `text` |
| `text` (TXT) | `text` | 1 rango, extractor `text` |
| `repository` (directorio con `.git/` + `README*`) | `repository` | 1 rango, extractor `repo_tree` |
| `epub` | `epub` | 1 rango, extractor `other_formats` |
| `docx` | `docx` | 1 rango, extractor `other_formats` |
| `pptx` | `pptx` | 1 rango, extractor `other_formats` |

## 4. Heurísticas y umbrales numéricos

Todos los valores viven en `scripts/ingest/thresholds.yaml` (versión `schema_version: "1.0.0"`). Cambiar un umbral es **modificar el YAML**, no el script.

| Heurística | Clave YAML | Umbral numérico | Condición |
|---|---|---|---|
| Caracteres extraíbles por página | `pdf.chars_per_page.reliable_min` | `1000.0` | `chars ≥ 1000` contribuye a `native_reliable` |
| Caracteres extraíbles por página | `pdf.chars_per_page.degraded_min` | `100.0` | `chars < 100` activa el camino de scan |
| Fuentes embebidas | `pdf.fonts.reliable_min` | `1.0` | `fonts ≥ 1` necesario para `native_reliable` |
| Cobertura de imagen a página completa | `pdf.full_page_image.rate_scan_min` | `0.9` | `rate ≥ 0.9` requerido para `pure_scan` |
| Cobertura de imagen a página completa | `pdf.full_page_image.rate_hybrid_min` | `0.5` | `rate ≥ 0.5` activa `hybrid_page` |
| Caracteres no imprimibles | `pdf.non_printable_ratio.degraded_min` | `0.05` | `ratio ≥ 0.05` marca como `native_degraded` |
| Cuota dominante para clase global | `pdf.global_classification.dominant_share` | `0.8` | ≥ 80 % de páginas → clase global |
| Mínimo de clases para `pdf_hybrid` | `pdf.global_classification.hybrid_min_classes` | `2` | ≥ 2 clases distintas → `pdf_hybrid` |
| Ratio tag/texto en HTML | `non_pdf.html_tag_ratio_max` | `0.3` | (reservado para heurística de fallback) |
| Imprimibilidad mínima de texto | `non_pdf.text_printable_min` | `0.95` | ≥ 95 % → `text` |

### 4.1 Algoritmo de clasificación por página (orden de prioridad)

```
1. pure_scan:        chars < degraded_min  Y  full_page_image_rate ≥ rate_scan_min
2. native_reliable:  chars ≥ reliable_min  Y  fonts ≥ reliable_min
3. hybrid_page:      full_page_image_rate ≥ rate_hybrid_min  Y  chars ≥ degraded_min
4. native_degraded:  (chars ∈ [degraded_min, reliable_min))
                     O non_printable_ratio ≥ degraded_min
                     O fonts < reliable_min
```

Sin adjetivos: cada paso cita un número exacto. Si la heurística cambia, se reabre §4 (no el script).

## 5. Pipeline de análisis

```
load_thresholds()           carga scripts/ingest/thresholds.yaml
  ↓
detect_format(source)        magic bytes primero, extensión después
  ├── pdf                    analyze_pdf()
  │     ├── pypdf preferido (chars por página, fuentes, imágenes)
  │     └── fallback a bytes si pypdf ausente
  ├── epub / docx / pptx     ZIP sniff (mimetype, word/, ppt/)
  ├── html                   <!DOCTYPE> o <html> en primeros 4096 bytes
  ├── markdown               extensión .md/.markdown
  ├── text                   ratio imprimible ≥ 0.95
  └── repository             .git/ + README* dentro del directorio
  ↓
classify_pdf_page(metrics, thresholds)   ← solo si pdf
classify_pdf_global(pages)              ← solo si pdf
  ↓
build_plan(pages, thresholds)           colapsa rangos
  ↓
atomic_write(triage.json + triage.md)
```

Detección de formato: PDF por magic `%PDF-`, EPUB/DOCX/PPTX por estructura ZIP. HTML antes que Markdown antes que Texto: el orden importa porque un `.html` detectado por `<!DOCTYPE>` no se reinterpreta como texto.

## 6. Forma del plan de ingesta

Cada rango declara `pages` (rango o página única), clase, extractor (responsabilidad F18–F29), `ocr_required` y `confidence_expected`:

| Clase | Extractor L0 | `ocr_required` | `confidence_expected` |
|---|---|---|---|
| `native_reliable` | `pdf_native` (F18) | `false` | `high` |
| `native_degraded` | `pdf_native` (F18) | `false` | `medium` |
| `pure_scan` | `ocr` (F19+F20) | `true` | `low` |
| `hybrid_page` | `pdf_native` (F18) | `false` | `medium` |
| `html` | `web_docs` (F29) | `false` | `high` |
| `markdown`, `text` | `text` (F28) | `false` | `high` |
| `repository` | `repo_tree` (F28) | `false` | `high` |
| `epub`, `docx`, `pptx` | `other_formats` (F28) | `false` | `high`/`medium` |

**Ejemplo de plan colapsado** (PDF híbrido de 8 páginas: 3 reliable + 2 scan + 3 degraded):

```json
[
  {"pages": "1-3",   "class": "native_reliable", "extractor": "pdf_native", "ocr_required": false, "confidence_expected": "high"},
  {"pages": "4-5",   "class": "pure_scan",       "extractor": "ocr",        "ocr_required": true,  "confidence_expected": "low"},
  {"pages": "6-8",   "class": "native_degraded", "extractor": "pdf_native", "ocr_required": false, "confidence_expected": "medium"}
]
```

Tres rangos distintos. El colapso es por `(clase, ocr_required, extractor)`: dos páginas consecutivas con la misma ternaria se unen.

## 7. Forma del `triage.json`

`schema_version: "1.0.0"` (const en cada salida). Campos:

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `schema_version` | string const | sí | `"1.0.0"` |
| `source.path` | string | sí | ruta absoluta del archivo o directorio |
| `source.hash` | string hex 64 | sí | sha256 del archivo (architecture.md §6) |
| `source.size_bytes` | int | sí | bytes del archivo |
| `source.format` | enum | sí | `pdf / epub / docx / pptx / html / markdown / text / repository` |
| `thresholds_version` | string | sí | `schema_version` del YAML cargado |
| `format_classification` | string | sí | clase global (§3.2 o §3.3) |
| `page_count` | int | sí | 1 para no-PDF |
| `pages[]` | array | sí | métricas por página; omitido si no aplica (no-PDF = 1 entrada) |
| `pages[].page` | int | sí | 1-indexed |
| `pages[].chars` | int | sí | caracteres extraíbles |
| `pages[].fonts` | int | sí | fuentes embebidas detectadas |
| `pages[].full_page_image_rate` | float | sí | ratio [0, 1] |
| `pages[].images` | int | sí | número de XObjects /Image |
| `pages[].non_printable_ratio` | float | sí | ratio [0, 1] |
| `pages[].class` | string | sí | clase por página (omítido en no-PDF: igual a `format`) |
| `plan[]` | array | sí | rangos colapsados (§6) |
| `warnings[]` | array<string> | sí (puede ser vacío) | advertencias detectadas |
| `generated_at` | string ISO 8601 | sí | timestamp UTC |

El `triage.md` derivado tiene el mismo contenido en formato tabla Markdown legible por humanos.

## 8. Mapeo del corpus dorado

Mapeo esperado para las 14 fuentes de `evals/corpus/` + 1 fixture híbrido sintético. La verificación material corre vía `evals/triage-sample/run_eval.py` (F118 la ejecutará contra corpus completo).

| # | Fuente | Formato real | `format_classification` | Plan típico |
|---|---|---|---|---|
| 01 | postgresql-chapter | HTML (`sample.html`) | `html` | `web_docs` 1 rango |
| 02 | database-internals-chapter (scanned) | PDF (sin muestra: stub) | `pdf_pure_scan` | `ocr` 1 rango |
| 03 | rfc-7231 | TXT (`sample.txt`) | `text` | `text` 1 rango |
| 04 | arxiv-two-column | PDF (`sample.pdf`) | `pdf_native_reliable` | `pdf_native` 1 rango |
| 05 | iso-sql-tables | HTML (`sample.html`) | `html` | `web_docs` 1 rango |
| 06 | kubernetes-api-ref | HTML (`sample.html`) | `html` | `web_docs` 1 rango |
| 07 | docker-cli-ref | HTML (`sample.html`) | `html` | `web_docs` 1 rango |
| 08 | conference-transcript | TXT (sin muestra: stub) | `text` | `text` 1 rango |
| 09 | conference-slides | PDF (sin muestra: stub) | `pdf_pure_scan` | `ocr` 1 rango |
| 10 | postgres-readme-repo | directorio (stub) | `repository` | `repo_tree` 1 rango |
| 11 | iso-cpp-syntax | HTML (`sample.html`) | `html` | `web_docs` 1 rango |
| 12 | arxiv-formulas | PDF (`sample.pdf`) | `pdf_native_reliable` | `pdf_native` 1 rango |
| 13 | internet-archive-scan-hostil | PDF (sin muestra: stub) | `pdf_pure_scan` | `ocr` 1 rango |
| 14 | book-bad-numbering-hostil | PDF (sin muestra: stub) | `pdf_hybrid` | `pdf_native` + `ocr` ≥ 2 rangos |
| — | hybrid-synthetic (fixture) | PDF (`fixtures/hybrid-synthetic.pdf`) | `pdf_hybrid` | 3 rangos distintos |

Para las fuentes sin muestra, `evals/triage-sample/run_eval.py` genera un stub sintético etiquetado (HTML/TXT/PDF-stub) para verificar la mecánica del script. La verificación contra la muestra real se difiere a F118.

## 9. Advertencias y modo degradado

El script no bloquea. Emite códigos de salida (0 ok, 2 con warnings) y entradas en `warnings[]`:

- `pypdf not available; using byte-level analysis (less precise than pypdf path)` — el fallback a bytes da métricas aproximadas; el caller debe considerar revisar el JSON manualmente.
- `thresholds file not found: <path>; using built-in defaults` — cualquier problema con el YAML dispara defaults internos; revisar.
- `thresholds schema_version is <v>, expected "1.0.0"; using built-in defaults` — incompatibilidad de versión.
- `PyYAML not available; using built-in defaults instead of thresholds file` — sin PyYAML instalado; el script sigue funcionando con defaults internos.

`architecture.md` §8 (modo degradado de L0) sigue aplicando aguas abajo: si `confidence_expected: "low"` aparece para un rango, F26 (`review_report.py`) debe confirmar antes de L2.

## 10. Anti-patrones

- **No clasificar el documento entero como una clase.** El caso híbrido es frecuente; un PDF con capítulos nativos + apéndices escaneados es regla, no excepción.
- **No basarse solo en caracteres.** Una página con 1500 caracteres sin fonts embebidas puede ser OCR previo o encoding corrupto: `chars ≥ reliable_min` solo no es fiable; hace falta `fonts ≥ reliable_min` también.
- **No adivinar formato por extensión.** `mi_documento.pdf` que en realidad es un TXT renombrado se detecta por magic bytes, no por `.pdf`.
- **No usar OCR como fallback universal.** `pdf_pure_scan` debe ir a `ocr` (F19+F20). `native_reliable` nunca pasa por OCR.
- **No escribir el plan sin colapsar rangos.** 200 páginas de `native_reliable` no son 200 entradas en `plan[]`, son 1 rango `"1-200"`.
- **No fijar umbrales en el código.** Todo umbral vive en `thresholds.yaml`. Si necesitas cambiar un número, edita el YAML.
- **No inventar formato global `pdf_degraded`.** Las 4 clases globales del PDF son `pdf_native_reliable`, `pdf_native_degraded`, `pdf_pure_scan`, `pdf_hybrid`.

## 11. Cómo verificar + cambios permitidos

Cinco pasos (mismo patrón que `architecture.md` §10):

1. ¿Cada formato top-level tiene un clasificador? (PDF página a página; el resto, formato único).
2. ¿Las heurísticas son declaradas en `thresholds.yaml` y referenciadas desde aquí? (verificar `grep "pdf.chars_per_page" triage.md`).
3. ¿El plan tiene rangos colapsados y al menos un extractor por rango?
4. ¿El `triage.json` declara `schema_version` y pasa el validador de `evals/triage-sample/run_eval.py`?
5. ¿La tabla §8 se cumple para los 14 fuentes + 1 fixture híbrido?

```bash
python3 evals/triage-sample/run_eval.py
# Esperado: "PASS: 15/15"
```

**Cambios permitidos sin reabrir Fase 17:**

- Añadir una nueva clase PDF cuando aparezca un caso real no modelado (con ADR).
- Añadir una nueva heurística al YAML con su umbral (con ADR; actualizar §4 y el script).
- Cambiar un umbral del YAML sin ADR si la evidencia experimental contra el corpus lo justifica (registrar en `CHANGELOG.md`).

**Reabren Fase 17:**

- Cambiar el algoritmo de hash (`architecture.md` §6).
- Cambiar el orden de prioridad del clasificador por página (afecta a `pdf_hybrid`).
- Dividir `pure_scan` en subclases.
- Cambiar `extractor_map` (afecta a F18–F29; requiere coordinación con esas fases).

Materialización de la suite de evals automatizada contra el corpus completo: F118 (evals).

## 12. Siguiente extractor — `pdf_native.py` (F18)

Tras el triaje, el siguiente paso L0 sobre PDFs clasificados como `native_reliable` o `native_degraded` es la extracción nativa de runs de texto con coordenadas, fuente y tamaño. La conexión entre ambos scripts:

1. `triage.py` emite `triage.json` con `plan[].class ∈ {native_reliable, native_degraded}` y rangos por páginas.
2. `pdf_native.py --source <pdf> --plan triage.json` consume ese plan: extrae solo los rangos nativos, salta `pure_scan` con warning (F19+F20 los cubren).
3. `pdf_native.py` produce `fragments.json` con runs tipográficos + role + heading_level + section_path + is_boilerplate, además de `outline[]` y `boilerplate_summary`. Esa es la entrada contractual para `build_sdm.py` (F31).

Detalles y algoritmos: [`pdf-native.md`](pdf-native.md).
