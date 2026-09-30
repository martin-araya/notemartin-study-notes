# `evals/self-evaluation-sample/` — Fase 102 `Autoevaluación por tipo`

Eval de la Fase 102 — patrón transversal de autoevaluación: 5 tipos de
pregunta cerrados (recuerdo, aplicación, diagnóstico, decisión, predicción),
tabla cerrada de 15 filas × 5 columnas (mapeo `note-type` × tipos-de-pregunta),
forma canónica `:::collapsible{default_open=false}` + `> Fundamento: …`,
regla de referencia pura (glossary-term y index-moc: solo recuerdo / sin
sección), validador algorítmico `scripts/validate/self_eval_check.py`
con 7 reglas V1-V7, y 3 anti-patrones AP13-AP15.

## Estructura

| Archivo / carpeta | Rol |
|---|---|
| `notes/self-eval-good-1-concept.md` | **Positivo**: nota `concept` MVCC con recuerdo + aplicación + decisión, 3 preguntas por H3, todas con `> Fundamento:` y respuesta reformulada. |
| `notes/self-eval-good-2-procedure.md` | **Positivo**: nota `procedure` pg_dump con aplicación + predicción, fundamento mixto (`{src:blk_xxxx}` + `[[note:id#§N]]`). |
| `notes/self-eval-good-3-error-troubleshooting.md` | **Positivo**: nota `error-troubleshooting` Connection refused con diagnóstico + decisión, mensaje literal preservado. |
| `notes/self-eval-good-4-glossary-term.md` | **Positivo**: nota `glossary-term` Snapshot con solo recuerdo (referencia pura), 3 preguntas. |
| `notes/self-eval-bad-1-no-fundamento.md` | **Negativo**: colapsable sin línea `> Fundamento:` (falla V3 / AP14). |
| `notes/self-eval-bad-2-copiada.md` | **Negativo**: respuestas triviales (1 token no-técnico) — fallan V4 (heurística de reformulación). |
| `notes/self-eval-bad-3-recuerdo-en-referencia.md` | **Negativo**: glossary-term con `### Aplicación` (falla V2 / AP15 / §4 regla de referencia pura estricta). |
| `notes/self-eval-bad-4-index-moc-con-seccion.md` | **Negativo**: index-moc con sección `## Autoevaluación` (falla V6). |
| `build_fixtures.py` | Regenera las 8 notas inline. Idempotente; `--force` regenera. |
| `run_eval.py` | Batería de 14 sub-criterios (3 ROADMAP + 4 positivos + 4 reglas/wirings + 3 derivados). |

## Modo de uso

```bash
# Regenera fixtures y ejecuta el eval.
python3 evals/self-evaluation-sample/build_fixtures.py --force
python3 evals/self-evaluation-sample/run_eval.py

# Solo evalúa (asume fixtures ya generadas).
python3 evals/self-evaluation-sample/run_eval.py
```

## Batería (14 sub-criterios)

### Criterios ROADMAP (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C1** | `self-evaluation.md` existe, ≤ 600 líneas, 8 secciones canónicas §1-§8 | Estructura del doc |
| **C2** | §3 tabla cerrada con 15 filas × 5 columnas (mapeo `note-type` × tipos-de-pregunta) | Criterio #1 ROADMAP |
| **C3** | §5 plantilla NoteMark con `:::collapsible{default_open=false}` + `> Fundamento: …` | Criterio #2 ROADMAP |

### Positivos (4)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C4** | §6 V4 menciona Jaccard ≤ 0.8 sobre palabras no técnicas (excluyendo lista F101 §3) | Criterio #3 ROADMAP |
| **C5** | Las 4 notas positivas pasan `self_eval_check.py --strict` exit 0 | V1-V6 |
| **C6** | Las 4 notas negativas son detectadas (V1/V2/V3/V4/V6) | Casos negativos |
| **C7** | `concept.md §6` lista los 2 items `**F102-1**` y `**F102-2**` | Integración checklist |

### Reglas y wirings (4)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C8** | Los 15 archivos de `05-note-types/` declaran `### Autoevaluación` con tabla copiada de §3 | Wiring con F78-F92 |
| **C9** | `properties.md §5.21` cita F102 + declara propiedad `self-evaluation-types` | Wiring con F47 |
| **C10** | `anti-patterns.md §2` lista AP13, AP14, AP15 | Wiring con F100 |
| **C11** | Wirings cerrados: `SKILL.md §5.3` menciona `self-evaluation.md`; `references/09-study/README.md` no marca `[pendiente F102]` | Wirings |

### Derivados (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **D1** | `wc -l self-evaluation.md` ≤ 600 | INV-02 |
| **D2** | 8 secciones canónicas §1-§8 presentes | Estructura |
| **D3** | Las 8 notas fixture pasan `density_check.py --strict` exit 0 | R1-R8 F76 (con exención R3/R5/R8 en `## Autoevaluación`) |

## Salida esperada

```
PASS 14/14
  [PASS] C1
  [PASS] C2
  [PASS] C3
  [PASS] C4
  [PASS] C5
  [PASS] C6
  [PASS] C7
  [PASS] C8
  [PASS] C9
  [PASS] C10
  [PASS] C11
  [PASS] D1
  [PASS] D2
  [PASS] D3
```

## Wirings (fases relacionadas)

- **F45** `references/04-authoring/block-directives.md` §10.7 (`:::collapsible`) y §10.17 (`:::question`) — primitivas reutilizadas.
- **F46** `references/04-authoring/inline-marks.md` — `{src:blk_xxxx}` y `[[note:id]]` para los fundamentos.
- **F47** `references/04-authoring/properties.md` §5.21 — propiedad opcional `self-evaluation-types`.
- **F51** `references/04-authoring/depth-layers.md` — `## Autoevaluación` en L2; collapsibles en L3.
- **F76** `references/07-visual/density.md` + `density_check.py` — R1-R8 con exención R3/R5/R8 en la sección `## Autoevaluación`.
- **F78-F92** `references/05-note-types/*.md` — los 15 tipos declaran `### Autoevaluación` con tabla copiada de §3.
- **F98** `references/06-writing/paraphrase.md` §2 L1-L8 — literales verbatim excluidos del cómputo Jaccard.
- **F100** `references/06-writing/anti-patterns.md` §2 — AP13, AP14, AP15 específicos de autoevaluación.
- **F101** `references/06-writing/i18n-and-citation.md` §3 — lista de 45 no-traducibles usada por V4.

## Sin dependencias externas

Python 3.9+ stdlib puro + invocación de `density_check.py` (F76) y
`self_eval_check.py` (F102). Las 8 notas se generan inline en
`build_fixtures.py` para evitar divergencia entre fixtures y la regla
que verifican.
