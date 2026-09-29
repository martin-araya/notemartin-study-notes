# `evals/anti-patterns-sample/` — Fase 100 `Anti-patrones`

Eval de la Fase 100 — patrón transversal de anti-patrones (12 AP + 10
señales algorítmicas + checklist de 12 items). Verifica que
`skill/notemartin-study-notes/references/06-writing/anti-patterns.md`
materializa los 3 criterios del ROADMAP §1692-1694 y se integra en
`concept.md §6`.

## Estructura

| Archivo / carpeta | Rol |
|---|---|
| `notes/antipatterns-clean.md` | **Positivo**: nota `concept` PostgreSQL sin AP transversales; cumple los 12 items del checklist. |
| `notes/antipatterns-bad-1-circular.md` | **Negativo**: definición circular (falla AP2). |
| `notes/antipatterns-bad-2-marketing.md` | **Negativo**: marketing copiado (falla AP9). |
| `notes/antipatterns-bad-3-bullet-dump.md` | **Negativo**: volcado de 18 viñetas consecutivas (falla AP8). |
| `notes/antipatterns-bad-4-link-no-context.md` | **Negativo**: `[[note:id]]` sin frase introductoria (falla AP7). |
| `notes/antipatterns-bad-5-transcription.md` | **Negativo**: `## Resumen` copia verbatim el SDM (falla AP1). |
| `notes/antipatterns-bad-6-empty-section.md` | **Negativo**: `## Pendiente` con 1 línea trivial (falla AP12). |
| `build_fixtures.py` | Regenera las 7 notas inline. Idempotente; `--force` regenera. |
| `run_eval.py` | Batería de 18 sub-criterios (3 ROADMAP + 4 positivos + 3 reglas + 2 integración + 6 derivados). |
| `README.md` | Este archivo. |

## Modo de uso

```bash
# Regenera fixtures y ejecuta el eval.
python3 evals/anti-patterns-sample/build_fixtures.py --force
python3 evals/anti-patterns-sample/run_eval.py

# Solo evalúa (asume fixtures ya generadas).
python3 evals/anti-patterns-sample/run_eval.py
```

## Batería (18 sub-criterios)

### Criterios ROADMAP (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C1** | `anti-patterns.md` existe, ≤ 600 líneas, 8 secciones canónicas | Estructura del doc |
| **C2** | §2 tabla tiene ≥ 12 anti-patrones AP1-AP12 | Criterio #1 ROADMAP |
| **C3** | §3 tabla tiene ≥ 10 señales S1-S10 algorítmicas | Criterio #2 ROADMAP |

### Positivos (4)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C4** | §4 lista cerrada enumera los 12 AP | Lista compacta |
| **C5** | §5 referencias cruzadas a F94-F99 cubre ≥ 4 fases | Cross-refs |
| **C6** | §6 checklist tiene ≥ 12 items binarios con `[ ] **APn**` | Checklist |
| **C7** | `antipatterns-clean.md` cumple los 12 items del checklist | Caso positivo |

### Reglas (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C8** | Las 6 notas negativas son detectadas por al menos 1 señal cada una | Criterio #2 ROADMAP |
| **C9** | Wirings cerrados (`06-writing/README.md` y `SKILL.md` mencionan `anti-patterns.md`) | Wirings |
| **C10** | Las 7 notas fixture pasan `density_check.py --strict` exit 0 | R1-R8 F76 |

### Integración (2)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C11** | `concept.md §6` referencia los 12 AP como items del checklist | Criterio #3 ROADMAP |
| **C12** | `concept.md §6` lista explícitamente los 12 AP con `[ ] **APn**` | Criterio #3 ROADMAP |

### Derivados (6)

| # | Sub-criterio | Verifica |
|---|---|---|
| **D1** | `wc -l anti-patterns.md` ≤ 600 | INV-02 |
| **D2** | 8 secciones canónicas §1-§8 presentes | Estructura |
| **D3** | §6 checklist ≥ 12 items (alias C6) | Checklist |
| **D4** | §5 cross-refs ≥ 4 fases (alias C5) | Cross-refs |
| **D5** | Wirings cerrados (alias C9) | Wirings |
| **D6** | Density check alias (alias C10) | R1-R8 F76 |

## Salida esperada

```
PASS 18/18
```

## Wirings (fases relacionadas)

- **F45** `references/04-authoring/block-directives.md` §6 — `:::warning`, `:::tip`, etc.
- **F46** `references/04-authoring/inline-marks.md` — `{src:blk_xxxx}`, `[[note:id]]`.
- **F67** `references/07-visual/` + `scripts/validate/mermaid.py` — AP11.
- **F76** `references/07-visual/density.md` — R5 (AP8), R3 (anclajes).
- **F78** `references/05-note-types/concept.md` §6 — checklist extendido con 12 AP.
- **F94-F99** — AP específicos ya cubiertos por cada fase; F100 los referencia.
- **F101** `references/06-writing/i18n-and-citation.md` — sin solapamiento.
- **F112** F112 (suite de checks) — base para automatizar S1-S10.

## Sin dependencias externas

Python 3.9+ stdlib puro + invocación de `density_check.py` (F76) que
también es stdlib puro. Las 7 notas se generan inline para evitar
divergencia entre fixtures y la regla que verifican.
