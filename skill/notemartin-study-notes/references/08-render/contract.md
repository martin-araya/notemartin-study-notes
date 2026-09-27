# Contrato de renderer y degradación — `references/08-render/contract.md`

> Documento normativo de la **Fase 53** del roadmap. Define la interfaz del renderer (L4), la tabla cerrada de degradación para las 20 celdas ❌ de la matriz de capacidades (F8), la forma del reporte de degradaciones, y refuerza `INV-07`.
>
> Documentos complementarios: `references/08-render/capability-matrix.md` (F8, **fuente de las celdas ❌**), `references/04-authoring/ir-spec.md` (F14, catálogo de 33 nodos y `capability`), `references/00-pipeline/architecture.md` §3.5 (contrato L4), `references/00-pipeline/responsibilities.md` (F3, tabla de responsabilidades), `schemas/profile.schema.json` (F11, `targets.active`).
>
> Enrutado desde N2: `SKILL.md` §5.3 fila `F53`. Lo consumen los renderers individuales (F54-F60), F63 (equivalencia cross-target), y F118 (suite de evals).

## Índice

1. [Propósito y alcance](#1-propósito-y-alcance) · 2. [Cuándo se aplica](#2-cuándo-se-aplica) · 3. [Reglas duras RC-01…RC-05](#3-reglas-duras-invariantes) · 4. [Interfaz del renderer](#4-interfaz-del-renderer) · 5. [Pipeline interno](#5-pipeline-interno-del-renderer) · 6. [Tabla cerrada de degradación](#6-tabla-cerrada-de-degradación) · 7. [Reporte de degradaciones](#7-reporte-de-degradaciones) · 8. [Forma del artefacto renderizado](#8-forma-del-artefacto-renderizado) · 9. [Anti-patrones](#9-anti-patrones) · 10. [Verificación](#10-verificación) · 11. [Cambios permitidos](#11-cambios-permitidos)

## 1. Propósito y alcance

El contrato del renderer es el **documento normativo que cierra tres preguntas** abiertas por F8, F14 y `architecture.md` §3.5:

1. **Interfaz:** ¿qué consume y qué produce exactamente cada renderer? F8 da la matriz; F14 da el IR; F11 da el perfil. Falta la **función pura** `render(ir, profile, matrix) → (artefacts, degradation_report)` que F54-F60 implementan y que F63 compara.
2. **Tabla cerrada:** las 20 celdas ❌ de `capability-matrix.md §2.1` tienen notas en prosa. Falta la **tabla cerrada** que el renderer consulta sin ambigüedad: para cada (capacidad, destino), ¿qué nodo IR se ve afectado y cuál es la **alternativa exacta** que mantiene el contenido?
3. **Reporte obligatorio:** la puerta de render (`architecture.md §3.5`) declara que la degradación es correcta y el contenido íntegro, pero no define **qué evidencia** verifica esa afirmación. Este contrato define el reporte doble (`render-degradation.json` + `render-degradation.md`) que **se genera siempre** (RC-03).

**No es** la matriz F8 (su insumo). **No es** la spec de un renderer concreto (F54-F60). **No es** el esquema del IR (F14). **No es** el validador del reporte (eso vive en `evals/render-contract-sample/run_eval.py`).

## 2. Cuándo se aplica

- **L4** cuando un renderer individual traduce el IR al dialecto del destino.
- **F63** cuando se compara el IR contra el artefacto de otro destino para medir equivalencia.
- **F118** cuando la suite automatizada mide "nodos degradados" como métrica de rúbrica.

**No se aplica a** L0-L3 ni a la suite automatizada como consumidora (F118 solo lee el reporte, no lo genera).

## 3. Reglas duras (invariantes)

| ID | Invariante | Si se omite… |
|---|---|---|
| **RC-01** | Toda degradación cambia la forma, **nunca** elimina contenido fáctico. Refuerza `INV-07`. | El contenido desaparece sin quedar registrado en el reporte; la nota miente por omisión. |
| **RC-02** | La tabla §6 es **cerrada**: cada celda ❌ de `capability-matrix.md §2.1` tiene exactamente una fila. Cualquier celda ❌ sin fila es bug y reabre F53. | El renderer decide "no sé qué hacer" en silencio; la degradación queda fuera del reporte. |
| **RC-03** | El reporte `reports/render-degradation.md` se genera **siempre**, incluso con cero degradaciones. Bloque literal: `> Cero degradaciones en este destino. Esta sección se mantiene siempre para confirmar cobertura.` | La ausencia de reporte se confunde con "todo OK" cuando puede significar "el render falló". |
| **RC-04** | El renderer es **función pura** respecto al dialecto: misma `(ir, profile_target, matrix)` produce mismo artefacto modulo timestamps. `ir_sha256` en la cabecera permite verificar byte-a-byte. F62 se encarga de la idempotencia de publicación (página remota), no del dialecto. | Re-render idempotente queda a merced del renderer; F62 detecta cambios espurios. |
| **RC-05** | El contrato nombra el **dialecto** (`obsidian`, `notion_api`, `notion_md`, `appflowy`, `markdown`, `html_pdf`, `flashcards`), no la sintaxis interna. La traducción dialecto → sintaxis es responsabilidad del renderer. | La spec del contrato se mezcla con detalles de implementación; reabre innecesariamente. |

`INV-07` (degradación cambia forma, nunca contenido) se invoca explícitamente en §1, RC-01 y §7 para que cualquier cambio del contrato preserve su autoridad.

## 4. Interfaz del renderer

Forma canónica (TypeScript-style para legibilidad, **no se ejecuta**):

```ts
type TargetName = "obsidian" | "notion_api" | "notion_md"
                | "appflowy" | "markdown" | "html_pdf" | "flashcards";

interface RenderInput {
  ir: NoteIR;                  // ir/<note-id>.json (F14, schemas/note-ir.schema.json)
  profile: ProfileTarget;      // profile.yaml.targets[target]
  target: TargetName;          // uno de los 7 dialectos
  matrix: CapabilityMatrix;    // estructura §2.1 de capability-matrix.md
  source_hash: string;         // sha256 hex 64 del SDM
}

interface Artifact {
  path: string;                // relativo a render/<target>/
  bytes: Uint8Array;
  sha256: string;             // verificación post-render
}

interface DegradationEntry {
  id: string;                 // "deg-" + sha1 12
  node_path: string;          // ir/<note-id>.json#0/children/2
  node_type: NodeType;        // uno de los 33 de ir-spec.md §4
  capability: string;         // mismo string que capability-matrix.md §3
  alternative: string;        // forma exacta (ver §6)
  evidence: string;           // selector ejecutable: rg / conteo / sha256
  content_intact: true;       // siempre true; si fuera false, viola INV-07
}

interface RenderOutput {
  artifacts: Artifact[];       // 1+ archivos en render/<target>/
  degradation_report: {
    json: DegradationReport;  // ver §7
    md: string;               // ver §7
  };
}

type RenderFn = (input: RenderInput) => RenderOutput;
```

**Campos del perfil leídos por destino:** `targets.<target>.enabled` (bool, default true), `targets.<target>.config.*` (estructura por destino, definida en F11 §4 y `schemas/profile.schema.json`). El renderer **no lee** `writing.*`, `depth.*`, `ocr.*`, etc. — esos campos pertenecen a L0-L3.

**Artefactos producidos (paths canónicos):**

- `render/<target>/<note-id>.<ext>` para una sola pieza (Obsidian, AppFlowy, Markdown, HTML).
- `render/<target>/<note-id>-NNN.<ext>` cuando el destino trocea (Notion API con > 100 bloques; mismo prefijo ya previsto en `architecture.md §3.5`).
- `render/<target>/<note-id>.csv` para flashcards (Anki).
- `reports/render-degradation.json` y `reports/render-degradation.md` siempre (RC-03).

## 5. Pipeline interno del renderer

Cinco etapas en orden estricto. Cada etapa nombra entrada, salida, función y modo degradado aplicable:

| # | Etapa | Entrada | Salida | Función | Modo degradado |
|---|---|---|---|---|---|
| 1 | `load_inputs` | `RenderInput` | IR validado, perfil del target, matriz del target | Validación de schema (F14); extracción de `targets.<target>` | Si el target está en ❌ global, no se renderiza; se emite reporte con `blocked: true` |
| 2 | `traverse_ir` | IR | Árbol de nodos visitados en orden | Recorrido depth-first sobre `children` | — |
| 3 | `resolve_capabilities` | Árbol + matriz | Mapa `node_path → capability` + `node_path → status ∈ {✅, ⚠, ❌}` | Cruzar `node.capability` (F14 §4) con `matrix[capability][target]` (F8 §2.1) | ⚠ emite degradación con `evidence = warning_description` |
| 4 | `apply_degradations` | Mapa + tabla §6 | IR modificado (forma) + lista de entradas de degradación | Para cada nodo con `status = ❌`, sustituir por la `alternative` de §6 manteniendo `source_refs` y `text` íntegros | Cada sustitución se registra como `DegradationEntry` |
| 5 | `emit_artifacts` | IR modificado + reporte | `Artifact[]` + `render-degradation.{json,md}` | Serialización al dialecto; cabecera YAML §8; escritura atómica (`tempfile + Path.replace`) | Si falla la escritura, exit 2 con reporte parcial en stderr |

El renderer **no modifica el IR original**; el IR modificado vive en memoria durante `emit_artifacts` y nunca se persiste como `ir/<note-id>.json` nuevo (F50 cubre las transformaciones que sí se persisten).

## 6. Tabla cerrada de degradación

**Esta tabla es la fuente de verdad operativa para las 20 celdas ❌ de `capability-matrix.md §2.1`.** Una fila por celda ❌, sin "varios" ni "misc".

Convención de columnas: `# | Capacidad (F8 §3) | Destino | Nodos IR afectados | Alternativa exacta | Evidencia de no-pérdida | Sección reporte`.

### 6.1 Capacidades estructurales (10 filas)

| # | Capacidad | Destino | Nodos IR | Alternativa exacta | Evidencia | Reporte |
|---|---|---|---|---|---|---|
| 1 | Celdas combinadas | obsidian | `table` con `rowspan`/`colspan` | Tabla Markdown con celdas vacías replicando la estructura; nota de leyenda `> Estructura original con celdas combinadas (X filas × Y cols) — ver fuente §<section_path>`; bloque `<details>` con la matriz completa `rowspan/colspan` como tabla anidada | `rg -c '<td' render/obsidian/<id>.md` ≥ celdas_con_contenido(IR); `<details>` contiene el árbol | `### obsidian / Celdas combinadas` |
| 2 | Celdas combinadas | notion_api | `table` con `rowspan`/`colspan` | Tabla Notion con celdas vacías replicando la estructura; bloque `callout` adyacente con la matriz original; mención de la fuente | Conteo de bloques `table` = tablas_con_contenido(IR); callout contiene la matriz completa | `### notion_api / Celdas combinadas` |
| 3 | Celdas combinadas | notion_md | `table` con `rowspan`/`colspan` | Markdown plano (Notion import no soporta rowspan); tabla con celdas vacías; nota explícita | `rg '<details>' render/notion_md/<id>.md` exit 0; `rg -c 'source_refs' render/notion_md/<id>.md` ≥ 1 | `### notion_md / Celdas combinadas` |
| 4 | Celdas combinadas | appflowy | `table` con `rowspan`/`colspan` | Markdown compatible AppFlowy con celdas vacías; nota de leyenda | `rg -c '<td' render/appflowy/<id>.md` = celdas_con_contenido(IR); `rg '> Estructura original' render/appflowy/<id>.md` exit 0 | `### appflowy / Celdas combinadas` |
| 5 | Celdas combinadas | markdown | `table` con `rowspan`/`colspan` | Misma estrategia que obsidian; `<details>` con la matriz; nota de leyenda | Conteo de celdas preservado; `<details>` contiene el árbol | `### markdown / Celdas combinadas` |
| 6 | Celdas combinadas | flashcards | `table` con `rowspan`/`colspan` | Serialización lineal: cada celda se convierte en una tarjeta `front: <cell>` o se omite con `discard_reason: redundant-with:<otra>`; la matriz se conserva como `back: <referencia>` | `wc -l render/flashcards/<id>.csv` ≥ celdas_no_vacias(IR); `rg 'redundant-with:' render/flashcards/<id>.csv` exit 0; `discard_reason` de la lista cerrada | `### flashcards / Celdas combinadas` |
| 7 | Backlinks | markdown | sección generada | Sección `## Referenciado por` al final de la nota, generada desde `[[note:...]]` salientes del resto del workdir | `rg '^## Referenciado por' render/markdown/<id>.md` exit 0; lista de wikilinks no vacía si hay notas salientes | `### markdown / Backlinks` |
| 8 | Backlinks | html_pdf | sección generada | Sección `<aside class="backlinks">` al final del HTML con `<ul>` de `<a href="...">` hacia las notas referenciadas | `grep '<aside class="backlinks"' render/html_pdf/<id>.html` exit 0; `<li>` count = backlinks_count | `### html_pdf / Backlinks` |
| 9 | Backlinks | flashcards | no aplica | No aplica: flashcards no tienen backlinks. Registrado como `no-op` con `evidence: not_applicable` y `content_intact: true` | `rg '"node_path": "none"' reports/render-degradation.json` exit 0; `rg '"alternative": "no-op"' reports/render-degradation.json` exit 0 | `### flashcards / Backlinks` |
| 10 | Enlaces entre notas | flashcards | no aplica | No aplica: una tarjeta no contiene enlaces a otras tarjetas. Registrado como `no-op` con `evidence: not_applicable` y `content_intact: true` | `rg 'flashcards / Enlaces' reports/render-degradation.md` exit 0; `jq '.totals.content_loss' reports/render-degradation.json` = 0 | `### flashcards / Enlaces entre notas` |

### 6.2 Capacidades de formato y navegación (10 filas)

| # | Capacidad | Destino | Nodos IR | Alternativa exacta | Evidencia | Reporte |
|---|---|---|---|---|---|---|
| 11 | Callouts semánticos | notion_md | `admonition` | Bloque `>` con prefijo emoji (`⚠️`, `ℹ️`, `❌`, `💡`, `📌`) + texto del título + cuerpo del admonition; el `severity` se mapea al emoji según tabla canónica en `scripts/util/style_mapping.py` (F73) | `grep -E '^> (⚠️\|ℹ️\|❌\|💡\|📌)' render/notion_md/<id>.md` ≥ admonitions_count(IR); texto del cuerpo íntegro | `### notion_md / Callouts semánticos` |
| 12 | Callouts semánticos | markdown | `admonition` | Bloque `>` con emoji + texto + CSS class `callout-<severity>` (per `scripts/util/style_mapping.py`); el color se reemplaza por emoji (GFM no soporta color directo) | `grep -c '^> ' render/markdown/<id>.md` ≥ admonitions_count(IR); `class="callout-` presente si el renderer incluye CSS inline | `### markdown / Callouts semánticos` |
| 13 | Callouts semánticos | flashcards | no aplica | No aplica. Registrado como `no-op` con `evidence: not_applicable` y `content_intact: true` | `rg 'flashcards / Callouts' reports/render-degradation.md` exit 0; `jq '.totals.content_loss' reports/render-degradation.json` = 0 | `### flashcards / Callouts semánticos` |
| 14 | Plegables | flashcards | no aplica | No aplica. Registrado como `no-op` con `evidence: not_applicable` y `content_intact: true` | `rg 'flashcards / Plegables' reports/render-degradation.md` exit 0; `jq '.totals.content_loss' reports/render-degradation.json` = 0 | `### flashcards / Plegables` |
| 15 | Propiedades | notion_md | `property-block` | Frontmatter YAML al inicio del archivo (Notion import respeta YAML en cabecera); cada `property-block` se aplana como `key: value` | `rg '^---$' render/notion_md/<id>.md` ≥ 2 (apertura + cierre); número de keys = properties_count(IR) | `### notion_md / Propiedades` |
| 16 | Consultas dinámicas | markdown | tabla con filtros | Tabla estática `## Consultas habituales` con las filas que la consulta habría producido en build-time; generada por `scripts/render/markdown.py` desde el SDM + ledger | `grep '^## Consultas habituales' render/markdown/<id>.md` exit 0; conteo de filas ≥ 0 si la consulta no devolvió nada | `### markdown / Consultas dinámicas` |
| 17 | Consultas dinámicas | html_pdf | tabla con filtros | Bloque `<section class="queries">` con `<table>` estática equivalente a la del destino Markdown | `grep '<section class="queries"' render/html_pdf/<id>.html` exit 0; `<tr>` count = filas_consulta | `### html_pdf / Consultas dinámicas` |
| 18 | Consultas dinámicas | flashcards | no aplica | No aplica. Registrado como `no-op` con `evidence: not_applicable` y `content_intact: true` | `rg 'flashcards / Consultas' reports/render-degradation.md` exit 0; `jq '.totals.content_loss' reports/render-degradation.json` = 0 | `### flashcards / Consultas dinámicas` |
| 19 | Colores semánticos | notion_md | tokens via CSS | Emoji semántico (`⚠️`, `ℹ️`, `❌`, `💡`, `✅`) prefijo en la línea; sin CSS (Notion import no respeta clases externas); el color se pierde como estilo pero el significado se preserva como emoji; el icono proviene de la tabla canónica `scripts/util/style_mapping.py` (F73) | `grep -cE '(⚠️\|ℹ️\|❌\|💡\|✅)' render/notion_md/<id>.md` ≥ admonitions_count(IR); tokens de `assets/tokens.json` consultados via `scripts/util/style_mapping.py` | `### notion_md / Colores semánticos` |
| 20 | Colores semánticos | markdown | tokens via CSS | Emoji semántico prefijo + clase CSS inline opcional (`class="callout-<severity>"` per `scripts/util/style_mapping.py`); el renderer añade la clase para portabilidad GitHub | `grep -cE '(⚠️\|ℹ️\|❌\|💡\|✅)' render/markdown/<id>.md` ≥ admonitions_count(IR); tokens consultados | `### markdown / Colores semánticos` |

> **Nota:** las 6 entradas "no aplica" de Flashcards (filas 6, 9, 10, 13, 14, 18) son legítimas: la celda es ❌ porque el destino no admite la capacidad; la alternativa es `no-op` con `content_intact: true` porque el nodo IR no se traduce al dialecto Flashcards (las flashcards son tarjetas individuales, no documentos con secciones). Sin la entrada, F63 no podría afirmar equivalencia cross-target sobre flashcards.

## 7. Reporte de degradaciones

Dos artefactos coordinados, siempre generados (RC-03).

### 7.1 `reports/render-degradation.json` (machine-parseable)

```json
{
  "schema_version": "1.0.0",
  "source_hash": "<sha256 hex 64>",
  "generated_at": "<ISO 8601 UTC>",
  "target": "obsidian",
  "totals": {
    "ir_nodes": 0,
    "degradations": 0,
    "content_loss": 0
  },
  "degradations": [
    {
      "id": "deg-<sha1 12>",
      "node_path": "ir/notes/<note-id>.json#0/children/2",
      "node_type": "table",
      "capability": "table-merged-cells",
      "alternative": "Tabla Markdown con celdas vacías + <details>...",
      "evidence": "rg -c '<td' render/obsidian/<id>.md >= ... ",
      "content_intact": true
    }
  ]
}
```

Reglas:

- `totals.content_loss` cuenta entradas con `content_intact: false`; debe ser **siempre 0** (si fuera > 0, el renderer violó RC-01).
- `totals.degradations` cuenta todas las entradas, incluidas las `no-op` (filas 6, 9, 10, 13, 14, 18 de §6).
- `evidence` es un selector ejecutable: el evaluador de F118 puede correrlo y verificar.

### 7.2 `reports/render-degradation.md` (humano)

Estructura obligatoria:

- **Encabezado:** `schema_version`, `source_hash`, `target`, `generated_at`, totales.
- **`## Resumen`:** tabla `{capacidad} | {nº nodos afectados} | {destino}`.
- **`## Degradaciones`:** subsección `### <destino> / <capacidad>` por entrada, con `node_path`, `node_type`, `alternative`, `evidence`, anclaje a la fuente (`source_refs` del nodo IR).
- **`## Cobertura`:** verificación dura — `nodos IR contabilizados = nodos contabilizados en el reporte (degradados + no degradados)`; tabla de no-pérdida (caracteres de texto, `source_refs` totales, `content_loss == 0`).
- **Si `degradations == 0`:** bloque literal `> Cero degradaciones en este destino. Esta sección se mantiene siempre para confirmar cobertura.` (RC-03 textual).

### 7.3 Esquema JSON Schema

Vive en `evals/render-contract-sample/schema/report.schema.json` (incluido en el eval battery). Cubre los campos de §7.1; cualquier renderer que emita un reporte fuera de esquema falla F118.

## 8. Forma del artefacto renderizado

Cabecera YAML al inicio de cada archivo en `render/<target>/`:

```yaml
---
schema_version: "1.0.0"
target: obsidian
note_id: "<hex 12>"
source_hash: "<sha256 hex 64>"
ir_sha256: "<sha256 hex 64>"
rendered_at: "<ISO 8601 UTC>"
renderer_version: "0.0.0"
---
```

Reglas:

- `ir_sha256` permite verificar idempotencia byte-a-byte del dialecto (RC-04).
- `renderer_version` es del renderer concreto (F54-F60), no del contrato. Inicia en `"0.0.0"` y bumpea con cada cambio del renderer.
- `rendered_at` es siempre ISO 8601 UTC (`Z` suffix) para que dos invocaciones en la misma sesión produzcan artefactos distintos solo en este campo, lo que facilita el diff.

Reglas de nombrado:

- `render/<target>/<note-id>.<ext>` para una sola pieza por nota.
- `render/<target>/<note-id>-NNN.<ext>` cuando el destino trocea (Notion API con > 100 bloques).
- `render/<target>/<note-id>.csv` para Anki (encoding UTF-8, separador `,`, quote `"`).

## 9. Anti-patrones

| # | Anti-patrón | Consecuencia | Reemplazo correcto |
|---|---|---|---|
| 1 | Dropear `diagram` Mermaid en destino sin pre-render | Pierde el diagrama en Notion API y AppFlowy (RC-01) | Pre-render con `scripts/render/diagram_image.py`; degradación registrada en §6 fila correspondiente |
| 2 | Emitir Markdown de Obsidian con `![[image.png]]` a Notion | El wikilink se rompe en silencio (no resuelve en Notion) | Usar `![alt](url)` estándar con URL del asset (F31) |
| 3 | Omitir el reporte porque no hubo degradaciones | Viola RC-03; ausencia de reporte se confunde con "todo OK" | Generar siempre con `degradations: []` y bloque literal de §7.2 |
| 4 | Resumir un nodo `table` "porque tiene muchas filas" | Viola INV-10 (ninguna enumeración cerrada se trunca) | Mantener todas las filas; la tabla puede dividirse en chunks pero no resumirse |
| 5 | Traducir el IR "a mano" desde un script en lugar de usar la tabla §6 | El renderer diverge del contrato; F63 falla | Consultar §6; cualquier celda ❌ sin fila reabre F53 |
| 6 | Devolver `content_intact: false` para una degradación "porque es muy costoso" | Viola RC-01; la nota pierde contenido | RC-04 obliga a mantener la forma (no el contenido); si es costoso, degradar al `no-op` con `evidence: not_applicable` cuando aplique, o añadir la alternativa a §6 |
| 7 | Añadir una fila a §6 sin recontar las celdas ❌ de F8 §2.1 | El eval battery falla por desalineación | Recorrer `rg '\| ❌' capability-matrix.md` y comparar conteo antes de añadir |

## 10. Verificación

10 checks con comandos shell. Todos deben pasar antes de cerrar F53:

```bash
# 1. Presupuesto de líneas.
wc -l references/08-render/contract.md                                                # ≤ 300

# 2. 11 secciones numeradas (formato "## N. Título").
rg '^## [0-9]+\. ' references/08-render/contract.md | wc -l                          # = 11

# 3. Paridad de filas en §6 con celdas ❌ de F8 (C1 del eval = C3 aquí).
#    Aisla §6 con awk y cuenta filas de datos.
awk '/^## 6\./,/^## 7\./' references/08-render/contract.md | rg -c '^\| [0-9]+ \|'  # = 20

# Equivalencia con la matriz: cada celda ❌ cuenta una (no una por línea).
rg -o '\| ❌' references/08-render/capability-matrix.md | wc -l                        # = 20

# 4. Cinco invariantes RC presentes.
rg 'RC-0[1-5]' references/08-render/contract.md | wc -l                             # ≥ 5

# 5. INV-06 no-regresión (solo aplica a 04-authoring/; 08-render SÍ menciona dialectos).
rg -i 'obsidian|notion|appflowy' references/04-authoring/ | wc -l                    # = 0 (pre-existente, no introducido por F53)

# 6. Schema version declarada en §7 y §8 (JSON + YAML, dos sintaxis).
rg 'schema_version.*1\.0\.0' references/08-render/contract.md | wc -l                 # ≥ 2

# 7. Suite del eval battery.
python3 evals/render-contract-sample/run_eval.py                                     # 10/10 verde

# 8. Reporte de ejemplo es JSON válido.
python3 -c "import json; json.load(open('evals/render-contract-sample/fixtures/report-sample.json'))"   # exit 0

# 9. RC-03 textual (reporte siempre generado).
rg 'Cero degradaciones' references/08-render/contract.md                              # ≥ 1

# 10. INV-07 reforzado (≥ 3 invocaciones).
rg 'INV-07' references/08-render/contract.md | wc -l                                  # ≥ 3
```

Para INV-06: la verificación 5 confirma no-regresión; `08-render/contract.md` SÍ contiene dialectos (es el objeto del contrato) — eso no rompe INV-06, que aplica a `04-authoring/`.

## 11. Cambios permitidos

**Sí, sin reabrir F53:**

- Corregir errores tipográficos en §6 sin cambiar la forma de la alternativa.
- Añadir referencias a scripts que aún no existen (F54-F60) en §4 y §5.
- Extender §10 con un check adicional.
- Actualizar la versión del esquema del reporte (§7) de `"1.0.0"` a `"1.1.0"` sin breaking change (campo nuevo opcional).

**Reabren F53 (y obligan a ADR nuevo si afectan §3, §6, §7 o §8):**

- Añadir, eliminar o reasignar una fila de §6.
- Cambiar RC-01 a RC-05.
- Cambiar el esquema JSON del reporte (§7) con breaking change.
- Cambiar la forma de la cabecera YAML del artefacto (§8).
- Cambiar el set de dialectos canónicos (`obsidian`, `notion_api`, `notion_md`, `appflowy`, `markdown`, `html_pdf`, `flashcards`).
- Cambiar el estado de una celda en F8 §2.1 que mueva el conteo de ❌ (lo cual obliga a reescribir §6).
