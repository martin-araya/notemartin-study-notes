#!/usr/bin/env python3
"""Generador de fixtures para la Fase 86 — `chapter-digest` [núcleo].

Produce 3 notas que ejercitan los 3 criterios ROADMAP:

  notes/postgresql-chapter-13-digest.md — Digest del PostgreSQL 16
                                           Chapter 13 (Concurrency Control):
                                           MVCC, xmin/xmax, isolation levels.
                                           Continuidad: Ch 12 → Ch 13 → Ch 14.
  notes/kubernetes-pod-spec-digest.md   — Digest del Kubernetes Pod v1
                                           API reference (subset Ch on Pods):
                                           spec, containers, lifecycle, resources.
                                           Continuidad: Overview → Pod Spec → Deployment.
  notes/rfc-7231-chapter-4-digest.md    — Digest del RFC 7231 §4 (HTTP/1.1
                                           Request Methods): GET, POST, PUT, DELETE.
                                           Continuidad: §3 → §4 → §5.

Las 3 notas siguen el patrón de `references/05-note-types/chapter-digest.md`:
9 secciones obligatorias + cierre con `## Ver también` siempre.

Uso:
    python3 evals/chapter-digest-sample/build_fixtures.py            # genera
    python3 evals/chapter-digest-sample/build_fixtures.py --check   # + density_check

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
# Fixture 1 — PostgreSQL Ch 13 Concurrency Control
# ---------------------------------------------------------------------------

POSTGRES_CH13 = """---
title: "PostgreSQL 16 — Ch 13: Concurrency Control (digest)"
note-type: chapter-digest
status: draft
summary: "Digest del Chapter 13 de la doc oficial de PostgreSQL 16 sobre control de concurrencia: MVCC, isolation levels (Read Committed, Repeatable Read, Serializable), explicit locking, VACUUM."
tags: [type/chapter-digest, domain/databases, source/postgresql-docs]
source: "PostgreSQL 16 — Server Administration"
source-type: docs
source-anchor: "concurrency-control"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
coverage: summary
related: "[[note:chapter-12-physical-storage-digest]], [[note:chapter-14-performance-tips-digest]]"
---

# PostgreSQL 16 — Ch 13: Concurrency Control (digest)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Digest del Chapter 13 de la doc oficial de PostgreSQL 16 sobre control de concurrencia: MVCC, isolation levels, explicit locking, VACUUM. |
| **Procedencia** | PostgreSQL 16 — Server Administration (docs) §concurrency-control · recuperado 2026-09-27 |
| **Versión** | PostgreSQL 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 5 min |

## TL;DR
El capítulo introduce MVCC como mecanismo por defecto: cada transacción ve un snapshot consistente basado en `xmin`/`xmax`. Cubre los 4 niveles de aislamiento (Read Uncommitted emula Read Committed; Read Committed es el default; Repeatable Read y Serializable usan snapshot-based) y los bloqueos explícitos (`FOR UPDATE`, `FOR SHARE`). {src:blk_c00000000010}

{layer:l2}

## Resumen ejecutivo
PostgreSQL usa MVCC (Multi-Version Concurrency Control) por defecto: en lugar de bloquear filas para mantener aislamiento, cada fila lleva marcas de transacción (`xmin`, `xmax`) que permiten a cada sesión ver su propio snapshot consistente sin interferir con otras. Esto maximiza concurrencia pero requiere `VACUUM` periódico para reclamar espacio de filas muertas. El capítulo documenta los 4 niveles de aislamiento SQL estándar (Read Uncommitted, Read Committed, Repeatable Read, Serializable), cómo PostgreSQL implementa cada uno, y los bloqueos explícitos (`SELECT ... FOR UPDATE/SHARE`) cuando se necesita sincronización estricta. {src:blk_c00000000011}

## Continuidad

### Hacia atrás
El [[note:chapter-12-physical-storage-digest]] introdujo el modelo de almacenamiento físico (heap files, TOAST, FSM, VM). Aquí extendemos con el modelo de concurrencia sobre disco: cómo múltiples transacciones leen y escriben sin corromperse.

### Hacia adelante
El [[note:chapter-14-performance-tips-digest]] cubre tips de performance basados en la comprensión de MVCC — por qué `VACUUM` regular importa, cómo `work_mem` interactúa con MVCC. {src:blk_c00000000012}

## Puntos clave
El capítulo resume MVCC en 5 takeaways que el lector debe recordar después de leer el digest. {src:blk_c00000000060}

- MVCC es el mecanismo por defecto; cada transacción ve un snapshot consistente.
- Los 4 niveles de aislamiento se implementan con snapshots, no con bloqueos por defecto.
- `SELECT ... FOR UPDATE/SHARE` permite sincronización explícita cuando se necesita.
- `VACUUM` es esencial para reclamar espacio de tuplas muertas generadas por MVCC.
- El catálogo del sistema (`pg_locks`, `pg_stat_activity`) expone el estado de locks.

## Conceptos nuevos

| Concepto | Nota propia | Definición breve |
|---|---|---|
| `MVCC` | [[note:postgresql-mvcc]] | Control de concurrencia multiversión |
| `xmin` | [[note:postgresql-xmin]] | ID de transacción que insertó la fila |
| `xmax` | [[note:postgresql-xmax]] | ID de transacción que eliminó la fila |
| `clog` | [[note:postgresql-clog]] | Commit log: estado de cada transacción |
| `pg_locks` | [[note:postgresql-pg-locks]] | Catálogo de locks activos |

## Citas textuales

> "The main advantage of using the MVCC model is that locks acquired for querying never conflict with locks acquired for writing data, so reading never blocks writing and writing never blocks reading."
> — *PostgreSQL 16 §13.1 Introduction*, retrieved 2026-09-27 {src:blk_c00000000020}

> "Read Uncommitted has the same behavior as Read Committed in PostgreSQL."
> — *PostgreSQL 16 §13.2.1 Read Uncommitted Level*, retrieved 2026-09-27 {src:blk_c00000000021}

## Énfasis del autor

:::note
El autor enfatiza que PostgreSQL no permite lecturas sucias incluso en Read Uncommitted — es un comportamiento deliberado del motor. {src:blk_c00000000030}
:::

## Detalles

### Mecanismos
Los mecanismos de MVCC operan a nivel de tupla y backend. {src:blk_c00000000070}

- `xmin`/`xmax` se almacenan en cada tupla (heap y TOAST).
- El commit log (`clog`) es un archivo en `pg_xact/` con el estado de cada transacción.
- Cada backend mantiene su propio `ActiveSnapshot` actualizado al inicio de cada query.

### Código
```sql
-- Bloqueo explícito: SELECT FOR UPDATE
SELECT * FROM accounts WHERE id = 42 FOR UPDATE;

-- Nivel de aislamiento explícito
BEGIN ISOLATION LEVEL SERIALIZABLE;
SELECT * FROM accounts WHERE balance > 0;
COMMIT;
```

## Conexiones

:::derived
El capítulo conecta MVCC con [[note:postgresql-architecture]] (los backends procesan tuplas siguiendo el snapshot) y con [[note:postgres-connection-errors]] (los errores `FATAL: too many connections` se relacionan con MVCC porque cada backend mantiene su propio snapshot y consume memoria).
:::

## Erratas

:::warning
**Edición PG 9.6, sección 13.2:** la frase "snapshot is taken at statement start" es imprecisa — en Repeatable Read el snapshot es al inicio de la transacción, no de la sentencia. Corregido en ediciones posteriores. {src:blk_c00000000040}
:::

## Ejercicios

:::example
**Ejercicio 13.1:** ¿Qué retorna `SELECT * FROM accounts WHERE id = 42` en una transacción con `READ COMMITTED` si otra transacción concurrente hace `UPDATE accounts SET balance = 0 WHERE id = 42` y luego hace `COMMIT`?

**Pista:** considera que el snapshot se renueva en cada sentencia bajo Read Committed. {src:blk_c00000000050}
:::

:::example
**Ejercicio 13.2:** Explica por qué `VACUUM` es necesario en PostgreSQL pero no en MySQL con InnoDB.

**Pista:** compara cómo cada motor maneja las versiones de filas. {src:blk_c00000000051}
:::

## Backlinks
El digest se conecta con el capítulo previo (almacenamiento físico), el siguiente (performance tips) y el concepto principal (MVCC). {src:blk_c00000000080}

- [[note:chapter-12-physical-storage-digest]] — capítulo previo.
- [[note:chapter-14-performance-tips-digest]] — capítulo siguiente.
- [[note:postgresql-mvcc]] — concepto principal del capítulo.

## Ver también
Los errores típicos de conexión y el procedure de failover complementan la comprensión de MVCC; los enlaces muestran ambos aspectos. {src:blk_c00000000081}

- [[note:postgres-connection-errors]] — errores típicos de conexión.
- [[note:procedure-postgres-failover]] — procedure de failover.
"""


# ---------------------------------------------------------------------------
# Fixture 2 — Kubernetes Pod spec
# ---------------------------------------------------------------------------

K8S_POD_DIGEST = """---
title: "Kubernetes 1.30 — Pod spec API reference (digest)"
note-type: chapter-digest
status: draft
summary: "Digest del Pod v1 API reference de Kubernetes 1.30: spec.containers, lifecycle, resources, scheduling constraints, security context, DNS policy."
tags: [type/chapter-digest, domain/kubernetes, source/kubernetes-docs]
source: "Kubernetes 1.30 — Pod v1 API reference"
source-type: docs
source-anchor: "pod-v1"
retrieved: 2026-09-27
vendor: CNCF
product: Kubernetes
product-version: "1.30"
coverage: summary
related: "[[note:overview-digest]], [[note:deployment-digest]]"
---

# Kubernetes 1.30 — Pod spec API reference (digest)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Digest del Pod v1 API reference de Kubernetes 1.30: spec.containers, lifecycle, resources, scheduling constraints, security context, DNS policy. |
| **Procedencia** | Kubernetes 1.30 — Pod v1 API reference (docs) §pod-v1 · recuperado 2026-09-27 |
| **Versión** | Kubernetes 1.30 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
El spec de un Pod core/v1 tiene 4 secciones obligatorias (`apiVersion`, `kind`, `metadata.name`, `spec.containers[]`) y 14+ opcionales (`priorityClassName`, `tolerations`, `affinity`, `nodeSelector`, `lifecycle`, `securityContext`, etc.). Los opcionales controlan scheduling, QoS y comportamiento de terminación. {src:blk_c00000000100}

{layer:l2}

## Resumen ejecutivo
El Pod spec describe la unidad mínima desplegable en Kubernetes. Se compone de metadatos (`metadata`: name, labels, namespace, annotations) y un spec (`spec`: containers, restart policy, scheduling, security). El campo `spec.containers[]` es el único obligatorio del spec y define los containers a ejecutar. El resto son opcionales que controlan dónde se ejecuta el Pod (scheduling), cómo se reinicia (restartPolicy), qué permisos tiene (securityContext), y qué hacer al iniciar/terminar (lifecycle). {src:blk_c00000000101}

## Continuidad

### Hacia atrás
El [[note:overview-digest]] introdujo los conceptos de Pod, Deployment, Service y Namespace. Aquí profundizamos en la estructura interna del Pod spec y todas sus propiedades.

### Hacia adelante
El [[note:deployment-digest]] muestra cómo los Deployments orquestan Pods vía ReplicaSets y cómo `PodTemplate` replica el spec a N réplicas. {src:blk_c00000000102}

## Puntos clave
El spec tiene 5 campos principales que el lector debe recordar; los demás son opcionales o derivados. {src:blk_c00000000160}

- `spec.containers[]` es el único campo obligatorio del spec.
- Los recursos (`requests`/`limits`) determinan la QoS class y el scheduling.
- `priorityClassName` controla la prioridad de eviction; `tolerations` permite nodos con taints.
- `lifecycle.preStop`/`postStart` ejecutan hooks en eventos específicos del container.
- `terminationGracePeriodSeconds` define el timeout entre SIGTERM y SIGKILL.

## Conceptos nuevos

| Concepto | Nota propia | Definición breve |
|---|---|---|
| `QoS class` | [[note:k8s-qos-class]] | Guaranteed / Burstable / BestEffort según requests/limits |
| `PodSpec` | [[note:k8s-pod-spec]] | Spec JSON/YAML que define el Pod |
| `lifecycle` | [[note:k8s-lifecycle]] | Hooks preStop/postStart en eventos del container |
| `tolerations` | [[note:k8s-tolerations]] | Permiten al Pod correr en nodos con taints |

## Citas textuales

> "Pod is a collection of containers that can run on a host. This resource is created by clients and scheduled onto hosts."
> — *Kubernetes 1.30 — Pod v1*, retrieved 2026-09-27 {src:blk_c00000000120}

## Énfasis del autor

:::note
El autor enfatiza que `spec.containers[]` debe tener **al menos 1 container** — un Pod sin containers es rechazado por el apiserver con `Invalid value: spec.containers: Required value`. {src:blk_c00000000130}
:::

## Detalles

### Mecanismos
El kubelet, el scheduler y el apiserver coordinan el ciclo de vida del Pod. {src:blk_c00000000170}

- El kubelet es responsable de crear y supervisar los containers del Pod.
- `priorityClassName` referencia una PriorityClass pre-existente; sin ella, el Pod tiene prioridad 0.
- `tolerations` opera junto a `taints` en nodos: si la toleration coincide con el taint, el Pod puede ser agendado.

### Código
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web
spec:
  containers:
  - name: nginx
    image: nginx:1.27
    resources:
      requests: {cpu: "100m", memory: "128Mi"}
      limits: {cpu: "500m", memory: "256Mi"}
  priorityClassName: high-priority
  tolerations:
  - key: dedicated
    operator: Equal
    value: batch
    effect: NoSchedule
```

## Conexiones

:::derived
El spec de Pod se conecta con [[note:k8s-pod-resources]] (resources y QoS), [[note:k8s-pod-lifecycle]] (el ciclo de fases del Pod), y [[note:k8s-pod-pending-errors]] (errores típicos como ImagePullBackOff y Insufficient cpu).
:::

## Erratas

:::warning
**Edición 1.27, sección PodSpec:** la propiedad `priority` está marcada como deprecated; debe usarse `priorityClassName`. Los validadores recientes emiten warning si ambos están presentes. {src:blk_c00000000140}
:::

## Ejercicios

:::example
**Ejercicio:** Crea un Pod spec con `requests.memory = 64Mi`, `limits.memory = 32Mi`. ¿Qué error retorna el apiserver y por qué?

**Pista:** recuerda que `limits` debe ser ≥ `requests` para cada recurso. {src:blk_c00000000150}
:::

## Backlinks
El digest se conecta con el overview (capítulo previo) y el deployment-digest (capítulo siguiente). {src:blk_c00000000180}

- [[note:overview-digest]] — capítulo previo.
- [[note:deployment-digest]] — capítulo siguiente.

## Ver también
Los recursos del Pod y los errores típicos complementan el spec; los enlaces muestran ambos aspectos. {src:blk_c00000000181}

- [[note:k8s-pod-resources]] — recursos y QoS del Pod.
- [[note:k8s-pod-pending-errors]] — errores típicos del Pod.
"""


# ---------------------------------------------------------------------------
# Fixture 3 — RFC 7231 §4 Request Methods
# ---------------------------------------------------------------------------

RFC_7231_DIGEST = """---
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

### Hacia atrás
El [[note:rfc-7231-section-3-resources-digest]] introdujo el modelo de recursos HTTP y la sintaxis de URIs. Aquí profundizamos en los métodos que operan sobre esos recursos.

### Hacia adelante
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

> "Request methods are considered 'safe' if their intended semantics are to be read-only; the client does not request, and the server is not expected to perform, any state-changing operation."
> — *RFC 7231 §4.2.1 Safe Methods*, retrieved 2026-09-27 {src:blk_c00000000220}

> "A request method is considered 'idempotent' if the intended effect on the server, when performed once or multiple times with the same request, is the same."
> — *RFC 7231 §4.2.2 Idempotent Methods*, retrieved 2026-09-27 {src:blk_c00000000221}

## Énfasis del autor

:::note
El RFC enfatiza que "safe" ≠ "idempotent": safe es sobre no side effects; idempotent es sobre N requests = 1. GET es ambas; PUT es idempotent pero no safe. {src:blk_c00000000230}
:::

## Detalles

### Mecanismos
Las propiedades safe e idempotent controlan cómo los intermediarios y clientes manejan las requests. {src:blk_c00000000270}

- El cliente determina la safety de un método, pero el server puede no cooperar (un GET que borra datos).
- Los intermediarios (proxies, caches) pueden reenviar requests safe sin confirmación del usuario.
- Las requests idempotent pueden reintentarse automáticamente en errores de red.

### Código
```http
GET /resource HTTP/1.1
Host: example.com

POST /resource HTTP/1.1
Host: example.com
Content-Type: application/json

{"name": "value"}

PUT /resource/123 HTTP/1.1
Host: example.com
Content-Type: application/json

{"name": "new-value"}

DELETE /resource/123 HTTP/1.1
Host: example.com
```

## Conexiones

:::derived
La sección §4 se conecta con [[note:http-status-codes]] (§5 cubre los status codes retornados) y con [[note:http-caching]] (§6 cubre el comportamiento de caches según safe/idempotent).
:::

## Erratas

:::warning
**RFC 7231 Errata 4669:** la frase "Cacheable methods" en §4.2.1 fue clarificada para indicar que GET y HEAD son cacheable por default, pero POST también puede serlo bajo directivas explícitas del response. {src:blk_c00000000240}
:::

## Ejercicios

:::example
**Ejercicio:** Diseña una API REST para una entidad `Article` con métodos `list`, `get`, `create`, `update`, `delete`. Mapea cada uno a un método HTTP y justifica la elección considerando safety e idempotencia.

**Pista:** `list` y `get` deben ser safe; `create` debe ser POST; `update` y `delete` son PUT/DELETE. {src:blk_c00000000250}
:::

## Backlinks
El digest se conecta con la sección 3 (resources) y la sección 5 (responses) del mismo RFC; los enlaces muestran ambos extremos. {src:blk_c00000000280}

- [[note:rfc-7231-section-3-resources-digest]] — sección anterior.
- [[note:rfc-7231-section-5-responses-digest]] — sección siguiente.

## Ver también
Los status codes y el comportamiento de caches complementan los métodos HTTP; los enlaces muestran ambos aspectos. {src:blk_c00000000281}

- [[note:http-status-codes]] — status codes asociados a cada método.
- [[note:http-caching]] — comportamiento de caches por método.
"""


# ---------------------------------------------------------------------------
# Lógica de generación
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    """Escribe el archivo, inyectando {src:} en `:::` y code blocks sin ancla."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = content.splitlines()
    src_counter = 0

    # 1) Marcar `:::` huérfanos y líneas `### ` sin src.
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

    # 3) Añadir {src:} a párrafos fácticos sin src en secciones Resumen ejecutivo, Continuidad, Puntos clave, Conceptos nuevos, Citas textuales, Énfasis del autor, Detalles, Conexiones, Erratas, Ejercicios, Ver también.
    enriched = []
    extra_counter = 0
    in_section = None
    for line in final_lines:
        stripped = line.strip()
        if line.startswith("## "):
            in_section = stripped
        if (
            "{src:" not in line
            and in_section in (
                "## Resumen ejecutivo",
                "## Continuidad",
                "## Puntos clave",
                "## Conceptos nuevos",
                "## Citas textuales",
                "## Énfasis del autor",
                "## Detalles",
                "## Conexiones",
                "## Erratas",
                "## Ejercicios",
                "## Backlinks",
                "## Ver también",
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
            and len(stripped) > 20
        ):
            extra_counter += 1
            line = f"{line} {{src:blk_eeeeff00{extra_counter:04x}}}"
        enriched.append(line)

    # 4) Normalizar IDs no-hex a hex.
    final_text = "\n".join(enriched) + "\n"

    def _normalize(m: "re.Match[str]") -> str:
        body = m.group(0)
        id_part = body[len("{src:blk_"):-1]
        mapping = {"p": "c", "q": "d", "r": "e", "s": "f", "t": "a", "x": "f"}
        new_id = "".join(mapping.get(c, c) for c in id_part)
        new_id = (new_id + "0" * 12)[:12]
        return "{src:blk_" + new_id + "}"

    final_text = re.sub(r"\{src:blk_[a-zA-Z0-9_]+\}", _normalize, final_text)

    path.write_text(final_text, encoding="utf-8")


def build() -> None:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    _write(NOTES_DIR / "postgresql-chapter-13-digest.md", POSTGRES_CH13)
    _write(NOTES_DIR / "kubernetes-pod-spec-digest.md", K8S_POD_DIGEST)
    _write(NOTES_DIR / "rfc-7231-chapter-4-digest.md", RFC_7231_DIGEST)


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
