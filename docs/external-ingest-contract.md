# Contrato de ingesta externa — `docs/external-ingest-contract.md`

> Documento normativo de la **Fase 124** del roadmap. Define cómo un conversor externo (PDF, EPUB, DOCX, PPTX, HTML, Markdown, transcripciones, repositorio Git) produce los artefactos L0 que consume el pipeline de la skill. **Tool-independent**: el contrato es JSON Schema + paths; el implementador elige el lenguaje y las librerías.
>
> Documentos complementarios: [`CONTRIBUTING.md`](../CONTRIBUTING.md) §5 (cómo registrar un conversor), [`references/01-ingest/regions.md`](../skill/notemartin-study-notes/references/01-ingest/regions.md) (F22, spec de `regions.json`), [`references/01-ingest/triage.md`](../skill/notemartin-study-notes/references/01-ingest/triage.md) (F17, spec de `triage.json`), [`references/01-ingest/other-formats.md`](../skill/notemartin-study-notes/references/01-ingest/other-formats.md) (F28, otros formatos), [`scripts/ingest/other_formats.py`](../skill/notemartin-study-notes/scripts/ingest/other_formats.py) (referencia Python de implementación), [`docs/adr/`](../docs/adr/) (decisiones de arquitectura).

## Índice

1. [Resumen](#1-resumen) · 2. [Contrato de `regions.json`](#2-contrato-de-regionsjson) · 3. [Contrato de `summary.json`](#3-contrato-de-summaryjson) · 4. [Contrato de `triage.json`](#4-contrato-de-triagejson) · 5. [Tool-independent](#5-tool-independent) · 6. [Cómo registrar un conversor externo](#6-cómo-registrar-un-conversor-externo) · 7. [Cambios permitidos sin reabrir F124](#7-cambios-permitidos-sin-reabrir-f124)

## §1 · Resumen

El conversor externo toma una fuente arbitraria y produce, en `<workdir>/ingest/`:

- `<basename>.regions.json` (per F22).
- `<basename>.summary.json` (per F28 / F17).
- `<basename>.triage.json` (per F17).

Si la fuente es PDF escaneada, opcionalmente también produce:

- `<basename>.ocr.json` (per F20 / F25 / F27).
- `<basename>.preprocess.json` (per F19).

El resto del pipeline (L1 SDM, L2 conocimiento, L3 autoría, L4 render) es interno de la skill y **no se extiende**. El conversor externo se detiene al producir los artefactos L0.

### 1.1 · Forma del workdir (vista del conversor externo)

```
<workdir>/ingest/
├── <basename>.triage.json          # obligatorio; preflight
├── <basename>.regions.json         # obligatorio; artefacto principal
├── <basename>.summary.json         # obligatorio; resumen global
├── <basename>.preprocess.json      # opcional; solo si preprocessado
└── <basename>.ocr.json             # opcional; solo si OCR aplicado
```

Donde `<basename>` es el nombre de la fuente sin extensión (`my-doc.pdf` → `my-doc`).

### 1.2 · Forma del workdir (vista del agente, post-L0)

El agente espera encontrar `<workdir>/ingest/*.json` y los consume sin saber de dónde vienen. El path es el contrato; el contenido es portable.

## §2 · Contrato de `regions.json`

Spec completa en `references/01-ingest/regions.md` §3. Resumen:

```json
{
  "schema_version": "1.0.0",
  "source_id": "<corpus_id>",
  "format": "pdf" | "epub" | "docx" | "pptx" | "html" | "md" | "txt" | "srt" | "vtt" | "json" | "git",
  "regions": [
    {
      "region_id": "<sha1-prefix-12>",
      "semantic_class": "heading" | "paragraph" | "table" | "figure" | "code" | "formula" | "list" | "quote" | "footnote" | "toc" | "boilerplate" | "caption" | "syntax-diagram" | "note" | "warning" | "example" | "console" | "admonition",
      "content": {
        "text": "...",
        "html": "...",
        "language": "es" | "en" | "..."
      },
      "bbox": [x, y, w, h],
      "page": 1,
      "block_index": 0,
      "section_path": "<ruta jerárquica, e.g. 'Chapter 1 > Section 1.2'>",
      "confidence": 0.95,
      "origin": "native_text" | "ocr" | "manual" | "external",
      "language": "es" | "en" | "...",
      "source_ref": "<source_hash>"
    }
  ]
}
```

Cada campo está documentado en `references/01-ingest/regions.md` §3. **Reglas duras:**

- `region_id` = sha1(`source_hash` + `section_path` + `block_index`)[:12]. Inmutable una vez calculado.
- `source_ref` resoluble al SDM (F13). Si el conversor no puede resolver, marca `confidence: 0.0` y `origin: "manual"`.
- `confidence` ∈ [0.0, 1.0]. Para `origin: native_text` ≥ 0.95; para `origin: ocr` ≥ 0.60 (umbral F26).
- `schema_version` const `"1.0.0"`. Cambiar esto reabre F22.

## §3 · Contrato de `summary.json`

```json
{
  "schema_version": "1.0.0",
  "source_id": "<corpus_id>",
  "format": "<formato detectado>",
  "region_count": 42,
  "class_distribution": {
    "heading": 5,
    "paragraph": 30,
    "table": 2,
    "code": 1,
    "figure": 4
  },
  "fillers_removed_count": 0,
  "ocr_engine": "tesseract" | "easyocr" | "paddleocr" | null,
  "ocr_avg_confidence": 0.92 | null,
  "language_detected": ["en", "es"] | ["es"],
  "warnings": ["region 12 confidence < 0.6", "..."]
}
```

`warnings` es la lista de issues no fatales (baja confianza, regiones huérfanas, OCR reintentado). Errores fatales deben abortar el conversor con exit code != 0, no aparecer aquí.

## §4 · Contrato de `triage.json`

Shape completa en `references/01-ingest/triage.md` §7. Resumen:

```json
{
  "schema_version": "1.0.0",
  "source_id": "<corpus_id>",
  "classification": "native_reliable" | "native_unreliable" | "mixed" | "scanned" | "text_only" | "...",
  "plan": {
    "extractors": ["pdf_native", "layout", "ocr"],
    "languages": ["en", "es"],
    "skip_pages": [12, 13]
  },
  "confidence": 0.95,
  "warnings": ["..."]
}
```

El triage decide qué extractores aplicar (pdf_native, layout, ocr, post_ocr, code_ocr, formulas, etc.) antes de que el conversor externo los invoque. Tras el triage, el conversor produce los artefactos L0 y los demás extractores se ejecutan.

## §5 · Tool-independent

El contrato NO especifica:

- **Lenguaje de implementación** (Python, Go, Rust, JS, Kotlin, todos válidos).
- **Librería de OCR** (Tesseract, EasyOCR, PaddleOCR, AWS Textract, Google Document AI, todos válidos).
- **Librería de PDF** (qpdf, mupdf, pdfium, lopdf, unidoc, todas válidas).
- **Librería de DOCX** (python-docx, docx-rs, todas válidas).
- **Sistema operativo** (Linux, macOS, Windows).
- **Formato binario intermedio** (no hay; es JSON puro).

**Cualquier conversor que produzca `regions.json` + `summary.json` + opcionalmente `triage.json` + opcionalmente artefactos de OCR, en el workdir correcto, es un conversor válido.** El resto del pipeline los consume sin saber de dónde vienen.

Ejemplos de conversores válidos (no exhaustivo):

- `scripts/ingest/other_formats.py` (F28, Python, stdlib + ebooklib opcional).
- Un conversor Go que use `unidoc` para PDF + `tesseract` CLI.
- Un conversor Rust que use `lopdf` + `tesseract-rs`.
- Un servicio web que reciba un PDF vía HTTP y devuelva el JSON directamente.
- Una integración con AWS Textract que produce `summary.json` + `regions.json` desde una llamada API.

## §6 · Cómo registrar un conversor externo

Si quieres que tu conversor sea first-class en la skill (recomendado para conversores de uso común):

1. **Implementa el contrato** de §2-§4 en cualquier lenguaje.
2. **Añade un test de integración** en `evals/<fase>-sample/` siguiendo la triada de `CONTRIBUTING.md` §2:
   - Caso de fallo: input que tu conversor debería rechazar pero acepta sin tu validación.
   - Caso de éxito: input conocido con output esperado.
3. **Documenta en ADR** (`docs/adr/ADR-NNNN-<nombre>.md`) la decisión de incluirlo.
4. **PR con triada + ADR + test de integración**.

Si solo quieres usar tu conversor localmente sin contribuirlo al repo: **no necesitas registrarlo**. La skill consume cualquier `regions.json` válido. El contrato es la interfaz pública; la implementación interna es libre.

## §7 · Cambios permitidos sin reabrir F124

**No reabren F124:**
- Añadir un nuevo formato al enum `format` de §2 (e.g. `ipynb` para Jupyter notebooks).
- Documentar una nueva forma de `bbox` (e.g. coordenadas normalizadas vs píxeles) en `regions.md` §3.
- Cambiar el threshold de `confidence` por defecto (con ADR; puede requerir MAJOR bump de un schema).
- Añadir campos opcionales al `summary.json` (no quitar los obligatorios).

**Reabren F124:**
- Cambiar el shape de `regions.json` o `summary.json` (campos obligatorios).
- Eliminar un campo obligatorio del contrato.
- Hacer tool-specific el contrato (e.g. "debe usar la librería X" o "debe generar el JSON desde Python").
- Cambiar el formato del workdir (path `<workdir>/ingest/`).
