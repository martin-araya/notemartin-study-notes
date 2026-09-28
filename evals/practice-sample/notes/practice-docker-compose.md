---
title: "Docker — compose con servicio web + base de datos"
note-type: practice
status: draft
difficulty: 2
tags: [type/practice, domain/containers, product/docker]
source: "Docker 25 docs"
source-type: docs
source-anchor: "compose-multi-container"
retrieved: 2026-09-27
vendor: Docker
product: Docker Engine
product-version: "25"
related: "[[note:docker-compose]], [[note:docker-network-modes]]"
---

# Docker — compose con servicio web + base de datos

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Lab: levantar un stack con un servicio web (nginx) y una base de datos (PostgreSQL) usando docker compose. |
| **Procedencia** | Docker 25 docs (docs) §compose-multi-container · recuperado 2026-09-27 |
| **Versión** | 25 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 8 min |

## TL;DR
Levantar un stack multi-container con docker compose: nginx como proxy + PostgreSQL como BD. Aprende a definir servicios en YAML, exponer puertos, y limpiar el stack. {src:blk_c00000000002}

{layer:l2}

## Enunciado
Necesitas levantar localmente un stack con un servicio web (nginx) y una base de datos (PostgreSQL). El objetivo es practicar la definición de servicios en `docker-compose.yml`, el networking entre containers, y la limpieza completa del stack. {src:blk_fedcba000100}

## Entorno

| Componente | Versión | Notas |
|---|---|---|
| Docker | 25.x | con docker compose v2 |
| Recursos | 500 MB RAM, 1 GB disco | mínimo para el lab |

## Objetivo
Aprender a definir un stack multi-container en `docker-compose.yml`, exponer puertos al host, y limpiar el stack completamente. {src:blk_fedcba000200}

## Solución

### Paso 1: Crear el directorio del lab {src:blk_aabbccddee01}
```bash
mkdir practice-nginx-pg && cd practice-nginx-pg
# {src:blk_ccddeebf0001}
```

### Paso 2: Crear el archivo `docker-compose.yml` {src:blk_aabbccddee02}
```yaml
services:
  web:
    image: nginx:1.27
    ports:
      - "8080:80"
    depends_on:
      - db
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: appdb
# {src:blk_ccddeebf0002}
```

### Paso 3: Levantar el stack {src:blk_aabbccddee03}
```bash
docker compose up -d
# {src:blk_ccddeebf0003}
```

### Paso 4: Verificar que ambos servicios están corriendo {src:blk_aabbccddee04}
```bash
docker compose ps
# {src:blk_ccddeebf0004}
```

### Paso 5: Probar el acceso {src:blk_aabbccddee05}
```bash
curl http://localhost:8080
# {src:blk_ccddeebf0005}
```
Resultado esperado: página de inicio de nginx.

## Qué observar
:::note {src:blk_fedcba000300}
- `docker compose ps` debe mostrar 2 servicios: `web` (running) y `db` (running).
- El log de `web` debe mostrar "db_1 ready" antes de "nginx started".
- `curl` retorna HTML con título "Welcome to nginx!".
::: {src:blk_bbccddee0006}

## Verificación
La verificación cubre 3 señales que confirman que el stack funciona correctamente. {src:blk_c00000000004}

- `docker compose ps` muestra 2 servicios `running`.
- `curl http://localhost:8080` retorna HTML.
- `docker compose logs db | grep "database system is ready"` muestra el mensaje.

## Limpieza

1. Parar y borrar el stack: {src:blk_fedcba000400}
   :::warning {src:blk_fedcba000500}
   **`-v` borra los volúmenes.** Todos los datos de PostgreSQL se ELIMINAN permanentemente. NO uses `-v` en producción.
::: {src:blk_bbccddee0007}
   ```bash
   docker compose down -v {src:blk_fedcba000600}
# {src:blk_ccddeebf0006}
   ```
2. Borrar las imágenes descargadas (opcional): {src:blk_fedcba000700}
   ```bash
   docker rmi nginx:1.27 postgres:16 {src:blk_fedcba000800}
# {src:blk_ccddeebf0007}
   ```
3. Borrar el directorio del lab: {src:blk_fedcba000900}
   ```bash
   cd .. && rm -rf practice-nginx-pg {src:blk_fedcba000a00}
# {src:blk_ccddeebf0008}
   ```

Después de la limpieza, no quedan containers, imágenes ni volúmenes del lab. {src:blk_fedcba000b00}

## Lo que NO debe correrse en producción

:::danger {src:blk_fedcba000c00}
- `docker compose down -v` (Paso 1 de limpieza): borra los volúmenes persistentes de PostgreSQL.
- `docker rmi <image>`: borra imágenes usadas por otros containers.

En producción, ejecuta `docker compose stop` (pausa) o `docker compose down` (sin `-v`) para mantener los volúmenes. {src:blk_fedcba000d00}
::: {src:blk_bbccddee0008}

## Cuándo omitir este lab

:::note
Omite este lab si: (1) ya dominas docker compose con networking multi-container; (2) trabajas con Kubernetes y prefieres practicar con Deployments + Services; (3) tu proyecto usa un orquestador distinto (Nomad, ECS) y prefieres practicar su sintaxis; (4) los servicios reales de tu proyecto requieren configuración compleja (volúmenes compartidos, secrets, configs) que este lab no cubre.
::: {src:blk_bbccddee0009}

## Pistas

:::tip
Si `web` no arranca, ejecuta `docker compose logs web` para ver el error. Si `db` no está listo, añade `healthcheck` con `test: ["CMD-SHELL", "pg_isready -U postgres"]` y `depends_on: condition: service_healthy`.
::: {src:blk_bbccddee000a}

## Backlinks
El lab se conecta con la nota de docker compose y la nota de network modes; los enlaces muestran los 2 ángulos del stack. {src:blk_c00000000005}

- [[note:docker-compose]]
- [[note:docker-network-modes]]
