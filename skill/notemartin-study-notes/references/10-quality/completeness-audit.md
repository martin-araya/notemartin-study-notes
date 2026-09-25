# Auditoría de no-pérdida — `references/10-quality/completeness-audit.md`

> Documento normativo de la **Fase 43** del roadmap. Define el script que verifica que el Coverage Ledger (F15/F38) cubre todos los `must-keep` del SDM sin mutilación, localiza cada entry contra su bloque fuente, y muestrea inversamente el SDM para detectar omisiones inversas. Implementa el gate que enforza `architecture.md` §3.3: "100 % de `must-keep` con estado terminal antes de cerrar".
>
> Documentos complementarios: `references/03-knowledge/ledger.md` (F15, fuente de verdad del ledger), `references/03-knowledge/ledger-operativo.md` (F38, operador read+write; F43 lee), `references/03-knowledge/information-units.md` (F37, fuente de los 14 tipos y reglas R1–R5), `references/02-source-model/spec.md` (F13, contratos de `block.id` sha1 hex 12), `references/02-source-model/editorial-semantics.md` (F35, severidades editorial_note), `references/10-quality/fidelity-rules.md` (F42, lista de valores técnicos), `references/00-pipeline/architecture.md` §3.3 (regla del 100 % must-keep), `docs/adr/ADR-0007-completeness-audit.md` (justificación de las decisiones cerradas).
>
> Enrutado desde N2: `docs/skill-anatomy.md` §6 fila `F43`. Lo corre el script `scripts/validate/completeness.py`; lo consulta F44 (note-plan) antes de diseñar; F114 (quality gate) mide cobertura continua; F118 (evals) ejecuta el eval.

## §1 · Propósito y alcance

La auditoría de no-pérdida es el **gate mecánico** que verifica dos invariantes:

1. **Forward**: cada entry del ledger existe en el SDM (localización) sin mutilación.
2. **Inverse**: el muestreo del SDM no encuentra bloques `must-keep` sin respaldo.

El umbral es **100 % de `must-keep` con estado terminal** (`written`/`merged`/`discarded`). Cero excepciones. Coherente con `architecture.md` §3.3 y `INV-08` del AGENT.md.

**Sí es**:
- El verificador mecánico que ejecuta el agente antes de cerrar un workdir.
- El mecanismo que produce la "lista accionable con anclas" para el agente o para F114.
- El gate que conecta `INV-08` (regla del 100 %) con un exit code.

**No es**:
- Un detector de omisiones semánticas: el muestreo inverso es 100 % must-keep + 10 % context; el resto se detecta por auditoría humana.
- Un rebuilder del ledger: el script NO modifica `ledger.json`. Solo lee y emite reporte.

## §2 · Cuándo se aplica

| Capa / fase | Lee este doc cuando… |
|---|---|
| L2 (agente al cerrar workdir) | Ejecuta `completeness.py audit` antes de marcar L2 como `done` en el manifest. |
| F44 (note-plan) | Lo consulta para diseñar notas que cubran todos los must-keep antes de cerrar. |
| F114 (quality gate) | Lo corre continuamente para detectar drift entre ledger y SDM. |
| F43 (este doc, recurrente) | Cada vez que se cierra un workdir o se actualiza el SDM. |
| F118 (suite automatizada) | Corre `evals/completeness-sample/run_eval.py` para verificar los 3 criterios. |

**No se aplica a**: ingesta (L0–L1), autoría (L3), render (L4).

## §3 · Forward pass (R1)

Recorre `knowledge/ledger.json` y aplica 3 checks a cada entry.

### R1.a — Localización

Para cada `entry.source_block_ids[*]`: el `block.id` debe existir en `sdm.sections[*].blocks[*].id`. Reusa la lógica de `scripts/util/ledger.py check` (F38).

Violación: `category: "orphan-block"`, `severity: "critical"` si el entry es `must-keep`, `warning` si es `context`.

### R1.b — No-mutilación

Para cada `entry.source_block_ids[i]` que resuelve en el SDM, comparar `entry.content[*]` contra `block.content[*]` según la tabla §5. Cualquier diferencia = mutilación.

Violación: `category: "mutilated"`, `severity: "critical"` si `entry.criticality == "must-keep"`, `warning` si es `context`.

### R1.c — Tipo coherente

`entry.type` debe estar en el enum cerrada de 14 tipos (F37 §3). El `block.type` debe ser compatible: si `entry.type = parameter`, el block debe tener `type ∈ {parameter}` o estar en una sección que el agente razonablemente clasifica como parámetro.

Violación: `category: "type-mismatch"`, `severity: "warning"`.

## §4 · Inverse sample (R2)

Recorre `sdm.json` y muestrea bloques. Método **estratificado** (decisión confirmada):

| Estrato | Cobertura | Razón |
|---|---|---|
| Bloques cuyo tipo activa regla R1–R5 de F37 (`parameter`, `default`, `error-code`, `warning` con origen editorial, `formula` con `numbered:true`) | **100 %** | Must-keep por construcción. |
| Bloques con `editorial_note.severity ∈ {deprecated, removed, novelty}` (F35) | **100 %** | Información crítica de ciclo de vida. |
| Resto (`prose`, `example`, `step`, `definition`, `mechanism`, `tradeoff`, `cross-reference`, `syntax-rule`, `version-note` no numerada) | **10 % aleatorio** | Detección de drift/mutilación con seed configurable (default `0`). |

**Tamaño**: `100 % must-keep + 10 % context` (criterio 2 del roadmap).
**Método**: estratificado con seed (default `0`, reproducible). Determinista: misma entrada + mismo seed = misma muestra.

Para cada bloque muestreado, el audit busca un `entry` en el ledger cuyo `source_block_ids[*]` matchee el `block.id`. Si no hay match, finding `category: "missing-backward"`, `severity: "critical"` si el bloque activa regla R1–R5, `warning` si está en el 10 %.

## §5 · Umbrales de mutilación (R3)

Tabla `(campo, regla, threshold)`:

| Campo | Regla | Threshold |
|---|---|---|
| `parameter.name` | Exact match (case-sensitive, whitespace-sensitive) | Cualquier diferencia = mutilación |
| `error-code.code` | Exact match | Cualquier diferencia |
| `version-note.version_introduced` | Exact match | Cualquier diferencia |
| `version-note.version_removed` | Exact match | Cualquier diferencia |
| `syntax-rule.rule` | Exact match | Cualquier diferencia |
| `definition.text` | Normalized match (lowercase + whitespace collapsed) | Cualquier diferencia normalizada |
| `example.text`, `example.code` | Normalized match | Cualquier diferencia normalizada |
| `step.text` | Normalized match | Cualquier diferencia normalizada |
| `warning.text` | Normalized match | Cualquier diferencia normalizada |
| `cross-reference.target` | Normalized match | Cualquier diferencia normalizada |
| `mechanism.text` | Normalized match | Cualquier diferencia normalizada |
| `tradeoff.text` | Normalized match | Cualquier diferencia normalizada |

Sin tolerancia: cualquier diferencia normalizada = `critical` para `must-keep`, `warning` para `context`.

## §6 · Threshold gate (R4)

El gate falla (exit 1) si **cualquiera** de:

- `must-keep` con `state == "pending"` (sin terminal).
- Forward pass: finding `critical` (orphan-block o mutilated en must-keep).
- Inverse sample: finding `critical` (missing-backward en must-keep).

Cero excepciones. Coherente con `INV-08` (architecture.md §3.3).

## §7 · Lista accionable con anclas (R5)

Cada finding del reporte es un objeto JSON:

```json
{
  "anchor": { "type": "block", "id": "a8f4ce140580" },
  "severity": "critical",
  "category": "orphan-block",
  "expected": "block_id existe en SDM",
  "actual": "block_id no encontrado",
  "fix": "Re-extraer la unidad desde el SDM; si el bloque fue renumerado, actualizar source_block_ids en el entry."
}
```

`anchor.type ∈ {block, entry, section}`. `severity ∈ {critical, warning, info}`. `category` enum cerrada: `orphan-block`, `mutilated`, `type-mismatch`, `missing-backward`, `pending-must-keep`.

Cada finding es accionable: un humano o un script de fix (no provisto por F43) puede resolverlo siguiendo `fix`.

## §8 · CLI (R6)

```
completeness.py [--workdir PATH] [--sdm PATH] [--ledger PATH]
                [--sample-rate 0.10] [--seed 0]
                <subcommand> [args]
```

| Subcomando | Propósito | Salida | Exit |
|---|---|---|---|
| `audit` (default) | Forward pass + inverse sample + threshold gate. | JSON a stdout + opcional `--out <path>`. | 0/1/2 |
| `report` | Imprime el reporte en formato humano (no JSON). | Texto a stdout. | 0/1 |
| `check --strict` | Igual a `audit` pero aborta al primer `critical`. | Lo mismo. | 0/1 |
| `fix` | Imprime solo la lista accionable. | Texto a stdout. | 0/1 |

Códigos: `0` PASS (sin critical), `1` FAIL (al menos 1 critical), `2` uso (paths faltantes).

Sin flag `--allow-critical` (a diferencia de `ingest_check.py` F30): el gate NO permite cerrar con rojo.

## §9 · Anti-patrones

- Auditar sin schema validation: dejar que `jsonschema` falle sin reportar el error.
- Ignorar hallazgos `critical` (cerrar con exit 0 forzado).
- Cerrar el workdir con la auditoría en rojo: viola `INV-08` y el criterio 3 del roadmap.
- Sample rate 0 %: omite el inverse sample context (pierde detecciones de mutilación context).
- Sample rate 100 %: ignora el muestreo y audita todo el SDM (más lento, no respeta la decisión R2).
- Modificar `ledger.json` desde el script: solo lee; el script NO es operador.

## §10 · Cómo verificar + cambios permitidos

```bash
# 1. Spec dentro de presupuesto.
wc -l references/10-quality/completeness-audit.md              # ≤ 230
rg -c '^## §' references/10-quality/completeness-audit.md       # 11 secciones

# 2. CLI funcional.
python3 scripts/validate/completeness.py --help                  # 4 subcomandos

# 3. Eval de los 3 criterios del roadmap.
python3 evals/completeness-sample/run_eval.py                    # exit 0

# 4. Sin regresión.
python3 scripts/util/validate_ledger.py --validate evals/ledger-sample/*.json
python3 evals/information-units-sample/run_eval.py
python3 evals/ledger-operativo-sample/run_eval.py
python3 evals/concept-graph-sample/run_eval.py
python3 evals/terminology-sample/run_eval.py
python3 evals/conflicts-sample/run_eval.py
python3 evals/fidelity-sample/run_eval.py

# 5. Cero mención a plataformas (INV-06).
rg -i '<placeholder>' references/10-quality/completeness-audit.md   # vacío
```

**Permitidos sin reabrir F43** (versión menor):
- Añadir un valor a `category` (e.g., `duplicated-entry`).
- Refinar el wording de §1.
- Cambiar el `default_seed` (manteniendo `0` para reproducibilidad).

**Reabren F43** (versión mayor):
- Cambiar el estrato del inverse sample (R2).
- Cambiar los umbrales de mutilación (R3).
- Cambiar el threshold gate (R4): permitir must-keep pending.
- Añadir un flag `--allow-critical` (romper el criterio 3).
- Cambiar la forma de los anchors (R5).

## §11 · Cambios que reabren + glosario

**Reabren F43 además de §10**:
- Cambiar el formato JSON del reporte.
- Cambiar la lista cerrada de categorías.
- Cambiar el método de muestreo (no estratificado).

**No reabren F43**:
- Mensajes de error más claros.
- Añadir `--out` para redirigir el reporte a archivo.
- Cambiar el formato de impresión en `report` (humano).

**Glosario**:

| Término | Significado |
|---|---|
| **Forward pass** | Recorrido ledger → SDM (localización + no-mutilación). |
| **Inverse sample** | Recorrido SDM → ledger (muestreo estratificado). |
| **Estrato** | Subconjunto de bloques con la misma regla de cobertura (100 % must-keep / 10 % context). |
| **Mutilación** | Diferencia entre `entry.content[*]` y `block.content[*]`. |
| **Threshold gate** | Condición 100 % must-keep con estado terminal; cualquier falla = exit 1. |
| **Finding** | Hallazgo accionable del audit con anchor + severity + category + fix. |
| **Lista accionable** | Lista de findings que el agente o un script puede resolver siguiendo `fix`. |
| **Anchor** | `{type: block|entry|section, id: string}` que apunta al elemento afectado. |
