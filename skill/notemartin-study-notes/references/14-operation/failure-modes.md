# Modos de fallo — `references/14-operation/failure-modes.md`

> Documento normativo de la **Fase 116** del roadmap. Define el catálogo
> cerrado de 7 modos de fallo que el pipeline puede encontrar (OCR
> fallido, fuente ilegible, contexto agotado, API caída, validador en
> rojo repetido, conflicto irresoluble, interrupción) con los 4 campos
> canónicos (detección, acción, estado resultante, reanudación). Norma
> los contratos "interrupción no deja notas sin marcar `draft`" y
> "reprocesar tras un fallo no duplica contenido".
>
> **Cuándo cargar:** antes de implementar cualquier orquestador de
> larga duración (modo libro, modo chunk, dedup, consolidación,
> incremental); en F118 evals para verificar reglas duras R-INT-* y
> R-REP-*; en cada `SIGTERM`/`SIGINT` handler para validar la acción
> canónica.
>
> **Wirings:**
> - F41 `references/03-knowledge/conflicts.md` — modo "conflicto irresoluble".
> - F47 `references/04-authoring/properties.md` — capa schema de INV-P13.
> - F55 `scripts/render/notion_api.py` — modo "API caída" (Notion).
> - F106 `references/00-pipeline/book-mode.md` §4 (BM-R2..R5b) — implementación conforme existente (interrupción).
> - F107 `references/00-pipeline/chunk-loop.md` §5 (CHK-R1..R5) — implementación conforme existente (budget excedido).
> - F108 `references/03-knowledge/dedup.md` §6 (DEDUP-R1..R5) — aplicación de no-duplicación.
> - F109 `references/10-quality/consolidation-passes.md` §4 (CON-R1..R5) — aplicación de idempotencia.
> - F111 `references/04-authoring/incremental-update.md` §4 (INC-R1..R5) — aplicación de no-borrado y delta estable.
> - F115 `references/10-quality/quality-gate.md` §8 — modo "validador en rojo repetido".

---

## §1 · Propósito y alcance

Todo orquestador de larga duración puede encontrar 7 modos de fallo
cerrados. Este spec los normaliza para que:

1. El agente sepa **qué hacer** ante cada modo (4 campos canónicos).
2. La **interrupción** (SIGINT/SIGTERM/KeyboardInterrupt) siempre
   deje las notas en `status: draft` (contrato R-INT-1..3).
3. El **reproceso** tras un fallo nunca duplique contenido
   (contrato R-REP-1..3).
4. Los modos adicionales se documenten antes de aparecer en cualquier
   script (regla de extensión §10).

**Sí es**: contrato normativo cross-fase para los 7 modos cerrados.

**No es**: documentación de scripts individuales (cada orquestador
documenta su propia lógica en su spec; F116 solo norma la **cara** del
contrato).

---

## §2 · Cuándo se aplica

| Capa / fase | Lee este doc cuando… |
|---|---|
| Cualquier orquestador de larga duración | Antes de implementar SIGTERM/SIGINT handler. |
| F43 auditoría | Al auditar la invariante "no a medias". |
| F44 note-plan | Antes de diseñar el chunking para un libro grande. |
| F118 evals | Suite `evals/failure-modes-sample/` (cuando exista) o inspección manual de las reglas R-INT-* y R-REP-*. |
| Humano al diagnosticar "¿por qué la nota quedó en `draft`?" | Lee §4 para identificar el modo. |

**No se aplica a:** ingesta L0-L1 (cubierto por F30 ingest_check),
validación de esquema (cubierto por F49 validate_ir).

---

## §3 · Los 4 campos canónicos

Cada modo de fallo se documenta con exactamente 4 campos:

| Campo | Significado |
|---|---|
| **Detección** | Cómo se sabe que el modo está activo: signal handler, regex, exception específica, o condición booleana. |
| **Acción** | Lo que el script hace cuando detecta el modo (secuencia de operaciones). |
| **Estado resultante** | El nombre del estado + la ruta del archivo donde persiste. |
| **Reanudación** | Cómo continuar el trabajo tras el fallo (sub-comando, flag, o reintento). |

Forma resumida en §4 con una fila por modo. Forma extendida (con
scripts concretos y código de ejemplo) en §5 (interrupción) y §6
(reproceso).

---

## §4 · Catálogo cerrado de 7 modos

| # | Modo | Detección | Acción | Estado resultante | Reanudación |
|---|---|---|---|---|---|
| 1 | **OCR fallido** | `scripts/ingest/ocr.py` retorna `confidence < 0.5` o `paddleocr.easyocr` lanza `OCREngineError` | Marcar unidad como `ocr_failed` con `confidence` registrado; NO promover a `sdm.json`; emitir `stderr` con código f`OCR_LOW_CONFIDENCE` | `knowledge/ledger.json::entries[i].source = "ocr_failed"`; `state = "pending"` | Re-ejecutar `ingest` con `--force-ocr` (override manual del umbral) o post-OCR manual con `--manual` |
| 2 | **Fuente ilegible** | `scripts/ingest/identify.py` no detecta tipo MIME o `PyMuPDF` lanza `EmptyPageError` en > 30 % de páginas | Abortar con `sdm.status: "illegible"`; persistir partial sdm en `sdm.json.partial` con diagnóstico | `sdm.json::status = "illegible"`; `sdm.json.partial` con lista de páginas fallidas | Cambiar de fuente (manual upload de OCR limpio) o continuar en otra fuente si es libro multi-tomo |
| 3 | **Contexto agotado** | Cualquier orquestador L2-L4 excede `budget` configurado (F107 BUDGET_PER_STAGE) | Abortar la etapa actual con `chunk.status: "budget_exceeded"`; persistir state parcial; emitir f`CHUNK_BUDGET_EXCEEDED` | `chunk-state.json::chunks[i].status = "budget_exceeded"` con `cumulative_ms > budget_ms` | Reanudar con `chunk_loop.py walk --resume` que continúa desde el último chunk done; `--force-budget` aumenta el umbral |
| 4 | **API caída** | `notion_api.py`, `appflowy.py`, otros renderers externos; `requests.exceptions.ConnectionError` o `HTTPError 5xx` 3 veces consecutivas | Retry con backoff exponencial (1s, 2s, 4s, 8s, 16s); tras 5 intentos, abortar con `render.status: "transient_error"` | `render/reports/render-transient.json` con timestamp + último error | Reanudar con `pipeline/publish.py --retry-only <note-id>`; si la API sigue caída, marca `note.status = "draft"` |
| 5 | **Validador en rojo repetido** | F113 o F114 emite el mismo `critical`/`error` en 2+ ejecuciones consecutivas sobre la misma nota (`run_eval.py` detecta por `rule_id` + `node`) | Agregar entrada a `reports/debt.json` con `kind: "blocker"`, `raised_by: "validators|fidelity"` | `reports/debt.json::debt_registry[]` con id `QG-DEBT-NNNN` | `quality_gate.py promote` sigue bloqueado; `debt accept --id ... --by ...` es la única salida, o corregir la nota |
| 6 | **Conflicto irresoluble** | `references/03-knowledge/conflicts.md` (F41): dos fuentes autoritativas se contradicen y la regla "fuente gana" no aplica (paridad) | Marcar nota como `status: draft` con `conflict: {kind, sources, summary}` en frontmatter; NO emitir `published` | `notemark/<id>.nm::status = "draft"`; `notemark/<id>.nm::conflict = {...}` | Preguntar al usuario (`--ask` flag abre prompt) o decidir por regla explícita del perfil (`profile.yaml::conflict_resolution`) |
| 7 | **Interrupción** | `signal.SIGTERM`, `signal.SIGINT`, `KeyboardInterrupt` en cualquier orquestador de larga duración | **3 capas** (§5): revertir `status: published → draft` en notas con `last_modified_at > start_at - 5min`; flush atómico + `.bak` snapshot; exit 0 | `notemark/<id>.nm::status = "draft"`; state files preservados con `.bak` | `pipeline/<orquestador>.py --resume` continúa desde el último paso done; F106 BM-R5b documenta el patrón |

---

## §5 · Contrato "interrupción no deja notas sin marcar `draft`"

3 capas enforced por reglas duras R-INT-1..3.

### §5.1 Capa schema (R-INT-1, F47)

- **INV-P13** *(F116)*: una nota con `status: published` y frontmatter
  incompleto o sin `verified_at` cuando el workdir está en
  `partial_state: true` es **inválida**. El validador (F113) lo enforza.
- Implementación: `validate_properties.py` (F113) añade check:
  si `status == "published"` y el workdir está parcial, retorna
  `V-PR-08: error`.

### §5.2 Capa orquestador conforme (R-INT-2, F106/F107/F108/F109)

- **BM-R5b** *(F106)*, **CHK-R3** *(F107)*, **CON-R1** *(F109)*,
  **INC-R5** *(F111)* ya implementan: registro de `signal.SIGTERM` +
  `SIGINT` handler que hace **flush atómico + exit 0**.
- Generalización F116: **antes del flush**, el handler revierte
  `status: published → draft` en notas con
  `last_modified_at > start_at - 5min` (ventana de la sesión actual).
- Notas con `status: draft` o `status: verified` no se tocan.

### §5.3 Capa orquestador general (R-INT-3, nuevo patrón F116)

- Patrón reutilizable: cualquier orquestador nuevo debe importar
  `scripts/util/safe_interrupt.py` (F116 introduce este helper) que
  encapsula el handler de 3 capas.
- Helper: `safe_interrupt.register(workdir, active_notes, on_signal)`
  con la lógica de reversión de status + flush + exit 0.
- Wirings: F106 BM-R5b / F107 CHK-R3 / F108 / F109 deben migrar a usar
  este helper en un commit de seguimiento; F116 no obliga la migración
  pero la documenta como camino de reducción de gasto.

---

## §6 · Contrato "reprocesar tras un fallo no duplica contenido"

3 capas enforced por reglas duras R-REP-1..3.

### §6.1 Capa hash-stable inputs (R-REP-1, F106 BM-R4)

- Antes de escribir, el script calcula `sha256(input)` y lo compara
  con `previous_sha256_input` (F106 BM-R4 ya tiene esto).
- Si `sha256(input) == previous_sha256_input`: skip escritura (idempotente).
- Si difieren: continuar con la escritura normal.

### §6.2 Capa idempotencia estructural (R-REP-2, F109 CON-R1)

- Los writes usan `Path.replace()` atómico + `.bak` snapshot.
- Re-procesar sobre-escribe el `.bak` con el contenido anterior; **no acumula**.
- Wirings: F109 CON-R1 (idempotente), F106 BM-R2 (atomic write).

### §6.3 Capa source-refs no se duplican (R-REP-3, F111 INC-R2)

- `source_refs` se trata como **set** en la deduplicación.
- Cualquier append lineal falla validador F113 (`validate_sdm.py`
  V-SDM-03 detecta bloques duplicados; equivalente para `source_refs`
  en IR: `validate_ir.py` ya emite E4 sobre `source_refs` repetidos).
- Wirings: F111 INC-R2 (no borra), F49 E4 (source_refs únicos).

---

## §7 · Estados resultantes — enum cerrado

Nombres de los `state` que aparecen en la columna 5 de §4:

| Estado | Significado | Aparece en |
|---|---|---|
| `ocr_failed` | unidad con OCR de baja confianza | `ledger.json::entries[i]` |
| `illegible` | SDM no se pudo construir | `sdm.json::status` |
| `budget_exceeded` | etapa excedió presupuesto | `chunk-state.json::chunks[i].status` |
| `transient_error` | renderer externo no responde | `render/reports/render-transient.json` |
| `blocker` | deuda aceptada pendiente | `reports/debt.json::debt_registry[i].kind` |
| `draft` (revertido) | nota revertida por interrupción | `notemark/<id>.nm::status` |
| `conflict` | nota con conflicto abierto | `notemark/<id>.nm::conflict` |

---

## §8 · Wirings y referencias cruzadas

- **F41** `references/03-knowledge/conflicts.md` — modo 6 (conflicto irresoluble).
- **F47** `references/04-authoring/properties.md` — capa schema R-INT-1 + INV-P13.
- **F55** `scripts/render/notion_api.py` — modo 4 (API caída, Notion).
- **F106** `references/00-pipeline/book-mode.md` §4 — implementación conforme existente (R-INT-2).
- **F107** `references/00-pipeline/chunk-loop.md` §5 — implementación conforme existente (modo 3).
- **F108** `references/03-knowledge/dedup.md` §6 — aplicación de no-duplicación.
- **F109** `references/10-quality/consolidation-passes.md` §4 — idempotencia (R-REP-2).
- **F111** `references/04-authoring/incremental-update.md` §4 — no-borrado + delta estable.
- **F115** `references/10-quality/quality-gate.md` §8 — modo 5 (validador en rojo repetido).
- **F118** evals — verifica reglas R-INT-* y R-REP-* en la suite.

---

## §9 · Anti-patrones (AP-FMOD-1..5)

- **AP-FMOD-1**: manejar SIGTERM con `sys.exit(1)` directo (sin flush). Viola R-INT-2.
- **AP-FMOD-2**: usar `try/except` con `pass` silencioso en cualquier modo. El estado debe persistir siempre.
- **AP-FMOD-3**: re-procesar sin comparar `sha256(input)`. Viola R-REP-1.
- **AP-FMOD-4**: marcar `status: published` en una nota cuyo contenido no se ha completado. Viola R-INT-2 capa orquestador.
- **AP-FMOD-5**: introducir un modo de fallo nuevo en código sin documentarlo aquí (§10). Viola el contrato cerrado.

---

## §10 · Modos adicionales — regla de extensión

Cualquier fallo nuevo se documenta con los 4 campos canónicos (§3)
**antes** de aparecer en cualquier script. La forma es:

```yaml
- nombre: <snake_case>
  detección: <trigger>
  acción: <secuencia>
  estado: <uno de §7>
  reanudación: <cómo continuar>
  wirings:
    - <fase>: <referencia>
```

El script que lo detecta cita `references/14-operation/failure-modes.md`
§<número> en su docstring o comentario. Sin cita, el código no abre la
capa.

**Modos cerrados al v1.0.0 (F116):** exactamente 7 (§4). Cualquier
adición es delta aditivo compatible con INV-P8; no reabre F116.

---

## §11 · Cambios permitidos + tabla de auto-verificación

```bash
# 1. Spec dentro de presupuesto.
wc -l references/14-operation/failure-modes.md        # ≤ 400

# 2. 11 secciones canónicas.
rg -c '^## §' references/14-operation/failure-modes.md  # 11

# 3. 7 modos cerrados.
rg -c '^\| [0-9] \|' references/14-operation/failure-modes.md   # 7

# 4. 5 anti-patrones.
rg -c '^- \*\*AP-FMOD-' references/14-operation/failure-modes.md  # 5

# 5. Sin regresión en orquestadores existentes.
python3 scripts/pipeline/book_mode.py --help
python3 scripts/pipeline/chunk_loop.py --help
python3 scripts/dedup/detect.py --help
python3 scripts/pipeline/consolidate.py --help
python3 scripts/diff/update.py --help
```

Reabren F116:
- Cambiar un campo canónico de §3.
- Eliminar o renumerar un modo de §4.
- Relajar R-INT-* o R-REP-*.
- Eliminar la regla de extensión de §10.

**Criterios de aceptación del ROADMAP F116:**

1. _Cada fallo tiene acción definida y estado resultante._ → §4 tiene exactamente 7 filas; cada fila con 4 campos canónicos.
2. _Una interrupción no deja notas sin marcar `draft`._ → §5 documenta las 3 capas + reglas duras R-INT-1..3.
3. _Reprocesar tras un fallo no duplica contenido._ → §6 documenta las 3 capas + reglas duras R-REP-1..3.