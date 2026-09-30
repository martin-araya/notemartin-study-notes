# Auditoría automatizada de fidelidad — `references/10-quality/fidelity-audit.md`

> Documento normativo de la **Fase 114** del roadmap. Define el script
> `scripts/audit/fidelity_audit.py` que ejecuta tres pasadas sobre el
> par (IR, SDM): forward source-check (nodos fácticos con respaldo),
> content-fidelity check (valores inventados), e inverse sampling
> (bloques SDM no cubiertos). Emite JSON con la shape de
> `validators.md` §3 y exit codes 0/1/2/3.
>
> **Cuándo cargar:** antes de cerrar un trabajo (cierre de `status: published`),
> en F43 auditoría, en F114 quality gate continuo, en F118 evals.
>
> **Wirings:**
> - **F42** `references/10-quality/fidelity-rules.md` — fuente de las prohibiciones (taxonomía 3 niveles, lista cerrada de valores técnicos).
> - **F43** `scripts/validate/completeness.py` — patrón arquitectónico (forward + inverse + threshold gate); F114 auditoría semántica vs F43 cobertura ledger.
> - **F37** `references/03-knowledge/information-units.md` — taxonomía R1–R5 (parameter, default, error-code, version-note, syntax-rule).
> - **F35** `references/02-source-model/editorial-semantics.md` — severidades editorial_note (deprecated, removed, novelty).
> - **F49** `scripts/validate/validate_ir.py` — esquema de `source_refs`; F114 complementa (existencia) con verificación semántica (contenido).
> - **F100** `references/06-writing/anti-patterns.md` — lista de palabras prohibidas.
> - **F113** `references/10-quality/validators.md` — contrato (schema JSON, exit codes, modos de invocación).
> - **F118** evals — corre `evals/fidelity-audit-sample/run_eval.py`.

---

## §1 · Propósito y alcance

F114 implementa la **auditoría semántica automatizada** que detecta
afirmaciones inventadas, nodos fácticos sin respaldo y bloques del SDM
no cubiertos en las notas publicadas. Complementa la auditoría de
cobertura del ledger (F43) y la validación de esquema del IR (F49).

**Sí es**:
- Forward source-check sobre cada nodo IR fáctico.
- Content-fidelity check: comparar el contenido del IR contra el SDM (regex + búsqueda literal).
- Inverse sample estratificado del SDM con seed reproducible.

**No es**:
- Detector de plagio o de paráfrasis insuficiente.
- Detector de contradicciones entre unidades (F41 ya cubre `conflicts.md`).
- LLM-as-judge: la detección es puramente determinista.

---

## §2 · Cuándo se aplica

| Capa / fase | Ejecuta F114 cuando… |
|---|---|
| Agente en L3 antes de `status: published` | `--note <note-ir.json>` o `--workdir`. |
| F43 auditoría (forward pass) | Complementa con pasada semántica (no cobertura ledger). |
| F114 quality gate continuo | Lo corre en CI / pre-publish para detectar drift. |
| F111 incremental (diff SDM) | Sobre la porción modificada. |
| F118 evals | Corre `evals/fidelity-audit-sample/run_eval.py` con **4/4 PASS**. |

**No se aplica a:** notas sin IR (modo `--note` rechaza); SDMs sin IRs
asociados (el script salta con `V-FAUDIT-99` info).

---

## §3 · Tres pasadas

### §3.1 · Pasada 1 — Forward source-check (R-FAUDIT-01)

Para cada nodo del IR:

| Nodo | Condición | Resultado |
|---|---|---|
| `paragraph`, `list`, `code`, `table`, `equation`, `figure`, `definition_list` | `external: false` y `derived: false` y `source_refs: []` | **V-FAUDIT-01: error** |
| Cualquier nodo | `external: true` y `source_refs` no vacío | OK (respaldo explícito) |
| Cualquier nodo | `derived: true` y `source_refs` no vacío | OK |
| `admonition`, `collapsible`, `columns`, `divider`, `quote`, `question` | estructural | exento |

Severidad: **error** (criterio 2 del ROADMAP F114).

### §3.2 · Pasada 2 — Content-fidelity check (R-FAUDIT-02)

Para cada nodo IR con valores verificables contra el SDM:

| Atributo IR | Comprobación | Regla |
|---|---|---|
| `attrs.value` numérico | `attrs.unit` poblado (no `null`, no `""`) | **V-FAUDIT-02: warning** |
| `parameter.name` (F37 tipo `parameter`) | Texto aparece en SDM (lowercase + whitespace collapsed) | **V-FAUDIT-03: error** |
| `error-code.code` (F37 tipo `error-code`) | Texto aparece en SDM | **V-FAUDIT-04: error** |
| `version-note` | `version_introduced` o `version_removed` poblado | **V-FAUDIT-05: warning** |
| `syntax-rule.rule` | Texto aparece en SDM | **V-FAUDIT-03: error** |

Detección por **búsqueda literal** sobre el texto del SDM (F13 blocks,
`content.text` concatenado). Sin fuzzy match en esta fase; sinonimia
queda para futuras iteraciones.

Severidad: V-FAUDIT-03/04 = error (criterio 1 del ROADMAP); resto = warning.

### §3.3 · Pasada 3 — Inverse sample (R-FAUDIT-03)

Reutiliza el patrón de F43 §4 con seed reproducible (default `0`).

Estratos sobre el SDM:

| Estrato | Cobertura | Razón |
|---|---|---|
| `content.type ∈ {parameter, default, error-code, version-note, syntax-rule}` | **100 %** | Must-keep por F37. |
| `editorial_note.severity ∈ {deprecated, removed, novelty}` | **100 %** | Ciclo de vida crítico (F35). |
| Resto | **`sample_rate` (default 10 %)** | Detección de drift con `--seed`. |

Para cada bloque muestreado, buscar `block.id` en todos los `source_refs[*]`
de todos los IRs del workdir. Si no aparece:

- must-keep → **V-FAUDIT-06: critical** (severity `error`).
- context → **V-FAUDIT-06: warning**.

El muestreo **corre automáticamente** sin flag (criterio 3 del ROADMAP).

Si el SDM tiene < 10 bloques, `sample_rate` se eleva automáticamente a
`1.0` para garantizar cobertura del contexto.

---

## §4 · Lista cerrada de reglas

| Rule ID | Severidad | Pasada | Mensaje |
|---|---|---|---|
| V-FAUDIT-01 | error | 1 | Nodo fáctico sin respaldo (source_refs vacío) |
| V-FAUDIT-02 | warning | 2 | Valor numérico sin unidad |
| V-FAUDIT-03 | error | 2 | Valor técnico inventado (no aparece en SDM) |
| V-FAUDIT-04 | error | 2 | Código de error inventado |
| V-FAUDIT-05 | warning | 2 | Version-note sin version_introduced/removed |
| V-FAUDIT-06 | error/warning | 3 | Bloque SDM must-keep/context no cubierto |
| V-FAUDIT-99 | info | — | SDM vacío o IR no encontrado |

---

## §5 · Reglas duras (R-FAUDIT-01..06)

- **R-FAUDIT-01**: la Pasada 1 es **obligatoria** en `audit`.
- **R-FAUDIT-02**: la Pasada 2 compara texto con lowercase + whitespace collapsed (sin fuzzy match).
- **R-FAUDIT-03**: la Pasada 3 muestrea automáticamente sin flag (`--seed` configurable; `--sample-rate` opcional).
- **R-FAUDIT-04**: determinismo — misma entrada + mismo `--seed` = mismo `sample_metadata`.
- **R-FAUDIT-05**: cada `issue` lleva `fix_hint` no vacío (R-V-05 de validators.md).
- **R-FAUDIT-06**: cada `issue.node` no vacío (R-V-04 de validators.md).

---

## §6 · Inverse sample — algoritmo

```python
def inverse_sample(sdm, irs, sample_rate, sd_rng):
    must_keep_blocks = []
    editorial_blocks = []
    context_blocks = []
    for blk in all_blocks(sdm):
        if is_must_keep(blk):
            must_keep_blocks.append(blk)
        elif is_editorial_critical(blk):
            editorial_blocks.append(blk)
        else:
            context_blocks.append(blk)

    # 100 % de must-keep y editorial.
    sampled = must_keep_blocks + editorial_blocks
    # 10 % (o sample_rate) del resto, determinista.
    k = max(1, int(len(context_blocks) * sample_rate))
    sampled += sd_rng.sample(context_blocks, k)

    return sampled
```

El `sd_rng` es `random.Random(seed)`, garantizando determinismo.

Para cada bloque muestreado, el audit busca `block.id` en
`{ir.source_refs[*].block_id for ir in all_irs}`. Si no aparece →
finding.

---

## §7 · CLI

```
fidelity_audit.py [--note PATH | --notes-dir DIR | --workdir DIR]
                  [--sdm PATH] [--irs-dir DIR]
                  [--sample-rate 0.10] [--seed 0]
                  [--out PATH] [--strict] [--json]
                  <subcommand>
```

| Subcomando | Propósito | Salida | Exit |
|---|---|---|---|
| `audit` (default) | 3 pasadas + threshold gate | JSON a stdout o `--out` | 0/1/2 |
| `report` | Mismo en formato humano | Texto | 0/1 |
| `check --strict` | Aborta al primer error | JSON | 0/1 |
| `fix` | Lista accionable solo | Texto | 0/1 |

Códigos: `0` PASS, `1` FAIL (≥1 error), `2` uso, `3` error de IO/schema.
Sin flag `--allow-critical` (criterio 3 del ROADMAP: gate no permite
cerrar con rojo, coherente con INV-08).

---

## §8 · Wirings y referencias cruzadas

- **F42** `fidelity-rules.md` — fuente de la lista cerrada de prohibiciones (§4) y la regla de la duda (§5).
- **F43** `completeness.py` + `completeness-audit.md` — patrón arquitectónico reutilizado (forward + inverse + threshold gate).
- **F37** `information-units.md` — taxonomía R1–R5.
- **F35** `editorial-semantics.md` — severidades editorial_note.
- **F49** `validate_ir.py` — valida `source_refs` resolubles al SDM; F114 complementa semánticamente.
- **F100** `anti-patterns.md` — lista de palabras prohibidas.
- **F113** `validators.md` — contrato de shape JSON, exit codes, modos.
- **F118** evals — corre `evals/fidelity-audit-sample/run_eval.py`.

---

## §9 · Anti-patrones (AP-FAUDIT-1..5)

- **AP-FAUDIT-1**: emitir findings sin `fix_hint` — viola R-FAUDIT-05.
- **AP-FAUDIT-2**: usar `--allow-critical` para forzar exit 0 — viola criterio 3.
- **AP-FAUDIT-3**: ignorar Pasada 3 cuando el SDM es grande — viola R-FAUDIT-03.
- **AP-FAUDIT-4**: usar fuzzy match para sinonimia — fuera de alcance (F114 es determinista).
- **AP-FAUDIT-5**: duplicar la cobertura de F43 sobre el ledger — F114 audita IR, no ledger.

---

## §10 · Cómo verificar + cambios permitidos

```bash
# 1. Spec dentro de presupuesto.
wc -l references/10-quality/fidelity-audit.md              # ≤ 400

# 2. CLI funcional.
python3 scripts/audit/fidelity_audit.py --help             # 4 subcomandos

# 3. Eval de los 4 sub-criterios del cierre.
python3 evals/fidelity-audit-sample/run_eval.py             # 4/4 PASS

# 4. Sin regresión con validadores previos.
python3 evals/validator-suite-sample/run_eval.py            # 3/3 PASS
python3 evals/completeness-sample/run_eval.py               # PASS
python3 evals/fidelity-sample/run_eval.py                  # PASS (F42)
```

Reabren F114:
- Cambiar las 3 pasadas o su severidad.
- Añadir un nivel de severidad.
- Romper R-FAUDIT-01..06.
- Cambiar el prefijo `V-FAUDIT`.

---

## §11 · Tabla de auto-verificación

- `wc -l references/10-quality/fidelity-audit.md` ≤ 400.
- 11 secciones canónicas (§1–§11).
- 6 reglas `V-FAUDIT-01..06` + `V-FAUDIT-99`.
- 6 reglas duras `R-FAUDIT-01..06`.
- 5 anti-patrones `AP-FAUDIT-1..5`.
- 4 subcomandos CLI.
- `run_eval.py` **4/4 PASS**.

**Criterios de aceptación del ROADMAP F114:**

1. _Detecta un dato inventado inyectado a propósito._ → C1: fixture `ir-invented-parameter/` produce ≥ 1 issue `V-FAUDIT-03`.
2. _Reporta todo nodo fáctico sin respaldo._ → C1: fixture `ir-no-source-refs/` produce ≥ 1 issue `V-FAUDIT-01`.
3. _El muestreo inverso corre automáticamente._ → C4: dos invocaciones con `--seed 0` producen idéntico `sample_metadata`; fixture `ir-missing-backward/` produce ≥ 1 issue `V-FAUDIT-06`.