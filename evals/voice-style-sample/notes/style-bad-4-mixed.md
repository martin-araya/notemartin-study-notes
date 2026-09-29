---
title: "Tiempos mezclados (mixed-tenses)"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: presente + pasado + futuro en la misma sección."
reading-time-minutes: 1
tags: [type/concept, domain/databases, f99/voice-style, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=1"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# Tiempos mezclados (mixed-tenses)

## TL;DR

PostgreSQL crea la tabla. El usuario la modificó. La aplicación consultará
los datos. `VACUUM` libera espacio. El servidor responde a las
peticiones.

## Mecanismo

PostgreSQL crea cada fila con `xmin`. La transacción marcó la fila como
vieja. `VACUUM` reciclará las versiones. El cliente recibirá el resultado.
