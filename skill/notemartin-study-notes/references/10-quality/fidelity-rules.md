# Reglas de fidelidad — `references/10-quality/fidelity-rules.md`

> Documento normativo de la **Fase 42** del roadmap. Define los 3 niveles de fidelidad (`source`/`derived`/`external`), las prohibiciones absolutas sobre valores técnicos inventados, la regla de la duda, y cómo se renderiza la fidelidad en los 7 destinos. Es la base de la "puerta de fidelidad absoluta" de L2 (architecture.md §3.3).
>
> Documentos complementarios: `references/03-knowledge/conflicts.md` (F41, regla "fuente gana" para contradicciones; F42 la generaliza), `references/03-knowledge/information-units.md` (F37, taxonomía de tipos; §4 mapea a las prohibiciones), `references/03-knowledge/ledger.md` (F15, fuente de respaldo para valores técnicos), `references/04-authoring/notemark.md` (F12, directivas `:::external` existente y `:::derived` añadida en F42), `references/08-render/capability-matrix.md` (matriz 14×7 destinos; F42 documenta cómo se preservan los bloques de nivel), `docs/adr/ADR-0006-fidelity-levels.md` (justificación de las decisiones cerradas).
>
> Enrutado desde N2: `docs/skill-anatomy.md` §6 fila `F42`. Lo lee el agente en L3 al redactar; F43 auditoría para verificar; F44 note-plan consulta la lista cerrada de prohibiciones; F114 quality gate mide cobertura de bloques; F118 evals.

## §1 · Propósito y alcance

La fidelidad al original es la promesa central del proyecto (architecture.md §3.3, INV-09). F42 formaliza esa promesa como un conjunto cerrado de reglas verificables:

1. Cada fragmento de la nota tiene un **nivel de origen** explícito: viene de la fuente, es derivado del agente, o es externo.
2. Los **valores técnicos** (defaults, rangos, parámetros, códigos de error, versiones, sintaxis, comandos) nunca se inventan: cada uno tiene respaldo en el ledger.
3. Cuando la fuente es silenciosa, se **escribe la ausencia**, no se completa.
4. Los niveles se **preservan como bloques identificables** en los 7 destinos, no se funden con el cuerpo principal.

**Sí es**:
- La taxonomía normativa de los 3 niveles.
- La lista cerrada de valores técnicos prohibidos sin respaldo.
- El contrato de las directivas `:::external` y `:::derived` en NoteMark.

**No es**:
- Un detector automático de invenciones: la fidelidad se mide por auditoría (F43) y por los criterios 1-3 del roadmap.
- El renderer: F42 doc-spec; cada renderer (F54–F60, F65 Anki) implementa la invariante.

## §2 · Cuándo se aplica

| Capa / fase | Lee este doc cuando… |
|---|---|
| L3 (agente al redactar) | Antes de cada bloque fáctico, decide su nivel (source/derived/external) y si requiere tag. |
| L3 (agente al redactar) | Antes de declarar un valor técnico (default, parámetro, etc.), busca en el ledger. Si no existe, escribe la ausencia. |
| F43 (auditoría de no-pérdida) | Verifica cobertura: todo bloque externo está en `:::external`, todo valor técnico está en el ledger. |
| F44 (note-plan) | Consulta la lista cerrada de prohibiciones al diseñar la división del trabajo. |
| F114 (quality gate) | Mide la proporción de bloques con tag por nota y por destino. |
| F118 (suite automatizada) | Corre `evals/fidelity-sample/run_eval.py` para verificar los 3 criterios. |

**No se aplica a**: ingesta (L0–L1), render puro sin nota (no aplica), destinos vacíos.

## §3 · Taxonomía de niveles (R1)

Enum cerrada. Extensible solo vía reabrir F42.

| Nivel | Cuándo aplica | Tag | Ejemplo |
|---|---|---|---|
| `source` | Paráfrasis directa o cita de la fuente. Default. | (sin tag) | "PostgreSQL es un ORDBMS." (paráfrasis de /ch01/intro) |
| `derived` | Síntesis, analogía, diagrama o paráfrasis larga propios del agente, basados en la fuente. | `:::derived` | Diagrama Mermaid que explica la arquitectura descrita en /ch02/intro. |
| `external` | Conocimiento del modelo fuera de la fuente (RFC, experiencia previa, dominio general). | `:::external` | "La mayoría de los ORDBMS usan MVCC; ver RFC 1234." |

Reglas:
- El nivel `source` es el default y no requiere tag.
- `derived` y `external` requieren block-level tag.
- No se mezclan niveles en el mismo bloque: cada bloque NoteMark tiene un único nivel.

## §4 · Prohibiciones absolutas (R2)

Prohibido inventar cualquiera de estos valores técnicos sin respaldo en el ledger (F15/F38):

| Categoría | Tipo de unidad F37 | Forma esperada |
|---|---|---|
| Defaults | `default` | Entry con `content.value` |
| Rangos | `parameter` (extensión aditiva con `content.range`) | Entry con `content.range` poblado |
| Nombres de parámetro | `parameter` | Entry con `content.name` |
| Códigos de error | `error-code` | Entry con `content.code` |
| Versiones | `version-note` | Entry con `version_introduced` o `version_removed` |
| Sintaxis | `syntax-rule` | Entry con `content.rule` o `content.ebnf` |
| Comandos | `example` (código) o `step` (procedimiento) | Entry con texto verbatim del SDM |

Regla: si el agente no encuentra el valor en el ledger, debe escribir la ausencia (R3) o marcar el bloque como `:::external` (R5), no inventarlo.

## §5 · Regla de la duda (R3)

Cuando la fuente es silenciosa o el agente no tiene respaldo, escribe la **ausencia**:

Formas aceptables:
- "El manual no menciona X."
- "X es desconocido en esta fuente; consultar documentación original."
- "Fuente incompleta: falta información sobre X."
- "No cubierto por la fuente consultada."

Palabras y frases prohibidas (subjetivas, no verificables):
- "probablemente", "típicamente", "en general", "asumimos", "suponemos", "creemos", "suele ser", "lo más común es", "por defecto", "a menudo".

Excepción: las palabras prohibidas pueden aparecer dentro de un bloque `:::external` o `:::derived` explícitamente marcado como tal (el lector sabe que es opinión/derivación).

## §6 · Directivas NoteMark (R4)

| Directiva | Forma | Significado |
|---|---|---|
| `:::external` | `:::external` … `:::external` | Conocimiento del modelo fuera de la fuente. Existente en F12 línea 155. |
| `:::derived` | `:::derived` … `:::derived` | Síntesis, analogías, diagramas propios del agente, basados en la fuente. Añadida en F42. |

Ambas son block-level. El renderer resuelve la directiva y muestra el badge apropiado.

## §7 · Renderizado en 7 destinos (R5)

Los 7 destinos (architecture.md §4, capability-matrix.md §2; nombres en `references/00-pipeline/manifest.md`) preservan los bloques de nivel como sigue:

| Destino | `:::derived` | `:::external` |
|---|---|---|
| Markdown estándar | Bloque con clase CSS `derived-block` + badge "🔗 derivado" | Bloque con clase `external-block` + badge "⚡ externo" |
| Destino A (admonition block) | Admonition con label "Derivado" | Callout naranja con label "Externo" |
| Destino B (callout) | Callout azul con label "Derivado" | Callout naranja con label "Externo" |
| Destino C (callout) | Callout con label "Derivado" | Callout con label "Externo" |
| HTML | `<aside class="derived">` | `<aside class="external">` |
| PDF | Caja con borde + label "Derivado" | Caja con borde + label "Externo" |
| Anki | Campo separado `Derived` | Campo separado `External` |

El identificador "Destino A/B/C" se mapea a los nombres concretos en `references/08-render/capability-matrix.md`; este spec mantiene la forma agnóstica para respetar INV-06. La capability-matrix.md §2 documenta la matriz 14 capacidades × 7 destinos; F42 añade la fila "fidelidad" como capacidad invariante.

## §8 · Auditoría de respaldo (R6)

Para cada valor técnico en el cuerpo de la nota, debe existir un ledger entry (F15/F38) del tipo correspondiente. Algoritmo del eval:

1. Parsea el note y extrae candidatos a valor técnico (regex sobre defaults, rangos, nombres de parámetro, códigos de error, versiones, sintaxis, comandos).
2. Para cada candidato, busca en `knowledge/ledger.json` un entry con `type` coincidente y `content` que matchee.
3. Si no hay match, exit 1 y reporta el valor sin respaldo.

## §9 · Anti-patrones (R7)

- Inventar un default (e.g., "el default es 64 MB" sin ledger entry).
- Paráfrasis larga sin `:::derived` (e.g., un párrafo que no es cita literal y no está marcado).
- Conocimiento externo sin `:::external` (e.g., "generalmente se usa X" mezclado en el cuerpo).
- Completar lo que la fuente omite ("probablemente X es Y").
- Usar palabras prohibidas fuera de bloques marcados.

## §10 · Cómo verificar + cambios permitidos

```bash
# 1. Spec dentro de presupuesto.
wc -l references/10-quality/fidelity-rules.md                # ≤ 230
rg -c '^## §' references/10-quality/fidelity-rules.md         # 11 secciones

# 2. Eval de los 3 criterios del roadmap.
python3 evals/fidelity-sample/run_eval.py                     # exit 0

# 3. Sin regresión.
python3 scripts/util/validate_ledger.py --validate evals/ledger-sample/*.json
python3 evals/information-units-sample/run_eval.py
python3 evals/ledger-operativo-sample/run_eval.py
python3 evals/concept-graph-sample/run_eval.py
python3 evals/terminology-sample/run_eval.py
python3 evals/conflicts-sample/run_eval.py

# 4. Cero mención a plataformas de render (INV-06).
rg -i '<placeholder>' references/10-quality/fidelity-rules.md   # vacío

# 5. Las 7 directivas NoteMark están bien tipadas.
rg -E '^### :::{external|derived}' references/04-authoring/notemark.md
```

**Permitidos sin reabrir F42** (versión menor):
- Añadir una forma aceptable a la lista de R3 (ausencia).
- Refinar el wording de §1.
- Añadir un anti-patrón a §9.

**Reabren F42** (versión mayor):
- Añadir un nivel a la taxonomía (§3).
- Cambiar la lista cerrada de categorías de R2.
- Cambiar las directivas NoteMark (R4).
- Cambiar el mapeo de renderizado (R5).
- Permitir una palabra prohibida por defecto.

## §11 · Cambios que reabren + glosario

**Reabren F42 además de §10**:
- Cambiar el formato de `:::derived`/`:::external` (e.g., atributo `level`).
- Eliminar la regla de la duda.
- Cambiar la lista de R2 (prohibiciones).

**No reabren F42**:
- Refinar mensajes de error.
- Cambiar el path por defecto del workdir.

**Glosario**:

| Término | Significado |
|---|---|
| **Nivel** | Categoría de origen del contenido de un bloque NoteMark: `source`/`derived`/`external`. |
| **`source`** | Paráfrasis directa o cita de la fuente. Default. |
| **`derived`** | Síntesis, analogía, diagrama del agente basado en la fuente. Requiere `:::derived`. |
| **`external`** | Conocimiento del modelo fuera de la fuente. Requiere `:::external`. |
| **Valor técnico** | Cualquiera de las 7 categorías de R2 (defaults, rangos, parámetros, error-codes, versiones, sintaxis, comandos). |
| **Regla de la duda** | Cuando el agente no sabe o la fuente es silenciosa, escribe la ausencia (R3). |
| **Respaldo** | Entry en el ledger (F15/F38) que justifica un valor técnico en el cuerpo. |
| **7 destinos** | Los formatos de publicación (nombres en `references/00-pipeline/manifest.md` y `references/08-render/capability-matrix.md`). |
