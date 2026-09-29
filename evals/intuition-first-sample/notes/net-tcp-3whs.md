---
title: "TCP three-way handshake"
note-type: concept
status: published
summary: "Apertura de conexión TCP en tres mensajes: SYN, SYN+ACK y ACK, donde cada lado confirma que puede enviar y recibir."
reading-time-minutes: 5
tags: [type/concept, domain/networking, f78/concept, f94/intuition-first]
source: "evals/corpus/03-rfc-7231/sdm.json"
source-type: rfc
source-anchor: "section_path=/rfc9293/connection-establishment"
source-url: ""
retrieved: 2026-09-28
product: "TCP"
product-version: "RFC 9293"
related: "[[note:tcp-states]], [[note:isn]]"
---

# TCP three-way handshake

> Cabecera. Resumen, procedencia, versión, estado y tiempo de lectura en el
> frontmatter superior.

## TL;DR

El handshake TCP son tres mensajes: el cliente envía SYN, el servidor
responde SYN+ACK y el cliente cierra con ACK. Tras los tres, ambos lados
saben que pueden enviar y recibir.

## Problema

Antes del handshake de tres pasos, los primeros protocolos (ej. TFTP sobre
datagrama único) abrían una conexión enviando datos directamente. El problema
es que un datagrama de petición podía ser duplicado por la red y el servidor
entregaba el archivo dos veces si lo procesaba dos veces. {src:blk_b712}

## Intuición

La conexión TCP necesita probar que ambos lados pueden enviar y recibir en
ese instante. Eso requiere tres mensajes: el cliente dice "quiero hablar"
(SYN), el servidor reconoce y propone parámetros (SYN+ACK), y el cliente
reconoce a su vez (ACK). [[term:three-way-handshake]]

## Analogía

Como una llamada telefónica: tú marcas mi número, yo descuelgo y digo
"¿Hola?", tú dices "Hola, soy yo". Solo después de los tres "habla" sabemos
que los dos podemos oír y ser oídos. :::external
**Dónde se rompe:** en una llamada no se negocian números de secuencia;
TCP sí, porque los paquetes pueden llegar fuera de orden.

## Definición formal

Estados y transiciones del cliente:

| Estado cliente | Evento | Estado siguiente | Envía |
|---|---|---|---|
| CLOSED | enviar SYN | SYN-SENT | SYN seq=ISN_c |
| SYN-SENT | recibir SYN+ACK, enviar ACK | ESTABLISHED | ACK seq=ISN_c+1, ack=ISN_s+1 |
| ESTABLISHED | datos | ESTABLISHED | — |

{src:blk_b712}

:::equation
SYN:        cliente → servidor, seq = ISN_c
SYN+ACK:    servidor → cliente, seq = ISN_s, ack = ISN_c + 1
ACK:        cliente → servidor, seq = ISN_c + 1, ack = ISN_s + 1
:::

## Confirmación

`tcpdump -i any -nn -S port 80` durante `curl https://example.com` muestra
las tres líneas con flags `S`, `S.`, `.` (SYN, SYN+ACK, ACK) en orden. {src:blk_b712}

## Trampas

:::warning
**SYN flood.** Un atacante envía SYN sin completar el ACK. El servidor
acumula estado en SYN-RECEIVED hasta el timeout. Causa: el handshake
asimétrico expone al servidor a DoS. Evitación: SYN cookies o rate limit.
:::

## Resumen

- TCP abre conexión en 3 mensajes para confirmar envío + recepción en ambos lados. {src:blk_b712}
- Los números de secuencia iniciales (ISN) se negocian en los dos primeros mensajes. {src:blk_b712}

## Cuándo NO usarlo

- Cuando se necesita transferencia sin handshake (TFTP, QUIC 0-RTT). {external}

## Límites y alternativas

| Mecanismo | [[note:tcp-states]] | QUIC 0-RTT |
|---|---|---|
| Mensajes de apertura | 3 | 0-1 |
| Confirma envío + recepción | sí | parcial |

## Relacionados

- [[note:tcp-states]] — derivado (transiciones de estado).
- [[note:isn]] — prerrequisito (números de secuencia iniciales).

## Backlinks

- [[note:tcp-states]]

## Queries

```dataview
LIST FROM [[note:tcp-three-way-handshake]] AND -"templates"
```
