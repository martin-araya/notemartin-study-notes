---
title: "Errores propios — Docker"
domain: docker
note-type: error-log
status: published
summary: "Registro de 2 errores propios de Docker: permisos de socket y volumen nombrado faltante."
reading-time-minutes: 1
tags: [study/errors, domain/docker]
retrieved: 2026-09-15
source-self: "Living-doc meta-documental; no se publica como nota de conocimiento (F103 §1)."
---

# Errores propios — Docker

## Resumen de errores

Dos errores propios del dominio Docker: acceso al socket y volumen
nombrado no resuelto en compose.

## Errores registrados

### Error DOCKER-001

#### Concepto

Permisos del socket Unix de Docker.

#### Comando erróneo

:::code
docker ps
:::

Salida literal:

:::code
permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock
:::

#### Corrección

:::code
sudo usermod -aG docker $USER
newgrp docker
docker ps
:::

El usuario actual no está en el grupo `docker`; agregar y refrescar
la sesión. {src:blk_d11f8e02c1d3}

Nota canónica: [[note:docker-postinstall#permissions]].

#### Origen

Fecha del error: 2026-09-05. Contexto: configurar CI runner para
ejecutar pruebas de integración con Testcontainers.

#### Repaso

Próximo repaso: review-next: 2026-09-20. Tarjeta prioritaria: sí.

### Error DOCKER-002

#### Concepto

Volumen nombrado faltante en compose.

#### Comando erróneo

:::code
docker compose up web
:::

Salida literal:

:::code
Error response from daemon: create <<volume>>: volume not found
:::

#### Corrección

:::code
docker volume create app_data
docker compose up web
:::

Compose no crea volúmenes nombrados si la entrada `external: true`
está mal colocada; revisar `docker-compose.yml`. {src:blk_d12f8e02c1d3}

Nota canónica: [[note:docker-compose-volumes#external]].

#### Origen

Fecha del error: 2026-09-13. Contexto: levantar stack local con
PostgreSQL + API para reproducir un bug de producción.

#### Repaso

Próximo repaso: review-next: 2026-10-01. Tarjeta prioritaria: sí.
