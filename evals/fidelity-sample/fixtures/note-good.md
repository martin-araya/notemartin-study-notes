# Postgres Configuration

PostgreSQL es un ORDBMS. {src:blk_a1b2c3d4e5f6}

:::derived
Diagrama de la arquitectura cliente-servidor:
```mermaid
flowchart LR
    A[Cliente] --> B[Servidor]
```
:::

:::external
La mayoría de los ORDBMS usan MVCC; ver RFC 1234. {external}
:::

El parámetro `shared_buffers` controla el caché compartido. {src:blk_b2c3d4e5f6a7}
El default es 128 MB. {src:blk_c3d4e5f6a7b8}
El código de error EADDRINUSE indica puerto en uso. {src:blk_d4e5f6a7b8c9}
