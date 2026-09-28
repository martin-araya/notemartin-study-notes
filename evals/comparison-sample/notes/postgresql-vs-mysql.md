---
title: "PostgreSQL 16 vs MySQL 8 (comparativa)"
note-type: comparison
status: draft
summary: "Comparativa de PostgreSQL 16 y MySQL 8: madurez, conformidad SQL, tipos de datos, replicación, JSON, y decisión por escenario (OLTP, web simple, OLAP, embedded)."
tags: [type/comparison, domain/databases]
source: "PostgreSQL 16 docs vs MySQL 8 docs"
source-type: docs
source-anchor: "comparativa"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group / Oracle
product: PostgreSQL 16 / MySQL 8
product-version: "16 / 8"
related: "[[note:postgresql-architecture]], [[note:postgres-connection-errors]]"
---

# PostgreSQL 16 vs MySQL 8 (comparativa)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Comparativa de PostgreSQL 16 y MySQL 8: madurez, conformidad SQL, tipos de datos, replicación, JSON, y decisión por escenario. |
| **Procedencia** | PostgreSQL 16 docs vs MySQL 8 docs (docs) §comparativa · recuperado 2026-09-27 |
| **Versión** | 16 / 8 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 5 min |

## TL;DR
PostgreSQL y MySQL son las dos RDBMS open source más maduras. PostgreSQL sobresale en conformidad SQL, extensibilidad (JSONB) y tipos ricos; MySQL sobresale en simplicidad operativa y read-heavy. La elección depende del caso de uso. {src:blk_b00000000001}

{layer:l2} {src:blk_fedcba000100}

## Comparativa
| Criterio | PostgreSQL 16 | MySQL 8 |
|---|---|---|
| Madurez (años en producción) | 28 | 28 |
| Conformidad SQL | alta (la más cercana al estándar) | media |
| Tipos de datos | rico (arrays, JSONB, ranges, hstore) | estándar |
| Replicación | streaming + logical replication | group replication + binlog |
| JSON | JSONB (binario, indexable) | JSON (texto) |
| Ecosistema | amplio | amplio |
:::tip
**Fila decisiva — Madurez.** Ambas tienen > 25 años de producción; el resto de criterios tiene diferencias superables con configuración y expertise del equipo. {src:blk_b00000000002}
::: {src:blk_bbccddee0001}

## Síntesis
Ambas RDBMS son open source y comparten [similitud 1: > 25 años de madurez con amplia adopción en producción] y [similitud 2: replicación nativa robusta con failover automático]. La diferencia clave es que PostgreSQL prioriza conformidad SQL y extensibilidad (JSONB indexable, arrays, tipos custom, extensiones) mientras MySQL prioriza simplicidad operativa y rendimiento en read-heavy workloads. {src:blk_b00000000003}

## Criterios
Los criterios cubren madurez, conformidad, tipos, replicación, JSON y ecosistema; cada uno se aplica a ambas opciones de forma paralela. {src:blk_b00000000004}

- **Madurez:** años en producción y estabilidad; ambas están entre las más estables del ecosistema open source. {src:blk_b00000000005}
- **Conformidad SQL:** cercanía al estándar SQL; PostgreSQL lidera históricamente. {src:blk_b00000000006}
- **Tipos de datos:** riqueza de tipos nativos; PostgreSQL tiene JSONB, arrays, ranges, hstore. {src:blk_b00000000007}
- **Replicación:** ambas soportan streaming y logical replication; MySQL tiene group replication multi-master. {src:blk_b00000000008}
- **JSON + ecosistema:** PostgreSQL JSONB es binario e indexable; MySQL JSON es texto; ecosistema similar en ambos. {src:blk_b00000000009}

## Matriz de decisión por escenario
| Escenario | Mejor opción | Justificación |
|---|---|---|
| OLTP con consultas complejas | PostgreSQL | Mejor planner, conformidad SQL, JSONB |
| Web app simple | MySQL | Más simple de operar |
| Data warehouse (OLAP) | PostgreSQL | JSONB + extensiones analíticas |
| Embedded / móvil | MySQL | Footprint menor |

## Trade-offs
| Trade-off | PostgreSQL 16 | MySQL 8 |
|---|---|---|
| Conformidad SQL vs simplicidad | alta | media |
| Tipos ricos vs footprint | rico | estándar |
| JSON binario vs texto | JSONB indexable | JSON texto |
| Extensibilidad vs operaciones | requiere expertise | más simple de operar |

## Casos de uso

### Cuándo elegir PostgreSQL {src:blk_aabbccddee02}
:::tip {src:blk_fedcba000200}
- Sistemas OLTP con consultas SQL complejas (joins, subqueries, window functions).
- Aplicaciones que requieren JSON indexable y búsqueda full-text.
- Data warehousing con PostgreSQL + extensiones (PostGIS, pg_partman, TimescaleDB).
- Sistemas con requisitos de conformidad SQL estrictos.
::: {src:blk_bbccddee0003}

### Cuándo elegir MySQL {src:blk_aabbccddee04}
:::tip {src:blk_fedcba000300}
- Web apps simples con read-heavy (CMS, blogs, e-commerce).
- Equipos con experiencia operativa en MySQL/InnoDB.
- Sistemas con infraestructura LAMP existente.
- Casos donde simplicidad operativa es prioridad sobre conformidad.
::: {src:blk_bbccddee0005}

## Veredicto
Para la mayoría de proyectos nuevos, **PostgreSQL es la opción por defecto** por su conformidad SQL, extensibilidad y ecosistema JSONB. Para web apps simples o cuando la operación del equipo es prioridad, **MySQL sigue siendo válido**. La diferencia real es de ecosistema y cultura del equipo, no de capacidad técnica pura — ambas manejan petabytes con la configuración correcta. {src:blk_b00000000010}

:::derived {src:blk_fedcba000400}
La "madurez equivalente" entre ambas es una percepción común pero PostgreSQL tiene una trayectoria más larga como proyecto open source mantenido por una comunidad (BSD license) vs MySQL que pasó por la adquisición de Sun/Oracle (GPL/comercial). Esto afecta a largo plazo el modelo de contribución, no la calidad técnica. {src:blk_fedcba000500}
::: {src:blk_bbccddee0006}

## Backlinks
La comparativa se complementa con la arquitectura interna de PostgreSQL y los errores típicos de conexión; los enlaces muestran los 2 ángulos. {src:blk_b00000000050}

- [[note:postgresql-architecture]] — arquitectura interna de PostgreSQL.
- [[note:postgres-connection-errors]] — errores típicos de conexión.
