# `references/00-pipeline/`

Reglas globales del pipeline: división agente/script, arquitectura de capas y manifiesto reanudable.

## Orden de lectura

Cargar al inicio de cada sesión, antes de cualquier operación sobre una fuente.

## Estado actual

- [`responsibilities.md`](responsibilities.md) `[existente]` — F3: test de tres preguntas, anti-patrones, auditoría de scripts e instrucciones.
- [`architecture.md`](architecture.md) `[existente]` — F4: contrato de las 5 capas, workdir, modo degradado.
- [`book-mode.md`](book-mode.md) `[existente]` — F106: modo obra completa (reconocimiento previo, estado compartido, consolidación parcial, stop/resume).
- [`chunk-loop.md`](chunk-loop.md) `[existente]` — F107: bucle por chunks y presupuesto de contexto (ciclo 6 etapas, unidades cruzadas, anti-full-load).
- `manifest.md` `[pendiente F16]` — reglas del manifiesto reanudable.

## Quién lee / quién produce

| Archivo | Lee | Produce |
|---|---|---|
| `responsibilities.md` | Toda fase que implemente script o reference | F3 (este paquete) |
| `architecture.md` | Toda fase que produzca o consuma un artefacto | F4 (este paquete) |
| `book-mode.md` | Toda fase que opere sobre una fuente multi-capítulo | F106 (este paquete) |
| `chunk-loop.md` | Toda fase que procese una fuente cuyo SDM supere el presupuesto de contexto | F107 (este paquete) |
| `manifest.md` | F31, F62, F111 | F16 |
