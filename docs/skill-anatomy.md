# Anatomía y divulgación progresiva de `notemartin-study-notes`

> Documento normativo de la Fase 2 del roadmap. Define cómo se reparte el contenido entre los tres niveles de divulgación (N1/N2/N3), la regla 1:1 de enrutado, y el presupuesto de archivos cargables a la vez por etapa.
>
> Lectura complementaria, no duplicada: `skills/AGENT.md` §4 (reglas de `SKILL.md`) y §7.2 (convenciones de archivos de `references/`). Este documento **completa** la anatomía con la regla 1:1, el presupuesto numérico por etapa y el discriminador operativo N1/N2/N3.

---

## 1. Propósito y alcance

Este documento define:

- Qué contenido vive en cada uno de los tres niveles (N1, N2, N3).
- Cómo se decide el nivel de una instrucción nueva.
- Cómo se enruta toda instrucción de N3 desde N2 sin ambigüedad.
- Cuántos archivos de `references/` se cargan a la vez en cada etapa del pipeline.

No define:

- El contenido de cada `references/` individual (eso es cada fase que lo entrega).
- El contenido de `SKILL.md` (Fase 9).
- La división agente/script (Fase 3) ni la arquitectura de capas (Fase 4).
- El catálogo de scripts (Fase 117).

El destino del enrutado es siempre una futura fila de la tabla de enrutado de `SKILL.md`. Este documento entrega la **plantilla** y el **mapeo declarado**; la tabla instanciada se materializa en Fase 9.

---

## 2. Los tres niveles

### 2.1 N1 — Metadatos de disparo

- **Qué es:** frontmatter de `SKILL.md`. Solo `name` y `description`.
- **Presupuesto:** ~100 palabras. Ningún archivo físico más.
- **Va:** nombre canónico, descripción de disparo (qué hace la skill, sobre qué tipo de entrada, en qué destinos publica). Debe nombrar explícitamente documentación técnica, manuales de producto, libros técnicos, PDFs escaneados, API reference, apuntes, Obsidian, Notion, AppFlowy (ver `AGENT.md` §4 — regla `description` insistente).
- **No va:** reglas, ejemplos, plantillas, catálogos, árboles de decisión. Cualquier frase operativa en N1 se mueve a N2.

### 2.2 N2 — Cuerpo de `SKILL.md`

- **Qué es:** el archivo `SKILL.md` ya cargado cuando la skill se dispara.
- **Presupuesto:** <500 líneas (`INV-02`). Si se acerca, se añade jerarquía en `references/`, no se comprime la prosa.
- **Va:** invariantes que aplican a toda invocación, flujo resumido de las 5 capas, árbol de decisión de tipo de fuente, **tabla de enrutado** (sección 5 de este documento), catálogo mínimo de scripts con invocación, modos de operación, prohibición explícita de escribir Markdown de destino a mano.
- **No va:** plantillas de nota completas, reglas de redacción, gramática NoteMark, catálogos de diagramas, tablas de degradación, listas cerradas de motivos, nada que aplique solo a una operación concreta.

### 2.3 N3 — Referencias y scripts

- **Qué es:** archivos de `references/*.md` y archivos bajo `scripts/`.
- **Presupuesto:** sin límite. Los scripts no se leen, se ejecutan. Los `references/` se cargan bajo demanda.
- **Va:** toda regla que aplica a una operación concreta, plantillas de tipo de nota, gramáticas, catálogos, tablas de degradación por destino, instrucciones de redacción, instrucciones de validación.
- **No va:** nada que aplique a toda invocación sin alternativa. Si algo de N3 resulta ser universal, se promueve a N2 (y se documenta el movimiento).

### 2.4 N3 leíble vs N3 ejecutable

- **N3 leíble:** el agente lee el archivo. Cuenta para el presupuesto de la sección 7. Ejemplos: `references/04-authoring/notemark.md`, `scripts/README.md`.
- **N3 ejecutable:** el agente invoca el script por su comando; el código no se carga en contexto. **No cuenta** para el presupuesto. Ejemplos: `scripts/ingest/ocr.py`, `scripts/render/obsidian.py`.

---

## 3. Criterio de asignación N1 / N2 / N3

Tres preguntas en cascada, en este orden:

1. **¿Es metadato de disparo (frontmatter de `SKILL.md`)?** → **N1**.
2. **¿La instrucción es necesaria en TODAS las invocaciones de la skill y su omisión produciría un fallo silencioso?** → **N2**.
3. **En cualquier otro caso** → **N3**.

**Definición operativa de "fallo silencioso":** omitir la regla produce un artefacto incorrecto que **ningún validador del proyecto detecta** automáticamente (Fase 113). Si un validador lo detecta —aunque sea con severidad de advertencia—, la regla puede vivir en N3.

**Definición operativa de "todas las invocaciones":** aplica cuando la skill se dispara, sin condicionar por modo (nota rápida / capítulo / obra / actualización / re-render), tipo de fuente (PDF nativo / escaneado / EPUB / DOCX / PPTX / HTML / transcripción), tipo de nota, o destino.

**No existe "casi siempre".** Una regla que aplica en 9 de cada 10 invocaciones pero no en la décima es N3, con su modo o tipo de fuente declarado como condición de carga.

---

## 4. Regla de enrutado 1:1 N3 → N2

Toda instrucción de N3 tiene **exactamente un punto de entrada** desde N2.

- **N3 huérfano:** un archivo de `references/` que ningún disparador de N2 cita. Equivale a un archivo muerto. Se corrige añadiendo una fila a la tabla de enrutado de `SKILL.md` que lo referencie; si ningún caso lo necesita, se elimina el archivo.
- **N3 duplicado:** un archivo de `references/` citado por dos situaciones distintas en N2. Se corrige fusionando las dos filas de la tabla en una sola, o moviendo el contenido a un único archivo (la duplicación de N3 es señal de que dos situaciones en realidad son una).
- **N2 que parece N3:** una regla en `SKILL.md` que solo aplica a una operación concreta. Se corrige moviendo la regla a `references/` y dejando en N2 solo la fila de la tabla de enrutado que la cita.

---

## 5. Plantilla de tabla de enrutado

La tabla de enrutado de `SKILL.md` (Fase 9) tiene cuatro columnas, en este orden:

| Situación (modo / etapa / tipo de fuente / tipo de nota) | Archivo a leer | Archivos a NO leer | Fase del roadmap |
|---|---|---|---|

Restricciones obligatorias de la plantilla:

- Una fila por unidad discreta de decisión del agente. No se mezclan dos situaciones en una fila aunque compartan archivo.
- La columna **"Archivos a NO leer"** es obligatoria y no puede estar vacía. Cargar de más agota el contexto en fuentes grandes. Si una situación no tiene archivos a evitar, se escribe explícitamente "ninguno" y se justifica en una nota al pie.
- La columna **"Fase del roadmap"** usa el identificador `Fxxx` literal del `ROADMAP.md`. Si una fila se instancia antes de que la fase correspondiente haya creado el archivo físico, se marca `[pendiente Fxxx]`.
- La regla 1:1 (sección 4) se verifica sobre esta tabla: cada fila N3 aparece una y solo una vez.

---

## 6. Mapeo declarado N3-planificado → entrada N2-declarada

Lista de archivos `references/` planificados en el roadmap, con la futura fila de la tabla de enrutado. Materialización: Fase 9.

| Ruta futura | Situación de disparo | Fase |
|---|---|---|
| `references/00-pipeline/responsibilities.md` | Antes de implementar, decidir si algo es script o instrucción | F3 |
| `references/00-pipeline/architecture.md` | Inicio de capítulo u obra completa, para entender qué artefacto produce cada capa | F4 |
| `references/00-pipeline/manifest.md` | Interrupción o reanudación de un trabajo | F16 |
| `references/01-ingest/triage.md` | Antes de la primera ingesta de un documento | F17 |
| `references/01-ingest/ocr-engines.md` | Selección de motor OCR para un documento | F20 |
| `references/01-ingest/code-ocr.md` | OCR sobre región clasificada como código | F25 |
| `references/01-ingest/confidence.md` | Umbrales por tipo de región para revisión humana | F26 |
| `references/02-source-model/spec.md` | Cualquier consulta al SDM o a sus anclas | F13 |
| `references/02-source-model/anchors.md` | Documento sin numeración o con numeración inconsistente | F32 |
| `references/02-source-model/provenance.md` | Extracción de metadatos editoriales de la fuente | F34 |
| `references/02-source-model/editorial-semantics.md` | Clasificación de regiones editoriales (Nota, Precaución, Ejemplo) | F35 |
| `references/03-knowledge/information-units.md` | Extracción de unidades de información en L2 | F37 |
| `references/03-knowledge/ledger.md` | Cualquier operación sobre el Coverage Ledger | F15 |
| `references/03-knowledge/concept-graph.md` | Construcción del grafo de prerrequisitos | F39 |
| `references/03-knowledge/terminology.md` | Resolución de términos canónicos y colisiones | F40 |
| `references/03-knowledge/conflicts.md` | Detección de contradicciones u obsolescencia | F41 |
| `references/03-knowledge/note-plan.md` | División del trabajo en notas (Note Plan) | F44 |
| `references/04-authoring/notemark.md` | Redacción de cualquier nota en NoteMark | F12 |
| `references/04-authoring/ir-spec.md` | Validación del IR o consulta del catálogo de nodos | F14 |
| `references/04-authoring/block-directives.md` | Elección de directiva de bloque NoteMark | F45 |
| `references/04-authoring/inline-marks.md` | Inserción de marcas inline en redacción | F46 |
| `references/04-authoring/properties.md` | Definición de propiedades YAML de una nota | F47 |
| `references/04-authoring/depth-layers.md` | Definir capas L1, L2, L3 de una nota | F51 |
| `references/05-note-types/concept.md` | Seleccionar el tipo de nota `concept` | F78 |
| `references/05-note-types/api-reference.md` | Seleccionar el tipo de nota `api-reference` | F79 |
| `references/05-note-types/procedure.md` | Seleccionar el tipo de nota `procedure` | F80 |
| `references/05-note-types/configuration.md` | Seleccionar el tipo de nota `configuration` | F81 |
| `references/05-note-types/error-troubleshooting.md` | Seleccionar el tipo de nota `error-troubleshooting` | F82 |
| `references/05-note-types/architecture.md` | Seleccionar el tipo de nota `architecture` | F83 |
| `references/05-note-types/syntax.md` | Seleccionar el tipo de nota `syntax` | F84 |
| `references/05-note-types/data-model.md` | Seleccionar el tipo de nota `data-model` | F85 |
| `references/05-note-types/chapter-digest.md` | Seleccionar el tipo de nota `chapter-digest` | F86 |
| `references/05-note-types/comparison.md` | Seleccionar el tipo de nota `comparison` | F87 |
| `references/05-note-types/version-delta.md` | Seleccionar el tipo de nota `version-delta` | F88 |
| `references/05-note-types/glossary-term.md` | Seleccionar el tipo de nota `glossary-term` | F89 |
| `references/05-note-types/cheatsheet.md` | Seleccionar el tipo de nota `cheatsheet` | F90 |
| `references/05-note-types/index-moc.md` | Seleccionar el tipo de nota `index-moc` | F91 |
| `references/05-note-types/practice.md` | Seleccionar el tipo de nota `practice` o lab | F92 |
| `references/07-visual/diagram-catalog.md` | Elegir el tipo de diagrama para una intención | F65 |
| `references/07-visual/mermaid-portable.md` | Escribir un bloque Mermaid portable | F66 |
| `references/07-visual/monospace-diagrams.md` | Decidir entre diagrama monoespaciado, Mermaid o imagen | F69 |
| `references/07-visual/reconstruction.md` | Decidir si reconstruir un diagrama impreso o conservar la captura | F71 |
| `references/07-visual/accessibility.md` | Verificación de accesibilidad visual | F71 |
| `references/07-visual/tokens.md` | Uso de tokens visuales (color, tipografía, espaciado) | F72 |
| `references/07-visual/style-mapping.md` | Mapear intención semántica a estilo por destino | F73 |
| `references/07-visual/note-templates.md` | Definir cabecera visual por tipo de nota | F75 |
| `references/07-visual/density.md` | Revisar densidad visual de una nota | F76 |
| `references/08-render/capability-matrix.md` | Verificar capacidad de un destino antes de renderizar | F8 |
| `references/08-render/contract.md` | Cualquier operación de renderizado | F53 |
| `references/08-render/linking.md` | Resolver enlaces entre notas según destino | F61 |
| `references/08-render/publishing.md` | Publicación idempotente en destinos remotos | F62 |
| `references/08-render/migration.md` | Re-render o migración entre destinos | F64 |
| `references/10-quality/fidelity-rules.md` | Cualquier redacción de contenido fáctico | F42 |
| `references/10-quality/completeness-audit.md` | Auditoría de no-pérdida antes de cerrar | F43 |

Total declarado: 54 archivos `references/` (38 rutas únicas más 15 tipos de nota de la Fase 78–92). Cada uno aparece exactamente una vez. Cobertura del roadmap: 100 % de las rutas `@/references/` listadas en las fases del bloque 0–11.

---

## 7. Presupuesto por etapa (nº de archivos)

### 7.1 Tabla A — Presupuesto por capa del pipeline

| Capa | Etapas del agente dentro de la capa | Nº máx. de archivos de `references/` cargados a la vez | Scripts ejecutables permitidos (no cuentan) |
|---|---|---|---|
| L0 Ingesta | Triaje, OCR, layout, regiones | 2 | ilimitados |
| L1 SDM | Inspección, anclas, procedencia, semántica editorial | 2 | 0–1 |
| L2 Conocimiento | Unidades, ledger, grafo, plan, terminología, conflictos | 3 | 0–1 |
| L3 Autoría | Redacción en NoteMark, marcas inline, propiedades, capas | 4 | 0 |
| L4 Render | Validación de capacidad, contrato, degradación, publicación | 2 | ilimitados |

Reglas de la tabla:

- "Nº máx." es un entero cerrado. No hay rangos. Cualquier excepción reabre la tabla.
- "Scripts ejecutables permitidos" enumera los scripts que la etapa puede invocar; **no cuentan** en el presupuesto porque se ejecutan sin cargarse en contexto.
- "0–1" significa cero o uno, no dos ni más. Si la etapa necesita dos scripts, se reabre la tabla.

### 7.2 Tabla B — Presupuesto por modo de operación

| Modo | Capas que toca | Suma máxima de archivos de `references/` en cualquier instante |
|---|---|---|
| Nota rápida | L1, L2, L3, L4 | 4 |
| Capítulo | L0, L1, L2, L3, L4 | 6 |
| Obra completa | L0, L1, L2, L3, L4 | 6 |
| Actualización incremental | L1, L2, L3, L4 | 4 |
| Re-render a otro destino | L4 | 2 |

La suma máxima de la tabla B es siempre menor o igual a la suma de los máximos de la tabla A de las capas que el modo toca. Si en una ejecución concreta se supera, el modo se reabre.

---

## 8. Diez casos de prueba del criterio N1/N2/N3

Cada caso sigue el mismo formato: (a) regla candidata con fase del roadmap, (b) pregunta del criterio §3, (c) nivel asignado, (d) motivo.

### Caso 1 — N1

- **Regla:** la descripción de disparo de `SKILL.md` debe nombrar documentación técnica, manuales de producto, libros técnicos, PDFs escaneados, API reference, apuntes, Obsidian, Notion y AppFlowy.
- **Origen:** `AGENT.md` §4 + roadmap F10.
- **Pregunta §3:** ¿Es metadato de disparo (frontmatter de `SKILL.md`)?
- **Nivel:** N1.
- **Motivo:** vive en el frontmatter `description`. Cualquier intento de moverla a `SKILL.md` cuerpo o a `references/` la convierte en algo que el sistema carga o no carga condicionalmente; debe estar siempre visible para el disparador.

### Caso 2 — N2

- **Regla:** árbol de decisión de tipo de fuente (PDF nativo / PDF escaneado / EPUB / DOCX / PPTX / HTML / transcripción / repositorio) que elige la cadena de ingesta L0.
- **Origen:** roadmap F9 (cuerpo de `SKILL.md`).
- **Pregunta §3:** ¿Necesaria en TODAS las invocaciones y su omisión produce fallo silencioso?
- **Nivel:** N2.
- **Motivo:** toda invocación con un documento nuevo debe elegir la cadena de ingesta antes de empezar. Si elige mal, se invoca el OCR sobre un PDF nativo (caro, lento) o el extractor nativo sobre un escaneado (silencioso: produce texto vacío o fragmentado). El validador de la Fase 30 detecta la anomalía tarde, no al inicio.

### Caso 3 — N2

- **Regla:** "Cargar el SDM antes de redactar cualquier nota."
- **Origen:** roadmap F9 + F12 + F44 (Note Plan precede a la redacción).
- **Pregunta §3:** ¿Necesaria en TODAS las invocaciones y su omisión produce fallo silencioso?
- **Nivel:** N2.
- **Motivo:** redactar sin SDM significa redactar sin anclas; el parser genera IR sin `source_refs` y el validador lo detecta, pero solo tras escribir la nota entera. El error es silencioso durante la redacción y caro de revertir.

### Caso 4 — N2

- **Regla:** "`SKILL.md` se mantiene bajo 500 líneas" (`INV-02`).
- **Origen:** `AGENT.md` §2.
- **Pregunta §3:** ¿Necesaria en TODAS las invocaciones y su omisión produce fallo silencioso?
- **Nivel:** N2.
- **Motivo:** aplicar la regla aplica a cada commit que toca `SKILL.md`. Si se omite, el archivo crece, satura el contexto de toda invocación futura, y ningún validador mide el coste de contexto directamente. Es un fallo silencioso acumulativo.

### Caso 5 — N2

- **Regla:** "El agente escribe NoteMark, nunca Markdown de destino ni JSON del IR a mano" (`INV-05`).
- **Origen:** `AGENT.md` §2 + roadmap F9.
- **Pregunta §3:** ¿Necesaria en TODAS las invocaciones y su omisión produce fallo silencioso?
- **Nivel:** N2.
- **Motivo:** el agente puede generar Markdown de Obsidian directamente y "funcionar" en ese destino. El fallo es silencioso porque los otros destinos quedan rotos sin que el validador detecte nada específico: simplemente no hay IR, así que no hay a qué aplicar el validador cross-target.

### Caso 6 — N3

- **Regla:** gramática NoteMark completa con directivas de bloque y marcas inline.
- **Origen:** roadmap F12 (`references/04-authoring/notemark.md`).
- **Pregunta §3:** ¿Necesaria en TODAS las invocaciones y su omisión produce fallo silencioso?
- **Nivel:** N3.
- **Motivo:** aplica solo en L3 (redacción). El parser de la Fase 48 rechaza sintaxis inválida con mensaje que incluye archivo, línea y directiva; el fallo **no es silencioso**, es inmediato y accionable.

### Caso 7 — N3

- **Regla:** literales de la fuente —mensajes de error, nombres de parámetro, sintaxis, defaults, comandos— se conservan textualmente (`INV-09` + roadmap F98).
- **Origen:** `AGENT.md` §2 + roadmap F42 + F98.
- **Pregunta §3:** ¿Necesaria en TODAS las invocaciones y su omisión produce fallo silencioso?
- **Nivel:** N3.
- **Motivo:** aplica a la redacción de contenido fáctico, no a todas las operaciones. El validador de la Fase 113 detecta reescritura de literales comparando contra el SDM. El fallo no es silencioso.

### Caso 8 — N3

- **Regla:** lista cerrada de motivos de descarte del Coverage Ledger (`redundant-with:<unit_id>`, `boilerplate`, `navigation`, `out-of-scope-by-user`).
- **Origen:** roadmap F15 + F38.
- **Pregunta §3:** ¿Necesaria en TODAS las invocaciones y su omisión produce fallo silencioso?
- **Nivel:** N3.
- **Motivo:** aplica solo en L2 cuando se descarta una unidad. El script del ledger rechaza cualquier motivo fuera de la lista cerrada con error explícito; el fallo no es silencioso.

### Caso 9 — N3

- **Regla:** plantilla del tipo de nota `procedure` con sus secciones obligatorias y opcionales.
- **Origen:** roadmap F80.
- **Pregunta §3:** ¿Necesaria en TODAS las invocaciones y su omisión produce fallo silencioso?
- **Nivel:** N3.
- **Motivo:** aplica solo cuando el agente ha decidido que la nota es de tipo `procedure`. El checklist por tipo (Fase 112) verifica estructura; el fallo no es silencioso.

### Caso 10 — N3

- **Regla:** catálogo de scripts (`scripts/README.md`) con qué hace cada script, entrada, salida, dependencias, invocación y comportamiento si falta la dependencia.
- **Origen:** roadmap F117 + `AGENT.md` §6.
- **Pregunta §3:** ¿Necesaria en TODAS las invocaciones y su omisión produce fallo silencioso?
- **Nivel:** N3.
- **Motivo:** aplica solo cuando el agente necesita invocar un script. Un agente que no tiene que invocar ningún script en una sesión no necesita el catálogo cargado. El validador detecta invocaciones mal formadas por el código de salida del script.

**Resumen:** 1 caso N1, 4 casos N2, 5 casos N3. Distribución coherente con el volumen esperado de cada nivel.

---

## 9. Anti-patrones

Seis errores de enrutado previsibles, cada uno con ejemplo malo y corregido.

### 9.1 Regla de detalle metida en N2

- **Malo:** "`SKILL.md` contiene la tabla completa de degradación por destino (matriz 7×14)."
- **Corregido:** "`SKILL.md` cita la regla 'aplicar tabla de degradación' y enruta a `references/08-render/contract.md`, donde vive la tabla."

### 9.2 Regla crítica de disparo metida en N3

- **Malo:** la lista de tipos de fuente (PDF nativo, escaneado, EPUB…) vive en `references/01-ingest/triage.md`.
- **Corregido:** el árbol de decisión resumido vive en `SKILL.md` (N2); la versión detallada y los umbrales numéricos van a `references/01-ingest/triage.md` (N3).

### 9.3 Dos N3 que deberían ser uno

- **Malo:** `references/04-authoring/notemark-grammar.md` y `references/04-authoring/notemark-block-directives.md`, ambos citados desde la misma fila de enrutado.
- **Corregido:** fusionar en un único `references/04-authoring/notemark.md` con secciones internas; la fila de enrutado queda única.

### 9.4 N3 huérfano sin entrada

- **Malo:** `references/02-source-model/typography.md` existe pero la tabla de enrutado de `SKILL.md` no lo cita.
- **Corregido:** añadir fila en la tabla; si la fase que debería haberlo creado ya cerró sin entrada, el archivo se elimina.

### 9.5 N2 sin respaldo en N3

- **Malo:** `SKILL.md` dice "consultar la rúbrica de evaluación" pero no existe `references/10-quality/rubric.md`.
- **Corregido:** el N2 cita solo referencias que existen o están marcadas `[pendiente Fxxx]`; cuando la fase crea el archivo, se elimina la marca.

### 9.6 "Archivos a NO leer" vacío

- **Malo:** fila de enrutado sin columna "Archivos a NO leer" o con la palabra "ninguno" sin justificación.
- **Corregido:** la columna lista explícitamente los archivos que el agente **no** debe cargar en esa situación (por ejemplo: "no cargar `references/05-note-types/` hasta saber el tipo de nota").

---

## 10. Validación al cerrar

Lista de comprobaciones grepeables que un revisor externo debe poder ejecutar sobre `docs/skill-anatomy.md` y `ROADMAP.md`:

1. `test -f docs/skill-anatomy.md` → existe.
2. `rg -c '^## ' docs/skill-anatomy.md` → al menos 10 secciones.
3. `rg -c 'N[123]\b' docs/skill-anatomy.md` → aparecen los tres niveles con texto, no solo menciones.
4. `rg -c 'F[0-9]+' docs/skill-anatomy.md` → al menos 30 apariciones (declaraciones en §6 y §8).
5. `rg 'Tabla A —' docs/skill-anatomy.md && rg 'Tabla B —' docs/skill-anatomy.md` → ambas tablas existen.
6. `rg -c '\| *[0-9]+ *\|' docs/skill-anatomy.md` → la sección de presupuesto contiene enteros en las celdas numéricas.
7. `rg 'TBD|≈|depende' docs/skill-anatomy.md` → no devuelve resultados en las secciones de presupuesto (si los hay en otras secciones, se justifican).
8. `rg '^- \[ \]' ROADMAP.md` → no devuelve las tres casillas de Fase 2.
9. Test manual: leer los 10 casos de §8 en orden y asignar nivel sin mirar la respuesta del documento. Coincidencia mínima: 9 de 10.

Si cualquiera falla, la fase no se marca como completa.

---

## 11. Cambios permitidos sin reabrir Fase 2

- Añadir filas a la tabla de §6 cuando fases futuras creen nuevos archivos `references/`.
- Añadir entradas a §9 cuando se descubran nuevos anti-patrones.
- Ajustar la suma máxima de §7.2 si una fase posterior obliga a revisarla, siempre con un ADR que documente el motivo.

Cambios que **sí** reabren Fase 2:

- Mover una regla existente de N2 a N3 o viceversa (cambia el discriminador).
- Cambiar el discriminador "fallo silencioso" de §3.
- Reducir el número de casos de prueba de §8 por debajo de 10.
