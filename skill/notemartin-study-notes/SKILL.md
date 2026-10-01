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
| Verificar el cierre de una nota contra el checklist consolidado por tipo (común + 15 bloques + reglas por perfil, orden cheap→expensive) | [references/10-quality/checklists-by-type.md](references/10-quality/checklists-by-type.md) | `references/05-note-types/<tipo>.md` §6.1/§6.2 (espejo local del archivo maestro); `evals/checklists-sample/run_eval.py` (verifica los 3 criterios del ROADMAP F112) | F112 |
| Ejecutar la suite de validadores sobre una nota / carpeta / workdir con shape JSON común, severidades error/warning/info y exit codes consistentes | [references/10-quality/validators.md](references/10-quality/validators.md) | `scripts/validate/<categoria>.py` (F113); `evals/validator-suite-sample/run_eval.py` (batería 3/3 PASS sobre 28 fixtures + 6 golden) | F113 |
| Auditar la fidelidad semántica del IR contra el SDM (forward source-check + content-fidelity + inverse sample, automatizado) | [references/10-quality/fidelity-audit.md](references/10-quality/fidelity-audit.md) | `scripts/audit/fidelity_audit.py` (F114); `evals/fidelity-audit-sample/run_eval.py` (batería 4/4 PASS) | F114 |
| Cerrar un trabajo con reporte (cobertura + validadores + degradaciones + rúbrica auto + deuda aceptada) y promover notas a `status: verified` si la puerta de calidad pasa | [references/10-quality/quality-gate.md](references/10-quality/quality-gate.md) | `scripts/quality_gate.py` (F115); `evals/quality-gate-sample/run_eval.py` (batería 5/5 PASS); `schemas/quality-gate.schema.json` | F115 |
| Diagnosticar un modo de fallo del pipeline (7 modos cerrados: OCR fallido / fuente ilegible / contexto agotado / API caída / validador en rojo repetido / conflicto irresoluble / interrupción) y aplicar la acción canónica | [references/14-operation/failure-modes.md](references/14-operation/failure-modes.md) | F106 BM-R2..R5b (interrupción); F107 CHK-R1..R5 (budget); F109 CON-R1..R5 (idempotencia); F111 INC-R1..R5 (no-borrado) | F116 |
| Diagnosticar el entorno antes de invocar cualquier script (qué deps faltan, qué se degrada sin ellas, exit codes 0/2/1/3) | [scripts/CHECKLIST.md](scripts/CHECKLIST.md) | `scripts/check_deps.py` (F117); `scripts/pkg/deps.yaml` (manifest); `scripts/README.md` (catálogo) | F117 |
| Inicializar / operar el modo obra completa de un libro (reconocimiento previo, estado compartido, consolidación parcial cada N capítulos, stop/resume) | [references/00-pipeline/book-mode.md](references/00-pipeline/book-mode.md) | `references/00-pipeline/architecture.md` (F106 orquesta sobre las 5 capas; §3.6); `scripts/pipeline/book_mode.py` (CLI 9 sub-comandos) | F106 |
| Procesar fuente por chunks con presupuesto acotado (ciclo leer→inventariar→ledger→NoteMark→validar→manifiesto, unidades cruzadas una sola vez, sin cargar el texto crudo fuera de L0) | [references/00-pipeline/chunk-loop.md](references/00-pipeline/chunk-loop.md) | `references/00-pipeline/book-mode.md` (F106 compone por capítulo; F107 por chunk dentro del capítulo o standalone); `scripts/pipeline/chunk_loop.py` (CLI 5 sub-comandos) | F107 |
| Detectar duplicados entre notas (canonical/alias/similarity) y aplicar merge/specialize/split preservando source_refs y redirigiendo enlaces entrantes | [references/03-knowledge/dedup.md](references/03-knowledge/dedup.md) | `scripts/authoring/transform.py` (F50; merge/split/dedup a nivel IR) + `scripts/dedup/apply.py` (orquestador F108 que invoca F50 + actualiza `manifest.json::link_debt[]`) | F108 |
| Ejecutar los 5 pases de consolidación (link-debt, glossary, indices, cheatsheets, consistency) idempotentemente | [references/10-quality/consolidation-passes.md](references/10-quality/consolidation-passes.md) | `scripts/pipeline/book_mode.py` (F106 §7 consolidate lo invoca) + `scripts/dedup/detect.py` (F108 pase 5) | F109 |
| Generar el índice de obra (10 secciones canónicas con mapa Mermaid, glosario, cheatsheets, prácticas, erratas, progreso) | [references/05-note-types/index-moc-generator.md](references/05-note-types/index-moc-generator.md) | `scripts/pipeline/book_mode.py` (F106 consolidate) + `scripts/pipeline/consolidate.py` (F109 reports) + `scripts/pipeline/book_index.py` (generador) | F110 |
| Comparar SDM antiguo y nuevo, reprocesar solo lo afectado, generar `version-delta`, marcar obsoletos sin borrar, republicar selectivamente | [references/04-authoring/incremental-update.md](references/04-authoring/incremental-update.md) | `references/00-pipeline/manifest.md` §6 (F16 política MIGRATE dispara F111 cuando `hash_mismatch`); `scripts/diff/update.py` (orquestador); `references/05-note-types/version-delta.md` (F88; F111 genera instancias) | F111 |
| Redactar prosa en el idioma del perfil con primera aparición bilingüe + bloque de procedencia al pie (45 no-traducibles) | [references/06-writing/i18n-and-citation.md](references/06-writing/i18n-and-citation.md) | `references/04-authoring/properties.md` §5.13 (F47 norma el enum `language`; F101 norma cómo redactar según el valor) | F101 |
| Elegir el tipo de diagrama para una intención | `references/07-visual/diagram-catalog.md` | `references/04-authoring/` | F65 |
| Escribir un bloque Mermaid portable | `references/07-visual/mermaid-portable.md` | `references/08-render/` (la portabilidad es decisión de L3, no de L4) | F66 |
| Decidir entre diagrama monoespaciado, Mermaid o imagen | `references/07-visual/monospace-diagrams.md` | `references/08-render/` | F69 |
| Decidir si reconstruir un diagrama impreso o conservar la captura | `references/07-visual/reconstruction.md` | `references/08-render/` | F71 |
| Verificación de accesibilidad visual | `references/07-visual/accessibility.md` | `references/08-render/` | F71 |
| Uso de tokens visuales (color, tipografía, espaciado) | `references/07-visual/tokens.md` | `assets/tokens.json` (fuente única; `INV-14`); ningún archivo con colores literales | F72 |
| Mapear intención semántica a estilo por destino | `references/07-visual/style-mapping.md` | `assets/tokens.json` (F72) + tabla canónica en `scripts/util/style_mapping.py` (F73); los 6 renderers L4 consumen la tabla consolidada | F73 |
| Estilizar el snippet CSS para Obsidian | `assets/notemartin.css` | `assets/css-tokens.generated.css` (auto-generado por `scripts/render/css_from_tokens.py`); tokens en `assets/tokens.json` (F72); clases semánticas desde `scripts/util/style_mapping.py` (F73) | F74 |
| Definir cabecera visual por tipo de nota | `references/07-visual/note-templates.md` | `assets/tokens.json` (F72) + `scripts/util/style_mapping.py` (F73) + `assets/notemartin.css` (F74) + `scripts/render/_header.py` (F75) + los 15 archivos `references/05-note-types/*.md` (F78-F92) que instancian el patrón | F75 |
| Revisar densidad visual de una nota | `references/07-visual/density.md` | `scripts/validate/density_check.py` (F76) mide 8 reglas R1-R8; `references/04-authoring/depth-layers.md` (F51) y `references/04-authoring/inline-marks.md` (F46) son los wirings fuente | F76 |
| Verificar visualmente la nota en los 7 destinos | `evals/visual/` | 12 artefactos reales (4 destinos × 2 notas) + `visual_inspect.py` (valida overflow/truncado/ilegible) + `defects.md` (log de defectos) + `checklist.md` (12 entradas para 3 destinos externos) | F77 |
| Revisar densidad visual de una nota | `references/07-visual/density.md` | ninguno | [pendiente F76] |

### §5.3 · Rutas en `references/08-render/`, `09-study/`, `10-quality/`, `11-i18n/` y catálogo de scripts

| Situación | Archivo a leer | Archivos a NO leer | Fase |
|---|---|---|---|
| Verificar capacidad de un destino antes de renderizar | [capability-matrix.md](references/08-render/capability-matrix.md) | ninguno (es input de toda decisión L4) | F8 |
| Cualquier operación de renderizado | [contract.md](references/08-render/contract.md) | `references/04-authoring/` (no modificar IR después de validar) | F53 |
| Resolver enlaces entre notas según destino | `references/08-render/linking.md` | `references/04-authoring/` | [pendiente F61] |
| Publicación idempotente en destinos remotos | `references/08-render/publishing.md` | `references/03-knowledge/` | [pendiente F62] |
| Re-render o migración entre destinos | `references/08-render/migration.md` | `references/03-knowledge/`, `references/04-authoring/` (migrar no es re-redactar) | [pendiente F64] |
| Cualquier redacción de contenido fáctico | `references/10-quality/fidelity-rules.md` | `references/07-visual/` hasta cerrar el contenido | [pendiente F42] |
| Auditoría de no-pérdida antes de cerrar | `references/10-quality/completeness-audit.md` | `references/04-authoring/` (la auditoría no reescribe) | [pendiente F43] |
| Antes de cerrar una nota que requiere autoevaluación (cualquier `note-type` excepto `index-moc`) | [self-evaluation.md](references/09-study/self-evaluation.md) | ninguno (la fase lo define todo) | F102 |
| Al registrar un error propio o consultar el repaso vencido del registro | [error-log.md](references/09-study/error-log.md) | `references/04-authoring/` (no se reescribe el IR del error) | F103 |
| Al planificar una ruta de estudio (operar hoy / entender a fondo / repasar) | [study-paths.md](references/09-study/study-paths.md) | `references/03-knowledge/` (consultar grafo + note-plan) | F104 |
| Al configurar el perfil de objetivo (interview / certification / work) o consultar cobertura por objetivo | [goal-profiles.md](references/09-study/goal-profiles.md) | `references/04-authoring/` (sobrescribe el perfil global) | F105 |

> Las carpetas `references/09-study/` y `references/11-i18n/` se poblarán desde F102, F103, F104, F105 y F101 respectivamente; cada archivo que se cree en ellas se enruta desde §5 en el mismo commit. F102, F103, F104 y F105 publican los cuatro archivos de `09-study/` (`self-evaluation.md`, `error-log.md`, `study-paths.md` y `goal-profiles.md`). El catálogo exhaustivo de scripts se publica en `scripts/README.md` cuando F117 cierre; mientras tanto, §6 de este router lista los únicos scripts físicos del paquete.

## §6 · Catálogo de scripts invocables hoy

El catálogo exhaustivo vive en `scripts/README.md` `[pendiente F117]` y se materializa cuando esa fase corra. Mientras tanto, los únicos scripts físicos del paquete son:

| Ruta | Qué hace | Invocación | Dependencias |
|---|---|---|---|
| `scripts/util/build_probe_note.py` | Regenera `evals/probe/probe.nm` (la nota sonda que ejercita todas las capacidades de la matriz) | `python scripts/util/build_probe_note.py --out <ruta>` | Python 3.10+ sin dependencias externas |
| `scripts/util/sdm_cache.py` | F36: caché por hash con invalidación selectiva por `engine_version`; CLI `put/get/list/invalidate/info` y API `cache_get_or_compute`. Criterio 1 (reprocess no-repeat) + Criterio 2 (motor cambiado invalida solo esa rama) | `python scripts/util/sdm_cache.py put --step <s> --source-hash <h> --engine-version <ev> --value-file <f>` | Python 3.9+ stdlib |
| `scripts/util/sdm_view.py` | F36: visor HTML self-contained del SDM con jerarquía, conteos por tipo, histogramas de confianza, y filtros client-side (type, confidence ≥ threshold, low-confidence one-click) | `python scripts/util/sdm_view.py --sdm <sdm.json> --out <viewer.html>` | Python 3.9+ stdlib |
| `scripts/ingest/triage.py` | L0 preflight: clasifica fuente (PDF/EPUB/DOCX/PPTX/HTML/MD/TXT/repo) y emite `triage.json` + `triage.md` con plan por rangos | `python scripts/ingest/triage.py --source <ruta> --out-dir <dir>` | Python 3.9+ stdlib; PyYAML (recomendado); pypdf (opcional, mejora precisión) |
| `scripts/ingest/pdf_native.py` | L0 extracción de PDF nativo: runs de texto con bbox + fuente + tamaño; encabezados por tipografía; boilerplate posicional; outline | `python scripts/ingest/pdf_native.py --source <pdf> --out-dir <dir> [--plan <triage.json>]` | Python 3.9+ stdlib; pypdf >= 4 (obligatorio) |
| `scripts/ingest/preprocess.py` | L0 preprocesado de imagen: rasteriza PDF/PNG y aplica pipeline de 6 etapas (deskew, denoise, binarize, border, curvature opt-in). Preserva el original | `python scripts/ingest/preprocess.py --source <pdf|img|dir> --out-dir <dir> [--dpi 300] [--pipeline rasterize,deskew,denoise,binarize,border]` | Python 3.9+ stdlib; pypdfium2 >= 4; opencv-python-headless >= 4; Pillow >= 10; numpy >= 1.24 |
| `scripts/ingest/ocr.py` | L0 OCR multilingüe: Tesseract primario, EasyOCR alternativo, reintentos en cascada (invert, alternative_engine, sparse_psm) con `mean_conf < 0.70` | `python scripts/ingest/ocr.py --source <dir|img> --out-dir <dir> [--languages "spa+eng"] [--engine tesseract] [--user-words <path>]` | Python 3.9+ stdlib; pytesseract; Pillow; opencv-python-headless; numpy; Tesseract 5.x binario externo |
| `scripts/ingest/layout.py` | L0 layout y orden de lectura: detecta columnas, sidebars, margin notes, captions, floats; verifica orden; reunifica párrafos/tablas/código cross-page | `python scripts/ingest/layout.py --source <fragments.json\|ocr_summary.json> --out-dir <dir> [--json-only]` o `--pdf <pdf>` | Python 3.9+ stdlib; numpy (recomendado) |
| `scripts/ingest/regions.py` | L0 clasificación semántica de regiones (13 clases × 11 señales, ambigüedad marcada) | `python scripts/ingest/regions.py --source <layout_dir> --out-dir <dir> [--fragments <fragments.json>] [--ocr <ocr_summary.json>]` | Python 3.9+ stdlib |
| `scripts/ingest/tables.py` | L0 extracción de tablas (clusterización filas/columnas, merged cells, headers multinivel, cross-page merge) | `python scripts/ingest/tables.py --source <regions_dir> --out-dir <dir> [--fragments <fragments.json>]` | Python 3.9+ stdlib |
| `scripts/ingest/formulas.py` | L0 OCR de fórmulas (LaTeX, validador regex, pending fallback, numeración preservada) | `python scripts/ingest/formulas.py --source <regions_dir> --out-dir <dir> [--fragments <fragments.json>] [--images-dir <dir>]` | Python 3.9+ stdlib; Pillow opcional |
| `scripts/ingest/code_ocr.py` | L0 OCR de código y consolas (byte-exact, correcciones forzadas registradas, prompt/salida, low_confidence) | `python scripts/ingest/code_ocr.py --source <regions_dir> --out-dir <dir> [--fragments <fragments.json>]` | Python 3.9+ stdlib |
| `scripts/ingest/review_report.py` | Mixta: confianza por tipo de región, reporte HTML con `<img>`+`<pre>` lado a lado, bloqueo por regiones críticas, propagación de correcciones humanas | `python scripts/ingest/review_report.py --source <ingest_dir> --out-dir <dir> [--images-dir <dir>] [--corrections <corrections.json>]` | Python 3.9+ stdlib; Pillow opcional |
| `scripts/ingest/post_ocr.py` | Corrección post-OCR determinista (R001-R010 + diccionario, sin ML, sin tocar código/tabla, cada corrección revertible) | `python scripts/ingest/post_ocr.py --source <ingest_dir> --out-dir <dir> [--dictionary <dict.yaml>]` o `--revert <correction_id>` / `--revert-all` | Python 3.9+ stdlib |
| `scripts/ingest/other_formats.py` | EPUB (ebooklib), DOCX (python-docx), PPTX (python-pptx), SRT/VTT/JSON → `regions.json` con speaker_note + anchor_id temporal | `python scripts/ingest/other_formats.py --source <dir> --out-dir <dir> [--format auto]` | Python 3.9+ stdlib + ebooklib + python-docx + python-pptx opcionales |
| `scripts/ingest/web_docs.py` | Web docs multipágina (BFS desde índice, sin boilerplate, canonical_url profunda, robots.txt opcional, sin ML ni OCR) | `python scripts/ingest/web_docs.py --source <dir> --base-url <url> --out-dir <dir> [--index <path>]` | Python 3.9+ stdlib |
| `scripts/validate/ingest_check.py` | Núcleo: gate entre L0 y L1/L2 — verifica páginas omitidas, secciones del índice ausentes, saltos de numeración, bloques vacíos, densidad anómala; override humano explícito con `--allow-critical --human-decision` | `python scripts/validate/ingest_check.py --sdm <path> --out-dir <dir> [--declared-index <path>]` | Python 3.9+ stdlib |
| `scripts/validate/provenance.py` | F34: valida `source_provenance` (procedencia por campo), distinguibilidad read/inferred y gate `--require-version` (documentación sin versión ⇒ exit 1) | `python scripts/validate/provenance.py --sdm <path\|dir> [--require-version] [--min-confidence 0.7]` | Python 3.9+ stdlib |
| `scripts/ingest/build_sdm.py` | Núcleo L0→L1: ensambla regions/tables/formulas/code/web_docs/other_formats en `sdm.json` conforme a `sdm.schema.json`, asocia pies a figuras (`CAPTION_MAX_PAGES_AHEAD=1`), ids deterministas `sha1(hash+path+idx)[:12]`, emite `source_provenance` (F34) por campo | `python scripts/ingest/build_sdm.py --ingest-dir <dir> --source-meta <yaml> --out-dir <dir> [--format auto] [--check-determinism]` | Python 3.9+ stdlib; PyYAML (obligatorio) |
| `scripts/ingest/assets.py` | Post-F31: extrae imágenes del source (PDF pypdfium2 / EPUB ZIP), dedup por sha256 → nombre determinista `assets/<sid>/<sha256[:16]>.<ext>`, clasifica en `diagram_conceptual|screenshot|data_figure|decorative` (heurística Pillow + override YAML), valida alt text, actualiza `figure.content.src` en el SDM, emite `assets.json` + `assets_summary.json` | `python scripts/ingest/assets.py --sdm <path> --source-file <pdf\|epub> --out-dir <dir> [--out-sdm <path>] [--classify <yaml>]` | Python 3.9+ stdlib; Pillow ≥ 10 obligatorio; pypdfium2 ≥ 4 para PDF |
| `scripts/render/obsidian.py` | L4 renderer Obsidian 1.5+: admonition → callout nativo, collapsible → callout plegable (`+`/`-`), link-note → wikilink con alias, propiedades → YAML frontmatter, diagram → bloque Mermaid. Celdas combinadas → degradación elegante (fila 1 §6 contract F53). Dataview opt-in (`--enable-dataview`); por default se degrada a admonition estática para cumplir "sin ningún plugin" (criterio 1) | `python scripts/render/obsidian.py --ir <path> --profile <yaml> --out-dir <dir> [--enable-dataview]` | Python 3.9+ stdlib puro (parser YAML mínimo propio para `targets.obsidian.*`) |
| `scripts/render/notion_api.py` | L4 renderer Notion API: callout con icon+color, toggle, equation, code Mermaid, propiedades de database (con tipo correcto), mención de página, columnas. Troceo en chunks de 100 bloques/petición; 2 pasadas para anidamiento (≤2 niveles); reintentos con backoff 5s/30s/2m/10m ante 429/5xx; idempotencia por `notemartin_note_id` property (ADR-0010); `--dry-run` para testing sin token | `python scripts/render/notion_api.py --ir <path> --profile <yaml> --out-dir <dir> --notion-token <token> [--database-id <hex>] [--dry-run]` | Python 3.9+ stdlib puro (`urllib.request`) |
| `scripts/render/notion_md.py` | L4 renderer Notion import (Markdown limitado a subconjunto importer): admonition → blockquote con emoji prefijo, collapsible → `<details markdown="1">`, link-note → wikilink, propiedades → YAML frontmatter, diagram → Mermaid. Reporte incluye `vs_notion_api` por entrada + sección `cross_target_diff`. `--include-import-instructions` para guía UI | `python scripts/render/notion_md.py --ir <path> --profile <yaml> --out-dir <dir> [--include-import-instructions]` | Python 3.9+ stdlib puro |
| `scripts/render/appflowy.py` | L4 renderer AppFlowy: admonition → `> [!type]` (callout nativo con color), collapsible → `<details markdown="1">` (toggle), diagram Mermaid nativo (con `--pre-render-diagrams` activa F70 si existe), propiedades en YAML frontmatter. Reporte incluye `cross_target_diff` vs obsidian y vs notion_md | `python scripts/render/appflowy.py --ir <path> --profile <yaml> --out-dir <dir> [--pre-render-diagrams] [--include-import-instructions]` | Python 3.9+ stdlib puro |
| `scripts/render/markdown.py` | L4 renderer Markdown estándar (GFM, GitHub-compatible): admonition → blockquote con emoji + CSS class `callout-<severity>`, collapsible → `<details markdown="1">`, link-note → `[text](<id>.md)` (ruta relativa, criterio 3), propiedades → YAML frontmatter, diagram → ```mermaid + fallback imagen. Genera automáticamente `## Referenciado por` (fila 7 §6) y `## Consultas habituales` (fila 16 §6) | `python scripts/render/markdown.py --ir <path> --profile <yaml> --out-dir <dir> [--base-url <url>] [--pre-render-diagrams]` | Python 3.9+ stdlib puro |
| `scripts/render/html_pdf.py` | L4 renderer HTML y PDF: HTML5 autocontenido con `<style>` inline (sin recursos externos); callout `<aside class="callout-*">`, collapsible `<details>`, table con rowspan/colspan nativos, backlinks `<aside class="backlinks">`, queries `<section class="queries">`. PDF opcional vía weasyprint. Print CSS con `page-break-inside: avoid` para no partir tablas/código | `python scripts/render/html_pdf.py --ir <path> --profile <yaml> --out-dir <dir> [--no-pdf] [--print-instructions]` | Python 3.9+ stdlib puro; weasyprint opcional |
| `scripts/render/flashcards.py` | L4 renderer de repaso espaciado: extrae tarjetas solo de `question` o nodos con `is_atomic_card=true` (definition/formula/glossary-term/key-fact). Salida en 2 formatos: Obsidian Spaced Repetition plugin (`Pregunta:: Respuesta`) + Anki CSV (RFC 4180). Reglas: D1 solo atómicos, D2 una tarjeta un hecho (descarta si >2 cláusulas), D3 trazabilidad con `note_id`, D4 prohibido prosa narrativa | `python scripts/render/flashcards.py --ir <path> --profile <yaml> --out-dir <dir> [--max-clauses N] [--max-words N]` | Python 3.9+ stdlib puro |
| `scripts/render/linking.py` | F61 CLI orquestador de enlaces: invoca renderers, computa link debt, emite `reports/link_debt.json` y `linking-report.{json,md}`. Módulo compartido `_linking.py` con API `LinkTarget/LinkReport/LinkGraph/resolve_links` | `python scripts/render/linking.py --ir <path> --out-dir <dir> --profile <yaml> [--renderers csv] [--pass1-only|--pass2-only]` | Python 3.9+ stdlib puro |
| `scripts/publish/publishing.py` | F62 CLI de publicación idempotente con 4 sub-comandos (plan/publish/status/mark-edited); manifest por destino con detección de ediciones manuales por hash y preservación de comentarios via `<!-- user-content -->` | `python scripts/publish/publishing.py plan|publish|status|mark-edited --ir <path> --out-dir <dir> [--destinations csv]` | Python 3.9+ stdlib puro |
| `scripts/validate/cross_target.py` | F63 validación cross-target: extrae texto canónico del IR, lo busca en artifacts renderizados por cada destino, y verifica que toda unidad aparezca en el artifact o esté cubierta por una degradación declarada en `reports/render-degradation.json` | `python scripts/validate/cross_target.py --ir <path> --out-dir <dir> [--destinations csv]` | Python 3.9+ stdlib puro |
| `scripts/render/migrate.py` | F64 CLI de migración entre destinos: re-render desde IRs persistidos sin re-ingestar la fuente (3 sub-comandos: re-render, reverse-import, diff-capabilities); invoca el renderer del destino y emite migration-report con gains/losses por capacidad | `python scripts/render/migrate.py re-render|reverse-import|diff-capabilities [args]` | Python 3.9+ stdlib puro |
| `scripts/validate/mermaid.py` | F67 validador de diagramas Mermaid: extrae bloques `:::diagram` y valida 20 reglas (S-01..S-08 sintaxis, P-01..P-06 portabilidad F66 §5, L-01..L-06 legibilidad F65 §6). Reporte JSON+Markdown con archivo/nodo/regla/severidad. CLI `--source\|--glob`, `--out-dir`, `--severity`, `--fail-on`, `--max-nodes`, `--max-label-len`, `--include-types` | `python scripts/validate/mermaid.py --source <path> [--out-dir <dir>] [--severity info\|warning\|error] [--fail-on error] [--json]` | Python 3.9+ stdlib puro |
| `scripts/render/diagram_image.py` | F68 pre-renderizado de diagramas Mermaid a SVG/PNG vía `mmdc` (Mermaid CLI). Extrae bloques `:::diagram`, hashea por (código+theme+format+ir_sha256), consulta caché determinista, renderiza. Tema claro/oscuro (light default, `both` para ambos). Formato svg/png/both. Fallback `native_mermaid` cuando `mmdc` no disponible (criterio D-01); código fuente plegable siempre en manifest (criterio 3 F68). CLI `--source\|--glob`, `--out-dir`, `--cache-dir`, `--theme`, `--format`, `--mmdc`, `--no-fallback`, `--force`, `--cache-clear`. Invocado automáticamente desde appflowy/markdown/html_pdf con `--pre-render-diagrams` | `python scripts/render/diagram_image.py --source <path> --out-dir <dir> --cache-dir <dir> [--theme light\|dark\|both] [--format svg\|png\|both] [--no-fallback] [--force]` | Python 3.9+ stdlib puro + mmdc opcional |
| `scripts/render/make_figure.py` | F70 generador de figuras de datos en SVG (bar, line, heatmap, confusion_matrix, distribution, before_after). Paleta Okabe-Ito colorblind-safe (verificada con ΔE CIEL76 ≥ 20 entre pares adyacentes), ejes neutros grises que no compiten con series, fondo transparente/tema claro/oscuro, alt text auto-generado. Valida `source_refs` no vacío por serie (INV-04, criterio 3 F70) con `--allow-missing-refs` opcional. CLI `--input`/`--input-dir`, `--out-dir`, `--theme`, `--format`, `--width`, `--height`, `--allow-missing-refs`, `--fail-on`, `--json` | `python scripts/render/make_figure.py --input <spec.json> --out-dir <dir> [--theme light\|dark] [--allow-missing-refs]` | Python 3.9+ stdlib puro |
| `scripts/util/tokens.py` | F72 loader de design tokens: lee `assets/tokens.json` (la fuente única de color/tipografía/espaciado per `INV-14`), valida `$version` semver y expone `load_tokens()`, `resolve_token(t, category, name, mode, field)`, `resolve_series(t, name, mode)`, `warn_if_unsupported_major(version)`. Usado por `scripts/render/make_figure.py` (Okabe-Ito + ejes), `scripts/validate/contrast_check.py` (verificación WCAG), y los renderers L4 que necesiten tokens en F73/F74. CLI `--dump` (imprime el JSON), `--resolve CATEGORY NAME [MODE] [FIELD]` (imprime el hex resuelto) | `python -m scripts.util.tokens --dump` o `--resolve semantic info light fgOnBg` | Python 3.9+ stdlib puro |
| `scripts/validate/contrast_check.py` | F72 verificador WCAG 2.1 sobre `semantic.*` (9 tokens × 2 modos = 18 pares). Calcula ratio entre `fgOnBg` y `bg` con la fórmula WCAG (linealización sRGB + luminancia relativa 0.2126 R + 0.7152 G + 0.0722 B), exige mínimo (4.5:1 AA por defecto, ajustable con `--min-ratio`). Salida Markdown (default) o JSON (`--json`). Exit codes: 0 PASS, 1 algún par falla, 2 archivo no encontrado / JSON inválido | `python scripts/validate/contrast_check.py --tokens <path> --min-ratio 4.5 --mode both` | Python 3.9+ stdlib puro |
| `scripts/util/style_mapping.py` | F73 tabla canónica `severidad → estilo por destino`: 20 severidades × 7 campos (semantic_token + icon + obsidian_callout + notion_icon + notion_color + appflowy_callout + html_css_class). Valida al import (20 entradas, Notion color ∈ lista cerrada de 10, sin campos vacíos). Consumida por los 6 renderers L4 (`obsidian.py`, `notion_api.py`, `notion_md.py`, `appflowy.py`, `markdown.py`, `html_pdf.py`); elimina sus dicts `SEVERITY_TO_*` locales. Expone `icon_for`, `obsidian_callout_for`, `notion_callout_for` (→ `(icon, color)`), `appflowy_callout_for`, `html_css_class_for`, `semantic_token_for`, `all_mappings`. CLI `--dump` (JSON con los 20 mappings) y `--resolve SEVERITY` (un mapping) | `python -m scripts.util.style_mapping --dump` o `--resolve warning` | Python 3.9+ stdlib puro |
| `scripts/render/css_from_tokens.py` | F74 generador de CSS variables desde `assets/tokens.json`: produce `assets/css-tokens.generated.css` con `:root` (light) + `@media (prefers-color-scheme: dark)` y los alias typography/spacing/radii mode-agnostic. Naming convention: `semantic.<name>.<field>` → `--semantic-<name>-<field>`, `_neutral.<name>` → `--_neutral-<name>`, etc. Carga tokens vía `scripts/util/tokens.py` (F72); valida `$version`; advertencia si major > 1 sin abortar. CLI `--out <path>` (default `assets/css-tokens.generated.css`), `--check` (exit 0 si al día, 1 si drift), `--print` (stdout) | `python3 -m scripts.render.css_from_tokens --out <path>` o `--check` | Python 3.9+ stdlib puro |
| `scripts/render/_header.py` | F75 helper `## Cabecera`: emite el bloque de cabecera (5 campos canónicos: Resumen, Procedencia, Versión, Estado, Tiempo de lectura) en 7 formatos distintos según `dest`: callout nativo para Obsidian/AppFlowy/Notion API, tabla GFM para notion_md/markdown, `<table>` HTML para html_pdf, tupla `(anverso, reverso)` para flashcards (sin bloque visible; hint en reverso). Consumido por los 7 renderers L4. Valida `SUPPORTED_DESTS` cubre los 7 destinos. Sin literales de color. CLI: API Python únicamente, no CLI | `python3 -c "from scripts.render._header import emit_cabecera; print(emit_cabecera({'summary': 'x', 'status': 'published'}, dest='obsidian'))"` | Python 3.9+ stdlib puro |
| `scripts/validate/density_check.py` | F76 verificador de densidad y jerarquía: lee una nota NoteMark (`.md`) o un directorio, parsea bloques por sección H2/H3, y mide las 8 reglas R1-R8 (max párrafo L1 ≤ 60 palabras, max párrafo L2 ≤ 200, ≥ 1 anclaje por 200 palabras, ≤ 3 callouts consecutivos, ≤ 5 viñetas consecutivas, sección ≥ 1 estructura, L3 plegable si > 100 líneas, densidad `{src:}` ≥ 0.80). Exenciones: glossary-term (R3+R6), cheatsheet (R3+R5+R6), index-moc (R3+R5+R6). CLI `--note <path>`, `--notes <dir>`, `--json`, `--strict`, `--allow-violations R2,R5`. Exit 0 sin violaciones; 1 con violaciones; 2 error de uso | `python3 scripts/validate/density_check.py --note <path> [--json] [--strict]` | Python 3.9+ stdlib puro |
| `evals/visual/run_eval.py` | F77 eval visual: 5 sub-criterios (C1 notas fuente + sha256, C2 12 artefactos válidos, C3 45 vars semánticas en light+dark, C4 visual_inspect.py exit 0 o issues documentados, C5 checklist 12 entradas). Verifica los 3 criterios del ROADMAP §1498-1500: capturas en 7 destinos / no contenido cortado / defectos corregidos o asignados | `python3 evals/visual/run_eval.py` | Python 3.9+ stdlib puro |
| `evals/visual/visual_inspect.py` | F77 inspector de artefactos: lee los 12 artefactos en `artifacts/` y detecta líneas > 200 chars, tablas 10+ cols sin wrapper, links rotos, marcas `{src:}` no canónicas, HTML sin cerrar, `<th>` sin scope (a11y WCAG 1.3.1), SVG sin `<title>` o viewBox, CSV con > 5 clauses. CLI `--artifacts-dir <dir>`, `--json`, `--strict`. Exit 0 sin issues; 1 con issues; 2 error de uso | `python3 evals/visual/visual_inspect.py --artifacts-dir evals/visual/artifacts` | Python 3.9+ stdlib puro |

### §6.1 · Suite de evals de la skill (F118) — **no la invoca el agente**

La suite de evaluación de la skill vive en `evals/suite/` y la opera un **evaluador** (humano o proceso externo), **no el agente**. El agente no carga estos archivos en su contexto y no los invoca durante el procesamiento de fuentes. Sirven para medir si la skill cumple su contrato sobre prompts realistas del corpus (F6).

| Ruta | Qué hace | Invocación | Dependencias |
|---|---|---|---|
| `evals/suite/runner/run_case.py` | Lanza un caso: ejecuta el agente con el prompt del YAML o en modo dry-run; captura stdout + workdir; vuelca `skill_fingerprint.json` | `python3 evals/suite/runner/run_case.py --case <yaml> --run-id <id> [--agent-command <cmd>] [--dry-run]` | Python 3.9+ stdlib + PyYAML |
| `evals/suite/runner/check_assertions.py` | Evalúa las aserciones automáticas declaradas en el caso (tipos: `param_table_coverage`, `ledger_coverage`, `ir_validation`, `sdm_validation`, `ocr_code_fidelity`, `fidelity_audit`, `manifest_valid`) y vuelca `assertions.json` | `python3 evals/suite/runner/check_assertions.py --case <yaml> --run-dir <path>` | Python 3.9+ stdlib + PyYAML + invocación de `scripts/util/validate_*.py` |
| `evals/suite/runner/build_canonical.py` | Genera `param_table_canonical` desde el HTML de muestra del corpus (extrae `<dl class="variablelist">` y asigna sección por h3 previo) | `python3 evals/suite/runner/build_canonical.py --card <md> --sample <html> --out <yaml>` | Python 3.9+ stdlib + PyYAML opcional |
| `evals/suite/runner/apply_rubric.py` | Genera plantilla `human.json` por caso con las 8 dimensiones de `evals/rubric.md` + pesos y mínimos por perfil; incluye `compute_global()` | `python3 evals/suite/runner/apply_rubric.py --case <yaml> --rubric <md> --out <json>` | Python 3.9+ stdlib + PyYAML |
| `evals/suite/runner/compare_runs.py` | Diff entre dos runs (`runs/<run-A>` vs `runs/<run-B>`): cambios de skill_fingerprint, casos añadidos/eliminados, aserciones que cambian pass/fail, scores humanos por dimensión | `python3 evals/suite/runner/compare_runs.py <run-A> <run-B> [--markdown]` | Python 3.9+ stdlib puro |
| `evals/suite/runner/drive_suite.py` | Lanza los 6 casos de la suite y agrega `report.json` | `python3 evals/suite/runner/drive_suite.py --run-id <id> [--agent-command <cmd>] [--dry-run]` | Python 3.9+ stdlib |

Contrato y casos en `evals/suite/SCHEMA.md`, `evals/suite/cases/*.yaml` y `evals/suite/rubric-application.md`. Comparabilidad entre iteraciones de la skill cerrada por C4 (F118) — ver `compare_runs.py` y `runs/<run-id>/skill_fingerprint.json`.

### §6.2 · Regresión y varianza (F119) — **no la invoca el agente**

Set de regresión y medición de varianza. La opera el evaluador (humano o proceso externo), no el agente. Ejecuta N veces cada caso del set, mide varianza sobre 5 métricas, y bloquea un release cuando una métrica cae fuera de umbral.

| Ruta | Qué hace | Invocación | Dependencias |
|---|---|---|---|
| `evals/suite/runner/run_regression.py` | Ejecuta N veces cada caso del set de regresión (default 5), mide 5 métricas (`coverage_must_keep_terminal`, `notes_planned`, `ir_node_count`, `human_global_avg`, `approved_rate`), compara contra umbrales, emite `variance.json` | `python3 evals/suite/runner/run_regression.py --case-dir evals/regression/cases/ --release-tag <tag> --out-dir <dir> [--agent-command <cmd>] [--dry-run] [--n-runs N]` | Python 3.9+ stdlib + PyYAML + invocación de `run_case.py` / `check_assertions.py` / `apply_rubric.py` (F118) |
| `evals/suite/runner/release_gate.py` | Evalúa las 4 condiciones del gate (variance_within_threshold + no_blocking_failures + no_regression_flip + no_human_pending) y emite `gate.json` | `python3 evals/suite/runner/release_gate.py --candidate <report.json> --baseline <report.json> --variance <variance.json> [--regression-set SET.md] --out <gate.json>` | Python 3.9+ stdlib puro + invocación de `compare_runs.py` (F118) |

Set, spec normativa y umbrales en `evals/regression/{README,SET,variance}.md` y `variance_thresholds.yaml`. Proceso de release (6 pasos + evidencia de no-regresión) en `docs/release.md`.

### §6.3 · Ejemplos end-to-end (F120) — **no la invoca el agente**

Cuatro ejemplos end-to-end que demuestran la cadena L0-L4 sobre el corpus. Los produce un orquestador a partir de los scripts del paquete. Sirven como referencia verificable (artefactos commiteados) de cómo se ven las salidas en los 3 destinos ricos + 2 bonus.

| Ruta | Qué hace | Invocación | Dependencias |
|---|---|---|---|
| `examples/build_examples.py` | Regenera los 4 ejemplos: copia/ensambla SDM+ledger+IR sintéticos, ejecuta los 7 renderers L4 (F54-F59 + F60), genera reportes de calidad | `python3 examples/build_examples.py [--example <id>] [--all] [--real-captures]` | Python 3.9+ stdlib + PyYAML + invocación de `scripts/render/*.py` y `scripts/util/validate_*.py` |
| `examples/capture.py` | Genera capturas SVG sintéticas por destino (con placeholders Jinja-like) + PNG opcional con Playwright/cairosvg | `python3 examples/capture.py --render-dir <dir> --note-id <id> [--real-captures]` | Python 3.9+ stdlib puro + opcional Playwright/cairosvg |

Estructura por ejemplo en `examples/SCHEMA.md` (artifacts/ + render/<dest>/ + reports/ + 5 capturas SVG por destino). Caso 13 reutiliza el fixture sintético `evals/preprocess-sample/fixtures/hostile-scan.png` porque la muestra del corpus 13 sigue pendiente por F6; el README del ejemplo documenta cómo swap cuando llegue.

Cualquier otra acción ejecutable prevista por el pipeline (validación, parseo NoteMark, otros renderers F55-F60, publicación) sigue marcada `[pendiente Fxxx]` en `docs/skill-anatomy.md` §6. El agente **no inventa** invocaciones; cuando la fase que materializa el script cierre, esa fila entra en `scripts/README.md` y se cita desde §5.

## §7 · Modos de operación

Cinco modos, cada uno con qué capas toca, presupuesto simultáneo de `references/` (per `docs/skill-anatomy.md` §7.2 Tabla B) y criterio de parada. El modo se elige al inicio de la sesión y se mantiene hasta cerrar.

### §7.1 · Nota rápida

Toca **L1, L2, L3, L4**. Presupuesto: **4 archivos** simultáneos de `references/`. Disparador: una pregunta suelta o un único concepto nuevo que el usuario quiere convertir en nota enlazable. Criterio de parada: nota en NoteMark parseada al IR sin errores y publicada en al menos un destino activo. Detalle operativo: §7.2 Tabla B.

### §7.2 · Capítulo

Toca **L0, L1, L2, L3, L4**. Presupuesto: **6 archivos**. Disparador: el usuario entrega un capítulo (PDF, EPUB, Markdown numerado) y pide procesarlo completo. Criterio de parada: cobertura 100 % de unidades `must-keep` del capítulo con estado terminal en el ledger (`INV-08`). Detalle operativo: §7.2 Tabla B.

### §7.3 · Obra completa

Toca **L0, L1, L2, L3, L4**. Presupuesto: **6 archivos**. Disparador: el usuario entrega un libro entero (o un documento multiparte con manifiesto) y pide procesarlo. Criterio de parada: mismo que §7.2 más cierre del `manifest.json` con hash de fuente registrado. Detalle operativo: §7.2 Tabla B.

### §7.4 · Actualización incremental

Toca **L1, L2, L3, L4** (no re-ingesta; la fuente ya está en `sdm.json`). Presupuesto: **4 archivos**. Disparador: el hash de fuente cambió (F16 dispara acción explícita) **o** el usuario pidió ampliar/corregir notas existentes. Criterio de parada: ledger actualizado, IR revalidado, destinos republicados idempotentemente. Detalle operativo: §7.2 Tabla B.

### §7.5 · Re-render a otro destino

Toca **solo L4**. Presupuesto: **2 archivos**. Disparador: el IR ya está validado y el usuario pide publicar (o republicar) en un destino distinto o adicional. Criterio de parada: `render/<destino>/` poblado para cada destino activo y `reports/render-degradation.md` sin pérdidas fácticas. Detalle operativo: §7.2 Tabla B.

## §8 · Lo que la skill prohíbe explícitamente

Tres reglas que el agente lee en cada invocación. Refuerzan los invariantes de §2 y los enumera `AGENT.md` §14.

- **No escribas Markdown de destino ni JSON de IR a mano.** Escribe NoteMark; deja que el parser (`scripts/authoring/parse_notemark.py`, F48) y los renderers traduzcan. Saltarse esto rompe todos los destinos no-Obsidian en silencio (`INV-05`).
- **No embebas en `SKILL.md` plantillas, gramáticas, catálogos ni tablas de degradación.** Este archivo solo enruta. El detalle vive en `references/`. Si una sección se acerca a 30 líneas y es contenido N3, se mueve a `references/` (`INV-02`).
- **No omitas unidades `must-keep` por prisa, peso o estilo.** La puerta de fidelidad no se salta en ningún modo (`INV-08`). Si la fuente no da la cobertura, la nota lo dice; no se rellena con conocimiento propio (`INV-03`, `INV-17`).

## §9 · Cómo cerrar sesión

Tres comprobaciones que cualquier sesión que toque este archivo debe ejecutar antes de cerrar:

- **Enrutado vigente.** Si tocaste `references/`, verifica que la fila correspondiente de §5 sigue siendo correcta. Si el archivo se ha materializado, retira la marca `[pendiente Fxxx]`; si creaste un archivo nuevo en `references/` no previsto en `docs/skill-anatomy.md` §6, añade su fila en §5 en el mismo commit.
- **Catálogo de scripts vigente.** Si tocaste `scripts/`, actualiza §6 (hoy una sola fila) o, si F117 ya cerró, edita `scripts/README.md` en su lugar.
- **Presupuesto de líneas.** `wc -l SKILL.md` debe seguir ≤ 500. Si se acerca (≥ 450), añade jerarquía en `references/`, **no** se comprime la prosa (`INV-02`).