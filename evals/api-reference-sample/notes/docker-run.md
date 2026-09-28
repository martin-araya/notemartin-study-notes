---
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
# {src:blk_aabbccddee01}
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
# {src:blk_aabbccddee02}
```
::: {src:blk_aabbcc0001ee}

:::example
**Realista:** nginx en segundo plano con nombre, puerto y volumen persistido. {src:blk_d0c00000b011}

```bash
# {src:blk_aabbccddee03}
```
::: {src:blk_aabbcc0002ee}

:::example
**Con variables de entorno y restart policy:** PostgreSQL 16 con política de reinicio y password vía env. {src:blk_d0c00000b012}

```bash
# {src:blk_aabbccddee04}
```
::: {src:blk_aabbcc0003ee}

## Gotchas
:::warning
**`--rm` no funciona con `--restart=always`.** Docker rechaza la combinación con exit 125. Solución: usar `--restart=on-failure:5` o eliminar manualmente con `docker rm`. {src:blk_d0c00000b00b}
::: {src:blk_aabbcc0004ee}

:::warning
**`-p 80:80` requiere Docker daemon en host con port 80 libre.** Si está ocupado, el comando falla con `bind: address already in use`. Solución: usar otro host port (`8080:80`) o liberar el puerto. {src:blk_d0c00000b00c}
::: {src:blk_aabbcc0005ee}

:::warning
**`--volume` con paths relativos** se resuelve contra el CWD del daemon, no del cliente. En Mac/Windows con Docker Desktop, el daemon está en la VM: los paths deben estar dentro del árbol compartido. {src:blk_d0c00000b00d}
::: {src:blk_aabbcc0006ee}

:::warning
**`-d` con proceso que falla inmediatamente** sale con código 137 sin dejar logs. Solución: ejecutar sin `-d` para inspeccionar, o `docker logs <id>` tras el fallo. {src:blk_d0c00000b00e}
::: {src:blk_aabbcc0007ee}

## Backlinks
`docker run` aparece como dependencia en el bundle y como atajo directo desde procedure/procedure-pasos. {src:blk_d0c00000b00f}

- [[note:docker-cli-bundle]] — la nota bundle con 15+ subcomandos.
- [[note:docker-create]] — prefijo que crea sin arrancar.
- [[note:docker-start]] — arranca un contenedor ya creado.

## Queries
```dataview
# {src:blk_aabbccddee05}
```
