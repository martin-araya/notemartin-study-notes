# `references/00-pipeline/`

Reglas globales del pipeline: división agente/script, arquitectura de capas y manifiesto reanudable.

## Orden de lectura

Cargar al inicio de cada sesión, antes de cualquier operación sobre una fuente.

## Estado actual

- [`responsibilities.md`](responsibilities.md) `[existente]` — F3: test de tres preguntas, anti-patrones, auditoría de scripts e instrucciones.
- [`architecture.md`](architecture.md) `[existente]` — F4: contrato de las 5 capas, workdir, modo degradado.
- `manifest.md` `[pendiente F16]` — reglas del manifiesto reanudable.

## Quién lee / quién produce

| Archivo | Lee | Produce |
|---|---|---|
| `responsibilities.md` | Toda fase que implemente script o reference | F3 (este paquete) |
| `architecture.md` | Toda fase que produzca o consuma un artefacto | F4 (este paquete) |
| `manifest.md` | F31, F62, F111 | F16 |
