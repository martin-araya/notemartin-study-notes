# `evals/glossary-term-sample/` — Fase 89 `glossary-term`

Eval de la Fase 89 — tipo de nota `glossary-term`. Verifica que cada
término tiene definición + aliases (criterio #1), confundibles con enlaces
bidireccionales (criterio #2), y formas en inglés/español (criterio #3).

## Estructura

| Carpeta / archivo | Rol |
|---|---|
| `notes/xmin.md` | DB: PostgreSQL `xmin` (XID de transacción que insertó la fila). Formas inglés/español + aliases + confundibles (`[[term:xmax]]`, `[[term:cmin]]`) + notas donde aparece. |
| `notes/mvcc.md` | DB: PostgreSQL `MVCC` (Multi-Version Concurrency Control). Sigla universal + confundibles (`[[term:two-phase-locking]]`) + notas donde aparece (mvcc, architecture, connection-errors). |
| `notes/fork.md` | OS: Unix `fork()` (system call POSIX). Formas inglés/español + confundibles (`[[term:clone]]`) + notas donde aparece. |
| `build_fixtures.py` | Regenera las 3 notas. `--check` ejecuta `density_check.py --strict`. |
| `run_eval.py` | Batería de 6 sub-criterios (ver abajo). |

## Modo de uso

```bash
# Regenera fixtures + evalúa.
python3 evals/glossary-term-sample/run_eval.py --regen

# Solo evalúa (asume fixtures ya generadas).
python3 evals/glossary-term-sample/run_eval.py

# Solo regenera.
python3 evals/glossary-term-sample/build_fixtures.py
python3 evals/glossary-term-sample/build_fixtures.py --check
```

## Batería (6 sub-criterios)

| # | Sub-criterio | Verifica |
|---|---|---|
| C1 | `glossary-term.md` existe, ≤ 500 líneas, contiene las 9 secciones canónicas (§1-§9). | Estructura normativa del doc. |
| C2 | `## Definición` con 1 frase ≤ 40 palabras Y `## Aliases` con ≥ 1 item. | **Criterio ROADMAP #1**. |
| C3 | `## Confundibles` con ≥ 1 `[[note:]]` o `[[term:]]` (enlaces para bidireccionalidad). | **Criterio ROADMAP #2**. |
| C4 | `## Formas` contiene inglés + español o forma + sigla. | **Criterio ROADMAP #3**. |
| C5 | Los 3 fixtures pasan `density_check.py --strict` exit 0. | R1-R8 de F76. |
| C6 | `SKILL.md` §5.2 fila `glossary-term` y `references/05-note-types/README.md` ya no marcan `[pendiente F89]`. | Wirings cerrados. |

## Salida esperada

```
PASS 6/6
  [PASS] C1-doc-structure
  [PASS] C2-definition-and-aliases
  [PASS] C3-confundibles-with-links
  [PASS] C4-bilingual-forms
  [PASS] C5-density-check
  [PASS] C6-wirings-closed
```

## Wirings (fases previas)

- **F45** `references/04-authoring/block-directives.md` — directivas `:::example`, `:::tip`, `:::warning`.
- **F46** `references/04-authoring/inline-marks.md` — `[[term:nombre]]` para enlaces entre términos; `[[note:id]]` para notas donde aparece.
- **F47** `references/04-authoring/properties.md` — frontmatter sin `source-bearing` obligatorio.
- **F75** `references/07-visual/note-templates.md` — cabecera, apertura/cierre común, §6.12 patrón resumido + anti-patrón ≤ 30 líneas.
- **F76** `references/07-visual/density.md` + `density_check.py` — reglas R1-R8.
- **F78** `references/05-note-types/concept.md` — paraguas común; confundibles con notas concept.
- **F82** `references/05-note-types/error-troubleshooting.md` — errores referencian términos.

## Sin dependencias externas

Python 3.9+ stdlib puro. Las 3 notas se generan inline en `build_fixtures.py`
para evitar divergencia entre fixtures y la regla que verifican.
