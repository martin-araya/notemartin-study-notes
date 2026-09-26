# ADR-0009 — Contrato de renderer y tabla cerrada de degradación

**Fecha:** 2026-09-25
**Estado:** aceptada

**Atada a:** F53, F8 (capability-matrix), F14 (IR), F11 (profile), F62 (publishing), F63 (cross-target), F118 (evals), INV-07, RC-01…RC-05.

## Contexto

Tres problemas acumulados:

1. **Equivalencia cross-target no verificable.** Cada renderer (F54-F60) leería `references/08-render/capability-matrix.md` por su cuenta y reinterpretaría la matriz F8. Sin un contrato común, F63 (equivalencia entre destinos) no puede comparar dos artefactos porque las decisiones de degradación son opacas y diferentes.

2. **"Capacidad ausente" como puerta abierta a la omisión.** Sin tabla cerrada, una capacidad ❌ puede degradarse a "omitir el nodo". Esto viola INV-07 en silencio: el contenido desaparece sin quedar registrado en ningún reporte.

3. **Degradaciones invisibles para el lector.** Sin reporte obligatorio, una nota puede llegar al lector sin que este sepa qué se perdió en la traducción al dialecto del destino. La puerta de render (`architecture.md §3.5`) queda sin mecanismo de verificación material.

`references/08-render/capability-matrix.md` ya cerró sus ⚠ y dejó 20 celdas ❌ con notas de degradación en prosa. Hace falta la tabla cerrada que el renderer consulta y el reporte que el lector inspecciona.

## Decisión

Las cinco invariantes `RC-01` a `RC-05` del contrato (F53, `references/08-render/contract.md` §3):

- **RC-01** Toda degradación cambia la forma, nunca el contenido fáctico (`INV-07`).
- **RC-02** La tabla de degradación es cerrada: cada celda ❌ de la matriz F8 tiene exactamente una fila en §6. Cualquier celda ❌ sin fila es bug y reabre F53.
- **RC-03** El reporte `reports/render-degradation.md` se genera siempre, incluso con cero degradaciones.
- **RC-04** El renderer es función pura respecto al dialecto: misma `(ir, profile_target, matrix)` produce mismo artefacto modulo timestamps. F62 se encarga de la idempotencia de publicación.
- **RC-05** El contrato nombra el dialecto (`obsidian`, `notion_api`, `notion_md`, `appflowy`, `markdown`, `html_pdf`, `flashcards`), no la sintaxis interna.

Forma del reporte (§7): doble artefacto (`render-degradation.json` machine-parseable + `render-degradation.md` humano). Cada entrada declara `node_path`, `node_type`, `capability`, `alternative` (forma exacta), `evidence` (selector ejecutable) y `content_intact: true`. Forma del artefacto renderizado (§8): cabecera YAML común con `schema_version`, `target`, `note_id`, `source_hash`, `ir_sha256`, `rendered_at`, `renderer_version`.

**Tabla cerrada:** una fila por cada celda ❌ de F8 §2.1. Las 20 entradas (ver `contract.md §6`) cubren los 7 destinos y las 8 capacidades con celdas ❌: Celdas combinadas (6 ❌), Callouts semánticos (2 ❌), Plegables (1 ❌), Enlaces entre notas (1 ❌), Backlinks (3 ❌), Propiedades (1 ❌), Consultas dinámicas (3 ❌), Colores semánticos (3 ❌). Total: 20.

## Alternativas consideradas

1. **Dejar la decisión de degradación al renderer individual.** Descartada: rompe equivalencia cross-target (F63) y la auditabilidad de INV-07. Cada renderer inventaría su tabla privada y los reportes serían incomparables.
2. **Tabla no exhaustiva (el renderer puede añadir filas).** Descartada: reintroduce la zona gris que este contrato cierra. Una nueva capacidad ❌ abre un ADR que añade la fila; sin pasada por el contrato, no se acepta.
3. **Reporte opcional (solo si hubo degradación).** Descartada: viola RC-03 y la auditabilidad material de la puerta de render. La ausencia de reporte debe significar "el render no se ejecutó", no "todo salió bien".
4. **Tabla derivada de la matriz automáticamente (sin revisión manual).** Descartada: la columna "Alternativa exacta" es texto normativo redactado por humanos. La regeneración automática reintroduciría omisiones. La tabla se mantiene a mano en `contract.md` y el eval `evals/render-contract-sample/run_eval.py` verifica paridad de conteo con `capability-matrix.md`.
5. **Reporte machine-only o human-only.** Descartada: el reporte machine-parseable permite que F63 y F118 midan "nodos degradados" como métrica; el reporte humano permite al lector verificar lo que perdió. Ambos son necesarios.

## Consecuencias

**Ganamos:**

- Equivalencia cross-target verificable: F63 compara artefactos de dos destinos y puede afirmar "el contenido íntegro es el mismo módulo las 20 degradaciones declaradas".
- Auditabilidad de INV-07: cada degradación declara su verificador ejecutable (`rg`, conteo, sha256). El eval `run_eval.py` corre los 10 verificadores.
- Métrica para F118: "nodos degradados" se calcula del reporte JSON; "contenido preservado" se verifica con `content_loss == 0` global y `content_intact: true` por entrada.
- Reporte legible por el lector: `render-degradation.md` con subsecciones `### <destino> / <capacidad>` y resumen tabulado.

**Perdemos:**

- El contrato es un archivo más a mantener cuando F8 cambie. Mitigación: §11 del contrato limita la edición a filas de §6 (añadir capacidad nueva a F8 no reabre; cambiar el estado de una celda ❌ a ✅ sí reabre).
- Un poco de redundancia con `capability-matrix.md §2.1 nota:`. Mitigación: `contract.md §6` es la fuente de verdad operativa; la matriz mantiene solo la nota breve.

**Queda atado:**

- **INV-07**: una degradación cambia la forma, nunca el contenido. RC-01 lo refuerza con tabla cerrada.
- **F8**: la matriz 14×7 con 20 celdas ❌. Cualquier cambio recontado por el eval.
- **F14**: el IR (`schemas/note-ir.schema.json`) emite los 33 nodos con `capability` obligatoria. La tabla §6 se cierra contra este catálogo.
- **F11**: `targets.active` y `targets.<name>.*` son los campos del perfil que el renderer lee.
- **F62**: la idempotencia de publicación (hash de página remoto) es ortogonal; F53 garantiza idempotencia del dialecto, F62 la de la API.
- **F63**: cross-target consume el reporte JSON para calcular equivalencia.
- **F118**: suite automatizada mide degradaciones y cobertura como métrica de rúbrica.

## Cambios permitidos sin reabrir ADR-0009

- Corregir errores tipográficos en §6 sin cambiar la forma de la alternativa.
- Añadir referencias a scripts que aún no existen (F54-F60) en §4.
- Extender §10 con un check adicional.

## Cambios que reabren ADR-0009

- Añadir, eliminar o reasignar una fila de §6.
- Cambiar RC-01 a RC-05.
- Cambiar el esquema JSON del reporte (§7).
- Cambiar la forma de la cabecera YAML del artefacto (§8).
