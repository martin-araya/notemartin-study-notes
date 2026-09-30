# `references/00-pipeline/book-mode.md` — Modo obra completa

> Documento normativo de la **Fase 106**. Define el **modo obra**:
> reconocimiento previo (índice, prefacio, mapa de dependencias),
> procesamiento por capítulo con estado compartido, consolidación parcial
> cada N capítulos, y contrato de stop/resume con escritura atómica.
>
> F106 **no redefine** F11/F13/F15/F36/F39/F40/F41/F43/F108/F109/F110; los
> **orquesta** sobre el workdir de una fuente. Esta capa opera como
> meta-orquestador sobre las 5 capas L0-L4 (`architecture.md` §3).
>
> Documentos complementarios:
> - `references/00-pipeline/architecture.md` (F4) — capas L0-L4 + §3.6 modo obra
> - `references/00-pipeline/responsibilities.md` (F3) — división agente/script
> - `skill/notemartin-study-notes/scripts/pipeline/book_mode.py` — implementa esta spec
>
> Enrutado desde SKILL.md §5.2. Doc hermano: `manifest.md` (F16) por el
> estado reanudable.

## Índice

1. [Propósito](#1-propósito) · 2. [Cuándo aplica](#2-cuándo-aplica) · 3. [Reconocimiento previo](#3-reconocimiento-previo-init) · 4. [Estado compartido](#4-estado-compartido--book-statejson) · 5. [Registro de conceptos compartidos](#5-registro-de-conceptos-compartidos) · 6. [Procesamiento por capítulo](#6-procesamiento-por-capítulo) · 7. [Consolidación parcial](#7-consolidación-parcial-cada-n-capítulos) · 8. [Stop/resume](#8-detener-y-reanudar) · 9. [Wirings](#9-wirings-cerrados) · 10. [Anti-patrones](#10-anti-patrones) · 11. [Verificación al cierre](#11-verificación-al-cierre)

---

## 1. Propósito

F106 introduce el **modo obra completa** como meta-orquestador sobre L0-L4
para fuentes que son **libros** (múltiples capítulos con índice y prefacio
detectables). El modo obra garantiza tres propiedades que el pipeline
estándar por-fuente no cubre:

1. **Coherencia entre capítulos** — los conceptos definidos en un capítulo
   se referencian en los siguientes con `[[note:id]]`; no se redefinen.
2. **Estado durable y recuperable** — un crash a mitad del libro no pierde
   progreso; el agente reanuda desde el siguiente capítulo pendiente.
3. **Pases de consolidación periódicos** — cada N capítulos se ejecuta la
   cadena dedup → normalización → índice → cheatsheets → consistencia de
   definiciones (F108/F109/F110) sobre el rango acumulado, evitando que el
   drift se acumule.

**Cierra los 3 criterios del ROADMAP** §1747-1751:

1. _El mapa se genera antes del primer capítulo_ → §3 (BM-R1) + §11 V1.
2. _Un concepto del capítulo 2 no se redefine en el 9_ → §5 + §10 AP-BM1 + §11 V2.
3. _Se detiene y reanuda en cualquier capítulo_ → §4 (BM-R2 escritura atómica) + §8 + §11 V3.

**Fuera de alcance:**

- Orquestación por-capítulo del pipeline L0-L4 mismo (F31 `build_sdm` ya
  soporta SDM por rango de páginas; F48/F49 ya operan por nota).
- Detección automática de cuándo un corpus es "libro" (este spec es
  opt-in vía `init`; el agente decide cuándo invocarlo).
- Persistencia de notas del IR dentro del libro (cada capítulo invoca el
  flujo L0-L4 estándar; F106 solo persiste el progreso del modo obra).

---

## 2. Cuándo aplica

El modo obra **se activa opcionalmente** cuando se cumplen **todas** las
siguientes condiciones:

- El corpus tiene **≥ 2 capítulos** detectables (heading level==1).
- Existe un **índice impreso o reconstruido** (lista ordenada de capítulos).
- Hay **≥ 1 dependencia** entre capítulos (un capítulo referencia a otro).

**Exclusiones explícitas** (caer al pipeline L0-L4 estándar, NO activar modo
obra):

- Corpus de un solo capítulo (corpus 01, 06, 07, 08, 09, 10, 11, 12).
- Corpus sin TOC detectable (algunos casos de corpus 13/14 hostile).
- Corpus donde el TOC impreso contradice los headings (caso de corpus 14
  "book with inconsistent section numbering"): F106 detecta la
  inconsistencia durante `init` y emite `index_unreliable: true` + warning,
  pero el modo obra sigue siendo válido si el índice reconstruido es
  coherente (los anclas sintéticas F32 se usan en lugar de la numeración
  impresa).

**Activación**: el usuario o el agente decide invocar
`book_mode.py init --sdm <sdm.json> --workdir <workdir>`. Si el SDM no
tiene índice, `init` falla con `BOOK_MODE_NO_INDEX` (exit 2) y el modo
obra no se activa.

---

## 3. Reconocimiento previo (`init`)

Antes de tocar el primer capítulo, F106 ejecuta **4 pasos cerrados** sobre
el SDM:

### 3.1 Extraer índice

Cada bloque del SDM con `type == "heading"` y `level == 1` marca un
capítulo. Se conservan en orden de aparición; el primero es `ch01`, el
segundo `ch02`, etc. Si no hay headings level==1, `init` aborta con
`BOOK_MODE_NO_INDEX`.

### 3.2 Detectar prefacio

Si el título del primer capítulo ∈ `PREFACE_TITLES` (lista cerrada de 11
valores: `preface`, `prefacio`, `prólogo`, `prologo`, `introduction`,
`introducción`, `introduccion`, `foreword`, `nota del autor`, `nota del
editor`, `acknowledgements`, `agradecimientos`), se marca
`has_preface: true` y se preserva su `chapter_id` en `book_map.preface_chapter_id`.
El prefacio cuenta como capítulo 0 lógico pero tiene su propio ID.

### 3.3 Construir mapa de dependencias

Por cada par de capítulos `(A, B)`, se genera una arista `A → B` si:

- El título de `B` aparece en el `text` de un bloque de `A` (≥ 1
  ocurrencia, case-insensitive); **o**
- Una frase regex `\b(ver|véase|see|cf\.|chapter|capítulo)\s+(B_title)\b`
  aparece en `A`.

`direction` es `"forward"` si el índice de `A` < índice de `B`, sino
`"backward"`. Las aristas se deduplican por `(from, trid, direction)` y se
persiste el `evidence` (la frase literal que sostiene la arista) para
auditoría.

### 3.4 Generar mapa Mermaid (BM-R1)

Se emite un diagrama `graph LR` con un nodo por capítulo. Si el nº de
capítulos > 15, se emite un warning stderr (regla F65 §6 sobre la
legibilidad Mermaid). El diagrama se persiste en `<workdir>/book_map.mmd`
y se registra su ruta en `book-state.json.book_map_ref`.

**Regla dura BM-R1**: ningún capítulo puede transicionar a `status ==
"processing"` mientras `book_map.json` no exista en disco **y**
`book_map.generated_at < chapters[*].started_at` para cualquier capítulo
ya `processing`/`done`. El script `process` valida esta regla antes de
mutar el estado; la violación sale con `exit 1` y mensaje
`BOOK_MAP_MISSING` o `BOOK_MAP_GENERATED_AFTER_CHAPTER`.

---

## 4. Estado compartido — `book-state.json`

El estado del modo obra vive en `<workdir>/book-state.json` y sigue el
schema `schemas/book-state.schema.json` (Draft 2020-12,
`additionalProperties: false` estricto). Estructura de alto nivel:

| Campo | Tipo | Significado |
|---|---|---|
| `schema_version` | const `"1.0.0"` | Versión del schema. |
| `book_id` | slug | Identificador del libro. |
| `source_hash` | hex 64 | SHA-256 de la fuente cruda. |
| `total_chapters` | int ≥ 1 | Total excluyendo prefacio. |
| `has_preface` | bool | Prefacio detectado. |
| `chapters[]` | array | Estado por capítulo (ver §6). |
| `shared_concepts` | map | Conceptos canónicos (ver §5). |
| `book_map_ref` | path | Ruta a `book_map.json`. |
| `last_consolidation_chapter` | id? | Último capítulo consolidado. |
| `next_consolidation_at` | id? | Sugerencia de próximo pase. |
| `index_unreliable` | bool | TOC impreso ≠ headings del SDM. |
| `config` | objeto | `consolidation_every` (default 5) + `auto_consolidate` (default false). |
| `created_at` / `updated_at` | ISO 8601 UTC | Tiempos de creación/última mutación. |

### Reglas duras de mutación (BM-R2..BM-R5)

- **BM-R2** — Escritura atómica: toda mutación escribe el archivo
  completo vía `_atomic_write_json` (tempfile + `Path.replace`); antes de
  la escritura, si el archivo existe, se copia a `.bak` (verificación de
  AP-BM3).
- **BM-R3** — `chapters[i].status ∈ {pending, processing, done, failed}`
  (enum cerrado; el schema lo enforza).
- **BM-R4** — Al transicionar a `done`, `chapters[i].processed_at` se
  rellena con ISO 8601 UTC; `started_at` se sella (no se reescribe).
  Re-procesar con `--force` copia `processed_at` a `previous_processed_at`
  antes de sobreescribir (AP-BM4).
- **BM-R5** — Una falla (`status == "failed"`) deja `error: {code,
  message, recoverable}`. `resume` reintenta solo capítulos `pending` o
  `failed` con `recoverable: true`. El script captura SIGTERM y hace
  flush atómico + exit 0 antes de terminar (BM-R5b).

---

## 5. Registro de conceptos compartidos

El campo `shared_concepts` es un mapa `{concept_id → ConceptEntry}`:

```jsonc
{
  "canonical_chapter": "ch02",         // first-occurrence wins
  "canonical_note_id": "mvcc",         // puede ser null si aún no escrita
  "aliases": ["Multi-Version Concurrency Control"],
  "first_seen_at": "2026-09-30T15:00:00Z"
}
```

**Política first-occurrence wins**: el primer capítulo que registra un
concepto fija su `canonical_chapter`. Capítulos posteriores deben **referir**
la definición con `[[note:concept-id]]` (no redefinir). El comando CLI
`register-concept` agrega aliases si el concepto ya existe; en caso
contrario crea la entrada.

API Python:

```python
from book_mode import BookState, register_concept

state = BookState.load(workdir=Path(".notes-work/abc"))
register_concept(state, "mvcc", chapter="ch02", note_id="mvcc",
                 aliases=["Multi-Version Concurrency Control"])
state.save()
```

**Detección de redefinición (AP-BM1)**: `detect-ap-bm1` compara la sección
`## Definición` de la nota del capítulo canónico contra la `## Definición`
de cualquier nota de otro capítulo. Si la similitud (`difflib.SequenceMatcher.ratio()`)
> 0.5 y la nota del otro capítulo no contiene `[[note:concept-id]]`, se
reporta como violación. Esta es la verificación algorítmica del **criterio #2**
del ROADMAP.

---

## 6. Procesamiento por capítulo

Sub-comando `process --chapter chNN [--force] [--no-consolidate] [--notes id1,id2]`.

Pasos por capítulo:

1. Cargar `BookState` desde `<workdir>/book-state.json`.
2. Validar BM-R1: `book_map.json` existe y su `generated_at <
   chapters[*].started_at` para cualquier capítulo previo en `processing`/`done`.
3. Validar que el capítulo existe y no está `done` (a menos que `--force`).
4. Si `--force` y `status == "done"`: copiar `processed_at` a
   `previous_processed_at` (AP-BM4).
5. Transicionar a `status == "processing"`, sellar `started_at` con ISO 8601 UTC.
6. `state.save()` (escritura atómica + `.bak` BM-R2).
7. El agente externo continúa con el flujo L0-L4 del capítulo (F31 build_sdm
   por rango + F48/F49 por nota). F106 **no orquesta** esos pasos; solo
   persiste el progreso.
8. Si se invoca con `--notes`, `state.mark_done(chapter, notes)` + save.
9. Calcular `next_consolidation_target()` y emitir hint en stdout si
   `config.auto_consolidate == true` (el agente decide si consolidar).

**Idempotencia**: si `status == "done"` y no se pasa `--force`, `process`
falla con `BOOK_CHAPTER_ALREADY_DONE` (exit 1). El capítulo NO se
re-procesa.

---

## 7. Consolidación parcial cada N capítulos

`config.consolidation_every` (default **5**, decisión confirmada: 5 es el
sweet spot entre carga de contexto y reducción de drift; libros del corpus
friendly tienen 10-15 capítulos, lo que resulta en 2-3 pases de
consolidación). Configurable vía `--consolidation-every` en `init`.

Sub-comando `consolidate --workdir DIR` ejecuta la cadena de 5 pasos sobre
el rango `[last_consolidation_chapter+1 .. último capítulo done]`. Book-mode
**delegates** esta cadena al orquestador `consolidate.py run-all` (F109)
con `--strategy consolidate`:

```bash
python3 scripts/pipeline/consolidate.py run-all \
    --workdir <workdir> --strategy consolidate \
    --irs-glob 'ir/*.json' --notemark-glob 'notemark/*.nm'
```

F109 cubre los 5 pases (link-debt, glossary, indices, cheatsheets,
consistency); ver `references/10-quality/consolidation-passes.md` para el
contrato. Book-mode ahora simplemente invoca el orquestador y registra el
run en `book-state.json::consolidation_runs[]` (opcional, vía F16 manifest).

`consolidate` es **idempotente**: re-ejecutar sobre el mismo rango no
produce cambios (verificado por C4 del eval). El script registra
`last_consolidation_chapter` y `next_consolidation_at` en el state.

**Auto vs manual**: `config.auto_consolidate` default `false` (cumple
INV-12 "no sorpresa al usuario"). El script emite un hint tras cerrar
cada capítulo; el agente decide cuándo consolidar.

---

## 8. Detener y reanudar

El modo obra cumple el **criterio #3** del ROADMAP mediante 3 mecanismos
concurrentes:

1. **Escritura atómica + `.bak`** (BM-R2) — cada `save()` deja el archivo
   consistente; un crash a mitad de save no produce JSON corrupto.
2. **Marcado de estado por capítulo** (BM-R3/R4) — `next_chapter()`
   devuelve el primer capítulo `pending` o `failed` con `recoverable: true`.
3. **CLI `resume`** — continúa desde `next_chapter()` o `--from chNN` hasta
   el final o `--to chMM`.

Contrato CLI:

```bash
# Status: imprime tabla por capítulo + posición del cursor.
book_mode.py status --workdir DIR [--json]

# Resume: continúa desde next_chapter (o --from) hasta el final (o --to).
book_mode.py resume --workdir DIR [--from chNN] [--to chMM]
```

Tras un crash, el operador (o el agente en su próxima sesión) ejecuta
`resume` y el script continúa sin re-procesar capítulos `done`. Los
`started_at` y `processed_at` de los capítulos previos son **inmutables**
(BM-R4, verificado por C3 del eval: timestamps capturados antes de
`resume` son idénticos a los posteriores).

SIGTERM: el script registra `signal.SIGTERM` para hacer flush atómico
del state y `exit 0` antes de terminar (BM-R5b).

---

## 9. Wirings cerrados

| Fase | Archivo | Relación |
|---|---|---|
| F11 | `schemas/profile.schema.json` + `assets/profile.template.yaml` | Añade `book_mode: {enabled, consolidation_every, auto_consolidate}` opcional. |
| F13 | SDM | `book_mode init` lee SDM para extraer índice + detectar prefacio + mapear dependencias. |
| F15 | `scripts/util/ledger.py` (Coverage Ledger) | El ledger de cada capítulo lleva `chapter_id`; F106 no modifica el ledger, lo consulta. |
| F36 | `scripts/util/sdm_cache.py` | El key de caché incluye `chapter_id` (regla BM-R6) para no compartir caché entre capítulos. |
| F39 | `references/03-knowledge/concept-graph.md` | `shared_concepts` es un subconjunto del grafo; el script cruza y avisa si un concepto del grafo no está registrado. |
| F40 | `references/03-knowledge/terminology.md` | Al consolidar (F106 §7 paso 2), fusiona aliases duplicados en el glosario. |
| F41 | `references/03-knowledge/conflicts.md` | Definiciones incompatibles entre capítulos se registran como `conflict` (F106 §7 paso 3). |
| F43 | `references/10-quality/completeness-audit.md` | Audita por capítulo con `min(chapter_coverage) >= 0.6` cuando el libro entero está consolidado. |
| F108 | `references/03-knowledge/...` (deduplicación) | Invocado en cada consolidación (F106 §7 paso 1). |
| F109 | `references/09-study/...` (pases de consolidación) | Secuencia de 5 pasos en cada consolidación. |
| F110 | `references/05-note-types/index-moc.md` | Alimentado en cada consolidación parcial (F106 §7 paso 4). |
| F117 | `scripts/README.md` | `book_mode.py` catalogado con sus 9 sub-comandos. |
| F107 | `references/00-pipeline/chunk-loop.md` | Composición descrita en F107 §8: F106 orquesta por capítulo; F107 chunk-loop opera por chunk dentro del capítulo (sub-workdir `<workdir>/chapters/<chNN>/chunk-state.json`) o standalone para fuentes no-libro. Evita solapamiento; ambos modos son opt-in complementarios. |
| F108 | `references/03-knowledge/dedup.md` | F106 §7 paso 1 (consolidación) invoca `dedup/detect.py --strategy consolidate` para identificar candidatos a `merge` / `specialize` / `split` antes de aplicar F108 `apply.py merge`. F106 no redefine F108; lo invoca. |
| F109 | `references/10-quality/consolidation-passes.md` | F106 §7 paso 1 delega al orquestador `consolidate.py run-all --strategy consolidate` (5 pases idempotentes). F106 no redefine F109; lo invoca. |
| F110 | `references/05-note-types/index-moc-generator.md` | Tras `consolidate.py run-all`, opcionalmente invoca `book_index.py generate --strategy consolidate` cuando `profile.yaml::book_index.auto_on_consolidate == true` (default false; cumple INV-12). F106 no redefine F110; lo invoca. |
| F111 | `references/04-authoring/incremental-update.md` | Cuando book-mode detecta `hash_mismatch` entre 2 sesiones, opcionalmente invoca `update.py run-all --old-sdm OLD --new-sdm NEW --workdir DIR --yes` (política MIGRATE de F16 + script de F111). F106 no redefine F111; lo invoca. |

**Wirings colaterales:**

- `SKILL.md` §5.2 — entrada en la tabla de rutas para "Inicializar / operar el modo obra completa de un libro".
- `references/00-pipeline/README.md` — marca `book-mode.md` como publicado.
- `references/00-pipeline/architecture.md` §3.6 — subsección nueva declarando F106 como orquestador sobre L0-L4.
- `references/06-writing/anti-patterns.md` §2 — añade **AP-BM1** "Concepto redefinido fuera del capítulo canónico" como 13er AP.
- `assets/profile.template.yaml` — añade bloque `book_mode` opcional con `enabled`, `consolidation_every`, `auto_consolidate`.

---

## 10. Anti-patrones

F106 introduce **4 anti-patrones nuevos** AP-BM1..AP-BM4, todos detectables
algorítmicamente:

| ID | Nombre | Detección | Origen |
|---|---|---|---|
| **AP-BM1** | Concepto redefinido fuera del capítulo canónico | `difflib.SequenceMatcher.ratio() > 0.5` entre `## Definición` de la nota canónica y la nota del otro capítulo, sin `[[note:concept-id]]` en la otra nota | F106 §5 + §10 AP-BM1 |
| **AP-BM2** | Mapa generado después del primer capítulo | `book_map.generated_at > chapters[any].started_at` | F106 §3.4 BM-R1 + §10 AP-BM2 |
| **AP-BM3** | Estado corrupto no detectable | `book-state.json.bak` ausente tras ≥ 2 saves (no hay punto de recuperación) | F106 §4 BM-R2 + §10 AP-BM3 |
| **AP-BM4** | Re-procesar sin `--force` perdiendo trabajo | `state.mark_done` sobrescribe `processed_at` sin guardar en `previous_processed_at`; `--force` requerido | F106 §6 + §10 AP-BM4 |

La verificación algorítmica corre vía `book_mode.py check --workdir DIR` o
vía sub-comandos específicos (`detect-ap-bm1`).

---

## 11. Verificación al cierre

Los **3 criterios del ROADMAP** se verifican algorítmicamente en
`evals/book-mode-sample/run_eval.py`:

| Criterio | Sub-eval | Cómo se verifica |
|---|---|---|
| **V1** El mapa se genera antes del primer capítulo | C1 | `process` sin `book_map.json` → exit 1 + `BOOK_MAP_MISSING`; con mapa generado ANTES del `started_at` → exit 0. Verifica BM-R1. |
| **V2** Un concepto del capítulo 2 no se redefine en el 9 | C2 | `detect-ap-bm1` sobre 3 fixtures: ch02 canónica, ch03 con `[[note:mvcc]]` (NO violación), ch09 con misma definición y sin link (1 violación). |
| **V3** Se detiene y reanuda en cualquier capítulo | C3 | Procesar ch01..ch03, snapshot de timestamps, `resume --to ch11` → todos `done`; `started_at`/`processed_at` de ch01..ch03 **idénticos** al snapshot. |

**Criterios derivados** (también verificados por el eval):

- **V4.** `consolidation_every=5` dispara consolidación tras ch05 (C4).
- **V5.** `consolidate` es idempotente: re-ejecutar no produce cambios (C4).
- **V6.** `.bak` se crea tras cada `save()` ≥ 2; snapshot anterior verificable (C5).
- **V7.** AP-BM2 detectado por `check` cuando `book_map.generated_at > chapters[i].started_at` (C6).
- **V8.** AP-BM3 reportado cuando `.bak` ausente (C6).
- **V9.** AP-BM4 verificado: `previous_processed_at` poblado tras `--force` (C6).
- **V10.** Error no recuperable (`recoverable: false`) NO se reintenta en `resume`.

**Tabla de auto-verificación:**

```
python3 scripts/pipeline/book_mode.py --help                # exit 0, 9 sub-comandos
python3 evals/book-mode-sample/run_eval.py                  # exit 0, 6/6 PASS
wc -l references/00-pipeline/book-mode.md                   # ≤ 500
wc -l SKILL.md                                              # ≤ 500
python3 -c "import json; json.load(open('schemas/book-state.schema.json'))"  # exit 0
grep -c "AP-BM1" references/06-writing/anti-patterns.md     # ≥ 1
grep -c "F106" SKILL.md                                     # ≥ 1
grep -c "book_mode" scripts/README.md                        # ≥ 1
grep -c "book_mode" assets/profile.template.yaml            # ≥ 1
```