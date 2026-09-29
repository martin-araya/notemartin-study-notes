# `evals/executable-examples-sample/` — Fase 96 `Ejemplos ejecutables`

Eval de la Fase 96 — patrón del **mínimo reproducible** (Setup → Acción
→ Resultado → Limpieza), 3 plantillas canónicas (DB / redes / CLI), 3
niveles de escalado (mínimo / realista / límite), 8 anti-ejemplos, cabecera
de declaración de entorno y 10 señales algorítmicas. Verifica que
`skill/notemartin-study-notes/references/06-writing/executable-examples.md`
materializa los 3 criterios del ROADMAP §1660-1662.

## Estructura

| Archivo / carpeta | Rol |
|---|---|
| `notes/db-postgres-count.md` | Ejemplo **DB**: PostgreSQL SELECT count con 4 secciones + entorno + limpieza. |
| `notes/net-tcpdump-syn.md` | Ejemplo **redes**: `tcpdump` filtrando SYN con captura verbatim. |
| `notes/cli-docker-run.md` | Ejemplo **CLI**: `docker run --rm` con limpieza justificada "no requiere". |
| `notes/anti-missing-cleanup.md` | Fixture **NEGATIVO**: ejemplo SIN limpieza (test de la señal D2/C6). |
| `build_fixtures.py` | Regenera las 4 notas inline. Idempotente; `--force` regenera. |
| `run_eval.py` | Batería de 16 sub-criterios (3 ROADMAP + 4 positivos + 3 wirings + 6 derivados). |
| `README.md` | Este archivo. |

## Modo de uso

```bash
# Regenera fixtures y ejecuta el eval.
python3 evals/executable-examples-sample/build_fixtures.py --force
python3 evals/executable-examples-sample/run_eval.py

# Solo evalúa (asume fixtures ya generadas).
python3 evals/executable-examples-sample/run_eval.py
```

## Batería (16 sub-criterios)

### Criterios ROADMAP (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C1** | `executable-examples.md` existe, ≤ 600 líneas, 9 secciones canónicas | Estructura del doc |
| **C2** | §3 tiene 3 plantillas (§3.1 DB / §3.2 redes / §3.3 CLI) con `## Setup` / `## Acción` / `## Resultado` / `## Limpieza` cada una | Criterio #1 ROADMAP |
| **C3** | §5 tiene ≥ 5 anti-ejemplos NE1-NEN | Anti-patrones |

### Positivos (4)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C4** | 3 notas base tienen 4 secciones canónicas en orden | Patrón completo |
| **C5** | 3 notas base tienen cabecera `> **Entorno:** ...` con ≥ 4 campos | Criterio #3 ROADMAP (sin estado no declarado) |
| **C6** | 3 notas base declaran `## Limpieza` o "No requiere limpieza" | Criterio #1 ROADMAP |
| **C7** | `anti-missing-cleanup.md` **NO** tiene limpieza (test negativo de D2) | Test de regresión |

### Negativos y reglas (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C8** | Wirings cerrados (`06-writing/README.md` y `SKILL.md` mencionan `executable-examples.md`) | Wirings F94-F101 |
| **C9** | Cada nota base tiene ≥ 1 bloque de código en `## Resultado` (anclaje visual R3) | R3 F76 |
| **C10** | Sin "asumiendo / suponiendo / depende de" sin `## Setup` o cabecera `> **Entorno:**` | Criterio #3 ROADMAP |

### Derivados (6)

| # | Sub-criterio | Verifica |
|---|---|---|
| **D1** | `wc -l executable-examples.md` ≤ 600 | INV-02 |
| **D2** | 9 secciones canónicas §1-§9 presentes (alias C1) | Estructura |
| **D3** | §4 tabla tiene 3 niveles (mínimo/realista/límite) con umbrales numéricos | Escalado |
| **D4** | §7 tiene ≥ 8 señales D1-D10 algorítmicas | Diagnóstico |
| **D5** | Las 3 notas base pasan `density_check.py --strict` exit 0 | R1-R8 F76 |
| **D6** | Wirings cerrados (alias C8) | Wirings |

## Salida esperada

```
PASS 16/16
```

## Wirings (fases relacionadas)

- **F45** `references/04-authoring/block-directives.md` §10.4 — `:::example` admite 1 snippet.
- **F46** `references/04-authoring/inline-marks.md` — `{src:blk_xxxx}` para código del SDM.
- **F51** `references/04-authoring/depth-layers.md` — capas L1/L2/L3.
- **F76** `references/07-visual/density.md` + `scripts/validate/density_check.py` — R1-R8.
- **F78** `references/05-note-types/concept.md` §3 — `## Confirmación` usa ejemplos F96.
- **F94** `references/06-writing/intuition-first.md` §5.4 — regla C1 Confirmación.
- **F95** `references/06-writing/analogies.md` §7 — plantilla cerrada (estilo).
- **F97-F101** — citadas desde §8 del doc principal.

## Sin dependencias externas

Python 3.9+ stdlib puro + invocación de `density_check.py` (F76) que
también es stdlib puro. Las 4 notas se generan inline para evitar
divergencia entre fixtures y la regla que verifican.
