# `references/10-quality/`

Reglas de calidad: fidelidad (tres niveles), auditoría de no-pérdida, checklist
consolidado por tipo de nota.

## Orden de lectura

Cargar al redactar contenido fáctico y antes de cerrar cualquier trabajo.
`checklists-by-type.md` (F112) se carga tras redactar la última sección del
tipo y antes del cierre.

## Estado actual

- `fidelity-rules.md`
- `completeness-audit.md`
- `checklists-by-type.md` (F112) — checklist consolidado de cierre por tipo;
  3 secciones (común, 15 bloques por tipo, reglas por perfil) + orden cheap→expensive.
- `validators.md` (F113) — spec normativa de la suite de validadores:
  schema común JSON (severidades + exit codes), catálogo de 16 categorías ×
  12 validadores, reglas duras R-V-01..05, 3 modos de ejecución (--note /
  --notes-dir / --workdir).
- `fidelity-audit.md` (F114) — spec normativa de la auditoría semántica
  automatizada de fidelidad: 3 pasadas (forward source-check, content-
  fidelity check, inverse sample), 7 reglas V-FAUDIT-01..06 + V-FAUDIT-99,
  6 reglas duras R-FAUDIT-01..06.
- `quality-gate.md` (F115) — spec normativa de la puerta de calidad:
  4 fuentes agregadas (F43/F113/F114/F7) + F108 opcional; reporte
  JSON+Markdown con `summary`/`blocking`/`coverage`/`rubric`/
  `not_covered`/`debt_registry`; promoción a `status: verified` con
  bloqueo por errors o cobertura incompleta; CLI 5 sub-comandos.

## Quién lee / quién produce

| Archivo | Lee | Produce |
|---|---|---|
| `fidelity-rules.md` | Agente al redactar, F43 auditoría, F44 note-plan, F114 quality gate, F118 evals | F42 |
| `completeness-audit.md` | `completeness.py` (F43), humano al revisar; F44 note-plan antes de diseñar; F114 quality gate | F43 |
| `checklists-by-type.md` | Agente al cerrar nota, F113 validador (extrae [B]/[R]), F114 quality gate (cobertura), F111 incremental (diff), F118 evals | F112 |
| `validators.md` | Cada script `scripts/validate/*.py` sigue su contrato; F114 quality gate consume su JSON; F118 corre la suite | F113 |
| `fidelity-audit.md` | `scripts/audit/fidelity_audit.py` (3 clases ForwardSourceCheck + ContentFidelityCheck + InverseSampler); F114 quality gate mide cobertura continua; F118 corre `evals/fidelity-audit-sample/run_eval.py` | F114 |
| `quality-gate.md` | `scripts/quality_gate.py` (agregador de F43/F113/F114/F7/F108); cierra trabajos y promueve a `verified`; F118 corre `evals/quality-gate-sample/run_eval.py` | F115 |
