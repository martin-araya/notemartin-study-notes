---
title: "Long paragraph concept (R2 violation)"
note-type: concept
status: published
summary: "Una nota de prueba con un párrafo demasiado largo que viola la regla R2 (max 200 palabras)."
reading-time-minutes: 3
---

# Long paragraph concept (R2 violation)

## TL;DR

Una nota con un párrafo que excede el límite de 200 palabras para L2.

## Definición

PostgreSQL es un sistema de gestión de bases de datos relacional y orientado a objetos, conocido por su robustez, su conformidad con el estándar SQL y su extensibilidad. Una de sus características más distintivas es el soporte nativo para tipos de datos avanzados como JSONB, arrays, rangos, hstore y tipos geométricos, lo que permite modelar problemas complejos sin sacrificar la integridad transaccional. Además, PostgreSQL ofrece un sistema de extensiones que permite añadir funcionalidades específicas, como PostGIS para datos geoespaciales, pg_trgm para búsqueda difusa, o pgvector para búsqueda semántica. Su motor de planificación de consultas es altamente sofisticado y puede reordenar joins, elegir índices, y aplicar optimizaciones estadísticas de forma automática. La concurrencia se gestiona mediante un modelo MVCC (Multi-Version Concurrency Control) que permite a los lectores no bloquear a los escritores y viceversa. Los puntos de guardado (savepoints) y las transacciones anidadas dan flexibilidad adicional al programador. El lenguaje PL/pgSQL permite escribir funciones y procedimientos almacenados con control de flujo, manejo de excepciones y tipos definidos por el usuario. Todo esto convierte a PostgreSQL en una plataforma extremadamente versátil para una amplia variedad de casos de uso, desde aplicaciones web tradicionales hasta análisis de datos avanzado y sistemas de información geográfica.

## Ejemplos

> [!example] Un ejemplo mínimo

```sql
SELECT * FROM users WHERE id = 1;
```

## Características

- Open source
- MVCC
- Extensiones
- SQL estándar
- JSONB nativo

{src:blk_a1234567890}
