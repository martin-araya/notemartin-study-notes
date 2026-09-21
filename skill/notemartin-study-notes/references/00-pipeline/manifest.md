# Manifiesto reanudable — `references/00-pipeline/manifest.md`

> Documento normativo de la Fase 16 del roadmap. Define el formato del manifiesto que el workdir persiste para permitir interrumpir y retomar sin reprocesar. Schema JSON formal en [`schemas/manifest.schema.json`](../../../../schemas/manifest.schema.json).
>
> Documentos complementarios: `skills/AGENT.md` §13 (forma canónica), `references/00-pipeline/architecture.md` §4 (workdir per-fuente: `manifest.json` raíz), §6 (contrato del hash sha256), `references/00-pipeline/responsibilities.md` línea 194 (responsabilidad de F16), `references/02-source-model/spec.md` §7 (campos `source` en SDM, mismo hash pattern), `references/03-knowledge/ledger.md` §4 (entradas que `units_processed` referencia).
>
> Enrutado desde N2: `docs/skill-anatomy.md` §6 fila `F16`. Lo actualizan L0 al arrancar, L1 al cerrar la etapa, L2 al consolidar el ledger, L3 al cerrar una nota, L4 al publicar (`F62`). Lo lee el script de F118 (suite de evals) para reproducir el estado.

## §1 · Propósito y alcance

El manifiesto es el **estado persistente y reanudable** del workdir. Captura lo suficiente para que una sesión interrumpida pueda continuar sin re-procesar lo ya hecho, y para que un cambio en la fuente (hash distinto) sea explícitamente visible en lugar de una corrupción silenciosa.

Lo que el manifiesto **es**: el snapshot final de cada etapa + el conjunto de notas ya publicadas por destino + los identificadores remotos + el glosario acumulado + las decisiones de nomenclatura + la deuda de enlaces. Lo que el manifiesto **no es**: el SDM (F13), el IR (F14), ni el ledger (F15) — son artefactos distintos que el manifiesto referencia pero no contiene.

## §2 · Cuándo se aplica

- L0 al arrancar: escribe `current_stage: "l0"`, `stage_progress.l0: "in_progress"`, registra `source.hash`.
- L1, L2, L3, L4 al cerrar cada etapa: actualiza `stage_progress.<X>: "done"` y `current_stage: "<X+1>"`.
- L4 al publicar una nota: añade `published_notes[]` con `remote_id` + `remote_url?` + `etag?` + `published_at` + `last_updated`.
- L4 al republicar: actualiza `last_updated` y (opcionalmente) `etag` de la entrada existente; no añade duplicado.
- L2 al consolidar glosario: actualiza `glossary`.
- F43 al detectar enlace roto: añade `link_debt[]`.
- F118 al validar: lee el manifiesto y reproduce el estado para tests automatizados.

**No se aplica a:** ingesta cruda (L0 produce regiones, no manifest), ni a la validación del IR (eso es F49).

## §3 · Reglas duras (invariantes)

| ID | Invariante | Si se omite… |
|---|---|---|
| **M-01** | El manifiesto se escribe con atomic write (tmp + rename). | Un crash a mitad deja un archivo corrupto o parcialmente escrito. |
| **M-02** | Reprocesar la misma fuente con el mismo `source.hash` no duplica `published_notes`. La idempotencia se enforza por el par `(note_id, destination)`. | Una sesión interrumpida y reanudada publica dos veces la misma nota. |
| **M-03** | Si el hash actual del archivo difiere del registrado en `source.hash`, se marca `hash_mismatch: true` y se activa la política §6. El pipeline NO continúa automáticamente. | La fuente cambia silenciosamente y el manifiesto miente. |
| **M-04** | Las etapas avanzan secuencialmente (`l0 done` antes de `l1 in_progress`; idem para el resto). | Una etapa salta trabajo de la anterior. |
| **M-05** | `last_modified` se actualiza en cada escritura atómica. | Trazabilidad temporal rota; no se sabe cuándo cambió el estado. |
| **M-06** | `published_notes[*].remote_id` es siempre obligatorio (no `null`). Sin remote_id no hay idempotencia. | Una re-publicación crea un duplicado remoto. |

## §4 · Forma del manifiesto

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `schema_version` | string (const `1.0.0`) | sí | Versión del esquema. |
| `source` | object | sí | `{ id, path, hash (sha256 hex 64), algorithm: "sha256", version?, vendor?, product? }`. |
| `current_stage` | enum | sí | `none`, `l0`, `l1`, `l2`, `l3`, `l4`. Etapa en curso. |
| `stage_progress` | object | sí | Mapa `l0..l4 → pending\|in_progress\|done`. |
| `units_processed` | int ≥ 0 | no | Cuenta del ledger en estado terminal. |
| `published_notes` | array | sí | Lista de `{ note_id, destination, remote_id, remote_url?, etag?, published_at, last_updated }`. |
| `glossary` | object | no | Mapa término → descripción. Acumulado de L2. |
| `naming_decisions` | array | no | Lista de `{ entity, decision, rationale }`. |
| `link_debt` | array | no | Lista de `{ from_note, target, kind, detected_at }`. |
| `hash_mismatch` | bool | no (default false) | true cuando el hash actual difiere del registrado. |
| `last_modified` | date-time | sí | ISO 8601. |

`published_notes[*].destination` ∈ `{obsidian, notion, appflowy, markdown, html, pdf, anki}` (los 7 destinos declarados en `references/08-render/capability-matrix.md`).

`link_debt[*].kind` ∈ `{broken-wikilink, missing-target, redirected, external-dead}`:
- `broken-wikilink`: `[[note:xxx]]` con `xxx` que no existe en el corpus.
- `missing-target`: target es `null` o vacío.
- `redirected`: el destino existía pero cambió de ID (e.g., renombrado).
- `external-dead`: URL externa que no responde al comprobador de F118.

## §5 · Etapas y transiciones

```
none ────► l0:pending ────► l0:in_progress ────► l0:done ────► l1:pending ────► …
                                                ▲
                                                │
                              (L0 done) ◄─────┘
```

Transiciones permitidas:

- `none → l0:pending` al arrancar la fuente.
- `l<N>:pending → l<N>:in_progress → l<N>:done` durante el procesamiento.
- `l<N>:done → l<N+1>:pending` al cerrar la capa anterior.
- `l4:done → (sin transición; el manifest se cierra con `current_stage: "l4"`).

**No se permite** saltar etapas (`l0 pending` → `l1 in_progress` sin `l0 done`). Si una capa necesita re-procesar, vuelve a `in_progress` de su propia etapa (no salta hacia atrás para reprocesar la anterior; para eso está la regeneración del SDM en F31).

## §6 · Política ante cambio de hash

`architecture.md` §6 dice: "si el hash difiere entre dos sesiones sobre el mismo path, F16 dispara acción explícita (reanudar bloquea hasta decisión)". Esta sección materializa esa acción en tres políticas posibles, elegibles por el agente o el usuario:

| Política | Comportamiento |
|---|---|
| **REJECT** (default) | El script aborta la sesión. El usuario decide qué hacer. El manifiesto conserva `hash_mismatch: true` hasta intervención manual. |
| **RESET** | Archivar el manifiesto viejo como `manifest.json.bak-<timestamp>`. Empezar de cero desde L0. Las notas ya publicadas en destinos remotos siguen allí; la idempotencia por `remote_id` evita duplicación cuando se vuelve a publicar. |
| **MIGRATE** | Comparar `block_ids` del SDM actual contra el SDM viejo (si existe). Para cada bloque: si está en el viejo y no en el nuevo → marcar como `removed` en el ledger; si está en el nuevo y no en el viejo → procesarlo; si está en ambos → continuar normalmente. |

**Default: REJECT.** Razones:

- RESET puede destruir trabajo en curso; el usuario lo decide.
- MIGRATE requiere lógica de diff que es trabajo de F31 (build_sdm), no de F16.
- REJECT es la única política conservadora por defecto que no corrompe el estado sin intervención explícita.

Activación:

```bash
# Al arrancar la sesión sobre una fuente ya procesada:
sha256sum source.html
# Compara con manifest.source.hash:
jq -r .source.hash manifest.json
# Si difieren, el script setea hash_mismatch=true y aplica la política configurada.
```

Política configurable en `profile.yaml` (F11), clave `manifest.hash_policy` ∈ `{reject, reset, migrate}`. Default `reject`. Si la clave no existe o el perfil es mínimo, se aplica el default.

## §7 · Idempotencia

Tres casos de re-uso:

1. **Reprocesar la misma fuente, mismo hash, misma sesión interrumpida.** El agente lee `current_stage` + `stage_progress`, salta lo ya hecho, continúa en la capa pendiente. No se duplica trabajo.

2. **Republicar la misma nota en el mismo destino.** La entrada ya existe en `published_notes[]` con el mismo `(note_id, destination)`. La actualización toca `remote_id` (si el destino asignó un nuevo ID), `etag` (si el destino lo soporta), `last_updated`. No se añade una segunda entrada.

3. **Republicar la misma nota en un destino distinto.** Se añade una nueva entrada con el mismo `note_id` y un `destination` distinto. No se modifica la entrada existente.

Caso de duplicado accidental (mismo `(note_id, destination)` dos veces en el array): el schema lo rechaza. La librería `jsonschema` reporta el índice de la entrada duplicada.

**Diferencia entre re-publicar y duplicar:**

- Re-publicar: misma nota, mismo destino, contenido actualizado. Idempotente por `remote_id` + `etag`.
- Duplicar: misma nota, contenido copiado a otra nota. NO es el caso de uso del manifiesto; si necesitas dos notas del mismo tema, crea `note_id` distinto.

## §8 · Glosario acumulado

`glossary` es un mapa `término → descripción`. Lo actualiza L2 cuando consolida el `knowledge/glossary.json`. El manifiesto lo refleja en cada cierre de capa.

Las claves duplicadas sobrescriben (semántica del JSON). Si el agente introduce dos definiciones para el mismo término, gana la última; el spec recomienda avisar al usuario en lugar de sobrescribir silenciosamente.

`glossary` no reemplaza al `glossary.json` de L2. El `glossary.json` es el artefacto canónico; el del manifiesto es el snapshot que el resume (F118) lee sin tocar L2.

## §9 · Ejemplo de manifiesto

```json
{
  "schema_version": "1.0.0",
  "source": {
    "id": "01-postgresql-chapter",
    "path": "/Users/martin/Desktop/projects/notemartin-study-notes/sources/01-postgresql-chapter.html",
    "hash": "a8f4ce1405802cacbb35e6fb88f5e3cf138a4e872910cdfd276f378f13371657",
    "algorithm": "sha256",
    "version": "16",
    "vendor": "PostgreSQL Global Development Group",
    "product": "PostgreSQL 16"
  },
  "current_stage": "l4",
  "stage_progress": {
    "l0": "done", "l1": "done", "l2": "done", "l3": "done", "l4": "done"
  },
  "units_processed": 7,
  "published_notes": [
    {
      "note_id": "postgres-shared-buffers",
      "destination": "obsidian",
      "remote_id": "abc123-page-uuid",
      "remote_url": "obsidian://vault/notes/postgres-shared-buffers.md",
      "etag": null,
      "published_at": "2026-09-21T19:00:00Z",
      "last_updated": "2026-09-21T19:00:00Z"
    }
  ],
  "glossary": {
    "shared-buffers": "Región de memoria compartida usada como buffer pool.",
    "mvcc": "Control de concurrencia multiversión."
  },
  "naming_decisions": [
    {
      "entity": "note-id",
      "decision": "kebab-case",
      "rationale": "Coherencia con corpus y legibilidad en destinos."
    }
  ],
  "link_debt": [],
  "hash_mismatch": false,
  "last_modified": "2026-09-21T19:30:00Z"
}
```

## §10 · Anti-patrones

- ~~Edición manual del manifiesto sin atomic write~~ → corrompe en crash; M-01 lo prohíbe.
- ~~`published_notes` con dos entradas para el mismo `(note_id, destination)`~~ → el schema lo rechaza.
- ~~Continuar el pipeline con `hash_mismatch: true` y política REJECT~~ → M-03 lo prohíbe.
- ~~Saltar etapas (`l0 pending` → `l1 in_progress` sin `l0 done`)~~ → M-04 lo prohíbe.
- ~~`remote_id` ausente o vacío en una entrada de `published_notes`~~ → M-06 lo prohíbe.
- ~~Olvidar `last_modified`~~ → M-05 lo prohíbe.
- ~~Añadir campos top-level nuevos sin reabrir F16~~ → el schema lo rechaza.

## §11 · Cómo verificar + cambios permitidos

Comandos grepeables:

1. `python3 -c "import json; json.load(open('schemas/manifest.schema.json'))"` → OK.
2. `wc -l references/00-pipeline/manifest.md` ≤ 300.
3. Los 4 manifests de `evals/manifest-sample/*.json` validan contra el schema.
4. `hash-changed.json` tiene `hash_mismatch: true`; los otros no.
5. Cada `published_notes[*]` tiene `remote_id` no vacío.

**Cambios permitidos sin reabrir F16:**
- Añadir un campo opcional a un sub-objeto (versión menor).
- Añadir un valor al enum de `destination` (versión menor; coherente con capability-matrix F8).
- Añadir un valor al enum de `link_debt.kind` (versión menor).

**Reabren F16:** cambiar la política por defecto (REJECT), eliminar la idempotencia, mover `remote_id` fuera de `published_notes`, romper M-04 (saltos de etapa), cambiar `hash` pattern.
