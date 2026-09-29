---
title: "Hello world con docker run --rm"
note-type: procedure
status: published
summary: "Ejemplo CLI de docker run con flag --rm para auto-eliminar el contenedor."
reading-time-minutes: 1
tags: [type/example, domain/cli, f80/procedure, f96/executable-examples]
source: "evals/corpus/07-docker-cli-ref/sdm.json"
source-type: docs
source-anchor: "page=8,section_path=/docker-run/quickstart"
retrieved: 2026-09-28
product: "Docker"
product-version: "27.0"
related: "[[note:docker-rm]]"
---

# Hello world con docker run --rm

> Cabecera. Resumen, procedencia, versión, estado y tiempo de lectura en el
> frontmatter superior.

## TL;DR

`docker run --rm alpine:3.19 echo "hello"` ejecuta un comando en un
contenedor efímero; `--rm` borra el contenedor al salir. {src:blk_2d5e8a3b7c91}

> **Entorno:** Docker 27.0 · Ubuntu 24.04 LTS · imagen `alpine:3.19` · usuario con permisos de docker (no requiere root en el host). {src:blk_a2b3c4d5e6f7}

Ejemplo reproducible basado en la referencia CLI de Docker. {src:blk_4f5a6b7c8d9e}

:::example
## Setup

Descarga la imagen alpine (idempotente, no-op si ya existe). {src:blk_8f1c4d9e6a03}

```bash
# {src:blk_e01b2c3d4e5f}
docker pull alpine:3.19
```

## Acción

Lanza el contenedor con `--rm` para auto-eliminarlo al terminar. {src:blk_5a7b2e0c4d96}

```bash
# {src:blk_f12c3d4e5a6b}
docker run --rm alpine:3.19 echo "hello from notemartin"
```

## Resultado

El comando imprime la cadena exacta y el contenedor se elimina al salir. {src:blk_3c8f1a5d9b27}

```
# {src:blk_a7b8c9d0e1f2}
hello from notemartin
```

## Limpieza

No requiere limpieza: la flag `--rm` borra el contenedor automáticamente. {src:blk_7b4e9c1a5d83}
:::
