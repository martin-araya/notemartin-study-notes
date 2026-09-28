---
title: "cURL — sintaxis del comando CLI"
note-type: syntax
status: draft
summary: "Sintaxis del comando cURL con todas las opciones (cortas y largas), incluyendo autenticación, headers, métodos HTTP, datos y debugging."
tags: [type/syntax, domain/cli, product/curl]
source: "curl 8 — man page"
source-type: docs
source-anchor: "curl.1"
retrieved: 2026-09-27
vendor: The curl project
product: curl
product-version: "8"
related: "[[note:api-reference-curl-options]], [[note:docker-permission-errors]]"
---

# cURL — sintaxis del comando CLI

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Sintaxis del comando cURL con todas las opciones (cortas y largas), incluyendo autenticación, headers, métodos HTTP, datos y debugging. |
| **Procedencia** | curl 8 — man page (docs) §curl.1 · recuperado 2026-09-27 |
| **Versión** | curl 8 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 5 min |

## TL;DR
cURL usa convención CLI con opciones cortas (`-X`, `-H`, `-d`) y largas (`--request`, `--header`, `--data`). ≥ 200 opciones; las raras incluyen `--compressed`, `--fail-early`, `--http3`, `--rate`. {src:blk_f00000000040}

{layer:l2}

## Convención de metasímbolos
| Símbolo | Significado |
|---|---|
| `[...]` | opcional |
| `(a\|b\|c)` | alternativa |
| `...` | repetición |
| `-X` | opción corta (un guion + letra) |
| `--xxx` | opción larga (dos guiones + palabra) |

## Sintaxis
```bnf
curl [options] URL [URL ...] {src:blk_eeeeff000001}

options ::=
    [-X | --request METHOD]
    [-H | --header "Name: Value"] ...
    [-d | --data DATA | --data-binary DATA | --data-urlencode DATA] ...
    [-u | --user user:password]
    [-b | --cookie "name=value"] ...
    [-c | --cookie-jar file]
    [-A | --user-agent string]
    [-e | --referer URL]
    [-L | --location]
    [-k | --insecure]
    [-f | --fail]
    [-s | --silent | -S | --show-error]
    [-v | --verbose]
    [-o | --output file]
    [-O | --remote-name]
    [-T | --upload-file file]
    [-G | --get]
    [-I | --head]
    [-X CONNECT]
    [--compressed]
    [--http2 | --http2-prior-knowledge]
    [--http3]
    [--ssl | --ssl-revoke-best-effort]
    [--cacert file | --capath dir | --insecure]
    [--cert file[:password]]
    [--key file]
    [--user-agent string]
    [--cookie "name=value"]
    [--resolve host:port:address] ...
    [--max-time seconds]
    [--connect-timeout seconds]
    [--retry num]
    [--rate N/M]
    [--fail-early]
    [-# | --progress-bar]
# {src:blk_ccddeebf0001}
```

## Cláusula por cláusula

### `URL [URL ...]` {src:blk_aabbccddee01}
Una o más URLs a procesar. Si hay varias, cURL las intenta en paralelo. {src:blk_f00000000041}

### `-X | --request METHOD` {src:blk_aabbccddee02}
Sobrescribe el método HTTP (default: GET). Valores: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS, CONNECT. {src:blk_f00000000042}

### `-H | --header "Name: Value"` {src:blk_aabbccddee03}
Añade o sobrescribe un header HTTP. Se puede usar múltiples veces. {src:blk_f00000000043}

### `-d | --data DATA` {src:blk_aabbccddee04}
Body para POST/PUT. Si empieza con `@`, lee de archivo. {src:blk_f00000000044}

### `--data-binary DATA` {src:blk_aabbccddee05}
Como `-d` pero sin procesar `@`. {src:blk_f00000000045}

### `--data-urlencode DATA` {src:blk_aabbccddee06}
URL-encodea el dato. `data` puede ser `name=value` o `name@file`. {src:blk_f00000000046}

### `-u | --user user:password` {src:blk_aabbccddee07}
Autenticación básica. Sin password, cURL la pide por stdin. {src:blk_f00000000047}

### `-L | --location` {src:blk_aabbccddee08}
Sigue redirects (3xx). {src:blk_f00000000048}

### `-k | --insecure` {src:blk_aabbccddee09}
Desactiva verificación de certificados TLS. {src:blk_f00000000049}

### `-f | --fail` {src:blk_aabbccddee0a}
Falla con exit code 22 en errores HTTP (4xx, 5xx). Sin `-f`, cURL exit 0 incluso con errores HTTP. {src:blk_f00000000050}

### `-s | --silent` {src:blk_aabbccddee0b}
Silencia el progress meter y mensajes de error. Combinar con `-S | --show-error` para mostrar errores pero no progress. {src:blk_f00000000051}

### `-v | --verbose` {src:blk_aabbccddee0c}
Muestra handshake TLS, headers de request/response, y timing. {src:blk_f00000000052}

### `-o | --output file` {src:blk_aabbccddee0d}
Escribe el body a `file` en vez de stdout. {src:blk_f00000000053}

### `-O | --remote-name` {src:blk_aabbccddee0e}
Usa el nombre del archivo del servidor (de la URL). {src:blk_f00000000054}

### `-T | --upload-file file` {src:blk_aabbccddee0f}
Sube el archivo al URL (método PUT). {src:blk_f00000000055}

### `-G | --get` {src:blk_aabbccddee10}
Convierte `-d` a query string con método GET. {src:blk_f00000000056}

### `-I | --head` {src:blk_aabbccddee11}
Solo headers (método HEAD). {src:blk_f00000000057}

### `--compressed` {src:blk_aabbccddee12}
Pide gzip/deflate/br y descomprime automáticamente. {src:blk_f00000000058}

### `--http2` {src:blk_aabbccddee13}
Usa HTTP/2 con negotiation ALPN. {src:blk_f00000000059}

### `--http3` {src:blk_aabbccddee14}
Usa HTTP/3 sobre QUIC (opcional raro; requiere curl compilado con HTTP/3). {src:blk_f00000000060}

### `--resolve host:port:address` {src:blk_aabbccddee15}
Sobrescribe la resolución DNS para `host:port` con `address`. Útil para testing contra `localhost`. {src:blk_f00000000061}

### `--max-time seconds` {src:blk_aabbccddee16}
Timeout total (incluye conexión + transferencia). {src:blk_f00000000062}

### `--retry num` {src:blk_aabbccddee17}
Reintenta en errores transientes (timeouts, 5xx). No reintenta en 4xx. {src:blk_f00000000063}

### `--rate N/M` {src:blk_aabbccddee18}
Limita a N requests cada M segundos (opcional raro, requiere `--retry` desactivado). {src:blk_f00000000064}

### `--fail-early` {src:blk_aabbccddee19}
Aborta en el primer error de parseo de config. Sin esto, errores posteriores sobrescriben los anteriores. {src:blk_f00000000065}

## Diagramas de sintaxis
:::diagram
```mermaid
flowchart TD
    A[curl] --> B[options] {src:blk_eeeeff000002}
    A --> C[URL 1]
    A --> D[URL 2 ...] {src:blk_eeeeff000003}
    B --> E[method: -X GET/POST/...] {src:blk_eeeeff000004}
    B --> F[headers: -H x N] {src:blk_eeeeff000005}
    B --> G[body: -d / --data-urlencode] {src:blk_eeeeff000006}
    B --> H[auth: -u user:pass] {src:blk_eeeeff000007}
    B --> I[TLS: -k / --cacert] {src:blk_eeeeff000008}
    B --> J[output: -o / -O] {src:blk_eeeeff000009}
    B --> K[behavior: -L / -f / -v] {src:blk_eeeeff00000a}
# {src:blk_ccddeebf0002}
```
::: {src:blk_bbccddee001a}

## Ejemplos graduales

:::example
**Ejemplo 1 — mínimo:** GET simple.

```bash
curl https://api.example.com/users {src:blk_eeeeff00000b}
# {src:blk_ccddeebf0003}
```
::: {src:blk_bbccddee001b}

:::example
**Ejemplo 2 — + header + auth + POST:** Con body JSON.

```bash
curl -X POST https://api.example.com/users \ {src:blk_eeeeff00000c}
  -H "Content-Type: application/json" \
  -u admin:secret \
  -d '{"name": "Alice", "email": "[email protected]"}'
# {src:blk_ccddeebf0004}
```
::: {src:blk_bbccddee001c}

:::example
**Ejemplo 3 — + verbose + save + insecure:** Diagnóstico completo.

```bash
curl -X POST https://internal.example.com/api \ {src:blk_eeeeff00000d}
  -H "Content-Type: application/json" \
  -u admin:secret \
  -d @payload.json \
  -o response.json \
  --cacert /etc/ssl/certs/ca.pem \
  --resolve internal.example.com:443:127.0.0.1 \
  -v
# {src:blk_ccddeebf0005}
```
::: {src:blk_bbccddee001d}

## Contraejemplos

:::warning
**Input:** `curl -X POST https://api.example.com/users` (sin `-d` ni body).
**Error literal:** `curl: (3) HTTP/2 stream 1 was not closed cleanly: PROTOCOL_ERROR (err 1)`
**Causa:** muchos servidores (especialmente con HTTP/2) requieren Content-Length o Transfer-Encoding; sin `-d`, curl no envía body y el servidor rechaza.
**Solución:** añadir `-d ''` para enviar body vacío, o `-d @file` con datos.
::: {src:blk_bbccddee001e}

:::warning
**Input:** `curl -L https://example.com/redirect` con `-k` apuntando a servidor que redirige a HTTPS con cert inválido.
**Error literal:** `curl: (60) SSL certificate problem: self signed certificate`
**Causa:** `-k` desactiva verificación TLS, pero los redirects pueden apuntar a otro servidor con cert inválido.
**Solución:** usar `--cacert file.pem` específico o corregir el cert del servidor destino.
::: {src:blk_bbccddee001f}

## Backlinks
La sintaxis de cURL se complementa con el detalle de cada opción y los confundibles con errores de socket de Docker; los enlaces muestran ambos aspectos. {src:blk_f00000000072}

- [[note:api-reference-curl-options]] — el detalle de cada opción con ejemplos avanzados.
- [[note:docker-permission-errors]] — confundibles: errores de socket en Docker, no en curl.
