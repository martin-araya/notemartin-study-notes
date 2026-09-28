---
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
# {src:blk_aabbccddee01}
```

## Parámetros

### Subcomando: `docker run`

{layer:l2} {src:blk_a1b2c3d4e500}

## Sintaxis
```bash
# {src:blk_aabbccddee02}
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
# {src:blk_aabbccddee03}
```
::: {src:blk_aabbcc0001ee}

:::example
**docker compose realista:** arranca un stack `web` + `db` definido en `compose.yml`. {src:blk_d0c0ffeeb0cb}

```bash
# {src:blk_aabbccddee04}
```
::: {src:blk_aabbcc0002ee}

:::example
**docker inspect con format:** obtener solo la IP de un contenedor. {src:blk_d0c0ffeeb0cc}

```bash
# {src:blk_aabbccddee05}
```
::: {src:blk_aabbcc0003ee}

:::example
**docker system prune realista:** libera espacio eliminando imágenes huérfanas y contenedores detenidos. {src:blk_d0c0ffeeb0cd}

```bash
# {src:blk_aabbccddee06}
```
::: {src:blk_aabbcc0004ee}

## Gotchas
:::warning
**`docker rm` no acepta `CONTAINER` mientras está corriendo.** Sin `-f`, retorna error y sale con código 1. Solución: `docker rm -f <id>` o `docker stop <id> && docker rm <id>`. {src:blk_d0c0ffeeb0c5}
::: {src:blk_aabbcc0005ee}

:::warning
**`docker compose up -d` no propaga el exit code** de los servicios fallidos. Solución: `docker compose up` (sin `-d`) para ver logs y exit codes. {src:blk_d0c0ffeeb0c6}
::: {src:blk_aabbcc0006ee}

:::warning
**`docker logs --tail=N` con `N=0`** imprime todas las líneas, no ninguna. Es el comportamiento por diseño (`all` se serializa como `0` internamente). Solución: usar `--tail=all` explícito para autodocumentar. {src:blk_d0c0ffeeb0c7}
::: {src:blk_aabbcc0007ee}

:::warning
**`docker pull` sin tag** descarga `latest`, que puede cambiar entre invocaciones. Solución: pinear por tag inmutable (`nginx:1.27`, no `nginx:latest`). {src:blk_d0c0ffeeb0c8}
::: {src:blk_aabbcc0008ee}

## Backlinks
El bundle de Docker CLI es la entrada principal del producto; las notas individuales se enlazan desde aquí y desde el grafo de conceptos. {src:blk_d0c0ffeeb0c9}

- [[note:docker-run]] — la nota individual del subcomando más usado.

## Queries
```dataview
# {src:blk_aabbccddee07}
```
