# `incremental-update` — `references/04-authoring/incremental-update.md`

> Documento normativo de la **Fase 111**. Define el **orquestador de
> actualización incremental** que compara un SDM antiguo con uno nuevo,
> identifica los bloques afectados, marca obsoletos sin borrar, genera
> notas `version-delta` (F88) con el resumen de cambios, y republica
> selectivamente en destinos remotos.
>
> F111 **NO redefine** F16/F13/F31/F88/F38; los consume. La política
> **MIGRATE** de F16 (manifest.md §6) es el disparador principal.
>
> Documentos complementarios:
> - `references/00-pipeline/manifest.md` (F16) — `hash_mismatch` + política MIGRATE.
> - `references/02-source-model/spec.md` (F13) — SDM structure.
> - `references/02-source-model/anchors.md` (F32) — anchors estables (block_id).
> - `scripts/ingest/build_sdm.py` (F31) — produce SDM con `block_id` estable.
> - `references/05-note-types/version-delta.md` (F88) — note-type `version-delta`.
> - `references/03-knowledge/ledger.md` (F15) — `units_processed` + `merged_into`.
> - `SKILL.md` §7.4 — modo "Actualización incremental" (4 archivos; F16 dispara).
>
> Enrutado desde SKILL.md §5.2.

## Índice

1. [Propósito](#1-propósito) · 2. [Cuándo aplica](#2-cuándo-aplica) · 3. [Algoritmo de 5 pasos](#3-algoritmo-de-5-pasos) · 4. [Reglas duras (INC-R1..INC-R5)](#4-reglas-duras-inc-r1inc-r5) · 5. [CLI](#5-cli) · 6. [Wirings cerrados](#6-wirings-cerrados) · 7. [Anti-patrones](#7-anti-patrones) · 8. [Verificación al cierre](#8-verificación-al-cierre) · 9. [Cambios permitidos](#9-cambios-permitidos) · 10. [Ejemplo end-to-end](#10-ejemplo-end-to-end) · 11. [Tabla de auto-verificación](#11-tabla-de-auto-verificación)

---

## 1. Propósito

F111 introduce el **orquestador de actualización incremental** que
materializa el modo §7.4 de SKILL.md. Compara un SDM antiguo con uno
nuevo (mismo source, hash diferente), identifica los bloques afectados,
marca obsoletos sin borrar, genera notas `version-delta` con el resumen
de cambios, y republica selectivamente en destinos remotos.

**Cierra los 3 criterios del ROADMAP** §1787-1791:

1. _Un cambio en una sección reprocesa solo lo afectado_ → §3 + §8 V1.
2. _Se genera el delta automáticamente_ → §3 + §8 V2.
3. _Ninguna nota pierde contenido válido_ → §4 + §8 V3.

**Fuera de alcance:**

- Re-ingerir la fuente (L0); F111 consume SDM ya construido.
- Decidir si aplicar la actualización; el agente confirma (cumple INV-12).
- Eliminar notas obsoletas; F111 las **marca** (`status: archived` + `superseded_by`); nunca las borra.

---

## 2. Cuándo aplica

F111 se activa en uno de:

- **F16 dispara MIGRATE** — el hash del archivo fuente cambia entre 2 sesiones; F111 se invoca con `--strategy migrate`.
- **Manual** — el usuario o el agente invoca `update.py run-all --old-sdm A.json --new-sdm B.json --workdir DIR` cuando quiere comparar 2 SDMs del mismo source.

**Exclusiones**:

- SDMs con `source.id` distinto → exit 2 con `INC_SOURCE_MISMATCH`.
- SDMs sin `blocks[]` → exit 2 con `INC_NO_SDM`.

---

## 3. Algoritmo de 5 pasos

`update.py run-all` ejecuta **5 pasos cerrados**:

### Paso 1 — Diff de SDMs

Compara `old_sdm.blocks[]` vs `new_sdm.blocks[]` por `block_id`. Resultado:

- **`added`** — presente en `new` pero no en `old`.
- **`removed`** — presente en `old` pero no en `new`.
- **`modified`** — presente en ambos pero `text` (o `attrs`) difiere.
- **`unchanged`** — presente en ambos e idéntico.

Algoritmo: indexar `old.blocks[]` por `block_id`; iterar `new.blocks[]`.

### Paso 2 — Agrupación por sección

Los blocks en `added`/`removed`/`modified` se agrupan por `section_path`
para producir rangos contiguos. Cada grupo de cambios genera **1 entrada
en el version-delta**.

### Paso 3 — Identificar IRs afectados

Para cada `section_path` afectado:
1. Lee `manifest.json::published_notes[]` para obtener los destinos.
2. Recorre `ir/*.json` (F14 IRs) y para cada IR encuentra los
   `source_refs[]` cuyo `section_path` coincide.
3. Si un IR tiene ≥ 1 `source_ref` en una sección afectada → IR afectado.
4. Si el IR tiene `source_refs[]` solo en blocks `removed` → IR obsoleto
   (candidato a archivar).
5. Si el IR tiene `source_refs[]` en blocks `modified` o `added` → IR
   re-procesable (candidato a `--force`).

### Paso 4 — Marcar obsoletos sin borrar

Para cada IR obsoleto:
- Lee el IR; **no borra** el archivo.
- Añade `superseded_by: <new_note_id>` en `frontmatter` (donde
  `<new_note_id>` se infiere del bloque `added` en la misma sección;
  si no hay bloque `added`, `superseded_by` queda como `null`).
- Cambia `frontmatter.status` a `"archived"`.
- Preserva todos los `source_refs[]` originales (INC-R2).
- Escribe IR con `_atomic_write_json` + `.bak`.

Para cada IR re-procesable:
- Si la política del agente es `--force`, marca `previous_processed_at`
  y guarda el IR (INC-R5; análogo a F106 AP-BM4).
- Si la política es `--no-force`, omite el re-proceso.

### Paso 5 — Generar version-delta + republicar selectivamente

Por cada sección afectada, **genera 1 archivo** `<workdir>/ir/<delta_id>.note-ir.json`
con `note_type: "version-delta"` (F88) y la siguiente estructura:

```jsonc
{
  "schema_version": "1.0.0",
  "delta_id": "vd0001",
  "source_id": "<source.id>",
  "old_source_hash": "<sha256 old>",
  "new_source_hash": "<sha256 new>",
  "version": "1.0",                      // semver extraído del SDM si presente
  "created_at": "ISO 8601",
  "affected_chapters": ["ch01", "ch02"],
  "changes": [
    {
      "version": "1.0",
      "change_type": "modified",          // added | removed | modified | moved
      "description": "Sección X modificada",
      "section_path": "/ch02/intro",
      "block_ids": ["abc123..."]
    }
  ],
  "affected_ir_ids": ["note-a", "note-b"],
  "obsoleted_ir_ids": ["note-old"],
  "frontmatter": { ... }                   // para F88 / F47
}
```

Después de generar los version-delta, **republica selectivamente**:
- Para cada IR en `affected_ir_ids`, republica en los destinos donde
  `manifest.json::published_notes[]` lo registre (INC-R4).
- Destinos no afectados NO se tocan.

---

## 4. Reglas duras (INC-R1..INC-R5)

- **INC-R1** — Diff a **nivel de bloque** (`block_id`); nunca a nivel de página o nota. Reduce espacio de búsqueda.
- **INC-R2** — `obsolete_mark` **NO borra** archivos; solo añade `superseded_by` + cambia `status` a `archived`. `source_refs[]` se preserva.
- **INC-R3** — `version-delta` se genera **automáticamente** desde las diferencias detectadas; el agente puede editar el `description` post-generación (es información con marcado editable).
- **INC-R4** — Re-publicación **selectiva**: solo `affected_ir_ids ∩ published_destinations`; destinos no afectados no se tocan.
- **INC-R5** — `previous_processed_at` se preserva en IRs re-procesados (análogo a F106 AP-BM4).

---

## 5. CLI

```bash
update.py diff --old-sdm OLD.json --new-sdm NEW.json [--json-out PATH]
update.py dry-run --old-sdm OLD.json --new-sdm NEW.json --workdir DIR
update.py run-all --old-sdm OLD.json --new-sdm NEW.json --workdir DIR [--yes] [--force]
update.py status --workdir DIR [--json]
```

Códigos:
- **0** — OK (diff/dry-run/run-all/status exitoso).
- **1** — Validación (INC-R1..R5 violado, schema inválido, partial run failed).
- **2** — Uso (paths faltantes, INC_NO_SDM, INC_SOURCE_MISMATCH).

Dependencias: Python 3.9+ stdlib puro (sin `jsonschema`, sin red).

---

## 6. Wirings cerrados

| Fase | Archivo | Relación |
|---|---|---|
| F13 | `references/02-source-model/spec.md` | F111 consume SDM (`sdm.json::blocks[]`). |
| F16 | `references/00-pipeline/manifest.md` §6 | Política MIGRATE dispara F111. |
| F31 | `scripts/ingest/build_sdm.py` | SDM con `block_id` estable (F32) entra a F111. |
| F32 | `references/02-source-model/anchors.md` | Anchors estables garantizan diff confiable. |
| F88 | `references/05-note-types/version-delta.md` | F111 genera instancias de este note-type. |
| F15/F38 | `references/03-knowledge/ledger.md` | `units_processed` + `merged_into` para tracking. |
| F62 | `references/08-render/publishing.md` | F111 republica selectivamente (reusa el motor de F62). |
| F117 | `scripts/README.md` | `diff/update.py` catalogado. |

**Wirings colaterales**:

- `SKILL.md` §5.2 — entrada de routing.
- `references/04-authoring/README.md` — marca `incremental-update.md` como publicado.
- `references/06-writing/anti-patterns.md` §2 — añade **AP32** / **AP33** / **AP34**.
- `assets/profile.template.yaml` — bloque `incremental_update` opcional.
- `schemas/profile.schema.json` — `$defs/incremental_update`.

---

## 7. Anti-patrones

F111 introduce **3 anti-patrones nuevos** AP-INC-1..3:

| ID | Nombre | Detección | Origen |
|---|---|---|---|
| **AP-INC-1 / AP32** | Reproceso completo por cambio pequeño | Tras diff, el script marca obsoletos todos los IRs del workdir (no solo los afectados). Verificable: `len(obsoleted_ir_ids) == total_ir_count` cuando `len(affected_ir_ids) < total_ir_count` | F111 §3 paso 4 + §8 V1 |
| **AP-INC-2 / AP33** | Delta no generado | Tras `run-all`, no hay archivos `ir/<delta_id>.note-ir.json` en el workdir; o el archivo no tiene `note_type == "version-delta"` | F111 §3 paso 5 + §8 V2 |
| **AP-INC-3 / AP34** | Nota válida eliminada por obsoleto | Tras `run-all`, existe un IR con `source_refs[]` originales PERO el archivo fue borrado (no existe en filesystem); o `status: archived` SIN `superseded_by` poblado | F111 §3 paso 4 + §8 V3 |

---

## 8. Verificación al cierre

Los **3 criterios del ROADMAP** + **INC-R1..R5** se verifican algorítmicamente en `evals/incremental-sample/run_eval.py`:

| Criterio | Sub-eval | Cómo se verifica |
|---|---|---|
| **V1** Un cambio reprocesa solo lo afectado | C1 | Tras `run-all`: solo los IRs en `affected_ir_ids` tienen `status: archived` o `superseded_by` poblado; IRs no afectados mantienen `status: done` sin cambios |
| **V2** Delta generado automáticamente | C2 | Existe al menos 1 `ir/<delta_id>.note-ir.json` con `note_type == "version-delta"` + `changes[]` con ≥ 1 entrada por sección afectada |
| **V3** Ninguna nota pierde contenido válido | C3 | Los IRs no obsoletos mantienen sus `source_refs[]` originales byte-a-byte; los obsoletos NO se borran del filesystem y tienen `superseded_by` poblado |

---

## 9. Cambios permitidos

- Añadir nuevos campos opcionales al schema `VersionDelta` (versión menor).
- Añadir nuevo `change_type` al enum (versión menor; requiere actualizar `evals/incremental-sample`).
- Cambiar la política `auto_invoke_on_hash_mismatch` (cumple INV-12).

**Reabren F111**: cambiar INC-R2 (borrar en vez de archivar), cambiar INC-R1 (diff a nivel de página), cambiar el formato de `version-delta` que rompa compat con F88.

---

## 10. Ejemplo end-to-end

```bash
# Pre: existe workdir con SDM viejo + IRs publicados en obsidian.
$ python3 scripts/diff/update.py diff \
    --old-sdm sources/postgres-16-v15.json \
    --new-sdm sources/postgres-16-v16.json \
    --json-out reports/diff-2026-09-30.json
{
  "added": [{"block_id": "b99999...", "section_path": "/ch13/new"}],
  "removed": [{"block_id": "a11111...", "section_path": "/ch05/old"}],
  "modified": [{"block_id": "a22222...", "section_path": "/ch07/main"}],
  "affected_sections": ["/ch05/old", "/ch07/main", "/ch13/new"],
  "affected_ir_ids": ["postgres-mvcc-v15", "postgres-config"]
}

$ python3 scripts/diff/update.py run-all \
    --old-sdm sources/postgres-16-v15.json \
    --new-sdm sources/postgres-16-v16.json \
    --workdir .notes-work/postgres --yes
OK — run-all (5 pasos; 2 obsoletos; 1 version-delta generado; 2 republicados en obsidian)
```

Tras `run-all`:
- `postgres-mvcc-v15.note-ir.json` → `status: archived`, `superseded_by: "postgres-mvcc-v16"`.
- `ir/vd0001.note-ir.json` → `note_type: version-delta`, tabla `## Cambios` con 3 filas.
- `manifest.json::published_notes` actualiza `last_updated` para los 2 IRs republicados.

---

## 11. Tabla de auto-verificación

```
python3 scripts/diff/update.py --help                  # exit 0, 4 sub-comandos
python3 evals/incremental-sample/run_eval.py           # exit 0, 3/3 PASS
wc -l references/04-authoring/incremental-update.md    # ≤ 500
wc -l SKILL.md                                          # ≤ 500
python3 -c "import json; json.load(open('schemas/version-delta.schema.json'))"  # exit 0
grep -c "AP32\|AP33\|AP34" references/06-writing/anti-patterns.md  # ≥ 3
grep -c "F111" SKILL.md                                # ≥ 1
grep -c "diff/update\|update.py" scripts/README.md      # ≥ 1
grep -c "incremental_update" assets/profile.template.yaml  # ≥ 1
```