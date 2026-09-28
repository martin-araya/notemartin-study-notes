# `evals/api-reference-sample/` — Fase 79 `api-reference`

Eval de la Fase 79 — tipo de nota `api-reference`. Verifica que el patrón
documentado en `references/05-note-types/api-reference.md` cubre paquetes con
≥ 15 subprogramas sin omitir parámetros, exige tabla 5-col exhaustiva, e
incluye al menos un ejemplo ejecutable.

## Estructura

| Carpeta / archivo | Rol |
|---|---|
| `notes/docker-cli-bundle.md` | **Paquete con 15 subcomandos** Docker CLI. Cubre criterio ROADMAP #1 (≥ 15 subprogramas, ninguno queda fuera) y #3 (≥ 1 ejemplo ejecutable por subcomando). |
| `notes/docker-run.md` | **Subprograma individual** `docker run` con tabla exhaustiva de 14 flags. Cubre criterio #2 (5 columnas sin celdas vacías) y #3. |
| `notes/kubernetes-pod-v1.md` | **Endpoint REST** `POST /api/v1/namespaces/{namespace}/pods` con 14 campos del schema core/v1. Cubre criterio #2 + estructura Excepciones/Privilegios/Precondiciones. |
| `build_fixtures.py` | Regenera las 3 notas. `--check` ejecuta `density_check.py --strict`. |
| `run_eval.py` | Batería de 6 sub-criterios (ver abajo). |

## Modo de uso

```bash
# Regenera fixtures + evalúa.
python3 evals/api-reference-sample/run_eval.py --regen

# Solo evalúa (asume fixtures ya generadas).
python3 evals/api-reference-sample/run_eval.py

# Solo regenera (sin ejecutar eval).
python3 evals/api-reference-sample/build_fixtures.py
python3 evals/api-reference-sample/build_fixtures.py --check    # + density_check
```

## Batería (6 sub-criterios)

| # | Sub-criterio | Verifica |
|---|---|---|
| C1 | `api-reference.md` existe, ≤ 500 líneas, contiene las 9 secciones canónicas (§1-§9). | Estructura normativa del doc. |
| C2 | `docker-cli-bundle.md` cubre ≥ 15 subcomandos y cada uno tiene `### Subcomando:` + tabla 5-col. | **Criterio ROADMAP #1**. |
| C3 | Toda fila de toda tabla 5-col en los 3 fixtures tiene las 5 celdas rellenas (Parámetro, Tipo, Obligatorio, Default, Descripción). | **Criterio ROADMAP #2**. |
| C4 | Cada fixture tiene ≥ 1 bloque `:::example` o `code` con caption en `## Ejemplos`. | **Criterio ROADMAP #3**. |
| C5 | Los 3 fixtures pasan `density_check.py --strict` exit 0. | R1-R8 de F76. |
| C6 | `SKILL.md` §5.2 fila `api-reference` y `references/05-note-types/README.md` ya no marcan `[pendiente F79]`. | Wirings cerrados. |

## Salida esperada

```
PASS 6/6
  [PASS] C1-doc-structure
  [PASS] C2-bundle-coverage
  [PASS] C3-table-completeness
  [PASS] C4-examples-present
  [PASS] C5-density-check
  [PASS] C6-wirings-closed
```

## Wirings (fases previas)

- **F46** `references/04-authoring/inline-marks.md` — marcas `{src:blk_xxxx}` y `[[note:id]]`.
- **F47** `references/04-authoring/properties.md` — frontmatter canónico (20 propiedades; `source-bearing` obligatorio).
- **F51** `references/04-authoring/depth-layers.md` — capas L1/L2/L3.
- **F75** `references/07-visual/note-templates.md` — cabecera canónica, apertura/cierre común, §6.2 patrón resumido.
- **F76** `references/07-visual/density.md` + `scripts/validate/density_check.py` — reglas R1-R8 ejecutables.
- **F78** `references/05-note-types/concept.md` — paraguas común (perfil-activación, checklist).

## Sin dependencias externas

Python 3.9+ stdlib puro. Las 3 notas se generan inline en `build_fixtures.py`
para evitar divergencia entre fixtures y la regla que verifican.
