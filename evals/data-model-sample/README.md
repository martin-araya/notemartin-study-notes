# `evals/data-model-sample/` — Fase 85 `data-model`

Eval de la Fase 85 — tipo de nota `data-model`. Verifica que cada entidad
tiene atributos con tipo y restricciones (criterio #1), que el ER
Mermaid refleja las relaciones (criterio #2), y que las restricciones de
integridad están completas (criterio #3).

## Estructura

| Carpeta / archivo | Rol |
|---|---|
| `notes/ecommerce-data-model.md` | E-commerce clásico: User, Product, Order, OrderItem, Review, Category. Diagrama `erDiagram` con 7 relaciones. 4 tipos de integridad. |
| `notes/library-data-model.md` | Library: Author, Book, Borrower, Loan. 3 relaciones. 4 tipos de integridad. |
| `notes/postgresql-data-model.md` | PostgreSQL system catalogs: pg_class, pg_attribute, pg_type, pg_namespace. 4 relaciones. 4 tipos de integridad. |
| `build_fixtures.py` | Regenera las 3 notas. `--check` ejecuta `density_check.py --strict`. |
| `run_eval.py` | Batería de 6 sub-criterios (ver abajo). |

## Modo de uso

```bash
# Regenera fixtures + evalúa.
python3 evals/data-model-sample/run_eval.py --regen

# Solo evalúa (asume fixtures ya generadas).
python3 evals/data-model-sample/run_eval.py

# Solo regenera.
python3 evals/data-model-sample/build_fixtures.py
python3 evals/data-model-sample/build_fixtures.py --check
```

## Batería (6 sub-criterios)

| # | Sub-criterio | Verifica |
|---|---|---|
| C1 | `data-model.md` existe, ≤ 600 líneas, contiene las 9 secciones canónicas (§1-§9). | Estructura normativa del doc. |
| C2 | Cada entidad listada en `## Entidades` tiene ≥ 1 fila en `## Campos` con Tipo y Restricciones no vacíos. | **Criterio ROADMAP #1**. |
| C3 | Las relaciones en `## Relaciones` aparecen como líneas en el `erDiagram` Mermaid de `## Modelo` (con normalización de `_` → vacío). | **Criterio ROADMAP #2**. |
| C4 | `## Integridad` tiene `:::warning`/`:::danger` por cada tipo (PK, FK, UNIQUE, NOT NULL, CHECK). | **Criterio ROADMAP #3**. |
| C5 | Los 3 fixtures pasan `density_check.py --strict` exit 0. | R1-R8 de F76. |
| C6 | `SKILL.md` §5.2 fila `data-model` y `references/05-note-types/README.md` ya no marcan `[pendiente F85]`. | Wirings cerrados. |

## Salida esperada

```
PASS 6/6
  [PASS] C1-doc-structure
  [PASS] C2-entities-have-fields
  [PASS] C3-er-matches-relationships
  [PASS] C4-integrity-complete
  [PASS] C5-density-check
  [PASS] C6-wirings-closed
```

## Wirings (fases previas)

- **F45** `references/04-authoring/block-directives.md` — directivas `:::example`, `:::warning`, `:::danger`, `:::note`, `:::diagram`.
- **F46** `references/04-authoring/inline-marks.md` — `{src:blk_xxxx}` por entidad; `[[term:nombre]]` para tipos.
- **F47** `references/04-authoring/properties.md` — frontmatter canónico; `source-bearing` recomendado.
- **F66** `references/07-visual/mermaid-portable.md` — Mermaid portable en `## Modelo`.
- **F75** `references/07-visual/note-templates.md` — cabecera, apertura/cierre común, §6.8 patrón resumido.
- **F76** `references/07-visual/density.md` + `density_check.py` — reglas R1-R8.
- **F78** `references/05-note-types/concept.md` — paraguas común.
- **F80** `references/05-note-types/procedure.md` — migraciones como procedure.
- **F82** `references/05-note-types/error-troubleshooting.md` — errores de constraints.
- **F84** `references/05-note-types/syntax.md` — DDL completo del schema.

## Sin dependencias externas

Python 3.9+ stdlib puro. Las 3 notas se generan inline en `build_fixtures.py`
para evitar divergencia entre fixtures y la regla que verifican.
