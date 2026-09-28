# `evals/cheatsheet-sample/` — Fase 90 `cheatsheet`

Eval de la Fase 90 — tipo de nota `cheatsheet`. Verifica que cada entrada de
`## Comandos` enlaza a una nota (criterio #1 y #2), que las tablas tienen ≥ 10
filas (F75 §6.13), y que no contiene párrafos narrativos > 50 palabras
(criterio #3).

## Estructura

| Carpeta / archivo | Rol |
|---|---|
| `notes/postgres-cheatsheet.md` | DB: PostgreSQL 16 con 12 comandos + 6 atajos + 3 errores comunes. |
| `notes/docker-cheatsheet.md` | Containers: Docker 25 con 12 comandos + 8 atajos + 3 errores comunes. |
| `notes/git-cheatsheet.md` | VCS: Git 2.46 con 12 comandos + 6 atajos + 3 errores comunes. |
| `build_fixtures.py` | Regenera las 3 notas. `--check` ejecuta `density_check.py --strict`. |
| `run_eval.py` | Batería de 6 sub-criterios (ver abajo). |

## Modo de uso

```bash
# Regenera fixtures + evalúa.
python3 evals/cheatsheet-sample/run_eval.py --regen

# Solo evalúa (asume fixtures ya generadas).
python3 evals/cheatsheet-sample/run_eval.py

# Solo regenera.
python3 evals/cheatsheet-sample/build_fixtures.py
python3 evals/cheatsheet-sample/build_fixtures.py --check
```

## Batería (6 sub-criterios)

| # | Sub-criterio | Verifica |
|---|---|---|
| C1 | `cheatsheet.md` existe, ≤ 500 líneas, contiene las 9 secciones canónicas (§1-§9). | Estructura normativa del doc. |
| C2 | Cada fila de `## Comandos` tiene `[[note:id]]` o `[[term:X]]` apuntando a la nota que desarrolla el comando. | **Criterios ROADMAP #1 y #2**. |
| C3 | `## Comandos` tiene ≥ 10 filas (F75 §6.13). | Densidad mínima. |
| C4 | Sin párrafos narrativos > 50 palabras (criterio #3). | Sin prosa. |
| C5 | Los 3 fixtures pasan `density_check.py --strict` exit 0. | R1-R8 de F76. |
| C6 | `SKILL.md` §5.2 fila `cheatsheet` y `references/05-note-types/README.md` ya no marcan `[pendiente F90]`. | Wirings cerrados. |

## Salida esperada

```
PASS 6/6
  [PASS] C1-doc-structure
  [PASS] C2-each-row-has-link
  [PASS] C3-min-rows-in-table
  [PASS] C4-no-long-prose
  [PASS] C5-density-check
  [PASS] C6-wirings-closed
```

## Wirings (fases previas)

- **F45** `references/04-authoring/block-directives.md` — directivas `:::warning`, `:::tip`; exenta de frecuencia mínima de callouts (F75 §6.13).
- **F46** `references/04-authoring/inline-marks.md` — `[[note:id]]` por entrada (criterio #2).
- **F47** `references/04-authoring/properties.md` — frontmatter; `source-bearing` recomendado.
- **F75** `references/07-visual/note-templates.md` — cabecera, apertura/cierre común, §6.13 patrón resumido + exención de callouts.
- **F76** `references/07-visual/density.md` + `density_check.py` — reglas R1-R8.
- **F78** `references/05-note-types/concept.md` — paraguas común; cheatsheet deriva de notas concept.
- **F79** `references/05-note-types/api-reference.md` — cheatsheet deriva de API references.
- **F80** `references/05-note-types/procedure.md` — cheatsheet deriva de procedures.
- **F82** `references/05-note-types/error-troubleshooting.md` — errores comunes con `[[note:]]`.
- **F89** `references/05-note-types/glossary-term.md` — atajos con `[[term:X]]`.

## Sin dependencias externas

Python 3.9+ stdlib puro. Las 3 notas se generan inline en `build_fixtures.py`
para evitar divergencia entre fixtures y la regla que verifican.
