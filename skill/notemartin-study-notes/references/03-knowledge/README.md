# `references/03-knowledge/`

Reglas de L2 (capa de conocimiento): unidades, ledger, grafo, plan, terminología, conflictos.

## Orden de lectura

Cargar al construir el `knowledge/` del workdir (L2). Cada archivo se cita por separado desde `SKILL.md` según la operación.

## Estado actual

- `information-units.md`
- `ledger.md`
- `ledger-operativo.md`
- `concept-graph.md`
- `terminology.md`
- `conflicts.md` `[pendiente F41]`
- `note-plan.md` `[pendiente F44]`

## Quién lee / quién produce

| Archivo | Lee | Produce |
|---|---|---|
| `information-units.md` | Agente al extraer unidades; F38 para enum cerrado y R1–R5 | F37 |
| `ledger.md` | Agente y script del ledger (F38) | F15 |
| `ledger-operativo.md` | Agente en L2 para mantener el ledger; F43 auditoría; F118 evals | F38 |
| `concept-graph.md` | Agente en L2 al construir grafo; F44 note-plan; F104 rutas; F43 auditoría | F39 |
| `terminology.md` | Agente en L2 al construir y mantener glosario; F44 note-plan; F43 auditoría; F118 evals | F40 |
| `conflicts.md` | Agente al detectar contradicciones | F41 |
| `note-plan.md` | Agente al dividir el trabajo | F44 |
