# Contribución y mantenimiento — `CONTRIBUTING.md`

> Documento normativo de la **Fase 124** del roadmap. Define cómo contribuir al proyecto `notemartin-study-notes`: estilo de las referencias, proceso para proponer una regla nueva, política de ejemplos multi-dominio, checklist de PR, y contrato de ingesta externa.
>
> Documentos complementarios: [`VERSIONING.md`](VERSIONING.md) (F123), [`docs/repo-layout.md`](docs/repo-layout.md) (F5), [`docs/skill-anatomy.md`](docs/skill-anatomy.md) (F2), [`skill/notemartin-study-notes/references/00-pipeline/contributing.md`](skill/notemartin-study-notes/references/00-pipeline/contributing.md) (F124 §1, estilo de referencias), [`docs/adr/`](docs/adr/) (ADRs del proyecto), [`ROADMAP.md`](ROADMAP.md) (estado del proyecto), [`scripts/check_pr.py`](scripts/check_pr.py) (F124 §4, gate de CI).

## Índice

1. [Estilo de referencias](#1-estilo-de-referencias) · 2. [Proponer una regla nueva (triada)](#2-proponer-una-regla-nueva-triada) · 3. [Política de ejemplos multi-dominio](#3-política-de-ejemplos-multi-dominio) · 4. [Checklist de PR](#4-checklist-de-pr) · 5. [Contrato de ingesta externa](#5-contrato-de-ingesta-externa) · 6. [Proceso de revisión](#6-proceso-de-revisión) · 7. [Mantenimiento a largo plazo](#7-mantenimiento-a-largo-plazo) · 8. [Cambios permitidos sin reabrir F124](#8-cambios-permitidos-sin-reabrir-f124)

## §1 · Estilo de referencias

El estilo detallado vive en [`skill/notemartin-study-notes/references/00-pipeline/contributing.md`](skill/notemartin-study-notes/references/00-pipeline/contributing.md) (F124). Resumen ejecutivo:

- **Idioma**: español para prosa, inglés para terminología técnica cuando es el término canónico (`IR`, `SDM`, `NoteMark`, `ledger`).
- **Voz**: impersonal. Sin "tú", sin "vosotros". Evitar "se recomienda"; preferir "el agente debe" o "el script debe".
- **Tono**: instructivo, no argumentativo. Las justificaciones de decisiones viven en ADRs, no en `references/`.
- **Estructura por archivo** (patrón ya en los 13 archivos de `references/0X-*`):
  - Título H1 (`# nombre`).
  - Índice de 5-15 secciones `## §N · <título>`.
  - Cierre con `## §N · Cómo verificar + cambios permitidos` (sección final obligatoria; ver D1).
- **No emojis** en prosa (INV-06); solo en callouts y directivas cuando son sintaxis.
- **No tablas decorativas**: solo cuando la comparación aporta densidad de información.
- **No segunda persona**: "el agente" o "el script" en lugar de "tú".

Reglas duras adicionales:

- Toda regla nueva referencia al menos una `INV-NN` o número de fase (`F44`, `F75`).
- Toda decisión de arquitectura con impacto en ≥ 2 archivos se acompaña de un ADR.

## §2 · Proponer una regla nueva (triada)

Cada regla nueva requiere una **triada obligatoria**:

1. **Motivación** (caso de fallo real). ¿Qué falla hoy sin esta regla? Describe un caso concreto, no "podría fallar en algunos casos". El caso de fallo debe ser verificable hoy.
2. **Definición formal**. ¿Qué dice exactamente la regla? Cite la invariante (`INV-xx`) o el número de fase. Si la regla tiene excepciones, declara las condiciones.
3. **Caso de prueba**. Un archivo de test (en `evals/<fase>-sample/` o `tests/`) que:
   - **Sin la regla**: falla (`exit != 0` o assertion fail).
   - **Con la regla**: pasa.

Sin triada completa, el PR se cierra con el motivo "Falta triada".

**Si la regla es breaking** (cambio de contrato): abrir un ADR antes del PR (per `docs/adr/README.md`).

Plantilla de ADR: `docs/adr/ADR-NNNN-<slug>.md`. Ejemplo: `docs/adr/ADR-0001-units-closed-enum.md` (F37).

Ejemplo concreto de triada:

- **Motivación**: "Sin la regla INV-08, el agente puede declarar `must-keep` sin que la sección X.Y.Z aparezca en el SDM; cobertura falsa."
- **Definición**: "Cada unidad `must-keep` del ledger debe tener `source_block_ids` resoluble al SDM y `target_note` no nulo."
- **Caso de prueba**: `evals/ledger-sample/negative-pending.json` valida que sin la regla el ledger permite el estado; con la regla, falla.

## §3 · Política de ejemplos multi-dominio (INV-15)

Cada ejemplo o test nuevo:

- **Cubre ≥ 2 categorías distintas** del corpus (ver [`docs/galaxy.md`](docs/galaxy.md) con las 14 categorías de F6).
- Si introduce un nuevo dominio, también añade ≥ 1 fuente al corpus si es accesible.
- Si cubre una sola categoría, justifica explícitamente (p. ej. test unitario no necesita multi-dominio). Justificación: frontmatter `rationale: single-domain-test`.
- Las anclas `{src:blk_xxx}` siguen al SDM (per `references/02-source-model/`).

Política de cobertura global:

- Las 14 categorías del ROADMAP (F6) deben tener al menos 1 test o ejemplo en `evals/` o `examples/`.
- Las 4 categorías del ROADMAP F120 (documentación de producto, libro técnico, PDF escaneado, API reference) deben tener un ejemplo end-to-end.

Estado actual (2026-09-30):

- 4 ejemplos end-to-end: `01-postgresql-chapter`, `02-database-internals-chapter`, `13-internet-archive-scan-hostil`, `06-kubernetes-api-ref`.
- 6 casos en suite de evals: cubren 4 categorías + 2 hostiles.
- Categorías pendientes de ejemplo end-to-end: 10/14 (transcripción, README, diapositivas, fórmulas, ISO C++, Docker CLI, etc.).

## §4 · Checklist de PR

Ejecutar `python3 scripts/check_pr.py` antes de pedir review. El script valida **10 items** automáticamente:

| # | Item | Tipo | Bloquea |
|---|---|---|---|
| 1 | No archivos en denylist (`__pycache__`, `*.pyc`, `dist/*.skill`, etc.) | auto | sí (FAIL) |
| 2 | No archivos nuevos fuera de la regla de ubicación (per `docs/repo-layout.md` §5) | auto | sí (FAIL) |
| 3 | `python3 scripts/check_version.py --all` exit 0 | auto | sí (FAIL) |
| 4 | `python3 scripts/check_deps.py` no exit 1 | auto | sí (FAIL) |
| 5 | Si toca `references/**`: cada archivo modificado tiene sección "Cómo verificar + cambios permitidos" | semi-auto | no (WARN) |
| 6 | Si toca `schemas/**`: schema_version bumped coherentemente | semi-auto | no (WARN) |
| 7 | Si toca `skill/notemartin-study-notes/scripts/`: aparece en `scripts/README.md` con Dependencias | semi-auto | no (WARN) |
| 8 | Si introduce regla nueva (INV-NN): triada motivación + definición + prueba presente | semi-auto | no (WARN) |
| 9 | Si añade un ejemplo: INV-15 (≥ 2 categorías) o justificación explícita | semi-auto | no (WARN) |
| 10 | ADRs al día si el PR toca un contrato | semi-auto | no (WARN) |

**Modo soft gate** (default): exit 0 con warnings. El revisor humano decide si aceptar los warnings o pedir cambios. **Modo `--strict`**: trata WARN como FAIL.

Salida del script:
- `[OK]   ...` (verde)
- `[WARN] ...` (amarillo, no bloquea)
- `[FAIL] ...` (rojo, sí bloquea)

Exit codes: 0 (PASS o WARN), 1 (FAIL), 2 (USAGE).

## §5 · Contrato de ingesta externa

Ver [`docs/external-ingest-contract.md`](docs/external-ingest-contract.md). Resumen: el conversor externo produce un `regions.json` (per F22) + `summary.json` (per F28/F17) + opcionalmente `triage.json` (per F17) en el workdir del agente. **Tool-independent**: ningún lenguaje o librería específicos. Cualquier conversor válido produce el mismo contrato.

Para registrar un conversor first-class: implementa el contrato, añade test de integración en `evals/<fase>-sample/`, documenta en ADR, y abre PR con la triada.

## §6 · Proceso de revisión

Un PR se acepta cuando:

- Pasa `scripts/check_pr.py` con exit 0 (todos los items OK o WARN).
- Tiene al menos 1 revisión humana aprobatoria.
- Si es breaking: incluye ADR aprobado + entrada `## [X.Y.Z]` en CHANGELOG (per F123).
- Si toca la skill (`references/`, `SKILL.md`, `schemas/`, `scripts/` del paquete): evidencia de no-regresión adjunta (per F119 `release.md` §6 paso 5).

Tiempos de revisión (orientativos):

- Bugfix trivial (1-2 archivos): 1 día.
- Nueva regla / fix: 3 días.
- Cambio de contrato / ADR: 1 semana.

Cuando un revisor pide cambios, el autor responde en el mismo PR (no en un nuevo) y re-ejecuta `scripts/check_pr.py` antes de re-pedir review.

## §7 · Mantenimiento a largo plazo

- Cada release sigue el proceso de [`docs/release.md`](docs/release.md) (F119 + F122 + F123): paso 0.5 validar versionado, paso 1.5 empaquetar, paso 4 gate de release, paso 5 archivar evidencia, paso 6 tag.
- El [`CHANGELOG.md`](CHANGELOG.md) (F123) registra cada release con sus fases cerradas.
- Las ADRs viven para siempre; nunca se borran, solo se marcan `superseded` con un nuevo ADR que las reemplaza.
- El corpus ([`evals/corpus/`](evals/corpus/), F6) se actualiza cuando hay fuentes nuevas accesibles.
- La suite de evals (F118) y la regresión (F119) corren antes de cada merge a `main`.
- Los scripts de validación (`check_deps`, `check_version`, `check_pr`, `build_skill`, `smoke_test`) son **tools independientes**: pueden correr en CI, en local, o por un humano.

## §8 · Cambios permitidos sin reabrir F124

**No reabren F124:**
- Añadir un item al checklist de §4 si no rompe la regla D4 (soft gate).
- Cambiar el wording de cualquier sección (typos, redacción).
- Añadir un ADR nuevo en `docs/adr/`.
- Cerrar un ADR con un ADR supersededor.
- Añadir una nueva categoría de ejemplo o test, siguiendo INV-15.

**Reabren F124:**
- Cambiar la triada de §2.
- Cambiar la regla INV-15 (≥ 2 categorías).
- Cambiar el contrato de ingesta externa de `docs/external-ingest-contract.md`.
- Cambiar la regla del soft gate (D4): pasar a hard gate es decisión de F124.
- Eliminar `references/00-pipeline/contributing.md`.
