---
title: "RFC 7231 §4 — HTTP/1.1 Request Methods (digest)"
note-type: chapter-digest
status: draft
summary: "Digest del RFC 7231 §4 sobre métodos HTTP/1.1: GET, HEAD, POST, PUT, DELETE, CONNECT, OPTIONS, TRACE; safety e idempotencia."
tags: [type/chapter-digest, domain/http, source/rfc]
source: "RFC 7231 — HTTP/1.1 Semantics and Content"
source-type: rfc
source-anchor: "request-methods"
retrieved: 2026-09-27
vendor: IETF
product: RFC 7231
product-version: "7231"
coverage: summary
related: "[[note:rfc-7231-section-3-resources-digest]], [[note:rfc-7231-section-5-responses-digest]]"
---

# RFC 7231 §4 — HTTP/1.1 Request Methods (digest)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Digest del RFC 7231 §4 sobre métodos HTTP/1.1: GET, HEAD, POST, PUT, DELETE, CONNECT, OPTIONS, TRACE; safety e idempotencia. |
| **Procedencia** | RFC 7231 — HTTP/1.1 Semantics and Content (rfc) §request-methods · recuperado 2026-09-27 |
| **Versión** | RFC 7231 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 3 min |

## TL;DR
HTTP/1.1 define 8 métodos estándar: GET (safe + idempotent), HEAD (safe + idempotent), POST (no safe + no idempotent), PUT (no safe + idempotent), DELETE (no safe + idempotent), CONNECT, OPTIONS, TRACE. Las propiedades **safety** e **idempotencia** determinan cómo los intermediarios (proxies, caches) pueden manejar las requests. {src:blk_c00000000200}

{layer:l2}

## Resumen ejecutivo
La sección §4 del RFC 7231 define los métodos de request HTTP/1.1. Cada método tiene 2 propiedades clave: **safe** (no intended to cause side effects; puede ser cacheado/prefetched por el cliente) y **idempotent** (múltiples requests idénticas producen el mismo efecto que una sola; el cliente puede reintentar en fallo). GET y HEAD son safe e idempotent; POST no es safe ni idempotent; PUT y DELETE son idempotent pero no safe. Las propiedades safe/idempotent permiten a intermediarios y clientes reintentar requests en errores sin causar duplicación. {src:blk_c00000000201}

## Continuidad

### Hacia atrás {src:blk_aabbccddee01}
El [[note:rfc-7231-section-3-resources-digest]] introdujo el modelo de recursos HTTP y la sintaxis de URIs. Aquí profundizamos en los métodos que operan sobre esos recursos. {src:blk_eeeeff000001}

### Hacia adelante {src:blk_aabbccddee02}
El [[note:rfc-7231-section-5-responses-digest]] cubre los status codes (1xx, 2xx, 3xx, 4xx, 5xx) que los métodos retornan. {src:blk_c00000000202}

## Puntos clave
Los 8 métodos HTTP se resumen en 5 propiedades clave que el lector debe recordar. {src:blk_c00000000260}

- GET y HEAD son safe: no intended to cause side effects.
- PUT, DELETE, GET, HEAD son idempotent: múltiples requests idénticas producen el mismo efecto.
- POST es ni safe ni idempotent: cada call puede producir side effects adicionales.
- CONNECT se usa para tunneling (e.g., HTTPS a través de proxy HTTP).
- OPTIONS permite al cliente descubrir métodos soportados por el server.

## Conceptos nuevos

| Concepto | Nota propia | Definición breve |
|---|---|---|
| `safe method` | [[note:http-safe-method]] | Método que no causa side effects en el server |
| `idempotent method` | [[note:http-idempotent-method]] | Método donde N requests = 1 request en efecto |
| `OPTIONS method` | [[note:http-options]] | Método para descubrir capacidades del server |
| `CONNECT method` | [[note:http-connect]] | Establece tunnel al server (e.g., proxy HTTPS) |

## Citas textuales

> "Request methods are considered 'safe' if their intended semantics are to be read-only; the client does not request, and the server is not expected to perform, any state-changing operation." {src:blk_eeeeff000002}
> — *RFC 7231 §4.2.1 Safe Methods*, retrieved 2026-09-27 {src:blk_c00000000220}

> "A request method is considered 'idempotent' if the intended effect on the server, when performed once or multiple times with the same request, is the same." {src:blk_eeeeff000003}
> — *RFC 7231 §4.2.2 Idempotent Methods*, retrieved 2026-09-27 {src:blk_c00000000221}

## Énfasis del autor

:::note
El RFC enfatiza que "safe" ≠ "idempotent": safe es sobre no side effects; idempotent es sobre N requests = 1. GET es ambas; PUT es idempotent pero no safe. {src:blk_c00000000230}
::: {src:blk_bbccddee0003}

## Detalles

### Mecanismos {src:blk_aabbccddee04}
Las propiedades safe e idempotent controlan cómo los intermediarios y clientes manejan las requests. {src:blk_c00000000270}

- El cliente determina la safety de un método, pero el server puede no cooperar (un GET que borra datos).
- Los intermediarios (proxies, caches) pueden reenviar requests safe sin confirmación del usuario.
- Las requests idempotent pueden reintentarse automáticamente en errores de red.

### Código {src:blk_aabbccddee05}
```http
GET /resource HTTP/1.1 {src:blk_eeeeff000004}
Host: example.com

POST /resource HTTP/1.1 {src:blk_eeeeff000005}
Host: example.com
Content-Type: application/json {src:blk_eeeeff000006}

{"name": "value"}

PUT /resource/123 HTTP/1.1 {src:blk_eeeeff000007}
Host: example.com
Content-Type: application/json {src:blk_eeeeff000008}

{"name": "new-value"} {src:blk_eeeeff000009}

DELETE /resource/123 HTTP/1.1 {src:blk_eeeeff00000a}
Host: example.com
# {src:blk_ccddeebf0001}
```

## Conexiones

:::derived
La sección §4 se conecta con [[note:http-status-codes]] (§5 cubre los status codes retornados) y con [[note:http-caching]] (§6 cubre el comportamiento de caches según safe/idempotent). {src:blk_eeeeff00000b}
::: {src:blk_bbccddee0006}

## Erratas

:::warning
**RFC 7231 Errata 4669:** la frase "Cacheable methods" en §4.2.1 fue clarificada para indicar que GET y HEAD son cacheable por default, pero POST también puede serlo bajo directivas explícitas del response. {src:blk_c00000000240}
::: {src:blk_bbccddee0007}

## Ejercicios

:::example
**Ejercicio:** Diseña una API REST para una entidad `Article` con métodos `list`, `get`, `create`, `update`, `delete`. Mapea cada uno a un método HTTP y justifica la elección considerando safety e idempotencia.

**Pista:** `list` y `get` deben ser safe; `create` debe ser POST; `update` y `delete` son PUT/DELETE. {src:blk_c00000000250}
::: {src:blk_bbccddee0008}

## Backlinks
El digest se conecta con la sección 3 (resources) y la sección 5 (responses) del mismo RFC; los enlaces muestran ambos extremos. {src:blk_c00000000280}

- [[note:rfc-7231-section-3-resources-digest]] — sección anterior.
- [[note:rfc-7231-section-5-responses-digest]] — sección siguiente.

## Ver también
Los status codes y el comportamiento de caches complementan los métodos HTTP; los enlaces muestran ambos aspectos. {src:blk_c00000000281}

- [[note:http-status-codes]] — status codes asociados a cada método.
- [[note:http-caching]] — comportamiento de caches por método.
