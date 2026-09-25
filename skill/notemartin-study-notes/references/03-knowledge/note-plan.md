# Note Plan — `references/03-knowledge/note-plan.md`

> Documento normativo de la **Fase 44** del roadmap. Define el contrato L2 → L3: el agente divide el trabajo en notas (F45-F51) asignando cada unidad del ledger a una nota, con tipo, tamaño, dependencias y destino. La división es semántica (por concepto o dominio), no por conteo. Cuando el trabajo es grande (umbral combinado), el plan se muestra antes de redactar y requiere aprobación del usuario.
>
> Documentos complementarios: `references/03-knowledge/ledger.md` (F15, fuente de las unidades a asignar), `references/03-knowledge/information-units.md` (F37, taxonomía de tipos), `references/03-knowledge/concept-graph.md` (F39, fuente de dependencias `prerequisite`), `references/03-knowledge/ledger-operativo.md` (F38, mantiene el ledger durante L2), `references/03-knowledge/conflicts.md` (F41, contradicciones que pueden requerir notas adicionales), `references/03-knowledge/terminology.md` (F40, términos canónicos para cross-reference), `references/04-authoring/notemark.md` (F12, sintaxis de las notas resultantes), `references/05-note-types/README.md` (F78-F92, los 15 tipos cerrados), `schemas/note-plan.schema.json` (este doc, contrato del JSON), `architecture.md` §3.3-§4 (contrato L2 y paths), `docs/adr/ADR-0008-note-plan-model.md` (justificación de las decisiones cerradas).
>
> Enrutado desde N2: `docs/skill-anatomy.md` §6 fila `F44`. Lo produce el agente en L2 al cierre del corpus; lo consume L3 (F45-F51) para redactar; F43 auditoría verifica la cobertura del plan; F118 evals mide los criterios.

## §1 · Propósito y alcance

El Note Plan es el **contrato L2 → L3** del proyecto: el agente, tras construir el ledger (F15/F38) y el grafo de conceptos (F39), divide el trabajo en notas y emite el plan antes de redactar. El plan cumple tres promesas:

1. **Cobertura**: toda unidad `must-keep` está asignada a una nota.
2. **Atomicidad**: ningún procedimiento, tabla de parámetros o ejemplo desarrollado se parte entre notas.
3. **Aprobación**: cuando el trabajo es grande, el plan se muestra al usuario antes de redactar.

**Sí es**:
- El artefacto que cierra el contrato L2 (architecture.md §3.3) antes de pasar a L3.
- La entrada que F45-F51 (las 15 plantillas de tipo de nota) consumen para redactar cada nota.
- El mecanismo que evita "notas huérfanas" (sin unidades asignadas) y "unidades huérfanas" (sin nota asignada).

**No es**:
- El ledger: el plan ESCRIBE qué notas se crearán; el ledger rastrea qué unidades existen. Son complementarios.
- El grafo de conceptos: el plan CONSUME `concept-graph.json` para derivar dependencias, pero no lo modifica.
- Un script de generación: el plan lo construye el agente siguiendo este spec. Sin CLI en la skill.

## §2 · Cuándo se aplica

| Capa / fase | Lee este doc cuando… |
|---|---|
| L2 (agente al cerrar corpus) | Tras construir ledger + concept-graph + glossary, ejecuta el algoritmo §3-§8 para producir `knowledge/note-plan.json`. |
| L3 (agente al redactar) | F45-F51 consultan el plan para saber qué nota redactar; el `note_id` del plan es el `target_note` en el ledger. |
| F43 (auditoría de no-pérdida) | Verifica que `metadata.assigned_must_keep == metadata.total_must_keep` (criterio 1). |
| F44 (este doc, recurrente) | Cada vez que se re-evalúa un workdir o se actualiza el SDM. |
| F118 (suite automatizada) | Corre `evals/note-plan-sample/run_eval.py` para medir los 3 criterios. |

**No se aplica a**: ingesta (L0–L1), render (L4), publicaciones.

## §3 · Modelo del plan (R1–R2)

`knowledge/note-plan.json` con `schema_version: "1.0.0"`, dos secciones top-level: `notes[]` y `metadata`.

### Notas

Enum cerrada de **15 tipos** (F78-F92, `references/05-note-types/`): `concept`, `api-reference`, `procedure`, `configuration`, `error-troubleshooting`, `architecture`, `syntax`, `data-model`, `chapter-digest`, `comparison`, `version-delta`, `glossary-term`, `cheatsheet`, `index-moc`, `practice`.

Cada nota:

| Campo | Tipo | Descripción |
|---|---|---|
| `note_id` | string | Slug kebab-case, max 64 chars, regex `^[a-z0-9][a-z0-9_-]{0,63}$`. Único en el plan. Se convierte en `target_note` en el ledger. |
| `type` | enum(15) | Uno de los tipos de F78-F92. |
| `title` | string | ≤ 200 chars. |
| `unit_ids` | array | ≥ 1 unit_id del ledger (F15). Toda unidad debe aparecer en exactamente una nota (salvo `merged`/`discarded` que no requieren nota). |
| `block_ids` | array | Block_ids del SDM referenciados por las unidades. |
| `depends_on` | array | note_ids de notas prerrequisito. Deriva de `concept-graph.json` (F39). |
| `destination` | array | Identificadores de destino donde se publica la nota. Default `["<default-destination>"]` (ver `references/08-render/capability-matrix.md` para el nombre concreto). Vacío = todos los destinos activos en `profile.targets.active`. |
| `estimated_size` | enum | `small` (< 5 unidades, < 10 min), `medium` (5-15 unidades, 10-30 min), `large` (> 15 unidades, > 30 min). |
| `rationale` | string | Por qué este tipo para estas unidades. |
| `collision_with` | string \| null | note_id de una nota existente con solapamiento. |
| `collision_decision` | enum | `reuse`, `new`, o null. |

### Metadata

| Campo | Tipo | Descripción |
|---|---|---|
| `total_must_keep` | integer | Total de unidades `must-keep` en el ledger. |
| `assigned_must_keep` | integer | Unidades `must-keep` asignadas a una nota. |
| `unassigned_unit_ids` | array | Unit_ids must-keep sin asignar (criterio 1). |
| `total_units` | integer | Total de unidades en el ledger. |
| `total_blocks` | integer | Total de bloques en el SDM. |
| `notes_planned` | integer | `notes.length`. |
| `threshold_exceeded` | boolean | `notes_planned > 5` OR `total_must_keep > 30`. |
| `user_approval_required` | boolean | `threshold_exceeded`. El plan se muestra al usuario antes de redactar. |

## §4 · Reglas de división semántica (R3, criterio 2)

Las unidades se agrupan por **concepto o dominio**, no por conteo. Las unidades atómicas **nunca se parten** entre notas:

- **Procedimiento**: todas las unidades `step` que comparten `source_section_path` van a la misma nota.
- **Tabla de parámetros**: todas las unidades `parameter` + `default` que comparten `source_section_path` van a la misma nota.
- **Ejemplo desarrollado**: las unidades `example` van con el bloque que las introdujo, no se separan.

Algoritmo:

1. Agrupar unidades por `source_section_path`.
2. Para cada grupo, identificar el **tipo atómico dominante** (e.g., grupo con > 50 % `step` → procedimiento).
3. Asignar el grupo entero a una nota de tipo coherente con el dominante.
4. Si el grupo cubre varios dominios (procedimiento + tabla), dividir por dominio conceptual, **no por bloque**.

## §5 · Resolución de colisiones (R5)

Antes de crear el plan, el agente consulta `notemark/*.nm` y `ir/*.json` en el workdir. Si una nota existente cubre parte de las unidades a planificar:

| Decisión | Cuándo aplicarla |
|---|---|
| `collision_decision="reuse"` | La nota existente tiene el mismo dominio conceptual; se añaden las unidades nuevas. |
| `collision_decision="new"` | La nota existente tiene un scope distinto; se crea una nota nueva. |

El campo `collision_with` documenta la nota colisionada. Las decisiones `reuse` reducen el número de notas planificadas; las decisiones `new` lo aumentan.

## §6 · Umbral de aprobación (R4, criterio 3, decisión confirmada)

`metadata.user_approval_required = (notes_planned > 5) OR (total_must_keep > 30)`.

Cuando `true`, el plan **se muestra al usuario antes de redactar**. El usuario debe aprobar explícitamente. Sin aprobación, L3 no inicia.

El umbral combina dos dimensiones:
- **notes_planned > 5**: obras con muchas notas pequeñas (e.g., 30 cheatsheets).
- **total_must_keep > 30**: obras con pocas notas grandes (e.g., 1 manual entero).

## §7 · Dependencias entre notas (R7)

`notes[].depends_on` lista los `note_id` de notas prerrequisito. Algoritmo:

1. Para cada nota N con unidades U_N:
   - Consultar `concept-graph.json` (F39) para cada U_N.
   - Si hay arista `prerequisite` desde U_N hacia U_M (donde M != N), añadir `M.note_id` a `N.depends_on`.
2. Verificar que el grafo de `depends_on` sea **acíclico** (DFS con marcas white/gray/black; mismo algoritmo que F39 §7).

Si hay ciclo, exit 1 con la lista de ciclos. El agente resuelve reasignando unidades o partiendo una nota.

## §8 · Destinos y tamaño (R6, R8)

- `notes[].destination`: array de strings; default `["<default-destination>"]` (ver `references/08-render/capability-matrix.md` para los nombres concretos de los 7 destinos). Si está vacío, se interpreta como "todos los destinos activos en `profile.targets.active`".
- `notes[].estimated_size`: enum cerrada `small`/`medium`/`large` (ver §3). Es informativo; el threshold gate se calcula sobre `notes_planned` y `total_must_keep`.

## §9 · Anti-patrones

- Partir un procedimiento (R3): las unidades `step` deben estar todas en la misma nota si comparten `source_section_path`.
- Aprobar implícitamente un trabajo grande (R4): cuando `user_approval_required=true`, el plan se muestra al usuario; sin aprobación, no se inicia L3.
- Nota huérfana (sin unidades asignadas): toda nota del plan debe tener `unit_ids.length >= 1`.
- Unidad huérfana (must-keep sin asignar): `metadata.unassigned_unit_ids` debe estar vacío.
- Tipo incorrecto para las unidades: e.g., asignar unidades `parameter` a una nota `procedure` en lugar de `configuration`.
- Ciclos en `depends_on` (R7): el grafo debe ser acíclico.

## §10 · Cómo verificar + cambios permitidos

```bash
# 1. Spec dentro de presupuesto.
wc -l references/03-knowledge/note-plan.md                  # ≤ 230
rg -c '^## §' references/03-knowledge/note-plan.md           # 11 secciones

# 2. Schema JSON válido.
python3 -c "import json; json.load(open('schemas/note-plan.schema.json'))"

# 3. Eval de los 3 criterios del roadmap.
python3 evals/note-plan-sample/run_eval.py                    # exit 0

# 4. Sin regresión.
python3 scripts/util/validate_ledger.py --validate evals/ledger-sample/*.json
python3 evals/information-units-sample/run_eval.py
python3 evals/ledger-operativo-sample/run_eval.py
python3 evals/concept-graph-sample/run_eval.py
python3 evals/terminology-sample/run_eval.py
python3 evals/conflicts-sample/run_eval.py
python3 evals/fidelity-sample/run_eval.py
python3 evals/completeness-sample/run_eval.py

# 5. Cero mención a plataformas (INV-06).
rg -i '<placeholder>' references/03-knowledge/note-plan.md   # vacío
```

**Permitidos sin reabrir F44** (versión menor):
- Añadir un campo opcional a `notes[]` (e.g., `keywords[]`).
- Añadir un valor a `destination` (e.g., `markdown`).
- Refinar el wording de §1.

**Reabren F44** (versión mayor):
- Cambiar la enum de tipos de nota (los 15 de F78-F92).
- Cambiar el umbral combinado (R4).
- Cambiar las reglas de atomicidad (R3).
- Cambiar el formato de `collision_decision`.
- Cambiar la forma de `depends_on` (e.g., añadir grafo de precedencia estricto).

## §11 · Cambios que reabren + glosario

**Reabren F44 además de §10**:
- Cambiar la lista cerrada de tipos (los 15).
- Cambiar la resolución de colisiones (R5).
- Eliminar `unassigned_unit_ids` (criterio 1).

**No reabren F44**:
- Refinar mensajes de error.
- Añadir `--out` al eval para redirigir el reporte.

**Glosario**:

| Término | Significado |
|---|---|
| **Note Plan** | `knowledge/note-plan.json`; contrato L2 → L3 que divide el corpus en notas. |
| **`note_id`** | Slug kebab-case único; usado en `target_note` del ledger. |
| **Tipo de nota** | Uno de los 15 valores cerrados (F78-F92). |
| **División semántica** | Agrupar por concepto o dominio, no por conteo. |
| **Unidad atómica** | Bloque que no se puede partir entre notas (procedimiento, tabla de parámetros, ejemplo). |
| **Colisión** | Una nota existente en `notemark/*.nm` cubre parte de las unidades a planificar. |
| **Threshold gate** | `notes_planned > 5` OR `total_must_keep > 30`; activa `user_approval_required`. |
| **Trabajo grande** | Threshold gate activado; requiere aprobación explícita del usuario. |
| **Dependencia** | `depends_on` entre notas; deriva de `prerequisite` en `concept-graph.json` (F39). |
| **Aprobación** | Confirmación explícita del usuario antes de iniciar L3 cuando el threshold está activado. |
