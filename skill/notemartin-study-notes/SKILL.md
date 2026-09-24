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
├─ HTML multipágina → scripts/ingest/web_docs.py                         [pendiente F29]
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
| Cualquier consulta al SDM o a sus anclas | `references/02-source-model/spec.md` | `references/04-authoring/` (no redactar antes de tener SDM) | [pendiente F13] |
| Documento sin numeración o con numeración inconsistente | `references/02-source-model/anchors.md` | `references/03-knowledge/` (las anclas son prerrequisito del ledger) | [pendiente F32] |
| Extracción de metadatos editoriales de la fuente | `references/02-source-model/provenance.md` | `references/04-authoring/` | [pendiente F34] |
| Clasificación de regiones editoriales (Nota, Precaución, Ejemplo) | `references/02-source-model/editorial-semantics.md` | `references/03-knowledge/` | [pendiente F35] |
| Extracción de unidades de información en L2 | `references/03-knowledge/information-units.md` | `references/04-authoring/` (no decidir tipo de nota antes de tener unidades) | [pendiente F37] |
| Cualquier operación sobre el Coverage Ledger | `references/03-knowledge/ledger.md` | `references/04-authoring/`, `references/05-note-types/` | [pendiente F15] |
| Construcción del grafo de prerrequisitos | `references/03-knowledge/concept-graph.md` | `references/04-authoring/` | [pendiente F39] |
| Resolución de términos canónicos y colisiones | `references/03-knowledge/terminology.md` | `references/04-authoring/` | [pendiente F40] |
| Detección de contradicciones u obsolescencia | `references/03-knowledge/conflicts.md` | `references/04-authoring/` | [pendiente F41] |
| División del trabajo en notas (Note Plan) | `references/03-knowledge/note-plan.md` | `references/04-authoring/` hasta cerrar el plan | [pendiente F44] |
| Redacción de cualquier nota en NoteMark | `references/04-authoring/notemark.md` | el resto de `references/04-authoring/` (directivas/marcas/propiedades están cubiertos aquí) | [pendiente F12] |
| Validación del IR o consulta del catálogo de nodos | `references/04-authoring/ir-spec.md` | `references/05-note-types/` (el catálogo de tipos decide qué nodos usar, no al revés) | [pendiente F14] |
| Elección de directiva de bloque NoteMark | `references/04-authoring/block-directives.md` | `references/05-note-types/` (las plantillas fijan directivas por tipo) | [pendiente F45] |
| Inserción de marcas inline en redacción | `references/04-authoring/inline-marks.md` | ninguno | [pendiente F46] |
| Definición de propiedades YAML de una nota | `references/04-authoring/properties.md` | `references/05-note-types/` | [pendiente F47] |
| Definir capas L1, L2, L3 de una nota | `references/04-authoring/depth-layers.md` | `references/05-note-types/` | [pendiente F51] |
| Seleccionar el tipo de nota `concept` | `references/05-note-types/concept.md` | los otros 14 archivos de `references/05-note-types/` | [pendiente F78] |
| Seleccionar el tipo de nota `api-reference` | `references/05-note-types/api-reference.md` | los otros 14 archivos de `references/05-note-types/` | [pendiente F79] |
| Seleccionar el tipo de nota `procedure` | `references/05-note-types/procedure.md` | los otros 14 archivos de `references/05-note-types/` | [pendiente F80] |
| Seleccionar el tipo de nota `configuration` | `references/05-note-types/configuration.md` | los otros 14 archivos de `references/05-note-types/` | [pendiente F81] |
| Seleccionar el tipo de nota `error-troubleshooting` | `references/05-note-types/error-troubleshooting.md` | los otros 14 archivos de `references/05-note-types/` | [pendiente F82] |
| Seleccionar el tipo de nota `architecture` | `references/05-note-types/architecture.md` | los otros 14 archivos de `references/05-note-types/` | [pendiente F83] |
| Seleccionar el tipo de nota `syntax` | `references/05-note-types/syntax.md` | los otros 14 archivos de `references/05-note-types/` | [pendiente F84] |
| Seleccionar el tipo de nota `data-model` | `references/05-note-types/data-model.md` | los otros 14 archivos de `references/05-note-types/` | [pendiente F85] |
| Seleccionar el tipo de nota `chapter-digest` | `references/05-note-types/chapter-digest.md` | los otros 14 archivos de `references/05-note-types/` | [pendiente F86] |
| Seleccionar el tipo de nota `comparison` | `references/05-note-types/comparison.md` | los otros 14 archivos de `references/05-note-types/` | [pendiente F87] |
| Seleccionar el tipo de nota `version-delta` | `references/05-note-types/version-delta.md` | los otros 14 archivos de `references/05-note-types/` | [pendiente F88] |
| Seleccionar el tipo de nota `glossary-term` | `references/05-note-types/glossary-term.md` | los otros 14 archivos de `references/05-note-types/` | [pendiente F89] |
| Seleccionar el tipo de nota `cheatsheet` | `references/05-note-types/cheatsheet.md` | los otros 14 archivos de `references/05-note-types/` | [pendiente F90] |
| Seleccionar el tipo de nota `index-moc` | `references/05-note-types/index-moc.md` | los otros 14 archivos de `references/05-note-types/` | [pendiente F91] |
| Seleccionar el tipo de nota `practice` o lab | `references/05-note-types/practice.md` | los otros 14 archivos de `references/05-note-types/` | [pendiente F92] |
| Elegir el tipo de diagrama para una intención | `references/07-visual/diagram-catalog.md` | `references/04-authoring/` | [pendiente F65] |
| Escribir un bloque Mermaid portable | `references/07-visual/mermaid-portable.md` | `references/08-render/` (la portabilidad es decisión de L3, no de L4) | [pendiente F66] |
| Decidir entre diagrama monoespaciado, Mermaid o imagen | `references/07-visual/monospace-diagrams.md` | `references/08-render/` | [pendiente F69] |
| Decidir si reconstruir un diagrama impreso o conservar la captura | `references/07-visual/reconstruction.md` | `references/08-render/` | [pendiente F71] |
| Verificación de accesibilidad visual | `references/07-visual/accessibility.md` | `references/08-render/` | [pendiente F71] |
| Uso de tokens visuales (color, tipografía, espaciado) | `references/07-visual/tokens.md` | ningún archivo con colores literales (per `INV-14`) | [pendiente F72] |
| Mapear intención semántica a estilo por destino | `references/07-visual/style-mapping.md` | `references/08-render/contract.md` (el contrato va después) | [pendiente F73] |
| Definir cabecera visual por tipo de nota | `references/07-visual/note-templates.md` | `references/05-note-types/` (la cabecera se decide tras el tipo) | [pendiente F75] |
| Revisar densidad visual de una nota | `references/07-visual/density.md` | ninguno | [pendiente F76] |

### §5.3 · Rutas en `references/08-render/`, `09-study/`, `10-quality/`, `11-i18n/` y catálogo de scripts

| Situación | Archivo a leer | Archivos a NO leer | Fase |
|---|---|---|---|
| Verificar capacidad de un destino antes de renderizar | [capability-matrix.md](references/08-render/capability-matrix.md) | ninguno (es input de toda decisión L4) | F8 |
| Cualquier operación de renderizado | `references/08-render/contract.md` | `references/04-authoring/` (no modificar IR después de validar) | [pendiente F53] |
| Resolver enlaces entre notas según destino | `references/08-render/linking.md` | `references/04-authoring/` | [pendiente F61] |
| Publicación idempotente en destinos remotos | `references/08-render/publishing.md` | `references/03-knowledge/` | [pendiente F62] |
| Re-render o migración entre destinos | `references/08-render/migration.md` | `references/03-knowledge/`, `references/04-authoring/` (migrar no es re-redactar) | [pendiente F64] |
| Cualquier redacción de contenido fáctico | `references/10-quality/fidelity-rules.md` | `references/07-visual/` hasta cerrar el contenido | [pendiente F42] |
| Auditoría de no-pérdida antes de cerrar | `references/10-quality/completeness-audit.md` | `references/04-authoring/` (la auditoría no reescribe) | [pendiente F43] |

> Las carpetas `references/09-study/` y `references/11-i18n/` se poblarán desde F60 y F101 respectivamente; cada archivo que se cree en ellas se enruta desde §5 en el mismo commit. El catálogo exhaustivo de scripts se publica en `scripts/README.md` cuando F117 cierre; mientras tanto, §6 de este router lista los únicos scripts físicos del paquete.

## §6 · Catálogo de scripts invocables hoy

El catálogo exhaustivo vive en `scripts/README.md` `[pendiente F117]` y se materializa cuando esa fase corra. Mientras tanto, los únicos scripts físicos del paquete son:

| Ruta | Qué hace | Invocación | Dependencias |
|---|---|---|---|
| `scripts/util/build_probe_note.py` | Regenera `evals/probe/probe.nm` (la nota sonda que ejercita todas las capacidades de la matriz) | `python scripts/util/build_probe_note.py --out <ruta>` | Python 3.10+ sin dependencias externas |
| `scripts/ingest/triage.py` | L0 preflight: clasifica fuente (PDF/EPUB/DOCX/PPTX/HTML/MD/TXT/repo) y emite `triage.json` + `triage.md` con plan por rangos | `python scripts/ingest/triage.py --source <ruta> --out-dir <dir>` | Python 3.9+ stdlib; PyYAML (recomendado); pypdf (opcional, mejora precisión) |
| `scripts/ingest/pdf_native.py` | L0 extracción de PDF nativo: runs de texto con bbox + fuente + tamaño; encabezados por tipografía; boilerplate posicional; outline | `python scripts/ingest/pdf_native.py --source <pdf> --out-dir <dir> [--plan <triage.json>]` | Python 3.9+ stdlib; pypdf >= 4 (obligatorio) |
| `scripts/ingest/preprocess.py` | L0 preprocesado de imagen: rasteriza PDF/PNG y aplica pipeline de 6 etapas (deskew, denoise, binarize, border, curvature opt-in). Preserva el original | `python scripts/ingest/preprocess.py --source <pdf|img|dir> --out-dir <dir> [--dpi 300] [--pipeline rasterize,deskew,denoise,binarize,border]` | Python 3.9+ stdlib; pypdfium2 >= 4; opencv-python-headless >= 4; Pillow >= 10; numpy >= 1.24 |
| `scripts/ingest/ocr.py` | L0 OCR multilingüe: Tesseract primario, EasyOCR alternativo, reintentos en cascada (invert, alternative_engine, sparse_psm) con `mean_conf < 0.70` | `python scripts/ingest/ocr.py --source <dir|img> --out-dir <dir> [--languages "spa+eng"] [--engine tesseract] [--user-words <path>]` | Python 3.9+ stdlib; pytesseract; Pillow; opencv-python-headless; numpy; Tesseract 5.x binario externo |
| `scripts/ingest/layout.py` | L0 layout y orden de lectura: detecta columnas, sidebars, margin notes, captions, floats; verifica orden; reunifica párrafos/tablas/código cross-page | `python scripts/ingest/layout.py --source <fragments.json\|ocr_summary.json> --out-dir <dir> [--json-only]` o `--pdf <pdf>` | Python 3.9+ stdlib; numpy (recomendado) |
| `scripts/ingest/regions.py` | L0 clasificación semántica de regiones (13 clases × 11 señales, ambigüedad marcada) | `python scripts/ingest/regions.py --source <layout_dir> --out-dir <dir> [--fragments <fragments.json>] [--ocr <ocr_summary.json>]` | Python 3.9+ stdlib |
| `scripts/ingest/tables.py` | L0 extracción de tablas (clusterización filas/columnas, merged cells, headers multinivel, cross-page merge) | `python scripts/ingest/tables.py --source <regions_dir> --out-dir <dir> [--fragments <fragments.json>]` | Python 3.9+ stdlib |
| `scripts/ingest/formulas.py` | L0 OCR de fórmulas (LaTeX, validador regex, pending fallback, numeración preservada) | `python scripts/ingest/formulas.py --source <regions_dir> --out-dir <dir> [--fragments <fragments.json>] [--images-dir <dir>]` | Python 3.9+ stdlib; Pillow opcional |
| `scripts/ingest/code_ocr.py` | L0 OCR de código y consolas (byte-exact, correcciones forzadas registradas, prompt/salida, low_confidence) | `python scripts/ingest/code_ocr.py --source <regions_dir> --out-dir <dir> [--fragments <fragments.json>]` | Python 3.9+ stdlib |

Cualquier otra acción ejecutable prevista por el pipeline (ingesta, OCR, validación, parseo NoteMark, render, publicación) sigue marcada `[pendiente Fxxx]` en `docs/skill-anatomy.md` §6. El agente **no inventa** invocaciones; cuando la fase que materializa el script cierre, esa fila entra en `scripts/README.md` y se cita desde §5.

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

- **No escribas Markdown de destino ni JSON de IR a mano.** Escribe NoteMark; deja que el parser (`scripts/authoring/parse_notemark.py` `[pendiente F48]`) y los renderers traduzcan. Saltarse esto rompe todos los destinos no-Obsidian en silencio (`INV-05`).
- **No embebas en `SKILL.md` plantillas, gramáticas, catálogos ni tablas de degradación.** Este archivo solo enruta. El detalle vive en `references/`. Si una sección se acerca a 30 líneas y es contenido N3, se mueve a `references/` (`INV-02`).
- **No omitas unidades `must-keep` por prisa, peso o estilo.** La puerta de fidelidad no se salta en ningún modo (`INV-08`). Si la fuente no da la cobertura, la nota lo dice; no se rellena con conocimiento propio (`INV-03`, `INV-17`).

## §9 · Cómo cerrar sesión

Tres comprobaciones que cualquier sesión que toque este archivo debe ejecutar antes de cerrar:

- **Enrutado vigente.** Si tocaste `references/`, verifica que la fila correspondiente de §5 sigue siendo correcta. Si el archivo se ha materializado, retira la marca `[pendiente Fxxx]`; si creaste un archivo nuevo en `references/` no previsto en `docs/skill-anatomy.md` §6, añade su fila en §5 en el mismo commit.
- **Catálogo de scripts vigente.** Si tocaste `scripts/`, actualiza §6 (hoy una sola fila) o, si F117 ya cerró, edita `scripts/README.md` en su lugar.
- **Presupuesto de líneas.** `wc -l SKILL.md` debe seguir ≤ 500. Si se acerca (≥ 450), añade jerarquía en `references/`, **no** se comprime la prosa (`INV-02`).
