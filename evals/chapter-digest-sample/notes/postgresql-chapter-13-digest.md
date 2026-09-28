---
title: "PostgreSQL 16 — Ch 13: Concurrency Control (digest)"
note-type: chapter-digest
status: draft
summary: "Digest del Chapter 13 de la doc oficial de PostgreSQL 16 sobre control de concurrencia: MVCC, isolation levels (Read Committed, Repeatable Read, Serializable), explicit locking, VACUUM."
tags: [type/chapter-digest, domain/databases, source/postgresql-docs]
source: "PostgreSQL 16 — Server Administration"
source-type: docs
source-anchor: "concurrency-control"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
coverage: summary
related: "[[note:chapter-12-physical-storage-digest]], [[note:chapter-14-performance-tips-digest]]"
---

# PostgreSQL 16 — Ch 13: Concurrency Control (digest)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Digest del Chapter 13 de la doc oficial de PostgreSQL 16 sobre control de concurrencia: MVCC, isolation levels, explicit locking, VACUUM. |
| **Procedencia** | PostgreSQL 16 — Server Administration (docs) §concurrency-control · recuperado 2026-09-27 |
| **Versión** | PostgreSQL 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 5 min |

## TL;DR
El capítulo introduce MVCC como mecanismo por defecto: cada transacción ve un snapshot consistente basado en `xmin`/`xmax`. Cubre los 4 niveles de aislamiento (Read Uncommitted emula Read Committed; Read Committed es el default; Repeatable Read y Serializable usan snapshot-based) y los bloqueos explícitos (`FOR UPDATE`, `FOR SHARE`). {src:blk_c00000000010}

{layer:l2}

## Resumen ejecutivo
PostgreSQL usa MVCC (Multi-Version Concurrency Control) por defecto: en lugar de bloquear filas para mantener aislamiento, cada fila lleva marcas de transacción (`xmin`, `xmax`) que permiten a cada sesión ver su propio snapshot consistente sin interferir con otras. Esto maximiza concurrencia pero requiere `VACUUM` periódico para reclamar espacio de filas muertas. El capítulo documenta los 4 niveles de aislamiento SQL estándar (Read Uncommitted, Read Committed, Repeatable Read, Serializable), cómo PostgreSQL implementa cada uno, y los bloqueos explícitos (`SELECT ... FOR UPDATE/SHARE`) cuando se necesita sincronización estricta. {src:blk_c00000000011}

## Continuidad

### Hacia atrás {src:blk_aabbccddee01}
El [[note:chapter-12-physical-storage-digest]] introdujo el modelo de almacenamiento físico (heap files, TOAST, FSM, VM). Aquí extendemos con el modelo de concurrencia sobre disco: cómo múltiples transacciones leen y escriben sin corromperse. {src:blk_eeeeff000001}

### Hacia adelante {src:blk_aabbccddee02}
El [[note:chapter-14-performance-tips-digest]] cubre tips de performance basados en la comprensión de MVCC — por qué `VACUUM` regular importa, cómo `work_mem` interactúa con MVCC. {src:blk_c00000000012}

## Puntos clave
El capítulo resume MVCC en 5 takeaways que el lector debe recordar después de leer el digest. {src:blk_c00000000060}

- MVCC es el mecanismo por defecto; cada transacción ve un snapshot consistente.
- Los 4 niveles de aislamiento se implementan con snapshots, no con bloqueos por defecto.
- `SELECT ... FOR UPDATE/SHARE` permite sincronización explícita cuando se necesita.
- `VACUUM` es esencial para reclamar espacio de tuplas muertas generadas por MVCC.
- El catálogo del sistema (`pg_locks`, `pg_stat_activity`) expone el estado de locks.

## Conceptos nuevos

| Concepto | Nota propia | Definición breve |
|---|---|---|
| `MVCC` | [[note:postgresql-mvcc]] | Control de concurrencia multiversión |
| `xmin` | [[note:postgresql-xmin]] | ID de transacción que insertó la fila |
| `xmax` | [[note:postgresql-xmax]] | ID de transacción que eliminó la fila |
| `clog` | [[note:postgresql-clog]] | Commit log: estado de cada transacción |
| `pg_locks` | [[note:postgresql-pg-locks]] | Catálogo de locks activos |

## Citas textuales

> "The main advantage of using the MVCC model is that locks acquired for querying never conflict with locks acquired for writing data, so reading never blocks writing and writing never blocks reading." {src:blk_eeeeff000002}
> — *PostgreSQL 16 §13.1 Introduction*, retrieved 2026-09-27 {src:blk_c00000000020}

> "Read Uncommitted has the same behavior as Read Committed in PostgreSQL." {src:blk_eeeeff000003}
> — *PostgreSQL 16 §13.2.1 Read Uncommitted Level*, retrieved 2026-09-27 {src:blk_c00000000021}

## Énfasis del autor

:::note
El autor enfatiza que PostgreSQL no permite lecturas sucias incluso en Read Uncommitted — es un comportamiento deliberado del motor. {src:blk_c00000000030}
::: {src:blk_bbccddee0003}

## Detalles

### Mecanismos {src:blk_aabbccddee04}
Los mecanismos de MVCC operan a nivel de tupla y backend. {src:blk_c00000000070}

- `xmin`/`xmax` se almacenan en cada tupla (heap y TOAST).
- El commit log (`clog`) es un archivo en `pg_xact/` con el estado de cada transacción.
- Cada backend mantiene su propio `ActiveSnapshot` actualizado al inicio de cada query.

### Código {src:blk_aabbccddee05}
```sql
-- Bloqueo explícito: SELECT FOR UPDATE
SELECT * FROM accounts WHERE id = 42 FOR UPDATE; {src:blk_eeeeff000004}

-- Nivel de aislamiento explícito
BEGIN ISOLATION LEVEL SERIALIZABLE; {src:blk_eeeeff000005}
SELECT * FROM accounts WHERE balance > 0; {src:blk_eeeeff000006}
COMMIT;
# {src:blk_ccddeebf0001}
```

## Conexiones

:::derived
El capítulo conecta MVCC con [[note:postgresql-architecture]] (los backends procesan tuplas siguiendo el snapshot) y con [[note:postgres-connection-errors]] (los errores `FATAL: too many connections` se relacionan con MVCC porque cada backend mantiene su propio snapshot y consume memoria). {src:blk_eeeeff000007}
::: {src:blk_bbccddee0006}

## Erratas

:::warning
**Edición PG 9.6, sección 13.2:** la frase "snapshot is taken at statement start" es imprecisa — en Repeatable Read el snapshot es al inicio de la transacción, no de la sentencia. Corregido en ediciones posteriores. {src:blk_c00000000040}
::: {src:blk_bbccddee0007}

## Ejercicios

:::example
**Ejercicio 13.1:** ¿Qué retorna `SELECT * FROM accounts WHERE id = 42` en una transacción con `READ COMMITTED` si otra transacción concurrente hace `UPDATE accounts SET balance = 0 WHERE id = 42` y luego hace `COMMIT`?

**Pista:** considera que el snapshot se renueva en cada sentencia bajo Read Committed. {src:blk_c00000000050}
::: {src:blk_bbccddee0008}

:::example
**Ejercicio 13.2:** Explica por qué `VACUUM` es necesario en PostgreSQL pero no en MySQL con InnoDB.

**Pista:** compara cómo cada motor maneja las versiones de filas. {src:blk_c00000000051}
::: {src:blk_bbccddee0009}

## Backlinks
El digest se conecta con el capítulo previo (almacenamiento físico), el siguiente (performance tips) y el concepto principal (MVCC). {src:blk_c00000000080}

- [[note:chapter-12-physical-storage-digest]] — capítulo previo.
- [[note:chapter-14-performance-tips-digest]] — capítulo siguiente.
- [[note:postgresql-mvcc]] — concepto principal del capítulo.

## Ver también
Los errores típicos de conexión y el procedure de failover complementan la comprensión de MVCC; los enlaces muestran ambos aspectos. {src:blk_c00000000081}

- [[note:postgres-connection-errors]] — errores típicos de conexión.
- [[note:procedure-postgres-failover]] — procedure de failover.
