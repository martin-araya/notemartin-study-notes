# Compatibilidad de artefactos entre versiones — `COMPATIBILITY.md`

> Documento normativo de F123. Define la matriz de compatibilidad: qué versión del paquete acepta qué versión de cada artefacto. Complementa [`VERSIONING.md`](VERSIONING.md) §2 (cuándo bumpear) y [`CHANGELOG.md`](CHANGELOG.md) (bitácora).

## Índice

1. [Regla general](#1-regla-general) · 2. [Matriz por artefacto](#2-matriz-por-artefacto) · 3. [Cómo se valida](#3-cómo-se-valida) · 4. [Cómo se extiende](#4-cómo-se-extiende) · 5. [Cambios permitidos](#5-cambios-permitidos)

## 1. Regla general

**Validators de versión `X.Y.Z` aceptan artefactos producidos con versiones `>= X.0.0` y `< (X+1).0.0` (mismo major).**

- Mismo major, minor o patch diferente: ✓ acepta.
- Major más nuevo: warning (forward compat opcional, configurable).
- Major más viejo: ✗ reject.
- Pre-release (`-dev`, `-rc.N`): aceptado como `0.0.0-dev` en el cálculo de compat — los pre-releases no son estables.

**Pre-1.0**: la regla se relaja — validators aceptan cualquier versión `< 1.0.0` con el mismo major.

## 2. Matriz por artefacto

13 schemas declarados en `skill/notemartin-study-notes/schemas/` (F11-F16, F40, F44, F47, F112, etc.) + NoteMark como texto plano sin schema JSON. La versión del paquete (X.Y.Z) y la de cada schema son independientes pero se acotan por el contrato.

| Artefacto | Schema | schema_version actual | Mismo major (cualquier minor/patch) | Major más nuevo | Major más viejo |
|---|---|---|---|---|---|
| SDM | `schemas/sdm.schema.json` | 1.0.0 | ✓ | warning | ✗ reject |
| IR | `schemas/note-ir.schema.json` | 1.0.0 | ✓ | warning | ✗ reject |
| NoteMark | (texto, contrato en `references/04-authoring/notemark.md`) | (sin schema_version propio) | ✓ | warning | ✗ reject |
| Ledger | `schemas/ledger.schema.json` | 2.0.0 | ✓ | warning | ✗ reject |
| NotePlan | `schemas/note-plan.schema.json` | 1.0.0 | ✓ | warning | ✗ reject |
| Glossary | `schemas/glossary.schema.json` | 1.0.0 | ✓ | warning | ✗ reject |
| Concept-Graph | `schemas/concept-graph.schema.json` | 1.0.0 | ✓ | warning | ✗ reject |
| Conflicts | `schemas/conflicts.schema.json` | 1.0.0 | ✓ | warning | ✗ reject |
| Profile | `schemas/profile.schema.json` | 1.0.0 | ✓ | warning | ✗ reject |
| Quality-Gate | `schemas/quality-gate.schema.json` | 1.0.0 | ✓ | warning | ✗ reject |
| Manifest | `schemas/manifest.schema.json` | 1.0.0 | ✓ | warning | ✗ reject |
| Book-Map | `schemas/book-map.schema.json` | 1.0.0 | ✓ | warning | ✗ reject |
| Book-State | `schemas/book-state.schema.json` | 1.0.0 | ✓ | warning | ✗ reject |
| Chunk-State | `schemas/chunk-state.schema.json` | 1.0.0 | ✓ | warning | ✗ reject |
| Version-Delta | `schemas/version-delta.schema.json` | 1.0.0 | ✓ | warning | ✗ reject |

**Notas:**
- `ledger.schema.json` está en `2.0.0` mientras los demás están en `1.0.0`. Esto refleja el ADR-0002 (F38 bumpea de 1.0.0 a 2.0.0 sin que el resto bumpe). La regla del major aplica **independiente por artefacto**: ledger 2.x no es lo mismo que sdm 2.x.
- NoteMark no tiene `schema_version` formal; su contrato es prosa en `references/04-authoring/notemark.md`. La compat se declara ahí por separado.

## 3. Cómo se valida

`scripts/util/validate_*.py` (F13–F16) enforza el `schema_version` const de cada schema:

```bash
python3 scripts/util/validate_sdm.py --validate <sdm.json>
# exit 0 si schema_version == "1.0.0"
# exit 1 con mensaje si difiere
```

Para validación cross-version (artefacto X producido con versión A, validado con versión B), usar el script F123 `scripts/check_version.py --compat-check`:

```bash
python3 scripts/check_version.py --compat-check --artifact-type ledger --produced-version 2.0.0 --validating-version 0.1.0-dev
# Salida: OK | WARNING (forward compat) | REJECT
```

Esta funcionalidad queda como mejora post-F123; el script base valida solo `VERSION` ↔ `manifest.json::version` ↔ `schema_version` const.

## 4. Cómo se extiende

Procedimiento al bumpear de major `X.0.0` a `Y.0.0` (donde `Y = X + 1`):

1. **Editar el schema afectado**: cambiar `"const": "X.0.0"` por `"const": "Y.0.0"`. Si cambia la estructura, también las propiedades.
2. **Editar `VERSION`**: bumpear a `Y.0.0`.
3. **Editar `CHANGELOG.md`**: añadir entrada `## [Y.0.0]` con `### Changed` (contrato) + `### Removed` (artefactos v1.x incompatibles) si aplica.
4. **Editar `COMPATIBILITY.md`**: actualizar la fila del artefacto (`X.0.0` → `Y.0.0`); los validadores de `Y.0.0` ahora rechazan artefactos `< Y.0.0`.
5. **Migración** (si la hay): añadir `scripts/util/migrate_vX_to_vY.py` y documentar el flujo en el CHANGELOG.
6. **Tests**: actualizar `evals/<fase>-sample/` con fixtures que reflejen el nuevo formato.

Para bumps menores (D4): añadir fila a la matriz si es un artefacto nuevo; bumpear `schema_version` const del schema afectado (e.g. de `1.0.0` a `1.1.0`).

Para bumps patch (D5): no requiere actualización de COMPATIBILITY.md.

## 5. Cambios permitidos

**No reabren F123:**
- Añadir una fila a la matriz para un nuevo artefacto (e.g. `IR-mermaid-extension` cuando se introduzca).
- Documentar una nueva regla de compat aditiva en §1 (e.g. "los artefactos con `-dev` se aceptan solo en versiones `-dev`").
- Corregir el `schema_version` actual de un artefacto en la tabla (sin cambiar la regla).

**Reabren F123:**
- Cambiar la regla general de §1 (mismo major acepta vs accept all minors).
- Eliminar una fila de la matriz sin reemplazo (rompe contrato implícito).
- Cambiar el formato de la tabla (e.g. añadir columnas incompatibles con la regla D6).
- Cambiar el procedimiento de extensión de §4.
