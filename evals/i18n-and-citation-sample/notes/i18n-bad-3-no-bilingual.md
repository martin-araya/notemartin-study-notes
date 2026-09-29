---
title: "Sin marcas bilingues"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: nota language: es-en sin marcas bilingues ni glosario. Falla AP3 + AP4."
reading-time-minutes: 1
language: es-en
tags: [type/concept, domain/networking, f101/i18n, fixture/negative]
source: "evals/corpus/03-rfc-7231/sdm.json"
source-type: rfc
source-anchor: "section_path=/rfc9293/intro"
retrieved: 2026-09-29
product: "TCP"
product-version: "RFC 9293"
---

# Sin marcas bilingues

La conexion TCP requiere probar que ambos lados pueden enviar y recibir
en ese instante. {src:blk_b12c44f0a8e7}

## TL;DR

El cliente envia SYN; el servidor responde SYN+ACK; el cliente cierra
con ACK. {src:blk_b12c44f0a8e7}

## Procedencia

| Campo | Valor |
|---|---|
| **Fuente** | IETF RFC 9293 · rfc |
| **Versión** | RFC 9293 |
| **Fecha de recuperación** | 2026-09-29 |
| **URL/anchor** | `section_path=/rfc9293/intro` |
| {src:blk_b12c44f0a8e7}

## Comentario del fixture

BAD: la nota tiene language bilingue pero no usa las marcas de primera
aparicion ni tiene la seccion de glosario al pie.
