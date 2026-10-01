# Proceso de release — `docs/release.md`

> Documento normativo de la Fase 119 del roadmap. Define los 6 pasos canónicos para cerrar un release de `notemartin-study-notes`, qué evidencia se archiva, y cómo un PR que toca la skill se acepta sin regresión.
>
> Documentos complementarios: `evals/regression/README.md` y `variance.md` (F119), `evals/suite/README.md` y `SCHEMA.md` (F118), `skills/AGENT.md` §11 (pruebas "de la skill").

## 1. Definición operativa

- **Release:** tag semántico (string) que identifica un commit como entregable. La política de versionado semántico vive en F123; F119 no la impone.
- **Baseline:** ejecución completa de la suite + regresión sobre el último release tag aceptado.
- **Candidate:** ejecución completa de la suite + regresión sobre el commit candidato a release.
- **Evidencia de no-regresión:** los 4 archivos en `runs/<release-tag>/evidence/` (ver §5).

## 2. Requisitos previos

Antes de iniciar el proceso de release, verificar:

1. **Sin cambios sin commit:** `git status` limpio (cambios staged o unstaged rompen la reproducibilidad).
2. **Sin cambios en `variance_thresholds.yaml` sin ADR:** si los umbrales cambian, el diff con baseline es por config, no por skill.
3. **`SCHEMA_VERSION` consistente:** el `schema_version` de `report.json`, `variance.json` y `gate.json` debe ser el mismo entre candidate y baseline. Cambios incompatibles reabren F118 o F119.
4. **Set de regresión estable:** ningún caso nuevo en el set sin haber pasado ≥ 3 corridas consecutivas (per `evals/regression/SET.md` §3).

## 3. Los 6 pasos del release

### Paso 0.5 · Validar versionado (F123)

Antes del paso 1, validar que el versionado del paquete es coherente:

```bash
# ¿Qué versión vamos a releasear?
cat VERSION

# ¿El cambio propuesto (MAJOR/MINOR/PATCH) coincide con los schemas modificados?
python3 scripts/check_version.py --propose-bump

# ¿Todo OK?
python3 scripts/check_version.py --all
```

Si el bump propuesto no coincide con el tipo de cambio realizado, **abortar el release** y abrir un ADR (ver `VERSIONING.md` §5).

### Paso 1 · Verificar prerrequisitos

```bash
# 1a. Estado git limpio.
git status --porcelain
# Salida esperada: vacío.

# 1b. Branch correcto.
git rev-parse --abbrev-ref HEAD   # debe coincidir con la convención del repo

# 1c. Diff contra el último tag.
git diff <last-release-tag>..HEAD --stat
```

Si el diff toca `variance_thresholds.yaml`, abrir ADR antes de continuar.

### Paso 1.5 · Empaquetar la skill (F122)

Genera el `.skill` reproducible y verifica que pasa el caso de humo. Este paso se ejecuta tanto sobre baseline (paso 2) como sobre candidate (paso 3).

```bash
# Build del paquete
python3 scripts/build_skill.py --version <release-tag>

# Smoke test (5 verificaciones obligatorias: unpack, SKILL.md frontmatter,
# references resolubles, check_deps.py corre, tamaño ≤ 8 MB)
python3 scripts/smoke_test.py --skill dist/notemartin-study-notes-<release-tag>.skill
```

Si el smoke test falla: abortar el release. El `.skill` no se publica.

### Paso 2 · Generar `baseline`

Sobre el último release tag aceptado:

```bash
git checkout <last-release-tag>
python evals/suite/runner/run_regression.py \
  --case-dir evals/regression/cases/ \
  --release-tag <last-release-tag> \
  --agent-command "<comando>" \
  --out-dir evals/runs/<last-release-tag>/

# El comando anterior también produce report.json si se invoca drive_suite.py.
python evals/suite/runner/drive_suite.py \
  --run-id <last-release-tag> \
  --agent-command "<comando>"
```

Resultado esperado:
- `evals/runs/<last-release-tag>/report.json` (de F118).
- `evals/runs/<last-release-tag>/variance.json` (de F119).
- `evals/runs/<last-release-tag>/cases/<case-id>/run-N/` por cada caso.

### Paso 3 · Generar `candidate`

Sobre el commit candidato:

```bash
git checkout <candidate-commit>
python evals/suite/runner/run_regression.py \
  --case-dir evals/regression/cases/ \
  --release-tag <new-release-tag> \
  --agent-command "<comando>" \
  --out-dir evals/runs/<new-release-tag>/

python evals/suite/runner/drive_suite.py \
  --run-id <new-release-tag> \
  --agent-command "<comando>"
```

### Paso 4 · Correr el gate

```bash
python evals/suite/runner/release_gate.py \
  --candidate evals/runs/<new-release-tag>/report.json \
  --baseline evals/runs/<last-release-tag>/report.json \
  --variance evals/runs/<new-release-tag>/variance.json \
  --regression-set evals/regression/SET.md \
  --out evals/runs/<new-release-tag>/gate.json
```

Resultado esperado: `gate.json::status == "pass"` y exit 0.

Si el gate falla, las 4 condiciones que pueden haber fallado están en `gate.json::reasons[]`. Resolver antes de continuar:
- **variance_within_threshold**: o el cambio introduce varianza real (reabre el cambio) o el umbral es demasiado estricto (edita `variance_thresholds.yaml` con ADR).
- **no_blocking_failures**: hay un caso del set con `approved_rate < 1.0`. Investigar la causa en `variance.json::cases[].approved`.
- **no_regression_flip**: un caso del set pasó de aprobado a no aprobado entre baseline y candidate. Investigar el cambio.
- **no_human_pending**: faltan `human.json` por rellenar. Completar antes del release.

### Paso 5 · Archivar evidencia

Copiar los 4 archivos canónicos al directorio `evidence/` del release:

```bash
mkdir -p evals/runs/<new-release-tag>/evidence/
cp evals/runs/<new-release-tag>/report.json    evals/runs/<new-release-tag>/evidence/
cp evals/runs/<new-release-tag>/variance.json   evals/runs/<new-release-tag>/evidence/
cp evals/runs/<new-release-tag>/diff.json      evals/runs/<new-release-tag>/evidence/
cp evals/runs/<new-release-tag>/gate.json      evals/runs/<new-release-tag>/evidence/
```

Verificar que existen y son no vacíos:

```bash
test -s evals/runs/<new-release-tag>/evidence/report.json
test -s evals/runs/<new-release-tag>/evidence/variance.json
test -s evals/runs/<new-release-tag>/evidence/diff.json
test -s evals/runs/<new-release-tag>/evidence/gate.json
```

### Paso 6 · Tag y push

```bash
git tag -a <new-release-tag> -m "Release <new-release-tag>: ver evidence/ en evals/runs/<new-release-tag>/"
git push origin <new-release-tag>
```

## 4. Aceptación de un PR que toca la skill

Un PR cumple el criterio **C3 del ROADMAP F119** ("todo cambio aceptado tiene evidencia de no-regresión") si y solo si:

1. El PR incluye los 4 archivos de evidencia en `evals/runs/<release-tag>/evidence/` (commit aparte, sin squash).
2. El `gate.json` está en estado `pass`.
3. El revisor del PR firma el cambio tras inspeccionar `diff.json` y `variance.json`.

Si el PR toca:
- `references/` o `SKILL.md`: adjuntar evidencia obligatoria.
- `schemas/`: adjuntar evidencia obligatoria.
- `scripts/` del paquete: adjuntar evidencia obligatoria.
- Solo docs o `evals/` (sin tocar el paquete): evidencia opcional pero recomendada.

## 5. Override humano del gate

Si el gate falla por una razón justificada (umbral demasiado estricto para un caso nuevo, fluctuación aleatoria del modelo, etc.), el humano puede:

1. Editar `variance_thresholds.yaml` con commit + ADR que justifique el cambio.
2. Re-correr el gate (paso 4) sobre el mismo candidate.
3. Si el nuevo gate pasa: archivar el ADR junto a `evidence/overrides.json` con la firma.

El ADR queda referenciado en `evidence/overrides.json::adr`. El gate se respeta: el override es post-gate, no bypass.

## 6. Estructura esperada por release

```
evals/runs/<release-tag>/
├── report.json                       # F118 — resumen de la suite del candidate
├── variance.json                     # F119 — varianza sobre N ejecuciones
├── diff.json                         # F118 — compare_runs.py candidate vs baseline
├── gate.json                         # F119 — decisión del gate
├── evidence/                         # copia inmutable de los 4 archivos para auditoría
│   ├── report.json
│   ├── variance.json
│   ├── diff.json
│   └── gate.json
├── overrides.json                    # opcional — overrides humanos firmados
└── cases/<case-id>/                  # artefactos por caso (F118)
    └── run-N/                        # N ejecuciones (F119)
        ├── workdir/
        ├── assertions.json
        └── human.json
```

## 7. Cambios permitidos sin reabrir F119

- Cambiar el `release-tag` (es dato).
- Añadir evidencia adicional al directorio `evidence/` (sin quitar los 4 canónicos).
- Cambiar `n_runs` en `variance_thresholds.yaml` con ADR si el cambio es > 20 %.

## 8. Cambios que reabren F119

- Cambiar los 4 archivos canónicos de `evidence/` (lista cerrada).
- Cambiar las 4 condiciones del gate.
- Cambiar el comando del agente o el entorno sin ADR (rompe comparabilidad).
- Saltarse pasos del proceso sin override documentado.
