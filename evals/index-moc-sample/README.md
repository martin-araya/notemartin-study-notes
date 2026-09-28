# `evals/index-moc-sample/` — Fase 91 `index-moc` [núcleo]

Eval de la Fase 91 — tipo de nota `index-moc`. Verifica que cada enlace
lleva descripción (criterio #1), que los enlaces apuntan a notas existentes
(criterio #2), y que la cobertura de la fuente está declarada (criterio #3).

## Estructura

| Carpeta / archivo | Rol |
|---|---|
| `notes/postgresql-index.md` | DB: MOC de PostgreSQL 16 con 9 notas referenciadas (architecture, mvcc, configuration, backup, errors, cheatsheet, vacuum, explain, replication) + mapa conceptual Mermaid + 3 rutas de lectura + cobertura. |
| `notes/docker-index.md` | Containers: MOC de Docker 25 con 7 notas (cli-bundle, architecture, permission-errors, network-modes, rootless, cli-syntax, compose, buildx) + 3 rutas. |
| `notes/rust-index.md` | Programación: MOC de Rust 1.80 con 8 notas (ownership, borrow-checker, lifetimes, traits, error-handling, std-library, cargo, cheatsheet) + 3 rutas. |
| `phantom-notes/` | Notas placeholder (10+ cada una) para que las referencias del MOC pasen el filesystem check (criterio #2). |
| `build_fixtures.py` | Regenera las 3 notas + crea las phantom notes. `--check` ejecuta `density_check.py --strict`. |
| `run_eval.py` | Batería de 6 sub-criterios (ver abajo). |

## Modo de uso

```bash
# Regenera fixtures + evalúa.
python3 evals/index-moc-sample/run_eval.py --regen

# Solo evalúa (asume fixtures ya generadas).
python3 evals/index-moc-sample/run_eval.py

# Solo regenera.
python3 evals/index-moc-sample/build_fixtures.py
python3 evals/index-moc-sample/build_fixtures.py --check
```

## Batería (6 sub-criterios)

| # | Sub-criterio | Verifica |
|---|---|---|
| C1 | `index-moc.md` existe, ≤ 600 líneas, contiene las 9 secciones canónicas (§1-§9). | Estructura normativa del doc. |
| C2 | Cada `[[note:id]]` en los fixtures tiene descripción de ≥ 1 palabra después del link. | **Criterio ROADMAP #1**. |
| C3 | Cada `[[note:id]]` en los fixtures existe en `notes/` o `phantom-notes/`. | **Criterio ROADMAP #2**. |
| C4 | Existe `## Cobertura de la fuente` con keywords "cubre" + "no cubre". | **Criterio ROADMAP #3**. |
| C5 | Los 3 fixtures pasan `density_check.py --strict` exit 0. | R1-R8 de F76. |
| C6 | `SKILL.md` §5.2 fila `index-moc` y `references/05-note-types/README.md` ya no marcan `[pendiente F91]`. | Wirings cerrados. |

## Salida esperada

```
PASS 6/6
  [PASS] C1-doc-structure
  [PASS] C2-links-have-descriptions
  [PASS] C3-links-point-to-existing-notes
  [PASS] C4-coverage-section-present
  [PASS] C5-density-check
  [PASS] C6-wirings-closed
```

## Wirings (fases previas)

- **F45** `references/04-authoring/block-directives.md` — directivas `:::note`, `:::tip`, `:::warning`, `:::diagram`.
- **F46** `references/04-authoring/inline-marks.md` — `[[note:id]]` con descripción de 1 frase (criterio #1).
- **F47** `references/04-authoring/properties.md` — frontmatter sin `source-bearing` obligatorio.
- **F66** `references/07-visual/mermaid-portable.md` — Mermaid portable en `## Mapa conceptual`.
- **F75** `references/07-visual/note-templates.md` — cabecera, apertura/cierre común, §6.14 patrón resumido + exención de `## Backlinks` + anti-patrón de contenido fáctico.
- **F76** `references/07-visual/density.md` + `density_check.py` — reglas R1-R8.
- **F78** `references/05-note-types/concept.md` — paraguas común; el MOC referencia notas concept.
- **F86** `references/05-note-types/chapter-digest.md` — capítulos que el MOC puede resumir.
- **F90** `references/05-note-types/cheatsheet.md` — el MOC puede referenciar cheatsheets del mismo dominio.

## Sin dependencias externas

Python 3.9+ stdlib puro. Las 3 notas se generan inline en `build_fixtures.py`
junto con notas phantom que satisfacen el filesystem check (criterio #2).
