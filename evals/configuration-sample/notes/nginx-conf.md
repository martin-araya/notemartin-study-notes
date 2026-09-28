---
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
# {src:blk_ccddeebf0001}
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
# {src:blk_ccddeebf0002}
```
::: {src:blk_bbccddee0001}

## Combinaciones peligrosas
:::danger
**`worker_rlimit_nofile = 1024` + `worker_connections = 4096`.** Cada worker no puede abrir más de 1024 FD; con 4096 conexiones deseadas, nginx retorna `connection: too many open files` y rechaza requests. Solución: `worker_rlimit_nofile ≥ worker_connections × 2`.
::: {src:blk_bbccddee0002}

:::danger
**`client_max_body_size = 0` + uploads grandes.** `0` significa "no aceptar body" → todo POST/PUT con body retorna 413. Solución: subir a `10m` o más según el caso de uso.
::: {src:blk_bbccddee0003}

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
# {src:blk_ccddeebf0003}
```
::: {src:blk_bbccddee0004}

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
::: {src:blk_bbccddee0005}

## Backlinks
La tuning de nginx.conf es complementaria a la rotación de logs y a las directivas proxy_pass; los enlaces muestran ambos aspectos. {src:blk_c00000000060}

- [[note:nginx-logrotate]] — rotación de logs.
- [[note:nginx-proxy-conf]] — directivas `proxy_pass` y `upstream`.
