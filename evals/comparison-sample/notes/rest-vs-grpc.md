---
title: "REST vs gRPC (comparativa)"
note-type: comparison
status: draft
summary: "Comparativa de REST y gRPC: protocolo, schema, streaming, serialización, tooling y decisión por escenario (browser, microservices internal, mobile, public API)."
tags: [type/comparison, domain/api]
source: "REST Fielding 2000 vs gRPC docs"
source-type: docs
source-anchor: "comparativa"
retrieved: 2026-09-27
vendor: IETF / Google
product: REST / gRPC
product-version: "Fielding / 1.65"
related: "[[note:api-reference-curl-options]], [[note:http-status-codes]]"
---

# REST vs gRPC (comparativa)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Comparativa de REST y gRPC: protocolo, schema, streaming, serialización, tooling y decisión por escenario. |
| **Procedencia** | REST Fielding 2000 vs gRPC docs (docs) §comparativa · recuperado 2026-09-27 |
| **Versión** | Fielding / 1.65 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
REST usa HTTP/JSON con schema implícito; gRPC usa HTTP/2 + Protobuf con schema explícito. REST es ideal para APIs públicas y browser; gRPC es ideal para microservicios internos y streaming. La elección depende del contexto. {src:blk_b00000000201}

{layer:l2} {src:blk_fedcba000100}

## Comparativa
| Criterio | REST | gRPC |
|---|---|---|
| Protocolo | HTTP/1.1 o HTTP/2 | HTTP/2 obligatorio |
| Schema | implícito (OpenAPI opcional) | explícito (Protobuf .proto) |
| Serialización | JSON (texto) | Protobuf (binario) |
| Streaming | no nativo | bidireccional nativo |
| Tooling (codegen) | OpenAPI generators | nativo desde .proto |
| Tipos de datos | dinámicos | estáticos (typed) |
:::tip
**Fila decisiva — Schema.** REST tiene schema implícito (OpenAPI opcional, a menudo inexistente en producción); gRPC tiene schema explícito y obligatorio (.proto). Si necesitas contratos estrictos, gRPC; si necesitas flexibilidad, REST. {src:blk_b00000000202}
::: {src:blk_bbccddee0001}

## Síntesis
Ambos protocolos comparten [similitud 1: HTTP como transporte subyacente (REST en HTTP/1.1 o HTTP/2, gRPC en HTTP/2 obligatorio)] y [similitud 2: cliente-servidor request/response con autenticación y autorización]. La diferencia clave es que REST usa JSON texto con schema opcional mientras gRPC usa Protobuf binario con schema obligatorio, ofreciendo streaming bidireccional y tipado fuerte a costa de verbosidad para humanos. {src:blk_b00000000203}

## Criterios
Los criterios cubren protocolo, schema, serialización, streaming, codegen y tipado; cada uno se aplica a ambos protocolos de forma paralela. {src:blk_b00000000204}

- **Protocolo:** REST usa HTTP/1.1 o HTTP/2; gRPC requiere HTTP/2. {src:blk_b00000000205}
- **Schema:** REST no requiere schema; gRPC requiere `.proto` con tipos estrictos. {src:blk_b00000000206}
- **Serialización:** JSON texto vs Protobuf binario (más compacto). {src:blk_b00000000207}
- **Streaming:** REST no nativo (long polling, SSE, WebSocket); gRPC nativo bidireccional. {src:blk_b00000000208}
- **Codegen + tipos:** OpenAPI generators vs codegen nativo; dinámicos (JSON) vs estáticos (Protobuf). {src:blk_b00000000209}

## Matriz de decisión por escenario
| Escenario | Mejor opción | Justificación |
|---|---|---|
| Browser ↔ server API | REST | Compatible con fetch/XMLHttpRequest |
| Microservicios internal | gRPC | Schema estricto, streaming, performance |
| Mobile app ↔ backend | gRPC | Payload binario, tipado fuerte |
| Public API para terceros | REST | Familiaridad, debugging con curl |
| Streaming bidireccional | gRPC | Streaming nativo |
| CRUD simple | REST | Simplicidad, menos boilerplate |

## Trade-offs
| Trade-off | REST | gRPC |
|---|---|---|
| Schema implícito vs explícito | opcional OpenAPI | obligatorio .proto |
| JSON vs Protobuf | texto (legible) | binario (compacto) |
| Streaming | no nativo | nativo bidireccional |
| Tipado | dinámico | estático |
| Codegen | opcional (OpenAPI) | nativo |
| Tooling de debug | curl, browser, Postman | grpcurl, grpcox |

## Casos de uso

### Cuándo elegir REST {src:blk_aabbccddee02}
:::tip {src:blk_fedcba000200}
- APIs públicas accesibles desde browsers.
- APIs que terceras partes consumirán sin generar clientes tipados.
- Sistemas CRUD simples donde JSON es legible para humanos.
- Debugging en producción con curl.
::: {src:blk_bbccddee0003}

### Cuándo elegir gRPC {src:blk_aabbccddee04}
:::tip {src:blk_fedcba000300}
- Microservicios internal con contratos estrictos entre servicios.
- Streaming bidireccional (e.g., chat, real-time updates).
- Mobile apps donde el payload binario importa.
- Sistemas con requisitos de performance y baja latencia.
::: {src:blk_bbccddee0005}

## Veredicto
Para **APIs públicas** accesibles desde browsers o consumidas por terceros sin código generado, REST es la elección pragmática. Para **microservicios internal** con contratos estrictos y requisitos de performance, gRPC es superior. En la práctica, los sistemas modernos usan **ambos**: gRPC para la comunicación entre servicios internos y REST como gateway público. La diferencia clave es el contrato: schema implícito vs explícito. {src:blk_b00000000210}

:::derived {src:blk_fedcba000400}
El benchmark típico muestra gRPC ~7-10x más rápido que REST+JSON para payloads pequeños (< 1 KB), pero la diferencia se diluye para payloads grandes o con compresión gzip. Esta comparación depende mucho del caso de uso y no es universal. {src:blk_fedcba000500}
::: {src:blk_bbccddee0006}

## Backlinks
La comparativa se complementa con el detalle de curl y los status codes REST; los enlaces muestran los 2 ángulos. {src:blk_b00000000250}

- [[note:api-reference-curl-options]] — opciones de cURL (REST).
- [[note:http-status-codes]] — status codes REST.
