# `evals/intuition-first-sample/` — Fase 94 `intuition-first`

Eval de la Fase 94 — patrón de redacción `intuition-first` (Problema →
Intuición → Analogía → Definición formal → Confirmación). Verifica que
`skill/notemartin-study-notes/references/06-writing/intuition-first.md`
documenta el patrón con 2 ejemplos completos (BD + redes), la excepción
`reference-pure` acotada con 4 checks binarios, y 8+ señales de
diagnóstico algorítmicas verificables por un revisor externo.

## Estructura

| Carpeta / archivo | Rol |
|---|---|
| `notes/db-mvcc.md` | Concepto **DB**: PostgreSQL MVCC, 5 etapas completas. |
| `notes/net-tcp-3whs.md` | Concepto **redes**: TCP three-way handshake, 5 etapas. |
| `notes/ref-pure-config.md` | `api-reference` con **excepción acotada** `reference-pure`: solo `## Problema` + `## Definición formal` + `## Notas` con cita literal que descarta la intuición. |
| `build_fixtures.py` | Regenera las 3 notas in-line. Idempotente; `--force` regenera. |
| `run_eval.py` | Batería de 9 sub-criterios (4 ROADMAP + 5 derivados). |

## Modo de uso

```bash
# Regenera fixtures y ejecuta el eval.
python3 evals/intuition-first-sample/build_fixtures.py --force
python3 evals/intuition-first-sample/run_eval.py

# Solo evalúa (asume fixtures ya generadas).
python3 evals/intuition-first-sample/run_eval.py
```

## Batería (9 sub-criterios)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C1** | `intuition-first.md` §7.1 contiene `PostgreSQL` o `mvcc` (BD) | Criterio ROADMAP F94 #1: ejemplo de base de datos |
| **C2** | `intuition-first.md` §7.2 contiene `TCP` o `three.?way` o `handshake` (redes) | Criterio ROADMAP F94 #1: ejemplo de redes |
| **C3** | §4 contiene tabla con 4 checks binarios + override textual `study`+`hybrid` | Criterio ROADMAP F94 #2: excepción acotada |
| **C4** | §6 contiene ≥ 8 señales D1-D10 con columnas `Método` y `PASS si` y al menos un método algorítmico (regex/conteo/presencia/ratio) | Criterio ROADMAP F94 #3: señales verificables |
| **D1** | `wc -l intuition-first.md` ≤ 500 | INV-02 |
| **D2** | `db-mvcc.md` y `net-tcp-3whs.md` tienen las 5 etapas en orden canónico estricto | Patrón completo |
| **D3** | `## Analogía` en ambas notas contiene ≥ 1 frase que matchea D5 (`se rompe / no se parece / la diferencia / en cambio / difiere`) | Anti-patrón AP4 cazado |
| **D4** | `## Intuición` en ambas notas contiene ≥ 1 `[[term:...]]` | INV-I2 |
| **D5** | `references/06-writing/README.md` ya no marca `[pendiente F94]`; `SKILL.md` referencia `intuition-first.md` | Wirings cerrados |
| **D6** | Override textual presente (regex: `study.*hybrid.*no activan` / `reference-pure.*único` / `override.*perfil`) | Override de perfil |

## Salida esperada

```
PASS 9/9
```

## Wirings (fases relacionadas)

- **F11** `schemas/profile.schema.json` enum `writing.style` — define los 4 estilos.
- **F45** `references/04-authoring/block-directives.md` §10.11-§10.12 — `:::derived` / `:::external`.
- **F46** `references/04-authoring/inline-marks.md` §6-§7 — marcas `{src:blk_xxxx}` y `[[term:nombre]]`.
- **F51** `references/04-authoring/depth-layers.md` — L1 (Intuición/Analogía), L2 (Problema/Definición formal).
- **F76** `references/07-visual/density.md` + `scripts/validate/density_check.py` — R1-R8 sin exención.
- **F78** `references/05-note-types/concept.md` §3 — instancia las 5 etapas.
- **F93** `references/05-note-types/selector.md` §3 — decide si aplica intuition-first o reference-pure.
- **F95-F101** — citados desde §11 del doc principal.

## Sin dependencias externas

Python 3.9+ stdlib puro. Las 3 notas se generan inline en
`build_fixtures.py` para evitar divergencia entre fixtures y la
regla que verifican. El eval no instala nada; corre tal cual.
