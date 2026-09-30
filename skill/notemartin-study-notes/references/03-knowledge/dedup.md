# `references/03-knowledge/dedup.md` — Deduplicación y fusión

> Documento normativo de la **Fase 108**. Define el **detector de
> duplicados** (criterio canónico / alias / similitud textual) y el
> **orquestador de apply** que conecta el output del detector con el
> motor de F50 (`scripts/authoring/transform.py`) para ejecutar las
> acciones `merge` / `specialize` / `split` preservando `source_refs`
> y redirigiendo enlaces entrantes.
>
> F108 **NO redefine** F40/F41/F50/F43/F47/F16; orquesta el detector sobre
> F50 y emite entradas `link_debt[].redirected` en `manifest.json`.
>
> Documentos complementarios:
> - `references/03-knowledge/terminology.md` (F40) — glosario canónico + aliases.
> - `references/03-knowledge/conflicts.md` (F41) — conflictos irreconciliables (F108 deriva allí si la similitud es alta pero las definiciones divergen).
> - `scripts/authoring/transform.py` (F50) — `merge` / `split` / `dedup` a nivel IR.
> - `scripts/validate/completeness.py` (F43) — auditoría antes/después del merge.
> - `references/00-pipeline/manifest.md` (F16) — `link_debt[]` actualizado.
> - `references/00-pipeline/book-mode.md` (F106) §7 paso 1 invoca `detect.py` en consolidación.
> - `references/00-pipeline/chunk-loop.md` (F107) §9 wirings.
>
> Enrutado desde SKILL.md §5.2.

## Índice

1. [Propósito](#1-propósito) · 2. [Cuándo aplica](#2-cuándo-aplica) · 3. [Las 3 acciones](#3-las-3-acciones-merge--specialize--split) · 4. [El detector](#4-el-detector--algoritmo-de-4-pasos) · 5. [El orquestador de apply](#5-el-orquestador-de-apply) · 6. [Reglas duras (DEDUP-R1..R5)](#6-reglas-duras-dedup-r1r5) · 7. [Integración con F106/F107](#7-integración-con-f106f107) · 8. [Wirings cerrados](#8-wirings-cerrados) · 9. [Anti-patrones](#9-anti-patrones) · 10. [Verificación al cierre](#10-verificación-al-cierre)

---

## 1. Propósito

F108 introduce el **detector de duplicados** y un **orquestador de apply**
que conectan el output del detector con el motor de F50
(`transform.py merge/split`). El detector identifica pares (o grupos) de
notas candidatas a:

- **`merge`** — dos notas esencialmente idénticas → fusionar en una sola.
- **`specialize`** — una nota es subconjunto estricto de la otra → quedarse con la general; producir nota "sister" con back-link bidireccional.
- **`split`** — una nota cubre múltiples temáticas no relacionadas → dividir en 2+ notas (F50 ya lo cubre con `--at-heading`).

**Cierra los 3 criterios del ROADMAP** §1763-1767:

1. _Una fusión no pierde ninguna unidad de las notas originales_ → §6 DEDUP-R1 + §10 V1 (cumple F50 `merged_refs ⊇ original_union`).
2. _Los enlaces entrantes siguen funcionando_ → §6 DEDUP-R2 + DEDUP-R4 + §10 V2 (cumple F50 `_rewrite_links_in_workdir` + `manifest.json::link_debt[]`).
3. _El detector encuentra duplicados inyectados a propósito_ → §4 + §10 V3 (recall ≥ 80% en `evals/dedup-sample/`).

**Fuera de alcance:**

- Redefinir el motor de transformación (F50); F108 lo invoca por subproceso.
- Detección de conflictos (F41); si `similarity ≥ threshold` pero las definiciones divergen, F108 deriva a F41 y emite `suggested_action: "conflict"`.
- Decidir si aplicar el merge automáticamente; F108 emite candidatos; el agente revisa y aplica con `--yes` (cumple INV-12).

---

## 2. Cuándo aplica

El detector se activa opcionalmente cuando se cumple **alguna** de las
siguientes condiciones:

- El corpus tiene **≥ 5 notas** con `frontmatter.note-type` ∈ {`concept`, `glossary-term`, `procedure`, `api-reference`} (umbral configurable; `MIN_NOTES_TO_RUN = 5`).
- `book-mode.py consolidate` lo invoca (`--strategy consolidate`).
- El usuario o el agente lo solicita explícitamente.

**Excepciones explícitas** (no activar):

- Corpus < 5 notas (el detector emite `DEDUP_CORPUS_TOO_SMALL` exit 2).
- Corpus donde el usuario marcó `dedup.enabled: false` en `profile.yaml`.
- Corpus donde F41 ya marcó conflictos no resueltos (F108 deriva a F41).

---

## 3. Las 3 acciones (`merge` / `specialize` / `split`)

Tabla cerrada:

| Acción | Definición | Resultado | Garantía |
|---|---|---|---|
| `merge` | 2+ notas con mismo concepto canónico | 1 nota con `source_refs` unión + frontmatter `aliases` unión + `manifest.json::link_debt[].redirected` por cada ID viejo | `merged_refs ⊇ pre-merge union` (F50 §merge línea 453) |
| `specialize` | Nota A cubre subconjunto estricto de B | B se queda + nota "sister" C con back-link bidireccional `[[note:B]] ↔ [[note:C]]` | `source_refs(B ∪ C) ⊇ source_refs(A)` |
| `split` | 1 nota con ≥ 2 temáticas no relacionadas | N notas con `source_refs` particionados por sección | `source_refs(∪Notas) ⊇ source_refs(original)` (F50 §split) |

**Detección de conflicto (F41 derivación)**: si `similarity ≥ threshold`
pero `difflib.SequenceMatcher` entre las `## Definición` (concept) o
`## Resumen` (otros) es < 0.3 con ratio bajo en ambos sentidos, F108 emite
`suggested_action: "conflict"` y **NO** propone `merge`.

---

## 4. El detector — algoritmo de 4 pasos

El script `scripts/dedup/detect.py` implementa el siguiente algoritmo
sobre todos los IRs del workdir:

### Paso 1 — Canonical match (F40)

Para cada par de notas `(A, B)` del mismo `note-type`, compara sus
términos canónicos (extraídos de `glossary.json`). Score = 1.0 si
comparten canónico; 0.0 en caso contrario.

### Paso 2 — Alias match (F40 + F47 §5.17)

Compara:
- `note.frontmatter.aliases[]` (F47 §5.17).
- `glossary.terms[].aliases[].alias` (F40).

Score = 1.0 si comparten ≥ 1 alias normalizado (lowercase, kebab-case);
0.0 en caso contrario.

### Paso 3 — Textual similarity

`difflib.SequenceMatcher.ratio()` entre la `## Definición` (concept) o
`## Resumen` (otros tipos) de las dos notas. Score ∈ [0, 1].

### Paso 4 — Combined score + decisión

`combined_score = max(canonical, alias, similarity)`. Override: si
`similarity < 0.5` y no hay match canónico ni alias, el par se descarta
(no se reporta).

Output: JSON `candidates.json` con la estructura:

```jsonc
[
  {
    "pair": ["note-a-id", "note-b-id"],
    "scores": {
      "canonical": 0.0,
      "alias": 1.0,
      "similarity": 0.85,
      "combined": 1.0
    },
    "suggested_action": "merge",
    "confidence": 0.95,
    "rationale": "alias match (MVCC); similarity 0.85"
  }
]
```

**Constante clave**: `DEFAULT_SIMILARITY_THRESHOLD = 0.6` (configurable
vía `--threshold` o `profile.yaml::dedup.similarity_threshold`).

---

## 5. El orquestador de apply

El script `scripts/dedup/apply.py` envuelve F50 `transform.py` por
**subproceso** (aislamiento; F50 no expone API Python estable). Tres
sub-comandos:

### `apply merge --a A.json --b B.json --output C.json --workdir DIR [--irs-glob 'ir/*.json'] [--dry-run]`

Invoca:
```
python3 transform.py merge --irs A.json B.json --output C.json \
    --workdir DIR --irs-glob 'ir/*.json'
```

Tras el apply, actualiza `manifest.json::link_debt[]` con 1 registro
`redirected` por cada ID viejo. Verifica DEDUP-R1 (re-visa `merged_refs`).
Verifica DEDUP-R3 (lee `C.json` y comprueba `frontmatter.aliases`
contiene los IDs viejos).

### `apply specialize --parent P.json --child C.json --workdir DIR [--irs-glob 'ir/*.json'] [--dry-run]`

1. Lee `P.json`; extrae el subconjunto que cubre `C.json` (heurística:
   bloques cuyo `text` matchea con `C.## Definición` con ratio ≥ 0.6).
2. Invoca `transform.py split --ir P.json --at-heading <heading> --output <new>.json`.
3. Crea nota "sister" con back-link bidireccional.

### `apply split --ir A.json --at-heading H1 [--at-heading H2 ...] --output B.json --workdir DIR [--irs-glob 'ir/*.json'] [--dry-run]`

Wrapper directo de `transform.py split`.

---

## 6. Reglas duras (DEDUP-R1..R5)

- **DEDUP-R1** — `merged_refs.issuperset(original_union)` (delegado a F50);
  el orquestador **falla con exit 1** si F50 reporta `ERROR: source_refs
  perdidos` o si la verificación post-merge detecta pérdida. Anti-pattern
  **AP23 / AP-DEDUP-1**.
- **DEDUP-R2** — `_rewrite_links_in_workdir` (F50) se invoca con
  `--irs-glob` obligatorio cubriendo `ir/*.json` + `notemark/*.nm`; si
  no se pasa, `apply merge` aborta con exit 2. Anti-pattern **AP24 /
  AP-DEDUP-2**.
- **DEDUP-R3** — Tras el merge, `frontmatter.aliases` de la nota
  fusionada contiene los IDs viejos (verificable).
- **DEDUP-R4** — Una entrada `link_debt[].kind = "redirected"` se registra
  en `manifest.json` por cada ID viejo redirigido; `from_note = old_id`,
  `target = new_id`, `detected_at = ISO8601`.
- **DEDUP-R5** — `apply split` requiere ≥ 2 `--at-heading`; aborta con
  exit 2 si no.

---

## 7. Integración con F106/F107

- **`book-mode.py consolidate`** — invoca `detect.py --strategy consolidate`
  sobre los capítulos del rango `[last+1 .. current]`. Si encuentra
  candidatos, emite hint; el agente decide aplicar.
- **`chunk-loop.py consolidate`** — invoca `detect.py --strategy single-chunk`
  por chunk. (Declarado en F107 §9; cierre cuando F106/F107 se reabran.)

---

## 8. Wirings cerrados

| Fase | Archivo | Relación |
|---|---|---|
| F16 | `references/00-pipeline/manifest.md` + `schemas/manifest.schema.json` | `apply merge` actualiza `link_debt[].kind = "redirected"`. |
| F40 | `references/03-knowledge/terminology.md` | Detector consume `glossary.terms[]` para canonical + alias match. |
| F41 | `references/03-knowledge/conflicts.md` | F108 deriva aquí cuando `similarity ≥ threshold` pero divergencia detectada. |
| F43 | `scripts/validate/completeness.py` | `apply merge` invoca `completeness.py --before --after` para verificar DEDUP-R1. |
| F47 | `references/04-authoring/properties.md` §5.17 | Detector consume `frontmatter.aliases[]` (F47 §5.17). |
| F50 | `scripts/authoring/transform.py` | `apply` invoca `transform.py merge/split` por subproceso. |
| F106 | `references/00-pipeline/book-mode.md` §7 paso 1 | Book-mode invoca `detect.py --strategy consolidate`. |
| F107 | `references/00-pipeline/chunk-loop.md` §9 | Wirings declarados. |
| F117 | `scripts/README.md` | `detect.py` + `apply.py` catalogados. |

**Wirings colaterales:**

- `SKILL.md` §5.2 — entrada de routing.
- `references/03-knowledge/README.md` — marca `dedup.md` como publicado.
- `references/06-writing/anti-patterns.md` §2 — añade **AP23** / **AP24** / **AP25** (25 APs totales).
- `assets/profile.template.yaml` — bloque `dedup` opcional.
- `schemas/profile.schema.json` — `$defs/dedup`.
- `scripts/README.md` — entradas del catálogo.

---

## 9. Anti-patrones

F108 introduce **3 anti-patrones nuevos** AP-DEDUP-1..3 (mapeo a AP23/24/25
en `anti-patterns.md`), todos detectables algorítmicamente:

| ID | Nombre | Detección | Origen |
|---|---|---|---|
| **AP-DEDUP-1 / AP23** | Fusión con pérdida de unidades | `merged_refs ⊉ original_union` (F50 detecta; orquestador aborta con exit 1) | F108 §6 DEDUP-R1 + §10 |
| **AP-DEDUP-2 / AP24** | Enlace entrante no redirigido | Tras `apply merge`, existe IR con `[[note:old_id]]` que NO se ha reescrito | F108 §6 DEDUP-R2 + §10 |
| **AP-DEDUP-3 / AP25** | Detector omite duplicado canónico | Recall < 80% en fixture de 5 pares inyectados | F108 §4 + §10 V3 |

---

## 10. Verificación al cierre

Los **3 criterios del ROADMAP** + **DEDUP-R1..R5** se verifican
algorítmicamente en `evals/dedup-sample/run_eval.py`:

| Criterio | Sub-eval | Cómo se verifica |
|---|---|---|
| **V1** Una fusión no pierde ninguna unidad de las notas originales | C1 | `apply merge` sobre par A+B; F43 `completeness.py --before <snapshot> --after <post-merge-state>` verifica `must_keep_units_before ⊆ must_keep_units_after`. Verifica DEDUP-R1. |
| **V2** Los enlaces entrantes siguen funcionando | C2 | Tras merge A+B→C: `grep -RE '\[\[note:(a\|b)\]\]' ir/` → 0 matches; `manifest.json::link_debt` tiene 2 entradas (`from_note: a, b`; `kind: redirected`; `target: c`). Verifica DEDUP-R2 + DEDUP-R4. |
| **V3** El detector encuentra duplicados inyectados a propósito | C3 | `detect scan --workdir` sobre fixture de 5 pares inyectados: recall ≥ 4/5, false positive rate ≤ 1/10. Verifica AP-DEDUP-3. |

**Criterios derivados** (también verificados):

- **V4.** DEDUP-R3: tras merge, `frontmatter.aliases` de C contiene A y B.
- **V5.** DEDUP-R5: `apply split` con 1 solo `--at-heading` → exit 2.
- **V6.** Idempotencia: `apply merge` sobre el mismo par 2 veces → la 2ª aborta con exit 1 (no es trivial merge; la nota target ya existe).
- **V7.** Composicional: `detect.py` es invocable standalone y desde F106/F107 (mismas flags: `--strategy consolidate|single-chunk|default`).

**Tabla de auto-verificación:**

```
python3 scripts/dedup/detect.py --help                  # exit 0, 4 sub-comandos
python3 scripts/dedup/apply.py --help                   # exit 0, 3 sub-comandos
python3 evals/dedup-sample/run_eval.py                  # exit 0, 3/3 PASS
wc -l references/03-knowledge/dedup.md                  # ≤ 500
wc -l SKILL.md                                          # ≤ 500
python3 -c "import json; json.load(open('evals/dedup-sample/expected/candidates.json'))"  # exit 0
grep -c "AP23\|AP24\|AP25" references/06-writing/anti-patterns.md  # ≥ 3
grep -c "F108" SKILL.md                                 # ≥ 1
grep -c "dedup" scripts/README.md                        # ≥ 1
grep -c "dedup" assets/profile.template.yaml            # ≥ 1
```