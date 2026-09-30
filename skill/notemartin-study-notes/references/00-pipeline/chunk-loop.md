# `references/00-pipeline/chunk-loop.md` — Bucle por chunks y presupuesto de contexto

> Documento normativo de la **Fase 107**. Define el **bucle por chunks**:
> fragmentación del SDM en chunks acotados, ciclo de **6 etapas** con
> **presupuesto acotado** de archivos cargados por etapa, manejo de
> unidades cruzadas entre chunks, y contrato de stop/resume con escritura
> atómica.
>
> F107 **NO redefine** F12/F13/F15/F31/F48; prescribe el orden de
> invocación y el presupuesto. Se compone con **F106 book-mode**:
> F106 orquesta por capítulo; F107 opera por chunk dentro del capítulo o
> standalone para fuentes no-libro.
>
> Documentos complementarios:
> - `references/00-pipeline/architecture.md` (F4) — capas L0-L4 + §3.7 modo chunk
> - `references/00-pipeline/book-mode.md` (F106) — orquestador por capítulo
> - `skill/notemartin-study-notes/scripts/pipeline/chunk_loop.py` — implementa esta spec
>
> Enrutado desde SKILL.md §5.2.

## Índice

1. [Propósito](#1-propósito) · 2. [Cuándo aplica](#2-cuándo-aplica) · 3. [El ciclo de 6 etapas y presupuesto](#3-el-ciclo-de-6-etapas-y-presupuesto) · 4. [Definición de chunk](#4-definición-de-chunk) · 5. [Estado compartido — chunk-state.json](#5-estado-compartido--chunk-statejson) · 6. [Procesamiento por chunk](#6-procesamiento-por-chunk) · 7. [Reglas de frontera de chunk](#7-reglas-de-frontera-de-chunk) · 8. [Composición con F106](#8-composición-con-f106) · 9. [Wirings cerrados](#9-wirings-cerrados) · 10. [Anti-patrones](#10-anti-patrones) · 11. [Verificación al cierre](#11-verificación-al-cierre)

---

## 1. Propósito

F107 introduce el **bucle por chunks** como el patrón canónico de
procesamiento para fuentes cuyo SDM es demasiado grande para cargar en
contexto de una sola vez. Cada chunk es una **ventana acotada** sobre el
SDM identificada por `anchor.section_path` (o por rango de bloques); el
agente procesa un chunk a la vez siguiendo el ciclo de **6 etapas** con un
**presupuesto acotado** de archivos cargados por etapa. Las unidades que
cruzan la frontera entre dos chunks se documentan **una vez** en una sola
nota (no se duplican).

**Cierra los 3 criterios del ROADMAP** §1755-1759:

1. _Ninguna etapa requiere más de un número acotado de referencias_ → §3 (tabla presupuesto) + §11 V1.
2. _Una unidad que cruza dos chunks se documenta una vez y completa_ → §7 + §10 AP-CHK1 + §11 V2.
3. _Una fuente de 200+ páginas se procesa sin tenerla entera en contexto_ → §6 (modo `--audit-loads`) + §10 AP-CHK2 + §11 V3.

**Fuera de alcance:**

- Orquestación por-capítulo del pipeline (eso es F106).
- Substituir a F31 (`build_sdm`); F107 consume el SDM ya construido.
- Detección automática de cuándo un corpus requiere chunks (decisión opt-in
  del agente o el usuario; default para SDMs > 30 bloques).

---

## 2. Cuándo aplica

El modo chunk **se activa opcionalmente** cuando se cumple **alguna** de las
siguientes condiciones:

- El SDM tiene **≥ 30 bloques** (umbral configurable).
- La fuente tiene **≥ 50 páginas** impresas (equivalente a ~30 bloques densos).
- El agente o el usuario lo solicita explícitamente vía `init`.

**Excepciones explícitas** (caer al pipeline L1-L4 estándar, NO activar modo chunk):

- Corpus con SDM < 30 bloques (no aporta nada fragmentar).
- Corpus procesado en modo obra (F106) si el agente prefiere fragmentar por
  capítulo en su lugar (F106 §3 cubre la fragmentación lógica).

**Activación**: el usuario o el agente decide invocar
`chunk_loop.py init --sdm <sdm.json> --workdir <workdir>`. Si el SDM no
tiene bloques, `init` falla con `CHUNK_NO_SDM` (exit 2) y el modo chunk no
se activa.

---

## 3. El ciclo de 6 etapas y presupuesto

Cada chunk se procesa siguiendo un **ciclo cerrado de 6 etapas**:

```
leer(chunk_i) → inventariar → ledger → NoteMark → validar → manifiesto
        ↑                                                       │
        └───────────────────────────────────────────────────────┘
```

Con **presupuesto acotado por etapa** (tabla cerrada, contenido normativo):

| Etapa | Archivos a cargar (acotado) | Archivos a NO cargar | `max_files_loaded` |
|---|---|---|---|
| `leer` | `sdm.json` (filtrado a chunk_i ± neighbor_window), `chunk-state.json`, `profile.yaml` | `ingest/ocr/*`, `ingest/pages/*`, `ingest/regions.json` completo | 4 |
| `inventariar` | `sdm.json` (chunk_i), `chunk-state.json`, `notes/<unit>.md` solo si la unidad ya fue escrita | resto | 3 |
| `ledger` | `knowledge/ledger.json`, `sdm.json` (chunk_i), `chunk-state.json` | `ingest/*`, `notemark/*`, `ir/*` | 4 |
| `NoteMark` | `knowledge/note-plan.json`, `references/04-authoring/notemark.md`, `references/05-note-types/<type>.md` (1), `sdm.json` (chunk_i) | resto | 4 |
| `validar` | `ir/<note>.json` (1 nota), `schemas/note-ir.schema.json`, `scripts/validate/validate_ir.py` | resto | 3 |
| `manifiesto` | `manifest.json`, `chunk-state.json`, `ir/<note>.json` (1 nota) | `knowledge/glossary.json` completo (solo diff) | 3 |

**Reglas duras:**

- **CHK-R1** — Cualquier intento de cargar un archivo fuera de esta tabla
  viola el presupuesto y dispara **AP-CHK3**. Verificable en
  `chunk_loop.py check --budget`.
- **CHK-R2** — El texto crudo de la fuente NUNCA se abre fuera de L0
  (F18/F20); la verificación algorítmica se hace en `check --audit-loads`
  y dispara **AP-CHK2**. El log se registra con
  `--audit-loads <log.jsonl>` durante `walk`.

---

## 4. Definición de chunk

Un **chunk** es una ventana contigua sobre el SDM. El script soporta **3
estrategias** mutuamente excluyentes (`config.chunk_strategy`):

| Estrategia | Descripción | Default `chunk_size` |
|---|---|---|
| `by_blocks` | Cada chunk cubre N bloques consecutivos del SDM | 30 |
| `by_chapter` | Cada chunk agrupa N capítulos (heading level==1) | 3 |
| `by_section_path` | Cada chunk es una rama del `section_path` (primer nivel) | (no aplica) |

**Vecindad** (`config.neighbor_window`): el script carga siempre el chunk
actual + `neighbor_window` chunks previos y siguientes para resolver
referencias cruzadas. **Default 1** = 3 chunks en memoria simultáneamente
(≈ 90 bloques en `by_blocks`). Configurable hasta 0 (estricto, solo el
chunk actual).

**Decisión por defecto** (recomendada): `by_blocks` con `chunk_size=30` y
`neighbor_window=1`. Rationale: 30 bloques × ~50 tokens/bloque ≈ 1500
tokens por chunk; 3 chunks (current + 2 vecinos) ≈ 4500 tokens — cabe
holgadamente en el contexto del agente.

---

## 5. Estado compartido — `chunk-state.json`

El estado del modo chunk vive en `<workdir>/chunk-state.json` y sigue el
schema `schemas/chunk-state.schema.json` (Draft 2020-12,
`additionalProperties: false` estricto). Estructura de alto nivel:

| Campo | Tipo | Significado |
|---|---|---|
| `schema_version` | const `"1.0.0"` | Versión del schema. |
| `source_hash` | hex 64 | SHA-256 de la fuente cruda. |
| `chunk_strategy` | enum | Estrategia de fragmentación. |
| `chunks[]` | array | Estado por chunk (ver §6). |
| `cross_chunk_units[]` | array | Unidades con `source_block_ids[]` que abarca ≥ 2 chunks (CHK-R3). |
| `current_chunk_id` | id? | Cursor de procesamiento. |
| `config` | objeto | `chunk_strategy` + `chunk_size` + `neighbor_window` + `strict_no_full_load`. |
| `created_at` / `updated_at` | ISO 8601 UTC | Tiempos de creación/última mutación. |

### Reglas duras de mutación (CHK-R1..CHK-R5)

- **CHK-R1** — `chunks[i].status ∈ {pending, processing, done, failed}` (enum
  cerrado; el schema lo enforza).
- **CHK-R2** — Escritura atómica: toda mutación escribe el archivo completo
  vía `_atomic_write_json` (tempfile + `Path.replace`); antes de la
  escritura, si el archivo existe, se copia a `.bak` (AP-CHK3).
- **CHK-R3** — Una unidad con `source_block_ids[]` que abarca ≥ 2 chunks se
  asigna al chunk primario (el primero que vio el bloque más temprano).
  Política **first-seen wins**.
- **CHK-R4** — Los chunks secundarios donde aparece la unidad se registran
  en `cross_chunk_units[].secondary_chunks[]`; el script NUNCA crea una
  segunda nota para esa unidad (AP-CHK1 lo detecta).
- **CHK-R5** — Al transicionar a `done`, `chunks[i].processed_at` se
  rellena con ISO 8601 UTC; `started_at` se sella. Re-procesar con
  `--force` copia `processed_at` a `previous_processed_at` antes de
  sobreescribir (AP-CHK4).

---

## 6. Procesamiento por chunk

Sub-comando `walk --chunk chkNN [--force] [--audit-loads <log.jsonl>] [--notes id1,id2]`.

Pasos por chunk:

1. Cargar `ChunkState` desde `<workdir>/chunk-state.json`.
2. Validar que el chunk existe y no está `done` (a menos que `--force`).
3. Si `--force` y `status == "done"`: copiar `processed_at` a
   `previous_processed_at` (CHK-R5 + AP-CHK4).
4. Activar el log de auditoría si `--audit-loads` se especifica (CHK-R2).
5. Transicionar a `status == "processing"`, sellar `started_at` con ISO
   8601 UTC; actualizar `current_chunk_id` (CHK-R1).
6. Ejecutar el ciclo de las **6 etapas** sobre el rango del chunk (leer →
   inventariar → ledger → NoteMark → validar → manifiesto); cada etapa
   respeta su `max_files_loaded` (tabla §3).
7. Detectar unidades cruzadas: si una unidad aparece en el chunk actual Y
   en otro chunk (previamente procesado o por procesar), registrarla en
   `cross_chunk_units[]` con `primary_chunk` = el chunk primario ya
   existente; NO crear nueva nota (CHK-R4).
8. Al cerrar, `state.mark_done(chunk_id, units, notes)` + save.
9. Emitir hint si quedan chunks pendientes (`next_chunk()` no nulo).

**Idempotencia**: si `status == "done"` y no se pasa `--force`, `walk`
falla con `CHUNK_ALREADY_DONE` (exit 1). El chunk NO se re-procesa.

---

## 7. Reglas de frontera de chunk

- **CHK-R3** — Una unidad con `source_block_ids[]` que abarca ≥ 2 chunks
  se asigna al chunk primario (el primero donde aparece el bloque más
  temprano).
- **CHK-R4** — Los chunks secundarios se registran en
  `cross_chunk_units[].secondary_chunks[]`; el script NUNCA crea una
  segunda nota para esa unidad (**AP-CHK1** lo detecta).
- **CHK-R5** — El cierre de un chunk depende de que TODAS sus unidades
  primarias estén `merged` o `discarded` (terminal en el ledger F15/F38).

**Política first-seen wins** (consistente con F106 §5): el primer chunk
que descubre la unidad fija su `primary_chunk`. Los chunks posteriores
que la redescubren solo la **referencian** en `secondary_chunks[]`; el
script NO crea segunda nota.

**Detección de redefinición cruzada (AP-CHK1)**: `check` verifica que
`cross_chunk_units[].note_id` es UNIQUE en el array. Si dos entradas
comparten el mismo `note_id`, hay duplicación.

---

## 8. Composición con F106

Cuando F106 (modo obra) y F107 (modo chunk) están activos
simultáneamente:

- F106 orquesta por capítulo; por cada capítulo `chNN`, F107 inicia un
  sub-loop `chunk_loop.walk` con `strategy: "by_blocks"` y `chunk_size`
  recargado de `profile.yaml::chunk_loop`.
- El `chunk-state.json` se anida bajo
  `<workdir>/chapters/<chNN>/chunk-state.json` (sub-workdir por
  capítulo); el padre es `book-state.json` de F106.
- El manifiesto final agrega `published_notes[]` de todos los sub-chunks;
  F106 §6 hace el merge.

**Standalone**: cuando NO hay F106 (fuentes no-libro), F107 opera en
`<workdir>/chunk-state.json` directamente (lo que produce la presente
implementación; la composición con F106 es trivial porque F107 expone la
misma API `ChunkState` independientemente del workdir).

---

## 9. Wirings cerrados

| Fase | Archivo | Relación |
|---|---|---|
| F11 | `schemas/profile.schema.json` + `assets/profile.template.yaml` | Añade `chunk_loop: {strategy, chunk_size, neighbor_window, strict_no_full_load}` opcional. |
| F13 | SDM | `chunk_loop.walk` lee `sdm.json` filtrando por rango; nunca carga el archivo completo si ≥ 1000 bloques (usa streaming JSON). |
| F15/F38 | `scripts/util/ledger.py` (Coverage Ledger) | El ledger puede contener unidades cuyo `source_block_ids[]` abarca varios chunks; `chunk-state.json` los referencia sin copiarlos. |
| F31 | `scripts/ingest/build_sdm.py` | Produce SDM paginado; F107 asume `sdm.json` con `anchor.section_path` estable. |
| F32 | `references/02-source-model/anchors.md` | El corte por `section_path` requiere anchors estables (F32 cubre el caso hostil #14). |
| F37 | `references/03-knowledge/information-units.md` | `chunk_loop.walk` invoca el detector de unidades sobre el rango; la unidad devuelta puede tener bloques en múltiples chunks. |
| F44 | `references/03-knowledge/note-plan.md` | El `note-plan.json` se actualiza al cierre de cada chunk; las notas cruzadas se marcan con `note.cross_chunk: true` (flag opcional). |
| F16 | `references/00-pipeline/manifest.md` | Cada chunk actualiza `manifest.json` con `chunk_progress` (nuevo campo opcional). |
| F48 | `scripts/authoring/parse_notemark.py` | Invocado por etapa 4; opera sobre 1 nota a la vez (cumple presupuesto etapa 4). |
| F49 | `scripts/validate/validate_ir.py` | Invocado por etapa 5; opera sobre 1 IR a la vez (cumple presupuesto etapa 5). |
| F106 | `references/00-pipeline/book-mode.md` | Composición descrita en §8. |
| F108 | `references/03-knowledge/dedup.md` | F107 no invoca F108 directamente; wirings declarados para futura integración (`chunk_loop.consolidate` puede llamar `dedup/detect.py --strategy single-chunk`). |
| F109 | `references/10-quality/consolidation-passes.md` | Wirings declarados: `chunk_loop.consolidate` invocará `consolidate.py run-all --strategy single-chunk` cuando F107 se reabra. |
| F110 | `references/05-note-types/index-moc-generator.md` | Wirings declarados: `chunk_loop.consolidate` puede invocar `book_index.py generate --strategy single-chunk` cuando F107 se reabra. |
| F117 | `scripts/README.md` | `chunk_loop.py` catalogado con sus 5 sub-comandos. |

**Wirings colaterales:**

- `SKILL.md` §5.2 — entrada en la tabla de rutas para "Procesar fuente por chunks con presupuesto acotado".
- `references/00-pipeline/README.md` — marca `chunk-loop.md` como publicado.
- `references/00-pipeline/architecture.md` §3.7 — subsección nueva declarando F107 como meta-orquestador sobre L1-L4 (NO L0).
- `references/06-writing/anti-patterns.md` §2 — añade **AP21** "Unidad cruzada duplicada" + **AP22** "Carga completa del documento fuera de L0" (22 APs totales).
- `assets/profile.template.yaml` — añade bloque `chunk_loop` opcional.
- `scripts/README.md` — entrada de catálogo `chunk_loop.py` con 5 sub-comandos.

---

## 10. Anti-patrones

F107 introduce **4 anti-patrones nuevos** AP-CHK1..AP-CHK4, todos detectables
algorítmicamente:

| ID | Nombre | Detección | Origen |
|---|---|---|---|
| **AP-CHK1** | Unidad cruzada duplicada | `chunk-state.json.cross_chunk_units[].note_id` tiene duplicados; o hay 2 notas para la misma unidad | F107 §7 + §10 AP-CHK1 |
| **AP-CHK2** | Carga completa del documento fuera de L0 | Cualquier entrada en `<audit-loads>` con path terminando en `.pdf`/`.epub`/`.docx`/`.pptx`/`.html`/`.txt` | F107 §3 CHK-R2 + §10 AP-CHK2 |
| **AP-CHK3** | Etapa con presupuesto excedido | La suma de archivos cargados en una etapa supera `max_files_loaded` (tabla §3) | F107 §3 CHK-R1 + §10 AP-CHK3 |
| **AP-CHK4** | Re-procesar sin `--force` perdiendo trabajo | `state.mark_done` sobrescribe `processed_at` sin guardar en `previous_processed_at`; `--force` requerido | F107 §6 CHK-R5 + §10 AP-CHK4 |

La verificación algorítmica corre vía `chunk_loop.py check [--budget]
[--audit-loads <log.jsonl>]`.

---

## 11. Verificación al cierre

Los **3 criterios del ROADMAP** se verifican algorítmicamente en
`evals/chunk-loop-sample/run_eval.py`:

| Criterio | Sub-eval | Cómo se verifica |
|---|---|---|
| **V1** Ninguna etapa requiere más de un número acotado de referencias | C1 + C6 | Default `chunk_size=30` produce 9 chunks sobre 250 bloques; presupuesto por etapa en §3 (`max_files_loaded` ≤ 4); `chunk-loop.md` ≤ 500 líneas. |
| **V2** Una unidad que cruza dos chunks se documenta una vez y completa | C3 | `register_cross_chunk_unit(state, "mvcc", primary="chk01", secondary=["chk02"])`; `cross_chunk_units` tiene 1 entrada con `note_id` único. |
| **V3** Una fuente de 200+ páginas se procesa sin tenerla entera en contexto | C4 | `check --audit-loads` sobre log limpio → exit 0; sobre log con `.pdf` → exit 1 + AP-CHK2. |

**Criterios derivados** (también verificados por el eval):

- **V4.** Estrategia `by_chapter` con `chapter_size=3` sobre 25 chapters → 9 chunks (C2).
- **V5.** Walk idempotente: re-walk sin `--force` → exit 1 (C5).
- **V6.** `--force` preserva `previous_processed_at` (C5).
- **V7.** Resume continúa; `.bak` presente; timestamps inmutables (C6).

**Tabla de auto-verificación:**

```
python3 scripts/pipeline/chunk_loop.py --help                # exit 0, 5 sub-comandos
python3 evals/chunk-loop-sample/run_eval.py                  # exit 0, 6/6 PASS
wc -l references/00-pipeline/chunk-loop.md                   # ≤ 500
wc -l SKILL.md                                              # ≤ 500
python3 -c "import json; json.load(open('schemas/chunk-state.schema.json'))"  # exit 0
grep -c "AP21\|AP22" references/06-writing/anti-patterns.md  # ≥ 2
grep -c "F107" SKILL.md                                     # ≥ 1
grep -c "chunk_loop" scripts/README.md                      # ≥ 1
grep -c "chunk_loop" assets/profile.template.yaml           # ≥ 1
```