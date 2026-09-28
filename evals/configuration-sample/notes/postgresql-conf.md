---
title: "postgresql.conf — 11 GUC críticos"
note-type: configuration
status: draft
summary: "Tabla canónica de 11 parámetros de postgresql.conf en PostgreSQL 16 (memoria, conexión, logging, replicación) con sus interacciones y combinaciones peligrosas."
tags: [type/configuration, domain/databases, product/postgresql]
source: "PostgreSQL 16 — Server Configuration"
source-type: docs
source-anchor: "runtime-config"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:postgresql-mvcc]], [[note:procedure-tune-postgres]]"
---

# postgresql.conf — 11 GUC críticos

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Tabla canónica de 11 parámetros de postgresql.conf en PostgreSQL 16 (memoria, conexión, logging, replicación) con sus interacciones y combinaciones peligrosas. |
| **Procedencia** | PostgreSQL 16 — Server Configuration (docs) §runtime-config · recuperado 2026-09-27 |
| **Versión** | PostgreSQL 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 6 min |

## TL;DR
11 GUC controlan el grueso del tuning de PostgreSQL 16: memoria compartida, memoria per-orden, cache del planner, conexión, WAL y replicación. Los defaults son conservadores; producción típica sube `shared_buffers` a ~25% RAM. {src:blk_c00000000001}

{layer:l2}

## Configuración
```ini
# postgresql.conf — subset canónico de 11 GUC
# Memoria compartida y por sesión
shared_buffers = 128MB           # ~25% de RAM en producción
work_mem = 4MB                   # per orden; multiplicar por concurrencia
maintenance_work_mem = 64MB      # VACUUM, CREATE INDEX
effective_cache_size = 4GB       # hint al planner; no asigna memoria
# Conexión
max_connections = 100
# WAL y replicación
wal_level = replica
max_wal_size = 1GB
min_wal_size = 80MB
# Logging
log_min_duration_statement = -1  # -1 = off; >=0 activa log de queries lentas
log_checkpoints = on
# {src:blk_ccddeebf0001}
```

## Parámetros

### Parámetros de memoria
| Parámetro | Ámbito | Tipo | Default | Rango | Hot reload | Reinicio | Versión | Impacto |
|---|---|---|---|---|---|---|---|---|
| `shared_buffers` | instance | size | `128MB` | ≥ 128kB | no | sí | todas | memoria: cache principal de páginas (~25% RAM recomendado en producción) |
| `work_mem` | session | size | `4MB` | ≥ 64kB | sí | no | todas | memoria: por sort/hash; OOM si muchas ordenaciones concurrentes |
| `maintenance_work_mem` | session | size | `64MB` | ≥ 1MB | sí | no | todas | memoria: VACUUM/INDEX; reduce tiempo de mantenimiento |
| `effective_cache_size` | instance | size | `4GB` | ≥ 0 | sí | no | todas | comportamiento: hint al planner; usar ~75% RAM |

### Parámetros de conexión
| Parámetro | Ámbito | Tipo | Default | Rango | Hot reload | Reinicio | Versión | Impacto |
|---|---|---|---|---|---|---|---|---|
| `max_connections` | instance | int | `100` | 1–262143 | sí | no | todas | memoria: ~10 MB por conexión backend; usar pgbouncer para multiplexar |

### Parámetros de WAL y replicación
| Parámetro | Ámbito | Tipo | Default | Rango | Hot reload | Reinicio | Versión | Impacto |
|---|---|---|---|---|---|---|---|---|
| `wal_level` | instance | enum | `replica` | minimal/replica/logical | sí | no | 9.0+ | disponibilidad: `logical` permite logical replication; `minimal` reduce volumen |
| `max_wal_size` | instance | size | `1GB` | ≥ 2 × 16MB | sí | no | todas | disponibilidad: tamaño máximo antes de checkpoint; subir en escrituras masivas |
| `min_wal_size` | instance | size | `80MB` | ≥ 2 × 16MB | sí | no | todas | disponibilidad: mantener WAL caliente; reduce latencia de replicas |

### Parámetros de logging
| Parámetro | Ámbito | Tipo | Default | Rango | Hot reload | Reinicio | Versión | Impacto |
|---|---|---|---|---|---|---|---|---|
| `log_min_duration_statement` | instance | ms | `-1` (off) | -1 a 2.147e+09 | sí | no | todas | rendimiento: log activo degrada rendimiento; usar 1000-5000 ms para detectar lentas |
| `log_checkpoints` | instance | bool | `off` | on/off | sí | no | 8.0+ | rendimiento: log de cada checkpoint; útil para diagnosticar I/O |

## Ejemplo completo
:::example
**Producción 32 GB RAM, 200 conexiones, 10k TPS:** {src:blk_c00000000080}

```ini
shared_buffers = 8GB
work_mem = 16MB
maintenance_work_mem = 2GB
effective_cache_size = 24GB
max_connections = 200
wal_level = replica
max_wal_size = 4GB
min_wal_size = 1GB
log_min_duration_statement = 2000
log_checkpoints = on
# {src:blk_ccddeebf0002}
```
::: {src:blk_bbccddee0001}

## Combinaciones peligrosas
:::danger
**`shared_buffers = 16GB` + `work_mem = 256MB` + `max_connections = 500`.** Memoria: 16 GB compartida + 500 × 256 MB = 144 GB potencial → OOM killer. Solución: bajar `work_mem` a 16 MB o desplegar `pgbouncer` para multiplexar conexiones.
::: {src:blk_bbccddee0002}

:::danger
**`wal_level = minimal` + replicación lógica activa.** Logical replication requiere `wal_level = logical`. Solución: cambiar `wal_level` antes de crear subscriptions.
::: {src:blk_bbccddee0003}

## Interacciones
| Cambio | Revisar también |
|---|---|
| Subir `shared_buffers` | `effective_cache_size` (debe ser proporcional, hint al planner) |
| Subir `work_mem` | `max_connections` × nº de operaciones concurrentes (techo de memoria por sesión) |
| Subir `max_connections` | `shared_buffers`, `work_mem`, `max_connections` multiplica el techo de memoria |
| Cambiar `wal_level` | subscriptions de logical replication (requieren `logical`); archivado de WAL |
| Activar `log_min_duration_statement` | volumen de disco y rendimiento (log activo degrada TPS en 5-15%) |

## Diagrama de dependencias
:::diagram
```mermaid
flowchart LR
    SB[shared_buffers] --> EC[effective_cache_size]
    WM[work_mem] --> MC[max_connections]
    SB --> WM
    WL[wal_level] --> LR[logical replication]
    MCS[max_wal_size] --> CK[checkpoints]
    LMD[log_min_duration_statement] --> PERF[rendimiento TPS]
# {src:blk_ccddeebf0003}
```
::: {src:blk_bbccddee0004}

## Valores comunes

| Caso | shared_buffers | work_mem | effective_cache_size | max_connections |
|---|---|---|---|---|
| Desarrollo | `128MB` | `4MB` | `4GB` | `100` |
| Producción 16 GB | `4GB` | `16MB` | `12GB` | `100-200` |
| Producción 64 GB | `16GB` | `32MB` | `48GB` | `200-500` |
| OLTP pesado | `16GB` | `8MB` | `48GB` | `500+` con pgbouncer |

## Troubleshooting
:::warning
**`FATAL: could not allocate memory for shared buffers`.** `shared_buffers` excede RAM disponible. Solución: reducir a 25% de RAM o `sysctl -w kernel.shmmax=`.
::: {src:blk_bbccddee0005}

## Backlinks
La tuning de postgresql.conf es uno de los pasos iniciales de cualquier despliegue PostgreSQL; los enlaces muestran los conceptos subyacentes y el procedure asociado. {src:blk_c00000000050}

- [[note:postgresql-mvcc]] — por qué MVCC necesita `shared_buffers` grande.
- [[note:procedure-tune-postgres]] — pasos para aplicar estos cambios en producción.
