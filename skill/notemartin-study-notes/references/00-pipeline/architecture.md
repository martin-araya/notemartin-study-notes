# Arquitectura de capas y artefactos — `references/00-pipeline/architecture.md`

> Documento normativo de la Fase 4 del roadmap. Define las 5 capas como contratos cerrados de entrada/salida, fija el directorio de trabajo por fuente y establece el modo degradado con umbrales numéricos.
>
> Documentos complementarios: `skills/AGENT.md` §5 (resumen en una frase de las 5 capas + esqueleto del workdir — versión corta), `ROADMAP.md` §4 (diagrama Mermaid del flujo). Este doc los **referencia y completa**, no los repite.
>
> Enrutado desde N2: `docs/skill-anatomy.md` §6 fila `F4`. Doc hermano: `references/00-pipeline/responsibilities.md` (Fase 3, división agente/script y anti-patrones).

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

## 4. Directorio de trabajo por fuente

Árbol canónico. Cada archivo tiene un único productor (la capa que lo emite) y al menos un consumidor (la capa que lo lee). Las fases del roadmap entre paréntesis.

```
.notes-work/<source_hash>/
├── profile.yaml                      # L0–L4 (F11)
├── manifest.json                     # L4 / transversal (F16)
├── ingest/                           # L0
│   ├── pages/                        #   imágenes rasterizadas por página
│   ├── ocr/                          #   salida cruda del OCR por página
│   ├── regions.json                  #   regiones clasificadas
│   ├── tables/                       #   OCR de tablas por página
│   ├── formulas/                     #   OCR de fórmulas por página
│   ├── code/                         #   OCR de código por página
│   ├── review.html                   #   reporte de revisión humana (F26)
│   └── preprocess.log                #   bitácora del preprocesado (F19)
├── sdm.json                          # L1 (F13)
├── knowledge/                        # L2
│   ├── ledger.json                   #   F15
│   ├── concept-graph.json            #   F39
│   ├── note-plan.json                #   F44
│   └── glossary.json                 #   F40
├── notemark/                         # L3 (F12)
│   └── <note-id>.nm                  #   un archivo por nota
├── ir/                               # L3 (F14, F48, F49)
│   └── <note-id>.json                #   un archivo por nota
├── render/                           # L4
│   ├── obsidian/                     #   F54
│   ├── notion/                       #   F55
│   ├── appflowy/                     #   F57
│   ├── markdown/                     #   F58
│   ├── html/                         #   F59
│   └── pdf/                          #   F59
└── reports/                          # transversal
    ├── coverage.md                   #   F38, F43
    ├── fidelity.md                   #   F42, F114
    ├── quality.md                    #   F112-F115
    └── render-degradation.md         #   F53
```

### 4.1 Tabla productor / consumidor

| Ruta | Productor (capa · fase) | Consumidor (capa · fase) |
|---|---|---|
| `profile.yaml` | (entrada del usuario) | L0–L4 |
| `manifest.json` | transversal · F16 | L4 · F62 |
| `ingest/pages/` | L0 · F19 | L0 · F20 |
| `ingest/ocr/` | L0 · F20 | L0 · F22, L0 · F23-F25 |
| `ingest/regions.json` | L0 · F22 | L1 · F31 |
| `ingest/tables/` | L0 · F23 | L1 · F31 |
| `ingest/formulas/` | L0 · F24 | L1 · F31 |
| `ingest/code/` | L0 · F25 | L1 · F31 |
| `ingest/review.html` | L0 · F26 | (humano) |
| `ingest/preprocess.log` | L0 · F19 | (auditoría) |
| `sdm.json` | L1 · F31 | L2 · F15/F37, L3 (referencias), L4 (assets) |
| `knowledge/ledger.json` | L2 · F38 | L2 · F43, L3 · F44, transversal · F115 |
| `knowledge/concept-graph.json` | L2 · F39 | L2 · F104 (rutas), L3 (enlaces) |
| `knowledge/note-plan.json` | L2 · F44 | L3 · F45-F51 |
| `knowledge/glossary.json` | L2 · F40 | L3 (términos canónicos) |
| `notemark/<note-id>.nm` | L3 · F12 | L3 · F48 (parser), reproducibilidad |
| `ir/<note-id>.json` | L3 · F48 | L3 · F49 (validador), L4 · F53-F60 |
| `render/<destino>/...` | L4 · F54-F60 | (usuario) |
| `reports/coverage.md` | transversal · F38, F43 | (humano) |
| `reports/fidelity.md` | transversal · F42, F114 | (humano) |
| `reports/quality.md` | transversal · F112-F115 | (humano) |
| `reports/render-degradation.md` | transversal · F53 | (humano) |

Sin filas huérfanas: cada productor tiene al menos un consumidor; cada consumidor (excepto entradas de usuario) tiene un productor.

## 5. Regla de la frontera de capa

> **Una capa lee su artefacto de entrada y el perfil; nada más.**

Explicitación por capa:

| Capa | Puede leer | No puede leer |
|---|---|---|
| L0 | `<source_file>`, `profile.yaml`, sus propios productos efímeros | `sdm.json`, `knowledge/`, `notemark/`, `ir/`, `render/` |
| L1 | `ingest/`, `profile.yaml` | `knowledge/`, `notemark/`, `ir/`, `render/` |
| L2 | `sdm.json`, `profile.yaml` | `notemark/`, `ir/`, `render/` |
| L3 | `knowledge/`, `sdm.json` (solo referencias, no como contenido), `profile.yaml` | `ingest/`, `render/` |
| L4 | `ir/`, `sdm.json` (rutas de imágenes), `profile.yaml` | `ingest/`, `knowledge/`, `notemark/` |

**Procedimiento de excepción.** Si una capa necesita un dato que está dos capas más abajo, **sube el dato al artefacto intermedio**; no abras la frontera.

Tres ejemplos canónicos:

- **L1 necesita el conteo de bloques por tipo.** No lee el OCR crudo de `ingest/ocr/`; en su lugar, `ingest/regions.json` agrega ese conteo como un campo del propio archivo (`summary.by_type`).
- **L2 necesita la confianza por bloque.** No relee el OCR; `sdm.json` lleva `confidence` dentro de cada bloque (es responsabilidad de L1 haberla traído).
- **L4 necesita imágenes.** No abre `ingest/pages/`; `sdm.json` referencia las imágenes por path relativo (`assets/...`) y L4 las lee por esa referencia en el momento del render.

## 6. Hash de fuente

- **Algoritmo:** `sha256` del archivo de entrada tal como llega al L0, sin normalización previa.
- **Codificación:** hexadecimal minúscula.
- **Registro:** `manifest.json.source.hash` con campo acompañante `algorithm: "sha256"`.
- **Detección de cambio:** si el hash difiere entre dos sesiones sobre el mismo path, F16 dispara acción explícita (reanudar bloquea hasta decisión).
- **Invalidación:** cambio de hash invalida la caché de L0 (F36). Los artefactos L1+ no se invalidan automáticamente: se revalidan campo a campo contra `sdm.json` anterior.

## 7. Perfil — campos leídos por capa

El esquema completo del perfil es F11. Esta sección lista las **claves consumidas** por cada capa, agrupadas por capa para que el lector vea qué perfil necesita una fase concreta.

| Capa | Claves de `profile.yaml` |
|---|---|
| L0 | `ocr.engine`, `ocr.languages`, `ocr.confidence_threshold`, `preprocessing.chain` |
| L1 | `product.vendor`, `product.edition`, `product.version_policy` |
| L2 | `units.default_criticality`, `ledger.discard_policy`, `graph.cycle_policy` |
| L3 | `writing.language`, `writing.style`, `folders.schema`, `tags.prefixes`, `depth.layers` |
| L4 | `targets.active` (lista), `targets.<name>.*` (config por destino) |

Si una capa añade una clave nueva al perfil, debe declararla en esta tabla en el mismo commit que la introduce.

### 7.4 Precedencia prompt > perfil > defaults

Cuando una misma clave puede venir del prompt del usuario, del `profile.yaml` de la fuente, o del default del esquema, el orden de aplicación es:

1. **Prompt** gana. Si el usuario dice "publícalo en español", `writing.language` se sobrescribe a `es` aunque el perfil diga `en`.
2. **Perfil** gana sobre defaults. Si el perfil dice `targets.active: [notion]`, se aplica cuando el prompt no menciona destinos.
3. **Defaults** del esquema `schemas/profile.schema.json` (F11) se aplican cuando ni prompt ni perfil mencionan el campo.

La resolución se hace **en memoria, durante la sesión**, no se modifica el `profile.yaml` en disco. La resolución efectiva se registra en `manifest.json` para reproducibilidad. Cambios del prompt en sesiones sucesivas no se acumulan al perfil; el perfil se modifica solo cuando el usuario lo edita explícitamente.

#### Ejemplo de conflicto resuelto

Estado inicial:

- **Perfil** (`profile.yaml`):
  ```yaml
  writing:
    language: en
  targets:
    active: [obsidian]
  ocr:
    confidence_threshold: 0.8
  ```

- **Prompt del usuario:** "publícalo en español y súbelo a Notion como wiki".

- **Defaults del esquema** (resumidos): `style: intuition-first`, `use_case_profile: hybrid`, `ocr.engine: tesseract`, etc.

Estado final tras aplicar precedencia:

| Llave | Origen | Valor final |
|---|---|---|
| `writing.language` | prompt | `es` |
| `targets.active` | prompt | `[notion]` |
| `ocr.confidence_threshold` | perfil | `0.8` |
| `writing.style` | default | `intuition-first` |
| `use_case_profile` | default | `hybrid` |
| `ocr.engine` | default | `tesseract` |

Cada llave se resuelve **independiente** de las demás: el prompt sobrescribe solo las que nombra explícitamente; el resto mantiene el valor del perfil o, en su defecto, el del esquema.

#### Onboarding

Cuando no existe `profile.yaml`, el agente realiza un onboarding de **máximo 4 preguntas** para generar uno mínimo y guardarlo en el workdir. Las preguntas, en orden:

1. **¿A qué destinos quieres publicar?** (multi-selección: obsidian, notion, appflowy, markdown, html, pdf, anki). Default si vacío: `obsidian`.
2. **¿En qué idioma?** (es, en, es-en, en-es). Default: `es`.
3. **¿Estilo de redacción?** (intuition-first, reference-pure, tutorial, summary). Default: `intuition-first`.
4. **¿Las fuentes incluyen PDFs escaneados u otras imágenes?** (sí/no). Si sí, se pide el motor OCR y los idiomas (sub-pregunta anidada, no cuenta como pregunta adicional).

Cualquier campo no cubierto por las preguntas toma su default del esquema (`scripts/util/validate_profile.py --resolve --empty` los produce).

## 8. Modo degradado — umbrales numéricos

Toda condición de degradación tiene un número. Sin adjetivos, sin "si es corto".

| Capa | Condición | Umbral | Acción |
|---|---|---|---|
| L0 | Confianza media OCR por palabra | `< 0.70` | Reintentar con cadena de preprocesado alternativa |
| L0 | Reintentos por región | `> 2` | Bloquear y emitir `ingest/review.html` con la región marcada |
| L0 | Confianza OCR de código | `< 0.85` | Marcar para validación sintáctica del agente (zona gris §3.4 de `responsibilities.md`) |
| L0 | Confianza OCR de tablas | `< 0.80` | Marcar para revisión humana |
| L1 | Bloques huérfanos (sin ancla padre) | `> 20 %` | Bloquear; el agente no puede continuar |
| L1 | Confianza media de bloques OCR | `< 0.60` | Marcar la fuente como `degraded`; revisión obligatoria en L0 antes de L2 |
| L2 | Cobertura `must-keep` con estado terminal | `< 100 %` | **Bloquear — puerta de fidelidad, no se salta** |
| L2 | Ciclos sin resolver en grafo de prerrequisitos | `≥ 1` | Bloquear |
| L2 | Contradicciones sin marcar | `≥ 1` | Bloquear |
| L3 | Errores de sintaxis NoteMark | `≥ 1` | Parser rechaza con `archivo:línea:directiva`; el agente corrige |
| L3 | Iteraciones de corrección de una nota | `> 3` | Marcar nota como `status: draft`; notificar al usuario |
| L4 | Bloques en una sola petición Notion API | `> 100` | Trocear (F55) |
| L4 | Notion API devuelve 429 | `≥ 1` en 10 min | Espera exponencial: 5 s, 30 s, 2 min, 10 min; si persiste, marcar destino como `degraded` en reporte |
| L4 | Capacidad ausente en destino | `≥ 1` | Aplicar tabla de degradación de F53; nunca omitir contenido fáctico |

## 9. Regla dura — la puerta de fidelidad

Las tres puertas declaradas en `ROADMAP.md` §4:

| Puerta | Capa | Tipo | Se puede saltar |
|---|---|---|---|
| **Fidelidad** | L2 | Absoluta | No, bajo ninguna condición |
| **Calidad** | L3 | Negociable en forma, no en contenido | El estilo puede degradarse; los hechos no |
| **Render** | L4 | Negociable | La forma puede degradarse; el contenido no |

Frase literal: "Ningún modo degradado reduce la cobertura de unidades `must-keep`. Una fuente con 60 % de confianza puede renderizar con advertencias visibles; no puede emitir notas con unidades perdidas."

## 10. Cómo verificar el contrato sobre una capa nueva

Checklist de cinco pasos:

1. ¿La capa declara artefacto de entrada y salida con nombre de archivo? (Ver §3.)
2. ¿El artefacto de salida lleva `schema_version` y está validado contra un JSON Schema (producido por la fase que lo codifica)?
3. ¿La capa lee **solo** su artefacto de entrada + `profile.yaml` + sus productos efímeros? (Ver §5.)
4. ¿Toda condición de modo degradado tiene umbral numérico explícito? (Ver §8.)
5. ¿La capa figura en §3 con veredicto correcto de puerta aplicada (absoluta o negociable)?

Si algún paso falla, el contrato está incompleto y se reabre Fase 4.

## 11. Cambios permitidos sin reabrir Fase 4

- Añadir una carpeta al workdir si una fase futura lo justifica (con ADR; actualizar §3, §4 y §4.1).
- Añadir una fila a §3 (campos consumidos del perfil) cuando una capa lea una clave nueva.
- Ajustar umbrales numéricos de §8 si la experiencia contra el corpus (F6) muestra que son laxos o estrictos (con ADR).

**Reabren Fase 4:**

- Cambiar el algoritmo de hash (§6).
- Añadir una capa o dividir una existente.
- Cambiar el contrato de una capa ya existente (entrada, salida, perfil leído).
- Mover `manifest.json` de ubicación.
- Introducir una nueva entrada compartida (el perfil deja de ser la única).
- Convertir una puerta negociable en absoluta o viceversa.
