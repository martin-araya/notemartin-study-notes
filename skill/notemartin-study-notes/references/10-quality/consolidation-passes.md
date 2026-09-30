# `references/10-quality/consolidation-passes.md` — Pases de consolidación

> Documento normativo de la **Fase 109**. Define el **orquestador de
> pases de consolidación** que ejecuta 5 pases secuenciales (link-debt,
> glossary, indices, cheatsheets, consistency) sobre el workdir de una
> fuente. Cada pase es **idempotente** (re-ejecución produce el mismo
> output) y **conmutativo** (orden entre pases no afecta el resultado).
>
> F109 **NO redefine** F16/F40/F104/F108/F110; los orquesta. El pase 5
> (`consistency`) delega en `scripts/dedup/detect.py` (F108). El pase 1
> (`link-debt`) NO edita IRs/NoteMark; solo emite entradas en
> `manifest.json::link_debt[]` (F16).
>
> Documentos complementarios:
> - `references/00-pipeline/manifest.md` (F16) — schema `manifest.json` con `link_debt[]` y `consolidation_runs[]`.
> - `references/03-knowledge/terminology.md` (F40) — glosario canónico + aliases; regla R3 (alias único).
> - `references/09-study/study-paths.md` (F104) — rutas de estudio.
> - `references/03-knowledge/dedup.md` (F108) — detector de duplicados (pase 5 lo invoca).
> - `references/05-note-types/index-moc.md` (F110) — stub del índice de obra (pase 3 emite `index-moc-summary.json`).
> - `references/00-pipeline/book-mode.md` (F106) §7 paso 1 — book-mode `consolidate` invoca F109.
>
> Enrutado desde SKILL.md §5.2.

## Índice

1. [Propósito](#1-propósito) · 2. [Cuándo aplica](#2-cuándo-aplica) · 3. [Los 5 pases](#3-los-5-pases) · 4. [Reglas duras (CON-R1..CON-R5)](#4-reglas-duras-con-r1con-r5) · 5. [Contrato del orquestador `run-all`](#5-contrato-del-orquestador-run-all) · 6. [Idempotencia verificada algorítmicamente](#6-idempotencia-verificada-algorítmicamente) · 7. [Wirings cerrados](#7-wirings-cerrados) · 8. [Anti-patrones](#8-anti-patrones) · 9. [Verificación al cierre](#9-verificación-al-cierre) · 10. [Cambios permitidos](#10-cambios-permitidos) · 11. [Tabla de auto-verificación](#11-tabla-de-auto-verificación)

---

## 1. Propósito

F109 introduce el **orquestador de pases de consolidación** que ejecuta
**5 pases secuenciales** sobre el workdir. Cada pase:

- Lee inputs (IRs, NoteMark, manifest, glossary, etc.).
- Emite outputs (reportes en `reports/`, entradas en `manifest.json::link_debt[]`,
  entradas en `manifest.json::consolidation_runs[]`).
- **NO modifica inputs** (cumple CON-R3).

**Cierra los 3 criterios del ROADMAP** §1771-1775:

1. _Tras consolidar no quedan enlaces rotos ni huérfanos_ → §3 pase 1 + §9 V1.
2. _Ningún término tiene dos definiciones canónicas_ → §3 pase 2 (R3) + §3 pase 5 (F108) + §9 V2.
3. _Es re-ejecutable sin efectos secundarios_ → §4 CON-R1 + §6 + §9 V3.

**Fuera de alcance:**

- Redefinir F16/F40/F104/F108/F110; F109 los orquesta.
- Decidir qué hacer con `link_debt`; el agente decide (cumple INV-12).
- Aplicar merge/split; F108 `apply.py` ya lo hace opt-in.

---

## 2. Cuándo aplica

El orquestador se activa opcionalmente:

- Manualmente: el usuario o el agente invoca `consolidate.py run-all --workdir DIR`.
- `book-mode.py consolidate` lo invoca (F106 §7 paso 1) — pasa
  `--strategy consolidate` para que el orquestador sepa el contexto.
- `chunk-loop.py consolidate` lo invoca (F107 §9 wiring) — pasa
  `--strategy single-chunk`.

**Por defecto los pases no rompen el workdir**: solo escriben en
`reports/` y `manifest.json`. La política `consolidation.auto_on_consolidate`
y `consolidation.link_debt_auto_resolve` se declaran en
`profile.yaml::consolidation` (default `false` para ambas — cumple INV-12).

---

## 3. Los 5 pases

Tabla cerrada (input / output / garantía idempotente por pase):

| # | Pase | Entrada | Salida | Garantía idempotente |
|---|---|---|---|---|
| **1** | `pass-link-debt` | `ir/*.json` + `notemark/*.nm` + `manifest.json::link_debt[]` | Entradas `link_debt[].kind ∈ {"broken-wikilink", "missing-target", "orphan-note"}` para refs cuyo `target` no existe o notas sin incoming links | `link_debt[]` no crece en re-ejecución (se deduplica por `from_note`+`target`+`kind`) |
| **2** | `pass-glossary` | `knowledge/glossary.json` + IRs (concept/glossary-term) | `reports/report-glossary.json`: candidatos a nuevos términos + violaciones R3 (alias duplicado) | El glosario NO se modifica; el reporte es nuevo pero su contenido es determinista |
| **3** | `pass-indices` | `ir/*.json` + `notemark/*.nm` + `book-state.json` (si F106) | `reports/index-moc-summary.json` (stub F110): nº notas por tipo, por capítulo | El `sha256` del archivo generado es estable entre runs sin cambios en inputs |
| **4** | `pass-cheatsheets` | `ir/*.json` (cheatsheet) + `knowledge/*.json` | `reports/cheatsheets-index.json` + `reports/study-paths.json` (stub F104) | Estable |
| **5** | `pass-consistency` | `scripts/dedup/detect.py --strategy consolidate` (F108) | `reports/consistency-report.json` con AP-BM1/AP-CHK1 violations; exit 0 si 0 violations | confirmar halt; no aplica cambios |

### Pase 1 — `pass-link-debt` (CON-R4)

Escanea recursivamente:

1. **broken-wikilink** — para cada `link-note` con `attrs.target = X`,
   verifica que `X` exista como `note_id` en cualquier IR del workdir.
   Si no, emite `link_debt[].kind = "broken-wikilink"`,
   `from_note = parent_note_id`, `target = X`,
   `detected_at = ISO 8601 UTC`.
2. **missing-target** — `target` es `null` o vacío.
3. **orphan-note** — `note_id` no aparece como `target` en ningún otro
   `link-note` del workdir.

**No edita IRs/NoteMark** (CON-R4). El reporte lista las refs para que el
agente decida (borrar la línea, redirigir a otra nota, marcar
`redirected` vía F108 `apply.py merge`).

### Pase 2 — `pass-glossary` (F40 R3 + R8)

Lee `glossary.json` y:

1. **R3 (alias único)** — verifica que cada `alias` normalizado aparezca
   en ≤ 1 término (verificable iterando `terms[].aliases[]`).
2. **R8 (normalización retroactiva)** — escanea `## Definición` de notas
   `concept`/`glossary-term`; busca términos no presentes en el glosario;
   emite candidatos (`new_term_candidates`).

**No modifica `glossary.json`** (CON-R3). El reporte es nuevo.

### Pase 3 — `pass-indices` (F110 stub)

Genera `<workdir>/reports/index-moc-summary.json`:

```jsonc
{
  "schema_version": "1.0.0",
  "generated_at": "ISO 8601",
  "by_type": {"concept": 4, "glossary-term": 2, "procedure": 1, ...},
  "by_chapter": {"ch01": 3, "ch02": 4, ...},  // si F106 book-state presente
  "total_notes": 7
}
```

### Pase 4 — `pass-cheatsheets` (F104 stub)

Genera 2 archivos:

- `reports/cheatsheets-index.json`: lista de notas con
  `frontmatter.note-type == "cheatsheet"`.
- `reports/study-paths.json`: rutas inferidas (e.g., "MVP → RR") según
  heurística simple (cheatsheet → su `source-anchor` → conceptos
  enlazados).

### Pase 5 — `pass-consistency` (F108 delega)

Invoca `python3 scripts/dedup/detect.py scan --workdir DIR
--strategy consolidate --glossary <path> --json-out
reports/consistency-report.json`. El output es el JSON de candidatos
detectados. F109 NO modifica IRs; el reporte es lectura.

---

## 4. Reglas duras (CON-R1..CON-R5)

- **CON-R1** — Cada pase es **idempotente**: re-ejecutar produce el
  mismo output (mismo `sha256` del archivo generado). Verificable
  ejecutando `run-all` 2 veces; comparar `after_sha256` del reporte
  generado en cada run.
- **CON-R2** — Cada pase es **conmutativo**: el orden entre pases no
  afecta el resultado final. Cada pase opera sobre inputs
  independientes (CON-R3 garantiza que ningún pase modifica inputs de
  otros pases).
- **CON-R3** — Cada pase **NO modifica inputs**; solo escribe archivos
  en `<workdir>/reports/` y `manifest.json::link_debt[]` +
  `manifest.json::consolidation_runs[]`.
- **CON-R4** — Pase 1 detecta `broken-wikilink` / `missing-target` /
  `orphan-note` pero **NO edita IRs/NoteMark**; el agente decide qué
  hacer (borrar, redirigir, marcar como `redirected` vía F108).
- **CON-R5** — Pase 5 delega en F108 detector; no redefine el detector.
  Si F108 cambia su CLI, el orquestador aborta con `CON_RUN_FAILED` y
  el agente ajusta el comando.

---

## 5. Contrato del orquestador `run-all`

`run-all --workdir DIR [--strategy {default,consolidate}]` ejecuta los
5 pases en orden:

```
link-debt → glossary → indices → cheatsheets → consistency
```

Cada pase:

- Captura `started_at` + `finished_at` (ISO 8601 UTC).
- Captura `sha256_input` (hash de los inputs leídos) + `sha256_output`
  (hash del output escrito).
- Captura `duration_ms`.

`run-all` agrega 1 entrada a `manifest.json::consolidation_runs[]` con
la lista de los 5 pases + `before_sha256` (del workdir pre-run) +
`after_sha256` (del workdir post-run) + `status: "done" | "failed"`.

Si un pase falla (exit ≠ 0):

- `run-all` aborta con exit 1.
- Emite `consolidation_runs[].status = "failed"` con `finished_at`
  poblado y los pases ejecutados hasta el fallo.
- El agente decide: re-ejecutar `run-all` (CON-R1 garantiza idempotencia)
  o corregir el input que causa el fallo.

**Escritura atómica** del `manifest.json` (CON-R1 + `.bak` antes de
cada save, análogo a F106 BM-R2).

---

## 6. Idempotencia verificada algorítmicamente

Ejecutar `run-all` 2 veces consecutivas:

1. **Primera ejecución**: `run-all` corre los 5 pases; genera los 4
   archivos en `reports/` + actualiza `manifest.json::consolidation_runs[]`.
2. **Segunda ejecución** (sin cambios en inputs): `run-all` corre los 5
   pases; cada pase produce archivos con **el mismo `sha256`** que la
   1ª ejecución. `manifest.json::consolidation_runs[]` recibe una
   **nueva entrada** (historial), pero los `sha256_output` por pase son
   idénticos.

Verificación algorítmica: `eval C3` ejecuta `run-all` 2 veces y compara
los `sha256_output` por pase. Si difieren → AP-CON-1 detectado.

---

## 7. Wirings cerrados

| Fase | Archivo | Relación |
|---|---|---|
| F16 | `references/00-pipeline/manifest.md` + `schemas/manifest.schema.json` | F109 actualiza `manifest.json::link_debt[]` (F16 enum `kind`) + `manifest.json::consolidation_runs[]` (nuevo). |
| F40 | `references/03-knowledge/terminology.md` | Pase 2 verifica R3 (alias único) + R8 (normalización retroactiva). |
| F104 | `references/09-study/study-paths.md` | Pase 4 emite `reports/study-paths.json` (stub). |
| F106 | `references/00-pipeline/book-mode.md` §7 paso 1 | `book-mode.py consolidate` invoca `consolidate.py run-all --strategy consolidate`. |
| F107 | `references/00-pipeline/chunk-loop.md` §9 | `chunk-loop.py consolidate` invocará `consolidate.py run-all --strategy single-chunk` cuando se reabra. |
| F108 | `scripts/dedup/detect.py` | Pase 5 delega en F108 detector; reusa el output sin redefinir. |
| F110 | `references/05-note-types/index-moc-generator.md` + `scripts/pipeline/book_index.py` | F109 no invoca F110 directamente; tras `run-all`, el agente puede invocar `book_index.py generate` para producir `reports/book-index.md`. |
| F117 | `scripts/README.md` | `consolidate.py` catalogado. |

**Wirings colaterales:**

- `SKILL.md` §5.2 — entrada de routing.
- `references/10-quality/README.md` — marca `consolidation-passes.md` como publicado.
- `references/06-writing/anti-patterns.md` §2 — añade **AP26** / **AP27** / **AP28** (28 APs totales).
- `assets/profile.template.yaml` — bloque `consolidation` opcional.
- `schemas/profile.schema.json` — `$defs/consolidation`.

---

## 8. Anti-patrones

F109 introduce **3 anti-patrones nuevos** AP-CON-1..3, todos detectables
algorítmicamente:

| ID | Nombre | Detección | Origen |
|---|---|---|---|
| **AP-CON-1 / AP26** | Pase de consolidación no idempotente | `sha256_output` del mismo pase difiere entre 2 ejecuciones consecutivas de `run-all` (CON-R1 violado) | F109 §4 CON-R1 + §9 V3 |
| **AP-CON-2 / AP27** | Re-ejecución con side-effects | Algún pase modifica un IR/NoteMark/`glossary.json`/etc. fuera de `reports/` + `manifest.json` (CON-R3 violado) | F109 §4 CON-R3 + §9 |
| **AP-CON-3 / AP28** | Término con 2 definiciones canónicas | Pase 2 reporta R3 violation: el mismo alias normalizado aparece en 2 términos del glosario | F109 §3 pase 2 + §9 V2 |

---

## 9. Verificación al cierre

Los **3 criterios del ROADMAP** + **CON-R1..R5** se verifican
algorítmicamente en `evals/consolidation-sample/run_eval.py`:

| Criterio | Sub-eval | Cómo se verifica |
|---|---|---|
| **V1** Sin enlaces rotos ni huérfanos | C1 | Tras `run-all`: `report-link-debt.json` lista los 2 broken-wikilink + 1 orphan; `manifest.json::link_debt[]` tiene 3 entradas nuevas (kind ∈ `broken-wikilink\|missing-target\|orphan-note`). Verifica CON-R4. |
| **V2** Ningún término tiene 2 definiciones canónicas | C2 | `pass-glossary` reporta R3 violation (alias duplicado); `consistency-report.json` reporta AP-BM1 si aplica. Verifica CON-R1 + AP-CON-3. |
| **V3** Re-ejecutable sin side-effects | C3 | `run-all` 2 veces consecutivas; `sha256_output` por pase idéntico. Verifica CON-R1 + AP26. |

**Criterios derivados**:

- **V4.** CON-R2: orden de pases conmutable (verificable intercambiando
  orden en un fixture y comparando `after_sha256`).
- **V5.** CON-R3: ningún pase modifica IRs (verificable con `git diff`
  o checksum de `ir/*.json` antes/después).
- **V6.** CON-R5: pase 5 falla si F108 no disponible; `run-all` aborta con
  `CON_RUN_FAILED`.

---

## 10. Cambios permitidos

- Añadir un nuevo pase en el futuro (orden estable; no reordenar los 5
  existentes).
- Añadir campos opcionales al schema `consolidationRun` (versión menor).
- Extender `link_debt.kind` con nuevos valores (versión menor).

**Reabren F109**: cambiar el orden de los 5 pases, romper CON-R1..R5,
eliminar la idempotencia, modificar inputs sin permiso del agente.

---

## 11. Tabla de auto-verificación

```
python3 scripts/pipeline/consolidate.py --help              # exit 0, 6 sub-comandos
python3 evals/consolidation-sample/run_eval.py             # exit 0, 3/3 PASS
wc -l references/10-quality/consolidation-passes.md        # ≤ 500
wc -l SKILL.md                                              # ≤ 500
python3 -c "import json; json.load(open('schemas/manifest.schema.json'))"  # exit 0
grep -c "AP26\|AP27\|AP28" references/06-writing/anti-patterns.md  # ≥ 3
grep -c "F109" SKILL.md                                     # ≥ 1
grep -c "consolidate" scripts/README.md                     # ≥ 1
grep -c "consolidation" assets/profile.template.yaml        # ≥ 1
```