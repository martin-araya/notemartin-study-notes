# `evals/voice-style-sample/` — Fase 99 `Voz y estilo`

Eval de la Fase 99 — patrón transversal de voz y estilo (8 reglas
verificables R1-R8: frases cortas, voz activa, sin adjetivos valorativos,
sin relleno, segunda persona en procedimientos, tiempos consistentes,
sin nominalizaciones, sin subjuntivo dudoso), tabla cerrada de 20
adjetivos valorativos prohibidos, 8 anti-patrones AP1-AP8, plantilla
de verificación con 8 preguntas binarias. Verifica los 3 criterios del
ROADMAP §1684-1686.

## Estructura

| Archivo / carpeta | Rol |
|---|---|
| `notes/style-good-1.md` | **Positivo**: nota `concept` PostgreSQL con las 8 reglas aplicadas. |
| `notes/style-good-2.md` | **Positivo**: nota `procedure` Kubernetes con segunda persona. |
| `notes/style-bad-1-passive.md` | **Negativo**: ≥ 30% frases en voz pasiva (falla R2). |
| `notes/style-bad-2-adjectives.md` | **Negativo**: ≥ 5 adjetivos valorativos (falla R3). |
| `notes/style-bad-3-long.md` | **Negativo**: ≥ 50% frases > 25 palabras (falla R1). |
| `notes/style-bad-4-mixed.md` | **Negativo**: mezcla de presente + pasado + futuro (falla R6). |
| `build_fixtures.py` | Regenera las 6 notas inline. Idempotente; `--force` regenera. |
| `run_eval.py` | Batería de 17 sub-criterios (3 ROADMAP + 5 positivos + 3 reglas/wirings + 6 derivados). |
| `README.md` | Este archivo. |

## Modo de uso

```bash
# Regenera fixtures y ejecuta el eval.
python3 evals/voice-style-sample/build_fixtures.py --force
python3 evals/voice-style-sample/run_eval.py

# Solo evalúa (asume fixtures ya generadas).
python3 evals/voice-style-sample/run_eval.py
```

## Batería (17 sub-criterios)

### Criterios ROADMAP (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C1** | `voice-style.md` existe, ≤ 500 líneas, 11 secciones canónicas | Estructura del doc |
| **C2** | §2 tiene 8 reglas R1-R8 con regex/señal algorítmica | Criterio #1 ROADMAP |
| **C3** | §3 tiene ≥ 15 adjetivos V1-V20 | Criterio #2 ROADMAP (≥ 15 entradas) |

### Positivos (5)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C4** | 2 notas base (style-good-1, style-good-2) cumplen R1, R2, R3 | Criterio #3 ROADMAP (estilo idéntico entre fuentes) |
| **C5** | style-bad-1-passive detectado por R2 (≥ 30% pasivas) | Criterio #1 ROADMAP (regla verificable) |
| **C6** | style-bad-2-adjectives detectado por R3 (≥ 5 adjetivos) | Criterio #1 ROADMAP |
| **C7** | style-bad-3-long detectado por R1 (≥ 50% frases largas) | Criterio #1 ROADMAP |
| **C8** | style-bad-4-mixed detectado por R6 (mezcla de tiempos) | Criterio #1 ROADMAP |

### Reglas y wirings (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C9** | §9 tiene 8 preguntas binarias P1-P8 con método algorítmico | Plantilla de verificación |
| **C10** | Wirings cerrados (`06-writing/README.md` y `SKILL.md` mencionan `voice-style.md`) | Wirings |
| **C11** | Las 6 notas fixture pasan `density_check.py --strict` exit 0 | R1-R8 F76 |

### Derivados (6)

| # | Sub-criterio | Verifica |
|---|---|---|
| **D1** | `wc -l voice-style.md` ≤ 500 | INV-02 |
| **D2** | 11 secciones canónicas §1-§11 presentes | Estructura |
| **D3** | §3 tiene ≥ 15 adjetivos (alias C3) | Tabla cerrada |
| **D4** | §6 tabla de persona tiene ≥ 4 filas | Persona por sección |
| **D5** | §7 regla de tiempos tiene regex concreto | Tiempos |
| **D6** | Wirings cerrados (alias C10) | Wirings |

## Salida esperada

```
PASS 17/17
```

## Wirings (fases relacionadas)

- **F42** `references/10-quality/fidelity-rules.md` — citas SDM.
- **F46** `references/04-authoring/inline-marks.md` — marcas inline.
- **F51** `references/04-authoring/depth-layers.md` — capas L1/L2/L3.
- **F76** `references/07-visual/density.md` + `scripts/validate/density_check.py` — R1-R8.
- **F78** `references/05-note-types/concept.md` §3 — 10 secciones obligatorias.
- **F80** `references/05-note-types/procedure.md` — segunda persona obligatoria.
- **F94-F98** — citadas desde §10 del doc principal.

## Sin dependencias externas

Python 3.9+ stdlib puro + invocación de `density_check.py` (F76) que
también es stdlib puro. Las 6 notas se generan inline para evitar
divergencia entre fixtures y la regla que verifican.
