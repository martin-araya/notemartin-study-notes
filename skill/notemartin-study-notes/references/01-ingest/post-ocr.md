# Corrección post-OCR — `references/01-ingest/post-ocr.md`

> Documento normativo de la Fase 27 del roadmap. Define cómo el script `scripts/ingest/post_ocr.py` aplica correcciones deterministas guiadas por reglas (R001-R010) y un diccionario técnico auditable sobre la salida de F22/F23/F24/F25. **Nunca** modifica código ni tablas. Cada corrección es rastreable e individualmente revertible.
>
> Documentos complementarios: `references/01-ingest/regions.md` (F22, provee `semantic_class` por región), `references/01-ingest/code-ocr.md` (F25, política de corrección forzada), `references/01-ingest/tables.md` (F23), `references/01-ingest/formulas.md` (F24), `references/01-ingest/confidence.md` (F26), `references/00-pipeline/architecture.md` §3.1 (L0 Ingesta), §5 (frontera de capa), §8 (modo degradado).

## Índice

1. [Propósito](#1-propósito) · 2. [Cuándo se aplica](#2-cuándo-aplica) · 3. [Catálogo de reglas (R001-R010)](#3-catálogo-de-reglas-r001-r010) · 4. [Diccionario técnico (formato YAML)](#4-diccionario-técnico-formato-yaml) · 5. [Regiones saltadas (código y tablas)](#5-regiones-saltadas-código-y-tablas) · 6. [Aplicación y revertibilidad](#6-aplicación-y-revertibilidad) · 7. [Audit log](#7-audit-log) · 8. [Forma de `post_ocr.json` y `post_ocr_summary.json`](#8-forma-de-post_ocrjson-y-post_ocr_summaryjson) · 9. [Cómo conectar con F31](#9-cómo-conectar-con-f31) · 10. [Anti-patrones](#10-anti-patrones) · 11. [Cómo verificar + cambios permitidos](#11-cómo-verificar--cambios-permitidos)

## 1. Propósito

Aplicar correcciones deterministas y rastreables a las regiones de prosa extraídas por F22/F23/F24/F25. **Nunca** usar modelos de lenguaje ni heurísticas de plausibilidad. Cada corrección está anclada a una regla explícita o a una entrada de diccionario técnico, y es individualmente revertible.

`scripts/ingest/post_ocr.py` produce, en `<out-dir>/ingest/post_ocr/`:

- `page-NNNN.post_ocr.json` — array de regiones con `original_text`, `corrected_text`, `corrections[]`.
- `post_ocr_summary.json` — global con conteo de correcciones, distribución por `rule_id`, `skipped_regions_count`, `revertible: true`.
- `audit_log.json` — registro de applies y reverts.

## 2. Cuándo se aplica

Tras F22 (regions). Es la última capa L0 antes de F31 (build_sdm). NO se ejecuta sobre código ni tablas; esas regiones se saltan intactas.

```
python3 scripts/ingest/post_ocr.py \
    --source <ingest_dir> --out-dir <dir> \
    [--dictionary <dictionary.yaml>] [--json-only]

# Revertir una corrección específica:
python3 scripts/ingest/post_ocr.py --source <dir> --out-dir <dir> --revert <correction_id>

# Revertir todas:
python3 scripts/ingest/post_ocr.py --source <dir> --out-dir <dir> --revert-all
```

## 3. Catálogo de reglas (R001-R010)

| ID | Regla | Acción | Aplica a | Whitelist |
|---|---|---|---|---|
| R001 | `(\S)\n(\S)` con espacios faltantes | Inserta espacio después de `\n` si la palabra siguiente NO comienza con mayúscula, dígito, `[`, `(`, `{`, `<`, o marcador de lista | prose | skip si inicia con `[`/`(`/`{`/`<`/dígito |
| R002 | `\n{3,}` | Colapsa a `\n\n` (separador de párrafo) | prose | — |
| R003 | Doble espacio `  ` (no dentro de indentación de ≥ 4 chars) | Colapsa a un solo espacio | prose | preserva si la línea tiene indent |
| R004 | Tab `\t` mezclado con espacios en la misma línea | Convierte tabs a N espacios donde N = siguiente columna (o 4 si no se detecta) | prose | preserva si toda la línea tiene solo tabs |
| R005 | Ligadura `ﬁ` (U+FB01) | Expande a `fi` | prose | skip si URL-like |
| R006 | Ligadura `ﬂ` (U+FB02) | Expande a `fl` | prose | skip si URL-like |
| R007 | Ligadura `ﬃ` (U+FB03) | Expande a `ffi` | prose | skip si URL-like |
| R008 | Ligadura `ﬄ` (U+FB04) | Expande a `ffl` | prose | skip si URL-like |
| R009 | `(\d+)\.\s+([A-Z][a-z]+)` (numeración incrustada) | Inserta `\n\n` después del número si la palabra siguiente es nombre propio | prose | skip si el número tiene más de 3 dígitos |
| R010 | Línea que comienza con `(N)` o `[N]` (referencia a ecuación/nota) | Marca como `footnote_marker: true` y separa en línea propia | prose | — |
| D001-D100 | Diccionario técnico `original → corrected` | Reemplazo exacto por entrada | prose, formula | — |

**Reglas para `formula`**: SOLO se aplican entradas del diccionario (D001-D100), NO las reglas R001-R010. Las reglas de whitespace/ligaduras podrían romper LaTeX.

## 4. Diccionario técnico (formato YAML)

`<out-dir>/ingest/post_ocr/dictionary.yaml` (opcional; si falta, F27 usa default):

```yaml
schema_version: "1.0.0"
entries:
  - id: D001
    original: "PostgresQL"
    corrected: "PostgreSQL"
    case_sensitive: true
    scope: prose
  - id: D002
    original: "Javascript"
    corrected: "JavaScript"
    case_sensitive: false
    scope: prose
  - id: D003
    original: "mySQL"
    corrected: "MySQL"
    case_sensitive: true
    scope: prose
  - id: D004
    original: "Typescript"
    corrected: "TypeScript"
    case_sensitive: true
    scope: prose
  - id: D005
    original: "k8s"
    corrected: "Kubernetes"
    case_sensitive: false
    scope: prose
```

**Default dictionary** (cuando no se pasa `--dictionary`): 5 entradas comunes (PostgreSQL, JavaScript, TypeScript, Python, mySQL).

Cada entrada tiene `id` único, `original`, `corrected`, `case_sensitive`, `scope`. F27 rechaza entradas con `original == corrected` o `id` duplicado.

## 5. Regiones saltadas (código y tablas)

Regla dura: F27 NO modifica regiones con `semantic_class` ∈ `{code, console, table, syntax_diagram}`. Cada región saltada se registra en la salida con `skipped: true` y `skip_reason: "code_or_table_intact"`.

Para `formula`: F27 aplica SOLO entradas del diccionario (no R001-R010) para preservar LaTeX.

Las regiones `text`, `heading`, `caption`, `figure_caption`, `index`, `editorial_note` reciben el tratamiento completo (reglas + diccionario).

## 6. Aplicación y revertibilidad

### Aplicación

Para cada región aplicable, F27:
1. Aplica R001-R010 en orden (cada corrección genera un `correction_id` único global).
2. Aplica el diccionario técnico (cada entry genera un `correction_id`).
3. Registra cada corrección en `corrections[]` con `correction_id`, `source` ∈ {`rule_id`, `dict_id`}, `char_pos`, `char_end`, `original`, `corrected`, `applied_at`.

### Revertibilidad

`--revert <correction_id>` invierte esa corrección específica:
- Encuentra la corrección por `correction_id`.
- Reemplaza `corrected` por `original` en la región.
- Registra la reversión en `audit_log`.

`--revert-all` revierte todas las correcciones del último run.

## 7. Audit log

`audit_log.json` registra todas las acciones (apply y revert) con timestamp y `correction_id`:

```jsonc
{
  "schema_version": "1.0.0",
  "entries": [
    {"action": "apply", "correction_id": "c-0001", "region_id": "r001", "rule_id": "R001", "applied_at": "..."},
    {"action": "apply", "correction_id": "c-0002", "region_id": "r001", "rule_id": "D001", "applied_at": "..."},
    {"action": "revert", "correction_id": "c-0001", "region_id": "r001", "applied_at": "..."}
  ]
}
```

Truncado a las últimas `MAX_AUDIT_LOG_ENTRIES = 1000` entradas.

## 8. Forma de `post_ocr.json` y `post_ocr_summary.json`

`post_ocr.json` por página:

```jsonc
{
  "page": 1,
  "regions": [
    {
      "id": "r001",
      "semantic_class": "text",
      "original_text": "PostgresQL is a SQL database.\n\nIt has many features.",
      "corrected_text": "PostgreSQL is a SQL database.\n\nIt has many features.",
      "corrections": [
        {
          "correction_id": "c-0001",
          "rule_id": null,
          "dict_id": "D001",
          "char_pos": 0,
          "char_end": 11,
          "original": "PostgresQL",
          "corrected": "PostgreSQL",
          "applied_at": "2026-09-24T..."
        }
      ],
      "skipped": false,
      "skip_reason": null
    }
  ]
}
```

`post_ocr_summary.json` global:

```jsonc
{
  "schema_version": "1.0.0",
  "source": {
    "ingest_dir": "...",
    "dictionary_path": "...",
    "hash": "..."
  },
  "total_regions": 24,
  "modified_regions": 18,
  "skipped_regions_count": 6,
  "rule_distribution": {
    "R001": 12, "R002": 3, "R005": 1, ...
  },
  "dict_distribution": {
    "D001": 4, "D002": 2, ...
  },
  "total_corrections": 17,
  "revertible": true,
  "warnings": [],
  "generated_at": "2026-09-24T..."
}
```

## 9. Cómo conectar con F31

F31 consume `post_ocr_summary.json` y los `text` corregidos (NO los `original_text`). Si `revertible == true`, F31 debe respetar las correcciones aplicadas.

## 10. Anti-patrones

- **No** usar modelos de lenguaje para adivinar contenido (criterio 1).
- **No** modificar regiones code/console/table/syntax_diagram (criterio 2).
- **No** omitir el `correction_id` único en ninguna corrección.
- **No** aceptar entradas de diccionario con `original == corrected`.
- **No** insertar espacio después de `\n` si la siguiente palabra comienza con `[`, `(`, `{`, `<`, o dígito.
- **No** expandir ligaduras en URLs (heurística: presencia de `://` o `.com`/`.org` en las 30 chars siguientes).
- **No** emitir corrección sin registrar en `audit_log`.
- **No** aplicar R001-R010 a regiones `formula` (solo diccionario para preservar LaTeX).

## 11. Cómo verificar + cambios permitidos

Cinco pasos:

1. ¿El input son `regions.json` + opcional `tables.json`/`formulas.json`/`code.json`?
2. ¿Cada corrección tiene `correction_id` único + `source` rule o dict?
3. ¿Las regiones code/table/syntax_diagram tienen `skipped: true`?
4. ¿`--revert <correction_id>` revierte solo esa corrección?
5. ¿El audit log persiste los applies y reverts?

```bash
python3 evals/post-ocr-sample/run_eval.py
# Esperado: "PASS los 3 criterios"
```

**Cambios permitidos sin reabrir Fase 27:**

- Añadir una nueva regla al catálogo (R011+) con ADR.
- Añadir una nueva entrada al diccionario default con ADR.
- Cambiar las constantes numéricas (`INDENT_PRESERVE_MIN`, etc.) con ADR.

**Reabren Fase 27:**

- Cambiar la regla dura "código y tablas intactas".
- Eliminar la revertibilidad individual.
- Cambiar el formato del `correction_id`.
- Eliminar el audit log.

## 12. Siguiente fase — `other_formats.py` (F28)

Tras F27 (post-ocr), F28 procesa formatos que no son PDF y los normaliza al contrato de F22:

1. F28 detecta el formato por extensión + magic bytes (EPUB/DOCX/PPTX/SRT/VTT/JSON).
2. **EPUB** (`ebooklib`): orden desde OPF spine, capítulos, imágenes, notas al pie (ITEM_NOTE=10).
3. **DOCX** (`python-docx`): estilos como `semantic_class` (`Heading 1` → `heading` con `level`, `Quote` → `editorial_note`, `Code` → `code`, etc.); comentarios, change tracking (`<w:ins>`/`<w:del>`), tablas nativas.
4. **PPTX** (`python-pptx`): 3 slides con `notes_slide.notes_text_frame` → `speaker_note` (criterio 2); grupos recursivos.
5. **Transcripciones** (SRT/VTT/JSON): muletillas fuera (whitelist `um/uh/er/ah/eh/mm/hmm/mm-hmm/uh-huh`) solo en pausas > `MIN_PAUSE_FOR_FILLER_REMOVAL_S = 2.0`. Marcas temporales conservadas como `anchor_id: "t-NNNN"` con `start`/`end` numéricos (criterio 3).
6. Cada formato emite `regions.json` compatible con F22. Regla dura: NO usa ML; NO modifica código (no aplica aquí, pero preserva estructura).

Detalles y constantes: [`other-formats.md`](other-formats.md).
