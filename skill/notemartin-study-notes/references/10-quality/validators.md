# Validadores — `references/10-quality/validators.md`

> Documento normativo de la **Fase 113** del roadmap. Define el schema
> común de severidades y exit codes, el catálogo de las 16 categorías de
> validación y los 12 validadores que las cubren, y el contrato del
> orquestador `run_all.py`.
>
> **Cuándo cargar:** antes de ejecutar `scripts/validate/run_all.py` o
> cualquier validador individual; antes de añadir un validador nuevo;
> en F114 quality gate para agregar issues al reporte.
>
> **Wirings:**
> - F11 `assets/profile.template.yaml` + `schemas/profile.schema.json` — entrada de `validate_profile`.
> - F12 `references/04-authoring/notemark.ebnf` — gramática de `validate_notemark`.
> - F13 `schemas/sdm.schema.json` — entrada de `validate_sdm`.
> - F15 `schemas/ledger.schema.json` — entrada de `validate_ledger`.
> - F47 `schemas/properties.schema.json` — entrada de `validate_properties`.
> - F49 `scripts/validate/validate_ir.py` — IR.
> - F63 `scripts/validate/cross_target.py` — invocado por `validate_destinations`.
> - F66 / F67 `scripts/validate/mermaid.py` — diagramas Mermaid.
> - F69 — diagramas monoespaciados (`monospace_diagrams.py`).
> - F72 `scripts/validate/contrast_check.py` — tokens WCAG.
> - F75 `references/07-visual/note-templates.md` — patrones por tipo.
> - F76 `scripts/validate/density_check.py` — longitudes y estructura.
> - F100 `references/06-writing/anti-patterns.md` — base de `validate_links.py` (V-LK-02).
> - F102–F105 — `self_eval_check`, `error_log_check`, `study_paths_check`, `goal_profile_check`.
> - F114 quality gate — agrega issues al reporte.
> - F118 evals — corre la suite `evals/validator-suite-sample/`.

---

## §1 · Propósito y alcance

La fase F113 consolida la **suite de validadores** que el agente (y el
humano) ejecutan para cerrar un trabajo. Un validador es un script
`scripts/validate/*.py` que:

- Carga un artefacto (perfil, SDM, ledger, nota, IR, render, etc.).
- Emite una lista de issues con shape JSON cerrada (§3).
- Retorna exit code según §3.2.

Este documento norma el **contrato**; cada validador individual se
describe en su propio docstring + entrada de `scripts/README.md`.

---

## §2 · Cuándo se aplica

| Capa / fase | Ejecuta validadores cuando… |
|---|---|
| Agente en L3 | Antes de `status: published`; modo `--note` o `--workdir`. |
| F43 auditoría | Cierra el trabajo; invoca `run_all.py --workdir`. |
| F114 quality gate | Agrega issues al reporte de cierre. |
| F111 incremental | Diff entre versiones; corre validador afectado. |
| F115 puerta de calidad | Bloquea si `run_all.py` retorna exit 1. |
| F118 evals | Suite automatizada sobre corpus + golden. |

**No se aplica a:** ingesta L0 (gate separado en F30), render L4
(verificación visual en F77).

---

## §3 · Schema común de severidades y exit codes

### §3.1 · Forma del JSON emitido

```json
{
  "schema_version": "1.0.0",
  "validator": "validate_<categoria>",
  "target": "<ruta>",
  "started_at": "<ISO8601>",
  "duration_ms": <int>,
  "summary": { "errors": <int>, "warnings": <int>, "info": <int> },
  "issues": [
    {
      "rule_id": "V-<CAT>-<NNN>",
      "severity": "error | warning | info",
      "message": "<string>",
      "file": "<ruta relativa>",
      "node": "<sección / block_id / line:col / node_path>",
      "fix_hint": "<string opcional>"
    }
  ]
}
```

Campos obligatorios: `schema_version`, `validator`, `target`, `summary`,
`issues[*].rule_id`, `issues[*].severity`, `issues[*].message`,
`issues[*].file`, `issues[*].node`.

### §3.2 · Exit codes (cerrados)

| Condición | Exit |
|---|---|
| Sin issues | 0 |
| Solo `info` | 0 |
| Cualquier `warning` y 0 `error` | 2 |
| Cualquier `error` | 1 |
| Error de uso / IO / schema no encontrado | 3 |

### §3.3 · Prefijos `rule_id`

| Prefijo | Validador |
|---|---|
| `V-PROF-NNN` | `validate_profile.py` |
| `V-SDM-NNN` | `validate_sdm.py` |
| `V-LED-NNN` | `validate_ledger.py` |
| `V-NM-NNN` | `validate_notemark.py` |
| `V-LK-NNN` | `validate_links.py` |
| `V-IMG-NNN` | `validate_images.py` |
| `V-PR-NNN` | `validate_properties.py` |
| `V-TBL-NNN` | `validate_tables.py` |
| `V-LEN-NNN` | `validate_lengths.py` |
| `V-MD-NNN` | `monospace_diagrams.py` |
| `V-DST-NNN` | `validate_destinations.py` |
| `V-RUN-NNN` | `run_all.py` (issues del orquestador) |

---

## §4 · Catálogo cerrado

16 categorías del ROADMAP F113 × 12 scripts (los 11 nuevos + `run_all.py`
que los orquesta; los 11 validadores preexistentes listados en `scripts/`
se invocan también desde `run_all.py` pero mantienen su contrato propio
cuando se ejecutan standalone).

| # | Categoría | Validador | Modo de target |
|---|---|---|---|
| 1 | Perfil | `validate_profile.py` | `--note profile.yaml` o `--workdir` |
| 2 | SDM | `validate_sdm.py` | `--note sdm.json` o `--workdir` |
| 3 | Ledger | `validate_ledger.py` | `--note ledger.json` o `--workdir` |
| 4 | NoteMark | `validate_notemark.py` | `--note <.nm/.md>` |
| 5 | IR | `validate_ir.py` (F49, preexistente) | `--note <note-ir.json>` |
| 6 | Diagramas Mermaid | `mermaid.py` (F67, preexistente) | `--note <.nm/.md>` |
| 7 | Diagramas mono | `monospace_diagrams.py` | `--note <.nm/.md>` |
| 8 | Salidas por destino | `validate_destinations.py` (wrapper de `cross_target.py`) | `--workdir` o `--note <note-id>` |
| 9 | Enlaces | `validate_links.py` | `--notes-dir` o `--workdir` |
| 10 | Imágenes | `validate_images.py` | `--note <.nm/.md>` |
| 11 | Propiedades | `validate_properties.py` | `--note <.nm/.md>` |
| 12 | Tablas | `validate_tables.py` | `--note <.nm/.md>` |
| 13 | Longitudes | `validate_lengths.py` | `--note <.nm/.md>` |
| 14 | Densidad | `density_check.py` (F76, preexistente) | `--note <.nm/.md>` |
| 15 | Cobertura | `completeness.py` (F43, preexistente) | `--workdir` |
| 16 | Ingesta (gate L2) | `ingest_check.py` (F30, preexistente) | `--note sdm.json` |

> **Fidelidad semántica** — la auditoría de fidelidad del IR contra el
> SDM (`scripts/audit/fidelity_audit.py`, F114) sigue el mismo contrato
> JSON + exit codes pero vive bajo `scripts/audit/` (separada de la
> `scripts/validate/` que F113 orquesta); ver
> `references/10-quality/fidelity-audit.md` §4.

> **Verificador de entorno** — `scripts/check_deps.py` (F117) NO es un
> validador. No emite JSON con la shape §3; emite texto humano con el
> estado de las dependencias declaradas en `scripts/README.md` (4 niveles
> req/rec/opt/bin). Su exit code es independiente: 0 = entorno sano, 2 =
> sólo rec/opt faltan, 1 = ≥ 1 req falta. Ver `scripts/CHECKLIST.md`.

---

## §5 · Reglas duras comunes (R-V-01..05)

- **R-V-01**: todo validador emite JSON con `schema_version: "1.0.0"` cuando se invoca con `--json` o desde `run_all.py`.
- **R-V-02**: todo `issue.rule_id` empieza por `V-<CAT>-NNN` con `CAT` ∈ {PROF, SDM, LED, NM, LK, IMG, PR, TBL, LEN, MD, DST, RUN}.
- **R-V-03**: todo `issue.file` es ruta relativa al CWD o al workdir; nunca absoluta.
- **R-V-04**: orden de ejecución cheap → expensive (heredado de F112 §6): schema → densidad → IR → Mermaid → AP.
- **R-V-05**: todo validador se ejecuta sin red salvo `validate_destinations.py` (F77/V103).

---

## §6 · Modos de ejecución

Tres modos aceptados por todos los validadores nuevos y por `run_all.py`:

- `--note <path>` — un archivo único (`.nm` / `.md` / `.note-ir.json` / `sdm.json` / `ledger.json` / `profile.yaml`).
- `--notes-dir <path>` — carpeta con notas; el validador itera `*.md` / `*.nm` / `*.note-ir.json` (recursivo).
- `--workdir <path>` — directorio `.notes-work/<hash>/`; el validador detecta por convención (`sdm.json` + `ir/` + `manifest.json`) y carga `profile.yaml` si existe.

`run_all.py` traduce el modo a la batería correspondiente (§T3 del plan).

---

## §7 · Wirings y referencias cruzadas

- **F11** — `validate_profile.py` consume `schemas/profile.schema.json`.
- **F12** — `validate_notemark.py` consume la gramática EBNF.
- **F13** — `validate_sdm.py` consume `schemas/sdm.schema.json`.
- **F15** — `validate_ledger.py` consume `schemas/ledger.schema.json`.
- **F47** — `validate_properties.py` consume `schemas/properties.schema.json`.
- **F49** — `validate_ir.py` (preexistente) emite JSON compatible desde F113.
- **F63** — `cross_target.py` invocado por `validate_destinations.py`.
- **F66/F67** — `mermaid.py` mantiene su shape JSON.
- **F69** — `monospace_diagrams.py` implementa las reglas F69.
- **F72** — `contrast_check.py` mantiene su shape.
- **F75** — `validate_lengths.py` consulta los patrones de `note-templates.md` por tipo.
- **F76** — `density_check.py` mantiene su shape JSON.
- **F100** — `validate_links.py` regla V-LK-02 (F100 §3 S4: ≥ 5 palabras introductorias).
- **F102**–**F105** — `self_eval_check`, `error_log_check`, `study_paths_check`, `goal_profile_check`.
- **F114** — quality gate agrega los issues al reporte.
- **F118** — corre `evals/validator-suite-sample/run_eval.py`.

---

## §8 · Anti-patrones (AP-V-1..5)

- **AP-V-1**: emitir texto libre en stdout en lugar de JSON cuando `--json` está activo.
- **AP-V-2**: marcar `severity: error` para reglas configurables; usar `warning`.
- **AP-V-3**: ignorar `profile.yaml` y aplicar defaults globales — viola R-V-04.
- **AP-V-4**: omitir `node` cuando el issue es global — siempre declarar al menos `file`.
- **AP-V-5**: usar regex ad-hoc en lugar del JSON Schema cuando existe schema normativo.

---

## §9 · Verificación al cierre de la fase

- `wc -l references/10-quality/validators.md` ≤ 400 líneas.
- 11 validadores nuevos creados en `scripts/validate/`.
- 1 orquestador `run_all.py`.
- Batería `evals/validator-suite-sample/` con 9 categorías × ≥ 3 defectos (≥ 27 fixtures) + ≥ 5 golden del repo.
- `evals/validator-suite-sample/run_eval.py` con **3/3 PASS**.

**Criterios de aceptación del ROADMAP F113:**

1. _Detecta el 100 % de una batería de defectos inyectados._ → `run_eval.py` C1 PASS: cada `(validador, fixture)` produce ≥ 1 issue de severidad `error|warning` con `rule_id` correcto.
2. _Cero falsos positivos sobre los ejemplos del repo._ → `run_eval.py` C2 PASS: 0 issues de severidad `error` sobre los golden.
3. _Reporta archivo, nodo y regla violada._ → `run_eval.py` C3 PASS: 100 % de issues emitidos por C1 tienen `file`, `node`, `rule_id` no vacíos y formato `V-<CAT>-NNN`.

---

## §10 · Cambios permitidos

- Añadir nuevas reglas (`V-<CAT>-NNN`) sin reabrir F113 si no rompen la shape.
- Añadir nuevos validadores siguiendo el contrato F113 (severidades, exit codes, JSON shape).
- Añadir nuevos campos al JSON con `schema_version` bumped.
- Cambiar un `warning` a `error` solo si la regla ya estaba documentada como tal.

Reabren F113:
- Cambiar el contrato de exit codes.
- Añadir un nivel de severidad.
- Romper R-V-01..05.
- Cambiar el prefijo de `rule_id`.