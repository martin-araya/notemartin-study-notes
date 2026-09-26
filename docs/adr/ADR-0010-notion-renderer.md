# ADR-0010 — Renderer Notion API

**Fecha:** 2026-09-26
**Estado:** aceptada

**Atada a:** F55, F53 (render contract), F11 (profile schema), F8 (capability matrix), F62 (publishing idempotente), F63 (cross-target), F118 (evals), INV-07, RC-01…RC-05.

## Contexto

Tres problemas acumulados:

1. **Discrepancia de nombre de dialecto.** El contrato F53 (`references/08-render/contract.md`) declara el set canónico `obsidian | notion_api | notion_md | appflowy | markdown | html_pdf | flashcards`. El profile schema F11 (`schemas/profile.schema.json`) declara `obsidian | notion | appflowy | markdown | html | pdf | anki`. F54 (Obsidian) sorteó el problema porque "obsidian" coincide en ambos. F55 (Notion API) diverge: `notion` vs `notion_api`.

2. **Cliente HTTP sin dependencias externas.** El principio del proyecto (F17, F38, F50, F54) es Python 3.9+ stdlib puro. Notion requiere HTTP sobre `api.notion.com` con header `Notion-Version`. Sin `requests`/`httpx`, hay que implementar el cliente con `urllib.request`.

3. **Límite de anidamiento de la API.** Notion permite nesting arbitrario, pero la experiencia empírica (F8 §4 capability-matrix.md) muestra que > 2 niveles prácticos rompen por timeouts. Sin un plan, el renderer colapsaría silenciosamente el contenido (violaría INV-07).

`references/08-render/capability-matrix.md §4` ya documenta los límites duros: 100 bloques/petición, 2000 chars/bloque rich_text, 5 MB file / 20 MB imagen, 3 req/s rate limit, 2 niveles prácticos de anidamiento. Falta el código que los respete.

## Decisión

Cuatro decisiones:

- **D1.** El renderer usa `notion_api` como nombre canónico del dialecto (alineado con F53 contract §6, fila 2 y §4). El profile schema F11 mantiene `notion` por retrocompatibilidad: el renderer acepta ambos nombres en `profile.targets.notion` y `profile.targets.notion_api`, mapeando internamente al canónico. Cualquier discrepancia futura se cierra con un ADR. Esto preserva RC-05 (contract nombra el dialecto) y la equivalencia cross-target (F63).

- **D2.** Cliente HTTP con `urllib.request` stdlib puro. Sin `requests`, `httpx` ni `urllib3`. Timeouts 30s por petición. Reintentos con backoff exponencial 5s/30s/2min/10min (per `architecture.md §8`). 4 reintentos; tras 4 fallos consecutivos contra el mismo endpoint, marca `degraded` y sigue procesando las demás notas.

- **D3.** Anidamiento en 2 pasadas. Pass 1 crea la página + top-level blocks; para `toggle`/`column_list`/`collapsible` los hijos se serializan como placeholders `{"_nested": true, "_depth": N}`. Pass 2 emite los hijos reales via PATCH `/blocks/{id}/children`. > 2 niveles se aplana con placeholder `(anidamiento > 2 niveles no soportado; contenido preservado en notas adjuntas)` y degradación registrada (`content_intact: true`).

- **D4.** Idempotencia por búsqueda de `notemartin_note_id` rich_text property en la database (per property auto-injected) o, sin database, por título `[<note_id>]`. Si existe → PATCH. Si no → POST crear. El primer render crea; el segundo encuentra y actualiza.

## Alternativas consideradas

1. **Usar `requests` como dependencia.** Descartada: viola el principio stdlib puro mantenido por F17, F38, F50, F54 y anunciado en `references/00-pipeline/responsibilities.md`. La diferencia en líneas (~150) no compensa la erosión del principio.

2. **Una sola pasada con aceptación de pérdida > 2 niveles.** Descartada: viola INV-07 (degradación nunca elimina contenido). El placeholder con `content_intact: true` y la nota de "contenido preservado en notas adjuntas" es lo mínimo aceptable.

3. **Renombrar `notion_api` → `notion` en F53 para alinear con F11.** Descartada: rompe RC-05 (el contrato ya está cerrado y nombra `notion_api`), rompe la equivalencia cross-target (F63), y obligaría a reabrir F53. Mejor resolver con mapeo interno en el renderer.

4. **Idempotencia por hash del contenido de la página.** Descartada: cara computacionalmente (Notion no expone un GET que devuelva un hash), frágil ante cambios cosméticos, y rompe la regla "el IR es la fuente de verdad" (F14). El note_id es estable y resuelve el caso.

5. **Pre-renderizar Mermaid a SVG antes de subir.** Considerada y diferida: F70 cubre diagram_image.py; F55 acepta `--pre-render-diagrams` flag (off por defecto) para activarlo cuando exista.

## Consecuencias

**Ganamos:**

- Render completo de 500+ bloques (criterio 1): troceo en chunks de 100 + retries.
- Idempotencia real (criterio 2): re-publicar no duplica.
- Callouts con color + icono correctos (criterio 3): tabla cerrada `SEVERITY_TO_CALLOUT` con 19 entradas (13 canónicas + 6 no nativas con fallback).
- Properties con tipo correcto (criterio 4): `PROPERTY_TYPE_MAP` declara el mapping `python-type → notion-type` para 11 tipos.
- Testing sin token: `--dry-run` emite payloads a disco; eval battery usa mock HTTP server (`http.server` stdlib).

**Perdemos:**

- El cliente HTTP ad-hoc (~120 líneas) requiere mantenimiento; se documenta exhaustivamente en docstring.
- HTTP/2 no se usa (Notion soporta HTTP/1.1; sin impacto funcional).
- 4 reintentos × 10min = 40min worst case antes de `degraded`. Documentado en docstring.

**Quedan atados:**

- **INV-07** (degradación cambia forma, nunca contenido): RC-01 lo refuerza con `content_intact: true` en cada degradación; cada placeholder > 2 niveles mantiene el texto original en una nota "adjunta".
- **RC-04** (función pura respecto al dialecto): `ir_sha256` en payload + `notemartin_ir_sha256` property; dos renders del mismo IR sin cambio remoto producen misma secuencia de llamadas (idempotencia por nota).
- **F62** (publicación idempotente remota): F55 garantiza idempotencia del dialecto; F62 garantiza idempotencia de página (mismo page_id estable).
- **F63** (cross-target): el reporte JSON `content_loss == 0` permite comparar contra Obsidian (F54) y otros.
- **F118** (suite evals): `evals/notion-api-render-sample/` se incorpora como métrica.

## Cambios permitidos sin reabrir ADR-0010

- Cambiar los valores numéricos de `RETRY_DELAYS` o `BLOCKS_PER_REQUEST` (alineados con capability-matrix §4).
- Añadir entradas a `SEVERITY_TO_CALLOUT` para nuevas severidades del IR.
- Añadir entradas a `PROPERTY_TYPE_MAP` para nuevos tipos de Notion.
- Cambiar el timeout por petición.

## Cambios que reabren ADR-0010

- Cambiar la estrategia de 2 pasadas (e.g., aceptar nesting completo a costa de INV-07).
- Cambiar la estrategia de idempotencia (e.g., pasar de `note_id` a hash de contenido).
- Añadir dependencias externas (rompe el principio stdlib puro del proyecto).
- Cambiar el nombre del dialecto en F53 (canónico `notion_api`).
