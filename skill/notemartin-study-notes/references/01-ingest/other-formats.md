# EPUB, DOCX, PPTX y transcripciones — `references/01-ingest/other-formats.md`

> Documento normativo de la Fase 28 del roadmap. Define cómo el script `scripts/ingest/other_formats.py` procesa archivos EPUB (manifiesto + capítulos + imágenes + notas), DOCX (estilos + comentarios + change tracking + tablas nativas), PPTX (slides + notas del orador + grupos) y transcripciones (SRT/VTT/JSON con limpieza de muletillas y anclas temporales).
>
> Documentos complementarios: `references/01-ingest/regions.md` (F22, contrato de `regions.json`), `references/01-ingest/post-ocr.md` (F27), `references/01-ingest/confidence.md` (F26), `references/00-pipeline/architecture.md` §3.1 (L0 Ingesta), §5 (frontera de capa).

## Índice

1. [Propósito](#1-propósito) · 2. [Detección de formato](#2-detección-de-formato) · 3. [EPUB](#3-epub-manifiesto-capítulos-imágenes) · 4. [DOCX](#4-docx-estilos-comentarios-change-tracking-tablas) · 5. [PPTX](#5-pptx-slides-notas-del-orador-grupos) · 6. [Transcripciones](#6-transcripciones-srtvttjson) · 7. [Limpieza de muletillas](#7-limpieza-de-muletillas) · 8. [Anclas temporales](#8-anclas-temporales) · 9. [Forma de `regions.json` y `summary.json`](#9-forma-de-regionsjson-y-summaryjson) · 10. [Anti-patrones](#10-anti-patrones) · 11. [Cómo verificar + cambios permitidos](#11-cómo-verificar--cambios-permitidos)

## 1. Propósito

Producir `regions.json` estandarizado para formatos que no son PDF: EPUB, DOCX, PPTX, y transcripciones (SRT/VTT/JSON). El formato de salida es compatible con el contrato de F22 para que F31 pueda consumirlo sin transformaciones.

`scripts/ingest/other_formats.py` produce, en `<out-dir>/ingest/other_formats/`:

- `<basename>.regions.json` — array de regiones con `semantic_class` específico del formato.
- `summary.json` — global con `format`, `region_count`, `class_distribution`, `fillers_removed_count`.

## 2. Detección de formato

| Formato | Extensión | Magic bytes / heurística |
|---|---|---|
| EPUB | `.epub` | ZIP + primer archivo es `mimetype` con contenido `application/epub+zip` |
| DOCX | `.docx` | ZIP + archivo `[Content_Types].xml` presente |
| PPTX | `.pptx` | ZIP + archivo `ppt/presentation.xml` presente |
| SRT | `.srt` | Texto plano, bloques con `HH:MM:SS,mmm --> HH:MM:SS,mmm` |
| VTT | `.vtt` | Texto plano, comienza con `WEBVTT`, bloques `HH:MM:SS.mmm --> HH:MM:SS.mmm` |
| JSON | `.json` | JSON con campo `segments` (Whisper) o `results`/`items` (AWS Transcribe) |

Si `--format auto` (default), F28 detecta el formato por extensión + magic bytes. Si `--format` se especifica explícitamente, F28 usa ese formato sin detección.

## 3. EPUB (manifiesto, capítulos, imágenes)

Algoritmo con `ebooklib`:

1. Leer `epub.read_epub(path)` → `book`.
2. Iterar `book.spine` en orden → cada `SpineItem` es un `Chapter` (XHTML).
3. Para cada capítulo, parsear el XHTML y extraer:
   - `<h1>` → `heading, level: 1`
   - `<h2>` → `heading, level: 2`
   - `<p>` → `text`
   - `<li>` → `list_item`
   - `<blockquote>` → `editorial_note`
   - `<pre>` / `<code>` → `code`
   - `<img>` → `figure` con `src` y `alt` extraídos como atributos.
   - `<a href="#note-N">` → marca como anchor; el texto del ancla es la referencia.
   - Notas (endnotes del libro): `book.get_items_of_type(ebooklib.ITEM_NOTE)` → `footnote` con `anchor: "note-N"` y `text`.

Cada región emitida tiene:
```jsonc
{
  "id": "epub-c1-r001",
  "semantic_class": "heading",  // o "text", "list_item", "figure", "footnote", ...
  "level": 1,                    // solo para heading
  "text": "...",
  "anchor": "note-3",            // solo para footnote
  "chapter": 1,
  "confidence": 0.95,
  "src": "images/diagram.png",   // solo para figure
  "alt": "Diagram 1"             // solo para figure
}
```

## 4. DOCX (estilos, comentarios, change tracking, tablas)

Algoritmo con `python-docx`:

1. Leer `docx.Document(path)` → `doc`.
2. Para cada `paragraph` en `doc.paragraphs`:
   - `paragraph.style.name` → mapeo a `semantic_class`:
     - `Heading 1` / `Heading 2` / `Heading 3` → `heading` con `level`.
     - `List Bullet` / `List Number` → `list_item` con `bullet: true/false`.
     - `Quote` → `editorial_note`.
     - `Code` → `code`.
     - `Normal` → `text`.
   - Detectar `change_tracked: true` si `<w:ins>` o `<w:del>` está presente en `paragraph._element`.
3. Comentarios: `doc.part.related_parts` con `comments_part` → cada comment con `author`, `text`, `anchor_para_id`.
4. Tablas nativas: `doc.tables` → cada tabla con `rows`, `cols`, `cells[r][c]`.

Cada región:
```jsonc
{
  "id": "docx-r001",
  "semantic_class": "heading",  // o "text", "list_item", "code", "comment", "table"
  "level": 1,
  "text": "...",
  "chapter": null,            // no aplica para DOCX
  "confidence": 0.95,
  "author": "user@example.com",  // solo para comment
  "anchor_para_id": "p-001",     // solo para comment
  "change_tracked": true,         // opcional
  "rows": 3, "cols": 4, "cells": [...]  // solo para table
}
```

## 5. PPTX (slides, notas del orador, grupos)

Algoritmo con `python-pptx`:

1. Leer `pptx.Presentation(path)` → `prs`.
2. Iterar `prs.slides` en orden (preserva el orden del archivo PPTX).
3. Para cada `slide`:
   - `slide.shapes.title` → `heading, level: 1`.
   - Otros `shape.has_text_frame` → `text` con `text: shape.text_frame.text`.
   - `slide.notes_slide.notes_text_frame` → `speaker_note` con el texto (criterio 2).
   - `slide.shapes` con `shape.shape_type == MSO_SHAPE_TYPE.GROUP` → grupo con `children[]` recursivos.

Cada región:
```jsonc
{
  "id": "pptx-s1-r002",
  "semantic_class": "speaker_note",  // o "heading", "text"
  "text": "...",
  "slide": 1,
  "confidence": 0.95
}
```

## 6. Transcripciones (SRT/VTT/JSON)

### SRT

```
1
00:00:00,000 --> 00:00:02,500
Hello world.

2
00:00:02,500 --> 00:00:05,000
Um, this is a test.
```

Cada bloque se parsea con regex:
- `^(\d+)$` → índice.
- `^(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})$` → timestamps.
- Texto hasta el siguiente bloque.

### VTT

```
WEBVTT

00:00:00.000 --> 00:00:02.500
Hello world.
```

Similar pero timestamps usan `.` en lugar de `,`.

### JSON (Whisper-style)

```json
{
  "segments": [
    {"start": 0.0, "end": 2.5, "text": "Hello world."},
    {"start": 2.5, "end": 5.0, "text": "Um, this is a test."}
  ]
}
```

### AWS Transcribe

```json
{
  "results": {
    "items": [
      {"start_time": "0.0", "end_time": "2.5", "alternatives": [{"content": "Hello world."}]}
    ]
  }
}
```

## 7. Limpieza de muletillas

Whitelist cerrada de muletillas: `um`, `uh`, `er`, `ah`, `eh`, `mm`, `hmm`, `mm-hmm`.

Reglas:
- Una muletilla SOLO se elimina si está **al inicio del segmento** o **entre pausas > `MIN_PAUSE_FOR_FILLER_REMOVAL_S = 2.0` segundos**.
- Las muletillas dentro de una frase sustantiva NO se eliminan (p.ej. "um" como sustantivo en alemán).

```python
def clean_filler_words(text: str, prev_pause_s: float = 0.0) -> str:
    if prev_pause_s < MIN_PAUSE_FOR_FILLER_REMOVAL_S:
        return text
    words = text.split()
    out = []
    for w in words:
        clean = re.sub(r"[.,;:!?]$", "", w.lower())
        if clean in TRANSCRIPT_FILLER_WORDS and (not out or len(out) == 0):
            continue  # remove filler at start
        out.append(w)
    return " ".join(out)
```

Cada muletilla eliminada se cuenta en `fillers_removed_count` en el summary.

## 8. Anclas temporales

Cada bloque de transcripción tiene:
```jsonc
{
  "id": "srt-r001",            // ID único global
  "semantic_class": "transcript_segment",
  "anchor_id": "t-0001",     // ancla temporal para F31
  "start": 0.0,             // segundos desde el inicio
  "end": 2.5,
  "text": "Hello world.",
  "confidence": 0.95
}
```

F31 puede resolver `anchor_id` ↔ `text` mediante el campo `anchor_id`. La marca temporal (`start`, `end`) se conserva para sincronización con video/audio.

## 9. Forma de `regions.json` y `summary.json`

`regions.json` por archivo (formato-aware, ver §3-§6).

`summary.json` global:

```jsonc
{
  "schema_version": "1.0.0",
  "source": {
    "format": "epub",
    "path": "...",
    "hash": "..."
  },
  "region_count": 24,
  "class_distribution": {
    "heading": 3, "text": 18, "figure": 2, "footnote": 1
  },
  "fillers_removed_count": 5,
  "warnings": [],
  "generated_at": "2026-09-24T..."
}
```

## 10. Anti-patrones

- **No** inventar texto cuando el formato está corrupto o vacío (warning + región vacía).
- **No** usar ML para entender el contenido (criterio 1: cada formato produce SDM válido, sin adivinanzas).
- **No** eliminar muletillas que NO estén en la whitelist.
- **No** emitir notas del orador como `text`; siempre como `speaker_note` (criterio 2).
- **No** perder la marca temporal al limpiar muletillas (criterio 3: anclas resolubles).
- **No** aceptar archivos sin formato reconocido (error claro con `--format` sugerido).

## 11. Cómo verificar + cambios permitidos

Cinco pasos:

1. ¿El formato se detectó correctamente (EPUB/DOCX/PPTX/SRT/VTT/JSON)?
2. ¿Cada formato produce `regions.json` con `text` no vacío?
3. ¿Las notas del orador son `speaker_note` con su texto?
4. ¿Las anclas temporales tienen `start` y `end` numéricos?
5. ¿Las muletillas en pausas > 2s se eliminaron?

```bash
python3 evals/other-formats-sample/run_eval.py
# Esperado: "PASS los 3 criterios"
```

**Cambios permitidos sin reabrir Fase 28:**

- Añadir un nuevo formato (PDF, RTF, etc.) con ADR.
- Añadir más palabras a la whitelist de muletillas con ADR.
- Cambiar el threshold `MIN_PAUSE_FOR_FILLER_REMOVAL_S` con ADR.

**Reabren Fase 28:**

- Cambiar el algoritmo de detección de formato.
- Eliminar la whitelist cerrada de muletillas.
- Cambiar el formato de `anchor_id` en transcripciones.
- Eliminar la separación entre notas del orador y texto de slide.

## 12. Siguiente fase — `web_docs.py` (F29)

Tras F28 (other-formats), F29 procesa documentación web multipágina (mirror descargado con `wget --mirror` o presente en un directorio local) y la normaliza al contrato de F22:

1. F29 lee directorio local de HTML + opcional `--base-url <url>`.
2. **BFS desde `--index`**: preserva orden del nav; cada `<a href>` interno se sigue.
3. **Eliminación de boilerplate**: selectores CSS configurables (`nav`, `header.navbar`, `footer`, `aside`, `div.sidebar`, `div.banner`, `script`, `style`, `noscript`) + atributos ARIA (`role="banner"|"navigation"|"complementary"`). Solo `<main>` y `<article>` se preservan.
4. **URL canónica por sección**: extraída de `<link rel="canonical">` o construida como `base-url + path + #anchor-del-primer-h1`.
5. **Detección de versión**: `<meta name="product">` o `<meta name="version">` o regex en URL (`/v\d+\.\d+\.\d+/`).
6. **robots.txt** opcional: respeta `Disallow:` cuando `--respect-robots-txt`.
7. Sin ML, sin OCR. Sin descarga de URLs (wget se hace fuera).

Detalles y constantes: [`web-docs.md`](web-docs.md).
