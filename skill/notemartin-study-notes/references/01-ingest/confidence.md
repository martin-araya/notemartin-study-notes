# Confianza y revisión humana — `references/01-ingest/confidence.md`

> Documento normativo de la Fase 26 del roadmap. Define cómo el script `scripts/ingest/review_report.py` agrega la capa de confianza por tipo de región sobre la salida de F22/F23/F24/F25, genera un reporte HTML interactivo con recortes de imagen y texto lado a lado, bloquea si hay demasiadas regiones críticas dudosas, y propaga correcciones humanas a repeticiones del mismo error.
>
> Documentos complementarios: `references/01-ingest/regions.md` (F22), `references/01-ingest/code-ocr.md` (F25), `references/01-ingest/formulas.md` (F24), `references/01-ingest/tables.md` (F23), `references/01-ingest/preprocess.md` (F19, provee imágenes para recortes), `references/00-pipeline/architecture.md` §3.1 (L0 Ingesta), §5 (frontera de capa), §8 (modo degradado).

## Índice

1. [Propósito](#1-propósito) · 2. [Umbrales por tipo de región](#2-umbrales-por-tipo-de-región) · 3. [Bloqueo por regiones críticas](#3-bloqueo-por-regiones-críticas) · 4. [Recortes de imagen lado a lado](#4-recortes-de-imagen-lado-a-lado) · 5. [Correcciones humanas y propagación](#5-correcciones-humanas-y-propagación) · 6. [Reporte HTML interactivo (filtros)](#6-reporte-html-interactivo-filtros) · 7. [Forma de `summary.json`](#7-forma-de-summaryjson) · 8. [Anti-patrones](#8-anti-patrones) · 9. [Cómo conectar con F27+](#9-cómo-conectar-con-f27) · 10. [Cómo verificar + cambios permitidos](#10-cómo-verificar--cambios-permitidos) · 11. [Cómo generar correcciones humanas](#11-cómo-generar-correcciones-humanas)

## 1. Propósito

Agregar la capa de confianza y revisión humana sobre la salida de las fases F22/F23/F24/F25. Producir un reporte HTML que muestre el recorte de imagen junto al texto extraído (filtrable) y bloquee fuentes muy degradadas. Propagar correcciones humanas a regiones con el mismo error.

`scripts/ingest/review_report.py` produce, en `<out-dir>/ingest/review/`:

- `report.html` — reporte interactivo con filter bar JS.
- `summary.json` — machine-readable: umbrales por tipo, conteo de low_confidence, `blocked`, correcciones aplicadas y propagadas.
- `crops/page-NNNN/<id>.png` — recortes de imagen para regiones low_confidence o críticas.

## 2. Umbrales por tipo de región

Cada tipo de región exige un nivel de confianza mínimo distinto. Los umbrales reflejan la sensibilidad del contenido: un error tipográfico en código rompe syntax, mientras que un error en prosa es recuperable.

| Tipo | Umbral mínimo | Razón |
|---|---|---|
| `code` | `≥ 0.90` | Un typo en código significa syntax error. El bloque es inutilizable si está mal. |
| `console` | `≥ 0.90` | Output de terminal. Errores de transcipción rompen el análisis posterior. |
| `table` | `≥ 0.85` | Números equivocados en tablas afectan análisis cuantitativo. |
| `formula` | `≥ 0.75` | Notación matemática tiene tolerancia (un `=` vs `\approx` puede no ser detectable). |
| `syntax_diagram` | `≥ 0.75` | Diagrama de sintaxis tiene estructura reconocible incluso con baja confianza. |
| `heading` | `≥ 0.70` | Títulos son texto corto; se pueden re-formular. |
| `caption` | `≥ 0.70` | Captions son frases cortas; la imprecisión no invalida el bloque. |
| `figure_caption` | `≥ 0.70` | Igual que `caption`. |
| `index` | `≥ 0.70` | Entradas de índice son texto breve; tolerante. |
| `editorial_note` | `≥ 0.65` | Notas son opcionales; pueden omitirse sin perder información central. |
| `text` | `≥ 0.60` | Prosa tolera más errores; el reviewer puede editar manualmente. |
| `figure` | `≥ 0.50` | Imágenes/figures se evalúan visualmente. |
| `capture` | `≥ 0.50` | Igual que `figure`. |
| `diagram` | `≥ 0.50` | Diagramas son imágenes; baja confianza aceptable. |
| `unknown` | `≥ 0.60` | Default; mismo umbral que `text`. |

**Regiones críticas**: `code`, `console`, `table`, `formula`, `syntax_diagram`. Estas son las que más impacto tienen en la utilidad del documento final.

## 3. Bloqueo por regiones críticas

Política de fail-fast: si el reporte tiene `critical_low_confidence_count ≥ MAX_LOW_CONF_CRITICAL = 3`, el script retorna exit code 1 con `summary.json.blocked = true` y `blocked_reason = "too_many_low_confidence_critical_regions"`.

El reporte HTML muestra un banner rojo prominente: **"BLOCKED: revisión obligatoria"**.

Una fuente muy degradada no avanza sin confirmación. El caller (humano o pipeline) debe revisar las regiones críticas y emitir `corrections.json` con correcciones humanas; F26 (re-invocación con `--corrections`) propaga las correcciones y reevalúa.

## 4. Recortes de imagen lado a lado

Para cada región con `low_confidence: true` O tipo crítico, F26:

1. Lee `<images-dir>/page-NNNN.processed.png` (output de F19).
2. Recorta el bbox de la región con padding `CROP_PADDING_PX = 5`.
3. Guarda como `<out-dir>/ingest/review/crops/page-NNNN/<id>.png`.
4. En el reporte HTML, `<img src="page-NNNN-<id>.png">` y `<pre class="region-text">` se renderizan lado a lado en la misma fila de la tabla.

Si el recorte falla (bbox fuera de la imagen, archivo ausente), el HTML muestra `<img alt="(crop unavailable)">` y la celda de texto sigue presente.

## 5. Correcciones humanas y propagación

### 5.1 Formato `corrections.json`

El reviewer produce este archivo después de editar el HTML:

```jsonc
{
  "corrections": [
    {
      "region_id": "c001",
      "original_text": "def foo():",
      "corrected_text": "def foo():",
      "applied_at": "2026-09-24T15:00:00Z",
      "reason": "missing colon"
    }
  ]
}
```

### 5.2 Aplicación local

Cuando F26 se invoca con `--corrections <path>`:

1. Para cada entrada en `corrections.json`, F26 busca la región por `region_id`.
2. Reemplaza el `text` de la región por `corrected_text`.
3. Marca la región como `human_corrected: true`.

### 5.3 Propagación a repeticiones

F26 busca todas las regiones con `text == original_text` y aplica la misma corrección. Las propagaciones se registran en `propagated_corrections[]`:

```jsonc
{
  "propagated_corrections": [
    {
      "region_id": "f003",
      "applied_correction": {
        "original_text": "def foo():",
        "corrected_text": "def foo():"
      }
    }
  ]
}
```

**Restricciones**: la propagación solo aplica a `original_text` con longitud ≥ `PROPAGATION_MIN_LENGTH = 5` chars (evita propagar caracteres sueltos ambiguos).

Si una región tenía `low_confidence: true` y la corrección resuelve el issue, F26 pone `low_confidence: false`.

## 6. Reporte HTML interactivo (filtros)

`<out-dir>/ingest/review/report.html` contiene:

- **Header**: título, fecha, summary stats (`total_regions`, `low_confidence_count`, `critical_low_confidence_count`, `blocked`).
- **Filter bar** (JavaScript inline, sin dependencias):
  - Dropdown `class`: filtra por tipo (`code`, `table`, `formula`, `text`, etc.).
  - Range `confidence`: filtra por rango `[min, max]`.
  - Dropdown `page`: filtra por página.
  - Dropdown `block`: filtra por `low_confidence: true/false`.
- **Tabla de regiones**: cada fila tiene `<img>` (recorte) + `<pre>` (texto extraído) lado a lado, más botones "Accept", "Edit", "Reject" (form-based, action stub).
- **Banner rojo** si `blocked: true`.

## 7. Forma de `summary.json`

```jsonc
{
  "schema_version": "1.0.0",
  "source": {
    "ingest_dir": "...",
    "images_dir": "...",
    "corrections_path": "...",
    "hash": "..."
  },
  "blocked": true,
  "blocked_reason": "too_many_low_confidence_critical_regions",
  "total_regions": 24,
  "low_confidence_count": 5,
  "critical_low_confidence_count": 4,
  "class_thresholds": {
    "code": 0.90, "console": 0.90, "table": 0.85, "formula": 0.75,
    "syntax_diagram": 0.75, "heading": 0.70, "caption": 0.70,
    "figure_caption": 0.70, "index": 0.70, "editorial_note": 0.65,
    "text": 0.60, "figure": 0.50, "capture": 0.50, "diagram": 0.50,
    "unknown": 0.60
  },
  "applied_corrections": [
    {"region_id": "c001", "original": "...", "corrected": "...", "applied_at": "..."}
  ],
  "propagated_corrections": [
    {"region_id": "f003", "applied_correction": {"original": "...", "corrected": "..."}}
  ],
  "warnings": [],
  "generated_at": "2026-09-24T..."
}
```

## 8. Anti-patrones

- **No** aplicar un umbral uniforme a todos los tipos (criterio 2 del roadmap).
- **No** avanzar si hay `critical_low_confidence_count ≥ 3` (criterio 3).
- **No** propagar correcciones humanas sin registrar en `propagated_corrections[]` para auditoría.
- **No** omitir el `<img>` junto al `<pre>` en el HTML (criterio 1).
- **No** corregir el `text` original sin que el reviewer lo indique explícitamente en `corrections.json`.
- **No** aceptar imágenes de baja confianza sin marcar `low_confidence: true`.

## 9. Cómo conectar con F27+

F27+ (cualquier fase que dependa de la salida de F23/F24/F25) debe:

1. Antes de consumir `tables.json`, `formulas.json`, `code.json`, consultar `ingest/review/summary.json`.
2. Si `summary.blocked == true`, ABORTAR y emitir un mensaje claro: "fuente bloqueada por F26; revise el reporte en `ingest/review/report.html` y emita `corrections.json`".
3. Si `summary.blocked == false`, continuar normalmente.

## 10. Cómo verificar + cambios permitidos

Cinco pasos:

1. ¿El reporte HTML tiene `<img>` y `<pre>` lado a lado?
2. ¿`summary.json.class_thresholds` tiene umbrales distintos por tipo?
3. ¿`summary.json.blocked` es `true` cuando hay ≥ 3 regiones críticas dudosas?
4. ¿Las correcciones humanas se aplican a la región correcta?
5. ¿Las propagaciones a regiones con el mismo `original_text` se registran en `propagated_corrections[]`?

```bash
python3 evals/review-sample/run_eval.py
# Esperado: "PASS los 3 criterios"
```

**Cambios permitidos sin reabrir Fase 26:**

- Ajustar los umbrales numéricos por tipo con ADR.
- Añadir un nuevo tipo de región con su umbral justificado.
- Cambiar el formato HTML del reporte (mientras conserve `<img>` + `<pre>` lado a lado).
- Cambiar el tamaño de `MAX_LOW_CONF_CRITICAL` con ADR.

**Reabren Fase 26:**

- Cambiar la lista de regiones críticas.
- Cambiar la política de propagación (e.g., aplicar también por similitud no-exacta).
- Eliminar el bloqueo.
- Cambiar la convención del reporte HTML.

## 12. Siguiente fase — `post_ocr.py` (F27)

Tras F26 (review), F27 aplica la capa final de limpieza determinista antes de F31:

1. F27 lee `ingest/regions/page-NNNN.regions.json` + opcional `dictionary.yaml`.
2. **Reglas deterministas** (R001-R010): R001 espacio después de `\n` (whitelist), R002 colapsa `\n{3,}` a `\n\n`, R003 colapsa dobles espacios (preserva indentación ≥ 4), R004 tabs a espacios, R005-R008 ligaduras (ﬁ, ﬂ, ﬃ, ﬄ → fi, fl, ffi, ffl), R009 numeración incrustada, R010 marcadores `(N)`/`[N]`. **Sin ML, sin heurísticas de plausibilidad**.
3. **Diccionario técnico auditable** YAML con pares `original → corrected` (default: 5 entradas comunes: PostgreSQL, JavaScript, TypeScript, python, mySQL).
4. **Regla dura**: código/console/table/syntax_diagram **intactos** (skipped=True); formula SOLO recibe diccionario (no reglas R001-R010).
5. **Cada corrección rastreable** con `correction_id` único global y `source` ∈ {`rule_id`, `dict_id`}.
6. **Revertibilidad individual**: `--revert <correction_id>` revierte esa corrección específica; `--revert-all` revierte todas.
7. **Audit log** (`audit_log.json`) registra applies y reverts con timestamp.

Detalles y constantes: [`post-ocr.md`](post-ocr.md).

## 11. Cómo generar correcciones humanas

El reviewer edita el HTML generado por F26 (en un navegador o editor). Para cada fila con `low_confidence: true`, el reviewer:

1. Compara el recorte de imagen con el texto extraído.
2. Si el texto es incorrecto, lo edita en el campo de texto.
3. Al guardar, el reviewer produce un `corrections.json`:

```jsonc
{
  "corrections": [
    {
      "region_id": "c001",
      "original_text": "def foo():",
      "corrected_text": "def foo():",
      "applied_at": "2026-09-24T15:00:00Z",
      "reason": "missing colon at end of def"
    }
  ]
}
```

4. Re-invoca F26 con `--corrections <path>`:
   ```
   python3 scripts/ingest/review_report.py \
       --source <ingest_dir> --images-dir <images_dir> \
       --corrections corrections.json --out-dir <review_dir>
   ```
5. F26 aplica las correcciones, propaga a regiones con el mismo `original_text`, y re-genera el reporte.
