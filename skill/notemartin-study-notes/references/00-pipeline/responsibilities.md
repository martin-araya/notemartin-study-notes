# División agente/script — `references/00-pipeline/responsibilities.md`

> Documento normativo de la Fase 3 del roadmap. Cierra la división entre lo que hace un script y lo que hace el agente, audita los 35 scripts y las 54 instrucciones planificadas, y aporta 15 casos de prueba.
>
> Documentos complementarios: `skills/AGENT.md` §3 (test de tres preguntas y anti-patrones — versión corta), `ROADMAP.md` §2 (tabla semilla — versión resumida). Este doc los **referencia y completa**, no los repite.
>
> Enrutado desde N2: `docs/skill-anatomy.md` §6 fila `F3`.

## Índice

1. [Propósito](#1-propósito) · 2. [Cuándo se aplica](#2-cuándo-se-aplica) · 3. [Reglas](#3-reglas) · 4. [Quince casos de prueba](#4-quince-casos-de-prueba) · 5. [Apéndice A — Auditoría de scripts](#5-apéndice-a--auditoría-de-scripts) · 6. [Apéndice B — Auditoría de instrucciones](#6-apéndice-b--auditoría-de-instrucciones) · 7. [Cómo verificar](#7-cómo-verificar-el-test-sobre-una-tarea-nueva) · 8. [Cambios permitidos](#8-cambios-permitidos-sin-reabrir-fase-3)

## 1. Propósito

Cerrar la división entre lo que hace un script y lo que hace el agente, de forma que ninguna fase posterior del roadmap tenga que reinventar el test. Una tarea nueva cae en uno de tres lugares: **script**, **instrucción** o **zona gris resuelta**.

**No es** el catálogo de scripts (`scripts/README.md`, Fase 117) ni la arquitectura de capas (Fase 4). El catálogo describe archivos; este doc describe el test.

## 2. Cuándo se aplica

- Antes de implementar un script nuevo: las tres preguntas de §3.1 deben dar "sí".
- Antes de escribir una instrucción nueva: las tres preguntas deben dar "no".
- Cuando un revisor dude del lugar de una tarea ya existente en una fase del roadmap.
- En la revisión de PR si el cambio toca la frontera agente/script.

## 3. Reglas

### 3.1 Test de tres preguntas

| # | Pregunta | Definición operativa |
|---|---|---|
| 1 | ¿**Determinista**? | Misma entrada, misma salida, siempre, sin importar el contexto. |
| 2 | ¿**Repetitivo**? | Se ejecuta más de una vez por trabajo o más de un trabajo por sesión. |
| 3 | ¿El agente lo haría **mal, caro o no reproducible**? | Salida no determinista del LLM, lenta por consumo de tokens, o no reproducible bit a bit entre ejecuciones. |

**Veredicto:**
- Tres síes → **script**.
- Tres noes → **instrucción**.
- Mezcla → **zona gris**, ir a §3.4.

### 3.2 Tabla normativa "Lo hace un script"

Cada fila: tarea, motivo, umbral o condición, ruta del script, `references/` complementario.

| Tarea | Por qué no el agente | Umbral / condición | Script | `references/` complementario |
|---|---|---|---|---|
| Rasterizar PDF a imagen | Procesamiento de imagen | DPI configurable (default 300) | `scripts/ingest/preprocess.py` | `references/01-ingest/` |
| OCR con posición y confianza | Requiere motor especializado | Confianza por palabra ≥ umbral del motor | `scripts/ingest/ocr.py` | `references/01-ingest/ocr-engines.md` |
| Detectar columnas y orden de lectura | Geometría sobre coordenadas | Densidad y gap entre cajas | `scripts/ingest/layout.py` | — |
| Clasificar regiones (texto/tabla/figura/código) | Señales estructurales (fuente, fondo, bordes) | Regiones ambiguas se marcan, nunca se fuerzan | `scripts/ingest/regions.py` | `references/02-source-model/editorial-semantics.md` |
| OCR de tablas con celdas combinadas | Estructura con/sin bordes | Verificación de filas/columnas; baja confianza marcada | `scripts/ingest/tables.py` | — |
| OCR de fórmulas a LaTeX | Verificación de compilación | Fórmula no reconocida → imagen marcada, nunca aproximada | `scripts/ingest/formulas.py` | — |
| Corrección post-OCR (guionado, ligaduras) | Reglas y diccionario auditable | Nunca toca código ni tablas; cada corrección revertible | `scripts/ingest/post_ocr.py` | `references/01-ingest/` |
| Validar sintaxis Mermaid | Parseo determinista | Reporta archivo, nodo y regla violada | `scripts/validate/mermaid.py` | `references/07-visual/mermaid-portable.md` |
| Renderizar Mermaid a SVG/PNG | Necesita el motor de render | Tema claro/oscuro; caché por hash | `scripts/render/diagram_image.py` | `references/07-visual/mermaid-portable.md` |
| Generar figuras de datos | Matplotlib con tokens; reproducible | Paleta daltonismo-segura; `source_refs` por serie | `scripts/render/make_figure.py` | `references/07-visual/tokens.md` |
| Hashear fuente, generar ids deterministas | Debe ser reproducible bit a bit | `sha1(source_hash + section_path + block_index)[:12]` | `scripts/util/sdm_cache.py`, `build_sdm.py` | `references/02-source-model/spec.md` |
| Calcular cobertura del ledger | Aritmética sobre estructura | 100 % `must-keep` requerido | `scripts/util/ledger.py` | `references/03-knowledge/ledger.md` |
| Validar SDM, IR, NoteMark contra esquema | Verificación exhaustiva y barata | Severidades error / advertencia / info | `scripts/validate/validate_ir.py`, `ingest_check.py` | `references/02-source-model/spec.md`, `references/04-authoring/ir-spec.md` |
| Transformar IR (`split`, `merge`, `dedup`) | Operación mecánica sobre nodos | Conserva unión de `source_refs` | `scripts/authoring/transform.py` | `references/04-authoring/ir-spec.md` |
| Parsear NoteMark al IR | Gramática formal | Errores con archivo, línea y directiva | `scripts/authoring/parse_notemark.py` | `references/04-authoring/notemark.md` |
| Trazabilidad bidireccional nodo↔bloque | Búsqueda en índices | Cobertura binaria por nodo | `scripts/util/trace.py` | — |
| Renderizar IR a cada destino | Mapeo IR → dialecto del destino | Tabla de degradación por capacidad ausente | `scripts/render/obsidian.py`, `notion_api.py`, `notion_md.py`, `appflowy.py`, `markdown.py`, `html_pdf.py` | `references/08-render/contract.md`, `linking.md`, `publishing.md` |
| Exportar flashcards | Transformación de formato | Plugin Obsidian + CSV Anki | `scripts/render/flashcards.py` | `references/09-study/` |
| Publicar en Notion respetando límites | Troceo, reintentos, idempotencia | Límites Notion declarados en `references/08-render/capability-matrix.md` | `scripts/render/notion_api.py` | `references/08-render/publishing.md` |
| Equivalencia entre destinos | Extracción y comparación contra IR | Cero pérdidas, diferencias justificadas | `scripts/validate/cross_target.py` | `references/08-render/contract.md` |
| Auditoría de no-pérdida | Muestreo inverso automatizado | Umbral 100 % `must-keep` | `scripts/validate/completeness.py` | `references/10-quality/completeness-audit.md` |
| Triaje de archivo de entrada | Heurísticas con umbrales numéricos | Caracteres extraíbles por página, fuentes embebidas, imágenes a página completa | `scripts/ingest/triage.py` | `references/01-ingest/triage.md` |
| Extracción de PDF nativo con coordenadas | Tipografía y posición, no heurística de texto | Coincidencia con índice ≥ 95 % | `scripts/ingest/pdf_native.py` | — |
| Otros formatos (EPUB/DOCX/PPTX/transcripción) | Cada uno con su parser nativo | Anclas resolubles en todos los casos | `scripts/ingest/other_formats.py` | — |
| Documentación web multipágina | Descubrimiento de índice y limpieza de boilerplate | URL canónica por sección | `scripts/ingest/web_docs.py` | — |
| Catálogo y dedup de assets | Hash + nombre determinista | Sin duplicados; alt text obligatorio | `scripts/ingest/assets.py` | — |
| Visor HTML del SDM | Presentación, sin cálculo | Filtros por tipo y confianza | `scripts/util/sdm_view.py` | — |

### 3.3 Tabla normativa "Lo hace el agente"

| Tarea | Por qué no un script | `references/` |
|---|---|---|
| Identificar unidades de información y su criticidad | Requiere entender qué dice el texto | `references/03-knowledge/information-units.md` |
| Decidir redundancia vs esencialidad | Juicio semántico | `references/03-knowledge/information-units.md` |
| Elegir tipo de nota y dividir en archivos | Juicio estructural | `references/05-note-types/`, `references/03-knowledge/note-plan.md` |
| Redactar intuición, analogías, ejemplos, comparaciones | Núcleo del valor | `references/06-writing/`, `references/07-visual/` |
| Decidir qué diagrama comunica mejor una idea | Juicio | `references/07-visual/diagram-catalog.md` |
| Detectar contradicciones y obsolescencia en la fuente | Comprensión | `references/03-knowledge/conflicts.md` |
| Reconstruir un diagrama impreso en Mermaid | Lectura de la figura + el texto | `references/07-visual/reconstruction.md` |
| Resolver terminología y colisiones de nombres | Contexto acumulado | `references/03-knowledge/terminology.md` |
| Verificar que el parafraseo no perdió nada | Comparación semántica | `references/06-writing/`, `references/10-quality/fidelity-rules.md` |
| Definir Note Plan y aprobación del usuario | División semántica del trabajo | `references/03-knowledge/note-plan.md` |
| Seleccionar términos canónicos bilingües | Política lingüística del perfil | `references/11-i18n/` |
| Aplicar estilo de redacción (voz, tono) | Intención del autor | `references/06-writing/` |

### 3.4 Zona gris resuelta

Tres casos canónicos resueltos, más una cláusula genérica.

| Caso | Resolución | Referencia |
|---|---|---|
| **Corrección post-OCR de código** | Script aplica reglas y diccionario; agente valida sintaxis solo cuando la corrección es forzosa. Nunca agente solo: ahí se inventa código que compila pero no es el del libro. | `ROADMAP.md` §2, `AGENT.md` §3 |
| **Reconstrucción de diagrama impreso** | Script extrae la imagen y mide geometría; agente reconstruye el Mermaid a partir de la imagen y el texto. La imagen original siempre se conserva. | `ROADMAP.md` §2, `references/07-visual/reconstruction.md` |
| **Selección de motor OCR** | Script selecciona por umbrales numéricos del preprocesado (confianza, densidad, idioma detectado); agente solo elige el idioma activo cuando ninguno pasa el umbral. | `references/01-ingest/ocr-engines.md` |

**Cláusula genérica:** cualquier tarea que combine entrada numérica (umbral, confianza, coordenada) con validación semántica se divide en **script + agente**, nunca en agente solo. Si una tarea cae en esta categoría y no está en los tres casos canónicos, se documenta como nueva fila en esta tabla.

### 3.5 Anti-patrón: programar juicio

Un script cruza la línea cuando su responsabilidad usa verbos como **decidir**, **evaluar**, **jugar**, **determinar si esto es importante**, **clasificar por significado**, **priorizar**.

- **Ejemplo malo (anti):** `scripts/ingest/classify.py` con función `is_important(block) → bool`.
- **Ejemplo bueno:** la clasificación de regiones usa señales estructurales (fuente monoespaciada, fondo sombreado, bordes, densidad de símbolos); las regiones ambiguas se marcan como `uncertain` y la decisión final la toma el agente consultando `references/02-source-model/editorial-semantics.md`.
- **Remedio:** sacar la decisión a `references/`; dejar en el script solo la operación que aplica el criterio (cómputo, hash, parseo).

### 3.6 Anti-patrón inverso: pedir aritmética al agente

Una instrucción cruza la línea cuando pide al agente **contar**, **hashear**, **sumar**, **iterar**, **ordenar**, **validar sintaxis exacta**, **comparar listas**, **aplicar regex**, **calcular un porcentaje**.

- **Ejemplo malo (anti):** en `references/03-knowledge/ledger.md`, "cuenta cuántas unidades `must-keep` faltan y dime el número".
- **Ejemplo bueno:** el script `scripts/util/ledger.py` produce el reporte con conteos exactos; la instrucción dice "lee el reporte y decide si la cobertura es aceptable o qué sección reprocesar".
- **Remedio:** el script ejecuta; el agente consume el resultado y razona sobre él. Nunca el agente hace la cuenta.

## 4. Quince casos de prueba

| ID | Tarea | Dominio | Determinista | Repetitivo | Caro/mal/no reproducible | Veredicto |
|---|---|---|---|---|---|---|
| T01 | Rasterizar PDF a PNG a 300 DPI | Documentación de producto | Sí | Sí | Caro | Script |
| T02 | Hashear fuente PDF para detectar cambios | Documentación de producto | Sí | No | Caro (irrelevante) | Script |
| T03 | Validar sintaxis exacta de un bloque Mermaid | Sistemas | Sí | Sí | Mal (falsos negativos del agente) | Script |
| T04 | Renderizar Mermaid a SVG | Sistemas | Sí | Sí | Caro | Script |
| T05 | Contar unidades `must-keep` sin asignar en el ledger | Bases de datos | Sí | Sí | Caro | Script (anti-patrón 3.6 si se pide al agente) |
| T06 | Decidir si una nota debe ser tipo `procedure` o `concept` | Bases de datos | No | No | — | Instrucción |
| T07 | Redactar la sección "intuición" de una nota `concept` | Bases de datos | No | No | — | Instrucción |
| T08 | Decidir si una región OCR necesita revisión humana por umbral | Documentación | Sí | Sí | — | Script (zona gris resuelta: agente solo si el umbral es borroso) |
| T09 | Validar código OCR con validación sintáctica forzosa | Sistemas | Sí | Sí | — | Zona gris resuelta (§3.4) |
| T10 | Elegir el motor OCR para un documento | Documentación | Sí | Sí | — | Script (agente solo si ningún motor pasa el umbral) |
| T11 | Redactar analogía para un concepto de redes | Redes | No | No | — | Instrucción |
| T12 | Detectar duplicados por similitud de término canónico | Bases de datos | Sí | Sí | — | Script con umbral numérico |
| T13 | Decidir si dos definiciones son realmente contradictorias | Documentación | No | No | — | Instrucción |
| T14 | Ordenar candidatos de Note Plan por longitud | Bases de datos | Sí | Sí | — | Script |
| T15 | Decidir si una sección admite analogía pedagógica | Documentación | No | No | — | Instrucción |

**Distribución:** 10 script · 1 zona gris resuelta · 4 instrucción. **Dominios cubiertos:** bases de datos, redes, sistemas, documentación de producto (4).

## 5. Apéndice A — Auditoría de scripts

Tabla con los 35 scripts planificados. Cada fila: ruta, responsabilidad en una frase, veredicto.

| Ruta (Fase) | Responsabilidad | Veredicto |
|---|---|---|
| `scripts/ingest/triage.py` (F17) | Clasificar cada página por densidad de texto y presencia de imágenes | Limpio |
| `scripts/ingest/pdf_native.py` (F18) | Extraer texto, fuente y coordenadas de PDF nativo | Limpio |
| `scripts/ingest/preprocess.py` (F19) | Rasterizar, corregir inclinación, binarizar, eliminar bordes | Limpio |
| `scripts/ingest/ocr.py` (F20) | Invocar motor OCR, devolver palabra + bbox + confianza | Limpio |
| `scripts/ingest/layout.py` (F21) | Detectar columnas y orden de lectura por geometría | Limpio |
| `scripts/ingest/regions.py` (F22) | Clasificar regiones por señales estructurales; ambiguas → `uncertain` | Limpio (zona gris 3.4: agente solo en `uncertain`) |
| `scripts/ingest/tables.py` (F23) | OCR de tablas con encabezados multinivel y celdas combinadas | Limpio |
| `scripts/ingest/formulas.py` (F24) | OCR de fórmulas a LaTeX; verificación de compilación | Limpio |
| `scripts/ingest/code_ocr.py` (F25) | OCR de código con tabla de confusiones; agente valida sintaxis si forzoso | Limpio (zona gris 3.4) |
| `scripts/ingest/review_report.py` (F26) | Reporte HTML con recorte y texto lado a lado, filtrable | Limpio |
| `scripts/ingest/post_ocr.py` (F27) | Guionado, ligaduras, diccionario técnico auditable | Limpio |
| `scripts/ingest/other_formats.py` (F28) | EPUB/DOCX/PPTX/transcripciones con anclas propias | Limpio |
| `scripts/ingest/web_docs.py` (F29) | Descubrir índice web, eliminar boilerplate, URL canónica | Limpio |
| `scripts/validate/ingest_check.py` (F30) | Verificar cobertura de páginas, secciones del índice, anomalías | Limpio |
| `scripts/ingest/build_sdm.py` (F31) | Ensamblar regiones en jerarquía con ids deterministas | Limpio |
| `scripts/ingest/assets.py` (F33) | Extraer imágenes con nombre determinista, dedup por hash, alt text | Limpio |
| `scripts/util/sdm_cache.py` (F36) | Caché por hash con invalidación selectiva | Limpio |
| `scripts/util/sdm_view.py` (F36) | Visor HTML del SDM con filtros | Limpio |
| `scripts/util/ledger.py` (F38) | Contabilizar, validar transiciones, generar reporte del ledger | Limpio |
| `scripts/validate/completeness.py` (F43) | Auditoría de no-pérdida con muestreo inverso | Limpio |
| `scripts/authoring/parse_notemark.py` (F48) | Parsear NoteMark a IR; errores con archivo, línea, directiva | Limpio |
| `scripts/validate/validate_ir.py` (F49) | Validar IR contra esquema; reportar archivo, nodo, regla | Limpio |
| `scripts/authoring/transform.py` (F50) | Aplicar `split`, `merge`, `dedup` sobre IR | Limpio |
| `scripts/util/trace.py` (F52) | Resolver `source_ref` ↔ bloque SDM; reportar huérfanos | Limpio |
| `scripts/render/obsidian.py` (F54) | Traducir IR a Markdown de Obsidian con callouts, propiedades, wikilinks | Limpio |
| `scripts/render/notion_api.py` (F55) | Publicar IR en Notion API con troceo, idempotencia, reintentos | Limpio |
| `scripts/render/notion_md.py` (F56) | Generar Markdown limitado para importación a Notion | Limpio |
| `scripts/render/appflowy.py` (F57) | Generar Markdown compatible con AppFlowy | Limpio |
| `scripts/render/markdown.py` (F58) | Generar Markdown estándar con `<details>` para plegables | Limpio |
| `scripts/render/html_pdf.py` (F59) | Generar HTML autocontenido y PDF con saltos controlados | Limpio |
| `scripts/render/flashcards.py` (F60) | Exportar tarjetas a plugin Obsidian y CSV Anki | Limpio |
| `scripts/validate/cross_target.py` (F63) | Comparar salidas por destino contra IR; reportar pérdidas | Limpio |
| `scripts/validate/mermaid.py` (F67) | Validar Mermaid con parser real y lista blanca portable | Limpio |
| `scripts/render/diagram_image.py` (F68) | Pre-renderizar Mermaid a SVG/PNG con caché por hash | Limpio |
| `scripts/render/make_figure.py` (F70) | Generar figuras de datos con tokens y paleta daltonismo-segura | Limpio |

**Total: 35 scripts auditados. 35 limpios. 0 cruces. 0 fases correctoras asignadas.**

## 6. Apéndice B — Auditoría de instrucciones

Las 54 instrucciones corresponden a las 54 filas de `docs/skill-anatomy.md` §6. Cada fila: ruta, responsabilidad en una frase, veredicto.

| Ruta (Fase) | Responsabilidad | Veredicto |
|---|---|---|
| `references/00-pipeline/responsibilities.md` (F3) | Este doc; norma de división agente/script | Limpio |
| `references/00-pipeline/architecture.md` (F4) | Describir 5 capas, artefactos y directorio de trabajo | Limpio |
| `references/00-pipeline/manifest.md` (F16) | Reglas del manifiesto reanudable; acción ante cambio de hash | Limpio |
| `references/01-ingest/triage.md` (F17) | Criterios para elegir cadena de ingesta por página | Limpio |
| `references/01-ingest/ocr-engines.md` (F20) | Cuándo usar cada motor OCR; instalación por SO | Limpio |
| `references/01-ingest/code-ocr.md` (F25) | Tabla de confusiones en monoespaciado; cuándo validar sintaxis | Limpio |
| `references/01-ingest/confidence.md` (F26) | Umbrales por tipo de región; reporte de revisión | Limpio |
| `references/02-source-model/spec.md` (F13) | Contrato del SDM: tipos de bloque, anclas, confianza | Limpio |
| `references/02-source-model/anchors.md` (F32) | Anclas sintéticas estables; resolución de numeración inconsistente | Limpio |
| `references/02-source-model/provenance.md` (F34) | Detectar producto, vendor, versión, ISBN, fecha | Limpio |
| `references/02-source-model/editorial-semantics.md` (F35) | Mapear cajas editoriales a tipos de bloque | Limpio |
| `references/03-knowledge/information-units.md` (F37) | Tipos de unidad; reglas de criticidad automática | Limpio |
| `references/03-knowledge/ledger.md` (F15) | Lista cerrada de motivos de descarte; reporte de cobertura | Limpio |
| `references/03-knowledge/concept-graph.md` (F39) | Construcción del grafo; rutas de lectura | Limpio |
| `references/03-knowledge/terminology.md` (F40) | Término canónico, alias, colisiones entre dominios | Limpio |
| `references/03-knowledge/conflicts.md` (F41) | Detección de contradicciones; nunca resolver en silencio | Limpio |
| `references/03-knowledge/note-plan.md` (F44) | División semántica del trabajo en notas | Limpio |
| `references/04-authoring/notemark.md` (F12) | Gramática NoteMark: directivas de bloque y marcas inline | Limpio |
| `references/04-authoring/ir-spec.md` (F14) | Catálogo de nodos del IR; capacidades requeridas | Limpio |
| `references/04-authoring/block-directives.md` (F45) | Cuándo usar cada directiva de bloque | Limpio |
| `references/04-authoring/inline-marks.md` (F46) | Cuándo insertar `{src:}`, `[[term:]]`, `[[note:]]` | Limpio |
| `references/04-authoring/properties.md` (F47) | Propiedades YAML canónicas; obligatoriedad por tipo | Limpio |
| `references/04-authoring/depth-layers.md` (F51) | Definir L1/L2/L3; cuándo extraer nota hermana | Limpio |
| `references/05-note-types/concept.md` (F78) | Plantilla `concept` | Limpio |
| `references/05-note-types/api-reference.md` (F79) | Plantilla `api-reference` | Limpio |
| `references/05-note-types/procedure.md` (F80) | Plantilla `procedure` con rollback | Limpio |
| `references/05-note-types/configuration.md` (F81) | Plantilla `configuration` | Limpio |
| `references/05-note-types/error-troubleshooting.md` (F82) | Plantilla `error-troubleshooting` con árbol de diagnóstico | Limpio |
| `references/05-note-types/architecture.md` (F83) | Plantilla `architecture` con diagrama obligatorio | Limpio |
| `references/05-note-types/syntax.md` (F84) | Plantilla `syntax` con metasímbolos | Limpio |
| `references/05-note-types/data-model.md` (F85) | Plantilla `data-model` con ER | Limpio |
| `references/05-note-types/chapter-digest.md` (F86) | Plantilla `chapter-digest` con continuidad bidireccional | Limpio |
| `references/05-note-types/comparison.md` (F87) | Plantilla `comparison` con párrafo de síntesis obligatorio | Limpio |
| `references/05-note-types/version-delta.md` (F88) | Plantilla `version-delta` con versión exacta por cambio | Limpio |
| `references/05-note-types/glossary-term.md` (F89) | Plantilla `glossary-term` con definiciones bilingües | Limpio |
| `references/05-note-types/cheatsheet.md` (F90) | Plantilla `cheatsheet` sin prosa | Limpio |
| `references/05-note-types/index-moc.md` (F91) | Plantilla `index-moc` con descripción por enlace | Limpio |
| `references/05-note-types/practice.md` (F92) | Plantilla `practice` / lab con entorno y limpieza | Limpio |
| `references/07-visual/diagram-catalog.md` (F65) | Matriz intención → tipo de diagrama | Limpio |
| `references/07-visual/mermaid-portable.md` (F66) | Subconjunto Mermaid portable; lista blanca y negra | Limpio |
| `references/07-visual/monospace-diagrams.md` (F69) | Patrones de diagramas en monoespaciado | Limpio |
| `references/07-visual/reconstruction.md` (F71) | Cuándo reconstruir, cuándo conservar captura | Limpio |
| `references/07-visual/accessibility.md` (F71) | Contraste, tamaño mínimo, color no único | Limpio |
| `references/07-visual/tokens.md` (F72) | Design tokens; valor claro y oscuro por token | Limpio |
| `references/07-visual/style-mapping.md` (F73) | Mapeo intención semántica → estilo por destino | Limpio |
| `references/07-visual/note-templates.md` (F75) | Cabecera visual por tipo de nota | Limpio |
| `references/07-visual/density.md` (F76) | Reglas numéricas de densidad visual | Limpio |
| `references/08-render/capability-matrix.md` (F8) | Capacidades verificadas por destino | Limpio |
| `references/08-render/contract.md` (F53) | Interfaz renderer; tabla de degradación | Limpio |
| `references/08-render/linking.md` (F61) | Resolución de `link-note` por destino; deuda de enlaces | Limpio |
| `references/08-render/publishing.md` (F62) | Publicación idempotente; detección de edición manual | Limpio |
| `references/08-render/migration.md` (F64) | Re-render desde IR; importación inversa | Limpio |
| `references/10-quality/fidelity-rules.md` (F42) | Tres niveles de fidelidad; regla de la duda | Limpio |
| `references/10-quality/completeness-audit.md` (F43) | Recorrido del ledger; muestreo inverso | Limpio |

**Total: 54 instrucciones auditadas. 54 limpias. 0 cruces. 0 fases correctoras asignadas.**

## 7. Cómo verificar el test sobre una tarea nueva

1. **Determinista?** Anotar Sí o No con una frase que lo justifique (qué entrada/salida).
2. **Repetitivo?** Anotar Sí o No con la frecuencia esperada.
3. **El agente lo haría mal/caro/no reproducible?** Anotar Sí o No con la evidencia (coste en tokens, varianza observada, etc.).
4. Si las tres son **Sí** → tarea de script. Anotar la fila correspondiente en §3.2 o crear fila nueva si no encaja.
5. Si las tres son **No** → tarea de instrucción. Anotar en §3.3 o crear fila nueva.
6. Si hay **mezcla** → ir a §3.4. Si ninguno de los tres casos canónicos aplica, aplicar la cláusula genérica; si tampoco, **reabre Fase 3** con la nueva fila propuesta.
7. Verificar el resultado contra `references/` y `scripts/` existentes; si hay colisión, resolver antes de cerrar.

## 8. Cambios permitidos sin reabrir Fase 3

- Añadir filas a las tablas §3.2/§3.3 cuando fases futuras introduzcan tareas nuevas que encajen en categorías existentes.
- Añadir filas a los Apéndices A/B si la auditoría se rehace tras una fase posterior y no hay nuevos cruces.
- Añadir entradas a §3.4 cuando aparezca una nueva zona gris resuelta, siempre que la cláusula genérica la cubra.

**Reabren Fase 3:**

- Modificar las tres preguntas de §3.1.
- Mover una fila de zona gris a script o instrucción (o viceversa) sin evidencia.
- Descubrir un cruce en A/B y no asignarle fase correctora.
- Cambiar la cláusula genérica de §3.4.
