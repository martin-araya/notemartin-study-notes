# Puerta de calidad y reporte — `references/10-quality/quality-gate.md`

> Documento normativo de la **Fase 115** del roadmap. Define el script
> `scripts/quality_gate.py` que agrega 4 fuentes (F43, F113, F114, F7),
> produce un reporte JSON + Markdown por trabajo, y bloquea la promoción
> a `status: verified` cuando hay errors bloqueantes o cobertura
> incompleta. Registra la deuda aceptada en `reports/debt.json`.
>
> **Cuándo cargar:** al cerrar un trabajo (paso previo a
> `status: verified`); en F118 evals; en CI / pre-publish.
>
> **Wirings:**
> - F43 `scripts/validate/completeness.py` — cobertura ledger ↔ SDM.
> - F113 `scripts/validate/run_all.py` — issues estructurales.
> - F114 `scripts/audit/fidelity_audit.py` — fidelidad semántica.
> - F7 `evals/rubric.md` — rúbrica de 8 dimensiones (4 detectables).
> - F108 `scripts/dedup/detect.py` — duplicados (opcional, si ≥ 5 notas).
> - F47 `schemas/properties.schema.json` — extensión del enum `status` con `verified`.
> - F118 evals — corre `evals/quality-gate-sample/run_eval.py`.

---

## §1 · Propósito y alcance

F115 implementa la **puerta de calidad** que un trabajo debe atravesar
para recibir `status: verified`. Combina:

- Cobertura del ledger (F43).
- Issues estructurales (F113, 11+ validadores).
- Fidelidad semántica (F114).
- Rúbrica auto-aplicada (F7, 4 dimensiones detectables).
- Detección de duplicados (F108, opcional).

Y emite dos artefactos:

1. `reports/quality-gate.json` — agregado consumible por máquina.
2. `reports/quality-gate.md` — resumen legible para revisión humana.

**Sí es**:
- Agregador de fuentes existentes.
- Enforcement del 4° valor de `status`.
- Registro de deuda aceptada.

**No es**:
- Detector de invenciones (F114 ya lo hace).
- Detector de cobertura de ledger (F43 ya lo hace).
- LLM-as-judge para pedagogía / estructura / componentes / utilidad.

---

## §2 · Cuándo se aplica

| Capa / fase | Ejecuta F115 cuando… |
|---|---|
| Agente al cerrar trabajo | Antes de promover notas a `verified`. |
| F43 / F113 / F114 quality gate continuo | Tras cambios en SDM/IR/workdir. |
| F118 evals | Sobre la suite de workdirs. |
| CI / pre-publish | `quality_gate.py check` debe retornar exit 0. |

**No se aplica a:** notas sin workdir (sin `sdm.json`).

---

## §3 · Las 5 fuentes que agrega

| Fuente | ¿Qué aporta? | Cómo se invoca |
|---|---|---|
| **F43** `completeness.py audit` | Cobertura ledger ↔ SDM, forward + inverse | `subprocess` (timeout 30s); consume JSON |
| **F113** `validate/run_all.py` | Issues de 11+ validadores | `subprocess` (timeout 30s); consume JSON |
| **F114** `audit/fidelity_audit.py` | 3 pasadas: forward + content + sampling | `subprocess` (timeout 30s); consume JSON |
| **F7** `evals/rubric.md` | Rúbrica 8 dimensiones; 4 detectables | Cálculo interno (sin red) |
| **F108** `dedup/detect.py` (opcional) | Duplicados canónicos/alias/similarity | `subprocess`; sólo si `len(notes) ≥ 5` |

Las 4 primeras son obligatorias. F108 se omite automáticamente cuando el
workdir tiene < 5 notas (`MIN_NOTES_TO_RUN` de F108).

---

## §4 · Estructura del reporte

```json
{
  "schema_version": "1.0.0",
  "workdir": "<path>",
  "source_hash": "<sha256>",
  "generated_at": "<ISO8601>",
  "summary": { "errors": <int>, "warnings": <int>, "info": <int> },
  "blocking": <bool>,
  "coverage": <float 0..1>,
  "rubric": {
    "fidelity":     { "level": 0-4, "justification": "<str>" },
    "coverage":     { "level": 0-4, "justification": "<str>" },
    "traceability": { "level": 0-4, "justification": "<str>" },
    "render":       { "level": 0-4, "justification": "<str>" },
    "pedagogy":     { "level": null, "justification": "human evaluation required" },
    "structure":    { "level": null, "justification": "human evaluation required" },
    "components":   { "level": null, "justification": "human evaluation required" },
    "operational":  { "level": null, "justification": "human evaluation required" }
  },
  "not_covered": [
    { "section_path": "<xpath>", "reason": "out-of-scope-by-user|navigation|boilerplate|redundante|futuro" }
  ],
  "debt_registry": [
    {
      "id": "QG-DEBT-NNNN",
      "kind": "blocker|warning|info",
      "scope": "<note-id | section | global>",
      "reason": "<str>",
      "raised_by": "<validator>",
      "rule_id": "V-...",
      "created_at": "<ISO8601>",
      "expires_at": "<ISO8601 | null>",
      "accepted_by": "<name | null>"
    }
  ],
  "sources": {
    "completeness": {...},
    "validators":   {...},
    "fidelity":     {...},
    "dedup":        {...} | null
  }
}
```

---

## §5 · Sección `not_covered`

Lista cada sección del SDM que **no** tiene unidad en el ledger.
Enumeración explícita; campo obligatorio (vacío = `[]`).

Cada entrada:
- `section_path` — jerarquía completa (`/ch01/intro/...`).
- `reason` — enum cerrado:
  - `out-of-scope-by-user` — el usuario la excluyó explícitamente.
  - `navigation` — índice, TOC.
  - `boilerplate` — copyright, prefacio.
  - `redundante` — duplicado de otra sección cubierta.
  - `futuro` — pendiente para iteraciones siguientes.

Si una sección no tiene unidad y **no** aparece en `not_covered`, el
quality gate la cuenta como cobertura incompleta (criterio 2 ROADMAP).

---

## §6 · Rúbrica auto-aplicada

| Dimension | Cómo se calcula automáticamente | Niveles |
|---|---|---|
| **Fidelidad** | inversa a `errors`/`warnings` de F114 | 4 si 0 issues; 3 si 0 errors y ≤ 2 warnings; 2 si ≤ 2 errors; 1 si > 2; 0 si > 5 |
| **Cobertura** | `1.0 - (not_covered / total_sections)` | 4 si 100%; 3 si ≥ 95%; 2 si ≥ 90%; 1 si ≥ 70%; 0 si < 70% |
| **Trazabilidad** | inversa a `F113 validate_sdm V-SDM-04/05` + `F114 V-FAUDIT-01` | 4 si 0; 3 si ≤ 2; 2 si ≤ 10; 1 si > 10 |
| **Render** | inversa a `cross_target.py units_lost` | 4 si 0; 3 si ≤ 1; 2 si ≤ 5; 1 si > 5 |

Las 4 dimensiones humanas (pedagogía, estructura, componentes,
utilidad operativa) quedan como `level: null` con `justification:
"human evaluation required"`. **El `promote` NO requiere las
dimensiones humanas.**

---

## §7 · CLI

```
quality_gate.py [--workdir DIR] [--out-dir DIR]
                [--coverage-min 1.0] [--yes] [--markdown-only]
                <subcommand>

report       (default) — produce reports/quality-gate.{json,md}
promote      — modifica frontmatter published→verified si blocking=false
check        — sólo exit code (CI)
debt list    — lista entradas activas en reports/debt.json
debt add     — añade entrada con --kind/--scope/--reason/--expires
debt accept  — marca entrada con --id/--by
```

| Sub-comando | Salida | Exit |
|---|---|---|
| `report` | `reports/quality-gate.json` + `reports/quality-gate.md` | 0/1/2/3 |
| `promote` | Modifica frontmatter + `reports/promote-log.json` | 0/1/2/3 |
| `check` | stdout: `PASS` / `FAIL (<n> errors)` | 0/1/3 |
| `debt list` | JSON | 0/1 |
| `debt add` | JSON con id asignado | 0/1 |
| `debt accept` | JSON con la entrada actualizada | 0/1 |

Códigos: `0` PASS / `1` FAIL (blocking=true o debt non-accepted) / `2`
uso / `3` IO/schema.

---

## §8 · Promoción a `verified` y bloqueo

`promote` itera las notas del workdir (`notemark/*.nm` o
`ir/*.note-ir.json` según destino):

1. Si `frontmatter.status == "published"` y `blocking == false`:
   - Backup automático `.bak`.
   - Modifica `status: published` → `status: verified`.
   - Añade `verified_at: <ISO8601>` y `quality_gate_run_id: <uuid>`.
2. Si `blocking == true`: exit 1 sin mutar.

`blocking` se calcula:

```
blocking = (summary.errors > 0) OR (coverage < COVERAGE_MIN) OR
           (any non-accepted debt with kind == "blocker")
```

`COVERAGE_MIN = 1.0` por default (cumple `INV-08`); configurable con
`--coverage-min`.

**Criterio 3 ROADMAP**: no es posible marcar `status: verified` con
errors bloqueantes. El `promote` lo enforce.

---

## §9 · Wirings y referencias cruzadas

- **F7** `evals/rubric.md` — fuente de las 8 dimensiones; F115 auto-aplica 4.
- **F43** `completeness.py` — fuente `completeness` del reporte.
- **F113** `run_all.py` — fuente `validators` del reporte.
- **F114** `fidelity_audit.py` — fuente `fidelity` del reporte.
- **F108** `dedup/detect.py` — fuente opcional `dedup` del reporte.
- **F47** `properties.schema.json` — extensión del enum `status` con `verified`.
- **F118** evals — corre `evals/quality-gate-sample/run_eval.py`.

---

## §10 · Anti-patrones (AP-QG-1..5)

- **AP-QG-1**: promover notas con errors bloqueantes usando `--yes` para forzar — viola criterio 3.
- **AP-QG-2**: omitir la sección `not_covered` cuando hay secciones sin unidad — viola criterio 2.
- **AP-QG-3**: ejecutar `promote` sin `report` previo — usar el último reporte guardado; nunca ejecutar `promote` sin `report` en el mismo run.
- **AP-QG-4**: aceptar deuda sin `reason` y `expires_at` — la `debt_registry` exige ambos campos.
- **AP-QG-5**: emitir el reporte sin las 4 dimensiones de la rúbrica — el schema las requiere (`null` para las humanas).

---

## §11 · Cambios permitidos + auto-verificación

```bash
# 1. Spec dentro de presupuesto.
wc -l references/10-quality/quality-gate.md                  # ≤ 400

# 2. CLI funcional.
python3 scripts/quality_gate.py --help                       # 5 sub-comandos

# 3. Eval de los 5 sub-criterios del cierre.
python3 evals/quality-gate-sample/run_eval.py                 # 5/5 PASS

# 4. Sin regresión con validadores previos.
python3 evals/validator-suite-sample/run_eval.py              # 3/3 PASS
python3 evals/fidelity-audit-sample/run_eval.py               # 4/4 PASS
python3 evals/completeness-sample/run_eval.py                 # PASS
```

Reabren F115:
- Cambiar la estructura del reporte JSON (rompe `schemas/quality-gate.schema.json`).
- Eliminar `verified` del enum (rompe F47).
- Cambiar la fórmula de `blocking`.

**Criterios de aceptación del ROADMAP F115:**

1. _Cada trabajo produce reporte con cobertura y validación._ → C5: `clean/report` produce `reports/quality-gate.json` con `summary`, `coverage`, `sources` no nulos.
2. _El reporte declara explícitamente lo no cubierto._ → C3: `with-incomplete-coverage/report` tiene `not_covered` no vacío.
3. _No es posible marcar `status: verified` con errores bloqueantes._ → C1+C2: `clean/promote` exit 0 + frontmatter modificado; `with-errors/promote` exit 1 + ningún frontmatter modificado.