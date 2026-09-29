---
title: "TCP three-way handshake"
note-type: concept
status: published
summary: "Apertura de conexión TCP en 3 pasos: SYN, SYN+ACK y ACK, donde cada lado confirma que puede enviar y recibir."
reading-time-minutes: 5
language: es-en
tags: [type/concept, domain/networking, f78/concept, f101/i18n]
source: "evals/corpus/03-rfc-7231/sdm.json"
source-type: rfc
source-anchor: "section_path=/rfc9293/connection-establishment"
retrieved: 2026-09-29
product: "TCP"
product-version: "RFC 9293"
related: "[[note:tcp-states]], [[note:isn]]"
---

# TCP three-way handshake

La conexión TCP requiere probar que ambos lados pueden enviar y
recibir en ese instante ([[en:three-way-handshake]]). {src:blk_b12c44f0a8e7}

## TL;DR

El cliente envía SYN; el servidor responde SYN+ACK; el cliente cierra
con ACK. Tras los 3 mensajes, ambos lados saben que pueden enviar y
recibir. {src:blk_b12c44f0a8e7}

## Definición formal

Estados del cliente:

- `CLOSED` → enviar `SYN` → `SYN-SENT`
- `SYN-SENT` → recibir `SYN+ACK` y enviar `ACK` → `ESTABLISHED` {src:blk_b12c44f0a8e7}

## Mecanismo

TCP usa 3 mensajes para confirmar bidireccionalidad. Los números de
secuencia iniciales (ISN) se negocian en los dos primeros mensajes. {src:blk_b12c44f0a8e7}

## Glosario

| Término | ES | EN |
|---|---|---|
| `three-way-handshake` | Apertura de conexión TCP en 3 pasos | TCP three-way handshake |
| `isn` | Número de secuencia inicial | Initial Sequence Number |
| `syn` | Petición de sincronización | Synchronize |

## Procedencia

| Campo | Valor |
|---|---|
| **Fuente** | IETF RFC 9293 · rfc |
| **Versión** | RFC 9293 (agosto 2022) |
| **Fecha de recuperación** | 2026-09-29 |
| **URL/anchor** | `section_path=/rfc9293/connection-establishment` |

## Backlinks

Notas relacionadas para profundizar en TCP. {src:blk_3f6b9d2e7c14}

- [[note:tcp-states]] — máquina de estados completa.
- [[note:isn]] — números de secuencia iniciales.
