# ADR-0001 — Unidades de información: enum cerrado, criticidad derivada, fusión prohibida en must-keep

**Fecha:** 2026-09-24
**Estado:** aceptada
**Atada a:** F37, INV-08, INV-09

## Contexto

F37 necesita formalizar la taxonomía de unidades de información y la mecánica de criticidad. Tres decisiones afectan a fases vecinas (F38 ledger operativo, F43 auditoría, F118 suite de evals) y deben cerrarse antes de implementar.

Las alternativas consideradas:

1. **Enum abierto** (string libre con sugerencias): cualquier valor pasa el schema; el validador no puede enforzar cobertura. Se descart porque rompe la auditoría de no-pérdida.
2. **Enum cerrado con `other`/`unknown`**: el agente puede escamotear tipos difíciles marcándolos `other`. Se descartó porque reintroduce el problema de (1).
3. **Criticidad declarada por el agente**: el agente marca cada unidad `must-keep` o `context` libremente. Se descartó porque el "sin excepción" del criterio 2 de F37 exige cálculo mecánico.
4. **Fusión libre en `must-keep`**: dos `error-code` similares pueden colapsarse en una sola entrada. Se descartó porque viola INV-08 (cobertura 1-a-1 trazable).
5. **Schema endurecido en F37**: el `schemas/ledger.schema.json` se muta en esta misma fase para usar el enum cerrado. Se descartó por atomicidad de PR (un PR contiene spec → schema → validador es más fácil de revertir que dos PRs coordinados).

## Decisión

1. **Enum cerrado de 14 tipos** sin `other`/`unknown`. Lo que no encaja queda como bloque huérfano que F38 detecta con "contenido sin respaldo". Extender el enum reabre F37.

2. **`criticality` es derivada, no declarada**, salvo override explícito con `content.rationale` (elevación). Las reglas R1–R5 del spec §5 las calcula el script de F38.

3. **`must-keep` se eleva solo con `rationale`**. Default es `context` para lo que no activa regla automática. Esto limita la discrecionalidad del agente y hace auditable cada excepción.

4. **Fusión libre solo en `context`**. Dos `must-keep` que repiten información se declaran `redundant-with:<unit_id>` (F15) y producen dos entradas en el ledger, una descartada y otra `written`. No se funden.

5. **Schema del ledger endurecido en F38, no en F37**. F37 produce el spec; F38 lee ese spec para endurecer el JSON Schema y aplicar las reglas. Un solo PR cubre el trío spec → schema → validador.

## Consecuencias

**Gana**:
- INV-08 (100 % must-keep terminal) es verificable: el script de F38 sabe qué unidades son `must-keep` por construcción.
- F43 (auditoría) puede recorrer el ledger con un set fijo de reglas; no hay ambigüedad sobre qué es "una unidad crítica".
- F118 (evals) puede medir acuerdo entre dos extracciones independientes porque el espacio de tipos está acotado.
- Las decisiones heredan la rigidez del SDM (F13), que también tiene enum cerrado de 16 tipos.

**Pierde**:
- El agente no puede clasificar contenido genuinamente nuevo (un tipo que no existe en el spec); debe dejarlo como bloque huérfano. Riesgo mitigado por `unknown_conventions[]` (F35) y el eval de F118 que detecta lagunas del catálogo.
- Una versión mayor del spec es costosa (reabre F37, regenera eval battery, reentrena el script de F38). Riesgo aceptable: añadir un tipo es raro y debe pasar por revisión.

**Queda atado**:
- INV-08: la cobertura 1-a-1 trazable exige granularidad de `must-keep`; este ADR la garantiza.
- INV-09: los literales de la fuente se conservan textualmente; el `error-code` R3 los protege (un código no se trunca).
- F38: la fase siguiente debe (a) leer este spec, (b) endurecer el `schemas/ledger.schema.json` al enum cerrado, (c) implementar R1–R5 como funciones puras testeables.
