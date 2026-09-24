# Build SDM — Contrato de `scripts/ingest/build_sdm.py`

> Documento normativo de la **Fase 31** del roadmap. Ensambla la salida de F17-F30 en un `sdm.json` conforme a `schemas/sdm.schema.json` (F13). Genera ids deterministas, asocia pies a figuras y preserva referencias de footnotes. Núcleo del pipeline: sin SDM no hay L2/L3.
>
> Documentos complementarios: `references/02-source-model/spec.md` (F13, el contrato del SDM que este script produce), `references/01-ingest/*.md` (los ingestores cuyas salidas consume), `references/00-pipeline/architecture.md` §3.2 (L1 ensambla el SDM), `references/00-pipeline/responsibilities.md` (tabla normativa "Lo hace un script").

## §1 · Propósito y alcance

`build_sdm.py` cierra la transición **L0 → L1**. Recibe los artefactos JSON producidos por `triage.py` (F17), `pdf_native.py` (F18), `ocr.py` (F20), `layout.py` (F21), `regions.py` (F22), `tables.py` (F23), `formulas.py` (F24), `code_ocr.py` (F25), `post_ocr.py` (F27), `other_formats.py` (F28), `web_docs.py` (F29) y, opcionalmente, `review_report.py` (F26); y emite un único `sdm.json` que:

1. cumple el JSON Schema `sdm.schema.json` (criterio 1 de la fase);
2. produce ids estables entre ejecuciones sobre los mismos inputs (criterio 2);
3. asocia cada `figure` con su pie cuando el pie existe en la fuente (criterio 3).

**No es**: un conversor de IR (F14), un parser de NoteMark (F48) ni un validador de completitud (F43). Tampoco decide qué unidades de información extraer (F37) ni escribe notas (F12).

## §2 · Cuándo se aplica

- Tras cerrar L0 sobre una fuente con `ingest_check.py` (F30) en exit 0 o 2 (o con override humano aplicado).
- Antes de cualquier consulta que necesite anclas, cobertura, o referencia cruzada (L2 onward, F37-F40).
- En re-render o migración entre destinos: si el SDM ya existe, este script **no** se vuelve a ejecutar.

**No se aplica** a: notas en sí (F12/F14), IR (F14), políticas editoriales (F34/F35) ni documentos sin ingesta (se aborta con exit 1).

## §3 · Entradas por formato

| Formato | Detectado por presencia de | `regions.json` viene de |
|---|---|---|
| `pdf` | `regions/page-NNNN.regions.json` o `fragments.json` | F22 (sobre F18/F20) |
| `html` | `web_docs/sections.json` | F29 (no usa F22; lee `text` + `headings`) |
| `epub` / `docx` / `pptx` | `other_formats/<basename>.<fmt>.regions.json` | F28 |
| `transcript` (srt/vtt/json) | `other_formats/*.regions.json` con `semantic_class` apropiado | F28 |
| `repo` (Markdown) | F29B futuro o F28 si el script lo reconoce | — |

El script acepta `--format {auto,pdf,html,epub,docx,pptx,transcript,repo}`. Con `auto` se infiere del primer artefacto presente según el orden anterior. Los flags `--check-determinism` y `--json-only` modifican el modo sin cambiar la entrada.

## §4 · Tabla de mapeo `semantic_class` (F22) → `type` SDM (F13)

| F22 `semantic_class` | SDM `type` | Forma de `content` | Origen confianza |
|---|---|---|---|
| `text` (no ambiguo) | `prose` | string (texto corrido) | `1.0` / `native` |
| `text` ambiguo (`semantic_class=null` o `class_confidence < 0.45`) | `prose` | string; `confidence = class_confidence` | forzado a `prose` (D8) |
| `heading` | `heading` | `{level:int 1-6, text:string}` | tipografía (F22 S_LARGE+S_BOLD) |
| `table` | `table` | `{headers:[string], rows:[[string]]}` desde F23 | F23; fallback geométrico si falta F23 |
| `code` | `code` | `{lang:string, text:string}` desde F25 | F25 |
| `console` | `console` | `{lines:[string]}` desde F25 | F25 |
| `formula` | `formula` | `{latex:string, display:bool}` desde F24 | F24 |
| `figure` | `figure` | `{src, alt, caption?}` (caption se llena en §6) | F22 / F33 (cuando exista) |
| `capture` o `text` con patrón `^(Figure|Fig\.|Tabla|Tab\.) N` | `caption` | string (texto del pie) | F22 sub_kind |
| `editorial_note` (`sub_kind="box"` con "warning" en texto) | `warning` | `{text}` | semántica editorial |
| `editorial_note` (resto) | `note` | `{text, severity:"info"\|"tip"}` | semántica editorial |
| `syntax_diagram` | `syntax-diagram` | `{notation:"railroad"\|"ebnf", text}` | patrón de glifos (F22) |
| `diagram` (no `syntax_diagram`) | descartado | — | warning `unmapped_diagram` |
| `footer` | descartado | — | boilerplate (cuenta en `boilerplate_discarded`) |
| `index` (sin formato `1.2 Title`) | descartado | — | warning |
| `index` (formato jerárquico) | `toc` | `{entries:[{label, page, anchor}]}` | estructura |
| `footnote` | `footnote` | `{text, ref}` (`ref` rellenada por §7) | estructura EPUB/DOCX (F28) |

## §5 · Ensamblado de secciones

**PDF.** Se lee `fragments.json.outline` (F18 §6). Cada item del outline aporta `section_path`. Si no hay outline, se construye por fallback de headings (F18 §6.2). Los bloques sin section resuelta caen en `/uncategorized` con warning.

**HTML.** Se usa `web_docs/sections.json` (F29). Cada entrada produce una sección SDM con `section_path = /<slug>` derivado de `url_path`. Los headings 1-6 detectados por F29 se traducen a bloques `heading`. El cuerpo textual se fragmenta por párrafos (`\n{2,}`) como bloques `prose`.

**EPUB / DOCX / PPTX.** Se usa `other_formats/<basename>.<fmt>.regions.json` (F28). Las regiones se agrupan por `chapter` (EPUB) o `slide` (PPTX) en secciones discretas; DOCX cae todo en una sección salvo que F28 emita `heading` bloques.

**Transcript.** Se agrupa en una sola sección; cada bloque lleva `anchor.page=null` y `anchor.bbox=null`.

**Repo / Markdown.** Una única sección `"/readme"`. Pendiente de materializar el ingestor específico (no hay script para Markdown aún; ver F29B futuro).

## §6 · Asociación figura↔pie

Para cada bloque `type=figure`:

1. Se recorre el resto de bloques de la **misma sección** (`section_path`) en orden de aparición.
2. El primer bloque `type=caption` cuyo texto case `^(Figure|Fig\.|Tabla|Tab\.) N` y cuyo `anchor.page` esté dentro de `CAPTION_MAX_PAGES_AHEAD=1` página de la figura es su pie candidato.
3. Si hay match, el texto del pie se copia a `figure.content.caption`; el caption se conserva **además** como bloque propio `type=caption` (per spec §4.1: ambas formas son legales — figura con `caption` y bloque `caption` separado coexisten en los SDMs canónicos).
4. Si no hay match, se registra `warnings[]` con `{page, figure_block_id, reason:"caption_not_found"}` y se sigue.
5. Captions huérfanos (sin figura previa) se emiten como bloque `caption` propio y cuentan en `captions_orphan`.

Constante: `CAPTION_MAX_PAGES_AHEAD = 1`. Una figura cuya pie está dos o más páginas adelante **no** se asocia.

## §7 · Footnotes y referencia

`build_sdm.py` **no resuelve** qué bloque de prosa apunta al footnote (esa resolución es trabajo del agente en L2). Sí garantiza:

- Cada bloque `type=footnote` lleva `content.ref` no vacío. Si la fuente (EPUB) lo trae (F28 ya emite `anchor` por `ITEM_NOTE`), se preserva literal.
- Si `content.ref` está vacío, se sintetiza como `"<page>:<N>"` donde `N` es el ordinal del footnote dentro del documento (1, 2, 3, …) y `<page>` es el `anchor.page` o `"src"`.
- El footnote queda en la sección del bloque que lo rodea (F28 ya emite `anchor_para_id` para EPUB; en PDF se infiere por contigüidad de página).

## §8 · Ids deterministas

Fórmula:

```
id = sha1(source.hash + section_path + str(block_index))[:12]
```

- `source.hash` es sha256 hex del archivo fuente (architecture §6).
- `section_path` es el path canónico de la sección padre.
- `block_index` es 0-based dentro de la sección, en el orden final de los bloques.
- Se concatenan sin separador; el resultado son los 12 primeros caracteres hex del digest.

La función `compute_block_id` aquí y la de `scripts/util/validate_sdm.py` (F13) son idénticas byte a byte. Un test en `evals/build-sdm-sample/run_eval.py` verifica esa paridad sobre 1000 ids.

## §9 · Confianza y origen

| Condición de origen | `confidence` (salida) | `origin` (salida) |
|---|---|---|
| Bloque F22 nativo `class_confidence ≥ 0.85` | `1.0` | `native` |
| Bloque F22 nativo `class_confidence < 0.85` o ambiguo | `class_confidence` | `reconstructed` |
| Bloque originado de OCR (F19+F20) | `ocr_summary.retries[].resulting_mean_conf` (media) | `ocr` |
| Bloque F25 con `low_confidence=true` | `< 0.70` | preserva `origin` |

Regla dura (validate_sdm.py la enforza): si `origin == "ocr"` entonces `confidence < 1.0`. El script nunca emite un bloque ocr con `confidence = 1.0`.

## §10 · Validación final

Tras escribir `sdm.json`, el script invoca como subproceso `scripts/util/validate_sdm.py --validate <path>`. Ese script:

1. ejecuta `jsonschema.Draft202012Validator` contra `sdm.schema.json`;
2. recomputa cada id con `compute_block_id` y compara con el declarado;
3. verifica que cada bloque tiene `anchor.page` y `anchor.section_path`;
4. verifica la regla `ocr ⇒ confidence < 1.0` y `native ⇒ confidence = 1.0`.

Si la validación falla, `build_sdm.py` devuelve exit 1 y muestra el detalle completo en stderr. Si pasa, devuelve exit 0 o 2 (según haya warnings).

## §11 · Anti-patrones

- **Editar `sdm.json` a mano** para arreglar un bloque que el script no asoció bien → invalida el contrato de L1 y rompe la trazabilidad. La corrección correcta es ajustar el ingestor (F22-F25) o alimentar al agente con override explícito.
- **Llamar a `build_sdm.py` con un `source.hash` inventado** para reutilizar ids entre fuentes distintas → los ids colisionan y el ledger (F15) reporta cobertura cruzada falsa.
- **Cambiar la fórmula del id en `build_sdm.py`** sin actualizar `validate_sdm.py` (F13) → los dos divergen y la validación de criterio 2 falla.
- **Confiar en `content.caption` para resolver la asociación** sin emitir el bloque `caption` separado → los renders que consultan el caption como bloque (`obsidian`, `notion`) pierden el texto.

## §12 · Cómo verificar

Comandos grepeables:

1. `python3 scripts/ingest/build_sdm.py --help` → imprime uso completo.
2. `python3 -c "import json; json.load(open('schemas/sdm.schema.json'))"` → OK sintaxis schema.
3. `python3 evals/build-sdm-sample/run_eval.py` → imprime `PASS los 3 criterios` o lista de fallos.
4. `python3 scripts/util/validate_sdm.py --validate evals/build-sdm-sample/build/*/sdm.json` → exit 0 con `OK — <path>` por archivo.
5. `wc -l references/02-source-model/build-sdm.md` → ≤ 400 (al cierre de la fase).

## §13 · Cambios permitidos sin reabrir F31

- Ampliar la tabla de mapeo §4 con nuevas clases semánticas (cambio menor de versión).
- Cambiar `CAPTION_MAX_PAGES_AHEAD` (constante inline).
- Añadir campos opcionales a `meta` del `--source-meta` YAML.

**Reabren F31:** cambiar la fórmula del id, mover el `caption` al figure quitando el bloque separado, alterar `CAPTION_PATTERN` a algo que case captions con números distintos (`Figure 1.A` vs `Fig. 1`).
