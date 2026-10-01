# Set de regresión — `evals/regression/SET.md`

> Composición y justificación del set de regresión de F119. Define qué casos se ejecutan N veces antes de cada release, qué tipo de regresión detecta cada uno, y cómo añadir o retirar casos.

## 1. Composición actual

| Case ID | Origen | Categoría roadmap | Perfil | Métrica primaria | Estado |
|---|---|---|---|---|---|
| `case-01-postgresql-select` | F118 (referenciado) | documentación Oracle (sustituto: PostgreSQL) | reference | cobertura de parámetros canónicos | activo |
| `case-04-arxiv-two-column-arch` | F118 (referenciado) | PDF dos columnas | hybrid | lectura columnar + IR ordenado | activo |
| `case-05-iso-sql-tables-config` | F118 (referenciado) | doc con 20+ tablas / ≥ 200 pp | reference | no truncado (INV-10) | activo |
| `case-13-internet-archive-scan` | F118 (referenciado) | hostil: escaneo torcido | hybrid | fidelidad de código OCR | activo (sample pendiente F6) |
| `case-09-conference-slides-diag` | F119 nuevo | diapositivas (PPT/PDF) | hybrid | ingesta de PPT + decisión diagram/slide | activo |
| `case-06-kubernetes-api-ref-params` | F119 nuevo | API reference | reference | tabla de parámetros exhaustiva | activo |

**Total:** 6 casos. Soft-cap registrado en README §3: 12 casos.

## 2. Justificación por caso

### 2.1 `case-01-postgresql-select` — referencia a F118

- **Por qué está en el set:** la aserción `param-table-coverage` exige 100 % de cobertura de 12 parámetros canónicos. Es la aserción con threshold más estricto del suite (1.0). Una regresión aquí significa que el agente perdió un parámetro del manual.
- **Tipo de regresión que detecta:** caída del agente a cubrir < 100 %; cambio en los parámetros canónicos mismos (rotura del contrato del YAML).
- **Variabilidad esperada:** baja. La tabla `param_table_canonical_01.yaml` es fija (sha256 del sample HTML). Estabilidad depende de que el agente cubra el parámetro en `target_note` o `target_node` del ledger.

### 2.2 `case-04-arxiv-two-column-arch` — referencia a F118

- **Por qué está en el set:** layout a dos columnas es histórico de bugs en pipelines L0 (F21). Cambios en el extractor de layout, en `reading_order_valid`, o en la detección de columnas pueden romper el orden de lectura sin que la cobertura caiga.
- **Tipo de regresión que detecta:** orden de lectura incorrecto, bloques entrelazados, IR con estructura incoherente con el orden columnar real.
- **Variabilidad esperada:** media. Layout es geométrico + heurístico; cambios en `preprocess.py` o `layout.py` pueden afectar el resultado sin tocar las instrucciones del agente.

### 2.3 `case-05-iso-sql-tables-config` — referencia a F118

- **Por qué está en el set:** INV-10 prohíbe explícitamente truncar tablas. La aserción `no-truncation` de F118 (`check: no_etc_or_entre_otros_in_target_notes`) verifica esto. Una regresión aquí suele venir de "mejoras" en la redacción que introducen "etc." o "entre otros".
- **Tipo de regresión que detecta:** truncado (INV-10), paráfrasis que pierde literales, introducción de marcadores prohibidos.
- **Variabilidad esperada:** baja en métricas de cobertura; media en redacción (los matices de paráfrasis pueden variar).

### 2.4 `case-13-internet-archive-scan` — referencia a F118

- **Por qué está en el set:** el modo degradado del pipeline (`architecture.md` §8) se activa aquí. Cambios en el threshold de confianza OCR, en los reintentos, o en la lógica de `low_confidence` pueden romper la decisión de qué bloques se aceptan.
- **Tipo de regresión que detecta:** invenciones sobre OCR dudoso (INV-11), pérdida de bloques marcados como low_confidence, cambio en el threshold de aceptación.
- **Variabilidad esperada:** alta en condiciones reales; la aserción queda en `pending_due_to_missing_sample` hasta que F6 descargue la muestra.
- **Particularidad:** declarado como `pending_due_to_missing_sample` por ausencia de `sample.pdf`; se reactiva automáticamente cuando F6 descargue la muestra.

### 2.5 `case-09-conference-slides-diag` — caso nuevo F119

- **Por qué se añade:** F29C (ingesta de PPTX) puede no estar cerrado al cierre de F119. Aún así, el caso está en el set porque ejercita el camino de "fuente con diagrams + slides", que es la única categoría del corpus que combina diagramas explícitos con texto limitado.
- **Tipo de regresión que detecta:** pérdida de diagramas en la ingesta, asignación incorrecta de `type` (slides como `figure` en vez de `syntax-diagram`), truncado de bullet points.
- **Variabilidad esperada:** alta. Las diapositivas tienen semántica ambigua por diseño; distintas corridas pueden elegir distintas divisiones.

### 2.6 `case-06-kubernetes-api-ref-params` — caso nuevo F119

- **Por qué se añade:** API reference es el caso paradigmático de `reference` profile con tabla de parámetros exhaustiva. Kubernetes Pod v1 tiene 50+ parámetros documentados, lo que ejercita el ledger y la nota api-reference en su peor caso.
- **Tipo de regresión que detecta:** truncado de tabla (50+ filas), pérdida de literales (mensajes de error, defaults), mezcla de tipos de nodos en la tabla.
- **Variabilidad esperada:** baja en métricas de cobertura (la tabla es enumerable); media en redacción.

## 3. Política de extensión

**Añadir un caso al set** se permite sin reabrir F119 cuando se cumplen **las dos** condiciones:

1. Ha aparecido una regresión real en producción (un bug o un caso edge que pasó el suite).
2. El caso es estable: ha pasado el suite ≥ 3 veces consecutivas con `passes_regression: true`.

**Retirar un caso** se permite sin reabrir F119 cuando:

- La métrica que el caso cubría ha sido absorbida por otro caso del set, **y** la cobertura se mantiene.
- La categoría del corpus ya no es relevante (poco probable; F6 marcaría la fuente como `obsolete`).

**Soft-cap:** 12 casos. Superar el soft-cap reabre F119 con ADR.

## 4. Referencias vs nuevos

Los 4 casos marcados "F118 (referenciado)" usan un YAML en `evals/regression/cases/` que **referencia** el caso original en `evals/suite/cases/`. El runner desreferencia y carga el caso real de F118.

Los 2 casos marcados "F119 nuevo" tienen su propio YAML completo en `evals/regression/cases/`.

Esto evita duplicación de prompts y mantiene una sola fuente de verdad para cada caso. El plan futuro: si F120 / F121 / etc. amplían el set de F118, F119 los referencia sin tocarlos.
