# `evals/paraphrase-sample/` — Fase 98 `Parafraseo fiel vs literal`

Eval de la Fase 98 — lista cerrada de literales protegidos (8 tipos),
técnica de enumeración de unidades (4 pasos), tabla de reformulaciones
prohibidas (≥ 12 pares), 7 anti-patrones y 3 verificaciones algorítmicas
V1-V3 que corresponden a los 3 criterios del ROADMAP §1676-1678.

## Estructura

| Carpeta / archivo | Rol |
|---|---|
| `corpus/source-1-oracle.txt` | Párrafo fuente Oracle RAC con 5 unidades (1 mensaje de error, 1 enumeración de 5, 2 definiciones, 1 comando). |
| `corpus/source-2-kubernetes.txt` | Párrafo fuente K8s con 1 mensaje, 1 enumeración de 4, 1 sintaxis, 1 warning. |
| `corpus/source-3-postgresql.txt` | Párrafo fuente PostgreSQL con 1 enumeración de 7, 1 default, 1 comando. |
| `notes/paraphrase-good-1.md` | **Positivo**: parafraseo CORRECTO de source-1 (cubre 5/5 unidades con literales verbatim). |
| `notes/paraphrase-bad-1-reformulated.md` | **Negativo**: parafraseo con mensaje reformulado (falla V1). |
| `notes/paraphrase-bad-2-truncated.md` | **Negativo**: parafraseo con enumeración truncada en `etc.` (falla V2). |
| `build_fixtures.py` | Regenera las 6 fixtures inline. Idempotente; `--force` regenera. |
| `run_eval.py` | Batería de 17 sub-criterios (3 ROADMAP + 5 positivos + 3 reglas/wirings + 6 derivados). |
| `README.md` | Este archivo. |

## Modo de uso

```bash
# Regenera fixtures y ejecuta el eval.
python3 evals/paraphrase-sample/build_fixtures.py --force
python3 evals/paraphrase-sample/run_eval.py

# Solo evalúa (asume fixtures ya generadas).
python3 evals/paraphrase-sample/run_eval.py
```

## Batería (17 sub-criterios)

### Criterios ROADMAP (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C1** | `paraphrase.md` existe, ≤ 600 líneas, contiene las 10 secciones canónicas | Estructura del doc |
| **C2** | §2 tiene ≥ 6 tipos de literales L1-L8 | Literales protegidos |
| **C3** | §5 menciona `etc.`, `entre otros`, `los más relevantes`, `y más`, `etcétera` | Palabras prohibidas |

### Positivos (5)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C4** | §6 incluye V1, V2, V3 con método algorítmico | Verificaciones |
| **C5** | `paraphrase-good-1.md` cubre ≥ 80% de unidades de source-1 (V3) | Criterio #3 ROADMAP |
| **C6** | `paraphrase-bad-1-reformulated.md` detectado por V1 | Criterio #1 ROADMAP |
| **C7** | `paraphrase-bad-2-truncated.md` detectado por V2 | Criterio #2 ROADMAP |
| **C8** | Los 3 corpus tienen ≥ 1 literal preservado en paraphrase-good-1 | Cross-check V3 |

### Reglas y wirings (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C9** | §7 tabla de reformulaciones prohibidas tiene ≥ 10 filas P* | Tabla cerrada |
| **C10** | Wirings cerrados (`06-writing/README.md` y `SKILL.md` mencionan `paraphrase.md`) | Wirings |
| **C11** | Las notas fixture pasan `density_check.py --strict` exit 0 | R1-R8 F76 |

### Derivados (6)

| # | Sub-criterio | Verifica |
|---|---|---|
| **D1** | `wc -l paraphrase.md` ≤ 600 | INV-02 |
| **D2** | 10 secciones canónicas §1-§10 presentes | Estructura |
| **D3** | §4 técnica de enumeración tiene 4 pasos numerados | Algoritmo |
| **D4** | §6 V1-V3 tienen método algorítmico (regex/conteo) | Diagnóstico |
| **D5** | §7 tabla ≥ 10 filas (alias C9) | Tabla |
| **D6** | Wirings cerrados (alias C10) | Wirings |

## Salida esperada

```
PASS 17/17
```

## Wirings (fases relacionadas)

- **F45** `references/04-authoring/block-directives.md` §10.4 — `:::example` con salida verbatim.
- **F46** `references/04-authoring/inline-marks.md` — `{src:blk_xxxx}` ancla el literal.
- **F76** `references/07-visual/density.md` + `scripts/validate/density_check.py` — R1-R8.
- **F78** `references/05-note-types/concept.md` §4.2 — marcas inline.
- **F94-F97** — citadas desde §9 del doc principal.
- **F99-F101** — out-of-scope explícito.

## Sin dependencias externas

Python 3.9+ stdlib puro + invocación de `density_check.py` (F76) que
también es stdlib puro. Los 6 fixtures se generan inline para evitar
divergencia entre fixtures y la regla que verifican.
