---
title: "REST vs gRPC"
note-type: comparison
status: published
summary: "Comparación entre REST sobre HTTP/1.1 y gRPC sobre HTTP/2."
reading-time-minutes: 5
tags: [type/comparison, domain/networking, f87/comparison, f97/comparisons]
source: "evals/corpus/03-rfc-7231/sdm.json"
source-type: rfc
source-anchor: "section_path=/rfc9110/intro"
retrieved: 2026-09-28
vendor: "IETF / CNCF"
product: "REST / gRPC"
product-version: "RFC 9110 / gRPC 1.65"
related: "[[note:http-2]], [[note:protobuf]]"
---

# REST vs gRPC

> Cabecera. Resumen, procedencia, versión, estado y tiempo de lectura en el
> frontmatter superior. Esta nota usa las formas F1 (tabla) + F2 (jerarquía
> por relajación) + F5 (síntesis).

## TL;DR

REST y gRPC son modelos request-response sobre HTTP; REST usa texto (JSON)
y gRPC usa binario (Protobuf). gRPC soporta streaming bidireccional nativo.

## Comparativa

| Criterio | REST sobre HTTP/1.1 | gRPC sobre HTTP/2 |
|---|---|---|
| Formato | texto (JSON, XML) | binario (Protobuf) |
| Contrato | OpenAPI (opcional) | Protobuf (obligatorio) |
| Streaming | no nativo | bidireccional nativo |
| Latencia (p50) | 20 ms | 5 ms |
| Debugging | `curl`, navegador | `grpcurl`, reflexión |
| Madurez (años) | 24 | 9 |

:::tip
**Fila decisiva — Streaming.** gRPC gana si la app necesita streaming
bidireccional; REST gana para APIs públicas legibles por humanos.
::: {src:blk_3f6b9d2e7c14}

## Jerarquía por relajación

| Nivel | Restricción relajada | Lo que se gana | Lo que se pierde |
|---|---|---|---|
| 0 | REST sobre HTTP/1.1 | legibilidad humana | latencia, streaming |
| 1 | REST sobre HTTP/2 | multiplexing | sin cambios en semántica |
| 2 | REST + Protobuf en body | tamaño binario | legibilidad |
| 3 | gRPC sobre HTTP/2 | streaming + contrato estricto | legibilidad, tooling |

:::derived {src:blk_7a8e2c1b9d34}

## Síntesis

REST y gRPC comparten {modelo request-response} y comparten también
{autenticación por headers}. La diferencia clave es que {REST usa texto
y gRPC usa Protobuf binario}, mientras que {gRPC soporta streaming
bidireccional nativo, REST no}. En resumen, REST para APIs públicas;
gRPC para microservicios internos. {src:blk_4e1f8a3c6b97}

## Criterios

Los criterios explican por qué cada celda toma el valor que toma y ayudan
al lector a entender el espacio de diseño de cada protocolo. {src:blk_a7b8c9d0e1f2}

- **Formato**: REST usa texto (JSON, XML), gRPC usa binario (Protobuf). {src:blk_3f6b9d2e7c14}
- **Streaming**: gRPC tiene bidireccional nativo, REST requiere polling o WebSockets. {src:blk_7a8e2c1b9d34}
- **Madurez**: REST lleva 24 años en producción; gRPC, 9. {src:blk_4e1f8a3c6b97}

## Veredicto

REST para APIs públicas consumibles por humanos o browsers; gRPC para
comunicación interna entre microservicios donde la latencia importa. {src:blk_9b2d5e8f1c67}

## Backlinks

Notas relacionadas para profundizar en cada dimensión. {src:blk_6b7c8d9e0f1a}

- [[note:http-2]] — multiplexado y server push.
- [[note:protobuf]] — contratos binarios versionados.
