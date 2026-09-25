# ADR-0008 — Note Plan (Fase 44)

**Fecha:** 2026-09-25
**Estado:** aceptada
**Atada a:** F44, F15 (ledger), F37 (information-units), F39 (concept-graph), F38 (ledger operativo), F78-F92 (15 tipos de nota), F43 (auditoría de no-pérdida)

## Contexto

Fase 44 implementa el contrato L2 → L3 del proyecto: el agente divide el trabajo en notas asignando cada unidad del ledger a una nota, con tipo, tamaño, dependencias y destino. La división es semántica (por concepto o dominio), no por conteo. Cuando el trabajo es grande (umbral combinado), el plan se muestra antes de redactar.

Las alternativas consideradas:

1. **Plan sin tipos fijos** — el agente elige el tipo libremente. Descartada: sin enum cerrada, el eval no puede verificar la cobertura ni la completitud.
2. **Plan por conteo** — N unidades por nota. Descartada: viola "división semántica, no por conteo".
3. **Plan con enum cerrada (15 tipos) + división semántica + threshold combinado** (elegida).

## Decisión

1. **Forma JSON** del `knowledge/note-plan.json` con dos secciones: `notes[]` y `metadata`. Cada nota lleva `note_id` (slug kebab-case), `type` (uno de los 15 tipos cerrados de F78-F92), `unit_ids`, `block_ids`, `depends_on`, `destination`, `estimated_size`, `rationale`, `collision_with`, `collision_decision`. Metadata lleva totales y `user_approval_required`.

2. **División semántica** (R3, criterio 2): las unidades se agrupan por concepto o dominio. Las unidades atómicas (procedimiento, tabla de parámetros, ejemplo desarrollado) **nunca se parten** entre notas. Reusa el algoritmo de F39 §7 para verificar aciclicidad en `depends_on`.

3. **Umbral combinado** (R4, criterio 3, decisión confirmada): `notes_planned > 5` OR `total_must_keep > 30`. Combinación de ambas dimensiones: cubre obras con muchas notas pequeñas (e.g., 30 cheatsheets) y obras con pocas notas grandes (e.g., 1 manual entero).

4. **Resolución de colisiones** (R5): antes de crear el plan, el agente consulta `notemark/*.nm` y `ir/*.json`. Decisiones `collision_decision ∈ {reuse, new}` con `collision_with` documentando la nota colisionada.

5. **Sin script de mantenimiento en la skill** (R9): el agente construye el plan siguiendo el spec; el eval lo verifica. Sin CLI en la skill. Coherente con F40 (terminology) y F41 (conflicts), que son `[ref]` puros.

6. **Tipos cerrados (15)**: `concept`, `api-reference`, `procedure`, `configuration`, `error-troubleshooting`, `architecture`, `syntax`, `data-model`, `chapter-digest`, `comparison`, `version-delta`, `glossary-term`, `cheatsheet`, `index-moc`, `practice`. Extensible solo vía reabrir F44.

7. **Coherencia con F43** (completeness-audit): el plan cumple con la regla 100 % must-keep (criterio 1); F43 verifica que toda unidad tiene entry en el ledger y que toda entry tiene respaldo.

8. **Coherencia con F39** (concept-graph): `depends_on` deriva de las aristas `prerequisite`. Una nota B depende de A si las unidades de B tienen `cross-reference` con `from_concept = unidad-en-B` y `to_concept = unidad-en-A`.

9. **`note_id` ↔ `target_note`**: el `note_id` del plan es el `target_note` que el ledger (F15) usa. El plan ES el contrato L2 → L3: las notas que F45-F51 redactan usan estos `note_id`.

## Consecuencias

**Gana**:
- El plan es verificable mecánicamente (3 criterios del roadmap via eval).
- La división semántica evita "notas huérfanas" y "unidades huérfanas".
- El threshold combinado evita obras grandes sin aprobación.
- La resolución de colisiones documenta la decisión (reuse vs new).
- Los 15 tipos cerrados conectan F44 con F78-F92.

**Pierde**:
- El agente tiene más carga: elegir tipo, calcular dependencias, decidir colisiones.
- Los 15 tipos pueden no estar implementados todavía (F78-F92 son fases futuras); el plan declara el tipo, no lo ejecuta.

**Queda atado**:
- F15 (ledger): `target_note` se llena desde el plan.
- F37 (information-units): los tipos F37 §3 (parameter, default, etc.) son el universo de unidades que el plan asigna.
- F39 (concept-graph): `depends_on` deriva de las aristas `prerequisite`.
- F38 (ledger operativo): mantiene el ledger durante L2; el plan se construye después.
- F78-F92: los 15 tipos cerrados que el plan declara.
- F43 (auditoría): verifica `metadata.assigned_must_keep == metadata.total_must_keep` (criterio 1).
