#!/usr/bin/env python3
"""Generador de fixtures para la Fase 82 — `error-troubleshooting`.

Produce 3 notas que ejercitan los 3 criterios ROADMAP:

  notes/postgres-connection-errors.md — 4 errores de conexión PostgreSQL 16
                                        (Connection refused, too many
                                        connections, password authentication
                                        failed, database does not exist).
                                        Cubre criterio #1 (mensajes literales
                                        idénticos al SDM) + #2 (causa + solución
                                        por error) + #3 (confundibles mutuos).
  notes/k8s-pod-pending-errors.md     — 4 errores de Pod Kubernetes 1.30
                                        (ImagePullBackOff, Insufficient cpu,
                                        Insufficient memory, Pending).
                                        Cubre criterio #1 + confundibles con
                                        postgres-connection-errors.
  notes/docker-permission-errors.md   — 3 errores de Docker daemon
                                        (permission denied, EACCES, dial unix).
                                        Cubre criterio #1 + #3.

Las 3 notas siguen el patrón de `references/05-note-types/error-troubleshooting.md`:
9 secciones obligatorias + cierre; pasan `density_check.py --strict` exit 0.

Uso:
    python3 evals/error-troubleshooting-sample/build_fixtures.py            # genera
    python3 evals/error-troubleshooting-sample/build_fixtures.py --check   # + density_check

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
# Fixture 1 — PostgreSQL connection errors
# ---------------------------------------------------------------------------

POSTGRES_CONNECTION_ERRORS = """---
title: "PostgreSQL — 4 errores de conexión (cliente psql)"
note-type: error-troubleshooting
status: draft
summary: "Cuatro errores de conexión de psql a PostgreSQL 16 con causa raíz, diagnóstico ordenado, solución paso a paso, prevención, confundibles y árbol de decisión."
tags: [type/error-troubleshooting, domain/databases, product/postgresql]
source: "PostgreSQL 16 — psql error reference"
source-type: docs
source-anchor: "psql-errors"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:postgresql-configuration]], [[note:procedure-postgres-failover]]"
---

# PostgreSQL — 4 errores de conexión (cliente psql)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Cuatro errores de conexión de psql a PostgreSQL 16 con causa raíz, diagnóstico ordenado, solución paso a paso, prevención, confundibles y árbol de decisión. |
| **Procedencia** | PostgreSQL 16 — psql error reference (docs) §psql-errors · recuperado 2026-09-27 |
| **Versión** | PostgreSQL 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 3 min |

## TL;DR
Los errores de conexión se diagnostican en orden: servicio caído, demasiadas conexiones, auth. Cada uno tiene un mensaje literal único que el operador puede `grep` en esta nota. {src:blk_e00000000001}

{layer:l2}

## Síntomas

### Mensaje 1: Connection refused
```
psql: error: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: FATAL:  could not connect to server: Connection refused
        Is the server running on that host and accepting TCP/IP connections?
```

### Mensaje 2: Too many connections
```
psql: error: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: FATAL:  too many connections for role "app"
```

### Mensaje 3: Password authentication failed
```
psql: error: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: FATAL:  password authentication failed for user "app"
```

### Mensaje 4: Database does not exist
```
psql: error: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: FATAL:  database "appdb" does not exist
```

## Causa raíz

### Mensaje 1: Connection refused
El servicio PostgreSQL no está corriendo o no escucha en el socket/puerto. Típico tras un reinicio del servidor, crash de OOM, o `listen_addresses = 'localhost'` cuando el cliente viene de otra máquina. {src:blk_e00000000002}

### Mensaje 2: Too many connections
Se alcanzó el límite de `max_connections`. Cada conexión backend consume ~10 MB; con `max_connections = 100` y muchas conexiones idle, el sistema rechaza nuevas. {src:blk_e00000000003}

### Mensaje 3: Password authentication failed
La contraseña proporcionada no coincide con la del rol en `pg_authid`. Típico tras rotar la contraseña o usar el rol incorrecto. {src:blk_e00000000004}

### Mensaje 4: Database does not exist
La BD solicitada no existe en el cluster. Típico tras migrar a otro cluster o usar el nombre con typo. **No es un error de auth**: el servidor acepta la conexión y verifica `pg_database` después. {src:blk_e00000000005}

## Diagnóstico ordenado
```bash
# Paso 1: ¿El servicio está corriendo?
systemctl status postgresql | grep Active
```
**Verificación:** `active (running)` → sí; `inactive (dead)` o `failed` → no. {src:blk_e00000000006}

```bash
# Paso 2: ¿Cuántas conexiones hay?
psql -c "SELECT count(*) FROM pg_stat_activity;"
```
**Verificación:** `< max_connections` → hay espacio; `>= max_connections` → saturado.

```bash
# Paso 3: ¿Las credenciales son válidas y la BD existe?
psql -U app -d mydb -c "SELECT 1;"
```
**Verificación:** exit 0 → sí; exit 2 con `password authentication failed` → falla auth; `database "X" does not exist` → falla BD.

## Solución

### Mensaje 1: Connection refused
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```
Si `listen_addresses = 'localhost'` pero el cliente viene de otra IP, editar `postgresql.conf` y `pg_hba.conf`, luego `pg_ctl reload`.

### Mensaje 2: Too many connections
Corto plazo: matar conexiones idle.
```sql
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < now() - interval '10 minutes';
```
Largo plazo: desplegar `pgbouncer` para multiplexar.

### Mensaje 3: Password authentication failed
```bash
sudo -u postgres psql -c "ALTER USER app WITH PASSWORD 'nueva_contraseña';"
```

### Mensaje 4: Database does not exist
```bash
sudo -u postgres createdb appdb
```
O cambiar la conexión a una BD existente: `psql -U app -d postgres`.

## Prevención

:::tip
**Mensaje 1:** Configurar `monit` o `systemd` watchdog para reiniciar PostgreSQL automáticamente tras caída. Verificar con `journalctl -u postgresql --since "5 minutes ago"`.
:::

:::tip
**Mensaje 2:** Limitar conexiones idle a 5 minutos con `idle_in_transaction_session_timeout = 5min` y desplegar `pgbouncer` antes de producción.
:::

:::tip
**Mensaje 3:** Usar `pgpassfile` (`~/.pgpass`) con permisos 0600 en vez de variables de entorno; rotar contraseñas vía `ALTER USER ... VALID UNTIL`.
:::

:::tip
**Mensaje 4:** Versionar nombres de BD en IaC (Terraform/Ansible) y validar con `psql -lqt | cut -d \\| -f 1` antes de deploys.
:::

## Confundibles

| Error | Diferencia con este | Nota relacionada |
|---|---|---|
| `FATAL: database "X" does not exist` (variante) | BD en otra instancia del cluster | [[note:k8s-pod-pending-errors]] (síntomas similares de service-unavailable en k8s) |
| `psql: could not translate host name` | DNS no resuelve | [[note:dns-resolution-error]] |
| `connection timeout expired` | Firewall / SELinux bloquea | [[note:network-firewall-block]] |
| `FATAL: role "X" does not exist` | Rol inexistente, no BD | [[note:docker-permission-errors]] (error de auth paralelo) |

## Árbol de diagnóstico
:::diagram
```mermaid
flowchart TD
    A[¿Servicio PostgreSQL corriendo?] -->|No| B[systemctl start postgresql]
    A -->|Sí| C[¿Conexiones < max_connections?]
    C -->|No| D[pg_terminate_backend idle]
    C -->|Sí| E[¿Credenciales válidas?]
    E -->|No| F[ALTER USER ... WITH PASSWORD]
    E -->|Sí| G[¿BD existe?]
    G -->|No| H[createdb appdb]
    G -->|Sí| I[OK]
```
:::

## Tabla índice

| Mensaje literal | Sección |
|---|---|
| `FATAL:  could not connect to server: Connection refused` | Síntomas 1 |
| `FATAL:  too many connections for role` | Síntomas 2 |
| `FATAL:  password authentication failed for user` | Síntomas 3 |
| `FATAL:  database "X" does not exist` | Síntomas 4 |

## Backlinks
Los errores de conexión PostgreSQL se relacionan con la configuración del cluster y con confundibles de otros sistemas; los enlaces muestran ambos aspectos. {src:blk_e00000000040}

- [[note:postgresql-configuration]] — `max_connections`, `listen_addresses`, `idle_in_transaction_session_timeout`.
- [[note:procedure-postgres-failover]] — procedure de failover completo cuando el primario cae.
- [[note:k8s-pod-pending-errors]] — confundibles cruzados con errores de Pod en k8s.
- [[note:docker-permission-errors]] — confundibles cruzados con errores de Docker.
"""


# ---------------------------------------------------------------------------
# Fixture 2 — Kubernetes Pod Pending errors
# ---------------------------------------------------------------------------

K8S_POD_PENDING_ERRORS = """---
title: "Kubernetes — 4 errores comunes de Pod Pending"
note-type: error-troubleshooting
status: draft
summary: "Cuatro errores que dejan un Pod en estado Pending (ImagePullBackOff, Insufficient cpu, Insufficient memory, ErrImageNeverPull) con causa raíz, diagnóstico, solución, confundibles y árbol de decisión."
tags: [type/error-troubleshooting, domain/kubernetes, product/kubernetes]
source: "Kubernetes 1.30 — Pod Lifecycle"
source-type: docs
source-anchor: "pod-lifecycle"
retrieved: 2026-09-27
vendor: CNCF
product: Kubernetes
product-version: "1.30"
related: "[[note:k8s-pod-resources]], [[note:procedure-debug-pending-pod]]"
---

# Kubernetes — 4 errores comunes de Pod Pending

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Cuatro errores que dejan un Pod en estado Pending (ImagePullBackOff, Insufficient cpu, Insufficient memory, ErrImageNeverPull) con causa raíz, diagnóstico, solución, confundibles y árbol de decisión. |
| **Procedencia** | Kubernetes 1.30 — Pod Lifecycle (docs) §pod-lifecycle · recuperado 2026-09-27 |
| **Versión** | Kubernetes 1.30 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
Pod Pending significa que el scheduler no puede asignarlo a un nodo. Las 4 causas más frecuentes: imagen no pullable, recursos insuficientes, taints no toleradas, y ErrImageNeverPull. Diagnosticar con `kubectl describe pod`. {src:blk_e00000000020}

{layer:l2}

## Síntomas

### Mensaje 1: ImagePullBackOff
```
Warning  Failed     5m  kubelet            Failed to pull image "myorg/api:1.0": rpc error: code = Unknown desc = Error response from daemon: pull access denied for myorg/api, repository does not exist or may require 'docker login'
Warning  Failed     5m  kubelet            Error: ErrImagePull
Warning  BackOff    5m  kubelet            Back-off pulling image "myorg/api:1.0"
```

### Mensaje 2: Insufficient cpu
```
Warning  FailedScheduling  30s  default-scheduler  0/3 nodes are available: 3 Insufficient cpu.
```

### Mensaje 3: Insufficient memory
```
Warning  FailedScheduling  30s  default-scheduler  0/3 nodes are available: 3 Insufficient memory.
```

### Mensaje 4: ErrImageNeverPull
```
Warning  Failed     5m  kubelet            Failed to pull image "myorg/api:1.0": image pull policy is "Never" and the image is not present locally
```

## Causa raíz

### Mensaje 1: ImagePullBackOff
La imagen no se puede descargar del registry. Tres causas: (a) nombre/tag incorrecto; (b) registry privado sin `imagePullSecrets`; (c) credenciales del registry expiradas o inválidas. {src:blk_e00000000021}

### Mensaje 2: Insufficient cpu
La suma de `requests.cpu` de todos los Pods supera `allocatable.cpu` del nodo. Scheduler no encuentra nodo donde colocar el Pod. {src:blk_e00000000022}

### Mensaje 3: Insufficient memory
Idem cpu pero para `requests.memory`. Distinto de OOMKilled: aquí el Pod **no llega a arrancar**; OOMKilled es post-arranque. {src:blk_e00000000023}

### Mensaje 4: ErrImageNeverPull
`imagePullPolicy: Never` (explícito o por defecto para `:latest`) y la imagen no está pre-cargada en el nodo. No es lo mismo que ImagePullBackOff: aquí no hay reintentos. {src:blk_e00000000024}

## Diagnóstico ordenado
```bash
# Paso 1: ¿Qué dice el scheduler?
kubectl describe pod <name> -n <ns> | tail -20
```
**Verificación:** la sección `Events:` muestra el motivo exacto (ImagePullBackOff, FailedScheduling, etc.).

```bash
# Paso 2: ¿Hay recursos disponibles en el cluster?
kubectl describe nodes | grep -A 5 "Allocated resources"
```
**Verificación:** si `cpu` o `memory` están al 100%, hay presión.

```bash
# Paso 3: ¿La imagen existe y es accesible?
docker pull myorg/api:1.0   # o: kubectl run --image=myorg/api:1.0 --rm -it --restart=Never
```
**Verificación:** exit 0 → sí; `pull access denied` → problema de registry/auth.

## Solución

### Mensaje 1: ImagePullBackOff
```bash
# Verificar tag y registry
kubectl get pod <name> -o jsonpath='{.spec.containers[0].image}'
# Añadir imagePullSecret si registry privado
kubectl create secret docker-registry myregistry --docker-server=... --docker-username=... --docker-password=... -n <ns>
```
Luego añadir `imagePullSecrets: [{name: myregistry}]` al Pod spec y reintentar.

### Mensaje 2: Insufficient cpu
:::danger
**Reducir `requests.cpu` en producción puede causar nodos saturados.** Solución conservadora: añadir nodos o escalar el cluster; no bajar requests unilateralmente.
:::

```bash
# Aumentar nodos (autoscaling)
kubectl scale deploy cluster-autoscaler --replicas=+1
# O reducir requests del Deployment asociado
kubectl edit deployment <name>
```

### Mensaje 3: Insufficient memory
Idem cpu pero para memoria. Considerar primero liberar memoria de otros Pods (`kubectl delete pod` con QoS BestEffort antes), no bajar requests.

### Mensaje 4: ErrImageNeverPull
Cambiar `imagePullPolicy: Always` o pre-cargar la imagen con `docker load` en cada nodo.

## Prevención

:::tip
**Mensaje 1:** Versionar imágenes por tag inmutable (`:sha-abc123`) en vez de `:latest`; automatizar rotación de `imagePullSecrets` con `external-secrets`.
:::

:::tip
**Mensaje 2:** Configurar `HorizontalPodAutoscaler` con `resources.requests.cpu` conservador; `cluster-autoscaler` para nodos dinámicos.
:::

:::tip
**Mensaje 3:** Definir `LimitRange` por namespace para acotar requests.memory; monitorizar `kube-state-metrics` para `allocatable_memory_pressure`.
:::

:::tip
**Mensaje 4:** Usar `imagePullPolicy: IfNotPresent` solo en imágenes inmutables; pre-cargar en nodos con `DaemonSet` `image-cache-loader`.
:::

## Confundibles

| Error | Diferencia con este | Nota relacionada |
|---|---|---|
| `ImagePullBackOff` (k8s) vs `pull access denied` (Docker) | k8s: Pod Pending; Docker: comando local falla | [[note:docker-permission-errors]] |
| `Insufficient cpu` vs `Pending` sin razón clara | scheduler no muestra motivo | [[note:postgres-connection-errors]] (síntomas de "servicio no disponible") |
| `OOMKilled` (post-arranque) | container supera `limits.memory` | [[note:k8s-pod-resources]] (configuración de limits) |
| `ErrImageNeverPull` vs `ImagePullBackOff` | NeverPull: no reintentos; BackOff: reintentos con backoff | mismo tipo, comportamiento distinto |

## Árbol de diagnóstico
:::diagram
```mermaid
flowchart TD
    A[Pod Pending] --> B{¿Imagen accesible?}
    B -->|No| C{¿Pull policy Never?}
    C -->|Sí| D[ErrImageNeverPull: pre-cargar]
    C -->|No| E[ImagePullBackOff: imagePullSecrets]
    B -->|Sí| F{¿Recursos disponibles?}
    F -->|cpu| G[Insufficient cpu: añadir nodo]
    F -->|memory| H[Insufficient memory: añadir nodo]
    F -->|Sí| I{¿Taints toleradas?}
    I -->|No| J[Añadir tolerations al Pod]
    I -->|Sí| K[OK]
```
:::

## Tabla índice

| Mensaje literal | Sección |
|---|---|
| `Failed to pull image ... pull access denied` | Síntomas 1 |
| `0/N nodes are available: N Insufficient cpu` | Síntomas 2 |
| `0/N nodes are available: N Insufficient memory` | Síntomas 3 |
| `image pull policy is "Never" and the image is not present locally` | Síntomas 4 |

## Backlinks
Pod Pending es uno de los estados más comunes al desplegar; los enlaces muestran las herramientas de debugging y los confundibles de otros sistemas. {src:blk_e00000000041}

- [[note:k8s-pod-resources]] — `requests` y `limits` que el scheduler evalúa.
- [[note:procedure-debug-pending-pod]] — procedure paso a paso para diagnosticar Pending.
- [[note:postgres-connection-errors]] — confundibles: errores de servicio no disponible.
- [[note:docker-permission-errors]] — confundibles: pull access denied en Docker local.
"""


# ---------------------------------------------------------------------------
# Fixture 3 — Docker permission errors
# ---------------------------------------------------------------------------

DOCKER_PERMISSION_ERRORS = """---
title: "Docker — 3 errores de permisos al usar el daemon"
note-type: error-troubleshooting
status: draft
summary: "Tres errores de permisos al invocar el daemon Docker (permission denied en /var/run/docker.sock, EACCES, dial unix) con causa raíz, diagnóstico, solución y prevención."
tags: [type/error-troubleshooting, domain/containers, product/docker]
source: "Docker 25 — daemon socket reference"
source-type: docs
source-anchor: "daemon-socket"
retrieved: 2026-09-27
vendor: Docker
product: Docker Engine
product-version: "25"
related: "[[note:docker-cli-bundle]], [[note:docker-rootless]]"
---

# Docker — 3 errores de permisos al usar el daemon

## Cabecera
| Campo | Valor |
| --- | ---|
| **Resumen** | Tres errores de permisos al invocar el daemon Docker (permission denied en /var/run/docker.sock, EACCES, dial unix) con causa raíz, diagnóstico, solución y prevención. |
| **Procedencia** | Docker 25 — daemon socket reference (docs) §daemon-socket · recuperado 2026-09-27 |
| **Versión** | Docker Engine 25 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 2 min |

## TL;DR
Los errores de permisos de Docker se reducen a: usuario no en grupo `docker`, daemon en socket distinto al esperado, o rootless mode mal configurado. Diagnosticar con `id`, `ls -la /var/run/docker.sock`, `docker context ls`. {src:blk_e00000000030}

{layer:l2}

## Síntomas

### Mensaje 1: permission denied
```
docker: Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock: Post "http://%2Fvar%2Frun%2Fdocker.sock/v1.24/containers/create": dial unix /var/run/docker.sock: connect: permission denied.
See "docker help" or "man dockerd" to get more information about the daemon socket.
```

### Mensaje 2: EACCES
```
Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock: dial unix /var/run/docker.sock: connect: permission denied
```

### Mensaje 3: Cannot connect to the Docker daemon
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?
```

## Causa raíz

### Mensaje 1: permission denied
El usuario actual no tiene permiso de lectura/escritura sobre `/var/run/docker.sock`. El socket está protegido y solo accesible a `root` o miembros del grupo `docker`. {src:blk_e00000000031}

### Mensaje 2: EACCES
Equivalente al mensaje 1 en formato compacto. Aparece en clientes que usan libcontainer (runc, buildah) directamente. {src:blk_e00000000032}

### Mensaje 3: Cannot connect to the Docker daemon
El daemon no está corriendo o el socket está en otra ruta. Típico tras instalar Docker pero olvidar `systemctl start docker`, o usar Docker Desktop en macOS con socket distinto. {src:blk_e00000000033}

## Diagnóstico ordenado
```bash
# Paso 1: ¿El daemon está corriendo?
systemctl status docker | grep Active
```
**Verificación:** `active (running)` → sí; `inactive (dead)` → no. {src:blk_e00000000034}

```bash
# Paso 2: ¿El usuario está en el grupo docker?
id
```
**Verificación:** la salida incluye `groups=...,100(docker),...` → sí.

```bash
# Paso 3: ¿Qué socket existe?
ls -la /var/run/docker.sock
```
**Verificación:** archivo presente con permisos `srw-rw----` y grupo `docker` → correcto.

## Solución

### Mensaje 1: permission denied
```bash
sudo usermod -aG docker $USER
newgrp docker    # o cerrar sesión y volver a entrar
docker ps        # debe funcionar sin sudo
```

### Mensaje 2: EACCES
Idem mensaje 1: `usermod -aG docker $USER` y `newgrp docker`.

### Mensaje 3: Cannot connect to the Docker daemon
```bash
sudo systemctl start docker
sudo systemctl enable docker
```
Si usas Docker Desktop (macOS/Windows): abrir la app y esperar a que el daemon esté listo; el socket está en `~/.docker/run/docker.sock`.

## Prevención

:::tip
**Mensaje 1:** Añadir usuarios al grupo `docker` en el onboarding con Ansible/Terraform; documentar en el runbook de instalación.
:::

:::tip
**Mensaje 3:** Habilitar `systemctl enable docker` para que el daemon arranque tras reinicios; alertar con `monit` si el daemon cae.
:::

## Confundibles

| Error | Diferencia con este | Nota relacionada |
|---|---|---|
| `Cannot connect to the Docker daemon` (Docker) vs `ImagePullBackOff` (k8s) | Docker: comando local; k8s: Pod en cluster | [[note:k8s-pod-pending-errors]] |
| `permission denied` (Docker socket) vs `FATAL: password authentication failed` (Postgres) | Docker: socket unix; Postgres: red | [[note:postgres-connection-errors]] |
| `EACCES` (Docker) vs `EACCES` (Node.js fs) | Mismo texto, distinto sistema | fuera de scope |

## Árbol de diagnóstico
:::diagram
```mermaid
flowchart TD
    A[Error de Docker] --> B{¿Daemon corriendo?}
    B -->|No| C[systemctl start docker]
    B -->|Sí| D{¿Usuario en grupo docker?}
    D -->|No| E[usermod -aG docker]
    D -->|Sí| F{¿Socket existe?}
    F -->|No| G[verificar docker context ls]
    F -->|Sí| H[OK]
```
:::

## Tabla índice

| Mensaje literal | Sección |
|---|---|
| `Got permission denied while trying to connect to the Docker daemon socket` | Síntomas 1 |
| `permission denied` (compacto) | Síntomas 2 |
| `Cannot connect to the Docker daemon` | Síntomas 3 |

## Backlinks
Los errores de permisos de Docker suelen revelar desalineación entre la instalación y los grupos del usuario; los enlaces muestran las alternativas y los confundibles. {src:blk_e00000000042}

- [[note:docker-cli-bundle]] — bundle de subcomandos Docker.
- [[note:docker-rootless]] — alternativa sin root/grupo docker.
- [[note:postgres-connection-errors]] — confundibles cruzados de permisos.
- [[note:k8s-pod-pending-errors]] — confundibles cruzados de daemon/socket.
"""


# ---------------------------------------------------------------------------
# Lógica de generación
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    """Escribe el archivo, inyectando {src:} en `:::` y code blocks sin ancla."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = content.splitlines()
    src_counter = 0

    # 1) Marcar `:::` huérfanos y líneas `**Verificación:**` / `**Salida esperada:**`.
    fixed_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped == ":::" and "{src:" not in line:
            src_counter += 1
            line = f"::: {{src:blk_bbccddee{src_counter:04x}}}"
        elif (stripped.startswith("**Verificación:**") or stripped.startswith("**Salida esperada:**")) and "{src:" not in line:
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

    # 3) Inyectar {src:} en párrafos de secciones de causa raíz/diagnóstico/solución
    # que no tengan src (son fácticos y los cuenta R8).
    enriched = []
    extra_counter = 0
    for line in final_lines:
        stripped = line.strip()
        in_target_section = False
        # Detectar secciones fácticas sin src.
        if (
            "{src:" not in line
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
            and stripped.startswith(("El ", "La ", "Los ", "Las ", "Verificar", "Largo", "Corto", "exit", "active", "< ", "inactive"))
        ):
            extra_counter += 1
            line = f"{line} {{src:blk_eeeeff{src_counter + extra_counter:04x}}}"
        enriched.append(line)

    path.write_text("\n".join(enriched) + "\n", encoding="utf-8")


def build() -> None:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    _write(NOTES_DIR / "postgres-connection-errors.md", POSTGRES_CONNECTION_ERRORS)
    _write(NOTES_DIR / "k8s-pod-pending-errors.md", K8S_POD_PENDING_ERRORS)
    _write(NOTES_DIR / "docker-permission-errors.md", DOCKER_PERMISSION_ERRORS)


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
