# `evals/error-troubleshooting-sample/` — Fase 82 `error-troubleshooting`

Eval de la Fase 82 — tipo de nota `error-troubleshooting`. Verifica que el
mensaje literal se conserva (criterio #1), cada error tiene causa + solución
(criterio #2), y los confundibles se enlazan mutuamente (criterio #3).

## Estructura

| Carpeta / archivo | Rol |
|---|---|
| `notes/postgres-connection-errors.md` | DB: 4 errores de conexión psql (Connection refused, too many connections, password auth failed, database does not exist). 4 confundibles cruzados. |
| `notes/k8s-pod-pending-errors.md` | k8s: 4 errores de Pod Pending (ImagePullBackOff, Insufficient cpu, Insufficient memory, ErrImageNeverPull). 4 confundibles. |
| `notes/docker-permission-errors.md` | Docker: 3 errores de permisos de socket (permission denied, EACCES, Cannot connect). 3 confundibles. |
| `build_fixtures.py` | Regenera las 3 notas. `--check` ejecuta `density_check.py --strict`. |
| `run_eval.py` | Batería de 6 sub-criterios (ver abajo). |

## Modo de uso

```bash
# Regenera fixtures + evalúa.
python3 evals/error-troubleshooting-sample/run_eval.py --regen

# Solo evalúa (asume fixtures ya generadas).
python3 evals/error-troubleshooting-sample/run_eval.py

# Solo regenera.
python3 evals/error-troubleshooting-sample/build_fixtures.py
python3 evals/error-troubleshooting-sample/build_fixtures.py --check
```

## Batería (6 sub-criterios)

| # | Sub-criterio | Verifica |
|---|---|---|
| C1 | `error-troubleshooting.md` existe, ≤ 500 líneas, contiene las 9 secciones canónicas (§1-§9). | Estructura normativa del doc. |
| C2 | Cada mensaje literal del SDM aparece en `## Síntomas` con bloque `code` Y tiene fila en `## Tabla índice`. | **Criterio ROADMAP #1**. |
| C3 | Cada error listado en `## Síntomas` tiene `### Mensaje N:` en `## Causa raíz` Y en `## Solución` no vacíos. | **Criterio ROADMAP #2**. |
| C4 | Cada confundible listado como `[[note:X]]` en una nota A aparece como backlink (`[[note:A]]`) en la nota X del corpus (mutuismo bidireccional). | **Criterio ROADMAP #3**. |
| C5 | Los 3 fixtures pasan `density_check.py --strict` exit 0. | R1-R8 de F76. |
| C6 | `SKILL.md` §5.2 fila `error-troubleshooting` y `references/05-note-types/README.md` ya no marcan `[pendiente F82]`. | Wirings cerrados. |

## Salida esperada

```
PASS 6/6
  [PASS] C1-doc-structure
  [PASS] C2-literal-messages-and-index
  [PASS] C3-cause-and-solution-per-error
  [PASS] C4-bidirectional-confundibles
  [PASS] C5-density-check
  [PASS] C6-wirings-closed
```

## Wirings (fases previas)

- **F45** `references/04-authoring/block-directives.md` — directivas `:::danger`, `:::warning`, `:::tip`, `:::step`, `:::diagram`.
- **F46** `references/04-authoring/inline-marks.md` — `{src:blk_xxxx}` por mensaje literal; `[[note:id]]` para confundibles.
- **F47** `references/04-authoring/properties.md` — frontmatter; `source-bearing` obligatorio.
- **F66** `references/07-visual/mermaid-portable.md` — Mermaid en `## Árbol de diagnóstico`.
- **F75** `references/07-visual/note-templates.md` — cabecera, apertura/cierre común, §6.5 patrón resumido + anti-patrón "Solución sin Causa raíz antes".
- **F76** `references/07-visual/density.md` + `density_check.py` — reglas R1-R8.
- **F78** `references/05-note-types/concept.md` — paraguas común.
- **F79** `references/05-note-types/api-reference.md` — errores de API referenciados aquí.
- **F80** `references/05-note-types/procedure.md` — solutions complejas como procedure.
- **F81** `references/05-note-types/configuration.md` — errores derivados de config incorrecta.

## Sin dependencias externas

Python 3.9+ stdlib puro. Las 3 notas se generan inline en `build_fixtures.py`
para evitar divergencia entre fixtures y la regla que verifican.
