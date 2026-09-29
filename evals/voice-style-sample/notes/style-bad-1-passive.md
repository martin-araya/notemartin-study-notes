---
title: "Tabla es creada por el usuario (pasiva)"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: ≥ 30% frases en voz pasiva. Falla R2 (voz activa)."
reading-time-minutes: 1
tags: [type/concept, domain/databases, f99/voice-style, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=1"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# Tabla es creada por el usuario (pasiva)

## TL;DR

La tabla es creada por el usuario con `CREATE TABLE`. La fila es marcada
por la transacción con `xmin`. La versión vieja es reciclada por
`VACUUM`. El resultado es devuelto al cliente.

## Mecanismo

La operación es ejecutada por el motor. El plan es generado por el
optimizador. El resultado es enviado al cliente. La conexión es
gestionada por el pool. {src:blk_a91f8e02c1d3}
