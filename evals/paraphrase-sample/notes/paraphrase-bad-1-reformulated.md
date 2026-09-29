---
title: "Parafraseo con mensaje reformulado (anti-ejemplo)"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: el mensaje de error fue reformulado, perdiendo el literal."
reading-time-minutes: 1
tags: [type/paraphrase, domain/databases, f98/paraphrase, fixture/negative]
source: "evals/paraphrase-sample/corpus/source-1-oracle.txt"
source-type: docs
source-anchor: "section_path=/ch01/intro"
retrieved: 2026-09-28
---

# Parafraseo con mensaje reformulado (anti-ejemplo)

Antes de Oracle RAC, una base de datos podía caerse con un solo servidor.
RAC añade mecanismos de protección y comando de verificación. {src:blk_b12c44f0a8e7}

## Error reformulado (ANTICIPADA)

Cuando un nodo falla, el alert log reporta un error indicando que no se
pudo conectar al servicio de sincronización del cluster. {src:blk_b12c44f0a8e7}

## Comentario del fixture

BAD: el mensaje original `ORA-29701: unable to connect to Cluster
Synchronization Service` fue REFORMULADO a "no se pudo conectar al
servicio de sincronización del cluster". Esto viola INV-09 (L1
mensajes de error verbatim). {src:blk_b12c44f0a8e7}
