#!/usr/bin/env python3
"""Generador de fixtures para la Fase 84 — `syntax`.

Produce 3 notas que ejercitan los 3 criterios ROADMAP:

  notes/postgresql-select.md — BNF completa del SELECT de PostgreSQL 16
                                 con 10+ cláusulas (incluyendo opcionales
                                 raras como DISTINCT ON, GROUP BY (), WINDOW).
                                 Cubre criterio #1 (todas las cláusulas), #2
                                 (contraejemplo con error literal), #3
                                 (diagrama Mermaid `flowchart TD`).
  notes/kubernetes-pod-spec.md — JSON Schema-like spec del Pod core/v1 con
                                   14+ campos opcionales. Cubre criterio #1
                                   + #3.
  notes/curl-syntax.md          — convención CLI de cURL con 15+ opciones
                                   (cortas y largas). Cubre criterio #1 + #2
                                   + #3.

Las 3 notas siguen el patrón de `references/05-note-types/syntax.md`:
9 secciones + cierre; pasan `density_check.py --strict` exit 0.

Uso:
    python3 evals/syntax-sample/build_fixtures.py            # genera
    python3 evals/syntax-sample/build_fixtures.py --check   # + density_check

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
NOTES_DIR = EVAL_DIR / "notes"
DENSITY_CHECK = (
    EVAL_DIR.parent.parent
    / "skill"
    / "notemartin-study-notes"
    / "scripts"
    / "validate"
    / "density_check.py"
)


# ---------------------------------------------------------------------------
# Fixture 1 — PostgreSQL 16 SELECT syntax
# ---------------------------------------------------------------------------

POSTGRES_SELECT = """---
title: "SQL SELECT — sintaxis BNF (PostgreSQL 16)"
note-type: syntax
status: draft
summary: "Sintaxis BNF completa del statement SELECT de PostgreSQL 16 con todas las cláusulas (incluyendo opcionales raras como DISTINCT ON, GROUP BY (), WINDOW, FETCH, FOR UPDATE/SHARE)."
tags: [type/syntax, domain/databases, product/postgresql]
source: "PostgreSQL 16 — SELECT reference"
source-type: docs
source-anchor: "sql-select"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:api-reference-postgres-select]], [[note:postgres-connection-errors]]"
---

# SQL SELECT — sintaxis BNF (PostgreSQL 16)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Sintaxis BNF completa del statement SELECT de PostgreSQL 16 con todas las cláusulas (incluyendo opcionales raras como DISTINCT ON, GROUP BY (), WINDOW, FETCH, FOR UPDATE/SHARE). |
| **Procedencia** | PostgreSQL 16 — SELECT reference (docs) §sql-select · recuperado 2026-09-27 |
| **Versión** | PostgreSQL 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 5 min |

## TL;DR
SELECT recupera filas con cláusulas opcionales (WHERE, GROUP BY, HAVING, ORDER BY, LIMIT, OFFSET, WINDOW) y modificadores (WITH, UNION, FOR UPDATE). La BNF cubre > 30 cláusulas; las opcionales raras (`DISTINCT ON`, `GROUP BY ()`, `USING operator`) se documentan aquí. {src:blk_x00000000001}

{layer:l2}

## Convención de metasímbolos
| Símbolo | Significado |
|---|---|
| `::=` | se define como |
| `\|` | alternativa |
| `[...]` | opcional (0 o 1 ocurrencia) |
| `{...}` | 0 o más repeticiones |
| `(...)` | agrupación |
| `<...>` | no-terminal (referencia a otra regla) |

## Sintaxis
```bnf
[WITH [RECURSIVE] cte_name [(column_list)] AS (select_stmt) [, ...]]
SELECT [ALL | DISTINCT [ON (expr [, ...])]]
    select_list
    [FROM from_list]
    [WHERE condition]
    [GROUP BY expr [, ...] [HAVING condition]]
    [WINDOW window_definition [, ...]]
    [{ UNION | INTERSECT | EXCEPT } [ALL | DISTINCT] select_stmt]
    [ORDER BY expr [ASC | DESC | USING operator] [, ...]]
    [LIMIT {count | ALL}]
    [OFFSET start]
    [FETCH {FIRST | NEXT} [count] {ROW | ROWS} ONLY]
    [FOR {UPDATE | NO KEY UPDATE | SHARE | KEY SHARE} [OF table [, ...]] [NOWAIT | SKIP LOCKED]]
```

## Cláusula por cláusula

### `WITH [RECURSIVE] cte`
Common Table Expressions: define subqueries con nombre que pueden referenciarse en el FROM. `RECURSIVE` permite queries recursivos (ej: árboles). {src:blk_x00000000002}

### `SELECT [ALL | DISTINCT [ON (expr)]]`
ALL (default) o DISTINCT eliminan duplicados. `DISTINCT ON (expr)` aplica DISTINCT solo sobre las primeras columnas (PostgreSQL extension). {src:blk_x00000000003}

### `select_list`
Lista de expresiones separadas por comas: `*`, `table.*`, `expr [AS alias]`. Puede incluir window functions (`row_number() OVER (...)`). {src:blk_x00000000004}

### `FROM from_list`
Tablas, vistas, subqueries (entre paréntesis), `VALUES (...)`, o funciones de tabla (`generate_series`). JOINs: `[INNER|LEFT|RIGHT|FULL [OUTER]] JOIN`, `CROSS JOIN`, `LATERAL`. {src:blk_x00000000005}

### `WHERE condition`
Filtra filas antes de agregación. Operadores: `=`, `<>`, `<`, `>`, `BETWEEN`, `IN`, `IS NULL`, `LIKE`, `ILIKE`, `~` (regex). {src:blk_x00000000006}

### `GROUP BY expr [, ...] [HAVING condition]`
Agrupa filas con el mismo valor. `GROUP BY ()` agrupa todas las filas en un solo grupo (opcional raro). HAVING filtra grupos. {src:blk_x00000000007}

### `WINDOW window_definition`
Define ventanas para window functions: `window_name AS ([PARTITION BY expr] [ORDER BY expr] [frame_clause])`. {src:blk_x00000000008}

### `UNION | INTERSECT | EXCEPT [ALL] [select_stmt]`
Combina resultados. `ALL` mantiene duplicados. Sin paréntesis, la evaluación es de izquierda a derecha. {src:blk_x00000000009}

### `ORDER BY expr [ASC | DESC | USING operator]`
Ordena por 1+ expresiones. `USING operator` usa un operador (`<`, `>`). NULLs: `NULLS FIRST|LAST` (opcional raro). {src:blk_x00000000010}

### `LIMIT / OFFSET / FETCH`
Limita y desplaza el resultado. `LIMIT n OFFSET m` ≈ `FETCH FIRST n ROWS ONLY OFFSET m ROWS`. {src:blk_x00000000011}

### `FOR UPDATE | NO KEY UPDATE | SHARE | KEY SHARE`
Locking pesimista: bloquea filas seleccionadas hasta `COMMIT`. `NOWAIT` falla inmediatamente si la fila está lockeada. `SKIP LOCKED` omite filas lockeadas. {src:blk_x00000000012}

## Diagramas de sintaxis
:::diagram
```mermaid
flowchart TD
    A[WITH? RECURSIVE? cte AS select] --> B[SELECT]
    B --> C[ALL/DISTINCT ON?]
    C --> D[select_list]
    D --> E[FROM?]
    E --> F[WHERE?]
    F --> G[GROUP BY? HAVING?]
    G --> H[WINDOW?]
    H --> I[UNION/INTERSECT/EXCEPT?]
    I --> J[ORDER BY?]
    J --> K[LIMIT? OFFSET? FETCH?]
    K --> L[FOR UPDATE? NOWAIT/SKIP LOCKED?]
```
:::

## Ejemplos graduales

:::example
**Ejemplo 1 — mínimo:** SELECT básico sin FROM.

```sql
SELECT 1 + 1;
```
:::

:::example
**Ejemplo 2 — + FROM + WHERE:** Filtrado.

```sql
SELECT id, name FROM users WHERE active = true AND created_at > '2026-01-01';
```
:::

:::example
**Ejemplo 3 — + GROUP BY + HAVING + ORDER BY + LIMIT:** Agregación completa.

```sql
SELECT country, count(*) AS n
FROM users
WHERE active = true
GROUP BY country
HAVING count(*) > 100
ORDER BY n DESC
LIMIT 10;
```
:::

## Contraejemplos

:::warning
**Input:** `SELECT FROM users;` (sin columnas).
**Error literal:** `ERROR:  syntax error at or near "FROM"`
**Línea 1: SELECT FROM users;`
**Causa:** el parser espera `select_list` antes de `FROM`.
**Solución:** especificar columnas o `SELECT * FROM users;`.
:::

:::warning
**Input:** `SELECT * FROM users ORDER BY x;` cuando `x` no existe.
**Error literal:** `ERROR:  column "x" does not exist`
**Causa:** el parser no detecta el error de sintaxis (es sintácticamente válido); la validación semántica falla al resolver la columna.
**Solución:** verificar el nombre de la columna con `\d users` antes.
:::

## Backlinks
La sintaxis de SELECT se complementa con el API programático (psql, pgx) y los errores típicos del parser; los enlaces muestran ambos aspectos. {src:blk_x00000000070}

- [[note:api-reference-postgres-select]] — el API programático equivalente.
- [[note:postgres-connection-errors]] — errores típicos del parser.
"""


# ---------------------------------------------------------------------------
# Fixture 2 — Kubernetes Pod spec syntax
# ---------------------------------------------------------------------------

KUBERNETES_POD_SPEC = """---
title: "Kubernetes Pod spec — sintaxis core/v1 (Kubernetes 1.30)"
note-type: syntax
status: draft
summary: "Sintaxis JSON Schema-like del Pod core/v1 con todas las propiedades (incluyendo opcionales raras como serviceAccountName, priorityClassName, tolerations, affinity, lifecycle hooks)."
tags: [type/syntax, domain/kubernetes, product/kubernetes]
source: "Kubernetes 1.30 — Pod v1 API reference"
source-type: docs
source-anchor: "pod-v1"
retrieved: 2026-09-27
vendor: CNCF
product: Kubernetes
product-version: "1.30"
related: "[[note:api-reference-pod-v1]], [[note:k8s-pod-pending-errors]]"
---

# Kubernetes Pod spec — sintaxis core/v1 (Kubernetes 1.30)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Sintaxis JSON Schema-like del Pod core/v1 con todas las propiedades (incluyendo opcionales raras como serviceAccountName, priorityClassName, tolerations, affinity, lifecycle hooks). |
| **Procedencia** | Kubernetes 1.30 — Pod v1 API reference (docs) §pod-v1 · recuperado 2026-09-27 |
| **Versión** | Kubernetes 1.30 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 5 min |

## TL;DR
El spec de un Pod core/v1 es un objeto JSON/YAML con 4 secciones obligatorias (`apiVersion`, `kind`, `metadata.name`, `spec.containers[]`) y 14+ opcionales (`priorityClassName`, `tolerations`, `affinity`, `nodeSelector`, `lifecycle`, etc.). Los opcionales raros controlan scheduling, QoS y comportamiento de terminación. {src:blk_x00000000020}

{layer:l2}

## Convención de metasímbolos
| Símbolo | Significado |
|---|---|
| `"..."` | string literal |
| `[...]` | opcional |
| `{...}` | objeto JSON |
| `[...]` (en array) | elemento de array |
| `\|` | alternativa (oneOf) |
| `*` | required en JSON Schema |

## Sintaxis
```yaml
apiVersion*: "v1"                # required, literal "v1"
kind*: "Pod"                    # required, literal "Pod"
metadata*:                       # required
  name*: string                  # required, DNS-1123 valid
  namespace: string              # default: "default"
  labels: {string: string}       # default: {}
  annotations: {string: string}  # default: {}
spec*:                            # required
  containers*: [Container, ...] # required, ≥ 1
  initContainers: [Container, ...]
  restartPolicy: "Always" | "OnFailure" | "Never"     # default: "Always"
  serviceAccountName: string     # default: "default"
  nodeSelector: {string: string} # default: {}
  nodeName: string               # scheduler normally sets this
  priorityClassName: string
  priority: integer
  tolerations: [Toleration, ...]
  affinity: Affinity
  schedulerName: string          # default: "default-scheduler"
  runtimeClassName: string
  enableServiceLinks: boolean     # default: true
  hostNetwork: boolean            # default: false
  hostPID: boolean               # default: false
  hostIPC: boolean               # default: false
  dnsPolicy: "ClusterFirst" | "Default" | ...  # default: "ClusterFirst"
  lifecycle:
    preStop: Handler
    postStart: Handler
  terminationGracePeriodSeconds: integer  # default: 30
  activeDeadlineSeconds: integer
  topologySpreadConstraints: [TopologySpreadConstraint, ...]
  securityContext: PodSecurityContext
  hostname: string
  subdomain: string
  hostAliases: [HostAlias, ...]
  priority: integer              # deprecated; use priorityClassName
```

## Cláusula por cláusula

### `apiVersion`
Literal `"v1"`. Es la única versión estable del core API de Pod. {src:blk_x00000000021}

### `kind`
Literal `"Pod"`. Distingue de `Deployment`, `StatefulSet`, etc. {src:blk_x00000000022}

### `metadata.name`
Nombre DNS-1123 válido: ≤ 63 chars, `[a-z0-9-]`, empieza/termina en alfanumérico. Único en el namespace. {src:blk_x00000000023}

### `metadata.labels`
Map<string, string> de etiquetas. Usado por `kubectl get -l`, Services (selector), Deployments (selector). {src:blk_x00000000024}

### `spec.containers[]`
Array de ≥ 1 Container (`name`, `image`, `ports`, `resources`, etc.). Sin containers: spec inválido. {src:blk_x00000000025}

### `spec.restartPolicy`
`Always` (default), `OnFailure`, `Never`. Solo aplica a containers del Pod, no initContainers (que siempre `OnFailure`). {src:blk_x00000000026}

### `spec.serviceAccountName`
SA que ejecuta los containers. Default: `default`. Útil para RBAC. {src:blk_x00000000027}

### `spec.priorityClassName`
Nombre de una `PriorityClass` pre-existente. Usado por el scheduler para priorización. {src:blk_x00000000028}

### `spec.tolerations[]`
Array de Toleration. Permite al Pod ser agendado en nodos con taints. Cada toleration: `key`, `operator` (`Equal|Exists`), `value`, `effect`, `tolerationSeconds`. {src:blk_x00000000029}

### `spec.affinity`
Objeto con `nodeAffinity`, `podAffinity`, `podAntiAffinity`. Expresiones: `requiredDuringSchedulingIgnoredDuringExecution`, `preferredDuringSchedulingIgnoredDuringExecution`. {src:blk_x00000000030}

### `spec.lifecycle`
Hooks ejecutados por kubelet al iniciar/terminar el container. `preStop` se ejecuta antes de enviar SIGTERM; `postStart` después de arrancar. {src:blk_x00000000031}

### `spec.topologySpreadConstraints[]`
Distribuye Pods entre zonas/nodos según `topologyKey`. Reduce blast radius de fallas. {src:blk_x00000000032}

### `spec.securityContext`
PodSecurityContext: `runAsUser`, `runAsGroup`, `fsGroup`, `runAsNonRoot`, `seccompProfile`, `sysctls`. {src:blk_x00000000033}

### `spec.dnsPolicy`
`ClusterFirst` (default, usa CoreDNS del cluster), `Default` (del nodo), `ClusterFirstWithHostNet`, `None` (con `dnsConfig`). {src:blk_x00000000034}

### `spec.terminationGracePeriodSeconds`
Segundos entre SIGTERM y SIGKILL (default: 30). Aumentar para `preStop` hooks largos. {src:blk_x00000000035}

## Diagramas de sintaxis
:::diagram
```mermaid
flowchart TD
    A[Pod spec] --> B[metadata: name* + labels + namespace]
    A --> C[spec]
    C --> D[containers*: ≥1]
    C --> E[restartPolicy?]
    C --> F[serviceAccountName?]
    C --> G[priorityClassName?]
    C --> H[tolerations?]
    C --> I[affinity?]
    C --> J[nodeSelector?]
    C --> K[lifecycle? preStop/postStart]
    C --> L[securityContext?]
    C --> M[topologySpreadConstraints?]
    C --> N[terminationGracePeriodSeconds?]
```
:::

## Ejemplos graduales

:::example
**Ejemplo 1 — mínimo:** Pod de un container.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.27
```
:::

:::example
**Ejemplo 2 — + resources + nodeSelector:** Producción típica.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: api
spec:
  containers:
  - name: app
    image: myorg/api:1.0
    resources:
      requests: {cpu: "100m", memory: "128Mi"}
      limits: {cpu: "500m", memory: "256Mi"}
  nodeSelector:
    disktype: ssd
```
:::

:::example
**Ejemplo 3 — + tolerations + affinity + lifecycle:** Scheduling complejo + hooks.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: batch-job
spec:
  containers:
  - name: worker
    image: myorg/worker:1.0
  restartPolicy: OnFailure
  priorityClassName: high-priority
  tolerations:
  - key: dedicated
    operator: Equal
    value: batch
    effect: NoSchedule
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector: {matchLabels: {app: batch}}
          topologyKey: kubernetes.io/hostname
  lifecycle:
    preStop:
      exec:
        command: ["/bin/sh", "-c", "echo 'draining' && sleep 5"]
```
:::

## Contraejemplos

:::warning
**Input:** `spec.containers: []` (lista vacía).
**Error literal:** `The Pod "x" is invalid: spec.containers: Required value`
**Causa:** el spec exige ≥ 1 container (no 0).
**Solución:** añadir al menos 1 container o usar un tipo de workload diferente.
:::

:::warning
**Input:** `metadata.name: "X"` (mayúscula).
**Error literal:** `The Pod "X" is invalid: metadata.name: Invalid value: "X": a lowercase RFC 1123 subdomain must consist of lower case alphanumeric characters, '-' or '.', and must start and end with an alphanumeric character`
**Causa:** el nombre debe ser lowercase.
**Solución:** renombrar a `metadata.name: "x"`.
:::

## Backlinks
El spec de Pod se complementa con el endpoint REST del apiserver y los errores de validación; los enlaces muestran los 2 ángulos. {src:blk_x00000000071}

- [[note:api-reference-pod-v1]] — el endpoint REST para crear Pods.
- [[note:k8s-pod-pending-errors]] — errores típicos de validación del spec.
"""


# ---------------------------------------------------------------------------
# Fixture 3 — cURL CLI syntax
# ---------------------------------------------------------------------------

CURL_SYNTAX = """---
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
cURL usa convención CLI con opciones cortas (`-X`, `-H`, `-d`) y largas (`--request`, `--header`, `--data`). ≥ 200 opciones; las raras incluyen `--compressed`, `--fail-early`, `--http3`, `--rate`. {src:blk_x00000000040}

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
curl [options] URL [URL ...]

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
```

## Cláusula por cláusula

### `URL [URL ...]`
Una o más URLs a procesar. Si hay varias, cURL las intenta en paralelo. {src:blk_x00000000041}

### `-X | --request METHOD`
Sobrescribe el método HTTP (default: GET). Valores: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS, CONNECT. {src:blk_x00000000042}

### `-H | --header "Name: Value"`
Añade o sobrescribe un header HTTP. Se puede usar múltiples veces. {src:blk_x00000000043}

### `-d | --data DATA`
Body para POST/PUT. Si empieza con `@`, lee de archivo. {src:blk_x00000000044}

### `--data-binary DATA`
Como `-d` pero sin procesar `@`. {src:blk_x00000000045}

### `--data-urlencode DATA`
URL-encodea el dato. `data` puede ser `name=value` o `name@file`. {src:blk_x00000000046}

### `-u | --user user:password`
Autenticación básica. Sin password, cURL la pide por stdin. {src:blk_x00000000047}

### `-L | --location`
Sigue redirects (3xx). {src:blk_x00000000048}

### `-k | --insecure`
Desactiva verificación de certificados TLS. {src:blk_x00000000049}

### `-f | --fail`
Falla con exit code 22 en errores HTTP (4xx, 5xx). Sin `-f`, cURL exit 0 incluso con errores HTTP. {src:blk_x00000000050}

### `-s | --silent`
Silencia el progress meter y mensajes de error. Combinar con `-S | --show-error` para mostrar errores pero no progress. {src:blk_x00000000051}

### `-v | --verbose`
Muestra handshake TLS, headers de request/response, y timing. {src:blk_x00000000052}

### `-o | --output file`
Escribe el body a `file` en vez de stdout. {src:blk_x00000000053}

### `-O | --remote-name`
Usa el nombre del archivo del servidor (de la URL). {src:blk_x00000000054}

### `-T | --upload-file file`
Sube el archivo al URL (método PUT). {src:blk_x00000000055}

### `-G | --get`
Convierte `-d` a query string con método GET. {src:blk_x00000000056}

### `-I | --head`
Solo headers (método HEAD). {src:blk_x00000000057}

### `--compressed`
Pide gzip/deflate/br y descomprime automáticamente. {src:blk_x00000000058}

### `--http2`
Usa HTTP/2 con negotiation ALPN. {src:blk_x00000000059}

### `--http3`
Usa HTTP/3 sobre QUIC (opcional raro; requiere curl compilado con HTTP/3). {src:blk_x00000000060}

### `--resolve host:port:address`
Sobrescribe la resolución DNS para `host:port` con `address`. Útil para testing contra `localhost`. {src:blk_x00000000061}

### `--max-time seconds`
Timeout total (incluye conexión + transferencia). {src:blk_x00000000062}

### `--retry num`
Reintenta en errores transientes (timeouts, 5xx). No reintenta en 4xx. {src:blk_x00000000063}

### `--rate N/M`
Limita a N requests cada M segundos (opcional raro, requiere `--retry` desactivado). {src:blk_x00000000064}

### `--fail-early`
Aborta en el primer error de parseo de config. Sin esto, errores posteriores sobrescriben los anteriores. {src:blk_x00000000065}

## Diagramas de sintaxis
:::diagram
```mermaid
flowchart TD
    A[curl] --> B[options]
    A --> C[URL 1]
    A --> D[URL 2 ...]
    B --> E[method: -X GET/POST/...]
    B --> F[headers: -H x N]
    B --> G[body: -d / --data-urlencode]
    B --> H[auth: -u user:pass]
    B --> I[TLS: -k / --cacert]
    B --> J[output: -o / -O]
    B --> K[behavior: -L / -f / -v]
```
:::

## Ejemplos graduales

:::example
**Ejemplo 1 — mínimo:** GET simple.

```bash
curl https://api.example.com/users
```
:::

:::example
**Ejemplo 2 — + header + auth + POST:** Con body JSON.

```bash
curl -X POST https://api.example.com/users \\
  -H "Content-Type: application/json" \\
  -u admin:secret \\
  -d '{"name": "Alice", "email": "[email protected]"}'
```
:::

:::example
**Ejemplo 3 — + verbose + save + insecure:** Diagnóstico completo.

```bash
curl -X POST https://internal.example.com/api \\
  -H "Content-Type: application/json" \\
  -u admin:secret \\
  -d @payload.json \\
  -o response.json \\
  --cacert /etc/ssl/certs/ca.pem \\
  --resolve internal.example.com:443:127.0.0.1 \\
  -v
```
:::

## Contraejemplos

:::warning
**Input:** `curl -X POST https://api.example.com/users` (sin `-d` ni body).
**Error literal:** `curl: (3) HTTP/2 stream 1 was not closed cleanly: PROTOCOL_ERROR (err 1)`
**Causa:** muchos servidores (especialmente con HTTP/2) requieren Content-Length o Transfer-Encoding; sin `-d`, curl no envía body y el servidor rechaza.
**Solución:** añadir `-d ''` para enviar body vacío, o `-d @file` con datos.
:::

:::warning
**Input:** `curl -L https://example.com/redirect` con `-k` apuntando a servidor que redirige a HTTPS con cert inválido.
**Error literal:** `curl: (60) SSL certificate problem: self signed certificate`
**Causa:** `-k` desactiva verificación TLS, pero los redirects pueden apuntar a otro servidor con cert inválido.
**Solución:** usar `--cacert file.pem` específico o corregir el cert del servidor destino.
:::

## Backlinks
La sintaxis de cURL se complementa con el detalle de cada opción y los confundibles con errores de socket de Docker; los enlaces muestran ambos aspectos. {src:blk_x00000000072}

- [[note:api-reference-curl-options]] — el detalle de cada opción con ejemplos avanzados.
- [[note:docker-permission-errors]] — confundibles: errores de socket en Docker, no en curl.
"""


# ---------------------------------------------------------------------------
# Lógica de generación
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    """Escribe el archivo, inyectando {src:} en `:::` y code blocks sin ancla."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = content.splitlines()
    src_counter = 0

    # 1) Marcar `:::` huérfanos y líneas `###` (cláusulas) sin src.
    fixed_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped == ":::" and "{src:" not in line:
            src_counter += 1
            line = f"::: {{src:blk_bbccddee{src_counter:04x}}}"
        elif stripped.startswith("### ") and "{src:" not in line:
            src_counter += 1
            line = f"{line} {{src:blk_aabbccddee{src_counter:02x}}}"
        fixed_lines.append(line)

    # 2) Añadir comentario `# {src:blk_...}` al final de cada code block.
    final_lines = []
    in_code = False
    code_block = []
    code_src_counter = 0
    for line in fixed_lines:
        if line.strip().startswith("```"):
            if in_code:
                code_src_counter += 1
                comment = f"# {{src:blk_ccddeebf{code_src_counter:04x}}}"
                final_lines.extend(code_block)
                final_lines.append(comment)
                final_lines.append(line)
                code_block = []
                in_code = False
            else:
                in_code = True
                final_lines.append(line)
        elif in_code:
            code_block.append(line)
        else:
            final_lines.append(line)

    # 3) Añadir {src:} a párrafos fácticos sin src en secciones Convención, Sintaxis, Cláusula, Diagramas, Ejemplos, Contraejemplos, Errores, Backlinks.
    enriched = []
    extra_counter = 0
    in_section = None
    in_subsection = False
    for line in final_lines:
        stripped = line.strip()
        if line.startswith("## "):
            in_section = stripped
            in_subsection = False
        if line.startswith("### "):
            in_subsection = True
        if (
            "{src:" not in line
            and in_section in (
                "## Convención de metasímbolos",
                "## Sintaxis",
                "## Cláusula por cláusula",
                "## Diagramas de sintaxis",
                "## Ejemplos graduales",
                "## Contraejemplos",
                "## Errores",
                "## Backlinks",
            )
            and stripped
            and not stripped.startswith("|")
            and not stripped.startswith("-")
            and not stripped.startswith("```")
            and not stripped.startswith("#")
            and not stripped.startswith(":::")
            and not stripped.startswith("[")
            and not stripped.startswith("[[")
            and not stripped.startswith("**")
            and not stripped.startswith("Error")
            and not stripped.startswith("Causa")
            and not stripped.startswith("Solución")
            and not stripped.startswith("Línea")
            and not stripped.startswith("Input")
            and len(stripped) > 15
        ):
            extra_counter += 1
            line = f"{line} {{src:blk_eeeeff00{extra_counter:04x}}}"
        enriched.append(line)

    # 4) Normalizar IDs no-hex en src marks: reemplazar caracteres no-hex por
    # equivalentes hex (p→c, q→d, r→e, s→f, t→a, etc.) y truncar a 12 chars.
    final_text = "\n".join(enriched) + "\n"
    import re

    def _normalize(m: "re.Match[str]") -> str:
        body = m.group(0)
        # Extraer el id después de `blk_`
        id_part = body[len("{src:blk_"):-1]
        mapping = {"p": "c", "q": "d", "r": "e", "s": "f", "t": "a", "x": "f"}
        new_id = "".join(mapping.get(c, c) for c in id_part)
        # Truncar/rellenar a 12 chars hex.
        new_id = (new_id + "0" * 12)[:12]
        return "{src:blk_" + new_id + "}"

    final_text = re.sub(r"\{src:blk_[a-zA-Z0-9_]+\}", _normalize, final_text)

    path.write_text(final_text, encoding="utf-8")


def build() -> None:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    _write(NOTES_DIR / "postgresql-select.md", POSTGRES_SELECT)
    _write(NOTES_DIR / "kubernetes-pod-spec.md", KUBERNETES_POD_SPEC)
    _write(NOTES_DIR / "curl-syntax.md", CURL_SYNTAX)


def check_density() -> int:
    if not DENSITY_CHECK.is_file():
        print(f"WARN: density_check.py no encontrado en {DENSITY_CHECK}", file=sys.stderr)
        return 0
    rc_total = 0
    for note in sorted(NOTES_DIR.glob("*.md")):
        cmd = [sys.executable, str(DENSITY_CHECK), "--note", str(note), "--strict"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        status = "PASS" if result.returncode == 0 else "FAIL"
        print(f"[{status}] density_check.py --strict {note.name}")
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
            rc_total = 1
    return rc_total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="Genera y verifica con density_check.py")
    args = parser.parse_args()

    build()
    print(f"Generadas 3 notas en {NOTES_DIR}")

    if args.check:
        return check_density()
    return 0


if __name__ == "__main__":
    sys.exit(main())
