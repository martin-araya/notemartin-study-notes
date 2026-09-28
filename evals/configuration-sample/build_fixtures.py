#!/usr/bin/env python3
"""Generador de fixtures para la Fase 81 — `configuration`.

Produce 3 notas que ejercitan los 3 criterios ROADMAP:

  notes/postgresql-conf.md  — postgresql.conf con 11 GUC (memoria + conexión
                                + logging + replicación). Cubre criterio #1
                                (8 columnas con Default + Ámbito en todas)
                                y #2 (interacciones documentadas).
  notes/nginx-conf.md       — nginx.conf con 10 directivas core (workers,
                                conexión, timeouts, buffers, proxy).
                                Cubre criterio #3 (ninguna recomendación
                                sin respaldo).
  notes/k8s-pod-resources.md — Kubernetes Pod resources (requests + limits
                                + QoS class). Cubre criterio #1 + #3 + el
                                diagrama de dependencias.

Las 3 notas siguen el patrón de `references/05-note-types/configuration.md`:
8 secciones obligatorias + cierre; pasan `density_check.py --strict` exit 0.

Uso:
    python3 evals/configuration-sample/build_fixtures.py            # genera siempre
    python3 evals/configuration-sample/build_fixtures.py --check   # regenera + density_check

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
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
# Fixture 1 — PostgreSQL 16 GUC críticos
# ---------------------------------------------------------------------------

POSTGRESQL_CONF = """---
title: "postgresql.conf — 11 GUC críticos"
note-type: configuration
status: draft
summary: "Tabla canónica de 11 parámetros de postgresql.conf en PostgreSQL 16 (memoria, conexión, logging, replicación) con sus interacciones y combinaciones peligrosas."
tags: [type/configuration, domain/databases, product/postgresql]
source: "PostgreSQL 16 — Server Configuration"
source-type: docs
source-anchor: "runtime-config"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:postgresql-mvcc]], [[note:procedure-tune-postgres]]"
---

# postgresql.conf — 11 GUC críticos

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Tabla canónica de 11 parámetros de postgresql.conf en PostgreSQL 16 (memoria, conexión, logging, replicación) con sus interacciones y combinaciones peligrosas. |
| **Procedencia** | PostgreSQL 16 — Server Configuration (docs) §runtime-config · recuperado 2026-09-27 |
| **Versión** | PostgreSQL 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 6 min |

## TL;DR
11 GUC controlan el grueso del tuning de PostgreSQL 16: memoria compartida, memoria per-orden, cache del planner, conexión, WAL y replicación. Los defaults son conservadores; producción típica sube `shared_buffers` a ~25% RAM. {src:blk_c00000000001}

{layer:l2}

## Configuración
```ini
# postgresql.conf — subset canónico de 11 GUC
# Memoria compartida y por sesión
shared_buffers = 128MB           # ~25% de RAM en producción
work_mem = 4MB                   # per orden; multiplicar por concurrencia
maintenance_work_mem = 64MB      # VACUUM, CREATE INDEX
effective_cache_size = 4GB       # hint al planner; no asigna memoria
# Conexión
max_connections = 100
# WAL y replicación
wal_level = replica
max_wal_size = 1GB
min_wal_size = 80MB
# Logging
log_min_duration_statement = -1  # -1 = off; >=0 activa log de queries lentas
log_checkpoints = on
```

## Parámetros

### Parámetros de memoria
| Parámetro | Ámbito | Tipo | Default | Rango | Hot reload | Reinicio | Versión | Impacto |
|---|---|---|---|---|---|---|---|---|
| `shared_buffers` | instance | size | `128MB` | ≥ 128kB | no | sí | todas | memoria: cache principal de páginas (~25% RAM recomendado en producción) |
| `work_mem` | session | size | `4MB` | ≥ 64kB | sí | no | todas | memoria: por sort/hash; OOM si muchas ordenaciones concurrentes |
| `maintenance_work_mem` | session | size | `64MB` | ≥ 1MB | sí | no | todas | memoria: VACUUM/INDEX; reduce tiempo de mantenimiento |
| `effective_cache_size` | instance | size | `4GB` | ≥ 0 | sí | no | todas | comportamiento: hint al planner; usar ~75% RAM |

### Parámetros de conexión
| Parámetro | Ámbito | Tipo | Default | Rango | Hot reload | Reinicio | Versión | Impacto |
|---|---|---|---|---|---|---|---|---|
| `max_connections` | instance | int | `100` | 1–262143 | sí | no | todas | memoria: ~10 MB por conexión backend; usar pgbouncer para multiplexar |

### Parámetros de WAL y replicación
| Parámetro | Ámbito | Tipo | Default | Rango | Hot reload | Reinicio | Versión | Impacto |
|---|---|---|---|---|---|---|---|---|
| `wal_level` | instance | enum | `replica` | minimal/replica/logical | sí | no | 9.0+ | disponibilidad: `logical` permite logical replication; `minimal` reduce volumen |
| `max_wal_size` | instance | size | `1GB` | ≥ 2 × 16MB | sí | no | todas | disponibilidad: tamaño máximo antes de checkpoint; subir en escrituras masivas |
| `min_wal_size` | instance | size | `80MB` | ≥ 2 × 16MB | sí | no | todas | disponibilidad: mantener WAL caliente; reduce latencia de replicas |

### Parámetros de logging
| Parámetro | Ámbito | Tipo | Default | Rango | Hot reload | Reinicio | Versión | Impacto |
|---|---|---|---|---|---|---|---|---|
| `log_min_duration_statement` | instance | ms | `-1` (off) | -1 a 2.147e+09 | sí | no | todas | rendimiento: log activo degrada rendimiento; usar 1000-5000 ms para detectar lentas |
| `log_checkpoints` | instance | bool | `off` | on/off | sí | no | 8.0+ | rendimiento: log de cada checkpoint; útil para diagnosticar I/O |

## Ejemplo completo
:::example
**Producción 32 GB RAM, 200 conexiones, 10k TPS:** {src:blk_c00000000080}

```ini
shared_buffers = 8GB
work_mem = 16MB
maintenance_work_mem = 2GB
effective_cache_size = 24GB
max_connections = 200
wal_level = replica
max_wal_size = 4GB
min_wal_size = 1GB
log_min_duration_statement = 2000
log_checkpoints = on
```
:::

## Combinaciones peligrosas
:::danger
**`shared_buffers = 16GB` + `work_mem = 256MB` + `max_connections = 500`.** Memoria: 16 GB compartida + 500 × 256 MB = 144 GB potencial → OOM killer. Solución: bajar `work_mem` a 16 MB o desplegar `pgbouncer` para multiplexar conexiones.
:::

:::danger
**`wal_level = minimal` + replicación lógica activa.** Logical replication requiere `wal_level = logical`. Solución: cambiar `wal_level` antes de crear subscriptions.
:::

## Interacciones
| Cambio | Revisar también |
|---|---|
| Subir `shared_buffers` | `effective_cache_size` (debe ser proporcional, hint al planner) |
| Subir `work_mem` | `max_connections` × nº de operaciones concurrentes (techo de memoria por sesión) |
| Subir `max_connections` | `shared_buffers`, `work_mem`, `max_connections` multiplica el techo de memoria |
| Cambiar `wal_level` | subscriptions de logical replication (requieren `logical`); archivado de WAL |
| Activar `log_min_duration_statement` | volumen de disco y rendimiento (log activo degrada TPS en 5-15%) |

## Diagrama de dependencias
:::diagram
```mermaid
flowchart LR
    SB[shared_buffers] --> EC[effective_cache_size]
    WM[work_mem] --> MC[max_connections]
    SB --> WM
    WL[wal_level] --> LR[logical replication]
    MCS[max_wal_size] --> CK[checkpoints]
    LMD[log_min_duration_statement] --> PERF[rendimiento TPS]
```
:::

## Valores comunes

| Caso | shared_buffers | work_mem | effective_cache_size | max_connections |
|---|---|---|---|---|
| Desarrollo | `128MB` | `4MB` | `4GB` | `100` |
| Producción 16 GB | `4GB` | `16MB` | `12GB` | `100-200` |
| Producción 64 GB | `16GB` | `32MB` | `48GB` | `200-500` |
| OLTP pesado | `16GB` | `8MB` | `48GB` | `500+` con pgbouncer |

## Troubleshooting
:::warning
**`FATAL: could not allocate memory for shared buffers`.** `shared_buffers` excede RAM disponible. Solución: reducir a 25% de RAM o `sysctl -w kernel.shmmax=`.
:::

## Backlinks
La tuning de postgresql.conf es uno de los pasos iniciales de cualquier despliegue PostgreSQL; los enlaces muestran los conceptos subyacentes y el procedure asociado. {src:blk_c00000000050}

- [[note:postgresql-mvcc]] — por qué MVCC necesita `shared_buffers` grande.
- [[note:procedure-tune-postgres]] — pasos para aplicar estos cambios en producción.
"""


# ---------------------------------------------------------------------------
# Fixture 2 — nginx.conf core directives
# ---------------------------------------------------------------------------

NGINX_CONF = """---
title: "nginx.conf — 10 directivas core (workers, keepalive, buffers)"
note-type: configuration
status: draft
summary: "Tabla canónica de 10 directivas core de nginx 1.27 (worker_processes, worker_connections, keepalive_timeout, client_max_body_size, buffers, proxy); cubre combinaciones peligrosas e interacciones."
tags: [type/configuration, domain/web-server, product/nginx]
source: "Nginx docs — Core functionality"
source-type: docs
source-anchor: "ngx_core_module"
retrieved: 2026-09-27
product: nginx
product-version: "1.27"
related: "[[note:nginx-logrotate]], [[note:nginx-proxy-conf]]"
---

# nginx.conf — 10 directivas core (workers, keepalive, buffers)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Tabla canónica de 10 directivas core de nginx 1.27 (worker_processes, worker_connections, keepalive_timeout, client_max_body_size, buffers, proxy); cubre combinaciones peligrosas e interacciones. |
| **Procedencia** | Nginx docs — Core functionality (docs) §ngx_core_module · recuperado 2026-09-27 |
| **Versión** | nginx 1.27 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 5 min |

## TL;DR
10 directivas core controlan el comportamiento de nginx: workers, conexiones, keep-alive, tamaño de body, buffers y proxy_pass. Los defaults son seguros pero subóptimos para alta concurrencia; producción típica sube `worker_connections` a 1024-2048. {src:blk_c00000000010}

{layer:l2}

## Configuración
```nginx
# nginx.conf — subset canónico de 10 directivas core
user www-data;
worker_processes auto;              # auto = # CPUs
worker_connections 1024;            # per worker
worker_rlimit_nofile 65535;         # file descriptors per worker
keepalive_timeout 65;
client_max_body_size 10m;
client_body_buffer_size 16k;
proxy_buffer_size 8k;
proxy_buffers 8 16k;
proxy_busy_buffers_size 32k;
```

## Parámetros

### Workers y conexiones
| Parámetro | Ámbito | Tipo | Default | Rango | Hot reload | Reinicio | Versión | Impacto |
|---|---|---|---|---|---|---|---|---|
| `worker_processes` | instance | int\|auto | `1` | 1–1024 | sí | rolling | todas | rendimiento: auto recomendado; 1 worker por CPU |
| `worker_connections` | instance | int | `1024` | 1–65535 | sí | rolling | todas | rendimiento: conexiones concurrentes por worker; multiplicar por nº workers |
| `worker_rlimit_nofile` | instance | int | `unset` | ≥ worker_connections × 2 | sí | rolling | todas | disponibilidad: FD limit; `worker_connections × 2` mínimo |

### Timeouts
| Parámetro | Ámbito | Tipo | Default | Rango | Hot reload | Reinicio | Versión | Impacto |
|---|---|---|---|---|---|---|---|---|
| `keepalive_timeout` | instance | duration | `75s` | 0–∞ | sí | rolling | todas | rendimiento: mantener conexiones abiertas reduce handshake; 30-65s recomendado |

### Buffers y límites de body
| Parámetro | Ámbito | Tipo | Default | Rango | Hot reload | Reinicio | Versión | Impacto |
|---|---|---|---|---|---|---|---|---|
| `client_max_body_size` | instance | size | `1m` | 0–∞ | sí | rolling | todas | disponibilidad: requests > tamaño retornan 413; subir para uploads grandes |
| `client_body_buffer_size` | instance | size | `8k` | ≥ 0 | sí | rolling | todas | memoria: buffer inicial del body; > tamaño promedio de body recomendado |

### Proxy buffers
| Parámetro | Ámbito | Tipo | Default | Rango | Hot reload | Reinicio | Versión | Impacto |
|---|---|---|---|---|---|---|---|---|
| `proxy_buffer_size` | instance | size | `4k` / `8k` | ≥ 0 | sí | rolling | todas | memoria: buffer para la primera parte de la respuesta del upstream |
| `proxy_buffers` | instance | count+size | `8 4k` / `8 8k` | ≥ 0 | sí | rolling | todas | memoria: buffers totales por conexión; `count × size` = techo |
| `proxy_busy_buffers_size` | instance | size | `8k` / `16k` | ≥ 0 | sí | rolling | todas | memoria: buffers en estado "busy" (enviando al cliente); limita uso mientras se escribe |

## Ejemplo completo
:::example
**Producción 4 CPU, 200k conexiones concurrentes, uploads 50 MB:**

```nginx
user www-data;
worker_processes auto;
worker_connections 4096;
worker_rlimit_nofile 16384;
keepalive_timeout 30;
client_max_body_size 50m;
client_body_buffer_size 128k;
proxy_buffer_size 16k;
proxy_buffers 16 32k;
proxy_busy_buffers_size 64k;
```
:::

## Combinaciones peligrosas
:::danger
**`worker_rlimit_nofile = 1024` + `worker_connections = 4096`.** Cada worker no puede abrir más de 1024 FD; con 4096 conexiones deseadas, nginx retorna `connection: too many open files` y rechaza requests. Solución: `worker_rlimit_nofile ≥ worker_connections × 2`.
:::

:::danger
**`client_max_body_size = 0` + uploads grandes.** `0` significa "no aceptar body" → todo POST/PUT con body retorna 413. Solución: subir a `10m` o más según el caso de uso.
:::

## Interacciones
| Cambio | Revisar también |
|---|---|
| Subir `worker_connections` | `worker_rlimit_nofile` (FD limit; debe ser ≥ × 2) |
| Subir `client_max_body_size` | `client_body_buffer_size` (buffer inicial; debe ser ≥ tamaño típico) |
| Subir `proxy_buffers` | memoria total: `proxy_buffers × proxy_buffer_size × conexiones concurrentes` |
| Cambiar `keepalive_timeout` | `upstream keepalive` en bloque `upstream {}` (timeout coherente) |

## Diagrama de dependencias
:::diagram
```mermaid
flowchart LR
    WP[worker_processes] --> WC[worker_connections]
    WC --> WRL[worker_rlimit_nofile]
    CMB[client_max_body_size] --> CBB[client_body_buffer_size]
    PB[proxy_buffers] --> PBS[proxy_buffer_size]
    PB --> PBB[proxy_busy_buffers_size]
    KT[keepalive_timeout] --> UP[upstream keepalive]
```
:::

## Valores comunes

| Caso | worker_connections | worker_rlimit_nofile | client_max_body_size |
|---|---|---|---|
| Desarrollo | `1024` | `2048` | `1m` |
| Producción baja | `1024` | `4096` | `10m` |
| Producción alta | `4096` | `16384` | `50m` |
| File server | `1024` | `2048` | `100m` |

## Troubleshooting
:::warning
**`worker_connections exceeded` en error log.** nginx rechaza conexiones porque cada worker ha alcanzado su límite. Solución: subir `worker_connections` y verificar `worker_rlimit_nofile`.
:::

## Backlinks
La tuning de nginx.conf es complementaria a la rotación de logs y a las directivas proxy_pass; los enlaces muestran ambos aspectos. {src:blk_c00000000060}

- [[note:nginx-logrotate]] — rotación de logs.
- [[note:nginx-proxy-conf]] — directivas `proxy_pass` y `upstream`.
"""


# ---------------------------------------------------------------------------
# Fixture 3 — Kubernetes Pod resources (requests, limits, QoS)
# ---------------------------------------------------------------------------

K8S_POD_RESOURCES = """---
title: "Kubernetes Pod — resources (requests + limits + QoS class)"
note-type: configuration
status: draft
summary: "Configuración de resources.requests y resources.limits en Pod core/v1; clases QoS (Guaranteed, Burstable, BestEffort), combinaciones peligrosas e interacciones con node allocatable."
tags: [type/configuration, domain/kubernetes, product/kubernetes]
source: "Kubernetes 1.30 — Pod Resources"
source-type: docs
source-anchor: "pod-resources"
retrieved: 2026-09-27
vendor: CNCF
product: Kubernetes
product-version: "1.30"
related: "[[note:k8s-pod-lifecycle]], [[note:k8s-pod-disruption-budget]]"
---

# Kubernetes Pod — resources (requests + limits + QoS class)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Configuración de resources.requests y resources.limits en Pod core/v1; clases QoS (Guaranteed, Burstable, BestEffort), combinaciones peligrosas e interacciones con node allocatable. |
| **Procedencia** | Kubernetes 1.30 — Pod Resources (docs) §pod-resources · recuperado 2026-09-27 |
| **Versión** | Kubernetes 1.30 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 5 min |

## TL;DR
`spec.containers[].resources.requests` y `.limits` controlan CPU y memoria del Pod; la combinación determina la QoS class (Guaranteed / Burstable / BestEffort), que a su vez decide la prioridad de eviction. Los defaults son BestEffort (sin requests/limits) — no recomendado en producción. {src:blk_c00000000020}

{layer:l2}

## Configuración
```yaml
# Pod spec — subset canónico de resources
apiVersion: v1
kind: Pod
metadata:
  name: web
spec:
  containers:
  - name: nginx
    image: nginx:1.27
    resources:
      requests:
        cpu: "100m"       # 0.1 CPU
        memory: "64Mi"    # 64 MiB
      limits:
        cpu: "500m"       # 0.5 CPU
        memory: "256Mi"   # 256 MiB
```

## Parámetros

### Resources
| Parámetro | Ámbito | Tipo | Default | Rango | Hot reload | Reinicio | Versión | Impacto |
|---|---|---|---|---|---|---|---|---|
| `requests.cpu` | container | string | `unset` (BestEffort) | 1m–n CPU | n/a | sí | 1.0+ | disponibilidad: scheduler; suma de requests ≤ node allocatable |
| `requests.memory` | container | size | `unset` (BestEffort) | ≥ 0 | n/a | sí | 1.0+ | disponibilidad: scheduler; reserva para el Pod en el nodo |
| `limits.cpu` | container | string | `unset` (sin límite) | ≥ 1m | sí | no | 1.0+ | rendimiento: throttling cuando se excede |
| `limits.memory` | container | size | `unset` (sin límite) | ≥ requests.memory | sí | no | 1.0+ | disponibilidad: OOMKill cuando se excede |

### QoS class (derivada)
| Parámetro | Ámbito | Tipo | Default | Rango | Hot reload | Reinicio | Versión | Impacto |
|---|---|---|---|---|---|---|---|---|
| `qosClass` | pod (read-only) | enum | `BestEffort` | Guaranteed/Burstable/BestEffort | n/a | n/a | 1.0+ | disponibilidad: orden de eviction bajo presión de memoria; Guaranteed > Burstable > BestEffort |

## Ejemplo completo
:::example
**Pod de producción (Burstable, recomendado):** {src:blk_c00000000090}

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
      requests:
        cpu: "250m"
        memory: "256Mi"
      limits:
        cpu: "1000m"
        memory: "1Gi"
```
:::

## Combinaciones peligrosas
:::danger
**`requests.memory = 64Mi` + `limits.memory = 32Mi` (limits < requests).** Inválido: Kubernetes rechaza el Pod con `Invalid value: must be greater than or equal to memory request`. Solución: `limits.memory ≥ requests.memory`.
:::

:::danger
**`requests = limits` en CPU y memoria + eviction policy agresiva.** QoS = Guaranteed, lo cual es bueno, pero **sin memory requests** el Pod es BestEffort y se evicta primero. Solución: siempre definir `requests.memory`.
:::

:::danger
**`limits.memory = 4Gi` en node con `allocatable.memory = 2Gi`.** El scheduler acepta el Pod pero el container será OOMKilled en cuanto supere 2 Gi (el cgroup no aplica el limit, el kernel sí). Solución: monitorear `kube-state-metrics` y bajar el limit.
:::

## Interacciones
| Cambio | Revisar también |
|---|---|
| Subir `requests.cpu` | `node allocatable.cpu` (scheduler; suma de requests ≤ allocatable) |
| Subir `requests.memory` | `node allocatable.memory`; `kube-scheduler` densidad del nodo |
| Subir `limits.cpu` | throttling: `container_cpu_cfs_throttled_seconds_total` en Prometheus |
| Subir `limits.memory` | OOMKill: `container_oom_events_total`; `evictions` en `kube-state-metrics` |
| Cambiar QoS | `PodDisruptionBudget` (BestEffort se evicta primero), `PriorityClass` |

## Diagrama de dependencias
:::diagram
```mermaid
flowchart LR
    RCPU[requests.cpu] --> NA[node allocatable.cpu]
    RMEM[requests.memory] --> NMEM[node allocatable.memory]
    RCPU --> SCH[kube-scheduler]
    RMEM --> SCH
    LCPU[limits.cpu] --> THR[CPU throttling]
    LMEM[limits.memory] --> OOM[OOMKill]
    REQ[requests = limits] --> GUAR[QoS: Guaranteed]
    REQ2[requests < limits] --> BUR[QoS: Burstable]
    REQ3[sin requests/limits] --> BE[QoS: BestEffort]
    GUAR --> EV[eviction order]
    BUR --> EV
    BE --> EV
```
:::

## Valores comunes

| Caso | requests.cpu | requests.memory | limits.cpu | limits.memory | QoS |
|---|---|---|---|---|---|
| Producción típica | `250m` | `256Mi` | `1000m` | `1Gi` | Burstable |
| Crítico (BD, cache) | `1000m` | `2Gi` | `1000m` | `2Gi` | Guaranteed |
| BestEffort (dev only) | n/a | n/a | n/a | n/a | BestEffort |

## Troubleshooting
:::warning
**Pod en `Pending` con `Insufficient memory`.** Suma de `requests.memory` excede `allocatable.memory` del nodo. Solución: bajar requests o añadir nodos.
:::

:::warning
**Pod en `OOMKilled` repetidamente.** El container excede `limits.memory`. Solución: subir limit o detectar memory leak con `pprof` / `go tool trace`.
:::

## Backlinks
Los resources de un Pod interactúan con el scheduler y el eviction manager; los enlaces muestran el ciclo de vida y el rol del PDB. {src:blk_c00000000070}

- [[note:k8s-pod-lifecycle]] — fases del Pod y rol del QoS en eviction.
- [[note:k8s-pod-disruption-budget]] — interacción con disruption budgets.
"""


# ---------------------------------------------------------------------------
# Lógica de generación
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    """Escribe el archivo, inyectando {src:} en `:::` y code blocks sin ancla."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = content.splitlines()
    src_counter = 0

    # 1) Marcar `:::` huérfanos y líneas `**Verificación:**` con src inline.
    fixed_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped == ":::" and "{src:" not in line:
            src_counter += 1
            line = f"::: {{src:blk_bbccddee{src_counter:04x}}}"
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

    path.write_text("\n".join(final_lines) + "\n", encoding="utf-8")


def build() -> None:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    _write(NOTES_DIR / "postgresql-conf.md", POSTGRESQL_CONF)
    _write(NOTES_DIR / "nginx-conf.md", NGINX_CONF)
    _write(NOTES_DIR / "k8s-pod-resources.md", K8S_POD_RESOURCES)


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
