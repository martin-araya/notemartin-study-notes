---
title: "Captura de paquetes SYN con tcpdump"
note-type: concept
status: published
summary: "Ejemplo ejecutable de tcpdump filtrando SYN con captura verbatim y limpieza."
reading-time-minutes: 2
tags: [type/example, domain/networking, f78/concept, f96/executable-examples]
source: "evals/corpus/03-rfc-7231/sdm.json"
source-type: rfc
source-anchor: "section_path=/rfc9293/tcp-flags"
retrieved: 2026-09-28
product: "tcpdump"
product-version: "4.99"
related: "[[note:tcp-three-way-handshake]]"
---

# Captura de paquetes SYN con tcpdump

> Cabecera. Resumen, procedencia, versión, estado y tiempo de lectura en el
> frontmatter superior.

## TL;DR

`tcpdump -i any -w captura.pcap 'tcp[tcpflags] & tcp-syn != 0'` filtra
los paquetes SYN y los guarda en un archivo para análisis posterior. {src:blk_3f6b9d2e7c14}

> **Entorno:** Linux kernel 6.8 · tcpdump 4.99 · iface `eth0` · permisos root (CAP_NET_RAW). {src:blk_a2b3c4d5e6f7}

Ejemplo reproducible basado en el RFC 9293. {src:blk_4f5a6b7c8d9e}

:::example
## Setup

Inicia `tcpdump` en background con el filtro SYN y guarda el PID. {src:blk_7a8e2c1b9d34}

```bash
# {src:blk_e01b2c3d4e5f}
sudo tcpdump -i eth0 -w /tmp/syn.pcap 'tcp[tcpflags] & tcp-syn != 0' &
TCPDUMP_PID=$!
```

## Acción

Genera una conexión TCP saliente que producirá el 3WHS. {src:blk_4e1f8a3c6b97}

```bash
# {src:blk_f12c3d4e5a6b}
curl -s https://example.com > /dev/null
```

## Resultado

Lectura del archivo pcap; deben verse las 3 fases del handshake (S, S., .). {src:blk_9b2d5e8f1c67}

```bash
# {src:blk_a7b8c9d0e1f2}
sudo tcpdump -r /tmp/syn.pcap 2>/dev/null | head -3
```

```
# {src:blk_6b7c8d9e0f1a}
Reading from file /tmp/syn.pcap, link-type EN10MB (Ethernet)
12:00:01.123 IP 192.168.1.10.54321 > 93.184.216.34.443: Flags [S], seq 12345
12:00:01.234 IP 93.184.216.34.443 > 192.168.1.10.54321: Flags [S.], seq 50000, ack 12346
12:00:01.235 IP 192.168.1.10.54321 > 93.184.216.34.443: Flags [.], ack 50001
```

## Limpieza

Termina `tcpdump` y elimina el archivo de captura. {src:blk_6c4a7b0e3d92}

```bash
# {src:blk_b3c4d5e6f7a8}
sudo kill $TCPDUMP_PID
sudo rm /tmp/syn.pcap
```
:::
