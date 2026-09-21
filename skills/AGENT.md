# `agent.md` — Contexto de ejecución para `notemartin-study-notes`

> Contrato de trabajo entre el proyecto y cualquier agente que lo construya.
> Se lee completo al inicio de toda sesión. Su compañero es `roadmap.md`: este documento dice **cómo** trabajar, el roadmap dice **qué** construir.

---

## 0. Lo primero que tienes que entender

Estás construyendo una **skill**, no una aplicación. Si en algún momento el trabajo empieza a parecerse a un paquete Python con su CLI, sus modelos y su gestor de dependencias, te desviaste.

| | Aplicación | Skill |
|---|---|---|
| Quién razona | el código | el agente |
| Quién decide qué importa | heurísticas programadas | el agente, guiado por instrucciones |
| Qué hace el código | todo | solo lo determinista y lo caro |
| Qué se entrega | un repositorio que se ejecuta | un paquete que se carga en el contexto |
| Cómo se extiende | escribiendo funciones | escribiendo instrucciones verificables |

Una skill es: `SKILL.md` + `references/` + `schemas/` + `scripts/` + `assets/`. Los scripts son herramientas puntuales que el agente invoca; no son el producto. El producto son las instrucciones.

**El test rápido:** si estás a punto de escribir una función que decide si un párrafo es importante, para. Eso es una instrucción en `references/`, no código.

---

## 1. Cómo usar este documento

| Si vas a… | Lee |
|---|---|
| Empezar sesión | §0, §2, §3, §12 y las últimas entradas de `PROGRESS.md` |
| Implementar una fase | §9 (ciclo) + la fase en `roadmap.md` |
| Decidir si algo es script o instrucción | §3 — es la decisión más frecuente del proyecto |
| Escribir un `references/` | §7.2 |
| Escribir un script | §6, §7.3, §11 |
| Tocar `SKILL.md` | §4 — tiene reglas propias |
| Cerrar una fase | §10 y §19 |
| Dudar | §2 y §15. Si persiste, pregunta |

Si esto contradice al usuario, gana el usuario. Si contradice tu criterio, gana esto. Los invariantes de §2 solo los cambia una decisión explícita del usuario registrada como ADR nueva.

---

## 2. Invariantes

| ID | Invariante |
|---|---|
| **INV-01** | Esto es una skill. El razonamiento vive en `references/`; el código solo hace lo determinista (§3). |
| **INV-02** | `SKILL.md` se mantiene bajo 500 líneas y solo enruta. Nunca contiene plantillas completas ni reglas de detalle. |
| **INV-03** | Ninguna capa afirma un hecho que no exista en la capa inferior. |
| **INV-04** | Todo nodo fáctico del IR porta `source_refs` resolubles. Sin respaldo no es un hecho: o se marca derivado, o no entra. |
| **INV-05** | El agente escribe **NoteMark**, nunca Markdown de destino ni JSON de IR a mano. Los renderers traducen. |
| **INV-06** | NoteMark y el IR expresan intención semántica. Ni una mención de plataforma en `references/04-authoring/`. |
| **INV-07** | Una degradación de render cambia la forma, **nunca** elimina contenido. |
| **INV-08** | El 100 % de las unidades `must-keep` alcanza estado terminal antes de cerrar. La puerta de fidelidad no se salta en ningún modo. |
| **INV-09** | Los literales de la fuente —mensajes de error, nombres de parámetro, sintaxis, defaults, comandos— se conservan textualmente. |
| **INV-10** | Ninguna enumeración cerrada de la fuente se emite truncada. Prohibidos `etc.`, `entre otros`, `los más relevantes`. |
| **INV-11** | Las correcciones post-OCR proceden de reglas, diccionario o validación sintáctica forzosa. Nunca de plausibilidad. |
| **INV-12** | Todo artefacto intermedio se persiste en disco y es inspeccionable por un humano. |
| **INV-13** | Los procesos son idempotentes y reanudables. Reprocesar no duplica; publicar dos veces actualiza. |
| **INV-14** | Ningún archivo contiene un color literal. Los colores viven en `assets/tokens.json`. |
| **INV-15** | Los ejemplos de cualquier regla vienen de al menos dos dominios técnicos distintos. |
| **INV-16** | Ninguna regla entra en `references/` sin criterio verificable. Si no se puede comprobar, no es regla: es opinión, y va a `docs/`. |
| **INV-17** | Toda incertidumbre se declara. Versión indeterminable → `unknown`; nunca se infiere en silencio. |

---

## 3. Script o instrucción

La decisión más frecuente del proyecto. Tres preguntas; tres síes → script.

1. ¿Es **determinista**? Misma entrada, misma salida, siempre.
2. ¿Es **repetitivo**? Se ejecuta muchas veces por trabajo.
3. ¿El agente lo haría **mal, caro o de forma no reproducible**?

**Script:** rasterizar, OCR, geometría de layout, hashes e ids, validación de esquemas y sintaxis, render de Mermaid a imagen, generación de figuras, traducción IR → destino, publicación con límites de API, cálculo de cobertura, exportación de flashcards.

**Instrucción:** identificar unidades de información y su criticidad, decidir qué es redundante, elegir tipo de nota y división en archivos, redactar, elegir el diagrama que comunica mejor, detectar contradicciones, reconstruir un diagrama impreso, resolver terminología, verificar que un parafraseo no perdió nada.

**Dos anti-patrones simétricos:**
- *Programar juicio.* Si un script necesita decidir si algo es importante, el diseño está mal. Sácalo a `references/`.
- *Pedir aritmética al agente.* Si una instrucción le pide contar, hashear o parsear, sácalo a un script.

**Zona gris resuelta:** la corrección post-OCR es script (reglas y diccionario) **más** agente (validación sintáctica de código, solo cuando la corrección es forzosa). Nunca agente solo: ahí se inventa código que compila pero no es el del libro.

---

## 4. Reglas de `SKILL.md`

Es el archivo más delicado del proyecto porque es lo único que el agente lee siempre que la skill se dispara.

- **Límite duro: 500 líneas.** Cuando se acerque, se añade jerarquía en `references/`, no se comprime la prosa.
- **Solo enruta.** Contiene: invariantes, flujo de 5 capas, árbol de decisión de tipo de fuente, tabla de enrutado, catálogo de scripts con su invocación, modos de operación.
- **Nunca contiene:** plantillas de nota, reglas de redacción, catálogos de diagramas, tablas de degradación. Todo eso es N3.
- **Tabla de enrutado:** cada fila es `situación → archivo a leer → archivos a NO leer`. La segunda columna importa tanto como la primera: cargar de más agota el contexto en fuentes grandes.
- **Cobertura:** todo archivo de `references/` debe ser alcanzable desde la tabla. Un archivo inalcanzable no existe.
- **`description` insistente.** Los agentes tienden a no disparar skills que parecen opcionales. La descripción debe nombrar explícitamente documentación técnica, manuales de producto, libros técnicos, PDFs escaneados, API reference, apuntes, y los destinos Obsidian, Notion y AppFlowy.

---

## 5. Arquitectura

```
L0 Ingesta        scripts: archivo → regiones, texto, assets, confianza
L1 SDM            script construye, agente inspecciona: árbol con anclas estables
L2 Conocimiento   agente decide, script contabiliza: unidades, ledger, grafo, plan
L3 Autoría        agente redacta NoteMark; script parsea a IR y valida
L4 Render         scripts: siete destinos + reporte de degradaciones
```

Tres puertas bloqueantes: **fidelidad** (¿está todo?), **calidad** (¿enseña bien?), **render** (¿se ve bien en el destino?).

**Directorio de trabajo por fuente:**

```
.notes-work/<source_hash>/
├── ingest/       imágenes procesadas, OCR crudo, reporte de revisión
├── sdm.json
├── knowledge/    ledger.json, concept-graph.json, note-plan.json, glossary.json
├── notemark/     <note-id>.nm      ← lo que escribe el agente
├── ir/           <note-id>.json    ← lo que produce el parser
├── render/       salidas por destino
├── manifest.json
└── reports/
```

Una capa lee su artefacto de entrada y el perfil; nada más. Si necesitas algo de dos capas más abajo, el diseño está mal: sube el dato al artefacto intermedio.

---

## 6. Convenciones de los scripts

Los scripts son herramientas, no una aplicación. Eso impone restricciones concretas:

- **Independientes.** Cada uno se invoca solo, sin importar un paquete común pesado. Comparten utilidades mínimas en `scripts/util/`.
- **Entrada y salida por archivo**, rutas explícitas por argumento. Nada de estado global ni configuración implícita.
- **`--help` útil** y entrada obligatoria en `scripts/README.md` con: qué hace, entrada, salida, dependencias del sistema, qué pasa si falta la dependencia.
- **Dependencias mínimas y declaradas.** Un `requirements.txt` plano. Si un script necesita algo pesado, es opcional y su ausencia degrada, no rompe.
- **Salida en dos formatos:** legible por humano y estructurada para el agente.
- **Códigos de salida significativos:** 0 correcto, 1 error, 2 advertencias que requieren decisión.
- **Escritura atómica:** temporal + `rename`. Un fallo nunca deja un artefacto a medias.
- **Sin `print` suelto:** salida por canal correcto, errores a stderr.
- **Umbrales con nombre.** Prohibido un `0.85` suelto: constante nombrada con comentario que explique de dónde sale el número.

Lo que **no** hacemos: un paquete instalable, una CLI monolítica con subcomandos por capa, tipado estricto en todo, gestor de entornos sofisticado. Son señales de aplicación.

---

## 7. Convenciones de contenido

### 7.1 Idioma

- `references/`, `docs/`, roadmap, `PROGRESS.md`, ADRs, docstrings: **español**.
- Identificadores, nombres de archivo de código, claves de esquema, valores de enumeración, mensajes de log, commits: **inglés**.
- Las notas generadas: el idioma del perfil del usuario, con la política bilingüe de la Fase 101.

### 7.2 Archivos de `references/`

Los lee otro agente en tiempo de ejecución. Se escriben para ser **aplicados**.

- Estructura fija: **Propósito** (1–3 líneas) → **Cuándo se aplica** → **Reglas** → **Ejemplos** → **Anti-ejemplos** → **Cómo verificar**.
- Máximo 300 líneas; por encima, índice al inicio.
- Toda regla con criterio verificable y, cuando aplique, umbral numérico. "Que sea legible" no es regla; "máximo 6 líneas por callout" sí.
- Ejemplos de al menos dos dominios (INV-15).
- Cero duplicación: si la regla ya existe en otro archivo, se enlaza.
- Ni una mención de plataforma en `04-authoring/` (INV-06).
- Enlazado desde la tabla de enrutado de `SKILL.md`, siempre.

### 7.3 Nomenclatura

- `references/`: `kebab-case.md`, nombre por concepto (`coverage-ledger.md`), no por descripción.
- Carpetas de `references/` con prefijo numérico de dos dígitos para fijar el orden de lectura.
- Claves de esquema: `snake_case`. Valores de enumeración: `kebab-case`.
- Fases: `F001`…`F125`. Invariantes `INV-xx`. Decisiones `ADR-xxxx`.

### 7.4 Contratos

- Definidos en JSON Schema, versionados, con descripción por campo.
- Todo artefacto persistido lleva `schema_version`; el cargador rechaza versiones incompatibles con mensaje claro.
- Inmutables dentro de una versión mayor: añadir campo opcional es menor; cambiar tipo, semántica u obligatoriedad es mayor.
- Cambiar NoteMark, SDM o IR es siempre versión mayor.

### 7.5 Git

- Ramas: `phase/F048-notemark-parser`, `fix/notion-block-chunking`, `docs/adr-0010`.
- Commits en inglés con la fase entre corchetes:
  `feat(authoring): [F048] add NoteMark parser with round-trip test`
  `docs(refs): [F066] document portable mermaid subset`
- Un commit por unidad lógica. Ningún commit deja validadores en rojo.
- El PR incluye: fase cerrada, criterios con evidencia, salida de validadores, capturas si toca render.

---

## 8. Decisiones tomadas

Cerradas. No las reabras salvo que el usuario lo pida; si lo pide, ADR nueva que sustituya a la anterior.

**ADR-0001 — NoteMark como formato de autoría.**
*Decisión:* el agente redacta en Markdown canónico con directivas explícitas; un script lo parsea al IR.
*Motivo:* escribir un árbol JSON de 500 nodos a mano es caro, frágil y va contra lo que un modelo hace bien. NoteMark le deja escribir prosa mientras el contrato formal sigue existiendo. Esta es la decisión que mantiene el proyecto como skill y no como app.
*Coste aceptado:* un parser y una gramática que mantener.

**ADR-0002 — Representación intermedia semántica (IR).**
*Decisión:* el contenido se decide una vez; los renderers traducen a cada destino.
*Motivo:* con siete destinos, escribir Markdown de Obsidian y "adaptarlo" obliga a mantener siete motores de redacción con siete conjuntos de bugs.

**ADR-0003 — Coverage Ledger como fuente de verdad de la cobertura.**
*Motivo:* verificar cobertura leyendo la salida es circular. El ledger permite responder "¿dónde quedó la sección 4.3.2?" y bloquear la entrega de forma objetiva.

**ADR-0004 — El SDM es independiente del formato de origen.**
*Motivo:* las capas superiores no deben saber si el contenido vino de una capa de texto o de un escáner. Solo les importa el bloque, su ancla y su confianza.

**ADR-0005 — La matriz de capacidades se verifica empíricamente antes de escribir renderers.**
*Motivo:* las capacidades de Notion y AppFlowy cambian entre versiones y la documentación no siempre refleja el comportamiento real de la importación.

**ADR-0006 — División semántica, no por conteo de líneas.**
*Motivo:* el umbral de líneas del sistema anterior partía tablas de parámetros y procedimientos a la mitad. Una tabla de 60 filas es indivisible aunque ocupe 70 líneas.

**ADR-0007 — Español para documentación, inglés para código.**
*Motivo:* el usuario trabaja en español, pero mezclar idiomas dentro del código genera identificadores híbridos y rompe convenciones.

**ADR-0008 — Motores de OCR, layout, tablas y fórmulas intercambiables.**
*Decisión:* cada uno tras una interfaz de invocación estable.
*Motivo:* el ecosistema cambia rápido y el motor óptimo depende del documento.

**ADR-0009 — Sin borrado destructivo en destinos remotos.**
*Motivo:* el usuario puede haber comentado o enlazado esa página desde otro sitio.

---

## 9. Ciclo de trabajo por fase

No se salta ningún paso, ni en fases fáciles.

**1 · Preparar.** Lee la fase completa en `roadmap.md`. Verifica prerrequisitos en `PROGRESS.md`. Si falta uno, para y dilo.

**2 · Clasificar.** ¿La fase es `[ref]`, `[script]`, `[contrato]` o `[mixta]`? Aplica §3. Si te sale distinto de lo que dice el roadmap, discútelo antes de implementar.

**3 · Delimitar.** Enumera los entregables exactos. Si el alcance real resulta mayor, **propón dividir la fase** antes de empezar, no a mitad.

**4 · Diseñar.** Solo si hay decisión con consecuencias: ADR antes del código. Si es aplicación directa de lo ya decidido, no escribas ADR; sería ruido.

**5 · Implementar.** Contrato → implementación → entrada en el catálogo de scripts o en la tabla de enrutado de `SKILL.md`. En ese orden.

**6 · Enrutar.** Si creaste un `references/`, añádelo a la tabla de enrutado. Si creaste un script, añádelo a `scripts/README.md`. Un entregable no enrutado no existe.

**7 · Probar.** Tests de la lógica nueva y, si produce artefactos, un caso contra una fuente real del corpus. §11.

**8 · Validar.** Validadores en verde. Si la fase introduce algo que ningún validador cubre, **añade el validador ahí mismo**: una capacidad sin validador es una regresión futura garantizada.

**9 · Verificar criterios.** Uno por uno con evidencia concreta: salida de comando, archivo generado, captura. Si uno no se cumple, la fase no está cerrada. No existe "al 90 %".

**10 · Documentar y registrar.** `references/` afectados, `CHANGELOG.md`, `PROGRESS.md`.

**11 · Entregar.** Commit y PR según §7.5. Informa al usuario en dos o tres frases: qué se cerró, qué se decidió, qué sigue.

**Si te bloqueas:** no adivines. Registra el bloqueo, deja el repositorio consistente y pregunta. Un bloqueo declarado cuesta cinco minutos; una decisión inventada cuesta tres fases.

---

## 10. Definición de Hecho

**Entregable `[ref]`**
- [ ] Estructura de §7.2 completa
- [ ] Toda regla con criterio verificable
- [ ] Ejemplos de dos dominios distintos y anti-ejemplos incluidos
- [ ] Cero duplicación; enlaces donde corresponda
- [ ] Enrutado desde `SKILL.md`
- [ ] Bajo 300 líneas, o con índice
- [ ] Ninguna mención de plataforma si vive en `04-authoring/`

**Entregable `[script]`**
- [ ] Invocable de forma independiente, con `--help`
- [ ] Entrada en `scripts/README.md` con dependencias y comportamiento si faltan
- [ ] Salida legible y estructurada; códigos de salida correctos
- [ ] Escritura atómica; ningún artefacto a medias ante fallo
- [ ] Tests de lógica y caso contra fuente real del corpus
- [ ] Cero lógica de juicio semántico (§3)
- [ ] Umbrales nombrados y justificados

**Entregable `[contrato]`**
- [ ] JSON Schema con descripción por campo y `schema_version`
- [ ] Valida los artefactos reales del corpus
- [ ] Rechaza casos malformados de prueba
- [ ] Impacto de versión evaluado (mayor/menor)
- [ ] Documentado en su `references/` correspondiente

**Plantilla de tipo de nota**
- [ ] Expresada en NoteMark, no en Markdown de destino
- [ ] Secciones obligatorias y opcionales declaradas
- [ ] Checklist propio y nota mínima viable
- [ ] Probada contra fuente real y renderizada en los tres destinos ricos

**Renderer**
- [ ] Todos los nodos del IR cubiertos, sin "no soportado" silencioso
- [ ] Tabla de degradación completa y reportada
- [ ] Verificación visual con captura en tema claro y oscuro
- [ ] Idempotencia probada
- [ ] Límites de plataforma manejados con troceo, no con fallo

**Validador**
- [ ] Detecta el 100 % de una batería de defectos inyectados
- [ ] Cero falsos positivos sobre los ejemplos del repo
- [ ] Reporta archivo, nodo y regla violada
- [ ] Severidad correcta

---

## 11. Pruebas

**De scripts** — lógica pura: clasificación de regiones, ids deterministas, parseo de NoteMark, degradaciones, troceo de bloques. Rápidas, sin red.

**Golden files** — para SDM e IR, versionados en `tests/golden/`. Un diff inesperado es regresión hasta que se demuestre que es mejora, y entonces se actualiza en un commit propio que explique por qué.

**Round-trip** — NoteMark → IR → NoteMark produce el mismo árbol. Es la prueba que protege ADR-0001.

**Inyección de defectos** — cada validador con su batería de casos rotos. Es la única forma de saber que sirve.

**Fixtures** — recortes de 2–5 páginas que cubren: dos columnas, tabla que cruza página, código escaneado, fórmula, caja de advertencia editorial, numeración inconsistente.

**De la skill** — distinto de todo lo anterior: se ejecuta un prompt realista con la skill cargada y se evalúa el resultado con la rúbrica. Es lo único que mide si las instrucciones funcionan. Los tests de scripts pueden estar todos verdes y la skill seguir produciendo notas malas.

**Lo que no se prueba automáticamente:** calidad pedagógica y fidelidad visual. Para eso están la rúbrica y las capturas. No inventes un test que "mida" si una analogía es buena.

---

## 12. Estado entre sesiones

`PROGRESS.md` es el punto de sincronización:

```markdown
## F048 — Parser NoteMark → IR
- Estado: cerrada | en curso | bloqueada
- Tipo: [script]
- Entregables: scripts/authoring/parse_notemark.py, tests/golden/notemark/
- Criterios verificados: 4/4 — evidencia en tests/ y evals/runs/2026-xx/
- Decisiones: directiva `:::columns` pospuesta a F053 (ver ADR-0011)
- Aprendido: las tablas de parámetros necesitan directiva propia, no tabla genérica
- Pendiente: anidamiento de plegable dentro de columns
- Siguiente: F049
```

**Al arrancar:** `agent.md` completo + la sección "Camino mínimo" del roadmap + las últimas tres entradas de `PROGRESS.md`. No releas todo el roadmap; lee la fase que toca.

**Al cerrar:** repositorio consistente, `PROGRESS.md` actualizado, y un párrafo de traspaso con qué sigue.

```markdown
### Traspaso — <fecha>
- Última fase cerrada: Fxxx
- En curso: Fxxx (qué falta exactamente)
- Estado: validadores verde/rojo, tests verde/rojo
- Decisiones esta sesión: (o "ninguna")
- Bloqueos abiertos: (o "ninguno")
- Siguiente paso concreto: (una frase accionable, no "continuar")
```

---

## 13. Contratos: referencia rápida

**SDM — bloque**
```
id          sha1(source_hash + section_path + block_index)[:12]
type        prose|heading|list|table|code|console|formula|figure|caption|
            note|warning|example|syntax-diagram|footnote|toc|boilerplate
content     forma según el tipo
anchor      page, section_path, bbox, char_range
confidence  1.0 si es nativo; valor del OCR si viene de imagen
origin      native|ocr|reconstructed
```
Los ids son sensibles a la posición estructural, no a la numeración impresa, que puede ser inconsistente.

**NoteMark — forma**
```
---
propiedades YAML
---
Prosa normal en Markdown.

:::warning
Contenido de la advertencia. {src:blk_a91f}
:::

:::param-table
| nombre | tipo | default | rango | versión |
:::

Enlace a [[note:undo-tablespace]] y término [[term:undo-segment]].
Sustituye {{nombre_del_tablespace}} por el tuyo.
```

**IR — nodo**
```
node, attrs, children, source_refs, derived, external, layer, capability
```
`derived` o `external` en `true` → el renderer lo marca visiblemente. Un nodo `external` fuera de bloque identificable es error de fidelidad, no detalle de estilo.

**Ledger — entrada**
```
unit_id, source_block_ids, type, criticality (must-keep|context),
target_note, target_node, state (pending|written|merged|discarded),
discard_reason ∈ {redundant-with:<id>, boilerplate, navigation, out-of-scope-by-user}
```
Cualquier otro motivo de descarte significa que la unidad no debía descartarse.

---

## 14. Prohibiciones explícitas

Cosas que un agente competente hace por buenas razones y que aquí están prohibidas por razones mejores.

- **No conviertas esto en una aplicación.** Ni paquete instalable, ni CLI monolítica, ni framework. Scripts independientes e instrucciones (INV-01).
- **No metas reglas de detalle en `SKILL.md`.** Va a `references/` y se enruta (INV-02).
- **No programes juicio.** Si un script tiene que decidir qué es importante, es una instrucción (§3).
- **No escribas Markdown de destino ni JSON de IR a mano.** NoteMark y el parser (INV-05).
- **No construyas la skill completa de una vez.** El usuario ejecuta fase por fase; diez fases en un commit impiden revisar.
- **No rellenes un dato ausente** con conocimiento propio. La fuente no lo dice → la nota dice que no lo dice (INV-03, INV-17).
- **No resumas una tabla.** Nunca. Ni la de 60 filas (INV-10).
- **No "mejores" el código de la fuente.** Se transcribe tal cual, con sus comentarios y su indentación.
- **No corrijas OCR por plausibilidad** (INV-11).
- **No saltes la puerta de fidelidad** aunque haya prisa. Si la hay, se acuerda deuda explícita y queda registrada.
- **No inventes capacidades de plataforma.** Si la matriz dice ⚠, se verifica (ADR-0005).
- **No uses ejemplos de ML o visión por computador** en las referencias. El sistema anterior murió de eso (INV-15).
- **No metas un color literal** en ningún archivo (INV-14).
- **No amplíes el alcance de una fase en silencio.** Propón dividirla.
- **No borres y recrees** una página remota si puedes actualizarla (ADR-0009).

---

## 15. Casos límite conocidos

| Caso | Tratamiento |
|---|---|
| PDF híbrido (capítulos nativos, anexos escaneados) | Triaje por página, no por documento (F017) |
| Tabla que cruza páginas | Encabezado repetido detectado y unido antes de construir el bloque (F023) |
| Bloque de código escaneado | Confianza mínima más alta; validación sintáctica; marcado obligatorio si queda dudoso (F025, F026) |
| Numeración de secciones inconsistente | Anclas sintéticas estables; nunca depender de la numeración impresa (F032) |
| Fórmula no reconocida | Recorte de imagen marcado como pendiente. Jamás se aproxima (F024) |
| Documento sin versión declarada | `product-version: unknown`, nunca inferida en silencio (INV-17) |
| La fuente se contradice | Ambas versiones con sus anclas en bloque de conflicto. No elegir en silencio (F041) |
| Concepto ya definido antes | Se enlaza, no se redefine. El glosario acumulativo es la memoria (F040) |
| Enlace a nota inexistente | Deuda registrada; se resuelve en la segunda pasada de consolidación (F061, F109) |
| Nota de 500 bloques en Notion | Troceo por límites de API y anidamiento en pasadas sucesivas (F055) |
| Colisión de nombres entre productos | Sufijo de desambiguación más alias (F040) |
| Página remota editada a mano | Detección y confirmación antes de sobrescribir (F062) |
| La fuente cambia a mitad del trabajo | Cambio de hash → acción explícita registrada (F016) |
| `SKILL.md` se acerca a 500 líneas | Se añade jerarquía en `references/`, no se comprime la prosa (INV-02) |

---

## 16. Herramientas externas de ingesta

Antes de implementar la cadena de OCR completa (bloque 2), **comprueba qué existe ya en el entorno del usuario**: hay conversores propios de PDF a Markdown con extracción de imágenes y OCR local que pueden cubrir parte de L0. La Fase 124 define un contrato de entrada independiente de la herramienta —Markdown más mapa de secciones más carpeta de imágenes— precisamente para poder enchufarlos.

Si una herramienta existente satisface el contrato, úsala y dedica el esfuerzo a lo que ninguna cubre: verificación de ingesta, confianza por región y OCR de código. Si no lo satisface, impleméntalo respetando el mismo contrato para poder sustituirlo después.

En cualquier caso, la entrada externa pasa por la verificación de la Fase 30 igual que la interna. Que venga de una herramienta propia no la exime de comprobar que no faltan páginas.

---

## 17. Glosario

| Término | Significado aquí |
|---|---|
| **SDM** | Source Document Model. La fuente, independiente de su formato |
| **NoteMark** | Markdown canónico con directivas. Lo que el agente escribe |
| **IR** | Note IR. Árbol semántico producido por el parser, independiente del destino |
| **Unidad de información** | Afirmación mínima con valor independiente. Lo que el ledger rastrea |
| **`must-keep`** | Unidad que no puede omitirse ni fusionarse bajo ninguna circunstancia |
| **Ledger** | Registro fuente→nota que hace verificable la cobertura |
| **Ancla** | Referencia resoluble a una posición exacta de la fuente |
| **Degradación** | Representación alternativa cuando el destino no soporta algo. Nunca una omisión |
| **Capa de profundidad** | L1 TL;DR, L2 operativo, L3 referencia exhaustiva. L3 nunca se elimina |
| **Deuda de enlaces** | Enlaces a notas aún inexistentes, pendientes de la consolidación |
| **Nota sonda** | Nota de prueba que ejercita todas las capacidades, para verificar la matriz |
| **Puerta** | Control bloqueante: fidelidad, calidad, render |
| **Tabla de enrutado** | La tabla de `SKILL.md` que dice qué leer y qué no en cada situación |
| **N1 / N2 / N3** | Niveles de divulgación progresiva: metadatos / `SKILL.md` / referencias y scripts |

---

## 18. Checklist antes de cerrar una fase

- [ ] Todos los criterios de aceptación verificados con evidencia concreta
- [ ] Definición de Hecho de §10 cumplida para el tipo de entregable
- [ ] La clasificación script/instrucción es correcta (§3)
- [ ] El entregable está enrutado: tabla de `SKILL.md` o `scripts/README.md`
- [ ] Ningún invariante de §2 violado; si alguno estorbó, lo dijiste en vez de esquivarlo
- [ ] Ninguna prohibición de §14 infringida
- [ ] `SKILL.md` sigue bajo 500 líneas
- [ ] Validadores y tests en verde
- [ ] `CHANGELOG.md` y `PROGRESS.md` actualizados
- [ ] Commit y PR según §7.5
- [ ] Resumen al usuario: qué se cerró, qué se decidió, qué sigue

---

## 19. Lo que no debes perder de vista

Esta skill existe porque la anterior producía notas que **parecían** completas. Se veían bien, tenían callouts y diagramas, y faltaba el 30 % de la información. Nadie lo notaba hasta que necesitabas ese parámetro a las dos de la mañana y no estaba.

Cada mecanismo del proyecto —el ledger, las anclas, la auditoría de no-pérdida, la prohibición del `etc.`— existe contra ese fallo concreto. Cuando una fase te parezca burocrática, es probable que sea exactamente la que impide que vuelva a pasar.

Y hay un segundo fallo, más reciente, del que este documento también te protege: convertir la skill en una aplicación. Pasa gradualmente. Empieza con "voy a extraer esto a un módulo común", sigue con "mejor una CLI que orqueste", y termina con un sistema donde el agente ya no razona: solo ejecuta. Si en algún momento te descubres escribiendo una función que decide qué es importante, vuelve a §3.

Cuando tengas que elegir entre una nota elegante y una nota completa: completa.
Cuando tengas que elegir entre código que lo hace todo e instrucciones que enseñan a hacerlo: instrucciones.