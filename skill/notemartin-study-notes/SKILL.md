---
name: notemartin-study-notes
description: Convierte documentación técnica, manuales de producto, libros técnicos (incluidos PDFs escaneados), referencias de API y apuntes sueltos en notas de estudio completas, trazables y publicables en Obsidian, Notion, AppFlowy, Markdown estándar, HTML/PDF y sistemas de repaso espaciado. Mantiene fidelidad al original, cobertura verificable por ledger y formato intermedio NoteMark para que las notas viajen entre destinos sin reescritura.
---

# `notemartin-study-notes` — SKILL.md

> Router N2 (`AGENT.md` §4). Lo único que el agente lee cuando la skill se dispara. **Solo enruta.** Cero plantillas embebidas; cero gramática NoteMark; cero tablas de degradación. Toda regla de detalle vive en `references/`. El límite duro son **500 líneas** (`INV-02`); el objetivo operativo de esta versión es ~360.

## §1 · Cuándo se dispara esta skill

Dispara cuando el usuario entrega una fuente técnica (documentación, manual, libro, PDF escaneado, referencia de API, apunte, transcripción, repositorio) y pide —o implica— producir **notas de estudio trazables** con publicación en uno o varios destinos (Obsidian, Notion, AppFlowy, Markdown, HTML/PDF, Anki/plugin de repaso).

**No dispara** para: resumir un correo, traducir prosa libre, generar código sin destino de notas, redactar un ensayo, analizar un dataset sin intención de notas. Tampoco para producir Markdown de un destino concreto — eso es lo que el render hace a partir del IR; pedirlo al agente rompe la fidelidad y la portabilidad (`INV-05`).

## §2 · Invariantes que aplican a toda invocación

Subset de `skills/AGENT.md` §2 cuyas omisiones producen fallo silencioso. El resto de invariantes siguen vigentes y se citan desde la columna "Archivos a NO leer" cuando una etapa concreta los exige.

| ID | Invariante (resumen) | Si se omite… |
|---|---|---|
| **INV-02** | `SKILL.md` ≤ 500 líneas; solo enruta. | El contexto de toda invocación futura se satura. |
| **INV-03** | Ninguna capa afirma un hecho que no exista en la capa inferior. | Aparecen notas plausibles pero falsas. |
| **INV-04** | Todo nodo fáctico del IR porta `source_refs` resolubles. | La trazabilidad se rompe y la auditoría no puede verificar cobertura. |
| **INV-05** | El agente escribe **NoteMark**, nunca Markdown de destino ni JSON de IR a mano. | Los destinos no-Obsidian quedan rotos en silencio. |
| **INV-08** | El 100 % de las unidades `must-keep` alcanza estado terminal antes de cerrar. | La puerta de fidelidad se salta y la nota miente por omisión. |
| **INV-09** | Los literales de la fuente (mensajes de error, nombres de parámetro, sintaxis, defaults, comandos) se conservan textualmente. | La nota "explica" cosas que la fuente no dice. |
| **INV-10** | Ninguna enumeración cerrada se emite truncada. Prohibidos `etc.`, `entre otros`, `los más relevantes`. | La fuente dice 7 cosas; la nota dice "varias". |
| **INV-17** | Toda incertidumbre se declara. Versión indeterminable → `unknown`; nunca se infiere en silencio. | El agente rellena huecos con conocimiento propio. |

## §3 · Árbol de decisión de tipo de fuente

El agente elige la cadena de ingesta L0 con este árbol. Cada hoja nombra el script y la fase que lo produce; el catálogo en §6 da la invocación cuando existe.

```
¿Archivo o URL?
├─ Archivo PDF
│   ├─ ¿Tiene capa de texto extraíble? (heurística: ≥ 100 caracteres/página en muestra)
│   │   ├─ Sí → PDF nativo  → scripts/ingest/pdf_native.py       [pendiente F18]
│   │   └─ No → PDF escaneado
│   │        ├─ ¿Idioma del OCR en profile.yaml?
│   │        │    ├─ Sí → rasterizar + scripts/ingest/ocr.py    [F19, F20]
│   │        │    └─ No → rasterizar, detección de idioma por el agente, ocr.py
│   │        └─ ¿Hay zonas de código monoespaciadas? → scripts/ingest/code_ocr.py [F25]
│   ├─ ¿Tiene tablas con celdas combinadas? → scripts/ingest/tables.py    [pendiente F23]
│   └─ ¿Tiene fórmulas? → scripts/ingest/formulas.py                    [pendiente F24]
├─ EPUB / DOCX / PPTX → scripts/ingest/other_formats.py                  [pendiente F28]
├─ HTML multipágina → scripts/ingest/web_docs.py                         F29
├─ Transcripción (TXT/MD con marcas de hablante) → scripts/ingest/other_formats.py [F28]
└─ Repositorio con README → catalogar como fuente plurilingüe (per F10 corpus)
```

Triage por página, no por documento: un PDF híbrido (capítulos nativos, anexos escaneados) se divide página a página. Detalle y umbrales numéricos en `references/01-ingest/triage.md` (F17). El script ejecutable es `scripts/ingest/triage.py` (§6).

## §4 · Flujo de las 5 capas

Una línea por capa. El contrato detallado (entrada, salida, perfil leído, puertas, modo degradado) vive en `references/00-pipeline/architecture.md` (F4); este router NO lo reproduce.

### L0 Ingesta

Lee: archivo fuente + `profile.yaml`. Produce: `ingest/regions.json` + `ingest/{pages,ocr,tables,formulas,code}/`, `ingest/review.html`, `ingest/preprocess.log`. Puertas: ninguna por sí sola (F30 cubre la validación de ingesta). Detalle: `references/00-pipeline/architecture.md` §3.1.

### L1 SDM

Lee: artefactos de `ingest/` + `profile.yaml`. Produce: `sdm.json` con ids deterministas y anclas estables. Puertas: bloquea si orphan ratio > 20 % o confianza media OCR < 0.60. Detalle: `references/00-pipeline/architecture.md` §3.2.

### L2 Conocimiento

Lee: `sdm.json` + `profile.yaml`. Produce: `knowledge/{ledger.json, concept-graph.json, note-plan.json, glossary.json}`. **Puerta de fidelidad:** 100 % de `must-keep` con estado terminal, no se salta (`INV-08`). Detalle: `references/00-pipeline/architecture.md` §3.3.

### L3 Autoría

Lee: `knowledge/` + `sdm.json` (referencias, no como contenido) + `profile.yaml`. Produce: `notemark/<note-id>.nm` + `ir/<note-id>.json`. **Puerta de calidad:** IR válido y sin avisos estructurales bloqueantes. Detalle: `references/00-pipeline/architecture.md` §3.4.

### L4 Render

Lee: `ir/` + `sdm.json` (rutas de imágenes) + `profile.yaml`. Produce: `render/<destino>/<note-id>...` + `reports/render-degradation.md`. **Puerta de render:** degradación correcta, contenido íntegro (`INV-07`). Detalle: `references/00-pipeline/architecture.md` §3.5 y `references/08-render/capability-matrix.md` (F8).

## §5 · Tabla de enrutado

Plantilla de 4 columnas fijada por `docs/skill-anatomy.md` §5: **Situación | Archivo a leer | Archivos a NO leer | Fase**. Una fila por unidad discreta de decisión. Las 54 rutas declaradas en `skill-anatomy.md` §6 aparecen aquí: 3 con archivo físico y 51 marcadas `[pendiente Fxxx]`. Cuando una fase materialice su archivo, se retira la marca en el mismo commit que la crea; la fila sigue siendo la misma.

### §5.1 · Rutas en `references/00-pipeline/` y `01-ingest/`

| Situación | Archivo a leer | Archivos a NO leer | Fase |
|---|---|---|---|
| Antes de implementar, decidir si algo es script o instrucción | [responsibilities.md](references/00-pipeline/responsibilities.md) | ninguno (es el discriminador raíz) | F3 |
| Inicio de capítulo u obra completa, para entender qué artefacto produce cada capa | [architecture.md](references/00-pipeline/architecture.md) | `references/01-ingest/` y posteriores hasta saber la cadena L0 | F4 |
| Interrupción o reanudación de un trabajo | `references/00-pipeline/manifest.md` | ninguno | [pendiente F16] |
| Antes de la primera ingesta de un documento | [triage.md](references/01-ingest/triage.md) | `references/02-source-model/` y posteriores | F17 |
| Selección de motor OCR para un documento | `references/01-ingest/ocr-engines.md` | `references/04-authoring/`, `references/05-note-types/` | [pendiente F20] |
| OCR sobre región clasificada como código | `references/01-ingest/code-ocr.md` | `references/04-authoring/` (la validación sintáctica se decide en zona gris) | [pendiente F25] |
| Umbrales por tipo de región para revisión humana | `references/01-ingest/confidence.md` | `references/03-knowledge/` | [pendiente F26] |

### §5.2 · Rutas en `references/02-source-model/`, `03-knowledge/`, `04-authoring/`, `05-note-types/`, `06-writing/`, `07-visual/`

| Situación | Archivo a leer | Archivos a NO leer | Fase |
|---|---|---|---|
| Cualquier consulta al SDM o a sus anclas | `references/02-source-model/spec.md` | `references/04-authoring/` (no redactar antes de tener SDM) | F13 |
| Construcción del SDM a partir de la ingesta L0 | `references/02-source-model/build-sdm.md` | `references/02-source-model/spec.md` (consulta solo si necesitas saber qué valida el schema) | F31 |
| Documento sin numeración o con numeración inconsistente | `references/02-source-model/anchors.md` | `references/03-knowledge/` (las anclas son prerrequisito del ledger) | F32 |
| Extracción de metadatos editoriales de la fuente (version, vendor, ISBN…) y propagación read/inferred | `references/02-source-model/provenance.md` | `references/04-authoring/` (no redactar antes de tener la procedencia) | F34 |
| Clasificación de regiones editoriales (Nota, Precaución, Ejemplo, Consejo, Novedad, Obsoleto) y convenciones por vendor | `references/02-source-model/editorial-semantics.md` | `references/03-knowledge/` (las cajas son prerrequisito del ledger si el bloque es una unidad) | F35 |
| Extracción de unidades de información en L2 | `references/03-knowledge/information-units.md` | `references/04-authoring/` (no decidir tipo de nota antes de tener unidades) | F37 |
| Cualquier operación sobre el Coverage Ledger (init, add, mark, report, check, manifest) | `references/03-knowledge/ledger-operativo.md` | `references/03-knowledge/ledger.md` (forma e invariantes), `references/03-knowledge/information-units.md` (taxonomía R1–R5) | F38 |
| Construcción del grafo de prerrequisitos (build, routes, export, check) | `references/03-knowledge/concept-graph.md` | `references/03-knowledge/ledger-operativo.md` (corre tras F38), `references/03-knowledge/information-units.md` (fuente de aristas) | F39 |
| Resolución de términos canónicos, aliases y colisiones entre dominios | `references/03-knowledge/terminology.md` | `references/03-knowledge/information-units.md` (tipo `definition`), `references/03-knowledge/concept-graph.md` (related_concepts) | F40 |
| Detección de contradicciones u obsolescencia | `references/03-knowledge/conflicts.md` | `references/04-authoring/` | [pendiente F41] |
| División del trabajo en notas (Note Plan) | `references/03-knowledge/note-plan.md` | `references/04-authoring/` hasta cerrar el plan | [pendiente F44] |
| Detección de contradicciones u obsolescencia (registry + directivas `:::contradiction` y `:::discrepancy`) | `references/03-knowledge/conflicts.md` | `references/04-authoring/notemark.md` (directivas F12), `references/03-knowledge/information-units.md` (version-note), `references/03-knowledge/terminology.md` (deprecation_status cross-cutting) | F41 |
| División del trabajo en notas (Note Plan: 15 tipos cerrados + threshold de aprobación) | `references/03-knowledge/note-plan.md` | `references/03-knowledge/ledger.md` (F15 unidades a asignar), `references/03-knowledge/concept-graph.md` (F39 dependencias), `references/05-note-types/README.md` (F78-F92 tipos) | F44 |
| Redacción de cualquier nota en NoteMark | `references/04-authoring/notemark.md` | el resto de `references/04-authoring/` (directivas/marcas/propiedades están cubiertos aquí) | [pendiente F12] |
| Validación del IR o consulta del catálogo de nodos | `references/04-authoring/ir-spec.md` | `references/05-note-types/` (el catálogo de tipos decide qué nodos usar, no al revés) | [pendiente F14] |
| Elección de directiva de bloque NoteMark | `references/04-authoring/block-directives.md` | `references/05-note-types/` (las plantillas fijan directivas por tipo) | F45 |
| Inserción de marcas inline en redacción | `references/04-authoring/inline-marks.md` | ninguno | F46 |
| Definición de propiedades YAML de una nota | `references/04-authoring/properties.md` | `references/05-note-types/` | F47 |
| Definir capas L1, L2, L3 de una nota | `references/04-authoring/depth-layers.md` | `references/05-note-types/` | F51 |
| Seleccionar el tipo de nota `concept` | `references/05-note-types/concept.md` | los otros 14 archivos de `references/05-note-types/` | F78 |
| Seleccionar el tipo de nota `api-reference` | `references/05-note-types/api-reference.md` | los otros 14 archivos de `references/05-note-types/` | F79 |
| Seleccionar el tipo de nota `procedure` | `references/05-note-types/procedure.md` | los otros 14 archivos de `references/05-note-types/` | F80 |
| Seleccionar el tipo de nota `configuration` | `references/05-note-types/configuration.md` | los otros 14 archivos de `references/05-note-types/` | F81 |
| Seleccionar el tipo de nota `error-troubleshooting` | `references/05-note-types/error-troubleshooting.md` | los otros 14 archivos de `references/05-note-types/` | F82 |
| Seleccionar el tipo de nota `architecture` | `references/05-note-types/architecture.md` | los otros 14 archivos de `references/05-note-types/` | F83 |
| Seleccionar el tipo de nota `syntax` | `references/05-note-types/syntax.md` | los otros 14 archivos de `references/05-note-types/` | F84 |
| Seleccionar el tipo de nota `data-model` | `references/05-note-types/data-model.md` | los otros 14 archivos de `references/05-note-types/` | F85 |
| Seleccionar el tipo de nota `chapter-digest` | `references/05-note-types/chapter-digest.md` | los otros 14 archivos de `references/05-note-types/` | F86 |
| Seleccionar el tipo de nota `comparison` | `references/05-note-types/comparison.md` | los otros 14 archivos de `references/05-note-types/` | F87 |
| Seleccionar el tipo de nota `version-delta` | `references/05-note-types/version-delta.md` | los otros 14 archivos de `references/05-note-types/` | F88 |
| Seleccionar el tipo de nota `glossary-term` | `references/05-note-types/glossary-term.md` | los otros 14 archivos de `references/05-note-types/` | F89 |
| Seleccionar el tipo de nota `cheatsheet` | `references/05-note-types/cheatsheet.md` | los otros 14 archivos de `references/05-note-types/` | F90 |
| Seleccionar el tipo de nota `index-moc` | `references/05-note-types/index-moc.md` | los otros 14 archivos de `references/05-note-types/` | F91 |
| Seleccionar el tipo de nota `practice` o lab | `references/05-note-types/practice.md` | los otros 14 archivos de `references/05-note-types/` | F92 |
| Seleccionar el tipo de nota `selector` | `references/05-note-types/selector.md` | los 15 archivos de `references/05-note-types/` | F93 |
| Estilo `intuition-first` al redactar prosa pedagógica (Problema → Intuición → Analogía → Definición formal → Confirmación) | [references/06-writing/intuition-first.md](references/06-writing/intuition-first.md) | el resto de `references/06-writing/` (cada archivo cubre una dimensión ortogonal) | F94 |
| Elegir o crear analogía al redactar prosa pedagógica (catálogo de 12 patrones + banco de 18 entradas con `Rotura:`) | [references/06-writing/analogies.md](references/06-writing/analogies.md) | `references/06-writing/intuition-first.md` (F94 norma el **cuándo**; F95 norma el **qué**) | F95 |
| Redactar ejemplo ejecutable con setup/acción/resultado/limpieza + cabecera `> **Entorno:**` | [references/06-writing/executable-examples.md](references/06-writing/executable-examples.md) | `references/06-writing/intuition-first.md` (F94 norma la mecánica de `## Confirmación`; F96 norma el contenido del `:::example`) | F96 |
| Construir comparación correcta (tabla lado a lado / jerarquía por relajación / matriz de decisión / trade-offs / síntesis + marcado derivado) | [references/06-writing/comparisons.md](references/06-writing/comparisons.md) | `references/05-note-types/comparison.md` (F87 norma el **tipo** `comparison`; F97 norma el **artefacto** transversal) | F97 |
| Reescribir prosa preservando literales y enumeraciones cerradas (normativiza INV-09 + INV-10) | [references/06-writing/paraphrase.md](references/06-writing/paraphrase.md) | `references/06-writing/intuition-first.md` (F94 norma el patrón de 5 etapas; F98 norma el parafraseo dentro de cada etapa) | F98 |
| Aplicar voz y estilo consistentes (frases cortas, voz activa, segunda persona en procedimientos, sin adjetivos valorativos) | [references/06-writing/voice-style.md](references/06-writing/voice-style.md) | `references/06-writing/paraphrase.md` (F98 norma el **contenido**; F99 norma la **forma** sobre el mismo párrafo) | F99 |
| Diagnosticar anti-patrones transversales (12 AP + 10 señales + checklist de 12 items integrable en `concept.md §6`) | [references/06-writing/anti-patterns.md](references/06-writing/anti-patterns.md) | F94-F99 (cada fase norma sus AP específicos; F100 los **agrega** los transversales y los referencia desde el checklist de calidad) | F100 |
| Inicializar / operar el modo obra completa de un libro (reconocimiento previo, estado compartido, consolidación parcial cada N capítulos, stop/resume) | [references/00-pipeline/book-mode.md](references/00-pipeline/book-mode.md) | `references/00-pipeline/architecture.md` (F106 orquesta sobre las 5 capas; §3.6); `scripts/pipeline/book_mode.py` (CLI 9 sub-comandos) | F106 |
| Procesar fuente por chunks con presupuesto acotado (ciclo leer→inventariar→ledger→NoteMark→validar→manifiesto, unidades cruzadas una sola vez, sin cargar el texto crudo fuera de L0) | [references/00-pipeline/chunk-loop.md](references/00-pipeline/chunk-loop.md) | `references/00-pipeline/book-mode.md` (F106 compone por capítulo; F107 por chunk dentro del capítulo o standalone); `scripts/pipeline/chunk_loop.py` (CLI 5 sub-comandos) | F107 |
| Detectar duplicados entre notas (canonical/alias/similarity) y aplicar merge/specialize/split preservando source_refs y redirigiendo enlaces entrantes | [references/03-knowledge/dedup.md](references/03-knowledge/dedup.md) | `scripts/authoring/transform.py` (F50; merge/split/dedup a nivel IR) + `scripts/dedup/apply.py` (orquestador F108 que invoca F50 + actualiza `manifest.json::link_debt[]`) | F108 |
