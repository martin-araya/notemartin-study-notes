---
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
# {src:blk_ccddeebf0001}
```

### Mensaje 2: Too many connections
```
psql: error: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: FATAL:  too many connections for role "app"
# {src:blk_ccddeebf0002}
```

### Mensaje 3: Password authentication failed
```
psql: error: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: FATAL:  password authentication failed for user "app"
# {src:blk_ccddeebf0003}
```

### Mensaje 4: Database does not exist
```
psql: error: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: FATAL:  database "appdb" does not exist
# {src:blk_ccddeebf0004}
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
# {src:blk_ccddeebf0005}
```
**Verificación:** `active (running)` → sí; `inactive (dead)` o `failed` → no. {src:blk_e00000000006}

```bash
# Paso 2: ¿Cuántas conexiones hay?
psql -c "SELECT count(*) FROM pg_stat_activity;"
# {src:blk_ccddeebf0006}
```
**Verificación:** `< max_connections` → hay espacio; `>= max_connections` → saturado. {src:blk_aabbccddee01}

```bash
# Paso 3: ¿Las credenciales son válidas y la BD existe?
psql -U app -d mydb -c "SELECT 1;"
# {src:blk_ccddeebf0007}
```
**Verificación:** exit 0 → sí; exit 2 con `password authentication failed` → falla auth; `database "X" does not exist` → falla BD. {src:blk_aabbccddee02}

## Solución

### Mensaje 1: Connection refused
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
# {src:blk_ccddeebf0008}
```
Si `listen_addresses = 'localhost'` pero el cliente viene de otra IP, editar `postgresql.conf` y `pg_hba.conf`, luego `pg_ctl reload`.

### Mensaje 2: Too many connections
Corto plazo: matar conexiones idle. {src:blk_eeeeff0008}
```sql
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < now() - interval '10 minutes';
# {src:blk_ccddeebf0009}
```
Largo plazo: desplegar `pgbouncer` para multiplexar. {src:blk_eeeeff0009}

### Mensaje 3: Password authentication failed
```bash
sudo -u postgres psql -c "ALTER USER app WITH PASSWORD 'nueva_contraseña';"
# {src:blk_ccddeebf000a}
```

### Mensaje 4: Database does not exist
```bash
sudo -u postgres createdb appdb
# {src:blk_ccddeebf000b}
```
O cambiar la conexión a una BD existente: `psql -U app -d postgres`.

## Prevención

:::tip
**Mensaje 1:** Configurar `monit` o `systemd` watchdog para reiniciar PostgreSQL automáticamente tras caída. Verificar con `journalctl -u postgresql --since "5 minutes ago"`.
::: {src:blk_bbccddee0003}

:::tip
**Mensaje 2:** Limitar conexiones idle a 5 minutos con `idle_in_transaction_session_timeout = 5min` y desplegar `pgbouncer` antes de producción.
::: {src:blk_bbccddee0004}

:::tip
**Mensaje 3:** Usar `pgpassfile` (`~/.pgpass`) con permisos 0600 en vez de variables de entorno; rotar contraseñas vía `ALTER USER ... VALID UNTIL`.
::: {src:blk_bbccddee0005}

:::tip
**Mensaje 4:** Versionar nombres de BD en IaC (Terraform/Ansible) y validar con `psql -lqt | cut -d \| -f 1` antes de deploys.
::: {src:blk_bbccddee0006}

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
# {src:blk_ccddeebf000c}
```
::: {src:blk_bbccddee0007}

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
