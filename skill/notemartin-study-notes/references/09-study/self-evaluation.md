# `references/09-study/self-evaluation.md` — Autoevaluación por tipo

> Documento normativo de la **Fase 102** `[ref]`. Define el catálogo cerrado
> de los **5 tipos de pregunta** (recuerdo, aplicación, diagnóstico, decisión,
> predicción), el **mapeo cerrado tipo-de-nota × tipos-de-pregunta** para
> los 15 tipos de nota canónicos (F78-F92), la **forma canónica** de las
> preguntas y respuestas plegables, la **regla de referencia pura** (solo
> diagnóstico + decisión; nunca recuerdo), el **validador algorítmico**
> `scripts/validate/self_eval_check.py` con 7 reglas V1-V7, y los
> **3 anti-patrones AP13-AP15** específicos de autoevaluación.
>
> F102 cierra los 3 criterios del ROADMAP §1713-1715:
> cada tipo de nota tiene tipos de pregunta asignados (§3);
> toda respuesta plegable enlaza a su fundamento (`> Fundamento: …`, §5);
> ninguna pregunta se responde copiando una línea (Jaccard ≤ 0.8 sobre
> palabras no técnicas, §6 V4).
>
> **Cuándo cargar:** antes de cerrar una nota que requiere autoevaluación
> (todo `note-type` excepto `index-moc`); al revisar una nota con `## Autoevaluación`
> detectada por `self_eval_check.py` como violatoria; al construir el deck
> de repaso (F103 lo extenderá).
>
> **Wirings:**
> - `references/04-authoring/properties.md` (F47) §5.21 — propiedad opcional `self-evaluation-types`.
> - `references/04-authoring/block-directives.md` (F45) §10.7 (`:::collapsible`)
>   y §10.17 (`:::question`) — primitivas reutilizadas.
> - `references/04-authoring/inline-marks.md` (F46) — `{src:blk_xxxx}` y `[[note:id]]` para los fundamentos.
> - `references/05-note-types/concept.md` (F78) y los otros 14 tipos — `### Autoevaluación` y checklist `**F102-1**` / `**F102-2**`.
> - `references/06-writing/anti-patterns.md` (F100) §2 — AP13, AP14, AP15.
> - `references/06-writing/i18n-and-citation.md` (F101) §3 — lista de 45 no-traducibles usada por V4.
> - `references/07-visual/density.md` (F76) — R1-R8; la sección `## Autoevaluación` cumple R1 (≤ 60 palabras L1), R2 (≤ 200 palabras L2), R4 (≤ 3 callouts consecutivos), R6 (≥ 1 estructura por sección). Queda **exenta de R3** (≥ 1 anclaje por 200 palabras aplica al cuerpo, no a las preguntas atómicas), de **R5** (las preguntas usan collapsibles, no viñetas GFM), y de **R8** (las respuestas son ejercicios del lector; no son bloques fácticos con anclaje al SDM).
> - `scripts/validate/density_check.py` (F76) — verificador ortogonal invocado por el eval (C10).
> - `SKILL.md` §5.3 — wiring.

---

## §1 · Propósito y alcance

Tres problemas resueltos por F102:

1. **El lector no puede verificar si entendió.** Las notas exponen el contenido pero no le exigen al lector un gesto activo. F102 introduce una **sección `## Autoevaluación`** al final de cada nota (excepto `index-moc`) con **preguntas plegables** que el lector intenta responder antes de mirar.
2. **Las respuestas son copias literales o genéricas.** El estudiante responde con la primera frase que encuentra o recopia la línea de la tabla. F102 obliga a que **toda respuesta sea reformulada** y **enlace a su fundamento** (`{src:blk_xxxx}` o `[[note:id#§N]]`).
3. **Todas las notas se autoevalúan igual.** Una `glossary-term` no debería tener preguntas de aplicación; una `practice` no debería tener preguntas de recuerdo puro. F102 introduce el **mapeo cerrado tipo-de-nota × tipos-de-pregunta** (§3) y la **regla de referencia pura** (§4) para que la autoevaluación sea proporcional al tipo.

**Cierra los 3 criterios del ROADMAP §1713-1715:**

1. _Cada tipo de nota tiene tipos de pregunta asignados_ → §3 (tabla cerrada de 15 filas × 5 columnas) + §6 V2 (validador).
2. _Toda respuesta enlaza a su fundamento_ → §5 (plantilla NoteMark con `> Fundamento: …`) + §6 V3.
3. _Ninguna pregunta se responde copiando una línea_ → §6 V4 (Jaccard ≤ 0.8 sobre palabras no técnicas) + §6 V5 (3-7 preguntas por H3) + §7 AP13.

**Fuera de alcance:**

- Generación de tarjetas (`.apkg` / `.csv` SR) — `scripts/render/flashcards.py` (F55/F56) toma solo nodos `is_atomic_card=true` (definition/formula/glossary-term/key-fact). F102 no convierte preguntas plegables en tarjetas — eso es **F103** (registro de errores propios) y **F104** (rutas de estudio).
- Consulta de repaso vencido (`review-next`) — F103.
- Perfiles de objetivo (`interview`, `certification`, `work`) — F105.
- Detección automática de todos los anti-patrones — F112 (`scripts/validate/` con la suite consolidada). F102 entrega solo el validador específico `self_eval_check.py`.

---

## §2 · Los 5 tipos de pregunta (catálogo cerrado)

Tabla cerrada con los **5 tipos de pregunta** autoasignables. Cada tipo tiene: definición operativa (verbo de inicio), forma canónica del enunciado, ejemplo positivo (con anclaje), ejemplo negativo (qué NO es).

| # | Tipo | Verbo de inicio | Forma canónica del enunciado | Qué verifica |
|---|---|---|---|---|
| 1 | **Recuerdo** | _"¿Qué es…?"_, _"¿Cuál es…?"_, _"Enumera…"_ | _"¿Cuál es el propósito principal de **X**?"_, _"¿Cuál es el valor por defecto de `--flag` en `cmd`?"_ | Memoria factual (recuperar dato nominal). |
| 2 | **Aplicación** | _"Dados…", "¿Cómo…?"_ | _"Dados estos datos de entrada, ¿qué comando usarías para…?"_, _"¿Cómo configurarías X para que Y?"_ | Transferencia a un caso (uso operativo). |
| 3 | **Diagnóstico** | _"Si ves…", "¿Por qué…?"_ | _"Si ves el error `Connection refused`, ¿cuál es la causa más probable?"_, _"¿Por qué `git push --force` devuelve este aviso?"_ | Lectura de síntomas (causa raíz). |
| 4 | **Decisión** | _"Entre… y…, ¿cuál…?"_, _"¿Cuándo NO…?"_ | _"Entre A y B, ¿cuál elegirías para este caso y por qué?"_, _"¿Cuándo NO usar X?"_ | Criterio de diseño (trade-off explícito). |
| 5 | **Predicción** | _"¿Qué ocurre si…?"_, _"¿Qué log/efecto esperas?"_ | _"¿Qué ocurre si ejecutas `kubectl delete pod` con un `ReplicaSet` activo?"_, _"¿Qué log esperas al iniciar `psql` con la variable `PGHOST` apuntando a un host caído?"_ | Anticipación de efectos (encadenamiento). |

**Reglas algorítmicas S1-S3** (para un revisor externo sin abrir el SDM):

- **S1** _Pregunta de recuerdo válida_ → empieza con uno de los verbos de la columna 2, o con "¿Cuál…?", "¿Qué…?", "¿Enumera…?", "¿Cuántos…?". Si no, no es recuerdo.
- **S2** _Pregunta de aplicación válida_ → contiene al menos uno de los marcadores: "dado", "dada", "si tuvieras que", "con estos datos", "para este caso". Si no, no es aplicación.
- **S3** _Pregunta de diagnóstico / decisión / predicción_ → contiene el verbo de inicio de la columna 2 en forma explícita o su paráfrasis canónica.

**Ejemplos negativos** (qué NO es cada tipo):

- _"¿Cómo funciona MVCC?"_ NO es recuerdo: la respuesta requiere explicar un mecanismo (es **aplicación** si la pregunta da un caso, o no encaja si pide teoría abstracta — para teoría abstracta, abrir la nota en lugar de cuestionarla).
- _"¿Qué pasa si ejecuto `rm -rf /`?"_ NO es aplicación: es **predicción** (anticipa el efecto). Aplicación sería _"Dados estos 3 archivos críticos, ¿qué comando usarías para borrarlos de forma reversible?"_.
- _"¿Por qué `docker run` falla?"_ NO es decisión: es **diagnóstico** (causa raíz). Decisión sería _"Entre `docker run -d` y `docker compose up -d`, ¿cuál elegirías para producción y por qué?"_.

---

## §3 · Mapeo cerrado tipo-de-nota × tipos-de-pregunta

**Tabla cerrada de 15 filas × 5 columnas.** Cada celda es `✅` (asignado) o `—` (no aplica). Las notas pueden declarar `self-evaluation-types` con un **superset** del default (nunca un subset) — ver regla V2.

| `note-type` (Fase) | Recuerdo | Aplicación | Diagnóstico | Decisión | Predicción | Notas |
|---|---|---|---|---|---|---|
| `concept` (F78) | ✅ | ✅ | — | ✅ | — | Predicción solo si la nota documenta comportamiento dinámico. |
| `api-reference` (F79) | ✅ | ✅ | — | — | — | Diagnóstico + decisión solo si la nota documenta errores (sub-tipo con errores). |
| `procedure` (F80) | — | ✅ | — | — | ✅ | Recuerdo solo si la nota enumera comandos (sub-tipo recordatorio). |
| `configuration` (F81) | ✅ | — | — | ✅ | — | Aplicación si la nota incluye casos de tuning (sub-tuno). |
| `error-troubleshooting` (F82) | — | — | ✅ | ✅ | — | Mensaje literal del error preservado verbatim (INV-09). |
| `architecture` (F83) | ✅ | — | — | ✅ | — | Aplicación si la nota documenta trade-offs operativos. |
| `syntax` (F84) | ✅ | ✅ | — | — | — | Diagnóstico si la nota documenta errores de parseo (sub-tipo). |
| `data-model` (F85) | ✅ | ✅ | — | — | — | Decisión si la nota discute normalización / desnormalización. |
| `chapter-digest` (F86) | ✅ | — | — | ✅ | — | Aplicación + diagnóstico solo si la nota conserva ejemplos ejecutables. |
| `comparison` (F87) | — | ✅ | — | ✅ | — | Recuerdo si la tabla es 100 % factual (sin mecanismo). |
| `version-delta` (F88) | ✅ | — | — | — | ✅ | Diagnóstico si lista incompatibilidades. |
| `glossary-term` (F89) | ✅ | — | — | — | — | **Único tipo donde solo recuerdo aplica** — terminología pura. |
| `cheatsheet` (F90) | ✅ | ✅ | — | — | — | Solo recuerdo si la tabla es 100 % declarativa (sin casos). |
| `index-moc` (F91) | — | — | — | — | — | **Sección `## Autoevaluación` se omite por completo.** |
| `practice` (F92) | — | ✅ | ✅ | — | ✅ | Nota ejecutable; el lector verifica con el lab. |

**Reglas duras:**

- **R-T1** Una nota puede declarar `self-evaluation-types` con un superset del default (nunca subset). El validador V2 acepta nota con `✅` adicionales; rechaza nota con `—` donde la tabla marca `✅`.
- **R-T2** La tabla es **cerrada**: solo estos 5 tipos de pregunta son asignables. Si una nota requiere otro tipo (ej. "explica con tus palabras"), abrir nueva fase.
- **R-T3** El orden de las H3 dentro de `## Autoevaluación` sigue el orden de la tabla (recuerdo → aplicación → diagnóstico → decisión → predicción), saltando los no asignados.

---

## §4 · Regla de referencia pura

**Definición operativa de referencia pura:** una nota cuyo contenido es **índice, tabla cerrada, glosario, MOC, comparativa factual sin mecanismo, o lista de mensajes literales**. Para estas notas, los únicos tipos de pregunta asignados son **diagnóstico + decisión**. Nunca recuerdo (la respuesta de recuerdo en una referencia pura es la fila literal de la tabla, y eso viola el criterio #3 ROADMAP: _"ninguna pregunta se responde copiando una línea"_).

**Lista cerrada de tipos de nota que se consideran referencia pura por defecto:**

| `note-type` | Aplica referencia pura | Tipos asignados | Excepción |
|---|---|---|---|
| `glossary-term` | ✅ siempre | Solo recuerdo | El término + la definición breve **son** la unidad de recuerdo; no aplica la regla general. |
| `cheatsheet` | ✅ siempre | Solo recuerdo | Tabla de comandos; el diagnóstico y la decisión no tienen sentido sin contexto. |
| `index-moc` | ✅ siempre | (sin sección) | La MOC no contiene conocimiento propio. |
| `comparison` | ✅ si la tabla es 100 % factual | Solo recuerdo + decisión | Si la tabla tiene mecanismo (ej. "X usa Y porque Z"), se permiten aplicación + recuerdo. |
| `api-reference` | ✅ si no documenta errores | Solo recuerdo + aplicación | Si documenta errores, aplica el caso general (diagnóstico + decisión opcionales). |
| `configuration` | ✅ si es solo tabla de parámetros | Solo recuerdo | Si incluye casos de tuning, aplica aplicación + decisión. |

**Por qué no recuerdo en referencia pura:**

- El **recuerdo** exige "reformular la respuesta y enlazar al fundamento". En una tabla de parámetros, la "reformulación" es la fila literal (no hay nada que reformular). Eso es copia literal.
- El **diagnóstico** sí tiene sentido: "¿Si el parámetro X vale Y, ¿qué pasa?" — el lector razona sobre el efecto.
- La **decisión** sí tiene sentido: "¿Entre X=A y X=B, ¿cuál elegirías para Z?" — el lector compara trade-offs.

**Reglas algorítmicas S4-S5:**

- **S4** _Detección de referencia pura_ → la nota tiene `note-type` en la columna "Aplica referencia pura = siempre", O cumple simultáneamente: ≥ 80 % del cuerpo son tablas o listas GFM, ≤ 2 secciones con narrativa libre (≥ 3 párrafos consecutivos), sin bloques `:::example` o `:::console`.
- **S5** _Regla de sub-tipos_ → si la nota declara `subtype: <X>` (campo futuro, F47 §5.22), el validador aplica el sub-tipo de la columna "Excepción". F102 documenta los sub-tipos conocidos pero no los implementa en el frontmatter — esa materialización es F47 §10.

---

## §5 · Forma canónica de la pregunta y la respuesta

### §5.1 · Plantilla NoteMark (H2 + H3 + colapsables)

```notemark
## Autoevaluación

Tipos de pregunta asignados a este note-type: <lista>. Cada bloque
plegable contiene la pregunta, la respuesta reformulada y el enlace a
su fundamento. Intenta responder antes de desplegar.

### Recuerdo

:::collapsible{default_open=false}
¿Cuál es el propósito principal del **concepto X**?
Respuesta reformulada (no copia literal): <2-4 frases>.
> Fundamento: {src:blk_k901} o [[note:concept-x#§3]]
:::

:::collapsible{default_open=false}
¿Cuál es el valor por defecto de `--max-connections` en `postgres`?
<respuesta>.
> Fundamento: [[note:configuration-postgres#parametros-base]]
:::

### Aplicación

:::collapsible{default_open=false}
Dados 3 archivos críticos en `/etc`, ¿qué comando usarías para
respaldarlos antes de un cambio destructivo?
<respuesta con `{src:blk_xxxx}` si la nota documenta el patrón>.
> Fundamento: {src:blk_m201}
:::
```

### §5.2 · Reglas duras (R-T4 a R-T9)

| ID | Regla | Si se omite… |
|---|---|---|
| **R-T4** | La sección `## Autoevaluación` es **H2**, las preguntas se agrupan en **H3** por tipo (`### Recuerdo`, `### Aplicación`, `### Diagnóstico`, `### Decisión`, `### Predicción`). | El validador V1 falla. |
| **R-T5** | Cada bloque de pregunta es **`:::collapsible{default_open=false}`** (el lector debe intentar responder antes de mirar). | El validador V3 falla. |
| **R-T6** | Cada bloque plegable contiene **exactamente** tres partes en este orden: (1) pregunta, (2) respuesta reformulada, (3) línea final `> Fundamento: <ref>`. | El validador V3 falla. |
| **R-T7** | La línea de fundamento usa el formato `> Fundamento: {src:blk_xxxx}` o `> Fundamento: [[note:id#§N]]`. Sin esta línea, la pregunta falla (criterio #2 ROADMAP). | El validador V3 falla. |
| **R-T8** | La respuesta **nunca es copia literal** de una línea de la nota (criterio #3 ROADMAP). Regla algorítmica: Jaccard ≤ 0.8 entre respuesta y bloque referenciado, **sobre palabras no técnicas** (excluir la lista de 45 no-traducibles de F101 §3). | El validador V4 falla. |
| **R-T9** | **3-7 preguntas** por H3 de tipo asignado. Por debajo de 3, la nota no se considera autoevaluada; por encima de 7, ruido. | El validador V5 falla. |

### §5.3 · Ejemplo positivo completo (nota `concept` sobre PostgreSQL MVCC)

```notemark
## Autoevaluación

Tipos de pregunta asignados a `concept`: recuerdo, aplicación, decisión.

### Recuerdo

:::collapsible{default_open=false}
¿Qué garantiza el aislamiento **snapshot** en PostgreSQL MVCC?
Cada transacción observa un estado del database consistente con el momento de su inicio; las escrituras concurrentes no son visibles hasta el commit.
> Fundamento: {src:blk_k901}
:::

:::collapsible{default_open=false}
¿Cuál es el campo del header de heap tuple que marca la transacción creadora?
`xmin`.
> Fundamento: [[note:heap-tuple-layout#header]]
:::

### Aplicación

:::collapsible{default_open=false}
Dados dos transacciones T1 y T2 que arrancan antes de que T1 haga commit, ¿qué versión de la fila ve T2 al hacer SELECT?
La versión previa al commit de T1 (T2 sigue en su snapshot original); el commit posterior de T1 no es visible para T2.
> Fundamento: {src:blk_k902}
:::

### Decisión

:::collapsible{default_open=false}
Entre `READ COMMITTED` y `REPEATABLE READ`, ¿cuál elegirías para un reporte agregado que no puede mostrar lecturas no repetibles?
`REPEATABLE READ`: garantiza snapshot estable durante toda la transacción.
> Fundamento: [[note:isolation-levels#trade-offs]]
:::
```

---

## §6 · Algoritmo del validador `scripts/validate/self_eval_check.py`

**Ubicación:** `skill/notemartin-study-notes/scripts/validate/self_eval_check.py`.
**CLI:** `--note <path>` / `--notes <dir>` / `--json` / `--strict` / `--allow-violations V5`.
**Salida:** Markdown (default) o JSON (`--json`).
**Exit codes:** 0 = sin violaciones, 1 = violaciones, 2 = error de uso.

**Siete reglas V1-V7:**

### V1 · Existencia y sección

Para cada nota con `note-type` declarado en `properties.md`, existe una sección `## Autoevaluación` **si y solo si** su tipo NO está en la lista cerrada de "sin autoevaluación" (actualmente: solo `index-moc`).

### V2 · Tipos asignados coherentes con §3

Las H3 dentro de `## Autoevaluación` (`### Recuerdo`, `### Aplicación`, `### Diagnóstico`, `### Decisión`, `### Predicción`) son exactamente el **superset declarado** en el frontmatter `self-evaluation-types`, intersectado con la tabla §3. Reglas:

- Si la nota no declara `self-evaluation-types`, se usa la fila de §3 por defecto.
- Si la nota declara `self-evaluation-types` con tipos no presentes en §3 para ese note-type → falla con `unknown-question-type`.
- Si la nota omite una H3 que §3 marca como `✅` para el note-type → falla con `missing-question-type`.
- Si la nota añade una H3 que §3 marca como `—` para el note-type → falla con `forbidden-question-type` (la regla R-T1 de superset aplica solo si la nota declara explícitamente `self-evaluation-types` con tipos extra; sin declaración, vale §3 estricto).

### V3 · Forma de cada colapsable

Cada bloque `:::collapsible{default_open=false}` contiene exactamente:

1. **Pregunta** (≥ 1 línea, termina en `?` o es imperativo: "Enumera…", "Compara…").
2. **Respuesta** (≥ 1 línea de prosa, lista, código, diagrama; **nunca** una sola línea de copia).
3. **Línea de fundamento** que matchea la regex:
   ```
   ^>\s*Fundamento\s*:\s*(\{src:blk_[a-z0-9]{4,}\}|\[\[note:[a-z0-9][a-z0-9\-]*(?:#§[\w\-]+)?\]\])
   ```

Si falta cualquiera de las tres partes, la pregunta falla con `incomplete-block`.

### V4 · No copia literal (Jaccard sobre palabras no técnicas)

Algoritmo:

1. Cargar la nota actual.
2. Para cada bloque colapsable, extraer la **respuesta** (líneas entre la pregunta y el `> Fundamento: …`).
3. Resolver el **fundamento referenciado**:
   - Si es `{src:blk_xxxx}` y la nota actual tiene un anexo `## Trazabilidad` con esos bloques, extraer el bloque textual. Si no, intentar cargar `[[note:id]]` alternativo.
   - Si es `[[note:id#§N]]`, cargar la nota `id` desde el corpus y extraer la sección `§N`.
4. **Tokenizar** ambas cadenas (respuesta + bloque referenciado): split por whitespace, lowercase, quitar puntuación.
5. **Excluir palabras no técnicas**: cargar la lista de 45 no-traducibles de F101 §3 (categorías: identificadores snake_case/kebab-case/PascalCase, parámetros CLI, mensajes de error, comandos shell, sintaxis de funciones, versiones de protocolo, códigos HTTP).
6. Calcular **Jaccard** = `|A ∩ B| / |A ∪ B|` sobre los tokens restantes.
7. Si Jaccard > 0.8 → falla con `verbatim-copy`.

**Por qué 0.8 y no 0.6:** los términos técnicos (verbos, sustantivos) deben aparecer literales (INV-09, F98 L1-L8). Una reformulación honesta reordena y parafrasea, pero conserva el vocabulario técnico. Umbral 0.8 acepta reformulación honesta y rechaza copia.

### V5 · Densidad por H3 (3-7 preguntas)

Por cada H3 `### <tipo-de-pregunta>`, contar bloques `:::collapsible{default_open=false}` dentro. Si `< 3` → warning (no bloqueante por default; `--strict` lo convierte en error). Si `> 7` → error.

### V6 · Exención de `index-moc`

Notas con `note-type: index-moc` **no deben** tener sección `## Autoevaluación`. Si la tienen → falla con `unexpected-section-for-moc`.

### V7 · Wirings cerrados

Comprobaciones estáticas (modo `--check-wirings` o como parte del eval):

- `SKILL.md` §5.3 menciona `self-evaluation.md`.
- Los 15 archivos de `references/05-note-types/*.md` declaran la sub-sección `### Autoevaluación` con tabla de tipos asignados.
- `references/04-authoring/properties.md` §5 cita F102.
- `references/06-writing/anti-patterns.md` §2 lista AP13, AP14, AP15.
- `references/09-study/README.md` no marca `self-evaluation.md` como `[pendiente F102]`.

---

## §7 · Wirings y referencias cruzadas

| Fase | Archivo | Relación |
|---|---|---|
| F45 | `references/04-authoring/block-directives.md` §10.7 + §10.17 | Primitivas `:::collapsible` y `:::question` reutilizadas. |
| F46 | `references/04-authoring/inline-marks.md` | `{src:blk_xxxx}` y `[[note:id]]` para los fundamentos. |
| F47 | `references/04-authoring/properties.md` §5.21 | Propiedad opcional `self-evaluation-types`. |
| F51 | `references/04-authoring/depth-layers.md` | `## Autoevaluación` en L2; collapsibles en L3. |
| F76 | `references/07-visual/density.md` + `density_check.py` | R1-R8 ortogonales; R3 y R5 exentas en `## Autoevaluación`. |
| F78-F92 | `references/05-note-types/*.md` (15 archivos) | Cada uno declara `### Autoevaluación` con tabla copiada de §3. |
| F78 | `references/05-note-types/concept.md` §6 | Checklist extendido con `**F102-1**` y `**F102-2**`. |
| F98 | `references/06-writing/paraphrase.md` §2 L1-L8 | Literales verbatim; V4 los excluye del cómputo Jaccard. |
| F100 | `references/06-writing/anti-patterns.md` §2 | AP13, AP14, AP15. |
| F101 | `references/06-writing/i18n-and-citation.md` §3 | Lista de 45 no-traducibles; V4 la consume. |
| F103 | (futuro) `references/09-study/error-log.md` | Consumirá los colapsables para detectar errores del lector. |
| F104 | (futuro) `references/09-study/study-paths.md` | Caminos de repaso usarán las H3 de `## Autoevaluación`. |
| F112 | (futuro) suite consolidada | `self_eval_check.py` se invocará desde la suite. |
| F115 | (futuro) reporte de calidad | El reporte cita las violaciones de V1-V7. |

**Invocación desde SKILL.md:** la fila de `references/09-study/self-evaluation.md`
aparece en §5.3 con la entrada _"Antes de cerrar una nota que requiere
autoevaluación (cualquier `note-type` excepto `index-moc`)"_, entre la fila
de `completeness-audit.md` (F43) y el comentario final sobre `09-study/`.

---

## §8 · Verificación al cierre de la fase

Los **3 criterios del ROADMAP** se verifican algorítmicamente:

| Criterio | Cómo se verifica |
|---|---|
| **C1** Cada tipo de nota tiene tipos de pregunta asignados | `evals/self-evaluation-sample/run_eval.py` C3 detecta la tabla cerrada de 15 filas × 5 columnas en §3. Los 15 archivos de `05-note-types/*.md` declaran la sub-sección `### Autoevaluación` copiada de §3 (C8 wiring). El validador `self_eval_check.py --strict` aplica V2 a cada nota. |
| **C2** Toda respuesta enlaza a su fundamento | C4 detecta la plantilla NoteMark con `> Fundamento: …` en §5. El validador aplica V3 a cada colapsable. Las 4 notas positivas del eval (C6) tienen fundamento en cada bloque. |
| **C3** Ninguna pregunta se responde copiando una línea | C5 detecta la regla Jaccard ≤ 0.8 sobre palabras no técnicas en §6 V4. La nota negativa `self-eval-bad-2-copiada.md` falla V4 (C7). |

Criterios derivados cubiertos por el eval:

- **D1.** `wc -l self-evaluation.md` ≤ 600.
- **D2.** 8 secciones canónicas §1-§8 presentes.
- **D3.** §2 catálogo cerrado con 5 tipos, cada uno con verbo + forma + ejemplo + negativo (alias C2 + C5).
- **D4.** §3 tabla cerrada con 15 filas × 5 columnas (alias C3).
- **D5.** §5 plantilla NoteMark con `:::collapsible{default_open=false}` + `> Fundamento: …` (alias C4).
- **D6.** §6 V4 menciona Jaccard ≤ 0.8 y exclusión de la lista F101 §3 (alias C5).
- **D7.** Wirings cerrados (alias C8 + C9 + C11 + C12 + C13).
