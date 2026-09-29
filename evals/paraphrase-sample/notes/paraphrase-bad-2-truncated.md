---
title: "Parafraseo con enumeración truncada (anti-ejemplo)"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: la enumeración de 4 motivos termina en 'etc.', perdiendo 2 ítems."
reading-time-minutes: 1
tags: [type/paraphrase, domain/networking, f98/paraphrase, fixture/negative]
source: "evals/paraphrase-sample/corpus/source-2-kubernetes.txt"
source-type: docs
source-anchor: "section_path=/ch02/pods"
retrieved: 2026-09-28
---

# Parafraseo con enumeración truncada (anti-ejemplo)

Los pods de Kubernetes pueden fallar al iniciar por motivos comunes
(imagen no encontrada, recursos insuficientes, etc.) y errores de
configuración. {src:blk_5e7f0a3b2c19}

## Enumeración truncada (ANTICIPADA)

Los motivos por los que un pod puede fallar son:
- imagen no encontrada
- recursos insuficientes
- etc.

## Comentario del fixture

BAD: la enumeración original tiene 4 motivos. El parafraseo lista 2
+ `etc.`, perdiendo los motivos 3 (configuración de probe) y 4
(volumen no montado). Esto viola INV-10 y F98 §5.2. {src:blk_5e7f0a3b2c19}
