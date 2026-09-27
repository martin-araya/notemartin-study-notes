# `evals/density-sample/` — Fase 76

Verificador de la Fase 76 (densidad y jerarquía). Cubre los 3 criterios del ROADMAP §1483-1485 con 5 sub-criterios:

| Criterio | Qué verifica | Método |
|---|---|---|
| **C1** | `density.md` existe, ≤ 500 líneas, contiene tabla cerrada R1-R8 (en §2 y §9) | in-process: wc + regex |
| **C2** | `density_check.py` detecta violación R2 en nota con párrafo > 200 palabras | exec del script |
| **C3** | `density_check.py` detecta violación R4 en nota con 4+ callouts consecutivos | exec del script |
| **C4** | `density_check.py` no emite R3 ni R6 en nota `glossary-term` (exenta per §4 de density.md) | exec del script |
| **C5** | `density_check.py` no emite errores en nota `compliant` que cumple R1-R8 | exec del script |

## Uso

```bash
python3 evals/density-sample/run_eval.py
```

## Salida esperada

```
============================================================
Fase 76 — Densidad y jerarquía
============================================================
  PASS  C1-doc-8-rules (309 líneas ≤ 500; §2 tabla=8 reglas, §9 tabla=8 reglas)
  PASS  C2-r2-detected (R2 detectado, exit=1)
  PASS  C3-r4-detected (R4 detectado, exit=1)
  PASS  C4-glossary-exempt (R3+R6 exentos; exit=0)
  PASS  C5-compliant (0 errores, exit=0)
============================================================
PASS 5/5
```

Exit code `0` si todos pasan; `1` si alguno falla.

## Archivos

- `build_fixtures.py` — las 5 notas sintéticas ya están commiteadas; el script no se usa en CI (se mantiene como referencia para regenerar las fixtures si cambian las reglas).
- `run_eval.py` — los 5 sub-criterios documentados arriba.
- `fixtures/notes/` — 5 notas sintéticas:
  - `r2-violation.md` — 1 párrafo de 201 palabras (viola R2).
  - `r4-violation.md` — 4 callouts consecutivos (viola R4).
  - `r5-violation.md` — 8 viñetas consecutivas (viola R5; bonus test).
  - `glossary.md` — `note-type: glossary-term` con sección 100% viñetas; exenta de R3+R6.
  - `compliant.md` — golden que cumple las 8 reglas.

## Wirings

- Cierra los 3 criterios de `ROADMAP.md` §1483-1485 para Fase 76.
- El criterio C1 (8 reglas numeradas) es el más estricto: garantiza que la tabla cerrada existe y que se publica tanto en la sección principal como en el apéndice de notas históricas.
- El criterio C4 (exenciones) es el segundo más estricto: garantiza que las exenciones documentadas en `density.md` §4 (glossary-term, cheatsheet, index-moc) están implementadas en el código.

## Exenciones verificadas

- **glossary-term:** exenta de R3 (frecuencia mínima) y R6 (sección 100% viñetas). El fixture `glossary.md` tiene 8 bullets sin anclaje; el script NO emite R3 ni R6.
- **cheatsheet, index-moc:** no tienen fixtures específicos, pero las exenciones están implementadas en `EXEMPT_FROM_R3`, `EXEMPT_FROM_R5`, `EXEMPT_FROM_R6` en `scripts/validate/density_check.py`.
