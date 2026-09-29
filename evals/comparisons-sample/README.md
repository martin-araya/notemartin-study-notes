# `evals/comparisons-sample/` — Fase 97 `Comparaciones y trade-offs`

Eval de la Fase 97 — patrón transversal de comparación (5 formas canónicas:
tabla lado a lado / jerarquía por relajación / matriz de decisión / tabla
de trade-offs / párrafo de síntesis), ≥ 3 plantillas, 5 marcas de
comparación derivada, 8 anti-patrones y 10 señales algorítmicas. Verifica
que `skill/notemartin-study-notes/references/06-writing/comparisons.md`
materializa los 3 criterios del ROADMAP §1668-1670.

## Estructura

| Archivo / carpeta | Rol |
|---|---|
| `notes/cmp-db-postgres-vs-mysql.md` | Comparación **DB vs DB**: tabla lado a lado con fila decisiva + síntesis con 2 similitudes + 1 diferencia. |
| `notes/cmp-rest-vs-grpc.md` | Comparación **protocolos**: tabla + jerarquía por relajación + síntesis. |
| `notes/cmp-mono-vs-micro.md` | Comparación **arquitectura**: trade-offs + matriz de decisión por escenario (criterio #3 ROADMAP). |
| `notes/cmp-sql-vs-nosql-hierarchy.md` | **Jerarquía por relajación** (4 niveles): SQL → NewSQL → NoSQL documental → NoSQL clave-valor. |
| `notes/anti-missing-sintesis.md` | Fixture **NEGATIVO**: tabla sin `## Síntesis` (test de la señal D1/C6). |
| `build_fixtures.py` | Regenera las 5 notas inline. Idempotente; `--force` regenera. |
| `run_eval.py` | Batería de 18 sub-criterios (3 ROADMAP + 4 positivos + 5 reglas/wirings + 6 derivados). |
| `README.md` | Este archivo. |

## Modo de uso

```bash
# Regenera fixtures y ejecuta el eval.
python3 evals/comparisons-sample/build_fixtures.py --force
python3 evals/comparisons-sample/run_eval.py

# Solo evalúa (asume fixtures ya generadas).
python3 evals/comparisons-sample/run_eval.py
```

## Batería (18 sub-criterios)

### Criterios ROADMAP (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C1** | `comparisons.md` existe, ≤ 600 líneas, contiene las 13 secciones canónicas | Estructura del doc |
| **C2** | §3 tiene 3 plantillas (DB / protocolos / arquitectura) | Plantillas |
| **C3** | §4 incluye tabla lado a lado con regla de fila decisiva (`:::tip`) + regla de paralelismo | Forma F1 |

### Positivos (4)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C4** | §6 matriz de decisión por escenario con ≥ 3 filas | Forma F3 |
| **C5** | §7 tabla de trade-offs con ≥ 3 filas | Forma F4 |
| **C6** | 4 notas base tienen tabla + `## Síntesis` ≥ 30 palabras con ≥ 2 similitudes + 1 diferencia | Criterio #1 ROADMAP |
| **C7** | 4 notas base declaran `:::derived` o `:::external` cuando la comparación la construye el agente | Criterio #2 ROADMAP |

### Reglas y wirings (5)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C8** | `cmp-sql-vs-nosql-hierarchy.md` tiene ≥ 3 niveles en la jerarquía | Criterio #3 ROADMAP (forma F2) |
| **C9** | Wirings cerrados (`06-writing/README.md` y `SKILL.md` mencionan `comparisons.md`) | Wirings F78-F101 |
| **C10** | Las 4 notas base pasan `density_check.py --strict` exit 0 | R1-R8 F76 |
| **C11** | `anti-missing-sintesis.md` NO tiene `## Síntesis` (test negativo de D1) | Test de regresión |
| **C12** | `cmp-mono-vs-micro.md` tiene ≥ 1 matriz de decisión con ≥ 3 filas | Criterio #3 ROADMAP |

### Derivados (6)

| # | Sub-criterio | Verifica |
|---|---|---|
| **D1** | `wc -l comparisons.md` ≤ 600 | INV-02 |
| **D2** | 13 secciones canónicas §1-§13 presentes (alias C1) | Estructura |
| **D3** | §5 jerarquía por relajación tiene ≥ 3 niveles | Forma F2 |
| **D4** | §11 tiene ≥ 8 señales D1-D10 algorítmicas | Diagnóstico |
| **D5** | Wirings cerrados (alias C9) | Wirings |
| **D6** | `density_check` (alias C10) | R1-R8 F76 |

## Salida esperada

```
PASS 18/18
```

## Wirings (fases relacionadas)

- **F45** `references/04-authoring/block-directives.md` §10.11-§10.12 — `:::derived` / `:::external`.
- **F46** `references/04-authoring/inline-marks.md` — `{derived}` / `{external}` inline.
- **F76** `references/07-visual/density.md` + `scripts/validate/density_check.py` — R1-R8.
- **F78** `references/05-note-types/concept.md` §3 fila `## Comparaciones` — usa F1+F5.
- **F83** `references/05-note-types/architecture.md` `## Trade-offs` — usa F4.
- **F87** `references/05-note-types/comparison.md` — tipo de nota dedicado.
- **F94-F96** — citadas desde §12 del doc principal.

## Sin dependencias externas

Python 3.9+ stdlib puro + invocación de `density_check.py` (F76) que
también es stdlib puro. Las 5 notas se generan inline para evitar
divergencia entre fixtures y la regla que verifican.
