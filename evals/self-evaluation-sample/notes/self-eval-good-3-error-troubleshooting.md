---
title: "Connection refused en PostgreSQL"
note-type: error-troubleshooting
status: published
summary: "Causa raíz y diagnóstico cuando psql o un cliente devuelve `Connection refused` apuntando al puerto 5432."
reading-time-minutes: 3
language: es
tags: [type/error-troubleshooting, domain/sample, f102/self-eval]
source: "evals/corpus/sample/sdm.json"
source-type: docs
source-anchor: "section_path=/sample"
retrieved: 2026-09-29
self-evaluation-types: [diagnostico, decision]
---


# Connection refused en PostgreSQL

## TL;DR

El mensaje `Connection refused` indica que el puerto 5432 está cerrado
o el servidor no escucha en la interfaz esperada. {src:blk_c11f8e02c1d3}

## Síntomas

```
psql: error: connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
        Is the server running on that host and accepting TCP/IP connections?
```

Este mensaje literal preserva el formato exacto del cliente `psql`
cuando no puede establecer la conexión TCP/IP. {src:blk_c11f8e02c1d3}

## Causa raíz

PostgreSQL no escucha en el puerto; el servicio no está activo, o
`listen_addresses` excluye la interfaz de origen. {src:blk_c11f8e02c1d3}

## Diagnóstico

1. Verificar que el servicio esté activo: `systemctl status postgresql`.
2. Verificar el puerto: `ss -tln | grep 5432`.
3. Revisar `postgresql.conf`: `listen_addresses = '*'` o la IP esperada.
4. Comprobar `pg_hba.conf` para descartar rechazo por autenticación. {src:blk_c11f8e02c1d3}

## Solución

La corrección típica tiene tres pasos. Primero, verificar si el servicio
está activo (`systemctl status postgresql`); si está caído, iniciarlo.
Segundo, ajustar `listen_addresses` en `postgresql.conf` para incluir la
interfaz de origen. Tercero, comprobar `pg_hba.conf` si el cliente llega
al puerto pero la autenticación falla. {src:blk_c11f8e02c1d3}

## Autoevaluación

Tipos asignados a `error-troubleshooting`: diagnóstico, decisión.

### Diagnóstico

:::collapsible{default_open=false}
Si ves `Connection refused` al conectar a `localhost:5432`, ¿cuál es la causa más probable?
El puerto 5432 está cerrado: el servicio PostgreSQL no está activo o `listen_addresses` excluye `localhost`.
> Fundamento: {src:blk_c11f8e02c1d3}
:::

:::collapsible{default_open=false}
¿Por qué `psql -h localhost` falla con `Connection refused` pero `psql -h /var/run/postgresql` funciona?
La segunda forma usa el socket Unix del sistema de archivos, que no depende de la pila TCP/IP; la primera requiere que PostgreSQL esté escuchando en la interfaz de red.
> Fundamento: [[note:postgres-listen-addresses#tcp-vs-unix]]
:::

:::collapsible{default_open=false}
Si `ss -tln` no muestra el puerto 5432, ¿qué conclusión sacas?
El servidor no está aceptando conexiones TCP/IP entrantes; puede estar caído, configurado solo para socket local, o filtrado por un firewall upstream que bloquea el puerto.
> Fundamento: [[note:postgres-network-troubleshooting#listen]]
:::

### Decisión

:::collapsible{default_open=false}
Entre reiniciar el servicio y corregir `postgresql.conf`, ¿cuál haces primero si el servicio está caído?
Reiniciar el servicio primero (recupera la conexión); la corrección de `postgresql.conf` la haces en una ventana de mantenimiento.
> Fundamento: [[note:postgres-incident-response#restart-vs-config]]
:::

:::collapsible{default_open=false}
Si la aplicación se conecta vía TCP/IP y `listen_addresses = 'localhost'`, ¿prefieres ampliar a `'*'` o configurar un proxy?
Configurar un proxy (PgBouncer) con TLS y ACL; evita exponer el puerto a toda la red.
> Fundamento: [[note:postgres-security#proxy-vs-bind]]
:::

:::collapsible{default_open=false}
Cuando el `Connection refused` es intermitente y coincide con despliegues, ¿qué revisas primero?
Los logs de systemd y el journal del kernel para detectar OOM kills del proceso postgres durante picos de memoria.
> Fundamento: [[note:postgres-incident-response#oom]]
:::
