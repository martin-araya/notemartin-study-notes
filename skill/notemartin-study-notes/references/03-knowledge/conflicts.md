# Contradicciones y obsolescencia — `references/03-knowledge/conflicts.md`

> Documento normativo de la **Fase 41** del roadmap. Define cómo el agente detecta, documenta y resuelve contradicciones internas (fuente vs fuente, fuente vs modelo, fuente vs externo), formaliza la taxonomía cross-cutting de obsolescencia (`current`/`preview`/`deprecated`/`legacy`/`removed`), y establece la regla "fuente gana" con discrepancia aparte.
>
> Documentos complementarios: `references/03-knowledge/information-units.md` (F37, `version-note.version_removed`), `references/02-source-model/editorial-semantics.md` (F35, `severity: deprecated`/`removed` en cajas), `references/03-knowledge/terminology.md` (F40, `definitions[].status: historical`), `references/04-authoring/notemark.md` (F12, directivas `:::contradiction`/`:::discrepancy`), `schemas/conflicts.schema.json` (este doc, contrato del JSON), `docs/adr/ADR-0005-conflicts-model.md` (justificación de las decisiones cerradas).
>
> Enrutado desde N2: `docs/skill-anatomy.md` §6 fila `F41`. Lo lee el agente en L2/L3 al redactar; F43 auditoría para verificar; F118 evals para medir los 3 criterios.

## §1 · Propósito y alcance

Las contradicciones internas en una obra técnica son inevitables: dos capítulos describen un parámetro con valores distintos; la fuente dice X y el modelo deriva Y; una feature está marcada como `current` aquí y como `deprecated` allá. El glosario acumula términos (F40), el ledger rastrea unidades (F15/F38), pero ninguno documenta **desacuerdos**. F41 cierra esa brecha.

**Regla dura**: la fuente siempre gana. Si el modelo deriva algo distinto, se registra la discrepancia pero el cuerpo refleja la fuente. Una contradicción nunca se resuelve en silencio.

**Sí es**:
- El registro canónico de contradicciones detectadas (JSON + directivas inline).
- La taxonomía cross-cutting de obsolescencia que comparten glossary (F40), concept-graph (F39), ledger (F15/F38) y notas (F12).
- El contrato para las directivas `:::contradiction` y `:::discrepancy` en NoteMark.

**No es**:
- Un detector automático: la detección es semántica; el agente decide cuándo hay contradicción. El eval verifica que las contradicciones *documentadas* cumplan las reglas.
- Una resolución unilateral: las contradicciones fuente-vs-fuente quedan `open` o `unresolved` hasta intervención humana.

## §2 · Cuándo se aplica

| Capa / fase | Lee este doc cuando… |
|---|---|
| L2 (agente durante extracción) | Detecta contradicciones entre bloques del SDM; las registra en `knowledge/conflicts.json`. |
| L3 (agente al redactar notas) | Aplica directivas `:::contradiction` y `:::discrepancy` cuando el cuerpo refleja una contradicción del registry. |
| L3 (agente al redactar notas) | Marca contenido deprecado con directivas inline o con el campo `deprecation_status`. |
| F43 (auditoría de no-pérdida) | Verifica que toda contradicción tenga 2 anchors distintos; que todo `severity: deprecated` del SDM tenga `deprecation_status` poblado. |
| F118 (suite automatizada) | Corre `evals/conflicts-sample/run_eval.py` para medir los 3 criterios. |

**No se aplica a**: ingesta (L0–L1), render (L4), publicación a destinos.

## §3 · Modelo del registry (`knowledge/conflicts.json`)

```json
{
  "schema_version": "1.0.0",
  "source": { "id": "...", "hash": "<sha256 hex 64>" },
  "conflicts": [
    {
      "id": "c_001",
      "type": "source-vs-source",
      "anchors": [
        { "type": "block", "id": "a8f4ce140580" },
        { "type": "block", "id": "b9e0d250691" }
      ],
      "description": "El parámetro `shared_buffers` aparece con default 128 MB en /ch02 y 64 MB en /ch07.",
      "status": "open",
      "resolution": null,
      "model_says": null,
      "first_seen_at": "2026-09-25T14:00:00Z",
      "deprecation_status": null
    }
  ],
  "build_metadata": {
    "built_at": "2026-09-25T14:00:00Z",
    "conflict_count": 1
  }
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | `c_001`, `c_002`, … (slug dentro del ledger). |
| `type` | enum | Uno de los 5 tipos cerrados (R1, §4). |
| `anchors` | array | ≥ 2 anchors de tipos o instancias distintas (R2–R3). |
| `description` | string | ≤ 500 chars; explica la contradicción en lenguaje natural. |
| `status` | enum | `open` / `resolved` / `unresolved`. |
| `resolution` | string \| null | Texto libre cuando `status=resolved`. |
| `model_says` | string \| null | Lo que el modelo deriva cuando hay `source-vs-derived`. |
| `first_seen_at` | string | ISO-8601 UTC. |
| `deprecation_status` | enum \| null | `current`/`preview`/`deprecated`/`legacy`/`removed` (R7). |

## §4 · Tipos de contradicción (R1)

Enum cerrada. Extensible solo vía reabrir F41.

| Tipo | Cuándo aplica |
|---|---|
| `source-vs-source` | Dos partes de la fuente se contradicen (e.g., parámetro con default distinto en dos capítulos). |
| `source-vs-derived` | La fuente dice X pero el modelo deriva Y (resolución: fuente gana). |
| `source-vs-external` | La fuente es silenciosa; el agente usa conocimiento externo que puede ser incorrecto. |
| `deprecation-mismatch` | Marcado como `current` en un lugar y `deprecated`/`removed` en otro. |
| `version-mismatch` | Información de versión inconsistente entre capítulos. |

## §5 · Reglas de anchors (R2–R3)

- **R2 (mínimo 2)**: cada contradicción tiene ≥ 2 anchors.
- **R3 (distintos)**: los 2 anchors son de **tipo diferente** (`block`, `note`, `concept`) **o** apuntan a instancias diferentes del mismo tipo.
- **Tipo `block`** (R2.a): `id` es un `block.id` del SDM (sha1 hex 12). Origen: F13.
- **Tipo `note`** (R2.b): `id` es un `target_note` del ledger. Origen: F38.
- **Tipo `concept`** (R2.c): `id` es un `concept_id` del grafo. Origen: F39.

## §6 · Estados de contradicción (R4–R5)

- **R4 (estados cerrados)**: `open`, `resolved`, `unresolved`. No hay transiciones implícitas; el agente actualiza el estado explícitamente.
- **R5 (registro obligatorio)**: cuando `status=resolved`, `resolution` es obligatorio y no vacío. Cuando `status=unresolved`, `description` debe mencionar por qué no se pudo resolver.

## §7 · Resolución fuente vs modelo (R6)

Cuando `type = source-vs-derived`:
- El cuerpo de la nota refleja la fuente (R6.a).
- `model_says` se popula con la derivación del modelo (R6.b).
- El cuerpo incluye una directiva `:::discrepancy source-says="..." model-says="..."` que muestra la diferencia (R6.c).
- El agente **nunca** deja que el cuerpo contradiga la fuente sin marcarlo. Coherente con F42 (reglas de fidelidad) y AGENT.md INV-09.

## §8 · Taxonomía de obsolescencia (R7)

Enum cerrada cross-cutting. Aplica a:

| Mecanismo | Cómo se aplica |
|---|---|
| `glossary.json` (F40) | `term.deprecation_status` por término; coexiste con `definitions[].status: historical`. |
| `concept-graph.json` (F39) | `node.deprecation_status` por nodo-concepto. |
| `ledger.json` (F15/F38) | `entry.deprecation_status` por unidad. |
| Notas (F12) | Directiva inline `:::deprecated` o atributo en bloques. |
| Cajas editoriales (F35) | Reusa `severity: deprecated`/`removed` existente. |
| `version-note` (F37) | Reusa `version_removed`; si está poblado, `deprecation_status=removed`. |

Enum cerrada: `current`, `preview`, `deprecated`, `legacy`, `removed`.

| Status | Significado |
|---|---|
| `current` | Vigente; comportamiento por defecto. |
| `preview` | Experimental; puede cambiar sin aviso. |
| `deprecated` | Sigue funcionando pero está marcado para removal. |
| `legacy` | Versión vieja; reemplazada pero aún soportada. |
| `removed` | Eliminado; existe solo por compatibilidad histórica. |

## §9 · Directivas NoteMark (R8)

Añadidas a F12 (`references/04-authoring/notemark.md` §4):

| Directiva | Forma | Significado |
|---|---|---|
| `:::contradiction` | `:::contradiction id="c_001"` | Apunta a un conflicto del registry. El renderer muestra "⚠ contradicción" con enlace al id. |
| `:::discrepancy` | `:::discrepancy source-says="X" model-says="Y"` | Inline diff cuando el modelo deriva algo distinto de la fuente (R6.c). |

Estas directivas son **inline** (al lado del párrafo relevante) y referencian al registry JSON para el detalle completo.

## §10 · Cómo verificar + cambios permitidos

```bash
# 1. Spec dentro de presupuesto.
wc -l references/03-knowledge/conflicts.md                  # ≤ 230
rg -c '^## §' references/03-knowledge/conflicts.md           # 11 secciones

# 2. Schema JSON válido.
python3 -c "import json; json.load(open('schemas/conflicts.schema.json'))"

# 3. Eval de los 3 criterios del roadmap.
python3 evals/conflicts-sample/run_eval.py                   # exit 0

# 4. Sin regresión.
python3 scripts/util/validate_ledger.py --validate evals/ledger-sample/*.json
python3 evals/information-units-sample/run_eval.py
python3 evals/ledger-operativo-sample/run_eval.py
python3 evals/concept-graph-sample/run_eval.py
python3 evals/terminology-sample/run_eval.py

# 5. Cero mención a plataformas (INV-06).
rg -i 'obsidian|notion|appflowy' references/03-knowledge/conflicts.md   # vacío
```

**Permitidos sin reabrir F41** (versión menor):
- Añadir un campo opcional al JSON del conflicto.
- Añadir un valor a `deprecation_status` (e.g., `experimental`).
- Refinar el wording de §1.

**Reabren F41** (versión mayor):
- Añadir un tipo a la enum de `type` (§4).
- Eliminar un valor de `deprecation_status` (§8).
- Cambiar la regla "fuente gana" (§7).
- Cambiar el formato de `anchors`.
- Cambiar el mínimo de anchors (R2).

## §11 · Cambios que reabren + glosario

**Reabren F41 además de §10**:
- Cambiar las directivas NoteMark (`:::contradiction`, `:::discrepancy`).
- Eliminar la taxonomía de obsolescencia cross-cutting.
- Cambiar la forma de `resolution`.

**No reabren F41**:
- Refinar mensajes de error.
- Cambiar el path por defecto del workdir.

**Glosario**:

| Término | Significado |
|---|---|
| **Anchor** | Referencia a una entidad del corpus (`block`, `note`, `concept`) usada para localizar una contradicción. |
| **Registry** | `knowledge/conflicts.json`; lista estructurada de contradicciones. |
| **`source-vs-source`** | Dos partes de la fuente se contradicen entre sí. |
| **`source-vs-derived`** | La fuente dice X pero el modelo deriva Y; resolución: fuente gana. |
| **`deprecation_status`** | Estado cross-cutting del ciclo de vida (`current`→`preview`→`deprecated`→`legacy`→`removed`). |
| **`:::discrepancy`** | Directiva inline que muestra el diff entre fuente y derivación del modelo. |
