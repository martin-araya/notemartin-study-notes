---
title: "Docker 25 cheatsheet"
note-type: cheatsheet
status: draft
tags: [type/cheatsheet, domain/containers, product/docker]
source: "Docker 25 docs"
source-type: docs
source-anchor: "cheatsheet"
retrieved: 2026-09-27
vendor: Docker
product: Docker Engine
product-version: "25"
related: "[[note:docker-cli-bundle]], [[note:docker-permission-errors]]"
---

# Docker 25 cheatsheet

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Cheatsheet de Docker 25: comandos CLI, atajos, errores frecuentes. |
| **Procedencia** | Docker 25 docs (docs) §cheatsheet · recuperado 2026-09-27 |
| **Versión** | 25 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 3 min |

## TL;DR
Comandos CLI de Docker 25, atajos (`-it`, `-d`, `--rm`), y errores frecuentes con enlaces a notas detalladas. {src:blk_fedcba000100}

{layer:l1}

## Comandos
| Comando | Descripción | Ver |
|---|---|---|
| `docker run -d -p 8080:80 --name web nginx` | Crear y arrancar container | [[note:docker-cli-bundle]] |
| `docker ps -a` | Listar containers (incluyendo detenidos) | [[note:docker-cli-bundle]] |
| `docker exec -it <id> bash` | Entrar a un container interactivo | [[note:docker-permission-errors]] |
| `docker logs -f <id>` | Ver logs en vivo | [[note:docker-cli-bundle]] |
| `docker stop <id>` | Parar container | [[note:docker-cli-bundle]] |
| `docker rm -f <id>` | Eliminar container | [[note:docker-cli-bundle]] |
| `docker images` | Listar imágenes locales | [[note:docker-cli-bundle]] |
| `docker pull image:tag` | Descargar imagen | [[note:docker-cli-bundle]] |
| `docker push registry/image:tag` | Subir imagen | [[note:docker-cli-bundle]] |
| `docker system prune -a` | Limpiar containers, imágenes, networks | [[note:docker-cli-bundle]] |
| `docker compose up -d` | Levantar stack compose | [[note:docker-cli-bundle]] |
| `docker compose logs -f` | Ver logs de stack | [[note:docker-cli-bundle]] |

## Atajos
| Atajo | Significado |
|---|---|
| `-d` | Modo detached (background) |
| `-it` | Interactivo + TTY (shell) |
| `--rm` | Eliminar container al salir |
| `-p` | Publicar puerto host:container |
| `-v` | Montar volumen |
| `-e` | Variable de entorno |
| `--name` | Nombre del container |
| `--restart` | Política de restart |

## Errores comunes

:::warning
**`permission denied while trying to connect to /var/run/docker.sock`** — usuario sin acceso al socket. Solución: `usermod -aG docker $USER; newgrp docker`. Ver [[note:docker-permission-errors]].
::: {src:blk_bbccddee0001}

:::warning
**`no space left on device`** — disco lleno. Solución: `docker system prune -a --volumes` para limpiar. Ver [[note:docker-cli-bundle]].
::: {src:blk_bbccddee0002}

:::warning
**`port is already allocated`** — puerto host ocupado. Solución: cambiar `-p` a otro puerto o liberar el puerto. Ver [[note:docker-cli-bundle]].
::: {src:blk_bbccddee0003}

## Backlinks
- [[note:docker-cli-bundle]]
- [[note:docker-permission-errors]]
