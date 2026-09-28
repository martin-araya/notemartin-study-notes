# `evals/practice-sample/` — Fase 92 `practice` / lab

Eval de la Fase 92 — tipo de nota `practice`. Verifica que cada lab declara
entorno + limpieza (criterio #1), que cada paso destructivo tiene `:::warning`
adyacente (criterio #2), y que cada lab tiene criterio de cuándo omitir
(criterio #3).

## Estructura

| Carpeta / archivo | Rol |
|---|---|
| `notes/practice-postgres-backup.md` | DB: backup + restore con `pg_dump -Fc` + `pg_restore`. Entorno + `DROP DATABASE` con `:::warning` + limpieza + cuándo omitir. |
| `notes/practice-docker-compose.md` | Containers: compose con web (nginx) + db (PostgreSQL). `docker compose down -v` con `:::warning`. |
| `notes/practice-git-rebase.md` | VCS: rebase interactivo (`reword` + `squash` + `pick`). `git push --force` con `:::warning`. |
| `build_fixtures.py` | Regenera las 3 notas. `--check` ejecuta `density_check.py --strict`. |
| `run_eval.py` | Batería de 6 sub-criterios (ver abajo). |

## Modo de uso

```bash
# Regenera fixtures + evalúa.
python3 evals/practice-sample/run_eval.py --regen

# Solo evalúa (asume fixtures ya generadas).
python3 evals/practice-sample/run_eval.py

# Solo regenera.
python3 evals/practice-sample/build_fixtures.py
python3 evals/practice-sample/build_fixtures.py --check
```

## Batería (6 sub-criterios)

| # | Sub-criterio | Verifica |
|---|---|---|
| C1 | `practice.md` existe, ≤ 600 líneas, contiene las 9 secciones canónicas (§1-§9). | Estructura normativa del doc. |
| C2 | Cada fixture tiene `## Entorno` con tabla ≥ 3 componentes Y `## Limpieza` con ≥ 1 paso. | **Criterio ROADMAP #1**. |
| C3 | Cada paso destructivo (`DROP`, `DELETE`, `rm -rf`, `kubectl delete`, `dropdb`, `docker rmi`, `git push --force`) tiene `:::warning` o `:::danger` en la misma sección `## ` (±10 líneas). | **Criterio ROADMAP #2**. |
| C4 | Cada fixture tiene `## Cuándo omitir este lab` con ≥ 1 criterio explícito (`si:`, `(1)`, `omite`). | **Criterio ROADMAP #3**. |
| C5 | Los 3 fixtures pasan `density_check.py --strict` exit 0. | R1-R8 de F76. |
| C6 | `SKILL.md` §5.2 fila `practice` y `references/05-note-types/README.md` ya no marcan `[pendiente F92]`. | Wirings cerrados. |

## Salida esperada

```
PASS 6/6
  [PASS] C1-doc-structure
  [PASS] C2-entorno-and-limpieza
  [PASS] C3-warning-on-destructive
  [PASS] C4-cuando-omitir
  [PASS] C5-density-check
  [PASS] C6-wirings-closed
```

## Wirings (fases previas)

- **F45** `references/04-authoring/block-directives.md` — directivas `:::warning`, `:::danger`, `:::tip`, `:::note`.
- **F46** `references/04-authoring/inline-marks.md` — `{src:blk_xxxx}` por paso del SDM; `[[note:id]]` para referencias.
- **F47** `references/04-authoring/properties.md` — frontmatter con `difficulty` (1-5) enum.
- **F75** `references/07-visual/note-templates.md` — cabecera, apertura/cierre común, §6.15 patrón resumido + exención de callouts.
- **F76** `references/07-visual/density.md` + `density_check.py` — reglas R1-R8.
- **F78** `references/05-note-types/concept.md` — paraguas común; el lab practica conceptos.
- **F79** `references/05-note-types/api-reference.md` — el lab usa APIs documentadas.
- **F80** `references/05-note-types/procedure.md` — el lab deriva de procedures.
- **F82** `references/05-note-types/error-troubleshooting.md` — errores típicos del lab.
- **F86** `references/05-note-types/chapter-digest.md` — capítulos que contienen labs.
- **F90** `references/05-note-types/cheatsheet.md` — cheatsheets de comandos usados en el lab.

## Sin dependencias externas

Python 3.9+ stdlib puro. Las 3 notas se generan inline en `build_fixtures.py`
para evitar divergencia entre fixtures y la regla que verifican.
