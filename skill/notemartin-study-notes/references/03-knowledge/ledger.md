# Coverage Ledger — `references/03-knowledge/ledger.md`

> Documento normativo de la Fase 15 del roadmap. Define el formato del registro fuente→nota que el agente consulta para verificar la cobertura y la fidelidad. Schema JSON formal en [`schemas/ledger.schema.json`](../../../../schemas/ledger.schema.json).
>
> Documentos complementarios: `skills/AGENT.md` §13 (forma canónica de la entrada — este doc la formaliza), `references/00-pipeline/architecture.md` §3.3 (puerta de fidelidad), §4 (workdir per-fuente: `knowledge/ledger.json`), §8 (discard_policy default `closed-list`), `evals/rubric.md` §3.2 (niveles de cobertura 0-4).
>
> Enrutado desde N2: `docs/skill-anatomy.md` §6 fila `F15`. Lo producen el script del ledger (F38) y el agente; lo consultan F38, F43 (auditoría de no-pérdida), F49 (validador IR) y los renderers (F54-F60) para trazabilidad.

## §1 · Propósito y alcance

El Coverage Ledger es la **fuente de verdad de la puerta de fidelidad** (architecture.md §3.3). Una nota puede mentir; un ledger se valida contra el SDM y la cierra el script. Si el ledger dice "100 % must-keep en estado terminal", la nota ha cubierto la fuente o ha documentado los descartes con motivo. Si la nota dice algo distinto, el ledger gana.

Lo que el ledger **es**: el registro uno-a-uno entre unidades de información extraídas del SDM y su destino en las notas (o su descarte). Lo que el ledger **no es**: una nota, un plan, un grafo de conceptos, ni un log de actividades. Cada uno tiene su propio archivo (F12 NoteMark, F44 note plan, F39 concept graph).

## §2 · Cuándo se aplica

- L2 cuando el agente extrae unidades del SDM y decide su destino.
- L2 cuando el script del ledger (F38) cierra la sesión y bloquea si hay `must-keep` en `pending`.
- F43 cuando el auditor recorre el ledger para verificar no-pérdida.
- F118 cuando la suite automatizada ejecuta los tres criterios del roadmap.

**No se aplica a:** ingesta (L0-L1 producen SDM), ni a la redacción en sí (que produce NoteMark, no el ledger).

## §3 · Reglas duras (invariantes)

| ID | Invariante | Si se omite… |
|---|---|---|
| **L-01** | Toda unidad `must-keep` debe alcanzar estado terminal (`written`, `merged` o `discarded`) antes de cerrar el workdir. | La puerta de fidelidad se salta; la nota pierde contenido sin documento de la pérdida. |
| **L-02** | Todo descarte lleva motivo de la lista cerrada; ningún motivo fuera de lista. | El agente justifica con palabras lo que el schema no puede verificar; los descartes se vuelven arbitrarios. |
| **L-03** | El descarte nunca se aplica a `must-keep` con motivo no-lista. Si una unidad debe descartarse, se reclasifica a `context` primero. | La fidelidad se erosiona silenciosamente. |
| **L-04** | El ledger se cierra en disco con escritura atómica (temporal + rename). | Un crash a mitad deja un ledger corrupto, no detectable. |
| **L-05** | `target_note` es obligatorio en `must-keep`. | No se sabe qué nota cubre la unidad; la trazabilidad queda en el aire. |

## §4 · Forma de la entrada

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `unit_id` | string | sí | Identificador único dentro del ledger (`u_001`, `u_002`, …). |
| `source_block_ids` | array[string] | sí | Lista de `block_id` del SDM (sha1 hex 12, F13) que respaldan la unidad. Mínimo 1. |
| `source_section_path` | string | recomendado | Ruta canónica de la sección; habilita el query "¿dónde quedó la sección X?". |
| `type` | string | sí | Tipo semántico: `parameter`, `step`, `definition`, `error`, `warning`, `example`, `comparison`, etc. |
| `criticality` | enum | sí | `must-keep` o `context`. |
| `target_note` | string \| null | sí para must-keep | `note_id` destino. |
| `target_section` | string \| null | no | Sección dentro de la nota destino. |
| `state` | enum | sí | `pending` / `written` / `merged` / `discarded`. |
| `discard_reason` | string \| null | sí si state=discarded | Motivo de la lista cerrada (regex en schema). |

## §5 · Estados y transiciones

Cuatro estados; tres son terminales.

```
pending ─────► written ─────► merged
   │             │
   │             └─────────────► (sin transición; written es estable)
   │
   └────► discarded ─────► (terminal)
```

- `pending`: extraída del SDM, sin destino asignado.
- `written`: el agente redactó la unidad en una nota (el `target_note` está poblado).
- `merged`: la unidad fue absorbida por otra unidad (e.g., dos parámetros similares se fusionaron en uno); no aparece standalone.
- `discarded`: descartada con motivo de la lista cerrada.

**Transiciones permitidas**: solo hacia adelante en el diagrama. No se revierte de `written` a `pending`. Un descarte se justifica con `discard_reason` y es terminal.

**Estado terminal**: cualquier estado ≠ `pending`. Cobertura 100 % de `must-keep` exige estado terminal para cada uno.

## §6 · Lista cerrada de motivos de descarte

Cuatro motivos. El schema los enforza por regex (`^(redundant-with:<unit_id>|boilerplate|navigation|out-of-scope-by-user)$`):

| Motivo | Cuándo aplica | Ejemplo |
|---|---|---|
| `redundant-with:<unit_id>` | El contenido ya está cubierto por otra unidad; fusionar. | `redundant-with:u_007` |
| `boilerplate` | Texto repetitivo sin valor: licencias, headers, footers, "About this document". | Un bloque de copyright repetido en cada página. |
| `navigation` | Índice, tabla de contenidos, breadcrumbs, links de UI. | El TOC de un manual técnico. |
| `out-of-scope-by-user` | El usuario pidió explícitamente no cubrir este contenido (e.g., "ignorar el capítulo X"). | El usuario decide acotar. |

Cualquier otro valor falla la validación. Si un motivo legítimo falta en la lista, se **añade** a la lista cerrada y se reabre F15; no se introduce un valor ad-hoc.

## §7 · Reporte de cobertura

El script `validate_ledger.py --coverage` emite el reporte en tres vistas:

```
Global
  Total unidades: N
  must-keep: X / Y en estado terminal  (X = written + merged + discarded; Y = total must-keep)
  context:   X' / Y' en estado terminal

Por estado (todas las criticalities)
  pending   : N1
  written   : N2
  merged    : N3
  discarded : N4

Por motivo de descarte
  redundant-with:...      : M1
  boilerplate             : M2
  navigation              : M3
  out-of-scope-by-user    : M4

Por sección (top N con mayor número de must-keep pending)
  /ch02/section-2.3.2 : 3 must-keep pending
  /ch04/intro         : 1 must-keep pending
```

El reporte no se almacena en el ledger; se computa on-demand desde `entries`. El ledger es la fuente; el reporte es una vista derivada.

## §8 · Query "¿dónde quedó la sección X?"

Algoritmo lineal sobre `entries` (O(n)):

1. Recibir `section_path` como argumento.
2. Para cada entry, comparar `source_section_path` con el argumento (prefijo o igualdad exacta).
3. Imprimir los matches con su `unit_id`, `criticality`, `state`, `target_note`.

Latencia esperada: sub-milisegundo para ledgers de hasta 10 000 unidades. No se pre-computa un índice porque la divergencia entre índice y entries es un riesgo real.

Caso "sección no tiene entradas": el query imprime `(sin resultados)`. **No** se infiere que la sección "se cubre por contexto" o "no tiene unidades"; el revisor debe verificar manualmente (puede haber un error en el SDM o unidades que el agente no detectó).

## §9 · Ejemplo de ledger

```json
{
  "schema_version": "1.0.0",
  "source": {
    "id": "01-postgresql-chapter",
    "hash": "a8f4ce1405802cacbb35e6fb88f5e3cf138a4e872910cdfd276f378f13371657"
  },
  "entries": [
    {
      "unit_id": "u_001",
      "source_block_ids": ["a8f4ce140580"],
      "source_section_path": "/ch02/section-2.3.2",
      "type": "parameter",
      "criticality": "must-keep",
      "target_note": "postgres-shared-buffers",
      "target_section": "Configuration",
      "state": "written"
    },
    {
      "unit_id": "u_002",
      "source_block_ids": ["a8f4ce140581"],
      "source_section_path": "/ch02/section-2.3.2",
      "type": "warning",
      "criticality": "context",
      "state": "discarded",
      "discard_reason": "boilerplate"
    }
  ]
}
```

## §10 · Anti-patrones

- ~~Estado terminal en `must-keep` con `pending`~~ → falla el script `--validate` (criterio 1).
- ~~`discard_reason` con valor fuera de la lista cerrada (`"outdated"`, `"too-hard"`, etc.)~~ → falla el schema.
- ~~`discard_reason` ausente en una entrada con `state: "discarded"`~~ → falla el schema (`allOf[0]`).
- ~~`discard_reason` presente en una entrada con `state ≠ "discarded"`~~ → falla el schema (`allOf[1]`).
- ~~`must-keep` sin `target_note`~~ → falla el schema (`allOf[2]`).
- ~~Añadir un motivo a la lista cerrada sin reabrir F15~~ → el schema lo rechaza; el revisor detecta el cambio.
- ~~Edición manual del ledger por el agente (sin pasar por el script)~~ → viola INV-13 (idempotencia y auditabilidad).

## §11 · Cómo verificar + cambios permitidos

Comandos grepeables:

1. `python3 -c "import json; json.load(open('schemas/ledger.schema.json'))"` → OK.
2. `wc -l references/03-knowledge/ledger.md` ≤ 300.
3. `python3 scripts/util/validate_ledger.py --validate evals/ledger-sample/*.json` → exit 0 para los 3 positivos; exit 1 para los 2 negativos.
4. `python3 scripts/util/validate_ledger.py --coverage <ledger.json>` → imprime reporte §7.
5. `python3 scripts/util/validate_ledger.py --query <ledger.json> "/ch02/section-2.3.2"` → imprime unidades en esa sección.

**Cambios permitidos sin reabrir F15:**
- Añadir un campo opcional nuevo a la entrada (versión menor).
- Añadir un valor al enum de `state` o de `criticality` (versión menor).
- Refinar la tabla §7 sin cambiar la semántica.

**Reabren F15:** añadir un motivo a la lista cerrada (F15 explícitamente), cambiar la regla "100 % must-keep terminal", permitir motivos fuera de la lista, eliminar estados, mover `discard_reason` fuera de `entry`.
