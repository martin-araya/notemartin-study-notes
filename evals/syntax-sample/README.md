# `evals/syntax-sample/` — Fase 84 `syntax`

Eval de la Fase 84 — tipo de nota `syntax`. Verifica que la gramática BNF/EBNF
cubre todas las cláusulas (incluyendo opcionales), que hay contraejemplos con
el error literal del parser (criterio #2), y que los diagramas de sintaxis
están presentes (criterio #3).

## Estructura

| Carpeta / archivo | Rol |
|---|---|
| `notes/postgresql-select.md` | SQL: BNF del `SELECT` PostgreSQL 16 con 12 cláusulas (10 obligatorias + opcionales raras: DISTINCT ON, GROUP BY (), WINDOW, FETCH, FOR UPDATE). Cubre criterio #1 + #2 + #3. |
| `notes/kubernetes-pod-spec.md` | k8s: YAML schema-like del `Pod core/v1` con 15+ propiedades opcionales (tolerations, affinity, lifecycle, etc.). Cubre criterio #1 + #3. |
| `notes/curl-syntax.md` | CLI: convención cURL con 20+ opciones (cortas y largas, incluyendo raras: `--http3`, `--rate`, `--fail-early`). Cubre criterio #1 + #2 + #3. |
| `build_fixtures.py` | Regenera las 3 notas. `--check` ejecuta `density_check.py --strict`. |
| `run_eval.py` | Batería de 6 sub-criterios (ver abajo). |

## Modo de uso

```bash
# Regenera fixtures + evalúa.
python3 evals/syntax-sample/run_eval.py --regen

# Solo evalúa (asume fixtures ya generadas).
python3 evals/syntax-sample/run_eval.py

# Solo regenera.
python3 evals/syntax-sample/build_fixtures.py
python3 evals/syntax-sample/build_fixtures.py --check
```

## Batería (6 sub-criterios)

| # | Sub-criterio | Verifica |
|---|---|---|
| C1 | `syntax.md` existe, ≤ 500 líneas, contiene las 9 secciones canónicas (§1-§9). | Estructura normativa del doc. |
| C2 | `## Cláusula por cláusula` tiene ≥ 5 sub-secciones H3 (cubre cláusulas obligatorias y opcionales). | **Criterio ROADMAP #1**. |
| C3 | `## Contraejemplos` tiene ≥ 1 `:::warning` con input + error literal del parser. | **Criterio ROADMAP #2**. |
| C4 | `## Diagramas de sintaxis` tiene `:::diagram` Mermaid con ≥ 3 nodos. | **Criterio ROADMAP #3**. |
| C5 | Los 3 fixtures pasan `density_check.py --strict` exit 0. | R1-R8 de F76. |
| C6 | `SKILL.md` §5.2 fila `syntax` y `references/05-note-types/README.md` ya no marcan `[pendiente F84]`. | Wirings cerrados. |

## Salida esperada

```
PASS 6/6
  [PASS] C1-doc-structure
  [PASS] C2-optional-clauses-documented
  [PASS] C3-counter-examples-present
  [PASS] C4-syntax-diagrams
  [PASS] C5-density-check
  [PASS] C6-wirings-closed
```

## Wirings (fases previas)

- **F45** `references/04-authoring/block-directives.md` — directivas `:::example`, `:::warning`, `:::tip`, `:::diagram`.
- **F46** `references/04-authoring/inline-marks.md` — `{src:blk_xxxx}` por cláusula; `[[term:nombre]]` para keywords.
- **F47** `references/04-authoring/properties.md` — frontmatter canónico; `source-bearing` obligatorio.
- **F66** `references/07-visual/mermaid-portable.md` — Mermaid portable en `## Diagramas de sintaxis`.
- **F75** `references/07-visual/note-templates.md` — cabecera, apertura/cierre común, §6.7 patrón resumido.
- **F76** `references/07-visual/density.md` + `density_check.py` — reglas R1-R8.
- **F78** `references/05-note-types/concept.md` — paraguas común.
- **F79** `references/05-note-types/api-reference.md` — `syntax` documenta la forma; `api-reference` lista operaciones.
- **F82** `references/05-note-types/error-troubleshooting.md` — errores de parseo se enlazan a troubleshooting.

## Sin dependencias externas

Python 3.9+ stdlib puro. Las 3 notas se generan inline en `build_fixtures.py`
para evitar divergencia entre fixtures y la regla que verifican.
