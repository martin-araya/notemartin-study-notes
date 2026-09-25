# ADR-0006 — Niveles de fidelidad (Fase 42)

**Fecha:** 2026-09-25
**Estado:** aceptada
**Atada a:** F42, F12 (notemark), F15 (ledger), F37 (information-units), F41 (conflicts), INV-09

## Contexto

Fase 42 formaliza los 3 niveles de fidelidad del corpus. La pregunta central: ¿cómo distinguir el contenido que viene de la fuente del que produce el agente?

Las alternativas consideradas:

1. **Sin niveles** — todo el contenido se presenta como si fuera de la fuente. Descartada: viola INV-09 y la promesa de fidelidad.
2. **Dos niveles (source/external)** — lo que ya existe en F12 con `:::external`. Descartada: no distingue paráfrasis larga del modelo de conocimiento externo.
3. **Tres niveles (source/derived/external)** (elegida) — separamos la síntesis del agente del conocimiento externo, ambos marcados pero con directivas distintas.

## Decisión

1. **Tres niveles cerrados**: `source` (default), `derived`, `external`. Extensible solo vía reabrir F42. Decisión confirmada por el usuario.

2. **Tagging dual**:
   - `:::external` (existente en F12): conocimiento del modelo fuera de la fuente.
   - `:::derived` (nueva en F42): síntesis, analogías, diagramas del agente basados en la fuente.
   - "source" no requiere tag.
   - Cada bloque NoteMark tiene un único nivel.

3. **Prohibiciones absolutas** sobre 7 categorías de valores técnicos:
   - Defaults, rangos, nombres de parámetro, códigos de error, versiones, sintaxis, comandos.
   - Cada uno mapea a un tipo de unidad F37 (`default`, `parameter`, `error-code`, `version-note`, `syntax-rule`, `example`/`step`).
   - Sin respaldo en el ledger, no se puede declarar el valor.

4. **Regla de la duda** (R3): cuando el agente no sabe, escribe la ausencia con formas cerradas. Lista de palabras prohibidas: "probablemente", "típicamente", "en general", "asumimos", "suponemos", "suele ser", "lo más común es", "por defecto", "a menudo".

5. **Renderizado en 7 destinos** (R5): cada destino preserva los bloques como admonition/callout/aside según corresponda. La capability-matrix.md §2 se mantiene como referencia canónica; F42 añade la fila "fidelidad" como capacidad invariante.

6. **Sin JSON nuevo** — los niveles viven en directivas inline en NoteMark. La coherencia se verifica por el eval (F42 §8) y por auditoría humana (F43).

7. **Coherencia con F41**: la regla "fuente gana" de F41 §7 es un subconjunto de F42 R1 (prohibición de inventar). Las directivas `:::contradiction` y `:::discrepancy` (F41 §9) complementan F42: `:::discrepancy` se usa dentro de `:::external` o `:::derived` cuando el modelo diverge.

## Consecuencias

**Gana**:
- La fidelidad es verificable por el eval (3 criterios del roadmap) sin requerir razonamiento semántico profundo (parsing de regex).
- El lector siempre sabe si un bloque es de la fuente, derivado o externo (badges por destino).
- La regla "fuente gana" se generaliza de contradicciones (F41) a todo contenido técnico (F42).
- El renderer de cada destino tiene una invariante clara: preservar bloques de nivel.

**Pierde**:
- El agente tiene más carga: declarar el nivel de cada bloque y verificar el respaldo de cada valor técnico.
- Las palabras prohibidas son listas cerradas pero incompletas (sinónimos infinitos). El eval verifica las más comunes; F43 auditoría cierra el gap.

**Queda atado**:
- F12 (notemark): `:::derived` se añade a §4.
- F15 (ledger): cada valor técnico debe tener entry correspondiente.
- F37 (information-units): los tipos `default`, `parameter`, `error-code`, `version-note`, `syntax-rule` son los tipos de respaldo.
- F41 (conflicts): `:::discrepancy` opera dentro de `:::external` o `:::derived`.
- F43 (auditoría): ejecuta las verificaciones de F42.
- F114 (quality gate): mide la proporción de bloques con tag por nota y por destino.
