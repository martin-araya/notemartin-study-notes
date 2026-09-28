#!/usr/bin/env python3
"""Generador de fixtures para la Fase 83 — `architecture`.

Produce 3 notas que ejercitan los 3 criterios ROADMAP:

  notes/postgresql-architecture.md  — PostgreSQL 16: postmaster, backend,
                                        WAL writer, bgwriter, autovacuum,
                                        shared buffers. 5 puntos de fallo +
                                        3 cuellos de botella con métrica.
  notes/kubernetes-architecture.md  — Kubernetes 1.30 control plane: kube-
                                        apiserver, etcd, kube-scheduler,
                                        kube-controller-manager, kubelet.
                                        5 puntos de fallo + 3 cuellos de
                                        botella.
  notes/docker-architecture.md       — Docker 25: dockerd, containerd, runc,
                                        shim, namespace/cgroup. 4 puntos de
                                        fallo + 3 cuellos de botella.

Las 3 notas siguen el patrón de `references/05-note-types/architecture.md`:
9 secciones obligatorias + cierre; pasan `density_check.py --strict` exit 0.

Uso:
    python3 evals/architecture-sample/build_fixtures.py            # genera
    python3 evals/architecture-sample/build_fixtures.py --check   # + density_check

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
# Fixture 1 — PostgreSQL 16 architecture
# ---------------------------------------------------------------------------

POSTGRES_ARCHITECTURE = """---
title: "PostgreSQL 16 — arquitectura interna"
note-type: architecture
status: draft
summary: "Arquitectura interna de PostgreSQL 16: procesos postmaster/backends/bgwriter/autovacuum, modelo de memoria shared_buffers/WAL, flujo de un query, puntos de fallo y cuellos de botella."
tags: [type/architecture, domain/databases, product/postgresql]
source: "PostgreSQL 16 — Internals"
source-type: docs
source-anchor: "internals"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:postgresql-mvcc]], [[note:postgresql-configuration]], [[note:postgres-connection-errors]]"
---

# PostgreSQL 16 — arquitectura interna

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Arquitectura interna de PostgreSQL 16: procesos postmaster/backends/bgwriter/autovacuum, modelo de memoria shared_buffers/WAL, flujo de un query, puntos de fallo y cuellos de botella. |
| **Procedencia** | PostgreSQL 16 — Internals (docs) §internals · recuperado 2026-09-27 |
| **Versión** | PostgreSQL 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 6 min |

## TL;DR
PostgreSQL usa un modelo de procesos (no threads): un postmaster coordina N backends por conexión, con procesos de fondo para WAL, bgwriter y autovacuum. El dataset vive en shared_buffers + heap files + WAL. {src:blk_a00000000010}

{layer:l2}

## Vista general
PostgreSQL es un SGBD relacional con arquitectura cliente-servidor basada en procesos Unix. Cada conexión cliente recibe un proceso backend dedicado (fork del postmaster); el aislamiento entre backends se logra vía memoria privada y locks sobre estructuras compartidas. El modelo de persistencia es write-ahead log (WAL) + checkpoints periódicos. {src:blk_a00000000011}

:::diagram
```mermaid
flowchart LR
    C[Cliente: psql] -->|TCP 5432| P[postmaster]
    P -->|fork| B1[backend 1]
    P -->|fork| B2[backend 2]
    P --> BW[bgwriter]
    P --> AV[autovacuum]
    P --> WW[walwriter]
    BW --> SB[shared_buffers]
    WW --> WAL[(WAL files)]
    AV --> HF[(heap files)]
```
:::

## Componentes y responsabilidades
| Componente | Responsabilidad | Ubicación |
|---|---|---|
| `postmaster` | Proceso principal que escucha en 5432 y coordina la creación de backends | proceso Unix; `pg_ctl start` |
| `backend` | Proceso por conexión; parsea, planifica y ejecuta queries | fork del postmaster; ≤ `max_connections` |
| `bgwriter` | Escribe dirty pages de shared_buffers a heap files en background | proceso bgwriter |
| `walwriter` | Flush del WAL buffer a los WAL files en disco de forma asíncrona | proceso walwriter |
| `autovacuum` | Libera tuplas muertas y actualiza estadísticas del planner | workers autovacuum |

## Flujo paso a paso

### Paso 1: Conexión
El cliente abre TCP al 5432; el postmaster hace `fork()` de un nuevo backend dedicado (no thread). {src:blk_a00000000012}

### Paso 2: Parse + Plan
El backend recibe el query SQL, lo parsea (parser → árbol), lo reescribe (rewriter) y lo planifica (planner → plan tree con costos estimados). {src:blk_a00000000013}

### Paso 3: Ejecución
El executor recorre el plan tree y aplica operadores sobre shared_buffers (en RAM) o lee de heap files (en disco). Las escrituras se hacen primero en WAL buffer. {src:blk_a00000000014}

### Paso 4: Commit
Al hacer `COMMIT`, el walwriter flushea el WAL buffer a disco antes de retornar éxito al cliente (garantía WAL). El backend notifica al cliente con `CommandComplete`. {src:blk_a00000000015}

:::diagram
```mermaid
sequenceDiagram
    participant C as Cliente
    participant P as postmaster
    participant B as backend
    participant SB as shared_buffers
    participant W as walwriter
    participant D as Disco
    C->>P: CONNECT
    P->>B: fork()
    C->>B: SELECT * FROM t
    B->>SB: leer páginas
    SB-->>B: tuplas
    B-->>C: rows
    C->>B: UPDATE + COMMIT
    B->>W: flush WAL buffer
    W->>D: WAL file write+fsync
    W-->>B: OK
    B-->>C: CommandComplete
```
:::

## Interacciones

| Origen | Destino | Protocolo | Frecuencia |
|---|---|---|---|
| Cliente ↔ postmaster/backend | TCP/5432 | protocolo v3 (`pgwire`) | por query |
| backend → shared_buffers | memoria compartida | IPC lock-free en lo posible | por acceso a página |
| walwriter → disco | fsync | llamada al sistema | cada ~200ms o al commit |
| bgwriter → disco | write + fsync | llamada al sistema | cada ~200ms |

## Estructuras en memoria y disco

### En memoria
| Estructura | Tamaño típico | Vida |
|---|---|---|
| `shared_buffers` | 25% de RAM (ej: 8 GB) | persistente, mmap a `base/pg_dir` |
| `WAL buffers` | 16 MB (config `wal_buffers`) | por sesión hasta flush |
| `backend work_mem` | 4-64 MB por query (config `work_mem`) | por sort/hash |
| Lock table | 16 MB (config `max_locks_per_transaction`) | persistente |

### En disco
| Archivo | Tamaño típico | Rotación |
|---|---|---|
| Heap files (`base/*/`) | 1 GB - 10 TB | nunca (viven hasta `VACUUM FULL`) |
| WAL files (`pg_wal/`) | 16 MB cada uno (config `wal_segment_size`) | reciclados tras `archive_command` o `max_wal_size` |
| `pg_xact/` (clog) | 1 página por 32k transacciones | truncado por `VACUUM` |

## Puntos de fallo

:::danger
**Crash durante WAL write → pérdida de la transacción no flusheada.** El WAL buffer puede contener el COMMIT antes del fsync; un crash del OS entre el write y el fsync rompe la durabilidad. {src:blk_a00000000016} Mitigación: `synchronous_commit = on` (default) o `on` + batería con redundancia de energía.
:::

:::warning
**Autovacuum no se ejecuta → table bloat.** Si autovacuum está deshabilitado o no puede obtener lock, las tuplas muertas se acumulan y el archivo de heap crece sin parar. {src:blk_a00000000017} Mitigación: monitorizar `pg_stat_all_tables.n_dead_tup` con `pgwatch2`; nunca deshabilitar autovacuum.
:::

:::warning
**Backend saturado por OOM en sort.** `work_mem = 256MB` × 100 conexiones activas con sort = 25 GB potenciales → OOM killer. {src:blk_a00000000018} Mitigación: `work_mem` bajo (16-64 MB); `pgbouncer` para multiplexar.
:::

:::warning
**Lock contention en `pg_stat_activity`.** `SELECT * FROM pg_stat_activity` toma `ACCESS SHARE` en `pg_database`; si otra transacción tiene `ACCESS EXCLUSIVE`, el query espera. {src:blk_a00000000019} Mitigación: usar `pg_stat_activity` con `pg_locks` solo en diagnóstico, no en monitoring automático.
:::

:::warning
**WAL archival falla → backups rotos.** Si `archive_command` retorna no-cero, PostgreSQL acumula WAL files y llena el disco. {src:blk_a00000000020} Mitigación: alertar con `archive_command` en `monit`; rate-limit WAL con `archive_timeout`.
:::

## Cuellos de botella

:::warning
**Disco I/O en WAL flush.** Throughput limitado por fsync (~1000-5000 ops/s en SSD; ~100-200 en HDD). Métrica: `pg_stat_wal.wal_write_time / wal_write_count`. Mitigación: SSD NVMe con `wal_compression = on` + `synchronous_commit = off` (si RPO de ms es aceptable).
:::

:::warning
**Lock manager en DDL.** `ACCESS EXCLUSIVE` lock bloquea todos los readers durante ALTER TABLE; tables grandes (> 100 GB) pueden tardar minutos. Métrica: `pg_locks.mode = AccessExclusiveLock` en `pg_stat_activity`. Mitigación: herramientas de schema migration online (pg_repack, pg_squeeze).
:::

:::warning
**Connection storms.** Sin pooler, picos de tráfico crean miles de backends que agotan `max_connections` (memoria + slots). Métrica: `pg_stat_activity.count` vs `max_connections`. Mitigación: `pgbouncer` en modo transaction; `max_connections = 100` con 1000 clients.
:::

## Decisiones de diseño

:::note
**Procesos, no threads.** PostgreSQL usa procesos Unix para backends por aislamiento de memoria y robustez (un crash de un backend no afecta a otros); trade-off: ~10 MB por backend, mayor fork overhead.
:::

:::note
**MVCC en lugar de locks pesimistas.** Cada transacción ve su propio snapshot vía `xmin`/`xmax`; trade-off: table bloat que requiere vacuum periódico.
:::

## Backlinks
La arquitectura interna de PostgreSQL se complementa con los conceptos (MVCC), la configuración (GUCs críticos) y los errores típicos; los enlaces muestran los 3 ángulos. {src:blk_a00000000060}

- [[note:postgresql-mvcc]] — modelo de visibilidad que explica el table bloat.
- [[note:postgresql-configuration]] — `shared_buffers`, `work_mem`, `max_connections`.
- [[note:postgres-connection-errors]] — confundibles: errores típicos del backend.
"""


# ---------------------------------------------------------------------------
# Fixture 2 — Kubernetes 1.30 architecture
# ---------------------------------------------------------------------------

KUBERNETES_ARCHITECTURE = """---
title: "Kubernetes 1.30 — arquitectura del control plane y worker nodes"
note-type: architecture
status: draft
summary: "Arquitectura interna de Kubernetes 1.30: control plane (kube-apiserver, etcd, scheduler, controller-manager) y worker nodes (kubelet, kube-proxy, runtime); flujo de un Pod, puntos de fallo y cuellos de botella."
tags: [type/architecture, domain/kubernetes, product/kubernetes]
source: "Kubernetes 1.30 — Components"
source-type: docs
source-anchor: "components"
retrieved: 2026-09-27
vendor: CNCF
product: Kubernetes
product-version: "1.30"
related: "[[note:k8s-pod-resources]], [[note:k8s-pod-lifecycle]], [[note:k8s-pod-pending-errors]]"
---

# Kubernetes 1.30 — arquitectura del control plane y worker nodes

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Arquitectura interna de Kubernetes 1.30: control plane (kube-apiserver, etcd, scheduler, controller-manager) y worker nodes (kubelet, kube-proxy, runtime); flujo de un Pod, puntos de fallo y cuellos de botella. |
| **Procedencia** | Kubernetes 1.30 — Components (docs) §components · recuperado 2026-09-27 |
| **Versión** | Kubernetes 1.30 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 7 min |

## TL;DR
Kubernetes separa control plane (apiserver + etcd + scheduler + controller-manager) de worker nodes (kubelet + kube-proxy + runtime). Toda interacción pasa por el apiserver; etcd es la única fuente de verdad. {src:blk_a00000000030}

{layer:l2}

## Vista general
Kubernetes es un orquestador de containers con arquitectura de 2 niveles: control plane (toma decisiones globales) y worker nodes (ejecutan Pods). El componente central es `kube-apiserver` que expone la API REST y persiste el estado en `etcd`. Los nodos ejecutan `kubelet` que reporta capacidad y arranca Pods vía el container runtime (`containerd`, `cri-o`). {src:blk_a00000000031}

:::diagram
```mermaid
flowchart LR
    U[kubectl] -->|HTTPS| A[kube-apiserver]
    A --> E[(etcd)]
    A --> S[kube-scheduler]
    A --> CM[kube-controller-manager]
    CM --> A
    S --> A
    A -->|watch| K1[kubelet node-1]
    A -->|watch| K2[kubelet node-2]
    K1 --> CR1[containerd]
    K2 --> CR2[containerd]
    K1 --> P1[kube-proxy]
    K2 --> P2[kube-proxy]
```
:::

## Componentes y responsabilidades
| Componente | Responsabilidad | Ubicación |
|---|---|---|
| `kube-apiserver` | API REST que valida y persiste el estado del cluster en etcd | pod estático en control plane |
| `etcd` | Key-value store distribuido; única fuente de verdad del cluster | pod estático (3 réplicas para HA) |
| `kube-scheduler` | Asigna cada Pod nuevo a un nodo según recursos, afinidad, taints | pod del control plane |
| `kube-controller-manager` | Ejecuta los controllers (Deployment, ReplicaSet, Node, Endpoint, etc.) | pod del control plane |
| `kubelet` | Agente en cada nodo; arranca Pods, reporta estado al apiserver | proceso en cada worker node |
| `kube-proxy` | Mantiene reglas iptables/IPVS para que los Services enruten tráfico | proceso en cada worker node |

## Flujo paso a paso

### Paso 1: kubectl aplica el manifest
El usuario ejecuta `kubectl apply -f pod.yaml`; el cliente envía un POST al apiserver con el YAML convertido a JSON. {src:blk_a00000000032}

### Paso 2: Apiserver valida y persiste
El apiserver autentica, autoriza (RBAC), ejecuta los admission webhooks, valida con el schema OpenAPI y escribe en etcd con un watch event. {src:blk_a00000000033}

### Paso 3: Scheduler decide el nodo
El scheduler ve el nuevo Pod (no asignado) y elige un nodo según recursos disponibles, afinidad, taints/tolerations. Marca el Pod con `spec.nodeName` via apiserver. {src:blk_a00000000034}

### Paso 4: Kubelet arranca el Pod
El kubelet del nodo elegido detecta que le asignaron un Pod, llama al container runtime (containerd) para pull la imagen y crear el container con los namespaces/cgroups. Reporta el estado al apiserver. {src:blk_a00000000035}

:::diagram
```mermaid
sequenceDiagram
    participant U as kubectl
    participant A as apiserver
    participant E as etcd
    participant S as scheduler
    participant K as kubelet
    participant CR as containerd
    U->>A: POST /pods
    A->>E: persist Pod
    A->>S: watch: new Pod unassigned
    S->>A: PATCH nodeName
    A->>E: persist assignment
    A->>K: watch: my Pod
    K->>CR: pull image + runc create
    CR-->>K: container started
    K->>A: PATCH status.running
    A->>E: persist status
```
:::

## Interacciones

| Origen | Destino | Protocolo | Frecuencia |
|---|---|---|---|
| kubectl ↔ apiserver | HTTPS/6443 | REST + autenticación (cert o token) | por comando |
| apiserver ↔ etcd | gRPC | protocolo etcd v3 | por escritura |
| scheduler → apiserver | HTTPS | REST | continuo (loop) |
| kubelet → apiserver | HTTPS | REST + heartbeats cada 10s | continuo |
| kubelet → containerd | UNIX socket | CRI gRPC | por Pod |

## Estructuras en memoria y disco

### En memoria
| Estructura | Tamaño típico | Vida |
|---|---|---|
| `apiserver` heap | 1-4 GB (`--max-open-connections`) | persistente |
| `etcd` WAL en memoria | 8 GB (`--quota-backend-bytes`) | persistente |
| `kubelet` Pod cache | bytes × pods en el nodo | volátil |
| `kube-proxy` iptables rules | 10k-100k reglas según Services | volátil |

### En disco
| Archivo | Tamaño típico | Rotación |
|---|---|---|
| etcd data dir (`/var/lib/etcd`) | 8 GB máximo (`--quota-backend-bytes`) | compactación automática |
| etcd WAL (`Member WAL`) | 8 GB máximo | snapshot periódico |
| Container logs (`/var/log/pods/`) | 10 MB por Pod | rotación por kubelet |

## Puntos de fallo

:::danger
**etcd pierde quorum → cluster caído.** etcd requiere mayoría simple (2 de 3 réplicas); si 2 réplicas caen, el cluster se vuelve read-only. {src:blk_a00000000036} Mitigación: 3 réplicas en hosts diferentes; `etcdctl snapshot save` diario off-cluster.
:::

:::warning
**apiserver saturado por requests → latencia global.** El apiserver serializa escrituras; un cliente que hace miles de `kubectl get` puede degradar a todo el cluster. {src:blk_a00000000037} Mitigación: `--max-requests-inflight=2000` + `--max-mutating-requests-inflight=1000`; `PriorityLevelConfiguration` para rate-limit por namespace.
:::

:::warning
**kubelet pierde conectividad con apiserver.** El nodo reporta `NotReady` y los Pods siguen corriendo pero no se reasignan. {src:blk_a00000000038} Mitigación: lease de kubelet permite 40s sin reportar; alertas en `node Ready` flips.
:::

:::warning
**Scheduler backlog alto → Pods pendientes minutos.** Con 10k Pods y un scheduler de 1 réplica, los Pods pueden esperar > 5 min. {src:blk_a00000000039} Mitigación: scheduler con `percentageOfNodesToScore=50`; scheduler profile con `plugin configs` paralelos.
:::

:::warning
**Container runtime (containerd) down → nodo entero.** Si containerd crashea, todos los Pods del nodo entran en `NotReady`. {src:blk_a00000000040} Mitigación: `systemd` watchdog reinicia containerd; `runsc`/`kata` como runtime alternativo más aislado.
:::

## Cuellos de botella

:::warning
**Apiserver: serialización de escrituras.** ~1000 writes/s por apiserver; cada write requiere consenso en etcd (~10ms). Métrica: `apiserver_request_duration_seconds{verb=POST}`. Mitigación: HA con 3 apiserver detrás de LB; sharding por `--etcd-servers` separados.
:::

:::warning
**etcd: latencia del fsync.** Cada write a etcd requiere fsync (~1-10ms en SSD). Métrica: `etcd_disk_wal_fsync_duration_seconds`. Mitigación: SSD NVMe dedicado; `--quota-backend-bytes` para compactar agresivamente.
:::

:::warning
**kube-proxy: número de Services.** iptables escala a 10k Services; > 50k degrada el plano de datos. Métrica: `iptables-save | wc -l`. Mitigación: IPVS mode (`--proxy-mode=ipvs`); Cilium con eBPF.
:::

## Decisiones de diseño

:::note
**API declarativa.** El usuario declara el estado deseado; los controllers reconcilian; trade-off: latencia entre estado declarado y real.
:::

:::note
**etcd como única fuente de verdad.** Consistencia fuerte vía Raft; trade-off: scalability limitada por latencia de fsync.
:::

## Backlinks
La arquitectura de Kubernetes se complementa con el ciclo de vida del Pod, los recursos y los errores típicos del scheduler; los enlaces muestran los 3 ángulos. {src:blk_a00000000061}

- [[note:k8s-pod-resources]] — recursos que el scheduler evalúa.
- [[note:k8s-pod-lifecycle]] — fases del Pod que kubelet coordina.
- [[note:k8s-pod-pending-errors]] — confundibles: errores del scheduler/kubelet.
"""


# ---------------------------------------------------------------------------
# Fixture 3 — Docker 25 architecture
# ---------------------------------------------------------------------------

DOCKER_ARCHITECTURE = """---
title: "Docker Engine 25 — arquitectura interna"
note-type: architecture
status: draft
summary: "Arquitectura de Docker Engine 25: dockerd (REST API + state), containerd (gRPC daemon), runc (OCI runtime), shim (lifecycle por container), kernel namespaces/cgroups; flujo de docker run, puntos de fallo y cuellos de botella."
tags: [type/architecture, domain/containers, product/docker]
source: "Docker 25 — Architecture"
source-type: docs
source-anchor: "architecture"
retrieved: 2026-09-27
vendor: Docker
product: Docker Engine
product-version: "25"
related: "[[note:docker-cli-bundle]], [[note:docker-permission-errors]], [[note:docker-rootless]]"
---

# Docker Engine 25 — arquitectura interna

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Arquitectura de Docker Engine 25: dockerd (REST API + state), containerd (gRPC daemon), runc (OCI runtime), shim (lifecycle por container), kernel namespaces/cgroups; flujo de docker run, puntos de fallo y cuellos de botella. |
| **Procedencia** | Docker 25 — Architecture (docs) §architecture · recuperado 2026-09-27 |
| **Versión** | Docker Engine 25 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 5 min |

## TL;DR
Docker Engine se compone de dockerd (API REST), containerd (gRPC daemon), runc (OCI runtime) y containerd-shim (parent de cada container). Los containers usan kernel namespaces (PID, NET, MNT) y cgroups (CPU, MEM, BLKIO). {src:blk_a00000000050}

{layer:l2}

## Vista general
Docker Engine sigue el patrón daemon + shim: `dockerd` recibe comandos REST del CLI y los traduce a llamadas gRPC a `containerd`. `containerd` gestiona el ciclo de vida de los containers y delega la creación real al binario `runc`, que usa las primitives del kernel Linux (namespaces, cgroups, seccomp, capabilities). Cada container tiene un proceso `containerd-shim` como parent, lo que permite a `containerd` reiniciarse sin matar los containers. {src:blk_a00000000051}

:::diagram
```mermaid
flowchart LR
    CLI[docker CLI] -->|REST Unix socket| D[dockerd]
    D -->|gRPC| CT[containerd]
    CT -->|fork+exec| R[runc]
    R --> NS[Linux namespaces: PID, NET, MNT, UTS, IPC]
    R --> CG[cgroups v2: CPU, MEM, BLKIO]
    CT --> SH[containerd-shim]
    SH --> CT1[container 1]
    SH --> CT2[container 2]
```
:::

## Componentes y responsabilidades
| Componente | Responsabilidad | Ubicación |
|---|---|---|
| `dockerd` | Daemon REST API; gestiona imágenes, redes, volúmenes y supervisa containers | proceso Unix; socket `/var/run/docker.sock` |
| `containerd` | Daemon gRPC que gestiona el ciclo de vida de containers e imágenes OCI | proceso Unix; socket `/run/containerd/containerd.sock` |
| `runc` | Binario OCI runtime que crea el container usando namespaces y cgroups | binario en PATH |
| `containerd-shim` | Proceso parent de cada container; permite que containerd reinicie sin matar containers | proceso por container |
| `Linux kernel` | Aísla containers con namespaces (PID, NET, MNT, UTS, IPC, USER) y limita recursos con cgroups v2 | kernel Linux 5.x+ |

## Flujo paso a paso

### Paso 1: CLI envía comando
`docker run alpine echo hola` → el CLI envía `POST /containers/create` al socket de dockerd con la imagen y el comando. {src:blk_a00000000052}

### Paso 2: dockerd traduce a gRPC
dockerd valida, gestiona el pull de la imagen y llama a containerd vía gRPC con la spec del container. {src:blk_a00000000053}

### Paso 3: containerd invoca runc
containerd hace `fork+exec` de `runc` pasando la spec OCI (namespaces, cgroups, mounts, capabilities). runc configura los namespaces con `clone()`, monta los cgroups, y hace `execve()` del comando. {src:blk_a00000000054}

### Paso 4: shim supervisa el container
runc termina tras `execve()`; el container queda bajo `containerd-shim`, que reenvía stdio y permite a containerd reiniciar sin afectar containers existentes. {src:blk_a00000000055}

:::diagram
```mermaid
sequenceDiagram
    participant CLI as docker CLI
    participant D as dockerd
    participant CT as containerd
    participant R as runc
    participant SH as shim
    participant K as Kernel
    CLI->>D: POST /containers/create (REST)
    D->>CT: CreateContainer (gRPC)
    CT->>R: fork+exec (OCI spec)
    R->>K: clone(NEWNS|NEWPID|NEWNET)
    R->>K: write cgroups
    R->>K: execve(echo hola)
    R-->>SH: containerd-shim becomes parent
    SH-->>CT: ready
    CT-->>D: container ID
    D-->>CLI: 201 Created
```
:::

## Interacciones

| Origen | Destino | Protocolo | Frecuencia |
|---|---|---|---|
| CLI → dockerd | UNIX socket | REST/HTTP | por comando |
| dockerd → containerd | UNIX socket | gRPC | por container |
| containerd → runc | stdin/stdout | OCI bundle JSON | una vez por container |
| runc → kernel | syscalls | namespaces + cgroups | continuo |

## Estructuras en memoria y disco

### En memoria
| Estructura | Tamaño típico | Vida |
|---|---|---|
| `dockerd` Go heap | 100-500 MB según nº de containers | persistente |
| `containerd` Go heap | 50-200 MB | persistente |
| `containerd-shim` RSS | 10-30 MB por shim | volátil |
| `cgroups` del kernel | bytes × containers | volátil |

### En disco
| Archivo | Tamaño típico | Rotación |
|---|---|---|
| `/var/lib/docker/overlay2/<id>` | GB según imagen | hasta `docker image prune` |
| `/var/lib/docker/containers/<id>/` | logs + metadata | hasta `docker rm` |
| `/var/run/docker.sock` | socket UNIX | volátil |

## Puntos de fallo

:::danger
**dockerd caído → CLI no responde.** Si dockerd crashea, todos los comandos `docker` fallan; los containers siguen corriendo bajo containerd-shim. {src:blk_a00000000056} Mitigación: `systemd` watchdog reinicia dockerd; usar `nerdctl` (CLI directo a containerd) como bypass.
:::

:::warning
**containerd no disponible → no se pueden crear containers nuevos.** Containers existentes siguen corriendo bajo shim. {src:blk_a00000000057} Mitigación: `systemd` watchdog; alertas con `crictl ps` periódico.
:::

:::warning
**runc falla por namespace ya usado.** Si el mismo PID namespace está activo en otro container, runc retorna error. {src:blk_a00000000058} Mitigación: usar `host` network solo cuando sea explícito; nunca `--pid=host` salvo debugging.
:::

:::warning
**OOM killer mata un container por exceso de cgroup memory.** El container termina con SIGKILL sin warning previo. {src:blk_a00000000059} Mitigación: `--memory` y `--memory-swap` límites; alertas con `docker events --filter type=oom`.
:::

## Cuellos de botella

:::warning
**I/O en overlay2 layer.** Pull de imágenes grandes (~1 GB) puede tardar 30s en SSD; lectura/escritura de containers con bind-mounts sufre latencia del filesystem. Métrica: `iostat -x` sobre el device del docker dir. Mitigación: `--storage-driver=vfs` (overhead); imágenes multi-stage.
:::

:::warning
**Número de containers por host.** > 200 containers por host degrada dockerd (cada container = 1 shim). Métrica: `docker ps -q | wc -l`. Mitigación: sharding con Docker Swarm o Kubernetes.
:::

:::warning
**Network namespaces saturados.** Cada container con `--net=bridge` crea un par veth; > 1000 containers agotan las IDs de netns. Métrica: `ip netns list | wc -l`. Mitigación: CNI con IPAM compartido (Calico, Cilium).
:::

## Decisiones de diseño

:::note
**Daemon + shim.** Cada container tiene un shim parent; trade-off: +10 MB RSS por shim, pero containerd puede reiniciar sin matar containers.
:::

:::note
**Namespaces + cgroups (no VMs).** Containers son procesos Linux aislados; trade-off: aislamiento más débil que VMs, pero arranque en ms.
:::

## Backlinks
La arquitectura de Docker Engine se complementa con los subcomandos CLI, los errores de permisos del socket y la alternativa rootless; los enlaces muestran los 3 ángulos. {src:blk_a00000000062}

- [[note:docker-cli-bundle]] — los 15 subcomandos que orquestan esta arquitectura.
- [[note:docker-permission-errors]] — confundibles: errores típicos del socket.
- [[note:docker-rootless]] — alternativa sin daemon root.
"""


# ---------------------------------------------------------------------------
# Lógica de generación
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    """Escribe el archivo, inyectando {src:} en `:::` y code blocks sin ancla."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = content.splitlines()
    src_counter = 0

    # 1) Marcar `:::` huérfanos y líneas `### Paso N:` (sin src) y párrafos fácticos.
    fixed_lines = []
    in_section = None
    for line in lines:
        stripped = line.strip()
        if line.startswith("## "):
            in_section = stripped
        if stripped == ":::" and "{src:" not in line:
            src_counter += 1
            line = f"::: {{src:blk_bbccddee{src_counter:04x}}}"
        elif (stripped.startswith("### Paso") or stripped.startswith("**Verificación:**")) and "{src:" not in line:
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

    # 3) Añadir {src:} a párrafos fácticos sin src en secciones Vista general / Causa raíz / Componentes / Flujo / Interacciones / Estructuras / Puntos de fallo / Cuellos de botella / Decisiones.
    enriched = []
    extra_counter = 0
    for line in final_lines:
        stripped = line.strip()
        if (
            "{src:" not in line
            and in_section in (
                "## Vista general",
                "## Componentes y responsabilidades",
                "## Flujo paso a paso",
                "## Interacciones",
                "## Estructuras en memoria y disco",
                "## Puntos de fallo",
                "## Cuellos de botella",
                "## Decisiones de diseño",
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
            line = f"{line} {{src:blk_eeeeff{extra_counter:04x}}}"
        enriched.append(line)

    path.write_text("\n".join(enriched) + "\n", encoding="utf-8")


def build() -> None:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    _write(NOTES_DIR / "postgresql-architecture.md", POSTGRES_ARCHITECTURE)
    _write(NOTES_DIR / "kubernetes-architecture.md", KUBERNETES_ARCHITECTURE)
    _write(NOTES_DIR / "docker-architecture.md", DOCKER_ARCHITECTURE)


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
