# ADR-0002 — Separación `validate_ledger.py` (F15) vs `ledger.py` (F38)

**Fecha:** 2026-09-25
**Estado:** aceptada
**Atada a:** F15, F38, INV-04 (separación de concerns)

## Contexto

F15 cerró el Coverage Ledger como artefacto validable: el JSON, el schema, los invariantes L-01–L-05 y el linter `validate_ledger.py` (read-only). F38 cierra el siguiente paso: un CLI que el agente usa en L2 para **mantener** el ledger — `init`, `add`, `mark`, `report`, `check`, `manifest`. Ambos scripts tocan `knowledge/ledger.json`.

Las alternativas consideradas:

1. **Un solo script** con `--mode {read-only,rw}` o subcomandos que mezclan validación y operación. Descartada: mezcla concerns (CI vs agente runtime), dificulta el linting puro en CI sin dependencias de runtime, y rompe el principio de un script por responsabilidad (`skills/AGENT.md` §6).
2. **Fusionar `validate_ledger.py` en `ledger.py`** y deprecar el primero. Descartada: el linter lo invoca CI sin necesidad del workdir completo; `ledger.py` requiere SDM + ledger + manifest. Romper el linter para reescribir el operador arrastra dependencias innecesarias.
3. **Dos scripts conviviendo** con responsabilidades distintas. Elegida.

## Decisión

1. **`validate_ledger.py` (F15) permanece** como linter read-only para CI. Comando típico: `python3 scripts/util/validate_ledger.py --validate ledger.json` desde cualquier runner.
2. **`ledger.py` (F38) es el operador read+write** que el agente invoca en L2. Comando típico: `python3 scripts/util/ledger.py --workdir .notes-work/<hash> add --unit-id ...`.
3. **Comparten el path del archivo** `knowledge/ledger.json`. Ambos usan escritura atómica `tempfile` + `Path.replace` (L-04). Como ambos leen el archivo completo antes de escribir, no hay race condition lógica: el último en escribir gana.
4. **Comparten ~30 líneas** de lógica de reporte (`_coverage_report`); si la duplicación crece, refactor menor a `scripts/util/_report.py`. No se hace ahora (ruido); ADR-0003 podría cerrarlo si en F118 la duplicación duele.
5. **No comparten dependencias de runtime**: `validate_ledger.py` requiere `jsonschema`; `ledger.py` la trata como opcional. Esto preserva la portabilidad del linter.

## Consecuencias

**Gana**:
- CI sigue corriendo un linter puro, sin la complejidad del workdir, sin la dependencia operativa del operador.
- El operador `ledger.py` puede evolucionar (más subcomandos, integración con otros artefactos) sin tocar el linter ni reabrir F15.
- El cambio de `schema_version` (F38 bumpea de 1.0.0 a 2.0.0) se gestiona aquí, en `ledger.py`, sin romper `validate_ledger.py` que ya enforza la nueva versión por el const `"2.0.0"`.

**Pierde**:
- Dos CLIs con nombres similares (`validate_ledger.py` vs `ledger.py`) pueden confundir al usuario novel. Mitigado por SKILL.md §6 que los distingue explícitamente.
- Si el reporte de cobertura diverge entre los dos, hay dos fuentes de verdad. Mitigado por tests de no-regresión (sub-check 4 del eval de F38).

**Queda atado**:
- INV-04: separación de concerns. Cada script tiene una responsabilidad primaria.
- F15: schema endurecido en F38; los ledgers pre-2.0 con tipos fuera del enum cerrado fallan la validación — breaking change documentado.
- F43 auditoría: usa `ledger.py check --strict` para verificar no-pérdida.
