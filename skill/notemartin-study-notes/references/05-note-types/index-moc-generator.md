# `index-moc-generator` — `references/05-note-types/index-moc-generator.md`

> Documento normativo de la **Fase 110**. Define el **generador
> automático** del índice de obra (`scripts/pipeline/book_index.py`)
> que produce un único archivo Markdown `<workdir>/reports/book-index.md`
> agregando 10 secciones canónicas: ficha, mapa de capítulos, grafo de
> dependencias, rutas, cobertura por capítulo, glosario, cheatsheets,
> prácticas, erratas y progreso.
>
> F110 **NO redefine** F91 (el patrón de la nota `index-moc`); lo usa
> como plantilla. F110 implementa el **generador** que rellena el
> patrón a partir del estado real del corpus (IRs, manifest, glossary,
> concept-graph, F106 book-state, F107 chunk-state, F109 reports).
>
> Documentos complementarios:
> - `references/05-note-types/index-moc.md` (F91) — patrón `index-moc` (plantilla).
> - `references/00-pipeline/manifest.md` (F16) — schema `manifest.json` (`source`, `stage_progress`, `link_debt[]`).
> - `references/03-knowledge/concept-graph.md` (F39) — grafo de prerrequisitos.
> - `references/00-pipeline/book-mode.md` (F106) — `book-state.json` + `book_map.mmd`.
> - `references/00-pipeline/chunk-loop.md` (F107) — `chunk-state.json` (opcional).
> - `references/10-quality/consolidation-passes.md` (F109) — 4 reports en `reports/`.
> - `references/03-knowledge/terminology.md` (F40) — `glossary.json` canónico.
> - `references/05-note-types/cheatsheet.md` (F90) — notas cheatsheet.
>
> Enrutado desde SKILL.md §5.2.

## Índice

1. [Propósito](#1-propósito) · 2. [Cuándo aplica](#2-cuándo-aplica) · 3. [Las 10 secciones del archivo generado](#3-las-10-secciones-del-archivo-generado) · 4. [Algoritmo del generador](#4-algoritmo-del-generador) · 5. [Reglas duras (IDX-R1..IDX-R5)](#5-reglas-duras-idx-r1idx-r5) · 6. [CLI](#6-cli) · 7. [Wirings cerrados](#7-wirings-cerrados) · 8. [Anti-patrones](#8-anti-patrones) · 9. [Verificación al cierre](#9-verificación-al-cierre) · 10. [Cambios permitidos](#10-cambios-permitidos) · 11. [Tabla de auto-verificación](#11-tabla-de-auto-verificación)

---

## 1. Propósito

F110 introduce el **generador de índice de obra** (`book_index.py`) que
produce un único archivo Markdown `<workdir>/reports/book-index.md`
agregando todo el estado del corpus. El formato del archivo sigue el
patrón de 9 secciones canónicas definido por **F91** (`references/05-note-types/index-moc.md`).

**Cierra los 3 criterios del ROADMAP** §1779-1783:

1. _Refleja el estado real de cobertura por capítulo_ → §3 + §9 V1.
2. _Incluye grafo renderizado_ → §3 + §9 V2 (Mermaid `graph LR` embebido).
3. _Enlaza glosario, cheatsheets y prácticas_ → §3 + §9 V3 (secciones con `[[note:id]]` + descripción).

**Fuera de alcance:**

- Redefinir F91 (la plantilla); F110 la usa.
- Editar IRs/NoteMark; F110 solo lee.
- Renderizar Mermaid; el archivo `.md` se interpreta downstream.

---

## 2. Cuándo aplica

El generador se activa opcionalmente:

- Manualmente: `book_index.py generate --workdir DIR`.
- `book-mode.py consolidate` (F106 §7) lo invoca cuando
  `profile.yaml::book_index.auto_on_consolidate == true` (default `false`,
  cumple INV-12).

**Exclusiones** (no genera):

- Corpus sin `manifest.json` → exit 2 con `IDX_NO_MANIFEST`.
- Workdir inválido → exit 2 con `IDX_NO_WORKDIR`.

---

## 3. Las 10 secciones del archivo generado

El archivo `book-index.md` se compone de **10 secciones canónicas** en
orden estricto (IDX-R3). Cada sección tiene una fuente de datos y una
garantía.

| # | Sección | Fuente de datos | Garantía |
|---|---|---|---|
| **1** | `## Ficha` | `manifest.json::source` + `stage_progress` + `current_stage` | Renderiza source.id + hash + algoritmo + stage progress |
| **2** | `## Mapa de capítulos` | `book-map.mmd` (F106) embebido + lista de capítulos (de `book-state.json`) | Bloque Mermaid `graph LR` con aristas forward/backward; valida con F65 §6 (≤ 15 nodos) |
| **3** | `## Grafo de dependencias` | `concept-graph.json` (F39) + glosario de F109 | Bloque Mermaid `graph TD` con conceptos canónicos; omite si > 15 nodos (warning + sub-grafos) |
| **4** | `## Rutas de lectura` | `study-paths.json` (F109 stub) + heurística simple | Tabla con 3-5 rutas temáticas |
| **5** | `## Cobertura por capítulo` | `book-state.json::chapters[]` + IRs por chapter | capítulo / total / done / pending / % |
| **6** | `## Glosario` | `glossary.json` (F40) + `report-glossary.json` (F109) | bullets `[[note:id]]` — descripción; omite los huérfanos (sin nota) |
| **7** | `## Cheatsheets` | `cheatsheets-index.json` (F109) + escaneo IR `note_type == "cheatsheet"` | bullets `[[note:id]]` — descripción |
| **8** | `## Prácticas` | escaneo IR `note_type == "practice"` | bullets `[[note:id]]` — descripción |
| **9** | `## Erratas` | `report-link-debt.json` (F109) filtrado a `kind ∈ {broken-wikilink, missing-target, orphan-note}` | Tabla tipo / nota / target |
| **10** | `## Progreso` | `book-state.json::chapters[]::status` + `chunk-state.json::chunks[]::status` (si F107) | Porcentaje done vs pending a nivel corpus |

**Marcador `_(vacío)_`**: cuando una sección no tiene datos (e.g., el
workdir no tiene F106 activado), se renderiza con el literal
`_(vacío)_` para garantizar orden canónico (IDX-R3).

---

## 4. Algoritmo del generador

`generate --workdir DIR` ejecuta **5 pasos cerrados**:

1. **Cargar header**: `manifest.json` (header del archivo).
2. **Cargar capítulos**: `book-state.json` (F106) y `book_map.mmd`. Si no
   existen, secciones 2/5/10 con marcador `_(no F106 book-mode activo)_`.
3. **Cargar grafo**: `concept-graph.json` (F39). Si no existe, sección 3
   con marcador.
4. **Cargar reports + glossary + cheatsheets + practices**:
   - `reports/report-link-debt.json` (F109) → sección 9.
   - `reports/report-glossary.json` (F109) → sección 6 cross-reference.
   - `knowledge/glossary.json` → sección 6.
   - `reports/cheatsheets-index.json` (F109) + escaneo IRs → sección 7.
   - Escaneo IRs `note_type == "practice"` → sección 8.
5. **Renderizar Markdown**: 10 secciones en orden canónico; escritura
   atómica con `tempfile + Path.replace` + backup `.bak` (IDX-R2 análogo
   a F106 BM-R2).

---

## 5. Reglas duras (IDX-R1..IDX-R5)

- **IDX-R1** — El archivo generado es **idempotente**: re-ejecución
  produce el mismo `sha256` (excluyendo `generated_at` y `.bak`).
  Verificable ejecutando `generate` 2 veces y comparando el contenido
  semántico.
- **IDX-R2** — El archivo **NO modifica los inputs**; solo escribe
  `<workdir>/reports/book-index.md` (cumple CON-R3 análogo).
- **IDX-R3** — Las 10 secciones aparecen **en orden canónico** incluso si
  están vacías (marcador `_(vacío)_`).
- **IDX-R4** — Cada `[[note:id]]` en las secciones 6/7/8/9 debe existir
  en el corpus o en `phantom-notes/`; si no, se omite (no se renderiza
  link roto).
- **IDX-R5** — El grafo (sección 3) debe estar embebido como bloque
  Mermaid ` ```mermaid `; nunca inline como imagen.

---

## 6. CLI

```bash
book_index.py generate --workdir DIR
                       [--strategy {default,consolidate}]
                       [--output reports/book-index.md]
                       [--include-errata]            # default true
                       [--yes]                         # confirmación (cumple INV-12)

book_index.py check --workdir DIR
                     [--output reports/book-index.md]
```

Códigos de salida:
- **0** — OK (generado o check passed).
- **1** — Validación (IDX-R1..R5 violado; check falla).
- **2** — Uso (paths faltantes, `IDX_NO_WORKDIR`, `IDX_NO_MANIFEST`).

Dependencias: Python 3.9+ stdlib puro (sin `jsonschema`).

---

## 7. Wirings cerrados

| Fase | Archivo | Relación |
|---|---|---|
| F16 | `references/00-pipeline/manifest.md` | Generador lee `manifest.json` para la ficha. |
| F39 | `references/03-knowledge/concept-graph.md` | Generador lee `concept-graph.json` para el grafo de dependencias. |
| F40 | `references/03-knowledge/terminology.md` | Generador lee `glossary.json` para la sección Glosario. |
| F91 | `references/05-note-types/index-moc.md` | Generador usa el patrón canónico (9 secciones base + 1 sección Progreso propia de F110). |
| F90 | `references/05-note-types/cheatsheet.md` | Generador detecta `note_type == "cheatsheet"` para la sección Cheatsheets. |
| F104 | `references/09-study/study-paths.md` | Generador lee `study-paths.json` para la sección Rutas. |
| F106 | `references/00-pipeline/book-mode.md` | Generador lee `book-state.json` + `book_map.mmd` para las secciones Mapa de capítulos / Cobertura / Progreso. |
| F107 | `references/00-pipeline/chunk-loop.md` | Generador opcionalmente lee `chunk-state.json` para la sección Progreso. |
| F109 | `references/10-quality/consolidation-passes.md` | Generador lee 4 reports (link-debt / cheatsheets / study-paths / glossary) + 1 cross-ref. |
| F117 | `scripts/README.md` | `book_index.py` catalogado. |

**Wirings colaterales:**

- `SKILL.md` §5.2 — entrada de routing.
- `references/05-note-types/README.md` — marca `index-moc-generator.md` como publicado.
- `references/00-pipeline/book-mode.md` §7 — wiring: tras `consolidate.py run-all`, opcionalmente invoca `book_index.py generate`.
- `references/06-writing/anti-patterns.md` §2 — añade **AP29** / **AP30** / **AP31**.
- `assets/profile.template.yaml` — bloque `book_index` opcional.
- `schemas/profile.schema.json` — `$defs/book_index`.

---

## 8. Anti-patrones

F110 introduce **3 anti-patrones nuevos** AP-IDX-1..3:

| ID | Nombre | Detección | Origen |
|---|---|---|---|
| **AP-IDX-1 / AP29** | Índice desactualizado | `book-index.md` no refleja el estado actual: tras `consolidate.py run-all` + `book_index.py generate` 2 veces, el archivo debe tener el mismo `sha256` (IDX-R1) | F110 §5 IDX-R1 + §9 V3 |
| **AP-IDX-2 / AP30** | Grafo no renderizado en índice | Sección 3 (`## Grafo de dependencias`) ausente o sin bloque Mermaid ` ```mermaid ` (IDX-R5 violado) | F110 §3 + §5 IDX-R5 |
| **AP-IDX-3 / AP31** | Índice sin enlaces a glosario/cheatsheets | Las secciones 6/7/8 no tienen `[[note:id]]` (están vacías o con `_(vacío)_`); o los `[[note:id]]` apuntan a notas inexistentes (IDX-R4 violado) | F110 §3 + §5 IDX-R4 + §9 |

---

## 9. Verificación al cierre

Los **3 criterios del ROADMAP** + **IDX-R1..R5** se verifican algorítmicamente en `evals/book-index-sample/run_eval.py`:

| Criterio | Sub-eval | Cómo se verifica |
|---|---|---|
| **V1** Refleja estado real de cobertura por capítulo | C1 | Sección 5 (`## Cobertura por capítulo`) tiene tabla con ≥ 1 capítulo; columnas `total` / `done` / `pending`; % done > 0 | 
| **V2** Incluye grafo renderizado | C2 | Sección 3 (`## Grafo de dependencias`) tiene bloque ` ```mermaid `; ≥ 1 nodo + ≥ 1 arista |
| **V3** Enlaza glosario, cheatsheets, prácticas | C3 | Secciones 6/7/8 tienen ≥ 1 `[[note:id]]` cada una; todos los IDs existen en IRs (filesystem check) |

**Criterios derivados** (también verificados):

- **V4.** IDX-R1: `sha256` del archivo (excluyendo `generated_at`) es estable entre 2 ejecuciones.
- **V5.** IDX-R2: el archivo `manifest.json` no se modifica (verificable con checksum).
- **V6.** IDX-R3: las 10 secciones aparecen en orden canónico.
- **V7.** IDX-R4: ningún `[[note:id]]` apunta a nota inexistente.
- **V8.** IDX-R5: bloque Mermaid de la sección 3 es válido (regex).

---

## 10. Cambios permitidos

- Añadir nueva sección entre las 10 existentes (versión mayor).
- Cambiar el formato de la sección Glosario (versión menor).
- Añadir campos opcionales al header (versión menor).

**Reabren F110**: cambiar el orden de las 10 secciones, romper IDX-R1..R5, eliminar el archivo generado sin notificar al agente.

---

## 11. Tabla de auto-verificación

```
python3 scripts/pipeline/book_index.py --help              # exit 0, 2 sub-comandos
python3 evals/book-index-sample/run_eval.py              # exit 0, 3/3 PASS
wc -l references/05-note-types/index-moc-generator.md    # ≤ 500
wc -l SKILL.md                                            # ≤ 500
grep -c "AP29\|AP30\|AP31" references/06-writing/anti-patterns.md  # ≥ 3
grep -c "F110" SKILL.md                                   # ≥ 1
grep -c "book_index" scripts/README.md                    # ≥ 1
grep -c "book_index" assets/profile.template.yaml         # ≥ 1
```