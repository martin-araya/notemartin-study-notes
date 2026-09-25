# Depth layers — `references/04-authoring/depth-layers.md`

> Documento normativo de la Fase 51 del roadmap. Define el sistema de capas de
> profundidad (L1 TL;DR, L2 operativo, L3 referencia exhaustiva) que toda nota
> extensa debe identificar, y las reglas de extracción a nota hermana cuando
> L3 desborda.
>
> Documentos relacionados:
> - [`notemark.md`](notemark.md) §9 — puntero canónico a este doc.
> - [`notemark.ebnf`](notemark.ebnf) línea 67 — gramática formal `layer`.
> - [`inline-marks.md`](inline-marks.md) — `{layer:l1|l2|l3}` se documenta como
>   marca inline de bloque.
> - [`ir-spec.md`](ir-spec.md) — `layer` como atributo per-nodo + top-level en
>   el schema JSON.
> - [`block-directives.md`](block-directives.md) §10.13 — `:::collapsible` con
>   `default_open: false` como renderizado canónico de L3.
> - [`../03-knowledge/ledger.md`](../03-knowledge/ledger.md) (F15) — cobertura
>   de unidades must-keep; cada unidad se cuenta por capa.
> - [`../05-note-types/`](../05-note-types/README.md) — los 15 tipos cerrados
>   con override por tipo (§7).

## §1 · Propósito y alcance

Este documento es la **referencia normativa** del sistema de capas de
profundidad. Responde cinco preguntas por nota:

1. ¿Es esta nota "extensa" y, por tanto, obligada a las 3 capas?
2. ¿Qué debe contener cada capa (L1, L2, L3)?
3. ¿Cómo se identifica cada capa en NoteMark?
4. ¿Qué pasa si L3 desborda y debe extraerse?
5. ¿Cómo se mantiene la cobertura del ledger al aplicar capas?

`notemark.md` §9 documentaba las 3 capas en 3 párrafos. La Fase 51 las
consolida en un documento normativo con umbrales concretos, override por
tipo (F78-F92), reglas de extracción a nota hermana, e integración con el
ledger.

**Frontera con otros documentos:**
- Las capas L1/L2/L3 son **ortogonales** a las directivas de bloque (F45)
  y a las marcas inline (F46). Una sección puede tener directiva + marca
  inline + layer marker simultáneamente.
- La gramática `layer = "l1" | "l2" | "l3"` está en `notemark.ebnf`; este
  doc describe la **semántica** de cada valor.
- El schema IR (`note-ir.schema.json`) tiene `layer` como atributo per-node
  y top-level; este doc explica cuándo usar cada uno.

## §2 · Cuándo se aplica — definición de "nota extensa"

Una nota es **extensa** (y, por tanto, obligada a las 3 capas) si cumple
cualquiera de estas condiciones:

| Trigger | Las 3 capas son obligatorias |
|---|---|
| `len(body_lines) >= 50` | sí |
| Tipo `chapter-digest` (F86) | sí (siempre) |
| Tipo `architecture` (F83) | sí (siempre) |
| Tipo `data-model` (F85) | sí (siempre) |
| Tipo `comparison` (F87) | sí (siempre) |
| Otros tipos con `< 50` líneas | no (L2 basta) |

`len(body_lines)` cuenta solo las líneas de cuerpo (sin frontmatter, sin
marcadores `{layer:}` ni headings vacíos).

**Detección práctica:** el validador `validate_ir.py` (F49) puede emitir
W12 si la nota excede el threshold sin las 3 capas (extensión menor del F49).
El script `transform.py` (F50) tiene el subcomando `layer` para asignar
layers en bulk.

**Override por tipo (tabla completa en §7):** 4 tipos siempre requieren 3
capas (`chapter-digest`, `architecture`, `data-model`, `comparison`); los
otros 11 solo las requieren si ≥ 50 líneas.

## §3 · Las tres capas

### 3.1 L1 — TL;DR autónomo

**Propósito:** lectura independiente en ≤ 30 segundos; comprensión correcta
sin leer nada más.

**Tamaño objetivo:** ≤ 8 líneas / ≤ 60 palabras.

**Contenido obligatorio:**

1. **Definición del concepto** (1-2 frases). Ej: "PostgreSQL es un RDBMS
   relacional open-source que usa MVCC para aislamiento transaccional."
2. **Propósito principal** (1 frase). Ej: "Sirve para persistir datos con
   garantías ACID y rendimiento ajustable."
3. **Ejemplo mínimo** (1 línea, sin código extenso). Ej: "Un SELECT
   básico: `SELECT * FROM users WHERE id = 1`."
4. **Caso de uso canónico** (1 frase). Ej: "Aplicaciones web transaccionales
   con esquema estable."

**Contenido prohibido en L1:**

- Procedimientos paso a paso (eso es L2).
- Tablas de configuración (eso es L2/L3).
- Edge cases o troubleshooting (eso es L3).
- Versiones o historial (eso es L3).
- Anécdotas o analogías (> 30 palabras).

**Anti-ejemplo de L1:** "PostgreSQL tiene tres capas: operativa, referencia
exhaustiva y TL;DR. La operativa es donde... [500 palabras]". Esto NO es un
TL;DR; es un párrafo largo.

### 3.2 L2 — Operativo

**Propósito:** aplicar el concepto en práctica; suficiente para ejecutar
tareas comunes.

**Tamaño objetivo:** 30-70% del cuerpo total de la nota.

**Contenido típico:**

- Procedimiento principal paso a paso.
- Tabla de parámetros con valores por defecto.
- Admonitions operativas (`:::warning`, `:::tip`, `:::note`).
- Comandos CLI ejecutables.
- Advertencias sobre errores comunes.
- Cross-references a otras notas (`[[note:id]]`).

**Renderizado canónico:** headings `##` / `###` con texto conciso; listas
numeradas para procedimientos; tablas GFM para parámetros; admonitions de F45.

**Relación con L1:** L2 NO debe repetir lo que L1 ya dijo. Si L1 dice
"PostgreSQL es MVCC", L2 empieza directamente con "Para configurar...".
No hay solapamiento.

### 3.3 L3 — Referencia exhaustiva

**Propósito:** detalle completo; cobertura del must-keep; consulta puntual.

**Tamaño objetivo:** 30-70% del cuerpo total. Si L3 excede 100 líneas o 30%
del total, se extrae a nota hermana (ver §5).

**Contenido típico:**

- Tabla exhaustiva de parámetros con todas las columnas canónicas (incluidas
  las opcionales).
- Edge cases y comportamiento por defecto.
- Comparación con alternativas (`:::columns` o tabla comparativa).
- Historial de versiones (`:::version from="..." to="..."`).
- Troubleshooting detallado (`:::question` por error común).
- Limitaciones y casos no soportados.

**Renderizado canónico:** plegable (`:::collapsible title="..."` con
`default_open: false`) — ver `block-directives.md` §10.13. Esto evita que
el lector casual vea L3 a primera vista pero lo deja accesible.

**Regla dura (F12 §9 + INV-08): L3 NUNCA se omite.** Esto es la puerta de
fidelidad: aunque el agente decida no redactar L2, sigue redactando L3.
Si el agente omite L3, la nota falla la verificación de fidelidad (F42).

### 3.4 Resumen comparativo

| Capa | Tamaño | Contenido | Renderizado |
|---|---|---|---|
| L1 | ≤ 8 líneas / ≤ 60 palabras | Definición + propósito + ejemplo + caso de uso | Heading `## TL;DR` |
| L2 | 30-70% del cuerpo | Procedimiento + tabla principal + admonitions | Headings `##` con contenido visible |
| L3 | 30-70% del cuerpo (o nota hermana si > 100 líneas) | Detalle exhaustivo + edge cases + historia | `:::collapsible` con `default_open: false` |

## §4 · Sintaxis NoteMark

### 4.1 La marca `{layer:lX}`

```markdown
# Título de la nota

{layer:l1}
## TL;DR
L1 content here...

{layer:l2}
## Cómo aplicar
L2 content here...

{layer:l3}
## Detalle exhaustivo
L3 content here...
```

**Reglas de la marca:**

- Aparece inmediatamente **después** de un heading `##` o `###`.
- Aplica a todas las secciones hasta el siguiente `{layer:}` o fin de
  archivo.
- Si se omite, el layer se **hereda** del anterior o del top-level
  `layer:` del frontmatter (`properties.md` §5.16).
- Una marca por heading (no múltiples consecutivas).

### 4.2 Ejemplo canónico

````notemark
---
title: "PostgreSQL — Función array_append"
note-type: api-reference
status: published
---

# PostgreSQL — array_append

{layer:l1}
## TL;DR
`array_append(arr, elem)` añade `elem` al final de `arr` y devuelve el
resultado. No muta `arr` in-place. Útil para construir arrays dinámicamente
en una consulta sin subconsultas.

{layer:l2}
## Uso típico
Llamar en un `SELECT` para acumular elementos:

```sql
SELECT array_append(ARRAY[1, 2], 3);  -- {1, 2, 3}
SELECT array_append(ARRAY[]::int[], 42);  -- {42}
```

:::warning
Si `arr` es `NULL`, devuelve `NULL` (no un array con un elemento).
:::
````

### 4.3 Anti-patrones

- `{layer:l1}` dentro de un párrafo (debe estar después de un heading).
- Múltiples `{layer:lX}` en el mismo heading (solo uno; el segundo es error
  de sintaxis).
- Omitir la marca y depender de posición (ambiguo; **INV-08** lo prohíbe
  para L3).
- Usar `{layer:l1}` para secciones largas (defeción del propósito).
- Mezclar L1 dentro de L2 sin separador (rompe la autonomía de L1).

## §5 · Extracción a nota hermana

### 5.1 Cuándo extraer

Si L3 tiene **> 100 líneas** O **> 30% del total** de la nota, se extrae
a una nota hermana.

**Justificación:** L3 no debe dominar la nota. Si L3 es > 30% del total,
la nota se vuelve pesada y el lector casual nunca llega al L1/L2.

### 5.2 Procedimiento de extracción

1. **Crear nota hermana `<parent>-deep-dive`** (kebab-case derivado del
   `note_id` original con sufijo `-deep-dive`). Ej: `postgres-shared-buffers` →
   `postgres-shared-buffers-deep-dive`.
2. **Mover los bloques L3** menos esenciales a la nota hermana. El L3
   esencial (conceptos clave para entender L1/L2) se queda en la nota padre.
3. **Añadir `[[note:parent-deep-dive]]`** al final del L2 (o L3) de la nota
   original, dentro de una admonition `:::note` o `:::tip` para que sea
   visible sin expandir un plegable.
4. **La nota hermana hereda el `related`** de la original y añade
   `related: [parent]` en su frontmatter.
5. **Las unidades must-keep migran** con su contenido; el conteo total
   del ledger no cambia (ver §6).

### 5.3 Ejemplo de extracción

**Antes** (nota `postgres-shared-buffers` con 180 líneas, L3 = 120 líneas):

```
postgres-shared-buffers.note-ir.json
├── L1 (8 líneas)
├── L2 (52 líneas)
└── L3 (120 líneas)  ← demasiado grande
```

**Después** (extracción de L3 a nota hermana):

```
postgres-shared-buffers.note-ir.json          (60 líneas: L1 + L2 + cross-ref)
├── L1 (8 líneas)
├── L2 (52 líneas)
└── :::note
    Para detalles exhaustivos, ver [[note:postgres-shared-buffers-deep-dive]].

postgres-shared-buffers-deep-dive.note-ir.json (120 líneas: L3)
├── ## Edge cases
├── ## Comparación con alternativas
└── ## Historial de versiones
```

### 5.4 Anti-patrones de extracción

- Extraer sin back-link bidireccional (la nota padre debe apuntar a la
  hija y viceversa).
- Extraer el L3 esencial (el que aclara conceptos del L2); ese se queda.
- Crear nota hermana con nombre inconsistente (debe ser `<parent>-deep-dive`).
- Crear múltiples notas hermanas para una sola nota padre (una sola, máximo).

## §6 · Integración con el ledger

### 6.1 Asignación de unidades a capas

Cada `must-keep` unit del ledger se asigna a UN layer (l1, l2 o l3):

```json
{
  "unit_id": "u_001",
  "section_path": "/ch02/intro/l2/configuracion",
  "layer": "l2",
  "must_keep": true,
  "state": "written",
  "target_note": "postgres-shared-buffers"
}
```

### 6.2 Aplicación de capas (refactor)

Al refactorizar una nota para asignar capas:

- Cada unidad mantiene su `unit_id` y `must_keep: true`.
- Solo cambia el `layer` (l1/l2/l3) y el `section_path` si se mueve de
  sección.
- Las unidades pueden reasignarse entre capas sin perder su identidad.

### 6.3 Extracción a nota hermana (ledger)

Cuando se extrae L3 a `<parent>-deep-dive`:

- Las unidades L3 del padre **migran** al `target_note: parent-deep-dive`.
- El `must-keep` count del padre **no decrementa** (la unidad sigue
  existiendo; solo cambió de archivo).
- El `manifest.json` de la hermana registra las unidades migradas.

**Regla de invariancia (criterio #3):**

```
n_must_keep_terminal(parent_after) + n_must_keep_terminal(sibling_after)
    >= n_must_keep_terminal(parent_before)
```

El conteo total de unidades must-keep **no decrementa** tras aplicar
capas o extraer.

### 6.4 Comando CLI

```bash
# El validador F49 puede emitir W12 si la nota excede threshold sin capas.
python3 scripts/validate/validate_ir.py --ir foo.note-ir.json --sdm ...

# El transformador F50 tiene subcomando `layer` para asignar capas.
python3 scripts/authoring/transform.py layer \
    --ir foo.note-ir.json \
    --node-path "blocks[3]" \
    --layer l1

# El script `ledger.py mark` para migrar unidades (futuro: F52 trace).
python3 scripts/util/ledger.py mark UNIT_ID --state merged --target-note parent-deep-dive
```

## §7 · Override por tipo (15 tipos cerrados)

Tabla normativa: para cada uno de los 15 tipos cerrados de F78-F92, indica
si las 3 capas son obligatorias siempre o solo si ≥ 50 líneas.

| # | Tipo | Requiere 3 capas | Razón |
|---|---|---|---|
| 1 | `concept` | si ≥ 50 líneas | Concepto puede ser breve o extenso. |
| 2 | `api-reference` | siempre | Referencia API suele ser larga. |
| 3 | `procedure` | si ≥ 50 líneas | Procedimiento puede ser breve. |
| 4 | `configuration` | si ≥ 50 líneas | Configuración puede ser breve. |
| 5 | `error-troubleshooting` | siempre | Diagnóstico requiere L3 (todos los códigos). |
| 6 | `architecture` | siempre | Arquitectura es exhaustiva por naturaleza. |
| 7 | `syntax` | si ≥ 50 líneas | Sintaxis puede ser breve. |
| 8 | `data-model` | siempre | Modelo de datos es exhaustivo. |
| 9 | `chapter-digest` | siempre | Resumen estructurado. |
| 10 | `comparison` | siempre | Comparación tiene 3 niveles. |
| 11 | `version-delta` | si ≥ 50 líneas | Delta puede ser breve. |
| 12 | `glossary-term` | no (L2 basta) | Término de glosario es corto. |
| 13 | `cheatsheet` | no (L2 basta) | Cheatsheet es compacto. |
| 14 | `index-moc` | no | MOC es solo enlaces. |
| 15 | `practice` | si ≥ 50 líneas | Práctica puede ser breve. |

**Resumen:** 4 tipos siempre requieren 3 capas (filas 2, 5, 6, 8, 9, 10);
los otros 11 solo las requieren si exceden el threshold.

## §8 · Anti-patrones transversales

Patrones que cruzan varias capas y que el validador o el auditor marcan
como warning/error.

| # | Anti-patrón | Consecuencia | Reemplazo correcto |
|---|---|---|---|
| 1 | L3 omitido (no aparece en la nota) | Falla verificación de fidelidad (INV-08, F42). | L3 siempre presente, en plegable si > 100 líneas. |
| 2 | L3 mal asignado como L1 o L2 | El lector pierde la profundidad al expandir el L1. | Reasignar con `transform.py layer`. |
| 3 | L1 demasiado largo (> 8 líneas / > 60 palabras) | Pierde autonomía; el lector abandona. | Dividir entre L1 y L2. |
| 4 | L1 sin ejemplo mínimo | El lector no concreta el concepto. | Añadir 1 línea de ejemplo. |
| 5 | Marca `{layer:lX}` fuera de heading | El parser (F48) lo ignora o falla; el layer queda ambiguo. | Mover la marca inmediatamente después del heading. |
| 6 | Múltiples `{layer:lX}` consecutivos | Conflicto de asignación; el último gana. | Dejar solo uno. |
| 7 | Extracción a nota hermana sin back-link | El lector queda sin pista para profundizar. | Añadir `[[note:sibling]]` en la nota padre. |
| 8 | Mezclar L1 dentro de L2 sin separador | Rompe la autonomía de L1. | Mover el contenido de L1 a su propio heading antes del L2. |

## §9 · Cambios permitidos sin reabrir F51

Cambios que se pueden hacer en `depth-layers.md` sin reabrir la fase:

1. Añadir anti-patrones a §8 cuando F49 detecte un patrón nuevo.
2. Añadir entradas a §7 si F78-F92 modifican un tipo existente.
3. Refinar §6 si F15/F38 modifican el ledger.
4. Refinar §5 (extracción) si F50 añade nuevas operaciones.
5. Ajustar el threshold de 50 líneas si el corpus lo demanda (con evidencia
   de falsos positivos).

**Reabren F51:**

- Cambiar el conjunto cerrado de 3 capas (añadir/quitar L0, L4, etc.).
- Cambiar el contenido obligatorio de L1 (definición, propósito, ejemplo,
  caso de uso).
- Cambiar la regla "L3 nunca se omite" (rompe INV-08).
- Cambiar el threshold > 100 líneas / 30% para extracción.

## §10 · Cómo verificar

Verificaciones automatizables. Cada una debe pasar antes de cerrar F51.

```bash
# Estructura
wc -l skill/notemartin-study-notes/references/04-authoring/depth-layers.md   # 500-700
rg -c '^### 3\.' skill/notemartin-study-notes/references/04-authoring/depth-layers.md   # ≥ 3 (L1, L2, L3)

# Cobertura de las 3 capas
rg -c '^### 3\.1 L1' skill/notemartin-study-notes/references/04-authoring/depth-layers.md   # 1
rg -c '^### 3\.2 L2' skill/notemartin-study-notes/references/04-authoring/depth-layers.md   # 1
rg -c '^### 3\.3 L3' skill/notemartin-study-notes/references/04-authoring/depth-layers.md   # 1

# Sintaxis NoteMark documentada
rg -c '\{layer:' skill/notemartin-study-notes/references/04-authoring/depth-layers.md   # ≥ 3

# Override por tipo (15 entradas)
rg -c '^\| \d+ \| `(concept|api-reference|procedure|configuration|error-troubleshooting|architecture|syntax|data-model|chapter-digest|comparison|version-delta|glossary-term|cheatsheet|index-moc|practice)`' skill/notemartin-study-notes/references/04-authoring/depth-layers.md   # 15

# Coherencia con notemark.md
wc -l skill/notemartin-study-notes/references/04-authoring/notemark.md   # ≤ 159
rg '## §9' skill/notemartin-study-notes/references/04-authoring/notemark.md   # §9 sigue existiendo (ahora puntero)

# Fixture
python3 evals/depth-layers-sample/run_eval.py --check-all
```

Tres criterios de la Fase 51 (ROADMAP):

1. **Toda nota extensa identifica sus tres capas.** §7 tabla + §2 threshold.
   El fixture valida con 3 notas extensas.
2. **L1 se lee de forma independiente y da comprensión correcta.** §3.1
   contenido obligatorio. El fixture mide `len(L1_words) <= 60` y verifica
   que contenga definición, propósito, ejemplo y caso de uso.
3. **Ninguna unidad del ledger desaparece al aplicar capas.** §6 regla
   `n_must_keep_terminal(after) >= n_must_keep_terminal(before)`. El
   fixture ejecuta `ledger.py check` antes/después y compara.
