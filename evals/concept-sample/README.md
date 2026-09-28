# `evals/concept-sample/` — Fase 78 `concept`

Eval de la Fase 78 — tipo de nota `concept`. Verifica que el patrón documentado
en `references/05-note-types/concept.md` es aplicable sin cambios a un concepto
de base de datos y a uno de redes, e incluye la sección obligatoria
`## Límites y alternativas`.

## Estructura

| Carpeta / archivo | Rol |
|---|---|
| `notes/db-mvcc.md` | Concepto **DB**: MVCC (PostgreSQL). Patrón completo, sin `## Práctica`. |
| `notes/net-three-way-handshake.md` | Concepto **redes**: TCP 3WHS (RFC 9293). Patrón completo, sin `## Práctica`. |
| `notes/db-mvcc-practice.md` | Variante con `## Práctica` (caso `include_practice: true`). |
| `notes/net-three-way-handshake-practice.md` | Variante con `## Práctica` (caso `include_practice: true`). |
| `profiles/profile-practice.yaml` | Contrato de perfil que activa `## Práctica`. |
| `profiles/profile-no-practice.yaml` | Contrato de perfil que omite `## Práctica` (default). |
| `build_fixtures.py` | Regenera notas y perfiles. `--check` ejecuta `density_check.py --strict`. |
| `run_eval.py` | Batería de 5 sub-criterios (ver abajo). |

## Modo de uso

```bash
# Regenera fixtures + evalúa.
python3 evals/concept-sample/run_eval.py --regen

# Solo evalúa (asume fixtures ya generadas).
python3 evals/concept-sample/run_eval.py

# Solo regenera (sin ejecutar eval).
python3 evals/concept-sample/build_fixtures.py
python3 evals/concept-sample/build_fixtures.py --check    # + density_check
```

## Batería (5 sub-criterios)

| # | Sub-criterio | Verifica |
|---|---|---|
| C1 | `concept.md` existe, ≤ 400 líneas, contiene las 9 secciones canónicas (§1-§9). | Criterio del bloque 9: estructura normativa del doc. |
| C2 | Las 2 notas base pasan `density_check.py --strict` exit 0. | Criterio ROADMAP F78 #1: funciona para DB y redes. |
| C3 | Ambas notas contienen `## Límites y alternativas` con ≥ 1 fila tabular **y** ≥ 1 enlace `[[note:id]]` o `[[term:...]]`. | Criterio ROADMAP F78 #2: sección obligatoria. |
| C4 | Las variantes `*-practice.md` incluyen `## Práctica`; las bases NO la incluyen. | Criterio ROADMAP F78 #3: opcional por perfil. |
| C5 | `SKILL.md` §5.2 fila `concept` y `references/05-note-types/README.md` ya no marcan `[pendiente F78]`. | Wirings cerrados. |

## Salida esperada

```
PASS 5/5
  [PASS] C1-doc-structure
  [PASS] C2-density-check
  [PASS] C3-limits-alternatives
  [PASS] C4-practice-optional
  [PASS] C5-wirings-closed
```

## Wirings (fases previas)

- **F46** `references/04-authoring/inline-marks.md` — marcas `{src:blk_xxxx}` y `[[note:id]]`.
- **F47** `references/04-authoring/properties.md` — frontmatter canónico de 20 propiedades.
- **F51** `references/04-authoring/depth-layers.md` — capas L1/L2/L3.
- **F75** `references/07-visual/note-templates.md` — cabecera canónica, apertura/cierre común, §6.1 patrón resumido.
- **F76** `references/07-visual/density.md` + `scripts/validate/density_check.py` — reglas R1-R8 ejecutables.

## Sin dependencias externas

Python 3.9+ stdlib puro. Las 4 notas se generan inline en `build_fixtures.py`
para evitar divergencia entre fixtures y la regla que verifican.
