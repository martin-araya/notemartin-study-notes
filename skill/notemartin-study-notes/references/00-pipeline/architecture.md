# Arquitectura de capas y artefactos — `references/00-pipeline/architecture.md`

> Documento normativo de la Fase 4 del roadmap. Define las 5 capas como contratos cerrados de entrada/salida, fija el directorio de trabajo por fuente y establece el modo degradado con umbrales numéricos.
>
> Documentos complementarios: `skills/AGENT.md` §5 (resumen en una frase de las 5 capas + esqueleto del workdir — versión corta), `ROADMAP.md` §4 (diagrama Mermaid del flujo). Este doc los **referencia y completa**, no los repite.
>
> Enrutado desde N2: `docs/skill-anatomy.md` §6 fila `F4`. Doc hermano: `references/00-pipeline/responsibilities.md` (Fase 3, división agente/script y anti-patrones). Doc operativo: `references/14-operation/failure-modes.md` (Fase 116, catálogo de modos de fallo).

## Índice

1. [Propósito](#1-propósito) · 2. [Cuándo se aplica](#2-cuándo-se-aplica) · 3. [Las 5 capas](#3-las-5-capas--contrato-cerrado) · 4. [Directorio de trabajo](#4-directorio-de-trabajo-por-fuente) · 5. [Frontera de capa](#5-regla-de-la-frontera-de-capa) · 6. [Hash de fuente](#6-hash-de-fuente) · 7. [Perfil por capa](#7-perfil--campos-leídos-por-capa) · 8. [Modo degradado](#8-modo-degradado--umbrales-numéricos) · 9. [Puerta de fidelidad](#9-regla-dura--la-puerta-de-fidelidad) · 10. [Cómo verificar](#10-cómo-verificar-el-contrato-sobre-una-capa-nueva) · 11. [Cambios permitidos](#11-cambios-permitidos-sin-reabrir-fase-4)

## 1. Propósito

Fijar las 5 capas como **contratos cerrados de entrada/salida**, declarar el **directorio de trabajo completo** por fuente, y establecer el **modo degradado con umbrales numéricos**. Cualquier fase posterior que produzca o consuma un artefacto se atiene a este contrato.

**No es** el catálogo de scripts (`scripts/README.md`, F117), no es la anatomía (`docs/skill-anatomy.md`, F2), no es el SDM (F13). Los **esquemas JSON Schema** de cada artefacto los producen F11 (perfil), F13 (SDM), F14 (IR), F15 (ledger), F16 (manifest), etc. Este doc nombra los archivos y declara las reglas; no redefine los campos.

## 2. Cuándo se aplica

- Al implementar una fase del roadmap que produzca o consuma un artefacto del workdir.
- Al decidir dónde persistir un resultado intermedio nuevo.
- Al evaluar si una fase cruza una frontera de capa (debe ir a §5).
- Al revisar un PR que toque el workdir o el contrato de una capa.

## 3. Las 5 capas — contrato cerrado

Cada subsección sigue la misma tabla. "Persistente" significa que el archivo vive en el workdir tras cerrar la sesión; "efímero" significa que existe solo en memoria durante la ejecución de la capa.

### 3.1 L0 — Ingesta

| Campo | Valor |
|---|---|
| Definición operativa | Convierte el archivo de entrada en regiones, texto y assets con su confianza. No decide qué es importante ni a qué nota va cada contenido. |
| Artefacto de entrada | `<source_file>` (archivo original; ruta declarada en `manifest.json.source.path`) + `profile.yaml` |
| Artefacto de salida | `ingest/regions.json` (más subcarpetas `ingest/ocr/`, `ingest/tables/`, `ingest/formulas/`, `ingest/code/`, `ingest/pages/`) |
| Productos intermedios persistidos | `ingest/pages/`, `ingest/ocr/`, `ingest/regions.json`, `ingest/tables/`, `ingest/formulas/`, `ingest/code/`, `ingest/review.html`, `ingest/preprocess.log` |
| Productos efímeros | Imágenes en memoria durante la clasificación; resultados intermedios de OCR antes de consolidarse en `regions.json` |
| Perfil — campos leídos | `ocr.engine`, `ocr.languages`, `ocr.confidence_threshold`, `preprocessing.chain` |
| Puertas aplicadas | (validación de ingesta en F30 cubre lo suyo; L0 no bloquea por sí sola) |
| Fase del contrato | F17 triage, F18-F29 extractores, F19 preprocess, F20 ocr, F25 code_ocr, F26 review, F30 ingest_check |

### 3.2 L1 — Source Document Model (SDM)

| Campo | Valor |
|---|---|
| Definición operativa | Ensambla regiones en una jerarquía con anclas estables, ids deterministas, confianza y origen. No interpreta; el agente inspecciona el SDM resultante pero no lo modifica. |
| Artefacto de entrada | `ingest/regions.json` + `profile.yaml` |
| Artefacto de salida | `sdm.json` |
| Productos intermedios persistidos | (ninguno; todo se consolida en `sdm.json`) |
| Productos efímeros | Subárboles parciales durante el ensamblado; índices en memoria |
| Perfil — campos leídos | `product.vendor`, `product.edition`, `product.version_policy` (`strict` / `unknown_if_undeclared`) |
| Puertas aplicadas | (bloqueo por orphan ratio y confianza media; ver §8) |
| Fase del contrato | F13 SDM, F32 anchors, F34 provenance, F35 editorial-semantics, F33 assets, F31 build_sdm, F36 cache |

### 3.3 L2 — Conocimiento

| Campo | Valor |
|---|---|
| Definición operativa | El agente decide unidades, criticidad y plan; el script contabiliza y valida. Produce el ledger, el grafo de prerrequisitos, el note plan y el glosario acumulativo. |
| Artefacto de entrada | `sdm.json` + `profile.yaml` |
| Artefacto de salida | `knowledge/ledger.json`, `knowledge/concept-graph.json`, `knowledge/note-plan.json`, `knowledge/glossary.json` |
| Productos intermedios persistidos | Los cuatro archivos de `knowledge/` |
| Productos efímeros | Estado de unidades en memoria durante la sesión del agente; consultas parciales al SDM |
| Perfil — campos leídos | `units.default_criticality`, `ledger.discard_policy`, `graph.cycle_policy` |
| Puertas aplicadas | **Fidelidad (absoluta)** — 100 % de `must-keep` con estado terminal antes de cerrar |
| Fase del contrato | F15 ledger, F37 information-units, F38 ledger operativo, F39 concept-graph, F40 terminology, F41 conflicts, F44 note-plan, F42 fidelity-rules, F43 completeness-audit |

### 3.4 L3 — Autoría

| Campo | Valor |
|---|---|
| Definición operativa | El agente redacta NoteMark; un script lo parsea al Note IR y lo valida. NoteMark es lo que se conserva como fuente de verdad para reproducibilidad; el IR es lo que consume el render. |
| Artefacto de entrada | `knowledge/ledger.json`, `knowledge/note-plan.json`, `sdm.json` (referencias), `profile.yaml` |
| Artefacto de salida | `notemark/<note-id>.nm`, `ir/<note-id>.json` |
| Productos intermedios persistidos | Ambos (NoteMark para reproducibilidad, IR para render) |
| Productos efímeros | Versiones intermedias durante la redacción; resultados de validación antes de aceptar el IR |
| Perfil — campos leídos | `writing.language`, `writing.style`, `folders.schema`, `tags.prefixes`, `depth.layers` |
| Puertas aplicadas | **Calidad (negociable)** — IR válido y sin avisos estructurales bloqueantes |
| Fase del contrato | F12 notemark, F14 ir-spec, F45 block-directives, F46 inline-marks, F47 properties, F48 parse_notemark, F49 validate_ir, F50 transform, F51 depth-layers, F52 trace |

### 3.5 L4 — Render

| Campo | Valor |
|---|---|
| Definición operativa | Traduce el IR validado a cada destino activo, troceando y reportando degradaciones. Las imágenes y assets vienen referenciados desde el SDM; L4 los lee como bytes solo en el momento del render. |
| Artefacto de entrada | `ir/<note-id>.json`, `sdm.json` (rutas de imágenes), `profile.yaml` |
| Artefacto de salida | `render/<destino>/<note-id>...`, `reports/render-degradation.md` |
| Productos intermedios persistidos | `render/<destino>/` por destino activo; `reports/render-degradation.md` |
| Productos efímeros | Páginas en memoria durante la composición; chunks temporales para Notion API |
| Perfil — campos leídos | `targets.active` (lista), `targets.<name>.*` (configuración por destino) |
| Puertas aplicadas | **Render (negociable)** — degradación correcta, contenido íntegro |
| Fase del contrato | F8 capability-matrix, F53 contract, F54-F60 renderers, F61 linking, F62 publishing, F63 cross_target, F64 migration |

### 3.6 Modo obra — meta-orquestador sobre L0-L4 (F106, opt-in)

| Campo | Valor |
|---|---|
| Definición operativa | Cuando la fuente es un libro (≥ 2 capítulos con índice detectable), F106 orquesta L0-L4 **por capítulo** con estado compartido, mapa de dependencias precomputado y consolidación parcial cada N capítulos. NO es una capa nueva; es un orquestador opt-in que persiste progreso entre capítulos. |
| Artefacto de entrada | `sdm.json` (mismo que L1), `profile.yaml` |
| Artefacto de salida | `book-state.json` + `book_map.json` + `book_map.mmd` en el workdir |
| Productos intermedios persistidos | Los tres archivos de modo obra |
| Productos efímeros | Estado de capítulos en memoria durante la sesión |
| Perfil — campos leídos | `book_mode: {enabled, consolidation_every, auto_consolidate}` (opcional) |
| Puertas aplicadas | **Coherencia (estricto)** — BM-R1 (mapa antes de ch1) + BM-R2 (escritura atómica) + BM-R4 (timestamps sellados) + AP-BM1 (no redefinir conceptos) |
| Fase del contrato | F106 book-mode (spec en `references/00-pipeline/book-mode.md`; script en `scripts/pipeline/book_mode.py`) |

## 12. Bloque 14 — Operación (F116)

| Aspecto | Detalle |
|---|---|
| Definición operativa | Catálogo cerrado de modos de fallo (F116) que el pipeline puede encontrar. Norma los contratos "interrupción no deja notas sin marcar `draft`" (R-INT-1..3) y "reprocesar no duplica contenido" (R-REP-1..3). NO es un orquestador ni una capa nueva; es un contrato cross-fase que los orquestadores existentes (F106/F107/F108/F109/F111) ya implementan y que el spec normativiza. |
| Artefacto de entrada | Cualquier evento de fallo: signal handler, exception, condición booleana |
| Artefacto de salida | Estado persistente (`status: draft`, `state: failed`, `debt_registry[]`) |
| Productos intermedios | `reports/debt.json`; `.bak` snapshots |
| Productos efímeros | Memoria del orquestador en sesión actual |
| Puertas aplicadas | **Coherencia (estricto)** — R-INT-1 (schema), R-INT-2 (orquestador conforme), R-INT-3 (orquestador general); R-REP-1 (hash-stable), R-REP-2 (idempotencia estructural), R-REP-3 (source-refs como set) |
| Fase del contrato | F116 failure-modes (spec en `references/14-operation/failure-modes.md`) |

