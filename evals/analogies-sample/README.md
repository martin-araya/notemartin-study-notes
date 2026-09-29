# `evals/analogies-sample/` — Fase 95 `Analogías`

Eval de la Fase 95 — catálogo de patrones de analogía (≥ 10), banco
reutilizable (≥ 15 entradas con `Rotura:` explícito) y regla universal
de rotura. Verifica que `skill/notemartin-study-notes/references/06-writing/analogies.md`
materializa la promesa del ROADMAP §1652-1654 y de F94 §6 D5-D6.

## Estructura

| Archivo | Rol |
|---|---|
| `analogies.md` (en `references/06-writing/`) | Doc principal: 9 secciones canónicas, ≤ 600 líneas. |
| `build_catalog.py` | Genera `catalog.json` con 18 entradas estructuradas. Idempotente; `--force` regenera. |
| `catalog.json` | Fuente única de verdad para los criterios algorítmicos (C4, D5, D6). |
| `run_eval.py` | Batería de 13 sub-criterios (3 ROADMAP + 4 anti-patrones/wirings + 6 derivados). |
| `README.md` | Este archivo. |

## Modo de uso

```bash
# Regenera catálogo y ejecuta el eval.
python3 evals/analogies-sample/build_catalog.py --force
python3 evals/analogies-sample/run_eval.py

# Solo evalúa (asume catálogo y doc ya en su sitio).
python3 evals/analogies-sample/run_eval.py
```

## Batería (13 sub-criterios)

### Criterios ROADMAP (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C1** | `analogies.md` existe, ≤ 600 líneas, contiene las 9 secciones canónicas | Criterio ROADMAP F95 #1 + estructura |
| **C2** | §2 tabla tiene ≥ 10 patrones `P1`-`PN` con tabla markdown | Criterio ROADMAP F95 #1 |
| **C3** | §3 banco tiene ≥ 15 entradas `E1`-`EN` | Criterio ROADMAP F95 #3 |

### Anti-patrones y reglas (4)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C4** | Toda entrada del catálogo tiene `Rotura:` explícito y concreto (sin "casi", "más o menos", etc.) | Criterio ROADMAP F95 #2 |
| **C5** | §6 tiene ≥ 6 anti-patrones `AP1`-`APN` | Regla universal §4 + AP1-AP8 |
| **C6** | Wirings cerrados: `06-writing/README.md` y `SKILL.md` referencian `analogies.md` | Wirings F78-F101 |
| **C7** | El doc tiene ≥ 50 líneas de cuerpo (no es solo frontmatter) | INV-02 |

### Derivados (6)

| # | Sub-criterio | Verifica |
|---|---|---|
| **D1** | `wc -l analogies.md` ≤ 600 | INV-02 |
| **D2** | Las 9 secciones canónicas §1-§9 presentes | Estructura |
| **D3** | §4 regla universal tiene plantilla con verbos válidos | Regla §4 |
| **D4** | Wirings cerrados (alias de C6) | Wirings |
| **D5** | Banco cubre ≥ 2 dominios destino y ≥ 5 dominios fuente | Diversidad |
| **D6** | Cada patrón §2 tiene ≥ 1 entrada del banco que lo referencia | Auto-referencia P1-P12 ↔ E1-E18 |

## Salida esperada

```
PASS 13/13
```

## Wirings (fases relacionadas)

- **F11** `schemas/profile.schema.json` enum `writing.style` — el banco aplica a `intuition-first`.
- **F45** `references/04-authoring/block-directives.md` §10.11-§10.12 — `:::derived` vs `:::external`.
- **F46** `references/04-authoring/inline-marks.md` — `{external}` inline.
- **F78** `references/05-note-types/concept.md` §3 fila `## Analogía` — consume el banco.
- **F93** `references/05-note-types/selector.md` §3 — decide si la nota admite analogía.
- **F94** `references/06-writing/intuition-first.md` §6 D5-D6 — señales algorítmicas.
- **F96-F101** — fases adyacentes; sin dependencia directa con F95.

## Sin dependencias externas

Python 3.9+ stdlib puro. El catálogo JSON se genera inline para
mantener la trazabilidad entre las entradas y la verificación
algorítmica (sin regex sobre prosa markdown).
