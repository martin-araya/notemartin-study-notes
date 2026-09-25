# Unidades de información — `references/03-knowledge/information-units.md`

> Documento normativo de la **Fase 37** del roadmap. Define qué es una unidad de información, los 14 tipos cerrados, las reglas automáticas que asignan criticidad y la prohibición de fusionar `must-keep`. Es la entrada del Coverage Ledger (F15/F38).
>
> Documentos complementarios: `references/03-knowledge/ledger.md` (F15, contrato del ledger; este doc alimenta su campo `type`), `references/02-source-model/spec.md` (F13, contrato del SDM del que se leen los bloques), `references/02-source-model/editorial-semantics.md` (F35, mapeo de cajas editoriales a tipos `note`/`warning`/`example`; relevante para `warning` y `version-note`), `references/02-source-model/anchors.md` (F32, formato `source_block_ids`), `skills/AGENT.md` §17 (definición coloquial de unidad; este doc la operacionaliza), §13 INV-08 (100 % `must-keep` terminal).
>
> Enrutado desde N2: `docs/skill-anatomy.md` §6 fila `F37`. Lo lee el agente en L2 al extraer unidades; lo lee el script de F38 para obtener el enum cerrado y las reglas R1–R5.

## §1 · Propósito y alcance

Una **unidad de información** es una *afirmación atómica con valor independiente*: cambia el comportamiento del lector, responde una pregunta concreta sobre el dominio o fija una restricción operacional. Una unidad se respalda por uno o varios bloques del SDM y se registra en el Coverage Ledger con un `unit_id` único.

**Sí es unidad** (afirmativa):
1. `"shared_buffers" tiene default "128 MB"` — fija un valor configurable; perderlo rompe la operación.
2. `"PG_DUMP retorna exit code 2 ante error de conexión"` — un lector necesita saber cuándo la herramienta falla.
3. `"El algoritmo es estable cuando la matriz es diagonal dominante"` — un teorema enunciado por la fuente.

**No es unidad** (contraejemplos):
- Un párrafo descriptivo que cubre 4 ideas: cada idea es una unidad; el párrafo no lo es.
- Un encabezado de sección: la sección ya está en el SDM (`section.title`); el encabezado no añade contenido.
- Una nota editorial "vimos el capítulo anterior": navegación, no contenido.
- Una frase de transición ("A continuación veremos…") sin información nueva.

**Lo que este spec NO es**: la forma del ledger (F15), el script que contabiliza (F38), la redacción de la nota (F12 NoteMark + F43 auditoría), ni el render de cada tipo (L4). Este spec define **qué se extrae**, no **cómo se escribe** ni **cómo se publica**.

## §2 · Cuándo se aplica

| Capa / fase | Lee este doc cuando… |
|---|---|
| L2 (agente extrayendo unidades) | Recorre `sdm.json` y decide qué unidades declarar; consulta §3 para clasificar y §5 para asignar criticidad. |
| L3 (agente redactando NoteMark) | Antes de redactar, confirma que cada unidad extraída tiene destino (`target_note`); el doc le recuerda §6 (no fusión de `must-keep`). |
| F38 (`scripts/util/ledger.py`) | Para obtener el enum cerrado de tipos y aplicar R1–R5 sobre cada unidad entrante. |
| F43 (auditoría de no-pérdida) | Para verificar que toda unidad del ledger tiene tipo y criticidad consistentes con §3–§5. |
| F118 (suite automatizada) | Para correr el eval de §10 y comparar dos extracciones independientes. |

**No se aplica a**: ingesta (L0–L1 producen SDM, no unidades), ni al render (L4), ni al glosario/conflictos (F39–F41).

## §3 · Taxonomía cerrada de los 14 tipos

Enum cerrado. No existe `other` ni `unknown`. Una idea que no encaje en ninguno de los 14 tipos **no es una unidad** y queda como bloque huérfano; F38 lo detecta con "contenido sin respaldo".

| `type` | Definición operativa | Cómo se reconoce | Ejemplo técnico | Forma JSON de `content` |
|---|---|---|---|---|
| `definition` | Enunciado que **define** un término técnico o del dominio en una frase autocontenida. | Bloque `prose` cuya primera oración tiene forma "X es Y", "X (del inglés Y) …", o entrada de glosario de la fuente. | *“Una vista materializada es una relación almacenada que materializa el resultado de una consulta.”* | `{text: string}` |
| `mechanism` | Explicación **causal** de por qué algo funciona: cómo una pieza produce un efecto. | Bloque `prose` con conectores causales ("porque", "debido a", "as a result", "esto se debe a"). | *“El WAL previene la pérdida de datos porque cada cambio se fsyncea antes del COMMIT.”* | `{text: string}` |
| `parameter` | Nombre y semántica de un valor configurable de un sistema, comando o API. | Fila de tabla de parámetros, o bloque `prose` con forma `"<nombre>": <descripción>` donde `<nombre>` matchea `^[a-z][a-z0-9_.-]*$`. | *“`shared_buffers`: tamaño en MB del caché compartido de PostgreSQL.”* | `{name: string, description: string}` |
| `default` | Valor por defecto de un `parameter`, opcional o flag. | Bloque que sigue a un `parameter` y contiene "default", "por defecto", "valor predeterminado". | *“`shared_buffers` por defecto es `128 MB`.”* | `{name: string, value: string \| number \| boolean}` |
| `constraint` | Restricción **inviolable** del sistema: límite duro, precondición, invariante. | Bloque con tono imperativo negativo ("no puede", "no debe", "must not"), o tabla con columna "Constraints". | *“Una clave primaria no puede contener NULL.”* | `{text: string}` |
| `step` | Acción numerada o secuencial de un procedimiento. | Bloque `list` numerada, o `step` block del SDM (F13). | *“3. Verificar el hash con `sha256sum archivo.iso`.”* | `{ordinal: integer, text: string}` |
| `example` | Caso de uso ilustrativo, generalmente con código o entrada/salida. | Bloque `example` del SDM, bloque `code` introducido por "Ejemplo:" o "Example:". | *“Ejemplo: `SELECT pg_reload_conf();` recarga la configuración.”* | `{text?: string, code?: string}` |
| `warning` | Advertencia editorial de la fuente: peligro, trampa, consecuencia no obvia. | Bloque SDM `editorial_note.box` con severidad `caution`/`removed` (F35), o bloque `warning` nativo. | *“WARNING: este comando borra datos sin pedir confirmación.”* | `{text: string, severity: "caution" \| "removed" \| null}` |
| `error-code` | Identificador o mensaje textual de un error que el sistema puede emitir. | Bloque que contiene un código en MAYÚSCULAS + número (`E1234`, `ORA-00904`), o `error-code` block del SDM. | *“`EADDRINUSE`: el puerto ya está en uso.”* | `{code: string, message: string}` |
| `tradeoff` | Comparación explícita entre dos opciones con su criterio de elección. | Bloque `prose` con "frente a", "versus", "a cambio de", "however". | *“Usar un índice acelera lecturas pero ralentiza escrituras.”* | `{text: string}` |
| `version-note` | Hecho que cambia **entre versiones** del producto documentado. | Bloque con "desde vN", "new in", "obsolete in", "removed in"; o bloque SDM `note.severity=novelty` (F35). | *“Desde PostgreSQL 13, `wal_keep_size` reemplaza a `wal_keep_segments`.”* | `{text: string, version_introduced?: string, version_removed?: string}` |
| `syntax-rule` | Regla formal de la gramática o sintaxis de un lenguaje o DSL. | Bloque `syntax-diagram` del SDM, bloque `prose` con forma "la sintaxis es …", o bloque `code` con notación BNF/EBNF. | *“`<identificador>` ::= `[a-zA-Z_][a-zA-Z0-9_]*`.”* | `{rule: string, ebnf?: string}` |
| `cross-reference` | Apunta a otra sección, capítulo, RFC o nota externa donde se desarrolla el mismo concepto. | Bloque con "ver también", "see also", "véase", "cf.", o enlace explícito. | *“Ver §4.3.2 sobre el grafo de prerrequisitos.”* | `{target: string, label?: string}` |
| `formula` | Expresión matemática o algoritmo en pseudocódigo formal. | Bloque `formula` del SDM (F24) o `code` con sintaxis LaTeX/matemática predominante. | *“`t = O(n log n)` para heapsort.”* | `{latex: string, numbered?: boolean, label?: string}` |

## §4 · Criticidad

Dos valores, ambos terminales para la cobertura cuando la unidad alcanza estado ≠ `pending` (F15 §5).

| Valor | Definición | Consecuencia práctica |
|---|---|---|
| `must-keep` | La unidad no puede omitirse **bajo ninguna circunstancia**: si se pierde, la nota pierde fidelidad sobre la fuente y la puerta de fidelidad (architecture.md §3.3) falla. | Rige INV-08. Toda `must-keep` debe alcanzar estado terminal en el ledger (`written`, `merged` o `discarded` con motivo). |
| `context` | Aporta color, redundancia o profundidad pero no es indispensable para la fidelidad. | Puede fundirse en otra unidad con `discard_reason: "redundant-with:<unit_id>"`, o descartarse con cualquier motivo cerrado de F15. |

## §5 · Reglas automáticas de criticidad

Lista cerrada de reglas que el script de F38 aplica **sin intervención del agente**. Una unidad que active regla alguna **no puede declararse `context`**. El agente **no decide** estas críticas; el script las calcula.

| ID | Regla |
|---|---|
| **R1** | Toda unidad de tipo `parameter` con `content.name` no vacío → `must-keep`. |
| **R2** | Toda unidad de tipo `default` → `must-keep`. |
| **R3** | Toda unidad de tipo `error-code` → `must-keep`. |
| **R4** | Toda unidad de tipo `warning` cuyo bloque SDM origen sea `editorial_note` (severidad `caution`/`removed`) o `warning` → `must-keep`. |
| **R5** | Toda unidad de tipo `formula` con `content.numbered == true` → `must-keep`. |

**Default**: las unidades cuyo tipo no activa regla alguna quedan como `context`.

**Elevación**: el agente **puede** elevar una `context` a `must-keep` declarando `criticality: "must-keep"` con `content.rationale` no vacío. La elevación queda registrada y es auditable. La inversa —bajar una `must-keep` automática a `context`— está **prohibida** y falla el validador de F38.

**R-candidata no adoptada**: añadir `version-note` como regla automática. Decisión: queda fuera hasta que F118 (suite de evals) muestre que se pierden `version-note` críticas. Documentado en `PROGRESS.md` tras F118. No reabre F37.

## §6 · Prohibición de fusión

Regla dura: **dos unidades con `criticality: "must-keep"` nunca se fusionan en una sola**, ni en la redacción de la nota ni en el ledger. Una nota puede cubrir varias unidades `must-keep` en el mismo párrafo; lo que el ledger conserva es la granularidad, no la fusión textual.

Mecanismo: si una unidad `must-keep` repite información ya presente en otra, se declara `discard_reason: "redundant-with:<unit_id>"` (motivo cerrado del ledger, F15). Esto **no** es fusión: produce dos entradas en el ledger con destinos posiblemente idénticos y una marcada como descartada.

`context` se permite fusionar libremente con la misma mecánica (`redundant-with:<unit_id>`).

## §7 · Forma JSON canónica

El script de F38 construye las entradas del ledger. Esta es la forma que producirá (forward-looking; F38 cierra el schema):

```json
{
  "unit_id": "u_001",
  "source_block_ids": ["a8f4ce140580"],
  "source_section_path": "/ch02/section-2.3.2",
  "type": "parameter",
  "content": { "name": "shared_buffers", "description": "Tamaño en MB del caché compartido." },
  "criticality": "must-keep",
  "criticality_rationale": "R1",
  "merged_into": null,
  "state": "pending"
}
```

| Campo | Tipo | Notas |
|---|---|---|
| `unit_id` | string | `u_001`, `u_002`, … dentro del ledger. |
| `source_block_ids` | array[string] | sha1 hex 12 (F13); mínimo 1. |
| `source_section_path` | string | Ruta canónica de la sección. |
| `type` | enum(14) | Uno de los 14 valores de §3. |
| `content` | shape | Forma según `type`; ver tabla §3 columna derecha. |
| `criticality` | enum | `must-keep` o `context`; **calculada por R1–R5** salvo override. |
| `criticality_rationale` | string \| null | `"R1"`–`"R5"` cuando aplica regla automática; texto libre cuando es elevación; `null` cuando es `context` por default. |
| `merged_into` | string \| null | `unit_id` de la unidad que la absorbió; poblado en `redundant-with:<unit_id>`. |
| `state` | enum | `pending`/`written`/`merged`/`discarded` (F15). |

## §8 · Procedimiento de extracción

Algoritmo en 5 pasos que el agente aplica sobre `sdm.json`:

1. **Walk por bloques en orden de aparición** dentro de cada sección.
2. **Matchear uno o más tipos por señales**: usar la columna "Cómo se reconoce" de §3. Un bloque puede generar varias unidades (p. ej., una `parameter` + su `default`).
3. **Agrupar por sección si una unidad requiere varios bloques**: si una `mechanism` se explica en 2 bloques consecutivos sin titulación intermedia, agruparlos antes de crear la unidad; `source_block_ids` lleva los N ids.
4. **Aplicar R1–R5** al resultado: marcar `criticality` y `criticality_rationale` por construcción.
5. **Elevar `context` solo si hay razón**: si el agente cree que la unidad es crítica pese a no activar regla, añadir `criticality: "must-keep"` + `content.rationale`.

## §9 · Anti-patrones

- Fusionar dos `must-keep` en una sola unidad del ledger → viola §6.
- Tratar `default` como sub-tipo de `parameter` → son tipos distintos; `parameter` describe el nombre y semántica, `default` describe el valor.
- Asignar `must-keep` sin activar regla automática ni declarar `criticality_rationale` → el validador de F38 falla; el agente está "inventando" criticidad.
- Crear unidades "resumen de sección" → la sección ya está en el SDM; el resumen no aporta información nueva y se confunde con la unidad.
- Declarar `warning` cuando el SDM no tiene bloque `editorial_note` ni `warning` → §3 columna "Cómo se reconoce".
- Asignar `context` a un `error-code` o a un `default` → viola R2 y R3.
- Crear unidades cuyo `source_block_ids` esté vacío → viola F13 y el ledger schema.
- Usar `merged_into` cuando el destino es `written` (es solo para `discarded`).

## §10 · Cómo verificar + cambios permitidos

Comandos grepeables:

```bash
# 1. Spec dentro de presupuesto.
wc -l references/03-knowledge/information-units.md                  # ≤ 300
rg -c '^## §' references/03-knowledge/information-units.md           # 11 secciones

# 2. 14 tipos cubiertos en §3.
rg -o '\b(definition|mechanism|parameter|default|constraint|step|example|warning|error-code|tradeoff|version-note|syntax-rule|cross-reference|formula)\b' \
   references/03-knowledge/information-units.md | sort -u | wc -l    # = 14

# 3. Cero mención a plataformas (INV-06).
rg -i 'obsidian|notion|appflowy' references/03-knowledge/information-units.md  # vacío

# 4. Eval de los 3 criterios.
python3 evals/information-units-sample/run_eval.py                   # exit 0

# 5. Fixtures válidos.
for f in evals/information-units-sample/fixtures/*.json; do
  python3 -c "import json,sys; json.load(open('$f'))" && echo "OK $f"
done
```

**Cambios permitidos sin reabrir F37** (versión menor):
- Añadir un ejemplo técnico en §3.
- Refinar el wording de §1.
- Añadir una fila a la tabla §2.
- Añadir una R-candidata a §5 si se demuestra su necesidad (sin activarla).

**Reabren F37** (versión mayor):
- Añadir un tipo nuevo al enum de §3.
- Eliminar un tipo existente.
- Cambiar la definición operativa de un tipo.
- Mover una regla de R1–R5 a "caso especial" con override permitido.
- Permitir fusión de dos `must-keep`.
- Cambiar la lista cerrada de campos de §7.
- Cambiar la forma de `criticality_rationale`.

## §11 · Glosario compacto

| `type` | En una línea |
|---|---|
| `definition` | Enunciado que define un término. |
| `mechanism` | Explicación causal de por qué algo funciona. |
| `parameter` | Nombre y semántica de un valor configurable. |
| `default` | Valor por defecto de un `parameter`. |
| `constraint` | Restricción inviolable del sistema. |
| `step` | Acción numerada de un procedimiento. |
| `example` | Caso de uso ilustrativo. |
| `warning` | Advertencia editorial: peligro o trampa. |
| `error-code` | Identificador o mensaje de un error. |
| `tradeoff` | Comparación explícita entre dos opciones. |
| `version-note` | Hecho que cambia entre versiones. |
| `syntax-rule` | Regla formal de gramática o sintaxis. |
| `cross-reference` | Apunta a otra sección o documento. |
| `formula` | Expresión matemática o algoritmo formal. |
