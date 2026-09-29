# `evals/i18n-and-citation-sample/` — Fase 101 `Idioma bilingüe y citación`

Eval de la Fase 101 — patrón transversal de i18n: 4 valores del enum
`language` (`es` / `en` / `es-en` / `en-es`), lista cerrada de 45
no-traducibles en 8 categorías, primera aparición bilingüe con
`[[en:term]]` / `[[es:term]]`, bloque de procedencia con 4 campos
(fuente / versión / fecha / URL/anchor), 8 señales algorítmicas
S1-S8 y 7 anti-patrones AP1-AP7.

## Estructura

| Archivo / carpeta | Rol |
|---|---|
| `notes/i18n-good-1-es.md` | **Positivo**: nota `concept` PostgreSQL en español, con bloque de procedencia completo. |
| `notes/i18n-good-2-es-en.md` | **Positivo**: nota `concept` TCP en bilingüe español-primario, con `[[en:three-way-handshake]]` y glosario al pie. |
| `notes/i18n-good-3-citation.md` | **Positivo**: nota `concept` Kubernetes monolingüe inglés, con bloque de procedencia completo. |
| `notes/i18n-bad-1-translated.md` | **Negativo**: parámetro `--max-conexiones` traducido (falla AP1 / S1). |
| `notes/i18n-bad-2-no-citation.md` | **Negativo**: sin bloque `## Procedencia` (falla AP2 / S4). |
| `notes/i18n-bad-3-no-bilingual.md` | **Negativo**: `language: es-en` sin marcas `[[en:]]` ni glosario (falla AP3 + AP4 / S2 + S5). |
| `build_fixtures.py` | Regenera las 6 notas inline. Idempotente; `--force` regenera. |
| `run_eval.py` | Batería de 18 sub-criterios (4 ROADMAP + 4 positivos + 4 reglas + 6 derivados). |
| `README.md` | Este archivo. |

## Modo de uso

```bash
# Regenera fixtures y ejecuta el eval.
python3 evals/i18n-and-citation-sample/build_fixtures.py --force
python3 evals/i18n-and-citation-sample/run_eval.py

# Solo evalúa (asume fixtures ya generadas).
python3 evals/i18n-and-citation-sample/run_eval.py
```

## Batería (18 sub-criterios)

### Criterios ROADMAP (4)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C1** | `i18n-and-citation.md` existe, ≤ 600 líneas, 9 secciones canónicas | Estructura del doc |
| **C2** | §2 tabla tiene los 4 valores del enum `language` | Cubre idioma |
| **C3** | §3 lista cerrada tiene ≥ 40 entradas | Criterio #3 ROADMAP |
| **C4** | §4 menciona `[[en:term]]` / `[[es:term]]` + primera aparición | Criterio #2 ROADMAP |

### Positivos (4)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C5** | §5 plantilla de procedencia con 4 campos (Fuente, Versión, Fecha, URL/anchor) | Criterio #4 ROADMAP |
| **C6** | §6 tiene ≥ 8 señales algorítmicas S1-S8 | Criterio #1 ROADMAP |
| **C7** | 3 notas positivas (good-1, good-2, good-3) cumplen los criterios | Casos positivos |
| **C8** | 3 notas negativas son detectadas por las señales | Casos negativos |

### Reglas y wirings (4)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C9** | Wirings cerrados (`06-writing/README.md` y `SKILL.md` mencionan `i18n-and-citation.md`) | Wirings |
| **C10** | Las 6 notas fixture pasan `density_check.py --strict` exit 0 | R1-R8 F76 |
| **C11** | `properties.md §5.13` cita F101 | Wiring con F47 |
| **C12** | `concept.md §6` lista los 4 items `**F101-AP1**` a `**F101-AP4**` | Integración checklist |

### Derivados (6)

| # | Sub-criterio | Verifica |
|---|---|---|
| **D1** | `wc -l i18n-and-citation.md` ≤ 600 | INV-02 |
| **D2** | 9 secciones canónicas §1-§9 presentes | Estructura |
| **D3** | §3 lista cerrada ≥ 40 entradas (alias C3) | Tabla cerrada |
| **D4** | §5 plantilla de procedencia con 4 campos (alias C5) | Procedencia |
| **D5** | Wirings cerrados (alias C9) | Wirings |
| **D6** | Density check alias (alias C10) | R1-R8 F76 |

## Salida esperada

```
PASS 18/18
```

## Wirings (fases relacionadas)

- **F20** `references/01-ingest/ocr-engines.md` — OCR multi-idioma `spa+eng`.
- **F26/F27** `references/02-source-model/provenance.md` — BCP-47, source-bearing.
- **F45** `references/04-authoring/block-directives.md` §10.11-§10.12 — `:::external`.
- **F46** `references/04-authoring/inline-marks.md` — `[[term:nombre]]` canónica.
- **F47** `references/04-authoring/properties.md` §5.13 — enum `language`.
- **F76** `references/07-visual/density.md` + `scripts/validate/density_check.py` — R1-R8.
- **F78** `references/05-note-types/concept.md` §6 — checklist extendido con 4 items F101.
- **F94-F100** — citadas desde §8 del doc principal.

## Sin dependencias externas

Python 3.9+ stdlib puro + invocación de `density_check.py` (F76) que
también es stdlib puro. Las 6 notas se generan inline para evitar
divergencia entre fixtures y la regla que verifican.
