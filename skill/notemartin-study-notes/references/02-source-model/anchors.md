# Anclas — reglas del Source Document Model

> Documento normativo de la **Fase 32** del roadmap. Define las reglas que convierten un bloque del SDM en una unidad referenciable de forma estable entre ingestas, sesiones y herramientas downstream (L2 ledger, L3 redacción en NoteMark, L4 deep-links en destinos).
>
> Documentos complementarios: `references/02-source-model/spec.md` (F13, contrato del SDM y fórmula del id en §8), `references/02-source-model/build-sdm.md` (F31, mecánica de ensamblado), `references/00-pipeline/architecture.md` §3.2 (L1 cierra el SDM con anclas).
>
> Enrutado desde N2: `docs/skill-anatomy.md` §6 fila `F32`.

## §1 · Propósito y alcance

Un **ancla** es la combinación de cuatro elementos canónicos (`block_id`, `section_path`, `page`, `bbox`/`char_range` opcional) que hacen un bloque del SDM **referenciable de forma estable** en el tiempo y a través de herramientas. Mientras `spec.md` (F13) define el shape del ancla dentro del schema JSON, este doc define las **reglas** que la producen y la consumen, con énfasis en tres casos que han dado problemas empíricos:

- documentos sin numeración impresa (HTML, EPUB, transcripciones),
- documentos con numeración impresa inconsistente (duplicados, saltos),
- persistencia entre sesiones y entre ingestiones de la misma fuente.

**No es**: el contrato JSON Schema (eso es `spec.md`), ni el algoritmo de ensamblado (eso es `build-sdm.md` / F31). Tampoco es una decisión de cómo **mostrar** un ancla en destino — eso corresponde al render (L4).

## §2 · Cuándo se aplica

| Capa | Lee este doc cuando… |
|---|---|
| L1 (F31 `build_sdm.py`) | Decide cómo derivar `section_path` para una sección y cómo ligar cada bloque a su `block_id`. |
| L2 (`Coverage Ledger`, F15) | Construye `source_block_ids: [hex12]` al mapear unidades a bloques del SDM. |
| L3 (NoteMark, F12/F48) | El agente redacta una cita con `{src:blk_xxxx}`; consulta la regla para saber qué `block_id` poner. |
| L4 (`references/08-render/linking.md`) | Resuelve deep-links y back-links a partir del `block_id`. |

En el modo **§7.4 Actualización incremental** de `SKILL.md` se relee siempre que el agente consulta trazabilidad por ancla.

## §3 · Modelo de ancla — los cuatro elementos canónicos

| Elemento | Tipo | Obligatorio | Quién lo emite | Notas |
|---|---|---|---|---|
| `block.id` | `string` (12 hex) | sí | F31 `build_sdm.py` | `sha1(source.hash + section_path + str(block_index))[:12]`. Inmutable durante la vida del SDM. Ver `spec.md` §8. |
| `block.anchor.section_path` | `string` | sí | F31 | Mismo valor en todos los bloques de la sección (redundancia explícita per `spec.md` §5). |
| `block.anchor.page` | `integer≥1` o `null` | sí | F31 | `null` cuando la fuente no está paginada (HTML/EPUB/transcript). |
| `block.anchor.bbox` | `[x, y, w, h]` o `null` | no | F22/F18 cuando existe | `null` si la fuente no tiene coordenadas (HTML). |
| `block.anchor.char_range` | `[start, end]` o `null` | no | F18 cuando existe | Útil para resaltar sin recalcular OCR. |

La unidad mínima de ancla es el **bloque**, no el sub-elemento. No existen anclas a palabras, runs, ítems de lista, celdas de tabla o filas de tabla. Ver §4.

## §4 · Granularidad — bloque, no sub-elemento

Los **16 tipos de bloque** del SDM (per `spec.md` §4.1) son las unidades mínimas:

`prose`, `heading`, `list`, `table`, `code`, `console`, `formula`, `figure`, `caption`, `note`, `warning`, `example`, `syntax-diagram`, `footnote`, `toc`, `boilerplate`.

No se subdivide más fino porque (a) el schema exige `id` a nivel de bloque y (b) el ledger L2 trabaja con `source_block_ids` por bloque. Cualquier intento de anclar a sub-elementos **rompe la coherencia** entre schema, ledger y consumidores.

**Tabla de mapeo unidad-de-ancla vs unidad-de-texto:**

| Unidad de texto | Unidad de ancla |
|---|---|
| Página | varios bloques (no es una unidad) |
| Párrafo | 1 bloque `prose` |
| Bullet de lista | 1 bloque `list` (que contiene items como `content.items[]`, **no** como bloques separados) |
| Celda de tabla | 1 bloque `table` (la celda vive en `content.rows[i][j]`) |
| Línea de código | 1 bloque `code` (texto completo en `content.text`) |
| Pie de figura | 1 bloque `caption` separado (per F31 §6, ambos coexisten — `figure.content.caption` Y bloque `caption` propio) |
| Footnote | 1 bloque `footnote` con `content.ref` |
| Imagen | 1 bloque `figure` con `content.src` (resolución a bytes vía F33, fuera de alcance del ancla) |

## §5 · Construcción de `section_path` por formato

`section_path` es la **columna vertebral del ancla**. Cambia el algoritmo de asignación ⇒ cambian todos los `block_id` (ver §8). Cada formato tiene su regla; el script que las ejecuta es `build_sdm.py` (F31 §5).

| Formato | Regla de `section_path` | Fuente |
|---|---|---|
| PDF con outline | `outline[i].section_path` literal | `fragments.json.outline` (F18 §6) |
| PDF sin outline | heading hierarchy con fallback per-page (`/page-NNNN`) | F18 §6.2 |
| HTML (web docs) | slug de `url_path` con ordinal `-N` si colisión | F29 + F31 `_section_path_for_html_section` |
| EPUB | `/chNN` por `chapter` (uno por capítulo) | F28 + F31 `_section_path_for_other_format` |
| DOCX | `/chNN` por `Heading 1` detectado | F28 + F31 `_section_path_for_other_format` |
| PPTX | `/slide-NN` por `slide` index | F28 + F31 `_section_path_for_other_format` |
| Transcript (SRT/VTT/JSON) | `/talk/<slug>` para toda la charla (sin subdivisión por utterance) | F28 |
| Repo / Markdown | `/readme` (uno único) | F28 (stub hasta F29B Markdown) |

**Slugificación**: kebab-case ASCII, caracteres no alfanuméricos → `-`, recortado a 64 caracteres, fallback `"section"` si vacío. Implementada en F31 `_slugify`.

## §6 · Reglas posicionales del `section_path`

Cuatro reglas duras que el `section_path` debe cumplir:

1. **Nunca refleja el número impreso.** Un capítulo rotulado "1.1 Foo" puede tener `section_path = /ch01/foo`. La numeración impresa se conserva en `title` (atributo de la sección) pero **no entra** al `section_path`.
2. **Slug ASCII kebab-case**, sin espacios ni caracteres extendidos. E.g. `"Capítulo 1: Introducción"` → `"capitulo-1-introduccion"`.
3. **Ordinal `-N` si colisión.** Dos secciones con el mismo slug en la misma fuente reciben `-1`, `-2`, ... (F31 implementa ya `-2` para PDF en `_assign_sections_from_outline` y aplica la misma regla en las ramas HTML/EPUB via `_section_path_for_*`).
4. **Estable al renumerar la fuente.** Cambiar "1.2.3" por "1.3" en la siguiente impresión **no** mueve un bloque a otra sección. Id cambia solo si la **posición estructural** cambia (qué bloque es el N-ésimo de la sección).

> **Razón:** el `block.id` es `sha1(hash + section_path + idx)[:12]`. Si el `section_path` dependiera del número impreso, renumerar la siguiente edición invalidaría **todos los `source_block_ids`** del ledger y todas las citas `{src:blk_xxxx}` de las notas ya publicadas. Por eso la **posición es la firma**, no el número.

## §7 · Numeración impresa: duplicados y saltos

### 7.1 Duplicados

Una fuente con numeración repetida (`1.1 Foo`, `1.1 Bar — duplicate`, `1.2 Baz`) produce:

- **Primera** sección: `section_path = /ch01/foo`, `title = "1.1 Foo"`.
- **Segunda** (mismo slug): `section_path = /ch01/foo-2`, `title = "1.1 Bar — duplicate"` (la numeración impresa no se altera).
- **Tercera**: `section_path = /ch01/baz`, `title = "1.2 Baz"`.

Cada bloque dentro de cada sección recibe su propio `block.id` determinista (D5 del plan). El **número impreso se preserva tal cual** en `title`; el `section_path` lleva la firma posicional con ordinal.

### 7.2 Saltos

Una fuente con numeración saltada (`1.1 Foo`, `1.3 Skipped` sin `1.2`) produce dos secciones:

- `section_path = /ch01/foo`, `title = "1.1 Foo"`.
- `section_path = /ch01/skipped`, `title = "1.3 Skipped"`.

**Nunca se inventa** una sección `1.2`. La fidelidad a la fuente (INV-03) prohíbe rellenar huecos. Si el número faltante corresponde a un capítulo que el autor reservó para una próxima edición, el SDM no lo anuncia — es decisión del lector cruzarlo con la fuente.

**Reglas duras:**

| Caso | Acción |
|---|---|
| Numeración impresa igual entre dos secciones | Sufijo `-N` en `section_path`; ambas `title` preservan la numeración original. |
| Hueco en la numeración | No se rellena. Solo se procesan las secciones presentes. |
| Numeración impresa contradictoria (e.g. `1.5` antes de `1.4`) | Idéntico a duplicados: `section_path` usa posición + ordinal; `title` preserva la numeración impresa. |

## §8 · Persistencia entre sesiones

### 8.1 Invariante contractual

> Mismo `source.hash` + mismo algoritmo de asignación de `section_path` ⇒ mismos `section_path` ⇒ mismos `block.id`.

El `block.id` se recalcula siempre desde cero (`sha1(hash + section_path + str(block_index))[:12]`, `spec.md` §8) — nunca persiste entre sesiones en una tabla auxiliar. Si el input es idéntico y el algoritmo no cambia, el SDM producido es bit-a-bit idéntico.

`build_sdm.py --check-determinism` (F31 §11) lo verifica ejecutando dos veces y comparando bytes. El eval battery de F31 (`evals/build-sdm-sample/run_eval.py`) lo confirma con 4 fixtures + 1000 muestras de paridad con `validate_sdm.compute_block_id`.

### 8.2 Qué invalida la persistencia

| Cambio | Efecto en `block.id` | Acción |
|---|---|---|
| Mismo input, misma versión de `build_sdm.py` | idéntico | ninguna |
| Mismo input, **nuevo algoritmo de asignación** en `build_sdm.py` | TODOS cambian | declarar cambio de algoritmo en `CHANGELOG.md`; el ledger (F15) reporta cada `source_block_ids` que no resuelve; las notas que citan `{src:blk_xxxx}` quedan rotas y requieren regeneración |
| Input distinto (incluso edición nueva del mismo PDF con paginación cambiada) | cambian los afectados | `manifest.json` (F16) lo detecta por cambio de `source.hash`; acción del manifest: REJECT (default), RESET, o MIGRATE |

### 8.3 Persistencia entre formatos

Re-ingestar el mismo contenido como otro formato (e.g. pasar de EPUB a PDF) produce un SDM con hash de fuente distinto y por tanto `block.id`s distintos. **No hay contrato de portabilidad entre formatos**. Cada formato es su propia fuente lógica.

## §9 · L2 → ancla: contrato de referencia

El ledger (F15) representa cada unidad como:

```yaml
unit_id: u_03
source_block_ids: ["bbea33d7135a", "1d4636683c29"]
```

Reglas:

1. **Cada `block_id` debe existir** en el SDM actual. Verificable con `validate_ledger.py --referenced-blocks <sdm>` (cuando F15 se integre con F31).
2. **Una unidad puede referenciar varios bloques** si su contenido está distribuido (típico en unidades de cobertura que abarcan una sección entera). La lista se conserva en orden de aparición.
3. **Una unidad puede no tener `source_block_ids`** solo si su `discard_reason` es uno de `boilerplate | navigation | out-of-scope-by-user` (F15 §6). En cualquier otro caso, una unidad terminal sin anclas es **anomalía** y el agente debe justificarla.
4. **Un `block_id` puede ser referenciado por varias unidades** (e.g. una `concept-nota` y una `code-snippet` que apuntan al mismo bloque `code`). No es 1:1.
5. **El formato de cita en NoteMark** es `{src:blk_xxxx}` donde `xxxx` son los 12 caracteres hex del `block.id`. Esto convierte la cita en una URL relativa: `[[note:id]]` resuelve con L4 al deep-link del bloque.

## §10 · Anti-patrones

- **Derivar `section_path` del número impreso** (e.g. `section_path = "/1.1"`). Invalida §6 y rompe la persistencia.
- **Cambiar la fórmula del `block.id`** sin actualizar `validate_sdm.py` (F13) ni el eval de F31. Los dos divergen y la verificación falla en silencio.
- **Persistir `block.id` en tabla auxiliar** (cache). El id siempre se recomputa; cachear introduce ventanas de inconsistencia.
- **Anclar a sub-elementos** (palabra, run, ítem). Rompe §4 y obliga a rehacer schema, ledger y citas.
- **Rellenar huecos de numeración** (inventar un bloque 1.2 entre 1.1 y 1.3). Viola fidelidad (INV-03).
- **Asignar `section_path` por número de página** para fuentes no paginadas. Página es `null` por definición (schema); el `section_path` es la única coordenada lógica.

## §11 · Verificación

```bash
# 1. Spec dentro de presupuesto.
wc -l references/02-source-model/anchors.md                       # ≤ 250
rg -c '^## §' references/02-source-model/anchors.md              # 11 secciones

# 2. Criterio 1: doc sin numeración produce anclas utilizables.
python3 evals/anchors-sample/run_eval.py                          # PASS los 3 criterios

# 3. Criterio 2: anclas estables (reusa el eval de F31 sin regresión).
python3 evals/build-sdm-sample/run_eval.py                        # PASS los 3 criterios F31

# 4. Criterio 3: toda unidad L2 puede referenciar.
python3 scripts/util/validate_ledger.py --check-source-blocks \
    evals/anchors-sample/build/source-unnumbered-html/sdm.json \
    evals/anchors-sample/build/source-renumbered-pdf/ledger.json # OK referencias válidas

# 5. (Opcional) verificar que el spec F13 no se rompió.
python3 scripts/util/validate_sdm.py --validate \
    evals/anchors-sample/build/*/sdm.json \
    evals/sdm-sample/*.json                                       # todos OK
```

### Cambios permitidos sin reabrir F32

- Ajustar el límite de 64 chars del slug.
- Añadir formatos adicionales (Markdown, AsciiDoc) siguiendo el patrón de §5.
- Mover `char_range` a opcional-persistido (sin cambiar `section_path`).

### Cambios que reabren F32

- `block.id` deja de ser sha1 hash.
- `section_path` empieza a incorporar el número impreso.
- Granularidad cambia (anclas a sub-elementos).
- El anchor pierde `page` o `section_path` como obligatorios.
- Numeración saltada se "rellena" automáticamente.

### Documentos que NO reabren F32 al modificarse

- `references/02-source-model/spec.md` (F13): sus cambios a §5 y §8 ya están refrendados aquí. Si F13 cambia el shape, este doc se actualiza por referencia, no se reabre.
- `scripts/ingest/build_sdm.py` (F31): cambios en algoritmos que no afectan la regla posicional son transparentes para F32. Cambios sí afectados (e.g. nuevo modo de slugificación) **no** reabren F32, pero exigen ejecutar `evals/anchors-sample/run_eval.py` y pueden detectarse como regresión en `evals/build-sdm-sample/run_eval.py` (criterio 2 de F31).
