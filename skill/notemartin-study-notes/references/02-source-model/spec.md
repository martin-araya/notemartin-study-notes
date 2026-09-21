# SDM — Contrato del Source Document Model

> Documento normativo de la Fase 13 del roadmap. Define la jerarquía `documento → secciones → bloques` y los campos que cada bloque porta: `id` estable, `type`, `content`, `anchor`, `confidence` y `origin`. Schema JSON formal en [`schemas/sdm.schema.json`](../../../../schemas/sdm.schema.json).
>
> Documentos complementarios: `skills/AGENT.md` §13 (forma canónica del bloque — este doc la formaliza), `references/00-pipeline/architecture.md` §3.2 (contrato L1) y §6 (hash de fuente `sha256`), `references/04-authoring/notemark.md` §4 (cómo el SDM alimenta NoteMark).
>
> Enrutado desde N2: `docs/skill-anatomy.md` §6 fila `F13`.

## §1 · Propósito y alcance

El SDM es la **representación intermedia de la fuente**, independiente del formato original (PDF, HTML, EPUB, DOCX, PPTX, TXT, MD, repo, transcripción). El agente construye el SDM en L1; L2 lo consume para extraer unidades; L3 lo consulta como `source_refs` en el IR; L4 lo usa para localizar imágenes y assets.

Lo que el SDM **es**: la fuente estructurada, con anclas estables que sobreviven a renumeraciones y a cambios de formato. Lo que el SDM **no es**: el Note IR (F14) ni NoteMark (F12). SDM es la materia prima; IR y NoteMark son interpretaciones.

## §2 · Cuándo se aplica

- L1 construyendo el SDM por primera vez sobre una fuente.
- L2 consultando anclas (`source_refs`) al mapear unidades a bloques.
- L3 cuando el agente redacta y necesita ligar una frase a su bloque origen.
- L4 cuando un renderer necesita la imagen o el activo de un bloque.

**No se aplica a:** notas en sí (L3 produce IR y NoteMark, no SDM), ni a la ingesta cruda (L0 produce regiones, no bloques SDM).

## §3 · Modelo de tres niveles

```
sdm.json
├── source          ← metadatos del documento (vendor, hash, idioma, …)
├── sections[]      ← una entrada por sección canónica
│   ├── section_path  (e.g. "/ch02/intro" o "§2.1")
│   ├── title
│   └── blocks[]    ← bloques de la sección, en orden de aparición
│       ├── id
│       ├── type
│       ├── content (forma según type)
│       ├── anchor
│       ├── confidence
│       └── origin
```

Cada bloque vive dentro de **una** sección. Los `block_index` se cuentan por sección empezando en 0. Una sección sin bloques es inválida (`minItems: 1` en el schema).

## §4 · Bloque — campos

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string (12 hex) | `sha1(source.hash + section_path + str(block_index))[:12]`. Determinista. Ver §8. |
| `type` | enum (16) | Tipo de bloque; ver tabla abajo. |
| `content` | shape | Forma según `type`. Ver tabla abajo. |
| `anchor` | object | Ancla resoluble. Ver §5. |
| `confidence` | number [0, 1] | Certeza de la extracción. Ver §6. |
| `origin` | enum | `native` / `ocr` / `reconstructed`. Ver §6. |

### 4.1 Tipos de bloque y forma de `content`

| `type` | `content` | Notas |
|---|---|---|
| `prose` | string | Párrafo de texto corrido. |
| `heading` | `{ level: 1-6, text: string }` | Encabezado; `level` es la profundidad Markdown. |
| `list` | `{ ordered: bool, items: [string] }` | Lista; `ordered=true` para numerada. |
| `table` | `{ headers: [string], rows: [[string]] }` | Tabla; `headers` puede ser `[]` para tablas sin encabezado. |
| `code` | `{ lang: string, text: string }` | Bloque de código; `lang` puede ser `""` si desconocida. |
| `console` | `{ lines: [string] }` | Sesión CLI; cada línea puede llevar prompt. |
| `formula` | `{ latex: string, display: bool }` | Fórmula; `display=true` para bloque, `false` para inline. |
| `figure` | `{ src: string, alt: string, caption?: string }` | Imagen; `src` es ruta relativa dentro del workdir. |
| `caption` | string | Texto de pie de figura/tabla separado. |
| `note` | `{ text: string, severity?: "info"\|"tip" }` | Caja editorial "Nota" del documento. |
| `warning` | `{ text: string }` | Caja editorial "Advertencia". |
| `example` | `{ text: string }` | Caja editorial "Ejemplo". |
| `syntax-diagram` | `{ notation: "railroad"\|"ebnf", text: string }` | Diagrama de sintaxis (EBNF, railroad). |
| `footnote` | `{ text: string, ref: string }` | Nota al pie; `ref` es el marcador en el cuerpo. |
| `toc` | `{ entries: [{ label: string, page: integer\|null, anchor: string }] }` | Tabla de contenido. |
| `boilerplate` | string | Texto repetitivo (licencias, headers, footers) que se omite en L3. |

## §5 · Ancla (`anchor`)

El ancla es **obligatoria** y hace el bloque resoluble en la fuente original.

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `page` | integer ≥ 1 o null | sí | Página 1-based; `null` si la fuente no está paginada (HTML, EPUB). |
| `section_path` | string | sí | Mismo valor que el de la sección padre (redundancia explícita para que el bloque sea autosuficiente). |
| `bbox` | [x, y, w, h] o null | no | Bounding box en píxeles; `null` si la fuente no tiene coordenadas (HTML). |
| `char_range` | [start, end] o null | no | Rango de caracteres en el texto extraído de la página; útil para resaltar sin recalcular OCR. |

**Regla dura:** `page` o `section_path` faltantes invalidan el bloque (criterio 3). El validador (`scripts/util/validate_sdm.py`) confirma presencia.

## §6 · Confianza y origen

`origin` declara de dónde viene el bloque; `confidence` cuán fiable es.

| `origin` | `confidence` | Significado |
|---|---|---|
| `native` | siempre `1.0` | Extraído del texto nativo del formato (PDF con capa de texto, HTML, Markdown). Sin incertidumbre. |
| `ocr` | `0 < confidence < 1.0` | Reconocido por OCR; `confidence` viene del motor (palabra o bloque). |
| `reconstructed` | declarado por el agente | Reconstruido por el agente cuando la fuente está dañada (página en blanco, escaneo torcido). El agente fija el valor con justificación. |

**Regla dura:** un bloque con `origin: "ocr"` debe llevar `confidence < 1.0` (criterio 4). La inversa no se exige: un bloque `native` siempre lleva `1.0`; el validador lo verifica.

## §7 · Metadatos del documento (`source`)

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `id` | string | sí | Identificador único (e.g. `01-postgresql-chapter`). |
| `hash` | string (sha256 hex 64) | sí | Hash del archivo fuente, codificado en hexadecimal minúscula (architecture.md §6). |
| `algorithm` | enum: `sha256` | no | Algoritmo de hash; default `sha256`. |
| `vendor` | string | sí | Fabricante / editorial (e.g. `PostgreSQL Global Development Group`). |
| `product` | string | sí | Producto documentado (e.g. `PostgreSQL 16`). |
| `version` | string \| null | no | Versión del producto; `null` si no declarada (INV-17). |
| `edition` | string \| null | no | Edición (`Community`, `Enterprise`); `null` si no aplica. |
| `authors` | array[string] | no | Autores explícitos; vacío si anónimo. |
| `isbn` | string \| null | no | ISBN o part number del fabricante. |
| `url` | string (URI) | sí | URL canónica de la fuente. |
| `language` | string (BCP-47) | sí | Código de idioma. |
| `date` | date (ISO 8601) \| null | no | Fecha de la fuente; `null` si desconocida. |
| `format` | enum | sí | `pdf` / `html` / `epub` / `docx` / `pptx` / `txt` / `md` / `repo` / `transcript`. |

## §8 · Generación de ids

Fórmula exacta:

```
id = sha1(source.hash + section_path + str(block_index))[:12]
```

- Concatenación de strings sin separador.
- `source.hash` es el sha256 hex declarado en `source.hash` (64 chars).
- `section_path` es el `section_path` de la sección que contiene el bloque.
- `block_index` es el índice 0-based del bloque dentro de la sección.
- El id son los **primeros 12 caracteres hex** del digest (no 8, no 16 — 12).

Ejemplo reproducible:

```bash
python3 scripts/util/validate_sdm.py --id \
  a8f4ce1405802cacbb35e6fb88f5e3cf138a4e872910cdfd276f378f13371657 \
  /ch02/intro 0
```

**Regla dura:** los ids son sensibles a la **posición estructural**, no a la numeración impresa (que puede ser inconsistente). Renumerar el documento **no cambia los ids** si las posiciones estructurales son las mismas. Mover un bloque de sección **sí cambia su id** porque cambia `section_path` y posiblemente `block_index`. La consecuencia práctica: notas redactadas que citan `{src:blk_xxxx}` se invalidan si el bloque origen se mueve; el ledger (F15) detecta la ruptura.

## §9 · SDM mínimo válido

Once líneas, un bloque. Ejemplo PostgreSQL:

```json
{
  "schema_version": "1.0.0",
  "source": {
    "id": "01-postgresql-chapter",
    "hash": "a8f4ce1405802cacbb35e6fb88f5e3cf138a4e872910cdfd276f378f13371657",
    "vendor": "PostgreSQL Global Development Group",
    "product": "PostgreSQL 16",
    "url": "https://www.postgresql.org/docs/16/sql.html",
    "language": "en",
    "format": "html"
  },
  "sections": [{
    "section_path": "/ch02/intro",
    "blocks": [{
      "id": "<sha1 del hash + path + '0', primeros 12 hex>",
      "type": "prose",
      "content": "This chapter describes the SQL language...",
      "anchor": { "page": 1, "section_path": "/ch02/intro" },
      "confidence": 1.0,
      "origin": "native"
    }]
  }]
}
```

El id se calcula con el comando `--id` del script de validación.

## §10 · Anti-patrones

- `id` que no sea hex de 12 chars (e.g. UUID completo, hash truncado a 8) — invalida el contrato.
- Bloque sin `anchor` o `anchor` sin `page`/`section_path` — invalida el bloque (criterio 3).
- Bloque `origin: "ocr"` con `confidence = 1.0` — viola criterio 4.
- Bloque `origin: "native"` con `confidence < 1.0` — incoherente (debería ser ocr).
- `section` sin bloques — el schema lo rechaza (`minItems: 1`).
- IDs no deterministas (random UUIDs, timestamps) — imposibilita reproducir notas entre sesiones.
- `source.hash` que no sea sha256 hex 64 — viola architecture.md §6.

## §11 · Cómo verificar

Comandos grepeables:

1. `python3 -c "import json; json.load(open('schemas/sdm.schema.json'))"` → OK (sintaxis).
2. `python3 scripts/util/validate_sdm.py --validate evals/sdm-sample/*.json` → 15 `OK`, exit 0.
3. `python3 scripts/util/validate_sdm.py --id <hash> <path> <idx>` → imprime id; dos ejecuciones idénticas.
4. `wc -l references/02-source-model/spec.md` → ≤ 300.
5. `rg -c '^## §' references/02-source-model/spec.md` → 11 secciones.
6. Cada bloque en cada SDM tiene `anchor.page` y `anchor.section_path` (script lo verifica).
7. Bloques `origin: "ocr"` tienen `confidence < 1.0` (script lo verifica).

## §12 · Cambios permitidos sin reabrir F13

- Añadir un campo opcional a `source` (cambio menor de versión).
- Ampliar el enum `format` con un nuevo formato (versión menor si backwards-compat).
- Reorganizar secciones sin cambiar `section_path` (los ids no cambian).

**Reabren F13:** cambiar la fórmula del id, añadir un nuevo tipo de bloque obligatorio, mover `page`/`section_path` a opcional, eliminar la distinción `origin = ocr`, permitir `confidence > 1.0`.
