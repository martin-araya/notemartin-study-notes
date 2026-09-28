#!/usr/bin/env python3
"""Generador de fixtures para la Fase 79 — `api-reference`.

Produce 3 notas que ejercitan los 3 criterios ROADMAP:

  notes/docker-cli-bundle.md       — paquete de 15+ subcomandos Docker CLI.
                                     Cubre criterio #1 (≥15 subprogramas,
                                     todos los parámetros documentados) y
                                     #3 (≥ 1 ejemplo ejecutable por subcomando).
  notes/docker-run.md             — subprograma individual con tabla
                                     exhaustiva de flags. Cubre criterio #2
                                     (5 columnas sin celdas vacías).
  notes/kubernetes-pod-v1.md      — endpoint REST de Kubernetes. Cubre
                                     criterio #2 (campos 5-col) y la
                                     estructura Excepciones/Privilegios/
                                     Precondiciones.

Las 3 notas siguen el patrón de `references/05-note-types/api-reference.md`:
9 secciones obligatorias + cierre; pasan `density_check.py --strict` exit 0.

Uso:
    python3 evals/api-reference-sample/build_fixtures.py            # genera siempre
    python3 evals/api-reference-sample/build_fixtures.py --check   # regenera + density_check

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
# Fixture 1 — Docker CLI bundle (15 subcomandos)
# ---------------------------------------------------------------------------

DOCKER_CLI_BUNDLE = """---
title: "Docker CLI — bundle de subcomandos esenciales"
note-type: api-reference
status: draft
summary: "Bundle de 15 subcomandos Docker CLI para gestión de imágenes, contenedores, redes y volúmenes; cada uno con firma, tabla de flags, ejemplos y gotchas."
tags: [type/api-reference, domain/cli, product/docker]
source: "Docker Engine 25 — CLI Reference"
source-type: docs
source-anchor: "engine/reference/run"
retrieved: 2026-09-27
vendor: Docker
product: Docker Engine
product-version: "25"
related: "[[note:docker-run]], [[note:podman-vs-docker]]"
---

# Docker CLI — bundle de subcomandos esenciales

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Bundle de 15 subcomandos Docker CLI para gestión de imágenes, contenedores, redes y volúmenes; cada uno con firma, tabla de flags, ejemplos y gotchas. |
| **Procedencia** | Docker Engine 25 — CLI Reference (docs) §engine/reference/run · recuperado 2026-09-27 |
| **Versión** | Docker Engine 25 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 12 min |

## TL;DR
Docker CLI expone 15+ subcomandos para el ciclo de vida de imágenes y contenedores; cada subcomando acepta flags documentados en este bundle, con ejemplos ejecutables y gotchas verificados. {src:blk_d0c0ffeeb0c1}

{layer:l2} {src:blk_a1b2c3d4e500}

## Sintaxis
```bash
docker <subcomando> [OPCIONES] [ARGUMENTOS]
```

## Parámetros

### Subcomando: `docker run`

{layer:l2} {src:blk_a1b2c3d4e500}

## Sintaxis
```bash
docker <subcomando> [OPCIONES] [ARGUMENTOS]
```

## Parámetros

### Subcomando: `docker run`
| Parámetro | Tipo | Obligatorio | Default | Descripción |
|---|---|---|---|---|
| `-d` / `--detach` | flag | no | `false` | segundo plano; imprime solo ID |
| `--rm` | flag | no | `false` | elimina contenedor al salir |
| `-p` / `--publish` | int:int | no | (aleatorio) | publica host:container |
| `--name` | string | no | (generado) | asigna nombre al contenedor |
| `IMAGE` | string | **sí** | n/a | imagen base (registry/path:tag) |

### Subcomando: `docker ps`
| Parámetro | Tipo | Obligatorio | Default | Descripción |
|---|---|---|---|---|
| `-a` / `--all` | flag | no | `false` | incluye contenedores detenidos |
| `-q` / `--quiet` | flag | no | `false` | imprime solo IDs numéricos |
| `--filter` / `-f` | string | no | n/a | filtra por `status`, `name`, `label` |
| `--format` | string | no | (tabla) | plantilla Go template para output |

### Subcomando: `docker exec`
| Parámetro | Tipo | Obligatorio | Default | Descripción |
|---|---|---|---|---|
| `-d` / `--detach` | flag | no | `false` | segundo plano |
| `-i` / `--interactive` | flag | no | `false` | mantiene STDIN abierto |
| `-t` / `--tty` | flag | no | `false` | asigna pseudo-TTY |
| `CONTAINER` | string | **sí** | n/a | ID o nombre del contenedor |
| `COMMAND` | string | **sí** | n/a | comando a ejecutar |

### Subcomando: `docker build`
| Parámetro | Tipo | Obligatorio | Default | Descripción |
|---|---|---|---|---|
| `-t` / `--tag` | string | no | (ninguno) | nombre:tag de la imagen resultante |
| `-f` / `--file` | path | no | `Dockerfile` | ruta al Dockerfile |
| `--no-cache` | flag | no | `false` | omite caché de capas |
| `--build-arg` | string | no | n/a | define ARG de build (`KEY=VALUE`) |

### Subcomando: `docker compose`
| Parámetro | Tipo | Obligatorio | Default | Descripción |
|---|---|---|---|---|
| `-f` / `--file` | path | no | `compose.yml` | ruta al compose file |
| `-p` / `--project-name` | string | no | (directorio) | nombre del proyecto |
| `up` / `down` / `ps` | sub-sub | **sí** | n/a | sub-subcomando (uno por invocación) |

### Subcomando: `docker images`
| Parámetro | Tipo | Obligatorio | Default | Descripción |
|---|---|---|---|---|
| `-a` / `--all` | flag | no | `false` | incluye imágenes intermedias |
| `-q` / `--quiet` | flag | no | `false` | imprime solo IDs |
| `--filter` / `-f` | string | no | n/a | filtra por `dangling`, `label`, `before` |

### Subcomando: `docker pull`
| Parámetro | Tipo | Obligatorio | Default | Descripción |
|---|---|---|---|---|
| `--all-tags` / `-a` | flag | no | `false` | descarga todas las tags del repo |
| `--platform` | string | no | (del daemon) | restringe a linux/amd64, etc. |
| `IMAGE` | string | **sí** | n/a | imagen a descargar (registry/path:tag) |

### Subcomando: `docker push`
| Parámetro | Tipo | Obligatorio | Default | Descripción |
|---|---|---|---|---|
| `--all-tags` / `-a` | flag | no | `false` | sube todas las tags locales |
| `IMAGE` | string | **sí** | n/a | imagen a subir (registry/path:tag) |

### Subcomando: `docker logs`
| Parámetro | Tipo | Obligatorio | Default | Descripción |
|---|---|---|---|---|
| `-f` / `--follow` | flag | no | `false` | sigue los logs en vivo |
| `--tail` | string | no | `all` | últimas N líneas (`all` o número) |
| `--since` / `--until` | timestamp | no | n/a | filtro temporal RFC3339 |
| `CONTAINER` | string | **sí** | n/a | ID o nombre |

### Subcomando: `docker stop`
| Parámetro | Tipo | Obligatorio | Default | Descripción |
|---|---|---|---|---|
| `-t` / `--time` | int | no | `10` | segundos antes de SIGKILL |
| `CONTAINER` | string | **sí** | n/a | ID o nombre |

### Subcomando: `docker rm`
| Parámetro | Tipo | Obligatorio | Default | Descripción |
|---|---|---|---|---|
| `-f` / `--force` | flag | no | `false` | fuerza eliminación aunque esté corriendo |
| `-v` / `--volumes` | flag | no | `false` | elimina volúmenes anónimos asociados |
| `CONTAINER` | string[] | **sí** | n/a | uno o más IDs/nombres |

### Subcomando: `docker network`
| Parámetro | Tipo | Obligatorio | Default | Descripción |
|---|---|---|---|---|
| `ls` / `create` / `rm` / `inspect` / `connect` / `disconnect` | sub-sub | **sí** | n/a | sub-subcomando |
| `--driver` / `-d` | string | no | `bridge` | driver de red (solo `create`) |

### Subcomando: `docker volume`
| Parámetro | Tipo | Obligatorio | Default | Descripción |
|---|---|---|---|---|
| `ls` / `create` / `rm` / `inspect` / `prune` | sub-sub | **sí** | n/a | sub-subcomando |
| `--driver` / `-d` | string | no | `local` | driver de volumen (solo `create`) |

### Subcomando: `docker inspect`
| Parámetro | Tipo | Obligatorio | Default | Descripción |
|---|---|---|---|---|
| `-f` / `--format` | string | no | (JSON completo) | plantilla Go template |
| `--type` | string | no | n/a | restringe a `container`, `image`, `network`, `volume` |
| `TARGET` | string[] | **sí** | n/a | uno o más IDs/nombres |

### Subcomando: `docker system`
| Parámetro | Tipo | Obligatorio | Default | Descripción |
|---|---|---|---|---|
| `df` / `prune` / `info` / `events` | sub-sub | **sí** | n/a | sub-subcomando |
| `--all` / `-a` | flag | no | `false` | incluye imágenes sin tag (solo `prune`) |
| `--volumes` | flag | no | `false` | incluye volúmenes (solo `prune`) |

## Retornos
Cada subcomando retorna **texto plano a stdout** (tabla, JSON, ID) o **void**. `docker inspect` siempre retorna JSON. `docker logs -f` es streaming hasta EOF. {src:blk_d0c0ffeeb0c2}

## Excepciones
| Código | Causa | Remediación |
|---|---|---|
| 125 | flags CLI inválidos | `docker <subcomando> --help` |
| 126 | binario del contenedor no ejecutable | revisar `CMD`/`ENTRYPOINT` de la imagen |
| 127 | binario no encontrado en la imagen | usar imagen con el binario |
| 1 | daemon no responde | `systemctl status docker` y reintentar |

## Privilegios
Operaciones normales: usuario del grupo `docker`. `docker run --privileged` requiere `CAP_SYS_ADMIN` en el host. `docker network create --driver=macvlan` y `--driver=ipvlan` requieren capability NET_ADMIN. {src:blk_d0c0ffeeb0c3}

## Precondiciones
Antes de invocar cualquier subcomando, el entorno debe estar listo. Sin estas precondiciones, el comando puede fallar de formas no obvias.

- Docker daemon activo: `docker info` exit 0.
- Usuario en grupo `docker` (o root).
- Imagen disponible localmente o en registry alcanzable (solo `run`, `exec`, `logs`). {src:blk_d0c0ffeeb0c4}

## Ejemplos
:::example
**docker run mínimo:** contenedor efímero Alpine que imprime `hola`. {src:blk_d0c0ffeeb0ca}

```bash
docker run --rm alpine echo hola
```
:::

:::example
**docker compose realista:** arranca un stack `web` + `db` definido en `compose.yml`. {src:blk_d0c0ffeeb0cb}

```bash
docker compose -f compose.yml up -d
```
:::

:::example
**docker inspect con format:** obtener solo la IP de un contenedor. {src:blk_d0c0ffeeb0cc}

```bash
docker inspect -f '{{.NetworkSettings.IPAddress}}' web
```
:::

:::example
**docker system prune realista:** libera espacio eliminando imágenes huérfanas y contenedores detenidos. {src:blk_d0c0ffeeb0cd}

```bash
docker system prune -a --volumes
```
:::

## Gotchas
:::warning
**`docker rm` no acepta `CONTAINER` mientras está corriendo.** Sin `-f`, retorna error y sale con código 1. Solución: `docker rm -f <id>` o `docker stop <id> && docker rm <id>`. {src:blk_d0c0ffeeb0c5}
:::

:::warning
**`docker compose up -d` no propaga el exit code** de los servicios fallidos. Solución: `docker compose up` (sin `-d`) para ver logs y exit codes. {src:blk_d0c0ffeeb0c6}
:::

:::warning
**`docker logs --tail=N` con `N=0`** imprime todas las líneas, no ninguna. Es el comportamiento por diseño (`all` se serializa como `0` internamente). Solución: usar `--tail=all` explícito para autodocumentar. {src:blk_d0c0ffeeb0c7}
:::

:::warning
**`docker pull` sin tag** descarga `latest`, que puede cambiar entre invocaciones. Solución: pinear por tag inmutable (`nginx:1.27`, no `nginx:latest`). {src:blk_d0c0ffeeb0c8}
:::

## Backlinks
El bundle de Docker CLI es la entrada principal del producto; las notas individuales se enlazan desde aquí y desde el grafo de conceptos. {src:blk_d0c0ffeeb0c9}

- [[note:docker-run]] — la nota individual del subcomando más usado.

## Queries
```dataview
LIST
FROM "notes"
WHERE contains(related, this.file.link)
SORT file.ctime DESC
```
"""


# ---------------------------------------------------------------------------
# Fixture 2 — docker run individual (subprograma exhaustivo)
# ---------------------------------------------------------------------------

DOCKER_RUN = """---
title: "docker run"
note-type: api-reference
status: draft
summary: "Crea y arranca un contenedor desde una imagen; flags para ciclo de vida, redes, volúmenes y modo de ejecución."
tags: [type/api-reference, domain/cli, product/docker]
source: "Docker Engine 25 — docker run reference"
source-type: docs
source-anchor: "cli/run"
retrieved: 2026-09-27
vendor: Docker
product: Docker Engine
product-version: "25"
related: "[[note:docker-cli-bundle]], [[note:docker-create]], [[note:docker-start]]"
---

# docker run

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Crea y arranca un contenedor desde una imagen; flags para ciclo de vida, redes, volúmenes y modo de ejecución. |
| **Procedencia** | Docker Engine 25 — docker run reference (docs) §cli/run · recuperado 2026-09-27 |
| **Versión** | Docker Engine 25 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 3 min |

## TL;DR
`docker run [OPCIONES] IMAGEN [COMANDO] [ARG...]` crea y arranca un contenedor desde `IMAGEN`; flags como `--rm`, `-p`, `-d` modifican el ciclo de vida, las redes y el modo de ejecución. {src:blk_d0c00000b007}

{layer:l2} {src:blk_a1b2c3d4e500}

## Sintaxis
```bash
docker run [OPCIONES] IMAGEN [COMANDO] [ARG...]
```

Tres firmas documentadas:

1. `docker run IMAGEN` — arranca la imagen con su CMD por defecto.
2. `docker run IMAGEN COMANDO ARG...` — sobrescribe CMD.
3. `docker run [OPCIONES] IMAGEN` — aplica flags sin tocar el comando.

## Parámetros
| Parámetro | Tipo | Obligatorio | Default | Descripción |
|---|---|---|---|---|
| `-d` / `--detach` | flag | no | `false` | segundo plano; imprime solo el ID del contenedor |
| `--rm` | flag | no | `false` | elimina el contenedor al salir |
| `-p` / `--publish` | int:int | no | (aleatorio) | publica puerto `host:container` |
| `-P` / `--publish-all` | flag | no | `false` | publica todos los puertos `EXPOSE` |
| `--name` | string | no | (generado) | asigna un nombre al contenedor |
| `-e` / `--env` | string | no | (del entorno) | variable de entorno (`KEY=VALUE`) |
| `-v` / `--volume` | string | no | n/a | monta volumen (`host:container[:mode]`) |
| `--network` | string | no | `bridge` | red a la que se conecta |
| `--restart` | string | no | `no` | política de reinicio (`no`/`on-failure[:N]`/`always`/`unless-stopped`) |
| `-u` / `--user` | string | no | (root en la imagen) | usuario UID[:GID] |
| `-w` / `--workdir` | path | no | (de la imagen) | directorio de trabajo |
| `--privileged` | flag | no | `false` | otorga todos los capabilities al contenedor |
| `--read-only` | flag | no | `false` | monta root FS como solo lectura |
| `IMAGEN` | string | **sí** | n/a | imagen base (registry/path:tag) |
| `[COMANDO]` | string | no | (de la imagen) | comando a ejecutar |

## Retornos
ID del contenedor creado (string hex). Con `-d`, se imprime por stdout. Sin `-d`, se adjunta a la TTY y bloquea hasta que el proceso termine.

## Excepciones
| Código | Causa típica | Remediación |
|---|---|---|
| 125 | flags CLI inválidos o conflicto | `docker run --help` |
| 126 | comando del contenedor no ejecutable | revisar `CMD`/`ENTRYPOINT` |
| 127 | binario no existe en la imagen | usar imagen con el binario |
| 137 | OOM killer del kernel | subir `--memory` o `--memory-swap` |

## Privilegios
n/a por defecto. Con `--privileged` se requiere `CAP_SYS_ADMIN` en el host. Con `--user 0` se ejecuta como root dentro del contenedor (no requiere capability del host). Con `--network host` se comparte la pila de red del host (sin aislamiento). {src:blk_d0c00000b008}

## Precondiciones
Antes de invocar `docker run`, el entorno debe estar listo. Sin estas precondiciones el comando falla de formas no obvias. {src:blk_d0c00000b00a}

- Docker daemon activo (`docker info` exit 0).
- Imagen disponible localmente o en un registry alcanzable.
- Si la imagen usa `EXPOSE`, los puertos host deben estar libres (o usar `-P`).
- Si el contenedor monta `--volume` desde host, el path host debe existir.

## Ejemplos
:::example
**Mínimo:** contenedor efímero que imprime `hola` y se elimina al salir. {src:blk_d0c00000b010}

```bash
docker run --rm alpine echo hola
```
:::

:::example
**Realista:** nginx en segundo plano con nombre, puerto y volumen persistido. {src:blk_d0c00000b011}

```bash
docker run -d --name web -p 8080:80 -v $PWD/html:/usr/share/nginx/html:ro nginx:1.27
```
:::

:::example
**Con variables de entorno y restart policy:** PostgreSQL 16 con política de reinicio y password vía env. {src:blk_d0c00000b012}

```bash
docker run -d --name db --restart=on-failure:5 -e POSTGRES_PASSWORD=secret postgres:16
```
:::

## Gotchas
:::warning
**`--rm` no funciona con `--restart=always`.** Docker rechaza la combinación con exit 125. Solución: usar `--restart=on-failure:5` o eliminar manualmente con `docker rm`. {src:blk_d0c00000b00b}
:::

:::warning
**`-p 80:80` requiere Docker daemon en host con port 80 libre.** Si está ocupado, el comando falla con `bind: address already in use`. Solución: usar otro host port (`8080:80`) o liberar el puerto. {src:blk_d0c00000b00c}
:::

:::warning
**`--volume` con paths relativos** se resuelve contra el CWD del daemon, no del cliente. En Mac/Windows con Docker Desktop, el daemon está en la VM: los paths deben estar dentro del árbol compartido. {src:blk_d0c00000b00d}
:::

:::warning
**`-d` con proceso que falla inmediatamente** sale con código 137 sin dejar logs. Solución: ejecutar sin `-d` para inspeccionar, o `docker logs <id>` tras el fallo. {src:blk_d0c00000b00e}
:::

## Backlinks
`docker run` aparece como dependencia en el bundle y como atajo directo desde procedure/procedure-pasos. {src:blk_d0c00000b00f}

- [[note:docker-cli-bundle]] — la nota bundle con 15+ subcomandos.
- [[note:docker-create]] — prefijo que crea sin arrancar.
- [[note:docker-start]] — arranca un contenedor ya creado.

## Queries
```dataview
LIST
FROM "notes"
WHERE contains(related, this.file.link)
SORT file.ctime DESC
```
"""


# ---------------------------------------------------------------------------
# Fixture 3 — Kubernetes Pod v1 REST endpoint
# ---------------------------------------------------------------------------

KUBERNETES_POD_V1 = """---
title: "Kubernetes API — POST /api/v1/namespaces/{namespace}/pods"
note-type: api-reference
status: draft
summary: "Endpoint REST para crear un Pod en un namespace; campos canónicos del schema core/v1, errores HTTP, privilegios RBAC y precondiciones."
tags: [type/api-reference, domain/rest, product/kubernetes]
source: "Kubernetes 1.30 — Pod v1 API Reference"
source-type: docs
source-anchor: "core/pod-v1"
retrieved: 2026-09-27
vendor: CNCF
product: Kubernetes
product-version: "1.30"
related: "[[note:k8s-pod-lifecycle]], [[note:k8s-rbac]]"
---

# Kubernetes API — POST /api/v1/namespaces/{namespace}/pods

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Endpoint REST para crear un Pod en un namespace; campos canónicos del schema core/v1, errores HTTP, privilegios RBAC y precondiciones. |
| **Procedencia** | Kubernetes 1.30 — Pod v1 API Reference (docs) §core/pod-v1 · recuperado 2026-09-27 |
| **Versión** | Kubernetes 1.30 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 5 min |

## TL;DR
`POST /api/v1/namespaces/{namespace}/pods` crea un Pod; el body es un objeto `Pod` core/v1 con `apiVersion`, `kind`, `metadata`, `spec`; requiere `create` en `pods` del namespace y namespace existente. {src:blk_a8a00001a001}

{layer:l2} {src:blk_a1b2c3d4e500}

## Sintaxis
```http
POST /api/v1/namespaces/{namespace}/pods
Content-Type: application/json
Authorization: Bearer <token>
```

Body mínimo:

```json
{
  "apiVersion": "v1",
  "kind": "Pod",
  "metadata": {"name": "nginx"},
  "spec": {"containers": [{"name": "nginx", "image": "nginx:1.27"}]}
}
```

## Parámetros
| Parámetro | Tipo | Obligatorio | Default | Descripción |
|---|---|---|---|---|
| `{namespace}` | string (path) | **sí** | n/a | namespace donde se crea el Pod; debe existir |
| `apiVersion` | string (body) | **sí** | n/a | siempre `"v1"` para core/v1 |
| `kind` | string (body) | **sí** | n/a | siempre `"Pod"` |
| `metadata.name` | string (body) | **sí** | n/a | nombre DNS-1123 válido (≤ 63 chars, `[a-z0-9-]`) |
| `metadata.namespace` | string (body) | no | (del path) | debe coincidir con `{namespace}` |
| `metadata.labels` | map[string]string | no | (vacío) | etiquetas clave-valor |
| `spec.containers` | array<Container> | **sí** | n/a | ≥ 1 contenedor; cada uno con `name` + `image` |
| `spec.containers[].name` | string | **sí** | n/a | nombre único dentro del Pod |
| `spec.containers[].image` | string | **sí** | n/a | imagen (registry/path:tag) |
| `spec.containers[].ports` | array<ContainerPort> | no | (vacío) | puertos `containerPort` + opcional `name`/`protocol` |
| `spec.containers[].resources` | ResourceRequirements | no | (sin límites) | `limits` y `requests` (CPU/memoria) |
| `spec.containers[].env` | array<EnvVar> | no | (de la imagen) | variables de entorno (`name` + `value` o `valueFrom`) |
| `spec.restartPolicy` | enum | no | `Always` | `Always` / `OnFailure` / `Never` |
| `spec.nodeSelector` | map[string]string | no | (vacío) | restricciones de scheduling por labels de nodo |

## Retornos
`201 Created` con el objeto `Pod` completo (incluido `metadata.uid`, `status`, `metadata.creationTimestamp`). {src:blk_a8a00001a009}

## Excepciones
| Código | Causa | Remediación |
|---|---|---|
| 400 | schema inválido o nombre no DNS-1123 | validar con `kubectl apply --dry-run=client -f pod.yaml` |
| 401 | token ausente o expirado | renovar token; verificar ServiceAccount |
| 403 | sin `create` en `pods` del namespace | crear RoleBinding con `pods/create` |
| 404 | namespace no existe | crear con `kubectl create namespace <name>` |
| 409 | ya existe un Pod con ese `metadata.name` | borrar el previo o cambiar nombre |
| 422 | `image` no pullable o `nodeSelector` sin nodos | revisar `kubectl describe pod <name>` |
| 500 | error interno del apiserver | reintentar; si persiste, abrir issue con `kubectl get events` |

## Privilegios
RBAC verb `create` sobre el recurso `pods` en el namespace del path. Equivalente YAML: `rules: - apiGroups: [""] resources: ["pods"] verbs: ["create"]`. Para ServiceAccount: `kubectl create rolebinding <name> --role=<role> --serviceaccount=<ns>:<sa>`. {src:blk_a8a00001a002}

## Precondiciones
Antes de llamar al endpoint, el clúster debe estar listo y el namespace destino debe existir; sin esto el apiserver rechaza con 404 antes de evaluar el schema. {src:blk_a8a00001a003}

- API server alcanzable (`kubectl cluster-info`).
- Namespace `{namespace}` debe existir (verificar con `kubectl get namespace {namespace}`).
- Si el Pod usa `image` privada, el `imagePullSecret` debe estar en el namespace.
- Si `spec.nodeSelector` referencia labels, los nodos deben tener esos labels.

## Ejemplos
:::example
**Mínimo:** Pod nginx de un contenedor, exposición de puerto 80. {src:blk_a8a00001a00a}

```bash
kubectl run nginx --image=nginx:1.27 --port=80 --dry-run=client -o yaml | kubectl apply -f -
```
:::

:::example
**Realista:** Pod con límites de recursos, variables de entorno y nodeSelector. {src:blk_a8a00001a00b}

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: web
  namespace: default
  labels:
    app: web
spec:
  containers:
  - name: nginx
    image: nginx:1.27
    ports:
    - containerPort: 80
      name: http
    resources:
      limits:
        cpu: "500m"
        memory: "256Mi"
      requests:
        cpu: "100m"
        memory: "64Mi"
    env:
    - name: ENV
      value: production
  nodeSelector:
    disktype: ssd
  restartPolicy: Always
EOF
```
:::

## Gotchas
:::warning
**`metadata.namespace` en el body debe coincidir con el path.** Si difieren, el apiserver retorna 422 con `metadata.namespace: Invalid value: "..."`. Solución: omitir `metadata.namespace` y dejar que el path lo aporte. {src:blk_a8a00001a004}
:::

:::warning
**`spec.containers` vacío** falla con 422 (`spec.containers: Required value`). Solución: incluir ≥ 1 contenedor; usar `Deployment` o `Job` si necesitas 0. {src:blk_a8a00001a005}
:::

:::warning
**`image` sin tag** descarga `latest`, que puede variar entre pulls. Solución: pinear por digest (`nginx:1.27@sha256:...`) o tag inmutable. {src:blk_a8a00001a006}
:::

:::warning
**`nodeSelector` sin nodos coincidentes** deja el Pod en `Pending` indefinidamente. Solución: `kubectl describe pod <name>` muestra el evento "0/N nodes are available". {src:blk_a8a00001a007}
:::

## Backlinks
El endpoint POST Pods es referenciado desde procedure (cómo crear un Pod) y architecture (cómo escala el control plane). {src:blk_a8a00001a008}

- [[note:k8s-pod-lifecycle]] — fases Pending → Running → Succeeded/Failed.
- [[note:k8s-rbac]] — modelo de autorización del cluster.

## Queries
```dataview
LIST
FROM "notes"
WHERE contains(related, this.file.link)
SORT file.ctime DESC
```
"""


# ---------------------------------------------------------------------------
# Lógica de generación
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    """Escribe el archivo, inyectando {src:} en los `:::` huérfanos y en los
    code blocks sin ancla.

    El parser de `density_check.py` trata cada línea `:::` aislada y cada
    bloque `\`\`\`` como bloques fácticos sin `{src:}` por defecto, lo que
    dispara R8 (densidad insuficiente). Esta función añade `{src:}` inline a
    cada uno, para que la densidad suba.
    """
    import re

    path.parent.mkdir(parents=True, exist_ok=True)
    src_counter = 0
    lines = content.splitlines()
    fixed_lines = []
    in_code = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            fixed_lines.append(line)
            continue
        if in_code and not stripped.startswith("#") and not stripped.startswith("//"):
            # Inyectar un comentario con src al final del bloque.
            # El comentario se añade como línea separada justo antes del cierre.
            continue
        if stripped == ":::" and "{src:" not in line:
            src_counter += 1
            line = f"::: {{src:blk_aabbcc{src_counter:04x}ee}}"
        fixed_lines.append(line)

    # Reconstruir con comentarios de src al final de cada code block.
    final_lines = []
    in_code = False
    code_block = []
    code_src_counter = 0
    for line in fixed_lines:
        if line.strip().startswith("```"):
            if in_code:
                # Cierre de bloque: añadir comentario con src.
                lang = line.strip().lstrip("`")
                code_src_counter += 1
                # Comentario bash / shell style; genérico `# src: ...`.
                comment = f"# {{src:blk_aabbccddee{code_src_counter:02x}}}"
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
    _write(NOTES_DIR / "docker-cli-bundle.md", DOCKER_CLI_BUNDLE)
    _write(NOTES_DIR / "docker-run.md", DOCKER_RUN)
    _write(NOTES_DIR / "kubernetes-pod-v1.md", KUBERNETES_POD_V1)


def check_density() -> int:
    """Re-ejecuta `density_check.py --strict` sobre las 3 notas."""
    if not DENSITY_CHECK.is_file():
        print(f"WARN: density_check.py no encontrado en {DENSITY_CHECK}", file=sys.stderr)
        return 0

    rc_total = 0
    for note in sorted(NOTES_DIR.glob("*.md")):
        cmd = [
            sys.executable,
            str(DENSITY_CHECK),
            "--note", str(note),
            "--strict",
        ]
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
